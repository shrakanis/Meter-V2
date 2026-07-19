"""
database/db.py

SQLite database manager.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from database.schema import create_schema, migrate


class Database:
    _instance = None

    def __new__(cls, db_path: str = "data/energy.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "data/energy.db"):
        if self._initialized:
            return

        self._initialized = True

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

        self._configure()

        create_schema(self.connection)
        migrate(self.connection)

    def _configure(self):

        cursor = self.connection.cursor()

        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")

        self.connection.commit()

    def execute(self, sql: str, params=()):
        cur = self.connection.cursor()
        cur.execute(sql, params)
        self.connection.commit()
        return cur

    def query_one(self, sql: str, params=()):
        cur = self.connection.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def query_all(self, sql: str, params=()):
        cur = self.connection.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def close(self):
        self.connection.close()


db = Database()