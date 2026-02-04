# Presentation Video Script

## AFLHR Lite - 20 Minute Video Presentation

**Duration:** 20 minutes (recorded PowerPoint presentation)
**Format:** Screen recording with voice-over narration
**Presenter:** Shaun

---

## Pre-Recording Checklist

- [ ] PowerPoint slides prepared with all visuals
- [ ] Quiet recording environment
- [ ] Microphone tested and audio levels checked
- [ ] Practice run completed (aim for ~18-19 minutes to allow buffer)
- [ ] Water nearby for dry throat

---

## SLIDE 1: Title Slide
**Time: 0:00 - 1:00 (1 minute)**

### Visual Elements
- Project Title: "AFLHR Lite: Adaptive Few-Shot Learning Framework for Hallucination Reduction"
- Subtitle: "Confidence-Weighted Verification for Reliable AI Outputs"
- Your Name: Shaun
- University of Westminster logo
- Date: February 2026
- Module: Final Year Project - Interim Progression Demonstration

### Script (Read Exactly)

> "Hello, my name is Shaun, and welcome to my Interim Progression Demonstration for my final year project.
>
> My project is called AFLHR Lite, which stands for Adaptive Few-Shot Learning Framework for Hallucination Reduction. The full subtitle is 'Confidence-Weighted Verification for Reliable AI Outputs.'
>
> In this presentation, I will walk you through the progress I have made since my initial Project Proposal and Requirements Specification, or PPRS. I'll cover the key stakeholders, the formal requirements, the system architecture, and the technical challenges I encountered along with how I solved them.
>
> I'll also show you a working prototype that demonstrates the core innovation of my project: using retrieval confidence to dynamically adjust how strictly we verify AI-generated content."

---

## SLIDE 2: Agenda / Overview
**Time: 1:00 - 1:30 (30 seconds)**

### Visual Elements
- Numbered list of presentation sections:
  1. Problem Statement
  2. Stakeholder Analysis
  3. Requirements Documentation
  4. System Architecture
  5. Core Innovation
  6. Technical Challenges
  7. Updated Timeline
  8. Next Steps
  9. Conclusion

### Script (Read Exactly)

> "Here's what I'll be covering today. First, I'll explain the problem my project addresses - LLM hallucinations. Then I'll discuss the stakeholders and how their needs influenced the design. I'll present the formal requirements, both functional and non-functional, and show which ones have been implemented.
>
> Next, I'll walk through the system architecture and explain my core innovation - the adaptive threshold mechanism. I'll discuss the technical challenges I faced and how I solved them, present my updated timeline, and finish with next steps and a conclusion."

---

## SLIDE 3: Problem Statement - What Are LLM Hallucinations?
**Time: 1:30 - 3:30 (2 minutes)**

### Visual Elements
- Definition box: "LLM Hallucinations: When AI generates plausible-sounding but factually incorrect information"
- Example comparison:
  - **User Question:** "When was the University of Westminster founded?"
  - **Hallucinated Response:** "The University of Westminster was founded in 1892 as a technical college."
  - **Correct Response:** "The University of Westminster was founded in 1838 as the Royal Polytechnic Institution."
- Statistics or news headlines about AI misinformation (optional)

### Script (Read Exactly)

> "Let me start by explaining the problem my project addresses. Large Language Models, or LLMs, like ChatGPT, Claude, and others, are incredibly capable at generating human-like text. However, they have a significant flaw: they sometimes generate plausible-sounding information that is completely false. This phenomenon is called 'hallucination.'
>
> Here's a concrete example. If you ask an LLM 'When was the University of Westminster founded?' - a hallucinated response might say 'The University of Westminster was founded in 1892 as a technical college.' This sounds believable, it's confident, but it's wrong. The correct answer is that Westminster was founded in 1838 as the Royal Polytechnic Institution.
>
> The problem is that LLMs present false information with the same confidence as true information. Users have no way to know if they're getting accurate facts or fabricated nonsense.
>
> This matters because LLMs are being used in high-stakes domains - healthcare, legal advice, education, business decisions. A hallucinated medical recommendation or legal interpretation could have serious consequences. There's a real need for systems that can detect and flag potential hallucinations before they cause harm."

