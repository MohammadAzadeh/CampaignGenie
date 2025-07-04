from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("campaigns.db")


@contextmanager
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # For SQLite ≥ 3.38 you can enable JSON functions if you plan to store JSON
    # conn.execute("PRAGMA compile_options;")  # check JSON1 support
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
                id               INTEGER  PRIMARY KEY AUTOINCREMENT,
                advertiser_id    INTEGER  NOT NULL,
                business_name    TEXT     NOT NULL,
                business_type    TEXT     NOT NULL,
                target_audience  TEXT     NOT NULL,
                locations        TEXT     NOT NULL,  -- store JSON array or comma-sep
                daily_budget     INTEGER  NOT NULL,
                total_budget     INTEGER  NOT NULL,
                landing_address  TEXT     NOT NULL,
                landing_type     TEXT     NOT NULL,
                status           TEXT     NOT NULL,
                created_at       TEXT     NOT NULL
            )
            """,
        )
        conn.commit()
