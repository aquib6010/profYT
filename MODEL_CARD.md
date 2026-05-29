# Model Card

Per-model documentation for Profitly's ML services: what each model does, how it
was evaluated, and where it breaks.

---

## Revenue forecast

### Overview
Forecasts a creator's channel-level daily revenue up to 60 days ahead (default
14) with a calibrated prediction interval. Served by `GET /api/forecast`.

### Model
- **Selected by backtest, not assumed.** A ladder of candidates is scored with
  rolling-origin CV and the lowest-MAE model is served:
  naive · seasonal-naive · **damped Holt-Winters ETS** · LightGBM
  (· Prophet when its Stan backend is available).
- **Current winner on seed data: damped Holt-Winters ETS** (additive trend with
  damping, additive weekly seasonality). Damping is deliberate — it prevents
  level shifts (e.g. an audience-mix change) from being extrapolated forever.
- **Uncertainty: horizon-wise split-conformal intervals.** Per-horizon residual
  quantiles from the rolling backtest set the band half-width, so intervals
  widen with the forecast horizon and assume no error distribution.

### Training / input data
- Daily `estimated_revenue_usd` summed across the creator's videos, gap-filled
  to a continuous series; up to 180 days of history.
- Currently evaluated on the **synthetic seed dataset** (planted weekly
  seasonality, age decay, a day-60 audience shift).

### Metrics (seed, creator 2 — see EVALUATION.md)
- H=14: MAE **$1.46**, MAPE **26%**, beats naive by ~10%, coverage 0.98 (target 0.90).
- H=7: MAE **$1.18**, MAPE **20%**, beats naive by ~12%.

### Limitations & failure modes
- **Short / low-volume series:** with little history the model falls back toward
  the baseline; below ~21 days it returns `has_forecast=false` rather than guess.
- **Regime shifts:** a sharp, sustained change is smoothed, not predicted — the
  forecast adapts over days, and intervals widen rather than the point tracking
  the break instantly.
- **Conservative intervals:** coverage currently exceeds nominal (wider than
  needed). Safe, but not yet tightly calibrated.
- **Channel-level only:** forecasts total revenue, not per-video or per-category.
- **Not financial advice:** estimates depend on YouTube's reported revenue and
  can revise; treat as guidance, not a guarantee.

### Maintenance
- Re-evaluate with `app.scripts.backtest_forecast`; results cached per
  (creator, latest-data-date, horizon) and invalidate automatically when new
  data lands.

---

## Anomaly detection

### Overview
Flags abnormal days/periods in a creator's revenue metrics and explains the
cause. Served by `GET /api/anomalies`.

### Model
- **Point outliers:** Isolation Forest over standardized [revenue, views, CPM],
  with a robust rolling-MAD z-score as the baseline.
- **Regime shift:** PELT changepoint detection on the audience-mix signal.
- **Attribution:** KL-divergence on the country mix (which geographies moved) +
  per-feature deviation for point outliers.

### Input data
- Daily revenue, views, views-weighted CPM, and views-weighted country shares,
  aggregated from `DailyAnalytics`. Evaluated on the synthetic seed.

### Behavior (seed)
- Detects the planted day-60 audience shift and attributes it:
  "Effective CPM −22.9% — US −25pts, IN +29pts."

### Limitations & failure modes
- **Penalty sensitivity:** PELT's penalty is tuned to this data scale; needs
  per-series calibration in production.
- **CPM is a weak changepoint signal** — detection is anchored on the audience
  distribution instead.
- **Attribution is KL + deviation**, not yet SHAP (shap is installed; wiring is
  future work).
- **Unsupervised:** "anomaly" means statistically unusual, not necessarily bad;
  positive spikes are flagged too.

### Maintenance
- Cached per (creator, latest-data-date); recomputes when new data lands.

---

## Content categorization

### Overview
Classifies each video into tutorial / vlog / review / shorts / other from its
text. Backfilled by `app.scripts.categorize_videos`; labels feed the "Top
category" card, the video table, and (later) the uplift recommender.

### Model
- **Zero-shot:** `all-MiniLM-L6-v2` sentence embeddings + per-category prototype
  descriptors; nearest-prototype cosine. Confidence = softmax over similarities
  (stored in `Video.category_confidence`).
- No training data required — chosen because real channels arrive unlabeled.

### Input data
- Title + description + tags from the `Video` table.

### Metrics (seed, creator 2)
- Accuracy **0.94**, macro-F1 **0.87**, weighted-F1 **0.95** (n=50).

### Limitations & failure modes
- **Templated seed titles** make this an optimistic upper bound; real titles are
  noisier.
- **Catch-all "other"** has low precision — it absorbs ambiguous videos.
- **No confidence gating yet:** low-confidence predictions are stored but not yet
  routed to an active-learning/review queue.
- Prototype wording influences results; treat prototypes as tunable config.

### Maintenance
- Re-run `categorize_videos` after ingesting new videos; `--dry-run` evaluates
  without writing.

---

## Uplift recommendations

### Overview
Estimates the causal effect of content-mix decisions on revenue and turns it into
dollar-quantified recommendations. Served by `GET /api/recommendations`.

### Model
- **Doubly-robust AIPW** estimator (scikit-learn): per-category one-vs-rest
  treatment, window revenue outcome, confounders = log-reach, duration, age.
  Propensity (logistic) + per-arm outcome (linear) models combined via the AIPW
  influence function. **Bootstrap** CIs; naive diff reported as a sensitivity
  check.
- No econml/dowhy — hand-rolled AIPW; linear models chosen for the small sample.

### Input data
- Per-video aggregates from `DailyAnalytics` + `Video` (category, duration, age).

### Behavior (seed)
- Tutorial uplift **+$26/video** (CI [13.8, 34.6], excludes 0); top rec
  "shift toward 70% tutorials → +$46/mo".

### Limitations & failure modes
- **Observational + small n (≈50):** wide CIs; low-volume categories (shorts)
  barely identified. Not an RCT — unmeasured confounders could bias estimates.
- **Monthly extrapolation** assumes steady cadence × per-video uplift.
- **No refutation tests yet** (placebo, subset stability) — EconML/DoWhy
  validation is future work.
- Treat as decision-support with uncertainty, not a guarantee of returns.

### Maintenance
- Cached per (creator, video count); recompute as the catalog grows.