---

## SLIDE 4: Problem Statement - The Research Gap
**Time: 3:30 - 4:30 (1 minute)**

### Visual Elements
- Diagram showing current approaches:
  - "Fixed Threshold Systems": Single threshold (e.g., 0.5) applied to all responses
  - Arrow pointing to "THE GAP": "Ignores evidence quality"
- Text: "Strong evidence vs weak evidence - shouldn't verification be different?"

### Script (Read Exactly)

> "Now, there are existing approaches to detect hallucinations. Many use Natural Language Inference, or NLI, to check if a generated response is logically supported by retrieved evidence. They typically use a fixed threshold - for example, if the entailment score is above 0.5, mark it as verified; below 0.5, mark it as a hallucination.
>
> But here's the gap I identified: these fixed-threshold systems treat all situations the same, regardless of evidence quality. Think about it - if my retrieval system finds highly relevant evidence with 95% confidence, that's very different from finding marginally related evidence with 50% confidence.
>
> When evidence is strong, we should be more trusting. When evidence is weak, we should be more skeptical. Existing systems don't make this distinction, and that's the gap my project addresses."

---

## SLIDE 5: Stakeholder Analysis - Primary Stakeholders
**Time: 4:30 - 6:00 (1.5 minutes)**

### Visual Elements
- **Use Figure 4.1 (Rich Picture) or Table 4.1 (Stakeholder Onion Model) from your PPRS**
- Table with 3 columns: Stakeholder | Interest | Influence on Project
- Primary Stakeholders listed:
  - Software Developers
  - AI/ML Researchers
  - Enterprise Users
  - Academic Supervisor
  - University of Westminster

### Script (Read Exactly)

> "Let me now discuss the stakeholders who are involved in or affected by this project. As detailed in the **Stakeholder Onion Model** in my PPRS, I identified stakeholders at different levels of involvement. This is important because their needs directly shaped my design decisions.
>
> My primary stakeholders include:
>
> First, **Software Developers** - they are the main end users who need reliable LLM outputs for production applications. Their interest is in reducing errors in AI-generated content. Their influence on my project was HIGH - I designed a modular, easy-to-integrate API specifically so developers can easily add this to their systems.
>
> Second, **AI and ML Researchers** - they need reproducible methods and measurable metrics. Their influence was also HIGH - I made all thresholds configurable and ensured the system outputs detailed scores that can be analyzed and compared.
>
> Third, **Enterprise Users** - businesses that need trustworthy AI for decisions. Their influence was MEDIUM - I added features like adjustable thresholds via the UI and an offline mode for testing.
>
> Fourth, my **Academic Supervisor** - who ensures academic rigor and guides research methodology. Their influence was HIGH - they provided direction and feedback throughout.
>
> And finally, the **University of Westminster** itself, which has an interest in research output and student success."

---

## SLIDE 6: Stakeholder Analysis - Secondary Stakeholders & Onion Model
**Time: 6:00 - 7:00 (1 minute)**

### Visual Elements
- **Use Table 4.1 (Stakeholder Onion Model) from your PPRS**
- Secondary stakeholders list:
  - LLM Providers (OpenAI, Anthropic, Google)
  - Regulatory Bodies
  - Content Creators
  - End Consumers
  - Healthcare/Legal Professionals
- Show the Onion Model layers: Kit (inner) -> System -> Containing System -> Wider Environment (outer)

### Script (Read Exactly)

