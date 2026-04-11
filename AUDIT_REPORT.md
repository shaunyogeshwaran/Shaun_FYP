# AFLHR Lite FYP — Comprehensive Thesis & Project Audit

**Date:** 2026-03-30
**Module:** 6COSC023W — Computer Science Final Project
**Student:** Shaun Yogeshwaran (w1912919)
**Institution:** University of Westminster / Informatics Institute of Technology (IIT)

---

## 1. 10-CHAPTER STRUCTURE COMPLIANCE

**VERDICT: ALL 10 CHAPTERS EXIST**

| # | Required Chapter | Status | Evidence |
|---|-----------------|--------|----------|
| 1 | Introduction | PRESENT | update_thesis.py (RQs, objectives updated) |
| 2 | Literature Review | PRESENT | Research gap references exist |
| 3 | Methodology | PRESENT | Section 3.3.4 algorithmic pseudocode |
| 4 | Software Requirement Specification (SRS) | PRESENT | Referenced in format_thesis.py |
| 5 | SLEP (Social, Legal, Ethical, Professional) | PRESENT | Sections 5.2.1-5.2.5 confirmed |
| 6 | Design | PRESENT | Referenced in format_thesis.py |
| 7 | Implementation | PRESENT | Contains figures 7.x |
| 8 | Testing | PRESENT | Sections 8.1-8.10+, Tables 20-27 |
| 9 | Critical Evaluation | PRESENT | Sections 9.3-9.7, evaluator profiles |
| 10 | Conclusion | PRESENT | Referenced in update_thesis.py |

### HIGH-RISK: Chapter 10 Subsection Completeness

Template requires **12 specific subsections**:

| Section | Required Content | Verifiable from code? |
|---------|-----------------|----------------------|
| 10.1 | Chapter Overview | NO |
| 10.2 | Achievements of Research Aims & Objectives (table) | NO |
| 10.3 | Utilization of Knowledge from Course | NO |
| 10.4 | Use of Existing Skills | NO |
| 10.5 | Use of New Skills | NO |
| 10.6 | Achievement of Learning Outcomes | NO |
| 10.7 | Problems and Challenges Faced | NO |
| 10.8 | Deviations | NO |
| 10.9 | Limitations of the Research | NO |
| 10.10 | Future Enhancements | NO |
| 10.11 | Contribution to Body of Knowledge | NO |
| 10.12 | Concluding Remarks | NO |

**Action:** Open `thesis_updated.docx` and verify all 12 subsections exist. This is the most likely chapter to be missing content.

---

## 2. AI USAGE DECLARATIONS

**VERDICT: NO DECLARATIONS FOUND — REQUIRES IMMEDIATE MANUAL CHECK**

### Template Warning (page 42, RED/YELLOW highlight):
> "WARNING: while chatgpt can be used to understand the content to cover, never copy and paste anything from chatgpt — it is known as plagiarism"
> "Read Guidance for students on the use of Generative AI in the BB Module Page"

### Findings:
- **In code files:** Zero AI usage declarations in any `.py` file
- **CLAUDE.md:** Developer guide for Claude Code interaction — NOT a thesis declaration
- **In SLEP chapter:** Cannot verify from code — must check Section 5.2.3 in docx

### If AI tools were used, they MUST be declared in:
1. SLEP Chapter (Section 5.2.3 Ethical Issues)
2. Code comments where AI-assisted code appears
3. Template states: "Any code that is used without citations will be treated as plagiarized work and you will be penalized to get zero for the FYP model" (Ch7, highlighted RED)

**SEVERITY: CRITICAL — Academic misconduct risk if AI was used and not declared**

---

## 3. LITERATURE REVIEW & RESEARCH GAP

**VERDICT: CLEAR AND WELL-DEFINED**

### Done:
- Research gap identified: No existing work combines retrieval confidence with adaptive NLI thresholds
- Prior work comparison: CoNLI (Phung et al.), LLM-as-judge (GPT-4), Azure NLI
- Three research questions (RQ1-RQ3) clearly defined
- Dataset selection: HaluEval (Li et al., 2023) — 20K samples

### Cannot verify from code (manual check needed):
- [ ] Concept Map present?
- [ ] Literature Survey Table in tabular format (Citation, Summary, Limitation, Contribution)?
- [ ] Reference count >= 20 with 80% from high-impact journals/conference papers?
- [ ] Harvard referencing style used consistently?
- [ ] Benchmarking and Evaluation section in Ch2?

