"""Detection methods. Each is independent so the service can combine them and
so they can be benchmarked against the planted ground truth.

  - isolation_forest_flags : multivariate point-outlier detector (main method)
  - rolling_zscore_flags   : univariate statistical baseline to beat
  - pelt_changepoints      : regime-shift detection (the audience-mix break)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

METRIC_COLS = ["revenue", "views", "cpm"]


def _standardize(df: pd.DataFrame) -> np.ndarray:
    x = df.to_numpy(dtype=float)
    mu = x.mean(axis=0)
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - mu) / sd


def isolation_forest_flags(df: pd.DataFrame, contamination: float = 0.08) -> pd.Series:
    """Boolean Series (indexed by date): True where the day is a multivariate outlier."""
    from sklearn.ensemble import IsolationForest

    feats = df[METRIC_COLS]
    x = _standardize(feats)
    model = IsolationForest(
        n_estimators=200, contamination=contamination, random_state=42
    )
    pred = model.fit_predict(x)  # -1 = outlier
    return pd.Series(pred == -1, index=df.index, name="if_flag")


def rolling_zscore_flags(s: pd.Series, window: int = 14, z: float = 2.5) -> pd.Series:
    """Univariate baseline: flag points > z robust-MADs from the rolling median."""
    med = s.rolling(window, min_periods=5).median()
    mad = (s - med).abs().rolling(window, min_periods=5).median()
    scale = mad.replace(0, np.nan) * 1.4826  # MAD -> std equivalent
    score = (s - med).abs() / scale
    return (score > z).fillna(False)


def pelt_changepoints(s: pd.Series, penalty: float = 3.0) -> list[int]:
    """Return integer indices where the series' regime changes (PELT, RBF cost).

    Falls back to an empty list if `ruptures` isn't installed.
    """
    try:
        import ruptures as rpt
    except Exception:
        return []

    x = s.to_numpy(dtype=float).reshape(-1, 1)
    algo = rpt.Pelt(model="rbf").fit(x)
    bkps = algo.predict(pen=penalty)
    # ruptures returns the series length as the final "breakpoint"; drop it.
    return [b for b in bkps if 0 < b < len(s)]