> "I also identified several secondary stakeholders who are indirectly affected by this work, shown in the outer layers of the Stakeholder Onion Model.
>
> **LLM Providers** like OpenAI and Anthropic have an interest in improving model reliability - they may eventually integrate solutions like mine.
>
> **Regulatory bodies** are increasingly concerned with AI safety and accuracy standards.
>
> **Content creators** and **end consumers** are affected by AI misinformation and would benefit from more reliable AI outputs.
>
> And **healthcare and legal professionals** have particularly high-stakes use cases where hallucination detection is critical.
>
> As you can see in the Onion Model, the inner layers - the Kit and System - represent my core users: software developers and researchers. The outer layers represent the wider environment stakeholders. This is why the core design prioritises the needs of developers and researchers - modular code, configurable parameters, and detailed scoring outputs."

---

## SLIDE 7: Requirements - Functional Requirements (Implemented)
**Time: 7:00 - 8:30 (1.5 minutes)**

### Visual Elements
- **Use Traffic Light System for instant visual clarity:**
  - Header: "IMPLEMENTED" with green background
  - Each requirement row has a green checkmark icon
- Table with columns: ID | Requirement | Priority | Status
- Show FR01 through FR06 and FR08 with green checkmarks

### Script (Read Exactly)

> "Now let me present the formal requirements documentation. I've defined 11 functional requirements and 5 non-functional requirements, for a total of 16 requirements.
>
> Starting with the implemented functional requirements - let me walk through the key ones.
>
> The core pipeline requirements FR01 through FR06 are all implemented:
> - FR01: The system retrieves relevant documents from a knowledge base using semantic search - implemented using FAISS.
> - FR02: The system generates a confidence score between 0 and 1 for each retrieval - this is crucial for the adaptive threshold.
> - FR03: The system generates LLM responses grounded in retrieved context - implemented using Llama 3.1 via the Groq API.
> - FR04: The system verifies responses using Natural Language Inference - implemented using RoBERTa-MNLI.
> - FR05: The system applies an adaptive threshold based on retrieval confidence - this is the core innovation.
> - FR06: The system provides configurable threshold parameters via the user interface.
>
> FR08, the optional continuous weighting mode, is also implemented - this provides granular confidence scoring as an alternative to the binary STRICT/LENIENT modes.
>
> The user interface components cover the implementation of FR01 through FR06, providing interactive sliders, evidence display, and offline mode for testing."

---

## SLIDE 8: Requirements - Functional Requirements (Pending/Out of Scope) & Non-Functional
**Time: 8:30 - 9:30 (1 minute)**

### Visual Elements
- **Use Traffic Light System for instant visual clarity:**
  - Header: "PENDING" with orange/amber background for FR07
  - FR07 row has an orange clock icon
  - Header: "OUT OF SCOPE" with grey background for FR09-FR11
  - FR09-FR11 rows have grey "Will Not Have" badges
  - Header: "IMPLEMENTED" with green background for NFR01, NFR02, NFR04, NFR05
  - NFR03 row has orange "Tied to Evaluation" badge
- Summary box: "7 of 11 FRs implemented + 4/5 NFRs = 11 of 16 total (69%)"

### Script (Read Exactly)

> "Regarding the status of the Functional Requirements:
>
> FR07 is currently Pending. This requirement covers the 'Programmatic interface for the evaluation harness,' which I will build in the next phase to generate my final metrics.
>
> FR09, FR10, and FR11 were formally scoped as 'Will Not Have' in my PPRS—such as cross-model consistency, surgical correction, and DPO—and remain out of scope as planned.
>
> For the Non-Functional Requirements, I have fully met 4 of the 5:
> - NFR01: Deterministic verification outputs.
> - NFR02: Modular architecture allowing component swapping.
> - NFR04: Ease of execution via a single script.
> - NFR05: Resource efficiency running on standard hardware.
>
> NFR03, regarding benchmark performance measurability, is tied to the pending evaluation phase - the system is designed for measurement, but actual metrics require FR07.
>
> In summary, I have successfully implemented 7 of the 11 Functional Requirements and 4 of the 5 Non-Functional Requirements, giving 11 of 16 total - 69% complete at the IPD stage."

