"""
Pseudo random number generator.
Port of PseudoRandomNumberGenerator.cs.
Uses Python's built-in random module — useful for local development.
"""

from rngs.base_random_provider import BaseRandomProvider


class PseudoRNG(BaseRandomProvider):
    """Pseudo-random number generator for testing/development."""
    pass  # Inherits all default behavior from BaseRandomProvider which uses stdlib random
