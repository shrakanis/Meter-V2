"""PRO380 skeleton driver."""

from __future__ import annotations

from common.enums import ByteOrder, RegisterType
from modbus.device import Device
from modbus.drivers.base import BaseDriver
from modbus.drivers.factory import DriverFactory


class PRO380Driver(BaseDriver):
    NAME = "pro380"
    REGISTER_TYPE = RegisterType.HOLDING
    BYTE_ORDER = ByteOrder.ABCD

    BASE = 0x5000

    REG_VOLTAGE_AVG = 0x5000 - BASE
    REG_VOLTAGE_L1 = 0x5002 - BASE
    REG_VOLTAGE_L2 = 0x5004 - BASE
    REG_VOLTAGE_L3 = 0x5006 - BASE

    REG_CURRENT_TOTAL = 0x500A - BASE
    REG_CURRENT_L1 = 0x500C - BASE
    REG_CURRENT_L2 = 0x500E - BASE
    REG_CURRENT_L3 = 0x5010 - BASE

    def read(self, client, device: Device):
        block = self.read_block(client=client, device=device, address=0x5000, count=0x50)
        m = device.measurements
        m.voltage.average = block.float32(self.REG_VOLTAGE_AVG, self.BYTE_ORDER)
        m.voltage.l1 = block.float32(self.REG_VOLTAGE_L1, self.BYTE_ORDER)
        m.voltage.l2 = block.float32(self.REG_VOLTAGE_L2, self.BYTE_ORDER)
        m.voltage.l3 = block.float32(self.REG_VOLTAGE_L3, self.BYTE_ORDER)
        m.current.total = self.apply_ct(block.float32(self.REG_CURRENT_TOTAL, self.BYTE_ORDER), device)
        m.current.l1 = self.apply_ct(block.float32(self.REG_CURRENT_L1, self.BYTE_ORDER), device)
        m.current.l2 = self.apply_ct(block.float32(self.REG_CURRENT_L2, self.BYTE_ORDER), device)
        m.current.l3 = self.apply_ct(block.float32(self.REG_CURRENT_L3, self.BYTE_ORDER), device)

    def read_info(self, client, device: Device):
        return


DriverFactory.register(PRO380Driver)