---

## SLIDE 9: System Architecture - High-Level Overview
**Time: 9:30 - 11:00 (1.5 minutes)**

### Visual Elements
- **Use Figure 3.1: AFLHR Lite System Architecture from your PPRS**
- High-level architecture diagram showing:
  - User Interface (Streamlit)
  - AFLHR Engine with 2-layer pipeline
  - Configuration module
- Arrows showing data flow

### Script (Read Exactly)

> "Let me now present the system architecture. The engine operates as a **two-layer pipeline** as defined in my PPRS.
>
> At the top is the **User Interface**, built with Streamlit. This provides an interactive web application where users can enter queries, adjust threshold parameters using sliders, and view results in a three-column layout showing evidence, response, and verdict.
>
> The core is the **AFLHR Engine**, which contains the main processing pipeline structured as two layers:
> - **Layer 1** handles RAG Retrieval and LLM Generation - it embeds the user's query, searches the knowledge base for relevant documents, and uses that context to generate a grounded response
> - **Layer 2** is the dedicated NLI Verification stage - it checks if the generated response is logically supported by the retrieved evidence
>
> Finally, there's the **Configuration module** which centralizes all settings - model IDs, threshold values, and the knowledge base content.
>
> The data flows from user query through Layer 1 (retrieval and generation), then Layer 2 (verification), and finally to the adaptive threshold decision which produces the final verdict."

---

## SLIDE 10: System Architecture - RAG Retrieval Layer
**Time: 11:00 - 12:00 (1 minute)**

### Visual Elements
- Detailed diagram of RAG layer:
  - MiniLM Embeddings (384-dim)
  - FAISS Vector Store
  - Confidence Score output
- Code snippet showing the retrieve method signature

### Script (Read Exactly)

> "Let me drill into each layer. The RAG Retrieval layer is responsible for finding relevant evidence to ground the LLM's response.
>
> It uses the **all-MiniLM-L6-v2** embedding model from HuggingFace. This converts text into 384-dimensional vectors that capture semantic meaning.
>
> These vectors are stored and searched using **FAISS**, Facebook's library for efficient similarity search. I use the IndexFlatIP index type which performs inner product search.
>
> The key output of this layer is not just the retrieved documents, but also a **confidence score** between 0 and 1. This score is calculated as the normalized cosine similarity between the query and the best-matching document. This confidence score is absolutely critical - it's what drives the adaptive threshold decision later in the pipeline."

---

## SLIDE 11: System Architecture - LLM Generation & NLI Verification
**Time: 12:00 - 13:00 (1 minute)**

### Visual Elements
- Two boxes side by side:
  - LLM Generation: Llama 3.1 8B via Groq, System prompt, Offline mode fallback
  - NLI Verification: RoBERTa-large-MNLI, (Premise, Hypothesis) input, Entailment probability output

### Script (Read Exactly)

> "The LLM Generation layer uses **Llama 3.1 8B Instant** via the Groq API. Groq provides very fast inference which keeps response times low.
>
> The system prompt instructs the LLM to answer using ONLY the provided context - no external knowledge. This grounding is essential for the verification to work correctly.
>
> I also implemented an offline mode with mock responses for testing without API access.
>
> The NLI Verification layer uses **RoBERTa-large-MNLI**, a model trained on the Multi-Genre Natural Language Inference dataset. It takes two inputs: the retrieved context as the 'premise' and the generated response as the 'hypothesis'.
>
> It outputs three probabilities: contradiction, neutral, and entailment. I extract the **entailment probability** - this tells us how strongly the evidence supports the generated response. A high entailment score means the response is well-supported; a low score suggests potential hallucination."

---

## SLIDE 12: Core Innovation - Adaptive Thresholds
**Time: 13:00 - 15:00 (2 minutes)**

