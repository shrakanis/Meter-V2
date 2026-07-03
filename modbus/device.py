"""
modbus/device.py

Energy Monitor V2

Runtime device object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from common.enums import MeterState
from common.measurements import Measurements
from database.models import Meter


@dataclass(slots=True)
class Device:
    """
    Runtime representation of one Modbus device.

    Configuration:
        Meter

    Runtime:
        Measurements
        Connection state
    """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    meter: Meter

    # ------------------------------------------------------------------
    # Runtime state
    # ------------------------------------------------------------------

    state: MeterState = MeterState.OFFLINE

    connected: bool = False

    last_update: datetime | None = None

    last_error: str = ""

    response_time: float = 0.0

    # ------------------------------------------------------------------
    # Measurements
    # ------------------------------------------------------------------

    measurements: Measurements = field(
        default_factory=Measurements
    )

    # ------------------------------------------------------------------
    # Extra values
    # ------------------------------------------------------------------

    extra: dict[str, float] = field(
        default_factory=dict
    )

    # ==============================================================
    # Meter shortcuts
    # ==============================================================

    @property
    def id(self) -> int | None:
        return self.meter.id

    @property
    def name(self) -> str:
        return self.meter.name

    @property
    def driver(self) -> str:
        return self.meter.driver

    @property
    def protocol(self):
        return self.meter.protocol

    @property
    def slave(self) -> int:
        return self.meter.slave

    # ==============================================================
    # Runtime
    # ==============================================================

    def online(self) -> None:
        """Device communication successful."""

        self.connected = True

        self.state = MeterState.ONLINE

        self.last_error = ""

        self.last_update = datetime.now()

    def offline(
        self,
        error: str = "",
    ) -> None:
        """Device is offline."""

        self.connected = False

        self.state = MeterState.OFFLINE

        self.last_error = error

    def error(
        self,
        error: str,
    ) -> None:
        """Device communication error."""

        self.connected = False

        self.state = MeterState.ERROR

        self.last_error = error

    # ==============================================================
    # Helpers
    # ==============================================================

    def clear(self) -> None:
        """Clear runtime measurements."""

        self.measurements.reset()

        self.extra.clear()

    def update_timestamp(self) -> None:

        self.last_update = datetime.now()

    def age(self) -> float:
        """
        Seconds since last successful update.
        """

        if self.last_update is None:
            return 0.0

        return (
            datetime.now() - self.last_update
        ).total_seconds()

    # ==============================================================
    # Debug
    # ==============================================================

    def __str__(self) -> str:

        return (
            f"Device("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"state={self.state.name})"
        )