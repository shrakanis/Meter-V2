"""
modbus/clients/tcp.py

Energy Monitor V2
"""

from pymodbus.client import ModbusTcpClient

from modbus.clients.base_client import BaseModbusClient


class TCPClient(BaseModbusClient):

    def __init__(
        self,
        host: str,
        port: int = 502,
        timeout: float = 1.0,
    ) -> None:

        super().__init__()

        self.host = host
        self.port = port

        self._client = ModbusTcpClient(
            host=host,
            port=port,
            timeout=timeout,
        )