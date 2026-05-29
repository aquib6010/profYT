# Evaluation

Backtest results for Profitly's ML services. Numbers are reproducible — each
section names the script that regenerates it.

---

## Revenue forecast

**Reproduce:** `python -m app.scripts.backtest_forecast --creator <id>`

### Method
- **Target:** channel-level daily revenue, gap-filled to a continuous series.
- **Protocol:** expanding-window **rolling-origin** cross-validation (walk-forward).
  At each origin the model is refit on all prior days and forecasts `H` days
  ahead; errors are collected per horizon across up to 45 origins.
- **Point metrics:** MAE (USD), MAPE (%).
- **Interval metric:** out-of-sample **coverage** of the conformal prediction
  interval — offsets calibrated on the first half of origins, coverage measured
  on the second half. Nominal target = 90%.
- **Model selection:** lowest mean MAE wins. Baselines are listed first so ties
  resolve toward the simpler model.

### Results — seeded dataset (creator 2, 90 days, mean $8.08/day)

| Model | Horizon | MAE | MAPE | Coverage |
|---|---|---|---|---|
| naive (last value) | 7 | 1.344 | 22.2% | 0.971 |
| seasonal naive | 7 | 1.585 | 27.4% | 1.000 |
| **ETS (damped Holt-Winters)** | **7** | **1.178** | **19.7%** | 0.971 |
| LightGBM | 7 | 1.552 | 27.7% | 1.000 |
| naive (last value) | 14 | 1.617 | 29.0% | 0.983 |
| seasonal naive | 14 | 1.788 | 32.3% | 1.000 |
| **ETS (damped Holt-Winters)** | **14** | **1.463** | **26.3%** | 0.983 |
| LightGBM | 14 | 1.806 | 33.8% | 0.996 |

### Findings
- **Damped Holt-Winters ETS wins at both horizons**, beating the naive baseline
  by **12% at H=7** (1.178 vs 1.344) and **10% at H=14** (1.463 vs 1.617).
- **Damping is what wins it.** An undamped additive trend extrapolates the
  planted day-60 audience-mix shift downward and *loses* to naive at H=14
  (≈1.65). Damping pulls the projection back toward the recent level.
- **LightGBM loses** — with ~90 daily points it overfits and trails even the
  naive baseline. Documenting that the complex model doesn't help here is the
  point of the benchmark, not a failure.
- **Coverage is conservative** (~97–98% vs a 90% target): intervals are slightly
  wider than necessary. Honest and safe; tightening (e.g. CQR) is future work.

### Caveats
- Results are on the **synthetic seed** dataset, which has clean planted
  structure. Real channels are noisier; expect wider intervals and smaller
  gains over naive. The selection is data-driven, so a different channel may
  legitimately pick a different model.

---

## Anomaly detection

**Reproduce:** covered by `backend/tests/test_anomaly.py` (synthetic ground truth);
live results from `GET /api/anomalies`.

### Method
- **Detection (point outliers):** Isolation Forest over standardized
  [revenue, views, CPM]; a robust rolling-MAD z-score serves as the univariate
  baseline.
- **Detection (regime shift):** **PELT** changepoint detection (RBF cost) run on
  the **audience-mix** signal (the most volatile country share), not on CPM —
  CPM is too noisy and misses the real break.
- **Attribution:** **KL-divergence** between the audience mix before vs after a
  changepoint identifies which countries moved; per-feature deviation explains
  point outliers.

### Result — seeded dataset (creator 2)
The planted day-60 event (audience mix flips US→India) is detected at the correct
date and correctly attributed:

> **Effective CPM −22.9% — "Audience mix shifted: US −25pts, IN +29pts. Lower-CPM
> geography now larger."** (PELT changepoint + KL-divergence)

Point outliers (early high-view/revenue days) are flagged by Isolation Forest and
de-clustered so adjacent days don't repeat.

