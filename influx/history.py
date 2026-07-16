"""
influx/history.py

Energy Monitor V2

History reader for InfluxDB.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Iterable

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
        measurement: str = "meter",
    ) -> None:

        self._client = client
        self._bucket = bucket
        self._org = org
        self._measurement = measurement

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def query_api(self):
        """Return InfluxDB query API."""

        return self._client.query_api()

    @staticmethod
    def _format_timestamp(
        timestamp: datetime,
    ) -> str:
        """
        Return ISO-8601 timestamp with timezone information.

        InfluxDB returns UTC timestamps. Keeping the timezone allows
        the browser to convert UTC automatically to local time.
        """

        value = timestamp.isoformat()

        if value.endswith("+00:00"):
            value = value[:-6] + "Z"

        return value

    @classmethod
    def _window_for_custom_range(
        cls,
        start: datetime,
        stop: datetime,
    ) -> str:
        """Return aggregation window for a custom range."""

        seconds = (
            stop - start
        ).total_seconds()

        if seconds <= 0:
            raise ValueError(
                "Stop time must be later than start time."
            )

        if seconds <= 3600:
            return "10s"

        if seconds <= 86400:
            return "1m"

        if seconds <= 604800:
            return "10m"

        return "1h"

    @classmethod
    def _range_values(
        cls,
        *,
        range_name: str,
        start: datetime | None,
        stop: datetime | None,
    ) -> tuple[str, str | None, str]:
        """
        Return Flux start, optional stop and aggregation window.
        """

        if range_name == "custom":

            if start is None or stop is None:
                raise ValueError(
                    "Custom range requires start and stop."
                )

            window = cls._window_for_custom_range(
                start,
                stop,
            )

            return (
                f'time(v: "{start.isoformat()}")',
                f'time(v: "{stop.isoformat()}")',
                window,
            )

        if range_name not in cls._RANGES:
            raise ValueError(
                f"Unsupported range '{range_name}'"
            )

        start_value, window = cls._RANGES[
            range_name
        ]

        return (
            start_value,
            None,
            window,
        )

    @staticmethod
    def _normalize_fields(
        fields: Iterable[str],
    ) -> list[str]:
        """Return unique, non-empty field names."""

        result: list[str] = []

        for field in fields:

            normalized = str(
                field
            ).strip()

            if not normalized:
                continue

            if normalized in result:
                continue

            result.append(
                normalized
            )

        if not result:
            raise ValueError(
                "At least one history field is required."
            )

        return result

    @staticmethod
    def _escape_flux_string(
        value: str,
    ) -> str:
        """Escape a value used inside a Flux string."""

        return (
            value
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

    # ------------------------------------------------------------------
    # Single field history
    # ------------------------------------------------------------------

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
        Read history for one field.

        Returns
        -------
        {
            "labels": [],
            "values": [],
        }
        """

        result = self.history_multi(
            device_id=device_id,
            fields=[
                field,
            ],
            range_name=range_name,
            start=start,
            stop=stop,
        )

        dataset = result[
            "datasets"
        ][0]

        return {
            "labels": result[
                "labels"
            ],
            "values": dataset[
                "values"
            ],
        }

    # ------------------------------------------------------------------
    # Multiple field history
    # ------------------------------------------------------------------

    def history_multi(
        self,
        *,
        device_id: int,
        fields: Iterable[str],
        range_name: str = "1h",
        start: datetime | None = None,
        stop: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Read multiple fields using one InfluxDB query.

        Values from all fields are aligned against one common timestamp
        list. A missing value at a timestamp is returned as None.

        Returns
        -------
        {
            "labels": [
                "2026-07-15T10:00:00Z",
                ...
            ],
            "datasets": [
                {
                    "field": "reactive_power_l1",
                    "values": [
                        2.5,
                        ...
                    ],
                },
                ...
            ],
        }
        """

        normalized_fields = (
            self._normalize_fields(
                fields
            )
        )

        start_value, stop_value, window = (
            self._range_values(
                range_name=range_name,
                start=start,
                stop=stop,
            )
        )

        flux = self._build_multi_query(
            device_id=device_id,
            fields=normalized_fields,
            start=start_value,
            stop=stop_value,
            window=window,
        )

        field_records: dict[
            str,
            dict[datetime, float],
        ] = {
            field: {}
            for field in normalized_fields
        }

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

                    raw_value = (
                        record.get_value()
                    )

                    field_name = (
                        record.get_field()
                    )

                    if timestamp is None:
                        continue

                    if raw_value is None:
                        continue

                    if field_name not in field_records:
                        continue

                    try:

                        value = float(
                            raw_value
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        continue

                    field_records[
                        field_name
                    ][
                        timestamp
                    ] = value

        except Exception:

            logger.exception(
                "InfluxDB multi-field history query failed."
            )

        timestamps = sorted(
            {
                timestamp
                for records in field_records.values()
                for timestamp in records
            }
        )

        labels = [
            self._format_timestamp(
                timestamp
            )
            for timestamp in timestamps
        ]

        datasets: list[
            dict[str, Any]
        ] = []

        for field_name in normalized_fields:

            values = [
                field_records[
                    field_name
                ].get(
                    timestamp
                )
                for timestamp in timestamps
            ]

            datasets.append(
                {
                    "field": field_name,
                    "values": values,
                }
            )

        return {
            "labels": labels,
            "datasets": datasets,
        }

    # ------------------------------------------------------------------
    # Flux builders
    # ------------------------------------------------------------------

    def _build_multi_query(
        self,
        *,
        device_id: int,
        fields: list[str],
        start: str,
        stop: str | None,
        window: str,
    ) -> str:
        """Build a Flux query for one or more fields."""

        escaped_bucket = (
            self._escape_flux_string(
                self._bucket
            )
        )

        escaped_measurement = (
            self._escape_flux_string(
                self._measurement
            )
        )

        escaped_device_id = (
            self._escape_flux_string(
                str(device_id)
            )
        )

        field_conditions = " or ".join(
            (
                'r["_field"] == '
                f'"{self._escape_flux_string(field)}"'
            )
            for field in fields
        )

        if stop is None:

            range_clause = (
                f"|> range(start: {start})"
            )

        else:

            range_clause = (
                "|> range(\n"
                f"    start: {start},\n"
                f"    stop: {stop},\n"
                ")"
            )

        return f"""
from(bucket: "{escaped_bucket}")
{range_clause}
|> filter(
    fn: (r) =>
        r["_measurement"] == "{escaped_measurement}"
)
|> filter(
    fn: (r) =>
        r["device_id"] == "{escaped_device_id}"
)
|> filter(
    fn: (r) =>
        {field_conditions}
)
|> aggregateWindow(
    every: {window},
    fn: mean,
    createEmpty: false,
)
|> sort(
    columns: [
        "_time",
        "_field",
    ]
)
|> yield(
    name: "history"
)
"""