"""
modbus/rtu_codec.py

Energy Monitor V2

Modbus RTU frame builder/parser.
"""

from __future__ import annotations

import struct

from modbus.crc import append_crc, verify_crc
from modbus.exceptions import RegisterError
from modbus.register_block import RegisterBlock


# ----------------------------------------------------------------------
# Read Holding Registers (03)
# ----------------------------------------------------------------------


def build_read_holding(
    slave: int,
    address: int,
    count: int,
) -> bytes:
    """
    Build Read Holding Registers request.
    """

    frame = struct.pack(
        ">BBHH",
        slave,
        0x03,
        address,
        count,
    )

    return append_crc(frame)


# ----------------------------------------------------------------------
# Read Input Registers (04)
# ----------------------------------------------------------------------


def build_read_input(
    slave: int,
    address: int,
    count: int,
) -> bytes:
    """
    Build Read Input Registers request.
    """

    frame = struct.pack(
        ">BBHH",
        slave,
        0x04,
        address,
        count,
    )

    return append_crc(frame)


# ----------------------------------------------------------------------
# Write Single Register (06)
# ----------------------------------------------------------------------


def build_write_register(
    slave: int,
    address: int,
    value: int,
) -> bytes:
    """
    Build Write Single Register request.
    """

    frame = struct.pack(
        ">BBHH",
        slave,
        0x06,
        address,
        value,
    )

    return append_crc(frame)


# ----------------------------------------------------------------------
# Write Multiple Registers (10)
# ----------------------------------------------------------------------


def build_write_registers(
    slave: int,
    address: int,
    values: list[int],
) -> bytes:
    """
    Build Write Multiple Registers request.
    """

    count = len(values)

    payload = b"".join(
        struct.pack(">H", value)
        for value in values
    )

    frame = (
        struct.pack(
            ">BBHHB",
            slave,
            0x10,
            address,
            count,
            count * 2,
        )
        + payload
    )

    return append_crc(frame)


# ----------------------------------------------------------------------
# Response parser
# ----------------------------------------------------------------------


def parse_read_response(
    frame: bytes,
    *,
    expected_slave: int | None = None,
    expected_function: int | None = None,
) -> RegisterBlock:
    """
    Parse Read Holding/Input response.
    """

    if not verify_crc(frame):
        raise RegisterError("CRC error.")

    if len(frame) < 5:
        raise RegisterError("Invalid response.")

    slave = frame[0]
    function = frame[1]

    if (
        expected_slave is not None
        and slave != expected_slave
    ):
        raise RegisterError(
            f"Unexpected slave {slave}; "
            f"expected {expected_slave}."
        )

    if (
        expected_function is not None
        and function not in (
            expected_function,
            expected_function | 0x80,
        )
    ):
        raise RegisterError(
            f"Unexpected function 0x{function:02X}; "
            f"expected 0x{expected_function:02X}."
        )

    if function & 0x80:

        code = frame[2]

        raise RegisterError(
            f"Modbus exception {code}"
        )

    byte_count = frame[2]

    if len(frame) != byte_count + 5:
        raise RegisterError(
            "Invalid response length."
        )

    registers: list[int] = []

    offset = 3

    while offset < 3 + byte_count:

        registers.append(
            int.from_bytes(
                frame[offset:offset + 2],
                "big",
            )
        )

        offset += 2

    return RegisterBlock(registers)