"""
common/measurements.py

Energy Monitor V2

Common measurement models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ----------------------------------------------------------------------
# Phase measurement
# ----------------------------------------------------------------------

@dataclass(slots=True)
class PhaseMeasurement:
    """
    Measurement containing total and/or phase values.

    Not every meter provides every value.
    Missing values remain None.
    """

    total: float | None = None

    l1: float | None = None
    l2: float | None = None
    l3: float | None = None

    average: float | None = None


# ----------------------------------------------------------------------
# Energy
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Energy:

    import_active: float | None = None

    export_active: float | None = None

    import_reactive: float | None = None

    export_reactive: float | None = None


# ----------------------------------------------------------------------
# Measurements
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Measurements:
    """
    Standard measurements supported by the application.

    Any meter specific values should be stored in:

        device.extra
    """

    voltage: PhaseMeasurement = field(
        default_factory=PhaseMeasurement
    )

    current: PhaseMeasurement = field(
        default_factory=PhaseMeasurement
    )

    active_power: PhaseMeasurement = field(
        default_factory=PhaseMeasurement
    )

    reactive_power: PhaseMeasurement = field(
        default_factory=PhaseMeasurement
    )

    apparent_power: PhaseMeasurement = field(
        default_factory=PhaseMeasurement
    )

    power_factor: PhaseMeasurement = field(
        default_factory=PhaseMeasurement
    )

    frequency: float | None = None

    energy: Energy = field(
        default_factory=Energy
    )

    def reset(self) -> None:
        """
        Reset all measurements.
        """

        self.__dict__.update(
            Measurements().__dict__
        )