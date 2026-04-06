"""
Callback options for passing data between action handlers and dialog flow.
Port of CallbackOptions.cs.
"""

from dataclasses import dataclass, field
from typing import Optional, List

from models.enums import PointTypes
from models.fatum_types import FinalAttractor


@dataclass
class CallbackOptions:
    """Data passed between action execution and trip report / dialog resumption."""
    reset_flag: bool = False

    start_trip_report_dialog: bool = False
    short_codes: Optional[List[str]] = None
    generated_points: Optional[List[FinalAttractor]] = None
    sha_gids: Optional[List[str]] = None
    messages: Optional[List[str]] = None
    point_types: Optional[List[PointTypes]] = None
    num_water_points_skipped: Optional[List[int]] = None
    what3words: Optional[List[str]] = None
    nearest_places: Optional[List[str]] = None

    update_intent_suggestions: bool = False
    intent_suggestions: Optional[List[str]] = None
    time_intent_suggestions_set: Optional[str] = None

    update_settings: bool = False
