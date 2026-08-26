# adapters/memory_adapter.py
from __future__ import annotations
import sqlite3
from typing import Any, Callable
from adapters.schema import SCHEMA_SQL


class InMemoryAdapter:
    """測試用：SQLite in-memory，共用生產 Schema。"""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def execute_many(self, sql: str, params_list: list[tuple]) -> None:
        with self.conn:
            self.conn.executemany(sql, params_list)

    def transaction(self, fn: Callable[[sqlite3.Connection], Any]) -> Any:
        with self.conn:
            return fn(self.conn)

    def last_row_id(self) -> int:
        return self.conn.lastrowid

    def close(self) -> None:
        self.conn.close()
