"""
AFLHR Lite - Shared pytest fixtures.

Session-scoped so RoBERTa-large-MNLI (~1.4 GB) + MiniLM load exactly once
across the whole suite. Without this, per-test model loads would make
`make test` take hours.

All tests use offline_mode=True for Groq calls so the suite runs without
network access.
"""

from __future__ import annotations

import os
import sys

# Pin CPU-only before any torch import (matches engine.py env hardening)
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# Make repo root importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest


def pytest_addoption(parser):
    """Register --run-slow so `make test-all` (which passes it) doesn't error."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run tests marked as slow (currently: none — reserved for future use)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow-running")


@pytest.fixture(scope="session")
def engine_v1():
    """v1 baseline engine: MiniLM + RoBERTa-large-MNLI, no windowing/decomposition."""
    from engine import AFLHREngine
    return AFLHREngine(
        use_windowed_nli=False,
        use_decomposition=False,
        use_calibration=False,
        use_bge_embeddings=False,
    )


@pytest.fixture(scope="session")
def client(engine_v1, monkeypatch_session):
    """FastAPI TestClient with engine_v1 preloaded.

    Patches api.engine_v1 and api.get_v2_engine so the startup event is a no-op
    and v2 requests reuse the already-loaded engine (exercises the v2 code path
    without a second 1 GB model download).
    """
    from fastapi.testclient import TestClient
    import api

    monkeypatch_session.setattr(api, "engine_v1", engine_v1, raising=False)
    monkeypatch_session.setattr(api, "engine_v2", engine_v1, raising=False)
    monkeypatch_session.setattr(api, "get_v2_engine", lambda: engine_v1)

    with TestClient(api.app) as c:
        yield c


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch (pytest's built-in is function-scoped)."""
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()
