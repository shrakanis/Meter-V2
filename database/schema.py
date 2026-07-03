"""
database/schema.py

Energy Monitor V2

Version: 1.2.0
"""

from database.db import Database

DATABASE_VERSION = 1


def create_schema(database: Database) -> None:
    """Create database schema."""

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    database.execute("""
        CREATE TABLE IF NOT EXISTS settings (

            key TEXT PRIMARY KEY,

            value TEXT

        )
    """)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    database.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL UNIQUE,

            password TEXT NOT NULL,

            admin INTEGER NOT NULL DEFAULT 0

        )
    """)

    # ------------------------------------------------------------------
    # Meters
    # ------------------------------------------------------------------

    database.execute("""
        CREATE TABLE IF NOT EXISTS meters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            enabled INTEGER NOT NULL DEFAULT 1,

            driver TEXT NOT NULL,

            protocol INTEGER NOT NULL,

            address TEXT NOT NULL,

            port INTEGER NOT NULL DEFAULT 502,

            baudrate INTEGER NOT NULL DEFAULT 9600,

            parity TEXT NOT NULL DEFAULT 'N',

            stopbits INTEGER NOT NULL DEFAULT 1,

            slave INTEGER NOT NULL DEFAULT 1,

            ct REAL NOT NULL DEFAULT 1,

            pt REAL NOT NULL DEFAULT 1,

            poll_interval REAL NOT NULL DEFAULT 1,

            timeout REAL NOT NULL DEFAULT 1,

            retries INTEGER NOT NULL DEFAULT 3,

            location TEXT,

            description TEXT

        )
    """)


def get_database_version(database: Database) -> int:
    """Return current database version."""

    if not database.table_exists("settings"):
        return 0

    row = database.query_one(
        """
        SELECT value
        FROM settings
        WHERE key = ?
        """,
        ("database_version",),
    )

    if row is None:
        return 0

    return int(row["value"])


def set_database_version(
    database: Database,
    version: int,
) -> None:
    """Save current database version."""

    database.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        (
            "database_version",
            str(version),
        ),
    )


def migrate(database: Database) -> None:
    """Create or upgrade database."""

    version = get_database_version(database)

    # ------------------------------------------------------------------
    # Version 1
    # ------------------------------------------------------------------

    if version < 1:

        create_schema(database)

        set_database_version(
            database,
            DATABASE_VERSION,
        )

        version = DATABASE_VERSION

    # ------------------------------------------------------------------
    # Future migrations
    # ------------------------------------------------------------------

    # if version < 2:
    #
    #     database.execute(...)
    #
    #     set_database_version(database, 2)
    #
    #     version = 2