"""
modbus/register_block.py

Energy Monitor V2

Version: 1.0.0
"""

from __future__ import annotations

import struct


class RegisterBlock:
    """Wrapper around Modbus register list."""

    def __init__(self, registers: list[int]):

        self._registers = registers

    # ------------------------------------------------------------------
    # Basic
    # ------------------------------------------------------------------

    def __len__(self) -> int:

        return len(self._registers)

    def raw(self) -> list[int]:

        return self._registers

    def u16(self, index: int) -> int:

        return self._registers[index]

    def i16(self, index: int) -> int:

        value = self.u16(index)

        if value >= 0x8000:
            value -= 0x10000

        return value

    # ------------------------------------------------------------------
    # 32-bit
    # ------------------------------------------------------------------

    def u32(self, index: int) -> int:

        return (
            (self._registers[index] << 16)
            | self._registers[index + 1]
        )

    def i32(self, index: int) -> int:

        value = self.u32(index)

        if value >= 0x80000000:
            value -= 0x100000000

        return value

    # ------------------------------------------------------------------
    # Float (ABCD)
    # ------------------------------------------------------------------

    def float(self, index: int) -> float:

        data = struct.pack(
            ">HH",
            self._registers[index],
            self._registers[index + 1],
        )

        return struct.unpack(">f", data)[0]

    # ------------------------------------------------------------------
    # Float (CDAB)
    # ------------------------------------------------------------------

    def float_swapped(self, index: int) -> float:

        data = struct.pack(
            ">HH",
            self._registers[index + 1],
            self._registers[index],
        )

        return struct.unpack(">f", data)[0]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def slice(
        self,
        start: int,
        count: int,
    ) -> "RegisterBlock":

        return RegisterBlock(
            self._registers[start:start + count]
        )

    def __repr__(self) -> str:

        return f"RegisterBlock(registers={len(self._registers)})"