"""
modbus/clients/rtu.py

Energy Monitor V2

Modbus RTU client.
"""

from __future__ import annotations

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

from modbus.clients.base import BaseClient
from modbus.exceptions import (
    ConnectionError,
    RegisterError,
)
from modbus.register_block import RegisterBlock


class RTUClient(BaseClient):

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: float = 1.0,
    ) -> None:

        self.port = port

        self._client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
        )

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def connect(self) -> None:

        if self.connected():
            return

        if not self._client.connect():
            raise ConnectionError(
                f"Cannot open serial port '{self.port}'"
            )

    def disconnect(self) -> None:

        self._client.close()

    def connected(self) -> bool:

        return bool(self._client.connected)

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _ensure_connected(self) -> None:

        if not self.connected():
            self.connect()

    # ---------------------------------------------------------
    # Read Holding Registers
    # ---------------------------------------------------------

    def read_holding_registers(
        self,
        slave: int,
        address: int,
        count: int,
    ) -> RegisterBlock:

        self._ensure_connected()

        try:

            result = self._client.read_holding_registers(
                address=address,
                count=count,
                device_id=slave,
            )

        except ModbusException as ex:

            raise ConnectionError(str(ex)) from ex

        if result.isError():
            raise RegisterError(str(result))

        return RegisterBlock(result.registers)

    # ---------------------------------------------------------
    # Read Input Registers
    # ---------------------------------------------------------

    def read_input_registers(
        self,
        slave: int,
        address: int,
        count: int,
    ) -> RegisterBlock:

        self._ensure_connected()

        try:

            result = self._client.read_input_registers(
                address=address,
                count=count,
                device_id=slave,
            )

        except ModbusException as ex:

            raise ConnectionError(str(ex)) from ex

        if result.isError():
            raise RegisterError(str(result))

        return RegisterBlock(result.registers)

    # ---------------------------------------------------------
    # Write Register
    # ---------------------------------------------------------

    def write_register(
        self,
        slave: int,
        address: int,
        value: int,
    ) -> None:

        self._ensure_connected()

        try:

            result = self._client.write_register(
                address=address,
                value=value,
                device_id=slave,
            )

        except ModbusException as ex:

            raise ConnectionError(str(ex)) from ex

        if result.isError():
            raise RegisterError(str(result))

    # ---------------------------------------------------------
    # Write Registers
    # ---------------------------------------------------------

    def write_registers(
        self,
        slave: int,
        address: int,
        values: list[int],
    ) -> None:

        self._ensure_connected()

        try:

            result = self._client.write_registers(
                address=address,
                values=values,
                device_id=slave,
            )

        except ModbusException as ex:

            raise ConnectionError(str(ex)) from ex

        if result.isError():
            raise RegisterError(str(result))