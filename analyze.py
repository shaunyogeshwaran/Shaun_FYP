"""
AFLHR Lite - Results Analysis and Visualization
Generates comparison tables, plots, confusion matrices,
and statistical tests for the thesis.

Usage:
  python analyze.py                        # analyse test set, all tasks
  python analyze.py --task qa              # QA only
  python analyze.py --split dev            # dev set
"""

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix as sk_confusion_matrix

from config import RESULTS_DIR, FIGURES_DIR
from evaluate import load_precomputed, apply_condition, compute_metrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_tuning_results(suffix_key=None):
    suffix = f"_{suffix_key}" if suffix_key else ""
    path = os.path.join(RESULTS_DIR, f"tuning_results{suffix}.json")
    with open(path) as f:
        return json.load(f)


def _conditions(tuning):
    """Return ordered list of (display_name, condition_code, params)."""
    return [
        ("C1 (RAG-only)", "C1", {}),
        ("C2 (Static CONLI)", "C2", tuning["C2"]["best_params"]),
        ("C3 Tiered", "C3", tuning["C3_tiered"]["best_params"]),
        ("C3 Sqrt", "C3", tuning["C3_sqrt"]["best_params"]),
        ("C3 Sigmoid", "C3", tuning["C3_sigmoid"]["best_params"]),
    ]


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

def comparison_table(scores_path, tuning, task=None):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]
    labels = [s["label"] for s in scores]
    latencies = [s["latency_ms"] for s in scores]

    rows = []
    for name, cond, params in _conditions(tuning):
        preds = apply_condition(scores, cond, params)
        m = compute_metrics(labels, preds, latencies)
        rows.append({"Condition": name, **m})

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_f1_comparison(df, output_path):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#bdc3c7", "#3498db", "#2ecc71", "#27ae60", "#1abc9c"]
    bars = ax.bar(df["Condition"], df["f1"], color=colors,
                  edgecolor="black", linewidth=0.5)

    for bar, val in zip(bars, df["f1"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("F1 Score")
    ax.set_title("Hallucination Detection F1 by Condition")
    ax.set_ylim(0, 1.05)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_precision_recall(df, output_path):
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df))
    w = 0.35

    ax.bar(x - w / 2, df["precision"], w, label="Precision",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.bar(x + w / 2, df["recall"], w, label="Recall",
           color="#e74c3c", edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Score")
    ax.set_title("Precision and Recall by Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(df["Condition"], rotation=15, ha="right")
    ax.legend()
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_overflagging(df, output_path):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#95a5a6", "#e74c3c", "#f39c12", "#f1c40f", "#e67e22"]
    ax.bar(df["Condition"], df["over_flagging_rate"], color=colors,
           edgecolor="black", linewidth=0.5)

    for i, val in enumerate(df["over_flagging_rate"]):
        ax.text(i, val + 0.005, f"{val:.3f}", ha="center", va="bottom")

    ax.set_ylabel("Over-flagging Rate (FPR)")
    ax.set_title("Over-flagging Rate by Condition")
    ax.set_ylim(0, max(df["over_flagging_rate"].max() * 1.3, 0.05))
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_retrieval_distribution(scores_path, output_path, task=None):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]

    correct = [s["retrieval_score"] for s in scores if s["label"] == 0]
    hallucinated = [s["retrieval_score"] for s in scores if s["label"] == 1]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(correct, bins=50, alpha=0.6, label="Correct", color="#2ecc71")
    ax.hist(hallucinated, bins=50, alpha=0.6, label="Hallucinated",
            color="#e74c3c")
    ax.set_xlabel("Retrieval Score")
    ax.set_ylabel("Count")
    title = "Retrieval Score Distribution"
    if task:
        title += f" ({task})"
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_nli_distribution(scores_path, output_path, task=None):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]

    correct = [s["nli_score"] for s in scores if s["label"] == 0]
    hallucinated = [s["nli_score"] for s in scores if s["label"] == 1]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(correct, bins=50, alpha=0.6, label="Correct", color="#2ecc71")
    ax.hist(hallucinated, bins=50, alpha=0.6, label="Hallucinated",
            color="#e74c3c")
    ax.set_xlabel("NLI Entailment Score")
    ax.set_ylabel("Count")
    title = "NLI Score Distribution"
    if task:
        title += f" ({task})"
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_confusion_matrices(scores_path, tuning, output_path, task=None):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]
    labels = [s["label"] for s in scores]

    conds = _conditions(tuning)
    fig, axes = plt.subplots(1, len(conds), figsize=(4 * len(conds), 4))
    if len(conds) == 1:
        axes = [axes]

    for ax, (name, cond, params) in zip(axes, conds):
        preds = apply_condition(scores, cond, params)
        cm = sk_confusion_matrix(labels, preds, labels=[0, 1])

        ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        ax.set_title(name, fontsize=10)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Valid", "Halluc."])
        ax.set_yticklabels(["Valid", "Halluc."])

        for i in range(2):
            for j in range(2):
                color = "white" if cm[i, j] > cm.max() / 2 else "black"
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        color=color, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_latency_boxplot(scores_path, output_path, task=None):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]

    latencies = [s["latency_ms"] for s in scores]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(latencies, vert=True, patch_artist=True,
               boxprops=dict(facecolor="#3498db", alpha=0.7))
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Per-sample Latency Distribution (retrieval + NLI)")
    ax.set_xticklabels(["All samples"])
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


