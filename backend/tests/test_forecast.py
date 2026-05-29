"""Forecast service tests — turn 'it works' into checked claims.

These run on a synthetic series with known structure (weekly seasonality + trend
+ a mid-series level shift), so the assertions are deterministic and don't touch
the database.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.forecast.conformal import (
    conformal_offsets,
    empirical_coverage,
    rolling_backtest,
)
from app.services.forecast.models import ETSForecaster, NaiveForecaster
from app.services.forecast.service import forecast_revenue


def _synthetic(n: int = 90, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-01", periods=n, freq="D")
    t = np.arange(n)
    weekly = 1.0 + 0.25 * np.cos(2 * np.pi * (t % 7) / 7)
    level = 6.0 + 0.02 * t
    level[n // 2 :] *= 0.7  # planted regime shift
    noise = rng.normal(0, 0.4, n)
    return pd.Series(np.clip(level * weekly + noise, 0.1, None), index=idx)


def test_ets_beats_naive_on_seasonal_series():
    y = _synthetic()
    ets = rolling_backtest(y, ETSForecaster, horizon=14)
    naive = rolling_backtest(y, NaiveForecaster, horizon=14)
    assert np.isfinite(ets.mae)
    # Damped ETS should beat the naive baseline on a series with real structure.
    assert ets.mae < naive.mae


def test_conformal_offsets_widen_with_horizon():
    y = _synthetic()
    bt = rolling_backtest(y, ETSForecaster, horizon=14)
    offsets = conformal_offsets(bt, alpha=0.1)
    assert len(offsets) == 14
    assert (offsets >= 0).all()
    # Non-decreasing: later horizons are at least as uncertain as earlier ones.
    assert np.all(np.diff(offsets) >= -1e-9)


def test_coverage_near_nominal():
    y = _synthetic(n=120)
    bt = rolling_backtest(y, ETSForecaster, horizon=14)
    cov = empirical_coverage(bt, alpha=0.1)
    assert cov is not None
    # Conformal aims for ~90%; allow a generous band given finite samples.
    assert 0.8 <= cov <= 1.0


def test_forecast_revenue_shape_and_bounds():
    y = _synthetic()
    out = forecast_revenue(y, horizon=7)
    assert out["has_forecast"] is True
    assert out["model"] in {"ets", "naive", "seasonal_naive", "prophet", "lightgbm"}
    assert len(out["forecast"]) == 7
    for p in out["forecast"]:
        assert p["lower"] <= p["yhat"] <= p["upper"]
        assert p["lower"] >= 0.0


def test_low_data_returns_no_forecast():
    y = _synthetic(n=10)
    out = forecast_revenue(y, horizon=14)
    assert out["has_forecast"] is False
    assert out["low_data"] is True
