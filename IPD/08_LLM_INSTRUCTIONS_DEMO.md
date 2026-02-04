# LLM Instructions: Demo Video Assistance

## Purpose of This Document

This document provides comprehensive context for any LLM (Large Language Model) assistant helping with the IPD (Interim Progression Demonstration) prototype demonstration video. It contains all information needed to provide accurate, detailed assistance with the 5-10 minute demo video.

**Use this document when:** Recording the demo, explaining code, troubleshooting issues, preparing test scenarios, or improving any aspect of the demonstration video.

---

## Video Requirements Summary

### From Official Guidelines

**Duration:** 5-10 minutes total
- **Code Explanation:** Maximum 7 minutes
- **Prototype Demo:** Maximum 3 minutes

**Content Requirements:**
- Showcase the prototype developed so far
- Highlight key features and functionalities
- Include voice-over throughout
- Clearly explain project progress, objectives, and technical details

**Format:**
- Upload to YouTube as **unlisted** video
- Share the URL in submission
- **CRITICAL:** Ensure link is accessible - failure to provide access may result in 0 marks

**Quality:**
- Video editing skills are NOT assessed
- Audio quality is crucial - voice-over must be clear and understandable
- Video must be well-structured and clear

---

## Project Overview

### Project Title
**AFLHR Lite: Adaptive Framework for LLM Hallucination Reduction**

### Core Innovation
The system uses **retrieval confidence** to dynamically adjust **verification thresholds**:
- **Low confidence** (below pivot 0.75) = **STRICT mode** (threshold 0.95) = Be skeptical
- **High confidence** (at/above pivot 0.75) = **LENIENT mode** (threshold 0.70) = Trust evidence

### Why This Matters
Existing hallucination detection systems use fixed thresholds regardless of evidence quality. AFLHR Lite adapts strictness based on how confident we are in our evidence.

---

## Code Structure

### File Overview

```
AFLHR_Lite/
├── config.py          # Configuration settings (EXPLAIN FIRST)
├── engine.py          # Core logic (EXPLAIN SECOND - MOST IMPORTANT)
├── app.py             # User interface (EXPLAIN THIRD)
├── requirements.txt   # Dependencies
├── .env               # API key (DO NOT SHOW IN VIDEO)
└── IPD/               # Documentation
```

### config.py - What to Explain

**Location:** Root of project
**Purpose:** Centralizes all configuration for easy modification

**Key Sections to Highlight:**

1. **Model Configuration**
```python
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim embeddings
VERIFIER_MODEL = "FacebookAI/roberta-large-mnli"        # NLI verification
GENERATOR_MODEL = "llama-3.1-8b-instant"                # LLM generation via Groq
```

2. **Threshold Defaults (CORE INNOVATION)**
```python
DEFAULT_PIVOT = 0.75              # Switching point between modes
DEFAULT_STRICT_THRESHOLD = 0.95  # Used when evidence is WEAK
DEFAULT_LENIENT_THRESHOLD = 0.70 # Used when evidence is STRONG
```

3. **Knowledge Base**
```python
KNOWLEDGE_BASE = [
    "University of Westminster paragraph 1...",
    "University of Westminster paragraph 2...",
    "University of Westminster paragraph 3...",
    "AI hallucinations paragraph 1...",
    "AI hallucinations paragraph 2...",
    "Sri Lanka climate (distractor)..."
]
```

**Talking Points:**
- "All settings are centralized here for easy modification"
- "Three models work together: embedding, NLI verification, and LLM generation"
- "The threshold defaults are the key parameters for my adaptive system"
- "The knowledge base has 6 paragraphs - enough to demonstrate adaptive behavior"

---

### engine.py - What to Explain

**Location:** Root of project
**Purpose:** Contains the core AFLHREngine class that implements the pipeline

**Key Methods to Highlight:**

#### 1. `__init__` Method
**Purpose:** Initializes all components

**What it does:**
- Loads embedding model (MiniLM) with CPU mode
- Loads NLI verifier (RoBERTa-MNLI) with CPU mode
- Initializes Groq client for LLM generation
- Builds FAISS index from knowledge base

