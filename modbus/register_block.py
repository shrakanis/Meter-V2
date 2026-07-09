"""
modbus/register_block.py

Energy Monitor V2

Immutable Modbus register block helper.
"""

from __future__ import annotations

import struct

from common.enums import ByteOrder
from modbus.exceptions import RegisterError


class RegisterBlock:
    """Immutable Modbus register block."""

    def __init__(self, registers: list[int]) -> None:
        self._registers = tuple(registers)

    # ------------------------------------------------------------------
    # Basic
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._registers)

    def __repr__(self) -> str:
        return f"RegisterBlock(size={len(self)})"

    @property
    def registers(self) -> tuple[int, ...]:
        return self._registers

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def contains(self, index: int, words: int = 1) -> bool:
        return (
            index >= 0
            and index + words <= len(self._registers)
        )

    def _check(self, index: int, words: int) -> None:
        if not self.contains(index, words):
            raise RegisterError(
                f"Register index {index} requires {words} word(s)."
            )

    # ------------------------------------------------------------------
    # 16-bit
    # ------------------------------------------------------------------

    def uint16(self, index: int) -> int:
        self._check(index, 1)
        return self._registers[index]

    def int16(self, index: int) -> int:
        value = self.uint16(index)
        return value - 0x10000 if value >= 0x8000 else value

    # aliases
    u16 = uint16
    i16 = int16

    # ------------------------------------------------------------------
    # 32-bit
    # ------------------------------------------------------------------

    def uint32(
        self,
        index: int,
        order: ByteOrder = ByteOrder.ABCD,
    ) -> int:
        return int.from_bytes(
            self._bytes(index, order),
            "big",
            signed=False,
        )

    def int32(
        self,
        index: int,
        order: ByteOrder = ByteOrder.ABCD,
    ) -> int:
        return int.from_bytes(
            self._bytes(index, order),
            "big",
            signed=True,
        )

    # aliases
    u32 = uint32
    i32 = int32

    # ------------------------------------------------------------------
    # Float
    # ------------------------------------------------------------------

    def float32(
        self,
        index: int,
        order: ByteOrder = ByteOrder.ABCD,
    ) -> float:
        return struct.unpack(
            ">f",
            self._bytes(index, order),
        )[0]

    # ------------------------------------------------------------------
    # Bool
    # ------------------------------------------------------------------

    def bool(self, index: int) -> bool:
        return self.uint16(index) != 0

    # ------------------------------------------------------------------
    # String
    # ------------------------------------------------------------------

    def string(
        self,
        index: int,
        words: int,
    ) -> str:
        self._check(index, words)

        data = bytearray()

        for i in range(words):
            reg = self._registers[index + i]
            data.append((reg >> 8) & 0xFF)
            data.append(reg & 0xFF)

        return (
            data.decode("ascii", errors="ignore")
            .rstrip("\x00")
            .strip()
        )

    # ------------------------------------------------------------------
    # Bytes
    # ------------------------------------------------------------------

    def _bytes(
        self,
        index: int,
        order: ByteOrder,
    ) -> bytes:

        self._check(index, 2)

        hi = self._registers[index]
        lo = self._registers[index + 1]

        b = [
            (hi >> 8) & 0xFF,
            hi & 0xFF,
            (lo >> 8) & 0xFF,
            lo & 0xFF,
        ]

        if order == ByteOrder.ABCD:
            pass

        elif order == ByteOrder.BADC:
            b = [b[1], b[0], b[3], b[2]]

        elif order == ByteOrder.CDAB:
            b = [b[2], b[3], b[0], b[1]]

        elif order == ByteOrder.DCBA:
            b = [b[3], b[2], b[1], b[0]]

        else:
            raise RegisterError(
                f"Unsupported ByteOrder: {order}"
            )

        return bytes(b)

    # ------------------------------------------------------------------
    # Slice
    # ------------------------------------------------------------------

    def slice(
        self,
        start: int,
        count: int,
    ) -> "RegisterBlock":

        self._check(start, count)

        return RegisterBlock(
            list(self._registers[start:start + count])
        )
