"""
modbus/crc.py

Energy Monitor V2

Modbus RTU CRC16.
"""

from __future__ import annotations


def crc16(data: bytes) -> int:
    """
    Calculate Modbus CRC16.

    Returns
    -------
    CRC value as integer.
    """

    crc = 0xFFFF

    for byte in data:

        crc ^= byte

        for _ in range(8):

            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1

    return crc & 0xFFFF


def append_crc(data: bytes) -> bytes:
    """
    Append Modbus CRC to frame.

    CRC is appended Low byte first.
    """

    crc = crc16(data)

    return data + bytes(
        (
            crc & 0xFF,
            (crc >> 8) & 0xFF,
        )
    )


def verify_crc(frame: bytes) -> bool:
    """
    Verify Modbus CRC.
    """

    if len(frame) < 4:
        return False

    received = (
        frame[-2]
        | (frame[-1] << 8)
    )

    calculated = crc16(frame[:-2])

    return received == calculated