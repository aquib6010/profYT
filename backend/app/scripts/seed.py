"""Seed script — generates a controlled synthetic dataset with planted ground truth.

The goal is NOT to look like a real YouTube channel. It's to give every ML
service a controlled dataset whose answers we already know, so evaluation in
Sprint 7 can compare model output against ground truth.

What we plant:
  1. WEEKLY SEASONALITY    — weekday views are higher than weekend; the
                             forecast service should pick this up and improve
                             over a naive baseline.
  2. AGE DECAY             — every video peaks in its first ~7 days then decays
                             exponentially; the recommender's per-video revenue
                             estimates have to account for this.
  3. AUDIENCE-SHIFT EVENT  — on day 60 the country mix flips from US-heavy to
                             India-heavy. This drops the weighted CPM ~34%.
                             The anomaly explainer should detect this AND
                             attribute the cause to country mix via SHAP +
                             KL-divergence on the country distribution.
  4. UNDERPERFORMING MIX   — vlogs are the largest category (n=18) but earn
                             ~2.7x less per video than tutorials. The causal
                             uplift recommender should suggest shifting mix
                             toward tutorials and quote a $ impact with CI.

Reproducibility: SEED is fixed. The script clears existing Profitly rows on
every run (idempotent for dev), but does NOT touch any other table.

Run with:
    python -m app.scripts.seed
"""

from __future__ import annotations

import asyncio
import math
import random
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete

from app.db import AsyncSessionLocal, engine
from app.models import Creator, DailyAnalytics, Video, VideoCategory

# ----------------------------------------------------------------------------
# Reproducibility
# ----------------------------------------------------------------------------
SEED = 42
RNG = random.Random(SEED)

# ----------------------------------------------------------------------------
# Dataset shape
# ----------------------------------------------------------------------------
N_DAYS = 90
END_DATE = date(2026, 5, 28)
START_DATE = END_DATE - timedelta(days=N_DAYS - 1)
SHIFT_DAY_OFFSET = 60  # planted audience-shift changepoint

# ----------------------------------------------------------------------------
# Category economics — chosen to plant a clear recommendation signal.
# Tutorials earn ~2.7x more per video than vlogs.
# Real YouTube CPMs are in this range (tutorial/finance > vlog > shorts).
# ----------------------------------------------------------------------------
CATEGORY_PROFILE: dict[VideoCategory, dict[str, object]] = {
    VideoCategory.TUTORIAL: {"n": 15, "base_views": 800,  "rpm": 4.0, "cpm": 8.0, "avd": 480, "dur": (600, 1800)},
    VideoCategory.VLOG:     {"n": 18, "base_views": 1200, "rpm": 1.0, "cpm": 3.0, "avd": 180, "dur": (300, 900)},
    VideoCategory.SHORTS:   {"n": 10, "base_views": 5000, "rpm": 0.3, "cpm": 0.5, "avd": 30,  "dur": (30, 60)},
    VideoCategory.REVIEW:   {"n": 5,  "base_views": 700,  "rpm": 3.0, "cpm": 6.0, "avd": 360, "dur": (480, 1200)},
    VideoCategory.OTHER:    {"n": 2,  "base_views": 400,  "rpm": 1.5, "cpm": 3.0, "avd": 240, "dur": (300, 600)},
}

# Title templates so videos look plausible in the UI.
TITLES: dict[VideoCategory, list[str]] = {
    VideoCategory.TUTORIAL: [
        "How to {topic} in 2026", "Beginner guide to {topic}",
        "{topic} explained step by step", "Master {topic} in 10 minutes",
        "Complete {topic} crash course",
    ],
    VideoCategory.VLOG: [
        "My day vlog #{n}", "What I built this week", "Behind the scenes #{n}",
        "Q&A with the channel", "Studio update {n}",
    ],
    VideoCategory.SHORTS: [
        "{topic} in 30 seconds #shorts", "Quick tip: {topic} #shorts",
        "Did you know? {topic} #shorts", "{topic} fact #shorts",
        "One-liner: {topic} #shorts",
    ],
    VideoCategory.REVIEW: [
        "{topic} honest review", "Is {topic} worth it?",
        "{topic} vs {topic2} — which wins?", "I used {topic} for a month",
        "Hands-on with {topic}",
    ],
    VideoCategory.OTHER: ["Channel update #{n}", "Special announcement"],
}
TOPICS = [
    "FastAPI", "React hooks", "data engineering", "SQL", "Docker", "pandas",
    "AWS Lambda", "system design", "machine learning", "Kubernetes", "GraphQL",
    "Rust", "TypeScript", "PyTorch", "Postgres", "Redis", "Kafka",
]

