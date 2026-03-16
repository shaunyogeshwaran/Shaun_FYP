"""
AFLHR Lite - FastAPI Backend
REST API wrapping AFLHREngine for the React frontend.
"""

import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from engine import AFLHREngine
from config import (
    DEFAULT_PIVOT,
    DEFAULT_STRICT_THRESHOLD,
    DEFAULT_LENIENT_THRESHOLD,
    GROQ_API_KEY,
    KNOWLEDGE_BASE,
)

app = FastAPI(title="AFLHR Lite API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html><head><title>AFLHR Lite API</title></head>
    <body style="font-family:system-ui;max-width:600px;margin:60px auto;color:#333">
    <h1>AFLHR Lite API</h1>
    <p>The backend is running. Open the frontend at
    <a href="http://localhost:3001">http://localhost:3001</a></p>
    <h3>Endpoints:</h3>
    <ul>
    <li><code>GET /api/health</code> — Health check</li>
    <li><code>POST /api/verify</code> — Verify a query</li>
    <li><code>GET /api/knowledge-base</code> — Knowledge base info</li>
    <li><code>GET /docs</code> — Interactive API docs (Swagger)</li>
    </ul>
    </body></html>
    """


# Load engine once at startup
engine: AFLHREngine | None = None


@app.on_event("startup")
def startup():
    global engine
    print("Loading AFLHR Engine...")
    engine = AFLHREngine()
    print("Engine ready.")


class VerifyRequest(BaseModel):
    query: str
    pivot: float = DEFAULT_PIVOT
    strict_threshold: float = DEFAULT_STRICT_THRESHOLD
    lenient_threshold: float = DEFAULT_LENIENT_THRESHOLD
    offline_mode: bool = False


class VerifyResponse(BaseModel):
    query: str
    retrieval: dict
    generation: str
    nli_score: float
    verdict: dict


@app.post("/api/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    result = engine.run_pipeline(
        query=req.query,
        pivot=req.pivot,
        strict_threshold=req.strict_threshold,
        lenient_threshold=req.lenient_threshold,
        offline_mode=req.offline_mode if GROQ_API_KEY else True,
    )
    return VerifyResponse(
        query=result["query"],
        retrieval=result["retrieval"],
        generation=result["generation"],
        nli_score=result["nli_score"],
        verdict=result["verdict"],
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engine_loaded": engine is not None,
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
