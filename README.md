# Profitly — Revenue Intelligence for YouTube Creators

> Profitly answers the question YouTube Studio doesn't: **"Which of my videos actually made money, and what should I make more of?"**
> A revenue-first analytics platform with production-grade ML — per-video revenue, multi-model earnings forecasts with conformal prediction intervals, multivariate anomaly detection with SHAP attribution, semantic content categorization, and causal uplift estimation for content-mix recommendations.

[![CI](https://img.shields.io/badge/CI-pending-lightgrey)]() [![Python](https://img.shields.io/badge/python-3.11+-blue)]() [![Node](https://img.shields.io/badge/node-20+-green)]()

---

## What's inside

| Component | What it does | ML approach |
|---|---|---|
| **Revenue forecast** | Predict next-30-day channel revenue with calibrated uncertainty | Naive baseline → ARIMA → Prophet → LightGBM → NeuralProphet, compared via walk-forward CV; **conformal prediction intervals** |
| **Anomaly detection** | Flag revenue/CPM shocks and explain them | IsolationForest / One-Class SVM / LSTM-AE ensemble; **SHAP** feature attribution + **PELT changepoint** + **KL-divergence** on audience country mix |
| **Content categorization** | Auto-classify videos (tutorial / vlog / shorts / review / other) | Sentence-transformer embeddings + prototype cosine similarity vs. zero-shot BART-MNLI baseline; active-learning loop |
| **Uplift recommendations** | "Make 70% tutorials → +$600/mo" — with confidence interval | **Doubly-robust uplift estimation** (EconML / DoWhy) + bootstrap CIs + sensitivity analysis |
| **Audience drift** | Detect when your audience composition changes | Population Stability Index + rolling KL-divergence |

Each model is benchmarked against simpler baselines in [`notebooks/`](notebooks/) and documented in [`MODEL_CARD.md`](MODEL_CARD.md). Full backtest results in [`EVALUATION.md`](EVALUATION.md).

---

## Architecture

```
┌───────────────┐    OAuth     ┌──────────────────────────────┐
│  YouTube API  │ ◀──────────▶ │  FastAPI backend             │
│  Data + Anal. │              │  ┌────────────────────────┐  │
└───────────────┘              │  │ Ingest scheduler       │  │
                               │  ├────────────────────────┤  │
                               │  │ ML services            │  │
                               │  │ - forecast (ensemble)  │  │
                               │  │ - anomaly (IF+SHAP)    │  │
                               │  │ - categorize (sBERT)   │  │
                               │  │ - recommend (uplift)   │  │
                               │  ├────────────────────────┤  │
                               │  │ REST API + OpenAPI     │  │
                               │  └────────────────────────┘  │
                               └──────────┬───────────────────┘
                                          │
                               ┌──────────▼───────────────────┐
                               │  SQLite (dev) / Postgres     │
                               └──────────────────────────────┘
                                          ▲
                               ┌──────────┴───────────────────┐
                               │  React + Vite frontend       │
                               │  Recharts · TanStack Query   │
                               └──────────────────────────────┘
```

Detailed diagrams in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Local setup

### Prerequisites
- Python 3.11+
- Node 20+
- (No Docker needed — SQLite for dev.)

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows
# source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
copy .env.example .env
# edit .env — see "Google Cloud setup" below for OAuth credentials
alembic upgrade head
python -m app.scripts.seed       # generates demo data so you can use the dashboard without YouTube creds
uvicorn app.main:app --reload
```

Backend boots at `http://localhost:8000`. OpenAPI docs at `/docs`.

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend boots at `http://localhost:5173`.

---

## Google Cloud setup (required for real YouTube data)

1. Open [Google Cloud Console](https://console.cloud.google.com/) → create a new project named `Profitly`.
2. **Enable these APIs** (APIs & Services → Library):
   - YouTube Data API v3
   - YouTube Analytics API
   - YouTube Reporting API
3. **OAuth consent screen:**
   - User type: External
   - Add scopes:
     - `https://www.googleapis.com/auth/youtube.readonly`
     - `https://www.googleapis.com/auth/yt-analytics.readonly`
     - `https://www.googleapis.com/auth/yt-analytics-monetary.readonly`  ← **required for revenue data**
     - `userinfo.email`, `userinfo.profile`
   - Add yourself as a Test user (no Google verification required while in Testing).
4. **Credentials → Create OAuth client ID:**
   - Application type: Web application
   - Authorized redirect URI: `http://localhost:8000/auth/google/callback`
5. Copy the client ID + secret into `backend/.env`:
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   ```

Without `yt-analytics-monetary.readonly` you cannot read revenue — the whole product depends on this scope.

---

## Project layout

```
CreatorAnalytics/
├── backend/                      FastAPI + SQLAlchemy + ML services
│   ├── app/
│   │   ├── api/                  REST endpoints
│   │   ├── auth/                 Google OAuth + Fernet token encryption
│   │   ├── models/               SQLAlchemy 2 async models
│   │   ├── schemas/              Pydantic request/response
│   │   ├── services/             ML services (forecast, anomaly, categorize, recommend)
│   │   ├── youtube/              YouTube Data + Analytics clients
│   │   ├── workers/              APScheduler ingest jobs
│   │   └── scripts/              seed, backtest, train
│   ├── alembic/                  Migrations
│   ├── tests/                    Pytest
│   └── requirements.txt
├── frontend/                     React + Vite + TS + Tailwind
│   └── src/
│       ├── api/                  Typed fetch client
│       ├── components/           RevenueCard, ForecastChart, AnomalyAlert, etc.
│       └── pages/                Login, Dashboard, VideoDetail
├── notebooks/                    EDA + model comparison + evaluation
├── MODEL_CARD.md                 Per-model metrics, limitations, fairness
├── EVALUATION.md                 Backtest results
├── ARCHITECTURE.md               System + ML pipeline diagrams
└── .github/workflows/            CI (ruff + mypy + pytest)
```

---

## Tech stack

**Backend** — Python 3.11 · FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic v2 · APScheduler · httpx
**ML** — pandas · numpy · scikit-learn · prophet · lightgbm · neuralprophet · statsmodels · sentence-transformers · transformers · shap · ruptures · econml · dowhy · torch
**Frontend** — React 18 · Vite · TypeScript · TanStack Query · Recharts · Tailwind
**Infra** — SQLite (dev) / Postgres (prod) · GitHub Actions CI · Railway + Vercel (deploy)

---

## License

MIT
