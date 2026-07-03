"""
modbus/clients/base.py

Energy Monitor V2

Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from modbus.register_block import RegisterBlock


class BaseClient(ABC):
    """
    Base Modbus client interface.

    Drivers never communicate directly with pymodbus.
    They only use this interface.
    """

    @abstractmethod
    def connect(self) -> None:
        """Open communication."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close communication."""

    @abstractmethod
    def connected(self) -> bool:
        """Return connection state."""

    @abstractmethod
    def read_holding_registers(
        self,
        slave: int,
        address: int,
        count: int,
    ) -> RegisterBlock:
        """Read Holding Registers."""

    @abstractmethod
    def read_input_registers(
        self,
        slave: int,
        address: int,
        count: int,
    ) -> RegisterBlock:
        """Read Input Registers."""

    @abstractmethod
    def write_register(
        self,
        slave: int,
        address: int,
        value: int,
    ) -> None:
        """Write single register."""

    @abstractmethod
    def write_registers(
        self,
        slave: int,
        address: int,
        values: list[int],
    ) -> None:
        """Write multiple registers."""