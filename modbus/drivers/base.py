"""
modbus/drivers/base.py

Energy Monitor V2

Base class for all Modbus drivers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from modbus.clients.base import BaseClient
from modbus.device import Device


class BaseDriver(ABC):
    """
    Base class for all Modbus drivers.

    Every driver is responsible only for:
        - Reading Modbus registers
        - Converting register values
        - Applying CT/PT scaling
        - Updating Device measurements

    Drivers must NOT:
        - Open TCP/RTU connections
        - Access the database
        - Write to InfluxDB
        - Use Flask
    """

    #: Driver name used in database
    NAME: str = ""

    #: Register byte order
    BYTE_ORDER = None

    @abstractmethod
    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """
        Read all required registers and update Device.

        Raises:
            ModbusError
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def apply_ct(
        value: float,
        device: Device,
    ) -> float:
        """
        Apply CT ratio.
        """

        return value * device.meter.ct

    @staticmethod
    def apply_pt(
        value: float,
        device: Device,
    ) -> float:
        """
        Apply PT ratio.
        """

        return value * device.meter.pt

    @staticmethod
    def apply_ct_pt(
        value: float,
        device: Device,
    ) -> float:
        """
        Apply CT and PT ratios.
        """

        return (
            value
            * device.meter.ct
            * device.meter.pt
        )