"""
Unit tests for AFLHREngine — maps to thesis Appendix C (UT-01 … UT-26).

Each test's docstring cites the thesis Test ID and the component it exercises.
Assertions follow the "Expected Output" column of Table C.1; tolerances use
pytest.approx to absorb float variance from PyTorch inference.

Run with:
    make test
    pytest tests/test_engine.py -v
"""

from __future__ import annotations

import math

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# UT-01 … UT-05 — _encode()
# ---------------------------------------------------------------------------

class TestEncode:
    """Unit tests for AFLHREngine._encode (embedding layer)."""

    def test_ut_01_encode_dimensionality(self, engine_v1):
        """UT-01: Single sentence produces a 384-dimensional embedding vector."""
        emb = engine_v1._encode(["University of Westminster"])
        assert emb.shape == (1, 384), f"Expected shape (1, 384), got {emb.shape}"

    def test_ut_02_encode_l2_normalisation(self, engine_v1):
        """UT-02: Embeddings are L2-normalised (norm = 1.0)."""
        emb = engine_v1._encode(["test input"])
        norm = float(np.linalg.norm(emb[0]))
        assert norm == pytest.approx(1.0, abs=1e-4), f"Expected L2 norm=1.0, got {norm}"

    def test_ut_03_encode_batch_consistency(self, engine_v1):
        """UT-03: Two identical sentences encode to identical vectors."""
        emb = engine_v1._encode(["test input", "test input"])
        diff = float(np.max(np.abs(emb[0] - emb[1])))
        assert diff < 1e-6, f"Expected identical vectors, max diff = {diff}"

    def test_ut_04_encode_empty_string(self, engine_v1):
        """UT-04: Empty string input returns a 384-dim vector without raising."""
        emb = engine_v1._encode([""])
        assert emb.shape == (1, 384)
        assert float(np.linalg.norm(emb[0])) == pytest.approx(1.0, abs=1e-4)

    def test_ut_05_encode_long_input_truncation(self, engine_v1):
        """UT-05: Input exceeding 512 tokens is truncated; 384-dim output returned."""
        long_text = "word " * 2000  # ~2000 tokens, well over 512
        emb = engine_v1._encode([long_text])
        assert emb.shape == (1, 384)


# ---------------------------------------------------------------------------
# UT-06 … UT-10 — retrieve()
# ---------------------------------------------------------------------------

class TestRetrieve:
    """Unit tests for AFLHREngine.retrieve (FAISS retrieval layer)."""

    def test_ut_06_retrieve_in_domain_query(self, engine_v1):
        """UT-06: In-domain query returns high-confidence top document mentioning '1838'."""
        r = engine_v1.retrieve("When was the University of Westminster founded?")
        assert r["retrieval_score"] > 0.80, f"Score {r['retrieval_score']} too low"
        assert "1838" in r["documents"][0], "Top doc should mention founding year"

    def test_ut_07_retrieve_out_of_domain_query(self, engine_v1):
        """UT-07: Out-of-domain query returns low similarity score."""
        r = engine_v1.retrieve("What is the population of Tokyo?")
        assert r["retrieval_score"] < 0.70, (
            f"Out-of-domain score {r['retrieval_score']} should be < 0.70"
        )

    def test_ut_08_retrieve_distractor_topic(self, engine_v1):
        """UT-08: Sri Lanka query retrieves the distractor document (topic-relevant)."""
        r = engine_v1.retrieve("What is the climate of Sri Lanka?")
        assert r["retrieval_score"] > 0.80
        assert "Sri Lanka" in r["documents"][0]

    def test_ut_09_retrieve_empty_query(self, engine_v1):
        """UT-09: Empty query returns a valid result dict without raising."""
        r = engine_v1.retrieve("")
        assert "retrieval_score" in r
        assert "documents" in r
        assert 0.0 <= r["retrieval_score"] <= 1.0

    def test_ut_10_retrieve_score_range_validation(self, engine_v1):
        """UT-10: Retrieval score is always in [0, 1] for arbitrary queries."""
        queries = [
            "University of Westminster",
            "Tokyo",
            "climate",
            "",
            "xyzzy qwerty random nonsense",
        ]
        for q in queries:
            r = engine_v1.retrieve(q)
            assert 0.0 <= r["retrieval_score"] <= 1.0, (
                f"Score {r['retrieval_score']} for query {q!r} out of range"
            )