# ---------------------------------------------------------------------------
# Statistical test
# ---------------------------------------------------------------------------

def run_mcnemar(scores_path, tuning, task=None):
    """McNemar's test: C2 vs best C3 variant."""
    from scipy.stats import chi2

    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]
    labels = [s["label"] for s in scores]

    c2_preds = apply_condition(scores, "C2", tuning["C2"]["best_params"])

    # Pick the best C3 variant by tuning F1
    best_c3_key = max(
        ["C3_tiered", "C3_sqrt", "C3_sigmoid"],
        key=lambda k: tuning[k]["best_f1"],
    )
    c3_preds = apply_condition(scores, "C3", tuning[best_c3_key]["best_params"])

    c2_ok = [int(p == l) for p, l in zip(c2_preds, labels)]
    c3_ok = [int(p == l) for p, l in zip(c3_preds, labels)]

    # b = C2 right & C3 wrong, c = C2 wrong & C3 right
    b = sum(1 for a, b_ in zip(c2_ok, c3_ok) if a == 1 and b_ == 0)
    c = sum(1 for a, b_ in zip(c2_ok, c3_ok) if a == 0 and b_ == 1)

    if b + c == 0:
        return {"statistic": 0, "p_value": 1.0, "significant": False,
                "b_c2_right_c3_wrong": b, "c_c2_wrong_c3_right": c,
                "c3_variant": best_c3_key}

    stat = (abs(b - c) - 1) ** 2 / (b + c)  # continuity correction
    p_val = 1 - chi2.cdf(stat, df=1)

    return {
        "statistic": round(stat, 4),
        "p_value": round(p_val, 6),
        "significant": bool(p_val < 0.05),
        "b_c2_right_c3_wrong": b,
        "c_c2_wrong_c3_right": c,
        "c3_variant": best_c3_key,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AFLHR Results Analysis")
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    parser.add_argument("--task", default=None,
                        choices=["qa", "summarization"])
    parser.add_argument("--realistic", action="store_true",
                        help="Use realistic retrieval scores")
    args = parser.parse_args()

    os.makedirs(FIGURES_DIR, exist_ok=True)

    rsuffix = "_realistic" if args.realistic else ""
    scores_path = os.path.join(RESULTS_DIR,
                               f"scores_{args.split}{rsuffix}.csv")

    if not os.path.exists(scores_path):
        print(f"Error: scores not found at {scores_path}")
        flag = " --realistic" if args.realistic else ""
        print(f"Run: python evaluate.py --precompute --split {args.split}{flag}")
        return

    # Build suffix that matches tune.py output filenames
    sfx = f"_{args.task}" if args.task else ""
    sfx += rsuffix

    # load_tuning_results expects the suffix (without leading _)
    tuning_key = sfx.lstrip("_") if sfx else None
    tuning = load_tuning_results(tuning_key)

    # ---- 1. Comparison table ----
    print("\n=== Comparison Table ===")
    df = comparison_table(scores_path, tuning, task=args.task)
    cols = ["Condition", "f1", "precision", "recall", "over_flagging_rate"]
    print(df[cols].to_string(index=False))

    csv_path = os.path.join(RESULTS_DIR, f"comparison{sfx}_{args.split}.csv")
    df.to_csv(csv_path, index=False)
    print(f"  Saved {csv_path}")

    # ---- 2. Plots ----
    print("\n=== Generating Plots ===")
    plot_f1_comparison(
        df, os.path.join(FIGURES_DIR, f"f1_comparison{sfx}.png"))
    plot_precision_recall(
        df, os.path.join(FIGURES_DIR, f"precision_recall{sfx}.png"))
    plot_overflagging(
        df, os.path.join(FIGURES_DIR, f"overflagging{sfx}.png"))
    plot_retrieval_distribution(
        scores_path, os.path.join(FIGURES_DIR, f"retrieval_dist{sfx}.png"),
        task=args.task)
    plot_nli_distribution(
        scores_path, os.path.join(FIGURES_DIR, f"nli_dist{sfx}.png"),
        task=args.task)
    plot_confusion_matrices(
        scores_path, tuning,
        os.path.join(FIGURES_DIR, f"confusion_matrices{sfx}.png"),
        task=args.task)
    plot_latency_boxplot(
        scores_path, os.path.join(FIGURES_DIR, f"latency_boxplot{sfx}.png"),
        task=args.task)

    # ---- 3. McNemar's test ----
    print("\n=== McNemar's Test (C2 vs best C3) ===")
    mcnemar = run_mcnemar(scores_path, tuning, task=args.task)
    print(f"  C3 variant:  {mcnemar['c3_variant']}")
    print(f"  Statistic:   {mcnemar['statistic']}")
    print(f"  p-value:     {mcnemar['p_value']}")
    print(f"  Significant: {mcnemar['significant']}")

    mcnemar_path = os.path.join(
        RESULTS_DIR, f"mcnemar{sfx}_{args.split}.json")
    with open(mcnemar_path, "w") as f:
        json.dump(mcnemar, f, indent=2)
    print(f"  Saved {mcnemar_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
