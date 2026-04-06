"""
Card/message factory — generates Google Maps URLs and action buttons.
Port of CardFactory.cs — creates shareable links and button configurations for UI.
"""

from typing import List, Optional

import config


def create_google_maps_url(coords: List[float]) -> str:
    """Create a Google Maps place URL."""
    return f"https://www.google.com/maps/place/{coords[0]}+{coords[1]}/@{coords[0]}+{coords[1]},14z"


def create_google_street_view_url(coords: List[float]) -> str:
    """Create a Google Street View URL."""
    return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={coords[0]},{coords[1]}&fov=90&heading=235&pitch=10"


def create_google_earth_url(coords: List[float]) -> str:
    """Create a Google Earth URL."""
    return f"https://earth.google.com/web/search/{coords[0]},{coords[1]}"


def create_google_maps_static_thumbnail(coords: List[float], for_remote_viewing: bool = False) -> str:
    """Create a Google Static Maps thumbnail URL."""
    zoom = 4 if for_remote_viewing else 15
    return (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"&markers=color:red%7Clabel:C%7C{coords[0]}+{coords[1]}"
        f"&zoom={zoom}&size={config.THUMBNAIL_SIZE}"
        f"&maptype=roadmap&key={config.GOOGLE_MAPS_API_KEY}"
    )


def create_google_street_view_thumbnail(coords: List[float]) -> str:
    """Create a Google Street View thumbnail URL."""
    return (
        f"https://maps.googleapis.com/maps/api/streetview?"
        f"size={config.THUMBNAIL_SIZE}&location={coords[0]},{coords[1]}"
        f"&fov=90&heading=235&pitch=10&key={config.GOOGLE_MAPS_API_KEY}"
    )


def create_google_earth_thumbnail(coords: List[float]) -> str:
    """Create a Google Earth (satellite) thumbnail URL."""
    return (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"&markers=color:red%7Clabel:C%7C{coords[0]}+{coords[1]}"
        f"&zoom=18&size={config.THUMBNAIL_SIZE}"
        f"&maptype=satellite&key={config.GOOGLE_MAPS_API_KEY}"
    )


def create_google_maps_route_url(coords_list: List[List[float]]) -> str:
    """Create a Google Maps driving directions URL for chain points."""
    url = "https://www.google.com/maps/dir/"
    for coords in coords_list:
        url += f"{coords[0]}+{coords[1]}/"
    return url


def get_location_buttons(coords: List[float]) -> list:
    """
    Create action buttons for a location.
    Returns list of button dicts that can be used by any UI framework.
    """
    return [
        [
            {"text": "🗺 Maps", "url": create_google_maps_url(coords)},
            {"text": "🚶 Street View", "url": create_google_street_view_url(coords)},
            {"text": "🌍 Earth", "url": create_google_earth_url(coords)},
        ]
    ]


def get_chain_buttons(coords_list: List[List[float]]) -> list:
    """Create inline keyboard button for a chain route."""
    return [
        [{"text": "🗺 Open Route on Google Maps", "url": create_google_maps_route_url(coords_list)}]
    ]