# ----------------------------------------------------------------------------
# Audience composition — the planted anomaly.
# ----------------------------------------------------------------------------
COUNTRY_MIX_BEFORE = {"US": 0.50, "IN": 0.20, "BR": 0.10, "GB": 0.10, "DE": 0.10}
COUNTRY_MIX_AFTER  = {"IN": 0.50, "US": 0.25, "BR": 0.10, "GB": 0.05, "DE": 0.10}

# Country-level CPM multipliers (real-world inspired, normalized).
COUNTRY_CPM_FACTOR = {"US": 1.6, "GB": 1.4, "DE": 1.3, "BR": 0.4, "IN": 0.25}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def daily_country_mix(day_idx: int) -> dict[str, float]:
    """Returns the channel-wide country mix for one day.

    Pre-shift: noisy variation around COUNTRY_MIX_BEFORE.
    Post-shift: noisy variation around COUNTRY_MIX_AFTER.
    Shift is a step change at day SHIFT_DAY_OFFSET — clean changepoint for PELT.
    """
    base = COUNTRY_MIX_BEFORE if day_idx < SHIFT_DAY_OFFSET else COUNTRY_MIX_AFTER
    noisy = {k: max(0.0, v + RNG.gauss(0, 0.02)) for k, v in base.items()}
    s = sum(noisy.values())
    return {k: round(v / s, 4) for k, v in noisy.items()}


def country_cpm_factor(mix: dict[str, float]) -> float:
    return sum(mix[c] * COUNTRY_CPM_FACTOR[c] for c in mix)


