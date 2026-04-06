"""
Wrapper around RNG with error handling and mode switching.
Port of QuantumRandomNumberGeneratorWrapper.cs.
"""

import logging

from rngs.camera_rng import CameraRNG
from rngs.qrng_provider import QRNGProvider
from rngs.pseudo_rng import PseudoRNG
from rngs.base_random_provider import BaseRandomProvider

logger = logging.getLogger(__name__)

# Single instances to hold state across calls
camera_rng_instance = CameraRNG()
qrng_instance = QRNGProvider()

class CanIgnoreException(Exception):
    """Exception that can be safely ignored (QRNG source temporarily unavailable)."""
    pass


class RNGWrapper:
    """
    Wrapper around camera/qrng/pseudo RNG with error handling.
    """

    def __init__(self, mode: str = "camera"):
        """
        mode: 'camera', 'quantum', or 'pseudo'
        """
        if mode == "pseudo":
            self._rng: BaseRandomProvider = PseudoRNG()
        elif mode == "quantum":
            self._rng: BaseRandomProvider = qrng_instance
        else:
            self._rng: BaseRandomProvider = camera_rng_instance

    def next(self, max_value: int) -> int:
        """Generate random integer in [0, max_value)."""
        try:
            return self._rng.next(max_value)
        except CanIgnoreException:
            raise
        except Exception as e:
            logger.error(f"RNG error: {e}")
            raise CanIgnoreException(
                "Sorry, there was an error sourcing quantum entropy. Try again later."
            ) from e

    def next_range(self, min_value: int, max_value: int) -> int:
        """Generate random integer in [min_value, max_value)."""
        try:
            return self._rng.next_range(min_value, max_value)
        except CanIgnoreException:
            raise
        except Exception as e:
            logger.error(f"RNG error: {e}")
            raise CanIgnoreException(str(e)) from e

    def next_hex(self, length: int) -> str:
        """Generate random hex string."""
        try:
            return self._rng.next_hex(length)
        except CanIgnoreException:
            raise
        except Exception as e:
            logger.error(f"RNG error: {e}")
            raise CanIgnoreException(str(e)) from e

    def next_hex_bytes(self, length: int, meta: int = 0) -> tuple:
        """Generate random bytes from hex. Returns (bytes, sha_gid)."""
        try:
            return self._rng.next_hex_bytes(length, meta)
        except CanIgnoreException:
            raise
        except Exception as e:
            logger.error(f"RNG error: {e}")
            raise CanIgnoreException(str(e)) from e

    def next_bytes(self, count: int) -> bytes:
        """Generate random bytes."""
        try:
            return self._rng.next_bytes(count)
        except CanIgnoreException:
            raise
        except Exception as e:
            logger.error(f"RNG error: {e}")
            raise CanIgnoreException(str(e)) from e

    def next_double(self) -> float:
        """Generate random double in [0, 1)."""
        try:
            return self._rng.next_double()
        except CanIgnoreException:
            raise
        except Exception as e:
            logger.error(f"RNG error: {e}")
            raise CanIgnoreException(str(e)) from e
