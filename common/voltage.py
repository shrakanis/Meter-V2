"""
common/models.py

Energy Monitor V2

Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass


# ----------------------------------------------------------------------
# Voltage
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Voltage:

    l1: float = 0.0
    l2: float = 0.0
    l3: float = 0.0

    average: float = 0.0


# ----------------------------------------------------------------------
# Current
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Current:

    l1: float = 0.0
    l2: float = 0.0
    l3: float = 0.0

    average: float = 0.0


# ----------------------------------------------------------------------
# Power
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Power:

    active: float = 0.0

    reactive: float = 0.0

    apparent: float = 0.0

    power_factor: float = 0.0


# ----------------------------------------------------------------------
# Energy
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Energy:

    import_active: float = 0.0

    export_active: float = 0.0

    import_reactive: float = 0.0

    export_reactive: float = 0.0


# ----------------------------------------------------------------------
# Measurements
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Measurements:

    voltage: Voltage = Voltage()

    current: Current = Current()

    power: Power = Power()

    energy: Energy = Energy()

    frequency: float = 0.0

    def reset(self) -> None:

        self.voltage = Voltage()

        self.current = Current()

        self.power = Power()

        self.energy = Energy()

        self.frequency = 0.0