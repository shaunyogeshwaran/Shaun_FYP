"""
AFLHR Lite - Grid Search Hyperparameter Tuning
Sweeps threshold parameters for C2 and C3 on the dev set
using pre-computed scores (no model inference needed).

Usage:
  python tune.py                        # tune on all tasks
  python tune.py --task qa              # tune on QA only
  python tune.py --task summarization   # tune on summarization only
"""

import argparse
import json
import os
from itertools import product

import numpy as np

from config import (
    RESULTS_DIR,
    GRID_C2_T_STATIC,
    GRID_C3_PIVOT,
    GRID_C3_T_STRICT,
    GRID_C3_T_LENIENT,
    GRID_C3_CONT_T_STRICT,
    GRID_C3_CONT_T_LENIENT,
)
from evaluate import load_precomputed, apply_condition, compute_metrics


def make_range(cfg):
    """Create a list of values from a grid config dict."""
    values = []
    v = cfg["min"]
    while v <= cfg["max"] + 1e-9:
        values.append(round(v, 4))
        v += cfg["step"]
    return values


def _labels(scores):
    return [s["label"] for s in scores]


# ---------------------------------------------------------------------------
# C2 tuning
# ---------------------------------------------------------------------------

def tune_c2(scores):
    """Sweep T_static to maximise F1."""
    labels = _labels(scores)
    best_f1, best_params = -1, None
    log = []

    for t in make_range(GRID_C2_T_STATIC):
        params = {"T_static": t}
        preds = apply_condition(scores, "C2", params)
        m = compute_metrics(labels, preds)
        log.append({"params": params, **{k: m[k] for k in
                    ("f1", "precision", "recall", "over_flagging_rate")}})
        if m["f1"] > best_f1:
            best_f1, best_params = m["f1"], params

    return best_params, best_f1, log


# ---------------------------------------------------------------------------
# C3 tiered tuning
# ---------------------------------------------------------------------------

def tune_c3_tiered(scores):
    """Sweep pivot, T_strict, T_lenient to maximise F1."""
    labels = _labels(scores)
    best_f1, best_params = -1, None
    log = []

    pivots = make_range(GRID_C3_PIVOT)
    t_stricts = make_range(GRID_C3_T_STRICT)
    t_lenients = make_range(GRID_C3_T_LENIENT)

    total = len(pivots) * len(t_stricts) * len(t_lenients)
    print(f"  C3 tiered: up to {total} configurations")

    for pivot, ts, tl in product(pivots, t_stricts, t_lenients):
        if tl >= ts:
            continue  # lenient must be strictly less than strict

        params = {"method": "tiered", "pivot": pivot,
                  "T_strict": ts, "T_lenient": tl}
        preds = apply_condition(scores, "C3", params)
        m = compute_metrics(labels, preds)
        log.append({"params": params, **{k: m[k] for k in
                    ("f1", "precision", "recall", "over_flagging_rate")}})
        if m["f1"] > best_f1:
            best_f1, best_params = m["f1"], params

    return best_params, best_f1, log


# ---------------------------------------------------------------------------
# C3 continuous tuning (sqrt / sigmoid)
# ---------------------------------------------------------------------------

def tune_c3_continuous(scores, method="sqrt"):
    """Sweep T_strict, T_lenient for continuous weighting."""
    labels = _labels(scores)
    best_f1, best_params = -1, None
    log = []

    t_stricts = make_range(GRID_C3_CONT_T_STRICT)
    t_lenients = make_range(GRID_C3_CONT_T_LENIENT)

    total = len(t_stricts) * len(t_lenients)
    print(f"  C3 {method}: up to {total} configurations")

    for ts, tl in product(t_stricts, t_lenients):
        if tl >= ts:
            continue

        params = {"method": method, "T_strict": ts, "T_lenient": tl}
        preds = apply_condition(scores, "C3", params)
        m = compute_metrics(labels, preds)
        log.append({"params": params, **{k: m[k] for k in
                    ("f1", "precision", "recall", "over_flagging_rate")}})
        if m["f1"] > best_f1:
            best_f1, best_params = m["f1"], params

    return best_params, best_f1, log


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AFLHR Grid Search Tuning")
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--task", default=None,
                        choices=["qa", "summarization"])
    parser.add_argument("--realistic", action="store_true",
                        help="Use realistic retrieval scores")
    args = parser.parse_args()

    suffix = "_realistic" if args.realistic else ""
    scores_path = os.path.join(RESULTS_DIR,
                               f"scores_{args.split}{suffix}.csv")
    if not os.path.exists(scores_path):
        print(f"Error: Pre-computed scores not found at {scores_path}")
        flag = " --realistic" if args.realistic else ""
        print(f"Run: python evaluate.py --precompute --split {args.split}{flag}")
        return

    scores = load_precomputed(scores_path)
    if args.task:
        scores = [s for s in scores if s["task"] == args.task]

    print(f"Tuning on {len(scores)} samples "
          f"({args.split} split, task={args.task or 'all'})\n")

    all_results = {}

    # --- C2 ---
    print("--- Tuning C2 (fixed threshold) ---")
    c2_params, c2_f1, c2_log = tune_c2(scores)
    print(f"  Best C2: F1={c2_f1:.4f}  params={c2_params}\n")
    all_results["C2"] = {
        "best_params": c2_params, "best_f1": c2_f1, "log": c2_log,
    }

    # --- C3 tiered ---
    print("--- Tuning C3 tiered ---")
    c3t_params, c3t_f1, c3t_log = tune_c3_tiered(scores)
    print(f"  Best C3 tiered: F1={c3t_f1:.4f}  params={c3t_params}\n")
    all_results["C3_tiered"] = {
        "best_params": c3t_params, "best_f1": c3t_f1, "log": c3t_log,
    }

    # --- C3 sqrt ---
    print("--- Tuning C3 continuous (sqrt) ---")
    c3s_params, c3s_f1, c3s_log = tune_c3_continuous(scores, method="sqrt")
    print(f"  Best C3 sqrt: F1={c3s_f1:.4f}  params={c3s_params}\n")
    all_results["C3_sqrt"] = {
        "best_params": c3s_params, "best_f1": c3s_f1, "log": c3s_log,
    }

    # --- C3 sigmoid ---
    print("--- Tuning C3 continuous (sigmoid) ---")
    c3g_params, c3g_f1, c3g_log = tune_c3_continuous(scores, method="sigmoid")
    print(f"  Best C3 sigmoid: F1={c3g_f1:.4f}  params={c3g_params}\n")
    all_results["C3_sigmoid"] = {
        "best_params": c3g_params, "best_f1": c3g_f1, "log": c3g_log,
    }

    # --- Summary ---
    print(f"{'='*60}")
    print("TUNING SUMMARY")
    print(f"{'='*60}")
    for name, r in all_results.items():
        print(f"  {name:15s}  F1={r['best_f1']:.4f}  {r['best_params']}")

    # Save compact summary
    task_suffix = f"_{args.task}" if args.task else ""
    task_suffix += suffix
    summary = {k: {"best_params": v["best_params"], "best_f1": v["best_f1"]}
               for k, v in all_results.items()}

    out = os.path.join(RESULTS_DIR, f"tuning_results{task_suffix}.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved summary  -> {out}")

    # Save full log (for analysis)
    log_path = os.path.join(RESULTS_DIR, f"tuning_log{task_suffix}.json")
    with open(log_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved full log -> {log_path}")


if __name__ == "__main__":
    main()
