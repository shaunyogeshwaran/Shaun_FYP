# AFLHR Lite - Proof of Concept Guide

A plain-English explanation of how the notebook works.

---

## What Problem Are We Solving?

Large Language Models (like ChatGPT) sometimes make things up. These made-up facts are called **hallucinations**. For example, an AI might confidently say "The Eiffel Tower is 500 meters tall" when it's actually 330 meters.

Current systems try to catch these hallucinations by checking if the AI's statement matches trusted sources. But they use a **fixed rule** — essentially saying "if the match score is above 0.5, it's true."

**The problem:** A fixed rule doesn't account for how good the evidence is. Sometimes we find great evidence, sometimes we find weak evidence. We should be more trusting when evidence is strong, and more skeptical when it's weak.

---

## What Does This Notebook Prove?

This notebook demonstrates one key idea:

> **Adjust how strict we are based on how confident we are in the evidence we found.**

- Found great evidence? Lower the bar for verification (trust it more).
- Found weak evidence? Raise the bar (be more skeptical).

---

## How It Works (Step by Step)

### Step 1: Build a Mini Knowledge Base

We create a small database of 5 facts about Mars:

```
"Mars is the fourth planet from the Sun..."
"Mars is called the Red Planet..."
"Mars has two small moons..."
"A day on Mars is about 24 hours and 37 minutes..."
"Mars has the largest volcano in the solar system..."
```

Think of this as our "trusted source of truth."

### Step 2: Create a Smart Search Tool

When someone asks a question, we search our knowledge base for the most relevant fact. But here's the key: **we also get a confidence score** telling us how well the question matches what we found.

| Question | Best Match | Confidence |
|----------|-----------|------------|
| "What color is Mars?" | "Mars is called the Red Planet..." | **High** (0.805) |
| "How many moons does Mars have?" | "Mars has two small moons named Phobos and Deimos." | **High** (0.853) |
| "What's the weather on Jupiter?" | "A day on Mars (called a sol) is about 24 hours..." | **Low** (0.649) |

The third question gets a low score because our database is about Mars, not Jupiter. The system found *something*, but it's not really relevant.

### Step 3: The Adaptive Threshold (The Core Innovation)

Here's where the magic happens. Instead of using a fixed verification threshold (like 0.5), we **adjust the threshold based on the confidence score**.

**The Formula:**
```
threshold = 0.5 + 0.5 × (0.7 - confidence_score)
```

**In plain English:**

| If confidence is... | The threshold becomes... | Because... |
|---------------------|-------------------------|------------|
| Very High (0.95) | Lower (0.375) | We strongly trust good evidence |
| High (0.80) | Lower (0.45) | We trust good evidence |
| Medium (0.70) | Normal (0.50) | Neutral position |
| Low (0.55) | Higher (0.575) | We're skeptical of weak evidence |
| Very Low (0.40) | Higher (0.65) | We're very skeptical |

### Step 4: Verify Claims

Now when checking if a statement is true, we compare it against the evidence using Natural Language Inference (NLI). This gives us a score indicating how well the claim matches the evidence.

**The Decision:**
- If the NLI score is **above** the threshold → Claim is **verified**
- If the NLI score is **below** the threshold → Claim is **flagged as potential hallucination**

---

## The Two Scenarios Explained

### Scenario A: High Confidence (Good Evidence)

```
Question: "What color is Mars?"
Claim: "Mars appears red due to iron oxide on its surface."
```

**Actual Test Results:**

1. **Search:** Finds "Mars is called the Red Planet because of iron oxide (rust) on its surface."
2. **Confidence:** 0.805 (high — great match!)
3. **Threshold:** Lowered to 0.447 (trust this evidence)
4. **NLI Score:** 0.45 (claim matches evidence reasonably well)
5. **Decision:** 0.45 > 0.447 → **VERIFIED**

**What would a fixed threshold do?**
With a fixed 0.5 threshold: 0.45 < 0.5 → Would **incorrectly flag** this as a hallucination!  Since we know this claim is factually accurate (easily verifiable), rejecting it would be a false positive.

