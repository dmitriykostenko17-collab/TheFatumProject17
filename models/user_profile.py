"""
User profile models.
Port of UserProfilePersistent.cs and UserProfileTemporary.cs.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple

import config
from models.fatum_types import LatLng


@dataclass
class UserProfilePersistent:
    """Persisted user data (stored in SQLite)."""
    user_id: str = ""
    is_include_water_points: bool = True
    is_display_google_thumbnails: bool = False
    push_user_id: str = ""
    has_set_location_once: bool = False
    has_agreed_to_tos: bool = False


@dataclass
class UserProfileTemporary:
    """
    Session/temporary user data (in-memory).
    Includes location, radius, scanning flags, and settings synced from persistent.
    """
    user_id: str = ""
    push_user_id: str = ""
    is_include_water_points: bool = True
    is_display_google_thumbnails: bool = False

    latitude: float = config.INVALID_COORD
    longitude: float = config.INVALID_COORD
    radius: int = config.DEFAULT_RADIUS

    is_scanning: bool = False
    intent_suggestions: Optional[List[str]] = None
    time_intent_suggestions_set: Optional[str] = None

    @property
    def is_location_set(self) -> bool:
        return (self.latitude != config.INVALID_COORD
                and self.longitude != config.INVALID_COORD)

    @property
    def location(self) -> LatLng:
        return LatLng(self.latitude, self.longitude)

    def reset_location(self):
        self.latitude = config.INVALID_COORD
        self.longitude = config.INVALID_COORD
