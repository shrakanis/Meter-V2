"""
modbus/client_manager.py

Energy Monitor V2

Shared Modbus client manager.
"""

from __future__ import annotations

from threading import Lock

from common.enums import Protocol
from database.models import Meter
from modbus.clients.base import BaseClient
from modbus.clients.rtu import RTUClient
from modbus.clients.rtu_tcp import RTUOverTCPClient
from modbus.clients.tcp import TCPClient


class ClientManager:
    """
    Creates and caches shared Modbus clients.

    Devices using the same physical connection share one client.
    """

    def __init__(self) -> None:

        self._clients: dict[str, BaseClient] = {}
        self._lock = Lock()

    # ---------------------------------------------------------
    # Client key
    # ---------------------------------------------------------

    def _key(
        self,
        meter: Meter,
    ) -> str:

        if meter.protocol == Protocol.TCP:

            return (
                f"tcp:"
                f"{meter.address}:"
                f"{meter.port}:"
                f"{meter.timeout}"
            )

        if meter.protocol == Protocol.RTU_OVER_TCP:

            return (
                f"rtu-over-tcp:"
                f"{meter.address}:"
                f"{meter.port}:"
                f"{meter.timeout}"
            )

        if meter.protocol == Protocol.RTU:

            return (
                f"rtu:"
                f"{meter.serial_port}:"
                f"{meter.baudrate}:"
                f"{meter.bytesize}:"
                f"{meter.parity}:"
                f"{meter.stopbits}:"
                f"{meter.timeout}"
            )

        raise ValueError(
            f"Unsupported protocol: {meter.protocol}"
        )

    # ---------------------------------------------------------
    # Create client
    # ---------------------------------------------------------

    def _create(
        self,
        meter: Meter,
    ) -> BaseClient:

        if meter.protocol == Protocol.TCP:

            return TCPClient(
                host=meter.address,
                port=meter.port,
                timeout=meter.timeout,
            )

        if meter.protocol == Protocol.RTU:

            return RTUClient(
                port=meter.serial_port,
                baudrate=meter.baudrate,
                bytesize=meter.bytesize,
                parity=meter.parity,
                stopbits=meter.stopbits,
                timeout=meter.timeout,
            )

        if meter.protocol == Protocol.RTU_OVER_TCP:

            return RTUOverTCPClient(
                host=meter.address,
                port=meter.port,
                timeout=meter.timeout,
            )

        raise ValueError(
            f"Unsupported protocol: {meter.protocol}"
        )

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    def get_client(
        self,
        meter: Meter,
    ) -> BaseClient:

        key = self._key(meter)

        with self._lock:

            client = self._clients.get(key)

            if client is None:

                client = self._create(meter)

                self._clients[key] = client

            return client

    # ---------------------------------------------------------
    # Close one
    # ---------------------------------------------------------

    def close(
        self,
        meter: Meter,
    ) -> None:

        key = self._key(meter)

        with self._lock:

            client = self._clients.pop(
                key,
                None,
            )

        if client is not None:

            try:
                client.disconnect()
            except Exception:
                pass

    # ---------------------------------------------------------
    # Close all
    # ---------------------------------------------------------

    def close_all(self) -> None:

        with self._lock:

            clients = list(
                self._clients.values()
            )

            self._clients.clear()

        for client in clients:

            try:
                client.disconnect()
            except Exception:
                pass

    def __len__(self) -> int:

        with self._lock:
            return len(self._clients)