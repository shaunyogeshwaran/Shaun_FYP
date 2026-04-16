---
sidebar_position: 4
title: API Reference
---

# API Reference

The FastAPI backend runs on port **8000** and serves both the React frontend and programmatic access.

## Endpoints

### `GET /api/health`

Health check returning engine loading status.

**Response:**
```json
{
  "status": "ok",
  "engine_v1_loaded": true,
  "engine_v2_loaded": true,
  "has_api_key": true
}
```

### `POST /api/verify`

Main verification endpoint. Runs the full pipeline: retrieval → generation → NLI → verdict.

**Request body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | *required* | The claim or question to verify |
| `pivot` | float | 0.75 | Pivot threshold for tiered Cw-CONLI |
| `strict_threshold` | float | 0.95 | Upper threshold (low retrieval confidence) |
| `lenient_threshold` | float | 0.70 | Lower threshold (high retrieval confidence) |
| `offline_mode` | bool | false | Skip LLM generation (use mock response) |
| `v2_mode` | bool | false | Enable v2 features (windowed NLI, decomposition, BGE) |

**Example:**

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "query": "When was the University of Westminster founded?",
    "v2_mode": true
  }'
```

**Response:**

```json
{
  "query": "When was the University of Westminster founded?",
  "retrieval": {
    "context": "The University of Westminster was founded in 1838...",
    "retrieval_score": 0.877,
    "raw_score": 0.754,
    "documents": ["..."],
    "indices": [0, 2]
  },
  "generation": "The University of Westminster was founded in 1838...",
  "nli_score": 0.883,
  "verdict": {
    "status": "VERIFIED",
    "mode": "LENIENT",
    "threshold": 0.70,
    "nli_score": 0.883,
    "retrieval_score": 0.877,
    "reasoning": "High retrieval confidence -> trusting evidence quality",
    "passed": true
  },
  "version": "v2",
  "nli_method": "decomposed",
  "n_claims": 2,
  "per_claim": [
    {"claim": "The University of Westminster was founded in 1838", "score": 0.91},
    {"claim": "It was originally the Royal Polytechnic Institution", "score": 0.88}
  ]
}
```

### `GET /api/knowledge-base`

Returns information about the loaded knowledge base.

**Response:**
```json
{
  "topics": [
    {"name": "University of Westminster", "passages": 3},
    {"name": "AI Hallucinations", "passages": 2},
    {"name": "Climate of Sri Lanka (Distractor)", "passages": 1}
  ],
  "total_passages": 6
}
```

### `GET /docs`

Auto-generated Swagger/OpenAPI documentation (provided by FastAPI).

## Running the API

```bash
make start          # starts the full stack
# or manually:
python -m uvicorn api:app --port 8000
```
