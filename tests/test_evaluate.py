"""Tests for evaluation harness — condition logic, metrics, and dataset loading."""

import math
import pytest
import numpy as np

from evaluate import apply_condition, compute_metrics, load_precomputed
from dataset import load_halueval, split_dev_test
from config import EXPERIMENT_SEED, DEV_SPLIT_RATIO


# ======================================================================
# apply_condition
# ======================================================================

class TestApplyCondition:
    """Test condition application on pre-computed scores."""

    def _make_scores(self, retrieval=0.5, nli=0.8, label=1):
        return [{
            "sample_id": 0, "task": "qa", "label": label,
            "retrieval_score": retrieval, "nli_score": nli,
            "latency_ms": 10.0,
        }]

    def test_c1_always_accepts(self):
        """C1 (RAG-only) should always predict 0 (verified)."""
        scores = self._make_scores(nli=0.01)
        preds = apply_condition(scores, "C1", {})
        assert preds == [0]

    def test_c2_above_threshold(self):
        """C2: NLI >= T_static → verified (0)."""
        scores = self._make_scores(nli=0.80)
        preds = apply_condition(scores, "C2", {"T_static": 0.75})
        assert preds == [0]

    def test_c2_below_threshold(self):
        """C2: NLI < T_static → hallucination (1)."""
        scores = self._make_scores(nli=0.70)
        preds = apply_condition(scores, "C2", {"T_static": 0.75})
        assert preds == [1]

    def test_c2_at_threshold(self):
        """C2: NLI exactly at T_static → verified (>= comparison)."""
        scores = self._make_scores(nli=0.75)
        preds = apply_condition(scores, "C2", {"T_static": 0.75})
        assert preds == [0]

    def test_c3_tiered_strict(self):
        """C3 tiered: low retrieval → uses strict threshold."""
        scores = self._make_scores(retrieval=0.5, nli=0.80)
        preds = apply_condition(scores, "C3", {
            "method": "tiered", "pivot": 0.75,
            "T_strict": 0.90, "T_lenient": 0.60,
        })
        assert preds == [1]  # 0.80 < 0.90 → hallucination

    def test_c3_tiered_lenient(self):
        """C3 tiered: high retrieval → uses lenient threshold."""
        scores = self._make_scores(retrieval=0.80, nli=0.70)
        preds = apply_condition(scores, "C3", {
            "method": "tiered", "pivot": 0.75,
            "T_strict": 0.90, "T_lenient": 0.60,
        })
        assert preds == [0]  # 0.70 >= 0.60 → verified

    def test_c3_sqrt(self):
        """C3 sqrt: threshold computed via sqrt formula."""
        scores = self._make_scores(retrieval=0.64, nli=0.5)
        preds = apply_condition(scores, "C3", {
            "method": "sqrt", "T_strict": 0.9, "T_lenient": 0.3,
        })
        # T = 0.9 - (0.9-0.3)*sqrt(0.64) = 0.9 - 0.6*0.8 = 0.42
        # nli=0.5 >= 0.42 → verified
        assert preds == [0]

    def test_c3_sigmoid(self):
        """C3 sigmoid: threshold computed via sigmoid formula."""
        scores = self._make_scores(retrieval=0.5, nli=0.65)
        preds = apply_condition(scores, "C3", {
            "method": "sigmoid", "T_strict": 0.9, "T_lenient": 0.3,
            "sigmoid_k": 10, "sigmoid_pivot": 0.5,
        })
        # At pivot, sigmoid term = 0.5, so T = 0.3 + 0.6/2 = 0.6
        # nli=0.65 >= 0.6 → verified
        assert preds == [0]

    def test_unknown_condition_raises(self):
        scores = self._make_scores()
        with pytest.raises(ValueError, match="Unknown condition"):
            apply_condition(scores, "C4", {})

    def test_unknown_c3_method_raises(self):
        scores = self._make_scores()
        with pytest.raises(ValueError, match="Unknown C3 method"):
            apply_condition(scores, "C3", {"method": "linear", "T_strict": 0.9, "T_lenient": 0.3})

    def test_alternate_nli_key(self):
        """Should use nli_score_whole when specified."""
        scores = [{
            "sample_id": 0, "task": "qa", "label": 1,
            "retrieval_score": 0.5, "nli_score": 0.80,
            "nli_score_whole": 0.50,  # lower than nli_score
            "latency_ms": 10.0,
        }]
        # With default key, 0.80 >= 0.75 → verified
        preds_default = apply_condition(scores, "C2", {"T_static": 0.75})
        assert preds_default == [0]
        # With whole key, 0.50 < 0.75 → hallucination
        preds_whole = apply_condition(scores, "C2", {"T_static": 0.75},
                                      nli_key="nli_score_whole")
        assert preds_whole == [1]

    def test_multiple_samples(self):
        """Apply condition across multiple samples."""
        scores = [
            {"sample_id": 0, "task": "qa", "label": 1,
             "retrieval_score": 0.5, "nli_score": 0.80, "latency_ms": 10},
            {"sample_id": 1, "task": "qa", "label": 0,
             "retrieval_score": 0.5, "nli_score": 0.60, "latency_ms": 10},
            {"sample_id": 2, "task": "qa", "label": 1,
             "retrieval_score": 0.5, "nli_score": 0.75, "latency_ms": 10},
        ]
        preds = apply_condition(scores, "C2", {"T_static": 0.75})
        assert preds == [0, 1, 0]  # 0.80>=0.75, 0.60<0.75, 0.75>=0.75


