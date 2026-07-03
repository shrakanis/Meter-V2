"""
database/db.py

SQLite database wrapper for Energy Monitor V2.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any


class Database:
    """Thread-safe SQLite database wrapper."""

    def __init__(self, db_file: str | Path):

        self.db_file = Path(db_file)

        self.db_file.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()

        self.connection = sqlite3.connect(
            self.db_file,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

        self._configure()

    # ------------------------------------------------------------------
    # SQLite configuration
    # ------------------------------------------------------------------

    def _configure(self) -> None:
        """Configure SQLite."""

        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self.connection.execute("PRAGMA temp_store = MEMORY")
        self.connection.execute("PRAGMA cache_size = -10000")

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> sqlite3.Cursor:
        """Execute SQL query."""

        with self._lock:

            cursor = self.connection.cursor()

            cursor.execute(sql, params)

            self.connection.commit()

            return cursor

    def executemany(
        self,
        sql: str,
        params: list[tuple[Any, ...]],
    ) -> sqlite3.Cursor:
        """Execute SQL query for multiple rows."""

        with self._lock:

            cursor = self.connection.cursor()

            cursor.executemany(sql, params)

            self.connection.commit()

            return cursor

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> list[sqlite3.Row]:
        """Return all rows."""

        with self._lock:

            cursor = self.connection.cursor()

            cursor.execute(sql, params)

            return cursor.fetchall()

    def query_one(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> sqlite3.Row | None:
        """Return first row."""

        with self._lock:

            cursor = self.connection.cursor()

            cursor.execute(sql, params)

            return cursor.fetchone()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def table_exists(self, table: str) -> bool:
        """Check if table exists."""

        row = self.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (table,),
        )

        return row is not None

    # ------------------------------------------------------------------
    # Transaction
    # ------------------------------------------------------------------

    def commit(self) -> None:
        """Commit transaction."""

        with self._lock:
            self.connection.commit()

    def rollback(self) -> None:
        """Rollback transaction."""

        with self._lock:
            self.connection.rollback()

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close database."""

        with self._lock:
            self.connection.close()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "Database":

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if exc_type:
            self.rollback()
        else:
            self.commit()

        self.close()