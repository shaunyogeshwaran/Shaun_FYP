# AFLHR Lite: How It Works (Layman's Guide)

## The Problem: AI Makes Stuff Up

You've probably used ChatGPT or similar AI chatbots. They're impressive, but they have a serious flaw: **they sometimes make things up and sound completely confident about it**.

For example, ask ChatGPT about an obscure historical event, and it might give you dates, names, and details that are completely fabricated—but it says them with the same confidence as true facts.

This is called **"hallucination"**—the AI generates plausible-sounding but false information.

### Why Does This Happen?

AI language models don't actually "know" facts. They're trained to predict **what word comes next** based on patterns in text. They're essentially very sophisticated autocomplete systems.

When the AI doesn't have enough training data about something, it fills in the gaps with plausible-sounding guesses. It can't tell the difference between:
- Something it learned from reliable sources
- Something it's making up on the spot

---

## The Solution: AFLHR (This Project)

**AFLHR** stands for **Adaptive Framework for LLM Hallucination Reduction**.

This project tackles the problem with a **two-layer verification system**:

```
User Question → [LAYER 1: Find Evidence] → [LAYER 2: Verify Response] → Verdict
```

---

## Layer 1: RAG (Retrieval-Augmented Generation)

### What is RAG?

Instead of letting the AI answer from memory (which can be wrong), we:
1. First **search a trusted knowledge base** for relevant information
2. Then give that information to the AI as "context"
3. Tell the AI: "Answer based ONLY on this context"

It's like the difference between:
- Asking someone to answer a test from memory (risky)
- Letting them look at their notes while answering (safer)

### How This System Does It

#### Step 1: Convert Text to Numbers (Embeddings)

Computers can't understand words directly. We need to convert text into numbers that capture meaning.

**Model used:** `sentence-transformers/all-MiniLM-L6-v2`

This model converts any sentence into a list of 384 numbers (called a "vector" or "embedding"). Sentences with similar meanings get similar numbers.

Example:
```
"When was Westminster founded?" → [0.23, -0.45, 0.12, ... 384 numbers]
"What year did Westminster start?" → [0.24, -0.44, 0.11, ... similar numbers!]
"What's the weather in London?" → [0.67, 0.33, -0.89, ... different numbers]
```

#### Step 2: Search for Similar Documents (FAISS)

**FAISS** (Facebook AI Similarity Search) is like a super-fast search engine for these number vectors.

When you ask a question:
1. Your question gets converted to numbers
2. FAISS finds which knowledge base documents have the most similar numbers
3. Those documents become the "evidence" for the AI

The **similarity score** (0-100%) tells us how relevant the evidence is.

#### Step 3: Generate an Answer (Llama 3.1)

**Model used:** `llama-3.1-8b-instant` via Groq

Now we have relevant evidence. We send it to Llama with your question:

```
System: "You are a precise assistant. Answer ONLY using the context provided."

Context: [Retrieved documents about Westminster...]

Question: "When was Westminster founded?"
```

Llama generates an answer based on this evidence.

### Why Llama? Why Groq?

**Llama 3.1** is Meta's open-source language model:
- Free to use (unlike GPT-4)
- 8 billion parameters (large enough to be smart, small enough to be fast)
- Good at following instructions

**Groq** is a cloud service that runs Llama:
- Extremely fast (special hardware called LPUs)
- Pay-per-use API (no expensive GPU needed)
- Simple to integrate

---

## Layer 2: NLI Verification (The Fact-Checker)

### The Problem with Layer 1

RAG helps, but the AI can still:
- Misread the evidence
- Add details not in the context
- Hallucinate despite having good evidence

We need a **second opinion**—an independent fact-checker.

### What is NLI?

**NLI** = Natural Language Inference

