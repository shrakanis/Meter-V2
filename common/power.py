"""
common/power.py

Energy Monitor V2

Version: 1.1.0
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class PhasePower:
    """Per-phase power."""

    l1: float = 0.0
    l2: float = 0.0
    l3: float = 0.0

    total: float = 0.0


@dataclass(slots=True)
class Power:
    """Power measurements."""

    active: PhasePower = field(default_factory=PhasePower)

    reactive: PhasePower = field(default_factory=PhasePower)

    apparent: PhasePower = field(default_factory=PhasePower)

    power_factor: float = 0.0