# ---------------------------------------------------------------------------
# UT-11 … UT-15 — verify()
# ---------------------------------------------------------------------------

class TestVerify:
    """Unit tests for AFLHREngine.verify (NLI verification layer)."""

    def test_ut_11_verify_entailed_pair(self, engine_v1):
        """UT-11: Entailed pair produces entailment probability > 0.90."""
        score = engine_v1.verify(
            premise="Westminster was founded in 1838.",
            hypothesis="Westminster was established in 1838.",
        )
        assert score > 0.90, f"Entailed pair scored only {score}"

    def test_ut_12_verify_contradicted_pair(self, engine_v1):
        """UT-12: Contradicted pair produces entailment probability < 0.10."""
        score = engine_v1.verify(
            premise="Westminster was founded in 1838.",
            hypothesis="Westminster was founded in 2005.",
        )
        assert score < 0.10, f"Contradicted pair scored {score} (expected < 0.10)"

    def test_ut_13_verify_neutral_pair(self, engine_v1):
        """UT-13: Neutral pair produces entailment probability < 0.50."""
        score = engine_v1.verify(
            premise="Westminster has four campuses.",
            hypothesis="The weather in London is often rainy.",
        )
        assert score < 0.50, f"Neutral pair scored {score} (expected < 0.50)"

    def test_ut_14_verify_long_input_truncation(self, engine_v1):
        """UT-14: Premise and hypothesis each exceeding 512 tokens return a float in [0,1] without error."""
        long_premise = ("Westminster was founded in 1838. " * 200)  # ~1,400 tokens
        long_hypothesis = ("The institution dates to 1838. " * 200)
        score = engine_v1.verify(premise=long_premise, hypothesis=long_hypothesis)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_ut_15_verify_output_range(self, engine_v1):
        """UT-15: Various premise-hypothesis pairs all return scores in [0, 1]."""
        pairs = [
            ("The sky is blue.", "The sky is blue."),
            ("Cats are mammals.", "Dogs are reptiles."),
            ("The sun rises in the east.", "The moon is made of cheese."),
            ("Westminster was founded in 1838.", "Westminster has campuses."),
        ]
        for premise, hypothesis in pairs:
            s = engine_v1.verify(premise=premise, hypothesis=hypothesis)
            assert 0.0 <= s <= 1.0, f"Score {s} out of [0,1] for ({premise!r}, {hypothesis!r})"


# ---------------------------------------------------------------------------
# UT-16 … UT-19 — calculate_verdict() tiered
# ---------------------------------------------------------------------------

class TestCalculateVerdictTiered:
    """Unit tests for AFLHREngine.calculate_verdict (Cw-CONLI tiered)."""

    def test_ut_16_tiered_strict_mode_activation(self, engine_v1):
        """UT-16: Low retrieval (0.60 < pivot=0.75) triggers STRICT mode."""
        v = engine_v1.calculate_verdict(
            retrieval_score=0.60,
            nli_score=0.90,
            pivot=0.75,
            strict_threshold=0.95,
            lenient_threshold=0.70,
        )
        assert v["mode"] == "STRICT"
        assert v["threshold"] == 0.95
        assert v["status"] == "HALLUCINATION"  # 0.90 < 0.95

    def test_ut_17_tiered_lenient_mode_activation(self, engine_v1):
        """UT-17: High retrieval (0.80 >= pivot=0.75) triggers LENIENT mode."""
        v = engine_v1.calculate_verdict(
            retrieval_score=0.80,
            nli_score=0.75,
            pivot=0.75,
            strict_threshold=0.95,
            lenient_threshold=0.70,
        )
        assert v["mode"] == "LENIENT"
        assert v["threshold"] == 0.70
        assert v["status"] == "VERIFIED"  # 0.75 >= 0.70

    def test_ut_18_tiered_boundary_at_pivot(self, engine_v1):
        """UT-18: Retrieval exactly at pivot triggers LENIENT (rs >= pivot)."""
        v = engine_v1.calculate_verdict(
            retrieval_score=0.75,
            nli_score=0.80,
            pivot=0.75,
            strict_threshold=0.95,
            lenient_threshold=0.70,
        )
        assert v["mode"] == "LENIENT"
        assert v["status"] == "VERIFIED"

    def test_ut_19_tiered_nli_at_exact_threshold(self, engine_v1):
        """UT-19: NLI score exactly at strict threshold -> VERIFIED (nli >= T)."""
        v = engine_v1.calculate_verdict(
            retrieval_score=0.60,
            nli_score=0.95,
            pivot=0.75,
            strict_threshold=0.95,
            lenient_threshold=0.70,
        )
        assert v["status"] == "VERIFIED"