### Findings
- **Anchoring the changepoint on the audience distribution is what makes it
  work.** PELT on CPM found spurious breaks and missed the real shift; PELT on
  the US share lands exactly on day 60.
- KL-divergence cleanly names the cause (US down, India up), turning a red number
  into an explanation.

### Caveats
- PELT penalty is tuned for this data scale; a production version would calibrate
  it per series. SHAP-based attribution (installed) is not yet wired — current
  attribution is KL + dominant-metric deviation.

---

## Content categorization

**Reproduce:** `python -m app.scripts.categorize_videos --creator <id> --dry-run`

### Method
- **Zero-shot**, no training data: `all-MiniLM-L6-v2` sentence embeddings + a short
  descriptor ("prototype") per category; assign each video to the nearest
  prototype by cosine similarity. Confidence = softmax over the similarities.
- Input text = title + description + tags.

### Result — seeded dataset (creator 2, 50 videos)

| Metric | Value |
|---|---|
| Accuracy | **0.94** |
| Macro-F1 | 0.87 |
| Weighted-F1 | 0.95 |

Per-class: vlog 1.00 F1, tutorial 0.97, shorts 0.95, review 0.89. The only errors
are 3 borderline videos pulled into the catch-all **other** (which therefore has
low precision, 0.40 — expected for a catch-all bucket).

### Findings
- A tiny zero-shot embedding model recovers the categories at 94% with **no
  training and no labels** — the right tool when real channels arrive unlabeled.
- The catch-all "other" absorbs ambiguity; a confidence threshold + active-learning
  queue (future work) would route those for review.

### Caveat (important)
- The 0.94 uses title **+ description + tags**, and the synthetic descriptions
  literally contain the category ("Demo tutorial video…") — i.e. **label leakage**
  inflates this number. From **titles alone** (the realistic real-world signal)
  zero-shot accuracy is **~0.74** (see `notebooks/04_categorization_and_uplift.ipynb`).
  Treat 0.74 as the honest estimate and 0.94 as an optimistic ceiling; the
  pipeline is the deliverable, not the exact number.

---

## Uplift recommendations

**Reproduce:** covered by `backend/tests/test_recommend.py`; live via
`GET /api/recommendations`.

### Method
- **Unit = video. Treatment = category** (one-vs-rest). **Outcome = window
  revenue.** **Confounders = log-reach, duration, age.**
- **Doubly-robust AIPW** (augmented inverse-propensity weighting): a propensity
  model + per-arm outcome models, combined so the estimate is consistent if
  *either* is correct. **Bootstrap** over videos for the CI. We report the
  **naive (unadjusted) diff** alongside, as a confounding sensitivity check.
- scikit-learn + numpy (no econml/dowhy). Linear models suit n≈50.

### Result — seeded dataset (creator 2, 50 videos)
| Category | Adjusted uplift / video | 90% CI | Naive |
|---|---|---|---|
| **tutorial** | **+$26.0** | [13.8, 34.6] | +$11.0 |
| other | −$6.5 | [−10.3, 1.4] | −$8.3 |
| vlog | −$6.8 | [−10.4, −3.0] | −$8.5 |
| shorts | −$44.8 | [−283, 58] (noisy, n=9) | −$1.2 |

Top recommendation: **"Shift mix toward 70% tutorials → +$46/mo (90% CI $25–61),
high confidence."**

### Findings
- The planted economics (tutorials ≈2.7× vlogs) are recovered as a **positive,
  CI-excludes-zero** tutorial effect.
- **Adjusting for reach increases the tutorial estimate ($11 → $26):** tutorials
  get fewer views but higher RPM, so controlling for reach *reveals* a larger
  per-video effect — the naive number understates it. Good demonstration of why
  the causal adjustment matters.

### Caveats
- Observational, single channel, **n≈50** → wide CIs (shorts is barely
  identified). The monthly figure assumes steady cadence × per-video uplift —
  decision-support with uncertainty, not a guarantee. EconML/DoWhy validation +
  refutation tests are future work.
