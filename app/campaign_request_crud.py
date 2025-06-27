from __future__ import annotations

import json
import sqlite3
from typing import Sequence, Callable, ContextManager

from db import get_connection
from models import CampaignRequest


class CampaignRequestCRUD:
    """Encapsulates CRUD operations for campaign requests."""

    def __init__(self, conn_factory: Callable[[], ContextManager[sqlite3.Connection]] = get_connection):
        self._conn_factory = conn_factory

    def insert(self, campaign_request: CampaignRequest) -> None:
        with self._conn_factory() as conn:
            conn.execute(
                """
                INSERT INTO campaign_requests (
                    business_type,
                    target_audience,
                    locations,
                    daily_budget,
                    landing_type,
                    status,
                    created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    campaign_request.business_type,
                    campaign_request.target_audience,
                    json.dumps(campaign_request.locations, ensure_ascii=False),
                    campaign_request.daily_budget,
                    campaign_request.landing_type,
                    campaign_request.status,
                    campaign_request.created_at.isoformat(),
                ),
            )
            conn.commit()

    def all(self) -> Sequence[sqlite3.Row]:
        with self._conn_factory() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("""SELECT * FROM campaign_requests ORDER BY created_at DESC""").fetchall()


_crud_singleton: CampaignRequestCRUD | None = None


def _get_repo() -> CampaignRequestCRUD:
    global _crud_singleton
    if _crud_singleton is None:
        _crud_singleton = CampaignRequestCRUD()
    return _crud_singleton


def insert_campaign_request(campaign_request: CampaignRequest) -> None:
    _get_repo().insert(campaign_request)


def fetch_campaign_requests() -> Sequence[sqlite3.Row]:
    return _get_repo().all()
