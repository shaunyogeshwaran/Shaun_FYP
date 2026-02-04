# LLM Instructions: Presentation Video Assistance

## Purpose of This Document

This document provides comprehensive context for any LLM (Large Language Model) assistant helping with the IPD (Interim Progression Demonstration) presentation video. It contains all information needed to provide accurate, detailed assistance with the 20-minute presentation.

**Use this document when:** Creating slides, refining the script, practicing delivery, answering questions about presentation content, or improving any aspect of the presentation.

---

## Project Overview

### Project Title
**AFLHR Lite: Adaptive Few-Shot Learning Framework for Hallucination Reduction**

### Subtitle
Confidence-Weighted Verification for Reliable AI Outputs

### Presenter
Shaun - Final Year Student, University of Westminster

### Assignment Details
- **Assignment:** Interim Progression Demonstration (IPD)
- **Weight:** 15% of final grade
- **Duration:** 20 minutes (recorded video presentation)
- **Deadline:** 05 February 2026 at 13:00
- **Format:** PowerPoint presentation recorded with voice-over narration
- **Upload:** YouTube as unlisted video OR OneDrive with accessible link

---

## Marking Criteria (CRITICAL - Must Cover All)

The presentation is marked against these specific criteria. **Every single criterion must be explicitly addressed.**

### 1. Identification of Project Stakeholders (10%)

**What markers are looking for:**
- Comprehensive identification of ALL key stakeholders
- Clear explanation of their roles
- Clear explanation of their interests
- Clear explanation of their influence on the project's development

**How to satisfy this criterion:**

Present the following stakeholders with their roles, interests, and influence:

**Primary Stakeholders:**

| Stakeholder | Role | Interest | Influence on Project |
|-------------|------|----------|---------------------|
| Software Developers | End Users | Need reliable LLM outputs for production applications; want to reduce errors in AI-generated content | **HIGH** - Primary beneficiaries; their needs drove the modular API design (AFLHREngine class) |
| AI/ML Researchers | End Users | Advancing hallucination detection methods; publishing reproducible research | **HIGH** - Shape research direction; their needs drove configurable thresholds and detailed scoring outputs |
| Enterprise Users | End Users | Trustworthy AI for business decisions; compliance with accuracy standards | **MEDIUM** - Drive adoption; their needs drove adjustable thresholds via UI and offline mode |
| LLM Providers (OpenAI, Anthropic, Google) | Technology Partners | Improving model reliability; reducing liability from hallucinations | **MEDIUM** - May integrate solutions; provide API access |
| Academic Supervisor | Project Oversight | Ensuring academic rigor; guiding research methodology | **HIGH** - Direct assessment; provides feedback and direction |
| University of Westminster | Institution | Research output; student success; reputation in AI research | **MEDIUM** - Provides resources; sets academic standards |

**Secondary Stakeholders:**

| Stakeholder | Interest | Impact |
|-------------|----------|--------|
| Content Creators | Affected by AI misinformation; need accurate AI assistance | Indirect beneficiaries |
| End Consumers | Receive LLM-generated content; trust in AI systems | Ultimate beneficiaries |
| Regulatory Bodies | AI safety standards; accountability in AI systems | May influence future requirements |
| Healthcare/Legal Professionals | Critical accuracy requirements; high-stakes decisions | High-value use case |
| Educational Institutions | AI in education; academic integrity | Benefit from reliable AI tools |

