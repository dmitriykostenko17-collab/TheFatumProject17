"""
Configuration and constants for VFatumbot Python port.
Loads settings from .env file and defines application constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── App Info ───────────────────────────────────────────────────────
APP_VERSION = "4.1.0-py"

# ─── Environment ────────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# ─── Google Maps API ────────────────────────────────────────────────
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyDY2N2VQDGATq0DCwTlEsM2p23Z-ngLSng")

# ─── What3Words API ─────────────────────────────────────────────────
W3W_API_KEY = os.getenv("W3W_API_KEY", "")

# ─── QRNG API (Randonautica) ──────────────────────────────────────
# Extracted from Randonautica 3.2.4
QRNG_API_URL = "https://qrng.randonautica.app/api/json/randhex?device_id=QWR70154"

# ─── Entropy Sources ──────────────────────────────────────────────
# Users can now choose between local Camera Entropy or Quantum Cloud (QRNG).

# ─── Randonauts Entropy API ────────────────────────────────────────
if IS_PRODUCTION:
    RANDONAUTS_API_URL = "https://api.randonauts.com"
else:
    RANDONAUTS_API_URL = "https://devapi.randonauts.com"

# ─── Google Maps thumbnails ────────────────────────────────────────
THUMBNAIL_SIZE = "320x320"

# ─── Coordinate defaults ──────────────────────────────────────────
INVALID_COORD = -1000.0

# ─── Radius settings (meters) ──────────────────────────────────────
DEFAULT_RADIUS = 3000
RADIUS_MAX = 100000
RADIUS_MIN = 1000

# ─── Chain settings ────────────────────────────────────────────────
CHAIN_DISTANCE_MAX = 20.0
CHAIN_DISTANCE_MIN = 2.0

# ─── Water point detection ─────────────────────────────────────────
WATER_POINTS_SEARCH_MAX = 10

# ─── Attractor calculation thresholds ──────────────────────────────
SIGNIFICANCE_THRESHOLD = 2.5
FILTERING_SIGNIFICANCE = 4.0

# ─── Database ──────────────────────────────────────────────────────
DATABASE_PATH = os.getenv("DATABASE_PATH", "vfatumbot.db")

# ─── Words file for intent suggestions ─────────────────────────────
WORDS_FILE_PATH = os.path.join(os.path.dirname(__file__), "words.txt")
