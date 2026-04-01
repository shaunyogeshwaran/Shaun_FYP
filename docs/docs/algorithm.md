---
sidebar_position: 3
title: Algorithm
---

# Cw-CONLI Algorithm

## Research Question

> Should retrieval quality influence how strict NLI verification is?

Standard CONLI (Microsoft, 2024) uses a **fixed threshold** — the same verification strictness regardless of whether the retrieved evidence is highly relevant or barely related. Cw-CONLI introduces **confidence-weighted thresholds** that adapt based on retrieval score.

## Experimental Conditions

| Condition | Name | Description |
|-----------|------|-------------|
| **C1** | RAG-only | No NLI verification (baseline) |
| **C2** | Static CONLI | Fixed threshold regardless of retrieval confidence |
| **C3** | Cw-CONLI | Adaptive threshold weighted by retrieval confidence |

## Threshold Functions

C3 is implemented as three mathematical variants:

### Tiered (Step Function)

```
T(rs) = T_strict   if rs < pivot
         T_lenient  otherwise
```

A binary step controlled by the pivot parameter. Simple and interpretable but discontinuous at the pivot.

**Parameters:** `pivot`, `T_strict`, `T_lenient`

### Square Root (Continuous)

```
T(rs) = T_strict − (T_strict − T_lenient) · √rs
```

A smooth, monotonically decreasing function. The concave shape means modest retrieval improvements produce meaningful threshold relaxation.

**Parameters:** `T_strict`, `T_lenient`

### Sigmoid (Logistic)

```
T(rs) = T_lenient + (T_strict − T_lenient) / (1 + exp(k · (rs − pivot)))
```

An S-shaped logistic transition. Parameter `k` controls steepness. Most flexible but largest hyperparameter space.

**Parameters:** `T_strict`, `T_lenient`, `pivot`, `k`

## Classification Rule

For all variants, the verdict logic is identical:

```
if nli_score >= T(rs):
    verdict = VERIFIED
else:
    verdict = HALLUCINATION
```

## Relationship to Prior Work

| | Microsoft CoNLI | AFLHR Lite (Cw-CONLI) |
|---|---|---|
| NLI engine | GPT-3.5/GPT-4 via prompting | RoBERTa-large-MNLI (local) |
| Retrieval | None — source document given | FAISS + sentence embeddings |
| Detection | Sentence → entity-level (Azure NER) | Sentence decomposition + sliding-window NLI |
| Mitigation | GPT rewrites flagged text | Detection only |
| Infrastructure | Azure OpenAI + Azure Text Analytics | Runs locally on CPU |
| Novel addition | — | Confidence-weighted adaptive thresholds |

## v2 Engineering Improvements

| Improvement | Problem Addressed | Approach |
|---|---|---|
| Sliding-window NLI | RoBERTa 512-token limit truncates long premises | Split into overlapping 400-token windows, take max entailment |
| Claim decomposition | Whole-response NLI misses partial hallucinations | Split into sentences, verify each, take min score |
| BGE embeddings | MiniLM-L6-v2 is outdated (2021) | Upgrade to BAAI/bge-small-en-v1.5 |
| Temperature scaling | Raw NLI softmax outputs may be uncalibrated | Investigated (Guo et al. 2017); T=10.0 at boundary — disabled |
