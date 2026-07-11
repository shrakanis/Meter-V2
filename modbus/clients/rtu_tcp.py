"""
modbus/clients/rtu_tcp.py

Energy Monitor V2

Modbus RTU over TCP client.
"""

from __future__ import annotations

import logging
import socket

from modbus.clients.base import BaseClient
from modbus.exceptions import ConnectionError, RegisterError
from modbus.register_block import RegisterBlock
from modbus.rtu_codec import (
    build_read_holding,
    build_read_input,
    build_write_register,
    build_write_registers,
    parse_read_response,
)

logger = logging.getLogger(__name__)


class RTUOverTCPClient(BaseClient):
    """
    Modbus RTU over TCP.

    Uses raw TCP socket and RTU frames.
    """

    def __init__(
        self,
        host: str,
        port: int = 5000,
        timeout: float = 1.0,
    ) -> None:

        self.host = host
        self.port = port
        self.timeout = timeout

        self._socket: socket.socket | None = None

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def connect(self) -> None:

        if self.connected():
            return

        try:

            self._socket = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout,
            )

        except OSError as ex:

            raise ConnectionError(
                f"Cannot connect to {self.host}:{self.port}"
            ) from ex

    def disconnect(self) -> None:

        if self._socket is not None:

            try:
                self._socket.close()
            except Exception:
                pass

        self._socket = None

    def connected(self) -> bool:

        return self._socket is not None

    # ---------------------------------------------------------
    # Receive helpers
    # ---------------------------------------------------------

    def _recv_exact(
        self,
        size: int,
    ) -> bytes:

        data = bytearray()

        while len(data) < size:

            chunk = self._socket.recv(
                size - len(data)
            )

            if not chunk:

                raise ConnectionError(
                    "Connection closed."
                )

            data.extend(chunk)

        return bytes(data)

    def _recv_frame(self) -> bytes:

        #
        # Slave + Function + ByteCount
        #
        header = self._recv_exact(3)

        function = header[1]

        #
        # Exception response
        #
        if function & 0x80:

            tail = self._recv_exact(2 + 2)

            return header + tail

        byte_count = header[2]

        tail = self._recv_exact(
            byte_count + 2
        )

        return header + tail

    # ---------------------------------------------------------
    # Exchange
    # ---------------------------------------------------------

    def _exchange(
        self,
        frame: bytes,
    ) -> bytes:

        self.connect()

        logger.debug(
            "TX -> %s",
            frame.hex(" ").upper(),
        )

        self._socket.sendall(frame)

        response = self._recv_frame()

        logger.debug(
            "RX <- %s",
            response.hex(" ").upper(),
        )

        return response

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    def read_holding_registers(
        self,
        slave: int,
        address: int,
        count: int,
    ) -> RegisterBlock:

        frame = build_read_holding(
            slave=slave,
            address=address,
            count=count,
        )

        return parse_read_response(
            self._exchange(frame)
        )

    def read_input_registers(
        self,
        slave: int,
        address: int,
        count: int,
    ) -> RegisterBlock:

        frame = build_read_input(
            slave=slave,
            address=address,
            count=count,
        )

        return parse_read_response(
            self._exchange(frame)
        )

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------

    def write_register(
        self,
        slave: int,
        address: int,
        value: int,
    ) -> None:

        frame = build_write_register(
            slave=slave,
            address=address,
            value=value,
        )

        self._exchange(frame)

    def write_registers(
        self,
        slave: int,
        address: int,
        values: list[int],
    ) -> None:

        frame = build_write_registers(
            slave=slave,
            address=address,
            values=values,
        )

        self._exchange(frame)