def make_title(cat: VideoCategory, i: int) -> str:
    template = RNG.choice(TITLES[cat])
    return template.format(
        topic=RNG.choice(TOPICS), topic2=RNG.choice(TOPICS), n=i,
    )


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
async def main() -> None:
    print(f"Seeding with seed={SEED}")
    print(f"  date range:  {START_DATE} -> {END_DATE}  ({N_DAYS} days)")
    print(f"  shift event: {START_DATE + timedelta(days=SHIFT_DAY_OFFSET)}  (day {SHIFT_DAY_OFFSET})")
    print()

    async with AsyncSessionLocal() as session:
        # ── Clean Profitly's tables only (CASCADE handles dependents) ──
        await session.execute(delete(DailyAnalytics))
        await session.execute(delete(Video))
        await session.execute(delete(Creator))
        await session.flush()

        # ── Create the demo creator ──
        creator = Creator(
            google_sub="demo|aaqui",
            email="aaqui.demo@profitly.local",
            display_name="Aaqui (demo)",
            channel_id="UC_demo_aaqui",
        )
        session.add(creator)
        await session.flush()

        # ── Create videos ──
        videos: list[Video] = []
        idx = 0
        for cat, prof in CATEGORY_PROFILE.items():
            for _ in range(int(prof["n"])):
                idx += 1
                dur_lo, dur_hi = prof["dur"]  # type: ignore[misc]
                pub_offset = RNG.randint(0, 364)
                v = Video(
                    creator_id=creator.id,
                    youtube_video_id=f"DEMO{idx:06d}",
                    title=make_title(cat, idx),
                    description=f"Demo {cat.value} video #{idx}.",
                    published_at=datetime.combine(
                        END_DATE - timedelta(days=pub_offset),
                        datetime.min.time(),
                        tzinfo=UTC,
                    ),
                    duration_sec=RNG.randint(dur_lo, dur_hi),
                    category=cat,
                    thumbnail_url=f"https://demo.profitly/thumb/{idx}.jpg",
                    tags=[cat.value, RNG.choice(TOPICS).lower()],
                )
                videos.append(v)
                session.add(v)
        await session.flush()

        # ── Precompute one country mix per day (channel-wide) ──
        country_mixes = [daily_country_mix(d) for d in range(N_DAYS)]

        # ── Generate per-video per-day analytics ──
        daily_rows: list[DailyAnalytics] = []
        for v in videos:
            prof = CATEGORY_PROFILE[v.category]
            age_at_end = (END_DATE - v.published_at.date()).days
            for day_idx in range(N_DAYS):
                d = START_DATE + timedelta(days=day_idx)
                age = age_at_end - (N_DAYS - 1 - day_idx)
                if age < 0:
                    continue  # video not published yet

                age_factor = max(0.05, math.exp(-age / 14))                        # peak -> decay
                weekday_factor = 1.0 if d.weekday() < 5 else 0.85                  # weekly seasonality
                noise = max(0.0, 1 + RNG.gauss(0, 0.15))
                expected = float(prof["base_views"]) * age_factor * weekday_factor * noise
                views = max(0, int(RNG.gauss(expected, math.sqrt(expected + 1))))
                if views == 0:
                    continue

                mix = country_mixes[day_idx]
                cf = country_cpm_factor(mix)
                cpm = float(prof["cpm"]) * cf * (1 + RNG.gauss(0, 0.05))
                rpm = float(prof["rpm"]) * cf * (1 + RNG.gauss(0, 0.05))
                revenue = views * rpm / 1000.0
                ad_revenue = revenue * 0.85
                avd = float(prof["avd"]) * (1 + RNG.gauss(0, 0.05))
                watch_min = max(0.0, views * avd * (1 + RNG.gauss(0, 0.1)) / 60.0)

                daily_rows.append(DailyAnalytics(
                    video_id=v.id,
                    date=d,
                    views=views,
                    watch_time_min=round(watch_min, 2),
                    avg_view_duration_sec=round(max(1.0, avd), 2),
                    estimated_revenue_usd=Decimal(f"{revenue:.4f}"),
                    ad_revenue_usd=Decimal(f"{ad_revenue:.4f}"),
                    cpm_usd=Decimal(f"{max(0.0, cpm):.4f}"),
                    rpm_usd=Decimal(f"{max(0.0, rpm):.4f}"),
                    country_top=mix,
                ))

        session.add_all(daily_rows)

        # ── Backfill lifetime rollups on videos ──
        totals: dict[int, tuple[int, Decimal]] = {}
        for r in daily_rows:
            cv, cr = totals.get(r.video_id, (0, Decimal("0")))
            totals[r.video_id] = (cv + r.views, cr + r.estimated_revenue_usd)
        for v in videos:
            v_views, v_rev = totals.get(v.id, (0, Decimal("0")))
            v.lifetime_views = v_views
            v.lifetime_revenue_usd = v_rev.quantize(Decimal("0.01"))
            v.last_synced_at = datetime.now(UTC)
        creator.last_ingest_at = datetime.now(UTC)

        await session.commit()

        # ── Summary ──
        total_views = sum(v.lifetime_views for v in videos)
        total_rev = sum(v.lifetime_revenue_usd for v in videos)
        print(f"Inserted: 1 creator | {len(videos)} videos | {len(daily_rows):,} analytics rows")
        print(f"  total views (90d):   {total_views:>12,}")
        print(f"  total revenue (90d): ${total_rev:>12,.2f}")
        print()
        print(f"  {'category':10s} {'n':>3s} {'views':>14s} {'revenue':>14s} {'$/video':>10s}")
        for cat in CATEGORY_PROFILE:
            cat_vids = [v for v in videos if v.category == cat]
            cv = sum(v.lifetime_views for v in cat_vids)
            cr = sum(v.lifetime_revenue_usd for v in cat_vids)
            per_vid = (cr / len(cat_vids)) if cat_vids else Decimal("0")
            print(f"  {cat.value:10s} {len(cat_vids):>3d} {cv:>14,} ${cr:>13,.2f} ${per_vid:>9,.2f}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
