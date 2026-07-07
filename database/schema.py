"""
database/schema.py

Energy Monitor V2

Database schema and migrations.
"""

from __future__ import annotations

import sqlite3


SCHEMA_VERSION = 1


def create_schema(connection: sqlite3.Connection) -> None:
    """Create database schema."""

    cursor = connection.cursor()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT NOT NULL,
            active INTEGER DEFAULT 0
        )
        """
    )

    # ------------------------------------------------------------------
    # Meter models
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS meter_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,

            reg_kw INTEGER NOT NULL,
            reg_kwh INTEGER NOT NULL,

            meter_type INTEGER NOT NULL DEFAULT 1,
            transform REAL NOT NULL DEFAULT 1
        )
        """
    )

    # ------------------------------------------------------------------
    # Meters
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS meters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            ip TEXT NOT NULL,

            slave INTEGER NOT NULL,

            model_id INTEGER,

            meter_type INTEGER NOT NULL,

            reg_kw INTEGER NOT NULL,

            reg_kwh INTEGER NOT NULL,

            transform REAL NOT NULL DEFAULT 1,

            limit_kw REAL DEFAULT 0,

            state INTEGER DEFAULT 3,

            enabled INTEGER DEFAULT 1,

            pos_x INTEGER DEFAULT 100,

            pos_y INTEGER DEFAULT 100,

            description TEXT DEFAULT '',

            FOREIGN KEY(model_id)
                REFERENCES meter_models(id)
        )
        """
    )

    # ------------------------------------------------------------------
    # Monthly readings
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            meter_id INTEGER NOT NULL,

            reading REAL NOT NULL,

            created_at TEXT NOT NULL,

            FOREIGN KEY(meter_id)
                REFERENCES meters(id)
        )
        """
    )

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            created_at TEXT NOT NULL,

            level TEXT NOT NULL,

            module TEXT NOT NULL,

            message TEXT NOT NULL
        )
        """
    )

    connection.commit()