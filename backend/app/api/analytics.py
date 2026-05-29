"""Analytics endpoints — feed the dashboard's cards and charts.

GET /api/analytics/summary     aggregate cards (revenue/views/videos/top category)
GET /api/analytics/timeseries  daily revenue/views/cpm series for the chart + sparklines

Windows are anchored to the creator's most recent data date rather than
wall-clock today, so seeded/backfilled data isn't silently excluded.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_creator
from app.db import get_session
from app.models import Creator, DailyAnalytics, Video
from app.schemas.analytics import (
    AnalyticsSummary,
    CategoryRevenue,
    ChannelInfo,
    Timeseries,
    TimeseriesPoint,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

WINDOW_DAYS = 30


async def latest_data_date(session: AsyncSession, creator_id: int) -> date | None:
    """Most recent date this creator has any analytics for (the window anchor)."""
    return await session.scalar(
        select(func.max(DailyAnalytics.date))
        .join(Video, Video.id == DailyAnalytics.video_id)
        .where(Video.creator_id == creator_id)
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def summary(
    creator: Creator = Depends(current_creator),
    session: AsyncSession = Depends(get_session),
) -> AnalyticsSummary:
    channel = ChannelInfo(display_name=creator.display_name, channel_id=creator.channel_id)

    as_of = await latest_data_date(session, creator.id)
    if as_of is None:
        return AnalyticsSummary(
            channel=channel,
            has_data=False,
            as_of=None,
            window_days=WINDOW_DAYS,
            revenue_last_30d=0.0,
            revenue_prev_30d=0.0,
            revenue_change_pct=None,
            views_last_30d=0,
            videos_tracked=0,
            top_category=None,
        )

    cur_start = as_of - timedelta(days=WINDOW_DAYS - 1)
    prev_start = cur_start - timedelta(days=WINDOW_DAYS)
    prev_end = cur_start - timedelta(days=1)

    cur_row = (
        await session.execute(
            select(
                func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0),
                func.coalesce(func.sum(DailyAnalytics.views), 0),
            )
            .join(Video, Video.id == DailyAnalytics.video_id)
            .where(
                Video.creator_id == creator.id,
                DailyAnalytics.date >= cur_start,
                DailyAnalytics.date <= as_of,
            )
        )
    ).one()
    revenue_last_30d = float(cur_row[0])
    views_last_30d = int(cur_row[1])

    prev_revenue = float(
        await session.scalar(
            select(func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0))
            .join(Video, Video.id == DailyAnalytics.video_id)
            .where(
                Video.creator_id == creator.id,
                DailyAnalytics.date >= prev_start,
                DailyAnalytics.date <= prev_end,
            )
        )
    )

    change_pct: float | None = None
    if prev_revenue > 0:
        change_pct = round((revenue_last_30d - prev_revenue) / prev_revenue * 100, 1)

    videos_tracked = await session.scalar(
        select(func.count(Video.id)).where(Video.creator_id == creator.id)
    )

    top = (
        await session.execute(
            select(
                Video.category,
                func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0).label("rev"),
            )
            .join(DailyAnalytics, DailyAnalytics.video_id == Video.id)
            .where(
                Video.creator_id == creator.id,
                DailyAnalytics.date >= cur_start,
                DailyAnalytics.date <= as_of,
            )
            .group_by(Video.category)
            .order_by(func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0).desc())
            .limit(1)
        )
    ).first()

    top_category = (
        CategoryRevenue(category=top[0].value, revenue_usd=float(top[1])) if top else None
    )

    return AnalyticsSummary(
        channel=channel,
        has_data=True,
        as_of=as_of,
        window_days=WINDOW_DAYS,
        revenue_last_30d=round(revenue_last_30d, 2),
        revenue_prev_30d=round(prev_revenue, 2),
        revenue_change_pct=change_pct,
        views_last_30d=views_last_30d,
        videos_tracked=int(videos_tracked or 0),
        top_category=top_category,
    )


@router.get("/timeseries", response_model=Timeseries)
async def timeseries(
    days: int = 45,
    creator: Creator = Depends(current_creator),
    session: AsyncSession = Depends(get_session),
) -> Timeseries:
    """Daily revenue/views/cpm for the last `days`, anchored to the latest data."""
    as_of = await latest_data_date(session, creator.id)
    if as_of is None:
        return Timeseries(as_of=None, points=[])

    start = as_of - timedelta(days=max(1, days) - 1)

    # cpm_num / cpm_den implement a views-weighted CPM (ignoring rows with no CPM).
    cpm_num = func.sum(DailyAnalytics.cpm_usd * DailyAnalytics.views)
    cpm_den = func.sum(case((DailyAnalytics.cpm_usd.isnot(None), DailyAnalytics.views), else_=0))

    rows = (
        await session.execute(
            select(
                DailyAnalytics.date,
                func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0),
                func.coalesce(func.sum(DailyAnalytics.views), 0),
                cpm_num,
                cpm_den,
            )
            .join(Video, Video.id == DailyAnalytics.video_id)
            .where(
                Video.creator_id == creator.id,
                DailyAnalytics.date >= start,
                DailyAnalytics.date <= as_of,
            )
            .group_by(DailyAnalytics.date)
            .order_by(DailyAnalytics.date)
        )
    ).all()

    points: list[TimeseriesPoint] = []
    for d, rev, views, num, den in rows:
        cpm = float(num) / float(den) if den and num is not None else None
        points.append(
            TimeseriesPoint(
                date=d,
                revenue=round(float(rev), 2),
                views=int(views),
                cpm=round(cpm, 2) if cpm is not None else None,
            )
        )
    return Timeseries(as_of=as_of, points=points)