# ---------------------------------------------------------------------------
# UT-20 … UT-26 — calculate_verdict_continuous()
# ---------------------------------------------------------------------------

class TestCalculateVerdictContinuous:
    """Unit tests for AFLHREngine.calculate_verdict_continuous (sqrt + sigmoid)."""

    def test_ut_20_sqrt_formula(self, engine_v1):
        """UT-20: sqrt formula — T = T_strict - (T_strict - T_lenient) * sqrt(rs)."""
        v = engine_v1.calculate_verdict_continuous(
            retrieval_score=0.64,
            nli_score=0.80,
            T_strict=0.95,
            T_lenient=0.70,
            method="sqrt",
        )
        # 0.95 - 0.25 * sqrt(0.64) = 0.95 - 0.20 = 0.75
        assert v["threshold"] == pytest.approx(0.75, abs=1e-4)

    def test_ut_21_sqrt_low_retrieval(self, engine_v1):
        """UT-21: sqrt at rs=0.0 reduces to T_strict (strictest)."""
        v = engine_v1.calculate_verdict_continuous(
            retrieval_score=0.0,
            nli_score=0.80,
            T_strict=0.95,
            T_lenient=0.70,
            method="sqrt",
        )
        assert v["threshold"] == pytest.approx(0.95, abs=1e-4)

    def test_ut_22_sqrt_high_retrieval(self, engine_v1):
        """UT-22: sqrt at rs=1.0 reduces to T_lenient (most lenient)."""
        v = engine_v1.calculate_verdict_continuous(
            retrieval_score=1.0,
            nli_score=0.80,
            T_strict=0.95,
            T_lenient=0.70,
            method="sqrt",
        )
        assert v["threshold"] == pytest.approx(0.70, abs=1e-4)

    def test_ut_23_sigmoid_formula(self, engine_v1):
        """UT-23: sigmoid at rs=pivot gives mid-point T = T_lenient + (T_strict - T_lenient)/2."""
        v = engine_v1.calculate_verdict_continuous(
            retrieval_score=0.5,
            nli_score=0.80,
            T_strict=0.95,
            T_lenient=0.70,
            method="sigmoid",
            sigmoid_k=10.0,
            sigmoid_pivot=0.5,
        )
        # T = 0.70 + 0.25 / (1 + exp(0)) = 0.70 + 0.125 = 0.825
        assert v["threshold"] == pytest.approx(0.825, abs=1e-4)

    def test_ut_24_sigmoid_far_below_pivot(self, engine_v1):
        """UT-24: sigmoid far below pivot -> threshold approaches T_strict (0.95)."""
        v = engine_v1.calculate_verdict_continuous(
            retrieval_score=0.1,
            nli_score=0.80,
            T_strict=0.95,
            T_lenient=0.70,
            method="sigmoid",
            sigmoid_k=10.0,
            sigmoid_pivot=0.5,
        )
        # Expected behaviour: threshold in the upper half of [0.70, 0.95]
        assert v["threshold"] > 0.90

    def test_ut_25_sigmoid_far_above_pivot(self, engine_v1):
        """UT-25: sigmoid far above pivot -> threshold approaches T_lenient (0.70)."""
        v = engine_v1.calculate_verdict_continuous(
            retrieval_score=0.9,
            nli_score=0.80,
            T_strict=0.95,
            T_lenient=0.70,
            method="sigmoid",
            sigmoid_k=10.0,
            sigmoid_pivot=0.5,
        )
        assert v["threshold"] < 0.75

    def test_ut_26_invalid_continuous_method(self, engine_v1):
        """UT-26: Unknown weighting method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown continuous method"):
            engine_v1.calculate_verdict_continuous(
                retrieval_score=0.5,
                nli_score=0.80,
                T_strict=0.95,
                T_lenient=0.70,
                method="linear",  # not implemented
            )
