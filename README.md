# AFLHR Lite: Confidence-Weighted CONLI for Hallucination Detection

**Adaptive Framework for LLM Hallucination Reduction - Lite Version**

A two-layer verification pipeline that combines Retrieval-Augmented Generation (RAG) with Natural Language Inference (NLI) to detect hallucinations in LLM outputs. The core innovation is **Confidence-Weighted CONLI (Cw-CONLI)**: the NLI verification threshold adapts dynamically based on retrieval confidence, applying stricter scrutiny when evidence quality is low and more lenient thresholds when strong supporting evidence exists.

**v2** extends the pipeline with sliding-window NLI, sentence-level claim decomposition, and a BGE embedding upgrade — addressing token truncation and semantic illusion. (Temperature scaling was investigated but disabled: T=10.0 at optimizer boundary means NLI logits are not calibratable for this task.)

## Live Demo

| Resource | URL |
|---|---|
| **Interactive demo** | https://shaun-fyp-1yzu.vercel.app |
| **Backend API** | https://mrrobotttttt-shaun-fyp.hf.space |
| **API health** | https://mrrobotttttt-shaun-fyp.hf.space/api/health |
| **Swagger docs** | https://mrrobotttttt-shaun-fyp.hf.space/docs |
| **Documentation** | https://shaunyogeshwaran.github.io/Shaun_FYP/docs/overview |

The React frontend is hosted on Vercel; the FastAPI backend runs on a HuggingFace Space (Docker, `cpu-basic`). Both v1 (MiniLM baseline) and v2 (BGE + windowed NLI + decomposition) are loaded. First request after inactivity may take ~30s while the Space wakes and RoBERTa-large-MNLI reloads into memory.

## Results

| Metric | v2 (standard) | v2 (realistic) |
|--------|---------------|----------------|
| **Combined F1 (best C3)** | 0.6998 | 0.6558 |
| **QA F1** | 0.770 (C2 = C3) | — |
| **QA Over-flagging** | **11.2%** (C3 Tiered) | — |
| **Summarisation F1** | **≈ 0.663** (windowed NLI fixed 99% FPR) | — |
| **Realistic FPR (C2 → C3 Sqrt)** | — | **100% → 44.9%** |
| **C3 vs C2 significant?** | No (p = 1.0) | **Yes (p = 0.000014)** |
| **Calibration** | T = 10.0 at boundary (disabled) | — |

**Key finding:** On HaluEval's standard per-sample retrieval, C3 and C2 converge to the same operating point (McNemar's p = 1.0) — retrieval scores cluster too tightly for adaptive thresholds to differentiate. Under **realistic shared-index retrieval**, the difference is significant (p = 1.4×10⁻⁵): C2 flags 100% of correct responses while C3 Sqrt reduces over-flagging to 44.9%. The primary contribution is **v2 engineering** — sliding-window NLI fixes summarisation (99% FPR → functional), claim decomposition catches partial hallucinations, and BGE embeddings improve retrieval fidelity.

## Author

- **Name:** Shaun Yogeshwaran
- **Module:** 6COSC023W - Computer Science Final Project
- **Institution:** University of Westminster / Informatics Institute of Technology (IIT)
- **Degree:** BSc (Hons) Computer Science

## Prerequisites

- Python 3.9+ and make (Node.js 20 is installed automatically by `make install`)
- 24 GB RAM recommended
- GPU auto-detected (CUDA used when available; falls back to CPU on Mac/other). Colab notebook provided for faster GPU runs

## Quick Start (any machine)

