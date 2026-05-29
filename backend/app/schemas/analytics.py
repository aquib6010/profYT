"""Response schemas for the analytics summary endpoint.

The summary powers the dashboard's top cards. Every figure here is a plain
aggregate over DailyAnalytics — no ML. Forecast and uplift insights arrive in
later sprints via their own endpoints.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ChannelInfo(BaseModel):
    display_name: str | None
    channel_id: str | None


class CategoryRevenue(BaseModel):
    category: str
    revenue_usd: float


class AnalyticsSummary(BaseModel):
    channel: ChannelInfo

    # Whether this creator has any analytics rows at all. The frontend uses this
    # to show an empty state instead of a wall of zeros.
    has_data: bool

    # The window is anchored to the most recent date we have data for (not
    # "today"), so freshly ingested or seeded data always lands in-window.
    as_of: date | None
    window_days: int

    revenue_last_30d: float
    revenue_prev_30d: float
    # None when there's no prior-window baseline to compare against.
    revenue_change_pct: float | None

    views_last_30d: int
    videos_tracked: int

    # Highest-earning content category in the window (drives the "what's working"
    # card). None when there's no data.
    top_category: CategoryRevenue | None


class TimeseriesPoint(BaseModel):
    date: date
    revenue: float
    views: int
    # Views-weighted average CPM. Approximate: true CPM needs monetized-impression
    # counts we don't store, so this is derived from per-row cpm_usd. None when no
    # monetized rows that day.
    cpm: float | None


class Timeseries(BaseModel):
    as_of: date | None
    points: list[TimeseriesPoint]
