"""
Integration tests for AFLHR — maps to thesis Appendix D (IT-01 … IT-10).

Exercises run_pipeline end-to-end, the evaluation harness (precompute +
apply_condition + compute_metrics), and boundary logic that spans modules.

IT-08 replaces the thesis' Streamlit startup test with a FastAPI equivalent.
All tests use offline_mode=True to avoid Groq API calls.
"""

from __future__ import annotations

import pytest

from config import KNOWLEDGE_BASE, OFFLINE_MOCK_RESPONSE
from evaluate import apply_condition, compute_metrics


# ---------------------------------------------------------------------------
# IT-01 — In-domain query through full pipeline
# ---------------------------------------------------------------------------

def test_it_01_in_domain_full_pipeline(engine_v1):
    """IT-01: In-domain query -> retrieval >0.80, pipeline produces verdict dict."""
    result = engine_v1.run_pipeline(
        query="When was the University of Westminster founded?",
        pivot=0.75,
        strict_threshold=0.95,
        lenient_threshold=0.70,
        offline_mode=True,  # skip Groq
    )
    assert result["retrieval"]["retrieval_score"] > 0.80
    assert "1838" in result["retrieval"]["documents"][0]
    assert "status" in result["verdict"]
    assert result["verdict"]["status"] in ("VERIFIED", "HALLUCINATION")


# ---------------------------------------------------------------------------
# IT-02 — Out-of-domain query triggers STRICT mode
# ---------------------------------------------------------------------------

def test_it_02_out_of_domain_strict_mode(engine_v1):
    """IT-02: Out-of-domain query (low retrieval) triggers STRICT mode."""
    result = engine_v1.run_pipeline(
        query="What is the capital of Japan?",
        pivot=0.75,
        strict_threshold=0.95,
        lenient_threshold=0.70,
        offline_mode=True,
    )
    # Out-of-domain retrieval should be below pivot
    assert result["retrieval"]["retrieval_score"] < 0.75
    assert result["verdict"]["mode"] == "STRICT"
    # Mock response is unlikely to be entailed by unrelated context
    assert result["verdict"]["status"] == "HALLUCINATION"


# ---------------------------------------------------------------------------
# IT-03 — Offline mode pipeline
# ---------------------------------------------------------------------------

def test_it_03_offline_mode(engine_v1):
    """IT-03: offline_mode=True returns the mock response but still runs retrieval + NLI."""
    result = engine_v1.run_pipeline(
        query="Tell me about Westminster",
        pivot=0.75,
        strict_threshold=0.95,
        lenient_threshold=0.70,
        offline_mode=True,
    )
    assert result["generation"] == OFFLINE_MOCK_RESPONSE
    # Retrieval + NLI still ran despite the mock LLM
    assert result["retrieval"]["retrieval_score"] > 0.0
    assert 0.0 <= result["nli_score"] <= 1.0


# ---------------------------------------------------------------------------
# IT-04 — Pipeline output structure
# ---------------------------------------------------------------------------

def test_it_04_pipeline_output_structure(engine_v1):
    """IT-04: run_pipeline result contains all expected top-level keys with correct types."""
    result = engine_v1.run_pipeline(
        query="Westminster campuses",
        pivot=0.75,
        strict_threshold=0.95,
        lenient_threshold=0.70,
        offline_mode=True,
    )
    expected_keys = {"query", "retrieval", "generation", "nli_score", "verdict"}
    assert expected_keys.issubset(result.keys())
    assert isinstance(result["query"], str)
    assert isinstance(result["retrieval"], dict)
    assert isinstance(result["generation"], str)
    assert isinstance(result["nli_score"], float)
    assert isinstance(result["verdict"], dict)


# ---------------------------------------------------------------------------
# IT-05 — Evaluation harness: precompute then apply C2
# ---------------------------------------------------------------------------

def _make_mock_scores(n: int) -> list:
    """Construct n pre-computed score entries spanning the retrieval/NLI plane."""
    scores = []
    for i in range(n):
        scores.append({
            "sample_id": i,
            "task": "qa",
            "label": i % 2,  # alternating valid/hallucinated
            "retrieval_score": 0.5 + 0.05 * (i % 10),  # 0.50..0.95
            "nli_score": 0.3 + 0.07 * (i % 10),       # 0.30..0.93
            "latency_ms": 100.0,
        })
    return scores


def test_it_05_eval_harness_precompute_and_apply_c2():
    """IT-05: C2 condition on 10 precomputed samples -> 10 predictions in {0, 1}."""
    scores = _make_mock_scores(10)
    predictions = apply_condition(scores, condition="C2", params={"T_static": 0.54})
    assert len(predictions) == 10
    assert all(p in (0, 1) for p in predictions)


# ---------------------------------------------------------------------------
# IT-06 — Evaluation harness: C3 tiered differs from C2
# ---------------------------------------------------------------------------

