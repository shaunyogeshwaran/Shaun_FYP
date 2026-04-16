#!/usr/bin/env python
"""
AFLHR v2 - Automated Experiment Pipeline

AI Disclosure: Development of this module was assisted by AI tools
for code structuring, debugging, and refactoring. The experiment
pipeline orchestration and workflow design are the author's own work.

Runs the full v2 workflow end-to-end:
  1. Calibrate temperature on dev set
  2. Precompute v2 scores (dev + test)
  3. Tune thresholds on dev
  4. Evaluate on test
  5. Generate analysis plots

Usage:
  python run_v2.py                    # full pipeline
  python run_v2.py --limit 50         # smoke test with 50 samples
  python run_v2.py --calibrate         # include calibration step (off by default — T=10 boundary)
  python run_v2.py --skip-precompute  # skip precompute (use existing CSVs)
  python run_v2.py --realistic        # also run realistic retrieval experiment
"""

import argparse
import subprocess
import sys
import time


def run(cmd, desc):
    """Run a command, printing status and timing. Exits on failure."""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"  $ {cmd}")
    print(f"{'='*60}\n")

    start = time.time()
    result = subprocess.run(cmd, shell=True)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n  FAILED (exit code {result.returncode}) after {elapsed:.0f}s")
        sys.exit(1)

    mins, secs = divmod(elapsed, 60)
    hrs, mins = divmod(mins, 60)
    if hrs:
        print(f"\n  Done in {int(hrs)}h {int(mins)}m {int(secs)}s")
    elif mins:
        print(f"\n  Done in {int(mins)}m {int(secs)}s")
    else:
        print(f"\n  Done in {secs:.1f}s")

    return elapsed


def run_optional(cmd, desc):
    """Run a command, printing status and timing. Warns on failure but continues."""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"  $ {cmd}")
    print(f"{'='*60}\n")

    start = time.time()
    result = subprocess.run(cmd, shell=True)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n  WARNING: exited with code {result.returncode} (non-fatal, continuing)")
    else:
        secs = elapsed
        mins, secs = divmod(secs, 60)
        if mins:
            print(f"\n  Done in {int(mins)}m {int(secs)}s")
        else:
            print(f"\n  Done in {secs:.1f}s")

    return elapsed


def main():
    parser = argparse.ArgumentParser(description="AFLHR v2 Full Pipeline")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit samples (for smoke testing)")
    parser.add_argument("--calibrate", action="store_true",
                        help="Run calibration step (off by default — T=10 boundary issue)")
    parser.add_argument("--skip-calibrate", action="store_true",
                        help="(Deprecated) Calibration is now off by default")
    parser.add_argument("--skip-precompute", action="store_true",
                        help="Skip precomputation step")
    parser.add_argument("--skip-tune", action="store_true",
                        help="Skip tuning step")
    parser.add_argument("--realistic", action="store_true",
                        help="Also run realistic retrieval experiment")
    args = parser.parse_args()

    limit_flag = f" --limit {args.limit}" if args.limit else ""
    total_start = time.time()
    timings = {}

    # ---- Step 1: Calibrate (opt-in — T=10 boundary means it doesn't help) ----
    if args.calibrate:
        t = run(
            f"python calibrate.py --split dev{limit_flag}",
            "Step 1/5: Calibrate NLI temperature on dev set",
        )
        timings["calibrate"] = t

    # ---- Step 2: Precompute v2 scores ----
    if not args.skip_precompute:
        t = run(
            f"python evaluate.py --precompute --split dev --version v2{limit_flag}",
            "Step 2a/5: Precompute v2 scores (dev split)",
        )
        timings["precompute_dev"] = t

        t = run(
            f"python evaluate.py --precompute --split test --version v2{limit_flag}",
            "Step 2b/5: Precompute v2 scores (test split)",
        )
        timings["precompute_test"] = t

        if args.realistic:
            t = run(
                f"python evaluate.py --precompute --split dev --realistic --version v2{limit_flag}",
                "Step 2c/5: Precompute v2 realistic scores (dev split)",
            )
            timings["precompute_dev_realistic"] = t

            t = run(
                f"python evaluate.py --precompute --split test --realistic --version v2{limit_flag}",
                "Step 2d/5: Precompute v2 realistic scores (test split)",
            )
            timings["precompute_test_realistic"] = t

    # ---- Step 3: Tune on dev ----
    if not args.skip_tune:
        t = run(
            "python tune.py --split dev --version v2",
            "Step 3/5: Grid search tuning on dev set (v2 scores)",
        )
        timings["tune"] = t

        if args.realistic:
            t = run(
                "python tune.py --split dev --version v2 --realistic",
                "Step 3b/5: Grid search tuning on dev set (v2 realistic)",
            )
            timings["tune_realistic"] = t

    # ---- Step 4: Evaluate on test ----
    for cond in ["C1", "C2", "C3"]:
        tuned = " --tuned" if cond != "C1" else ""
        t = run(
            f"python evaluate.py --condition {cond} --split test --version v2{tuned}",
            f"Step 4/5: Evaluate {cond} on test set (v2)",
        )
        timings[f"eval_{cond}"] = t

    # ---- Step 5: Analysis ----
    t = run(
        "python analyze.py --split test --version v2",
        "Step 5/5: Generate analysis plots and tables (v2)",
    )
    timings["analyze"] = t

    # Per-task analysis (non-fatal — may lack samples with --limit)
    for task in ["qa", "summarization"]:
        run_optional(
            f"python analyze.py --split test --version v2 --task {task}",
            f"Step 5/5: Analysis for {task} (v2)",
        )

    if args.realistic:
        run_optional(
            "python analyze.py --split test --version v2 --realistic",
            "Step 5/5: Analysis (v2 realistic)",
        )

    # ---- Summary ----
    total = time.time() - total_start
    mins, secs = divmod(total, 60)
    hrs, mins = divmod(mins, 60)

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"\nStep timings:")
    for step, t in timings.items():
        m, s = divmod(t, 60)
        print(f"  {step:30s}  {int(m):2d}m {int(s):02d}s")
    if hrs:
        print(f"\nTotal wall time: {int(hrs)}h {int(mins)}m {int(secs)}s")
    else:
        print(f"\nTotal wall time: {int(mins)}m {int(secs)}s")

    print(f"\nResults in: results/")
    print(f"Figures in: results/figures/")


if __name__ == "__main__":
    main()
