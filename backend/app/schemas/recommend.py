"""Response schema for the recommendations endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class Recommendation(BaseModel):
    id: str
    action: str
    impact_usd: float  # estimated monthly revenue impact
    ci_low: float
    ci_high: float
    confidence: str  # high | medium
    detail: str


class RecommendationsResponse(BaseModel):
    has_data: bool
    items: list[Recommendation]
    method: str
