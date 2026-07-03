"""
modbus/drivers/base.py

Energy Monitor V2

Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from modbus.device import Device


class BaseDriver(ABC):
    """Base class for all Modbus drivers."""

    name: str = "unknown"

    @abstractmethod
    def read(self, client, device: Device) -> None:
        """
        Read device values.

        Raises:
            DriverError
            ConnectionError
            TimeoutError
        """
        raise NotImplementedError