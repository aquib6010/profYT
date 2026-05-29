"""Per-video profitability endpoint — feeds the dashboard's video table.

GET /api/videos
  Aggregates the signed-in creator's DailyAnalytics by video over the last
  `days`, joined to video metadata. RPM is revenue per 1000 views in the window.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analytics import latest_data_date
from app.api.deps import current_creator
from app.db import get_session
from app.models import Creator, DailyAnalytics, Video
from app.schemas.video import VideoRow

router = APIRouter(prefix="/api", tags=["videos"])

WINDOW_DAYS = 30


@router.get("/videos", response_model=list[VideoRow])
async def list_videos(
    days: int = WINDOW_DAYS,
    creator: Creator = Depends(current_creator),
    session: AsyncSession = Depends(get_session),
) -> list[VideoRow]:
    as_of = await latest_data_date(session, creator.id)
    if as_of is None:
        return []

    start = as_of - timedelta(days=max(1, days) - 1)

    rows = (
        await session.execute(
            select(
                Video.id,
                Video.title,
                Video.category,
                func.coalesce(func.sum(DailyAnalytics.views), 0).label("views"),
                func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0).label("rev"),
            )
            .join(DailyAnalytics, DailyAnalytics.video_id == Video.id)
            .where(
                Video.creator_id == creator.id,
                DailyAnalytics.date >= start,
                DailyAnalytics.date <= as_of,
            )
            .group_by(Video.id, Video.title, Video.category)
            .order_by(func.sum(DailyAnalytics.estimated_revenue_usd).desc())
        )
    ).all()

    out: list[VideoRow] = []
    for vid, title, category, views, rev in rows:
        views_i = int(views)
        rev_f = float(rev)
        rpm = (rev_f / views_i * 1000) if views_i else 0.0
        out.append(
            VideoRow(
                id=vid,
                title=title,
                category=category.value,
                views=views_i,
                revenue_usd=round(rev_f, 2),
                rpm_usd=round(rpm, 2),
            )
        )
    return out
