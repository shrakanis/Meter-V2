"""
p1/client.py

Energy Monitor V2

P1 serial client.
"""

from __future__ import annotations

import logging
import time

import serial


logger = logging.getLogger(__name__)


class P1Client:
    """
    P1 serial client.

    Responsibilities
    ----------------
    - Open serial port
    - Read complete telegram
    - Return telegram text
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: float = 2.0,
    ) -> None:

        self._port = port

        self._baudrate = baudrate

        self._bytesize = bytesize

        self._parity = parity

        self._stopbits = stopbits

        self._timeout = timeout

        self._serial: serial.Serial | None = None

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    @property
    def connected(self) -> bool:

        return (
            self._serial is not None
            and self._serial.is_open
        )

    def connect(self) -> None:

        if self.connected:
            return

        logger.info(
            "Opening P1 port %s",
            self._port,
        )

        self._serial = serial.Serial(

            port=self._port,

            baudrate=self._baudrate,

            bytesize=self._bytesize,

            parity=self._parity,

            stopbits=self._stopbits,

            timeout=self._timeout,

        )

        self._serial.reset_input_buffer()

    def disconnect(self) -> None:

        if self._serial is None:
            return

        try:

            self._serial.close()

        finally:

            self._serial = None

    # ---------------------------------------------------------
    # Reading
    # ---------------------------------------------------------

    def read(self) -> str:
        """
        Read one complete P1 telegram.
        """

        self.connect()

        assert self._serial is not None

        lines: list[str] = []

        started = False

        deadline = (
            time.monotonic()
            + self._timeout
        )

        while time.monotonic() < deadline:

            raw = self._serial.readline()

            if not raw:
                continue

            try:

                line = raw.decode(
                    "ascii",
                    errors="ignore",
                ).strip()

            except Exception:

                continue

            if not line:
                continue

            #
            # Telegram starts with /
            #

            if line.startswith("/"):

                started = True

                lines = [line]

                continue

            if not started:
                continue

            lines.append(line)

            #
            # Telegram ends with !
            #

            if line.startswith("!"):

                return "\n".join(lines)

        raise TimeoutError(
            "P1 telegram timeout."
        )

    # ---------------------------------------------------------
    # Context manager
    # ---------------------------------------------------------

    def __enter__(self):

        self.connect()

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        self.disconnect()