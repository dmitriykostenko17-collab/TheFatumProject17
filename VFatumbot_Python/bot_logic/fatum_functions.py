"""
Core Fatum/attractor calculation functions.
Port of FatumFunctions.cs — replaces the closed-source libAttract C++ library
with a pure Python implementation of the attractor/void detection algorithm.

The algorithm:
1. Generate N random points within a circular area
2. Divide the area into a grid and count points per cell
3. Calculate statistical significance (z-score) of clustering/rarefaction
4. Return points that are statistically anomalous (attractors/voids)
"""

import math
import random
import time
import logging
from typing import List, Tuple, Optional

import numpy as np

import config
from models.fatum_types import (
    LatLng, DistanceBearing, Coordinate, FinalAttr, FinalAttractor, RARITY_NAMES, TemporalAnomaly
)
from rngs.rng_wrapper import RNGWrapper

logger = logging.getLogger(__name__)

# Earth radius in meters
EARTH_RADIUS_M = 6371000


def get_distance(lat0: float, lon0: float, lat1: float, lon1: float) -> int:
    """
    Calculate distance between two lat/lng points using Haversine formula.
    Returns distance in meters. Exact port of original GetDistance().
    """
    dlon = math.radians(lon1 - lon0)
    dlat = math.radians(lat1 - lat0)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat0)) * math.cos(math.radians(lat1)) *
         math.sin(dlon / 2) ** 2)
    angle = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(angle * EARTH_RADIUS_M)


def get_optimized_dots(area_radius_m: float) -> int:
    """
    Calculate the number of random points needed for the given radius.
    Optimized for performance on larger areas.
    This replaces the libAttract getOptimizedDots() function.
    """
    # Heuristic: scale points with area, with diminishing returns for large radii
    base_points = 1024  # minimum points
    area = math.pi * area_radius_m ** 2
    ref_area = math.pi * 3000 ** 2  # reference area at 3km radius

    scale = area / ref_area
    # Use sqrt scaling to avoid excessive points for large radii
    n = int(base_points * math.sqrt(scale))
    n = max(base_points, min(n, 8192))  # clamp between 1024 and 8192
    return n


def _required_entropy_bytes(n: int) -> int:
    """Calculate bytes of entropy needed for N random points."""
    # Each point needs 2 coordinates, each coordinate needs 4 bytes
    return n * 8


def _generate_random_points(
    center: LatLng,
    radius_m: float,
    n: int,
    rng: RNGWrapper
) -> List[Tuple[float, float]]:
    """
    Generate N random points within a circular area around center.
    Uses the RNG to generate truly random (quantum or pseudo) coordinates.
    """
    points = []
    for _ in range(n):
        # Generate random angle and distance within circle
        angle = rng.next_double() * 2 * math.pi
        # Use sqrt for uniform distribution within circle
        dist = math.sqrt(rng.next_double()) * radius_m

        # Convert to lat/lng offset
        dlat = dist * math.cos(angle) / EARTH_RADIUS_M * (180 / math.pi)
        dlon = (dist * math.sin(angle) /
                (EARTH_RADIUS_M * math.cos(math.radians(center.latitude))) *
                (180 / math.pi))

        points.append((center.latitude + dlat, center.longitude + dlon))

    return points