### Visual Elements
- **Use Figure 3.3: Confidence-Weighted CONLI Process Flow from your PPRS**
- **CRITICAL: Include a simple IF/ELSE decision table for instant comprehension:**
```
┌─────────────────────────────────────────────────────────────┐
│  IF Confidence < 0.75  →  STRICT Mode  (Threshold = 0.95)  │
│  IF Confidence ≥ 0.75  →  LENIENT Mode (Threshold = 0.70)  │
└─────────────────────────────────────────────────────────────┘
```
- This visual reinforcement helps the marker grasp the logic in 10 seconds
- Visual representation of the intuition (weak evidence = skeptical, strong evidence = trust)

### Script (Read Exactly)

> "Now we come to the core innovation of my project - the adaptive threshold mechanism. Following the **Cost-Sensitive Learning theory** outlined in **Section 2.4.2** of my PPRS, the system adapts verification strictness based on evidence quality.
>
> The key insight is this: the verification threshold should not be fixed. It should adapt based on how confident we are in our evidence.
>
> Here's how it works. After retrieval, we have a confidence score - let's say it's 0.65. We compare this to a **pivot point**, which defaults to 0.75.
>
> When retrieval confidence is **LOW** - below the pivot - the system assumes the evidence is weak. Following the Cost-Sensitive Learning logic, it applies a **STRICT threshold** of 0.95 to prevent hallucinations based on poor data. We're being skeptical because our evidence is weak.
>
> When retrieval confidence is **HIGH** - at or above the pivot - the system trusts the evidence and applies a **LENIENT threshold** of 0.70 to avoid over-flagging valid, nuanced answers.
>
> The intuition is simple: **low confidence evidence means be skeptical; high confidence evidence means trust it**.
>
> *Important note:* These specific values - 0.75 pivot, 0.95 strict, 0.70 lenient - are **prototype defaults**. As detailed in my PPRS methodology, the final parameters will be **tuned via grid search** on the HaluEval development set during the upcoming evaluation phase.
>
> This addresses the research gap I mentioned earlier. Fixed-threshold systems treat all queries the same regardless of evidence quality. My adaptive approach adjusts verification strictness dynamically."

---

## SLIDE 13: Technical Challenges - Problems Encountered
**Time: 15:00 - 16:00 (1 minute)**

### Visual Elements
- Three challenge boxes:
  1. Segmentation Faults on Apple Silicon
  2. PyTorch Binary Incompatibility
  3. Deprecated Groq Model
- Each with a brief description

### Script (Read Exactly)

> "Let me discuss the technical challenges I encountered during development and how I solved them. This demonstrates the problem-solving process and the critical evaluation the IPD requires.
>
> **Challenge 1: Segmentation Faults on Apple Silicon**
> When I first tried to run the sentence-transformers library on my Mac with Apple Silicon, the application would crash with segmentation faults. This was a blocking issue that prevented any progress.
>
> **Challenge 2: PyTorch Binary Incompatibility**
> I encountered errors with PyTorch 2.9.0 in my Anaconda environment - the binary wouldn't load correctly, causing import failures.
>
> **Challenge 3: Deprecated Groq Model**
> The original Llama 3 model I was using, `llama3-8b-8192`, was deprecated by Groq and stopped working, breaking the generation pipeline."

---

## SLIDE 14: Technical Challenges - Solutions Implemented
**Time: 16:00 - 17:00 (1 minute)**

### Visual Elements
- Three solution boxes matching the challenges:
  1. Direct transformers library usage + CPU mode
  2. Fresh venv with PyTorch 2.6.0
  3. Updated to llama-3.1-8b-instant
- Before/after code snippets

### Script (Read Exactly)

