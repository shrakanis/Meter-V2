"""
models/meter.py

Energy Monitor V2

Meter model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Meter:

    id: int | None = None

    # Basic
    name: str = ""
    description: str = ""

    # Communication
    ip: str = ""
    slave: int = 1

    # Meter type
    model_id: int | None = None
    meter_type: int = 1

    # Registers
    reg_kw: int = 24576
    reg_kwh: int = 20498

    transform: float = 1.0

    # Dashboard
    pos_x: int = 100
    pos_y: int = 100

    # Alarm
    limit_kw: float = 0

    # Runtime
    state: int = 3
    enabled: bool = True

    # Live values
    kw: float = 0.0
    monthly: float = 0.0
    proc: float = 0.0

    last_good_kw: float = 0.0

    online: bool = False