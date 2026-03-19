# AFLHR Lite: Confidence-Weighted CONLI for Hallucination Detection

**Adaptive Framework for LLM Hallucination Reduction - Lite Version**

A two-layer verification pipeline that combines Retrieval-Augmented Generation (RAG) with Natural Language Inference (NLI) to detect hallucinations in LLM outputs. The core innovation is **Confidence-Weighted CONLI (Cw-CONLI)**: the NLI verification threshold adapts dynamically based on retrieval confidence, applying stricter scrutiny when evidence quality is low and more lenient thresholds when strong supporting evidence exists.

**v2** extends the pipeline with sliding-window NLI, sentence-level claim decomposition, NLI temperature scaling, and a BGE embedding upgrade — addressing token truncation, semantic illusion, and uncalibrated NLI outputs.

## Results

| Metric | v1 | v2 |
|--------|-----|-----|
| **QA F1 (best C3)** | 0.770 | 0.753 |
| **QA Over-flagging** | 13.6% | **13.8%** (C3 Tiered) |
| **Summarisation** | Broken (99%+ FPR) | **F1 = 0.656** (fixed) |
| **C3 vs C2 significant?** | No (p = 0.25) | **Yes (p = 0.000003)** |
| **Calibration** | None | T = 10.0 (NLL -43.7%) |