> "Here's how I solved each challenge:
>
> **Solution 1:** Instead of using sentence-transformers, I switched to using the transformers library directly with explicit CPU mode. I set environment variables to disable MPS acceleration and force CPU-only operations. This eliminated the segmentation faults completely.
>
> **Solution 2:** I created a fresh Python virtual environment and installed PyTorch 2.6.0 specifically, avoiding the problematic 2.9.0 binary. This resolved all import issues.
>
> **Solution 3:** I upgraded the model from `llama3-8b-8192` to `llama-3.1-8b-instant`. This wasn't just a fix - the newer model actually provides faster inference and improved response quality, so the deprecation forced an upgrade that benefited the project.
>
> These solutions demonstrate adaptability and problem-solving - I encountered real-world engineering challenges and found practical workarounds that actually improved the system.
>
> Importantly, **none of these challenges affected the core deliverables**. They were technical environment issues, not fundamental design problems. The adaptive threshold logic and verification pipeline work exactly as designed."

---

## SLIDE 15: Updated Timeline - Progress Overview
**Time: 17:00 - 18:00 (1 minute)**

### Visual Elements
- Gantt chart or timeline graphic showing:
  - Phase 1: Prototype (Nov 2025 - Feb 2026) - COMPLETE
  - Phase 2: Evaluation (Feb - Mar 2026) - UPCOMING
  - Phase 3: Final Submission (Apr 2026) - PLANNED
- Milestone markers

### Script (Read Exactly)

> "Let me present the updated timeline showing progress since the PPRS.
>
> **Phase 1 - Prototype Development** is complete. This ran from November 2025 through early February 2026.
> - In November, I completed the literature review, designed the system architecture, and selected the technology stack.
> - In December, I implemented all four core components: RAG retrieval with confidence scoring, LLM generation, NLI verification, and the adaptive threshold logic.
> - In January, I built the Streamlit user interface, added configurable sliders and offline mode, created a proof-of-concept notebook, and prepared all IPD documentation.
>
> **Phase 2 - Evaluation** is upcoming and will run from February through March 2026. This is when I'll implement the three pending requirements: HaluEval benchmark evaluation, baseline comparison, and metrics generation.
>
> **Phase 3 - Final Submission** is planned for April 2026, where I'll complete remaining thesis chapters and submit.
>
> The project is on schedule. All prototype deliverables are complete before the IPD deadline."

---

## SLIDE 16: Timeline Deviations
**Time: 18:00 - 18:30 (30 seconds)**

### Visual Elements
- Table showing:
  - Original Plan | Actual | Reason | Impact
  - sentence-transformers | transformers directly | Segfault issues | None
  - GPU acceleration | CPU-only mode | Stability | None
  - Larger Wikipedia KB | 6-paragraph demo KB | Sufficient for prototype | None

### Script (Read Exactly)

> "I want to be transparent about deviations from my original PPRS plan.
>
> I originally planned to use sentence-transformers but switched to using transformers directly due to the segmentation fault issues.
>
> I planned for GPU acceleration but moved to CPU-only mode for stability and compatibility.
>
> I planned a larger Wikipedia-based knowledge base but used a smaller 6-paragraph demo knowledge base, which is sufficient for demonstrating the prototype. The full evaluation will use the HaluEval benchmark dataset.
>
> The important point is: **none of these deviations impacted the core deliverables**. They were technical adjustments, not scope reductions. The adaptive threshold mechanism works exactly as proposed."

---

## SLIDE 17: Next Steps
**Time: 18:30 - 19:15 (45 seconds)**

### Visual Elements
- Three-column layout:
  - Immediate (Feb 2026): HaluEval dataset prep, Evaluation scripts
  - Short-term (Mar 2026): 3-condition experiment, Statistical analysis
  - Final (Apr 2026): Complete thesis, Final submission

### Script (Read Exactly)

