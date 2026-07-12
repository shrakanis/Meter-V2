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

from influx.recorder import MeasurementRecorder
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
    * Send successful measurements to the recorder
    """

    def __init__(
        self,
        repository: MeterRepository,
        poll_interval: float = 1.0,
        recorder: MeasurementRecorder | None = None,
    ) -> None:

        self._repository = repository

        self._poll_interval = poll_interval

        self._recorder = recorder

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
    # Recorder
    # -------------------------------------------------------------

    @property
    def recorder(self) -> MeasurementRecorder | None:
        """
        Return the configured measurement recorder.
        """

        return self._recorder

    def set_recorder(
        self,
        recorder: MeasurementRecorder | None,
    ) -> None:
        """
        Set or remove the measurement recorder.
        """

        self._recorder = recorder

    # -------------------------------------------------------------
    # Access
    # -------------------------------------------------------------

    def get(
        self,
        meter_id: int,
    ) -> Device | None:
        """
        Return one runtime device by meter ID.
        """

        with self._lock:

            return self._devices.get(
                meter_id
            )

    def all(self) -> list[Device]:
        """
        Return all runtime devices.
        """

        with self._lock:

            return list(
                self._devices.values()
            )

    def count(self) -> int:
        """
        Return number of runtime devices.
        """

        with self._lock:

            return len(
                self._devices
            )

    def online(self) -> list[Device]:
        """
        Return online devices.
        """

        with self._lock:

            return [
                device
                for device in self._devices.values()
                if device.connected
            ]

    def offline(self) -> list[Device]:
        """
        Return offline devices.
        """

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

            self._thread.join(
                timeout=5
            )

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

                devices = list(
                    self._devices.values()
                )

            for device in devices:

                if not self._running:
                    break

                self._poll_device(
                    device
                )

            elapsed = (
                perf_counter()
                - cycle_start
            )

            delay = (
                self._poll_interval
                - elapsed
            )

            if delay > 0:

                time.sleep(
                    delay
                )

    # -------------------------------------------------------------
    # Recorder helper
    # -------------------------------------------------------------

    def _record_device(
        self,
        device: Device,
    ) -> None:
        """
        Send one successful device snapshot to the recorder.

        Recorder failures must never interrupt Modbus polling.
        """

        recorder = self._recorder

        if recorder is None:
            return

        try:

            recorder.record(
                device
            )

        except Exception:

            logger.exception(
                "[%s] Unexpected recorder error",
                device.name,
            )

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
                    # Driver does not implement read_info().
                    #
                    pass

            # -------------------------------------------------
            # Read measurements
            # -------------------------------------------------

            driver.read(
                client=client,
                device=device,
            )

            # Response time must be updated before recording,
            # because it is written to InfluxDB as a field.
            device.response_time = (
                perf_counter()
                - start
            )

            device.online()

            # -------------------------------------------------
            # Record successful snapshot
            # -------------------------------------------------

            self._record_device(
                device
            )

            logger.debug(
                "[%s] %.1f ms",
                device.name,
                device.response_time * 1000.0,
            )

        except ModbusError as ex:

            device.response_time = (
                perf_counter()
                - start
            )

            device.clear()

            device.error(
                str(ex)
            )

            logger.warning(
                "[%s] %s",
                device.name,
                ex,
            )

        except Exception:

            device.response_time = (
                perf_counter()
                - start
            )

            logger.exception(
                "Unexpected error while polling '%s'",
                device.name,
            )

            device.clear()

            device.error(
                "Unexpected error"
            )

        finally:

            # Safety fallback in case an exception occurred before
            # response_time was assigned in one of the branches.
            if device.response_time < 0:

                device.response_time = (
                    perf_counter()
                    - start
                )

    # -------------------------------------------------------------
    # Python helpers
    # -------------------------------------------------------------

    def __iter__(self):

        with self._lock:

            return iter(
                list(
                    self._devices.values()
                )
            )

    def __len__(self) -> int:

        with self._lock:

            return len(
                self._devices
            )

    def __contains__(
        self,
        meter_id: int,
    ) -> bool:

        with self._lock:

            return (
                meter_id
                in self._devices
            )

    def __repr__(self) -> str:

        with self._lock:

            return (
                f"DeviceManager("
                f"devices={len(self._devices)}, "
                f"running={self._running}, "
                f"recorder={self._recorder is not None})"
            )