def _find_clusters(
    points: List[Tuple[float, float]],
    center: LatLng,
    radius_m: float,
    grid_size: int = 16
) -> List[FinalAttractor]:
    """
    Find statistical anomalies (attractors/voids) in point distribution.
    Uses grid-based density analysis with Poisson statistics.

    Returns list of FinalAttractor objects.
    """
    if not points:
        return []

    n_points = len(points)

    # Convert to numpy arrays for efficiency
    lats = np.array([p[0] for p in points])
    lons = np.array([p[1] for p in points])

    # Calculate grid bounds
    lat_min, lat_max = lats.min(), lats.max()
    lon_min, lon_max = lons.min(), lons.max()

    if lat_max == lat_min or lon_max == lon_min:
        return []

    # Create density grid
    lat_bins = np.linspace(lat_min, lat_max, grid_size + 1)
    lon_bins = np.linspace(lon_min, lon_max, grid_size + 1)

    grid, _, _ = np.histogram2d(lats, lons, bins=[lat_bins, lon_bins])

    # Calculate expected density (uniform distribution)
    total_cells = grid_size * grid_size
    expected = n_points / total_cells

    if expected <= 0:
        return []

    results = []

    # Scan for clusters using window scanning at multiple sizes
    for window_size in [2, 3, 4]:
        for i in range(grid_size - window_size + 1):
            for j in range(grid_size - window_size + 1):
                window = grid[i:i + window_size, j:j + window_size]
                observed = window.sum()
                window_cells = window_size * window_size
                window_expected = expected * window_cells

                if window_expected <= 0:
                    continue

                # Poisson z-score
                z_score = (observed - window_expected) / math.sqrt(window_expected)

                # Check significance
                if abs(z_score) < config.SIGNIFICANCE_THRESHOLD:
                    continue

                # Calculate center of this window
                lat_center = (lat_bins[i] + lat_bins[i + window_size]) / 2
                lon_center = (lon_bins[j] + lon_bins[j + window_size]) / 2

                # Calculate radius of this anomaly
                anomaly_radius = get_distance(
                    lat_center, lon_center,
                    lat_bins[i], lon_bins[j]
                )

                # Distance from origin
                dist_from_origin = get_distance(
                    center.latitude, center.longitude,
                    lat_center, lon_center
                )

                # Bearing from origin
                bearing = math.degrees(math.atan2(
                    math.sin(math.radians(lon_center - center.longitude)) *
                    math.cos(math.radians(lat_center)),
                    math.cos(math.radians(center.latitude)) *
                    math.sin(math.radians(lat_center)) -
                    math.sin(math.radians(center.latitude)) *
                    math.cos(math.radians(lat_center)) *
                    math.cos(math.radians(lon_center - center.longitude))
                ))
                if bearing < 0:
                    bearing = (bearing + 360) % 360

                # Determine type: attractor (z > 0) or void (z < 0)
                point_type = 1 if z_score > 0 else 2  # 1=attractor, 2=void

                # Power calculation
                if window_expected > 0:
                    power = observed / window_expected
                else:
                    power = 1.0

                # Rarity based on z-score
                abs_z = abs(z_score)
                if abs_z >= 8:
                    rarity = 8  # SINGULARITY
                elif abs_z >= 7:
                    rarity = 7  # UNICORN
                elif abs_z >= 6:
                    rarity = 6  # LEGENDARY
                elif abs_z >= 5:
                    rarity = 5  # EPIC
                elif abs_z >= 4.5:
                    rarity = 4  # RARE
                elif abs_z >= 4:
                    rarity = 3  # UNCOMMON
                elif abs_z >= 3.5:
                    rarity = 2  # COMMON
                elif abs_z >= config.SIGNIFICANCE_THRESHOLD:
                    rarity = 1  # POOR
                else:
                    rarity = 0

                # Calculate exact probability (p-value) using math.erfc (Normal approximation of Poisson)
                # This replaces the libAttract p-value logic.
                # z = (obs - exp) / sqrt(exp)
                # p = 0.5 * erfc(z / sqrt(2))
                prob = 0.5 * math.erfc(abs(z_score) / math.sqrt(2))

                attractor = FinalAttractor(
                    X=FinalAttr(
                        GID=0,
                        TID=int(time.time()),
                        LID=len(results),
                        type=point_type,
                        x=lon_center,
                        y=lat_center,
                        center=Coordinate(
                            point=LatLng(lat_center, lon_center),
                            bearing=DistanceBearing(
                                distance=dist_from_origin,
                                initial_bearing=bearing,
                                final_bearing=bearing,
                            )
                        ),
                        side=window_size,
                        distance_err=0.0,
                        radius_m=anomaly_radius,
                        n=int(observed),
                        mean=window_expected,
                        rarity=rarity,
                        power_old=power,
                        power=power,
                        z_score=z_score,
                        probability_single=prob,
                        integral_score=abs_z,
                        significance=z_score,
                        probability=prob,
                    )
                )
                results.append(attractor)

    # Deduplicate: if attractors overlap, keep the strongest
    results = _deduplicate_results(results, radius_m)

    return results

def _find_temporal_clusters(
    points_1d: List[float],
    ida_type: str = "any"
) -> Optional[TemporalAnomaly]:
    """Find the single strongest minute anomaly across 1440 granular bins (1 min each)."""
    if not points_1d: return None
    
    # 1440 granular minutes (0 to 1439)
    grid_size = 1440
    n_points = len(points_1d)
    expected = n_points / grid_size
    
    if expected <= 0: return None
    
    # Map all points directly to their integer minute bin [0..1439]
    grid, _ = np.histogram(points_1d, bins=range(1441))
    
    best_min = -1
    best_score = -1.0
    best_z = 0.0
    
    for minute in range(1440):
        observed = grid[minute]
        # Poisson Z-Score for a single minute bin
        z_score = (observed - expected) / math.sqrt(expected)
        
        # Filter by type (Attractor > 0, Void < 0)
        if ida_type == "attractor" and z_score <= 0: continue
        if ida_type == "void" and z_score >= 0: continue
        
        abs_z = abs(z_score)
        if abs_z > best_score:
            best_score = abs_z
            best_z = z_score
            best_min = minute

    if best_min == -1:
        return None
        
    point_type = 1 if best_z > 0 else 2
    power = (grid[best_min] / expected) if expected > 0 else 1.0
    
    # Direct mapping: The index 'best_min' is the minute of the day
    best_anomaly = TemporalAnomaly(
        type=point_type,
        center_minute=float(best_min),
        length=1.0, # Discrete 1-minute anomaly
        n_points=int(grid[best_min]),
        mean_expected=expected,
        z_score=best_z,
        power=power
    )
    
    best_anomaly.time_str = best_anomaly.format_time()
    return best_anomaly
        
    return best_anomaly


