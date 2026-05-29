"""API + auth integration tests.

Runs the real FastAPI app against an in-memory SQLite database (no Supabase, no
secrets) by overriding the `get_session` and `current_creator` dependencies. The
seed is intentionally small (2 videos, 12 days) so the ML endpoints exercise
their plumbing + the low-data guard paths without needing the heavy model libs —
model correctness is covered by the per-service tests.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import current_creator
from app.db import Base, get_session
from app.main import app
from app.models import Creator, DailyAnalytics, Video, VideoCategory

# Shared in-memory DB (StaticPool keeps one connection so the schema persists).
engine = create_async_engine(
    "sqlite+aiosqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


async def _seed() -> int:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as s:
        creator = Creator(
            google_sub="t", email="t@t.com", display_name="Tester", channel_id="UCtest"
        )
        s.add(creator)
        await s.flush()
        for vi, (title, cat) in enumerate(
            [("How to X", VideoCategory.TUTORIAL), ("My vlog", VideoCategory.VLOG)]
        ):
            v = Video(
                creator_id=creator.id,
                youtube_video_id=f"V{vi}",
                title=title,
                category=cat,
                duration_sec=600,
                published_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
            s.add(v)
            await s.flush()
            for d in range(12):
                s.add(
                    DailyAnalytics(
                        video_id=v.id,
                        date=date(2026, 5, 1) + timedelta(days=d),
                        views=1000 + d,
                        estimated_revenue_usd=5 + d * 0.1,
                        cpm_usd=3.0,
                        country_top={"US": 0.6, "IN": 0.4},
                    )
                )
        await s.commit()
        return creator.id


@pytest_asyncio.fixture
async def client():
    creator_id = await _seed()

    async def _get_session():
        async with TestSession() as s:
            yield s

    async def _current_creator():
        async with TestSession() as s:
            return await s.get(Creator, creator_id)

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[current_creator] = _current_creator
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_me_requires_auth(client):
    # /me reads the session directly (not the overridden dep) -> anonymous = 401.
    r = await client.get("/auth/google/me")
    assert r.status_code == 401


async def test_logout_is_idempotent(client):
    r = await client.post("/auth/google/logout")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


async def test_summary_with_data(client):
    r = await client.get("/api/analytics/summary")
    assert r.status_code == 200
    d = r.json()
    assert d["has_data"] is True
    assert d["videos_tracked"] == 2
    assert d["revenue_last_30d"] > 0


async def test_videos_list(client):
    r = await client.get("/api/videos")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    assert {row["category"] for row in rows} == {"tutorial", "vlog"}
    assert all(row["rpm_usd"] >= 0 for row in rows)


async def test_forecast_low_data_guard(client):
    # 12 days < MIN_HISTORY -> graceful "no forecast", no model libs needed.
    r = await client.get("/api/forecast")
    assert r.status_code == 200
    assert r.json()["has_forecast"] is False


async def test_anomalies_low_data_guard(client):
    r = await client.get("/api/anomalies")
    assert r.status_code == 200
    assert r.json()["has_data"] is False


async def test_recommendations_low_data_guard(client):
    r = await client.get("/api/recommendations")
    assert r.status_code == 200
    assert r.json()["has_data"] is False