# ======================================================================
# compute_metrics
# ======================================================================

class TestComputeMetrics:
    def test_perfect_predictions(self):
        labels = [1, 1, 0, 0]
        preds = [1, 1, 0, 0]
        m = compute_metrics(labels, preds)
        assert m["f1"] == 1.0
        assert m["precision"] == 1.0
        assert m["recall"] == 1.0
        assert m["accuracy"] == 1.0
        assert m["over_flagging_rate"] == 0.0

    def test_all_wrong(self):
        labels = [1, 1, 0, 0]
        preds = [0, 0, 1, 1]
        m = compute_metrics(labels, preds)
        assert m["f1"] == 0.0
        assert m["tp"] == 0
        assert m["fp"] == 2
        assert m["fn"] == 2
        assert m["tn"] == 0

    def test_empty_input(self):
        m = compute_metrics([], [])
        assert m["f1"] == 0.0
        assert m["tp"] == 0

    def test_all_positive(self):
        """All predicted positive."""
        labels = [1, 0, 1, 0]
        preds = [1, 1, 1, 1]
        m = compute_metrics(labels, preds)
        assert m["recall"] == 1.0
        assert m["fp"] == 2
        assert m["over_flagging_rate"] == 1.0  # FP / (FP+TN) = 2/2

    def test_all_negative(self):
        """All predicted negative (like C1)."""
        labels = [1, 1, 0, 0]
        preds = [0, 0, 0, 0]
        m = compute_metrics(labels, preds)
        assert m["recall"] == 0.0
        assert m["f1"] == 0.0
        assert m["tn"] == 2

    def test_with_latencies(self):
        labels = [1, 0]
        preds = [1, 0]
        m = compute_metrics(labels, preds, latencies=[100.0, 200.0])
        assert m["mean_latency_ms"] == 150.0
        assert m["median_latency_ms"] == 150.0

    def test_confusion_matrix_counts(self):
        """Verify TP/FP/TN/FN add up to total."""
        labels = [1, 1, 0, 0, 1, 0]
        preds = [1, 0, 1, 0, 1, 0]
        m = compute_metrics(labels, preds)
        total = m["tp"] + m["fp"] + m["tn"] + m["fn"]
        assert total == len(labels)


# ======================================================================
# Dataset split determinism
# ======================================================================