def _deduplicate_results(
    results: List[FinalAttractor],
    radius_m: float
) -> List[FinalAttractor]:
    """Remove overlapping results, keeping the strongest z-score."""
    if not results:
        return results

    # Sort by abs(z_score) descending
    results.sort(key=lambda a: abs(a.X.z_score), reverse=True)

    kept = []
    for candidate in results:
        is_duplicate = False
        for existing in kept:
            dist = get_distance(
                candidate.X.center.point.latitude,
                candidate.X.center.point.longitude,
                existing.X.center.point.latitude,
                existing.X.center.point.longitude,
            )
            # If within 20% of the anomaly radius, consider duplicate
            min_radius = min(candidate.X.radius_m, existing.X.radius_m)
            if dist < max(min_radius * 0.5, 100):
                is_duplicate = True
                break

        if not is_duplicate:
            kept.append(candidate)

    return kept


def get_ida(
    start_coord: LatLng,
    radius: float,
    meta: int,
    rng: RNGWrapper
) -> Tuple[List[FinalAttractor], Optional[str]]:
    """
    Main function: find Intent Driven Anomalies (attractors/voids).
    Port of FatumFunctions.GetIDA().

    Args:
        start_coord: Center location
        radius: Search radius in meters
        meta: 0 = normal, 1 = scan (longer, more entropy)
        rng: Random number generator wrapper

    Returns:
        (list of FinalAttractor, sha_gid, TemporalAnomaly)
    """
    result = []
    sha_gid = None
    temporal_result = None
    attempts = 0

    while len(result) == 0 and attempts < 10:
        attempts += 1
        n = get_optimized_dots(radius)

        # Get entropy
        entropy_bytes, sha_gid = rng.next_hex_bytes(
            _required_entropy_bytes(n), meta
        )

        # Generate random points
        points = _generate_random_points(start_coord, radius, n, rng)

        # Generate temporal points mapping directly to 0-1440 using the stream
        temporal_points = [rng.next_double() * 1440 for _ in range(n)]

        # Find clusters/anomalies
        result = _find_clusters(points, start_coord, radius)

        # Filter by filtering significance
        result = [
            a for a in result
            if abs(a.X.z_score) >= config.FILTERING_SIGNIFICANCE
        ]
        
        # If we found a valid spatial anomaly, use the temporal points of THIS EXACT ATTEMPT
        if len(result) > 0:
            temporal_result = _find_temporal_clusters(temporal_points)

    return result, sha_gid, temporal_result


def sort_ida(
    source: List[FinalAttractor],
    ida_type: str,
    ida_count: int
) -> List[FinalAttractor]:
    """
    Sort and filter IDAs by type and count.
    Port of FatumFunctions.SortIDA().
    """
    if not source:
        return []

    attractors = [a for a in source if a.X.type == 1]
    voids = [a for a in source if a.X.type == 2]

    # Sort by abs(z_score) descending, then by power descending
    def sort_key(a):
        p = a.X.power
        if a.X.type == 2 and p != 0:
            p = 1 / p
        return (abs(a.X.z_score), p)

    if ida_type == "attractor" and attractors:
        attractors.sort(key=sort_key, reverse=True)
        return attractors[:ida_count]
    elif ida_type == "void" and voids:
        voids.sort(key=sort_key, reverse=True)
        return voids[:ida_count]
    elif ida_type == "any" and (attractors or voids):
        combined = attractors + voids
        combined.sort(key=sort_key, reverse=True)
        return combined[:ida_count]

    return []


