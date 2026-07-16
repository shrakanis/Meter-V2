"""
influx/flux_builder.py

Energy Monitor V2

Flux query builder.
"""

from __future__ import annotations

from datetime import datetime

from common.measurements_registry import Measurement


class FluxBuilder:
    """
    Builds Flux queries.

    This class ONLY generates Flux strings.
    It never executes queries.
    """

    def __init__(
        self,
        bucket: str,
        measurement_name: str,
    ) -> None:

        self._bucket = bucket
        self._measurement = measurement_name

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def history(
        self,
        *,
        device_id: int,
        measurement: Measurement,
        start: str,
        window: str,
    ) -> str:
        """
        Build history query using relative time.

        Example:

            start="-24h"
        """

        return self._build_query(
            device_id=device_id,
            measurement=measurement,
            range_clause=f"range(start: {start})",
            window=window,
        )

    def custom(
        self,
        *,
        device_id: int,
        measurement: Measurement,
        start: datetime,
        stop: datetime,
        window: str,
    ) -> str:
        """
        Build custom history query.
        """

        return self._build_query(
            device_id=device_id,
            measurement=measurement,
            range_clause=(
                "range("
                f'start: time(v: "{start.isoformat()}"), '
                f'stop: time(v: "{stop.isoformat()}")'
                ")"
            ),
            window=window,
        )

    def live(
        self,
        *,
        device_id: int,
        measurement: Measurement,
        seconds: int = 60,
    ) -> str:
        """
        Build live query.

        Reads raw values from the last N seconds.
        """

        fields = self._field_filter(
            measurement,
        )

        return f"""
from(bucket: "{self._bucket}")
|> range(start: -{seconds}s)
|> filter(fn: (r) => r["_measurement"] == "{self._measurement}")
|> filter(fn: (r) => r["device_id"] == "{device_id}")
|> filter(fn: (r) => {fields})
|> sort(columns: ["_time"])
"""

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _field_filter(
        measurement: Measurement,
    ) -> str:
        """
        Create Flux OR filter for all datasets.
        """

        return " or ".join(
            f'r["_field"] == "{dataset.field}"'
            for dataset in measurement.datasets
        )

    def _build_query(
        self,
        *,
        device_id: int,
        measurement: Measurement,
        range_clause: str,
        window: str,
    ) -> str:
        """
        Internal history query builder.
        """

        fields = self._field_filter(
            measurement,
        )

        return f"""
from(bucket: "{self._bucket}")
|> {range_clause}
|> filter(fn: (r) => r["_measurement"] == "{self._measurement}")
|> filter(fn: (r) => r["device_id"] == "{device_id}")
|> filter(fn: (r) => {fields})
|> aggregateWindow(
    every: {window},
    fn: mean,
    createEmpty: false,
)
|> sort(columns: ["_time"])
"""