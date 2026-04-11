"""
AFLHR Lite - Grid Search Hyperparameter Tuning
Sweeps threshold parameters for C2 and C3 on the dev set
using pre-computed scores (no model inference needed).

AI Disclosure: Development of this module was assisted by AI tools
for code structuring, debugging, and refactoring. The grid search
methodology and threshold optimization strategy are the author's own work.

Usage:
  python tune.py                        # tune on all tasks
  python tune.py --task qa              # tune on QA only
  python tune.py --task summarization   # tune on summarization only
  python tune.py --split dev --version v2  # tune on v2 scores
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
    GRID_V2_C2_T_STATIC,
    GRID_V2_C3_PIVOT,
    GRID_V2_C3_T_STRICT,
    GRID_V2_C3_T_LENIENT,
    GRID_V2_C3_CONT_T_STRICT,
    GRID_V2_C3_CONT_T_LENIENT,
)
from evaluate import load_precomputed, apply_condition, compute_metrics


def get_grid_config(version="v1"):
    """Return the appropriate grid search ranges for v1 or v2."""
    if version == "v2":
        return {
            "c2": GRID_V2_C2_T_STATIC,
            "pivot": GRID_V2_C3_PIVOT,
            "strict": GRID_V2_C3_T_STRICT,
            "lenient": GRID_V2_C3_T_LENIENT,
            "cont_strict": GRID_V2_C3_CONT_T_STRICT,
            "cont_lenient": GRID_V2_C3_CONT_T_LENIENT,
        }
    return {
        "c2": GRID_C2_T_STATIC,
        "pivot": GRID_C3_PIVOT,
        "strict": GRID_C3_T_STRICT,
        "lenient": GRID_C3_T_LENIENT,
        "cont_strict": GRID_C3_CONT_T_STRICT,
        "cont_lenient": GRID_C3_CONT_T_LENIENT,
    }


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

def tune_c2(scores, nli_key="nli_score", grid=None):
    """Sweep T_static to maximise F1."""
    labels = _labels(scores)
    best_f1, best_params = -1, None
    log = []

    c2_grid = grid["c2"] if grid else GRID_C2_T_STATIC
    for t in make_range(c2_grid):
        params = {"T_static": t}
        preds = apply_condition(scores, "C2", params, nli_key=nli_key)
        m = compute_metrics(labels, preds)
        log.append({"params": params, **{k: m[k] for k in
                    ("f1", "precision", "recall", "over_flagging_rate")}})
        if m["f1"] > best_f1:
            best_f1, best_params = m["f1"], params

    return best_params, best_f1, log


# ---------------------------------------------------------------------------
# C3 tiered tuning
# ---------------------------------------------------------------------------

def tune_c3_tiered(scores, nli_key="nli_score", grid=None):
    """Sweep pivot, T_strict, T_lenient to maximise F1."""
    labels = _labels(scores)
    best_f1, best_params = -1, None
    log = []

    pivots = make_range(grid["pivot"] if grid else GRID_C3_PIVOT)
    t_stricts = make_range(grid["strict"] if grid else GRID_C3_T_STRICT)
    t_lenients = make_range(grid["lenient"] if grid else GRID_C3_T_LENIENT)

    total = len(pivots) * len(t_stricts) * len(t_lenients)
    print(f"  C3 tiered: up to {total} configurations")

    for pivot, ts, tl in product(pivots, t_stricts, t_lenients):
        if tl >= ts:
            continue  # lenient must be strictly less than strict

        params = {"method": "tiered", "pivot": pivot,
                  "T_strict": ts, "T_lenient": tl}
        preds = apply_condition(scores, "C3", params, nli_key=nli_key)
        m = compute_metrics(labels, preds)
        log.append({"params": params, **{k: m[k] for k in
                    ("f1", "precision", "recall", "over_flagging_rate")}})
        if m["f1"] > best_f1:
            best_f1, best_params = m["f1"], params

    return best_params, best_f1, log


# ---------------------------------------------------------------------------
# C3 continuous tuning (sqrt / sigmoid)
# ---------------------------------------------------------------------------

def tune_c3_continuous(scores, method="sqrt", nli_key="nli_score", grid=None):
    """Sweep T_strict, T_lenient for continuous weighting."""
    labels = _labels(scores)
    best_f1, best_params = -1, None
    log = []

    t_stricts = make_range(grid["cont_strict"] if grid else GRID_C3_CONT_T_STRICT)
    t_lenients = make_range(grid["cont_lenient"] if grid else GRID_C3_CONT_T_LENIENT)

    total = len(t_stricts) * len(t_lenients)
    print(f"  C3 {method}: up to {total} configurations")

    for ts, tl in product(t_stricts, t_lenients):
        if tl >= ts:
            continue

        params = {"method": method, "T_strict": ts, "T_lenient": tl}
        preds = apply_condition(scores, "C3", params, nli_key=nli_key)
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
    parser.add_argument("--version", default="v1", choices=["v1", "v2"],
                        help="Which pre-computed scores to use")
    parser.add_argument("--nli-key", default="nli_score",
                        help="NLI score column to use (for ablation)")
    args = parser.parse_args()

    suffix = "_realistic" if args.realistic else ""
    version_suffix = f"_{args.version}" if args.version != "v1" else ""
    scores_path = os.path.join(RESULTS_DIR,
                               f"scores_{args.split}{suffix}{version_suffix}.csv")
    if not os.path.exists(scores_path):
        print(f"Error: Pre-computed scores not found at {scores_path}")
        flag = " --realistic" if args.realistic else ""
        ver = f" --version {args.version}" if args.version != "v1" else ""
        print(f"Run: python evaluate.py --precompute --split {args.split}{flag}{ver}")
        return

    scores = load_precomputed(scores_path)
    if args.task:
        scores = [s for s in scores if s["task"] == args.task]

    nli_key = args.nli_key
    grid = get_grid_config(args.version)
    print(f"Tuning on {len(scores)} samples "
          f"({args.split} split, task={args.task or 'all'}, nli_key={nli_key}, grid={args.version})\n")

    all_results = {}

    # --- C2 ---
    print("--- Tuning C2 (fixed threshold) ---")
    c2_params, c2_f1, c2_log = tune_c2(scores, nli_key=nli_key, grid=grid)
    print(f"  Best C2: F1={c2_f1:.4f}  params={c2_params}\n")
    all_results["C2"] = {
        "best_params": c2_params, "best_f1": c2_f1, "log": c2_log,
    }

    # --- C3 tiered ---
    print("--- Tuning C3 tiered ---")
    c3t_params, c3t_f1, c3t_log = tune_c3_tiered(scores, nli_key=nli_key, grid=grid)
    print(f"  Best C3 tiered: F1={c3t_f1:.4f}  params={c3t_params}\n")
    all_results["C3_tiered"] = {
        "best_params": c3t_params, "best_f1": c3t_f1, "log": c3t_log,
    }

    # --- C3 sqrt ---
    print("--- Tuning C3 continuous (sqrt) ---")
    c3s_params, c3s_f1, c3s_log = tune_c3_continuous(scores, method="sqrt",
                                                      nli_key=nli_key, grid=grid)
    print(f"  Best C3 sqrt: F1={c3s_f1:.4f}  params={c3s_params}\n")
    all_results["C3_sqrt"] = {
        "best_params": c3s_params, "best_f1": c3s_f1, "log": c3s_log,
    }

    # --- C3 sigmoid ---
    print("--- Tuning C3 continuous (sigmoid) ---")
    c3g_params, c3g_f1, c3g_log = tune_c3_continuous(scores, method="sigmoid",
                                                      nli_key=nli_key, grid=grid)
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
    task_suffix += version_suffix
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
