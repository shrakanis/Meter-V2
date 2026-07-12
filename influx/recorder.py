"""
influx/recorder.py

Energy Monitor V2

Measurement recorder.
"""

from __future__ import annotations

import logging

from influx.client import InfluxClient
from modbus.device import Device

logger = logging.getLogger(__name__)


class MeasurementRecorder:
    """
    Writes Device measurements to InfluxDB.

    DeviceManager should call:

        recorder.record(device)

    after every successful poll.
    """

    def __init__(
        self,
        influx: InfluxClient,
    ) -> None:

        self._influx = influx

    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------

    def record(
        self,
        device: Device,
    ) -> bool:
        """
        Record one device snapshot.

        Returns
        -------
        bool
            True if written successfully.
        """

        if not self._influx.enabled:
            return False

        if not self._influx.connected():
            return False

        m = device.measurements

        point = self._influx.point(

            measurement="meter",

            tags={

                "device_id": device.id,
                "name": device.name,
                "driver": device.driver,
                "protocol": device.protocol.name,

            },

            fields={

                #
                # Voltage
                #

                "voltage_l1": m.voltage.l1,
                "voltage_l2": m.voltage.l2,
                "voltage_l3": m.voltage.l3,
                "voltage_average": m.voltage.average,

                #
                # Current
                #

                "current_l1": m.current.l1,
                "current_l2": m.current.l2,
                "current_l3": m.current.l3,
                "current_total": m.current.total,
                "current_average": m.current.average,

                #
                # Active power
                #

                "active_power_l1": m.active_power.l1,
                "active_power_l2": m.active_power.l2,
                "active_power_l3": m.active_power.l3,
                "active_power_total": m.active_power.total,

                #
                # Reactive power
                #

                "reactive_power_l1": m.reactive_power.l1,
                "reactive_power_l2": m.reactive_power.l2,
                "reactive_power_l3": m.reactive_power.l3,
                "reactive_power_total": m.reactive_power.total,

                #
                # Apparent power
                #

                "apparent_power_l1": m.apparent_power.l1,
                "apparent_power_l2": m.apparent_power.l2,
                "apparent_power_l3": m.apparent_power.l3,
                "apparent_power_total": m.apparent_power.total,

                #
                # Power factor
                #

                "power_factor_l1": m.power_factor.l1,
                "power_factor_l2": m.power_factor.l2,
                "power_factor_l3": m.power_factor.l3,
                "power_factor_total": m.power_factor.total,

                #
                # Frequency
                #

                "frequency": m.frequency,

                #
                # Energy
                #

                "energy_import_active": m.energy.import_active,
                "energy_export_active": m.energy.export_active,

                "energy_import_reactive": m.energy.import_reactive,
                "energy_export_reactive": m.energy.export_reactive,

                #
                # Diagnostics
                #

                "response_time_ms": round(
                    device.response_time * 1000.0,
                    2,
                ),

                "connected": int(
                    device.connected
                ),

            },

        )

        ok = self._influx.write(
            point,
        )

        if ok:

            logger.debug(
                "Recorded '%s' to InfluxDB",
                device.name,
            )

        return ok