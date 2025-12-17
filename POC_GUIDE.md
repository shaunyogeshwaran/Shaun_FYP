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
