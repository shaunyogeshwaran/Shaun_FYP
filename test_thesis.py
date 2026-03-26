#!/usr/bin/env python3
"""
AFLHR Lite — Functional & Non-Functional Testing Suite
Produces thesis-ready results for Chapter 8 sections 8.7 and 8.8.

Usage:
    python test_thesis.py              # Run all tests (API must be running on :8000)
    python test_thesis.py --skip-v2    # Skip v2 tests (faster, avoids v2 engine load)

Requires: requests, tabulate
    pip install requests tabulate
"""

import argparse
import json
import sys
import time

import requests

API_BASE = "http://localhost:8000"

# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def api_get(path, timeout=30):
    """GET request to the API."""
    return requests.get(f"{API_BASE}{path}", timeout=timeout)


def api_post(path, data, timeout=120):
    """POST request to the API."""
    return requests.post(f"{API_BASE}{path}", json=data, timeout=timeout)


def timed_post(path, data, timeout=120):
    """POST request returning (response, elapsed_ms)."""
    t0 = time.perf_counter()
    resp = requests.post(f"{API_BASE}{path}", json=data, timeout=timeout)
    elapsed = (time.perf_counter() - t0) * 1000
    return resp, elapsed


class TestResult:
    def __init__(self, test_id, description, requirement, expected, actual, passed, notes=""):
        self.test_id = test_id
        self.description = description
        self.requirement = requirement
        self.expected = expected
        self.actual = actual
        self.passed = passed
        self.notes = notes


# ═══════════════════════════════════════════════════════════════════════════
# FUNCTIONAL TESTS (Section 8.7)
# ═══════════════════════════════════════════════════════════════════════════

