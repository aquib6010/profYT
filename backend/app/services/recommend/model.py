"""Doubly-robust (AIPW) uplift estimator.

Estimates the causal effect of a binary treatment (e.g. "is a tutorial") on a
video's revenue, adjusting for confounders (reach, duration, age). AIPW combines
an outcome model and a propensity model and is consistent if *either* is correct.
Confidence intervals come from a nonparametric bootstrap over videos.

scikit-learn + numpy only — no econml/dowhy. Small linear models suit the small
sample (overfitting a gradient booster on ~50 videos would be worse).
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler

_PROP_CLIP = (0.05, 0.95)


def _aipw_point(y: np.ndarray, t: np.ndarray, x: np.ndarray) -> float | None:
    """Single AIPW ATE estimate. None if a treatment arm is empty."""
    if t.sum() < 2 or (1 - t).sum() < 2:
        return None

    xs = StandardScaler().fit_transform(x)

    # Propensity e(x) = P(T=1 | X)
    try:
        prop = LogisticRegression(max_iter=1000).fit(xs, t)
        e = np.clip(prop.predict_proba(xs)[:, 1], *_PROP_CLIP)
    except Exception:
        e = np.full(len(t), t.mean())

    # Outcome models mu1, mu0 (separate arms — a T-learner)
    mu1_m = LinearRegression().fit(xs[t == 1], y[t == 1])
    mu0_m = LinearRegression().fit(xs[t == 0], y[t == 0])
    mu1 = mu1_m.predict(xs)
    mu0 = mu0_m.predict(xs)

    # Augmented inverse-propensity-weighted influence function
    psi = (mu1 - mu0) + t * (y - mu1) / e - (1 - t) * (y - mu0) / (1 - e)
    return float(np.mean(psi))


def aipw(
    y: np.ndarray, t: np.ndarray, x: np.ndarray, n_boot: int = 300, seed: int = 0
) -> dict | None:
    """AIPW ATE with a bootstrap percentile CI, plus the naive (unadjusted) diff."""
    ate = _aipw_point(y, t, x)
    if ate is None:
        return None

    rng = np.random.default_rng(seed)
    n = len(y)
    boots: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        est = _aipw_point(y[idx], t[idx], x[idx])
        if est is not None:
            boots.append(est)

    lo, hi = (np.percentile(boots, [5, 95]) if boots else (ate, ate))
    naive = float(y[t == 1].mean() - y[t == 0].mean())
    return {
        "ate": round(ate, 4),
        "ci_low": round(float(lo), 4),
        "ci_high": round(float(hi), 4),
        "naive": round(naive, 4),
        "n_treated": int(t.sum()),
        "n_control": int((1 - t).sum()),
    }
