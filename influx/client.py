"""
influx/client.py

Energy Monitor V2

InfluxDB v2 client.
"""

from __future__ import annotations

import logging
from typing import Any

from influxdb_client import (
    InfluxDBClient,
    Point,
    WritePrecision,
)
from influxdb_client.client.write_api import SYNCHRONOUS


logger = logging.getLogger(__name__)


class InfluxClient:
    """
    Wrapper around influxdb-client.

    Responsibilities
    ----------------
    * Connect to InfluxDB
    * Write measurement points
    * Provide access to the query client
    * Check server health
    """

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
        enabled: bool = True,
    ) -> None:

        self._enabled = enabled

        self._url = url
        self._token = token
        self._org = org
        self._bucket = bucket

        self._client: InfluxDBClient | None = None
        self._write_api = None

        if self._enabled:
            self.connect()

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Return whether InfluxDB support is enabled."""

        return self._enabled

    @property
    def url(self) -> str:
        """Return InfluxDB URL."""

        return self._url

    @property
    def bucket(self) -> str:
        """Return configured bucket."""

        return self._bucket

    @property
    def org(self) -> str:
        """Return configured organisation."""

        return self._org

    @property
    def client(self) -> InfluxDBClient | None:
        """
        Return the underlying InfluxDB client.

        Used by HistoryReader for Flux queries.
        """

        return self._client

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def connect(self) -> bool:
        """
        Connect to InfluxDB.

        Returns
        -------
        bool
            True if the client was created successfully.
        """

        if not self._enabled:
            return False

        self.close()

        try:

            self._client = InfluxDBClient(
                url=self._url,
                token=self._token,
                org=self._org,
                timeout=10_000,
            )

            self._write_api = self._client.write_api(
                write_options=SYNCHRONOUS,
            )

            logger.info(
                "InfluxDB client initialized: %s, org=%s, bucket=%s",
                self._url,
                self._org,
                self._bucket,
            )

            return True

        except Exception:

            logger.exception(
                "Cannot initialize InfluxDB client."
            )

            self._client = None
            self._write_api = None

            return False

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def connected(self) -> bool:
        """
        Return whether the local client is initialized.

        This does not perform a network request.
        """

        return (
            self._enabled
            and self._client is not None
            and self._write_api is not None
        )

    def ping(self) -> bool:
        """
        Check whether the InfluxDB server is reachable.
        """

        if not self._enabled:
            return False

        if self._client is None:
            return False

        try:

            return bool(
                self._client.ping()
            )

        except Exception:

            return False

    # ---------------------------------------------------------
    # Close
    # ---------------------------------------------------------

    def close(self) -> None:
        """
        Close the InfluxDB client.
        """

        write_api = self._write_api
        client = self._client

        self._write_api = None
        self._client = None

        if write_api is not None:

            try:
                write_api.close()
            except Exception:
                logger.debug(
                    "InfluxDB write API close failed.",
                    exc_info=True,
                )

        if client is not None:

            try:
                client.close()
            except Exception:
                logger.debug(
                    "InfluxDB client close failed.",
                    exc_info=True,
                )

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------

    def write(
        self,
        point: Point,
    ) -> bool:
        """
        Write one point to InfluxDB.

        Recorder errors do not propagate to DeviceManager.
        """

        if not self._enabled:
            return False

        if not self.connected():
            self.connect()

        if self._write_api is None:
            return False

        try:

            self._write_api.write(
                bucket=self._bucket,
                org=self._org,
                record=point,
                write_precision=WritePrecision.S,
            )

            return True

        except Exception:

            logger.exception(
                "InfluxDB write failed."
            )

            return False

    # ---------------------------------------------------------
    # Point helper
    # ---------------------------------------------------------

    @staticmethod
    def point(
        measurement: str,
        tags: dict[str, Any] | None = None,
        fields: dict[str, Any] | None = None,
    ) -> Point:
        """
        Create an InfluxDB Point.
        """

        point = Point(
            measurement
        )

        if tags:

            for key, value in tags.items():

                if value is None:
                    continue

                point.tag(
                    key,
                    str(value),
                )

        if fields:

            for key, value in fields.items():

                if value is None:
                    continue

                if isinstance(value, bool):
                    value = int(value)

                point.field(
                    key,
                    value,
                )

        return point