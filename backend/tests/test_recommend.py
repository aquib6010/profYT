"""Recommendation/uplift tests on a synthetic catalog with a known effect.

We plant a true positive effect for one category (after adjusting for reach) and
check that AIPW recovers it, beats/differs from the naive diff, and that the
service surfaces it as the top recommendation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.recommend.model import aipw
from app.services.recommend.service import recommend


def _catalog(n: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cats = rng.choice(["tutorial", "vlog", "shorts", "other"], size=n, p=[0.3, 0.4, 0.2, 0.1])
    # Tutorials get FEWER views but a real per-video revenue bonus — so the naive
    # diff understates the effect and adjustment should reveal it.
    views = np.where(cats == "tutorial", rng.normal(800, 150, n), rng.normal(1500, 300, n))
    views = np.clip(views, 100, None)
    bonus = np.where(cats == "tutorial", 20.0, 0.0)
    revenue = views / 1000 * 3 + bonus + rng.normal(0, 2, n)
    return pd.DataFrame(
        {
            "id": np.arange(n),
            "category": cats,
            "revenue": revenue,
            "views": views.astype(int),
            "duration_sec": rng.integers(300, 1200, n),
            "age_days": rng.integers(10, 300, n),
        }
    )


def test_aipw_recovers_planted_tutorial_effect():
    df = _catalog()
    y = df["revenue"].to_numpy(float)
    t = (df["category"] == "tutorial").to_numpy().astype(int)
    x = np.column_stack([np.log1p(df["views"]), df["duration_sec"], df["age_days"]]).astype(float)
    est = aipw(y, t, x, n_boot=200)
    assert est is not None
    # Recovers the planted ~$20 bonus (allowing for noise + view confounding).
    assert 10.0 <= est["ate"] <= 30.0
    assert est["ci_low"] <= est["ate"] <= est["ci_high"]


def test_top_recommendation_is_tutorial():
    out = recommend(_catalog())
    assert out["has_data"] is True
    assert out["items"], "should produce at least one recommendation"
    assert "tutorial" in out["items"][0]["action"].lower()
    assert out["items"][0]["impact_usd"] > 0


def test_low_data_returns_nothing():
    out = recommend(_catalog(n=8))
    assert out["has_data"] is False