---

## 4. METHODOLOGY & PIPELINE

**VERDICT: PIPELINE IS COMPREHENSIVE**

### Done:
- Two-layer architecture: RAG retrieval -> NLI verification -> confidence-weighted verdict
- v1 -> v2 progression clearly documented
- Three conditions (C1/C2/C3) with three C3 variants (tiered/sqrt/sigmoid)
- Precompute-then-evaluate architecture
- Grid search tuning with full logging (90 C2 + 3,618 C3 iterations)

### Cannot verify (manual check needed):
- [ ] Saunders Research Onion table (Philosophy/Approach/Strategy/Time Horizon/Data Collection)?
- [ ] Development methodology named and justified (Waterfall/SCRUM/Agile)?
- [ ] Gantt Chart with WBS, start/end dates?
- [ ] Risk & Mitigation table with severity/frequency?
- [ ] Formal hypothesis statement?

---

## 5. IMPLEMENTATION ALIGNED WITH RESEARCH CLAIMS

**VERDICT: EXCELLENT — ALL CLAIMS BACKED BY CODE AND DATA**

| Claim | Evidence | Verified? |
|-------|----------|-----------|
| Sliding-window NLI fixes summarization (99% FPR -> F1~0.66) | `engine.py:verify_windowed()`, 400-token windows, 200 stride | YES |
| Claim decomposition with min aggregation | `engine.py:verify_decomposed()`, NLTK punkt, min(scores) | YES |
| BGE embeddings improve retrieval | `config.py` BAAI/bge-small-en-v1.5 | YES |
| Cw-CONLI adapts threshold on retrieval confidence | `engine.py:calculate_verdict()`, tiered/sqrt/sigmoid | YES |
| Temperature scaling failed (T=10 boundary) | `calibrate.py`, `calibration_temperature.json` T=9.999996 | YES |
| C3 converges to C2 on standard benchmark (p=1.0) | `mcnemar_v2_test.json` | YES |
| C3 significant in realistic scenario (p=1.4e-5) | `mcnemar_realistic_v2_test.json` | YES |
| 20,000 samples evaluated | 14K dev + 6K test CSVs | YES |
| Primary contribution is v2 engineering | Documented in CLAUDE.md, update_thesis.py | YES |

No overclaiming detected. Honest framing of null result is a strength.

---

## 6. EXPERIMENTAL RESULTS & EVALUATION METRICS

**VERDICT: STRONG for BSc, with notable gaps**

### Metrics Present:

| Metric | Present | Where |
|--------|---------|-------|
| F1 Score | YES | Primary metric, all comparisons |
| Precision | YES | All comparison CSVs |
| Recall | YES | All comparison CSVs |
| Accuracy | YES | All comparison CSVs |
| Over-flagging Rate (FPR) | YES | All comparison CSVs |
| Confusion Matrices | YES | 4 PNG files |
| Latency (mean, median, p95) | YES | Eval JSONs, boxplots |
| McNemar's Test | YES | 4 JSON files |
| Calibration ECE | YES | Reliability diagrams |
| NLI Score Distributions | YES | 8 PNG files |
| Retrieval Score Distributions | YES | 4 PNG files |

### Experiment Scope:
- 5 conditions: C1, C2, C3-tiered, C3-sqrt, C3-sigmoid
- 3 task splits: Combined, QA-only, Summarization-only
- 2 retrieval scenarios: Standard (ground-truth) and Realistic (shared-index)
- 40 visualization figures across 9 metric types

### Key Results:

| Metric | C2 (Static) | C3 Best | Significant? |
|--------|-------------|---------|-------------|
| Combined F1 (standard) | 0.6988 | 0.6998 (tiered) | NO (p=1.0) |
| QA F1 | 0.7702 | 0.7679 (tiered) | NO (p=0.46) |
| Summarization F1 | ~0.663 | ~0.663 | NO (p=0.81) |
| Realistic F1 | 0.6701 | 0.6558 (tiered) | YES (p=1.4e-5) |
| Realistic Over-flagging | 100% | 44.9% (sqrt) | Major improvement |

### Ablation Studies Present:

| Ablation | Status |
|----------|--------|
| C1 vs C2 vs C3 (condition comparison) | DONE |
| Three C3 variants (tiered/sqrt/sigmoid) | DONE |
| Standard vs realistic retrieval | DONE |
| Decomposed vs whole-response NLI scoring | DONE |
| Calibration enabled vs disabled | DONE |
| **Individual v2 features (windowed only, decomp only, BGE only)** | **NOT DONE** |

