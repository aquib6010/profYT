import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import analytics as analytics_api
from app.api import anomaly as anomaly_api
from app.api import auth as auth_api
from app.api import forecast as forecast_api
from app.api import recommend as recommend_api
from app.api import videos as videos_api
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Profitly API",
    description="Revenue intelligence for YouTube creators.",
    version="0.1.0",
)

# --- Middleware ---
# CORS must allow credentials so the browser sends our session cookie on /api/* calls.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# SessionMiddleware: signed-cookie session, used to carry OAuth CSRF state across
# the Google redirect, and (after callback) to identify the logged-in creator.
# https_only=False because dev runs on http://localhost; flip to True in prod.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="profitly_session",
    max_age=60 * 60 * 24 * 7,  # 7 days
    same_site="lax",           # Required so the cookie survives the OAuth redirect from Google.
    https_only=False,
)

# --- Routers ---
app.include_router(auth_api.router)
app.include_router(analytics_api.router)
app.include_router(videos_api.router)
app.include_router(forecast_api.router)
app.include_router(anomaly_api.router)
app.include_router(recommend_api.router)


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"name": "Profitly API", "docs": "/docs"}
