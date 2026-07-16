"""
web/history.py

Energy Monitor V2

History page and History API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
)

from influx.history import HistoryReader
from modbus.device import Device


history = Blueprint(
    "history",
    __name__,
)


# ----------------------------------------------------------------------
# History fields
# ----------------------------------------------------------------------


HISTORY_FIELDS: dict[str, dict[str, Any]] = {
    # ------------------------------------------------------------------
    # Voltage
    # ------------------------------------------------------------------

    "voltage_phases": {
        "title": "Voltage L1 / L2 / L3",
        "unit": "V",
        "decimals": 1,
        "fields": [
            {
                "field": "voltage_l1",
                "label": "L1",
            },
            {
                "field": "voltage_l2",
                "label": "L2",
            },
            {
                "field": "voltage_l3",
                "label": "L3",
            },
        ],
    },

    "voltage_l1": {
        "title": "Voltage L1",
        "unit": "V",
        "decimals": 1,
    },

    "voltage_l2": {
        "title": "Voltage L2",
        "unit": "V",
        "decimals": 1,
    },

    "voltage_l3": {
        "title": "Voltage L3",
        "unit": "V",
        "decimals": 1,
    },

    "voltage_average": {
        "title": "Average voltage",
        "unit": "V",
        "decimals": 1,
    },

    # ------------------------------------------------------------------
    # Current
    # ------------------------------------------------------------------

    "current_phases": {
        "title": "Current L1 / L2 / L3",
        "unit": "A",
        "decimals": 2,
        "fields": [
            {
                "field": "current_l1",
                "label": "L1",
            },
            {
                "field": "current_l2",
                "label": "L2",
            },
            {
                "field": "current_l3",
                "label": "L3",
            },
        ],
    },

    "current_l1": {
        "title": "Current L1",
        "unit": "A",
        "decimals": 2,
    },

    "current_l2": {
        "title": "Current L2",
        "unit": "A",
        "decimals": 2,
    },

    "current_l3": {
        "title": "Current L3",
        "unit": "A",
        "decimals": 2,
    },

    "current_total": {
        "title": "Total current",
        "unit": "A",
        "decimals": 2,
    },

    # ------------------------------------------------------------------
    # Active power
    # ------------------------------------------------------------------

    "active_power_phases": {
        "title": "Active power L1 / L2 / L3",
        "unit": "kW",
        "decimals": 2,
        "fields": [
            {
                "field": "active_power_l1",
                "label": "L1",
            },
            {
                "field": "active_power_l2",
                "label": "L2",
            },
            {
                "field": "active_power_l3",
                "label": "L3",
            },
        ],
    },

    "active_power_l1": {
        "title": "Active power L1",
        "unit": "kW",
        "decimals": 2,
    },

    "active_power_l2": {
        "title": "Active power L2",
        "unit": "kW",
        "decimals": 2,
    },

    "active_power_l3": {
        "title": "Active power L3",
        "unit": "kW",
        "decimals": 2,
    },

    "active_power_total": {
        "title": "Total active power",
        "unit": "kW",
        "decimals": 2,
    },

    # ------------------------------------------------------------------
    # Reactive power
    # ------------------------------------------------------------------

    "reactive_power_phases": {
        "title": "Reactive power L1 / L2 / L3",
        "unit": "kvar",
        "decimals": 2,
        "fields": [
            {
                "field": "reactive_power_l1",
                "label": "L1",
            },
            {
                "field": "reactive_power_l2",
                "label": "L2",
            },
            {
                "field": "reactive_power_l3",
                "label": "L3",
            },
        ],
    },

    "reactive_power_l1": {
        "title": "Reactive power L1",
        "unit": "kvar",
        "decimals": 2,
    },

    "reactive_power_l2": {
        "title": "Reactive power L2",
        "unit": "kvar",
        "decimals": 2,
    },

    "reactive_power_l3": {
        "title": "Reactive power L3",
        "unit": "kvar",
        "decimals": 2,
    },

    "reactive_power_total": {
        "title": "Total reactive power",
        "unit": "kvar",
        "decimals": 2,
    },

    # ------------------------------------------------------------------
    # Apparent power
    # ------------------------------------------------------------------

    "apparent_power_phases": {
        "title": "Apparent power L1 / L2 / L3",
        "unit": "kVA",
        "decimals": 2,
        "fields": [
            {
                "field": "apparent_power_l1",
                "label": "L1",
            },
            {
                "field": "apparent_power_l2",
                "label": "L2",
            },
            {
                "field": "apparent_power_l3",
                "label": "L3",
            },
        ],
    },

    "apparent_power_total": {
        "title": "Total apparent power",
        "unit": "kVA",
        "decimals": 2,
    },

    # ------------------------------------------------------------------
    # Power factor
    # ------------------------------------------------------------------

    "power_factor_phases": {
        "title": "Power factor L1 / L2 / L3",
        "unit": "",
        "decimals": 3,
        "fields": [
            {
                "field": "power_factor_l1",
                "label": "L1",
            },
            {
                "field": "power_factor_l2",
                "label": "L2",
            },
            {
                "field": "power_factor_l3",
                "label": "L3",
            },
        ],
    },

    "power_factor_total": {
        "title": "Power factor",
        "unit": "",
        "decimals": 3,
    },

    # ------------------------------------------------------------------
    # Other measurements
    # ------------------------------------------------------------------

    "frequency": {
        "title": "Frequency",
        "unit": "Hz",
        "decimals": 2,
    },

    "energy_import_active": {
        "title": "Imported active energy",
        "unit": "kWh",
        "decimals": 3,
    },

    "energy_export_active": {
        "title": "Exported active energy",
        "unit": "kWh",
        "decimals": 3,
    },

    "energy_import_reactive": {
        "title": "Imported reactive energy",
        "unit": "kvarh",
        "decimals": 3,
    },

    "energy_export_reactive": {
        "title": "Exported reactive energy",
        "unit": "kvarh",
        "decimals": 3,
    },

    "response_time_ms": {
        "title": "Response time",
        "unit": "ms",
        "decimals": 1,
    },
}


HISTORY_RANGES = {
    "1h",
    "24h",
    "7d",
    "30d",
    "custom",
}


DEFAULT_HISTORY_FIELD = "reactive_power_phases"
DEFAULT_HISTORY_RANGE = "1h"


# ----------------------------------------------------------------------
# Application helpers
# ----------------------------------------------------------------------


def application():
    """Return the Energy Monitor application container."""

    return current_app.application


def device_manager():
    """Return DeviceManager instance."""

    return application().device_manager


def history_reader() -> HistoryReader | None:
    """Return configured HistoryReader instance."""

    return application().history_reader


def get_device(
    device_id: int,
) -> Device:
    """Return runtime device or raise HTTP 404."""

    device = device_manager().get(
        device_id
    )

    if device is None:
        abort(404)

    return device


# ----------------------------------------------------------------------
# Request helpers
# ----------------------------------------------------------------------


def parse_datetime(
    value: str | None,
    parameter_name: str,
) -> datetime:
    """
    Parse an ISO-8601 datetime parameter.

    Supported examples:
        2026-07-14T15:30
        2026-07-14T15:30:00
        2026-07-14T12:30:00Z
        2026-07-14T12:30:00+00:00
    """

    if not value:
        raise ValueError(
            f"Missing '{parameter_name}' parameter."
        )

    normalized = value.strip()

    if normalized.endswith("Z"):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        return datetime.fromisoformat(
            normalized
        )

    except ValueError as ex:
        raise ValueError(
            f"Invalid '{parameter_name}' datetime."
        ) from ex


def error_response(
    message: str,
    status: int = 400,
):
    """Return a standard JSON error response."""

    return jsonify(
        {
            "ok": False,
            "error": message,
        }
    ), status


def is_multi_field(
    field_info: dict[str, Any],
) -> bool:
    """Return True when the selected item contains multiple fields."""

    fields = field_info.get(
        "fields"
    )

    return (
        isinstance(fields, list)
        and len(fields) > 0
    )


def count_numeric_values(
    values: list[Any],
) -> int:
    """Count non-null numeric dataset values."""

    count = 0

    for value in values:

        if value is None:
            continue

        if isinstance(
            value,
            (int, float),
        ):
            count += 1

    return count


# ----------------------------------------------------------------------
# History page
# ----------------------------------------------------------------------


@history.route(
    "/history/<int:device_id>"
)
def history_page(
    device_id: int,
):
    """Render the history page for one device."""

    device = get_device(
        device_id
    )

    return render_template(
        "history.html",
        device=device,
        history_fields=HISTORY_FIELDS,
        default_field=DEFAULT_HISTORY_FIELD,
        default_range=DEFAULT_HISTORY_RANGE,
    )


# ----------------------------------------------------------------------
# History API
# ----------------------------------------------------------------------


@history.route(
    "/api/history/<int:device_id>"
)
def history_api(
    device_id: int,
):
    """
    Return historical data for one device.

    A normal history field returns:

        labels
        values

    A grouped history field returns:

        labels
        datasets
    """

    device = get_device(
        device_id
    )

    selected_field = request.args.get(
        "field",
        DEFAULT_HISTORY_FIELD,
    ).strip()

    requested_range = request.args.get(
        "range",
        DEFAULT_HISTORY_RANGE,
    ).strip()

    start_value = request.args.get(
        "start"
    )

    stop_value = request.args.get(
        "stop"
    )

    if start_value or stop_value:
        range_name = "custom"
    else:
        range_name = requested_range

    if selected_field not in HISTORY_FIELDS:
        return error_response(
            "Unsupported history field: "
            f"{selected_field}"
        )

    if range_name not in HISTORY_RANGES:
        return error_response(
            "Unsupported history range: "
            f"{range_name}"
        )

    reader = history_reader()

    if reader is None:
        return error_response(
            "InfluxDB history is not configured.",
            503,
        )

    start: datetime | None = None
    stop: datetime | None = None

    if range_name == "custom":

        try:
            start = parse_datetime(
                start_value,
                "start",
            )

            stop = parse_datetime(
                stop_value,
                "stop",
            )

        except ValueError as ex:
            return error_response(
                str(ex)
            )

        if stop <= start:
            return error_response(
                "'stop' must be later than 'start'."
            )

    field_info = HISTORY_FIELDS[
        selected_field
    ]

    try:

        if is_multi_field(
            field_info
        ):

            field_definitions = field_info[
                "fields"
            ]

            influx_fields = [
                definition["field"]
                for definition in field_definitions
            ]

            result = reader.history_multi(
                device_id=device_id,
                fields=influx_fields,
                range_name=range_name,
                start=start,
                stop=stop,
            )

            raw_datasets = result.get(
                "datasets",
                [],
            )

            datasets_by_field = {
                dataset.get("field"): dataset
                for dataset in raw_datasets
            }

            datasets: list[
                dict[str, Any]
            ] = []

            samples = 0

            for definition in field_definitions:

                influx_field = definition[
                    "field"
                ]

                label = definition[
                    "label"
                ]

                raw_dataset = datasets_by_field.get(
                    influx_field,
                    {},
                )

                values = raw_dataset.get(
                    "values",
                    [],
                )

                samples = max(
                    samples,
                    count_numeric_values(
                        values
                    ),
                )

                datasets.append(
                    {
                        "field": influx_field,
                        "label": label,
                        "values": values,
                    }
                )

            return jsonify(
                {
                    "ok": True,
                    "multi": True,

                    "device": {
                        "id": device.id,
                        "name": device.name,
                    },

                    "field": selected_field,
                    "title": field_info["title"],
                    "unit": field_info["unit"],
                    "decimals": field_info["decimals"],
                    "range": range_name,

                    "labels": result.get(
                        "labels",
                        [],
                    ),

                    "datasets": datasets,

                    "samples": samples,
                }
            )

        result = reader.history(
            device_id=device_id,
            field=selected_field,
            range_name=range_name,
            start=start,
            stop=stop,
        )

    except ValueError as ex:
        return error_response(
            str(ex)
        )

    except Exception:
        current_app.logger.exception(
            "History query failed for device %s.",
            device_id,
        )

        return error_response(
            "InfluxDB history query failed.",
            500,
        )

    labels = result.get(
        "labels",
        [],
    )

    values = result.get(
        "values",
        [],
    )

    return jsonify(
        {
            "ok": True,
            "multi": False,

            "device": {
                "id": device.id,
                "name": device.name,
            },

            "field": selected_field,
            "title": field_info["title"],
            "unit": field_info["unit"],
            "decimals": field_info["decimals"],
            "range": range_name,

            "labels": labels,
            "values": values,

            "samples": count_numeric_values(
                values
            ),
        }
    )