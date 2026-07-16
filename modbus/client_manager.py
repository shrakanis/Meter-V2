"""
modbus/client_manager.py

Energy Monitor V2

Shared communication client manager.
"""

from __future__ import annotations

from threading import Lock
from typing import TypeAlias

from common.enums import Protocol
from database.models import Meter

from modbus.clients.base import BaseClient
from modbus.clients.rtu import RTUClient
from modbus.clients.rtu_tcp import RTUOverTCPClient
from modbus.clients.tcp import TCPClient

from p1.client import P1Client


CommunicationClient: TypeAlias = (
    BaseClient
    | P1Client
)


class ClientManager:
    """
    Creates and caches shared communication clients.

    Supported connections
    ---------------------
    - Modbus TCP
    - Modbus RTU
    - RTU over TCP
    - P1 serial

    Devices using the same physical connection share one client.
    """

    def __init__(self) -> None:

        self._clients: dict[
            str,
            CommunicationClient,
        ] = {}

        self._lock = Lock()

    # ---------------------------------------------------------
    # Client key
    # ---------------------------------------------------------

    def _key(
        self,
        meter: Meter,
    ) -> str:
        """
        Create a unique key for the physical connection.
        """

        if meter.is_p1:

            return (
                "p1:"
                f"{meter.serial_port}:"
                f"{meter.baudrate}:"
                f"{meter.bytesize}:"
                f"{meter.parity}:"
                f"{meter.stopbits}:"
                f"{meter.timeout}"
            )

        if meter.protocol == Protocol.TCP:

            return (
                "tcp:"
                f"{meter.address}:"
                f"{meter.port}:"
                f"{meter.timeout}"
            )

        if meter.protocol == Protocol.RTU_OVER_TCP:

            return (
                "rtu-over-tcp:"
                f"{meter.address}:"
                f"{meter.port}:"
                f"{meter.timeout}"
            )

        if meter.protocol == Protocol.RTU:

            return (
                "rtu:"
                f"{meter.serial_port}:"
                f"{meter.baudrate}:"
                f"{meter.bytesize}:"
                f"{meter.parity}:"
                f"{meter.stopbits}:"
                f"{meter.timeout}"
            )

        raise ValueError(
            "Unsupported communication configuration: "
            f"type={meter.normalized_meter_type}, "
            f"protocol={meter.protocol}"
        )

    # ---------------------------------------------------------
    # Create client
    # ---------------------------------------------------------

    def _create(
        self,
        meter: Meter,
    ) -> CommunicationClient:
        """
        Create a communication client for one meter.
        """

        if meter.is_p1:

            if not meter.serial_port:

                raise ValueError(
                    "P1 serial port is not configured."
                )

            return P1Client(
                port=meter.serial_port,
                baudrate=meter.baudrate,
                bytesize=meter.bytesize,
                parity=meter.parity,
                stopbits=meter.stopbits,
                timeout=meter.timeout,
            )

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
            "Unsupported communication configuration: "
            f"type={meter.normalized_meter_type}, "
            f"protocol={meter.protocol}"
        )

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    def get_client(
        self,
        meter: Meter,
    ) -> CommunicationClient:
        """
        Return an existing shared client or create a new one.
        """

        key = self._key(
            meter
        )

        with self._lock:

            client = self._clients.get(
                key
            )

            if client is None:

                client = self._create(
                    meter
                )

                self._clients[
                    key
                ] = client

            return client

    # ---------------------------------------------------------
    # Close one
    # ---------------------------------------------------------

    def close(
        self,
        meter: Meter,
    ) -> None:
        """
        Close and remove one cached client.
        """

        key = self._key(
            meter
        )

        with self._lock:

            client = self._clients.pop(
                key,
                None,
            )

        if client is None:
            return

        try:

            client.disconnect()

        except Exception:

            pass

    # ---------------------------------------------------------
    # Close all
    # ---------------------------------------------------------

    def close_all(self) -> None:
        """
        Close all cached communication clients.
        """

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

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def __len__(self) -> int:

        with self._lock:

            return len(
                self._clients
            )