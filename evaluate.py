"""
AFLHR Lite - Evaluation Harness
Pre-computes retrieval + NLI scores, then applies condition logic
(C1/C2/C3) to produce metrics.

Usage:
  # Pre-compute scores (slow - requires model inference)
  python evaluate.py --precompute --split dev
  python evaluate.py --precompute --split dev --limit 50   # smoke test

  # Evaluate a condition (fast - uses pre-computed scores)
  python evaluate.py --condition C1 --split dev
  python evaluate.py --condition C2 --split dev --params '{"T_static": 0.75}'
  python evaluate.py --condition C3 --split dev --params '{"method":"tiered","pivot":0.75,"T_strict":0.95,"T_lenient":0.70}'
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

def run_precomputation(engine, samples, output_path, limit=None,
                       checkpoint_every=100):
    """Pre-compute retrieval and NLI scores for all samples.

    Supports checkpointing: if output_path already has partial results,
    only the remaining samples are processed.
    """
    from tqdm import tqdm

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

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

    fieldnames = [
        "sample_id", "task", "label", "retrieval_score", "nli_score",
        "latency_ms",
    ]

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

            writer.writerow({
                "sample_id": sample["sample_id"],
                "task": sample["task"],
                "label": sample["label"],
                "retrieval_score": scores["retrieval_score"],
                "nli_score": scores["nli_score"],
                "latency_ms": scores["latency_ms"],
            })

            if (i + 1) % checkpoint_every == 0:
                f.flush()
    finally:
        f.close()

    print(f"Scores saved to {output_path}")
    return output_path


def run_precomputation_realistic(engine, split_samples, all_qa_samples,
                                  output_path, limit=None,
                                  checkpoint_every=100):
    """Pre-compute scores using realistic shared-index retrieval (QA only).

    Builds a FAISS index from ALL QA knowledge passages, then for each
    sample retrieves from this shared pool and runs NLI on the *retrieved*
    context (not the ground-truth knowledge).
    """
    from tqdm import tqdm

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

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

    fieldnames = [
        "sample_id", "task", "label", "retrieval_score", "nli_score",
        "latency_ms",
    ]

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
            nli_score = engine.verify(
                premise=retrieved_context,
                hypothesis=sample["response"],
            )

            elapsed = time.perf_counter() - start

            writer.writerow({
                "sample_id": sample["sample_id"],
                "task": sample["task"],
                "label": sample["label"],
                "retrieval_score": retrieval_score,
                "nli_score": nli_score,
                "latency_ms": round(elapsed * 1000, 2),
            })

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
    """Load pre-computed scores from CSV."""
    scores = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append({
                "sample_id": int(row["sample_id"]),
                "task": row["task"],
                "label": int(row["label"]),
                "retrieval_score": float(row["retrieval_score"]),
                "nli_score": float(row["nli_score"]),
                "latency_ms": float(row["latency_ms"]),
            })
    return scores


def apply_condition(scores, condition, params):
    """Apply condition logic to pre-computed scores.

    Returns list of predictions (0 = verified, 1 = hallucination).
    """
    predictions = []

    for s in scores:
        if condition == "C1":
            pred = 0  # Always accept (no NLI)

        elif condition == "C2":
            pred = 0 if s["nli_score"] >= params["T_static"] else 1

        elif condition == "C3":
            rs = s["retrieval_score"]
            nli = s["nli_score"]
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
                   task_filter=None, limit=None):
    """Run full evaluation for a condition + parameter set."""
    scores = load_precomputed(scores_path)

    if task_filter:
        scores = [s for s in scores if s["task"] == task_filter]
    if limit:
        scores = scores[:limit]

    labels = [s["label"] for s in scores]
    latencies = [s["latency_ms"] for s in scores]
    predictions = apply_condition(scores, condition, params)

    metrics = compute_metrics(labels, predictions, latencies)

    return {
        "condition": condition,
        "params": params,
        "split": split_name,
        "task": task_filter or "all",
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
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)

    suffix = "_realistic" if args.realistic else ""
    scores_path = os.path.join(RESULTS_DIR,
                               f"scores_{args.split}{suffix}.csv")

    if args.precompute:
        from engine import AFLHREngine
        engine = AFLHREngine()

        samples = load_halueval()
        dev, test = split_dev_test(samples)
        data = dev if args.split == "dev" else test

        if args.realistic:
            all_qa = [s for s in samples if s["task"] == "qa"]
            run_precomputation_realistic(
                engine, data, all_qa, scores_path, limit=args.limit,
            )
        else:
            run_precomputation(engine, data, scores_path, limit=args.limit)

    elif args.condition:
        # Parse params (or use defaults)
        if args.params:
            params = json.loads(args.params)
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
        )

        # Print results
        m = result["metrics"]
        print(f"\n{'='*60}")
        print(f"Condition: {result['condition']} | Split: {result['split']}"
              f" | Task: {result['task']}")
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
            f"eval_{args.condition}_{args.split}_{task_tag}.json",
        )
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to {result_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
