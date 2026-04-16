"""
AFLHR Lite - Evaluation Harness
Pre-computes retrieval + NLI scores, then applies condition logic
(C1/C2/C3) to produce metrics.

AI Disclosure: Development of this module was assisted by AI tools
for code structuring, debugging, and refactoring. The evaluation methodology
and experimental design are the author's own work.

Usage:
  # Pre-compute scores (slow - requires model inference)
  python evaluate.py --precompute --split dev
  python evaluate.py --precompute --split dev --limit 50   # smoke test

  # v2: Pre-compute with decomposition + windowed NLI
  python evaluate.py --precompute --split dev --version v2
  python evaluate.py --precompute --split test --version v2

  # Evaluate a condition (fast - uses pre-computed scores)
  python evaluate.py --condition C1 --split dev
  python evaluate.py --condition C2 --split dev --params '{"T_static": 0.75}'
  python evaluate.py --condition C3 --split dev --params '{"method":"tiered","pivot":0.75,"T_strict":0.95,"T_lenient":0.70}'

  # v2 evaluation using decomposed NLI scores
  python evaluate.py --condition C2 --split test --version v2
  python evaluate.py --condition C2 --split test --version v2 --nli-key nli_score_whole  # ablation
"""

import argparse
import csv
import json
import math
import os
import time

import numpy as np
from sklearn.metrics import (
    f1_score, precision_score, recall_score, confusion_matrix,
)

from config import (
    RESULTS_DIR,
    DEFAULT_PIVOT,
    DEFAULT_STRICT_THRESHOLD,
    DEFAULT_LENIENT_THRESHOLD,
)
from dataset import load_halueval, split_dev_test


# ---------------------------------------------------------------------------
# Pre-computation
# ---------------------------------------------------------------------------

# v1 CSV columns (backward compat)
FIELDNAMES_V1 = [
    "sample_id", "task", "label", "retrieval_score", "nli_score",
    "latency_ms",
]

# v2 CSV columns (superset of v1)
FIELDNAMES_V2 = [
    "sample_id", "task", "label", "retrieval_score", "nli_score",
    "nli_score_whole", "nli_mean_score", "n_claims", "n_windows",
    "nli_method", "latency_ms",
]


def run_precomputation(engine, samples, output_path, limit=None,
                       checkpoint_every=100, version="v1"):
    """Pre-compute retrieval and NLI scores for all samples.

    Supports checkpointing: if output_path already has partial results,
    only the remaining samples are processed.
    """
    from tqdm import tqdm

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = FIELDNAMES_V2 if version == "v2" else FIELDNAMES_V1

    # Load existing checkpoint
    computed = {}
    file_exists = os.path.exists(output_path)
    if file_exists:
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                computed[int(row["sample_id"])] = row
        print(f"Loaded {len(computed)} pre-computed scores from checkpoint")

    if limit:
        samples = samples[:limit]

    remaining = [s for s in samples if s["sample_id"] not in computed]
    print(f"Samples to process: {len(remaining)} (of {len(samples)} total)")

    if not remaining:
        print("All samples already computed.")
        return output_path

    if not file_exists:
        f = open(output_path, "w", newline="")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    else:
        f = open(output_path, "a", newline="")
        writer = csv.DictWriter(f, fieldnames=fieldnames)

    try:
        for i, sample in enumerate(tqdm(remaining, desc="Pre-computing")):
            # For QA, query = question; for summarization, query = response
            if sample["task"] == "qa":
                query = sample["question"]
            else:
                query = sample["response"]

            scores = engine.precompute_scores(
                knowledge=sample["knowledge"],
                query=query,
                response=sample["response"],
            )

            row = {
                "sample_id": sample["sample_id"],
                "task": sample["task"],
                "label": sample["label"],
                "retrieval_score": scores["retrieval_score"],
                "nli_score": scores["nli_score"],
                "latency_ms": scores["latency_ms"],
            }

            if version == "v2":
                row.update({
                    "nli_score_whole": scores.get("nli_score_whole", scores["nli_score"]),
                    "nli_mean_score": scores.get("nli_mean_score", scores["nli_score"]),
                    "n_claims": scores.get("n_claims", 1),
                    "n_windows": scores.get("n_windows", 1),
                    "nli_method": scores.get("nli_method", "whole"),
                })

            writer.writerow(row)

            if (i + 1) % checkpoint_every == 0:
                f.flush()
    finally:
        f.close()

    print(f"Scores saved to {output_path}")
    return output_path


