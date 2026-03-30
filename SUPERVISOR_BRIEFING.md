# Supervisor Briefing — AFLHR Lite (Cw-CONLI)

**Date:** 2026-03-22
**Meeting:** Supervisor catch-up (2026-03-23)

---

## 1. What the project does

A two-layer hallucination detection pipeline for LLM outputs:

1. **RAG Retrieval** — FAISS index finds relevant evidence for a given query
2. **NLI Verification** — RoBERTa-large-MNLI checks if the LLM response is entailed by the evidence
3. **Verdict** — Compares entailment probability against a threshold → VERIFIED or HALLUCINATION

The core research question: **should retrieval quality influence how strict verification is?**

- **C1** — RAG-only (no NLI). Baseline.
- **C2** — Static CONLI. Fixed threshold regardless of retrieval confidence.
- **C3** — Cw-CONLI. Adaptive threshold that tightens when retrieval confidence is low.

---

## 2. Relationship to prior work (Microsoft CoNLI)

AFLHR Lite builds on the CoNLI concept (NLI for hallucination detection) but is **not** a copy. Key differences:

| | Microsoft CoNLI | AFLHR Lite |
|---|---|---|
| NLI engine | GPT-3.5/GPT-4 via prompting | RoBERTa-large-MNLI (local classifier) |
| Retrieval | None — source document given | FAISS + sentence embeddings |
| Detection | Sentence → entity-level (Azure NER) | Sentence decomposition + sliding-window NLI |
| Mitigation | GPT rewrites flagged text | Detection only |
| Infrastructure | Azure OpenAI + Azure Text Analytics | Runs locally on CPU, no cloud costs |
| Novel addition | — | Confidence-weighted adaptive thresholds (C3) |

The name "Cw-CONLI" explicitly signals the lineage. This is standard academic practice — extending cited prior work, not replicating it.

---

## 3. What actually worked

### v2 engineering improvements (primary contribution)

- **Sliding-window NLI** — Fixed RoBERTa's 512-token limit. Summarisation went from 99% FPR (completely broken in v1) to F1 ~ 0.67 in v2.
- **Claim decomposition** — Splits responses into sentences, verifies each independently. Catches partial hallucinations that whole-response NLI misses.
- **BGE embedding upgrade** — BAAI/bge-small-en-v1.5 (2023) replaces all-MiniLM-L6-v2 (2021). Better retrieval quality.
- **Precompute-then-sweep architecture** — Model inference runs once; threshold tuning is instant arithmetic on cached scores.

### Realistic scenario result

- McNemar's p = 1.40 x 10^-5 (significant) when retrieval quality varies (shared-index setting)
- This is where the adaptive threshold was designed to help, and it does

---

## 4. What didn't work (honest negative results)

### C3 vs C2 on standard benchmark: p = 1.0

On HaluEval with per-task retrieval, C3 and C2 converge to essentially the same operating point:

| Condition | Combined F1 | Best dev F1 |
|-----------|------------|-------------|
| C2 (static) | 0.6988 | 0.7053 |
| C3 tiered | 0.6998 | 0.7055 |
| C3 sqrt | 0.6998 | 0.7054 |
| C3 sigmoid | 0.6992 | 0.7054 |

**Why:** HaluEval retrieval scores are uniformly high (~0.8-0.9), so the adaptive mechanism has nothing to adapt to. The threshold variance between strict and lenient is negligible.

### Calibration: T = 10.0 (optimizer boundary)

Temperature scaling (Guo et al. 2017) on RoBERTa-MNLI logits hit the boundary at T ~ 10. The logits are not calibratable with this technique. Documented as a negative result; `use_calibration=False` everywhere.

### Not competitive with SOTA

| System | HaluEval QA F1 | Approach |
|--------|---------------|----------|
| AFLHR Lite | 0.770 | Single NLI model + adaptive threshold |
| HALT-RAG (2025) | 0.979 | Multi-model NLI ensemble + lexical features |

---

## 5. What the pipeline does NOT do

1. **No mitigation** — Detects hallucinations but doesn't fix them
2. **Fails when retrieval fails** — If the knowledge base lacks relevant info, NLI verifies against irrelevant text
3. **Misses subtle distortions** — NLI checks semantic similarity, not factual precision (e.g., "65%" vs "67%")
4. **English + HaluEval only** — Not tested on other languages or domains
5. **No multi-hop reasoning** — Can't chain evidence across multiple documents

---

## 6. What's genuinely novel

### The research question itself

Nobody before had asked: **"should retrieval confidence modulate NLI verification strictness?"** Existing work treats retrieval and verification as independent stages. SGIC improves retrieval, HALT-RAG improves NLI — but nobody had connected the two. That's the "evidence blindness" gap. Even though the answer turned out to be "it doesn't help much on clean benchmarks," the question is original.

### Sliding-window NLI for hallucination detection

RoBERTa-MNLI has a 512-token hard limit. Prior work either used LLM-as-judge (CoNLI with GPT-4-32k) or just truncated. AFLHR splits long premises into overlapping windows and takes the max entailment score. This isn't a novel algorithm in general, but its application to NLI-based hallucination detection fixed summarisation from completely broken (99% FPR) to usable (F1 ~ 0.67). That's a practical contribution.

### The negative results, properly documented

- Calibration doesn't work on RoBERTa-MNLI (T = 10.0 boundary)
- Adaptive thresholds converge to static ones when retrieval variance is low

These aren't "novel" in the traditional sense, but they are **new knowledge**. Nobody had reported either finding before. Future researchers won't waste time trying the same things.

### What's NOT novel

- Using NLI for hallucination detection (CoNLI, 2023)
- RAG retrieval with FAISS (standard practice)
- Claim decomposition (used in various forms elsewhere)
- The models themselves (all off-the-shelf)

### The honest one-liner

> "The novelty is in the connection — using retrieval confidence as a dynamic cost-sensitive proxy for NLI threshold selection — and in the engineering that made a lightweight, CPU-runnable pipeline actually work across both QA and summarisation tasks."

Narrow novelty, but real. For a BSc FYP, that's the right scope.

---

## 7. Honest thesis framing

> The primary contribution is **v2 engineering** — windowed NLI, claim decomposition, BGE embeddings — not the C3 adaptive threshold mechanism itself.

The research gap (evidence blindness — no prior work connecting retrieval confidence to NLI verification strictness) is real and validated. The proposed solution (Cw-CONLI) addresses it in realistic conditions but does not improve on static thresholds in controlled benchmarks.

**This is a well-executed BSc project with:**
- A clearly identified research gap
- A proposed solution tested rigorously
- Honest reporting of both positive and negative results
- A working end-to-end system (API + React frontend, runs on CPU)
- Engineering contributions that fixed real problems (summarisation was unusable in v1)

**It is not:**
- A SOTA-beating algorithm
- A novel architecture
- A breakthrough result

---

## 8. Key numbers to remember

| Metric | Value |
|--------|-------|
| C2 combined F1 (test) | 0.6988 |
| C3 tiered F1 (test) | 0.6998 |
| C3 vs C2 McNemar p (standard) | 1.0 (not significant) |
| C3 vs C2 McNemar p (realistic) | 1.40 x 10^-5 (significant) |
| Summarisation v1 FPR | ~99% (broken) |
| Summarisation v2 F1 | ~0.67 (fixed) |
| Calibration temperature | 10.0 (boundary — unusable) |
| Test samples | 6,000 (3K QA + 3K summarisation) |
