"""
modbus/clients/rtu.py

Energy Monitor V2
"""

from pymodbus.client import ModbusSerialClient

from modbus.clients.base_client import BaseModbusClient


class RTUClient(BaseModbusClient):

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: float = 1.0,
    ) -> None:

        super().__init__()

        self.port = port

        self._client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
        )