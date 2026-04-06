"""
Base random number provider.
Port of the C# BaseRandomProvider class from QuantumRandomNumberGenerator.cs.
Provides anti-modulo-bias integer generation and hex/byte output.
"""

import math
import struct
import random as stdlib_random
from typing import List


class BaseRandomProvider:
    """
    Base class for random number generators.
    Provides methods for generating random integers, bytes, hex strings
    with anti-modulo-bias (Fisher-Yates style).
    """

    def get_random_byte(self) -> int:
        """Override in subclasses. Returns a random byte [0..255]."""
        return stdlib_random.randint(0, 255)

    def get_random_hex(self, length: int) -> str:
        """Override in subclasses. Returns hex string of given length."""
        buf = bytes([stdlib_random.randint(0, 255) for _ in range(length // 2 + 1)])
        result = buf.hex()[:length]
        return result

    def next_bytes(self, count: int) -> bytes:
        """Generate `count` random bytes."""
        return bytes([self.get_random_byte() for _ in range(count)])

    def next(self, max_value: int) -> int:
        """
        Returns a non-negative random integer less than max_value.
        Uses anti-modulo-bias algorithm from original C# codebase.
        """
        if max_value <= 1:
            return 0

        req_bits = math.ceil(math.log2(max_value)) if max_value > 1 else 1
        req_bytes = math.ceil(req_bits / 8.0)
        bits_to_reset = req_bytes * 8 - req_bits
        rand_max = 2 ** req_bits

        while True:
            rnd_bytes = self.next_bytes(4)
            rnd_list = list(rnd_bytes)

            i_byte_start = req_bytes - 1
            # Clear bits from beginning to get random number in range 0..2^reqBits
            rnd_list[i_byte_start] = ((rnd_list[i_byte_start] << bits_to_reset) & 0xFF) >> bits_to_reset
            # Reset rest of the buffer
            for i in range(i_byte_start + 1, len(rnd_list)):
                rnd_list[i] = 0

            x = int.from_bytes(bytes(rnd_list), byteorder='little', signed=False)
            n = max_value

            if not (x >= (rand_max - n) and x >= n):
                return x % n

    def next_range(self, min_value: int, max_value: int) -> int:
        """Returns a random integer in [min_value, max_value)."""
        if max_value < min_value:
            raise ValueError("max_value must be >= min_value")
        if max_value - min_value <= 1:
            return min_value
        return self.next(max_value - min_value) + min_value

    def next_hex(self, length: int) -> str:
        """Returns a random hex string of specified length."""
        return self.get_random_hex(length)

    def next_hex_bytes(self, length: int, meta: int = 0) -> tuple:
        """
        Returns (bytes, sha_gid) tuple.
        meta=1 means long-running scan (slower, more entropy).
        """
        hex_str = ""
        if meta == 1:
            # Long scan: accumulate entropy over time
            import time
            while len(hex_str) < length * 20:
                hex_str += self.get_random_hex(length * 2)
                time.sleep(0.5)  # Reduced from original 30s for practicality
        else:
            hex_str = self.get_random_hex(length * 2)

        # Convert hex to bytes
        num_chars = len(hex_str)
        result = bytes([int(hex_str[i:i+2], 16) for i in range(0, num_chars - 1, 2)])

        sha_gid = None
        return result, sha_gid

    def next_double(self) -> float:
        """Returns a random float in [0.0, 1.0)."""
        raw_bytes = self.next_bytes(4)
        val = int.from_bytes(raw_bytes, byteorder='little', signed=False)
        return val / (2**32)

    def next_coord(self, dlat: int, dlon: int, amount: int) -> List[List[int]]:
        """Generate random coordinates offsets."""
        result = []
        for _ in range(amount):
            rlat = self.next(dlat)
            rlon = self.next(dlon)
            result.append([rlat, rlon])
        return result
