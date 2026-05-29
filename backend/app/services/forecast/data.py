"""Load a creator's daily revenue as a clean, gap-filled pandas Series."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyAnalytics, Video


async def load_revenue_series(
    session: AsyncSession, creator_id: int, days: int = 180
) -> pd.Series:
    """Daily total revenue for the creator, indexed by date, missing days = 0.

    Anchored to the creator's most recent data date so seeded/backfilled data
    is included. Returns an empty Series when the creator has no analytics.
    """
    as_of = await session.scalar(
        select(func.max(DailyAnalytics.date))
        .join(Video, Video.id == DailyAnalytics.video_id)
        .where(Video.creator_id == creator_id)
    )
    if as_of is None:
        return pd.Series(dtype="float64")

    start = as_of - timedelta(days=days - 1)
    rows = (
        await session.execute(
            select(
                DailyAnalytics.date,
                func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0),
            )
            .join(Video, Video.id == DailyAnalytics.video_id)
            .where(
                Video.creator_id == creator_id,
                DailyAnalytics.date >= start,
                DailyAnalytics.date <= as_of,
            )
            .group_by(DailyAnalytics.date)
            .order_by(DailyAnalytics.date)
        )
    ).all()

    if not rows:
        return pd.Series(dtype="float64")

    s = pd.Series(
        {pd.Timestamp(d): float(v) for d, v in rows}, dtype="float64"
    ).sort_index()
    # Reindex to a continuous daily range so models see a regular series.
    full = pd.date_range(s.index.min(), s.index.max(), freq="D")
    return s.reindex(full, fill_value=0.0)