class TestDatasetSplit:
    def test_split_is_deterministic(self):
        """Same seed should produce identical splits."""
        samples = [{"sample_id": i, "task": "qa"} for i in range(100)]
        dev1, test1 = split_dev_test(samples, dev_ratio=0.7, seed=42)
        dev2, test2 = split_dev_test(samples, dev_ratio=0.7, seed=42)
        assert [s["sample_id"] for s in dev1] == [s["sample_id"] for s in dev2]
        assert [s["sample_id"] for s in test1] == [s["sample_id"] for s in test2]

    def test_split_ratio(self):
        """Split should respect the dev_ratio."""
        samples = [{"sample_id": i, "task": "qa"} for i in range(100)]
        dev, test = split_dev_test(samples, dev_ratio=0.7, seed=42)
        assert len(dev) == 70
        assert len(test) == 30

    def test_no_overlap(self):
        """Dev and test sets should be disjoint."""
        samples = [{"sample_id": i, "task": "qa"} for i in range(100)]
        dev, test = split_dev_test(samples, dev_ratio=0.7, seed=42)
        dev_ids = {s["sample_id"] for s in dev}
        test_ids = {s["sample_id"] for s in test}
        assert dev_ids & test_ids == set()  # no overlap
        assert dev_ids | test_ids == set(range(100))  # complete coverage

    def test_different_seeds_different_splits(self):
        """Different seeds should produce different splits."""
        samples = [{"sample_id": i, "task": "qa"} for i in range(100)]
        dev1, _ = split_dev_test(samples, dev_ratio=0.7, seed=42)
        dev2, _ = split_dev_test(samples, dev_ratio=0.7, seed=99)
        ids1 = [s["sample_id"] for s in dev1]
        ids2 = [s["sample_id"] for s in dev2]
        assert ids1 != ids2


# ======================================================================
# CSV round-trip
# ======================================================================

class TestLoadPrecomputed:
    def test_round_trip_v1(self, tmp_path):
        """Write v1 CSV and load it back."""
        import csv
        from evaluate import FIELDNAMES_V1

        path = tmp_path / "scores.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES_V1)
            writer.writeheader()
            writer.writerow({
                "sample_id": 0, "task": "qa", "label": 1,
                "retrieval_score": 0.85, "nli_score": 0.72,
                "latency_ms": 15.5,
            })

        scores = load_precomputed(str(path))
        assert len(scores) == 1
        assert scores[0]["sample_id"] == 0
        assert scores[0]["retrieval_score"] == 0.85
        assert scores[0]["nli_score"] == 0.72
        assert scores[0]["label"] == 1

    def test_round_trip_v2(self, tmp_path):
        """Write v2 CSV and load back with extra columns."""
        import csv
        from evaluate import FIELDNAMES_V2

        path = tmp_path / "scores_v2.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES_V2)
            writer.writeheader()
            writer.writerow({
                "sample_id": 0, "task": "qa", "label": 0,
                "retrieval_score": 0.90, "nli_score": 0.65,
                "nli_score_whole": 0.70, "nli_mean_score": 0.68,
                "n_claims": 3, "n_windows": 5,
                "nli_method": "decomposed", "latency_ms": 42.1,
            })

        scores = load_precomputed(str(path))
        assert len(scores) == 1
        assert scores[0]["nli_score_whole"] == 0.70
        assert scores[0]["n_claims"] == 3
        assert scores[0]["nli_method"] == "decomposed"

    def test_v2_csv_backward_compatible(self, tmp_path):
        """v1 CSV (missing v2 columns) should load without error."""
        import csv
        from evaluate import FIELDNAMES_V1

        path = tmp_path / "scores_v1.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES_V1)
            writer.writeheader()
            writer.writerow({
                "sample_id": 0, "task": "qa", "label": 1,
                "retrieval_score": 0.5, "nli_score": 0.8,
                "latency_ms": 10,
            })

        scores = load_precomputed(str(path))
        # v2 fields should be absent (not error)
        assert "nli_score_whole" not in scores[0]
        assert scores[0]["nli_score"] == 0.8
