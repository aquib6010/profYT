"""Video model — one row per YouTube video on a creator's channel.

`youtube_video_id` is the natural key from YouTube (e.g. "dQw4w9WgXcQ"); we use
an internal int surrogate `id` for foreign keys so the schema is decoupled from
YouTube's ID format.

`category` is filled by the semantic-classification service (Sprint 4). Until
then, defaults to OTHER. `category_confidence` is the classifier's probability
for the assigned label — used to drive the active-learning loop.
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class VideoCategory(str, enum.Enum):
    """Content categories. Extend with care — adding a value requires a migration."""

    TUTORIAL = "tutorial"
    VLOG = "vlog"
    SHORTS = "shorts"
    REVIEW = "review"
    OTHER = "other"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("creators.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # --- Natural key from YouTube ---
    youtube_video_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    # --- Video metadata (from YouTube Data API) ---
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    tags: Mapped[list[str] | None] = mapped_column(JSON)

    # --- Content classification (set by ML service) ---
    category: Mapped[VideoCategory] = mapped_column(
        Enum(VideoCategory, native_enum=False, length=16, validate_strings=True),
        default=VideoCategory.OTHER,
        server_default=VideoCategory.OTHER.value,
        nullable=False,
        index=True,
    )
    category_confidence: Mapped[float | None] = mapped_column(Float)

    # --- Lifetime rollups (refreshed by ingest) ---
    lifetime_views: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    lifetime_revenue_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), server_default="0"
    )

    # --- Bookkeeping ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        snippet = (self.title or "")[:40]
        return f"<Video id={self.id} yt={self.youtube_video_id!r} title={snippet!r}>"