**Talking Points:**
- "Note the `device='cpu'` - this prevents segmentation faults on Apple Silicon"
- "The FAISS index is built at initialization for fast similarity search"

#### 2. `retrieve()` Method
**Purpose:** Layer 1 - RAG Retrieval

**What it does:**
1. Embeds the query to 384-dim vector
2. Searches FAISS for top-k similar documents
3. Calculates confidence score (normalized cosine similarity)
4. Returns documents + confidence score

**Talking Points:**
- "This is Layer 1 of the pipeline"
- "The confidence score is crucial - it drives the adaptive threshold selection"
- "High confidence means we found highly relevant evidence"
- "Low confidence means marginally related or unrelated content"

#### 3. `generate()` Method
**Purpose:** LLM Response Generation

**What it does:**
1. Sends context + query to Groq API
2. System prompt instructs: "Use ONLY the provided context"
3. Returns grounded response
4. Falls back to mock response in offline mode

**Talking Points:**
- "The LLM is instructed to use ONLY the retrieved context"
- "This grounding is essential for the verification to work"
- "There's an offline mode for testing without API access"

#### 4. `verify()` Method
**Purpose:** Layer 2 - NLI Verification

**What it does:**
1. Takes context as premise, response as hypothesis
2. Runs through RoBERTa-MNLI
3. Returns entailment probability (0-1)

**Talking Points:**
- "This is Layer 2 of the pipeline"
- "NLI tells us how strongly the evidence supports the response"
- "High entailment = well-supported; Low entailment = potential hallucination"

#### 5. `calculate_verdict()` Method - MOST IMPORTANT
**Purpose:** Adaptive Threshold Decision (CORE INNOVATION)

**What it does:**
```python
if retrieval_confidence < pivot:
    mode = "STRICT"
    threshold = strict_threshold  # 0.95
else:
    mode = "LENIENT"
    threshold = lenient_threshold  # 0.70

verdict = "VERIFIED" if nli_score >= threshold else "HALLUCINATION"
```

**Talking Points:**
- "This is THE CORE INNOVATION of my project"
- "If retrieval confidence is below pivot, we have weak evidence - be skeptical"
- "If retrieval confidence is at or above pivot, we have strong evidence - trust it"
- "The threshold adapts based on evidence quality"
- "This is what differentiates my system from fixed-threshold approaches"

---

### app.py - What to Explain

**Location:** Root of project
**Purpose:** Streamlit user interface

**Key Sections to Highlight:**

1. **Sidebar Configuration**
```python
pivot = st.sidebar.slider("Pivot Point", 0.0, 1.0, DEFAULT_PIVOT)
strict = st.sidebar.slider("Strict Threshold", 0.0, 1.0, DEFAULT_STRICT_THRESHOLD)
lenient = st.sidebar.slider("Lenient Threshold", 0.0, 1.0, DEFAULT_LENIENT_THRESHOLD)
offline_mode = st.sidebar.checkbox("Offline Mode")
```

2. **Three-Column Results Display**
```python
col1, col2, col3 = st.columns(3)
with col1:  # Evidence
    st.write("Retrieved Evidence")
    st.metric("Retrieval Confidence", f"{confidence:.2%}")
with col2:  # Response
    st.write("Generated Response")
with col3:  # Verdict
    st.write("Verification Result")
    st.metric("Entailment Score", f"{nli_score:.2%}")
    # Color-coded verdict badge
```

**Talking Points:**
- "Users can adjust all three threshold parameters in real-time"
- "Results display in three columns: Evidence, Response, Verdict"
- "The verdict is color-coded - green for VERIFIED, red for HALLUCINATION"
- "This provides immediate visual feedback"

---

## Demo Scenarios

### Demo 1: High Confidence Query (LENIENT Mode)

**Query:** "When was the University of Westminster founded?"

**Expected Results:**
- Retrieval Confidence: ~0.85-0.90 (ABOVE pivot of 0.75)
- Mode: LENIENT
- Threshold Applied: 0.70
- Generated Response: "The University of Westminster was founded in 1838"
- NLI Entailment Score: ~0.85-0.95
- Verdict: **VERIFIED** (green)

