"""Per-video features for causal uplift estimation.

One row per video: window revenue + views (the outcome and the main confounder),
duration and age (confounders), and category (the treatment).
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyAnalytics, Video


async def load_video_features(session: AsyncSession, creator_id: int) -> pd.DataFrame:
    """Return a per-video frame: revenue, views, duration_sec, age_days, category."""
    as_of = await session.scalar(
        select(func.max(DailyAnalytics.date))
        .join(Video, Video.id == DailyAnalytics.video_id)
        .where(Video.creator_id == creator_id)
    )
    if as_of is None:
        return pd.DataFrame()

    rows = (
        await session.execute(
            select(
                Video.id,
                Video.category,
                Video.duration_sec,
                Video.published_at,
                func.coalesce(func.sum(DailyAnalytics.estimated_revenue_usd), 0).label("revenue"),
                func.coalesce(func.sum(DailyAnalytics.views), 0).label("views"),
            )
            .join(DailyAnalytics, DailyAnalytics.video_id == Video.id)
            .where(Video.creator_id == creator_id)
            .group_by(Video.id, Video.category, Video.duration_sec, Video.published_at)
        )
    ).all()

    if not rows:
        return pd.DataFrame()

    recs = []
    for vid, category, duration, published_at, revenue, views in rows:
        age_days = (as_of - published_at.date()).days if published_at else 0
        recs.append(
            {
                "id": vid,
                "category": category.value,
                "revenue": float(revenue),
                "views": int(views),
                "duration_sec": int(duration or 0),
                "age_days": max(0, age_days),
            }
        )
    return pd.DataFrame(recs)
