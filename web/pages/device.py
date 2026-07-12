"""
web/pages/device.py

Energy Monitor V2

Single device page and API.
"""

from __future__ import annotations

from typing import Any

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
)

from modbus.device import Device


device_pages = Blueprint(
    "device",
    __name__,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def device_manager():
    """Return DeviceManager."""

    return current_app.application.device_manager


def _number(value: Any) -> float | int | None:
    """Convert value to JSON-safe number."""

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return value

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _device_payload(device: Device) -> dict[str, Any]:
    """
    Convert Device -> JSON.
    """

    m = device.measurements

    return {

        "id": device.id,
        "name": device.name,
        "driver": device.driver,
        "protocol": device.protocol.name,

        "connected": device.connected,

        "state": device.state.name,

        "response_time_ms": round(
            device.response_time * 1000,
            1,
        ),

        "last_update": (
            device.last_update.isoformat(timespec="seconds")
            if device.last_update
            else None
        ),

        "last_error": device.last_error,

        "voltage": {

            "average": _number(m.voltage.average),

            "l1": _number(m.voltage.l1),
            "l2": _number(m.voltage.l2),
            "l3": _number(m.voltage.l3),

        },

        "current": {

            "total": _number(m.current.total),

            "average": _number(m.current.average),

            "l1": _number(m.current.l1),
            "l2": _number(m.current.l2),
            "l3": _number(m.current.l3),

        },

        "active_power": {

            "total": _number(m.active_power.total),

            "l1": _number(m.active_power.l1),
            "l2": _number(m.active_power.l2),
            "l3": _number(m.active_power.l3),

        },

        "reactive_power": {

            "total": _number(m.reactive_power.total),

            "l1": _number(m.reactive_power.l1),
            "l2": _number(m.reactive_power.l2),
            "l3": _number(m.reactive_power.l3),

        },

        "apparent_power": {

            "total": _number(m.apparent_power.total),

            "l1": _number(m.apparent_power.l1),
            "l2": _number(m.apparent_power.l2),
            "l3": _number(m.apparent_power.l3),

        },

        "power_factor": {

            "total": _number(m.power_factor.total),

            "l1": _number(m.power_factor.l1),
            "l2": _number(m.power_factor.l2),
            "l3": _number(m.power_factor.l3),

        },

        "frequency": _number(
            m.frequency
        ),

        "energy": {

            "import_active": _number(
                m.energy.import_active
            ),

            "export_active": _number(
                m.energy.export_active
            ),

            "import_reactive": _number(
                m.energy.import_reactive
            ),

            "export_reactive": _number(
                m.energy.export_reactive
            ),

        },

        "info": dict(device.info),

        "extra": dict(device.extra),

    }


# ----------------------------------------------------------------------
# Find device
# ----------------------------------------------------------------------


def get_device(
    device_id: int,
) -> Device:
    """
    Return runtime device.

    Raises 404 if not found.
    """

    manager = device_manager()

    for device in manager.all():

        if device.id == device_id:
            return device

    abort(404)


# ----------------------------------------------------------------------
# HTML page
# ----------------------------------------------------------------------


@device_pages.route(
    "/device/<int:device_id>"
)
def device(
    device_id: int,
):
    """
    Device page.
    """

    return render_template(

        "device.html",

        device=get_device(
            device_id,
        ),

    )


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------


@device_pages.route(
    "/api/device/<int:device_id>"
)
def device_api(
    device_id: int,
):
    """
    Device JSON.
    """

    device = get_device(
        device_id,
    )

    return jsonify(

        _device_payload(
            device,
        )

    )