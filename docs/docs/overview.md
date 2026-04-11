---
sidebar_position: 1
title: Overview
---

# AFLHR Lite

**Adaptive Framework for LLM Hallucination Reduction — Lite Version**

A two-layer verification pipeline that combines Retrieval-Augmented Generation (RAG) with Natural Language Inference (NLI) to detect hallucinations in LLM outputs. The core innovation is **Confidence-Weighted CONLI (Cw-CONLI)**: the NLI verification threshold adapts dynamically based on retrieval confidence.

## Quick Start

```bash
git clone https://github.com/shaunyogeshwaran/Shaun_FYP.git
cd Shaun_FYP
make install        # installs pip + npm dependencies, creates .env
# Edit .env and add your GROQ_API_KEY (free at https://console.groq.com)
make start          # starts backend (:8000) + frontend (:5173) + docs (:4000)
```

Open **http://localhost:5173** to use the app.

## Requirements

| Requirement | Details |
|---|---|
| **Python** | 3.10+ with pip |
| **Node.js** | 18+ with npm |
| **RAM** | 24 GB recommended (ML models load into memory) |
| **Disk** | ~3 GB (models auto-download from HuggingFace on first run) |
| **GPU** | Optional — CUDA auto-detected, falls back to CPU |
| **Groq API key** | Optional — offline mode works without it |

## Make Targets

```bash
make start      # starts backend (8000) + frontend (5173) + docs (4000)
make stop       # stop all servers
make restart    # bounce all servers
make status     # check what's running
make install    # install all dependencies
make smoke      # smoke test (precompute 20 samples)
```

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Verify** | `/` | Enter a claim, adjust thresholds, see the full pipeline and verdict |
| **Explore** | `/explore` | Batch-run 7 pre-configured queries across domains |
| **How It Works** | `/about` | Visual walkthrough of the 4-stage pipeline |

## Troubleshooting

| Problem | Fix |
|---|---|
| `make install` fails on pip | Ensure Python 3.10+ is on your PATH |
| Backend won't start | Check logs: `tail /tmp/aflhr_backend.log` |
| Frontend won't start | Check logs: `tail /tmp/aflhr_frontend.log` |
| Port in use | `make stop` first, or kill the process on that port |
| Models downloading slowly | First run downloads ~3 GB from HuggingFace |
| MPS/Apple GPU segfault | Expected — system auto-disables MPS and uses CPU |