---

## 7. GAPS AND MISSING ITEMS

### Experimental Gaps:

| Gap | Severity | Description |
|-----|----------|-------------|
| No individual feature ablation | **MEDIUM-HIGH** | Cannot isolate contribution of windowed NLI vs decomposition vs BGE separately. All bundled in v2. A marker could ask: "What's the effect of windowed NLI alone?" |
| No external baseline comparison | **MEDIUM** | Only internal C1/C2 baselines. No comparison against published CoNLI/SelfCheckGPT results on HaluEval. |
| No repeated runs / confidence intervals | **LOW-MEDIUM** | Single run, no error bars. Standard for BSc but noted. |
| No cross-dataset evaluation | **LOW** | Only HaluEval. No TruthfulQA/FactScore validation. |

### Structural/Compliance Gaps:

| Gap | Severity | Description |
|-----|----------|-------------|
| AI usage not declared (if AI was used) | **CRITICAL** | Academic misconduct risk |
| Chapter 10 may be missing subsections | **HIGH** | 12 required, many are reflective sections not touched by scripts |
| Evaluator count low (6 vs recommended 10) | **MEDIUM** | 2 domain + 4 technical. Template suggests 5+5 |
| Ch3/Ch4 diagrams unverified | **MEDIUM** | Saunders Onion, Gantt, Rich Picture, Use Case — manual check |
| Reference count/quality unknown | **MEDIUM** | Must verify >=20 refs, 80% high-impact, Harvard style |
| Class imbalance not discussed | **LOW** | HaluEval may be balanced but should be mentioned |

---

## 8. TECHNICAL DEPTH ASSESSMENT

| Criterion | Assessment |
|-----------|-----------|
| End-to-end pipeline design | STRONG — embedding -> FAISS -> NLI -> verdict -> API -> frontend |
| Algorithm/model selection justified | YES — documented rationale for each model choice |
| Data preprocessing & split | YES — 70/30 dev/test, seed=42, no data leakage |
| Overfitting handling | YES — dev/test separation, no model fine-tuning |
| Class imbalance | NOT DISCUSSED — should be mentioned even if balanced |
| Generalization | WEAK — single dataset, standard vs realistic is closest proxy |

---

## 9. NOVELTY & CONTRIBUTION

| Contribution | Type | Significance |
|---|---|---|
| Sliding-window NLI for hallucination detection | Novel application | **HIGH** — fixes 99% FPR -> F1~0.66 |
| Claim decomposition + min aggregation | Novel combination | Moderate — enables per-claim explainability |
| Confidence-weighted threshold adaptation (Cw-CONLI) | Novel mechanism | Moderate — significant on realistic, null on standard |
| Calibration negative result (T=10 boundary) | Documented finding | Valuable — honest negative result |
| v2 engineering bundle | Primary contribution | **HIGH** — appropriately framed |

---

## 10. CRITICAL EVALUATION CHAPTER (Ch9)

### Evaluator Count:
- Template recommends: 5 technical + 5 domain experts
- Thesis has: **2 domain experts (DE-1, DE-2) + 4 technical experts (TE-1 to TE-4) + Focus group = 6 evaluators + focus group**
- May be flagged as insufficient

### Sections Present:
- 9.3 Evaluation Criteria
- 9.5 Selection of Evaluators (Table 9.3)
- 9.6 Expert Feedback (9.6.1-9.6.4)
- 9.7 Limitations

### Cannot verify:
- [ ] 9.4 Self-Evaluation section present?
- [ ] 9.8 FR/NFR Implementation mapping?
- [ ] 9.9 Chapter Summary?

---

## 11. TESTING COMPLETENESS

**VERDICT: COMPREHENSIVE**

| Section | Required | Status |
|---------|----------|--------|
| Model Testing (AI/ML) | YES | DONE — Tables 20-25 |
| Benchmarking | YES | PARTIAL — internal only, no external |
| Further Evaluations | Optional | DONE — realistic retrieval |
| Results Discussion | YES | DONE |
| Functional Testing | YES | DONE — 18 tests, Table 26, all passing |
| Non-Functional Testing | YES | DONE — 10 tests, Table 27, all passing |
| Testing Limitations | YES | CANNOT VERIFY |

