"""
QRNG Provider for Randonautica API.
Fetches hex strings from the Randonautica Quantum RNG endpoint.
"""

import logging
import urllib.request
import json
import config
from .base_random_provider import BaseRandomProvider

logger = logging.getLogger(__name__)

class QRNGProvider(BaseRandomProvider):
    def __init__(self):
        super().__init__()
        self.hex_buffer = ""

    def get_binary_data(self, size_bytes: int) -> bytes:
        """
        Fetches quantum data from the API and returns it as bytes.
        """
        # API returns hex strings. Each hex pair is 1 byte.
        # We need double the hex characters for the requested bytes.
        needed_hex = size_bytes * 2
        
        try:
            # Note: The API might have a limit on how much it returns per request.
            # Randonautica typically fetches enough for the current operation.
            url = f"{config.QRNG_API_URL}&length={size_bytes}"
            req = urllib.request.Request(url, headers={"User-Agent": "VFatumbot-Python"})
            
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8")
                # Remove quotes if present
                content = content.strip().strip('"')
                
                # If it's a valid hex string, the length should be even
                if len(content) % 2 != 0:
                     # Maybe it's JSON with a list?
                     try:
                         data = json.loads(content)
                         if isinstance(data, dict) and "data" in data:
                             content = data["data"][0]
                         elif isinstance(data, list):
                             content = data[0]
                     except:
                         pass
                
                return bytes.fromhex(content)
                
        except Exception as e:
            logger.error(f"Error fetching from QRNG API: {e}")
            raise  # Fallback should be handled by the wrapper

    def next(self, max_val: int) -> int:
        """Get next random integer in range [0, max_val)"""
        if max_val <= 0:
            return 0
            
        # For simplicity in this port, we fetch 4 bytes for an integer
        data = self.get_binary_data(4)
        val = int.from_bytes(data, 'big')
        return val % max_val
