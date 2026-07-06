"""
modbus/drivers/sdm630.py

Energy Monitor V2

Eastron SDM630 Modbus driver.
"""

from __future__ import annotations

from common.enums import ByteOrder, RegisterType
from modbus.clients.base import BaseClient
from modbus.device import Device
from modbus.drivers.base import BaseDriver
from modbus.drivers.factory import DriverFactory


class SDM630Driver(BaseDriver):
    """Driver for Eastron SDM630."""

    NAME = "sdm630"
    REGISTER_TYPE = RegisterType.INPUT
    BYTE_ORDER = ByteOrder.CDAB

    REG_VOLTAGE_L1 = 0
    REG_VOLTAGE_L2 = 2
    REG_VOLTAGE_L3 = 4

    REG_CURRENT_L1 = 6
    REG_CURRENT_L2 = 8
    REG_CURRENT_L3 = 10

    REG_ACTIVE_L1 = 12
    REG_ACTIVE_L2 = 14
    REG_ACTIVE_L3 = 16

    REG_ACTIVE_TOTAL = 52
    REG_REACTIVE_TOTAL = 54
    REG_APPARENT_TOTAL = 56
    REG_POWER_FACTOR = 62
    REG_FREQUENCY = 70
    REG_IMPORT_ACTIVE = 72
    REG_EXPORT_ACTIVE = 74

    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:

        block = self.read_block(
            client=client,
            device=device,
            address=0,
            count=76,
        )

        m = device.measurements

        # Voltage
        m.voltage.l1 = block.float32(self.REG_VOLTAGE_L1, self.BYTE_ORDER)
        m.voltage.l2 = block.float32(self.REG_VOLTAGE_L2, self.BYTE_ORDER)
        m.voltage.l3 = block.float32(self.REG_VOLTAGE_L3, self.BYTE_ORDER)
        m.voltage.average = (
            m.voltage.l1 +
            m.voltage.l2 +
            m.voltage.l3
        ) / 3

        # Current
        m.current.l1 = self.apply_ct(
            block.float32(self.REG_CURRENT_L1, self.BYTE_ORDER),
            device,
        )
        m.current.l2 = self.apply_ct(
            block.float32(self.REG_CURRENT_L2, self.BYTE_ORDER),
            device,
        )
        m.current.l3 = self.apply_ct(
            block.float32(self.REG_CURRENT_L3, self.BYTE_ORDER),
            device,
        )
        m.current.average = (
            m.current.l1 +
            m.current.l2 +
            m.current.l3
        ) / 3

        # Active power
        m.active_power.l1 = self.apply_ct_pt(
            block.float32(self.REG_ACTIVE_L1, self.BYTE_ORDER),
            device,
        )
        m.active_power.l2 = self.apply_ct_pt(
            block.float32(self.REG_ACTIVE_L2, self.BYTE_ORDER),
            device,
        )
        m.active_power.l3 = self.apply_ct_pt(
            block.float32(self.REG_ACTIVE_L3, self.BYTE_ORDER),
            device,
        )
        m.active_power.total = self.apply_ct_pt(
            block.float32(self.REG_ACTIVE_TOTAL, self.BYTE_ORDER),
            device,
        )

        # Reactive/Apparent
        m.reactive_power.total = self.apply_ct_pt(
            block.float32(self.REG_REACTIVE_TOTAL, self.BYTE_ORDER),
            device,
        )
        m.apparent_power.total = self.apply_ct_pt(
            block.float32(self.REG_APPARENT_TOTAL, self.BYTE_ORDER),
            device,
        )

        # Power factor / Frequency
        m.power_factor.total = block.float32(
            self.REG_POWER_FACTOR,
            self.BYTE_ORDER,
        )
        m.frequency = block.float32(
            self.REG_FREQUENCY,
            self.BYTE_ORDER,
        )

        # Energy
        m.energy.import_active = self.apply_ct_pt(
            block.float32(self.REG_IMPORT_ACTIVE, self.BYTE_ORDER),
            device,
        )
        m.energy.export_active = self.apply_ct_pt(
            block.float32(self.REG_EXPORT_ACTIVE, self.BYTE_ORDER),
            device,
        )


DriverFactory.register(SDM630Driver)
