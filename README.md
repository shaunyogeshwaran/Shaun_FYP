# AFLHR Lite: Confidence-Weighted CONLI for Hallucination Detection

**Adaptive Framework for LLM Hallucination Reduction - Lite Version**

A two-layer verification pipeline that combines Retrieval-Augmented Generation (RAG) with Natural Language Inference (NLI) to detect hallucinations in LLM outputs. The core innovation is **Confidence-Weighted CONLI (Cw-CONLI)**: the NLI verification threshold adapts dynamically based on retrieval confidence, applying stricter scrutiny when evidence quality is low and more lenient thresholds when strong supporting evidence exists.

**v2** extends the pipeline with sliding-window NLI, sentence-level claim decomposition, NLI temperature scaling, and an optional embedding model upgrade — addressing known limitations around token truncation, semantic illusion, and uncalibrated NLI outputs.

## Author

- **Name:** Shaun Yogeshwaran
- **Module:** 6COSC023W - Computer Science Final Project
- **Institution:** University of Westminster / Informatics Institute of Technology (IIT)
- **Degree:** BSc (Hons) Computer Science

## Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- 24 GB RAM recommended (models loaded on CPU)
- No GPU required (all inference runs on CPU)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Shaun_FYP
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Groq API key (free at https://console.groq.com)
   ```
   Without a Groq API key the demo still works in offline mode (mock LLM responses; RAG + NLI verification still function).

## Running the Demo

```bash
# Terminal 1 — start the FastAPI backend
python api.py

# Terminal 2 — start the React frontend
cd frontend
npm run dev
```

Open **http://localhost:3001** (or the port shown in the terminal). The frontend has three pages:

- **Verify** (`/`) — Enter a claim, adjust Cw-CONLI thresholds via the control panel, toggle **v2 Mode**, and see the full pipeline: retrieval confidence gauge, LLM generation, NLI entailment score, per-claim breakdown (v2), and animated verdict
- **Explore** (`/explore`) — Batch-run 7 pre-configured queries across different knowledge domains and compare results in a table with aggregate stats (supports v1/v2 toggle)
- **How It Works** (`/about`) — Visual walkthrough of the 4-stage pipeline, v2 improvements, threshold variant formulas, and technical stack reference

### v2 Mode

The **v2 Mode** toggle in the control panel enables:
- **Sliding-window NLI** — splits long premises into overlapping 400-token windows so summarisation documents are fully evaluated
- **Sentence-level claim decomposition** — verifies each sentence independently, takes the minimum score (weakest-link)
- **Temperature-scaled calibration** — divides NLI logits by a learned temperature before softmax
- **BGE embeddings** — upgrades to BAAI/bge-small-en-v1.5 for higher retrieval fidelity

When v2 is active, the verification column shows a per-claim score breakdown highlighting the weakest claim.

## Running Experiments

The evaluation pipeline uses HaluEval (10K QA + 10K Summarization samples) to benchmark three conditions:

- **C1 (RAG-only):** Baseline with no NLI verification
- **C2 (Static CONLI):** Fixed NLI threshold
- **C3 (Cw-CONLI):** Dynamic threshold weighted by retrieval confidence (tiered, sqrt, sigmoid variants)

### v1 Pipeline (Baseline)

```bash
# Step 1: Verify dataset loading
python dataset.py

# Step 2: Pre-compute retrieval + NLI scores (slow - model inference)
python evaluate.py --precompute --split dev
python evaluate.py --precompute --split test

# Step 3: Grid search hyperparameter tuning on dev set
python tune.py --split dev

# Step 4: Evaluate all conditions on test set
python evaluate.py --condition C1 --split test
python evaluate.py --condition C2 --split test
python evaluate.py --condition C3 --split test

# Step 5: Generate figures, comparison tables, and statistical tests
python analyze.py --split test
```

### v2 Pipeline (Improved)

v2 adds four improvements over the baseline:

| Improvement | Problem Addressed | Approach |
|---|---|---|
| Sliding-window NLI | RoBERTa 512-token limit truncates long premises | Split premise into overlapping windows, take max entailment |
| Claim decomposition | Whole-response NLI washes out single altered facts | Split hypothesis into sentences, take min score (weakest-link) |
| Temperature scaling | Raw softmax outputs are uncalibrated | Fit temperature T on dev logits (Guo et al. 2017) |
| Embedding upgrade | all-MiniLM-L6-v2 is outdated (2021, 384-dim) | Optional swap to BAAI/bge-small-en-v1.5 (same dim, better quality) |

**Automated pipeline** (recommended):

```bash
python run_v2.py                   # full run (leave overnight)
python run_v2.py --limit 50        # smoke test (~minutes)
python run_v2.py --realistic       # includes shared-index retrieval experiment
python run_v2.py --skip-calibrate  # reuse existing calibration
python run_v2.py --skip-precompute # reuse existing precomputed scores
```

**Manual step-by-step:**

```bash
# Step 1: Calibrate NLI temperature on dev set
python calibrate.py --split dev

# Step 2: Pre-compute v2 scores (decomposition + windowed NLI + calibration + BGE)
python evaluate.py --precompute --split dev --version v2
python evaluate.py --precompute --split test --version v2

# Step 3: Tune thresholds on dev
python tune.py --split dev --version v2

# Step 4: Evaluate on test
python evaluate.py --condition C1 --split test --version v2
python evaluate.py --condition C2 --split test --version v2
python evaluate.py --condition C3 --split test --version v2

# Step 5: Generate analysis (includes v2-specific plots)
python analyze.py --split test --version v2
```

### Ablation Study

v2 scores include both decomposed (`nli_score`) and whole-response (`nli_score_whole`) NLI scores, enabling ablation via the `--nli-key` flag:

```bash
# Tune/evaluate using whole-response NLI on v2 data (isolates calibration + embedding effect)
python tune.py --split dev --version v2 --nli-key nli_score_whole
python evaluate.py --condition C3 --split test --version v2 --nli-key nli_score_whole
```

### Realistic Retrieval Experiment (QA only)

```bash
python evaluate.py --precompute --split dev --realistic
python evaluate.py --precompute --split test --realistic
python tune.py --split dev --realistic
python analyze.py --split test --realistic
```

## Project Structure

```
Shaun_FYP/
├── api.py              # FastAPI backend (v1 + v2 engine support)
├── engine.py           # Core AFLHREngine class (embedding, retrieval, NLI, verdict)
├── config.py           # Configuration, model IDs, thresholds, knowledge base
├── dataset.py          # HaluEval dataset loader with dev/test splitting
├── evaluate.py         # Evaluation harness (precompute scores, apply conditions)
├── tune.py             # Grid search hyperparameter tuning
├── analyze.py          # Results analysis, plots, McNemar's test
├── calibrate.py        # NLI temperature scaling calibration (v2)
├── run_v2.py           # Automated v2 experiment pipeline
├── test_components.py  # Component smoke tests
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
├── frontend/           # React + Vite frontend
│   ├── src/
│   │   ├── components/ # CircularGauge, VerdictStamp, ThresholdPanel, ClaimBreakdown, etc.
│   │   ├── pages/      # VerifyPage, ExplorePage, AboutPage
│   │   ├── styles/     # Design system (theme.js, global.css)
│   │   ├── App.jsx     # Root component with routing
│   │   └── main.jsx    # Entry point
│   ├── package.json    # Node dependencies (React, Framer Motion, Recharts)
│   └── vite.config.js  # Vite config (dev proxy to FastAPI)
├── data/               # Cached datasets (generated at runtime)
└── results/            # Experiment outputs (generated at runtime)
    └── figures/        # Generated plots and visualisations
```

## Key Models

| Component | Model (v1) | Model (v2) | Purpose |
|-----------|------------|------------|---------|
| Embeddings | `all-MiniLM-L6-v2` | `BAAI/bge-small-en-v1.5` | Semantic similarity for retrieval |
| NLI Verifier | `RoBERTa-large-MNLI` | `RoBERTa-large-MNLI` + temp. scaling | Entailment scoring for verification |
| LLM Generator | `Llama-3.1-8B-Instant` (via Groq) | same | Response generation |

## License

This project was developed as part of an undergraduate final year project for academic purposes.
