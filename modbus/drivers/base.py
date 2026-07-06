"""
modbus/drivers/base.py

Energy Monitor V2

Base class for all Modbus drivers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from common.enums import ByteOrder, RegisterType
from modbus.clients.base import BaseClient
from modbus.device import Device
from modbus.register_block import RegisterBlock


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

    #: Register type (Input/Holding)
    REGISTER_TYPE = RegisterType.INPUT

    #: Float byte order
    BYTE_ORDER = ByteOrder.ABCD

    # ------------------------------------------------------------------
    # Driver interface
    # ------------------------------------------------------------------

    @abstractmethod
    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """
        Read runtime measurements.
        """
        raise NotImplementedError

    def read_info(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """
        Read static device information.

        Override only if the meter supports it.
        """
        return

    # ------------------------------------------------------------------
    # Register helpers
    # ------------------------------------------------------------------

    def read_block(
        self,
        client: BaseClient,
        device: Device,
        address: int,
        count: int,
    ) -> RegisterBlock:
        """
        Read one Modbus register block.
        """

        if self.REGISTER_TYPE == RegisterType.INPUT:
            return client.read_input_registers(
                slave=device.slave,
                address=address,
                count=count,
            )

        return client.read_holding_registers(
            slave=device.slave,
            address=address,
            count=count,
        )

    # ------------------------------------------------------------------
    # Scaling helpers
    # ------------------------------------------------------------------

    @staticmethod
    def apply_ct(
        value: float | None,
        device: Device,
    ) -> float | None:
        """
        Apply CT ratio.
        """

        if value is None:
            return None

        return value * device.meter.ct

    @staticmethod
    def apply_pt(
        value: float | None,
        device: Device,
    ) -> float | None:
        """
        Apply PT ratio.
        """

        if value is None:
            return None

        return value * device.meter.pt

    @classmethod
    def apply_ct_pt(
        cls,
        value: float | None,
        device: Device,
    ) -> float | None:
        """
        Apply CT and PT ratios.
        """

        value = cls.apply_ct(value, device)
        value = cls.apply_pt(value, device)

        return value