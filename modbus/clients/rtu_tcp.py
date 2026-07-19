"""
modbus/clients/rtu_tcp.py

Energy Monitor V2

Modbus RTU over TCP client.
"""

from __future__ import annotations

import logging
import socket
import threading
import time

from modbus.clients.base import BaseClient
from modbus.exceptions import (
    ConnectionError,
    RegisterError,
    TimeoutError,
)
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
    Modbus RTU over TCP client.

    Uses a raw TCP socket and sends Modbus RTU frames unchanged.
    Automatically disconnects a broken socket so that the next
    polling attempt creates a new connection.
    """

    def __init__(
        self,
        host: str,
        port: int = 5000,
        timeout: float = 1.0,
        retries: int = 2,
        retry_delay: float = 0.15,
    ) -> None:

        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = max(0, int(retries))
        self.retry_delay = max(0.0, float(retry_delay))

        self._socket: socket.socket | None = None
        self._lock = threading.RLock()

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def connect(self) -> None:
        """
        Open TCP connection if it is not already connected.
        """

        with self._lock:

            if self._socket is not None:
                return

            try:

                sock = socket.create_connection(
                    (self.host, self.port),
                    timeout=self.timeout,
                )

                sock.settimeout(self.timeout)

                self._socket = sock

                logger.info(
                    "Connected to RTU over TCP gateway %s:%s",
                    self.host,
                    self.port,
                )

            except socket.timeout as ex:

                self._socket = None

                raise TimeoutError(
                    f"Connection timeout to "
                    f"{self.host}:{self.port}"
                ) from ex

            except OSError as ex:

                self._socket = None

                raise ConnectionError(
                    f"Cannot connect to "
                    f"{self.host}:{self.port}"
                ) from ex

    def disconnect(self) -> None:
        """
        Close TCP connection.
        """

        with self._lock:

            sock = self._socket
            self._socket = None

            if sock is None:
                return

            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            try:
                sock.close()
            except OSError:
                pass

            logger.debug(
                "Disconnected RTU over TCP gateway %s:%s",
                self.host,
                self.port,
            )

    def connected(self) -> bool:
        """
        Return whether a socket object currently exists.

        A TCP connection cannot be reliably checked without performing
        I/O. Broken sockets are cleared automatically inside _exchange().
        """

        with self._lock:
            return self._socket is not None

    # ---------------------------------------------------------
    # Receive helpers
    # ---------------------------------------------------------

    def _recv_exact(
        self,
        size: int,
    ) -> bytes:
        """
        Receive exactly the requested number of bytes.
        """

        if size <= 0:
            return b""

        data = bytearray()

        while len(data) < size:

            sock = self._socket

            if sock is None:
                raise ConnectionError(
                    "TCP socket is not connected."
                )

            try:

                chunk = sock.recv(
                    size - len(data)
                )

            except socket.timeout as ex:

                raise TimeoutError(
                    f"Response timeout from "
                    f"{self.host}:{self.port}"
                ) from ex

            except OSError as ex:

                raise ConnectionError(
                    f"Receive failed from "
                    f"{self.host}:{self.port}: {ex}"
                ) from ex

            if not chunk:

                raise ConnectionError(
                    f"Connection closed by "
                    f"{self.host}:{self.port}"
                )

            data.extend(chunk)

        return bytes(data)

    def _recv_frame(self) -> bytes:
        """
        Receive one Modbus RTU response frame.
        """

        # Slave + function + byte count or exception code
        header = self._recv_exact(3)

        function = header[1]

        # Modbus exception response:
        # slave + function|0x80 + exception code + CRC16
        if function & 0x80:

            crc = self._recv_exact(2)

            return header + crc

        byte_count = header[2]

        payload_and_crc = self._recv_exact(
            byte_count + 2
        )

        return header + payload_and_crc

    # ---------------------------------------------------------
    # Exchange
    # ---------------------------------------------------------

    def _exchange(
        self,
        frame: bytes,
    ) -> bytes:
        """
        Send one RTU frame and receive one response.

        Any socket or timeout error closes the current connection.
        The next polling cycle will then create a new socket.
        """

        with self._lock:

            try:

                self.connect()

                sock = self._socket

                if sock is None:
                    raise ConnectionError(
                        "TCP socket is not connected."
                    )

                logger.debug(
                    "TX %s:%s -> %s",
                    self.host,
                    self.port,
                    frame.hex(" ").upper(),
                )

                sock.sendall(frame)

                response = self._recv_frame()

                logger.debug(
                    "RX %s:%s <- %s",
                    self.host,
                    self.port,
                    response.hex(" ").upper(),
                )

                return response

            except (ConnectionError, TimeoutError):

                self.disconnect()
                raise

            except socket.timeout as ex:

                self.disconnect()

                raise TimeoutError(
                    f"Communication timeout with "
                    f"{self.host}:{self.port}"
                ) from ex

            except OSError as ex:

                self.disconnect()

                raise ConnectionError(
                    f"Communication error with "
                    f"{self.host}:{self.port}: {ex}"
                ) from ex

            except Exception:

                self.disconnect()
                raise

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    def _read_with_retry(
        self,
        *,
        frame: bytes,
        slave: int,
        function: int,
    ) -> RegisterBlock:
        """
        Execute one RTU read and recover from a corrupt/stale frame.

        A CRC or frame validation error means the TCP stream may no
        longer be aligned to the beginning of an RTU frame. Keeping
        that socket open can make every following request fail. The
        connection is therefore closed and recreated before retrying.
        """

        attempts = self.retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):

            try:

                response = self._exchange(frame)

                return parse_read_response(
                    response,
                    expected_slave=slave,
                    expected_function=function,
                )

            except RegisterError as ex:

                last_error = ex

                logger.warning(
                    "Invalid RTU frame from %s:%s "
                    "(attempt %s/%s): %s",
                    self.host,
                    self.port,
                    attempt,
                    attempts,
                    ex,
                )

                # A bad CRC, wrong slave/function or malformed length
                # can leave unread/stale bytes in the TCP stream.
                # Reusing the same socket would keep the stream out of
                # sync, so force a clean TCP connection.
                self.disconnect()

            except (ConnectionError, TimeoutError) as ex:

                last_error = ex

                # _exchange() already disconnects, but calling it here
                # is harmless and guarantees a clean retry state.
                self.disconnect()

            if attempt < attempts and self.retry_delay > 0:

                time.sleep(
                    self.retry_delay
                )

        if last_error is not None:
            raise last_error

        raise RegisterError(
            "RTU over TCP read failed."
        )

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

        return self._read_with_retry(
            frame=frame,
            slave=slave,
            function=0x03,
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

        return self._read_with_retry(
            frame=frame,
            slave=slave,
            function=0x04,
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