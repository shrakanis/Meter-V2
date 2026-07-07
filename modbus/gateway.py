"""
modbus/gateway.py

Gateway connection for custom Modbus TCP (CRC based).
"""

from __future__ import annotations

import socket
import struct

from modbus_crc import add_crc
import coding


class Gateway:

    def __init__(self, ip: str, port: int = 70, timeout: float = 2.0):

        self.ip = ip
        self.port = port
        self.timeout = timeout

    # ---------------------------------------------------------

    def _request(self, slave: int, register: int) -> bytes:

        register_bytes = struct.pack("<H", register)

        packet = struct.pack(
            "6B",
            slave,
            0x03,
            register_bytes[1],
            register_bytes[0],
            0x00,
            0x02,
        )

        packet = add_crc(packet)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:

            sock.connect((self.ip, self.port))

            sock.send(packet)

            data = sock.recv(64)

            if len(data) != 9:
                raise RuntimeError(
                    f"Invalid packet ({len(data)} bytes)"
                )

            if data[0] != slave:
                raise RuntimeError(
                    "Wrong slave returned"
                )

            if data[1] != 0x03:
                raise RuntimeError(
                    "Wrong function code"
                )

            return data

        finally:

            sock.close()

    # ---------------------------------------------------------

    def read_float_abcd(
        self,
        slave: int,
        register: int,
        transform: float = 1.0,
    ) -> float:

        data = self._request(slave, register)

        high = (data[3] << 8) | data[4]
        low = (data[5] << 8) | data[6]

        value = coding.abcd(high, low)

        return round(value * transform, 2)