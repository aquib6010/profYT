"""Anomaly detection endpoint.

GET /api/anomalies
  Loads the creator's daily metrics + audience mix, runs detection +
  attribution (in a threadpool), and returns an explained, ranked feed.
  Cached per (creator, latest-data-date).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.deps import current_creator
from app.db import get_session
from app.models import Creator
from app.schemas.anomaly import AnomalyResponse
from app.services.anomaly.data import load_daily_metrics
from app.services.anomaly.service import detect_anomalies

router = APIRouter(prefix="/api", tags=["anomaly"])

_CACHE: dict[tuple[int, str], dict] = {}


@router.get("/anomalies", response_model=AnomalyResponse)
async def anomalies(
    creator: Creator = Depends(current_creator),
    session: AsyncSession = Depends(get_session),
) -> AnomalyResponse:
    df = await load_daily_metrics(session, creator.id)
    if df.empty:
        return AnomalyResponse(has_data=False, items=[], detectors=[])

    as_of = df.index[-1].date().isoformat()
    key = (creator.id, as_of)
    if key not in _CACHE:
        _CACHE[key] = await run_in_threadpool(detect_anomalies, df)

    return AnomalyResponse(**_CACHE[key])
