"""
p1/telegram.py

Energy Monitor V2

P1 telegram data model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class P1Telegram:
    """
    Parsed P1 telegram.

    All values use the same names as Device.measurements
    to simplify driver implementation.
    """

    # ------------------------------------------------------------------
    # Voltage
    # ------------------------------------------------------------------

    voltage_l1: float = 0.0
    voltage_l2: float = 0.0
    voltage_l3: float = 0.0

    voltage_average: float = 0.0

    # ------------------------------------------------------------------
    # Current
    # ------------------------------------------------------------------

    current_l1: float = 0.0
    current_l2: float = 0.0
    current_l3: float = 0.0

    current_neutral: float = 0.0

    current_total: float = 0.0

    # ------------------------------------------------------------------
    # Active power
    # ------------------------------------------------------------------

    active_power_l1: float = 0.0
    active_power_l2: float = 0.0
    active_power_l3: float = 0.0

    active_power_total: float = 0.0

    # ------------------------------------------------------------------
    # Reactive power
    # ------------------------------------------------------------------

    reactive_power_l1: float = 0.0
    reactive_power_l2: float = 0.0
    reactive_power_l3: float = 0.0

    reactive_power_total: float = 0.0

    # ------------------------------------------------------------------
    # Apparant power
    # ------------------------------------------------------------------

    apparent_power_l1: float = 0.0
    apparent_power_l2: float = 0.0
    apparent_power_l3: float = 0.0

    apparent_power_total: float = 0.0

    # ------------------------------------------------------------------
    # Power factor
    # ------------------------------------------------------------------

    power_factor_l1: float = 0.0
    power_factor_l2: float = 0.0
    power_factor_l3: float = 0.0

    power_factor_total: float = 0.0

    # ------------------------------------------------------------------
    # Frequency
    # ------------------------------------------------------------------

    frequency: float = 0.0

    # ------------------------------------------------------------------
    # Energy
    # ------------------------------------------------------------------

    energy_import_active: float = 0.0
    energy_export_active: float = 0.0

    energy_import_reactive: float = 0.0
    energy_export_reactive: float = 0.0

    tariff1_import: float = 0.0
    tariff2_import: float = 0.0
    tariff3_import: float = 0.0
    tariff4_import: float = 0.0

    tariff1_export: float = 0.0
    tariff2_export: float = 0.0
    tariff3_export: float = 0.0
    tariff4_export: float = 0.0

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    power_failures: int = 0

    long_power_failures: int = 0

    voltage_sags_l1: int = 0
    voltage_sags_l2: int = 0
    voltage_sags_l3: int = 0

    voltage_swells_l1: int = 0
    voltage_swells_l2: int = 0
    voltage_swells_l3: int = 0

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    meter_id: str = ""

    manufacturer: str = ""

    firmware: str = ""

    timestamp: str = ""

    # ------------------------------------------------------------------
    # Raw telegram
    # ------------------------------------------------------------------

    raw: str = ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        """True if a telegram has been received."""

        return bool(self.raw)

    @property
    def phase_count(self) -> int:
        """Return detected number of phases."""

        phases = 0

        if self.voltage_l1:
            phases += 1

        if self.voltage_l2:
            phases += 1

        if self.voltage_l3:
            phases += 1

        return phases