> **Just want to try it?** The [live demo](https://shaun-fyp-1yzu.vercel.app) runs the full pipeline in your browser — no setup required. The steps below are for local development or reproducing the experiments.

```bash
git clone https://github.com/shaunyogeshwaran/Shaun_FYP.git
cd Shaun_FYP
make install        # creates venv, installs pip + npm deps, downloads NLTK data, creates .env
# Edit .env and add your GROQ_API_KEY (free at https://console.groq.com)
make start          # starts backend (:8000) + frontend (:5173)
```

Open **http://localhost:5173** — that's it.

### Requirements

| Requirement | Details |
|---|---|
| **Python** | 3.9+ with pip (only prerequisite; tested on 3.9–3.13) |
| **Node.js** | 20+ (installed automatically by `make install` via nodeenv) |
| **RAM** | 24 GB recommended (ML models load into memory) |
| **Disk** | ~3 GB (models auto-download from HuggingFace on first run) |
| **GPU** | Optional — CUDA auto-detected, falls back to CPU. Colab notebook provided for faster GPU runs |
| **Groq API key** | Optional — offline mode works without it (mock LLM responses; RAG + NLI verification still function) |

### How it works

`make install` creates a Python virtual environment (`venv/`), installs Node.js 20 into it via `nodeenv`, then installs all pip and npm dependencies. Everything lives inside `venv/` — no global installs, no PATH issues, no permission errors. All subsequent `make` commands use the venv's Python, Node, and npm automatically.

### Status indicator

The header shows one of three states:

| Indicator | Meaning |
|---|---|
| 🟢 **Engine Ready** | Backend loaded, Groq key valid — full pipeline active |
| 🟡 **Offline Only** | Backend loaded, no Groq key — RAG + NLI work, LLM step uses a mock response |
| 🔴 **Connecting** | Backend not reachable |

A `gsk_`-prefixed key in `.env` is required for online mode. The placeholder value (`your_groq_api_key_here`) is treated as unset.

### Troubleshooting

| Problem | Fix |
|---|---|
| `make install` fails on pip | Ensure Python 3.9+ is on your PATH: `python3 --version` |
| Backend won't start | Check logs: `tail .run/backend.log` |
| Frontend won't start | Check logs: `tail .run/frontend.log` |
| Port 8000/5173 in use | `make stop` first, or kill the process on that port |
| Models downloading slowly | First run downloads ~3 GB from HuggingFace. Subsequent runs use cache |
| v2 mode fails (NLTK error) | Run `make install` — downloads `punkt_tab` with correct SSL certs |
| SSL certificate errors on macOS | Run `make install` — uses certifi bundle automatically |
| npm EACCES permission denied | Run `sudo chown -R $(whoami) ~/.npm` then retry `make install` |
| MPS/Apple GPU segfault | Expected — the system auto-disables MPS and uses CPU |

## Installation (step-by-step)

If you prefer manual setup over `make install`:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shaunyogeshwaran/Shaun_FYP.git
   cd Shaun_FYP
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or: venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   cd docs && npm install && cd ..
   ```

4. **Set up environment variables:**
   ```bash
   cp -n .env.example .env   # -n = skip if .env already exists
   # Edit .env and add your Groq API key (free at https://console.groq.com)
   ```
   Without a Groq API key the demo still works in offline mode (mock LLM responses; RAG + NLI verification still function).

## Running the Demo

```bash
make start     # starts backend (port 8000) + frontend (port 5173)
make stop      # stop all servers
make restart   # bounce all servers
make status    # check what's running
```

Open **http://localhost:5173**. The frontend has three pages:

- **Verify** (`/`) — Enter a claim, adjust Cw-CONLI thresholds via the control panel, toggle **v2 Mode**, and see the full pipeline: retrieval confidence gauge, LLM generation, NLI entailment score, per-claim breakdown (v2), and animated verdict
- **Explore** (`/explore`) — Batch-run 7 pre-configured queries across different knowledge domains and compare results in a table with aggregate stats (supports v1/v2 toggle)
- **How It Works** (`/about`) — Visual walkthrough of the 4-stage pipeline, v2 improvements, threshold variant formulas, and technical stack reference

### v2 Mode

The **v2 Mode** toggle in the control panel enables:
- **Sliding-window NLI** — splits long premises into overlapping 400-token windows so summarisation documents are fully evaluated
- **Sentence-level claim decomposition** — verifies each sentence independently, takes the minimum score (weakest-link)
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
| Temperature scaling | Raw softmax outputs are uncalibrated | Investigated (Guo et al. 2017); T=10.0 at boundary — disabled, NLI logits not calibratable for this task |
| Embedding upgrade | all-MiniLM-L6-v2 is outdated (2021, 384-dim) | BAAI/bge-small-en-v1.5 (same dim, better quality) |

**Automated pipeline** (recommended):

```bash
python run_v2.py                   # full run (~4h on GPU, ~24h on CPU)
python run_v2.py --limit 50        # smoke test (~minutes)
python run_v2.py --calibrate       # include calibration step (off by default)
```

**Google Colab** (recommended for speed): Open `colab_v2_pipeline.ipynb` in Colab with a T4 GPU runtime for ~3-6 hour total runtime.

**Manual step-by-step:**

```bash
python calibrate.py --split dev                          # calibrate NLI temperature
python evaluate.py --precompute --split dev --version v2  # pre-compute v2 scores
python evaluate.py --precompute --split test --version v2
python tune.py --split dev --version v2                   # tune with v2 grid ranges
python evaluate.py --condition C3 --split test --version v2
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
├── colab_v2_pipeline.ipynb  # Colab notebook for GPU-accelerated experiments
├── requirements.txt        # Python dependencies (loose pins)
├── requirements-lock.txt   # Pinned dependencies for exact reproducibility
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
| NLI Verifier | `RoBERTa-large-MNLI` | `RoBERTa-large-MNLI` | Entailment scoring for verification |
| LLM Generator | `Llama-3.1-8B-Instant` (via Groq) | same | Response generation |

## v2 Detailed Results

### Combined Test Set — Standard (n = 6,000)

| Condition | F1 | Precision | Recall | Over-flagging (FPR) |
|-----------|-----|-----------|--------|---------------------|
| C1 (RAG-only) | 0.000 | 0.000 | 0.000 | 0.0% |
| C2 (Static CONLI) | 0.6988 | 0.6014 | 0.8338 | 55.3% |
| C3 Tiered | **0.6998** | 0.6010 | 0.8374 | 55.7% |
| C3 Sqrt | 0.6998 | 0.6008 | 0.8378 | 55.7% |
| C3 Sigmoid | 0.6992 | 0.6005 | 0.8368 | 55.7% |

### QA Test Set (n = 2,959)

| Condition | F1 | Precision | Recall | FPR |
|-----------|-----|-----------|--------|-----|
| C2 (Static) | **0.7702** | 0.8418 | 0.7098 | 13.6% |
| C3 Tiered | 0.7679 | 0.8629 | 0.6917 | **11.2%** |
| C3 Sqrt | 0.7618 | 0.8776 | 0.6729 | **9.5%** |
| C3 Sigmoid | 0.7687 | 0.8221 | 0.7218 | 15.9% |

### Summarisation Test Set (n = 3,041)

| Condition | F1 | FPR | Status |
|-----------|-----|-----|--------|
| v1 (all conditions) | ~0 | 99%+ | Broken (token truncation) |
| v2 C2 | 0.6626 | 99.5% | Functional (windowed NLI) |
| v2 C3 Sqrt | **0.6634** | 98.4% | Functional (windowed NLI) |

### Realistic Test Set — Shared-Index Retrieval (n = 5,918)

| Condition | F1 | Precision | Recall | FPR |
|-----------|-----|-----------|--------|-----|
| C2 (Static) | **0.6701** | 0.5041 | 0.9993 | 100.0% |
| C3 Tiered | 0.6558 | 0.5236 | 0.8773 | 81.2% |
| C3 Sqrt | 0.6414 | 0.6067 | 0.6803 | **44.9%** |
| C3 Sigmoid | 0.6400 | 0.5604 | 0.7460 | 59.5% |

### Statistical Significance (McNemar's Test)

| Split | Statistic | p-value | Significant? |
|-------|-----------|---------|-------------|
| Combined (standard) | 0.000 | 1.0 | No |
| QA | 0.544 | 0.461 | No |
| Summarisation | 0.056 | 0.814 | No |
| **Realistic** | **18.884** | **0.000014** | **Yes** |

## License

This project was developed as part of an undergraduate final year project for academic purposes.
