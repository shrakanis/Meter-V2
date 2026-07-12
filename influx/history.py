"""
influx/history.py

Energy Monitor V2

History reader for InfluxDB.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from influxdb_client import InfluxDBClient

logger = logging.getLogger(__name__)


class HistoryReader:
    """
    Reads historical measurements from InfluxDB.

    Supported ranges
    ----------------

    1h
    24h
    7d
    30d
    custom
    """

    _RANGES = {

        "1h": (

            "-1h",
            "10s",

        ),

        "24h": (

            "-24h",
            "1m",

        ),

        "7d": (

            "-7d",
            "10m",

        ),

        "30d": (

            "-30d",
            "1h",

        ),

    }

    def __init__(
        self,
        client: InfluxDBClient,
        bucket: str,
        org: str,
        measurement: str = "energy_monitor",
    ) -> None:

        self._client = client

        self._bucket = bucket

        self._org = org

        self._measurement = measurement

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @property
    def query_api(self):

        return self._client.query_api()

    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------

    def history(
        self,
        *,
        device_id: int,
        field: str,
        range_name: str = "1h",
        start: datetime | None = None,
        stop: datetime | None = None,
    ) -> dict[str, list[Any]]:
        """
        Read history.

        Returns
        -------
        {
            labels: [],
            values: [],
        }
        """

        if range_name == "custom":

            if start is None or stop is None:

                raise ValueError(
                    "Custom range requires start and stop."
                )

            flux = self._build_custom_query(

                device_id=device_id,

                field=field,

                start=start,

                stop=stop,

            )

        else:

            if range_name not in self._RANGES:

                raise ValueError(
                    f"Unsupported range '{range_name}'"
                )

            start_value, window = self._RANGES[
                range_name
            ]

            flux = self._build_query(

                device_id=device_id,

                field=field,

                start=start_value,

                window=window,

            )

        labels: list[str] = []

        values: list[float] = []

        try:

            tables = self.query_api.query(

                query=flux,

                org=self._org,

            )

            for table in tables:

                for record in table.records:

                    timestamp = (
                        record.get_time()
                    )

                    value = (
                        record.get_value()
                    )

                    labels.append(

                        timestamp.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                    )

                    values.append(
                        value
                    )

        except Exception:

            logger.exception(
                "InfluxDB history query failed."
            )

        return {

            "labels": labels,

            "values": values,

        }

    # ---------------------------------------------------------
    # Flux builders
    # ---------------------------------------------------------

    def _build_query(
        self,
        *,
        device_id: int,
        field: str,
        start: str,
        window: str,
    ) -> str:

        return f"""
from(bucket: "{self._bucket}")
|> range(start: {start})
|> filter(fn: (r) => r["_measurement"] == "{self._measurement}")
|> filter(fn: (r) => r["device_id"] == "{device_id}")
|> filter(fn: (r) => r["_field"] == "{field}")
|> aggregateWindow(
    every: {window},
    fn: mean,
    createEmpty: false,
)
|> yield(name: "history")
"""

    def _build_custom_query(
        self,
        *,
        device_id: int,
        field: str,
        start: datetime,
        stop: datetime,
    ) -> str:

        seconds = (
            stop - start
        ).total_seconds()

        if seconds <= 3600:

            window = "10s"

        elif seconds <= 86400:

            window = "1m"

        elif seconds <= 604800:

            window = "10m"

        else:

            window = "1h"

        return f"""
from(bucket: "{self._bucket}")
|> range(
    start: time(v: "{start.isoformat()}"),
    stop: time(v: "{stop.isoformat()}"),
)
|> filter(fn: (r) => r["_measurement"] == "{self._measurement}")
|> filter(fn: (r) => r["device_id"] == "{device_id}")
|> filter(fn: (r) => r["_field"] == "{field}")
|> aggregateWindow(
    every: {window},
    fn: mean,
    createEmpty: false,
)
|> yield(name: "history")
"""