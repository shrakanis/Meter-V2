"""
web/pages.py

Energy Monitor V2

HTML pages.
"""
from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    request,
    url_for,
    flash,
)

from common.enums import Protocol
from database.models import Meter
from web.forms import MeterForm

pages = Blueprint(
    "pages",
    __name__,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def device_manager():
    """
    Return DeviceManager instance.
    """

    return current_app.application.device_manager


def meter_repository():
    """
    Return MeterRepository instance.
    """

    return current_app.application.meters


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------

@pages.route("/")
def dashboard():

    manager = device_manager()

    return render_template(
        "dashboard.html",
        total=manager.count(),
        online=len(manager.online()),
        offline=len(manager.offline()),
        devices=manager.all(),   # <-- pridėti
    )


# ----------------------------------------------------------------------
# Meter list
# ----------------------------------------------------------------------

@pages.route("/meters")
def meters():

    manager = device_manager()

    return render_template(
        "meters.html",
        devices=manager.all(),
    )

# ----------------------------------------------------------------------
# Add meter
# ----------------------------------------------------------------------

@pages.route("/meters/add", methods=["GET", "POST"])
def add_meter():

    form = MeterForm()

    if form.validate_on_submit():

        meter = Meter(
            enabled=form.enabled.data,
            name=form.name.data,
            description=form.description.data,

            driver=form.driver.data,
            protocol=Protocol(form.protocol.data),

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

        repo = meter_repository()
        repo.add(meter)

        device_manager().reload()

        flash("Meter added successfully.", "success")

        return redirect(url_for("pages.meters"))

    return render_template(
        "meter_form.html",
        form=form,
        title="Add Meter",
    )

# ----------------------------------------------------------------------
# Edit meter
# ----------------------------------------------------------------------

@pages.route("/meters/<int:meter_id>/edit", methods=["GET", "POST"])
def edit_meter(meter_id: int):

    repo = meter_repository()

    meter = repo.get_by_id(meter_id)

    if meter is None:
        flash("Meter not found.", "danger")
        return redirect(url_for("pages.meters"))

    form = MeterForm(obj=meter)

    if form.validate_on_submit():

        meter.enabled = form.enabled.data
        meter.name = form.name.data
        meter.description = form.description.data

        meter.driver = form.driver.data
        meter.protocol = Protocol(form.protocol.data)

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

        repo.update(meter)

        device_manager().reload()

        flash("Meter updated successfully.", "success")

        return redirect(url_for("pages.meters"))

    return render_template(
        "meter_form.html",
        form=form,
        title="Edit Meter",
    )

# ----------------------------------------------------------------------
# Delete meter
# ----------------------------------------------------------------------

@pages.route("/meters/<int:meter_id>/delete", methods=["POST"])
def delete_meter(meter_id: int):

    repo = meter_repository()

    repo.delete(meter_id)

    device_manager().reload()

    flash("Meter deleted.", "success")

    return redirect(url_for("pages.meters"))