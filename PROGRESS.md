# AFLHR Lite - Project Progress Report

## What is AFLHR Lite?

**AFLHR** stands for **Adaptive Framework for LLM Hallucination Reduction**.

This is a proof-of-concept Streamlit application that demonstrates a novel approach to detecting and reducing hallucinations in Large Language Model (LLM) outputs. The key innovation is using **confidence-weighted dynamic thresholds** that adapt based on how well the retrieved evidence matches the user's query.

---

## The Problem We're Solving

LLMs can "hallucinate" - generating plausible-sounding but factually incorrect information. Traditional approaches use fixed thresholds to verify outputs, but this doesn't account for the quality of the underlying evidence.

**Our Solution:** Adjust the verification strictness based on retrieval confidence:
- **Weak evidence?** Be skeptical (STRICT mode)
- **Strong evidence?** Trust it more (LENIENT mode)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: RAG RETRIEVAL                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │  Embedding  │ -> │   FAISS     │ -> │  Retrieval Score    │  │
│  │  (MiniLM)   │    │   Search    │    │  (Confidence 0-1)   │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM GENERATION (Groq)                         │
│            Llama 3.1 8B generates response from context          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 2: NLI VERIFICATION                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  RoBERTa-MNLI checks if response is ENTAILED by context │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CONFIDENCE-WEIGHTED THRESHOLD SELECTION                │    │
│  │                                                         │    │
│  │  IF retrieval_score < 0.75 (pivot):                     │    │
│  │      → STRICT mode (threshold = 0.95)                   │    │
│  │      → "Low confidence, be skeptical"                   │    │
│  │                                                         │    │
│  │  IF retrieval_score >= 0.75 (pivot):                    │    │
│  │      → LENIENT mode (threshold = 0.70)                  │    │
│  │      → "High confidence, trust evidence"                │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FINAL VERDICT                              │
│         NLI Score >= Threshold ? VERIFIED : HALLUCINATION        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Retrieval Layer (RAG)
- **Embedding Model:** `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Vector Store:** FAISS with Inner Product similarity
- **Output:** Top-2 relevant documents + confidence score

### 2. Generation Layer
- **LLM:** Llama 3.1 8B via Groq API
- **System Prompt:** Instructs model to use ONLY provided context
- **Offline Mode:** Mock response for testing without API

### 3. Verification Layer (NLI)
- **Model:** `FacebookAI/roberta-large-mnli`
- **Task:** Natural Language Inference (entailment detection)
- **Output:** Probability that response is entailed by evidence

### 4. Threshold Logic
| Retrieval Score | Mode | Threshold | Reasoning |
|-----------------|------|-----------|-----------|
| < 0.75 | STRICT | 95% | Low confidence → be skeptical |
| ≥ 0.75 | LENIENT | 70% | High confidence → trust evidence |

---

## Files Created

| File | Purpose |
|------|---------|
| `config.py` | Configuration, model IDs, thresholds, knowledge base |
| `engine.py` | Core `AFLHREngine` class with RAG, generation, verification |
| `app.py` | Streamlit UI with 3-column layout and sliders |
| `test_components.py` | Diagnostic script to isolate component issues |
| `.env.example` | Template for Groq API key |
| `.gitignore` | Excludes `.env`, `__pycache__`, venv, etc. |
| `requirements.txt` | Python dependencies |

---

## Knowledge Base Topics

The demo includes 6 curated paragraphs:

1. **University of Westminster** (3 paragraphs)
   - Founding history (1838, Royal Polytechnic Institution)
   - Campus locations (Regent Street, Cavendish, Marylebone, Harrow)
   - Technological firsts (Lumière brothers, 1992 university status)

2. **AI Hallucinations** (2 paragraphs)
   - Definition and causes
   - Types (factual, entity, attribution, fabricated citations)

3. **Climate of Sri Lanka** (1 paragraph - distractor topic)
   - Monsoon patterns and temperature ranges

---

## Technical Challenges Resolved

### 1. Segmentation Faults
**Problem:** `sentence-transformers` library caused segfaults on Apple Silicon with Anaconda.

**Solution:** Replaced with direct `transformers` library usage:
- Manual mean pooling replicating SentenceTransformer behavior
- Force CPU mode to avoid MPS issues
- Set environment variables before imports

### 2. PyTorch Compatibility
**Problem:** PyTorch 2.9.0 in Anaconda had binary incompatibility.

**Solution:** Created fresh venv with PyTorch 2.6.0:
```bash
python -m venv aflhr_env
source aflhr_env/bin/activate
pip install torch==2.6.0
```

### 3. Deprecated Groq Model
**Problem:** `llama3-8b-8192` was decommissioned.

**Solution:** Updated to `llama-3.1-8b-instant` in config.py.

---

## Current Status

### Working Features
- RAG retrieval with FAISS indexing
- LLM generation via Groq API
- NLI verification with RoBERTa-MNLI
- Confidence-weighted threshold selection
- Streamlit UI with live-tunable sliders
- Offline mode for testing without API
- Debug info display

### Verified Test Results
**Query:** "When was the University of Westminster founded?"
- Retrieval Confidence: 87.71% (LENIENT mode triggered)
- Generated Response: "The University of Westminster was founded in 1838."
- NLI Entailment Score: 88.25%
- Threshold Applied: 70% (LENIENT)
- **Verdict: VERIFIED** ✅

---

## How to Run

```bash
# 1. Activate the virtual environment
source aflhr_env/bin/activate

# 2. Set your Groq API key (or use offline mode)
cp .env.example .env
# Edit .env with your key

# 3. Run the Streamlit app
streamlit run app.py
```

---

## Next Steps (Potential)

- [ ] Add more knowledge base topics
- [ ] Implement score calibration based on test runs
- [ ] Add export functionality for results
- [ ] Create evaluation metrics dashboard
- [ ] Test with adversarial queries
- [ ] Optimize for MPS/GPU acceleration

---

## End Goal

This proof-of-concept demonstrates that **adaptive, confidence-weighted verification** can improve hallucination detection compared to fixed thresholds. The system:

1. **Retrieves** relevant context from a knowledge base
2. **Generates** a response grounded in that context
3. **Verifies** the response using NLI entailment
4. **Adapts** the verification threshold based on evidence quality

The ultimate goal is to show that this approach reduces both false positives (rejecting good responses) and false negatives (accepting hallucinations) by being appropriately strict or lenient based on the situation.
