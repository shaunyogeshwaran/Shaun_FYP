"""
API-level functional tests — maps to thesis Appendix E (FT-01 … FT-18).

All tests use the FastAPI TestClient and offline_mode=True to avoid Groq
API calls. The v2 engine is patched (in conftest.py) to reuse engine_v1 so
v2-mode tests exercise the decomposition code path without loading a
second 1 GB model.
"""

from __future__ import annotations

import pytest


BASE_REQUEST = {
    "query": "When was the University of Westminster founded?",
    "pivot": 0.75,
    "strict_threshold": 0.95,
    "lenient_threshold": 0.70,
    "offline_mode": True,
    "v2_mode": False,
}


def _verify(client, **overrides):
    payload = {**BASE_REQUEST, **overrides}
    return client.post("/api/verify", json=payload)


# ---------------------------------------------------------------------------
# FT-01 — Health endpoint
# ---------------------------------------------------------------------------

def test_ft_01_health_endpoint(client):
    """FT-01: GET /api/health returns 200 with engine + API-key flags (FR-01)."""
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["engine_v1_loaded"] is True
    assert isinstance(body["has_api_key"], bool)


# ---------------------------------------------------------------------------
# FT-02 — Knowledge base endpoint
# ---------------------------------------------------------------------------

def test_ft_02_knowledge_base_endpoint(client):
    """FT-02: GET /api/knowledge-base returns 3 topics + 6 total passages (FR-02)."""
    r = client.get("/api/knowledge-base")
    assert r.status_code == 200
    body = r.json()
    assert body["total_passages"] == 6
    assert len(body["topics"]) == 3
    topic_names = {t["name"] for t in body["topics"]}
    assert "University of Westminster" in topic_names
    assert "AI Hallucinations" in topic_names


# ---------------------------------------------------------------------------
# FT-03 / FT-04 — Retrieval relevance
# ---------------------------------------------------------------------------

def test_ft_03_retrieval_in_domain(client):
    """FT-03: In-domain query context contains 'Westminster', retrieval > 0.5 (FR-03)."""
    r = _verify(client, query="When was the University of Westminster founded?")
    assert r.status_code == 200
    body = r.json()
    assert body["retrieval"]["retrieval_score"] > 0.5
    assert "Westminster" in body["retrieval"]["context"]


def test_ft_04_retrieval_off_topic_lower(client):
    """FT-04: Off-topic query retrieval score is lower than in-domain (FR-03)."""
    in_domain = _verify(client, query="When was the University of Westminster founded?").json()
    off_topic = _verify(client, query="What is the capital of Japan?").json()
    assert off_topic["retrieval"]["retrieval_score"] < in_domain["retrieval"]["retrieval_score"]


# ---------------------------------------------------------------------------
# FT-05 / FT-06 — Generation (online vs offline)
# ---------------------------------------------------------------------------

def test_ft_05_generation_substantive(client):
    """FT-05: Generation in offline mode returns the configured mock response (FR-04)."""
    # In CI we use offline_mode=True so this is the mock. When GROQ_API_KEY
    # is absent, online-mode requests are also downgraded to offline per
    # api.py:145, so the assertion holds either way.
    from config import OFFLINE_MOCK_RESPONSE
    body = _verify(client).json()
    assert isinstance(body["generation"], str)
    assert len(body["generation"]) > 20
    assert body["generation"] == OFFLINE_MOCK_RESPONSE


def test_ft_06_offline_mode_returns_mock(client):
    """FT-06: offline_mode=True returns the mock response (FR-05)."""
    from config import OFFLINE_MOCK_RESPONSE
    body = _verify(client, offline_mode=True).json()
    assert body["generation"] == OFFLINE_MOCK_RESPONSE


# ---------------------------------------------------------------------------
# FT-07 — NLI score range
# ---------------------------------------------------------------------------

def test_ft_07_nli_score_range(client):
    """FT-07: NLI entailment score is in [0, 1] (FR-06)."""
    body = _verify(client).json()
    assert 0.0 <= body["nli_score"] <= 1.0


# ---------------------------------------------------------------------------
# FT-08 — Verdict structure
# ---------------------------------------------------------------------------

def test_ft_08_verdict_structure(client):
    """FT-08: Verdict contains status, passed, mode, threshold, reasoning (FR-07)."""
    body = _verify(client).json()
    v = body["verdict"]
    for key in ("status", "passed", "mode", "threshold", "reasoning"):
        assert key in v, f"Missing verdict key: {key}"
    assert v["status"] in ("VERIFIED", "HALLUCINATION")


# ---------------------------------------------------------------------------
# FT-09 — Adaptive threshold STRICT/LENIENT switching
# ---------------------------------------------------------------------------

