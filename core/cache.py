"""
core/cache.py

Live meter cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time


@dataclass
class LiveMeter:

    kw: float = 0.0

    monthly: float = 0.0

    proc: float = 0.0

    state: int = 3

    online: bool = False

    last_update: float = 0

    last_good_kw: float = 0.0


class LiveCache:

    def __init__(self):

        self._lock = Lock()

        self._meters: dict[int, LiveMeter] = {}

    # -------------------------------------------------------

    def get(self, meter_id: int) -> LiveMeter:

        with self._lock:

            if meter_id not in self._meters:

                self._meters[meter_id] = LiveMeter()

            return self._meters[meter_id]

    # -------------------------------------------------------

    def update_kw(self, meter_id: int, kw: float):

        with self._lock:

            meter = self.get(meter_id)

            meter.kw = kw

            meter.last_good_kw = kw

            meter.online = True

            meter.last_update = time()

    # -------------------------------------------------------

    def set_offline(self, meter_id: int):

        with self._lock:

            meter = self.get(meter_id)

            meter.online = False

    # -------------------------------------------------------

    def update_state(self, meter_id: int, state: int):

        with self._lock:

            self.get(meter_id).state = state

    # -------------------------------------------------------

    def update_proc(self, meter_id: int, proc: float):

        with self._lock:

            self.get(meter_id).proc = proc

    # -------------------------------------------------------

    def update_monthly(self, meter_id: int, value: float):

        with self._lock:

            self.get(meter_id).monthly = value


live_cache = LiveCache()