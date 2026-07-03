"""
modbus/manager.py

Energy Monitor V2

Device manager.
"""

from __future__ import annotations

import logging
import threading
import time
from time import perf_counter

from database.repositories import MeterRepository

from modbus.client_manager import ClientManager
from modbus.device import Device
from modbus.drivers.factory import DriverFactory
from modbus.exceptions import ModbusError

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Loads all configured meters and polls them.

    Responsibilities:

    - Load meters
    - Create Device objects
    - Manage polling
    - Update device state
    - Handle communication errors
    """

    def __init__(
        self,
        repository: MeterRepository,
        poll_interval: float = 1.0,
    ) -> None:

        self._repository = repository

        self._poll_interval = poll_interval

        self._client_manager = ClientManager()

        self._devices: dict[int, Device] = {}

        self._running = False

        self._thread: threading.Thread | None = None

    # -------------------------------------------------------------
    # Loading
    # -------------------------------------------------------------

    def load(self) -> None:
        """
        Load enabled meters from database.
        """

        self._devices.clear()

        meters = self._repository.all()

        for meter in meters:

            if not meter.enabled:
                continue

            if meter.id is None:
                continue

            self._devices[meter.id] = Device(
                meter=meter,
            )

        logger.info(
            "Loaded %d devices.",
            len(self._devices),
        )

    def reload(self) -> None:
        """
        Reload configuration.
        """

        self.stop()

        self.load()

        self.start()

    # -------------------------------------------------------------
    # Access
    # -------------------------------------------------------------

    def get(
        self,
        meter_id: int,
    ) -> Device | None:

        return self._devices.get(meter_id)

    def all(self) -> list[Device]:

        return list(self._devices.values())

    def count(self) -> int:

        return len(self._devices)

    def online(self) -> list[Device]:

        return [
            d
            for d in self._devices.values()
            if d.connected
        ]

    def offline(self) -> list[Device]:

        return [
            d
            for d in self._devices.values()
            if not d.connected
        ]
    # -------------------------------------------------------------
    # Thread control
    # -------------------------------------------------------------

    def start(self) -> None:
        """
        Start polling thread.
        """

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._run,
            name="DeviceManager",
            daemon=True,
        )

        self._thread.start()

        logger.info("Device manager started.")

    def stop(self) -> None:
        """
        Stop polling thread.
        """

        if not self._running:
            return

        self._running = False

        if self._thread is not None:

            self._thread.join(timeout=5)

            self._thread = None

        self._client_manager.disconnect_all()

        logger.info("Device manager stopped.")

    # -------------------------------------------------------------
    # Poll loop
    # -------------------------------------------------------------

    def _run(self) -> None:
        """
        Main polling loop.
        """

        while self._running:

            cycle_start = perf_counter()

            for device in self._devices.values():

                self._poll_device(device)

            elapsed = perf_counter() - cycle_start

            delay = self._poll_interval - elapsed

            if delay > 0:

                time.sleep(delay)
        # -------------------------------------------------------------
    # Poll one device
    # -------------------------------------------------------------

    def _poll_device(
        self,
        device: Device,
    ) -> None:
        """
        Poll a single device.
        """

        start = perf_counter()

        try:

            # -----------------------------------------------------
            # Get communication client
            # -----------------------------------------------------

            client = self._client_manager.get(
                device.meter
            )

            # -----------------------------------------------------
            # Get driver
            # -----------------------------------------------------

            driver = DriverFactory.get(
                device.driver
            )

            # -----------------------------------------------------
            # Read device
            # -----------------------------------------------------

            driver.read(
                client=client,
                device=device,
            )

            # -----------------------------------------------------
            # Success
            # -----------------------------------------------------

            device.response_time = (
                perf_counter() - start
            )

            device.online()

        except ModbusError as ex:

            device.response_time = (
                perf_counter() - start
            )

            device.clear()

            device.error(str(ex))

            logger.warning(
                "[%s] %s",
                device.name,
                ex,
            )
    # -------------------------------------------------------------
    # Python helpers
    # -------------------------------------------------------------

    def __iter__(self):
        """
        Iterate over loaded devices.
        """

        return iter(self._devices.values())

    def __len__(self) -> int:

        return len(self._devices)

    def __contains__(
        self,
        meter_id: int,
    ) -> bool:

        return meter_id in self._devices

    def __repr__(self) -> str:

        return (
            f"DeviceManager("
            f"devices={len(self)}, "
            f"running={self._running})"
        )