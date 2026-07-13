"""
bootstrap.py

Energy Monitor V2

Application bootstrap.
"""

from __future__ import annotations

import atexit
import logging
import os

from flask import Flask

from database.db import Database
from database.repositories import MeterRepository

from influx.client import InfluxClient
from influx.history import HistoryReader
from influx.recorder import MeasurementRecorder

from modbus.device_manager import DeviceManager
from modbus.drivers.factory import DriverFactory
from modbus.drivers.pro380 import PRO380Driver
from modbus.drivers.sdm630 import SDM630Driver

from web.history import history
from web.pages import pages


logger = logging.getLogger(__name__)


def environment_bool(
    name: str,
    default: bool = False,
) -> bool:
    """Read a boolean environment variable."""

    value = os.getenv(
        name
    )

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


class Application:
    """
    Main application container.

    Holds all long-lived services.
    """

    def __init__(self) -> None:

        logger.info(
            "Initializing application..."
        )

        # ---------------------------------------------------------
        # Database
        # ---------------------------------------------------------

        self.database = Database()

        # ---------------------------------------------------------
        # Repositories
        # ---------------------------------------------------------

        self.meters = MeterRepository(
            self.database
        )

        # ---------------------------------------------------------
        # InfluxDB configuration
        # ---------------------------------------------------------

        influx_enabled = environment_bool(
            "INFLUX_ENABLED",
            True,
        )

        influx_url = os.getenv(
            "INFLUX_URL",
            "http://127.0.0.1:8086",
        )

        influx_token = os.getenv(
            "INFLUX_TOKEN",
            "",
        )

        influx_org = os.getenv(
            "INFLUX_ORG",
            "Gamykla",
        )

        influx_bucket = os.getenv(
            "INFLUX_BUCKET",
            "Elektra",
        )

        self.influx = InfluxClient(
            url=influx_url,
            token=influx_token,
            org=influx_org,
            bucket=influx_bucket,
            enabled=influx_enabled,
        )

        # ---------------------------------------------------------
        # Measurement recorder
        # ---------------------------------------------------------

        self.recorder: MeasurementRecorder | None = None

        if (
            influx_enabled
            and self.influx.client is not None
        ):

            self.recorder = MeasurementRecorder(
                self.influx
            )

        # ---------------------------------------------------------
        # History reader
        # ---------------------------------------------------------

        self.history_reader: HistoryReader | None = None

        if (
            influx_enabled
            and self.influx.client is not None
        ):

            self.history_reader = HistoryReader(
                client=self.influx.client,
                bucket=influx_bucket,
                org=influx_org,
                measurement="meter",
            )

        # ---------------------------------------------------------
        # Managers
        # ---------------------------------------------------------

        self.device_manager = DeviceManager(
            repository=self.meters,
            recorder=self.recorder,
        )

    # -------------------------------------------------------------
    # Runtime
    # -------------------------------------------------------------

    def start(self) -> None:
        """Start application services."""

        logger.info(
            "Starting Device Manager..."
        )

        self.device_manager.start()

    def stop(self) -> None:
        """Stop application services."""

        logger.info(
            "Stopping application..."
        )

        self.device_manager.stop()

        self.influx.close()

        self.database.close()


# ----------------------------------------------------------------------
# Drivers
# ----------------------------------------------------------------------


def register_drivers() -> None:
    """Register all Modbus drivers."""

    drivers = (
        SDM630Driver,
        PRO380Driver,
    )

    for driver in drivers:

        if not DriverFactory.exists(
            driver.NAME
        ):

            DriverFactory.register(
                driver
            )

    logger.info(
        "Registered drivers: %s",
        ", ".join(
            DriverFactory.names()
        ),
    )


# ----------------------------------------------------------------------
# Flask factory
# ----------------------------------------------------------------------


def create_app() -> Flask:
    """Create and configure the Flask application."""

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    app = Flask(
        __name__
    )

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "EnergyMonitorV2",
    )

    register_drivers()

    # ---------------------------------------------------------
    # Application container
    # ---------------------------------------------------------

    application = Application()

    app.application = application

    # ---------------------------------------------------------
    # Blueprints
    # ---------------------------------------------------------

    app.register_blueprint(
        pages
    )

    app.register_blueprint(
        history
    )

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    atexit.register(
        application.stop
    )

    logger.info(
        "Application ready."
    )

    return app