def run_functional_tests(skip_v2=False):
    """Run all functional test cases. Returns list of TestResult."""
    results = []

    # ── FR-01: Health Check Endpoint ─────────────────────────────────────
    try:
        resp = api_get("/api/health")
        data = resp.json()
        passed = (
            resp.status_code == 200
            and data.get("status") == "ok"
            and data.get("engine_v1_loaded") is True
            and "has_api_key" in data
        )
        results.append(TestResult(
            "FT-01", "Health endpoint returns system status",
            "FR-01", "200 OK with engine status and API key flag",
            f"status={data.get('status')}, v1={data.get('engine_v1_loaded')}, key={data.get('has_api_key')}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-01", "Health endpoint returns system status",
                                  "FR-01", "200 OK", str(e), False))

    # ── FR-02: Knowledge Base Endpoint ───────────────────────────────────
    try:
        resp = api_get("/api/knowledge-base")
        data = resp.json()
        passed = (
            resp.status_code == 200
            and data.get("total_passages") == 6
            and len(data.get("topics", [])) == 3
        )
        results.append(TestResult(
            "FT-02", "Knowledge base endpoint returns corpus metadata",
            "FR-02", "3 topics, 6 total passages",
            f"{len(data.get('topics',[]))} topics, {data.get('total_passages')} passages",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-02", "Knowledge base metadata",
                                  "FR-02", "3 topics, 6 passages", str(e), False))

    # ── FR-03: Retrieval — relevant evidence returned ────────────────────
    try:
        resp = api_post("/api/verify", {"query": "When was the University of Westminster founded?", "offline_mode": True})
        data = resp.json()
        docs = data.get("retrieval", {}).get("documents", [])
        context = data.get("retrieval", {}).get("context", "")
        score = data.get("retrieval", {}).get("retrieval_score", 0)
        has_westminster = "Westminster" in context or any("Westminster" in str(d) for d in docs)
        passed = resp.status_code == 200 and has_westminster and score > 0.5
        results.append(TestResult(
            "FT-03", "Retrieval returns relevant evidence for in-domain query",
            "FR-03", "Context contains 'Westminster', retrieval score > 0.5",
            f"score={score:.4f}, Westminster found={has_westminster}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-03", "Retrieval returns relevant evidence",
                                  "FR-03", "Relevant docs returned", str(e), False))

    # ── FR-04: Retrieval — lower score for off-topic query ──────────────
    try:
        # Use a completely unrelated query outside the knowledge base domains
        resp = api_post("/api/verify", {"query": "How do tectonic plates cause earthquakes in Japan?", "offline_mode": True})
        data = resp.json()
        score = data.get("retrieval", {}).get("retrieval_score", 1)
        # Also compare with in-domain score to show relative ranking
        resp_in = api_post("/api/verify", {"query": "When was Westminster founded?", "offline_mode": True})
        in_score = resp_in.json().get("retrieval", {}).get("retrieval_score", 0)
        passed = resp.status_code == 200 and score < in_score
        results.append(TestResult(
            "FT-04", "Off-topic query retrieval score lower than in-domain query",
            "FR-03", "Off-topic retrieval < in-domain retrieval",
            f"off_topic={score:.4f}, in_domain={in_score:.4f}, gap={in_score - score:.4f}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-04", "Low confidence for off-topic",
                                  "FR-03", "Off-topic < in-domain", str(e), False))

    # ── FR-05: LLM Generation (online) ───────────────────────────────────
    try:
        resp = api_post("/api/verify", {"query": "When was the University of Westminster founded?", "offline_mode": False})
        data = resp.json()
        gen = data.get("generation", "")
        passed = resp.status_code == 200 and len(gen) > 20 and "mock" not in gen.lower()
        results.append(TestResult(
            "FT-05", "LLM generates a substantive response (online mode)",
            "FR-04", "Non-empty response > 20 chars, not a mock",
            f"len={len(gen)}, starts='{gen[:60]}...'",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-05", "LLM generates response",
                                  "FR-04", "Substantive response", str(e), False))

    # ── FR-06: Offline mode uses mock response ───────────────────────────
    try:
        resp = api_post("/api/verify", {"query": "What is AI?", "offline_mode": True})
        data = resp.json()
        gen = data.get("generation", "")
        passed = resp.status_code == 200 and ("mock" in gen.lower() or "offline" in gen.lower())
        results.append(TestResult(
            "FT-06", "Offline mode returns mock response",
            "FR-05", "Response indicates mock/offline generation",
            f"contains_mock={'mock' in gen.lower()}, contains_offline={'offline' in gen.lower()}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-06", "Offline mock response",
                                  "FR-05", "Mock response", str(e), False))

    # ── FR-07: NLI verification produces entailment score ────────────────
    try:
        resp = api_post("/api/verify", {"query": "When was the University of Westminster founded?", "offline_mode": True})
        data = resp.json()
        nli = data.get("nli_score", -1)
        passed = resp.status_code == 200 and 0 <= nli <= 1
        results.append(TestResult(
            "FT-07", "NLI verification produces score in [0, 1]",
            "FR-06", "0 ≤ nli_score ≤ 1",
            f"nli_score={nli:.4f}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-07", "NLI score range",
                                  "FR-06", "0 ≤ score ≤ 1", str(e), False))

    # ── FR-08: Verdict contains required fields ──────────────────────────
    try:
        resp = api_post("/api/verify", {"query": "When was the University of Westminster founded?", "offline_mode": True})
        data = resp.json()
        verdict = data.get("verdict", {})
        has_fields = all(k in verdict for k in ["status", "passed", "mode", "threshold", "reasoning"])
        status_valid = verdict.get("status") in ("VERIFIED", "HALLUCINATION")
        passed = resp.status_code == 200 and has_fields and status_valid
        results.append(TestResult(
            "FT-08", "Verdict contains status, passed, mode, threshold, reasoning",
            "FR-07", "All verdict fields present, status is VERIFIED or HALLUCINATION",
            f"status={verdict.get('status')}, fields={list(verdict.keys())}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-08", "Verdict structure",
                                  "FR-07", "Complete verdict", str(e), False))

    # ── FR-09: Adaptive thresholds — strict vs lenient ───────────────────
    # Cw-CONLI logic: retrieval >= pivot → LENIENT (trust evidence),
    #                  retrieval <  pivot → STRICT (be skeptical)
    try:
        # High retrieval + low pivot → retrieval >= pivot → LENIENT mode
        resp1 = api_post("/api/verify", {
            "query": "When was the University of Westminster founded?",
            "offline_mode": True,
            "pivot": 0.3, "strict_threshold": 0.95, "lenient_threshold": 0.50
        })
        d1 = resp1.json()
        mode1 = d1.get("verdict", {}).get("mode", "")
        retr1 = d1.get("retrieval", {}).get("retrieval_score", 0)

        # Force pivot above all retrieval scores → retrieval < pivot → STRICT mode
        resp2 = api_post("/api/verify", {
            "query": "When was the University of Westminster founded?",
            "offline_mode": True,
            "pivot": 0.99, "strict_threshold": 0.95, "lenient_threshold": 0.50
        })
        d2 = resp2.json()
        mode2 = d2.get("verdict", {}).get("mode", "")
        retr2 = d2.get("retrieval", {}).get("retrieval_score", 0)

        passed = mode1 == "LENIENT" and mode2 == "STRICT"
        results.append(TestResult(
            "FT-09", "Adaptive threshold switches between STRICT and LENIENT modes",
            "FR-08", "retrieval >= pivot → LENIENT, retrieval < pivot → STRICT",
            f"retr={retr1:.2f},pivot=0.3→{mode1}; retr={retr2:.2f},pivot=0.99→{mode2}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-09", "Adaptive threshold modes",
                                  "FR-08", "Mode switching", str(e), False))

    # ── FR-10: Custom thresholds are applied ─────────────────────────────
    try:
        resp = api_post("/api/verify", {
            "query": "What is AI?",
            "offline_mode": True,
            "pivot": 0.01, "strict_threshold": 0.99, "lenient_threshold": 0.99
        })
        data = resp.json()
        # With threshold 0.99, almost everything should be HALLUCINATION
        verdict = data.get("verdict", {}).get("status", "")
        threshold = data.get("verdict", {}).get("threshold", -1)
        passed = resp.status_code == 200 and threshold >= 0.98
        results.append(TestResult(
            "FT-10", "Custom thresholds are respected in verdict calculation",
            "FR-08", "Threshold ≥ 0.98 when strict=0.99, lenient=0.99",
            f"threshold={threshold:.4f}, verdict={verdict}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-10", "Custom thresholds applied",
                                  "FR-08", "Threshold respected", str(e), False))

    # ── FR-11: v1 response structure ─────────────────────────────────────
    try:
        resp = api_post("/api/verify", {"query": "What is AI?", "offline_mode": True, "v2_mode": False})
        data = resp.json()
        passed = (
            resp.status_code == 200
            and data.get("version") == "v1"
            and data.get("nli_method") == "whole"
            and data.get("n_claims") == 1
            and data.get("per_claim") == []
        )
        results.append(TestResult(
            "FT-11", "v1 mode returns whole-response NLI with no per-claim breakdown",
            "FR-09", "version=v1, method=whole, n_claims=1, per_claim=[]",
            f"version={data.get('version')}, method={data.get('nli_method')}, claims={data.get('n_claims')}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-11", "v1 response structure",
                                  "FR-09", "v1 defaults", str(e), False))

    # ── FR-12 to FR-15: v2-specific tests ────────────────────────────────
    if not skip_v2:
        print("  Loading v2 engine (first request may take ~15s)...")
        try:
            resp = api_post("/api/verify", {
                "query": "When was the University of Westminster founded?",
                "offline_mode": True, "v2_mode": True
            }, timeout=180)
            data = resp.json()

            # FR-12: v2 returns decomposed NLI
            passed = (
                data.get("version") == "v2"
                and data.get("nli_method") == "decomposed"
                and data.get("n_claims", 0) >= 1
            )
            results.append(TestResult(
                "FT-12", "v2 mode uses decomposed NLI verification",
                "FR-10", "version=v2, method=decomposed, n_claims ≥ 1",
                f"version={data.get('version')}, method={data.get('nli_method')}, claims={data.get('n_claims')}",
                passed,
            ))

            # FR-13: Per-claim breakdown present
            per_claim = data.get("per_claim", [])
            all_have_fields = all("claim" in c and "score" in c for c in per_claim)
            all_scores_valid = all(0 <= c["score"] <= 1 for c in per_claim)
            passed = len(per_claim) >= 1 and all_have_fields and all_scores_valid
            results.append(TestResult(
                "FT-13", "v2 per-claim breakdown contains claim text and score",
                "FR-10", "Each claim has 'claim' (str) and 'score' (0-1)",
                f"{len(per_claim)} claims, all_valid={all_have_fields and all_scores_valid}",
                passed,
            ))

            # FR-14: v2 NLI score is minimum of claim scores (decomposition logic)
            if per_claim:
                min_claim = min(c["score"] for c in per_claim)
                nli = data.get("nli_score", -1)
                # Allow small floating point tolerance
                passed = abs(nli - min_claim) < 0.01
                results.append(TestResult(
                    "FT-14", "v2 NLI score equals minimum per-claim score",
                    "FR-10", "nli_score ≈ min(per_claim scores)",
                    f"nli={nli:.4f}, min_claim={min_claim:.4f}, diff={abs(nli-min_claim):.4f}",
                    passed,
                ))
            else:
                results.append(TestResult("FT-14", "v2 min-claim logic",
                                          "FR-10", "nli = min(claims)", "No claims returned", False))

        except Exception as e:
            for tid in ("FT-12", "FT-13", "FT-14"):
                results.append(TestResult(tid, "v2 test", "FR-10", "v2 features", str(e), False))

        # FR-15: v2 handles in-domain query correctly
        try:
            resp = api_post("/api/verify", {
                "query": "What types of AI hallucinations exist?",
                "offline_mode": True, "v2_mode": True
            }, timeout=120)
            data = resp.json()
            nli = data.get("nli_score", 0)
            retr = data.get("retrieval", {}).get("retrieval_score", 0)
            passed = resp.status_code == 200 and retr > 0.3 and nli > 0
            results.append(TestResult(
                "FT-15", "v2 produces valid scores for AI hallucination domain query",
                "FR-10", "retrieval > 0.3, nli > 0 for in-domain query",
                f"retrieval={retr:.4f}, nli={nli:.4f}",
                passed,
            ))
        except Exception as e:
            results.append(TestResult("FT-15", "v2 in-domain query",
                                      "FR-10", "Valid scores", str(e), False))
    else:
        print("  Skipping v2 tests (--skip-v2)")
        for tid, desc in [("FT-12","v2 decomposed NLI"), ("FT-13","v2 per-claim"), ("FT-14","v2 min-claim"), ("FT-15","v2 in-domain")]:
            results.append(TestResult(tid, desc, "FR-10", "Skipped", "Skipped", None, "v2 tests skipped"))

    # ── FR-16: Invalid request returns error ─────────────────────────────
    try:
        resp = api_post("/api/verify", {"not_a_query": "bad"})
        passed = resp.status_code == 422  # Pydantic validation error
        results.append(TestResult(
            "FT-16", "Invalid request body returns 422 validation error",
            "FR-11", "HTTP 422 for missing required 'query' field",
            f"status_code={resp.status_code}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-16", "Invalid request handling",
                                  "FR-11", "422 error", str(e), False))

    # ── FR-17: API root serves info page ─────────────────────────────────
    try:
        resp = api_get("/")
        passed = resp.status_code == 200 and "AFLHR" in resp.text
        results.append(TestResult(
            "FT-17", "Root endpoint serves API info page",
            "FR-12", "200 OK with HTML containing 'AFLHR'",
            f"status={resp.status_code}, has_aflhr={'AFLHR' in resp.text}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-17", "Root endpoint",
                                  "FR-12", "Info page", str(e), False))

    # ── FR-18: Swagger docs accessible ───────────────────────────────────
    try:
        resp = api_get("/docs")
        passed = resp.status_code == 200
        results.append(TestResult(
            "FT-18", "Swagger/OpenAPI documentation accessible at /docs",
            "FR-12", "200 OK at /docs",
            f"status={resp.status_code}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("FT-18", "Swagger docs",
                                  "FR-12", "200 at /docs", str(e), False))

    return results


