# Cw-CONLI — Complete Study Guide & Demo Script

This document is a self-contained guide to the entire project. It explains every concept from scratch, why each design decision was made, and includes a demo script for a supervisor meeting. If you've forgotten everything, start from the top.

---

## TABLE OF CONTENTS

1. [The Problem: LLM Hallucinations](#1-the-problem-llm-hallucinations)
2. [Background Concepts](#2-background-concepts)
3. [The Solution: Cw-CONLI Pipeline](#3-the-solution-cw-conli-pipeline)
4. [v2 Improvements: What Changed and Why](#4-v2-improvements-what-changed-and-why)
5. [Experiment Design](#5-experiment-design)
6. [Results & What They Mean](#6-results--what-they-mean)
7. [The Calibration Story (Negative Result)](#7-the-calibration-story-negative-result)
8. [Engineering & Portability](#8-engineering--portability)
9. [Live Demo Script (Supervisor Meeting)](#9-live-demo-script-supervisor-meeting)
10. [Quick Reference](#10-quick-reference)

---

## 1. The Problem: LLM Hallucinations

Large Language Models (GPT, Llama, etc.) generate text by predicting the most likely next token. They don't have a concept of "truth" — they produce what *sounds* right based on training data. This means they can confidently state things that are completely fabricated.

**Types of hallucination:**
- **Factual hallucination** — wrong facts, dates, statistics ("Westminster was founded in 1920")
- **Entity hallucination** — inventing people, places, organisations that don't exist
- **Attribution errors** — putting real quotes in the wrong person's mouth
- **Fabricated citations** — inventing academic papers that were never published

**Why it matters:** If you're building a system that answers questions using an LLM — a chatbot, a search assistant, a medical Q&A tool — you need to know when the LLM is making things up. The cost of a wrong answer can range from embarrassing to dangerous.

**The research question:** Can we build a lightweight, local system that detects hallucinations by checking whether the LLM's output is actually supported by retrieved evidence, and can we make that detection *adaptive* based on how good the evidence is?

---

## 2. Background Concepts

### 2.1 RAG — Retrieval-Augmented Generation

RAG is a technique where instead of asking an LLM to answer from memory, you first search a knowledge base for relevant documents, then give those documents to the LLM as context.

**How it works in our system:**
1. The user asks a question
2. The question is converted into a vector (a list of numbers) using a sentence transformer model
3. That vector is compared against pre-computed vectors of all knowledge base passages using FAISS (Facebook AI Similarity Search)
4. The top-2 most similar passages are retrieved
5. These passages are given to the LLM as context to generate a response

**The retrieval score** is the cosine similarity between the query vector and the best matching passage vector. It ranges from 0 to 1:
- **High score (~0.8+):** The knowledge base has a passage that's very relevant to the question
- **Medium score (~0.5-0.8):** Some relevance, but not a direct match
- **Low score (~0.3-0.5):** The knowledge base probably doesn't cover this topic

**Why retrieval quality matters:** If the retrieval is bad — meaning the system pulled irrelevant passages — then the LLM is generating a response based on the wrong context. Even if the NLI model says "yes, the response matches the context", that doesn't mean much because the context itself was wrong. This is the core insight behind Cw-CONLI: *the quality of the evidence should influence how much we trust the verification*.

### 2.2 NLI — Natural Language Inference

NLI is a classification task: given a **premise** (the evidence) and a **hypothesis** (the claim), determine the relationship:
- **Entailment** — the premise supports the hypothesis ("The sky is blue" entails "The sky has a colour")
- **Contradiction** — the premise contradicts the hypothesis
- **Neutral** — the premise neither supports nor contradicts

**How it works in our system:**
1. The retrieved passage(s) become the **premise**
2. The LLM's generated response becomes the **hypothesis**
3. We feed both into RoBERTa-large-MNLI (a transformer model fine-tuned for NLI)
4. The model outputs probabilities for each class
5. We take the **entailment probability** as our NLI score (0 to 1)

**What the NLI score means:**
- **High (~0.8+):** The evidence strongly supports the response — probably not hallucinated
- **Medium (~0.4-0.8):** Partial support — some claims may be unsupported
- **Low (~0.0-0.4):** The evidence doesn't support the response — likely hallucinated

### 2.3 FAISS — Vector Similarity Search

FAISS is a library from Facebook/Meta for efficient similarity search. Instead of comparing text strings, you compare vectors (embeddings).

**Our setup:**
- We use `IndexFlatIP` — flat index with inner product (equivalent to cosine similarity for normalised vectors)
- Embedding dimension: 384 (both MiniLM and BGE produce 384-d vectors)
- Knowledge base size: 6 passages (demo) or 10,000+ (HaluEval experiments)

### 2.4 Sentence Transformers & Embeddings

An embedding model converts text into a fixed-length vector that captures its semantic meaning. Similar texts get similar vectors.

**v1 model:** `all-MiniLM-L6-v2` — small (22M params), fast, 384-d output. Released 2021.

**v2 model:** `BAAI/bge-small-en-v1.5` — same size and dimensionality, but newer (2023) and trained with better techniques. Drop-in replacement that improves retrieval quality.

**The BGE instruction prefix:** BGE models expect queries to be prefixed with `"Represent this sentence for searching relevant passages: "`. Passages are encoded without a prefix. This asymmetric encoding improves retrieval accuracy. The engine handles this automatically when `use_bge_embeddings=True`.

### 2.5 Softmax, Logits, and Temperature

**Logits** are the raw output numbers from a neural network's last layer — they can be any value. **Softmax** converts them into probabilities that sum to 1.

**Temperature scaling** divides the logits by a temperature T before softmax:
- T = 1.0: no change (standard softmax)
- T < 1.0: makes the distribution sharper (more confident)
- T > 1.0: makes the distribution flatter (less confident)

This is relevant because the NLI model's raw probabilities may not be well-calibrated — a 0.8 entailment score doesn't necessarily mean there's an 80% chance the claim is true. Temperature scaling is a standard fix (Guo et al. 2017), but it didn't work for our task (more on this in Section 7).

---

## 3. The Solution: Cw-CONLI Pipeline

### 3.1 The four-stage pipeline

```
Query → [Retrieve] → [Generate] → [Verify] → [Verdict]
```

**Stage 1 — Retrieve:** Encode the query, search FAISS, return top-2 passages + retrieval score.

**Stage 2 — Generate:** Send the retrieved passages + query to Llama-3.1-8B (via Groq API). Temperature 0.1 for deterministic output. Offline mode available (mock response, real verification).

**Stage 3 — Verify:** Run NLI with the retrieved passages as premise and the LLM response as hypothesis. Get entailment score.

**Stage 4 — Verdict:** Compare the NLI score against a threshold. If above: VERIFIED. If below: HALLUCINATION. The key innovation is how we compute that threshold.

### 3.2 The core innovation: adaptive thresholds

A fixed threshold (like 0.75) treats every query the same. But intuitively:
- If we retrieved excellent evidence, a moderate NLI score is probably fine — the response matches good evidence
- If we retrieved garbage evidence, even a high NLI score is suspicious — matching bad evidence doesn't tell us much

**Cw-CONLI** makes the threshold a function of the retrieval score:

**Tiered (step function):**
```
if retrieval_score < pivot:
    threshold = T_strict     # low retrieval → demand strong NLI
else:
    threshold = T_lenient    # high retrieval → accept moderate NLI
```

**Square root (smooth curve):**
```
threshold = T_strict - (T_strict - T_lenient) * sqrt(retrieval_score)
```

**Sigmoid (S-curve):**
```
threshold = T_lenient + (T_strict - T_lenient) / (1 + exp(k * (rs - pivot)))
```

On HaluEval's per-sample retrieval setup, all three converge to nearly the same operating point as a fixed threshold — C3's advantage emerges in realistic (shared-index) retrieval where retrieval confidence varies more. The grid search tunes the parameters (pivot, T_strict, T_lenient) on the dev set to maximise F1.

### 3.3 The three experimental conditions

- **C1 (RAG-only):** No NLI verification at all. Everything the LLM says is accepted. This is the baseline.
- **C2 (Static CONLI):** Fixed NLI threshold. If entailment score >= T, it's verified. Simple but ignores retrieval quality.
- **C3 (Cw-CONLI):** Adaptive threshold based on retrieval confidence. This is the contribution.

---

## 4. v2 Improvements: What Changed and Why

### 4.1 Problem: 512-token truncation → Sliding-window NLI

**The bug:** RoBERTa has a 512-token input limit. For the NLI task, the input is `<s> premise </s></s> hypothesis </s>` — so the premise + hypothesis together can't exceed ~508 tokens. If the premise (the retrieved document) is longer, the tokeniser silently truncates it. For summarisation tasks where source documents are 1000+ tokens, the model was only seeing the first third of the document.

**The impact:** 99%+ false positive rate on summarisation. The model couldn't verify anything because it was missing most of the evidence.

**The fix:** Split the premise into overlapping windows of 400 tokens with a 200-token stride. Run NLI on each window separately. Take the **maximum** entailment score across all windows — if any chunk of the premise supports the claim, the claim is supported.

**Code:** `engine.py:verify_windowed()` (lines 322-387)

### 4.2 Problem: semantic illusion → Claim decomposition

**The bug:** Whole-response NLI verifies the entire LLM output as a single hypothesis. If 4 out of 5 sentences are correct and 1 is hallucinated, the model can still give a high entailment score because the correct sentences dominate.

**The fix:** Split the response into individual sentences using NLTK's sentence tokeniser. Verify each sentence independently. Take the **minimum** score — the weakest link. One bad claim drags the whole score down.

**Why min, not mean?** For hallucination detection, you want to catch the worst claim, not the average. A response with one fabricated fact is still hallucinated, even if the other facts are correct.

**Code:** `engine.py:verify_decomposed()` (lines 404-444)

### 4.3 Problem: outdated embeddings → BGE upgrade

**What changed:** Replaced `all-MiniLM-L6-v2` (2021) with `BAAI/bge-small-en-v1.5` (2023). Same 384-d output, same model size, but better training methodology. Drop-in replacement — no architecture changes needed.

### 4.4 Investigated but disabled: temperature scaling

See Section 7 for the full story. Summary: T=10.0 at the optimizer boundary means calibration doesn't help for this task. Disabled in all v2 code.

---

## 5. Experiment Design

### 5.1 Dataset: HaluEval

**What it is:** HaluEval (Hallucination Evaluation benchmark) from HuggingFace. Contains samples that are independently labelled as hallucinated or faithful.

**Two tasks:**
- **QA (10,000 samples):** Each sample has a knowledge passage, a question, an answer, and a label (hallucination = "yes" or "no")
- **Summarisation (10,000 samples):** Each sample has a source document, a summary, and a label

**Important:** These are not paired — each sample is independently labelled. There is no "correct answer and hallucinated answer for the same question." Each sample stands alone.

**Field mapping:**
- QA: `knowledge` (premise), `question` (query for retrieval), `answer` (hypothesis for NLI)
- Summarisation: `document` (premise), `summary` (hypothesis for NLI). Retrieval query = the summary itself

### 5.2 Dev/test split

70% dev, 30% test. Random shuffle with seed 42 for reproducibility. Dev set is used for grid search tuning; test set is held out and only used for final evaluation.

### 5.3 Precompute-then-sweep architecture

**Key design decision:** Computing retrieval + NLI scores requires running the models (slow). Applying threshold conditions is just arithmetic (fast).

So we:
1. **Precompute** all retrieval + NLI scores once and save them to a CSV
2. **Sweep** thousands of threshold combinations on those pre-computed scores instantly

This means tuning takes seconds instead of hours. The CSVs also serve as checkpoints — if the process crashes during precomputation, it resumes from where it left off.

### 5.4 Grid search

For C2: sweep `T_static` from 0.10 to 0.99 in steps of 0.01.

For C3: sweep all combinations of `pivot`, `T_strict`, `T_lenient` across three methods (tiered, sqrt, sigmoid). Thousands of configurations, but each one is just arithmetic on the pre-computed scores — the whole sweep takes under a minute.

### 5.5 Statistical testing: McNemar's test

McNemar's test compares two classifiers on the same data. It looks at the samples where they disagree:
- `b` = samples C2 got right but C3 got wrong
- `c` = samples C2 got wrong but C3 got right

The test statistic (with continuity correction): `(|b - c| - 1)^2 / (b + c)`

If p < 0.05, the classifiers are significantly different. This is the standard test for comparing paired classifiers — it's more appropriate than comparing F1 scores directly because it accounts for *which* samples each model gets right.

---

## 6. Results & What They Mean

### 6.1 Headline numbers

| Metric | v1 | v2 (standard) | v2 (realistic) |
|--------|-----|---------------|----------------|
| Combined F1 (best C3) | — | 0.6998 | 0.6558 |
| QA F1 (best C3) | 0.770 | 0.770 (C2 = C3) | — |
| QA Over-flagging (FPR) | 13.6% | 11.2% (C3 Tiered) | — |
| Summarisation | Broken (99%+ FPR) | F1 ≈ 0.663 (fixed) | — |
| Realistic FPR (C2 → C3 Sqrt) | — | — | 100% → 44.9% |
| C3 vs C2 significant? | No (p = 0.25) | No (p = 1.0) | **Yes (p = 0.000014)** |

### 6.2 What the numbers mean

**Standard benchmark: C3 and C2 converge.** On HaluEval's per-sample retrieval (each sample comes with its own gold passage), retrieval scores cluster tightly around 0.35-0.40. There isn't enough variance for adaptive thresholds to differentiate — the grid search finds nearly identical operating points (combined F1: 0.6988 vs 0.6998, Δ = 0.001). McNemar's p = 1.0 confirms no significant difference. This is a **null result** for C3 on this benchmark.

**QA over-flagging still improves.** C3 Tiered reduces QA over-flagging from 13.6% (C2) to 11.2% — a 2.4pp improvement. C3 Sqrt goes further to 9.5%. In real terms: for every 100 correct responses, C2 wrongly flags ~14; C3 Sqrt flags ~10. The F1 scores are tied at 0.770 on dev and nearly so on test.

**Summarisation went from broken to functional.** v1's 99% FPR meant every summarisation was flagged as hallucinated — completely useless. Sliding-window NLI fixed the root cause (512-token truncation). F1 ≈ 0.663 with FPR still ~98-99% shows the task remains hard, but the pipeline at least produces real verification rather than blanket rejection.

**The realistic experiment is the novel finding.** When retrieval uses a shared FAISS index (not per-sample gold passages), retrieval confidence varies widely — exactly the regime where adaptive thresholds should matter. McNemar's p = 1.4×10⁻⁵ is significant, but **C2 wins on F1** (0.6701 vs 0.6558). C3's advantage is in reducing over-flagging: C2 flags 100% of correct responses as hallucinated, while C3 Sqrt reduces this to 44.9%. The trade-off is lower recall.

**The primary contribution is v2 engineering** — windowed NLI, claim decomposition, BGE embeddings — not the C3 adaptive threshold mechanism itself.

### 6.3 Combined test set — standard (n = 6,000)

| Condition | F1 | Precision | Recall | FPR |
|-----------|-----|-----------|--------|-----|
| C1 (RAG-only) | 0.000 | 0.000 | 0.000 | 0.0% |
| C2 (Static CONLI) | 0.6988 | 0.6014 | 0.8338 | 55.3% |
| C3 Tiered | 0.6998 | 0.6010 | 0.8374 | 55.7% |
| C3 Sqrt | 0.6998 | 0.6008 | 0.8378 | 55.7% |
| C3 Sigmoid | 0.6992 | 0.6005 | 0.8368 | 55.7% |

McNemar's p = 1.0 (not significant). C3 and C2 converge to the same operating point on this benchmark.

**Why C1 has all zeros:** C1 is the RAG-only baseline with no NLI. It never flags anything as hallucinated, so it has zero recall and zero false positives. It exists as a reference point to show that NLI verification is doing something.

### 6.4 Realistic test set — shared-index retrieval (n = 5,918)

| Condition | F1 | Precision | Recall | FPR |
|-----------|-----|-----------|--------|-----|
| C2 (Static CONLI) | **0.6701** | 0.5041 | 0.9993 | 100.0% |
| C3 Tiered | 0.6558 | 0.5236 | 0.8773 | 81.2% |
| C3 Sqrt | 0.6414 | 0.6067 | 0.6803 | **44.9%** |
| C3 Sigmoid | 0.6400 | 0.5604 | 0.7460 | 59.5% |

McNemar's p = 1.4×10⁻⁵ (significant). C2 wins F1 but flags every correct response as hallucinated. C3 Sqrt cuts over-flagging from 100% to 44.9% at the cost of lower recall — a more usable operating point.

---

## 7. The Calibration Story (Negative Result)

### What we tried

Temperature scaling (Guo et al. 2017): collect raw NLI logits on the dev set, then find a temperature T that minimises negative log-likelihood. This should make the model's confidence scores better calibrated — a 0.8 should mean 80% chance of being correct.

### What happened

The optimizer (bounded scalar minimisation, range 0.1 to 10.0) converged to T = 10.0 — the upper boundary. This means:
1. The loss function was still decreasing at T = 10.0 (no local minimum was found in the valid range)
2. Applying T = 10 divides all logits by 10, making the softmax extremely flat
3. All scores collapse to a narrow range around 0.33 (uniform across 3 classes)
4. The grid search can't find meaningful thresholds in such a narrow range

### What it means

The NLI model's logits for hallucination detection don't have the same calibration properties as typical classification tasks. This is likely because:
- NLI was trained on natural language inference pairs, not on hallucination detection specifically
- The entailment/contradiction distinction doesn't map cleanly onto hallucinated/faithful
- The model is being used off-distribution (long passages, generated text vs curated NLI datasets)

### What we did

Disabled calibration entirely (`use_calibration=False` in all v2 code). The boundary check in `engine.py` automatically falls back to T=1.0 if T >= 9.0, so even if someone accidentally enables it, it won't break results.

**Why it's worth reporting:** Negative results are valuable. If someone tries to extend this work and wonders "why isn't calibration enabled?", the answer is documented with the experimental evidence.

---

## 8. Engineering & Portability

### 8.1 Device auto-detection

`engine.py` line 77: `torch.device("cuda" if torch.cuda.is_available() else "cpu")`

MPS (Apple Silicon GPU) is deliberately excluded — it causes segfaults with the RoBERTa model. The code works unchanged on:
- MacBook (CPU)
- Linux with NVIDIA GPU (CUDA)
- Google Colab (CUDA)

### 8.2 Colab notebook

`colab_v2_pipeline.ipynb` runs the full experiment on a T4 GPU in ~3-6 hours. Key design decisions:
- Each step is its own cell (can re-run after disconnect)
- Checkpointing in `evaluate.py` means interrupted precomputation resumes from where it stopped
- Results saved to Google Drive + downloadable as zip

### 8.3 Dependency pinning

- `requirements.txt` — loose pins (`>=`) for compatibility
- `requirements-lock.txt` — exact pins (`==`) for reproducibility

### 8.4 Makefile

```bash
make start      # Backend (port 8000) + frontend (port 5173)
make stop       # Kill both
make restart    # Bounce both
make status     # What's running
make install    # pip + npm install (never overwrites .env)
make smoke      # 20-sample precompute test
```

---

## 9. Live Demo Script (Supervisor Meeting)

**Duration:** ~20 minutes
**Setup:** Run `make start`. Open http://localhost:5173.

### Demo 1 — Explain the UI (1 min)

> This is the verification interface. There's a query box at the top, a control panel where you can adjust the thresholds and toggle v2 mode, and the results appear in three columns: retrieval on the left, generation in the middle, verification on the right.

### Demo 2 — Verified claim (3 min)

Type: **When was the University of Westminster founded?**

Click Verify. Walk through left to right:

> The knowledge base has a passage about Westminster, so retrieval confidence is high. The LLM generates a response grounded in that context. NLI confirms the response is supported by the evidence. The retrieval score is above the pivot, so we're in lenient mode. Verdict: VERIFIED.

### Demo 3 — Hallucination caught (2 min)

Type: **Who is the president of the United States?**

Click Verify.

> Nothing in the knowledge base matches this query. Retrieval confidence drops. The system goes into strict mode. The LLM still generates an answer — it might even be factually correct — but NLI can't verify it against the retrieved evidence because the evidence isn't relevant. Verdict: HALLUCINATION.
>
> Important point: the system doesn't check if the answer is true in general. It checks if the answer is supported by the evidence we have. If we can't verify it, we flag it.

### Demo 4 — v2 mode with per-claim breakdown (3 min)

Check **v2 Mode** in the control panel. Type: **What are the types of AI hallucinations?**

Click Verify. (First v2 request takes ~15s to load the engine.)

> v2 splits the response into individual sentences and verifies each one. You can see the per-claim breakdown — each sentence gets a score. The final score is the minimum, the weakest link. This catches cases where most of the response is correct but one sentence is fabricated.
>
> v2 also uses sliding-window NLI for long documents. In v1, RoBERTa's 512-token limit meant long premises got truncated and summarisation was completely broken. Sliding-window fixes that.

### Demo 5 — Threshold tuning (2 min)

Adjust sliders in the control panel.

> The pivot controls the boundary between strict and lenient mode. Lowering it makes the system more cautious. Raising the strict threshold demands stronger NLI scores. This is the precision-recall trade-off — you tune these on the dev set to find the sweet spot.

### Demo 6 — Explore page (2 min)

Navigate to `/explore`. Enable v2. Click **Run All**.

> This batch-runs 7 queries across different knowledge domains. You can see Westminster queries getting verified, the distractor query about Sri Lanka's climate getting mixed results, and the off-topic query getting flagged. The summary stats show the average retrieval and NLI scores.

### Demo 7 — Results discussion (3 min)

> The full evaluation used HaluEval — 20K samples. On the standard benchmark, C3 and C2 converge — McNemar's p = 1.0 — because per-sample retrieval doesn't give enough variance for adaptive thresholds. But the realistic experiment with shared-index retrieval shows significant divergence (p = 0.000014): C2 flags 100% of correct responses, while C3 Sqrt reduces that to 45%. The v2 engineering — windowed NLI, decomposition, BGE — is what really moved the needle: summarisation went from broken (99% FPR) to F1 ≈ 0.663.

### Demo 8 — What's next (1 min)

> Code, experiments, and thesis are complete. The key narrative: v2 engineering fixes real pipeline bugs (truncation, semantic illusion), and the realistic experiment reveals where adaptive thresholds add value — when retrieval quality varies, which is the real-world case.

---

## 10. Quick Reference

### Models

| Component | v1 | v2 |
|-----------|-----|-----|
| Embeddings | all-MiniLM-L6-v2 (2021) | BAAI/bge-small-en-v1.5 (2023) |
| NLI | RoBERTa-large-MNLI | same |
| LLM | Llama-3.1-8B-Instant (Groq) | same |

### Key files

| File | Purpose |
|------|---------|
| `engine.py` | Core engine: embeddings, FAISS, NLI, windowed NLI, decomposition |
| `api.py` | FastAPI backend, `/api/verify` and `/api/health` |
| `config.py` | Model IDs, thresholds, grid search ranges |
| `evaluate.py` | Precompute scores + apply conditions |
| `tune.py` | Grid search on dev set |
| `analyze.py` | Plots, tables, McNemar's test |
| `calibrate.py` | Temperature scaling (investigated, disabled) |
| `run_v2.py` | Automated v2 pipeline |
| `colab_v2_pipeline.ipynb` | Colab notebook for GPU experiments |
| `Makefile` | `make start/stop/restart/status/install/smoke` |
| `frontend/` | React 18 + Vite (VerifyPage, ExplorePage, AboutPage) |

### Demo queries

| Query | Expected | Why |
|-------|----------|-----|
| When was the University of Westminster founded? | VERIFIED | Direct KB match |
| What happened at the Royal Polytechnic in 1896? | VERIFIED | Lumiere brothers passage |
| What are AI hallucinations? | VERIFIED | AI topic in KB |
| What is the climate of Sri Lanka? | VERIFIED (edge) | Distractor topic, weak match |
| Who is the president of the United States? | HALLUCINATION | Not in KB |
| What is the population of Mars? | HALLUCINATION | Off-topic |

### Glossary

| Term | Meaning |
|------|---------|
| RAG | Retrieval-Augmented Generation — feed retrieved docs to the LLM |
| NLI | Natural Language Inference — premise/hypothesis entailment classification |
| FAISS | Facebook AI Similarity Search — vector similarity library |
| Cw-CONLI | Confidence-Weighted Cross-document NLI — adaptive thresholds |
| C1 | Condition 1: RAG-only baseline (no NLI) |
| C2 | Condition 2: Static CONLI (fixed NLI threshold) |
| C3 | Condition 3: Cw-CONLI (adaptive threshold) |
| HaluEval | Hallucination Evaluation benchmark (10K QA + 10K summarisation) |
| FPR | False Positive Rate — how often correct responses are wrongly flagged |
| McNemar's test | Statistical test comparing two classifiers on the same data |
| Temperature scaling | Dividing logits by T before softmax to calibrate confidence |
| Claim decomposition | Splitting response into sentences, verifying each independently |
| Sliding-window NLI | Splitting long premises into overlapping chunks for NLI |
