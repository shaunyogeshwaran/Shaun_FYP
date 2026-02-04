# Prototype Demonstration Video Script

## AFLHR Lite - 5-10 Minute Video Demonstration

**Duration:** 10 minutes maximum (5-10 minute range)
- **Part 1: Code Explanation** - Maximum 7 minutes
- **Part 2: Live Prototype Demo** - Maximum 3 minutes

**Format:** Screen recording with voice-over narration
**Presenter:** Shaun
**Upload:** YouTube as unlisted video

---

## Pre-Recording Checklist

### Environment Setup
- [ ] Terminal/IDE ready with project folder open
- [ ] Groq API key set in `.env` file (verify with `echo $GROQ_API_KEY`)
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list | grep -E "transformers|faiss|streamlit"`)
- [ ] Browser ready for Streamlit UI

### Test Queries Prepared
- [ ] Query 1 (High confidence): "When was the University of Westminster founded?"
- [ ] Query 2 (Low confidence): "What is the weather like on Jupiter?"
- [ ] Query 3 (For threshold demo): "What are LLM hallucinations?"

### Recording Setup
- [ ] Screen recording software ready (QuickTime, OBS, etc.)
- [ ] Microphone tested and audio levels checked
- [ ] Font size increased in IDE for readability
- [ ] Close unnecessary applications
- [ ] Quiet recording environment

---

## PART 1: CODE EXPLANATION (7 minutes maximum)

---

### SECTION 1.1: Introduction
**Time: 0:00 - 0:30 (30 seconds)**

#### Screen: Show VS Code/IDE with project folder open in file explorer

#### Script (Read Exactly)

> "Hello, I'm Shaun, and this is the prototype demonstration video for my final year project, AFLHR Lite - an Adaptive Framework for LLM Hallucination Reduction.
>
> In this video, I'll walk through the code structure explaining the key components, and then demonstrate the working prototype with live examples.
>
> The core innovation of my project is using retrieval confidence to dynamically adjust verification thresholds - being more skeptical when evidence is weak, and more trusting when evidence is strong.
>
> Let me start by showing you the project structure."

---

### SECTION 1.2: Project Structure Overview
**Time: 0:30 - 1:00 (30 seconds)**

#### Screen: Show file explorer with these files visible:
```
AFLHR_Lite/
├── config.py
├── engine.py
├── app.py
├── requirements.txt
├── .env
└── IPD/
```

#### Script (Read Exactly)

> "Here's the project structure. The three main files are:
>
> - **config.py** - Contains all configuration settings, model IDs, threshold defaults, and the knowledge base
> - **engine.py** - Contains the core AFLHREngine class that implements the retrieval, generation, and verification pipeline
> - **app.py** - Contains the Streamlit user interface
>
> Let me walk through each file, starting with the configuration."

---

### SECTION 1.3: config.py Walkthrough
**Time: 1:00 - 2:30 (1.5 minutes)**

#### Screen: Open config.py in the editor

#### Script (Read Exactly)

> "Opening config.py - this is where all settings are centralized for easy modification.
>
> [Scroll to model configuration section]
>
> First, the model configurations. We have three models:
> - **EMBED_MODEL** is set to `sentence-transformers/all-MiniLM-L6-v2` - this creates 384-dimensional embeddings for semantic search
> - **VERIFIER_MODEL** is `FacebookAI/roberta-large-mnli` - this is the Natural Language Inference model for verification
> - **GENERATOR_MODEL** is `llama-3.1-8b-instant` - this is the LLM we call via the Groq API
>
> [Scroll to threshold defaults section]
>
> Here are the threshold defaults - these are the key parameters for my adaptive system:
> - **DEFAULT_PIVOT** is 0.75 - this is the switching point between strict and lenient modes
> - **DEFAULT_STRICT_THRESHOLD** is 0.95 - used when retrieval confidence is LOW
> - **DEFAULT_LENIENT_THRESHOLD** is 0.70 - used when retrieval confidence is HIGH
>
> The logic is: if retrieval confidence is below 0.75, we apply the strict 0.95 threshold. If it's at or above 0.75, we apply the lenient 0.70 threshold.
>
> [Scroll to knowledge base section]
>
> Finally, the knowledge base. For this prototype, I have 6 curated paragraphs covering the University of Westminster, AI hallucinations, and a distractor topic about Sri Lanka's climate. This is sufficient for demonstrating the adaptive behavior. The full evaluation will use the HaluEval benchmark dataset."

---

### SECTION 1.4: engine.py Walkthrough - Class Initialization
**Time: 2:30 - 3:30 (1 minute)**

#### Screen: Open engine.py and scroll to the AFLHREngine class

#### Script (Read Exactly)

> "Now the heart of the system - engine.py. This contains the AFLHREngine class.
>
> [Highlight the __init__ method]
>
> The `__init__` method initializes three components:
>
> First, it loads the **embedding model** using the transformers library directly. I use AutoTokenizer and AutoModel, then create embeddings by taking the mean of the hidden states. Note the `device='cpu'` parameter - this is intentional to avoid segmentation faults on Apple Silicon.
>
> Second, it loads the **NLI verifier** using the transformers pipeline with `device='cpu'` explicitly set.
>
> Third, it initializes the **Groq client** for LLM generation. This requires an API key set in the environment.
>
> Finally, it calls `_build_index()` which creates the FAISS vector store from the knowledge base. Each paragraph is embedded and stored for fast similarity search."

---

### SECTION 1.5: engine.py Walkthrough - Retrieve Method
**Time: 3:30 - 4:30 (1 minute)**

#### Screen: Scroll to the retrieve() method

#### Script (Read Exactly)

> "The `retrieve` method is Layer 1 of my pipeline - RAG Retrieval.
>
> [Highlight the method]
>
> It takes a query string as input and performs these steps:
>
> 1. **Embed the query** - Convert the query text into a 384-dimensional vector using the same embedding model
> 2. **Search FAISS** - Find the top-k most similar documents using inner product similarity
> 3. **Calculate confidence** - This is crucial. I take the similarity scores, normalize them to a 0-1 range, and return the average as the confidence score
>
> The method returns three things: the retrieved documents as a combined string, the confidence score, and the raw similarity scores.
>
> This confidence score is what drives the adaptive threshold selection later. A high score means we found highly relevant evidence; a low score means we found marginally related or unrelated content."

---

### SECTION 1.6: engine.py Walkthrough - Generate and Verify Methods
**Time: 4:30 - 5:30 (1 minute)**

#### Screen: Scroll to the generate() and verify() methods

#### Script (Read Exactly)

> "The `generate` method calls the LLM to produce a response.
>
> [Highlight generate method]
>
> It sends a request to Groq with a system prompt that instructs the model: 'Answer using ONLY the provided context. If the information isn't in the context, say so.'
>
> This grounding is essential - we want the LLM to base its answer on the retrieved evidence, not its general knowledge. There's also an offline mode that returns a mock response for testing without API access.
>
> [Scroll to verify method]
>
> The `verify` method is Layer 2 - NLI Verification.
>
> It takes the retrieved context as the 'premise' and the generated response as the 'hypothesis'. The NLI model then classifies the relationship as contradiction, neutral, or entailment.
>
> I extract the **entailment probability** - this tells us how strongly the evidence supports the response. Note the truncation handling for long contexts to prevent memory issues."

---

### SECTION 1.7: engine.py Walkthrough - Calculate Verdict (CORE INNOVATION)
**Time: 5:30 - 6:30 (1 minute)**

#### Screen: Scroll to the calculate_verdict() method and highlight it

#### Script (Read Exactly)

> "Now the most important method - `calculate_verdict`. This is the CORE INNOVATION of my project.
>
> [Highlight the method and the conditional logic]
>
> Let me walk through the logic step by step:
>
> First, it checks: is the retrieval confidence score BELOW the pivot point?
>
> If YES - meaning we have weak evidence - it sets the mode to STRICT and uses the strict threshold of 0.95. The reasoning is 'Low retrieval confidence means weak evidence - applying strict verification.'
>
> If NO - meaning we have strong evidence - it sets the mode to LENIENT and uses the lenient threshold of 0.70. The reasoning is 'High retrieval confidence means strong evidence - applying lenient verification.'
>
> Finally, it compares the NLI entailment score against this dynamically selected threshold. If the NLI score meets or exceeds the threshold, verdict is VERIFIED. Otherwise, it's HALLUCINATION.
>
> This is what makes my system adaptive. It doesn't use a one-size-fits-all threshold. It adjusts based on evidence quality."

---

### SECTION 1.8: app.py Overview
**Time: 6:30 - 7:00 (30 seconds)**

#### Screen: Open app.py and show the structure

#### Script (Read Exactly)

> "Finally, app.py provides the Streamlit user interface.
>
> [Scroll through the file highlighting key sections]
>
> The sidebar contains three sliders for adjusting the pivot point, strict threshold, and lenient threshold in real-time. There's also an offline mode toggle.
>
> The main area has a text input for queries and a Verify button. Results display in three columns:
> - Column 1 shows the retrieved evidence and the retrieval confidence score
> - Column 2 shows the generated LLM response
> - Column 3 shows the NLI entailment score, the threshold applied, and the final verdict
>
> The verdict is color-coded - green for VERIFIED, red for HALLUCINATION. This provides immediate visual feedback.
>
> Now let me show you the prototype in action."

---

## PART 2: LIVE PROTOTYPE DEMONSTRATION (3 minutes maximum)

---

### SECTION 2.1: Starting the Application
**Time: 7:00 - 7:30 (30 seconds)**

#### Screen: Terminal window

#### Script (Read Exactly)

> "Let me start the Streamlit application."

#### Action: Type and run:
```bash
streamlit run app.py
```

#### Script (Continue)

> "The models are loading - this takes about 30 seconds on first run as it downloads and initializes the embedding model and the NLI model.
>
> [Wait for browser to open with the Streamlit UI]
>
> And here's the interface. You can see the sidebar with the threshold sliders, and the main area where we'll enter queries."

---

### SECTION 2.2: Demo 1 - High Confidence Query (LENIENT Mode)
**Time: 7:30 - 8:15 (45 seconds)**

#### Screen: Streamlit UI in browser

#### Script (Read Exactly)

> "First, let me demonstrate a query our knowledge base can answer well."

#### Action: Type in the query box: `When was the University of Westminster founded?`

#### Script (Continue)

> "I'm asking 'When was the University of Westminster founded?' - this is a topic covered in our knowledge base."

#### Action: Click the "Verify" button and wait for results

#### Script (Continue - point to each element as you speak)

> "Look at the results:
>
> In the **Evidence column**, you can see the retrieved documents about Westminster. The retrieval confidence is... [read the actual number, should be around 0.85-0.90]. This is ABOVE our pivot of 0.75.
>
> Because the confidence is high, we're in **LENIENT mode** - you can see that indicated here. The threshold being applied is 0.70.
>
> The **Generated Response** says the University of Westminster was founded in 1838. This is correct.
>
> The **NLI Entailment Score** is... [read the actual number, should be around 0.85-0.95]. This exceeds our lenient threshold of 0.70.
>
> Therefore, the verdict is **VERIFIED** - shown in green. The system correctly verified this factual response because we had strong evidence and the NLI score exceeded the lenient threshold."

---

### SECTION 2.3: Demo 2 - Low Confidence Query (STRICT Mode)
**Time: 8:15 - 9:00 (45 seconds)**

#### Screen: Streamlit UI

#### Script (Read Exactly)

> "Now let me demonstrate an off-topic query that our knowledge base cannot answer."

#### Action: Clear the query box and type: `What is the weather like on Jupiter?`

#### Script (Continue)

> "I'm asking about Jupiter's weather. Our knowledge base is about Westminster, AI hallucinations, and Sri Lanka - NOT astronomy."

#### Action: Click "Verify" and wait for results

#### Script (Continue - point to each element)

> "Look what happens:
>
> The **retrieval confidence** is... [read the actual number, should be around 0.55-0.70]. This is BELOW our pivot of 0.75.
>
> Because confidence is low, we're in **STRICT mode**. The threshold being applied is now 0.95 - much higher than before.
>
> The LLM might have generated something about Jupiter, but look at the **NLI Entailment Score** - it's very low, around... [read the actual number]. This makes sense because the retrieved context about Westminster and AI doesn't support claims about Jupiter.
>
> Even if the NLI score were moderate, say 0.75, it wouldn't pass the strict threshold of 0.95.
>
> The verdict is **HALLUCINATION** - shown in red.
>
> This is the adaptive behavior in action. Because our retrieval found weak evidence, we applied a stricter threshold and correctly flagged this as a potential hallucination."

---

### SECTION 2.4: Demo 3 - Threshold Adjustment
**Time: 9:00 - 9:30 (30 seconds)**

#### Screen: Streamlit UI, focus on the sidebar sliders

#### Script (Read Exactly)

> "Finally, let me demonstrate the real-time configurability."

#### Action: Adjust the pivot slider from 0.75 to 0.60

#### Script (Continue)

> "I'm lowering the pivot point from 0.75 to 0.60. This means more queries will qualify for lenient mode."

#### Action: Re-run the Westminster query

#### Script (Continue)

> "If I run the Westminster query again, you can see it still passes because the retrieval confidence exceeds even this lower pivot.
>
> [Point to the mode indicator]
>
> Users can tune these parameters based on their specific accuracy requirements. Higher pivot means stricter overall. Lower pivot means more lenient overall. This flexibility allows the system to be adapted for different use cases."

---

### SECTION 2.5: Conclusion
**Time: 9:30 - 10:00 (30 seconds)**

#### Screen: Return to showing the full UI or architecture diagram

#### Script (Read Exactly)

> "This demonstrates the core innovation of AFLHR Lite: confidence-weighted thresholds that adapt verification strictness based on evidence quality.
>
> When evidence is strong, we trust it and apply a lenient threshold. When evidence is weak, we're skeptical and apply a strict threshold.
>
> This addresses a gap in existing hallucination detection systems that use fixed thresholds regardless of evidence quality.
>
> The prototype demonstrates all core functionalities: semantic retrieval with confidence scoring, grounded LLM generation, NLI verification, and adaptive threshold selection.
>
> Thank you for watching."

---

## Post-Recording Checklist

### Review
- [ ] Total duration is between 5-10 minutes
- [ ] Code explanation portion is under 7 minutes
- [ ] Demo portion is under 3 minutes
- [ ] Audio is clear throughout
- [ ] All three demo scenarios are clearly shown
- [ ] Core innovation is clearly explained

### Upload
- [ ] Upload to YouTube as **unlisted** video
- [ ] Set video title: "AFLHR Lite - IPD Prototype Demonstration - Shaun"
- [ ] Verify link is accessible (test in incognito window)
- [ ] Copy the URL for submission

### Backup
- [ ] Save original video file locally
- [ ] Backup to cloud storage (OneDrive, Google Drive)

---

## Timing Summary

| Section | Content | Duration | Cumulative |
|---------|---------|----------|------------|
| 1.1 | Introduction | 0:30 | 0:30 |
| 1.2 | Project Structure | 0:30 | 1:00 |
| 1.3 | config.py | 1:30 | 2:30 |
| 1.4 | engine.py - Init | 1:00 | 3:30 |
| 1.5 | engine.py - Retrieve | 1:00 | 4:30 |
| 1.6 | engine.py - Generate/Verify | 1:00 | 5:30 |
| 1.7 | engine.py - Calculate Verdict | 1:00 | 6:30 |
| 1.8 | app.py | 0:30 | 7:00 |
| **Part 1 Total** | **Code Explanation** | **7:00** | |
| 2.1 | Starting App | 0:30 | 7:30 |
| 2.2 | Demo 1 - High Confidence | 0:45 | 8:15 |
| 2.3 | Demo 2 - Low Confidence | 0:45 | 9:00 |
| 2.4 | Demo 3 - Threshold Adjust | 0:30 | 9:30 |
| 2.5 | Conclusion | 0:30 | 10:00 |
| **Part 2 Total** | **Live Demo** | **3:00** | |
| **GRAND TOTAL** | | **10:00** | |

---

## Troubleshooting During Recording

### If the app doesn't start:
- Check virtual environment is activated: `source venv/bin/activate`
- Verify packages installed: `pip install -r requirements.txt`

### If API calls fail:
- Enable offline mode in the sidebar
- Continue demo with mock responses
- Explain this is a fallback for demonstration

### If models fail to load:
- Restart the application
- Check internet connection for model downloads
- Use pre-downloaded models if available

### If confidence scores are unexpected:
- The exact numbers may vary - focus on relative behavior
- High confidence = LENIENT mode, Low confidence = STRICT mode
- The principle is consistent even if exact numbers differ

---

## Key Points to Emphasize During Recording

1. **The confidence score from retrieval drives the threshold selection** - This is the core innovation
2. **STRICT mode (0.95) for weak evidence, LENIENT mode (0.70) for strong evidence** - Explain the intuition
3. **Real-time configurability** - Users can adjust parameters for their needs
4. **All core functionalities working** - Retrieval, generation, verification, adaptive decision
5. **This addresses the research gap** - Fixed thresholds don't account for evidence quality
