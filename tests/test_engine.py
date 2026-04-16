"""Tests for AFLHREngine — verdict logic, edge cases, and integration."""

import math
import pytest

from engine import AFLHREngine
from config import KNOWLEDGE_BASE


# ======================================================================
# Verdict calculation (pure logic — no models needed)
# ======================================================================

class TestCalculateVerdict:
    """Test the tiered Cw-CONLI verdict logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a minimal engine mock with just the verdict method."""
        # calculate_verdict is a pure method — we can call it on any instance
        # but we need an instance. Use __new__ to skip __init__ (no model loading).
        self.engine = object.__new__(AFLHREngine)

    def test_strict_mode_verified(self):
        """High NLI + low retrieval → STRICT mode, still VERIFIED."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.5, nli_score=0.96,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["status"] == "VERIFIED"
        assert v["mode"] == "STRICT"
        assert v["passed"] is True
        assert v["threshold"] == 0.95

    def test_strict_mode_hallucination(self):
        """Low NLI + low retrieval → STRICT mode, HALLUCINATION."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.5, nli_score=0.80,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["status"] == "HALLUCINATION"
        assert v["mode"] == "STRICT"
        assert v["passed"] is False

    def test_lenient_mode_verified(self):
        """Moderate NLI + high retrieval → LENIENT mode, VERIFIED."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.85, nli_score=0.75,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["status"] == "VERIFIED"
        assert v["mode"] == "LENIENT"
        assert v["passed"] is True
        assert v["threshold"] == 0.70

    def test_lenient_mode_hallucination(self):
        """Low NLI + high retrieval → LENIENT mode, still HALLUCINATION."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.85, nli_score=0.50,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["status"] == "HALLUCINATION"
        assert v["mode"] == "LENIENT"
        assert v["passed"] is False

    def test_pivot_boundary_goes_lenient(self):
        """Retrieval exactly at pivot → LENIENT (>= comparison)."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.75, nli_score=0.72,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["mode"] == "LENIENT"
        assert v["passed"] is True

    def test_nli_exactly_at_threshold(self):
        """NLI exactly equal to threshold → VERIFIED (>= comparison)."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.5, nli_score=0.95,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["passed"] is True

    def test_zero_scores(self):
        """Both scores at 0 → STRICT mode, HALLUCINATION."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.0, nli_score=0.0,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["status"] == "HALLUCINATION"
        assert v["mode"] == "STRICT"

    def test_perfect_scores(self):
        """Both scores at 1.0 → LENIENT mode, VERIFIED."""
        v = self.engine.calculate_verdict(
            retrieval_score=1.0, nli_score=1.0,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        assert v["status"] == "VERIFIED"
        assert v["mode"] == "LENIENT"

    def test_response_contains_all_fields(self):
        """Verdict dict has all expected keys."""
        v = self.engine.calculate_verdict(
            retrieval_score=0.5, nli_score=0.8,
            pivot=0.75, strict_threshold=0.95, lenient_threshold=0.70,
        )
        expected_keys = {"status", "mode", "threshold", "nli_score",
                         "retrieval_score", "reasoning", "passed"}
        assert set(v.keys()) == expected_keys


# ======================================================================
# Continuous verdict (sqrt / sigmoid)
# ======================================================================

class TestCalculateVerdictContinuous:
    """Test continuous Cw-CONLI threshold variants."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = object.__new__(AFLHREngine)

    def test_sqrt_threshold_decreases_with_retrieval(self):
        """Higher retrieval → lower threshold (more lenient) for sqrt."""
        v_low = self.engine.calculate_verdict_continuous(
            retrieval_score=0.1, nli_score=0.5,
            T_strict=0.9, T_lenient=0.3, method="sqrt",
        )
        v_high = self.engine.calculate_verdict_continuous(
            retrieval_score=0.9, nli_score=0.5,
            T_strict=0.9, T_lenient=0.3, method="sqrt",
        )
        assert v_low["threshold"] > v_high["threshold"]

    def test_sigmoid_threshold_decreases_with_retrieval(self):
        """Higher retrieval → lower threshold for sigmoid."""
        v_low = self.engine.calculate_verdict_continuous(
            retrieval_score=0.1, nli_score=0.5,
            T_strict=0.9, T_lenient=0.3, method="sigmoid",
        )
        v_high = self.engine.calculate_verdict_continuous(
            retrieval_score=0.9, nli_score=0.5,
            T_strict=0.9, T_lenient=0.3, method="sigmoid",
        )
        assert v_low["threshold"] > v_high["threshold"]

    def test_sqrt_at_zero_retrieval(self):
        """sqrt(0) = 0, so threshold = T_strict."""
        v = self.engine.calculate_verdict_continuous(
            retrieval_score=0.0, nli_score=0.5,
            T_strict=0.9, T_lenient=0.3, method="sqrt",
        )
        assert abs(v["threshold"] - 0.9) < 1e-6

    def test_sqrt_at_one_retrieval(self):
        """sqrt(1) = 1, so threshold = T_lenient."""
        v = self.engine.calculate_verdict_continuous(
            retrieval_score=1.0, nli_score=0.5,
            T_strict=0.9, T_lenient=0.3, method="sqrt",
        )
        assert abs(v["threshold"] - 0.3) < 1e-6

    def test_unknown_method_raises(self):
        """Unknown continuous method should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown continuous method"):
            self.engine.calculate_verdict_continuous(
                retrieval_score=0.5, nli_score=0.5,
                T_strict=0.9, T_lenient=0.3, method="linear",
            )

    def test_continuous_verdict_fields(self):
        """Continuous verdict has expected fields."""
        v = self.engine.calculate_verdict_continuous(
            retrieval_score=0.5, nli_score=0.5,
            T_strict=0.9, T_lenient=0.3, method="sqrt",
        )
        assert "CONTINUOUS_SQRT" == v["mode"]
        assert "threshold" in v
        assert "passed" in v


# ======================================================================
# Calibration guard
# ======================================================================

class TestCalibrationGuard:
    """Test that calibration boundary detection works."""

    def test_calibration_T_at_boundary_falls_back(self, tmp_path):
        """T >= 9.0 should fall back to T=1.0."""
        import json
        import engine as engine_mod
        cal_path = tmp_path / "cal.json"
        cal_path.write_text(json.dumps({"temperature": 10.0}))

        eng = object.__new__(AFLHREngine)
        eng.use_calibration = True
        eng.calibration_T = 1.0

        original = engine_mod.CALIBRATION_TEMP_PATH
        engine_mod.CALIBRATION_TEMP_PATH = str(cal_path)
        try:
            eng._load_calibration()
            assert eng.calibration_T == 1.0  # fell back
        finally:
            engine_mod.CALIBRATION_TEMP_PATH = original

    def test_calibration_normal_T_loads(self, tmp_path):
        """Normal T (e.g. 1.5) should load successfully."""
        import json
        import engine as engine_mod
        cal_path = tmp_path / "cal.json"
        cal_path.write_text(json.dumps({"temperature": 1.5}))

        eng = object.__new__(AFLHREngine)
        eng.use_calibration = True
        eng.calibration_T = 1.0

        original = engine_mod.CALIBRATION_TEMP_PATH
        engine_mod.CALIBRATION_TEMP_PATH = str(cal_path)
        try:
            eng._load_calibration()
            assert eng.calibration_T == 1.5
        finally:
            engine_mod.CALIBRATION_TEMP_PATH = original

    def test_calibration_missing_file(self, tmp_path):
        """Missing calibration file should stay at T=1.0."""
        import engine as engine_mod

        eng = object.__new__(AFLHREngine)
        eng.use_calibration = True
        eng.calibration_T = 1.0

        original = engine_mod.CALIBRATION_TEMP_PATH
        engine_mod.CALIBRATION_TEMP_PATH = str(tmp_path / "nonexistent.json")
        try:
            eng._load_calibration()
            assert eng.calibration_T == 1.0
        finally:
            engine_mod.CALIBRATION_TEMP_PATH = original


# ======================================================================
# Integration tests (require model loading — slow)
# ======================================================================

@pytest.mark.slow
class TestEngineIntegration:
    """Integration tests that load real models."""

    def test_knowledge_base_indexed(self, engine_v1):
        """FAISS index should have all knowledge base passages."""
        assert engine_v1.faiss_index is not None
        assert engine_v1.faiss_index.ntotal == len(KNOWLEDGE_BASE)

    def test_retrieve_returns_valid_structure(self, engine_v1):
        """Retrieve returns expected dict structure."""
        result = engine_v1.retrieve("University of Westminster", k=2)
        assert "context" in result
        assert "retrieval_score" in result
        assert "documents" in result
        assert 0 <= result["retrieval_score"] <= 1
        assert len(result["documents"]) == 2

    def test_retrieve_relevant_topic(self, engine_v1):
        """Westminster query should retrieve Westminster passages."""
        result = engine_v1.retrieve("When was University of Westminster founded?")
        assert "Westminster" in result["context"]

    def test_retrieve_distractor_lower_score(self, engine_v1):
        """Sri Lanka query should have lower score for Westminster index."""
        r_relevant = engine_v1.retrieve("University of Westminster history")
        r_distractor = engine_v1.retrieve("tropical monsoon weather patterns")
        # Distractor should score lower (less relevant to most passages)
        assert r_relevant["retrieval_score"] >= r_distractor["retrieval_score"]

    def test_verify_entailment(self, engine_v1):
        """Clear entailment should score high."""
        score = engine_v1.verify(
            premise="The sky is blue.",
            hypothesis="The sky is blue.",
        )
        assert score > 0.8

    def test_verify_contradiction(self, engine_v1):
        """Clear contradiction should score low."""
        score = engine_v1.verify(
            premise="The sky is blue.",
            hypothesis="The sky is red and green.",
        )
        assert score < 0.3

    def test_verify_empty_hypothesis(self, engine_v1):
        """Empty hypothesis should not crash."""
        score = engine_v1.verify(premise="The sky is blue.", hypothesis="")
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_verify_windowed_short_premise(self, engine_v2):
        """Short premise should use single-pass (not windowed)."""
        result = engine_v2.verify_windowed(
            premise="The sky is blue.",
            hypothesis="The sky is blue.",
        )
        assert result["method"] == "single_pass"
        assert result["n_windows"] == 1
        assert result["score"] > 0.5

    def test_verify_windowed_long_premise(self, engine_v2):
        """Long premise should trigger windowed NLI."""
        long_premise = " ".join(["This is a test sentence about various topics."] * 200)
        result = engine_v2.verify_windowed(
            premise=long_premise,
            hypothesis="This is about various topics.",
        )
        assert result["n_windows"] >= 1
        assert 0 <= result["score"] <= 1

    def test_decompose_claims_multiple(self, engine_v2):
        """Multi-sentence text should decompose into multiple claims."""
        text = "The sky is blue. Water is wet. Fire is hot."
        claims = engine_v2.decompose_claims(text)
        assert len(claims) == 3

    def test_decompose_claims_single(self, engine_v2):
        """Single sentence should return one claim."""
        claims = engine_v2.decompose_claims("The sky is blue.")
        assert len(claims) == 1

    def test_decompose_claims_empty(self, engine_v2):
        """Empty string should return empty list."""
        claims = engine_v2.decompose_claims("")
        assert len(claims) == 0

    def test_decompose_claims_short_fragments_filtered(self, engine_v2):
        """Fragments under 5 chars should be filtered out."""
        claims = engine_v2.decompose_claims("Hi. The sky is blue. Ok.")
        # "Hi." and "Ok." are under 5 chars — should be filtered
        assert all(len(c) >= 5 for c in claims)

    def test_verify_decomposed_structure(self, engine_v2):
        """Decomposed verification returns expected structure."""
        result = engine_v2.verify_decomposed(
            premise="The University of Westminster was founded in 1838.",
            hypothesis="Westminster was founded in 1838. It is in London.",
        )
        assert "score" in result
        assert "mean_score" in result
        assert "per_claim" in result
        assert "n_claims" in result
        assert result["n_claims"] == 2
        assert len(result["per_claim"]) == 2
        # Min aggregation: score should be <= mean
        assert result["score"] <= result["mean_score"] + 1e-6

    def test_offline_generation(self, engine_v1):
        """Offline mode returns mock response."""
        from config import OFFLINE_MOCK_RESPONSE
        response = engine_v1.generate("context", "query", offline_mode=True)
        assert response == OFFLINE_MOCK_RESPONSE

    def test_precompute_scores_structure(self, engine_v1):
        """precompute_scores returns all expected fields."""
        scores = engine_v1.precompute_scores(
            knowledge="The sky is blue.",
            query="What color is the sky?",
            response="The sky is blue.",
        )
        expected = {"retrieval_score", "nli_score", "nli_score_whole",
                    "nli_mean_score", "n_claims", "n_windows",
                    "nli_method", "latency_ms"}
        assert expected == set(scores.keys())
        assert scores["nli_method"] == "whole"  # v1 engine

    def test_precompute_scores_v2_decomposed(self, engine_v2):
        """v2 precompute uses decomposed method."""
        scores = engine_v2.precompute_scores(
            knowledge="The sky is blue.",
            query="What color is the sky?",
            response="The sky is blue.",
        )
        assert scores["nli_method"] == "decomposed"
