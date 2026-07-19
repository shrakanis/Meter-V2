"""
modbus/drivers/dtsu666.py

Energy Monitor V2

Chint DTSU666 / DTSU666-CT Modbus driver.
"""

from __future__ import annotations

import math

from common.enums import ByteOrder, RegisterType
from modbus.clients.base import BaseClient
from modbus.device import Device
from modbus.drivers.base import BaseDriver
from modbus.drivers.factory import DriverFactory
from modbus.register_block import RegisterBlock


class DTSU666Driver(BaseDriver):
    """
    Driver for Chint DTSU666 series meters, including DTSU666-CT.

    The public Modbus table exposes secondary-side quantities as IEEE-754
    single-precision values in ABCD byte order. Existing meter CT and PT
    configuration values are therefore applied by this driver.
    """

    NAME = "dtsu666"
    REGISTER_TYPE = RegisterType.HOLDING
    BYTE_ORDER = ByteOrder.ABCD

    # Measurement blocks. Separate reads avoid undefined address gaps in
    # the public register table.
    ELECTRICAL_BASE = 0x2000
    ELECTRICAL_COUNT = 0x22  # through 0x2021

    POWER_FACTOR_BASE = 0x202A
    POWER_FACTOR_COUNT = 0x08  # through 0x2031

    FREQUENCY_BASE = 0x2044
    FREQUENCY_COUNT = 0x02

    ENERGY_BASE = 0x101E
    ENERGY_COUNT = 0x14  # through 0x1031

    # Electrical values relative to ELECTRICAL_BASE
    REG_VOLTAGE_L1_L2 = 0x2000 - ELECTRICAL_BASE
    REG_VOLTAGE_L2_L3 = 0x2002 - ELECTRICAL_BASE
    REG_VOLTAGE_L3_L1 = 0x2004 - ELECTRICAL_BASE

    REG_VOLTAGE_L1 = 0x2006 - ELECTRICAL_BASE
    REG_VOLTAGE_L2 = 0x2008 - ELECTRICAL_BASE
    REG_VOLTAGE_L3 = 0x200A - ELECTRICAL_BASE

    REG_CURRENT_L1 = 0x200C - ELECTRICAL_BASE
    REG_CURRENT_L2 = 0x200E - ELECTRICAL_BASE
    REG_CURRENT_L3 = 0x2010 - ELECTRICAL_BASE

    REG_ACTIVE_POWER_TOTAL = 0x2012 - ELECTRICAL_BASE
    REG_ACTIVE_POWER_L1 = 0x2014 - ELECTRICAL_BASE
    REG_ACTIVE_POWER_L2 = 0x2016 - ELECTRICAL_BASE
    REG_ACTIVE_POWER_L3 = 0x2018 - ELECTRICAL_BASE

    REG_REACTIVE_POWER_TOTAL = 0x201A - ELECTRICAL_BASE
    REG_REACTIVE_POWER_L1 = 0x201C - ELECTRICAL_BASE
    REG_REACTIVE_POWER_L2 = 0x201E - ELECTRICAL_BASE
    REG_REACTIVE_POWER_L3 = 0x2020 - ELECTRICAL_BASE

    # Power factor relative to POWER_FACTOR_BASE
    REG_POWER_FACTOR_TOTAL = 0x202A - POWER_FACTOR_BASE
    REG_POWER_FACTOR_L1 = 0x202C - POWER_FACTOR_BASE
    REG_POWER_FACTOR_L2 = 0x202E - POWER_FACTOR_BASE
    REG_POWER_FACTOR_L3 = 0x2030 - POWER_FACTOR_BASE

    # Energy relative to ENERGY_BASE
    REG_IMPORT_ACTIVE_ENERGY = 0x101E - ENERGY_BASE
    REG_IMPORT_ACTIVE_ENERGY_L1 = 0x1020 - ENERGY_BASE
    REG_IMPORT_ACTIVE_ENERGY_L2 = 0x1022 - ENERGY_BASE
    REG_IMPORT_ACTIVE_ENERGY_L3 = 0x1024 - ENERGY_BASE
    REG_NET_IMPORT_ACTIVE_ENERGY = 0x1026 - ENERGY_BASE

    REG_EXPORT_ACTIVE_ENERGY = 0x1028 - ENERGY_BASE
    REG_EXPORT_ACTIVE_ENERGY_L1 = 0x102A - ENERGY_BASE
    REG_EXPORT_ACTIVE_ENERGY_L2 = 0x102C - ENERGY_BASE
    REG_EXPORT_ACTIVE_ENERGY_L3 = 0x102E - ENERGY_BASE
    REG_NET_EXPORT_ACTIVE_ENERGY = 0x1030 - ENERGY_BASE

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _float(
        self,
        block: RegisterBlock,
        index: int,
    ) -> float:
        """Decode one DTSU666 ABCD IEEE-754 floating-point value."""

        value = block.float32(
            index,
            self.BYTE_ORDER,
        )

        if not math.isfinite(value):
            raise ValueError(
                "DTSU666 returned a non-finite floating-point value."
            )

        return value

    @staticmethod
    def _apparent_power(
        active_power: float | None,
        reactive_power: float | None,
    ) -> float | None:
        """Calculate apparent power from active and reactive power."""

        if active_power is None or reactive_power is None:
            return None

        return math.hypot(
            active_power,
            reactive_power,
        )

    # ------------------------------------------------------------------
    # Runtime measurements
    # ------------------------------------------------------------------

    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """Read DTSU666 electrical values and active energy counters."""

        electrical = self.read_block(
            client=client,
            device=device,
            address=self.ELECTRICAL_BASE,
            count=self.ELECTRICAL_COUNT,
        )

        power_factor = self.read_block(
            client=client,
            device=device,
            address=self.POWER_FACTOR_BASE,
            count=self.POWER_FACTOR_COUNT,
        )

        frequency = self.read_block(
            client=client,
            device=device,
            address=self.FREQUENCY_BASE,
            count=self.FREQUENCY_COUNT,
        )

        energy = self.read_block(
            client=client,
            device=device,
            address=self.ENERGY_BASE,
            count=self.ENERGY_COUNT,
        )

        ct = device.meter.ct
        pt = device.meter.pt
        ct_pt = ct * pt

        m = device.measurements

        # Voltage (V)
        m.voltage.l1 = (
            self._float(electrical, self.REG_VOLTAGE_L1)
            * pt
        )
        m.voltage.l2 = (
            self._float(electrical, self.REG_VOLTAGE_L2)
            * pt
        )
        m.voltage.l3 = (
            self._float(electrical, self.REG_VOLTAGE_L3)
            * pt
        )
        m.voltage.average = (
            m.voltage.l1
            + m.voltage.l2
            + m.voltage.l3
        ) / 3.0

        # Current (A)
        m.current.l1 = (
            self._float(electrical, self.REG_CURRENT_L1)
            * ct
        )
        m.current.l2 = (
            self._float(electrical, self.REG_CURRENT_L2)
            * ct
        )
        m.current.l3 = (
            self._float(electrical, self.REG_CURRENT_L3)
            * ct
        )
        m.current.total = (
            m.current.l1
            + m.current.l2
            + m.current.l3
        )
        m.current.average = m.current.total / 3.0

        # The Modbus table reports power in W/var. Convert to kW/kvar.
        power_multiplier = ct_pt / 1000.0

        m.active_power.total = (
            self._float(
                electrical,
                self.REG_ACTIVE_POWER_TOTAL,
            )
            * power_multiplier
        )
        m.active_power.l1 = (
            self._float(
                electrical,
                self.REG_ACTIVE_POWER_L1,
            )
            * power_multiplier
        )
        m.active_power.l2 = (
            self._float(
                electrical,
                self.REG_ACTIVE_POWER_L2,
            )
            * power_multiplier
        )
        m.active_power.l3 = (
            self._float(
                electrical,
                self.REG_ACTIVE_POWER_L3,
            )
            * power_multiplier
        )

        m.reactive_power.total = (
            self._float(
                electrical,
                self.REG_REACTIVE_POWER_TOTAL,
            )
            * power_multiplier
        )
        m.reactive_power.l1 = (
            self._float(
                electrical,
                self.REG_REACTIVE_POWER_L1,
            )
            * power_multiplier
        )
        m.reactive_power.l2 = (
            self._float(
                electrical,
                self.REG_REACTIVE_POWER_L2,
            )
            * power_multiplier
        )
        m.reactive_power.l3 = (
            self._float(
                electrical,
                self.REG_REACTIVE_POWER_L3,
            )
            * power_multiplier
        )

        # Apparent power is not present in the regular public address table.
        # Calculate it from P and Q so Dashboard/History/Mimic remain complete.
        m.apparent_power.l1 = self._apparent_power(
            m.active_power.l1,
            m.reactive_power.l1,
        )
        m.apparent_power.l2 = self._apparent_power(
            m.active_power.l2,
            m.reactive_power.l2,
        )
        m.apparent_power.l3 = self._apparent_power(
            m.active_power.l3,
            m.reactive_power.l3,
        )
        m.apparent_power.total = self._apparent_power(
            m.active_power.total,
            m.reactive_power.total,
        )

        # Power factor and frequency
        m.power_factor.total = self._float(
            power_factor,
            self.REG_POWER_FACTOR_TOTAL,
        )
        m.power_factor.l1 = self._float(
            power_factor,
            self.REG_POWER_FACTOR_L1,
        )
        m.power_factor.l2 = self._float(
            power_factor,
            self.REG_POWER_FACTOR_L2,
        )
        m.power_factor.l3 = self._float(
            power_factor,
            self.REG_POWER_FACTOR_L3,
        )
        m.frequency = self._float(
            frequency,
            0,
        )

        # Active energy (kWh)
        m.energy.import_active = (
            self._float(
                energy,
                self.REG_IMPORT_ACTIVE_ENERGY,
            )
            * ct_pt
        )
        m.energy.export_active = (
            self._float(
                energy,
                self.REG_EXPORT_ACTIVE_ENERGY,
            )
            * ct_pt
        )

        device.info.update(
            {
                "manufacturer": "Chint",
                "model": "DTSU666 / DTSU666-CT",
                "connection": device.meter.connection_name,
            }
        )

        device.extra.update(
            {
                "voltage_l1_l2": self._float(
                    electrical,
                    self.REG_VOLTAGE_L1_L2,
                ) * pt,
                "voltage_l2_l3": self._float(
                    electrical,
                    self.REG_VOLTAGE_L2_L3,
                ) * pt,
                "voltage_l3_l1": self._float(
                    electrical,
                    self.REG_VOLTAGE_L3_L1,
                ) * pt,
                "energy_import_active_l1": self._float(
                    energy,
                    self.REG_IMPORT_ACTIVE_ENERGY_L1,
                ) * ct_pt,
                "energy_import_active_l2": self._float(
                    energy,
                    self.REG_IMPORT_ACTIVE_ENERGY_L2,
                ) * ct_pt,
                "energy_import_active_l3": self._float(
                    energy,
                    self.REG_IMPORT_ACTIVE_ENERGY_L3,
                ) * ct_pt,
                "energy_import_active_net": self._float(
                    energy,
                    self.REG_NET_IMPORT_ACTIVE_ENERGY,
                ) * ct_pt,
                "energy_export_active_l1": self._float(
                    energy,
                    self.REG_EXPORT_ACTIVE_ENERGY_L1,
                ) * ct_pt,
                "energy_export_active_l2": self._float(
                    energy,
                    self.REG_EXPORT_ACTIVE_ENERGY_L2,
                ) * ct_pt,
                "energy_export_active_l3": self._float(
                    energy,
                    self.REG_EXPORT_ACTIVE_ENERGY_L3,
                ) * ct_pt,
                "energy_export_active_net": self._float(
                    energy,
                    self.REG_NET_EXPORT_ACTIVE_ENERGY,
                ) * ct_pt,
            }
        )


DriverFactory.register(DTSU666Driver)
