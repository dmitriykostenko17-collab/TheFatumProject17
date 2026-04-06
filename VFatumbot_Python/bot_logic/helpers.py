"""
Helper functions.
Port of Helpers.cs — geocoding, W3W, water detection, hashing, intent suggestions.
"""

import hashlib
import re
import logging
import urllib.request
import json
from typing import Optional, Tuple, List

import config
from rngs.rng_wrapper import RNGWrapper

logger = logging.getLogger(__name__)


async def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address string using Google Maps Geocoding API.
    Returns (lat, lon) tuple or None if not found.
    """
    if not config.GOOGLE_MAPS_API_KEY:
        logger.warning("Google Maps API key not configured")
        return None

    try:
        encoded = urllib.parse.quote(address.strip())
        url = (f"https://maps.googleapis.com/maps/api/geocode/json"
               f"?address={encoded}&key={config.GOOGLE_MAPS_API_KEY}")
        req = urllib.request.Request(url, headers={"User-Agent": "VFatumbot-Python"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
    except Exception as e:
        logger.error(f"Geocoding error: {e}")

    return None


async def get_what3words_address(coords: List[float]) -> Optional[dict]:
    """
    Get What3Words address for coordinates.
    Returns dict with 'words', 'nearestPlace', 'country' keys.
    """
    if not config.W3W_API_KEY:
        return None

    try:
        url = (f"https://api.what3words.com/v3/convert-to-3wa"
               f"?coordinates={coords[0]}%2C{coords[1]}&key={config.W3W_API_KEY}")
        req = urllib.request.Request(url, headers={"User-Agent": "VFatumbot-Python"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data
    except Exception as e:
        logger.error(f"What3Words error: {e}")
    return None


async def is_water_coordinates(coords: List[float]) -> bool:
    """
    Check if coordinates are on water using Google Static Maps API.
    Gets 1x1 pixel map with water colored green and checks if result matches.
    Port of Helpers.IsWaterCoordinatesAsync().
    """
    if not config.GOOGLE_MAPS_API_KEY:
        return False

    try:
        url = (
            "https://maps.googleapis.com/maps/api/staticmap?scale=2"
            "&zoom=13&size=1x1&sensor=false&visual_refresh=true"
            "&style=feature:water|color:0x00FF00"
            "&style=element:labels|visibility:off"
            "&style=feature:transit|visibility:off"
            "&style=feature:poi|visibility:off"
            "&style=feature:road|visibility:off"
            "&style=feature:administrative|visibility:off"
            f"&format=png8&center={coords[0]},{coords[1]}"
            f"&key={config.GOOGLE_MAPS_API_KEY}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "VFatumbot-Python"})
        with urllib.request.urlopen(req, timeout=10) as response:
            result_png = response.read()

        # The solid green 2x2 PNG that represents water
        solid_green_hex = (
            "89504E470D0A1A0A0000000D494844520000000200000002010300000048789F67"
            "00000006504C544500FF00FFFFFF6FBD585100000001624B474401FF022DDE"
            "0000000C4944415408D7636060600000000400012734270A0000000049454E44AE426082"
        )
        solid_green_png = bytes.fromhex(solid_green_hex)
        return result_png == solid_green_png
    except Exception as e:
        logger.error(f"Water check error: {e}")
    return False


def get_intent_suggestions(rng: RNGWrapper, num_suggestions: int = 5) -> List[str]:
    """
    Get random word suggestions from the dictionary.
    Port of Helpers.GetIntentSuggestionsAsync().
    """
    try:
        with open(config.WORDS_FILE_PATH, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]

        if not words:
            return ["(dictionary not loaded)"]

        result = []
        for _ in range(num_suggestions):
            idx = rng.next(len(words))
            result.append(words[idx])
        return result
    except FileNotFoundError:
        logger.warning(f"Words file not found: {config.WORDS_FILE_PATH}")
        return ["(words.txt not found)"]
    except Exception as e:
        logger.error(f"Intent suggestions error: {e}")
        return ["(error loading words)"]


def sha256_hash(raw_data: str) -> str:
    """SHA-256 hash of a string. Port of Helpers.Sha256Hash()."""
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()


def crc32_hash(raw_data: str) -> str:
    """CRC-32 hash of a string, formatted as uppercase hex. Port of Helpers.Crc32Hash()."""
    import binascii
    crc = binascii.crc32(raw_data.encode("utf-8")) & 0xFFFFFFFF
    return f"{crc:08X}"


def intercept_location_from_text(text: str) -> Optional[Tuple[float, float]]:
    """
    Try to extract coordinates from a Google Maps URL or text.
    Port of Helpers.InterceptLocation() text parsing part.
    """
    if not text:
        return None

    # Check for Google Maps URL with @ coordinates
    if "google.com/maps/" in text or "Sending location @" in text:
        try:
            parts = text.split("@")
            if len(parts) >= 2:
                coord_parts = parts[1].split(",")
                if len(coord_parts) >= 2:
                    lat = float(coord_parts[0].strip())
                    lon = float(coord_parts[1].strip().split("/")[0].split("?")[0])
                    return (lat, lon)
        except (ValueError, IndexError):
            pass

    # Check for direct coordinate input (lat,lon or lat lon)
    stripped = text.strip()
    coord_match = re.match(
        r'^(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)$', stripped
    )
    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except ValueError:
            pass

    return None


def get_country_from_w3w(w3w_result: Optional[dict]) -> str:
    """Get country name from W3W result."""
    if not w3w_result or "country" not in w3w_result:
        return ""
    country_code = w3w_result.get("country", "")
    if country_code:
        return f" ({country_code.upper()})"
    return ""


import urllib.parse  # noqa: E402