**Stakeholder Onion Model (from PPRS Table 4.1):**
```
┌─────────────────────────────────────────────────────────────┐
│                    WIDER ENVIRONMENT                         │
│  (Regulatory Bodies, Content Creators, End Consumers)        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                 CONTAINING SYSTEM                        ││
│  │  (LLM Providers, Healthcare/Legal Professionals)         ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │                    SYSTEM                            │││
│  │  │  (Enterprise Users, Academic Supervisor, University) │││
│  │  │  ┌─────────────────────────────────────────────────┐│││
│  │  │  │                    KIT                           ││││
│  │  │  │  (Software Developers, AI/ML Researchers)        ││││
│  │  │  └─────────────────────────────────────────────────┘│││
│  │  └─────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**IMPORTANT:** Use the Stakeholder Onion Model terminology from your PPRS, NOT "Influence Matrix". Reference Figure 4.1 (Rich Picture) and Table 4.1 from your PPRS.

**Key talking points for this section:**
1. Reference the **Stakeholder Onion Model** from your PPRS explicitly
2. Primary users (Kit layer) are developers and researchers who need reliable LLM verification
3. Developers influenced the modular, easy-to-integrate design
4. Researchers influenced the configurable, measurable system
5. Academic supervisor ensured rigorous research approach
6. Future stakeholders include enterprise users as the system matures

**Visual Requirements for Slides 5-6:**
- Use **Figure 4.1 (Rich Picture)** from PPRS
- Use **Table 4.1 (Stakeholder Onion Model)** from PPRS

---

### 2. Formal Requirements Documentation (10%)

**What markers are looking for:**
- Complete and well-organised list of functional requirements
- Complete and well-organised list of non-functional requirements
- Presented in a structured manner
- Supporting the project's design and development process
- **Must clearly indicate which requirements are IMPLEMENTED vs PENDING**
- All requirements must be measurable
- All requirements must be aligned with project aims and objectives

**How to satisfy this criterion:**

**Functional Requirements - IMPLEMENTED (7/11):**

| ID | Requirement | Priority | Status | Evidence |
|----|-------------|----------|--------|----------|
| FR01 | System shall retrieve relevant documents from knowledge base using semantic search | Must Have | IMPLEMENTED | engine.py:retrieve() using FAISS |
| FR02 | System shall generate a confidence score (0-1) for each retrieval operation | Must Have | IMPLEMENTED | Normalized cosine similarity |
| FR03 | System shall generate LLM responses grounded in retrieved context | Must Have | IMPLEMENTED | engine.py:generate() using Groq API |
| FR04 | System shall verify generated responses using Natural Language Inference (NLI) | Must Have | IMPLEMENTED | engine.py:verify() using RoBERTa-MNLI |
| FR05 | System shall apply adaptive threshold based on retrieval confidence | Must Have | IMPLEMENTED | engine.py:calculate_verdict() |
| FR06 | System shall provide configurable threshold parameters via user interface | Must Have | IMPLEMENTED | Streamlit sliders in sidebar |
| FR08 | System shall support optional continuous weighting mode | Should Have | IMPLEMENTED | Granular confidence scoring alternative to binary modes |

**Functional Requirements - PENDING (1/11):**

| ID | Requirement | Priority | Status | Target |
|----|-------------|----------|--------|--------|
| FR07 | System shall provide programmatic interface for evaluation harness | Must Have | PENDING | Evaluation phase |

**Functional Requirements - OUT OF SCOPE (3/11 - "Will Not Have" per PPRS):**

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| FR09 | Cross-model consistency checking | Won't Have | OUT OF SCOPE | Formally scoped out in PPRS |
| FR10 | Surgical correction of hallucinations | Won't Have | OUT OF SCOPE | Formally scoped out in PPRS |
| FR11 | Direct Preference Optimization (DPO) | Won't Have | OUT OF SCOPE | Formally scoped out in PPRS |

**Non-Functional Requirements - IMPLEMENTED (4/5):**

| ID | Requirement | Priority | Status | Evidence |
|----|-------------|----------|--------|----------|
| NFR01 | Deterministic verification outputs | Must Have | IMPLEMENTED | Same input produces same verdict |
| NFR02 | Modular architecture allowing component swapping | Must Have | IMPLEMENTED | Separate config.py, engine.py, app.py |
| NFR04 | Ease of execution via single script | Must Have | IMPLEMENTED | `streamlit run app.py` |
| NFR05 | Resource efficiency on standard hardware | Must Have | IMPLEMENTED | CPU mode, no dedicated GPU required |

**Non-Functional Requirements - TIED TO EVALUATION (1/5):**

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| NFR03 | Performance measurable on HaluEval benchmark | Must Have | TIED TO EVALUATION | Requires FR07 (evaluation harness) to generate metrics |

**Summary for presentation:**

| Category | Total | Implemented | Pending/Tied | Out of Scope |
|----------|-------|-------------|--------------|--------------|
| Functional Requirements | 11 | 7 (64%) | 1 (FR07) | 3 (FR09-FR11) |
| Non-Functional Requirements | 5 | 4 (80%) | 1 (NFR03) | 0 |
| **Overall** | **16** | **11 (69%)** | **2** | **3** |

**Key talking points:**
1. 69% of requirements implemented at IPD stage (11 of 16)
2. FR07 (evaluation harness) is pending for the evaluation phase
3. NFR03 (benchmark measurability) is tied to FR07 - system is designed for measurement, but actual metrics require the evaluation harness
4. FR09-FR11 were formally scoped as "Will Not Have" in PPRS - remain out of scope as planned
5. Requirements are aligned with the project objective of adaptive hallucination detection

**Visual Requirements for Slides 7-8 (Traffic Light System):**
- Use clear visual indicators that markers can see instantly:
  - **IMPLEMENTED** header with green background + green checkmark icons
  - **PENDING** header with orange/amber background + orange clock icons
- The words "Implemented" and "Pending" must appear explicitly as headers

---

### 3. Overall System Architecture (10%)

**What markers are looking for:**
- Comprehensive presentation of system architecture
- Conceptual diagrams
- User interfaces
- Structure should be well-defined
- Structure should be coherent
- Structure should be aligned with project's requirements and objectives

**How to satisfy this criterion:**

**High-Level Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE                                │
│                          (Streamlit - app.py)                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐ │
│  │  Query Input   │  │    Sliders     │  │     Results Display        │ │
│  │                │  │  - Pivot       │  │  ┌────────┬────────┬─────┐ │ │
│  │  [Text Field]  │  │  - Strict      │  │  │Evidence│Response│Verd.│ │ │
│  │                │  │  - Lenient     │  │  └────────┴────────┴─────┘ │ │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AFLHR ENGINE (engine.py)                         │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              LAYER 1: RAG RETRIEVAL + LLM GENERATION              │  │
│  │  MiniLM Embeddings → FAISS Search → Confidence Score (0-1)       │  │
│  │  Llama 3.1 8B (via Groq) → Grounded Response                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                   LAYER 2: NLI VERIFICATION                       │  │
│  │         RoBERTa-MNLI - Entailment Probability (0-1)               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │           ADAPTIVE THRESHOLD DECISION (Core Innovation)           │  │
│  │  IF retrieval_confidence < PIVOT: threshold = STRICT (0.95)       │  │
│  │  ELSE: threshold = LENIENT (0.70)                                 │  │
│  │  VERDICT = (NLI_score >= threshold) ? VERIFIED : HALLUCINATION    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       CONFIGURATION (config.py)                          │
│   Models: MiniLM, RoBERTa-MNLI, Llama 3.1                               │
│   Thresholds: Pivot=0.75, Strict=0.95, Lenient=0.70                     │
│   Knowledge Base: 6 curated paragraphs                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Component Details:**

| Component | Technology | Purpose |
|-----------|------------|---------|
| User Interface | Streamlit | Interactive web application |
| Embedding Model | all-MiniLM-L6-v2 | 384-dimensional text embeddings |
| Vector Store | FAISS (IndexFlatIP) | Fast similarity search |
| LLM Provider | Groq API | Fast inference |
| Generator Model | Llama 3.1 8B Instant | Response generation |
| NLI Model | RoBERTa-large-MNLI | Entailment classification |
| Configuration | Python module | Centralized settings |

**Data Flow:**

1. User enters query
2. Query embedded to 384-dim vector
3. FAISS searches for top-2 similar documents
4. Confidence score calculated from similarity
5. LLM generates response grounded in context
6. NLI model calculates entailment probability
7. Adaptive threshold selected based on confidence
8. Verdict determined by comparing NLI score to threshold
9. Results displayed in 3-column layout

**Key talking points:**
1. Two-layer pipeline architecture as defined in PPRS
2. Layer 1 handles RAG retrieval and LLM generation; Layer 2 is dedicated NLI verification
3. Confidence score from retrieval drives the adaptive decision
4. User interface allows real-time parameter adjustment
5. Design aligns with requirements (modular, configurable, visual feedback)

**Visual Requirements for Architecture Slides:**
- **Slide 9:** Use **Figure 3.1: AFLHR Lite System Architecture** from PPRS
- **Slide 12:** Use **Figure 3.3: Confidence-Weighted CONLI Process Flow** from PPRS
- Using exact diagrams from documentation reinforces that you are building what you designed

---

### 4. Updated Time Schedule (5%)

**What markers are looking for:**
- Presentation of an updated time schedule
- Includes all major tasks
- Includes milestones
- Includes deadlines
- Explanation of any deviations from the original timeline
- Explanation of the impact of those deviations on the project

**How to satisfy this criterion:**

**Timeline Overview:**

```
PPRS Submission          IPD Deadline            Final Submission
    │                        │                        │
    ▼                        ▼                        ▼
