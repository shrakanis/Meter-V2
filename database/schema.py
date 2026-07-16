"""
database/schema.py

Energy Monitor V2

Database schema and migrations.
"""

from __future__ import annotations

import sqlite3


SCHEMA_VERSION = 2


def create_schema(
    connection: sqlite3.Connection,
) -> None:
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
    # Users
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,

            role INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL
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

            enabled INTEGER NOT NULL DEFAULT 1,

            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',

            meter_type TEXT NOT NULL DEFAULT 'modbus',

            driver TEXT NOT NULL,
            protocol INTEGER NOT NULL,

            address TEXT,
            port INTEGER DEFAULT 502,

            serial_port TEXT,
            baudrate INTEGER DEFAULT 9600,
            bytesize INTEGER DEFAULT 8,
            parity TEXT DEFAULT 'N',
            stopbits INTEGER DEFAULT 1,

            slave INTEGER NOT NULL DEFAULT 1,

            timeout REAL NOT NULL DEFAULT 1.0,

            ct REAL NOT NULL DEFAULT 1.0,
            pt REAL NOT NULL DEFAULT 1.0

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

    # ------------------------------------------------------------------
    # Schema version
    # ------------------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_info (
            version INTEGER NOT NULL
        )
        """
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM schema_info
        """
    )

    if cursor.fetchone()[0] == 0:

        cursor.execute(
            """
            INSERT INTO schema_info(version)
            VALUES(?)
            """,
            (1,),
        )

    connection.commit()


def get_schema_version(
    connection: sqlite3.Connection,
) -> int:
    """Return current schema version."""

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT version
            FROM schema_info
            LIMIT 1
            """
        )

    except sqlite3.OperationalError:

        return 0

    row = cursor.fetchone()

    if row is None:
        return 0

    return int(
        row[0]
    )


def column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> bool:
    """Return whether a table column exists."""

    cursor = connection.cursor()

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    return any(
        row[1] == column_name
        for row in columns
    )


def set_schema_version(
    connection: sqlite3.Connection,
    version: int,
) -> None:
    """Update current schema version."""

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM schema_info
        """
    )

    cursor.execute(
        """
        INSERT INTO schema_info(version)
        VALUES(?)
        """,
        (version,),
    )


def migrate(
    connection: sqlite3.Connection,
) -> None:
    """Apply database migrations."""

    version = get_schema_version(
        connection
    )

    # ------------------------------------------------------------------
    # Version 1 -> Version 2
    # Add meter_type column for Modbus / P1 support
    # ------------------------------------------------------------------

    if version < 2:

        if not column_exists(
            connection,
            "meters",
            "meter_type",
        ):

            connection.execute(
                """
                ALTER TABLE meters
                ADD COLUMN meter_type
                TEXT NOT NULL
                DEFAULT 'modbus'
                """
            )

        connection.execute(
            """
            UPDATE meters
            SET meter_type='modbus'
            WHERE meter_type IS NULL
               OR TRIM(meter_type)=''
            """
        )

        set_schema_version(
            connection,
            2,
        )

        version = 2

    # ------------------------------------------------------------------
    # Final version check
    # ------------------------------------------------------------------

    if version != SCHEMA_VERSION:

        raise RuntimeError(
            "Unsupported database schema version: "
            f"{version}; expected {SCHEMA_VERSION}"
        )

    connection.commit()