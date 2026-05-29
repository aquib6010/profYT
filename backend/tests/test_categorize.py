"""Categorizer tests — obvious texts should land in the obvious category.

Loads the MiniLM model (downloaded on first run), so these are integration
tests, not unit tests. Kept small so they're quick after the model is cached.
"""

from __future__ import annotations

import pytest

# Needs the heavy NLP stack (torch + sentence-transformers); skip where it's not
# installed (e.g. lightweight CI) rather than fail.
pytest.importorskip("sentence_transformers")

from app.services.categorize.model import classify  # noqa: E402


def test_obvious_texts_classify_correctly():
    texts = [
        "How to build a REST API in FastAPI — step by step tutorial",
        "My morning routine vlog: a day in my life",
        "iPhone 16 Pro honest review after one month",
        "Quick CSS tip in 30 seconds #shorts",
    ]
    preds = [cat for cat, _ in classify(texts)]
    assert preds[0] == "tutorial"
    assert preds[1] == "vlog"
    assert preds[2] == "review"
    assert preds[3] == "shorts"


def test_confidence_in_unit_range():
    (cat, conf), = classify(["Complete Docker crash course for beginners"])
    assert cat == "tutorial"
    assert 0.0 <= conf <= 1.0


def test_empty_input():
    assert classify([]) == []