---

## 12. FORMATTING COMPLIANCE (Manual Check Required)

- [ ] Cover page without page number
- [ ] Abstract <= 300 words, 3 paragraphs + Subject Descriptors + Keywords
- [ ] Declaration page present
- [ ] Acknowledgements present
- [ ] Table of Contents with Roman numerals
- [ ] List of Figures, Tables, Abbreviations
- [ ] Times New Roman, 12pt body, 14pt subheadings, 16pt chapter headings
- [ ] Line spacing 1.5, Justified, 1-inch margins
- [ ] Headers: Left=project name, Right=chapter name
- [ ] Footers: Page number center, student name/ID
- [ ] Chapters 1-10 <= 100 pages (Arabic numerals)
- [ ] Harvard referencing style, >= 20 sources, 80% high-impact
- [ ] All figures have captions + surrounding description paragraphs
- [ ] No line borders in header/footer (except coversheet)

---

## 13. RISK SUMMARY (Priority Order)

| Priority | Issue | Action Required |
|----------|-------|----------------|
| **CRITICAL** | AI usage not declared (if AI was used) | Open docx, check SLEP 5.2.3, add declaration if needed |
| **HIGH** | Chapter 10 may be missing subsections | Open docx, verify 10.1-10.12 all exist |
| **HIGH** | No individual feature ablation | Run windowed-only, decomp-only experiments if time permits |
| **MEDIUM** | No external baseline comparison | Add table comparing against published HaluEval results |
| **MEDIUM** | Only 6 evaluators (template suggests 10) | Add more evaluators or justify smaller count |
| **MEDIUM** | Ch3/Ch4 diagrams unverified | Check Saunders Onion, Gantt, Rich Picture, Use Case exist |
| **MEDIUM** | Reference count/quality unknown | Verify >=20 refs, 80% from journals/conferences |
| **LOW** | No repeated runs / confidence intervals | Document as limitation in Ch10 |
| **LOW** | Class imbalance not discussed | Add brief mention in Ch8 results discussion |
| **LOW** | Single dataset only | Already acknowledged as limitation |

---

## 14. WHAT'S DONE WELL (Strengths to Highlight in Viva)

1. **Intellectual honesty**: C3-C2 convergence (p=1.0) documented as null result rather than hidden
2. **Correct contribution framing**: v2 engineering > C3 adaptive thresholds
3. **Comprehensive evaluation**: 20K samples, 5 conditions, statistical testing
4. **Reproducible pipeline**: Seeds, checkpoints, automated thesis updates
5. **Full-stack prototype**: FastAPI backend + React frontend
6. **Negative results documented**: Calibration failure (T=10 boundary)
7. **Realistic scenario**: Shared-index retrieval exposes real-world behavior
8. **Automated tooling**: update_thesis.py, format_thesis.py, test_thesis.py
9. **40+ visualization figures** across 9 metric types
10. **Functional + non-functional testing** with passing suites

---

## Manual Verification Checklist

Open `thesis_updated.docx` and check:

- [ ] **Ch1**: All 13 subsections? Research Objectives table with LO mapping? H/W S/W table?
- [ ] **Ch2**: Concept Map? Literature Survey Table? >=20 references? 80% high-impact?
- [ ] **Ch3**: Saunders Onion table? Gantt Chart? Risk & Mitigation table?
- [ ] **Ch4**: Rich Picture? Stakeholder Onion? Context Diagram? Use Case Diagram? MoSCoW table?
- [ ] **Ch5**: SLEP 2x2 grid? BCS Code of Conduct referenced? AI tool usage declared?
- [ ] **Ch6**: System Architecture diagram? Algorithm pseudocode? Wireframes?
- [ ] **Ch7**: Technology selection justified? Code snippets with citations? Dataset statistics?
- [ ] **Ch8**: Testing criteria defined? Benchmarking discussion? Testing limitations section?
- [ ] **Ch9**: Self-evaluation? Evaluator count sufficient? FR/NFR implementation mapping?
- [ ] **Ch10**: ALL 12 subsections (10.1-10.12) present and substantive?
- [ ] **Formatting**: TNR 12pt? 1.5 spacing? Justified? 1-inch margins? <=100 pages?
- [ ] **Front matter**: Declaration? Acknowledgements? ToC? List of Figures? List of Tables? Abbreviations?
- [ ] **All figures** have captions and surrounding description paragraphs?
