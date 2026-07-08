"""
database/repositories.py

Energy Monitor V2
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

        rows = self.database.query_all(
            """
            SELECT *
            FROM meters
            ORDER BY id
            """
        )

        return [
            self._row_to_meter(row)
            for row in rows
        ]

    def get_by_id(
        self,
        meter_id: int,
    ) -> Meter | None:

        row = self.database.query_one(
            """
            SELECT *
            FROM meters
            WHERE id=?
            """,
            (meter_id,),
        )

        if row is None:
            return None

        return self._row_to_meter(row)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add(
        self,
        meter: Meter,
    ) -> int:

        cursor = self.database.execute(
            """
            INSERT INTO meters(

                enabled,

                name,
                description,

                driver,
                protocol,

                address,
                port,

                serial_port,
                baudrate,
                bytesize,
                parity,
                stopbits,

                slave,

                timeout,

                ct,
                pt

            )

            VALUES(

                ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?

            )
            """,
            (
                int(meter.enabled),

                meter.name,
                meter.description,

                meter.driver,
                int(meter.protocol),

                meter.address,
                meter.port,

                meter.serial_port,
                meter.baudrate,
                meter.bytesize,
                meter.parity,
                meter.stopbits,

                meter.slave,

                meter.timeout,

                meter.ct,
                meter.pt,
            ),
        )

        meter.id = cursor.lastrowid

        return meter.id

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        meter: Meter,
    ) -> None:

        self.database.execute(
            """
            UPDATE meters

            SET

                enabled=?,

                name=?,
                description=?,

                driver=?,
                protocol=?,

                address=?,
                port=?,

                serial_port=?,
                baudrate=?,
                bytesize=?,
                parity=?,
                stopbits=?,

                slave=?,

                timeout=?,

                ct=?,
                pt=?

            WHERE id=?
            """,
            (
                int(meter.enabled),

                meter.name,
                meter.description,

                meter.driver,
                int(meter.protocol),

                meter.address,
                meter.port,

                meter.serial_port,
                meter.baudrate,
                meter.bytesize,
                meter.parity,
                meter.stopbits,

                meter.slave,

                meter.timeout,

                meter.ct,
                meter.pt,

                meter.id,
            ),
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        meter_id: int,
    ) -> None:

        self.database.execute(
            """
            DELETE FROM meters
            WHERE id=?
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

            enabled=bool(row["enabled"]),

            name=row["name"],
            description=row["description"] or "",

            driver=row["driver"],

            protocol=Protocol(row["protocol"]),

            address=row["address"] or "",
            port=row["port"],

            serial_port=row["serial_port"] or "",
            baudrate=row["baudrate"],
            bytesize=row["bytesize"],
            parity=row["parity"],
            stopbits=row["stopbits"],

            slave=row["slave"],

            timeout=row["timeout"],

            ct=row["ct"],
            pt=row["pt"],
        )