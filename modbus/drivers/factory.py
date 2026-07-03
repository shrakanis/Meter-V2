"""
modbus/drivers/factory.py

Energy Monitor V2

Driver factory.
"""

from __future__ import annotations

from typing import Type

from modbus.drivers.base import BaseDriver
from modbus.exceptions import DriverError


class DriverFactory:
    """
    Factory for Modbus drivers.
    """

    _drivers: dict[str, Type[BaseDriver]] = {}

    # ---------------------------------------------------------
    # Registration
    # ---------------------------------------------------------

    @classmethod
    def register(
        cls,
        driver: Type[BaseDriver],
    ) -> None:
        """
        Register driver class.
        """

        if not driver.NAME:
            raise DriverError(
                f"{driver.__name__} has empty NAME."
            )

        name = driver.NAME.lower()

        if name in cls._drivers:
            raise DriverError(
                f"Driver '{name}' already registered."
            )

        cls._drivers[name] = driver

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    @classmethod
    def get(
        cls,
        name: str,
    ) -> BaseDriver:
        """
        Return driver instance.
        """

        try:

            return cls._drivers[name.lower()]()

        except KeyError as ex:

            raise DriverError(
                f"Unknown driver '{name}'."
            ) from ex

    @classmethod
    def exists(
        cls,
        name: str,
    ) -> bool:

        return name.lower() in cls._drivers

    @classmethod
    def names(cls) -> list[str]:

        return sorted(cls._drivers.keys())

    @classmethod
    def count(cls) -> int:

        return len(cls._drivers)

    @classmethod
    def clear(cls) -> None:
        """
        Used by unit tests.
        """

        cls._drivers.clear()