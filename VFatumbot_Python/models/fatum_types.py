"""
Data types for Fatum attractor/void calculations.
Port of the C# structs from FatumFunctions.cs (LatLng, Coordinate, FinalAttr, FinalAttractor).
"""

from dataclasses import dataclass, field


@dataclass
class LatLng:
    """Geographic coordinate."""
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class DistanceBearing:
    """Distance and bearing from origin to a point."""
    distance: float = 0.0
    initial_bearing: float = 0.0
    final_bearing: float = 0.0


@dataclass
class Coordinate:
    """A point with its bearing info."""
    point: LatLng = field(default_factory=LatLng)
    bearing: DistanceBearing = field(default_factory=DistanceBearing)


@dataclass
class FinalAttr:
    """
    Attributes of a found attractor/void anomaly.
    Mirrors the C# FinalAttr struct.
    """
    GID: int = 0              # global id
    TID: int = 0              # timestamp id
    LID: int = 0              # local id (number in array)
    type: int = 0             # 1 = attractor, 2 = void
    x: float = 0.0
    y: float = 0.0
    center: Coordinate = field(default_factory=Coordinate)
    side: int = 0
    distance_err: float = 0.0  # calculation error due to curvature
    radius_m: float = 0.0      # radius of attractor peak
    n: int = 0                  # number of points
    mean: float = 0.0           # mean average
    rarity: int = 0             # significance simplified (0-8)
    power_old: float = 0.0      # old-style power
    power: float = 0.0          # area-based power
    z_score: float = 0.0        # Poisson z-score
    probability_single: float = 0.0
    integral_score: float = 0.0
    significance: float = 0.0   # Poisson z-score of entire event
    probability: float = 0.0


@dataclass
class FinalAttractor:
    """Wrapper for FinalAttr (mirrors C# FinalAttractor class)."""
    X: FinalAttr = field(default_factory=FinalAttr)


# Rarity level names matching original
RARITY_NAMES = {
    0: "N/A",
    1: "POOR",
    2: "COMMON",
    3: "UNCOMMON",
    4: "RARE",
    5: "EPIC",
    6: "LEGENDARY",
    7: "UNICORN",
    8: "SINGULARITY",
}

@dataclass
class TemporalAnomaly:
    """1D Temporal Anomaly representing a cluster in time [0..1440]"""
    type: int = 0             # 1 = attractor, 2 = void
    center_minute: float = 0.0 # minute of the day [0-1440)
    length: float = 0.0        # duration in minutes
    n_points: int = 0
    mean_expected: float = 0.0
    z_score: float = 0.0
    power: float = 0.0
    time_str: str = "00:00"    # formatted HH:MM

    def format_time(self) -> str:
        """Helper to format the minute into string."""
        hrs = int(self.center_minute // 60) % 24
        mins = int(self.center_minute % 60)
        return f"{hrs:02d}:{mins:02d}"