def get_pseudo_random(lat: float, lon: float, radius: int) -> List[float]:
    """
    Generate a pseudo-random point within a circle.
    Port of FatumFunctions.GetPseudoRandom().
    """
    while True:
        lat01 = lat + radius * math.cos(math.pi) / (EARTH_RADIUS_M * math.pi / 180)
        dlat = ((lat + radius / (EARTH_RADIUS_M * math.pi / 180)) - lat01) * 1_000_000
        lon01 = lon + radius * math.sin(3 * math.pi / 2) / math.cos(math.radians(lat)) / (EARTH_RADIUS_M * math.pi / 180)
        dlon = ((lon + radius * math.sin(math.pi / 2) / math.cos(math.radians(lat)) / (EARTH_RADIUS_M * math.pi / 180)) - lon01) * 1_000_000

        rlat = random.randint(0, max(1, int(dlat)))
        rlon = random.randint(0, max(1, int(dlon)))
        lat1 = lat01 + rlat / 1_000_000
        lon1 = lon01 + rlon / 1_000_000

        dist = get_distance(lat, lon, lat1, lon1)
        if dist <= radius:
            return [lat1, lon1]


def get_quantum_random(
    lat: float, lon: float, radius: int, rng: RNGWrapper
) -> List[float]:
    """
    Generate a quantum-random point within a circle.
    Port of FatumFunctions.GetQuantumRandom().
    """
    while True:
        lat01 = lat + radius * math.cos(math.pi) / (EARTH_RADIUS_M * math.pi / 180)
        dlat = ((lat + radius / (EARTH_RADIUS_M * math.pi / 180)) - lat01) * 1_000_000
        lon01 = lon + radius * math.sin(3 * math.pi / 2) / math.cos(math.radians(lat)) / (EARTH_RADIUS_M * math.pi / 180)
        dlon = ((lon + radius * math.sin(math.pi / 2) / math.cos(math.radians(lat)) / (EARTH_RADIUS_M * math.pi / 180)) - lon01) * 1_000_000

        rlat = rng.next(max(2, int(dlat)))
        rlon = rng.next(max(2, int(dlon)))

        lat1 = lat01 + rlat / 1_000_000
        lon1 = lon01 + rlon / 1_000_000

        dist = get_distance(lat, lon, lat1, lon1)
        if dist <= radius:
            return [lat1, lon1]


def format_ida_message(
    point_type: str,
    ida: FinalAttractor,
    short_code: str
) -> str:
    """
    Format an IDA result message. Port of FatumFunctions.Tolog() for IDAs.
    """
    if point_type == "blind":
        resp = "Mystery Point Generated\n\n"
    else:
        resp = "Intention Driven Anomaly found\n\n"

    # Code prefix
    if point_type == "blind":
        code = f"X-{short_code}"
    elif ida.X.type == 1:
        code = f"A-{short_code}"
    elif ida.X.type == 2:
        code = f"V-{short_code}"
    else:
        code = short_code

    resp += (f"{code} ({ida.X.center.point.latitude:.6f} "
             f"{ida.X.center.point.longitude:.6f})\n\n")

    if point_type != "blind":
        bearing = ida.X.center.bearing.final_bearing
        if bearing < 0:
            bearing = (bearing + 360) % 360.0

        type_name = "Attractor" if ida.X.type == 1 else "Void"
        resp += f"Type: {type_name}\n\n"
        resp += f"Radius: {int(ida.X.radius_m)}m\n\n"

        power_display = ida.X.power if ida.X.type == 1 else (1 / ida.X.power if ida.X.power != 0 else 0)
        resp += f"Power: {power_display:.2f}\n\n"
        resp += (f"Bearing: {ida.X.center.bearing.distance:.0f}m / "
                 f"{bearing:.1f}°\n\n")

        rarity_name = RARITY_NAMES.get(ida.X.rarity, "N/A")
        if ida.X.rarity > 0:
            resp += f"Abnormality Rank: {rarity_name}\n\n"
        resp += f"z-score: {ida.X.z_score:.2f}\n\n"

    return resp


def format_random_message(
    point_type: str,
    lat: float,
    lon: float,
    ptype: str,
    short_code: str,
    rng: Optional[RNGWrapper] = None
) -> str:
    """
    Format a random point message. Port of FatumFunctions.Tolog() for randoms.
    """
    if point_type == "blind":
        resp = "Mystery Point Generated\n\n"
    else:
        resp = "Random Point generated\n\n"

    # Code prefix
    if point_type == "blind":
        code = f"X-{short_code}"
    elif ptype == "pseudo":
        code = f"P-{short_code}"
    elif ptype in ("quantum", "qtime"):
        code = f"Q-{short_code}"
    else:
        code = short_code

    resp += f"{code} ({lat:.6f} {lon:.6f})\n\n"

    if ptype == "qtime" and rng is not None:
        hour = rng.next(24)
        minute = rng.next(60)
        resp += f"Suggested time: {hour}:{minute:02d}\n\n"

    return resp
