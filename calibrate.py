"""
AFLHR Lite - NLI Temperature Scaling Calibration

Collects raw 3-class logits from dev set NLI runs and fits a single
temperature parameter T that minimizes negative log-likelihood.
Standard approach from Guo et al. (2017) "On Calibration of Modern Neural Networks".

Usage:
  python calibrate.py --split dev
  python calibrate.py --split dev --limit 500   # faster dev run
"""

import argparse
import csv
import json
import os
import time

import numpy as np
from scipy.optimize import minimize_scalar

from config import RESULTS_DIR, CALIBRATION_TEMP_PATH
from dataset import load_halueval, split_dev_test


def collect_logits(engine, samples, output_path, limit=None, checkpoint_every=100):
    """Collect raw 3-class NLI logits for calibration.

    Saves to CSV: sample_id, task, label, logit_contradiction, logit_neutral, logit_entailment
    """
    from tqdm import tqdm

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load checkpoint
    computed = set()
    file_exists = os.path.exists(output_path)
    if file_exists:
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                computed.add(int(row["sample_id"]))
        print(f"Loaded {len(computed)} from checkpoint")

    if limit:
        samples = samples[:limit]

    remaining = [s for s in samples if s["sample_id"] not in computed]
    print(f"Samples to process: {len(remaining)} (of {len(samples)} total)")

    if not remaining:
        print("All samples already computed.")
        return output_path

    fieldnames = [
        "sample_id", "task", "label",
        "logit_contradiction", "logit_neutral", "logit_entailment",
    ]

    if not file_exists:
        f = open(output_path, "w", newline="")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    else:
        f = open(output_path, "a", newline="")
        writer = csv.DictWriter(f, fieldnames=fieldnames)

    try:
        for i, sample in enumerate(tqdm(remaining, desc="Collecting logits")):
            logits = engine.verify_raw_logits(
                premise=sample["knowledge"],
                hypothesis=sample["response"],
            )

            writer.writerow({
                "sample_id": sample["sample_id"],
                "task": sample["task"],
                "label": sample["label"],
                "logit_contradiction": logits[0],
                "logit_neutral": logits[1],
                "logit_entailment": logits[2],
            })

            if (i + 1) % checkpoint_every == 0:
                f.flush()
    finally:
        f.close()

    print(f"Logits saved to {output_path}")
    return output_path


def fit_temperature(logits_path):
    """Fit temperature T by minimizing NLL on collected logits.

    For hallucination detection, the "true class" for NLI calibration is:
      - label=0 (faithful) -> entailment expected (class 2)
      - label=1 (hallucination) -> contradiction expected (class 0)

    Returns:
        dict with temperature, nll_before, nll_after
    """
    # Load logits
    logits_list = []
    targets = []
    with open(logits_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            logits_list.append([
                float(row["logit_contradiction"]),
                float(row["logit_neutral"]),
                float(row["logit_entailment"]),
            ])
            label = int(row["label"])
            # Map: faithful (0) -> entailment (2), hallucinated (1) -> contradiction (0)
            targets.append(0 if label == 1 else 2)

    logits_arr = np.array(logits_list)  # (N, 3)
    targets_arr = np.array(targets)      # (N,)

    def nll(T):
        """Negative log-likelihood with temperature scaling."""
        scaled = logits_arr / T
        # Numerically stable softmax
        shifted = scaled - scaled.max(axis=1, keepdims=True)
        exp_shifted = np.exp(shifted)
        log_sum_exp = np.log(exp_shifted.sum(axis=1))
        log_probs = shifted[np.arange(len(targets_arr)), targets_arr] - log_sum_exp
        return -log_probs.mean()

    nll_before = nll(1.0)

    result = minimize_scalar(nll, bounds=(0.1, 10.0), method="bounded")
    T_opt = result.x    # optimal temperature

    nll_after = nll(T_opt)

    print(f"Temperature scaling results:")
    print(f"  NLL before (T=1.0): {nll_before:.4f}")
    print(f"  NLL after  (T={T_opt:.4f}): {nll_after:.4f}")
    print(f"  Optimal T: {T_opt:.4f}")

    return {
        "temperature": round(T_opt, 6),
        "nll_before": round(nll_before, 6),
        "nll_after": round(nll_after, 6),
        "n_samples": len(targets_arr),
    }


def main():
    parser = argparse.ArgumentParser(description="AFLHR NLI Calibration")
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of samples for logit collection")
    parser.add_argument("--fit-only", action="store_true",
                        help="Skip logit collection, just fit temperature")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    logits_path = os.path.join(RESULTS_DIR, f"calibration_logits_{args.split}.csv")

    if not args.fit_only:
        # Collect logits (uses v1 engine - no calibration, no decomposition)
        from engine import AFLHREngine
        engine = AFLHREngine(
            use_windowed_nli=False,
            use_decomposition=False,
            use_calibration=False,
        )

        samples = load_halueval()
        dev, test = split_dev_test(samples)
        data = dev if args.split == "dev" else test

        collect_logits(engine, data, logits_path, limit=args.limit)

    # Fit temperature
    if not os.path.exists(logits_path):
        print(f"Error: logits not found at {logits_path}")
        print(f"Run without --fit-only first.")
        return

    result = fit_temperature(logits_path)

    # Save temperature
    with open(CALIBRATION_TEMP_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nCalibration saved to {CALIBRATION_TEMP_PATH}")


if __name__ == "__main__":
    main()
