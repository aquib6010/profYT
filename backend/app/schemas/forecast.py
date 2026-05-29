"""Response schema for the revenue forecast endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class HistoryPoint(BaseModel):
    date: str
    value: float


class ForecastPoint(BaseModel):
    date: str
    yhat: float
    lower: float
    upper: float


class BacktestInfo(BaseModel):
    mae: float
    mape: float | None
    naive_mae: float | None
    beats_naive: bool
    coverage: float | None  # out-of-sample interval coverage
    n_origins: int
    models_compared: list[str]


class ForecastResponse(BaseModel):
    has_forecast: bool
    low_data: bool
    model: str | None  # which model was selected by backtest MAE
    interval: float  # nominal coverage, e.g. 0.9
    as_of: str | None
    history: list[HistoryPoint]
    forecast: list[ForecastPoint]
    backtest: BacktestInfo | None
