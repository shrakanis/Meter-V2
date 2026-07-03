"""
modbus/drivers/factory.py

Energy Monitor V2

Version: 1.0.0
"""

from __future__ import annotations

from modbus.drivers.base import BaseDriver


class DriverFactory:
    """Creates and caches driver instances."""

    _drivers: dict[str, BaseDriver] = {}

    @classmethod
    def register(
        cls,
        driver: BaseDriver,
    ) -> None:

        cls._drivers[driver.name.lower()] = driver

    @classmethod
    def get(
        cls,
        name: str,
    ) -> BaseDriver:

        key = name.lower()

        if key not in cls._drivers:

            raise KeyError(f"Driver '{name}' not registered.")

        return cls._drivers[key]

    @classmethod
    def registered(cls) -> list[str]:

        return sorted(cls._drivers.keys())