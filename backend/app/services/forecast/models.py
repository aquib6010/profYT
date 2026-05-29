"""Forecast model ladder.

Every model implements the same tiny interface:

    fit(y: pd.Series) -> None      # y is a daily, gap-filled revenue series
    predict(horizon: int) -> np.ndarray   # length == horizon, non-negative

This uniform shape is what lets the backtester treat naive baselines and
LightGBM identically and pick a winner objectively. Optional heavy models
(Prophet, LightGBM) are imported lazily so the service still runs if they
failed to install — `available_models()` simply omits them.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

WEEK = 7


class NaiveForecaster:
    """Repeat the last observed value. The bar every other model must clear."""

    name = "naive"

    def fit(self, y: pd.Series) -> None:
        self._last = float(y.iloc[-1])

    def predict(self, horizon: int) -> np.ndarray:
        return np.clip(np.repeat(self._last, horizon), 0, None)


class SeasonalNaiveForecaster:
    """Repeat the last week — a strong baseline when seasonality dominates."""

    name = "seasonal_naive"

    def fit(self, y: pd.Series) -> None:
        self._tail = y.iloc[-WEEK:].to_numpy(dtype=float)

    def predict(self, horizon: int) -> np.ndarray:
        reps = int(np.ceil(horizon / WEEK))
        return np.clip(np.tile(self._tail, reps)[:horizon], 0, None)


class ETSForecaster:
    """Holt-Winters exponential smoothing with a DAMPED additive trend and weekly
    seasonality.

    The intended workhorse for this data shape. Damping is deliberate: revenue
    has level shifts (e.g. an audience-mix change), and an undamped trend
    extrapolates those shifts forever — damping reins the projection back toward
    the recent level and, on this data, is what lets ETS beat the naive baseline
    at a 14-day horizon. Falls back to trend-only when there isn't enough history
    for a seasonal fit (needs >= 2 full weeks).
    """

    name = "ets"

    def fit(self, y: pd.Series) -> None:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        seasonal = "add" if len(y) >= 2 * WEEK else None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._fit = ExponentialSmoothing(
                y.to_numpy(dtype=float),
                trend="add",
                damped_trend=True,
                seasonal=seasonal,
                seasonal_periods=WEEK if seasonal else None,
                initialization_method="estimated",
            ).fit()

    def predict(self, horizon: int) -> np.ndarray:
        return np.clip(np.asarray(self._fit.forecast(horizon), dtype=float), 0, None)


class ProphetForecaster:
    """Facebook Prophet. Optional — robust to the regime shift, but expected to
    be heavy for ~90 daily points."""

    name = "prophet"

    def fit(self, y: pd.Series) -> None:
        from prophet import Prophet

        df = pd.DataFrame({"ds": y.index, "y": y.to_numpy(dtype=float)})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = Prophet(weekly_seasonality=True, daily_seasonality=False, yearly_seasonality=False)
            m.fit(df)
        self._m = m
        self._last = y.index[-1]

    def predict(self, horizon: int) -> np.ndarray:
        future = self._m.make_future_dataframe(periods=horizon, freq="D")
        fc = self._m.predict(future).tail(horizon)["yhat"].to_numpy(dtype=float)
        return np.clip(fc, 0, None)


class LightGBMForecaster:
    """Gradient-boosted trees on lag + calendar features, forecast recursively.

    Included to benchmark a 'modern ML' model against the simple ones; on short
    daily series it usually overfits and loses — which is the point of measuring.
    """

    name = "lightgbm"
    LAGS = (1, 2, 3, 7, 14)

    def fit(self, y: pd.Series) -> None:
        import lightgbm as lgb

        self._history = y.copy()
        frame = self._features(y)
        frame = frame.dropna()
        x = frame.drop(columns=["y"])
        self._cols = list(x.columns)
        self._model = lgb.LGBMRegressor(
            n_estimators=200, learning_rate=0.05, num_leaves=15, min_child_samples=5, verbose=-1
        )
        self._model.fit(x, frame["y"])

    def predict(self, horizon: int) -> np.ndarray:
        series = self._history.copy()
        preds: list[float] = []
        for _ in range(horizon):
            next_day = series.index[-1] + pd.Timedelta(days=1)
            extended = pd.concat([series, pd.Series([np.nan], index=[next_day])])
            feat = self._features(extended).iloc[[-1]][self._cols]
            yhat = float(self._model.predict(feat)[0])
            yhat = max(0.0, yhat)
            preds.append(yhat)
            series = pd.concat([series, pd.Series([yhat], index=[next_day])])
        return np.asarray(preds, dtype=float)

    def _features(self, y: pd.Series) -> pd.DataFrame:
        df = pd.DataFrame({"y": y})
        for lag in self.LAGS:
            df[f"lag_{lag}"] = y.shift(lag)
        df["dow"] = df.index.dayofweek
        df["roll7"] = y.shift(1).rolling(WEEK).mean()
        return df


_PROBE: dict[str, bool] = {}


def _usable(name: str, probe) -> bool:
    """Cache whether an optional model is actually functional (not just importable).

    Prophet in particular imports fine on Windows but fails at instantiation when
    its Stan backend didn't compile — so we probe by constructing it once.
    """
    if name not in _PROBE:
        try:
            probe()
            _PROBE[name] = True
        except Exception:
            _PROBE[name] = False
    return _PROBE[name]


def _probe_prophet() -> None:
    from prophet import Prophet

    Prophet()  # triggers the Stan backend load that fails when uncompiled


def _probe_lightgbm() -> None:
    import lightgbm  # noqa: F401


def available_models() -> list:
    """Instantiate every model whose dependencies are importable AND functional.

    Baselines come first so MAE ties resolve toward the simpler model.
    """
    models: list = [NaiveForecaster(), SeasonalNaiveForecaster(), ETSForecaster()]
    if _usable("prophet", _probe_prophet):
        models.append(ProphetForecaster())
    if _usable("lightgbm", _probe_lightgbm):
        models.append(LightGBMForecaster())
    return models
