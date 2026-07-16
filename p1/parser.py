"""
p1/parser.py

Energy Monitor V2

ESO P1 telegram parser.
"""

from __future__ import annotations

import re
from dataclasses import fields

from p1.telegram import P1Telegram


_LINE_RE = re.compile(
    r"^(?P<obis>[0-9]+-[0-9]+:[0-9.]+)"
    r"\((?P<value>[^)]*)\)$"
)


class P1Parser:
    """
    Parse an ESO P1 telegram.

    Supported examples
    ------------------
    1-0:32.7.0(0000.232*kV)
    1-0:31.7.0(0000.304*kA)
    1-0:14.7.0(0000.049*kHz)
    1-0:1.8.0(01391785.630*kWh)
    1-0:13.7.0(00998)
    """

    def parse(
        self,
        telegram: str,
    ) -> P1Telegram:
        """Parse one complete P1 telegram."""

        if not telegram:
            raise ValueError(
                "P1 telegram is empty."
            )

        result = P1Telegram(
            raw=telegram
        )

        values: dict[str, tuple[str, str]] = {}

        for raw_line in telegram.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("/"):

                result.manufacturer = line

                self._parse_header(
                    line,
                    result,
                )

                continue

            if line.startswith("!"):
                continue

            match = _LINE_RE.match(
                line
            )

            if match is None:
                continue

            obis = match.group(
                "obis"
            )

            raw_value = match.group(
                "value"
            )

            value_text, unit = (
                self._split_value_and_unit(
                    raw_value
                )
            )

            values[obis] = (
                value_text,
                unit,
            )

        # --------------------------------------------------------------
        # Identification
        # --------------------------------------------------------------

        result.timestamp = self._text(
            values,
            "0-0:1.0.0",
        )

        result.firmware = self._text(
            values,
            "1-0:0.2.0",
        )

        # Some meters may provide a dedicated serial-number OBIS.
        result.meter_id = (
            self._text(
                values,
                "0-0:96.1.0",
            )
            or self._text(
                values,
                "0-0:96.1.1",
            )
            or result.meter_id
        )

        # --------------------------------------------------------------
        # Voltage
        # --------------------------------------------------------------

        result.voltage_l1 = self._number(
            values,
            "1-0:32.7.0",
            target_unit="V",
        )

        result.voltage_l2 = self._number(
            values,
            "1-0:52.7.0",
            target_unit="V",
        )

        result.voltage_l3 = self._number(
            values,
            "1-0:72.7.0",
            target_unit="V",
        )

        voltage_direct = self._number(
            values,
            "1-0:12.7.0",
            target_unit="V",
        )

        phase_voltages = [
            value
            for value in (
                result.voltage_l1,
                result.voltage_l2,
                result.voltage_l3,
            )
            if value > 0
        ]

        if phase_voltages:

            result.voltage_average = (
                sum(phase_voltages)
                / len(phase_voltages)
            )

        else:

            result.voltage_average = (
                voltage_direct
            )

        # --------------------------------------------------------------
        # Current
        # --------------------------------------------------------------

        result.current_l1 = self._number(
            values,
            "1-0:31.7.0",
            target_unit="A",
        )

        result.current_l2 = self._number(
            values,
            "1-0:51.7.0",
            target_unit="A",
        )

        result.current_l3 = self._number(
            values,
            "1-0:71.7.0",
            target_unit="A",
        )

        result.current_neutral = self._number(
            values,
            "1-0:91.7.0",
            target_unit="A",
        )

        current_total_direct = self._number(
            values,
            "1-0:90.7.0",
            target_unit="A",
        )

        result.current_total = (
            current_total_direct
            if current_total_direct != 0
            else (
                result.current_l1
                + result.current_l2
                + result.current_l3
            )
        )

        # --------------------------------------------------------------
        # Active power
        # Import is positive, export is negative.
        # --------------------------------------------------------------

        active_import_l1 = self._number(
            values,
            "1-0:21.7.0",
            target_unit="kW",
        )

        active_import_l2 = self._number(
            values,
            "1-0:41.7.0",
            target_unit="kW",
        )

        active_import_l3 = self._number(
            values,
            "1-0:61.7.0",
            target_unit="kW",
        )

        active_export_l1 = self._number(
            values,
            "1-0:22.7.0",
            target_unit="kW",
        )

        active_export_l2 = self._number(
            values,
            "1-0:42.7.0",
            target_unit="kW",
        )

        active_export_l3 = self._number(
            values,
            "1-0:62.7.0",
            target_unit="kW",
        )

        result.active_power_l1 = (
            active_import_l1
            - active_export_l1
        )

        result.active_power_l2 = (
            active_import_l2
            - active_export_l2
        )

        result.active_power_l3 = (
            active_import_l3
            - active_export_l3
        )

        result.active_power_total = (
            result.active_power_l1
            + result.active_power_l2
            + result.active_power_l3
        )

        # Fallback for meters without phase powers.
        if result.active_power_total == 0:

            result.active_power_total = (
                self._number(
                    values,
                    "1-0:15.7.0",
                    target_unit="kW",
                )
            )

        # --------------------------------------------------------------
        # Reactive power
        # Import is positive, export is negative.
        # --------------------------------------------------------------

        reactive_import_l1 = self._number(
            values,
            "1-0:23.7.0",
            target_unit="kvar",
        )

        reactive_import_l2 = self._number(
            values,
            "1-0:43.7.0",
            target_unit="kvar",
        )

        reactive_import_l3 = self._number(
            values,
            "1-0:63.7.0",
            target_unit="kvar",
        )

        reactive_export_l1 = self._number(
            values,
            "1-0:24.7.0",
            target_unit="kvar",
        )

        reactive_export_l2 = self._number(
            values,
            "1-0:44.7.0",
            target_unit="kvar",
        )

        reactive_export_l3 = self._number(
            values,
            "1-0:64.7.0",
            target_unit="kvar",
        )

        result.reactive_power_l1 = (
            reactive_import_l1
            - reactive_export_l1
        )

        result.reactive_power_l2 = (
            reactive_import_l2
            - reactive_export_l2
        )

        result.reactive_power_l3 = (
            reactive_import_l3
            - reactive_export_l3
        )

        result.reactive_power_total = (
            result.reactive_power_l1
            + result.reactive_power_l2
            + result.reactive_power_l3
        )

        # --------------------------------------------------------------
        # Apparent power
        # --------------------------------------------------------------

        apparent_import_l1 = self._number(
            values,
            "1-0:29.7.0",
            target_unit="kVA",
        )

        apparent_import_l2 = self._number(
            values,
            "1-0:49.7.0",
            target_unit="kVA",
        )

        apparent_import_l3 = self._number(
            values,
            "1-0:69.7.0",
            target_unit="kVA",
        )

        apparent_export_l1 = self._number(
            values,
            "1-0:30.7.0",
            target_unit="kVA",
        )

        apparent_export_l2 = self._number(
            values,
            "1-0:50.7.0",
            target_unit="kVA",
        )

        apparent_export_l3 = self._number(
            values,
            "1-0:70.7.0",
            target_unit="kVA",
        )

        result.apparent_power_l1 = (
            apparent_import_l1
            - apparent_export_l1
        )

        result.apparent_power_l2 = (
            apparent_import_l2
            - apparent_export_l2
        )

        result.apparent_power_l3 = (
            apparent_import_l3
            - apparent_export_l3
        )

        result.apparent_power_total = (
            result.apparent_power_l1
            + result.apparent_power_l2
            + result.apparent_power_l3
        )

        if result.apparent_power_total == 0:

            apparent_import_total = self._number(
                values,
                "1-0:9.7.0",
                target_unit="kVA",
            )

            apparent_export_total = self._number(
                values,
                "1-0:10.7.0",
                target_unit="kVA",
            )

            result.apparent_power_total = (
                apparent_import_total
                - apparent_export_total
            )

        # --------------------------------------------------------------
        # Power factor
        # ESO telegram sends values such as 00998 = 0.998.
        # --------------------------------------------------------------

        result.power_factor_total = (
            self._power_factor(
                values,
                "1-0:13.7.0",
            )
        )

        result.power_factor_l1 = (
            self._power_factor(
                values,
                "1-0:33.7.0",
            )
        )

        result.power_factor_l2 = (
            self._power_factor(
                values,
                "1-0:53.7.0",
            )
        )

        result.power_factor_l3 = (
            self._power_factor(
                values,
                "1-0:73.7.0",
            )
        )

        # --------------------------------------------------------------
        # Frequency
        # --------------------------------------------------------------

        result.frequency = self._number(
            values,
            "1-0:14.7.0",
            target_unit="Hz",
        )

        # --------------------------------------------------------------
        # Energy
        # --------------------------------------------------------------

        result.energy_import_active = (
            self._number(
                values,
                "1-0:1.8.0",
                target_unit="kWh",
            )
        )

        result.energy_export_active = (
            self._number(
                values,
                "1-0:2.8.0",
                target_unit="kWh",
            )
        )

        # ESO telegram may omit total 2.8.0 and provide tariffs only.
        if result.energy_export_active == 0:

            result.energy_export_active = sum(
                self._number(
                    values,
                    obis,
                    target_unit="kWh",
                )
                for obis in (
                    "1-0:2.8.1",
                    "1-0:2.8.2",
                    "1-0:2.8.3",
                    "1-0:2.8.4",
                )
            )

        result.energy_import_reactive = (
            self._number(
                values,
                "1-0:3.8.0",
                target_unit="kvarh",
            )
        )

        result.energy_export_reactive = (
            self._number(
                values,
                "1-0:4.8.0",
                target_unit="kvarh",
            )
        )

        result.tariff1_import = self._number(
            values,
            "1-0:1.8.1",
            target_unit="kWh",
        )

        result.tariff2_import = self._number(
            values,
            "1-0:1.8.2",
            target_unit="kWh",
        )

        result.tariff3_import = self._number(
            values,
            "1-0:1.8.3",
            target_unit="kWh",
        )

        result.tariff4_import = self._number(
            values,
            "1-0:1.8.4",
            target_unit="kWh",
        )

        result.tariff1_export = self._number(
            values,
            "1-0:2.8.1",
            target_unit="kWh",
        )

        result.tariff2_export = self._number(
            values,
            "1-0:2.8.2",
            target_unit="kWh",
        )

        result.tariff3_export = self._number(
            values,
            "1-0:2.8.3",
            target_unit="kWh",
        )

        result.tariff4_export = self._number(
            values,
            "1-0:2.8.4",
            target_unit="kWh",
        )

        # --------------------------------------------------------------
        # Events
        # --------------------------------------------------------------

        result.power_failures = int(
            self._number(
                values,
                "0-0:96.7.21",
            )
        )

        return result

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_header(
        line: str,
        result: P1Telegram,
    ) -> None:
        """Parse ESO identification header."""

        # Example:
        # /ESO5\\253876809_C

        if line.startswith("/ESO"):

            result.manufacturer = "ESO"

            identifier = line[5:].strip(
                "\\"
            )

            if identifier:

                result.meter_id = identifier

    # ------------------------------------------------------------------
    # Value parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _split_value_and_unit(
        raw_value: str,
    ) -> tuple[str, str]:
        """Split '(value*unit)' contents."""

        value = raw_value.strip()

        if "*" not in value:
            return value, ""

        value_text, unit = value.split(
            "*",
            1,
        )

        return (
            value_text.strip(),
            unit.strip(),
        )

    @staticmethod
    def _text(
        values: dict[str, tuple[str, str]],
        obis: str,
    ) -> str:
        """Return raw text value."""

        item = values.get(
            obis
        )

        if item is None:
            return ""

        return item[0]

    @classmethod
    def _number(
        cls,
        values: dict[str, tuple[str, str]],
        obis: str,
        target_unit: str = "",
    ) -> float:
        """Return numeric value converted to the requested unit."""

        item = values.get(
            obis
        )

        if item is None:
            return 0.0

        value_text, source_unit = item

        try:

            value = float(
                value_text
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

        return cls._convert_unit(
            value=value,
            source_unit=source_unit,
            target_unit=target_unit,
        )

    @staticmethod
    def _convert_unit(
        *,
        value: float,
        source_unit: str,
        target_unit: str,
    ) -> float:
        """Convert common P1 engineering units."""

        source = source_unit.strip()
        target = target_unit.strip()

        if not target or source == target:
            return value

        conversions: dict[
            tuple[str, str],
            float,
        ] = {
            ("kV", "V"): 1000.0,
            ("V", "kV"): 0.001,

            ("kA", "A"): 1000.0,
            ("A", "kA"): 0.001,

            ("kHz", "Hz"): 1000.0,
            ("Hz", "kHz"): 0.001,

            ("W", "kW"): 0.001,
            ("kW", "W"): 1000.0,

            ("var", "kvar"): 0.001,
            ("kvar", "var"): 1000.0,

            ("VA", "kVA"): 0.001,
            ("kVA", "VA"): 1000.0,

            ("Wh", "kWh"): 0.001,
            ("kWh", "Wh"): 1000.0,

            ("varh", "kvarh"): 0.001,
            ("kvarh", "varh"): 1000.0,
        }

        factor = conversions.get(
            (
                source,
                target,
            )
        )

        if factor is None:

            # Unknown conversion: retain the original value instead
            # of silently corrupting the measurement.
            return value

        return value * factor

    @classmethod
    def _power_factor(
        cls,
        values: dict[str, tuple[str, str]],
        obis: str,
    ) -> float:
        """Parse ESO power factor representation."""

        value = cls._number(
            values,
            obis,
        )

        if abs(value) > 1.0:
            value /= 1000.0

        return value