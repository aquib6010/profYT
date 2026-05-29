"""Uplift recommendations endpoint.

GET /api/recommendations
  Loads per-video features, runs doubly-robust uplift estimation (in a
  threadpool), and returns dollar-quantified content-mix recommendations.
  Cached per (creator, video count) — recompute when the catalog changes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.deps import current_creator
from app.db import get_session
from app.models import Creator
from app.schemas.recommend import RecommendationsResponse
from app.services.recommend.data import load_video_features
from app.services.recommend.service import recommend

router = APIRouter(prefix="/api", tags=["recommend"])

_CACHE: dict[tuple[int, int], dict] = {}


@router.get("/recommendations", response_model=RecommendationsResponse)
async def recommendations(
    creator: Creator = Depends(current_creator),
    session: AsyncSession = Depends(get_session),
) -> RecommendationsResponse:
    df = await load_video_features(session, creator.id)
    if df.empty:
        return RecommendationsResponse(has_data=False, items=[], method="")

    key = (creator.id, len(df))
    if key not in _CACHE:
        _CACHE[key] = await run_in_threadpool(recommend, df)

    return RecommendationsResponse(**_CACHE[key])
