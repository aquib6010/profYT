"""Zero-shot video categorizer: MiniLM embeddings + nearest-prototype cosine.

No training data needed. Each category is described by a short prototype
sentence; a video is assigned to the category whose prototype its text is most
similar to. Confidence is a softmax over the cosine similarities — a low value
flags an ambiguous video for an active-learning queue later.

The model is loaded lazily and cached (it's ~80MB and downloaded on first use).
"""

from __future__ import annotations

import functools

import numpy as np

from app.models import VideoCategory

# Prototype descriptors — richer than the bare label so the embedding captures
# the concept. Tuned to the category definitions, not to any single channel.
CATEGORY_PROTOTYPES: dict[VideoCategory, str] = {
    VideoCategory.TUTORIAL: "a step-by-step tutorial, how-to guide, course, or explainer that teaches a skill",
    VideoCategory.VLOG: "a personal vlog, daily life update, behind-the-scenes, or q and a with the creator",
    VideoCategory.REVIEW: "a product review, comparison, first impressions, or hands-on opinion piece",
    VideoCategory.SHORTS: "a short-form vertical clip, quick tip, or thirty-second short",
    VideoCategory.OTHER: "a channel announcement, general update, or miscellaneous video",
}

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@functools.lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_MODEL_NAME)


@functools.lru_cache(maxsize=1)
def _prototype_matrix() -> tuple[list[VideoCategory], np.ndarray]:
    cats = list(CATEGORY_PROTOTYPES.keys())
    embs = _model().encode(
        [CATEGORY_PROTOTYPES[c] for c in cats], normalize_embeddings=True
    )
    return cats, np.asarray(embs, dtype=np.float32)


def classify(texts: list[str]) -> list[tuple[str, float]]:
    """Return (category_value, confidence) for each input text.

    confidence = softmax over cosine similarities to each category prototype.
    """
    if not texts:
        return []

    cats, proto = _prototype_matrix()
    vecs = np.asarray(
        _model().encode(texts, normalize_embeddings=True), dtype=np.float32
    )
    sims = vecs @ proto.T  # cosine (both normalized) -> (n_texts, n_cats)

    # Softmax with a temperature so confidences are well-spread, not all ~0.2.
    scaled = sims / 0.1
    scaled -= scaled.max(axis=1, keepdims=True)
    probs = np.exp(scaled)
    probs /= probs.sum(axis=1, keepdims=True)

    out: list[tuple[str, float]] = []
    for i in range(len(texts)):
        j = int(sims[i].argmax())
        out.append((cats[j].value, round(float(probs[i, j]), 4)))
    return out
