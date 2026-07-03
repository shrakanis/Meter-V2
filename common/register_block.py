"""
modbus/register_block.py

Energy Monitor V2

Version: 1.0.0
"""

from __future__ import annotations

import struct

from common.enums import ByteOrder
from modbus.exceptions import RegisterError


class RegisterBlock:
    """Immutable Modbus register block."""

    def __init__(self, registers: list[int]):

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
    # Internal
    # ------------------------------------------------------------------

    def _check(self, index: int, words: int) -> None:

        if index < 0:
            raise RegisterError(
                f"Negative register index: {index}"
            )

        if index + words > len(self._registers):
            raise RegisterError(
                f"Register index {index} requires "
                f"{words} registers, "
                f"only {len(self._registers)-index} available."
            )

    # ------------------------------------------------------------------
    # 16 bit
    # ------------------------------------------------------------------

    def u16(self, index: int) -> int:

        self._check(index, 1)

        return self._registers[index]

    def i16(self, index: int) -> int:

        value = self.u16(index)

        if value >= 0x8000:
            value -= 0x10000

        return value

    # ------------------------------------------------------------------
    # 32 bit
    # ------------------------------------------------------------------

    def u32(
        self,
        index: int,
        order: ByteOrder = ByteOrder.ABCD,
    ) -> int:

        self._check(index, 2)

        raw = self._bytes(index, order)

        return int.from_bytes(
            raw,
            byteorder="big",
            signed=False,
        )

    def i32(
        self,
        index: int,
        order: ByteOrder = ByteOrder.ABCD,
    ) -> int:

        self._check(index, 2)

        raw = self._bytes(index, order)

        return int.from_bytes(
            raw,
            byteorder="big",
            signed=True,
        )

    # ------------------------------------------------------------------
    # Float
    # ------------------------------------------------------------------

    def float32(
        self,
        index: int,
        order: ByteOrder = ByteOrder.ABCD,
    ) -> float:

        self._check(index, 2)

        raw = self._bytes(index, order)

        return struct.unpack(">f", raw)[0]

    # ------------------------------------------------------------------
    # Raw bytes
    # ------------------------------------------------------------------

    def _bytes(
        self,
        index: int,
        order: ByteOrder,
    ) -> bytes:

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
    # Utilities
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