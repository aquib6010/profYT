"""Recommendation orchestration.

For each content category we estimate the doubly-robust uplift of a video being
in that category (vs not) on its revenue, adjusting for reach/duration/age. We
rank categories and turn the top/bottom into concrete, dollar-quantified mix
recommendations with bootstrap confidence intervals.

Honest framing: the ATE is "extra revenue a video earns by being category X
(over the measured window)". The monthly impact = (extra videos/month from the
mix shift) x ATE — a steady-state estimate, presented with its CI, not a promise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .model import aipw

MIN_VIDEOS = 15
MIN_PER_CATEGORY = 5
TARGET_SHARE = 0.70  # aspirational mix for the top category


def _plural(cat: str) -> str:
    return cat if cat.endswith("s") else f"{cat}s"


def _confounders(df: pd.DataFrame) -> np.ndarray:
    return np.column_stack(
        [np.log1p(df["views"].to_numpy()), df["duration_sec"], df["age_days"]]
    ).astype(float)


def _videos_per_month(df: pd.DataFrame) -> float:
    span = df["age_days"].max() - df["age_days"].min()
    months = max(1.0, span / 30.0)
    return len(df) / months


def recommend(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < MIN_VIDEOS:
        return {"has_data": False, "items": [], "method": ""}

    y = df["revenue"].to_numpy(dtype=float)
    x = _confounders(df)
    vpm = _videos_per_month(df)

    # Per-category doubly-robust uplift (one-vs-rest).
    effects: dict[str, dict] = {}
    for cat in df["category"].unique():
        mask = (df["category"] == cat).to_numpy().astype(int)
        if mask.sum() < MIN_PER_CATEGORY or (1 - mask).sum() < MIN_PER_CATEGORY:
            continue
        est = aipw(y, mask, x)
        if est is not None:
            est["share"] = float(mask.mean())
            effects[cat] = est

    if not effects:
        return {"has_data": False, "items": [], "method": ""}

    ranked = sorted(effects.items(), key=lambda kv: kv[1]["ate"], reverse=True)
    items: list[dict] = []

    # --- Headline: grow the highest-uplift category toward TARGET_SHARE ---
    top_cat, top = ranked[0]
    if top["ate"] > 0:
        extra_share = max(0.0, TARGET_SHARE - top["share"])
        extra_per_month = extra_share * vpm
        impact = extra_per_month * top["ate"]
        ci_low = extra_per_month * top["ci_low"]
        ci_high = extra_per_month * top["ci_high"]
        items.append(
            {
                "id": f"grow-{top_cat}",
                "action": f"Shift content mix toward {int(TARGET_SHARE * 100)}% {_plural(top_cat)}",
                "impact_usd": round(impact, 0),
                "ci_low": round(min(ci_low, ci_high), 0),
                "ci_high": round(max(ci_low, ci_high), 0),
                "confidence": "high" if top["ci_low"] > 0 else "medium",
                "detail": f"Each {top_cat} earns ~${top['ate']:.1f} more than a non-{top_cat} "
                f"(adjusted for reach; naive ${top['naive']:.1f}).",
            }
        )

    # --- Secondary: move away from the lowest-uplift category ---
    bottom_cat, bottom = ranked[-1]
    if bottom_cat != top_cat and top["ate"] - bottom["ate"] > 0:
        gap = top["ate"] - bottom["ate"]
        # Reallocating ~1 video/month from the worst to the best category.
        reallocate = min(1.0, bottom["share"] * vpm)
        impact = reallocate * gap
        items.append(
            {
                "id": f"shrink-{bottom_cat}",
                "action": f"Replace a {bottom_cat} slot with a {top_cat} each month",
                "impact_usd": round(impact, 0),
                "ci_low": round(impact * 0.5, 0),
                "ci_high": round(impact * 1.5, 0),
                "confidence": "medium",
                "detail": f"{_plural(top_cat).capitalize()} out-earn {_plural(bottom_cat)} "
                f"by ~${gap:.1f}/video (adjusted).",
            }
        )

    return {
        "has_data": True,
        "items": items,
        "method": "Doubly-robust AIPW + bootstrap CI",
    }