# ═══════════════════════════════════════════════════════════════════════════
# NON-FUNCTIONAL TESTS (Section 8.8)
# ═══════════════════════════════════════════════════════════════════════════

def run_nonfunctional_tests(skip_v2=False):
    """Run non-functional test cases. Returns list of TestResult."""
    results = []

    # ── NFR-01: Response Time — v1 online ────────────────────────────────
    print("  NFR-01: Measuring v1 online response time (3 runs)...")
    latencies_v1 = []
    for i in range(3):
        try:
            _, elapsed = timed_post("/api/verify", {
                "query": "When was the University of Westminster founded?",
                "offline_mode": False
            }, timeout=120)
            latencies_v1.append(elapsed)
        except Exception:
            pass

    if latencies_v1:
        avg_ms = sum(latencies_v1) / len(latencies_v1)
        max_ms = max(latencies_v1)
        passed = avg_ms < 30000  # 30 seconds for CPU-based ML pipeline
        results.append(TestResult(
            "NFT-01", "v1 online response time (3-run average)",
            "NFR-01", "Average response < 30s for CPU-based ML pipeline",
            f"avg={avg_ms:.0f}ms, max={max_ms:.0f}ms, runs={len(latencies_v1)}",
            passed,
        ))
    else:
        results.append(TestResult("NFT-01", "v1 response time",
                                  "NFR-01", "< 30s avg", "All requests failed", False))

    # ── NFR-02: Response Time — offline mode ─────────────────────────────
    print("  NFR-02: Measuring offline mode response time (3 runs)...")
    latencies_off = []
    for i in range(3):
        try:
            _, elapsed = timed_post("/api/verify", {
                "query": "What is AI?",
                "offline_mode": True
            })
            latencies_off.append(elapsed)
        except Exception:
            pass

    if latencies_off:
        avg_ms = sum(latencies_off) / len(latencies_off)
        passed = avg_ms < 15000  # Should be faster without Groq API call
        results.append(TestResult(
            "NFT-02", "Offline mode response time (3-run average)",
            "NFR-01", "Average response < 15s (no LLM API call)",
            f"avg={avg_ms:.0f}ms, max={max(latencies_off):.0f}ms",
            passed,
        ))
    else:
        results.append(TestResult("NFT-02", "Offline response time",
                                  "NFR-01", "< 15s avg", "All requests failed", False))

    # ── NFR-03: Response Time — v2 mode ──────────────────────────────────
    if not skip_v2:
        print("  NFR-03: Measuring v2 response time (3 runs)...")
        latencies_v2 = []
        for i in range(3):
            try:
                _, elapsed = timed_post("/api/verify", {
                    "query": "When was the University of Westminster founded?",
                    "offline_mode": True, "v2_mode": True
                }, timeout=180)
                latencies_v2.append(elapsed)
            except Exception:
                pass

        if latencies_v2:
            avg_ms = sum(latencies_v2) / len(latencies_v2)
            passed = avg_ms < 60000  # v2 has extra decomposition overhead
            results.append(TestResult(
                "NFT-03", "v2 mode response time (3-run average, offline)",
                "NFR-01", "Average response < 60s (decomposition + windowed NLI on CPU)",
                f"avg={avg_ms:.0f}ms, max={max(latencies_v2):.0f}ms",
                passed,
            ))
        else:
            results.append(TestResult("NFT-03", "v2 response time",
                                      "NFR-01", "< 60s avg", "All requests failed", False))
    else:
        results.append(TestResult("NFT-03", "v2 response time",
                                  "NFR-01", "Skipped", "Skipped", None, "v2 tests skipped"))

    # ── NFR-04: Accuracy — verified claim detection ──────────────────────
    print("  NFR-04: Testing accuracy on known verifiable query...")
    try:
        resp = api_post("/api/verify", {
            "query": "When was the University of Westminster founded?",
            "offline_mode": False,
            "pivot": 0.75, "strict_threshold": 0.50, "lenient_threshold": 0.30
        })
        data = resp.json()
        retr = data.get("retrieval", {}).get("retrieval_score", 0)
        nli = data.get("nli_score", 0)
        verdict = data.get("verdict", {}).get("status", "")
        # With lenient thresholds and an in-domain query, should verify
        passed = retr > 0.5 and nli > 0.1 and verdict == "VERIFIED"
        results.append(TestResult(
            "NFT-04", "System verifies factually supported in-domain claim",
            "NFR-02", "In-domain query → VERIFIED with retrieval > 0.5",
            f"retrieval={retr:.4f}, nli={nli:.4f}, verdict={verdict}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("NFT-04", "Verified claim accuracy",
                                  "NFR-02", "VERIFIED for in-domain", str(e), False))

    # ── NFR-05: Accuracy — hallucination detection ───────────────────────
    print("  NFR-05: Testing hallucination detection on off-topic query...")
    try:
        resp = api_post("/api/verify", {
            "query": "Who is the current president of the United States?",
            "offline_mode": False,
            "pivot": 0.75, "strict_threshold": 0.95, "lenient_threshold": 0.70
        })
        data = resp.json()
        retr = data.get("retrieval", {}).get("retrieval_score", 0)
        verdict = data.get("verdict", {}).get("status", "")
        # Off-topic query with default thresholds should flag as hallucination
        passed = retr < 0.5 and verdict == "HALLUCINATION"
        results.append(TestResult(
            "NFT-05", "System flags off-topic query as hallucination",
            "NFR-02", "Off-topic → HALLUCINATION with retrieval < 0.5",
            f"retrieval={retr:.4f}, verdict={verdict}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("NFT-05", "Hallucination detection",
                                  "NFR-02", "HALLUCINATION for off-topic", str(e), False))

    # ── NFR-06: Reproducibility — same query → same scores ───────────────
    print("  NFR-06: Testing reproducibility (same query twice)...")
    try:
        payload = {"query": "What are AI hallucinations?", "offline_mode": True}
        r1 = api_post("/api/verify", payload).json()
        r2 = api_post("/api/verify", payload).json()
        score1 = r1.get("nli_score", -1)
        score2 = r2.get("nli_score", -2)
        retr1 = r1.get("retrieval", {}).get("retrieval_score", -1)
        retr2 = r2.get("retrieval", {}).get("retrieval_score", -2)
        passed = abs(score1 - score2) < 0.001 and abs(retr1 - retr2) < 0.001
        results.append(TestResult(
            "NFT-06", "Identical queries produce identical scores (deterministic)",
            "NFR-03", "NLI and retrieval scores differ by < 0.001 across runs",
            f"nli_diff={abs(score1-score2):.6f}, retr_diff={abs(retr1-retr2):.6f}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("NFT-06", "Reproducibility",
                                  "NFR-03", "Deterministic scores", str(e), False))

    # ── NFR-07: Robustness — handles empty query ─────────────────────────
    print("  NFR-07: Testing robustness with edge-case inputs...")
    try:
        resp = api_post("/api/verify", {"query": "", "offline_mode": True})
        # Should either return a valid response or a handled error, not crash
        passed = resp.status_code in (200, 422)
        results.append(TestResult(
            "NFT-07", "System handles empty query without crashing",
            "NFR-04", "Returns 200 (with low scores) or 422 (validation), no 500",
            f"status_code={resp.status_code}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("NFT-07", "Empty query handling",
                                  "NFR-04", "No crash", str(e), False))

    # ── NFR-08: Robustness — handles very long query ─────────────────────
    try:
        long_q = "What is AI? " * 200  # ~2400 chars
        resp = api_post("/api/verify", {"query": long_q, "offline_mode": True})
        passed = resp.status_code in (200, 422)
        results.append(TestResult(
            "NFT-08", "System handles very long query (2400+ chars) without crashing",
            "NFR-04", "Returns valid response or validation error, no 500",
            f"status_code={resp.status_code}, query_len={len(long_q)}",
            passed,
        ))
    except Exception as e:
        results.append(TestResult("NFT-08", "Long query handling",
                                  "NFR-04", "No crash", str(e), False))

    # ── NFR-09: Concurrent request handling ──────────────────────────────
    print("  NFR-09: Testing sequential request consistency...")
    try:
        queries = [
            "When was Westminster founded?",
            "What types of AI hallucinations exist?",
            "What is the climate of Sri Lanka?",
        ]
        all_ok = True
        for q in queries:
            r = api_post("/api/verify", {"query": q, "offline_mode": True})
            if r.status_code != 200:
                all_ok = False
                break
        results.append(TestResult(
            "NFT-09", "System handles multiple sequential requests correctly",
            "NFR-05", "3 sequential queries all return 200 OK",
            f"all_ok={all_ok}",
            all_ok,
        ))
    except Exception as e:
        results.append(TestResult("NFT-09", "Sequential requests",
                                  "NFR-05", "All 200 OK", str(e), False))

    # ── NFR-10: CORS enabled ─────────────────────────────────────────────
    try:
        resp = requests.options(
            f"{API_BASE}/api/verify",
            headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
            timeout=10,
        )
        has_cors = "access-control-allow-origin" in {k.lower() for k in resp.headers}
        results.append(TestResult(
            "NFT-10", "CORS headers present for frontend cross-origin requests",
            "NFR-06", "Access-Control-Allow-Origin header present",
            f"cors_header_present={has_cors}",
            has_cors,
        ))
    except Exception as e:
        results.append(TestResult("NFT-10", "CORS enabled",
                                  "NFR-06", "CORS headers", str(e), False))

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════════

