from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from database.models import Meter


@dataclass(slots=True)
class Device:
    """Gyvas skaitiklio objektas."""

    meter: Meter

    # Būsena
    online: bool = False
    last_update: datetime | None = None
    last_error: str = ""

    # Įtampos
    voltage_l1: float = 0.0
    voltage_l2: float = 0.0
    voltage_l3: float = 0.0

    # Srovės
    current_l1: float = 0.0
    current_l2: float = 0.0
    current_l3: float = 0.0

    # Galia
    kw: float = 0.0
    kvar: float = 0.0
    kva: float = 0.0

    # Energija
    kwh_import: float = 0.0
    kwh_export: float = 0.0

    # Kita
    pf: float = 0.0
    freq: float = 0.0

    # Temperatūra (jei skaitiklis palaiko)
    temperature: float = 0.0

    # Driver'is gali čia laikyti savo duomenis
    cache: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.meter.name

    @property
    def id(self) -> int:
        return self.meter.id

    def update_time(self):
        self.last_update = datetime.now()

    def set_online(self):
        self.online = True
        self.last_error = ""
        self.update_time()

    def set_offline(self, error: str = ""):
        self.online = False
        self.last_error = error