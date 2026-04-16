# AFLHR Lite - Video Demo Script

**Target length:** 5-7 minutes
**Format:** Screen capture with voiceover
**Setup:** Run `make start` before recording. Have browser open to http://localhost:5173

---

## INTRO (30s)

> "This is AFLHR Lite — a hallucination detection system built as my final year project. It uses a two-layer pipeline: RAG retrieval followed by NLI verification, with an adaptive threshold called Confidence-Weighted CONLI, or Cw-CONLI, that adjusts its scrutiny based on how confident the system is in the retrieved evidence."

**On screen:** Show the landing page with the shield icon and "Verify a claim" prompt.

---

## 1. VERIFY PAGE — Basic Query (90s)

> "Let me demonstrate the core functionality. I'll start with a straightforward question."

**Action:** Click the suggested query "When was the University of Westminster founded?"

> "The pipeline runs in four stages — you can see each one light up as it progresses. First, it retrieves relevant passages from the knowledge base using FAISS vector search. Then, it sends the query and context to Llama 3.1 via the Groq API to generate a response. Next, RoBERTa-large-MNLI performs Natural Language Inference to check whether the response is actually supported by the evidence. Finally, the adaptive verdict decides if the response is verified or a hallucination."

**On screen:** Wait for results to appear. Point out the three result panels.

> "On the left, you can see the retrieval confidence gauge and the retrieved passages. The retrieval score is above the pivot, so the system uses LENIENT mode — it trusts the evidence. In the middle is the LLM's generated response. On the right, the NLI entailment score and the verdict. The threshold bar shows where the NLI score sits relative to the threshold. This response is verified."

---

## 2. CONTROL PANEL — Threshold Adjustment (60s)

> "What makes Cw-CONLI different from standard approaches is the adaptive threshold. Let me open the control panel to show how this works."

**Action:** Open the Control Panel if collapsed. Adjust the sliders.

> "There are three parameters. The pivot point determines where the system switches between strict and lenient mode. The strict threshold is applied when retrieval confidence is low — the system is sceptical. The lenient threshold is applied when retrieval is strong — the system trusts the evidence."

**Action:** Drag the strict threshold higher (e.g. 0.99) to show the verdict flip.

> "Watch what happens if I set a very high strict threshold — now even a well-supported response gets flagged. This demonstrates the core idea: the threshold is not hardcoded, it adapts to evidence quality."

**Action:** Reset thresholds to defaults (Pivot: 0.75, Strict: 0.95, Lenient: 0.70).

---

## 3. v2 MODE — Claim Decomposition (60s)

> "Version 2 of the pipeline adds three improvements. Let me enable v2 mode."

**Action:** Check the "v2 Mode" checkbox in the control panel.

> "v2 enables sliding-window NLI, which handles long documents that exceed RoBERTa's 512-token limit, sentence-level claim decomposition which verifies each claim independently, and an upgraded BGE embedding model."

**Action:** Run a query like "What happened at the Royal Polytechnic Institution in 1896?" or type a multi-sentence claim.

> "Now you can see the per-claim breakdown in the verification panel. Each sentence in the response is scored individually, and the system takes the minimum — a weakest-link approach. If even one claim is unsupported, the overall score drops. This catches partial hallucinations that whole-response NLI would miss."

---

## 4. OFFLINE MODE (30s)

> "The system also works without an API key. Let me enable offline mode."

**Action:** Check "Offline Mode" in the control panel. Run a query.

> "In offline mode, the LLM generation is replaced with a mock response, but the RAG retrieval and NLI verification still run fully. This means the verification pipeline can be demonstrated and tested without any external API dependency."

---

## 5. EXPLORE PAGE — Batch Comparison (60s)

**Action:** Navigate to the Explore page via the header.

> "The Explore page runs multiple queries in batch to compare how the pipeline handles different scenarios."

**Action:** Click "Run All Queries".

> "There are seven pre-configured queries: three about the University of Westminster, two about AI hallucinations, one about Sri Lanka's climate which is a distractor topic in our knowledge base, and one completely off-topic question about the US president."

**On screen:** Wait for results table to populate. Point out the stats bar.

> "You can see the aggregate stats at the top — how many were verified versus flagged as hallucinations, and the average retrieval and NLI scores. The results table shows each query with its category, retrieval confidence, NLI score, and verdict. Notice how the off-topic query has a low retrieval score and gets flagged, while questions matching our knowledge base score highly."

**Action:** Toggle v2 mode on and run again to show comparison.

> "I can also toggle v2 mode here to compare the v1 and v2 pipelines side by side."

---

## 6. HOW IT WORKS PAGE (45s)

**Action:** Navigate to the "How It Works" page.

> "This page provides a visual walkthrough of the four-stage pipeline. Each stage shows the model used, its purpose, and the output it produces."

**Action:** Scroll through the pipeline stages.

> "It also explains the three threshold variants that were evaluated — tiered, square root, and sigmoid — showing their formulas and trade-offs. At the bottom is the technical stack: the embedding models, FAISS for vector search, RoBERTa for NLI, and Llama via Groq for generation."

---

## 7. THEME TOGGLE + DOCS (15s)

**Action:** Click the theme toggle button in the header.

> "The interface supports both dark and light themes, optimised for projector visibility."

**Action:** Click the "Docs" link in the header.

> "There's also a full documentation site with the API reference, architecture details, and experiment results."

---

## WRAP-UP (30s)

**Action:** Navigate back to the Verify page.

> "To summarise: AFLHR Lite is a two-layer hallucination detection pipeline where the verification threshold adapts based on retrieval confidence. Version 2 adds sliding-window NLI for long documents, claim decomposition for partial hallucinations, and BGE embeddings for better retrieval. The system was evaluated on 20,000 HaluEval samples and the results are documented in the thesis. Thank you for watching."

---

## Recording Tips

- Use a clean browser window (no bookmarks bar, no other tabs)
- Resolution: 1920x1080 or 2560x1440
- Use dark theme for recording (more visually striking)
- Speak slowly and clearly — voiceover is assessed
- Keep mouse movements deliberate, don't rush between actions
- Total target: 5-7 minutes (screen capture + voiceover is sufficient)
- Tools: QuickTime Player (built-in Mac screen recording) or OBS
