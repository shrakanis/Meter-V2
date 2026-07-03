"""
common/measurements.py

Energy Monitor V2

Version: 1.1.0
"""

from dataclasses import dataclass, field

from common.current import Current
from common.energy import Energy
from common.power import Power
from common.voltage import Voltage


@dataclass(slots=True)
class Measurements:
    """Runtime measurements."""

    voltage: Voltage = field(default_factory=Voltage)

    current: Current = field(default_factory=Current)

    power: Power = field(default_factory=Power)

    energy: Energy = field(default_factory=Energy)

    frequency: float = 0.0

    def reset(self) -> None:
        """Reset all measurements."""

        self.voltage = Voltage()
        self.current = Current()
        self.power = Power()
        self.energy = Energy()

        self.frequency = 0.0