#!/usr/bin/env python3
"""Update thesis_updated.docx with canonical results from results/ directory.

Reads all numbers from the CSV/JSON files in results/, then patches paragraphs
and tables in the thesis using content-based search (not index) for safety.

Usage:
    python update_thesis.py                    # dry run (shows what would change)
    python update_thesis.py --apply            # apply changes
    python update_thesis.py --apply --no-backup  # skip backup (not recommended)

Requires: python-docx (pip install python-docx)
"""

import argparse
import csv
import json
import shutil
import datetime
import sys
from pathlib import Path

try:
    import docx
except ImportError:
    print("ERROR: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)

THESIS = Path("thesis_updated.docx")
RESULTS = Path("results")


# ── Data loading ─────────────────────────────────────────────────────────

def load_csv(path):
    """Load a comparison CSV into a dict keyed by Condition."""
    rows = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows[row["Condition"]] = {k: v for k, v in row.items()}
    return rows


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_all_results():
    """Load all canonical results into a single dict."""
    r = {}
    # Comparison CSVs
    for name in ["v2_test", "qa_v2_test", "summarization_v2_test", "realistic_v2_test"]:
        p = RESULTS / f"comparison_{name}.csv"
        if p.exists():
            r[f"comp_{name}"] = load_csv(p)

    # McNemar JSONs
    for name in ["v2_test", "qa_v2_test", "summarization_v2_test", "realistic_v2_test"]:
        p = RESULTS / f"mcnemar_{name}.json"
        if p.exists():
            r[f"mcn_{name}"] = load_json(p)

    # Tuning results
    for name in ["v2", "qa_v2", "summarization_v2", "realistic_v2"]:
        p = RESULTS / f"tuning_results_{name}.json"
        if p.exists():
            r[f"tune_{name}"] = load_json(p)

    return r


# ── Helpers ──────────────────────────────────────────────────────────────

def find_para(doc, needle, start=0):
    """Return (index, paragraph) for the first paragraph containing needle."""
    for i, p in enumerate(doc.paragraphs):
        if i < start:
            continue
        if needle in p.text:
            return i, p
    return None, None


def replace_para_text(para, new_text):
    """Replace paragraph text while preserving the first run's formatting."""
    if not para.runs:
        para.text = new_text
        return
    for run in para.runs:
        run.text = ""
    para.runs[0].text = new_text


def set_cell(table, row, col, value):
    """Set a table cell's text, preserving the first run's formatting."""
    cell = table.cell(row, col)
    if cell.paragraphs and cell.paragraphs[0].runs:
        for run in cell.paragraphs[0].runs:
            run.text = ""
        cell.paragraphs[0].runs[0].text = str(value)
    else:
        cell.paragraphs[0].text = str(value)


def fmt(val, decimals=4):
    """Format a numeric string to N decimal places."""
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)


def pct(val):
    """Format a 0-1 value as a percentage string like '44.9%'."""
    try:
        return f"{float(val) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(val)


# ── Paragraph updates ────────────────────────────────────────────────────

