"""Shared fixtures for AFLHR Lite test suite."""

import os
import sys
import pytest

# Ensure project root is on sys.path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress tokenizer parallelism warnings in tests
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="Run slow tests that require model loading (~30s startup)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: requires model loading")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="needs --run-slow option")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def engine_v1():
    """Load a v1 engine (session-scoped so models load only once)."""
    from engine import AFLHREngine
    return AFLHREngine(
        use_windowed_nli=False,
        use_decomposition=False,
        use_calibration=False,
        use_bge_embeddings=False,
    )


@pytest.fixture(scope="session")
def engine_v2():
    """Load a v2 engine (session-scoped so models load only once)."""
    from engine import AFLHREngine
    return AFLHREngine(
        use_windowed_nli=True,
        use_decomposition=True,
        use_calibration=False,
        use_bge_embeddings=True,
    )
