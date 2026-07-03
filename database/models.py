"""
database/models.py

Energy Monitor V2

Version: 1.1.0
"""

from dataclasses import dataclass

from common.enums import Protocol


# ----------------------------------------------------------------------
# User
# ----------------------------------------------------------------------

@dataclass(slots=True)
class User:
    """Application user."""

    id: int | None = None

    username: str = ""

    password: str = ""

    admin: bool = False


# ----------------------------------------------------------------------
# Setting
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Setting:
    """Application setting."""

    key: str = ""

    value: str = ""


# ----------------------------------------------------------------------
# Meter
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Meter:
    """Energy meter configuration."""

    id: int | None = None

    name: str = ""

    enabled: bool = True

    driver: str = ""

    protocol: Protocol = Protocol.TCP

    address: str = ""

    port: int = 502

    slave: int = 1

    ct: float = 1.0

    pt: float = 1.0

    location: str = ""

    description: str = ""


# ----------------------------------------------------------------------
# SystemInfo
# ----------------------------------------------------------------------

@dataclass(slots=True)
class SystemInfo:
    """Application information."""

    database_version: int = 1


# ----------------------------------------------------------------------
# DashboardData
# ----------------------------------------------------------------------

@dataclass(slots=True)
class DashboardData:
    """Dashboard summary."""

    total_power: float = 0.0

    total_energy: float = 0.0

    online_devices: int = 0

    offline_devices: int = 0