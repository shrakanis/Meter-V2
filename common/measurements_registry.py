"""
common/measurements_registry.py

Energy Monitor V2

Central measurement registry.

Every measurement that can be:
    - displayed
    - stored
    - charted
    - exported

is defined here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


# ----------------------------------------------------------------------
# Dataset
# ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Dataset:
    """
    One InfluxDB field.
    """

    field: str
    label: str


# ----------------------------------------------------------------------
# Measurement
# ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Measurement:
    """
    One logical measurement.

    Example:

        Voltage
            L1
            L2
            L3
    """

    key: str

    title: str

    unit: str

    decimals: int

    datasets: tuple[Dataset, ...]

    history: bool = True

    live: bool = True

    dashboard: bool = True


# ----------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------

MEASUREMENTS: dict[str, Measurement] = {

    #
    # Voltage
    #

    "voltage": Measurement(

        key="voltage",

        title="Voltage",

        unit="V",

        decimals=1,

        datasets=(

            Dataset("voltage_l1", "L1"),
            Dataset("voltage_l2", "L2"),
            Dataset("voltage_l3", "L3"),

        ),

    ),

    #
    # Current
    #

    "current": Measurement(

        key="current",

        title="Current",

        unit="A",

        decimals=2,

        datasets=(

            Dataset("current_l1", "L1"),
            Dataset("current_l2", "L2"),
            Dataset("current_l3", "L3"),

        ),

    ),

    #
    # Active Power
    #

    "active_power": Measurement(

        key="active_power",

        title="Active Power",

        unit="kW",

        decimals=2,

        datasets=(

            Dataset("active_power_l1", "L1"),
            Dataset("active_power_l2", "L2"),
            Dataset("active_power_l3", "L3"),

        ),

    ),

    #
    # Reactive Power
    #

    "reactive_power": Measurement(

        key="reactive_power",

        title="Reactive Power",

        unit="kvar",

        decimals=2,

        datasets=(

            Dataset("reactive_power_l1", "L1"),
            Dataset("reactive_power_l2", "L2"),
            Dataset("reactive_power_l3", "L3"),

        ),

    ),

    #
    # Apparent Power
    #

    "apparent_power": Measurement(

        key="apparent_power",

        title="Apparent Power",

        unit="kVA",

        decimals=2,

        datasets=(

            Dataset("apparent_power_l1", "L1"),
            Dataset("apparent_power_l2", "L2"),
            Dataset("apparent_power_l3", "L3"),

        ),

    ),

    #
    # Power Factor
    #

    "power_factor": Measurement(

        key="power_factor",

        title="Power Factor",

        unit="",

        decimals=3,

        datasets=(

            Dataset("power_factor_l1", "L1"),
            Dataset("power_factor_l2", "L2"),
            Dataset("power_factor_l3", "L3"),

        ),

    ),

    #
    # Frequency
    #

    "frequency": Measurement(

        key="frequency",

        title="Frequency",

        unit="Hz",

        decimals=2,

        datasets=(

            Dataset("frequency", "Frequency"),

        ),

    ),

    #
    # Active Energy
    #

    "energy_import": Measurement(

        key="energy_import",

        title="Imported Energy",

        unit="kWh",

        decimals=2,

        datasets=(

            Dataset("energy_import_active", "Import"),

        ),

    ),

    "energy_export": Measurement(

        key="energy_export",

        title="Exported Energy",

        unit="kWh",

        decimals=2,

        datasets=(

            Dataset("energy_export_active", "Export"),

        ),

    ),

    #
    # Reactive Energy
    #

    "reactive_energy_import": Measurement(

        key="reactive_energy_import",

        title="Reactive Energy (+)",

        unit="kvarh",

        decimals=2,

        datasets=(

            Dataset("energy_import_reactive", "+R"),

        ),

    ),

    "reactive_energy_export": Measurement(

        key="reactive_energy_export",

        title="Reactive Energy (-)",

        unit="kvarh",

        decimals=2,

        datasets=(

            Dataset("energy_export_reactive", "-R"),

        ),

    ),

}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def get_measurement(
    key: str,
) -> Measurement:

    return MEASUREMENTS[key]


def exists(
    key: str,
) -> bool:

    return key in MEASUREMENTS


def all_measurements() -> Iterable[Measurement]:

    return MEASUREMENTS.values()


def history_measurements() -> list[Measurement]:

    return [
        m
        for m in MEASUREMENTS.values()
        if m.history
    ]


def live_measurements() -> list[Measurement]:

    return [
        m
        for m in MEASUREMENTS.values()
        if m.live
    ]


def dashboard_measurements() -> list[Measurement]:

    return [
        m
        for m in MEASUREMENTS.values()
        if m.dashboard
    ]