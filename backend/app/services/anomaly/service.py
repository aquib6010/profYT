"""Anomaly orchestration.

Combines the detectors into a ranked, explained feed:
  1. PELT finds the regime shift in the AUDIENCE MIX (the strong, meaningful
     signal); KL-divergence attributes it (which countries moved) and we report
     the CPM impact across the break.
  2. Isolation Forest flags multivariate point outliers; the dominant-metric
     deviation explains each.
Pure CPU + pandas; the API runs it in a threadpool.
"""

from __future__ import annotations

import pandas as pd

from .attribute import attribute_geo_shift, dominant_metric_change
from .data import GEO_PREFIX
from .detect import isolation_forest_flags, pelt_changepoints

MIN_HISTORY = 21
KL_SIGNIFICANT = 0.02  # audience-mix shift worth calling out
GEO_PENALTY = 1.0
MAX_ITEMS = 6
MIN_SPACING_DAYS = 3  # de-cluster adjacent point anomalies


def _severity(delta_abs: float) -> str:
    if delta_abs >= 25:
        return "high"
    if delta_abs >= 12:
        return "medium"
    return "low"


def _cpm_delta_across(df: pd.DataFrame, idx: int, window: int = 14) -> float:
    before = df["cpm"].iloc[max(0, idx - window):idx].median()
    after = df["cpm"].iloc[idx:idx + window].median()
    if not before or before <= 1e-9:
        return 0.0
    return (after - before) / before * 100


def detect_anomalies(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < MIN_HISTORY:
        return {"has_data": False, "items": [], "detectors": []}

    items: list[dict] = []
    used_dates: list = []

    # --- 1. Audience-mix regime shift (changepoint on the most volatile geo) ---
    geo_cols = [c for c in df.columns if c.startswith(GEO_PREFIX)]
    if geo_cols:
        target = max(geo_cols, key=lambda c: df[c].max() - df[c].min())
        scored = []
        for idx in pelt_changepoints(df[target], penalty=GEO_PENALTY):
            geo = attribute_geo_shift(df, idx)
            scored.append((geo["kl"], idx, geo))
        scored.sort(reverse=True)

        for kl, idx, geo in scored[:2]:
            if kl < KL_SIGNIFICANT:
                continue
            date = df.index[idx]
            delta = _cpm_delta_across(df, idx)
            severity = "high" if (kl >= 0.1 or abs(delta) >= 25) else "medium"
            items.append(
                {
                    "id": f"cp-{date.date().isoformat()}",
                    "date": date.date().isoformat(),
                    "severity": severity,
                    "metric": "Effective CPM",
                    "delta": round(delta, 1),
                    "cause": geo["cause"],
                    "method": "PELT changepoint + KL-divergence",
                }
            )
            used_dates.append(date)

    # --- 2. Point outliers (Isolation Forest + dominant-metric attribution) ---
    flags = isolation_forest_flags(df)
    candidates: list[dict] = []
    for date, is_out in flags.items():
        if not is_out:
            continue
        dom = dominant_metric_change(df, date)
        candidates.append(
            {
                "id": f"if-{date.date().isoformat()}",
                "_date": date,
                "date": date.date().isoformat(),
                "severity": _severity(abs(dom["delta"])),
                "metric": dom["metric"],
                "delta": dom["delta"],
                "cause": f"{dom['metric']} deviated {dom['delta']:+.0f}% from its 14-day norm "
                f"(multivariate outlier).",
                "method": "Isolation Forest",
            }
        )

    # Most extreme first, then de-cluster anomalies that are within a few days.
    candidates.sort(key=lambda it: abs(it["delta"]), reverse=True)
    for c in candidates:
        if len(items) >= MAX_ITEMS:
            break
        if any(abs((c["_date"] - u).days) < MIN_SPACING_DAYS for u in used_dates):
            continue
        used_dates.append(c["_date"])
        items.append({k: v for k, v in c.items() if k != "_date"})

    items.sort(key=lambda it: it["date"], reverse=True)
    return {
        "has_data": True,
        "items": items[:MAX_ITEMS],
        "detectors": ["isolation_forest", "pelt_changepoint", "kl_divergence"],
    }
