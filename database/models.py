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

    This class contains only configuration.
    Runtime values are stored in modbus.device.Device.
    """

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------

    id: int | None = None

    enabled: bool = True

    name: str = ""

    description: str = ""

    driver: str = ""

    protocol: Protocol = Protocol.TCP

    # ------------------------------------------------------------------
    # Modbus TCP
    # ------------------------------------------------------------------

    address: str = ""

    port: int = 502

    # ------------------------------------------------------------------
    # Modbus RTU
    # ------------------------------------------------------------------

    serial_port: str = ""

    baudrate: int = 9600

    bytesize: int = 8

    parity: str = "N"

    stopbits: int = 1

    # ------------------------------------------------------------------
    # Common
    # ------------------------------------------------------------------

    slave: int = 1

    timeout: float = 1.0

    ct: float = 1.0

    pt: float = 1.0

    # ------------------------------------------------------------------
    # Helper properties
    # ------------------------------------------------------------------

    @property
    def is_tcp(self) -> bool:
        """Return True if Modbus TCP."""

        return self.protocol == Protocol.TCP

    @property
    def is_rtu(self) -> bool:
        """Return True if Modbus RTU."""

        return self.protocol == Protocol.RTU

    @property
    def connection_name(self) -> str:
        """Human readable connection."""

        if self.is_tcp:
            return f"{self.address}:{self.port}"

        return self.serial_port

    def __str__(self) -> str:

        return (
            f"Meter("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"driver='{self.driver}', "
            f"protocol={self.protocol.name})"
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