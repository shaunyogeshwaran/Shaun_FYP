# AFLHR Lite: Confidence-Weighted CONLI for Hallucination Detection

**Adaptive Framework for LLM Hallucination Reduction - Lite Version**

A two-layer verification pipeline that combines Retrieval-Augmented Generation (RAG) with Natural Language Inference (NLI) to detect hallucinations in LLM outputs. The core innovation is **Confidence-Weighted CONLI (Cw-CONLI)**: the NLI verification threshold adapts dynamically based on retrieval confidence, applying stricter scrutiny when evidence quality is low and more lenient thresholds when strong supporting evidence exists.

## Author

- **Name:** Shaun Yogeshwaran
- **Module:** 6COSC023W - Computer Science Final Project
- **Institution:** University of Westminster / Informatics Institute of Technology (IIT)
- **Degree:** BSc (Hons) Computer Science

## Prerequisites

- Python 3.10+
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
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Groq API key (free at https://console.groq.com)
   ```

## Running the Streamlit Demo

```bash
streamlit run app.py
```

This launches an interactive web interface where you can:
- Enter queries against a curated knowledge base
- Adjust threshold parameters (pivot, strict, lenient) via sidebar sliders
- View retrieval confidence, LLM-generated responses, and NLI verification results
- See colour-coded verdicts (VERIFIED / HALLUCINATION)

The demo works in **offline mode** without an API key (uses mock LLM responses; RAG and verification still function).

## Running Experiments

The evaluation pipeline uses HaluEval (10K QA + 10K Summarization samples) to benchmark three conditions:

- **C1 (RAG-only):** Baseline with no NLI verification
- **C2 (Static CONLI):** Fixed NLI threshold
- **C3 (Cw-CONLI):** Dynamic threshold weighted by retrieval confidence (tiered, sqrt, sigmoid variants)

### Full Pipeline

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
├── app.py              # Streamlit demo application
├── engine.py           # Core AFLHREngine class (embedding, retrieval, NLI, verdict)
├── config.py           # Configuration, model IDs, thresholds, knowledge base
├── dataset.py          # HaluEval dataset loader with dev/test splitting
├── evaluate.py         # Evaluation harness (precompute scores, apply conditions)
├── tune.py             # Grid search hyperparameter tuning
├── analyze.py          # Results analysis, plots, McNemar's test
├── test_components.py  # Component smoke tests
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
├── data/               # Cached datasets (generated at runtime)
└── results/            # Experiment outputs (generated at runtime)
    └── figures/        # Generated plots and visualisations
```

## Key Models

| Component | Model | Purpose |
|-----------|-------|---------|
| Embeddings | `all-MiniLM-L6-v2` | Semantic similarity for retrieval |
| NLI Verifier | `RoBERTa-large-MNLI` | Entailment scoring for verification |
| LLM Generator | `Llama-3.1-8B-Instant` (via Groq) | Response generation |

## License

This project was developed as part of an undergraduate final year project for academic purposes.
