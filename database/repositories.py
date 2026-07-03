"""
database/repositories.py

Energy Monitor V2

Version: 1.0.0
"""

from __future__ import annotations

from common.enums import Protocol
from database.db import Database
from database.models import Meter


class MeterRepository:
    """Energy meter repository."""

    def __init__(self, database: Database):

        self.database = database

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> list[Meter]:

        rows = self.database.query(
            """
            SELECT *
            FROM meters
            ORDER BY id
            """
        )

        meters = []

        for row in rows:

            meters.append(self._row_to_meter(row))

        return meters

    def get_by_id(self, meter_id: int) -> Meter | None:

        row = self.database.query_one(
            """
            SELECT *
            FROM meters
            WHERE id = ?
            """,
            (meter_id,),
        )

        if row is None:
            return None

        return self._row_to_meter(row)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add(self, meter: Meter) -> int:

        cursor = self.database.execute(
            """
            INSERT INTO meters(

                name,
                enabled,
                driver,
                protocol,
                address,
                port,
                slave,
                ct,
                pt,
                location,
                description

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meter.name,
                int(meter.enabled),
                meter.driver,
                int(meter.protocol),
                meter.address,
                meter.port,
                meter.slave,
                meter.ct,
                meter.pt,
                meter.location,
                meter.description,
            ),
        )

        meter.id = cursor.lastrowid

        return meter.id

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, meter: Meter) -> None:

        self.database.execute(
            """
            UPDATE meters

            SET

                name=?,
                enabled=?,
                driver=?,
                protocol=?,
                address=?,
                port=?,
                slave=?,
                ct=?,
                pt=?,
                location=?,
                description=?

            WHERE id=?
            """,
            (
                meter.name,
                int(meter.enabled),
                meter.driver,
                int(meter.protocol),
                meter.address,
                meter.port,
                meter.slave,
                meter.ct,
                meter.pt,
                meter.location,
                meter.description,
                meter.id,
            ),
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, meter_id: int) -> None:

        self.database.execute(
            """
            DELETE FROM meters
            WHERE id = ?
            """,
            (meter_id,),
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_meter(row) -> Meter:

        return Meter(

            id=row["id"],

            name=row["name"],

            enabled=bool(row["enabled"]),

            driver=row["driver"],

            protocol=Protocol(row["protocol"]),

            address=row["address"],

            port=row["port"],

            slave=row["slave"],

            ct=row["ct"],

            pt=row["pt"],

            location=row["location"] or "",

            description=row["description"] or "",

        )