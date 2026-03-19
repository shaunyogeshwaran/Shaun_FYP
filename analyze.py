"""
AFLHR Lite - Results Analysis and Visualization
Generates comparison tables, plots, confusion matrices,
and statistical tests for the thesis.

Usage:
  python analyze.py                        # analyse test set, all tasks
  python analyze.py --task qa              # QA only
  python analyze.py --split dev            # dev set
  python analyze.py --version v2           # v2 results
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
    if not os.path.exists(path) and suffix_key:
        # Fall back: strip task prefix and try version-only suffix
        # e.g. "qa_v2" -> "v2", "summarization_realistic" -> "realistic"
        parts = suffix_key.split("_")
        for i in range(1, len(parts) + 1):
            fallback_key = "_".join(parts[i:]) or None
            fallback_suffix = f"_{fallback_key}" if fallback_key else ""
            fallback_path = os.path.join(RESULTS_DIR, f"tuning_results{fallback_suffix}.json")
            if os.path.exists(fallback_path):
                print(f"  Tuning results not found at {path}, using {fallback_path}")
                path = fallback_path
                break
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

def comparison_table(scores_path, tuning, task=None, nli_key="nli_score"):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]
    labels = [s["label"] for s in scores]
    latencies = [s["latency_ms"] for s in scores]

    rows = []
    for name, cond, params in _conditions(tuning):
        preds = apply_condition(scores, cond, params, nli_key=nli_key)
        m = compute_metrics(labels, preds, latencies)
        rows.append({"Condition": name, **m})

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Original Plots (v1)
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


def plot_nli_distribution(scores_path, output_path, task=None,
                          nli_key="nli_score"):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]

    correct = [s.get(nli_key, s["nli_score"]) for s in scores if s["label"] == 0]
    hallucinated = [s.get(nli_key, s["nli_score"]) for s in scores if s["label"] == 1]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(correct, bins=50, alpha=0.6, label="Correct", color="#2ecc71")
    ax.hist(hallucinated, bins=50, alpha=0.6, label="Hallucinated",
            color="#e74c3c")
    ax.set_xlabel("NLI Entailment Score")
    ax.set_ylabel("Count")
    title = f"NLI Score Distribution ({nli_key})"
    if task:
        title += f" - {task}"
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_confusion_matrices(scores_path, tuning, output_path, task=None,
                            nli_key="nli_score"):
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]
    labels = [s["label"] for s in scores]

    conds = _conditions(tuning)
    fig, axes = plt.subplots(1, len(conds), figsize=(4 * len(conds), 4))
    if len(conds) == 1:
        axes = [axes]

    for ax, (name, cond, params) in zip(axes, conds):
        preds = apply_condition(scores, cond, params, nli_key=nli_key)
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
# v2 Plots
# ---------------------------------------------------------------------------

def plot_nli_before_after(scores_path_v1, scores_path_v2, output_path,
                          task=None):
    """Before/after NLI score distributions (v1 whole vs v2 decomposed)."""
    scores_v1 = load_precomputed(scores_path_v1)
    scores_v2 = load_precomputed(scores_path_v2)

    if task:
        scores_v1 = [s for s in scores_v1 if s["task"] == task]
        scores_v2 = [s for s in scores_v2 if s["task"] == task]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    for ax, scores, title in [
        (axes[0], scores_v1, "v1 (Whole-response NLI)"),
        (axes[1], scores_v2, "v2 (Decomposed NLI)"),
    ]:
        correct = [s["nli_score"] for s in scores if s["label"] == 0]
        halluc = [s["nli_score"] for s in scores if s["label"] == 1]

        ax.hist(correct, bins=40, alpha=0.6, label="Faithful", color="#2ecc71")
        ax.hist(halluc, bins=40, alpha=0.6, label="Hallucinated", color="#e74c3c")
        ax.set_xlabel("NLI Score")
        ax.set_title(title)
        ax.legend()

    axes[0].set_ylabel("Count")
    task_str = f" ({task})" if task else ""
    fig.suptitle(f"NLI Score Distribution: Before vs After Improvements{task_str}",
                 fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_calibration_reliability(scores_path, output_path, task=None,
                                 n_bins=10, nli_key="nli_score"):
    """Calibration reliability diagram (ECE plot)."""
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]

    # For reliability: confidence = entailment score, correct = label==0
    confidences = np.array([s.get(nli_key, s["nli_score"]) for s in scores])
    # "correct" means model says entailment and sample is indeed faithful
    actuals = np.array([1 - s["label"] for s in scores])  # 1=faithful, 0=halluc

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_centers = []
    bin_accs = []
    bin_confs = []
    bin_counts = []

    for lo, hi in zip(bin_boundaries[:-1], bin_boundaries[1:]):
        mask = (confidences > lo) & (confidences <= hi)
        if mask.sum() == 0:
            continue
        bin_centers.append((lo + hi) / 2)
        bin_accs.append(actuals[mask].mean())
        bin_confs.append(confidences[mask].mean())
        bin_counts.append(mask.sum())

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(bin_centers, bin_accs, width=1 / n_bins * 0.8, alpha=0.7,
           color="#3498db", edgecolor="black", linewidth=0.5, label="Accuracy")
    ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    ax.set_xlabel("Mean Predicted Confidence (Entailment Score)")
    ax.set_ylabel("Fraction of Faithful Samples")
    ax.set_title("Calibration Reliability Diagram")
    ax.legend()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_ablation_f1(results_dict, output_path):
    """Ablation F1 bar chart comparing different configurations.

    Args:
        results_dict: dict mapping variant name -> F1 score
    """
    names = list(results_dict.keys())
    f1s = list(results_dict.values())

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(names)))
    bars = ax.bar(names, f1s, color=colors, edgecolor="black", linewidth=0.5)

    for bar, val in zip(bars, f1s):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("F1 Score")
    ax.set_title("Ablation Study: F1 by Configuration")
    ax.set_ylim(0, 1.05)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


def plot_claims_distribution(scores_path, output_path, task=None):
    """Distribution of number of claims per sample (v2 only)."""
    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]

    n_claims = [s.get("n_claims", 1) for s in scores]
    if not n_claims or max(n_claims) <= 1:
        print(f"  Skipping claims distribution (all samples have 1 claim)")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(n_claims, bins=range(1, max(n_claims) + 2), alpha=0.7,
            color="#9b59b6", edgecolor="black", linewidth=0.5, align="left")
    ax.set_xlabel("Number of Claims (Sentences)")
    ax.set_ylabel("Count")
    title = "Claims per Sample Distribution"
    if task:
        title += f" ({task})"
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_path}")


# ---------------------------------------------------------------------------
# Statistical test
# ---------------------------------------------------------------------------

def run_mcnemar(scores_path, tuning, task=None, nli_key="nli_score"):
    """McNemar's test: C2 vs best C3 variant."""
    from scipy.stats import chi2

    scores = load_precomputed(scores_path)
    if task:
        scores = [s for s in scores if s["task"] == task]
    labels = [s["label"] for s in scores]

    c2_preds = apply_condition(scores, "C2", tuning["C2"]["best_params"],
                               nli_key=nli_key)

    # Pick the best C3 variant by tuning F1
    best_c3_key = max(
        ["C3_tiered", "C3_sqrt", "C3_sigmoid"],
        key=lambda k: tuning[k]["best_f1"],
    )
    c3_preds = apply_condition(scores, "C3", tuning[best_c3_key]["best_params"],
                               nli_key=nli_key)

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
    parser.add_argument("--version", default="v1", choices=["v1", "v2"],
                        help="Which scores/tuning to analyze")
    parser.add_argument("--nli-key", default="nli_score",
                        help="NLI score column for condition application")
    args = parser.parse_args()

    os.makedirs(FIGURES_DIR, exist_ok=True)

    rsuffix = "_realistic" if args.realistic else ""
    version_suffix = f"_{args.version}" if args.version != "v1" else ""
    scores_path = os.path.join(RESULTS_DIR,
                               f"scores_{args.split}{rsuffix}{version_suffix}.csv")

    if not os.path.exists(scores_path):
        print(f"Error: scores not found at {scores_path}")
        flag = " --realistic" if args.realistic else ""
        ver = f" --version {args.version}" if args.version != "v1" else ""
        print(f"Run: python evaluate.py --precompute --split {args.split}{flag}{ver}")
        return

    # Build suffix that matches tune.py output filenames
    sfx = f"_{args.task}" if args.task else ""
    sfx += rsuffix
    sfx += version_suffix

    # load_tuning_results expects the suffix (without leading _)
    tuning_key = sfx.lstrip("_") if sfx else None
    tuning = load_tuning_results(tuning_key)

    nli_key = args.nli_key

    # ---- 1. Comparison table ----
    print("\n=== Comparison Table ===")
    df = comparison_table(scores_path, tuning, task=args.task, nli_key=nli_key)
    cols = ["Condition", "f1", "precision", "recall", "over_flagging_rate"]
    print(df[cols].to_string(index=False))

    csv_path = os.path.join(RESULTS_DIR, f"comparison{sfx}_{args.split}.csv")
    df.to_csv(csv_path, index=False)
    print(f"  Saved {csv_path}")

    # ---- 2. Standard plots ----
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
        task=args.task, nli_key=nli_key)
    plot_confusion_matrices(
        scores_path, tuning,
        os.path.join(FIGURES_DIR, f"confusion_matrices{sfx}.png"),
        task=args.task, nli_key=nli_key)
    plot_latency_boxplot(
        scores_path, os.path.join(FIGURES_DIR, f"latency_boxplot{sfx}.png"),
        task=args.task)

    # ---- 2b. v2-specific plots ----
    if args.version == "v2":
        print("\n=== v2-Specific Plots ===")

        # Before/after NLI distributions (need v1 scores too)
        v1_scores_path = os.path.join(
            RESULTS_DIR, f"scores_{args.split}{rsuffix}.csv")
        if os.path.exists(v1_scores_path):
            plot_nli_before_after(
                v1_scores_path, scores_path,
                os.path.join(FIGURES_DIR, f"nli_before_after{sfx}.png"),
                task=args.task)

        # Whole-response NLI distribution (for comparison)
        plot_nli_distribution(
            scores_path,
            os.path.join(FIGURES_DIR, f"nli_dist_whole{sfx}.png"),
            task=args.task, nli_key="nli_score_whole")

        # Calibration reliability diagram
        plot_calibration_reliability(
            scores_path,
            os.path.join(FIGURES_DIR, f"calibration_reliability{sfx}.png"),
            task=args.task, nli_key=nli_key)

        # Claims distribution
        plot_claims_distribution(
            scores_path,
            os.path.join(FIGURES_DIR, f"claims_distribution{sfx}.png"),
            task=args.task)

    # ---- 3. McNemar's test ----
    print("\n=== McNemar's Test (C2 vs best C3) ===")
    mcnemar = run_mcnemar(scores_path, tuning, task=args.task, nli_key=nli_key)
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
