# repos/settings_repo.py
from __future__ import annotations
from domain.protocols import DatabaseAdapter


class SettingsRepoImpl:
    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter

    def get(self, key: str, default: str | None = None) -> str | None:
        rows = self.adapter.execute("SELECT value FROM settings WHERE key = ?", (key,))
        if rows:
            return rows[0]["value"]
        return default

    def set(self, key: str, value: str) -> None:
        def _tx(conn):
            cur = conn.cursor()
            row = cur.execute("SELECT 1 FROM settings WHERE key = ?", (key,)).fetchone()
            if row:
                cur.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
            else:
                cur.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)", (key, value)
                )

        self.adapter.transaction(_tx)
