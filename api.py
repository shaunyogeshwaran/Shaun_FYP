"""
AFLHR Lite - FastAPI Backend
REST API wrapping AFLHREngine for the React frontend.
Supports both v1 (baseline) and v2 (decomposition + windowed NLI + BGE embeddings).

AI Disclosure: Development of this module was assisted by AI tools
for code structuring, debugging, and refactoring. The API design and endpoint
logic are the author's own work.
"""

import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
from pydantic import BaseModel, Field
from engine import AFLHREngine
from config import (
    DEFAULT_PIVOT,
    DEFAULT_STRICT_THRESHOLD,
    DEFAULT_LENIENT_THRESHOLD,
    GROQ_API_KEY,
    KNOWLEDGE_BASE,
)

app = FastAPI(title="AFLHR Lite API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html><head><title>AFLHR Lite API</title></head>
    <body style="font-family:system-ui;max-width:600px;margin:60px auto;color:#333">
    <h1>AFLHR Lite API v2</h1>
    <p>The backend is running. Open the frontend at
    <a href="http://localhost:5173">http://localhost:5173</a></p>
    <h3>Endpoints:</h3>
    <ul>
    <li><code>GET /api/health</code> — Health check</li>
    <li><code>POST /api/verify</code> — Verify a query (supports v2 mode)</li>
    <li><code>GET /api/knowledge-base</code> — Knowledge base info</li>
    <li><code>GET /docs</code> — Interactive API docs (Swagger)</li>
    </ul>
    </body></html>
    """


# Engine instances — v1 loaded at startup, v2 loaded on first v2 request
engine_v1: AFLHREngine | None = None
engine_v2: AFLHREngine | None = None
_v2_lock = threading.Lock()


@app.on_event("startup")
def startup():
    global engine_v1
    print("Loading AFLHR Engine (v1)...")
    engine_v1 = AFLHREngine()
    print("Engine v1 ready.")


def get_v2_engine():
    """Lazy-load v2 engine on first v2 request (thread-safe)."""
    global engine_v2
    if engine_v2 is not None:
        return engine_v2
    with _v2_lock:
        if engine_v2 is None:
            print("Loading AFLHR Engine (v2: windowed + decomposition + BGE)...")
            engine_v2 = AFLHREngine(
                use_windowed_nli=True,
                use_decomposition=True,
                use_calibration=False,  # T=10 at boundary — calibration hurts
                use_bge_embeddings=True,
            )
            print("Engine v2 ready.")
    return engine_v2


class VerifyRequest(BaseModel):
    query: str
    pivot: float = DEFAULT_PIVOT
    strict_threshold: float = DEFAULT_STRICT_THRESHOLD
    lenient_threshold: float = DEFAULT_LENIENT_THRESHOLD
    offline_mode: bool = False
    v2_mode: bool = False


class ClaimScore(BaseModel):
    claim: str
    score: float


class VerifyResponse(BaseModel):
    query: str
    retrieval: dict
    generation: str
    nli_score: float
    verdict: dict
    # v2 fields
    version: str = "v1"
    nli_method: str = "whole"
    n_claims: int = 1
    per_claim: list[ClaimScore] = Field(default_factory=list)


@app.post("/api/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    engine = get_v2_engine() if req.v2_mode else engine_v1

    # Run the standard pipeline (retrieve + generate + single-pass verify + verdict)
    result = engine.run_pipeline(
        query=req.query,
        pivot=req.pivot,
        strict_threshold=req.strict_threshold,
        lenient_threshold=req.lenient_threshold,
        offline_mode=req.offline_mode if GROQ_API_KEY else True,
    )

    # v2: also run decomposed verification for the per-claim breakdown
    nli_score = result["nli_score"]
    nli_method = "whole"
    n_claims = 1
    per_claim = []

    if req.v2_mode:
        premise = result["retrieval"]["context"]
        hypothesis = result["generation"]
        decomp = engine.verify_decomposed(premise=premise, hypothesis=hypothesis)
        nli_score = decomp["score"]
        nli_method = "decomposed"
        n_claims = decomp["n_claims"]
        per_claim = [
            ClaimScore(claim=c["claim"], score=round(c["score"], 4))
            for c in decomp["per_claim"]
        ]
        # Recompute verdict with decomposed score
        result["verdict"] = engine.calculate_verdict(
            retrieval_score=result["retrieval"]["retrieval_score"],
            nli_score=nli_score,
            pivot=req.pivot,
            strict_threshold=req.strict_threshold,
            lenient_threshold=req.lenient_threshold,
        )

    return VerifyResponse(
        query=result["query"],
        retrieval=result["retrieval"],
        generation=result["generation"],
        nli_score=nli_score,
        verdict=result["verdict"],
        version="v2" if req.v2_mode else "v1",
        nli_method=nli_method,
        n_claims=n_claims,
        per_claim=per_claim,
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engine_v1_loaded": engine_v1 is not None,
        "engine_v2_loaded": engine_v2 is not None,
        "has_api_key": bool(GROQ_API_KEY),
    }


@app.get("/api/knowledge-base")
def get_knowledge_base():
    return {
        "topics": [
            {"name": "University of Westminster", "passages": 3},
            {"name": "AI Hallucinations", "passages": 2},
            {"name": "Climate of Sri Lanka (Distractor)", "passages": 1},
        ],
        "total_passages": len(KNOWLEDGE_BASE),
    }
