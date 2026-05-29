"""Load a creator's daily channel metrics + audience geography for anomaly work.

Returns one row per day with revenue, views, a views-weighted CPM, and the
views-weighted country mix (one column per country share). The country mix is
what powers the audience-drift attribution.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyAnalytics, Video

# Country-share columns are prefixed so they don't collide with metric columns.
GEO_PREFIX = "geo_"


async def load_daily_metrics(
    session: AsyncSession, creator_id: int, days: int = 120
) -> pd.DataFrame:
    """Per-day metrics frame indexed by date. Empty frame if no data.

    Columns: revenue, views, cpm, and geo_<CC> (audience share per country).
    """
    as_of = await session.scalar(
        select(func.max(DailyAnalytics.date))
        .join(Video, Video.id == DailyAnalytics.video_id)
        .where(Video.creator_id == creator_id)
    )
    if as_of is None:
        return pd.DataFrame()

    start = as_of - timedelta(days=days - 1)
    rows = (
        await session.execute(
            select(
                DailyAnalytics.date,
                DailyAnalytics.views,
                DailyAnalytics.estimated_revenue_usd,
                DailyAnalytics.cpm_usd,
                DailyAnalytics.country_top,
            )
            .join(Video, Video.id == DailyAnalytics.video_id)
            .where(
                Video.creator_id == creator_id,
                DailyAnalytics.date >= start,
                DailyAnalytics.date <= as_of,
            )
        )
    ).all()

    if not rows:
        return pd.DataFrame()

    # Aggregate per day in Python (JSON country_top is awkward to weight in SQL).
    revenue: dict = defaultdict(float)
    views: dict = defaultdict(float)
    cpm_num: dict = defaultdict(float)
    cpm_den: dict = defaultdict(float)
    geo_num: dict = defaultdict(lambda: defaultdict(float))  # date -> country -> weighted share

    for d, v, rev, cpm, ctop in rows:
        v = float(v or 0)
        revenue[d] += float(rev or 0)
        views[d] += v
        if cpm is not None:
            cpm_num[d] += float(cpm) * v
            cpm_den[d] += v
        if ctop:
            for country, share in ctop.items():
                geo_num[d][country] += float(share) * v

    dates = sorted(revenue.keys())
    countries = sorted({c for day in geo_num.values() for c in day})

    data: dict = {
        "revenue": [round(revenue[d], 4) for d in dates],
        "views": [int(views[d]) for d in dates],
        "cpm": [round(cpm_num[d] / cpm_den[d], 4) if cpm_den[d] else 0.0 for d in dates],
    }
    for c in countries:
        data[f"{GEO_PREFIX}{c}"] = [
            round(geo_num[d][c] / views[d], 4) if views[d] else 0.0 for d in dates
        ]

    return pd.DataFrame(data, index=pd.DatetimeIndex(dates, name="date"))