def print_report(title, results):
    """Print a formatted test report."""
    print(f"\n{'═' * 80}")
    print(f"  {title}")
    print(f"{'═' * 80}\n")

    # Table header
    print(f"{'ID':<8} {'Description':<58} {'Result':<8}")
    print(f"{'─' * 8} {'─' * 58} {'─' * 8}")

    for r in results:
        if r.passed is None:
            status = "SKIP"
        elif r.passed:
            status = "PASS"
        else:
            status = "FAIL"
        desc = r.description[:58]
        print(f"{r.test_id:<8} {desc:<58} {status:<8}")

    # Summary
    total = len([r for r in results if r.passed is not None])
    passed = len([r for r in results if r.passed is True])
    failed = len([r for r in results if r.passed is False])
    skipped = len([r for r in results if r.passed is None])

    print(f"\n{'─' * 80}")
    if total > 0:
        rate = (passed / total) * 100
        print(f"  Total: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}  |  Pass Rate: {rate:.1f}%")
    else:
        print(f"  Total: 0  |  All tests skipped")
    print(f"{'─' * 80}")

    return total, passed, failed, skipped


def print_detailed(results):
    """Print detailed results for each test."""
    print(f"\n{'─' * 80}")
    print("  DETAILED RESULTS")
    print(f"{'─' * 80}")
    for r in results:
        status = "SKIP" if r.passed is None else ("PASS" if r.passed else "FAIL")
        print(f"\n  [{status}] {r.test_id}: {r.description}")
        print(f"    Requirement: {r.requirement}")
        print(f"    Expected:    {r.expected}")
        print(f"    Actual:      {r.actual}")
        if r.notes:
            print(f"    Notes:       {r.notes}")


