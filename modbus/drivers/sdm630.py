"""
modbus/drivers/sdm630.py

Energy Monitor V2

Eastron SDM630 Modbus driver.
"""

from __future__ import annotations

from common.enums import ByteOrder

from modbus.clients.base import BaseClient
from modbus.device import Device
from modbus.drivers.base import BaseDriver
from modbus.drivers.factory import DriverFactory


class SDM630Driver(BaseDriver):
    """
    Driver for Eastron SDM630.
    """

    NAME = "sdm630"

    BYTE_ORDER = ByteOrder.CDAB

    # ---------------------------------------------------------
    # Registers
    # ---------------------------------------------------------

    REG_VOLTAGE_L1 = 0
    REG_VOLTAGE_L2 = 2
    REG_VOLTAGE_L3 = 4

    REG_CURRENT_L1 = 6
    REG_CURRENT_L2 = 8
    REG_CURRENT_L3 = 10

    REG_POWER_L1 = 12
    REG_POWER_L2 = 14
    REG_POWER_L3 = 16

    REG_ACTIVE_POWER = 52

    REG_POWER_FACTOR = 62

    REG_FREQUENCY = 70

    REG_IMPORT_ACTIVE_ENERGY = 72

    REG_EXPORT_ACTIVE_ENERGY = 74

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """
        Read SDM630 measurements.
        """

        block = client.read_input_registers(
            slave=device.slave,
            address=0,
            count=76,
        )

        m = device.measurements

        # -----------------------------------------------------
        # Voltage
        # -----------------------------------------------------

        m.voltage.l1 = block.float32(
            self.REG_VOLTAGE_L1,
            self.BYTE_ORDER,
        )

        m.voltage.l2 = block.float32(
            self.REG_VOLTAGE_L2,
            self.BYTE_ORDER,
        )

        m.voltage.l3 = block.float32(
            self.REG_VOLTAGE_L3,
            self.BYTE_ORDER,
        )

        m.voltage.average = (
            m.voltage.l1 +
            m.voltage.l2 +
            m.voltage.l3
        ) / 3

        # -----------------------------------------------------
        # Current
        # -----------------------------------------------------

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

        m.current.average = (
            m.current.l1 +
            m.current.l2 +
            m.current.l3
        ) / 3

        # -----------------------------------------------------
        # Active Power
        # -----------------------------------------------------

        m.power.active = self.apply_ct_pt(
            block.float32(
                self.REG_ACTIVE_POWER,
                self.BYTE_ORDER,
            ),
            device,
        )

        # -----------------------------------------------------
        # Reactive Power
        # -----------------------------------------------------

        m.power.reactive = self.apply_ct_pt(
            block.float32(
                54,
                self.BYTE_ORDER,
            ),
            device,
        )

        # -----------------------------------------------------
        # Apparent Power
        # -----------------------------------------------------

        m.power.apparent = self.apply_ct_pt(
            block.float32(
                56,
                self.BYTE_ORDER,
            ),
            device,
        )

        # -----------------------------------------------------
        # Power Factor
        # -----------------------------------------------------

        m.power.power_factor = block.float32(
            self.REG_POWER_FACTOR,
            self.BYTE_ORDER,
        )

        # -----------------------------------------------------
        # Frequency
        # -----------------------------------------------------

        m.frequency = block.float32(
            self.REG_FREQUENCY,
            self.BYTE_ORDER,
        )

        # -----------------------------------------------------
        # Energy
        # -----------------------------------------------------

        m.energy.import_active = self.apply_ct_pt(
            block.float32(
                self.REG_IMPORT_ACTIVE_ENERGY,
                self.BYTE_ORDER,
            ),
            device,
        )

        m.energy.export_active = self.apply_ct_pt(
            block.float32(
                self.REG_EXPORT_ACTIVE_ENERGY,
                self.BYTE_ORDER,
            ),
            device,
        )


DriverFactory.register(SDM630Driver)