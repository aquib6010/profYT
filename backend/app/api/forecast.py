"""Revenue forecast endpoint.

GET /api/forecast?horizon=14
  Loads the creator's daily revenue, runs the model ladder + conformal intervals
  (in a threadpool — it's CPU-bound), and returns history + forecast + the
  backtest diagnostics that justify the selected model.

Results are cached per (creator, latest-data-date, horizon): the backtest is a
few seconds of CPU and only changes when new data lands.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.deps import current_creator
from app.db import get_session
from app.models import Creator
from app.schemas.forecast import ForecastResponse
from app.services.forecast.data import load_revenue_series
from app.services.forecast.service import forecast_revenue

router = APIRouter(prefix="/api", tags=["forecast"])

# (creator_id, as_of_iso, horizon) -> response dict
_CACHE: dict[tuple[int, str, int], dict] = {}


@router.get("/forecast", response_model=ForecastResponse)
async def forecast(
    horizon: int = Query(default=14, ge=1, le=60),
    creator: Creator = Depends(current_creator),
    session: AsyncSession = Depends(get_session),
) -> ForecastResponse:
    y = await load_revenue_series(session, creator.id)

    as_of = y.index[-1].date().isoformat() if len(y) else None
    if as_of is None:
        return ForecastResponse(
            has_forecast=False,
            low_data=False,
            model=None,
            interval=0.9,
            as_of=None,
            history=[],
            forecast=[],
            backtest=None,
        )

    key = (creator.id, as_of, horizon)
    if key not in _CACHE:
        result = await run_in_threadpool(forecast_revenue, y, horizon)
        result["as_of"] = as_of
        _CACHE[key] = result

    return ForecastResponse(**_CACHE[key])
