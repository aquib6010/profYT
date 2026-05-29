"""Cause attribution — turn "something is off" into "here's why".

  - kl_divergence            : distance between two audience-mix distributions
  - attribute_geo_shift      : which countries moved across a changepoint
  - dominant_metric_change   : which metric (revenue/views/cpm) drove a point anomaly
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import GEO_PREFIX

_EPS = 1e-9


def kl_divergence(p: dict[str, float], q: dict[str, float]) -> float:
    """KL(p || q) over the union of countries, with smoothing."""
    keys = set(p) | set(q)
    total = 0.0
    for k in keys:
        pi = p.get(k, 0.0) + _EPS
        qi = q.get(k, 0.0) + _EPS
        total += pi * np.log(pi / qi)
    return float(total)


def _mix(df: pd.DataFrame, sl: slice) -> dict[str, float]:
    geo_cols = [c for c in df.columns if c.startswith(GEO_PREFIX)]
    window = df[geo_cols].iloc[sl].mean()
    return {c[len(GEO_PREFIX):]: float(window[c]) for c in geo_cols}


def attribute_geo_shift(df: pd.DataFrame, cp_idx: int) -> dict:
    """Compare audience mix before vs after a changepoint.

    Returns the KL distance, the biggest movers, and a human-readable cause.
    """
    before = _mix(df, slice(max(0, cp_idx - 21), cp_idx))
    after = _mix(df, slice(cp_idx, min(len(df), cp_idx + 21)))
    kl = kl_divergence(after, before)

    deltas = {c: after.get(c, 0) - before.get(c, 0) for c in set(before) | set(after)}
    gained = max(deltas.items(), key=lambda kv: kv[1])
    lost = min(deltas.items(), key=lambda kv: kv[1])

    cause = (
        f"Audience mix shifted: {lost[0]} share {lost[1] * 100:+.0f}pts, "
        f"{gained[0]} {gained[1] * 100:+.0f}pts. "
        f"Lower-CPM geography now larger."
    )
    return {"kl": round(kl, 4), "gained": gained, "lost": lost, "cause": cause}


def dominant_metric_change(df: pd.DataFrame, date, window: int = 14) -> dict:
    """For a flagged day, find which metric deviated most from its recent norm."""
    pos = df.index.get_loc(date)
    lo = max(0, pos - window)
    baseline = df.iloc[lo:pos]
    if baseline.empty:
        baseline = df.iloc[:pos] if pos > 0 else df

    best_metric, best_delta, best_abs = "revenue", 0.0, -1.0
    for m in ("cpm", "revenue", "views"):
        ref = float(baseline[m].median())
        cur = float(df[m].iloc[pos])
        if ref <= _EPS:
            continue
        delta = (cur - ref) / ref * 100
        if abs(delta) > best_abs:
            best_metric, best_delta, best_abs = m, delta, abs(delta)

    label = {"cpm": "Effective CPM", "revenue": "Revenue", "views": "Views"}[best_metric]
    return {"metric": label, "delta": round(best_delta, 1)}
