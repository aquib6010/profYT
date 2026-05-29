"""Categorization orchestration."""

from __future__ import annotations

from app.models import Video

from .model import classify


def build_text(video: Video) -> str:
    """Compose the text fed to the embedder from a video's metadata."""
    parts = [video.title or ""]
    if video.description:
        parts.append(video.description)
    if video.tags:
        parts.append(" ".join(video.tags))
    return ". ".join(p for p in parts if p).strip()


def categorize_texts(texts: list[str]) -> list[dict]:
    """Classify a batch of texts -> [{category, confidence}]."""
    return [{"category": c, "confidence": conf} for c, conf in classify(texts)]