### Scenario B: Low Confidence (Weak Evidence)

```
Question: "What is the weather like on Jupiter?"
Claim: "Jupiter has mild, pleasant weather similar to Earth."
```

**Actual Test Results:**

1. **Search:** Finds "A day on Mars (called a sol) is about 24 hours and 37 minutes long." (wrong planet!)
2. **Confidence:** 0.649 (lower — we don't have Jupiter info)
3. **Threshold:** Raised to 0.526 (be skeptical)
4. **NLI Score:** 0.42 (weak match)
5. **Decision:** 0.42 < 0.526 → **FLAGGED AS POTENTIAL HALLUCINATION**

The system correctly catches this because it's more skeptical when evidence quality is poor.

---

## Why This Matters

| Approach | Problem |
|----------|---------|
| **Fixed Threshold** | Treats all evidence equally. Might reject good claims or accept bad ones. |
| **Adaptive Threshold** | Adjusts strictness based on evidence quality. More accurate overall. |

The adaptive approach:
- **Reduces false positives** (incorrectly flagging true statements)
- **Catches more hallucinations** (when evidence is weak)
- **Adapts to evidence quality** (smarter verification)

---

## Summary

1. **Search** for relevant evidence and get a confidence score
2. **Adjust** the verification threshold based on that confidence
3. **Verify** claims against the evidence using the adjusted threshold

High confidence in evidence → Lower the bar → Trust more
Low confidence in evidence → Raise the bar → Be skeptical

This is the core innovation that makes AFLHR Lite different from existing hallucination detection systems.

---

## Running the Notebook

1. Open `poc_demo.ipynb` in Jupyter or VS Code
2. Run all cells in order (Shift+Enter)
3. Observe the output showing both scenarios

The notebook uses simulated NLI scores for demonstration. The full system would use a real NLI model (RoBERTa-MNLI) for actual verification.

---

## Cell-by-Cell Breakdown

### Cell 0-2: Introduction & Setup Header
Markdown cells explaining the PoC goals and the adaptive threshold concept.

### Cell 3: Install Dependencies
```python
!pip install -r requirements.txt -q
```
Installs required packages (sentence-transformers, faiss-cpu, numpy).

### Cell 4: Module Description
Markdown explaining the semantic retrieval component.

### Cell 5: Load Embedding Model
```python
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```
Loads the sentence transformer model used to convert text into 384-dimensional vectors.

### Cell 6: Define Knowledge Base
Creates a list of 5 Mars facts that serve as the "trusted source of truth" for retrieval.

### Cell 7: Embed Knowledge Base
Converts all 5 facts into normalized vector embeddings for similarity search.

### Cell 8: Build FAISS Index
```python
faiss_index = faiss.IndexFlatIP(dimension)
```
Creates an Inner Product index for cosine similarity search (works because vectors are normalized).

### Cell 9: Define `retrieve_with_confidence()`
The retrieval function that:
1. Embeds the query
2. Searches FAISS for the closest document
3. Normalizes the similarity score from [-1, 1] to [0, 1]
4. Returns the document, score, and index

### Cell 10: Test Retriever
Runs 4 test queries through the retriever to demonstrate varying confidence scores.

### Cell 11: Adaptive Threshold Description
Markdown explaining the formula and intuition behind dynamic thresholds.

### Cell 12: Define `calculate_dynamic_threshold()`
The core innovation function:
```python
dynamic_threshold = base_threshold + alpha * (pivot - retrieval_score)
```
Adjusts threshold up/down based on retrieval confidence.

### Cell 13: Threshold Demonstration
Shows how 5 different retrieval scores map to different thresholds.

### Cell 14: Pipeline Description
Markdown introducing the end-to-end verification demonstration.

### Cell 15: Define `verify_claim()`
Simple comparison function that checks if entailment_score > threshold.

### Cell 16: Scenario A Execution
Runs the high-confidence Mars query through the full pipeline.

### Cell 17: Scenario B Execution
Runs the low-confidence Jupiter query (off-topic) through the pipeline.

### Cell 18: Summary
Prints the PoC results and outlines next steps for the full prototype.

---

## Hardcoded Values Reference

These values are hardcoded in the notebook for demonstration purposes. In a production system, many would be configurable or learned.

### Model & Infrastructure

| Element | Value | Cell | Notes |
|---------|-------|------|-------|
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` | 5 | Lightweight model (384 dims). Could swap for larger models. |
| FAISS Index Type | `IndexFlatIP` | 8 | Brute-force inner product. Fine for small KB, would need IVF for scale. |

### Adaptive Threshold Parameters

| Parameter | Value | Cell | Purpose |
|-----------|-------|------|---------|
| `base_threshold` | `0.5` | 12 | Starting point for threshold adjustment |
| `alpha` | `0.5` | 12 | Sensitivity — how much confidence affects threshold |
| `pivot` | `0.7` | 12 | Breakpoint — scores above this lower the threshold |
| Clamp Min | `0.3` | 12 | Prevents threshold from going too low |
| Clamp Max | `0.7` | 12 | Prevents threshold from going too high |
| Fixed Baseline | `0.5` | 16 | For comparison with dynamic approach |

### Knowledge Base (5 facts)

| Index | Fact | Cell |
|-------|------|------|
| 0 | "Mars is the fourth planet from the Sun in our solar system." | 6 |
| 1 | "Mars is called the Red Planet because of iron oxide (rust) on its surface." | 6 |
| 2 | "Mars has two small moons named Phobos and Deimos." | 6 |
| 3 | "A day on Mars (called a sol) is about 24 hours and 37 minutes long." | 6 |
| 4 | "Mars has the largest volcano in the solar system, called Olympus Mons." | 6 |

### Test Queries

| Query | Cell | Purpose |
|-------|------|---------|
| "What color is Mars?" | 10, 16 | High-confidence on-topic query |
| "How many moons does Mars have?" | 10 | High-confidence on-topic query |
| "Is Mars blue?" | 10 | On-topic but factually wrong |
| "What is the weather like on Jupiter?" | 10, 17 | Off-topic query (KB has no Jupiter info) |

### Threshold Demo Scores

| Score | Cell | Maps to Threshold |
|-------|------|-------------------|
| 0.95 | 13 | 0.375 (very low — trust evidence) |
| 0.80 | 13 | 0.45 (low — trust evidence) |
| 0.70 | 13 | 0.50 (neutral — at pivot) |
| 0.55 | 13 | 0.575 (higher — skeptical) |
| 0.40 | 13 | 0.65 (high — very skeptical) |

### Simulated NLI Scores

| Scenario | Claim | Simulated Score | Cell | Why Simulated? |
|----------|-------|-----------------|------|----------------|
| A | "Mars appears red due to iron oxide on its surface." | `0.45` | 16 | Real NLI (RoBERTa-MNLI) not integrated yet |
| B | "Jupiter has mild, pleasant weather similar to Earth." | `0.42` | 17 | Represents weak entailment for off-topic claim |

### Score Normalization

| Element | Value | Cell | Notes |
|---------|-------|------|-------|
| Raw FAISS score range | `[-1, 1]` | 9 | Cosine similarity range |
| Normalized score formula | `(score + 1) / 2` | 9 | Converts to [0, 1] for intuitive interpretation |

---

## What Would Change in Production?

| Current (PoC) | Production | Why |
|---------------|------------|-----|
| 5 hardcoded Mars facts | Wikipedia/domain corpus | Scale to real-world coverage |
| Simulated NLI scores | RoBERTa-MNLI model | Actual semantic entailment inference |
| Fixed α and pivot | Learned or tuned values | Optimize for specific dataset/domain |
| `IndexFlatIP` | `IndexIVFFlat` or HNSW | Scale to millions of documents |
| No response generation | Llama-3-8B integration | Generate verified responses |
