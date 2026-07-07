"""
modbus/device_manager.py

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
    Loads all configured meters and continuously polls them.

    Responsibilities
    ----------------
    * Load enabled meters from database
    * Create runtime Device objects
    * Poll all devices
    * Handle communication errors
    * Keep runtime state updated
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

        self._lock = threading.RLock()

    # -------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------

    def load(self) -> None:
        """
        Load enabled meters from database.
        """

        with self._lock:

            self._devices.clear()

            meters = self._repository.get_all()

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
        Reload configuration from database.
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

        with self._lock:

            return self._devices.get(meter_id)

    def all(self) -> list[Device]:

        with self._lock:

            return list(self._devices.values())

    def count(self) -> int:

        with self._lock:

            return len(self._devices)

    def online(self) -> list[Device]:

        with self._lock:

            return [
                device
                for device in self._devices.values()
                if device.connected
            ]

    def offline(self) -> list[Device]:

        with self._lock:

            return [
                device
                for device in self._devices.values()
                if not device.connected
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

        if not self._devices:
            self.load()

        self._running = True

        self._thread = threading.Thread(
            target=self._run,
            name="DeviceManager",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "Device manager started."
        )

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

        self._client_manager.close_all()

        logger.info(
            "Device manager stopped."
        )
    # -------------------------------------------------------------
    # Poll loop
    # -------------------------------------------------------------

    def _run(self) -> None:
        """
        Main polling loop.
        """

        while self._running:

            cycle_start = perf_counter()

            with self._lock:

                devices = list(self._devices.values())

            for device in devices:

                if not self._running:
                    break

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
        Poll one Modbus device.
        """

        start = perf_counter()

        try:

            # -------------------------------------------------
            # Shared Modbus client
            # -------------------------------------------------

            client = self._client_manager.get_client(
                device.meter
            )

            # -------------------------------------------------
            # Driver
            # -------------------------------------------------

            driver = DriverFactory.get(
                device.driver
            )

            # -------------------------------------------------
            # Static information (read once)
            # -------------------------------------------------

            if not device.has_info:

                try:

                    driver.read_info(
                        client=client,
                        device=device,
                    )

                except AttributeError:
                    #
                    # Driver does not implement read_info()
                    #
                    pass

            # -------------------------------------------------
            # Read measurements
            # -------------------------------------------------

            driver.read(
                client=client,
                device=device,
            )

            device.online()

            logger.debug(
                "[%s] %.1f ms",
                device.name,
                (perf_counter() - start) * 1000,
            )

        except ModbusError as ex:

            device.clear()

            device.error(str(ex))

            logger.warning(
                "[%s] %s",
                device.name,
                ex,
            )

        except Exception:

            logger.exception(
                "Unexpected error while polling '%s'",
                device.name,
            )

            device.clear()

            device.error(
                "Unexpected error"
            )

        finally:

            device.response_time = (
                perf_counter() - start
            )
    # -------------------------------------------------------------
    # Python helpers
    # -------------------------------------------------------------

    def __iter__(self):

        with self._lock:

            return iter(list(self._devices.values()))

    def __len__(self) -> int:

        with self._lock:

            return len(self._devices)

    def __contains__(
        self,
        meter_id: int,
    ) -> bool:

        with self._lock:

            return meter_id in self._devices

    def __repr__(self) -> str:

        with self._lock:

            return (
                f"DeviceManager("
                f"devices={len(self._devices)}, "
                f"running={self._running})"
            )