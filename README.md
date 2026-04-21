# AFLHR Lite: Confidence-Weighted CONLI for Hallucination Detection

**Adaptive Framework for LLM Hallucination Reduction - Lite Version**

A two-layer verification pipeline that combines Retrieval-Augmented Generation (RAG) with Natural Language Inference (NLI) to detect hallucinations in LLM outputs. The core innovation is **Confidence-Weighted CONLI (Cw-CONLI)**: the NLI verification threshold adapts dynamically based on retrieval confidence, applying stricter scrutiny when evidence quality is low and more lenient thresholds when strong supporting evidence exists.

**v2** extends the pipeline with sliding-window NLI, sentence-level claim decomposition, and a BGE embedding upgrade — addressing token truncation and semantic illusion. Temperature scaling was investigated but disabled: T=10.0 at optimiser boundary means NLI logits are not calibratable for this task.

## Live Demo

| Resource | URL |
|---|---|
| Interactive demo | https://shaun-fyp-xi.vercel.app |
| Backend API | https://mrrobotttttt-shaun-fyp.hf.space |
| API health | https://mrrobotttttt-shaun-fyp.hf.space/api/health |
| Swagger docs | https://mrrobotttttt-shaun-fyp.hf.space/docs |
| Documentation | https://shaunyogeshwaran.github.io/Shaun_FYP/docs/overview |

The React frontend is hosted on Vercel. The FastAPI backend runs on a HuggingFace Space (Docker, `cpu-basic`) with both v1 (MiniLM baseline) and v2 (BGE, windowed NLI, decomposition) loaded. First request after inactivity takes ~30s while the Space wakes and RoBERTa-large-MNLI reloads.

## For Examiners

Three paths to verify the work, ordered by speed:

| Path | Time | What it demonstrates |
|---|---|---|
| 1. Open the [live demo](https://shaun-fyp-xi.vercel.app) | 30 seconds | End-to-end pipeline running in production |
| 2. Run the test suite locally | ~5 minutes | Unit, integration, and API tests pass |
| 3. Full local install and run | 10–15 minutes | Every code path exercised on your machine |

Reproducibility check:

```bash
# If you received this as a submission zip:
unzip Shaun_FYP-main.zip
cd Shaun_FYP-main

# Or clone from GitHub:
# git clone https://github.com/shaunyogeshwaran/Shaun_FYP.git
# cd Shaun_FYP

make install
make test
make start
```

The test suite runs in offline mode and does not require a `GROQ_API_KEY`. All experiments use `seed=42` and a 70/30 dev/test split.

## Results

| Metric | v2 (standard) | v2 (realistic) |
|--------|---------------|----------------|
| Combined F1 (best C3) | 0.6998 | 0.6558 |
| QA F1 | 0.770 (C2 = C3) | — |
| QA Over-flagging | **11.2%** (C3 Tiered) | — |
| Summarisation F1 | **≈ 0.663** (windowed NLI fixed 99% FPR) | — |
| Realistic FPR (C2 → C3 Sqrt) | — | **100% → 44.9%** |
| C3 vs C2 significant? | No (p = 1.0) | **Yes (p = 0.000014)** |
| Calibration | T = 10.0 at boundary (disabled) | — |

**Key finding:** On HaluEval's standard per-sample retrieval, C3 and C2 converge to the same operating point (McNemar's p = 1.0). Retrieval scores cluster too tightly for adaptive thresholds to differentiate. Under realistic shared-index retrieval, the difference is significant (p = 1.4×10⁻⁵): C2 flags 100% of correct responses while C3 Sqrt reduces over-flagging to 44.9%. The primary contribution is v2 engineering — sliding-window NLI fixes summarisation (99% FPR to functional), claim decomposition catches partial hallucinations, and BGE embeddings improve retrieval fidelity.

## Author

- **Name:** Shaun Yogeshwaran
- **Module:** 6COSC023W - Computer Science Final Project
- **Institution:** University of Westminster / Informatics Institute of Technology (IIT)
- **Degree:** BSc (Hons) Computer Science

## System Requirements

### Minimum

