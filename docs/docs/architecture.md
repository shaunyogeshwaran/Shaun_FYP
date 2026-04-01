---
sidebar_position: 2
title: Architecture
---

# System Architecture

AFLHR Lite uses a two-layer pipeline: **RAG retrieval** followed by **NLI verification**.

## Pipeline Stages

### Stage 1 — Retrieve Evidence

The user query is embedded using a sentence-transformer model and compared against a FAISS index of pre-embedded knowledge passages. The top-k most similar passages are returned with a **retrieval score** (cosine similarity), which measures how relevant the evidence is.

- **v1:** `all-MiniLM-L6-v2` (384 dimensions)
- **v2:** `BAAI/bge-small-en-v1.5` (384 dimensions, better quality)

### Stage 2 — Generate Response

The retrieved passages and original query are sent to an LLM (Llama-3.1-8B-Instant via Groq API) to generate a natural language response. In **offline mode**, a mock response is used instead.

### Stage 3 — Verify via NLI

The generated response (hypothesis) is checked against the retrieved passages (premise) using RoBERTa-large-MNLI. The model outputs an **entailment probability** — how strongly the evidence supports the response.

**v2 improvements:**
- **Sliding-window NLI** — premises longer than 512 tokens are split into overlapping 400-token windows with 200-token stride. The maximum entailment score across windows is used.
- **Claim decomposition** — the response is split into individual sentences. Each claim is verified independently, and the **minimum** score (weakest link) becomes the final NLI score.

### Stage 4 — Adaptive Verdict

The NLI score is compared against a threshold `T(rs)` that depends on retrieval confidence. This is the **Cw-CONLI** mechanism:

- If `nli_score >= T(rs)` → **VERIFIED**
- If `nli_score < T(rs)` → **HALLUCINATION**

When retrieval confidence is low, the threshold is strict (harder to pass). When retrieval confidence is high, the threshold is lenient (evidence is trusted).

## Models

| Component | v1 | v2 | Purpose |
|-----------|----|----|---------|
| Embeddings | `all-MiniLM-L6-v2` | `BAAI/bge-small-en-v1.5` | Semantic similarity for retrieval |
| NLI Verifier | `RoBERTa-large-MNLI` | same | Entailment scoring |
| LLM Generator | `Llama-3.1-8B-Instant` (Groq) | same | Response generation |

## Project Structure

```
Shaun_FYP/
├── api.py              # FastAPI backend (v1 + v2 engine support)
├── engine.py           # Core AFLHREngine class
├── config.py           # Configuration, model IDs, thresholds
├── dataset.py          # HaluEval dataset loader
├── evaluate.py         # Evaluation harness (precompute + conditions)
├── tune.py             # Grid search hyperparameter tuning
├── analyze.py          # Results analysis, plots, McNemar's test
├── calibrate.py        # NLI temperature scaling (investigated, disabled)
├── run_v2.py           # Automated v2 experiment pipeline
├── frontend/           # React + Vite frontend
│   ├── src/components/ # CircularGauge, VerdictStamp, ThresholdPanel, ...
│   ├── src/pages/      # VerifyPage, ExplorePage, AboutPage
│   └── src/styles/     # Design system (theme.js, global.css)
├── docs/               # Docusaurus documentation (this site)
└── results/            # Experiment outputs (CSVs, JSONs, figures)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| ML/NLP | sentence-transformers, FAISS, HuggingFace Transformers |
| LLM | Llama-3.1-8B-Instant via Groq API |
| Frontend | React 18, Vite 5, React Router 7, Framer Motion, Recharts |
| Documentation | Docusaurus |
| Build | GNU Make, pip, npm |
