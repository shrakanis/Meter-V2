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

    - Connect to InfluxDB
    - Write measurements
    - Query history (later)
    - Health check
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

        if enabled:
            self.connect()

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def org(self) -> str:
        return self._org

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def connect(self) -> None:
        """
        Connect to InfluxDB.
        """

        try:

            self._client = InfluxDBClient(
                url=self._url,
                token=self._token,
                org=self._org,
            )

            self._write_api = self._client.write_api(
                write_options=SYNCHRONOUS,
            )

            logger.info(
                "Connected to InfluxDB (%s)",
                self._url,
            )

        except Exception:

            logger.exception(
                "Cannot connect to InfluxDB",
            )

            self._client = None
            self._write_api = None

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def connected(self) -> bool:
        """
        Return True if connected.
        """

        return (
            self._client is not None
            and self._write_api is not None
        )

    # ---------------------------------------------------------
    # Close
    # ---------------------------------------------------------

    def close(self) -> None:
        """
        Close client.
        """

        if self._client is None:
            return

        try:

            self._client.close()

        finally:

            self._client = None
            self._write_api = None

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------

    def write(
        self,
        point: Point,
    ) -> bool:
        """
        Write one point.

        Returns
        -------
        bool
            True if successful.
        """

        if not self.connected():
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
                "InfluxDB write failed",
            )

            return False

    # ---------------------------------------------------------
    # Health
    # ---------------------------------------------------------

    def ping(self) -> bool:
        """
        Ping server.
        """

        if self._client is None:
            return False

        try:

            return self._client.ping()

        except Exception:

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
        Create Point().
        """

        point = Point(
            measurement,
        )

        if tags:

            for key, value in tags.items():

                point.tag(
                    key,
                    str(value),
                )

        if fields:

            for key, value in fields.items():

                if value is None:
                    continue

                point.field(
                    key,
                    value,
                )

        return point