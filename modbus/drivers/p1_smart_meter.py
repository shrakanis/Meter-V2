"""
modbus/drivers/p1_smart_meter.py

Energy Monitor V2

P1 Smart Meter driver.
"""

from __future__ import annotations

from typing import cast

from modbus.clients.base import BaseClient
from modbus.device import Device
from modbus.drivers.base import BaseDriver

from p1.client import P1Client
from p1.parser import P1Parser
from p1.telegram import P1Telegram


class P1SmartMeterDriver(BaseDriver):
    """
    Driver for an ESO P1 Smart Meter.

    The driver:

    - reads one complete P1 telegram;
    - parses OBIS values;
    - updates standard Device measurements;
    - stores P1-specific values in Device.extra;
    - stores static meter information in Device.info.

    Although this driver inherits BaseDriver for compatibility with
    DriverFactory, it does not use Modbus registers.
    """

    NAME = "p1"

    def __init__(self) -> None:

        self._parser = P1Parser()

    # ------------------------------------------------------------------
    # Runtime measurements
    # ------------------------------------------------------------------

    def read(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """
        Read and process one P1 telegram.
        """

        p1_client = cast(
            P1Client,
            client,
        )

        raw_telegram = p1_client.read()

        telegram = self._parser.parse(
            raw_telegram
        )

        self._update_measurements(
            device=device,
            telegram=telegram,
        )

        self._update_extra(
            device=device,
            telegram=telegram,
        )

        self._update_info(
            device=device,
            telegram=telegram,
        )

    # ------------------------------------------------------------------
    # Static information
    # ------------------------------------------------------------------

    def read_info(
        self,
        client: BaseClient,
        device: Device,
    ) -> None:
        """
        Static P1 information is read together with every telegram.

        P1 telegrams contain both measurements and identification
        fields, so no separate communication request is required.
        """

        return

    # ------------------------------------------------------------------
    # Standard measurements
    # ------------------------------------------------------------------

    @staticmethod
    def _update_measurements(
        *,
        device: Device,
        telegram: P1Telegram,
    ) -> None:
        """
        Copy parsed P1 values into the common Measurements model.
        """

        measurements = device.measurements

        # --------------------------------------------------------------
        # Voltage
        # --------------------------------------------------------------

        measurements.voltage.l1 = (
            telegram.voltage_l1
        )

        measurements.voltage.l2 = (
            telegram.voltage_l2
        )

        measurements.voltage.l3 = (
            telegram.voltage_l3
        )

        measurements.voltage.average = (
            telegram.voltage_average
        )

        # --------------------------------------------------------------
        # Current
        # --------------------------------------------------------------

        measurements.current.l1 = (
            telegram.current_l1
        )

        measurements.current.l2 = (
            telegram.current_l2
        )

        measurements.current.l3 = (
            telegram.current_l3
        )

        measurements.current.total = (
            telegram.current_total
        )

        # --------------------------------------------------------------
        # Active power
        # --------------------------------------------------------------

        measurements.active_power.l1 = (
            telegram.active_power_l1
        )

        measurements.active_power.l2 = (
            telegram.active_power_l2
        )

        measurements.active_power.l3 = (
            telegram.active_power_l3
        )

        measurements.active_power.total = (
            telegram.active_power_total
        )

        # --------------------------------------------------------------
        # Reactive power
        # --------------------------------------------------------------

        measurements.reactive_power.l1 = (
            telegram.reactive_power_l1
        )

        measurements.reactive_power.l2 = (
            telegram.reactive_power_l2
        )

        measurements.reactive_power.l3 = (
            telegram.reactive_power_l3
        )

        measurements.reactive_power.total = (
            telegram.reactive_power_total
        )

        # --------------------------------------------------------------
        # Apparent power
        # --------------------------------------------------------------

        measurements.apparent_power.l1 = (
            telegram.apparent_power_l1
        )

        measurements.apparent_power.l2 = (
            telegram.apparent_power_l2
        )

        measurements.apparent_power.l3 = (
            telegram.apparent_power_l3
        )

        measurements.apparent_power.total = (
            telegram.apparent_power_total
        )

        # --------------------------------------------------------------
        # Power factor
        # --------------------------------------------------------------

        measurements.power_factor.l1 = (
            telegram.power_factor_l1
        )

        measurements.power_factor.l2 = (
            telegram.power_factor_l2
        )

        measurements.power_factor.l3 = (
            telegram.power_factor_l3
        )

        measurements.power_factor.total = (
            telegram.power_factor_total
        )

        # --------------------------------------------------------------
        # Frequency
        # --------------------------------------------------------------

        measurements.frequency = (
            telegram.frequency
        )

        # --------------------------------------------------------------
        # Energy
        # --------------------------------------------------------------

        measurements.energy.import_active = (
            telegram.energy_import_active
        )

        measurements.energy.export_active = (
            telegram.energy_export_active
        )

        measurements.energy.import_reactive = (
            telegram.energy_import_reactive
        )

        measurements.energy.export_reactive = (
            telegram.energy_export_reactive
        )

    # ------------------------------------------------------------------
    # P1-specific values
    # ------------------------------------------------------------------

    @staticmethod
    def _update_extra(
        *,
        device: Device,
        telegram: P1Telegram,
    ) -> None:
        """
        Store measurements that are not part of the common model.
        """

        device.extra.update(
            {
                # Serial / communication
                "p1_timestamp": (
                    telegram.timestamp
                ),
                "p1_raw": (
                    telegram.raw
                ),

                # Additional currents
                "current_neutral": (
                    telegram.current_neutral
                ),

                # Active energy tariffs
                "tariff1_import": (
                    telegram.tariff1_import
                ),
                "tariff2_import": (
                    telegram.tariff2_import
                ),
                "tariff3_import": (
                    telegram.tariff3_import
                ),
                "tariff4_import": (
                    telegram.tariff4_import
                ),

                "tariff1_export": (
                    telegram.tariff1_export
                ),
                "tariff2_export": (
                    telegram.tariff2_export
                ),
                "tariff3_export": (
                    telegram.tariff3_export
                ),
                "tariff4_export": (
                    telegram.tariff4_export
                ),

                # Events
                "power_failures": (
                    telegram.power_failures
                ),
                "long_power_failures": (
                    telegram.long_power_failures
                ),

                "voltage_sags_l1": (
                    telegram.voltage_sags_l1
                ),
                "voltage_sags_l2": (
                    telegram.voltage_sags_l2
                ),
                "voltage_sags_l3": (
                    telegram.voltage_sags_l3
                ),

                "voltage_swells_l1": (
                    telegram.voltage_swells_l1
                ),
                "voltage_swells_l2": (
                    telegram.voltage_swells_l2
                ),
                "voltage_swells_l3": (
                    telegram.voltage_swells_l3
                ),
            }
        )

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    @staticmethod
    def _update_info(
        *,
        device: Device,
        telegram: P1Telegram,
    ) -> None:
        """
        Store meter identification information.
        """

        if telegram.manufacturer:

            device.info[
                "manufacturer"
            ] = telegram.manufacturer

        if telegram.meter_id:

            device.info[
                "meter_id"
            ] = telegram.meter_id

        if telegram.firmware:

            device.info[
                "firmware"
            ] = telegram.firmware

        device.info[
            "connection"
        ] = device.meter.connection_name

        device.info[
            "meter_type"
        ] = "p1"