"""Anomaly service tests on a synthetic frame with a planted geo shift + spike."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.anomaly.attribute import kl_divergence
from app.services.anomaly.service import detect_anomalies


def _frame(n: int = 90, shift_at: int = 45, spike_at: int = 20) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    idx = pd.date_range("2026-01-01", periods=n, freq="D")
    views = rng.normal(5000, 400, n)
    views[spike_at] *= 2.5  # planted point spike
    cpm = np.where(np.arange(n) < shift_at, 4.0, 2.6) + rng.normal(0, 0.1, n)
    revenue = views / 1000 * cpm

    # Audience mix flips US -> IN at shift_at.
    us = np.where(np.arange(n) < shift_at, 0.55, 0.25) + rng.normal(0, 0.01, n)
    inn = np.where(np.arange(n) < shift_at, 0.20, 0.50) + rng.normal(0, 0.01, n)
    return pd.DataFrame(
        {
            "revenue": revenue,
            "views": views.astype(int),
            "cpm": cpm,
            "geo_US": us,
            "geo_IN": inn,
            "geo_BR": np.full(n, 0.1),
        },
        index=pd.DatetimeIndex(idx, name="date"),
    )


def test_detects_geo_changepoint_and_attributes_cause():
    out = detect_anomalies(_frame())
    assert out["has_data"] is True
    cps = [i for i in out["items"] if "PELT" in i["method"]]
    assert cps, "should detect at least one audience-mix changepoint"
    top = cps[0]
    assert "US" in top["cause"] and "IN" in top["cause"]
    assert top["delta"] < 0  # CPM dropped across the shift


def test_detects_point_outlier():
    out = detect_anomalies(_frame())
    assert any("Isolation Forest" in i["method"] for i in out["items"])


def test_kl_divergence_zero_for_identical():
    p = {"US": 0.5, "IN": 0.3, "BR": 0.2}
    assert kl_divergence(p, p) == 0.0 or abs(kl_divergence(p, p)) < 1e-9
    moved = {"US": 0.2, "IN": 0.6, "BR": 0.2}
    assert kl_divergence(moved, p) > 0.05


def test_low_data_returns_no_anomalies():
    out = detect_anomalies(_frame(n=10, shift_at=5, spike_at=3))
    assert out["has_data"] is False
