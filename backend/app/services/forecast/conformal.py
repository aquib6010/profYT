"""Rolling-origin backtesting + horizon-wise split-conformal intervals.

The same rolling backtest serves three purposes:
  1. model selection      — pick the lowest-MAE model out-of-sample
  2. conformal intervals   — per-horizon residual quantiles -> bands that widen
                             with the forecast horizon, no distributional assumption
  3. honest coverage       — a calibrate/measure split estimates real coverage

Everything here is numpy; no model assumptions beyond the fit/predict interface.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

Factory = Callable[[], object]


@dataclass
class Backtest:
    residuals: np.ndarray  # (n_origins, horizon) signed errors (pred - actual), nan-padded
    actuals: np.ndarray  # (n_origins, horizon) aligned actuals, nan-padded
    mae: float
    mape: float
    n_origins: int


def rolling_backtest(
    y: pd.Series,
    factory: Factory,
    horizon: int,
    min_train: int = 21,
    max_origins: int = 45,
) -> Backtest:
    """Expanding-window rolling-origin evaluation of one model."""
    n = len(y)
    start = max(min_train, n - 1 - max_origins)
    rows_err: list[np.ndarray] = []
    rows_act: list[np.ndarray] = []

    for t in range(start, n - 1):
        train = y.iloc[: t + 1]
        model = factory()
        model.fit(train)  # type: ignore[attr-defined]
        pred = model.predict(horizon)  # type: ignore[attr-defined]
        err = np.full(horizon, np.nan)
        act = np.full(horizon, np.nan)
        for h in range(horizon):
            idx = t + 1 + h
            if idx < n:
                err[h] = pred[h] - float(y.iloc[idx])
                act[h] = float(y.iloc[idx])
        rows_err.append(err)
        rows_act.append(act)

    R = np.array(rows_err) if rows_err else np.empty((0, horizon))
    A = np.array(rows_act) if rows_act else np.empty((0, horizon))

    if R.size and np.isfinite(R).any():
        mae = float(np.nanmean(np.abs(R)))
        mask = A > 1e-9
        mape = float(np.nanmean(np.abs(R[mask] / A[mask])) * 100) if mask.any() else float("nan")
    else:
        mae = float("inf")
        mape = float("nan")

    return Backtest(residuals=R, actuals=A, mae=mae, mape=mape, n_origins=len(rows_err))


def conformal_offsets(bt: Backtest, alpha: float = 0.1) -> np.ndarray:
    """Per-horizon symmetric interval half-width = (1-alpha) quantile of |residual|."""
    horizon = bt.residuals.shape[1] if bt.residuals.size else 0
    out = np.zeros(horizon)
    for h in range(horizon):
        col = np.abs(bt.residuals[:, h])
        col = col[~np.isnan(col)]
        if col.size:
            out[h] = float(np.quantile(col, 1 - alpha))
    # Enforce non-decreasing width with horizon (intervals shouldn't shrink later).
    return np.maximum.accumulate(out)


def empirical_coverage(bt: Backtest, alpha: float = 0.1) -> float | None:
    """Out-of-sample coverage: calibrate offsets on the first half of origins,
    measure how often the later origins' actuals fall inside. None if too small."""
    n = bt.n_origins
    if n < 8:
        return None
    mid = n // 2
    calib = Backtest(bt.residuals[:mid], bt.actuals[:mid], 0, 0, mid)
    q = conformal_offsets(calib, alpha)
    test = bt.residuals[mid:]
    covered = total = 0
    for h in range(test.shape[1]):
        col = test[:, h]
        col = col[~np.isnan(col)]
        covered += int(np.sum(np.abs(col) <= q[h]))
        total += col.size
    return round(covered / total, 3) if total else None
