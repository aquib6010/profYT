"""Response schema for the per-video profitability list."""

from __future__ import annotations

from pydantic import BaseModel


class VideoRow(BaseModel):
    id: int
    title: str
    category: str
    views: int
    revenue_usd: float
    rpm_usd: float  # revenue per 1000 views, over the window
