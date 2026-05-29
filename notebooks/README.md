# Profitly — Analysis Notebooks

The analysis and model-selection work behind Profitly's ML services. Each
notebook imports the **production code** in `backend/app/services/` and runs it
on an exported snapshot of the seed dataset (`data/`), so the notebooks *are* the
evaluation behind the shipped models — not parallel reimplementations.

| Notebook | What it shows |
|---|---|
| `01_eda.ipynb` | Dataset structure: weekly seasonality, category economics (views ≠ money), and the day-60 audience-mix shift. |
| `02_revenue_forecasting.ipynb` | Model ladder + walk-forward CV; why **damped Holt-Winters ETS** wins; conformal prediction intervals. |
| `03_anomaly_detection.ipynb` | Isolation Forest + **PELT** changepoint (on audience mix, not CPM) + **KL-divergence** cause attribution. |
| `04_categorization_and_uplift.ipynb` | Zero-shot title categorization (honest title-only accuracy) + **doubly-robust AIPW** uplift, naive-vs-adjusted. |

## Reproducing

Notebooks are paired with `.py` (jupytext "percent" format) source — the `.py`
files are the source of truth; the `.ipynb` files carry executed outputs.

```bash
# from repo root, with the backend venv active
cd backend && pip install -r requirements.txt
pip install jupytext nbconvert ipykernel matplotlib seaborn   # notebook extras
python -m ipykernel install --user --name profitly

cd ../notebooks
jupytext --to ipynb --set-kernel profitly --execute 01_eda.py   # etc.
```

`data/` is a CSV export of the seed dataset (one creator, 50 videos, ~90 days),
so the notebooks run without database credentials.

## Data note
The dataset is **synthetic** (the project's seed), built with planted ground
truth so models can be scored against known answers. Where the synthetic data
flatters a model (e.g. descriptions leaking the content category), the notebooks
call it out and report the honest, realistic number instead.
