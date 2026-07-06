
"""
modbus/clients/tcp.py

Energy Monitor V2

Modbus TCP client.
"""

from __future__ import annotations

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from modbus.clients.base import BaseClient
from modbus.exceptions import ConnectionError, RegisterError
from modbus.register_block import RegisterBlock


class TCPClient(BaseClient):
    """Modbus TCP client wrapper."""

    def __init__(
        self,
        host: str,
        port: int = 502,
        timeout: float = 1.0,
    ) -> None:

        self.host = host
        self.port = port

        self._client = ModbusTcpClient(
            host=host,
            port=port,
            timeout=timeout,
        )

    def connect(self) -> None:
        if self.connected():
            return
        if not self._client.connect():
            raise ConnectionError(f"Cannot connect to {self.host}:{self.port}")

    def disconnect(self) -> None:
        self._client.close()

    def connected(self) -> bool:
        return bool(self._client.connected)

    def _ensure_connected(self) -> None:
        if not self.connected():
            self.connect()

    def read_holding_registers(self, slave: int, address: int, count: int) -> RegisterBlock:
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

    def read_input_registers(self, slave: int, address: int, count: int) -> RegisterBlock:
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

    def write_register(self, slave: int, address: int, value: int) -> None:
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

    def write_registers(self, slave: int, address: int, values: list[int]) -> None:
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
