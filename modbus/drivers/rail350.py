"""
modbus/drivers/rail350.py

Energy Monitor V2

Northern Design Rail350 Modbus driver.
"""

from __future__ import annotations

from common.enums import RegisterType
from modbus.clients.base import BaseClient
from modbus.device import Device
from modbus.drivers.base import BaseDriver
from modbus.drivers.factory import DriverFactory
from modbus.register_block import RegisterBlock


class Rail350Driver(BaseDriver):
    """
    Driver for the Northern Design Rail350 meter.

    The meter exposes an amalgamated holding-register table containing
    instantaneous values and their scaling constants. Instantaneous
    quantities are signed 16-bit integers and are converted with:

        real_base_units = raw * 10 ** (scale - 3)

    Power values are converted from W/VA/var to kW/kVA/kvar.
    Accumulated energy is stored as unsigned 32-bit integers and is
    converted to kWh/kvarh with the meter eScale value.
    """

    NAME = "rail350"
    REGISTER_TYPE = RegisterType.HOLDING

    # Rail350 data addresses are zero-based Modbus addresses.
    VALUES_BASE = 7680
    VALUES_COUNT = 58

    ENERGY_BASE = 512
    ENERGY_COUNT = 18

    # ------------------------------------------------------------------
    # Amalgamated table offsets (relative to VALUES_BASE)
    # ------------------------------------------------------------------

    REG_CURRENT_L1 = 7688 - VALUES_BASE
    REG_CURRENT_L2 = 7689 - VALUES_BASE
    REG_CURRENT_L3 = 7690 - VALUES_BASE

    REG_VOLTAGE_L1 = 7691 - VALUES_BASE
    REG_VOLTAGE_L2 = 7692 - VALUES_BASE
    REG_VOLTAGE_L3 = 7693 - VALUES_BASE

    REG_VOLTAGE_L1_L2 = 7694 - VALUES_BASE
    REG_VOLTAGE_L2_L3 = 7695 - VALUES_BASE
    REG_VOLTAGE_L3_L1 = 7696 - VALUES_BASE

    REG_FREQUENCY = 7697 - VALUES_BASE

    REG_POWER_FACTOR_L1 = 7698 - VALUES_BASE
    REG_POWER_FACTOR_L2 = 7699 - VALUES_BASE
    REG_POWER_FACTOR_L3 = 7700 - VALUES_BASE
    REG_POWER_FACTOR_TOTAL = 7701 - VALUES_BASE

    REG_ACTIVE_POWER_L1 = 7702 - VALUES_BASE
    REG_ACTIVE_POWER_L2 = 7703 - VALUES_BASE
    REG_ACTIVE_POWER_L3 = 7704 - VALUES_BASE
    REG_ACTIVE_POWER_TOTAL = 7705 - VALUES_BASE

    REG_APPARENT_POWER_L1 = 7706 - VALUES_BASE
    REG_APPARENT_POWER_L2 = 7707 - VALUES_BASE
    REG_APPARENT_POWER_L3 = 7708 - VALUES_BASE
    REG_APPARENT_POWER_TOTAL = 7709 - VALUES_BASE

    REG_REACTIVE_POWER_L1 = 7710 - VALUES_BASE
    REG_REACTIVE_POWER_L2 = 7711 - VALUES_BASE
    REG_REACTIVE_POWER_L3 = 7712 - VALUES_BASE
    REG_REACTIVE_POWER_TOTAL = 7713 - VALUES_BASE

    REG_NEUTRAL_CURRENT = 7732 - VALUES_BASE

    REG_SCALE_CURRENT = 7733 - VALUES_BASE
    REG_SCALE_PHASE_VOLTAGE = 7734 - VALUES_BASE
    REG_SCALE_LINE_VOLTAGE = 7735 - VALUES_BASE
    REG_SCALE_POWER = 7736 - VALUES_BASE
    REG_SCALE_ENERGY = 7737 - VALUES_BASE

    # ------------------------------------------------------------------
    # Main energy table offsets (relative to ENERGY_BASE)
    # ------------------------------------------------------------------

    REG_ENERGY_SCALE = 513 - ENERGY_BASE
    REG_IMPORT_ACTIVE_ENERGY = 514 - ENERGY_BASE
    REG_APPARENT_ENERGY = 516 - ENERGY_BASE
    REG_REACTIVE_INDUCTIVE_ENERGY = 518 - ENERGY_BASE
    REG_REACTIVE_CAPACITIVE_ENERGY = 520 - ENERGY_BASE
    REG_IMPORT_REACTIVE_ENERGY = 522 - ENERGY_BASE
    REG_EXPORT_ACTIVE_ENERGY = 524 - ENERGY_BASE
    REG_EXPORT_REACTIVE_ENERGY = 526 - ENERGY_BASE
    REG_HOURS_RUN = 528 - ENERGY_BASE

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _scale_factor(scale: int) -> float:
        """Return the Rail350 decimal scaling multiplier."""

        if scale < -12 or scale > 12:
            raise ValueError(
                f"Invalid Rail350 scaling value: {scale}"
            )

        return 10.0 ** (scale - 3)

    @classmethod
    def _scaled_i16(
        cls,
        block: RegisterBlock,
        index: int,
        scale: int,
    ) -> float:
        """Decode and scale one signed instantaneous register."""

        return block.int16(index) * cls._scale_factor(scale)

    @staticmethod
    def _energy_kwh(
        block: RegisterBlock,
        index: int,
        energy_scale: int,
    ) -> float:
        """Decode a 32-bit accumulated energy value as kWh/kvarh."""

        if energy_scale < -12 or energy_scale > 12:
            raise ValueError(
                f"Invalid Rail350 energy scale: {energy_scale}"
            )

        return block.uint32(index) * (10.0 ** (energy_scale - 6))

    # ------------------------------------------------------------------
    # Runtime measurements
    # ------------------------------------------------------------------

    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """Read Rail350 instantaneous values and accumulated energy."""

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

        current_scale = values.int16(
            self.REG_SCALE_CURRENT
        )
        phase_voltage_scale = values.int16(
            self.REG_SCALE_PHASE_VOLTAGE
        )
        line_voltage_scale = values.int16(
            self.REG_SCALE_LINE_VOLTAGE
        )
        power_scale = values.int16(
            self.REG_SCALE_POWER
        )

        # The energy scale low word is the documented source. The copy in
        # the amalgamated table is retained in extra data for diagnostics.
        energy_scale = energy.int16(
            self.REG_ENERGY_SCALE
        )

        ct = device.meter.ct
        pt = device.meter.pt
        ct_pt = ct * pt

        m = device.measurements

        # Voltage (V)
        m.voltage.l1 = (
            self._scaled_i16(
                values,
                self.REG_VOLTAGE_L1,
                phase_voltage_scale,
            )
            * pt
        )
        m.voltage.l2 = (
            self._scaled_i16(
                values,
                self.REG_VOLTAGE_L2,
                phase_voltage_scale,
            )
            * pt
        )
        m.voltage.l3 = (
            self._scaled_i16(
                values,
                self.REG_VOLTAGE_L3,
                phase_voltage_scale,
            )
            * pt
        )
        m.voltage.average = (
            m.voltage.l1
            + m.voltage.l2
            + m.voltage.l3
        ) / 3.0

        # Current (A)
        m.current.l1 = (
            self._scaled_i16(
                values,
                self.REG_CURRENT_L1,
                current_scale,
            )
            * ct
        )
        m.current.l2 = (
            self._scaled_i16(
                values,
                self.REG_CURRENT_L2,
                current_scale,
            )
            * ct
        )
        m.current.l3 = (
            self._scaled_i16(
                values,
                self.REG_CURRENT_L3,
                current_scale,
            )
            * ct
        )
        m.current.total = (
            m.current.l1
            + m.current.l2
            + m.current.l3
        )
        m.current.average = m.current.total / 3.0

        # Power registers are scaled to base units (W/VA/var), then
        # converted to the common application units (kW/kVA/kvar).
        power_multiplier = ct_pt / 1000.0

        m.active_power.l1 = self._scaled_i16(
            values,
            self.REG_ACTIVE_POWER_L1,
            power_scale,
        ) * power_multiplier
        m.active_power.l2 = self._scaled_i16(
            values,
            self.REG_ACTIVE_POWER_L2,
            power_scale,
        ) * power_multiplier
        m.active_power.l3 = self._scaled_i16(
            values,
            self.REG_ACTIVE_POWER_L3,
            power_scale,
        ) * power_multiplier
        m.active_power.total = self._scaled_i16(
            values,
            self.REG_ACTIVE_POWER_TOTAL,
            power_scale,
        ) * power_multiplier

        m.reactive_power.l1 = self._scaled_i16(
            values,
            self.REG_REACTIVE_POWER_L1,
            power_scale,
        ) * power_multiplier
        m.reactive_power.l2 = self._scaled_i16(
            values,
            self.REG_REACTIVE_POWER_L2,
            power_scale,
        ) * power_multiplier
        m.reactive_power.l3 = self._scaled_i16(
            values,
            self.REG_REACTIVE_POWER_L3,
            power_scale,
        ) * power_multiplier
        m.reactive_power.total = self._scaled_i16(
            values,
            self.REG_REACTIVE_POWER_TOTAL,
            power_scale,
        ) * power_multiplier

        m.apparent_power.l1 = self._scaled_i16(
            values,
            self.REG_APPARENT_POWER_L1,
            power_scale,
        ) * power_multiplier
        m.apparent_power.l2 = self._scaled_i16(
            values,
            self.REG_APPARENT_POWER_L2,
            power_scale,
        ) * power_multiplier
        m.apparent_power.l3 = self._scaled_i16(
            values,
            self.REG_APPARENT_POWER_L3,
            power_scale,
        ) * power_multiplier
        m.apparent_power.total = self._scaled_i16(
            values,
            self.REG_APPARENT_POWER_TOTAL,
            power_scale,
        ) * power_multiplier

        # Power factor and frequency
        m.power_factor.l1 = (
            values.int16(self.REG_POWER_FACTOR_L1)
            / 1000.0
        )
        m.power_factor.l2 = (
            values.int16(self.REG_POWER_FACTOR_L2)
            / 1000.0
        )
        m.power_factor.l3 = (
            values.int16(self.REG_POWER_FACTOR_L3)
            / 1000.0
        )
        m.power_factor.total = (
            values.int16(self.REG_POWER_FACTOR_TOTAL)
            / 1000.0
        )
        m.frequency = (
            values.int16(self.REG_FREQUENCY)
            / 10.0
        )

        # Accumulated energy. External CT/PT correction is optional and is
        # controlled by the existing meter configuration values.
        m.energy.import_active = self._energy_kwh(
            energy,
            self.REG_IMPORT_ACTIVE_ENERGY,
            energy_scale,
        ) * ct_pt
        m.energy.export_active = self._energy_kwh(
            energy,
            self.REG_EXPORT_ACTIVE_ENERGY,
            energy_scale,
        ) * ct_pt
        m.energy.import_reactive = self._energy_kwh(
            energy,
            self.REG_IMPORT_REACTIVE_ENERGY,
            energy_scale,
        ) * ct_pt
        m.energy.export_reactive = self._energy_kwh(
            energy,
            self.REG_EXPORT_REACTIVE_ENERGY,
            energy_scale,
        ) * ct_pt

        device.info.update(
            {
                "manufacturer": "Northern Design",
                "model": "Rail350",
                "connection": device.meter.connection_name,
            }
        )

        device.extra.update(
            {
                "voltage_l1_l2": self._scaled_i16(
                    values,
                    self.REG_VOLTAGE_L1_L2,
                    line_voltage_scale,
                ) * pt,
                "voltage_l2_l3": self._scaled_i16(
                    values,
                    self.REG_VOLTAGE_L2_L3,
                    line_voltage_scale,
                ) * pt,
                "voltage_l3_l1": self._scaled_i16(
                    values,
                    self.REG_VOLTAGE_L3_L1,
                    line_voltage_scale,
                ) * pt,
                "neutral_current": self._scaled_i16(
                    values,
                    self.REG_NEUTRAL_CURRENT,
                    current_scale,
                ) * ct,
                "energy_apparent": self._energy_kwh(
                    energy,
                    self.REG_APPARENT_ENERGY,
                    energy_scale,
                ) * ct_pt,
                "energy_reactive_inductive": self._energy_kwh(
                    energy,
                    self.REG_REACTIVE_INDUCTIVE_ENERGY,
                    energy_scale,
                ) * ct_pt,
                "energy_reactive_capacitive": self._energy_kwh(
                    energy,
                    self.REG_REACTIVE_CAPACITIVE_ENERGY,
                    energy_scale,
                ) * ct_pt,
                "hours_run": energy.uint32(
                    self.REG_HOURS_RUN
                ) * 0.1,
                "rail350_scale_current": current_scale,
                "rail350_scale_phase_voltage": phase_voltage_scale,
                "rail350_scale_line_voltage": line_voltage_scale,
                "rail350_scale_power": power_scale,
                "rail350_scale_energy": energy_scale,
                "rail350_scale_energy_copy": values.int16(
                    self.REG_SCALE_ENERGY
                ),
            }
        )


DriverFactory.register(Rail350Driver)