def build_paragraph_updates(r):
    """Return list of (search_needle, new_text, description) tuples.

    Each entry finds a paragraph by search_needle and replaces its text.
    Numbers are pulled from the results dict `r`.
    """
    # Shorthand accessors
    comb = r.get("comp_v2_test", {})
    qa = r.get("comp_qa_v2_test", {})
    summ = r.get("comp_summarization_v2_test", {})
    real = r.get("comp_realistic_v2_test", {})
    mcn_comb = r.get("mcn_v2_test", {})
    mcn_qa = r.get("mcn_qa_v2_test", {})
    mcn_summ = r.get("mcn_summarization_v2_test", {})
    mcn_real = r.get("mcn_realistic_v2_test", {})
    tune_comb = r.get("tune_v2", {})
    tune_qa = r.get("tune_qa_v2", {})

    c2 = comb.get("C2 (Static CONLI)", {})
    c3t = comb.get("C3 Tiered", {})
    c2_qa = qa.get("C2 (Static CONLI)", {})
    c3t_qa = qa.get("C3 Tiered", {})
    c3sq_qa = qa.get("C3 Sqrt", {})
    c3sig_qa = qa.get("C3 Sigmoid", {})
    c2_summ = summ.get("C2 (Static CONLI)", {})
    c3sq_summ = summ.get("C3 Sqrt", {})
    c2_real = real.get("C2 (Static CONLI)", {})
    c3t_real = real.get("C3 Tiered", {})
    c3sq_real = real.get("C3 Sqrt", {})
    c3sig_real = real.get("C3 Sigmoid", {})

    mcn_comb_p = mcn_comb.get("p_value", "?")
    mcn_qa_p = mcn_qa.get("p_value", "?")
    mcn_summ_p = mcn_summ.get("p_value", "?")
    mcn_real_p = mcn_real.get("p_value", "?")
    mcn_real_stat = mcn_real.get("statistic", "?")

    dev_c2 = tune_comb.get("C2", {}).get("best_f1", "?")
    dev_c3t = tune_comb.get("C3_tiered", {}).get("best_f1", "?")
    dev_qa_f1 = tune_qa.get("C2", {}).get("best_f1", "?")

    updates = []

    # Search needles are chosen to be unique, stable phrases that exist in
    # BOTH the old and new paragraph text so the script is idempotent.

    # ── Abstract ──
    updates.append((
        "A controlled three-condition experiment is conducted on the HaluEval benchmark",
        (
            f"A controlled three-condition experiment is conducted on the HaluEval benchmark "
            f"(20,000 samples across QA and Summarization tasks): C1 (RAG-only baseline), C2 "
            f"(static CONLI threshold), and C3 (Cw-CONLI with dynamic weighting). A v2 pipeline "
            f"adds sliding-window NLI (fixing 512-token truncation that broke summarisation), "
            f"sentence-level claim decomposition, and BGE embedding upgrades. On the standard "
            f"per-sample benchmark, C3 and C2 converge to the same operating point (combined F1: "
            f"{fmt(c2['f1'])} vs {fmt(c3t['f1'])}; McNemar\u2019s p = {mcn_comb_p}) because "
            f"retrieval scores cluster tightly (QA std = 0.075). Under realistic shared-index "
            f"retrieval, the difference is significant (p = {mcn_real_p}): C2 flags "
            f"{pct(c2_real.get('over_flagging_rate', '?'))} of correct responses while C3 Sqrt "
            f"reduces over-flagging to {pct(c3sq_real.get('over_flagging_rate', '?'))}. The "
            f"primary contribution is v2 engineering \u2014 windowed NLI, decomposition, BGE "
            f"embeddings \u2014 rather than the adaptive threshold mechanism itself. These "
            f"findings suggest Cw-CONLI\u2019s benefits emerge in retrieval environments with "
            f"greater score variability."
        ),
        "Abstract"
    ))

    # ── Dev set tuning ──
    updates.append((
        "Key observation: All conditions converge to similar F1 scores on the dev set",
        (
            f"Key observation: All conditions converge to similar F1 scores on the dev set. "
            f"For combined tasks, the spread is only {abs(float(dev_c3t) - float(dev_c2)):.4f} "
            f"(from C2 at {fmt(dev_c2)} to C3 Tiered at {fmt(dev_c3t)}). For QA only, all "
            f"conditions are tied at F1 = {fmt(dev_qa_f1)} \u2014 C2, C3 Tiered, C3 Sqrt, and "
            f"C3 Sigmoid achieve identical dev F1. This tight convergence foreshadows the null "
            f"result on the test set."
        ),
        "Dev set tuning"
    ))

    # ── Combined results ──
    updates.append((
        "All NLI-based conditions (C2 and C3 variants) substantially outperform C1",
        (
            f"All NLI-based conditions (C2 and C3 variants) substantially outperform C1 "
            f"(F1 = 0.0), confirming that NLI verification is essential. Among the NLI "
            f"conditions, the differences are negligible: F1 ranges from {fmt(c2['f1'])} to "
            f"{fmt(c3t['f1'])}, a spread of {abs(float(c3t['f1']) - float(c2['f1'])):.3f}. "
            f"C3 Tiered achieves the highest recall ({fmt(c3t['recall'])}), while C2 has the "
            f"highest precision ({fmt(c2['precision'])}). Over-flagging rates cluster around "
            f"55\u201356%, reflecting the Summarization task\u2019s poor NLI signal dragging "
            f"down combined performance."
        ),
        "Combined results"
    ))

    # ── QA results ──
    updates.append((
        "C2 leads with F1 =",
        (
            f"C2 leads with F1 = {fmt(c2_qa['f1'])}, followed by C3 Sigmoid at "
            f"{fmt(c3sig_qa['f1'])} and C3 Tiered at {fmt(c3t_qa['f1'])}. C3 Sqrt trails at "
            f"{fmt(c3sq_qa['f1'])} but achieves the lowest over-flagging rate of "
            f"{pct(c3sq_qa['over_flagging_rate'])}, compared to C2\u2019s "
            f"{pct(c2_qa['over_flagging_rate'])}. C3 Tiered achieves "
            f"{pct(c3t_qa['over_flagging_rate'])} over-flagging with the highest C3 precision "
            f"({fmt(c3t_qa['precision'])}). The pattern is consistent: C3 variants trade modest "
            f"F1 for reduced over-flagging, with continuous functions (sqrt, sigmoid) "
            f"outperforming the tiered step function on precision."
        ),
        "QA results"
    ))

    # ── Summarisation results ──
    updates.append((
        "Summarization results remain challenging despite v2",
        (
            f"Summarization results remain challenging despite v2\u2019s sliding-window NLI. "
            f"F1 scores are comparable across conditions (C2: {fmt(c2_summ['f1'])}, C3 Sqrt: "
            f"{fmt(c3sq_summ['f1'])}) with over-flagging rates of 98\u201399.5%. The windowed "
            f"approach fixes the complete breakage seen in v1 (where truncation caused 99%+ FPR "
            f"with near-zero F1), but the NLI model still struggles with the paraphrasing and "
            f"abstraction inherent in summarisation."
        ),
        "Summarisation results"
    ))

    # ── Summarisation root cause ──
    updates.append((
        "v2 pipeline addresses the 512-token truncation via sliding-window NLI",
        (
            "The v2 pipeline addresses the 512-token truncation via sliding-window NLI: "
            "premises are split into overlapping 400-token windows with 200-token stride, "
            "and the maximum entailment score across windows is used. This eliminates "
            "the complete failure mode of v1 (where truncation caused near-zero F1). "
            "However, over-flagging remains high (\u224898\u201399%) because summaries "
            "naturally use paraphrasing and abstraction, which the NLI model \u2014 trained "
            "on short, literal premise-hypothesis pairs from the MultiNLI corpus \u2014 "
            "still interprets as non-entailment."
        ),
        "Summarisation root cause"
    ))

    # ── Realistic retrieval ──
    updates.append((
        "Under realistic retrieval, C2 flags every single response as a hallucination",
        (
            f"Under realistic retrieval, C2 flags every single response as a hallucination "
            f"({pct(c2_real['over_flagging_rate'])} over-flagging, recall = "
            f"{fmt(c2_real['recall'])}, F1 = {fmt(c2_real['f1'])}). C3 Tiered reduces "
            f"over-flagging to {pct(c3t_real['over_flagging_rate'])} (F1 = "
            f"{fmt(c3t_real['f1'])}), while C3 Sqrt achieves "
            f"{pct(c3sq_real['over_flagging_rate'])} (F1 = {fmt(c3sq_real['f1'])}) and C3 "
            f"Sigmoid reaches {pct(c3sig_real['over_flagging_rate'])} (F1 = "
            f"{fmt(c3sig_real['f1'])}). The dramatic reduction from "
            f"{pct(c2_real['over_flagging_rate'])} to "
            f"{pct(c3sq_real['over_flagging_rate'])} demonstrates that confidence-weighted "
            f"thresholds provide substantial benefit when retrieval quality varies \u2014 "
            f"exactly the regime where adaptive thresholds are designed to operate."
        ),
        "Realistic retrieval"
    ))

    # ── Statistical significance ──
    updates.append((
        "On the standard benchmark, all p-values exceed 0.05",
        (
            f"On the standard benchmark, all p-values exceed 0.05: combined p = {mcn_comb_p}, "
            f"QA p = {mcn_qa_p}, summarisation p = {mcn_summ_p}. No C3 variant performs "
            f"significantly differently from C2 on per-sample retrieval. However, the realistic "
            f"experiment yields McNemar\u2019s p = {mcn_real_p} (statistic = "
            f"{fmt(mcn_real_stat, 3)}), confirming a significant difference \u2014 though C2 "
            f"wins on F1 ({fmt(c2_real['f1'])} vs {fmt(c3t_real['f1'])}), C3 achieves a more "
            f"practical operating point by drastically reducing over-flagging."
        ),
        "Statistical significance"
    ))

    # ── Chapter summary ──
    updates.append((
        "The results demonstrate that Cw-CONLI (C3) performs comparably to static CONLI (C2)",
        (
            f"The results demonstrate that Cw-CONLI (C3) performs comparably to static CONLI "
            f"(C2) on HaluEval\u2019s standard per-sample benchmark: combined F1 differs by "
            f"{abs(float(c3t['f1']) - float(c2['f1'])):.3f} ({fmt(c3t['f1'])} vs "
            f"{fmt(c2['f1'])}), and McNemar\u2019s p = {mcn_comb_p}. On QA, C3 variants reduce "
            f"over-flagging (C3 Sqrt: {pct(c3sq_qa['over_flagging_rate'])} vs C2: "
            f"{pct(c2_qa['over_flagging_rate'])}) with minimal F1 trade-off. Summarisation is "
            f"now functional (F1 \u2248 {fmt(c2_summ['f1'], 3)}) thanks to sliding-window NLI, "
            f"though over-flagging remains \u224898\u201399%. The realistic experiment reveals "
            f"where adaptive thresholds add value: C3 Sqrt reduces over-flagging from "
            f"{pct(c2_real['over_flagging_rate'])} to "
            f"{pct(c3sq_real['over_flagging_rate'])} (McNemar\u2019s p = {mcn_real_p}). "
            f"These findings are analysed in detail in Chapter 10."
        ),
        "Chapter summary"
    ))

    # ── RQ1 ──
    updates.append((
        "RQ1 asked whether Cw-CONLI (C3) improves hallucination detection F1",
        (
            f"RQ1 asked whether Cw-CONLI (C3) improves hallucination detection F1 compared "
            f"to static CONLI (C2). On the standard benchmark, the answer is no \u2014 C3 "
            f"and C2 converge. On the combined test set, C3 Tiered achieves F1 = "
            f"{fmt(c3t['f1'])} vs C2\u2019s {fmt(c2['f1'])} (\u0394 = "
            f"{abs(float(c3t['f1']) - float(c2['f1'])):.3f}). On QA, C2 leads with F1 = "
            f"{fmt(c2_qa['f1'])}. McNemar\u2019s p = {mcn_comb_p} on the combined set "
            f"confirms no significant difference. However, under realistic shared-index "
            f"retrieval, C3 shows a statistically significant difference (p = {mcn_real_p}), "
            f"though C2 wins on F1 ({fmt(c2_real['f1'])} vs {fmt(c3t_real['f1'])}). The "
            f"takeaway: adaptive thresholds do not improve F1 on this benchmark but become "
            f"relevant when retrieval confidence varies more widely."
        ),
        "RQ1"
    ))

    # ── RQ2 ──
    updates.append((
        "For over-flagging, C3 Sqrt achieves the best improvement on QA",
        (
            f"For over-flagging, C3 Sqrt achieves the best improvement on QA: "
            f"{pct(c3sq_qa['over_flagging_rate'])} vs C2\u2019s "
            f"{pct(c2_qa['over_flagging_rate'])}, a reduction of "
            f"{(float(c2_qa['over_flagging_rate']) - float(c3sq_qa['over_flagging_rate'])) * 100:.1f} "
            f"percentage points. C3 Tiered achieves {pct(c3t_qa['over_flagging_rate'])}. "
            f"This is consistent with the hypothesis that confidence-weighted thresholds can "
            f"reduce false positives. In the realistic retrieval experiment, the advantage is "
            f"dramatic: C3 Sqrt reduces over-flagging from C2\u2019s "
            f"{pct(c2_real['over_flagging_rate'])} to "
            f"{pct(c3sq_real['over_flagging_rate'])}, making the system practically usable "
            f"rather than a blanket rejection tool."
        ),
        "RQ2"
    ))

    # ── RQ3 ──
    updates.append((
        "On the QA dev set, all conditions achieve identical F1",
        (
            f"On the QA dev set, all conditions achieve identical F1 = {fmt(dev_qa_f1)}, "
            f"making it impossible to distinguish variants by F1 alone. On the test set, C3 "
            f"variants differentiate on over-flagging: C3 Sqrt achieves the lowest QA FPR "
            f"({pct(c3sq_qa['over_flagging_rate'])}) and highest precision "
            f"({fmt(c3sq_qa['precision'])}), while C3 Sigmoid achieves the best C3 F1 "
            f"({fmt(c3sig_qa['f1'])}). Among C3 variants, continuous functions (sqrt, sigmoid) "
            f"consistently outperform the tiered model on precision. The tiered model\u2019s "
            f"step-function discontinuity at the pivot creates a binary partition that does not "
            f"capture the gradual relationship between retrieval confidence and optimal threshold."
        ),
        "RQ3"
    ))

    # ── Realistic intro ──
    updates.append((
        "realistic retrieval experiment reveals where adaptive thresholds add genuine value",
        (
            f"The realistic retrieval experiment reveals where adaptive thresholds add genuine "
            f"value, and the results are now statistically significant (McNemar\u2019s p = "
            f"{mcn_real_p}):"
        ),
        "Realistic intro"
    ))

    # ── Realistic insight 1 ──
    updates.append((
        "C2 with T_static = 0.99 flags 100% of responses",
        (
            f"First, C2 with T_static = 0.99 flags {pct(c2_real['over_flagging_rate'])} of "
            f"responses as hallucinations (FPR = {pct(c2_real['over_flagging_rate'])}, F1 = "
            f"{fmt(c2_real['f1'])}). When retrieval quality degrades, a uniformly high "
            f"threshold becomes counterproductive. This confirms that static thresholds are "
            f"brittle outside controlled benchmark conditions."
        ),
        "Realistic insight 1"
    ))

    # ── Realistic insight 2 ──
    updates.append((
        "C3 variants dramatically reduce over-flagging",
        (
            f"Second, C3 variants dramatically reduce over-flagging: C3 Sqrt achieves "
            f"{pct(c3sq_real['over_flagging_rate'])} FPR (down from "
            f"{pct(c2_real['over_flagging_rate'])}), and C3 Tiered reaches "
            f"{pct(c3t_real['over_flagging_rate'])}. While C2 wins on F1 ({fmt(c2_real['f1'])} "
            f"vs {fmt(c3t_real['f1'])} for C3 Tiered), C3 Sqrt\u2019s operating point is far "
            f"more practical \u2014 a system that flags {pct(c3sq_real['over_flagging_rate'])} "
            f"of correct responses is usable, while one that flags "
            f"{pct(c2_real['over_flagging_rate'])} is not. This demonstrates the "
            f"correct-direction advantage of confidence-weighted thresholds in realistic "
            f"retrieval environments."
        ),
        "Realistic insight 2"
    ))

    # ── Summarisation discussion ──
    updates.append((
        "Summarization remains the most challenging task",
        (
            f"Summarization remains the most challenging task. With v2\u2019s sliding-window "
            f"NLI, the complete breakage of v1 (near-zero F1) is resolved \u2014 all conditions "
            f"now achieve F1 \u2248 {fmt(c2_summ['f1'], 3)}. However, over-flagging rates of "
            f"98\u201399.5% indicate that three interconnected issues persist:"
        ),
        "Summarisation discussion"
    ))

    # ── Token truncation ──
    updates.append((
        "Token truncation (partially addressed)",
        (
            "1. Token truncation (partially addressed): v2\u2019s sliding-window NLI splits "
            "premises into overlapping 400-token windows, eliminating the complete failure "
            "mode of v1. However, the aggregation strategy (max across windows) may miss "
            "cases where the summary synthesises information scattered across multiple "
            "non-overlapping sections."
        ),
        "Token truncation issue"
    ))

    # ── Future work ──
    updates.append((
        "Improved sliding-window NLI: The v2 sliding-window approach",
        (
            "2. Improved sliding-window NLI: The v2 sliding-window approach (400-token "
            "windows, 200-token stride, max aggregation) fixes the v1 truncation breakage "
            "but could be extended with weighted aggregation or attention-based fusion to "
            "better handle summaries that synthesise information across multiple document "
            "sections."
        ),
        "Future work"
    ))

    # ── Chapter conclusion ──
    updates.append((
        "This chapter has interpreted the experimental results in context",
        (
            f"This chapter has interpreted the experimental results in context. On HaluEval\u2019s "
            f"standard per-sample benchmark, Cw-CONLI and static CONLI converge (McNemar\u2019s "
            f"p = {mcn_comb_p}) due to tight retrieval score clustering. However, under realistic "
            f"shared-index retrieval, the difference is significant (p = {mcn_real_p}): C3 Sqrt "
            f"reduces over-flagging from {pct(c2_real['over_flagging_rate'])} to "
            f"{pct(c3sq_real['over_flagging_rate'])}. The primary contribution is v2 engineering "
            f"\u2014 sliding-window NLI, claim decomposition, and BGE embeddings \u2014 which fix "
            f"fundamental pipeline limitations. Continuous weighting functions (sqrt, sigmoid) "
            f"consistently outperform the tiered variant on precision. All four research "
            f"objectives are achieved. Future work should evaluate on datasets with greater "
            f"retrieval diversity to fully test the Cw-CONLI hypothesis."
        ),
        "Chapter conclusion"
    ))

    return updates


