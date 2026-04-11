# Video Demo Script — AFLHR Lite (Cw-CONLI)

**Target length:** 3-5 minutes
**Recording:** Screen recording with voiceover (QuickTime or OBS)
**Resolution:** 1080p minimum

---

## Scene 1: Introduction (30s)
- Show the terminal: `make start`
- Wait for "Engine v1 ready" message
- Open browser to `http://localhost:5173`
- **Say:** "This is AFLHR Lite, a hallucination detection system that uses Confidence-Weighted CONLI to verify LLM responses against retrieved evidence."

## Scene 2: Verify Page — Successful Verification (60s)
- Type query: "When was the University of Westminster founded?"
- Click Verify
- Show the pipeline animation (Retrieve → Generate → Verify → Verdict)
- Point out: retrieval confidence gauge (~0.88), the retrieved passages, the LLM response
- Point out: NLI entailment score, threshold bar, **VERIFIED** verdict stamp
- **Say:** "The system retrieves relevant passages, generates a response via Llama-3.1, and verifies it using RoBERTa-MNLI. High retrieval confidence triggers lenient mode — the system trusts the evidence."

## Scene 3: Verify Page — Hallucination Detection (45s)
- Type query: "Who is the current president of the United States?"
- Click Verify
- Show low retrieval score (~0.50), **HALLUCINATION** verdict
- Point out: the reasoning text explains why it was flagged
- **Say:** "For off-topic queries, retrieval confidence is low, triggering strict mode. The NLI score is below threshold, correctly flagging this as a hallucination."

## Scene 4: v2 Mode — Per-Claim Decomposition (45s)
- Toggle "v2 Mode" on
- Re-run the Westminster query
- Show the per-claim breakdown panel appearing
- Point out: individual claim scores, minimum score used as final NLI score
- **Say:** "v2 mode decomposes the response into individual claims and verifies each one separately. The minimum score catches partial hallucinations that whole-response NLI might miss."

## Scene 5: Threshold Controls (30s)
- Adjust the pivot slider
- Show how the verdict changes between STRICT and LENIENT modes
- **Say:** "The adaptive threshold adjusts based on retrieval confidence. Users can tune the pivot, strict, and lenient thresholds to control the sensitivity."

## Scene 6: Explore Page — Batch Testing (45s)
- Navigate to the Explore page
- Click "Run All Queries"
- Show the progress and results table filling in
- Point out: aggregate stats (Verified/Hallucinated counts, averages)
- **Say:** "The Explore page runs batch verification across multiple domains, showing how the system handles different query types."

## Scene 7: Closing (15s)
- Show the About page briefly (pipeline diagram, tech stack)
- **Say:** "AFLHR Lite runs entirely on CPU with sub-second response times. The full experiment pipeline evaluated 20,000 samples from HaluEval across three conditions."

---

## Recording Tips
- Use dark theme (looks better on screen)
- Close other browser tabs
- Make sure the API is running (`make status`)
- Record in a quiet environment for clear voiceover
- Export as MP4, 1080p