def test_ft_09_adaptive_threshold_switching(client):
    """FT-09: retrieval < pivot -> STRICT; retrieval >= pivot -> LENIENT (FR-08)."""
    # In-domain -> high retrieval -> LENIENT
    in_domain = _verify(client, query="When was Westminster founded?").json()
    # Set pivot just above the retrieval score to force STRICT mode
    low_retrieval_pivot = in_domain["retrieval"]["retrieval_score"] + 0.05
    low_retrieval_pivot = min(low_retrieval_pivot, 0.999)
    strict = _verify(
        client,
        query="When was Westminster founded?",
        pivot=low_retrieval_pivot,
    ).json()
    lenient = _verify(
        client,
        query="When was Westminster founded?",
        pivot=0.0,  # any score >= 0.0 -> LENIENT
    ).json()
    assert strict["verdict"]["mode"] == "STRICT"
    assert lenient["verdict"]["mode"] == "LENIENT"


# ---------------------------------------------------------------------------
# FT-10 — Custom thresholds respected
# ---------------------------------------------------------------------------

def test_ft_10_custom_thresholds(client):
    """FT-10: Custom strict/lenient thresholds flow through to verdict (FR-08)."""
    body = _verify(
        client,
        strict_threshold=0.99,
        lenient_threshold=0.99,
    ).json()
    assert body["verdict"]["threshold"] == pytest.approx(0.99, abs=1e-4)


# ---------------------------------------------------------------------------
# FT-11 — v1 mode (whole-response NLI)
# ---------------------------------------------------------------------------

def test_ft_11_v1_mode_whole_response(client):
    """FT-11: v1 mode -> version='v1', method='whole', n_claims=1, per_claim=[] (FR-09)."""
    body = _verify(client, v2_mode=False).json()
    assert body["version"] == "v1"
    assert body["nli_method"] == "whole"
    assert body["n_claims"] == 1
    assert body["per_claim"] == []


# ---------------------------------------------------------------------------
# FT-12 — v2 mode (decomposed NLI)
# ---------------------------------------------------------------------------

def test_ft_12_v2_mode_decomposed(client):
    """FT-12: v2 mode -> version='v2', method='decomposed', n_claims>=1 (FR-10)."""
    body = _verify(client, v2_mode=True).json()
    assert body["version"] == "v2"
    assert body["nli_method"] == "decomposed"
    assert body["n_claims"] >= 1


# ---------------------------------------------------------------------------
# FT-13 — v2 per-claim breakdown structure
# ---------------------------------------------------------------------------

def test_ft_13_v2_per_claim_structure(client):
    """FT-13: v2 per_claim entries contain 'claim' (str) and 'score' (float in [0,1]) (FR-10)."""
    body = _verify(client, v2_mode=True).json()
    assert isinstance(body["per_claim"], list)
    assert len(body["per_claim"]) >= 1
    for entry in body["per_claim"]:
        assert isinstance(entry["claim"], str)
        assert 0.0 <= entry["score"] <= 1.0


# ---------------------------------------------------------------------------
# FT-14 — v2 NLI score equals minimum per-claim score
# ---------------------------------------------------------------------------

def test_ft_14_v2_nli_equals_min_per_claim(client):
    """FT-14: v2 nli_score == min(per_claim scores) (weakest-link aggregation) (FR-10)."""
    body = _verify(client, v2_mode=True).json()
    if not body["per_claim"]:
        pytest.skip("Generation produced no sentences to decompose")
    min_score = min(c["score"] for c in body["per_claim"])
    assert body["nli_score"] == pytest.approx(min_score, abs=1e-3)


# ---------------------------------------------------------------------------
# FT-15 — v2 produces valid scores for an in-domain query
# ---------------------------------------------------------------------------

def test_ft_15_v2_valid_scores_in_domain(client):
    """FT-15: v2 with an AI-hallucination query -> retrieval > 0.3, nli_score > 0 (FR-10)."""
    body = _verify(
        client,
        query="What are AI hallucinations?",
        v2_mode=True,
    ).json()
    assert body["retrieval"]["retrieval_score"] > 0.3
    assert body["nli_score"] > 0.0


# ---------------------------------------------------------------------------
# FT-16 — Invalid request body
# ---------------------------------------------------------------------------

def test_ft_16_invalid_request_422(client):
    """FT-16: Missing required 'query' field returns HTTP 422 (FR-11)."""
    r = client.post("/api/verify", json={"pivot": 0.75})  # no 'query'
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# FT-17 — Root endpoint
# ---------------------------------------------------------------------------

def test_ft_17_root_html(client):
    """FT-17: GET / returns 200 HTML containing 'AFLHR' (FR-12)."""
    r = client.get("/")
    assert r.status_code == 200
    assert "AFLHR" in r.text


# ---------------------------------------------------------------------------
# FT-18 — OpenAPI docs accessible
# ---------------------------------------------------------------------------

def test_ft_18_openapi_docs(client):
    """FT-18: GET /docs returns 200 (FastAPI Swagger UI) (FR-12)."""
    r = client.get("/docs")
    assert r.status_code == 200
