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
)

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