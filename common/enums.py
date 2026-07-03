from enum import Enum, IntEnum


class Protocol(IntEnum):
    """Communication protocol."""

    TCP = 1
    RTU = 2


class ByteOrder(Enum):
    """32-bit register byte order."""

    ABCD = "ABCD"
    CDAB = "CDAB"
    BADC = "BADC"
    DCBA = "DCBA"


class MeterState(IntEnum):
    OFFLINE = 0
    ONLINE = 1
    ERROR = 2


class UserRole(IntEnum):
    USER = 0
    ADMIN = 1


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlarmState(IntEnum):
    NORMAL = 0
    ACTIVE = 1
    ACKNOWLEDGED = 2