def run_precomputation_realistic(engine, split_samples, all_qa_samples,
                                  output_path, limit=None,
                                  checkpoint_every=100, version="v1"):
    """Pre-compute scores using realistic shared-index retrieval (QA only).

    Builds a FAISS index from ALL QA knowledge passages, then for each
    sample retrieves from this shared pool and runs NLI on the *retrieved*
    context (not the ground-truth knowledge).
    """
    from tqdm import tqdm

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = FIELDNAMES_V2 if version == "v2" else FIELDNAMES_V1

    # Only QA samples
    samples = [s for s in split_samples if s["task"] == "qa"]
    if limit:
        samples = samples[:limit]

    # Build shared FAISS index from ALL unique QA knowledge passages
    all_passages = list(dict.fromkeys(
        s["knowledge"] for s in all_qa_samples
    ))
    print(f"Building shared FAISS index ({len(all_passages)} passages)...")
    index = engine.build_index(all_passages)
    print(f"Index built: {index.ntotal} vectors")

    # Load checkpoint
    computed = {}
    file_exists = os.path.exists(output_path)
    if file_exists:
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                computed[int(row["sample_id"])] = row
        print(f"Loaded {len(computed)} from checkpoint")

    remaining = [s for s in samples if s["sample_id"] not in computed]
    print(f"Samples to process: {len(remaining)} (of {len(samples)})")

    if not remaining:
        print("All samples already computed.")
        return output_path

    if not file_exists:
        f = open(output_path, "w", newline="")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    else:
        f = open(output_path, "a", newline="")
        writer = csv.DictWriter(f, fieldnames=fieldnames)

    try:
        for i, sample in enumerate(tqdm(remaining,
                                        desc="Pre-computing (realistic)")):
            start = time.perf_counter()

            # Retrieve from shared index using the question
            result = engine.retrieve_from_index(
                query=sample["question"],
                index=index,
                passages=all_passages,
                k=2,
            )
            retrieval_score = result["retrieval_score"]
            retrieved_context = result["context"]

            # NLI on *retrieved* context (not ground-truth knowledge)
            if version == "v2" and (engine.use_decomposition or engine.use_windowed_nli):
                scores = engine.precompute_scores(
                    knowledge=retrieved_context,
                    query=sample["question"],
                    response=sample["response"],
                )
                # Override retrieval_score with the one from shared index
                scores["retrieval_score"] = retrieval_score
            else:
                nli_score = engine.verify(
                    premise=retrieved_context,
                    hypothesis=sample["response"],
                )
                scores = {
                    "nli_score": nli_score,
                    "nli_score_whole": nli_score,
                    "nli_mean_score": nli_score,
                    "n_claims": 1,
                    "n_windows": 1,
                    "nli_method": "whole",
                }

            elapsed = time.perf_counter() - start

            row = {
                "sample_id": sample["sample_id"],
                "task": sample["task"],
                "label": sample["label"],
                "retrieval_score": retrieval_score,
                "nli_score": scores["nli_score"],
                "latency_ms": round(elapsed * 1000, 2),
            }

            if version == "v2":
                row.update({
                    "nli_score_whole": scores.get("nli_score_whole", scores["nli_score"]),
                    "nli_mean_score": scores.get("nli_mean_score", scores["nli_score"]),
                    "n_claims": scores.get("n_claims", 1),
                    "n_windows": scores.get("n_windows", 1),
                    "nli_method": scores.get("nli_method", "whole"),
                })

            writer.writerow(row)

            if (i + 1) % checkpoint_every == 0:
                f.flush()
    finally:
        f.close()

    print(f"Scores saved to {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Score loading & condition application
# ---------------------------------------------------------------------------

def load_precomputed(path):
    """Load pre-computed scores from CSV (backward-compatible with v1 and v2)."""
    scores = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = {
                "sample_id": int(row["sample_id"]),
                "task": row["task"],
                "label": int(row["label"]),
                "retrieval_score": float(row["retrieval_score"]),
                "nli_score": float(row["nli_score"]),
                "latency_ms": float(row["latency_ms"]),
            }
            # v2 columns (optional - backward compatible)
            if "nli_score_whole" in row and row["nli_score_whole"]:
                entry["nli_score_whole"] = float(row["nli_score_whole"])
            if "nli_mean_score" in row and row["nli_mean_score"]:
                entry["nli_mean_score"] = float(row["nli_mean_score"])
            if "n_claims" in row and row["n_claims"]:
                entry["n_claims"] = int(row["n_claims"])
            if "n_windows" in row and row["n_windows"]:
                entry["n_windows"] = int(row["n_windows"])
            if "nli_method" in row and row["nli_method"]:
                entry["nli_method"] = row["nli_method"]

            scores.append(entry)
    return scores


def apply_condition(scores, condition, params, nli_key="nli_score"):
    """Apply condition logic to pre-computed scores.

    Args:
        scores: List of score dicts from load_precomputed()
        condition: "C1", "C2", or "C3"
        params: Condition-specific parameters
        nli_key: Which NLI score column to use (default "nli_score",
                 can be "nli_score_whole" for ablation)

    Returns list of predictions (0 = verified, 1 = hallucination).
    """
    predictions = []

    for s in scores:
        if condition == "C1":
            pred = 0  # Always accept (no NLI)

        elif condition == "C2":
            nli = s.get(nli_key, s["nli_score"])
            pred = 0 if nli >= params["T_static"] else 1

        elif condition == "C3":
            rs = s["retrieval_score"]
            nli = s.get(nli_key, s["nli_score"])
            method = params.get("method", "tiered")

            if method == "tiered":
                threshold = (params["T_strict"]
                             if rs < params["pivot"]
                             else params["T_lenient"])
            elif method == "sqrt":
                threshold = (params["T_strict"]
                             - (params["T_strict"] - params["T_lenient"])
                             * math.sqrt(rs))
            elif method == "sigmoid":
                k = params.get("sigmoid_k", 10)
                p = params.get("sigmoid_pivot", 0.5)
                threshold = (params["T_lenient"]
                             + (params["T_strict"] - params["T_lenient"])
                             / (1 + math.exp(k * (rs - p))))
            else:
                raise ValueError(f"Unknown C3 method: {method}")

            pred = 0 if nli >= threshold else 1
        else:
            raise ValueError(f"Unknown condition: {condition}")

        predictions.append(pred)

    return predictions


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(labels, predictions, latencies=None):
    """Compute evaluation metrics from labels and predictions."""
    labels = np.array(labels)
    predictions = np.array(predictions)

    if len(labels) == 0:
        return {
            "f1": 0.0, "precision": 0.0, "recall": 0.0, "accuracy": 0.0,
            "over_flagging_rate": 0.0, "tp": 0, "fp": 0, "tn": 0, "fn": 0,
        }

    cm = confusion_matrix(labels, predictions, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "f1": round(f1_score(labels, predictions, zero_division=0), 4),
        "precision": round(precision_score(labels, predictions,
                                           zero_division=0), 4),
        "recall": round(recall_score(labels, predictions,
                                     zero_division=0), 4),
        "accuracy": round(float(tp + tn) / len(labels), 4),
        "over_flagging_rate": round(float(fp) / (fp + tn), 4) if (fp + tn) > 0 else 0.0,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }

    if latencies:
        metrics["mean_latency_ms"] = round(float(np.mean(latencies)), 2)
        metrics["median_latency_ms"] = round(float(np.median(latencies)), 2)
        metrics["p95_latency_ms"] = round(float(np.percentile(latencies, 95)), 2)

    return metrics


def run_evaluation(scores_path, condition, params, split_name="dev",
                   task_filter=None, limit=None, nli_key="nli_score"):
    """Run full evaluation for a condition + parameter set."""
    scores = load_precomputed(scores_path)

    if task_filter:
        scores = [s for s in scores if s["task"] == task_filter]
    if limit:
        scores = scores[:limit]

    labels = [s["label"] for s in scores]
    latencies = [s["latency_ms"] for s in scores]
    predictions = apply_condition(scores, condition, params, nli_key=nli_key)

    metrics = compute_metrics(labels, predictions, latencies)

    return {
        "condition": condition,
        "params": params,
        "split": split_name,
        "task": task_filter or "all",
        "nli_key": nli_key,
        "n_samples": len(scores),
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AFLHR Evaluation Harness")
    parser.add_argument("--precompute", action="store_true",
                        help="Pre-compute retrieval + NLI scores")
    parser.add_argument("--condition", choices=["C1", "C2", "C3"],
                        help="Condition to evaluate")
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--task", default=None,
                        choices=["qa", "summarization"])
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of samples")
    parser.add_argument("--params", type=str, default=None,
                        help="JSON string of condition parameters")
    parser.add_argument("--realistic", action="store_true",
                        help="Experiment 2: shared-index retrieval (QA only)")
    parser.add_argument("--version", default="v1", choices=["v1", "v2"],
                        help="v1=baseline, v2=decomposition+windowed+bge")
    parser.add_argument("--nli-key", default="nli_score",
                        help="NLI score column to use (default: nli_score)")
    parser.add_argument("--tuned", action="store_true",
                        help="Auto-load best params from tuning results")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)

    suffix = "_realistic" if args.realistic else ""
    version_suffix = f"_{args.version}" if args.version != "v1" else ""
    scores_path = os.path.join(RESULTS_DIR,
                               f"scores_{args.split}{suffix}{version_suffix}.csv")

    if args.precompute:
        from engine import AFLHREngine

        if args.version == "v2":
            engine = AFLHREngine(
                use_windowed_nli=True,
                use_decomposition=True,
                use_calibration=False,  # T=10 at boundary — calibration hurts
                use_bge_embeddings=True,
            )
        else:
            engine = AFLHREngine()

        samples = load_halueval()
        dev, test = split_dev_test(samples)
        data = dev if args.split == "dev" else test

        if args.realistic:
            all_qa = [s for s in samples if s["task"] == "qa"]
            run_precomputation_realistic(
                engine, data, all_qa, scores_path, limit=args.limit,
                version=args.version,
            )
        else:
            run_precomputation(engine, data, scores_path, limit=args.limit,
                               version=args.version)

    elif args.condition:
        # Parse params: --tuned loads from tuning results, --params takes JSON, else defaults
        if args.params:
            params = json.loads(args.params)
        elif args.tuned and args.condition in ("C2", "C3"):
            # Load best params from tuning results file
            rsuffix = "_realistic" if args.realistic else ""
            tuning_path = os.path.join(
                RESULTS_DIR, f"tuning_results{rsuffix}{version_suffix}.json")
            if not os.path.exists(tuning_path):
                print(f"Error: tuning results not found at {tuning_path}")
                print(f"Run: python tune.py --split dev{rsuffix}"
                      f"{' --version ' + args.version if args.version != 'v1' else ''}")
                return
            with open(tuning_path) as f:
                tuning = json.load(f)
            if args.condition == "C2":
                params = tuning["C2"]["best_params"]
            else:
                # Pick best C3 variant by F1
                best_c3 = max(
                    ["C3_tiered", "C3_sqrt", "C3_sigmoid"],
                    key=lambda k: tuning[k]["best_f1"],
                )
                params = tuning[best_c3]["best_params"]
            print(f"Loaded tuned params from {tuning_path}: {params}")
        else:
            if args.condition == "C1":
                params = {}
            elif args.condition == "C2":
                params = {"T_static": 0.75}
            elif args.condition == "C3":
                params = {
                    "method": "tiered",
                    "pivot": DEFAULT_PIVOT,
                    "T_strict": DEFAULT_STRICT_THRESHOLD,
                    "T_lenient": DEFAULT_LENIENT_THRESHOLD,
                }

        result = run_evaluation(
            scores_path, args.condition, params,
            split_name=args.split, task_filter=args.task, limit=args.limit,
            nli_key=args.nli_key,
        )

        # Print results
        m = result["metrics"]
        print(f"\n{'='*60}")
        print(f"Condition: {result['condition']} | Split: {result['split']}"
              f" | Task: {result['task']} | NLI key: {result['nli_key']}")
        print(f"Params: {result['params']}")
        print(f"N samples: {result['n_samples']}")
        print(f"{'='*60}")
        print(f"F1:          {m['f1']:.4f}")
        print(f"Precision:   {m['precision']:.4f}")
        print(f"Recall:      {m['recall']:.4f}")
        print(f"Accuracy:    {m['accuracy']:.4f}")
        print(f"Over-flag:   {m['over_flagging_rate']:.4f}")
        print(f"TP={m['tp']}  FP={m['fp']}  TN={m['tn']}  FN={m['fn']}")
        if "mean_latency_ms" in m:
            print(f"Latency:     {m['mean_latency_ms']:.1f}ms (mean), "
                  f"{m['p95_latency_ms']:.1f}ms (p95)")

        # Save result
        task_tag = args.task or "all"
        result_path = os.path.join(
            RESULTS_DIR,
            f"eval_{args.condition}_{args.split}_{task_tag}{suffix}{version_suffix}.json",
        )
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to {result_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
