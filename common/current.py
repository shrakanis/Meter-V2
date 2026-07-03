"""
common/current.py

Energy Monitor V2

Version: 1.0.0
"""

from dataclasses import dataclass


@dataclass(slots=True)
class Current:
    """Current measurements."""

    l1: float = 0.0
    l2: float = 0.0
    l3: float = 0.0

    average: float = 0.0