────┬────────────────────────┬────────────────────────┬────
    │   PHASE 1: PROTOTYPE   │   PHASE 2: EVALUATION  │
    │      (Completed)       │      (Upcoming)        │
    │                        │                        │
Nov 2025              Feb 5, 2026              Apr 2026
```

**Phase 1: Prototype Development (COMPLETED)**

| Month | Tasks | Status |
|-------|-------|--------|
| Nov 2025 | Literature review, Architecture design, Technology selection | COMPLETE |
| Dec 2025 | RAG retrieval, NLI verification, Adaptive thresholds, LLM integration | COMPLETE |
| Jan 2026 | Streamlit UI, Configuration sliders, PoC notebook, Documentation | COMPLETE |

**Phase 2: Evaluation (UPCOMING)**

| Month | Tasks | Status |
|-------|-------|--------|
| Feb 2026 | HaluEval dataset preparation, Evaluation scripts | PENDING |
| Mar 2026 | 3-condition experiment (C1, C2, C3), Statistical analysis | PENDING |

**Phase 3: Final Submission (PLANNED)**

| Month | Tasks | Status |
|-------|-------|--------|
| Apr 2026 | Complete thesis chapters, Final submission | PLANNED |

**Timeline Deviations and Impact:**

| Original Plan | Actual | Reason | Impact |
|---------------|--------|--------|--------|
| Use sentence-transformers | Use transformers directly | Segfault issues on Apple Silicon | **No impact** - same functionality |
| GPU acceleration | CPU-only mode | Stability and compatibility | **No impact** - acceptable performance |
| Larger Wikipedia KB | 6-paragraph demo KB | Sufficient for prototype | **No impact** - full KB for evaluation |

**Key talking points:**
1. Phase 1 (Prototype) completed on schedule
2. All deviations were technical environment issues, not scope reductions
3. Core deliverables unaffected by any changes
4. Clear plan for evaluation phase (Feb-Mar 2026)
5. On track for April 2026 final submission

---

### 5. Video Presentation & Video Demonstration (20%)

**What markers are looking for:**
- Clarity of both videos
- Demonstrates the project's development up to the current stage
- Highlighting key milestones
- Highlighting challenges faced
- Highlighting solutions implemented

**How to satisfy this criterion:**

**Key Milestones to Highlight:**
1. Successful implementation of RAG retrieval with confidence scoring
2. Integration of NLI verification using RoBERTa-MNLI
3. Implementation of adaptive threshold logic (core innovation)
4. Creation of interactive Streamlit UI with configurable parameters
5. Achievement of 69% requirements implementation (11 of 16)

**Challenges to Highlight:**

| Challenge | Details |
|-----------|---------|
| Segmentation Faults | sentence-transformers crashed on Apple Silicon |
| PyTorch Incompatibility | PyTorch 2.9.0 binary wouldn't load in Anaconda |
| Deprecated Model | Groq deprecated llama3-8b-8192 model |

**Solutions to Highlight:**

| Solution | How it Worked |
|----------|---------------|
| Direct transformers usage + CPU mode | Eliminated segfaults completely |
| Fresh venv with PyTorch 2.6.0 | Resolved all import issues |
| Updated to llama-3.1-8b-instant | Restored generation functionality |

**Key talking points:**
1. Speak clearly and at moderate pace
2. Explain the "why" not just the "what"
3. Point to specific code sections when discussing implementation
4. Show real numbers from the prototype demonstration
5. Emphasize the adaptive behavior with concrete examples

---

## Technical Details for Reference

### The Problem Being Solved

**LLM Hallucinations:** Large Language Models generate plausible-sounding but factually incorrect information. They present false information with the same confidence as true information, making it impossible for users to distinguish accurate from fabricated content.

**Real-world impact:**
- Healthcare misinformation
- Legal inaccuracies
- Educational errors
- Business decision failures

**The Research Gap:**
Existing hallucination detection systems use **fixed thresholds** (e.g., if NLI entailment > 0.5, mark as verified). This treats all situations the same regardless of evidence quality. Strong evidence should be treated differently from weak evidence.

### The Innovation

**Adaptive Thresholds:** AFLHR Lite adjusts verification strictness based on retrieval confidence.

- **When retrieval confidence is LOW** (below pivot of 0.75): Evidence is weak, so apply **STRICT threshold** (0.95). Be skeptical.
- **When retrieval confidence is HIGH** (at or above pivot of 0.75): Evidence is strong, so apply **LENIENT threshold** (0.70). Trust it.

**Why this matters:**
- Reduces false positives (incorrectly flagging good responses)
- Reduces false negatives (missing actual hallucinations)
- More nuanced than one-size-fits-all fixed thresholds

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Embedding | all-MiniLM-L6-v2 | 384-dim semantic vectors |
| Vector Search | FAISS | Fast similarity search |
| LLM | Llama 3.1 8B via Groq | Response generation |
| NLI | RoBERTa-large-MNLI | Entailment verification |
| UI | Streamlit | Interactive web app |
| Configuration | Python module | Centralized settings |

### File Structure

```
AFLHR_Lite/
├── config.py          # Configuration, model IDs, thresholds, KB
├── engine.py          # Core AFLHREngine class
├── app.py             # Streamlit UI
├── requirements.txt   # Python dependencies
├── .env               # API keys (not committed)
├── poc_demo.ipynb     # Proof of concept notebook
├── POC_GUIDE.md       # Plain English explanation
├── PROGRESS.md        # Development progress report
└── IPD/               # IPD submission materials
    ├── 04_DEMO_SCRIPT.md
    ├── 06_PRESENTATION_SCRIPT.md
    ├── 07_LLM_INSTRUCTIONS_PRESENTATION.md
    └── 08_LLM_INSTRUCTIONS_DEMO.md
