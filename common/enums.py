"""
common/enums.py

Energy Monitor V2

Version: 1.0.0
"""

from enum import Enum, IntEnum


class Protocol(IntEnum):
    """Communication protocol."""

    TCP = 1
    RTU = 2


class MeterState(IntEnum):
    """Current meter state."""

    OFFLINE = 0
    ONLINE = 1
    ERROR = 2


class UserRole(IntEnum):
    """User permissions."""

    USER = 0
    ADMIN = 1


class LogLevel(str, Enum):
    """Application log level."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlarmState(IntEnum):
    """Alarm state."""

    NORMAL = 0
    ACTIVE = 1
    ACKNOWLEDGED = 2