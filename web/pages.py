"""
web/pages.py

Energy Monitor V2

HTML pages and dashboard API.
"""

from __future__ import annotations

from typing import Any

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    url_for,
)

from common.enums import Protocol
from database.models import Meter
from modbus.device import Device
from web.forms import MeterForm


pages = Blueprint(
    "pages",
    __name__,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def device_manager():
    """Return DeviceManager instance."""

    return current_app.application.device_manager


def meter_repository():
    """Return MeterRepository instance."""

    return current_app.application.meters


def _number(value: Any) -> float | int | None:
    """Return a JSON-safe numeric value."""

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
    """Convert one runtime Device to dashboard JSON."""

    measurements = device.measurements

    return {
        "id": device.id,
        "name": device.name,
        "driver": device.driver,
        "protocol": (
            device.protocol.name
            if hasattr(device.protocol, "name")
            else str(device.protocol)
        ),
        "connected": device.connected,
        "state": (
            device.state.name
            if hasattr(device.state, "name")
            else str(device.state)
        ),
        "last_update": (
            device.last_update.isoformat(timespec="seconds")
            if device.last_update is not None
            else None
        ),
        "last_error": device.last_error,
        "response_time_ms": round(
            device.response_time * 1000.0,
            1,
        ),
        "voltage": {
            "average": _number(
                measurements.voltage.average
            ),
            "l1": _number(
                measurements.voltage.l1
            ),
            "l2": _number(
                measurements.voltage.l2
            ),
            "l3": _number(
                measurements.voltage.l3
            ),
        },
        "current": {
            "total": _number(
                measurements.current.total
            ),
            "average": _number(
                measurements.current.average
            ),
            "l1": _number(
                measurements.current.l1
            ),
            "l2": _number(
                measurements.current.l2
            ),
            "l3": _number(
                measurements.current.l3
            ),
        },
        "active_power": {
            "total": _number(
                measurements.active_power.total
            ),
            "l1": _number(
                measurements.active_power.l1
            ),
            "l2": _number(
                measurements.active_power.l2
            ),
            "l3": _number(
                measurements.active_power.l3
            ),
        },
        "reactive_power": {
            "total": _number(
                measurements.reactive_power.total
            ),
            "l1": _number(
                measurements.reactive_power.l1
            ),
            "l2": _number(
                measurements.reactive_power.l2
            ),
            "l3": _number(
                measurements.reactive_power.l3
            ),
        },
        "apparent_power": {
            "total": _number(
                measurements.apparent_power.total
            ),
            "l1": _number(
                measurements.apparent_power.l1
            ),
            "l2": _number(
                measurements.apparent_power.l2
            ),
            "l3": _number(
                measurements.apparent_power.l3
            ),
        },
        "power_factor": {
            "total": _number(
                measurements.power_factor.total
            ),
            "l1": _number(
                measurements.power_factor.l1
            ),
            "l2": _number(
                measurements.power_factor.l2
            ),
            "l3": _number(
                measurements.power_factor.l3
            ),
        },
        "frequency": _number(
            measurements.frequency
        ),
        "energy": {
            "import_active": _number(
                measurements.energy.import_active
            ),
            "export_active": _number(
                measurements.energy.export_active
            ),
            "import_reactive": _number(
                measurements.energy.import_reactive
            ),
            "export_reactive": _number(
                measurements.energy.export_reactive
            ),
        },
        "info": dict(device.info),
        "extra": dict(device.extra),
    }


def _get_runtime_device(
    device_id: int,
) -> Device:
    """Return runtime Device or raise HTTP 404."""

    manager = device_manager()

    for device in manager.all():
        if device.id == device_id:
            return device

    abort(404)


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------


@pages.route("/")
def dashboard():
    """Render factory overview dashboard."""

    manager = device_manager()
    devices = manager.all()

    return render_template(
        "dashboard.html",
        total=len(devices),
        online=sum(
            1
            for device in devices
            if device.connected
        ),
        offline=sum(
            1
            for device in devices
            if not device.connected
        ),
        devices=devices,
    )


@pages.route("/api/dashboard")
def dashboard_api():
    """Return current readings for all configured meters."""

    manager = device_manager()
    devices = manager.all()

    return jsonify(
        {
            "total": len(devices),
            "online": sum(
                1
                for device in devices
                if device.connected
            ),
            "offline": sum(
                1
                for device in devices
                if not device.connected
            ),
            "devices": [
                _device_payload(device)
                for device in devices
            ],
        }
    )


# ----------------------------------------------------------------------
# Device details
# ----------------------------------------------------------------------


@pages.route("/device/<int:device_id>")
def device_details(
    device_id: int,
):
    """Render detailed page for one runtime device."""

    device = _get_runtime_device(
        device_id
    )

    return render_template(
        "device.html",
        device=device,
    )


@pages.route("/api/device/<int:device_id>")
def device_api(
    device_id: int,
):
    """Return current readings for one runtime device."""

    device = _get_runtime_device(
        device_id
    )

    return jsonify(
        _device_payload(device)
    )


# ----------------------------------------------------------------------
# Meter list
# ----------------------------------------------------------------------


@pages.route("/meters")
def meters():
    """Render configured meter list."""

    manager = device_manager()

    return render_template(
        "meters.html",
        devices=manager.all(),
    )


# ----------------------------------------------------------------------
# Add meter
# ----------------------------------------------------------------------


@pages.route(
    "/meters/add",
    methods=["GET", "POST"],
)
def add_meter():
    """Add a meter."""

    form = MeterForm()

    if form.validate_on_submit():
        meter_type = form.meter_type.data

        driver = form.driver.data
        protocol = Protocol(form.protocol.data)

        if meter_type == "p1":

            driver = "p1"

            protocol = Protocol.RTU

        meter = Meter(

            enabled=form.enabled.data,

            name=form.name.data,
            description=form.description.data,

            meter_type=meter_type,

            driver=driver,

            protocol=protocol,

            address=form.address.data,
            port=form.port.data,

            serial_port=form.serial_port.data,
            baudrate=form.baudrate.data,
            bytesize=form.bytesize.data,
            parity=form.parity.data,
            stopbits=form.stopbits.data,

            slave=form.slave.data,

            timeout=form.timeout.data,

            ct=form.ct.data,
            pt=form.pt.data,
        )

        repository = meter_repository()
        repository.add(meter)

        device_manager().reload()

        flash(
            "Meter added successfully.",
            "success",
        )

        return redirect(
            url_for("pages.meters")
        )

    return render_template(
        "meter_form.html",
        form=form,
        title="Add Meter",
    )


# ----------------------------------------------------------------------
# Edit meter
# ----------------------------------------------------------------------


@pages.route(
    "/meters/<int:meter_id>/edit",
    methods=["GET", "POST"],
)
def edit_meter(
    meter_id: int,
):
    """Edit an existing meter."""

    repository = meter_repository()
    meter = repository.get_by_id(
        meter_id
    )

    if meter is None:
        flash(
            "Meter not found.",
            "danger",
        )

        return redirect(
            url_for("pages.meters")
        )

    form = MeterForm(
        obj=meter
    )

    if form.validate_on_submit():
        meter.enabled = form.enabled.data
        meter.name = form.name.data
        meter.description = form.description.data
        meter.meter_type = form.meter_type.data

        if meter.is_p1:

            meter.driver = "p1"

            meter.protocol = Protocol.RTU

        else:

            meter.driver = form.driver.data

            meter.protocol = Protocol(
                form.protocol.data
            )

        meter.address = form.address.data
        meter.port = form.port.data
        meter.serial_port = form.serial_port.data
        meter.baudrate = form.baudrate.data
        meter.bytesize = form.bytesize.data
        meter.parity = form.parity.data
        meter.stopbits = form.stopbits.data
        meter.slave = form.slave.data
        meter.timeout = form.timeout.data
        meter.ct = form.ct.data
        meter.pt = form.pt.data

        repository.update(
            meter
        )

        device_manager().reload()

        flash(
            "Meter updated successfully.",
            "success",
        )

        return redirect(
            url_for("pages.meters")
        )

    return render_template(
        "meter_form.html",
        form=form,
        title="Edit Meter",
    )


# ----------------------------------------------------------------------
# Delete meter
# ----------------------------------------------------------------------


@pages.route(
    "/meters/<int:meter_id>/delete",
    methods=["POST"],
)
def delete_meter(
    meter_id: int,
):
    """Delete a meter."""

    repository = meter_repository()

    repository.delete(
        meter_id
    )

    device_manager().reload()

    flash(
        "Meter deleted.",
        "success",
    )

    return redirect(
        url_for("pages.meters")
    )