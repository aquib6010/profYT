"""Creator model — one row per signed-in YouTube creator.

OAuth tokens are stored encrypted at rest via Fernet (see app.auth.crypto,
landing in Sprint 2). The plaintext token never touches the database.

Every other table in the schema (Video, DailyAnalytics, ChannelDaily) has a
foreign key back to this table.
"""

from datetime import datetime

from sqlalchemy import DateTime, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- Identity (from Google OAuth) ---
    google_sub: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))

    # --- YouTube channel reference ---
    channel_id: Mapped[str | None] = mapped_column(String(64), index=True, unique=True)

    # --- Encrypted OAuth tokens (Fernet ciphertext is bytes) ---
    access_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    refresh_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Bookkeeping ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_ingest_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Creator id={self.id} email={self.email!r}>"