# ── Table updates ────────────────────────────────────────────────────────

def update_tables(doc, r, dry_run=False):
    """Update Tables 20-25 with canonical numbers."""
    changes = 0
    tune_comb = r.get("tune_v2", {})
    tune_qa = r.get("tune_qa_v2", {})
    comb = r.get("comp_v2_test", {})
    qa = r.get("comp_qa_v2_test", {})
    real = r.get("comp_realistic_v2_test", {})
    mcn_comb = r.get("mcn_v2_test", {})
    mcn_qa = r.get("mcn_qa_v2_test", {})
    mcn_real = r.get("mcn_realistic_v2_test", {})

    # ── Table 20: Dev tuning — Combined ──
    t20 = doc.tables[20]
    t20_data = [
        (1, tune_comb["C2"], "T_static = {T_static}"),
        (2, tune_comb["C3_tiered"], "pivot={pivot}, T_s={T_strict}, T_l={T_lenient}"),
        (3, tune_comb["C3_sqrt"], "T_s={T_strict}, T_l={T_lenient}"),
        (4, tune_comb["C3_sigmoid"], "T_s={T_strict}, T_l={T_lenient}"),
    ]
    for row_idx, entry, param_fmt in t20_data:
        params_str = param_fmt.format(**entry["best_params"])
        if not dry_run:
            set_cell(t20, row_idx, 1, params_str)
            set_cell(t20, row_idx, 2, fmt(entry["best_f1"]))
    print(f"  Table 20: Dev tuning (combined)")
    changes += 1

    # ── Table 21: Dev tuning — QA ──
    t21 = doc.tables[21]
    t21_data = [
        (1, tune_qa["C2"], "T_static = {T_static}"),
        (2, tune_qa["C3_tiered"], "pivot={pivot}, T_s={T_strict}, T_l={T_lenient}"),
        (3, tune_qa["C3_sqrt"], "T_s={T_strict}, T_l={T_lenient}"),
        (4, tune_qa["C3_sigmoid"], "T_s={T_strict}, T_l={T_lenient}"),
    ]
    for row_idx, entry, param_fmt in t21_data:
        params_str = param_fmt.format(**entry["best_params"])
        if not dry_run:
            set_cell(t21, row_idx, 1, params_str)
            set_cell(t21, row_idx, 2, fmt(entry["best_f1"]))
    print(f"  Table 21: Dev tuning (QA)")
    changes += 1

    # ── Tables 22-24: Test set results ──
    table_configs = [
        (22, comb, "Combined test"),
        (23, qa, "QA test"),
        (24, real, "Realistic test"),
    ]
    conditions = ["C2 (Static CONLI)", "C3 Tiered", "C3 Sqrt", "C3 Sigmoid"]
    for tbl_idx, data, label in table_configs:
        tbl = doc.tables[tbl_idx]
        for row_offset, cond in enumerate(conditions):
            row_data = data.get(cond, {})
            if not row_data:
                continue
            row_idx = row_offset + 2  # skip header + C1 row
            if not dry_run:
                set_cell(tbl, row_idx, 1, fmt(row_data["f1"]))
                set_cell(tbl, row_idx, 2, fmt(row_data["precision"]))
                set_cell(tbl, row_idx, 3, fmt(row_data["recall"]))
                set_cell(tbl, row_idx, 4, fmt(row_data["accuracy"]))
                set_cell(tbl, row_idx, 5, fmt(row_data["over_flagging_rate"]))
        print(f"  Table {tbl_idx}: {label}")
        changes += 1

    # ── Table 25: McNemar's test ──
    t25 = doc.tables[25]
    mcn_rows = [
        (1, mcn_comb),
        (2, mcn_qa),
        (3, mcn_real),
    ]
    for row_idx, mcn in mcn_rows:
        if not dry_run:
            set_cell(t25, row_idx, 1, mcn.get("c3_variant", "?").replace("C3_", "C3 ").replace("tiered", "Tiered"))
            set_cell(t25, row_idx, 2, str(mcn.get("b_c2_right_c3_wrong", "?")))
            set_cell(t25, row_idx, 3, str(mcn.get("c_c2_wrong_c3_right", "?")))
            set_cell(t25, row_idx, 4, fmt(mcn.get("statistic", "?"), 3))
            set_cell(t25, row_idx, 5, str(mcn.get("p_value", "?")))
            set_cell(t25, row_idx, 6, "Yes" if mcn.get("significant") else "No")
    print(f"  Table 25: McNemar's test")
    changes += 1

    return changes


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Update thesis with canonical results")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry run)")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup")
    args = parser.parse_args()

    if not THESIS.exists():
        print(f"ERROR: {THESIS} not found")
        sys.exit(1)
    if not RESULTS.exists():
        print(f"ERROR: {RESULTS}/ directory not found")
        sys.exit(1)

    dry_run = not args.apply
    if dry_run:
        print("DRY RUN — no changes will be written. Use --apply to write.\n")

    # Load results
    r = load_all_results()
    print(f"Loaded {len(r)} result files from {RESULTS}/\n")

    # Backup
    if args.apply and not args.no_backup:
        backup = f"thesis_updated_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        shutil.copy2(THESIS, backup)
        print(f"Backup: {backup}\n")

    doc = docx.Document(str(THESIS))
    changes = 0

    # Paragraph updates
    print("Paragraph updates:")
    updates = build_paragraph_updates(r)
    for needle, new_text, desc in updates:
        idx, p = find_para(doc, needle)
        if p is None:
            print(f"  SKIP: {desc} — search text not found (already updated?)")
            continue
        if not dry_run:
            replace_para_text(p, new_text)
        print(f"  {'WOULD UPDATE' if dry_run else 'UPDATED'} P{idx}: {desc}")
        changes += 1

    # Table updates
    print("\nTable updates:")
    changes += update_tables(doc, r, dry_run=dry_run)

    # Save
    if args.apply:
        doc.save(str(THESIS))
        print(f"\nSaved {THESIS} with {changes} changes.")
        print("Verify: open in Word, check formatting and tables.")
    else:
        print(f"\nDry run complete. {changes} changes would be made.")
        print("Run with --apply to write changes.")


if __name__ == "__main__":
    main()
