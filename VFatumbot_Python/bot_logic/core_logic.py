"""
Core Logic Bridge.
Exposes Fatum functions for all frontends, platform-independent interface.
"""

from typing import List, Optional, Tuple, Dict
from datetime import datetime

import config
from bot_logic import fatum_functions as ff
from bot_logic import helpers
from rngs.rng_wrapper import RNGWrapper, CanIgnoreException
from models.enums import PointTypes


class PointResult:
    """Represents a generated point result."""
    def __init__(self, lat: float, lon: float, is_water: bool, message: str, w3w: dict = None, is_pair: bool = False, pair_type: str = None):
        self.lat = lat
        self.lon = lon
        self.is_water = is_water
        self.message = message
        self.w3w = w3w
        self.is_pair = is_pair
        self.pair_type = pair_type


async def generate_ida(
    lat: float, lon: float, radius: int, ida_type: str, entropy_mode: str = "camera", filter_water: bool = False
) -> Tuple[Optional[List[PointResult]], Optional[str]]:
    """
    Generate Intent Driven Anomaly (Attractor/Void/Anomaly).
    """
    try:
        rng = RNGWrapper(mode=entropy_mode)
        num_water_skipped = 0

        while True:
            from models.fatum_types import LatLng
            start_coord = LatLng(lat, lon)
            idas, sha_gid, temp_ida = ff.get_ida(start_coord, radius, 0, rng)
            idas = ff.sort_ida(idas, ida_type, 1)

            if not idas:
                return None, "No anomalies found. Try again later."

            ida = idas[0]
            coords = [ida.X.center.point.latitude, ida.X.center.point.longitude]

            is_water = await helpers.is_water_coordinates(coords)
            if filter_water and is_water:
                num_water_skipped += 1
                if num_water_skipped > config.WATER_POINTS_SEARCH_MAX:
                    return None, f"Couldn't find anything but water points ({num_water_skipped} skipped)."
                continue

            short_code = helpers.crc32_hash(f"gui_{datetime.now().isoformat()}")
            mesg = ff.format_ida_message(ida_type, ida, short_code)
            
            # Append Temporal Anomaly Info
            if temp_ida:
                t_type = "Attractor" if temp_ida.type == 1 else "Void"
                mesg += f"▶ Temporal {t_type}:\n"
                mesg += f"Suggested Time: {temp_ida.time_str}\n"
                mesg += f"Duration: ~{int(temp_ida.length)} min\n"
                mesg += f"Time z-score: {temp_ida.z_score:.2f}\n\n"

            w3w = await helpers.get_what3words_address(coords)

            if num_water_skipped > 0:
                mesg = f"(Water points skipped: {num_water_skipped})\n\n" + mesg

            res = PointResult(coords[0], coords[1], is_water, mesg, w3w)
            return [res], None

    except CanIgnoreException as e:
        return None, str(e)
    except Exception as e:
        return None, f"Error generating anomaly: {e}"


async def generate_random(
    lat: float, lon: float, radius: int, entropy_mode: str = "camera", filter_water: bool = False
) -> Tuple[Optional[List[PointResult]], Optional[str]]:
    """
    Generate Random point (Quantum or Pseudo).
    """
    try:
        rng = RNGWrapper(mode=entropy_mode)
        num_water_skipped = 0

        while True:
            if entropy_mode == "pseudo":
                coords = ff.get_pseudo_random(lat, lon, radius)
            else:
                coords = ff.get_quantum_random(lat, lon, radius, rng)

            is_water = await helpers.is_water_coordinates(coords)
            if filter_water and is_water:
                num_water_skipped += 1
                if num_water_skipped > config.WATER_POINTS_SEARCH_MAX:
                    return None, f"Couldn't find anything but water points ({num_water_skipped} skipped)."
                continue
            break

        ptype_code = "Q" if entropy_mode == "quantum" else ("P" if entropy_mode == "pseudo" else "C")
        short_code = ptype_code + "-" + helpers.crc32_hash(f"r_{datetime.now().isoformat()}")
        mesg = ff.format_random_message("random", coords[0], coords[1], entropy_mode, short_code, rng)
        
        w3w = await helpers.get_what3words_address(coords)
        
        if num_water_skipped > 0:
            mesg = f"(Water points skipped: {num_water_skipped})\n\n" + mesg

        res = PointResult(coords[0], coords[1], is_water, mesg, w3w)
        return [res], None
    except CanIgnoreException as e:
        return None, str(e)
    except Exception as e:
        return None, f"Error generating random point: {e}"
