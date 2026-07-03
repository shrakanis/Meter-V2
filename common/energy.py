"""
common/energy.py

Energy Monitor V2

Version: 1.0.0
"""

from dataclasses import dataclass


@dataclass(slots=True)
class Energy:
    """Energy measurements."""

    import_active: float = 0.0

    export_active: float = 0.0

    import_reactive: float = 0.0

    export_reactive: float = 0.0