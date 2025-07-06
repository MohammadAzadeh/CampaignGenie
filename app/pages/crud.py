from __future__ import annotations

import argparse
import contextlib
import json
from datetime import datetime
import pathlib
import sqlite3
from typing import Any, Callable, ContextManager, Sequence

from pages.models import CampaignPlan, CampaignRequest

_DB_PATH = pathlib.Path(__file__).with_name("campaign_genie.db")


@contextlib.contextmanager
def get_connection() -> ContextManager[sqlite3.Connection]:
    """Return a *context manager* that yields a SQLite connection.

    We use `check_same_thread=False` so the same DB file can be accessed from
    FastAPI background threads *and* Jupyter notebooks without errors.
    """

    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


_CREATE_TABLES_SQL = {
    "campaign_requests": """
        CREATE TABLE IF NOT EXISTS campaign_requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            advertiser_id   INTEGER NOT NULL,
            goal            TEXT,
            business_name   TEXT    NOT NULL,
            business_type   TEXT,
            target_audience TEXT,
            locations       TEXT,  -- JSON list
            daily_budget    REAL,
            total_budget    REAL,
            landing_address TEXT,
            landing_type    TEXT,
            experiences     TEXT,  -- JSON list
            status          TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            session_id      TEXT
        );
    """,
    "campaign_plans": """
        CREATE TABLE IF NOT EXISTS campaign_plans (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT    NOT NULL,
            data            TEXT    NOT NULL,  -- JSON blob of CampaignPlan
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """,
}

with get_connection() as _conn:
    for sql in _CREATE_TABLES_SQL.values():
        _conn.execute(sql)
    _conn.commit()


class _BaseCRUD:
    """Trivial helper that hides *execute / commit* boilerplate."""

    _table: str  # subclasses define the table name
    _conn_factory: Callable[[], ContextManager[sqlite3.Connection]] = get_connection

    @classmethod
    def _exec(cls, sql: str, params: Sequence[Any] | None = None) -> None:
        with cls._conn_factory() as conn:
            conn.execute(sql, params or [])
            conn.commit()

    @classmethod
    def _query(cls, sql: str, params: Sequence[Any] | None = None) -> Sequence[sqlite3.Row]:
        with cls._conn_factory() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, params or []).fetchall()


class CampaignRequestCRUD(_BaseCRUD):
    _table = "campaign_requests"

    @classmethod
    def insert(cls, cr: CampaignRequest) -> None:
        cls._exec(
            f"""
            INSERT INTO {cls._table} (
                advertiser_id, goal, business_name, business_type, target_audience,
                locations, daily_budget, total_budget, landing_address,
                landing_type, experiences, status, created_at, session_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                cr.advertiser_id,
                cr.goal,
                cr.business.name,
                cr.business.type,
                cr.target_audience,
                json.dumps(cr.locations, ensure_ascii=False),
                cr.daily_budget,
                cr.total_budget,
                cr.landing.address,
                cr.landing.type,
                json.dumps(cr.experiences, ensure_ascii=False),
                cr.status,
                cr.created_at.isoformat(timespec="seconds"),
                cr.session_id,
            ),
        )

    @classmethod
    def all(cls) -> Sequence[sqlite3.Row]:
        return cls._query(f"SELECT * FROM {cls._table} ORDER BY created_at DESC")

    @classmethod
    def latest_for_session(cls, session_id: str) -> CampaignRequest | None:
        rows = cls._query(
            f"""
            SELECT data FROM {cls._table}
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        )
        return CampaignRequest.parse_raw(rows[0]["data"]) if rows else None


class CampaignPlanCRUD(_BaseCRUD):
    _table = "campaign_plans"

    @classmethod
    def insert(cls, session_id: str, plan: CampaignPlan) -> None:
        cls._exec(
            f"INSERT INTO {cls._table} (session_id, data) VALUES (?, ?)",
            (session_id, plan.model_dump_json()),
        )

    @classmethod
    def latest_for_session(cls, session_id: str) -> CampaignPlan | None:
        rows = cls._query(
            f"""
            SELECT data FROM {cls._table}
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        )
        return CampaignPlan.parse_raw(rows[0]["data"]) if rows else None


def insert_campaign_request(cr: CampaignRequest) -> None:  # noqa: D401
    """Insert *one* `CampaignRequest`.  Thin wrapper around the CRUD class."""

    CampaignRequestCRUD.insert(cr)


def fetch_campaign_requests() -> Sequence[sqlite3.Row]:  # noqa: D401
    """Return **all** campaign requests, newest first."""

    return CampaignRequestCRUD.all()


def fetch_latest_campaign_request(session_id: str) -> CampaignRequest | None:  # noqa: D401
    """Fetch the most recent `CampaignPlan` for *session_id* or ``None``."""

    return CampaignRequestCRUD.latest_for_session(session_id)


def insert_campaign_plan(session_id: str, plan: CampaignPlan) -> None:  # noqa: D401
    """Persist a `CampaignPlan` linked to an agent session."""

    CampaignPlanCRUD.insert(session_id, plan)


def fetch_latest_campaign_plan(session_id: str) -> CampaignPlan | None:  # noqa: D401
    """Fetch the most recent `CampaignPlan` for *session_id* or ``None``."""

    return CampaignPlanCRUD.latest_for_session(session_id)
