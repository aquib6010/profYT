"""Response schema for the anomaly endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class AnomalyItem(BaseModel):
    id: str
    date: str
    severity: str  # high | medium | low
    metric: str
    delta: float  # percent change; negative = drop
    cause: str
    method: str  # which detector/attribution produced this


class AnomalyResponse(BaseModel):
    has_data: bool
    items: list[AnomalyItem]
    detectors: list[str]
