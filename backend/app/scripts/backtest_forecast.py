"""Reproducible forecast backtest — the evidence behind EVALUATION.md.

Runs the full model ladder against a creator's revenue series with rolling-origin
CV at multiple horizons and prints a comparison table (MAE / MAPE / coverage).

Run with:
    python -m app.scripts.backtest_forecast            # creator id 1
    python -m app.scripts.backtest_forecast --creator 2
"""

from __future__ import annotations

import argparse
import asyncio

from app.db import AsyncSessionLocal
from app.services.forecast.conformal import empirical_coverage, rolling_backtest
from app.services.forecast.data import load_revenue_series
from app.services.forecast.models import available_models


def _factory(model):
    cls = type(model)
    return lambda: cls()


async def main(creator_id: int) -> None:
    async with AsyncSessionLocal() as session:
        y = await load_revenue_series(session, creator_id)

    if len(y) == 0:
        print(f"No revenue data for creator {creator_id}.")
        return

    print(f"Creator {creator_id} - {len(y)} days "
          f"({y.index.min().date()} to {y.index.max().date()}), "
          f"mean ${y.mean():.2f}/day\n")

    header = f"{'model':16s} {'H':>3s} {'MAE':>8s} {'MAPE%':>7s} {'coverage':>9s}"
    print(header)
    print("-" * len(header))
    for horizon in (7, 14):
        for model in available_models():
            try:
                bt = rolling_backtest(y, _factory(model), horizon)
            except Exception as exc:  # noqa: BLE001
                print(f"{model.name:16s} {horizon:3d}  (failed: {type(exc).__name__})")
                continue
            cov = empirical_coverage(bt)
            cov_s = f"{cov:.3f}" if cov is not None else "  n/a"
            mape_s = f"{bt.mape:7.1f}" if bt.mape == bt.mape else "    n/a"  # nan check
            print(f"{model.name:16s} {horizon:3d} {bt.mae:8.3f} {mape_s} {cov_s:>9s}")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--creator", type=int, default=1)
    args = ap.parse_args()
    asyncio.run(main(args.creator))