**Why this works:**
- Query matches knowledge base well (Westminster content)
- High retrieval confidence triggers LENIENT mode
- NLI score easily exceeds 0.70 threshold
- System correctly verifies a factual response

**Talking Points:**
- "The retrieval confidence is high because we have good evidence about Westminster"
- "LENIENT mode is activated, so our threshold is 0.70"
- "The response is verified because the NLI score exceeds this threshold"

---

### Demo 2: Low Confidence Query (STRICT Mode)

**Query:** "What is the weather like on Jupiter?"

**Expected Results:**
- Retrieval Confidence: ~0.55-0.70 (BELOW pivot of 0.75)
- Mode: STRICT
- Threshold Applied: 0.95
- Generated Response: May generate something about Jupiter or acknowledge lack of info
- NLI Entailment Score: Very low (~0.1-0.3)
- Verdict: **HALLUCINATION** (red)

**Why this works:**
- Query doesn't match knowledge base (no Jupiter content)
- Low retrieval confidence triggers STRICT mode
- Even if NLI gave moderate score, it wouldn't reach 0.95
- System correctly flags potential hallucination

**Talking Points:**
- "The retrieval confidence is low because our knowledge base doesn't cover Jupiter"
- "STRICT mode is activated, so our threshold is now 0.95"
- "The NLI score is low because the evidence doesn't support claims about Jupiter"
- "This is correctly flagged as a hallucination"

---

### Demo 3: Threshold Adjustment

**Purpose:** Show real-time configurability

**Actions:**
1. Adjust pivot slider from 0.75 to 0.60
2. Re-run a query
3. Show how the mode selection changes

**Talking Points:**
- "Users can tune these parameters based on their accuracy requirements"
- "Higher pivot means stricter overall"
- "Lower pivot means more lenient overall"
- "This flexibility allows adaptation for different use cases"

---

## Technical Setup for Recording

### Prerequisites Checklist

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Verify Groq API key is set
echo $GROQ_API_KEY

# 3. Check dependencies installed
pip list | grep -E "transformers|faiss|streamlit|groq"

# 4. Start the application
streamlit run app.py
```

### Environment Variables Required

```bash
export GROQ_API_KEY="your-api-key-here"

# For Apple Silicon stability (already in code, but just in case)
export TOKENIZERS_PARALLELISM=false
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Segfault on start | Ensure CPU mode is set in code, restart terminal |
| API key error | Check .env file or export GROQ_API_KEY |
| Model download stalls | Check internet connection, wait for download |
| Port in use | Use `streamlit run app.py --server.port 8502` |
| Slow first load | Normal - models downloading, wait ~30 seconds |

---

## Recording Guidelines

### Before Recording

1. **Test all three demo queries** - Ensure they produce expected results
2. **Increase font size** in IDE for readability (Cmd+= on Mac)
3. **Clear terminal** history
4. **Close unnecessary applications** to reduce distractions
5. **Check microphone** levels
6. **Prepare browser** window with Streamlit UI

### During Recording

1. **Speak clearly** at moderate pace
2. **Pause briefly** when switching between files/screens
3. **Point out key code sections** explicitly (use cursor)
4. **Explain the "why"** not just the "what"
5. **Read actual numbers** from the UI during demo
6. **Highlight the adaptive behavior** - this is the innovation

### Timing Targets

| Section | Duration | Cumulative |
|---------|----------|------------|
| Introduction | 0:30 | 0:30 |
| Project Structure | 0:30 | 1:00 |
| config.py | 1:30 | 2:30 |
| engine.py - Init | 1:00 | 3:30 |
| engine.py - Retrieve | 1:00 | 4:30 |
| engine.py - Generate/Verify | 1:00 | 5:30 |
| engine.py - Calculate Verdict | 1:00 | 6:30 |
| app.py | 0:30 | 7:00 |
| **Part 1 Total** | **7:00** | |
| Starting App | 0:30 | 7:30 |
| Demo 1 - High Confidence | 0:45 | 8:15 |
| Demo 2 - Low Confidence | 0:45 | 9:00 |
| Demo 3 - Threshold Adjust | 0:30 | 9:30 |
| Conclusion | 0:30 | 10:00 |
| **Part 2 Total** | **3:00** | |
| **GRAND TOTAL** | **10:00** | |