```

---

## Common Pitfalls to Avoid

1. **Don't exceed 20 minutes** - Practice timing and cut content if necessary
2. **Don't skip any marking criterion** - Each one carries specific weight
3. **Don't be vague about stakeholders** - Name specific roles and their influence
4. **Don't forget to show IMPLEMENTED vs PENDING requirements** - This is explicitly required
5. **Don't skip the timeline deviations** - Markers want to see you acknowledge changes
6. **Don't rush the core innovation explanation** - This is your differentiator
7. **Don't forget to mention the prototype demo** - Reference the separate demo video
8. **Don't use jargon without explaining it** - Define NLI, RAG, FAISS on first use

---

## Suggested Script Flow

1. **Introduction (1 min)** - Who you are, what the project is
2. **Problem (2 min)** - What are hallucinations, why they matter, research gap
3. **Stakeholders (2 min)** - Who is affected, how they influenced design
4. **Requirements (3 min)** - Functional/non-functional, implemented vs pending
5. **Architecture (4 min)** - Layers, components, data flow
6. **Core Innovation (2 min)** - Adaptive thresholds explained
7. **Challenges (2 min)** - Problems faced, solutions implemented
8. **Timeline (1 min)** - Progress, deviations, plan
9. **Next Steps (1 min)** - Evaluation plan
10. **Conclusion (1 min)** - Summary, key contributions

---

## Quick Reference: Marking Criteria Checklist

Before recording, ensure your presentation covers:

- [ ] **Stakeholders (10%):** All primary and secondary stakeholders named with roles, interests, influence
- [ ] **Requirements (10%):** All 16 requirements listed with clear IMPLEMENTED/PENDING/OUT OF SCOPE status
- [ ] **Architecture (10%):** Diagrams shown, components explained, data flow clear
- [ ] **Timeline (5%):** Schedule presented, deviations acknowledged, impact assessed
- [ ] **Video Quality (20%):** Clear audio, logical flow, milestones/challenges/solutions highlighted

**Total coverage target: 100%**