def test_it_06_eval_harness_c3_tiered_differs_from_c2():
    """IT-06: C3 tiered makes at least one different prediction than C2 (dynamic vs fixed).

    Hand-crafted divergent samples:
      - S0: rs=0.50 (low), nli=0.80 -> C2(T=0.70)=verify; C3(strict=0.95)=reject
      - S1: rs=0.90 (high), nli=0.55 -> C2(T=0.70)=reject; C3(lenient=0.50)=verify
    """
    scores = [
        {"sample_id": 0, "task": "qa", "label": 0,
         "retrieval_score": 0.50, "nli_score": 0.80, "latency_ms": 100.0},
        {"sample_id": 1, "task": "qa", "label": 1,
         "retrieval_score": 0.90, "nli_score": 0.55, "latency_ms": 100.0},
    ]
    c2_preds = apply_condition(scores, "C2", {"T_static": 0.70})
    c3_preds = apply_condition(
        scores, "C3",
        {"method": "tiered", "pivot": 0.80, "T_strict": 0.95, "T_lenient": 0.50},
    )
    # C2:  [verify=0, reject=1]
    # C3:  [reject=1, verify=0]
    assert c2_preds == [0, 1]
    assert c3_preds == [1, 0]
    assert c2_preds != c3_preds


# ---------------------------------------------------------------------------
# IT-07 — Metric computation against scikit-learn
# ---------------------------------------------------------------------------

def test_it_07_metric_computation_matches_sklearn():
    """IT-07: compute_metrics F1/precision/recall agree with scikit-learn reference values."""
    from sklearn.metrics import f1_score, precision_score, recall_score
    labels = [0, 0, 1, 1, 0, 1, 1, 0, 1, 1]
    preds  = [0, 1, 1, 0, 0, 1, 0, 0, 1, 1]

    m = compute_metrics(labels, preds)
    assert m["f1"] == pytest.approx(f1_score(labels, preds), abs=1e-4)
    assert m["precision"] == pytest.approx(precision_score(labels, preds), abs=1e-4)
    assert m["recall"] == pytest.approx(recall_score(labels, preds), abs=1e-4)
    # Over-flag rate = FP / (FP + TN)
    expected_tn = sum(1 for l, p in zip(labels, preds) if l == 0 and p == 0)
    expected_fp = sum(1 for l, p in zip(labels, preds) if l == 0 and p == 1)
    assert m["over_flagging_rate"] == pytest.approx(
        expected_fp / (expected_fp + expected_tn), abs=1e-4
    )


# ---------------------------------------------------------------------------
# IT-08 — FastAPI startup (replacement for Streamlit IT-08)
# ---------------------------------------------------------------------------

def test_it_08_fastapi_startup(client):
    """IT-08 (FastAPI replacement): /api/health returns 200 with engine_v1 loaded.

    The thesis' original IT-08 launches `app.py` via `streamlit run`, but the
    shipped system is FastAPI + React. This test verifies the FastAPI
    equivalent: TestClient triggers startup, /api/health confirms readiness.
    """
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["engine_v1_loaded"] is True


# ---------------------------------------------------------------------------
# IT-09 — Continuous verdict consistency
# ---------------------------------------------------------------------------

def test_it_09_continuous_verdict_consistency(engine_v1):
    """IT-09: sqrt and sigmoid both return thresholds within [T_lenient, T_strict]."""
    T_strict, T_lenient = 0.95, 0.70
    for rs in [0.0, 0.25, 0.5, 0.75, 1.0]:
        sqrt_v = engine_v1.calculate_verdict_continuous(
            retrieval_score=rs, nli_score=0.8,
            T_strict=T_strict, T_lenient=T_lenient, method="sqrt",
        )
        sig_v = engine_v1.calculate_verdict_continuous(
            retrieval_score=rs, nli_score=0.8,
            T_strict=T_strict, T_lenient=T_lenient, method="sigmoid",
            sigmoid_k=10.0, sigmoid_pivot=0.5,
        )
        assert T_lenient - 1e-4 <= sqrt_v["threshold"] <= T_strict + 1e-4, (
            f"sqrt threshold {sqrt_v['threshold']} out of range at rs={rs}"
        )
        assert T_lenient - 1e-4 <= sig_v["threshold"] <= T_strict + 1e-4, (
            f"sigmoid threshold {sig_v['threshold']} out of range at rs={rs}"
        )


# ---------------------------------------------------------------------------
# IT-10 — Boundary retrieval at pivot
# ---------------------------------------------------------------------------

def test_it_10_boundary_retrieval_at_pivot(engine_v1):
    """IT-10: Retrieval just above pivot -> LENIENT, just below -> STRICT."""
    pivot, T_strict, T_lenient = 0.75, 0.95, 0.70
    just_below = engine_v1.calculate_verdict(
        retrieval_score=0.7499, nli_score=0.80,
        pivot=pivot, strict_threshold=T_strict, lenient_threshold=T_lenient,
    )
    just_above = engine_v1.calculate_verdict(
        retrieval_score=0.7501, nli_score=0.80,
        pivot=pivot, strict_threshold=T_strict, lenient_threshold=T_lenient,
    )
    assert just_below["mode"] == "STRICT"
    assert just_above["mode"] == "LENIENT"
    # Flip at the boundary changes which threshold applies
    assert just_below["threshold"] == T_strict
    assert just_above["threshold"] == T_lenient
