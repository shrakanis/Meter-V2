"""
database/models.py

Energy Monitor V2

Database models.
"""

from __future__ import annotations

from dataclasses import dataclass

from common.enums import Protocol


@dataclass(slots=True)
class Meter:
    """
    Energy meter configuration.

    Supported meter types
    ---------------------
    modbus
        Modbus TCP, RTU or RTU over TCP meter.

    p1
        Smart meter connected through a P1 serial/USB port.

    This class contains configuration only.
    Runtime measurements are stored in modbus.device.Device.
    """

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------

    id: int | None = None

    enabled: bool = True

    name: str = ""

    description: str = ""

    meter_type: str = "modbus"

    driver: str = ""

    protocol: Protocol = Protocol.TCP

    # ------------------------------------------------------------------
    # TCP / RTU over TCP
    # ------------------------------------------------------------------

    address: str = ""

    port: int = 502

    # ------------------------------------------------------------------
    # Serial / Modbus RTU / P1
    # ------------------------------------------------------------------

    serial_port: str = ""

    baudrate: int = 9600

    bytesize: int = 8

    parity: str = "N"

    stopbits: int = 1

    # ------------------------------------------------------------------
    # Modbus
    # ------------------------------------------------------------------

    slave: int = 1

    # ------------------------------------------------------------------
    # Common
    # ------------------------------------------------------------------

    timeout: float = 1.0

    ct: float = 1.0

    pt: float = 1.0

    # ------------------------------------------------------------------
    # Helper properties
    # ------------------------------------------------------------------

    @property
    def normalized_meter_type(self) -> str:
        """Return normalized meter type."""

        return (
            self.meter_type
            or "modbus"
        ).strip().lower()

    @property
    def is_modbus(self) -> bool:
        """Return True for a Modbus meter."""

        return (
            self.normalized_meter_type
            == "modbus"
        )

    @property
    def is_p1(self) -> bool:
        """Return True for a P1 smart meter."""

        return (
            self.normalized_meter_type
            == "p1"
        )

    @property
    def is_tcp(self) -> bool:
        """Return True for Modbus TCP."""

        return (
            self.is_modbus
            and self.protocol
            == Protocol.TCP
        )

    @property
    def is_rtu(self) -> bool:
        """Return True for Modbus RTU."""

        return (
            self.is_modbus
            and self.protocol
            == Protocol.RTU
        )

    @property
    def is_serial(self) -> bool:
        """
        Return True when the meter uses a serial port.

        This includes Modbus RTU and P1.
        """

        return (
            self.is_p1
            or self.is_rtu
        )

    @property
    def connection_name(self) -> str:
        """Return human-readable connection information."""

        if self.is_p1:

            if self.serial_port:
                return (
                    f"P1 {self.serial_port} "
                    f"@ {self.baudrate}"
                )

            return "P1 serial port not configured"

        if self.is_tcp:

            if self.address:
                return (
                    f"{self.address}:"
                    f"{self.port}"
                )

            return "TCP address not configured"

        if self.serial_port:

            return (
                f"{self.serial_port} "
                f"@ {self.baudrate}"
            )

        return "Serial port not configured"

    def __str__(self) -> str:

        protocol_name = getattr(
            self.protocol,
            "name",
            str(self.protocol),
        )

        return (
            "Meter("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type='{self.normalized_meter_type}', "
            f"driver='{self.driver}', "
            f"protocol={protocol_name}"
            ")"
        )


# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------


@dataclass(slots=True)
class Setting:
    """Application setting."""

    key: str

    value: str


# ----------------------------------------------------------------------
# User
# ----------------------------------------------------------------------


@dataclass(slots=True)
class User:
    """Application user."""

    id: int | None = None

    username: str = ""

    password: str = ""

    role: int = 0

    created_at: str = ""