"""
Enumerations matching the original C# Enums.cs.
"""

from enum import IntEnum


class PointTypes(IntEnum):
    """Types of generated points. Order matches DB integer values from original."""
    Attractor = 0
    Void = 1
    Anomaly = 2
    PairAttractor = 3
    PairVoid = 4
    ScanAttractor = 5
    ScanVoid = 6
    ScanAnomaly = 7
    ScanPair = 8
    Quantum = 9
    QuantumTime = 10
    Pseudo = 11
    MysteryPoint = 12
    ChainAttractor = 13
    ChainVoid = 14
    ChainAnomaly = 15
    ChainQuantum = 16
    ChainPseudo = 17