**Key finding:** Cw-CONLI significantly outperforms static CONLI (McNemar's p = 3 x 10^-6). C3 Tiered reduces QA over-flagging by 6.2 percentage points (13.8% vs 20.0%). Summarisation, previously broken due to 512-token truncation, is now functional with sliding-window NLI.

## Author

- **Name:** Shaun Yogeshwaran
- **Module:** 6COSC023W - Computer Science Final Project
- **Institution:** University of Westminster / Informatics Institute of Technology (IIT)
- **Degree:** BSc (Hons) Computer Science

## Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- 24 GB RAM recommended (models loaded on CPU)
- No GPU required (all inference runs on CPU; Colab notebook provided for faster runs)

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

Open **http://localhost:3000** (or the port shown in the terminal). The frontend has three pages:

- **Verify** (`/`) — Enter a claim, adjust Cw-CONLI thresholds via the control panel, toggle **v2 Mode**, and see the full pipeline: retrieval confidence gauge, LLM generation, NLI entailment score, per-claim breakdown (v2), and animated verdict
- **Explore** (`/explore`) — Batch-run 7 pre-configured queries across different knowledge domains and compare results in a table with aggregate stats (supports v1/v2 toggle)
- **How It Works** (`/about`) — Visual walkthrough of the 4-stage pipeline, v2 improvements, threshold variant formulas, and technical stack reference

### v2 Mode

The **v2 Mode** toggle in the control panel enables:
- **Sliding-window NLI** — splits long premises into overlapping 400-token windows so summarisation documents are fully evaluated
- **Sentence-level claim decomposition** — verifies each sentence independently, takes the minimum score (weakest-link)
- **Temperature-scaled calibration** — divides NLI logits by learned temperature T before softmax
- **BGE embeddings** — upgrades to BAAI/bge-small-en-v1.5 for higher retrieval fidelity

When v2 is active, the verification column shows a per-claim score breakdown highlighting the weakest claim.

### Offline Mode

The interface works **without an API key** (uses mock LLM responses; RAG and NLI verification still function).

## Running Experiments

The evaluation pipeline uses HaluEval (10K QA + 10K Summarization samples) to benchmark three conditions:

- **C1 (RAG-only):** Baseline with no NLI verification
- **C2 (Static CONLI):** Fixed NLI threshold
- **C3 (Cw-CONLI):** Dynamic threshold weighted by retrieval confidence (tiered, sqrt, sigmoid variants)

### v1 Pipeline (Baseline)

```bash
python dataset.py                                    # verify dataset loading
python evaluate.py --precompute --split dev           # pre-compute scores
python evaluate.py --precompute --split test
python tune.py --split dev                            # grid search tuning
python evaluate.py --condition C3 --split test        # evaluate
python analyze.py --split test                        # generate figures
```

### v2 Pipeline (Improved)

v2 adds four improvements over the baseline:

| Improvement | Problem Addressed | Approach |
|---|---|---|
| Sliding-window NLI | RoBERTa 512-token limit truncates long premises | Split premise into overlapping windows, take max entailment |
| Claim decomposition | Whole-response NLI washes out single altered facts | Split hypothesis into sentences, take min score (weakest-link) |
| Temperature scaling | Raw softmax outputs are uncalibrated (T=10.0 found) | Fit temperature T on dev logits (Guo et al. 2017) |
| Embedding upgrade | all-MiniLM-L6-v2 is outdated (2021, 384-dim) | BAAI/bge-small-en-v1.5 (same dim, better quality) |

**Automated pipeline** (recommended):

```bash
python run_v2.py                   # full run (~4h on GPU, ~24h on CPU)
python run_v2.py --limit 50        # smoke test (~minutes)
python run_v2.py --skip-calibrate  # reuse existing calibration
```

**Google Colab** (recommended for speed): Open `run_v2_colab.ipynb` in Colab with a T4 GPU runtime for ~4.5 hour total runtime.

**Manual step-by-step:**

```bash
python calibrate.py --split dev                          # calibrate NLI temperature
python evaluate.py --precompute --split dev --version v2  # pre-compute v2 scores
python evaluate.py --precompute --split test --version v2
python tune.py --split dev --version v2                   # tune with v2 grid ranges
python evaluate.py --condition C3 --split test --version v2 --params '{"method":"tiered","pivot":0.8,"T_strict":0.36,"T_lenient":0.355}'
python analyze.py --split test --version v2               # generate figures
```

### Ablation Study

v2 scores include both decomposed (`nli_score`) and whole-response (`nli_score_whole`) NLI scores, enabling ablation via the `--nli-key` flag:

```bash
python tune.py --split dev --version v2 --nli-key nli_score_whole
python evaluate.py --condition C3 --split test --version v2 --nli-key nli_score_whole
```

## Project Structure

```
Shaun_FYP/
├── api.py              # FastAPI backend (v1 + v2 engine support)
├── engine.py           # Core AFLHREngine class (embedding, retrieval, NLI, verdict)
├── config.py           # Configuration, model IDs, thresholds, grid search ranges (v1+v2)
├── dataset.py          # HaluEval dataset loader with dev/test splitting
├── evaluate.py         # Evaluation harness (precompute scores, apply conditions)
├── tune.py             # Grid search hyperparameter tuning (version-aware)
├── analyze.py          # Results analysis, plots, McNemar's test
├── calibrate.py        # NLI temperature scaling calibration
├── run_v2.py           # Automated v2 experiment pipeline
├── run_v2_colab.ipynb  # Colab notebook for GPU-accelerated experiments
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── frontend/           # React + Vite frontend
│   ├── src/
│   │   ├── components/ # CircularGauge, VerdictStamp, ThresholdPanel, ClaimBreakdown
│   │   ├── pages/      # VerifyPage, ExplorePage, AboutPage
│   │   ├── styles/     # Design system (theme.js, global.css)
│   │   ├── App.jsx     # Root component with routing
│   │   └── main.jsx    # Entry point
│   ├── package.json    # Node dependencies (React, Framer Motion, Recharts)
│   └── vite.config.js  # Vite config (dev proxy to FastAPI)
├── results/            # Experiment outputs
│   ├── *_v2.json/csv   # v2 experiment results
│   └── figures/        # Generated plots and visualisations
└── data/               # Cached datasets (generated at runtime)
```

## Key Models

| Component | Model (v1) | Model (v2) | Purpose |
|-----------|------------|------------|---------|
| Embeddings | `all-MiniLM-L6-v2` | `BAAI/bge-small-en-v1.5` | Semantic similarity for retrieval |
| NLI Verifier | `RoBERTa-large-MNLI` | `RoBERTa-large-MNLI` + temp. scaling (T=10) | Entailment scoring for verification |
| LLM Generator | `Llama-3.1-8B-Instant` (via Groq) | same | Response generation |

## v2 Detailed Results

### Combined Test Set (n = 6,000)

| Condition | F1 | Precision | Recall | Over-flagging (FPR) |
|-----------|-----|-----------|--------|---------------------|
| C1 (RAG-only) | 0.000 | 0.000 | 0.000 | 0.0% |
| C2 (Static CONLI) | 0.692 | 0.593 | 0.833 | 57.3% |
| C3 Tiered | 0.693 | 0.606 | 0.810 | **52.7%** |
| C3 Sqrt | **0.694** | 0.605 | 0.813 | 53.1% |
| C3 Sigmoid | 0.694 | 0.605 | 0.813 | 53.0% |

### QA Test Set (n = 2,959)

| Condition | F1 | Precision | Recall | FPR |
|-----------|-----|-----------|--------|-----|
| C2 (Static) | 0.749 | 0.785 | 0.717 | 20.0% |
| C3 Tiered | 0.752 | 0.834 | 0.684 | **13.8%** |
| C3 Sqrt | **0.753** | 0.831 | 0.689 | 14.3% |

### Summarisation Test Set (n = 3,041)

| Condition | F1 | FPR | Status |
|-----------|-----|-----|--------|
| v1 (all conditions) | ~0 | 99%+ | Broken (token truncation) |
| v2 C3 Sqrt | **0.656** | 90.3% | Functional (windowed NLI) |

### Statistical Significance

| | v1 | v2 |
|---|---|---|
| McNemar statistic | — | 22.124 |
| p-value | 0.25 | **0.000003** |
| Significant? | No | **Yes** |

## License

This project was developed as part of an undergraduate final year project for academic purposes.
