"""
bootstrap.py

Energy Monitor V2

Application bootstrap.
"""

from __future__ import annotations

from modbus.drivers.factory import DriverFactory
from modbus.drivers.sdm630 import SDM630Driver
from modbus.drivers.pro380 import PRO380Driver

import atexit
import logging

from flask import Flask

from database.db import Database
from database.repositories import MeterRepository

from modbus.device_manager import DeviceManager

from web.pages import pages

logger = logging.getLogger(__name__)


class Application:
    """
    Main application container.

    Holds all long-lived services.
    """

    def __init__(self) -> None:

        logger.info("Initializing application...")

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
        # Managers
        # ---------------------------------------------------------

        self.device_manager = DeviceManager(
            repository=self.meters
        )

    # -------------------------------------------------------------
    # Runtime
    # -------------------------------------------------------------

    def start(self) -> None:

        logger.info("Starting Device Manager...")

        self.device_manager.start()

    def stop(self) -> None:

        logger.info("Stopping Device Manager...")

        self.device_manager.stop()

        self.database.close()

def register_drivers() -> None:
    """Register all Modbus drivers."""

    drivers = (
        SDM630Driver,
        PRO380Driver,
    )

    for driver in drivers:
        if not DriverFactory.exists(driver.NAME):
            DriverFactory.register(driver)

    logger.info(
        "Registered drivers: %s",
        ", ".join(DriverFactory.names()),
    )

# ----------------------------------------------------------------------
# Flask factory
# ----------------------------------------------------------------------

def create_app() -> Flask:

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "EnergyMonitorV2"

    register_drivers()

    # ---------------------------------------------------------
    # Application container
    # ---------------------------------------------------------

    application = Application()

    application.start()

    app.application = application

    # ---------------------------------------------------------
    # Blueprints
    # ---------------------------------------------------------

    app.register_blueprint(pages)

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    atexit.register(application.stop)

    logger.info("Application ready.")

    return app