It's a classification task where you give the model two pieces of text:
- **Premise**: The evidence (what we know is true)
- **Hypothesis**: The claim to check (the AI's answer)

The model decides if the premise **supports** the hypothesis:

| Verdict | Meaning | Example |
|---------|---------|---------|
| **Entailment** | Premise supports hypothesis | Premise: "John is a doctor." Hypothesis: "John works in healthcare." ✓ |
| **Contradiction** | Premise contradicts hypothesis | Premise: "John is a doctor." Hypothesis: "John is unemployed." ✗ |
| **Neutral** | Can't tell either way | Premise: "John is a doctor." Hypothesis: "John likes pizza." ? |

### The NLI Model: RoBERTa-MNLI

**Model used:** `FacebookAI/roberta-large-mnli`

- **RoBERTa**: An improved version of BERT (a foundational AI model from Google)
- **Large**: 355 million parameters
- **MNLI**: Trained on the Multi-Genre Natural Language Inference dataset (433K examples)

This model outputs **probabilities**:
```
Contradiction: 5%
Neutral: 15%
Entailment: 80%  ← This is what we care about
```

The **entailment probability** (0-100%) tells us how much the evidence supports the AI's answer.

### How Verification Works

```
Evidence: "The University of Westminster was founded in 1838..."

AI's Answer: "Westminster was founded in 1838 as the Royal Polytechnic Institution."

RoBERTa says: 92% Entailment → Answer is likely correct!
```

```
Evidence: "The University of Westminster was founded in 1838..."

AI's Answer: "Westminster was founded in 1850 by Queen Victoria."

RoBERTa says: 8% Entailment → Hallucination detected!
```

---

## The Innovation: Adaptive Thresholds

### The Problem with Fixed Thresholds

Simple approach: "If entailment > 70%, it's verified."

But this ignores **how good our evidence was**:
- If we found perfect evidence (95% match), 70% entailment is suspicious
- If we found weak evidence (50% match), 70% entailment is actually impressive

### The Solution: Confidence-Weighted Thresholds

This system **adjusts the bar** based on evidence quality:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   Evidence Quality          Verification Mode           │
│   ─────────────────         ─────────────────           │
│   HIGH (≥ 75%)       →      LENIENT (need 70%)          │
│   LOW  (< 75%)       →      STRICT  (need 95%)          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**The Logic:**
- **Good evidence + AI agrees with it** → Probably correct (be lenient)
- **Weak evidence + AI agrees with it** → Suspicious, could be coincidence (be strict)

### Example Scenarios

| Retrieval Score | NLI Score | Mode | Threshold | Verdict |
|-----------------|-----------|------|-----------|---------|
| 90% (high) | 75% | LENIENT | 70% | ✅ VERIFIED |
| 50% (low) | 75% | STRICT | 95% | ❌ HALLUCINATION |
| 50% (low) | 96% | STRICT | 95% | ✅ VERIFIED |

---

## The Complete Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER QUESTION                            │
│              "When was Westminster founded?"                     │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    STEP 1: EMBED QUERY                           │
│         MiniLM converts question to 384 numbers                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    STEP 2: SEARCH (FAISS)                        │
│         Find most similar documents in knowledge base            │
│         Output: 2 documents + Retrieval Score (e.g., 88%)        │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    STEP 3: GENERATE (Llama)                      │
│         Send context + question to Llama 3.1                     │
│         Output: "Westminster was founded in 1838..."             │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    STEP 4: VERIFY (RoBERTa)                      │
│         Check if evidence supports the answer                    │
│         Output: Entailment Score (e.g., 91%)                     │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    STEP 5: ADAPTIVE VERDICT                      │
│         88% retrieval ≥ 75% pivot → LENIENT mode                 │
│         91% entailment ≥ 70% threshold → VERIFIED ✅              │
└──────────────────────────────────────────────────────────────────┘
```

---

## The Knowledge Base

This demo uses a small knowledge base with 6 paragraphs:

| Topic | Purpose |
|-------|---------|
| University of Westminster (3 paragraphs) | Main topic for testing |
| AI Hallucinations (2 paragraphs) | Secondary topic |
| Climate of Sri Lanka (1 paragraph) | **Distractor** - tests what happens when question doesn't match |

The **distractor** is clever: if someone asks about Sri Lanka's weather, the system should find that document. But if they ask about Westminster's weather, the system should show **low retrieval confidence** (evidence doesn't match well).

---

## Technologies Summary

| Component | Technology | Why This Choice |
|-----------|------------|-----------------|
| **Embeddings** | MiniLM-L6-v2 | Fast, lightweight, good quality |
| **Vector Search** | FAISS | Industry standard, very fast |
| **LLM** | Llama 3.1 8B | Open-source, free, capable |
| **LLM Hosting** | Groq | Fastest inference, simple API |
| **NLI Verifier** | RoBERTa-MNLI | High accuracy, well-established |
| **UI** | Streamlit | Quick Python web apps |

---

## Key Takeaways

1. **LLMs hallucinate** because they predict words, not facts
2. **RAG helps** by giving the AI evidence to work with
3. **NLI verification** provides a second opinion on accuracy
4. **Adaptive thresholds** make the system smarter by adjusting strictness based on evidence quality
5. **The combination** of RAG + NLI + adaptive thresholds is more robust than any single approach
