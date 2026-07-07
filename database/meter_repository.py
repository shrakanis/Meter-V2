"""
database/meter_repository.py

Energy Monitor V2
"""

from sqlite3 import Row

from database.db import db
from models.meter import Meter


class MeterRepository:

    @staticmethod
    def _row_to_meter(row: Row) -> Meter:
        return Meter(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            ip=row["ip"],
            slave=row["slave"],
            model_id=row["model_id"],
            meter_type=row["meter_type"],
            reg_kw=row["reg_kw"],
            reg_kwh=row["reg_kwh"],
            transform=row["transform"],
            limit_kw=row["limit_kw"],
            state=row["state"],
            enabled=bool(row["enabled"]),
            pos_x=row["pos_x"],
            pos_y=row["pos_y"],
        )

    # ------------------------------------------------------------

    def get_all(self) -> list[Meter]:

        rows = db.query_all(
            """
            SELECT *
            FROM meters
            ORDER BY id
            """
        )

        return [self._row_to_meter(r) for r in rows]

    # ------------------------------------------------------------

    def get(self, meter_id: int) -> Meter | None:

        row = db.query_one(
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

    # ------------------------------------------------------------

    def insert(self, meter: Meter):

        cur = db.execute(
            """
            INSERT INTO meters(

                name,
                description,

                ip,
                slave,

                model_id,
                meter_type,

                reg_kw,
                reg_kwh,

                transform,

                limit_kw,

                state,

                enabled,

                pos_x,
                pos_y

            )

            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)

            """,
            (
                meter.name,
                meter.description,

                meter.ip,
                meter.slave,

                meter.model_id,
                meter.meter_type,

                meter.reg_kw,
                meter.reg_kwh,

                meter.transform,

                meter.limit_kw,

                meter.state,

                int(meter.enabled),

                meter.pos_x,
                meter.pos_y,
            ),
        )

        meter.id = cur.lastrowid

        return meter

    # ------------------------------------------------------------

    def update(self, meter: Meter):

        db.execute(
            """
            UPDATE meters

            SET

            name=?,
            description=?,

            ip=?,
            slave=?,

            model_id=?,
            meter_type=?,

            reg_kw=?,
            reg_kwh=?,

            transform=?,

            limit_kw=?,

            state=?,

            enabled=?,

            pos_x=?,
            pos_y=?

            WHERE id=?

            """,
            (
                meter.name,
                meter.description,

                meter.ip,
                meter.slave,

                meter.model_id,
                meter.meter_type,

                meter.reg_kw,
                meter.reg_kwh,

                meter.transform,

                meter.limit_kw,

                meter.state,

                int(meter.enabled),

                meter.pos_x,
                meter.pos_y,

                meter.id,
            ),
        )

    # ------------------------------------------------------------

    def delete(self, meter_id: int):

        db.execute(
            """
            DELETE FROM meters
            WHERE id=?
            """,
            (meter_id,),
        )


meter_repository = MeterRepository()