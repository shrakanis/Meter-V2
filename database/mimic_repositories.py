"""
database/mimic_repositories.py

Energy Monitor V2

Repositories for mimic diagrams and widgets.
"""

from __future__ import annotations

from database.db import Database
from database.mimic_models import MimicDiagram, MimicWidget


class MimicDiagramRepository:
    """Mimic diagram repository."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def get_all(self) -> list[MimicDiagram]:
        rows = self.database.query_all(
            "SELECT * FROM mimic_diagrams ORDER BY name, id"
        )
        return [self._row_to_model(row) for row in rows]

    def get_by_id(self, diagram_id: int) -> MimicDiagram | None:
        row = self.database.query_one(
            "SELECT * FROM mimic_diagrams WHERE id=?",
            (diagram_id,),
        )
        return None if row is None else self._row_to_model(row)

    def add(self, diagram: MimicDiagram) -> int:
        cursor = self.database.execute(
            """
            INSERT INTO mimic_diagrams(
                name, description, background_image,
                canvas_width, canvas_height
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                diagram.name,
                diagram.description,
                diagram.background_image,
                diagram.canvas_width,
                diagram.canvas_height,
            ),
        )
        diagram.id = cursor.lastrowid
        return int(diagram.id)

    def update(self, diagram: MimicDiagram) -> None:
        self.database.execute(
            """
            UPDATE mimic_diagrams
            SET name=?, description=?, background_image=?,
                canvas_width=?, canvas_height=?
            WHERE id=?
            """,
            (
                diagram.name,
                diagram.description,
                diagram.background_image,
                diagram.canvas_width,
                diagram.canvas_height,
                diagram.id,
            ),
        )

    def delete(self, diagram_id: int) -> None:
        self.database.execute(
            "DELETE FROM mimic_diagrams WHERE id=?",
            (diagram_id,),
        )

    @staticmethod
    def _row_to_model(row) -> MimicDiagram:
        return MimicDiagram(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            background_image=row["background_image"] or "",
            canvas_width=int(row["canvas_width"] or 1600),
            canvas_height=int(row["canvas_height"] or 900),
        )


class MimicWidgetRepository:
    """Mimic widget repository."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def get_for_diagram(self, diagram_id: int) -> list[MimicWidget]:
        rows = self.database.query_all(
            """
            SELECT * FROM mimic_widgets
            WHERE diagram_id=?
            ORDER BY id
            """,
            (diagram_id,),
        )
        return [self._row_to_model(row) for row in rows]

    def get_by_id(self, widget_id: int) -> MimicWidget | None:
        row = self.database.query_one(
            "SELECT * FROM mimic_widgets WHERE id=?",
            (widget_id,),
        )
        return None if row is None else self._row_to_model(row)

    def add(self, widget: MimicWidget) -> int:
        cursor = self.database.execute(
            """
            INSERT INTO mimic_widgets(
                diagram_id, title, meter_id, measurement, widget_type,
                x, y, width, nominal_power, running_threshold,
                decimals, show_status, show_percent
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                widget.diagram_id,
                widget.title,
                widget.meter_id,
                widget.measurement,
                widget.widget_type,
                widget.x,
                widget.y,
                widget.width,
                widget.nominal_power,
                widget.running_threshold,
                widget.decimals,
                int(widget.show_status),
                int(widget.show_percent),
            ),
        )
        widget.id = cursor.lastrowid
        return int(widget.id)

    def update(self, widget: MimicWidget) -> None:
        self.database.execute(
            """
            UPDATE mimic_widgets
            SET title=?, meter_id=?, measurement=?, widget_type=?,
                x=?, y=?, width=?, nominal_power=?, running_threshold=?,
                decimals=?, show_status=?, show_percent=?
            WHERE id=? AND diagram_id=?
            """,
            (
                widget.title,
                widget.meter_id,
                widget.measurement,
                widget.widget_type,
                widget.x,
                widget.y,
                widget.width,
                widget.nominal_power,
                widget.running_threshold,
                widget.decimals,
                int(widget.show_status),
                int(widget.show_percent),
                widget.id,
                widget.diagram_id,
            ),
        )

    def delete(self, widget_id: int, diagram_id: int) -> None:
        self.database.execute(
            "DELETE FROM mimic_widgets WHERE id=? AND diagram_id=?",
            (widget_id, diagram_id),
        )

    @staticmethod
    def _row_to_model(row) -> MimicWidget:
        return MimicWidget(
            id=row["id"],
            diagram_id=row["diagram_id"],
            title=row["title"] or "",
            meter_id=row["meter_id"],
            measurement=row["measurement"] or "active_power.total",
            widget_type=row["widget_type"] or "equipment",
            x=float(row["x"] or 0.0),
            y=float(row["y"] or 0.0),
            width=float(row["width"] or 12.0),
            nominal_power=(
                None
                if row["nominal_power"] is None
                else float(row["nominal_power"])
            ),
            running_threshold=float(row["running_threshold"] or 0.0),
            decimals=int(row["decimals"] or 2),
            show_status=bool(row["show_status"]),
            show_percent=bool(row["show_percent"]),
        )
