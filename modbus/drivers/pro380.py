"""
modbus/drivers/pro380.py

Energy Monitor V2

PRO380 Modbus driver.
"""

from __future__ import annotations

from common.enums import ByteOrder, RegisterType
from modbus.device import Device
from modbus.drivers.base import BaseDriver
from modbus.drivers.factory import DriverFactory


class PRO380Driver(BaseDriver):
    """
    Inepro PRO380 Modbus driver.

    Manual:
        Registers 5000-5031  -> realtime values
        Registers 6000-6049  -> energy values
    """

    NAME = "pro380"

    REGISTER_TYPE = RegisterType.HOLDING

    BYTE_ORDER = ByteOrder.ABCD

    # ----------------------------------------------------------
    # Base addresses
    # ----------------------------------------------------------

    BASE = 0x5000
    ENERGY_BASE = 0x6000

    # ----------------------------------------------------------
    # Voltage
    # ----------------------------------------------------------

    REG_VOLTAGE_AVG = 0x5000 - BASE
    REG_VOLTAGE_L1 = 0x5002 - BASE
    REG_VOLTAGE_L2 = 0x5004 - BASE
    REG_VOLTAGE_L3 = 0x5006 - BASE

    # ----------------------------------------------------------
    # Frequency
    # ----------------------------------------------------------

    REG_FREQUENCY = 0x5008 - BASE

    # ----------------------------------------------------------
    # Current
    # ----------------------------------------------------------

    REG_CURRENT_TOTAL = 0x500A - BASE
    REG_CURRENT_L1 = 0x500C - BASE
    REG_CURRENT_L2 = 0x500E - BASE
    REG_CURRENT_L3 = 0x5010 - BASE

    # ----------------------------------------------------------
    # Active Power
    # ----------------------------------------------------------

    REG_ACTIVE_TOTAL = 0x5012 - BASE
    REG_ACTIVE_L1 = 0x5014 - BASE
    REG_ACTIVE_L2 = 0x5016 - BASE
    REG_ACTIVE_L3 = 0x5018 - BASE

    # ----------------------------------------------------------
    # Reactive Power
    # ----------------------------------------------------------

    REG_REACTIVE_TOTAL = 0x501A - BASE
    REG_REACTIVE_L1 = 0x501C - BASE
    REG_REACTIVE_L2 = 0x501E - BASE
    REG_REACTIVE_L3 = 0x5020 - BASE

    # ----------------------------------------------------------
    # Apparant Power
    # ----------------------------------------------------------

    REG_APPARENT_TOTAL = 0x5022 - BASE
    REG_APPARENT_L1 = 0x5024 - BASE
    REG_APPARENT_L2 = 0x5026 - BASE
    REG_APPARENT_L3 = 0x5028 - BASE

    # ----------------------------------------------------------
    # Power Factor
    # ----------------------------------------------------------

    REG_PF_TOTAL = 0x502A - BASE
    REG_PF_L1 = 0x502C - BASE
    REG_PF_L2 = 0x502E - BASE
    REG_PF_L3 = 0x5030 - BASE

    # ----------------------------------------------------------
    # Energy
    # ----------------------------------------------------------

    REG_TOTAL_ACTIVE = 0x6000 - ENERGY_BASE

    REG_FORWARD_ACTIVE = 0x600C - ENERGY_BASE

    REG_REVERSE_ACTIVE = 0x6018 - ENERGY_BASE

    REG_TOTAL_REACTIVE = 0x6024 - ENERGY_BASE

    REG_FORWARD_REACTIVE = 0x6030 - ENERGY_BASE

    REG_REVERSE_REACTIVE = 0x603C - ENERGY_BASE

    # ----------------------------------------------------------
    # Runtime values
    # ----------------------------------------------------------

    def read(
        self,
        client,
        device: Device,
    ) -> None:

        m = device.measurements

        #########################################################
        # Electrical values
        #########################################################

        block = self.read_block(
            client=client,
            device=device,
            address=self.BASE,
            count=0x32,
        )

        #
        # Voltage
        #

        m.voltage.average = self.apply_pt(
            block.float32(
                self.REG_VOLTAGE_AVG,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.voltage.l1 = self.apply_pt(
            block.float32(
                self.REG_VOLTAGE_L1,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.voltage.l2 = self.apply_pt(
            block.float32(
                self.REG_VOLTAGE_L2,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.voltage.l3 = self.apply_pt(
            block.float32(
                self.REG_VOLTAGE_L3,
                self.BYTE_ORDER,
            ),
            device,
        )

        #
        # Frequency
        #

        m.frequency = block.float32(
            self.REG_FREQUENCY,
            self.BYTE_ORDER,
        )

        #
        # Current
        #

        m.current.total = self.apply_ct(
            block.float32(
                self.REG_CURRENT_TOTAL,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.current.l1 = self.apply_ct(
            block.float32(
                self.REG_CURRENT_L1,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.current.l2 = self.apply_ct(
            block.float32(
                self.REG_CURRENT_L2,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.current.l3 = self.apply_ct(
            block.float32(
                self.REG_CURRENT_L3,
                self.BYTE_ORDER,
            ),
            device,
        )
        #
        # Active power
        #

        m.active_power.total = self.apply_ct_pt(
            block.float32(
                self.REG_ACTIVE_TOTAL,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.active_power.l1 = self.apply_ct_pt(
            block.float32(
                self.REG_ACTIVE_L1,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.active_power.l2 = self.apply_ct_pt(
            block.float32(
                self.REG_ACTIVE_L2,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.active_power.l3 = self.apply_ct_pt(
            block.float32(
                self.REG_ACTIVE_L3,
                self.BYTE_ORDER,
            ),
            device,
        )

        #
        # Reactive power
        #

        m.reactive_power.total = self.apply_ct_pt(
            block.float32(
                self.REG_REACTIVE_TOTAL,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.reactive_power.l1 = self.apply_ct_pt(
            block.float32(
                self.REG_REACTIVE_L1,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.reactive_power.l2 = self.apply_ct_pt(
            block.float32(
                self.REG_REACTIVE_L2,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.reactive_power.l3 = self.apply_ct_pt(
            block.float32(
                self.REG_REACTIVE_L3,
                self.BYTE_ORDER,
            ),
            device,
        )

        #
        # Apparant power
        #

        m.apparent_power.total = self.apply_ct_pt(
            block.float32(
                self.REG_APPARENT_TOTAL,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.apparent_power.l1 = self.apply_ct_pt(
            block.float32(
                self.REG_APPARENT_L1,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.apparent_power.l2 = self.apply_ct_pt(
            block.float32(
                self.REG_APPARENT_L2,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.apparent_power.l3 = self.apply_ct_pt(
            block.float32(
                self.REG_APPARENT_L3,
                self.BYTE_ORDER,
            ),
            device,
        )

        #
        # Power factor
        #

        m.power_factor.total = block.float32(
            self.REG_PF_TOTAL,
            self.BYTE_ORDER,
        )

        m.power_factor.l1 = block.float32(
            self.REG_PF_L1,
            self.BYTE_ORDER,
        )

        m.power_factor.l2 = block.float32(
            self.REG_PF_L2,
            self.BYTE_ORDER,
        )

        m.power_factor.l3 = block.float32(
            self.REG_PF_L3,
            self.BYTE_ORDER,
        )

        #########################################################
        # Energy values
        #########################################################

        energy = self.read_block(
            client=client,
            device=device,
            address=self.ENERGY_BASE,
            count=0x4B,
        )

        #
        # Active energy
        #

        m.energy.import_active = energy.float32(
            self.REG_FORWARD_ACTIVE,
            self.BYTE_ORDER,
        )

        m.energy.export_active = energy.float32(
            self.REG_REVERSE_ACTIVE,
            self.BYTE_ORDER,
        )

        #
        # Reactive energy
        #

        m.energy.import_reactive = energy.float32(
            self.REG_FORWARD_REACTIVE,
            self.BYTE_ORDER,
        )

        m.energy.export_reactive = energy.float32(
            self.REG_REVERSE_REACTIVE,
            self.BYTE_ORDER,
        )

        #
        # Extra values
        #

        device.extra["total_active_energy"] = energy.float32(
            self.REG_TOTAL_ACTIVE,
            self.BYTE_ORDER,
        )

        device.extra["total_reactive_energy"] = energy.float32(
            self.REG_TOTAL_REACTIVE,
            self.BYTE_ORDER,
        )

    # ----------------------------------------------------------
    # Static information
    # ----------------------------------------------------------

    def read_info(
        self,
        client,
        device: Device,
    ) -> None:

        info = self.read_block(
            client=client,
            device=device,
            address=0x4000,
            count=0x20,
        )

        device.info["serial"] = f"{info.uint32(0):08X}"
        device.info["meter_code"] = info.uint16(2)
        device.info["modbus_id"] = info.int16(3)
        device.info["baudrate"] = info.int16(4)
        device.info["protocol_version"] = info.float32(5)
        device.info["software_version"] = info.float32(7)
        device.info["hardware_version"] = info.float32(9)
        device.info["meter_amps"] = info.int16(11)
        device.info["ct_ratio"] = info.uint16(12)
        device.info["parity"] = info.int16(17)
        device.info["ct_mode"] = info.int16(31)


DriverFactory.register(PRO380Driver)
