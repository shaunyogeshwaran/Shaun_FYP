"""Tests for FastAPI endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_engine():
    """Create a mock AFLHREngine to avoid loading real models."""
    engine = MagicMock()
    engine.run_pipeline.return_value = {
        "query": "test query",
        "retrieval": {
            "context": "test context",
            "retrieval_score": 0.85,
            "raw_score": 0.70,
            "documents": ["doc1", "doc2"],
            "indices": [0, 1],
        },
        "generation": "test response",
        "nli_score": 0.90,
        "verdict": {
            "status": "VERIFIED",
            "mode": "LENIENT",
            "threshold": 0.70,
            "nli_score": 0.90,
            "retrieval_score": 0.85,
            "reasoning": "High retrieval confidence",
            "passed": True,
        },
    }
    engine.verify_decomposed.return_value = {
        "score": 0.88,
        "mean_score": 0.90,
        "per_claim": [
            {"claim": "claim 1", "score": 0.92},
            {"claim": "claim 2", "score": 0.88},
        ],
        "n_claims": 2,
        "n_windows": 2,
    }
    engine.calculate_verdict.return_value = {
        "status": "VERIFIED",
        "mode": "LENIENT",
        "threshold": 0.70,
        "nli_score": 0.88,
        "retrieval_score": 0.85,
        "reasoning": "High retrieval confidence",
        "passed": True,
    }
    return engine


@pytest.fixture
def client(mock_engine):
    """Create a TestClient with mocked engines."""
    import api
    api.engine_v1 = mock_engine
    api.engine_v2 = mock_engine
    return TestClient(api.app)


# ======================================================================
# Health endpoint
# ======================================================================

class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "engine_v1_loaded" in data
        assert "engine_v2_loaded" in data
        assert "has_api_key" in data


# ======================================================================
# Knowledge base endpoint
# ======================================================================

class TestKnowledgeBase:
    def test_returns_topics(self, client):
        r = client.get("/api/knowledge-base")
        assert r.status_code == 200
        data = r.json()
        assert data["total_passages"] == 6
        assert len(data["topics"]) == 3

    def test_topic_structure(self, client):
        r = client.get("/api/knowledge-base")
        topics = r.json()["topics"]
        for topic in topics:
            assert "name" in topic
            assert "passages" in topic
            assert isinstance(topic["passages"], int)


# ======================================================================
# Root endpoint
# ======================================================================

class TestRoot:
    def test_root_returns_html(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "AFLHR Lite API" in r.text


# ======================================================================
# Verify endpoint
# ======================================================================

class TestVerify:
    def test_basic_v1_verify(self, client):
        r = client.post("/api/verify", json={
            "query": "When was Westminster founded?",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == "v1"
        assert data["query"] == "test query"
        assert "verdict" in data
        assert "retrieval" in data
        assert "nli_score" in data

    def test_v2_verify(self, client):
        r = client.post("/api/verify", json={
            "query": "When was Westminster founded?",
            "v2_mode": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == "v2"
        assert data["nli_method"] == "decomposed"
        assert data["n_claims"] == 2
        assert len(data["per_claim"]) == 2

    def test_offline_mode(self, client, mock_engine):
        r = client.post("/api/verify", json={
            "query": "test",
            "offline_mode": True,
        })
        assert r.status_code == 200
        # Verify offline_mode was passed to the engine
        call_kwargs = mock_engine.run_pipeline.call_args
        assert call_kwargs.kwargs.get("offline_mode") is True or \
               call_kwargs[1].get("offline_mode") is True

    def test_custom_thresholds(self, client, mock_engine):
        r = client.post("/api/verify", json={
            "query": "test",
            "pivot": 0.6,
            "strict_threshold": 0.85,
            "lenient_threshold": 0.55,
        })
        assert r.status_code == 200
        call_kwargs = mock_engine.run_pipeline.call_args
        kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
        # Thresholds should be passed through
        assert kwargs.get("pivot") == 0.6 or call_kwargs[1].get("pivot") == 0.6

    def test_missing_query_returns_422(self, client):
        """Missing required 'query' field → 422 Unprocessable Entity."""
        r = client.post("/api/verify", json={})
        assert r.status_code == 422

    def test_empty_query(self, client):
        """Empty string query should still be accepted (validation is app-level)."""
        r = client.post("/api/verify", json={"query": ""})
        assert r.status_code == 200

    def test_invalid_json(self, client):
        """Malformed JSON → 422."""
        r = client.post("/api/verify", content="not json",
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_extra_fields_ignored(self, client):
        """Extra fields in request body should be silently ignored."""
        r = client.post("/api/verify", json={
            "query": "test",
            "unknown_field": "should be ignored",
        })
        assert r.status_code == 200

    def test_per_claim_scores_are_rounded(self, client):
        """v2 per-claim scores should be rounded to 4 decimal places."""
        r = client.post("/api/verify", json={
            "query": "test",
            "v2_mode": True,
        })
        data = r.json()
        for claim in data["per_claim"]:
            score_str = str(claim["score"])
            # At most 4 decimal places
            if "." in score_str:
                assert len(score_str.split(".")[1]) <= 4


# ======================================================================
# CORS
# ======================================================================

class TestCORS:
    def test_cors_headers_present(self, client):
        """Preflight OPTIONS should return CORS headers."""
        r = client.options("/api/health", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        })
        assert "access-control-allow-origin" in r.headers