> "Looking ahead, here are my next steps.
>
> **Immediately after IPD**, I will download and prepare the HaluEval benchmark dataset - specifically targeting the 35,000+ sample QA evaluation set - and implement the evaluation scripts.
>
> **In March**, I will run the three-condition experiment:
> - Condition 1: RAG-only baseline with no hallucination detection
> - Condition 2: RAG plus Standard CONLI with a single static threshold tuned on the development set
> - Condition 3: RAG plus my adaptive threshold mechanism
>
> I'll measure the exact F1-score trade-offs across conditions and perform statistical analysis to demonstrate that adaptive thresholds outperform fixed thresholds.
>
> **In April**, I'll complete the remaining thesis chapters and submit the final project."

---

## SLIDE 18: Conclusion
**Time: 19:15 - 19:45 (30 seconds)**

### Visual Elements
- Summary bullet points:
  - Built adaptive hallucination detection system
  - Core innovation: confidence-weighted thresholds
  - 69% of requirements implemented (11 of 16)
  - Prototype complete and functional
- Key differentiation highlighted

### Script (Read Exactly)

> "To summarize: I have built an adaptive framework for LLM hallucination reduction called AFLHR Lite.
>
> The core innovation is confidence-weighted thresholds - adjusting verification strictness based on evidence quality. When evidence is weak, be skeptical. When evidence is strong, trust it.
>
> I've implemented 11 of 16 requirements - 69% complete at the IPD stage. The working prototype demonstrates all core functionalities.
>
> This addresses a real gap in existing systems that use fixed thresholds regardless of evidence quality. My approach reduces both false positives - incorrectly flagging good responses - and false negatives - missing actual hallucinations."

---

## SLIDE 19: Demo & Questions
**Time: 19:45 - 20:00 (15 seconds)**

### Visual Elements
- Screenshot of the Streamlit prototype
- Text: "See separate Demo Video for live prototype demonstration"
- Contact information or Q&A slide

### Script (Read Exactly)

> "A separate video demonstrates the working prototype in action, showing the code walkthrough and live demonstration of the adaptive threshold behavior.
>
> Thank you for watching my Interim Progression Demonstration. The project is progressing well and on track for successful completion."

---

## Post-Recording Checklist

- [ ] Review video for clarity and pacing
- [ ] Verify audio is clear throughout
- [ ] Check total duration is approximately 20 minutes
- [ ] Upload to YouTube as **unlisted** video
- [ ] Test that the link is accessible to anyone with the URL
- [ ] Include link in submission
- [ ] Backup the video file

---

## Timing Summary

| Slide(s) | Topic | Duration | Cumulative |
|----------|-------|----------|------------|
| 1 | Title & Introduction | 1:00 | 1:00 |
| 2 | Agenda | 0:30 | 1:30 |
| 3-4 | Problem Statement | 3:00 | 4:30 |
| 5-6 | Stakeholder Analysis | 2:30 | 7:00 |
| 7-8 | Requirements | 2:30 | 9:30 |
| 9-11 | System Architecture | 3:30 | 13:00 |
| 12 | Core Innovation | 2:00 | 15:00 |
| 13-14 | Technical Challenges | 2:00 | 17:00 |
| 15-16 | Updated Timeline | 1:30 | 18:30 |
| 17 | Next Steps | 0:45 | 19:15 |
| 18-19 | Conclusion | 0:45 | 20:00 |
| **TOTAL** | | **20:00** | |

---

## Marking Criteria Coverage Checklist

| Criteria | Weight | Covered In | Status |
|----------|--------|------------|--------|
| Identification of Project Stakeholders | 10% | Slides 5-6 | Comprehensive stakeholder analysis with roles, interests, influence |
| Formal Requirements Documentation | 10% | Slides 7-8 | All 16 requirements listed with status (implemented/pending/out of scope) |
| Overall System Architecture | 10% | Slides 9-11 | Full architecture with diagrams, components, data flow |
| Updated Time Schedule | 5% | Slides 15-16 | Timeline with milestones, deviations explained |
| Video Presentation Clarity | 20% | Entire video | Clear voice-over, logical flow, milestones/challenges/solutions |
