from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("campaigns.db")


@contextmanager
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    """Create tables if they don't exist (idempotent)."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS campaign_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_type TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                locations TEXT NOT NULL,
                daily_budget INTEGER NOT NULL,
                landing_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        )
        conn.commit()