### After Recording

1. **Review video** for clarity and pacing
2. **Upload to YouTube** as **unlisted**
3. **Test link** in incognito window to verify accessibility
4. **Copy URL** for submission
5. **Backup video** locally and to cloud storage

---

## Key Messages to Convey

Throughout the demo, ensure these key messages come across:

### 1. The Core Innovation
"The system uses retrieval confidence to dynamically adjust verification thresholds - being more skeptical when evidence is weak, and more trusting when evidence is strong."

### 2. Why It Matters
"This addresses a gap in existing systems that use fixed thresholds regardless of evidence quality."

### 3. The Adaptive Behavior
"When retrieval confidence is below the pivot, STRICT mode applies a 0.95 threshold. When at or above, LENIENT mode applies a 0.70 threshold."

### 4. The Result
"This reduces both false positives (incorrectly flagging good responses) and false negatives (missing actual hallucinations)."

### 5. All Core Functionalities Work
"The prototype demonstrates semantic retrieval with confidence scoring, grounded LLM generation, NLI verification, and adaptive threshold selection."

---

## Sample Narration Snippets

### For config.py:
> "All settings are centralized in config.py for easy modification. The threshold defaults are key: pivot at 0.75 is where we switch between strict and lenient modes."

### For engine.py retrieve():
> "The retrieve method embeds the query, searches FAISS, and most importantly, calculates a confidence score. This score drives everything - it determines which threshold we'll use."

### For engine.py calculate_verdict():
> "This is the core innovation. If retrieval confidence is below 0.75, we have weak evidence, so we apply the strict 0.95 threshold. If it's above, we have strong evidence and apply the lenient 0.70 threshold."

### For Demo 1:
> "Look at the retrieval confidence - it's above 0.75, so we're in LENIENT mode. The NLI score easily exceeds 0.70, so this is correctly marked as VERIFIED."

### For Demo 2:
> "Now the retrieval confidence is below 0.75, so we're in STRICT mode. Even if the NLI score were moderate, it wouldn't reach 0.95. This is correctly flagged as a hallucination."

### For Conclusion:
> "This demonstrates the adaptive approach: strict when evidence is weak, lenient when evidence is strong. This is what differentiates AFLHR Lite from fixed-threshold systems."

---

## Troubleshooting During Recording

### If API calls fail:
- Enable offline mode in the sidebar
- Continue demo with mock responses
- Say: "I've enabled offline mode as a fallback for demonstration purposes"

### If confidence scores are unexpected:
- The exact numbers may vary
- Focus on relative behavior (high vs low)
- The principle is consistent: high confidence = LENIENT, low confidence = STRICT

### If models fail to load:
- Restart the application
- Check internet connection
- If persistent, restart terminal and try again

### If the app crashes:
- This shouldn't happen with CPU mode
- If it does, restart and continue from where you left off
- Minor editing in post is acceptable

---

## Quick Reference Card

```
PROJECT: AFLHR Lite - Adaptive Framework for LLM Hallucination Reduction

CORE INNOVATION:
- Retrieval Confidence < 0.75 → STRICT mode (threshold 0.95)
- Retrieval Confidence >= 0.75 → LENIENT mode (threshold 0.70)

FILES TO SHOW:
1. config.py - Models, thresholds, knowledge base
2. engine.py - retrieve(), generate(), verify(), calculate_verdict()
3. app.py - Sliders, 3-column display

DEMO QUERIES:
1. "When was the University of Westminster founded?" → VERIFIED (high confidence)
2. "What is the weather like on Jupiter?" → HALLUCINATION (low confidence)
3. Adjust pivot slider → Show configurability

VIDEO LIMITS:
- Code explanation: MAX 7 minutes
- Live demo: MAX 3 minutes
- Total: 5-10 minutes

UPLOAD: YouTube as UNLISTED - ensure link is accessible!
```
