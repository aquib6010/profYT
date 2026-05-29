"""Forecast orchestration: select the best model, fit it, attach conformal bands.

Pure CPU + pandas — no DB, no async. The API loads the series and runs this in
a threadpool. `forecast_revenue` returns a plain dict ready for the schema.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from .conformal import Backtest, conformal_offsets, empirical_coverage, rolling_backtest
from .models import NaiveForecaster, available_models

MIN_HISTORY = 21  # below this we don't trust a seasonal model


def _factory_for(model) -> Callable[[], object]:
    cls = type(model)
    return lambda: cls()


def forecast_revenue(y: pd.Series, horizon: int = 14, alpha: float = 0.1) -> dict:
    """Run the model ladder on `y` and return history + forecast + diagnostics."""
    history = [
        {"date": ts.date().isoformat(), "value": round(float(v), 2)} for ts, v in y.items()
    ]

    if len(y) < MIN_HISTORY:
        return {
            "has_forecast": False,
            "low_data": True,
            "model": None,
            "interval": 1 - alpha,
            "history": history,
            "forecast": [],
            "backtest": None,
        }

    # 1. Score every available model out-of-sample; keep each one's backtest so
    #    the winner's residuals can be reused for the conformal bands.
    candidates = available_models()
    scored: list[tuple[float, object, Backtest]] = []
    for model in candidates:
        try:
            bt = rolling_backtest(y, _factory_for(model), horizon)
        except Exception:
            # A model that blows up on this series is simply dropped from the
            # comparison rather than failing the whole request.
            continue
        if np.isfinite(bt.mae):
            scored.append((bt.mae, model, bt))

    scored.sort(key=lambda t: t[0])
    best_mae, best_model, best_bt = scored[0]
    naive_mae = next(
        (mae for mae, m, _ in scored if isinstance(m, NaiveForecaster)), float("inf")
    )

    # 2. Fit the winner on the full series and forecast forward.
    best_model.fit(y)  # type: ignore[attr-defined]
    yhat = best_model.predict(horizon)  # type: ignore[attr-defined]

    # 3. Conformal bands from the winner's rolling residuals.
    offsets = conformal_offsets(best_bt, alpha)
    coverage = empirical_coverage(best_bt, alpha)

    last = y.index[-1]
    forecast = []
    for h in range(horizon):
        d = (last + pd.Timedelta(days=h + 1)).date().isoformat()
        point = float(yhat[h])
        off = float(offsets[h]) if h < len(offsets) else 0.0
        forecast.append(
            {
                "date": d,
                "yhat": round(point, 2),
                "lower": round(max(0.0, point - off), 2),
                "upper": round(point + off, 2),
            }
        )

    return {
        "has_forecast": True,
        "low_data": False,
        "model": getattr(best_model, "name", "unknown"),
        "interval": round(1 - alpha, 2),
        "history": history,
        "forecast": forecast,
        "backtest": {
            "mae": round(best_mae, 3),
            "mape": None if np.isnan(best_bt.mape) else round(best_bt.mape, 1),
            "naive_mae": None if np.isinf(naive_mae) else round(naive_mae, 3),
            "beats_naive": bool(best_mae < naive_mae),
            "coverage": coverage,
            "n_origins": best_bt.n_origins,
            "models_compared": [getattr(m, "name", "?") for _, m, _ in scored],
        },
    }
