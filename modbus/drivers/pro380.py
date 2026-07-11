"""
modbus/drivers/pro380.py

Energy Monitor V2

Inepro PRO380 Modbus driver.
"""

from __future__ import annotations

from common.enums import ByteOrder, RegisterType
from modbus.clients.base import BaseClient
from modbus.device import Device
from modbus.drivers.base import BaseDriver
from modbus.drivers.factory import DriverFactory
from modbus.register_block import RegisterBlock


class PRO380Driver(BaseDriver):
    """Driver for the Inepro PRO380 three-phase energy meter."""

    NAME = "pro380"
    REGISTER_TYPE = RegisterType.HOLDING
    BYTE_ORDER = ByteOrder.ABCD

    # ------------------------------------------------------------------
    # Register blocks
    # ------------------------------------------------------------------

    INFO_BASE = 0x4000
    INFO_COUNT = 0x20       # 0x4000 .. 0x401F

    VALUES_BASE = 0x5000
    VALUES_COUNT = 0x32     # 0x5000 .. 0x5031

    ENERGY_BASE = 0x6000
    ENERGY_COUNT = 0x4B     # 0x6000 .. 0x604A

    # ------------------------------------------------------------------
    # Static information registers (relative to INFO_BASE)
    # ------------------------------------------------------------------

    REG_SERIAL_NUMBER = 0x4000 - INFO_BASE
    REG_METER_CODE = 0x4002 - INFO_BASE
    REG_MODBUS_ID = 0x4003 - INFO_BASE
    REG_BAUD_RATE = 0x4004 - INFO_BASE
    REG_PROTOCOL_VERSION = 0x4005 - INFO_BASE
    REG_SOFTWARE_VERSION = 0x4007 - INFO_BASE
    REG_HARDWARE_VERSION = 0x4009 - INFO_BASE
    REG_METER_AMPS = 0x400B - INFO_BASE
    REG_CT_RATIO = 0x400C - INFO_BASE
    REG_S0_OUTPUT_RATE = 0x400D - INFO_BASE
    REG_COMBINATION_CODE = 0x400F - INFO_BASE
    REG_LCD_CYCLE_TIME = 0x4010 - INFO_BASE
    REG_PARITY_SETTING = 0x4011 - INFO_BASE
    REG_CURRENT_DIRECTION = 0x4012 - INFO_BASE
    REG_L2_CURRENT_DIRECTION = 0x4013 - INFO_BASE
    REG_L3_CURRENT_DIRECTION = 0x4014 - INFO_BASE
    REG_ERROR_CODE = 0x4015 - INFO_BASE
    REG_POWER_DOWN_COUNTER = 0x4016 - INFO_BASE
    REG_PRESENT_QUADRANT = 0x4017 - INFO_BASE
    REG_L1_QUADRANT = 0x4018 - INFO_BASE
    REG_L2_QUADRANT = 0x4019 - INFO_BASE
    REG_L3_QUADRANT = 0x401A - INFO_BASE
    REG_CHECKSUM = 0x401B - INFO_BASE
    REG_ACTIVE_STATUS_WORD = 0x401D - INFO_BASE
    REG_CT_MODE = 0x401F - INFO_BASE

    # ------------------------------------------------------------------
    # Runtime measurement registers (relative to VALUES_BASE)
    # ------------------------------------------------------------------

    REG_VOLTAGE_AVERAGE = 0x5000 - VALUES_BASE
    REG_VOLTAGE_L1 = 0x5002 - VALUES_BASE
    REG_VOLTAGE_L2 = 0x5004 - VALUES_BASE
    REG_VOLTAGE_L3 = 0x5006 - VALUES_BASE

    REG_FREQUENCY = 0x5008 - VALUES_BASE

    REG_CURRENT_TOTAL = 0x500A - VALUES_BASE
    REG_CURRENT_L1 = 0x500C - VALUES_BASE
    REG_CURRENT_L2 = 0x500E - VALUES_BASE
    REG_CURRENT_L3 = 0x5010 - VALUES_BASE

    REG_ACTIVE_POWER_TOTAL = 0x5012 - VALUES_BASE
    REG_ACTIVE_POWER_L1 = 0x5014 - VALUES_BASE
    REG_ACTIVE_POWER_L2 = 0x5016 - VALUES_BASE
    REG_ACTIVE_POWER_L3 = 0x5018 - VALUES_BASE

    REG_REACTIVE_POWER_TOTAL = 0x501A - VALUES_BASE
    REG_REACTIVE_POWER_L1 = 0x501C - VALUES_BASE
    REG_REACTIVE_POWER_L2 = 0x501E - VALUES_BASE
    REG_REACTIVE_POWER_L3 = 0x5020 - VALUES_BASE

    REG_APPARENT_POWER_TOTAL = 0x5022 - VALUES_BASE
    REG_APPARENT_POWER_L1 = 0x5024 - VALUES_BASE
    REG_APPARENT_POWER_L2 = 0x5026 - VALUES_BASE
    REG_APPARENT_POWER_L3 = 0x5028 - VALUES_BASE

    REG_POWER_FACTOR_TOTAL = 0x502A - VALUES_BASE
    REG_POWER_FACTOR_L1 = 0x502C - VALUES_BASE
    REG_POWER_FACTOR_L2 = 0x502E - VALUES_BASE
    REG_POWER_FACTOR_L3 = 0x5030 - VALUES_BASE

    # ------------------------------------------------------------------
    # Energy registers (relative to ENERGY_BASE)
    # ------------------------------------------------------------------

    REG_TOTAL_ACTIVE_ENERGY = 0x6000 - ENERGY_BASE
    REG_T1_TOTAL_ACTIVE_ENERGY = 0x6002 - ENERGY_BASE
    REG_T2_TOTAL_ACTIVE_ENERGY = 0x6004 - ENERGY_BASE
    REG_L1_TOTAL_ACTIVE_ENERGY = 0x6006 - ENERGY_BASE
    REG_L2_TOTAL_ACTIVE_ENERGY = 0x6008 - ENERGY_BASE
    REG_L3_TOTAL_ACTIVE_ENERGY = 0x600A - ENERGY_BASE

    REG_FORWARD_ACTIVE_ENERGY = 0x600C - ENERGY_BASE
    REG_T1_FORWARD_ACTIVE_ENERGY = 0x600E - ENERGY_BASE
    REG_T2_FORWARD_ACTIVE_ENERGY = 0x6010 - ENERGY_BASE
    REG_L1_FORWARD_ACTIVE_ENERGY = 0x6012 - ENERGY_BASE
    REG_L2_FORWARD_ACTIVE_ENERGY = 0x6014 - ENERGY_BASE
    REG_L3_FORWARD_ACTIVE_ENERGY = 0x6016 - ENERGY_BASE

    REG_REVERSE_ACTIVE_ENERGY = 0x6018 - ENERGY_BASE
    REG_T1_REVERSE_ACTIVE_ENERGY = 0x601A - ENERGY_BASE
    REG_T2_REVERSE_ACTIVE_ENERGY = 0x601C - ENERGY_BASE
    REG_L1_REVERSE_ACTIVE_ENERGY = 0x601E - ENERGY_BASE
    REG_L2_REVERSE_ACTIVE_ENERGY = 0x6020 - ENERGY_BASE
    REG_L3_REVERSE_ACTIVE_ENERGY = 0x6022 - ENERGY_BASE

    REG_TOTAL_REACTIVE_ENERGY = 0x6024 - ENERGY_BASE
    REG_T1_TOTAL_REACTIVE_ENERGY = 0x6026 - ENERGY_BASE
    REG_T2_TOTAL_REACTIVE_ENERGY = 0x6028 - ENERGY_BASE
    REG_L1_TOTAL_REACTIVE_ENERGY = 0x602A - ENERGY_BASE
    REG_L2_TOTAL_REACTIVE_ENERGY = 0x602C - ENERGY_BASE
    REG_L3_TOTAL_REACTIVE_ENERGY = 0x602E - ENERGY_BASE

    REG_FORWARD_REACTIVE_ENERGY = 0x6030 - ENERGY_BASE
    REG_T1_FORWARD_REACTIVE_ENERGY = 0x6032 - ENERGY_BASE
    REG_T2_FORWARD_REACTIVE_ENERGY = 0x6034 - ENERGY_BASE
    REG_L1_FORWARD_REACTIVE_ENERGY = 0x6036 - ENERGY_BASE
    REG_L2_FORWARD_REACTIVE_ENERGY = 0x6038 - ENERGY_BASE
    REG_L3_FORWARD_REACTIVE_ENERGY = 0x603A - ENERGY_BASE

    REG_REVERSE_REACTIVE_ENERGY = 0x603C - ENERGY_BASE
    REG_T1_REVERSE_REACTIVE_ENERGY = 0x603E - ENERGY_BASE
    REG_T2_REVERSE_REACTIVE_ENERGY = 0x6040 - ENERGY_BASE
    REG_L1_REVERSE_REACTIVE_ENERGY = 0x6042 - ENERGY_BASE
    REG_L2_REVERSE_REACTIVE_ENERGY = 0x6044 - ENERGY_BASE
    REG_L3_REVERSE_REACTIVE_ENERGY = 0x6046 - ENERGY_BASE

    REG_TARIFF = 0x6048 - ENERGY_BASE
    REG_RESETTABLE_DAY_COUNTER = 0x6049 - ENERGY_BASE

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _float(self, block: RegisterBlock, register: int) -> float:
        """Decode one PRO380 32-bit ABCD floating-point value."""

        return block.float32(register, self.BYTE_ORDER)

    @staticmethod
    def _ascii_word(block: RegisterBlock, register: int) -> str:
        """Decode a one-register ASCII value."""

        return block.string(register, 1)

    @staticmethod
    def _scaled(value: float, factor: float) -> float:
        """Apply a configured CT/PT factor to a meter value."""

        return value * factor

    # ------------------------------------------------------------------
    # Runtime measurements
    # ------------------------------------------------------------------

    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """Read electrical measurements and accumulated energy values."""

        values = self.read_block(
            client=client,
            device=device,
            address=self.VALUES_BASE,
            count=self.VALUES_COUNT,
        )

        energy = self.read_block(
            client=client,
            device=device,
            address=self.ENERGY_BASE,
            count=self.ENERGY_COUNT,
        )

        m = device.measurements
        ct = device.meter.ct
        pt = device.meter.pt
        ct_pt = ct * pt

        # Voltage (V)
        m.voltage.average = self._scaled(
            self._float(values, self.REG_VOLTAGE_AVERAGE),
            pt,
        )
        m.voltage.l1 = self._scaled(
            self._float(values, self.REG_VOLTAGE_L1),
            pt,
        )
        m.voltage.l2 = self._scaled(
            self._float(values, self.REG_VOLTAGE_L2),
            pt,
        )
        m.voltage.l3 = self._scaled(
            self._float(values, self.REG_VOLTAGE_L3),
            pt,
        )

        # Frequency (Hz)
        m.frequency = self._float(values, self.REG_FREQUENCY)

        # Current (A)
        m.current.total = self._scaled(
            self._float(values, self.REG_CURRENT_TOTAL),
            ct,
        )
        m.current.l1 = self._scaled(
            self._float(values, self.REG_CURRENT_L1),
            ct,
        )
        m.current.l2 = self._scaled(
            self._float(values, self.REG_CURRENT_L2),
            ct,
        )
        m.current.l3 = self._scaled(
            self._float(values, self.REG_CURRENT_L3),
            ct,
        )
        m.current.average = (
            m.current.l1 + m.current.l2 + m.current.l3
        ) / 3.0

        # Active power (kW)
        m.active_power.total = self._scaled(
            self._float(values, self.REG_ACTIVE_POWER_TOTAL),
            ct_pt,
        )
        m.active_power.l1 = self._scaled(
            self._float(values, self.REG_ACTIVE_POWER_L1),
            ct_pt,
        )
        m.active_power.l2 = self._scaled(
            self._float(values, self.REG_ACTIVE_POWER_L2),
            ct_pt,
        )
        m.active_power.l3 = self._scaled(
            self._float(values, self.REG_ACTIVE_POWER_L3),
            ct_pt,
        )

        # Reactive power (kvar)
        m.reactive_power.total = self._scaled(
            self._float(values, self.REG_REACTIVE_POWER_TOTAL),
            ct_pt,
        )
        m.reactive_power.l1 = self._scaled(
            self._float(values, self.REG_REACTIVE_POWER_L1),
            ct_pt,
        )
        m.reactive_power.l2 = self._scaled(
            self._float(values, self.REG_REACTIVE_POWER_L2),
            ct_pt,
        )
        m.reactive_power.l3 = self._scaled(
            self._float(values, self.REG_REACTIVE_POWER_L3),
            ct_pt,
        )

        # Apparent power (kVA)
        m.apparent_power.total = self._scaled(
            self._float(values, self.REG_APPARENT_POWER_TOTAL),
            ct_pt,
        )
        m.apparent_power.l1 = self._scaled(
            self._float(values, self.REG_APPARENT_POWER_L1),
            ct_pt,
        )
        m.apparent_power.l2 = self._scaled(
            self._float(values, self.REG_APPARENT_POWER_L2),
            ct_pt,
        )
        m.apparent_power.l3 = self._scaled(
            self._float(values, self.REG_APPARENT_POWER_L3),
            ct_pt,
        )

        # Power factor
        m.power_factor.total = self._float(
            values,
            self.REG_POWER_FACTOR_TOTAL,
        )
        m.power_factor.l1 = self._float(
            values,
            self.REG_POWER_FACTOR_L1,
        )
        m.power_factor.l2 = self._float(
            values,
            self.REG_POWER_FACTOR_L2,
        )
        m.power_factor.l3 = self._float(
            values,
            self.REG_POWER_FACTOR_L3,
        )

        # Standard energy values (kWh / kvarh)
        m.energy.import_active = self._scaled(
            self._float(energy, self.REG_FORWARD_ACTIVE_ENERGY),
            ct_pt,
        )
        m.energy.export_active = self._scaled(
            self._float(energy, self.REG_REVERSE_ACTIVE_ENERGY),
            ct_pt,
        )
        m.energy.import_reactive = self._scaled(
            self._float(energy, self.REG_FORWARD_REACTIVE_ENERGY),
            ct_pt,
        )
        m.energy.export_reactive = self._scaled(
            self._float(energy, self.REG_REVERSE_REACTIVE_ENERGY),
            ct_pt,
        )

        # Meter-specific energy values
        active_energy_registers = {
            "total_active_energy": self.REG_TOTAL_ACTIVE_ENERGY,
            "t1_total_active_energy": self.REG_T1_TOTAL_ACTIVE_ENERGY,
            "t2_total_active_energy": self.REG_T2_TOTAL_ACTIVE_ENERGY,
            "l1_total_active_energy": self.REG_L1_TOTAL_ACTIVE_ENERGY,
            "l2_total_active_energy": self.REG_L2_TOTAL_ACTIVE_ENERGY,
            "l3_total_active_energy": self.REG_L3_TOTAL_ACTIVE_ENERGY,
            "t1_forward_active_energy": self.REG_T1_FORWARD_ACTIVE_ENERGY,
            "t2_forward_active_energy": self.REG_T2_FORWARD_ACTIVE_ENERGY,
            "l1_forward_active_energy": self.REG_L1_FORWARD_ACTIVE_ENERGY,
            "l2_forward_active_energy": self.REG_L2_FORWARD_ACTIVE_ENERGY,
            "l3_forward_active_energy": self.REG_L3_FORWARD_ACTIVE_ENERGY,
            "t1_reverse_active_energy": self.REG_T1_REVERSE_ACTIVE_ENERGY,
            "t2_reverse_active_energy": self.REG_T2_REVERSE_ACTIVE_ENERGY,
            "l1_reverse_active_energy": self.REG_L1_REVERSE_ACTIVE_ENERGY,
            "l2_reverse_active_energy": self.REG_L2_REVERSE_ACTIVE_ENERGY,
            "l3_reverse_active_energy": self.REG_L3_REVERSE_ACTIVE_ENERGY,
        }

        reactive_energy_registers = {
            "total_reactive_energy": self.REG_TOTAL_REACTIVE_ENERGY,
            "t1_total_reactive_energy": self.REG_T1_TOTAL_REACTIVE_ENERGY,
            "t2_total_reactive_energy": self.REG_T2_TOTAL_REACTIVE_ENERGY,
            "l1_total_reactive_energy": self.REG_L1_TOTAL_REACTIVE_ENERGY,
            "l2_total_reactive_energy": self.REG_L2_TOTAL_REACTIVE_ENERGY,
            "l3_total_reactive_energy": self.REG_L3_TOTAL_REACTIVE_ENERGY,
            "t1_forward_reactive_energy": self.REG_T1_FORWARD_REACTIVE_ENERGY,
            "t2_forward_reactive_energy": self.REG_T2_FORWARD_REACTIVE_ENERGY,
            "l1_forward_reactive_energy": self.REG_L1_FORWARD_REACTIVE_ENERGY,
            "l2_forward_reactive_energy": self.REG_L2_FORWARD_REACTIVE_ENERGY,
            "l3_forward_reactive_energy": self.REG_L3_FORWARD_REACTIVE_ENERGY,
            "t1_reverse_reactive_energy": self.REG_T1_REVERSE_REACTIVE_ENERGY,
            "t2_reverse_reactive_energy": self.REG_T2_REVERSE_REACTIVE_ENERGY,
            "l1_reverse_reactive_energy": self.REG_L1_REVERSE_REACTIVE_ENERGY,
            "l2_reverse_reactive_energy": self.REG_L2_REVERSE_REACTIVE_ENERGY,
            "l3_reverse_reactive_energy": self.REG_L3_REVERSE_REACTIVE_ENERGY,
        }

        for name, register in active_energy_registers.items():
            device.extra[name] = self._scaled(
                self._float(energy, register),
                ct_pt,
            )

        for name, register in reactive_energy_registers.items():
            device.extra[name] = self._scaled(
                self._float(energy, register),
                ct_pt,
            )

        device.extra["tariff"] = energy.int16(self.REG_TARIFF)
        device.extra["resettable_day_counter"] = self._scaled(
            self._float(energy, self.REG_RESETTABLE_DAY_COUNTER),
            ct_pt,
        )

    # ------------------------------------------------------------------
    # Static device information
    # ------------------------------------------------------------------

    def read_info(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """Read PRO380 identification and configuration registers."""

        info = self.read_block(
            client=client,
            device=device,
            address=self.INFO_BASE,
            count=self.INFO_COUNT,
        )

        device.info.update(
            {
                "serial": f"{info.uint32(self.REG_SERIAL_NUMBER):08X}",
                "meter_code": info.uint16(self.REG_METER_CODE),
                "modbus_id": info.int16(self.REG_MODBUS_ID),
                "baudrate": info.int16(self.REG_BAUD_RATE),
                "protocol_version": self._float(
                    info,
                    self.REG_PROTOCOL_VERSION,
                ),
                "software_version": self._float(
                    info,
                    self.REG_SOFTWARE_VERSION,
                ),
                "hardware_version": self._float(
                    info,
                    self.REG_HARDWARE_VERSION,
                ),
                "meter_amps": info.int16(self.REG_METER_AMPS),
                "ct_ratio": info.uint16(self.REG_CT_RATIO),
                "s0_output_rate": self._float(
                    info,
                    self.REG_S0_OUTPUT_RATE,
                ),
                "combination_code": info.int16(
                    self.REG_COMBINATION_CODE
                ),
                "lcd_cycle_time": info.uint16(
                    self.REG_LCD_CYCLE_TIME
                ),
                "parity": info.int16(self.REG_PARITY_SETTING),
                "current_direction": self._ascii_word(
                    info,
                    self.REG_CURRENT_DIRECTION,
                ),
                "l2_current_direction": self._ascii_word(
                    info,
                    self.REG_L2_CURRENT_DIRECTION,
                ),
                "l3_current_direction": self._ascii_word(
                    info,
                    self.REG_L3_CURRENT_DIRECTION,
                ),
                "error_code": info.int16(self.REG_ERROR_CODE),
                "power_down_counter": info.int16(
                    self.REG_POWER_DOWN_COUNTER
                ),
                "present_quadrant": info.int16(
                    self.REG_PRESENT_QUADRANT
                ),
                "l1_quadrant": info.int16(self.REG_L1_QUADRANT),
                "l2_quadrant": info.int16(self.REG_L2_QUADRANT),
                "l3_quadrant": info.int16(self.REG_L3_QUADRANT),
                "checksum": f"{info.uint32(self.REG_CHECKSUM):08X}",
                "active_status_word": (
                    f"{info.uint32(self.REG_ACTIVE_STATUS_WORD):08X}"
                ),
                "ct_mode": info.int16(self.REG_CT_MODE),
            }
        )


DriverFactory.register(PRO380Driver)
