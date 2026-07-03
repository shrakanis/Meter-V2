"""
modbus/exceptions.py

Energy Monitor V2

Version: 1.0.0
"""


class ModbusError(Exception):
    """Base Modbus exception."""


class ConnectionError(ModbusError):
    """Connection failed."""


class TimeoutError(ModbusError):
    """Communication timeout."""


class DriverError(ModbusError):
    """Driver error."""


class RegisterError(ModbusError):
    """Invalid register data."""