def save_json(functional, nonfunctional, filename="results/test_thesis_results.json"):
    """Save results as JSON for thesis reference."""
    def to_dict(r):
        return {
            "test_id": r.test_id,
            "description": r.description,
            "requirement": r.requirement,
            "expected": r.expected,
            "actual": r.actual,
            "passed": r.passed,
            "notes": r.notes,
        }

    data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "functional_tests": [to_dict(r) for r in functional],
        "nonfunctional_tests": [to_dict(r) for r in nonfunctional],
        "summary": {
            "functional": {
                "total": len([r for r in functional if r.passed is not None]),
                "passed": len([r for r in functional if r.passed is True]),
                "failed": len([r for r in functional if r.passed is False]),
            },
            "nonfunctional": {
                "total": len([r for r in nonfunctional if r.passed is not None]),
                "passed": len([r for r in nonfunctional if r.passed is True]),
                "failed": len([r for r in nonfunctional if r.passed is False]),
            },
        },
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {filename}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="AFLHR Lite — Thesis Testing Suite")
    parser.add_argument("--skip-v2", action="store_true", help="Skip v2-specific tests")
    args = parser.parse_args()

    print("AFLHR Lite — Functional & Non-Functional Testing Suite")
    print(f"Target: {API_BASE}")
    print(f"Time:   {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Pre-flight check
    try:
        r = api_get("/api/health")
        health = r.json()
        print(f"Health: v1={'loaded' if health.get('engine_v1_loaded') else 'NOT loaded'}, "
              f"v2={'loaded' if health.get('engine_v2_loaded') else 'not loaded'}, "
              f"key={'present' if health.get('has_api_key') else 'MISSING'}")
    except Exception:
        print("ERROR: Cannot reach API at", API_BASE)
        print("Start the backend first: make start")
        sys.exit(1)

    # Run tests
    print(f"\n{'━' * 80}")
    print("  SECTION 8.7: FUNCTIONAL TESTING")
    print(f"{'━' * 80}")
    functional = run_functional_tests(skip_v2=args.skip_v2)
    ft_total, ft_pass, ft_fail, ft_skip = print_report("FUNCTIONAL TEST RESULTS", functional)

    print(f"\n{'━' * 80}")
    print("  SECTION 8.8: NON-FUNCTIONAL TESTING")
    print(f"{'━' * 80}")
    nonfunctional = run_nonfunctional_tests(skip_v2=args.skip_v2)
    nft_total, nft_pass, nft_fail, nft_skip = print_report("NON-FUNCTIONAL TEST RESULTS", nonfunctional)

    # Detailed output
    print_detailed(functional + nonfunctional)

    # Overall summary
    total = ft_total + nft_total
    passed = ft_pass + nft_pass
    print(f"\n{'━' * 80}")
    print(f"  OVERALL: {passed}/{total} tests passed ({(passed/total*100):.1f}%)" if total else "  No tests run")
    print(f"  Functional: {ft_pass}/{ft_total} ({(ft_pass/ft_total*100):.1f}%)" if ft_total else "")
    print(f"  Non-Functional: {nft_pass}/{nft_total} ({(nft_pass/nft_total*100):.1f}%)" if nft_total else "")
    print(f"{'━' * 80}")

    # Save JSON
    save_json(functional, nonfunctional)

    return 0 if (ft_fail + nft_fail) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
