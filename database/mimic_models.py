"""
database/mimic_models.py

Energy Monitor V2

Mimic diagram database models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MimicDiagram:
    """One background image based process diagram."""

    id: int | None = None
    name: str = ""
    description: str = ""
    background_image: str = ""
    canvas_width: int = 1600
    canvas_height: int = 900


@dataclass(slots=True)
class MimicWidget:
    """One live value card placed on a mimic diagram."""

    id: int | None = None
    diagram_id: int = 0
    title: str = ""
    meter_id: int | None = None
    measurement: str = "active_power.total"
    widget_type: str = "equipment"
    x: float = 10.0
    y: float = 10.0
    width: float = 12.0
    nominal_power: float | None = None
    running_threshold: float = 1.0
    decimals: int = 2
    show_status: bool = True
    show_percent: bool = True
