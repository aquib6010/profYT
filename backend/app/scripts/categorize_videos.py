"""Categorize videos and (optionally) persist the labels.

Classifies each video from its text, evaluates against the existing (seed
ground-truth) categories, prints accuracy / macro-F1 / confusion matrix, and —
unless --dry-run — writes the predicted category + confidence back to the DB.

Run with:
    python -m app.scripts.categorize_videos --dry-run      # eval only
    python -m app.scripts.categorize_videos                # eval + persist
    python -m app.scripts.categorize_videos --creator 2
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import Video, VideoCategory
from app.services.categorize.model import CATEGORY_PROTOTYPES
from app.services.categorize.service import build_text, categorize_texts


def _report(y_true: list[str], y_pred: list[str]) -> None:
    from sklearn.metrics import classification_report, confusion_matrix

    labels = [c.value for c in CATEGORY_PROTOTYPES]
    acc = sum(t == p for t, p in zip(y_true, y_pred, strict=False)) / len(y_true)
    print(f"\nAccuracy: {acc:.3f}  (n={len(y_true)})\n")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print("Confusion (rows=true, cols=pred):")
    print("            " + " ".join(f"{lab[:6]:>7s}" for lab in labels))
    for i, lab in enumerate(labels):
        print(f"{lab:>10s}  " + " ".join(f"{cm[i][j]:7d}" for j in range(len(labels))))


async def main(creator_id: int | None, dry_run: bool) -> None:
    async with AsyncSessionLocal() as session:
        q = select(Video)
        if creator_id is not None:
            q = q.where(Video.creator_id == creator_id)
        videos = list((await session.execute(q)).scalars())

        if not videos:
            print("No videos found.")
            return

        texts = [build_text(v) for v in videos]
        preds = categorize_texts(texts)

        y_true = [v.category.value for v in videos]
        y_pred = [p["category"] for p in preds]
        _report(y_true, y_pred)

        if dry_run:
            print("\n[dry-run] not writing.")
            return

        for v, p in zip(videos, preds, strict=False):
            v.category = VideoCategory(p["category"])
            v.category_confidence = p["confidence"]
        await session.commit()
        print(f"\nWrote categories for {len(videos)} videos.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--creator", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    asyncio.run(main(args.creator, args.dry_run))