| Requirement | Details |
|---|---|
| Python | 3.9+ with pip. Tested on 3.9–3.13; 3.10 or 3.11 recommended |
| Node.js | 20+. Installed automatically by `make install` via nodeenv — do not install globally |
| RAM | 8 GB minimum; 16+ GB recommended; 24 GB required for full HaluEval 10K evaluation |
| Disk | 3 GB free for model downloads |
| Network | Required on first run for model downloads (~1.4 GB RoBERTa plus smaller embedding models) |

### Optional

| Requirement | Details |
|---|---|
| GPU | CUDA-capable GPU gives ~10× faster experiments. CPU is sufficient for the demo; a Colab notebook is provided for GPU runs |
| Groq API key | Free at [console.groq.com](https://console.groq.com). Enables online LLM generation. Without it, offline mode uses mock responses while RAG and NLI remain functional |

### Tested Platforms

| OS | Status | Notes |
|---|---|---|
| macOS 13+ (Apple Silicon M1–M4) | Supported (primary target) | MPS auto-disabled; CPU fallback is intentional (see [Known Limitations](#known-limitations-and-expected-behaviour)) |
| macOS 12+ (Intel) | Supported | CPU-only; identical performance profile |
| Ubuntu 20.04 / 22.04 (x86_64) | Supported via HF Spaces Docker | Production backend runs on `python:3.10-slim` |
| Windows 10/11 | WSL2 required | Native Windows paths are not tested. Install WSL2 (`wsl --install`), then follow Linux steps |
| Other Linux (Debian, Fedora, Arch) | Untested but expected to work | Requires Python 3.9+, pip, make, and a C compiler |

## Quick Start

```bash
# If you received this as a zip, extract it first:
unzip Shaun_FYP-main.zip
cd Shaun_FYP-main

# Or clone from GitHub:
# git clone https://github.com/shaunyogeshwaran/Shaun_FYP.git
# cd Shaun_FYP

make install        # creates venv, installs pip and npm deps, downloads NLTK data, creates .env
# Edit .env and add GROQ_API_KEY (optional)
make start          # starts backend (:8000) and frontend (:5173)
```

Open http://localhost:5173.

### Verify installation

After `make install`, run the test suite:

```bash
make test
```

Or load the engine manually:

```bash
source venv/bin/activate                                              # macOS/Linux
# venv\Scripts\activate                                               # Windows
python -c "from engine import AFLHREngine; AFLHREngine(); print('OK')"
```

First run takes ~60 seconds to download ~1.4 GB of model weights. Subsequent runs use the HuggingFace cache at `~/.cache/huggingface/`.

### How `make install` works

`make install` creates a Python virtual environment (`venv/`), installs Node.js 20 into it via `nodeenv`, then installs all pip and npm dependencies. Everything lives inside `venv/` — no global installs, no PATH issues, no permission errors. Subsequent `make` commands use the venv's Python, Node, and npm automatically.

### Status indicator

The frontend header shows one of three states:

| Indicator | Meaning |
|---|---|
| Engine Ready | Backend loaded, Groq key valid. Full pipeline active |
| Offline Only | Backend loaded, no Groq key. RAG and NLI work; LLM step uses a mock response |
| Connecting | Backend not reachable |

A `gsk_`-prefixed key in `.env` is required for online mode. The placeholder value `your_groq_api_key_here` is treated as unset.

## Manual Installation

Alternative to `make install`:

1. Obtain the source:
   ```bash
   # From the submission zip:
   unzip Shaun_FYP-main.zip
   cd Shaun_FYP-main

   # Or from GitHub:
   # git clone https://github.com/shaunyogeshwaran/Shaun_FYP.git
   # cd Shaun_FYP
   ```

2. Create a virtual environment and install Python dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate          # macOS/Linux
   # venv\Scripts\activate           # Windows (PowerShell: venv\Scripts\Activate.ps1)
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Install Node dependencies for frontend and docs:
   ```bash
   cd frontend && npm install && cd ..
   cd docs && npm install && cd ..
   ```

4. Download NLTK tokeniser data (required for v2 claim decomposition):
   ```bash
   python -c "import nltk; nltk.download('punkt_tab')"
   ```

5. Create the environment file:
   ```bash
   cp -n .env.example .env
   # Edit .env and add GROQ_API_KEY (optional)
   ```

6. Start the servers:
   ```bash
   # Terminal 1:
   source venv/bin/activate
   uvicorn api:app --host 0.0.0.0 --port 8000

   # Terminal 2:
   cd frontend && npm run dev
   ```

## Running the Demo

```bash
make start     # starts backend (port 8000) and frontend (port 5173)
make stop      # stops all servers
make restart   # bounces all servers
make status    # shows what is running
```

Open http://localhost:5173. The frontend has three pages:

- **Verify** (`/`) — Enter a claim, adjust Cw-CONLI thresholds via the control panel, toggle v2 Mode, and see the full pipeline: retrieval confidence gauge, LLM generation, NLI entailment score, per-claim breakdown (v2), and animated verdict.
- **Explore** (`/explore`) — Batch-run 7 pre-configured queries across different knowledge domains and compare results in a table with aggregate stats. Supports v1/v2 toggle.
- **How It Works** (`/about`) — Walkthrough of the 4-stage pipeline, v2 improvements, threshold variant formulas, and technical stack reference.

### v2 Mode

The v2 Mode toggle in the control panel enables:

- **Sliding-window NLI** — splits long premises into overlapping 400-token windows so summarisation documents are fully evaluated.
- **Sentence-level claim decomposition** — verifies each sentence independently, takes the minimum score (weakest-link).
- **BGE embeddings** — upgrades to BAAI/bge-small-en-v1.5 for higher retrieval fidelity.

When v2 is active, the verification column shows a per-claim score breakdown highlighting the weakest claim.

### Offline Mode

The interface works without an API key. Mock LLM responses are used; RAG and NLI verification still function.

## Running Tests

The pytest suite covers unit, integration, and API-level behaviour:

```bash
make test          # run the full pytest suite
make test-all      # include tests marked as slow (reserved)
```

Direct pytest invocation:

```bash
source venv/bin/activate
pytest tests/                        # run all
pytest tests/test_engine.py          # unit tests (engine components)
pytest tests/test_integration.py     # integration tests (full pipeline)
pytest tests/test_api.py             # API tests (FastAPI endpoints)
pytest tests/ -v                     # verbose output
pytest tests/ -k "verdict"           # run only tests matching a keyword
```

### Test coverage

| File | Focus | Approach |
|---|---|---|
| `tests/test_engine.py` | Embedding, NLI, verdict computation | White-box unit tests |
| `tests/test_integration.py` | Full pipeline, adaptive thresholds, offline mode | Black-box integration tests |
| `tests/test_api.py` | FastAPI endpoints, CORS, error handling, v1/v2 modes | API-level tests via `TestClient` |

Tests use session-scoped fixtures (`tests/conftest.py`) so the 1.4 GB RoBERTa-large-MNLI model loads once across the whole suite.

## Running Experiments

The evaluation pipeline uses HaluEval (10K QA + 10K Summarization samples) to benchmark three conditions:

- **C1 (RAG-only):** Baseline with no NLI verification.
- **C2 (Static CONLI):** Fixed NLI threshold.
- **C3 (Cw-CONLI):** Dynamic threshold weighted by retrieval confidence (tiered, sqrt, sigmoid variants).

### v1 Pipeline (Baseline)

```bash
python dataset.py                                     # verify dataset loading
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
| Temperature scaling | Raw softmax outputs are uncalibrated | Investigated (Guo et al. 2017). T=10.0 at boundary means logits are not calibratable for this task; disabled |
| Embedding upgrade | all-MiniLM-L6-v2 is outdated (2021, 384-dim) | BAAI/bge-small-en-v1.5 (same dim, better quality) |

Automated pipeline:

```bash
python run_v2.py                   # full run (~4h on GPU, ~24h on CPU)
python run_v2.py --limit 50        # smoke test (~minutes)
python run_v2.py --calibrate       # include calibration step (off by default)
```

Google Colab: open `colab_v2_pipeline.ipynb` with a T4 GPU runtime for ~3–6 hour total runtime.

Manual step-by-step:

```bash
python calibrate.py --split dev                           # calibrate NLI temperature
python evaluate.py --precompute --split dev --version v2  # pre-compute v2 scores
python evaluate.py --precompute --split test --version v2
python tune.py --split dev --version v2                   # tune with v2 grid ranges
python evaluate.py --condition C3 --split test --version v2
python analyze.py --split test --version v2               # generate figures
```

### Ablation Study

v2 scores include both decomposed (`nli_score`) and whole-response (`nli_score_whole`) NLI scores. Ablate via the `--nli-key` flag:

```bash
python tune.py --split dev --version v2 --nli-key nli_score_whole
python evaluate.py --condition C3 --split test --version v2 --nli-key nli_score_whole
```

## Environment Variables

User-configurable (set in `.env`, copied from `.env.example`):

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GROQ_API_KEY` | No | empty | Enables online LLM generation. Without it, mock responses are used. Must start with `gsk_`. |
| `HF_TOKEN` | No | empty | Avoids HuggingFace Hub rate limits during model download. Useful in restricted networks. |
| `BACKEND_PORT` | No | `8000` | Overrides backend port. The Vite dev proxy reads this too. |

Set automatically by `api.py` at startup. Do not override:

| Variable | Value | Purpose |
|---|---|---|
| `PYTORCH_ENABLE_MPS_FALLBACK` | `1` | Falls back to CPU when Apple MPS ops are unsupported |
| `TOKENIZERS_PARALLELISM` | `false` | Silences HuggingFace tokeniser fork warnings |
| `OMP_NUM_THREADS` | `1` | Prevents NumPy/PyTorch thread contention |
| `MKL_NUM_THREADS` | `1` | Same, for Intel MKL backend |

## Project Structure

```
Shaun_FYP/
├── api.py                      # FastAPI backend (v1 + v2 engine support)
├── engine.py                   # Core AFLHREngine class (embedding, retrieval, NLI, verdict)
├── config.py                   # Configuration, model IDs, thresholds, grid search ranges
├── dataset.py                  # HaluEval dataset loader with dev/test splitting
├── evaluate.py                 # Evaluation harness (precompute scores, apply conditions)
├── tune.py                     # Grid search hyperparameter tuning (version-aware)
├── analyze.py                  # Results analysis, plots, McNemar's test
├── calibrate.py                # NLI temperature scaling calibration
├── run_v2.py                   # Automated v2 experiment pipeline
├── colab_v2_pipeline.ipynb     # Colab notebook for GPU-accelerated experiments
├── start.py                    # Process supervisor used by `make start`
├── Makefile                    # install/start/stop/test/restart targets
├── Dockerfile                  # HuggingFace Space deployment image
├── requirements.txt            # Python dependencies (loose pins)
├── requirements-lock.txt       # Pinned dependencies for exact reproducibility
├── requirements-deploy.txt     # Lean dependencies for HF Space deployment
├── .env.example                # Environment variable template
├── tests/                      # Pytest suite (unit + integration + API)
│   ├── conftest.py             # Session-scoped fixtures (single model load)
│   ├── test_engine.py          # Engine unit tests
│   ├── test_integration.py     # Pipeline integration tests
│   └── test_api.py             # FastAPI endpoint tests
├── frontend/                   # React + Vite frontend (deployed to Vercel)
│   ├── src/
│   │   ├── components/         # CircularGauge, VerdictStamp, ThresholdPanel, ClaimBreakdown
│   │   ├── pages/              # VerifyPage, ExplorePage, AboutPage
│   │   ├── styles/             # Design system (theme.js, global.css)
│   │   ├── App.jsx             # Root component with routing
│   │   └── main.jsx            # Entry point
│   ├── package.json            # Node dependencies (React, Framer Motion, Recharts)
│   └── vite.config.js          # Vite config (dev proxy to FastAPI)
├── docs/                       # Docusaurus documentation site
├── results/                    # Experiment outputs
│   ├── *_v2.json/csv           # v2 experiment results
│   └── figures/                # Generated plots and visualisations
└── data/                       # Cached datasets (generated at runtime)
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

## Known Limitations and Expected Behaviour

These are documented behaviours, not defects:

- **MPS (Apple GPU) is disabled by design** on M1–M4 Macs. Intermittent segfaults during NLI inference on Metal led to an explicit CPU fallback. `PYTORCH_ENABLE_MPS_FALLBACK=1` is set in `api.py`.
- **Summarisation FPR remains ~98%** on HaluEval even with v2 windowed NLI. The remaining failure mode is the "semantic illusion" problem (Chen et al., 2025); sliding windows fix token truncation but not abstractive divergence. See thesis Chapter 10.2.6.
- **C3 does not outperform C2 on standard HaluEval** (McNemar's p = 1.0). This is a null result, not a broken implementation. Retrieval scores cluster tightly around 0.6–0.9, leaving no room for adaptive thresholds to differentiate. Under realistic shared-index retrieval, C3 Sqrt significantly reduces over-flagging (p = 1.4×10⁻⁵).
- **Temperature calibration is disabled.** The optimiser hits T = 10.0 at the search boundary, indicating NLI logits are not calibratable for this task. See `calibrate.py` output and thesis Chapter 8.8.
- **Groq free tier is rate-limited** (~30 requests/min). Heavy demo usage may hit limits; offline mode or a paid key is the workaround.
- **HF Space cold start is ~30 seconds** after 30 minutes of inactivity. This is a `cpu-basic` tier characteristic.
- **Demo knowledge base is 6 passages**. The full HaluEval evaluation uses 20,000 samples.
- **First-run model download takes 5–30 minutes** depending on connection. Models cache to `~/.cache/huggingface/` and are not re-downloaded on subsequent runs.

## Troubleshooting

### Installation

| Problem | Fix |
|---|---|
| `make: command not found` | macOS: `xcode-select --install`. Ubuntu/Debian: `sudo apt install build-essential`. Windows: use WSL2 |
| `python3: command not found` (Windows native) | Windows uses `python`, not `python3`. Use WSL2 and run Linux commands |
| `ERROR: Package requires a different Python` | Install Python 3.9+ (3.10 or 3.11 recommended). Verify with `python3 --version`. macOS: `brew install python@3.11` |
| `make install` fails on pip build | Missing C compiler. macOS: `xcode-select --install`. Linux: `sudo apt install build-essential python3-dev` |
| `make install` hangs on pip | Slow network or PyPI throttling. Wait up to 10 min. Debug: Ctrl+C, then `source venv/bin/activate && pip install -r requirements.txt -v` |
| `nodeenv` fails to download Node | Firewall blocking `nodejs.org`. Install Node 20 manually from [nodejs.org](https://nodejs.org) |
| `npm EACCES: permission denied` | `sudo chown -R $(whoami) ~/.npm`, then retry `make install` |
| `SSL: CERTIFICATE_VERIFY_FAILED` during model download | `make install` sets `SSL_CERT_FILE` to certifi's bundle. If still failing: `pip install --upgrade certifi` |
| `LookupError: Resource punkt_tab not found` | `python -c "import nltk; nltk.download('punkt_tab')"` inside the activated venv |
| `faiss-cpu` wheel install fails on ARM Mac | Upgrade pip: `pip install --upgrade pip` (21.3+ required for ARM wheels) |

### Runtime

| Problem | Fix |
|---|---|
| Backend will not start or `/api/health` 404 | Check `.run/backend.log`. Usually import error in `engine.py` or port conflict |
| Frontend blank or cannot connect | Check `.run/frontend.log`. Re-run `make install` if npm deps are missing |
| `[Errno 48] Address already in use` (port 8000) | `make stop`. If stuck: `lsof -i :8000` then `kill -9 <PID>` |
| Port 5173 already in use | Same approach with `:5173`, or set `BACKEND_PORT` and restart |
| Models download slowly | First run fetches ~3 GB from HuggingFace. Subsequent runs use `~/.cache/huggingface/` |
| `HTTPError: 429 Too Many Requests` from HuggingFace | Create a token at [hf.co/settings/tokens](https://huggingface.co/settings/tokens), then `export HF_TOKEN=hf_...` before `make start` |
| `MemoryError` or process killed during load | Close other apps. Requires ~4 GB free for MiniLM + RoBERTa-large, 16+ GB for HaluEval evaluation |
| MPS or Apple GPU segfault | Auto-handled by CPU fallback. Confirm `PYTORCH_ENABLE_MPS_FALLBACK=1` (default in `api.py`) |
| v2 mode returns `503: v2 engine unavailable` | BGE model download likely failed. `make restart`. If persistent: `rm -rf ~/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5` and retry |

### API and Network

| Problem | Fix |
|---|---|
| Status stuck on "Connecting" | Backend not reachable. Check `curl localhost:8000/api/health`. If it responds, restart frontend: `make restart` |
| Status stuck on "Offline Only" | Groq key not being read. Verify `.env` has `GROQ_API_KEY=gsk_...` (no quotes or spaces), then `make restart` |
| Groq `401 Unauthorized` | Invalid or expired key. Regenerate at [console.groq.com](https://console.groq.com). Placeholder `your_groq_api_key_here` is treated as unset |
| CORS error in browser console | `api.py` allows `*` by default. Only occurs if `allow_origins` was modified. Check `api.py` around line 39 |
| Live demo slow on first request | ~30s cold start is expected. HF Space sleeps after 30 minutes of inactivity and reloads RoBERTa-large on wake |

### Frontend

| Problem | Fix |
|---|---|
| `npm ERR! code ERESOLVE` | `cd frontend && npm install --legacy-peer-deps` |
| `EBADENGINE Unsupported engine` | Node version too old. Use the venv's nodeenv; do not use system Node if it is below 20 |
| Blank page after load | Hard refresh (Cmd+Shift+R or Ctrl+Shift+F5). Check browser console for errors |
| `fetch` fails with `ERR_CONNECTION_REFUSED` | Backend is not running. `make status` to check; `make start` to launch |

### Experiments

| Problem | Fix |
|---|---|
| `dataset.py` fails with `trust_remote_code` error | Incompatibility with `datasets>=4.6` for HaluEval. `requirements.txt` pins a compatible version; verify with `pip show datasets` |
| `evaluate.py --precompute` out of memory | Requires 16+ GB free RAM for full HaluEval 10K. Use `--limit 500` for smoke tests |
| `tune.py` takes hours | Expected. Full v2 grid is ~30 min on GPU, ~4 hours on CPU. Use `--limit` for quick iteration |
| Results do not match README tables | All experiments use `seed=42` and 70/30 dev/test split. Verify `config.py` has not been modified |
| NLTK segfault during v2 claim decomposition | Re-run `python -c "import nltk; nltk.download('punkt_tab')"` inside the venv |

### Cross-platform Notes

- On Windows, use WSL2. Native Windows path handling is untested and the Makefile uses POSIX shell syntax.
- On Apple Silicon Macs, MPS acceleration is disabled by design. CPU inference is the intended and tested path.
- On Linux servers, set the locale to UTF-8 (`export LANG=en_US.UTF-8`) to avoid tokeniser issues with non-ASCII HaluEval samples.

## Getting Help

If the troubleshooting section does not resolve the issue:

1. Check the logs. `.run/backend.log` and `.run/frontend.log` usually contain the exact error.
2. Verify key dependencies inside the venv:
   ```bash
   source venv/bin/activate
   pip list | grep -Ei "torch|transformers|sentence-transformers|faiss|fastapi|nltk"
   python --version
   node --version
   ```
3. Compare against the live demo. If [shaun-fyp-xi.vercel.app](https://shaun-fyp-xi.vercel.app) works but the local install does not, the issue is environment-specific.
4. Open a GitHub issue at https://github.com/shaunyogeshwaran/Shaun_FYP/issues with:
   - OS and Python version (`python3 --version`)
   - Full command and error message
   - Last ~50 lines of `.run/backend.log` or `.run/frontend.log`

## License

This project was developed as part of an undergraduate final year project for academic purposes.
