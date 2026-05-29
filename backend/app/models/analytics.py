"""DailyAnalytics — one row per video per day.

This is the time-series fact table that every ML service reads from:
- forecast    → aggregates revenue across the channel
- anomaly     → looks for per-day deltas in CPM / views / country_top
- recommend   → groups by Video.category and aggregates revenue
- drift       → tracks country_top distribution over time

`country_top` stores the top-N countries with their viewing share as JSON,
e.g. {"US": 0.42, "IN": 0.28, "BR": 0.12, ...}. This is what drives the
audience-shift attribution in the anomaly explainer.

Numeric precision: revenue is Numeric(12, 4) because per-day per-video values
can be very small (e.g. $0.0050). Lifetime rollups (on Video) only need 2 dp.
"""

from datetime import date as date_t
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DailyAnalytics(Base):
    __tablename__ = "daily_analytics"
    __table_args__ = (
        # One row per (video, date) — protects against duplicate ingests.
        # This composite unique index also serves queries filtered by video_id.
        UniqueConstraint("video_id", "date", name="uq_daily_analytics_video_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date_t] = mapped_column(Date, nullable=False, index=True)

    # --- Engagement ---
    views: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    watch_time_min: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    avg_view_duration_sec: Mapped[float | None] = mapped_column(Float)

    # --- Revenue (exact decimal, 4 dp for small per-day values) ---
    estimated_revenue_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0"), server_default="0"
    )
    ad_revenue_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0"), server_default="0"
    )

    # --- Rates ---
    # CPM = cost-per-mille (per 1000 monetized impressions, set by advertisers).
    # RPM = revenue-per-mille views (broader; includes non-ad revenue).
    cpm_usd: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    rpm_usd: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    # --- Audience composition: { "US": 0.42, "IN": 0.28, ... } ---
    country_top: Mapped[dict[str, float] | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<DailyAnalytics video_id={self.video_id} date={self.date} "
            f"views={self.views} rev=${self.estimated_revenue_usd}>"
        )
