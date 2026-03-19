"""
AFLHR Lite - Core Engine Module
Handles retrieval, generation, and verification logic.

v2 improvements:
  - Sliding-window NLI (fixes 512-token truncation for long premises)
  - Sentence-level claim decomposition (addresses semantic illusion)
  - NLI temperature scaling / calibration
  - Optional BGE embedding upgrade (ablation)
"""

import os
# Disable MPS and tokenizer parallelism to prevent segfaults on Apple Silicon
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import json
import math
import time

import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_V2,
    VERIFIER_MODEL,
    GENERATOR_MODEL,
    GROQ_API_KEY,
    KNOWLEDGE_BASE,
    GENERATION_SYSTEM_PROMPT,
    OFFLINE_MOCK_RESPONSE,
    NLI_MAX_PREMISE_TOKENS,
    NLI_STRIDE_TOKENS,
    CALIBRATION_TEMP_PATH,
)


class AFLHREngine:
    """
    Adaptive Framework for LLM Hallucination Reduction - Lite Version

    Two-layer pipeline:
    1. RAG Layer: Retrieval with confidence scoring
    2. Verification Layer: NLI-based verification with dynamic thresholds

    v2 feature flags (set in __init__):
      use_windowed_nli  - sliding-window NLI for long premises
      use_decomposition - sentence-level claim decomposition
      use_calibration   - temperature-scaled NLI logits
      use_bge_embeddings - BAAI/bge-small-en-v1.5 instead of MiniLM
    """

    def __init__(
        self,
        use_windowed_nli: bool = False,
        use_decomposition: bool = False,
        use_calibration: bool = False,
        use_bge_embeddings: bool = False,
    ):
        """Initialize models and build the knowledge base index."""
        print("Initializing AFLHR Engine...")

        # Store feature flags
        self.use_windowed_nli = use_windowed_nli
        self.use_decomposition = use_decomposition
        self.use_calibration = use_calibration
        self.use_bge_embeddings = use_bge_embeddings

        # Auto-detect CUDA; skip MPS (segfaults on Apple Silicon)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using {self.device} for all models")

        # Select embedding model
        embed_model_id = EMBEDDING_MODEL_V2 if use_bge_embeddings else EMBEDDING_MODEL
        print(f"Loading embedding model: {embed_model_id}")
        self.embed_tokenizer = AutoTokenizer.from_pretrained(embed_model_id)
        self.embed_model = AutoModel.from_pretrained(embed_model_id)
        self.embed_model.to(self.device)
        self.embed_model.eval()

        # Load NLI verifier model
        print(f"Loading verifier model: {VERIFIER_MODEL}")
        self.tokenizer = AutoTokenizer.from_pretrained(VERIFIER_MODEL)
        self.verifier_model = AutoModelForSequenceClassification.from_pretrained(VERIFIER_MODEL)
        self.verifier_model.to(self.device)
        self.verifier_model.eval()

        # Load calibration temperature
        self.calibration_T = 1.0
        if use_calibration:
            self._load_calibration()

        # Initialize LLM client (Groq)
        if GROQ_API_KEY:
            self.llm = ChatGroq(
                api_key=GROQ_API_KEY,
                model_name=GENERATOR_MODEL,
                temperature=0.1,
            )
            print("Groq LLM client initialized")
        else:
            self.llm = None
            print("Warning: No GROQ_API_KEY found. Running in offline mode only.")

        # Build knowledge base index
        self.knowledge_base = KNOWLEDGE_BASE
        self.faiss_index = None
        self.ingest_knowledge_base()

        flags = []
        if use_windowed_nli:
            flags.append("windowed_nli")
        if use_decomposition:
            flags.append("decomposition")
        if use_calibration:
            flags.append(f"calibration(T={self.calibration_T:.3f})")
        if use_bge_embeddings:
            flags.append("bge_embeddings")
        flag_str = ", ".join(flags) if flags else "v1 (baseline)"
        print(f"AFLHR Engine initialized [{flag_str}]")

    def _load_calibration(self):
        """Load temperature from calibration file.

        If T is at the optimizer boundary (>=9.0), it means calibration
        failed to find a useful temperature — fall back to T=1.0.
        """
        if os.path.exists(CALIBRATION_TEMP_PATH):
            with open(CALIBRATION_TEMP_PATH) as f:
                data = json.load(f)
            T = float(data["temperature"])
            if T >= 9.0:
                print(f"Warning: calibration T={T:.4f} is at optimizer boundary "
                      f"— NLI logits are not calibratable for this task. "
                      f"Falling back to T=1.0 (uncalibrated).")
                self.calibration_T = 1.0
            else:
                self.calibration_T = T
                print(f"Loaded calibration temperature: {self.calibration_T:.4f}")
        else:
            print(f"Warning: calibration file not found at {CALIBRATION_TEMP_PATH}, using T=1.0")

    def _encode(self, texts: list, is_query: bool = False) -> np.ndarray:
        """
        Generate embeddings using mean pooling (replicates SentenceTransformer behavior).

        Args:
            texts: List of strings to encode
            is_query: If True and using BGE, prepend instruction prefix

        Returns:
            Normalized embeddings as numpy array
        """
        # BGE models require instruction prefix for queries
        if self.use_bge_embeddings and is_query:
            texts = [f"Represent this sentence for searching relevant passages: {t}" for t in texts]

        # Tokenize
        inputs = self.embed_tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get embeddings
        with torch.no_grad():
            outputs = self.embed_model(**inputs)
            # Mean pooling over token embeddings (excluding padding)
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * mask_expanded, dim=1)
            sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
            embeddings = sum_embeddings / sum_mask

            # Normalize for cosine similarity
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().numpy().astype('float32')

    def ingest_knowledge_base(self):
        """Build FAISS index from the knowledge base."""
        print("Building FAISS index...")

        # Generate embeddings (normalized for cosine similarity)
        embeddings = self._encode(self.knowledge_base)

        # Build FAISS index (Inner Product for cosine similarity with normalized vectors)
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        self.faiss_index.add(embeddings)

        print(f"FAISS index built with {self.faiss_index.ntotal} documents")

    def retrieve(self, query: str, k: int = 2) -> dict:
        """
        Retrieve top-k relevant documents with confidence score.

        Args:
            query: The search query
            k: Number of documents to retrieve (default: 2)

        Returns:
            dict with 'context' (concatenated docs), 'retrieval_score', and 'documents'
        """
        # Embed the query
        query_embedding = self._encode([query], is_query=True)

        # Search FAISS
        scores, indices = self.faiss_index.search(query_embedding, k)

        # Extract results
        # With normalized embeddings and Inner Product, scores are cosine similarities in [-1, 1]
        # Normalize to [0, 1] for easier interpretation
        raw_score = float(scores[0][0])
        retrieval_score = (raw_score + 1) / 2  # Convert [-1, 1] to [0, 1]

        # Get retrieved documents
        documents = [self.knowledge_base[int(idx)] for idx in indices[0]]
        context = "\n\n".join(documents)

        return {
            'context': context,
            'retrieval_score': round(retrieval_score, 4),
            'raw_score': round(raw_score, 4),
            'documents': documents,
            'indices': indices[0].tolist()
        }

    def generate(self, context: str, query: str, offline_mode: bool = False) -> str:
        """
        Generate a response using the LLM.

        Args:
            context: Retrieved context to ground the response
            query: User's question
            offline_mode: If True, return mock response instead of calling API

        Returns:
            Generated response string
        """
        if offline_mode or self.llm is None:
            return OFFLINE_MOCK_RESPONSE

        # Construct messages
        messages = [
            SystemMessage(content=GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"Generation error: {e}")
            return f"Error generating response: {str(e)}"

    # ==================================================================
    # NLI Verification (v1 and v2)
    # ==================================================================

    def _nli_logits(self, premise: str, hypothesis: str) -> torch.Tensor:
        """Run NLI and return raw logits (before softmax).

        Returns:
            1-D tensor of shape (3,): [contradiction, neutral, entailment]
        """
        inputs = self.tokenizer(
            premise,
            hypothesis,
            return_tensors="pt",
            truncation="longest_first",
            max_length=512,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.verifier_model(**inputs)
        return outputs.logits[0]  # shape (3,)

    def _logits_to_entailment(self, logits: torch.Tensor) -> float:
        """Convert 3-class logits to entailment probability, with optional calibration."""
        if self.use_calibration and self.calibration_T != 1.0:
            logits = logits / self.calibration_T
        probs = torch.softmax(logits, dim=0)
        return probs[2].item()  # entailment index

    def verify(self, premise: str, hypothesis: str) -> float:
        """
        Verify the hypothesis against the premise using NLI (single-pass).

        Args:
            premise: The retrieved context (evidence)
            hypothesis: The generated response (claim to verify)

        Returns:
            Entailment probability (0-1)
        """
        logits = self._nli_logits(premise, hypothesis)
        return round(self._logits_to_entailment(logits), 4)

    def verify_raw_logits(self, premise: str, hypothesis: str) -> list:
        """Return raw 3-class logits (for calibration data collection)."""
        logits = self._nli_logits(premise, hypothesis)
        return logits.cpu().tolist()

    # ------------------------------------------------------------------
    # 1A. Sliding-Window NLI
    # ------------------------------------------------------------------

    def verify_windowed(
        self,
        premise: str,
        hypothesis: str,
        max_premise_tokens: int = None,
        stride: int = None,
    ) -> dict:
        """Sliding-window NLI for long premises.

        Tokenizes premise alone; if it fits within (512 - hypothesis_tokens),
        falls back to single-pass verify(). Otherwise splits premise tokens
        into overlapping windows and returns max entailment score.

        Returns:
            dict with 'score' (max entailment), 'n_windows', 'method'
        """
        if max_premise_tokens is None:
            max_premise_tokens = NLI_MAX_PREMISE_TOKENS
        if stride is None:
            stride = NLI_STRIDE_TOKENS

        # Tokenize premise and hypothesis separately to check lengths
        premise_ids = self.tokenizer.encode(premise, add_special_tokens=False)
        hypothesis_ids = self.tokenizer.encode(hypothesis, add_special_tokens=False)

        # RoBERTa uses: <s> premise </s></s> hypothesis </s> = 4 special tokens
        available_for_premise = 512 - len(hypothesis_ids) - 4

        if available_for_premise <= 0:
            # Hypothesis alone exceeds limit; fall back to single-pass with truncation
            score = self.verify(premise, hypothesis)
            return {"score": score, "n_windows": 1, "method": "single_pass_truncated"}

        if len(premise_ids) <= available_for_premise:
            # Single-pass is fine
            score = self.verify(premise, hypothesis)
            return {"score": score, "n_windows": 1, "method": "single_pass"}

        # Cap window size to what actually fits alongside the hypothesis
        effective_window = min(max_premise_tokens, available_for_premise)

        # Split premise into overlapping windows
        window_scores = []
        start = 0
        while start < len(premise_ids):
            end = min(start + effective_window, len(premise_ids))
            window_ids = premise_ids[start:end]

            # Decode window back to text
            window_text = self.tokenizer.decode(window_ids, skip_special_tokens=True)

            logits = self._nli_logits(window_text, hypothesis)
            score = self._logits_to_entailment(logits)
            window_scores.append(score)

            if end >= len(premise_ids):
                break
            start += stride

        # Max aggregation: if any chunk entails, it's supported
        max_score = max(window_scores)
        return {
            "score": round(max_score, 4),
            "n_windows": len(window_scores),
            "method": "windowed",
        }

    # ------------------------------------------------------------------
    # 1B. Sentence-Level Claim Decomposition
    # ------------------------------------------------------------------

    def decompose_claims(self, text: str) -> list:
        """Split text into individual claim sentences using NLTK."""
        import nltk
        try:
            sentences = nltk.sent_tokenize(text)
        except LookupError:
            nltk.download("punkt_tab", quiet=True)
            sentences = nltk.sent_tokenize(text)
        # Filter out very short fragments (< 5 chars)
        return [s.strip() for s in sentences if len(s.strip()) >= 5]

    def verify_decomposed(self, premise: str, hypothesis: str) -> dict:
        """Decompose hypothesis into sentences and verify each against premise.

        Uses windowed NLI if use_windowed_nli is enabled, otherwise single-pass.
        Aggregates with min (weakest-link: one bad claim = hallucination).

        Returns:
            dict with 'score' (min), 'mean_score', 'per_claim' list,
            'n_claims', 'n_windows' (total across all claims)
        """
        claims = self.decompose_claims(hypothesis)

        if not claims:
            # Fallback: treat whole hypothesis as single claim
            claims = [hypothesis]

        per_claim = []
        total_windows = 0

        for claim in claims:
            if self.use_windowed_nli:
                result = self.verify_windowed(premise, claim)
                score = result["score"]
                total_windows += result["n_windows"]
            else:
                score = self.verify(premise, claim)
                total_windows += 1

            per_claim.append({"claim": claim, "score": score})

        scores = [c["score"] for c in per_claim]
        min_score = min(scores)
        mean_score = sum(scores) / len(scores)

        return {
            "score": round(min_score, 4),
            "mean_score": round(mean_score, 4),
            "per_claim": per_claim,
            "n_claims": len(claims),
            "n_windows": total_windows,
        }

    # ==================================================================
    # Verdict Calculation
    # ==================================================================

    def calculate_verdict(
        self,
        retrieval_score: float,
        nli_score: float,
        pivot: float,
        strict_threshold: float,
        lenient_threshold: float
    ) -> dict:
        """
        Calculate verification verdict using confidence-weighted thresholds.

        The core innovation: threshold adapts based on retrieval confidence.
        - Low retrieval confidence -> Strict threshold (be skeptical)
        - High retrieval confidence -> Lenient threshold (trust evidence)

        Args:
            retrieval_score: FAISS similarity score (0-1)
            nli_score: NLI entailment probability (0-1)
            pivot: Threshold pivot point
            strict_threshold: Used when retrieval < pivot
            lenient_threshold: Used when retrieval >= pivot

        Returns:
            dict with verdict details
        """
        if retrieval_score < pivot:
            threshold = strict_threshold
            mode = "STRICT"
            reasoning = "Low retrieval confidence -> applying strict verification"
        else:
            threshold = lenient_threshold
            mode = "LENIENT"
            reasoning = "High retrieval confidence -> trusting evidence quality"

        is_verified = nli_score >= threshold

        return {
            "status": "VERIFIED" if is_verified else "HALLUCINATION",
            "mode": mode,
            "threshold": threshold,
            "nli_score": nli_score,
            "retrieval_score": retrieval_score,
            "reasoning": reasoning,
            "passed": is_verified
        }

    def run_pipeline(
        self,
        query: str,
        pivot: float,
        strict_threshold: float,
        lenient_threshold: float,
        offline_mode: bool = False
    ) -> dict:
        """
        Run the complete AFLHR pipeline.

        Args:
            query: User's question
            pivot: Threshold pivot point
            strict_threshold: Used when retrieval < pivot
            lenient_threshold: Used when retrieval >= pivot
            offline_mode: If True, use mock LLM response

        Returns:
            dict with all pipeline results
        """
        # Step 1: Retrieve
        retrieval_result = self.retrieve(query, k=2)

        # Step 2: Generate
        generated_response = self.generate(
            retrieval_result['context'],
            query,
            offline_mode=offline_mode
        )

        # Step 3: Verify
        nli_score = self.verify(
            premise=retrieval_result['context'],
            hypothesis=generated_response
        )

        # Step 4: Calculate verdict
        verdict = self.calculate_verdict(
            retrieval_score=retrieval_result['retrieval_score'],
            nli_score=nli_score,
            pivot=pivot,
            strict_threshold=strict_threshold,
            lenient_threshold=lenient_threshold
        )

        return {
            'query': query,
            'retrieval': retrieval_result,
            'generation': generated_response,
            'nli_score': nli_score,
            'verdict': verdict
        }

    # ==================================================================
    # Experiment / Evaluation Methods
    # ==================================================================

    def compute_retrieval_score(self, query: str, knowledge: str) -> float:
        """Compute cosine similarity between query and knowledge embeddings.

        Returns a score in [0, 1] (converted from cosine range [-1, 1]).
        """
        query_emb = self._encode([query], is_query=True)
        knowledge_emb = self._encode([knowledge])
        raw_score = float(np.dot(query_emb[0], knowledge_emb[0]))
        return round((raw_score + 1) / 2, 4)

    def calculate_verdict_continuous(
        self,
        retrieval_score: float,
        nli_score: float,
        T_strict: float,
        T_lenient: float,
        method: str = "sqrt",
        sigmoid_k: float = 10.0,
        sigmoid_pivot: float = 0.5,
    ) -> dict:
        """Continuous Cw-CONLI: threshold varies smoothly with retrieval score.

        Methods:
          sqrt:    T = T_strict - (T_strict - T_lenient) * sqrt(retrieval_score)
          sigmoid: T = T_lenient + (T_strict - T_lenient) / (1 + exp(k*(rs - pivot)))
        """
        if method == "sqrt":
            threshold = (T_strict
                         - (T_strict - T_lenient) * math.sqrt(retrieval_score))
        elif method == "sigmoid":
            threshold = (T_lenient
                         + (T_strict - T_lenient)
                         / (1 + math.exp(sigmoid_k
                                         * (retrieval_score - sigmoid_pivot))))
        else:
            raise ValueError(f"Unknown continuous method: {method}")

        is_verified = nli_score >= threshold

        return {
            "status": "VERIFIED" if is_verified else "HALLUCINATION",
            "mode": f"CONTINUOUS_{method.upper()}",
            "threshold": round(threshold, 4),
            "nli_score": nli_score,
            "retrieval_score": retrieval_score,
            "passed": is_verified,
        }

    def evaluate_sample(
        self,
        knowledge: str,
        query: str,
        response: str,
        condition: str,
        params: dict,
    ) -> dict:
        """Evaluate a single sample under a given condition (C1/C2/C3).

        Args:
            knowledge: Ground-truth context passage
            query: Retrieval query (question for QA, response for summarization)
            response: The response to evaluate
            condition: "C1", "C2", or "C3"
            params: Condition-specific parameters

        Returns:
            dict with prediction, retrieval_score, nli_score, threshold, latency_ms
        """
        start = time.perf_counter()

        retrieval_score = self.compute_retrieval_score(query, knowledge)

        if condition == "C1":
            # RAG-only baseline: no NLI, always accepts
            nli_score = None
            prediction = 0
            threshold = None

        elif condition == "C2":
            # Standard CONLI: fixed threshold
            nli_score = self.verify(premise=knowledge, hypothesis=response)
            T_static = params["T_static"]
            prediction = 0 if nli_score >= T_static else 1
            threshold = T_static

        elif condition == "C3":
            # Cw-CONLI: dynamic threshold
            nli_score = self.verify(premise=knowledge, hypothesis=response)
            method = params.get("method", "tiered")

            if method == "tiered":
                verdict = self.calculate_verdict(
                    retrieval_score, nli_score,
                    params["pivot"], params["T_strict"], params["T_lenient"],
                )
            else:
                verdict = self.calculate_verdict_continuous(
                    retrieval_score, nli_score,
                    params["T_strict"], params["T_lenient"],
                    method=method,
                    sigmoid_k=params.get("sigmoid_k", 10),
                    sigmoid_pivot=params.get("sigmoid_pivot", 0.5),
                )
            prediction = 0 if verdict["passed"] else 1
            threshold = verdict["threshold"]
        else:
            raise ValueError(f"Unknown condition: {condition}")

        elapsed = time.perf_counter() - start

        return {
            "prediction": prediction,
            "retrieval_score": retrieval_score,
            "nli_score": nli_score,
            "threshold": threshold,
            "latency_ms": round(elapsed * 1000, 2),
        }

    def precompute_scores(
        self, knowledge: str, query: str, response: str
    ) -> dict:
        """Pre-compute retrieval and NLI scores (condition-independent).

        Used by the evaluation harness to separate expensive model inference
        from fast threshold sweeping.

        v2: also computes decomposed and windowed scores when flags are set.
        """
        start = time.perf_counter()
        retrieval_score = self.compute_retrieval_score(query, knowledge)

        # v1-style whole-response NLI (always computed for backward compat)
        nli_score_whole = self.verify(premise=knowledge, hypothesis=response)

        # v2: decomposed claim-level NLI
        n_claims = 1
        n_windows = 1
        nli_mean_score = nli_score_whole
        nli_method = "whole"

        if self.use_decomposition:
            decomp = self.verify_decomposed(premise=knowledge, hypothesis=response)
            nli_score = decomp["score"]           # min over claims
            nli_mean_score = decomp["mean_score"]
            n_claims = decomp["n_claims"]
            n_windows = decomp["n_windows"]
            nli_method = "decomposed"
        elif self.use_windowed_nli:
            windowed = self.verify_windowed(premise=knowledge, hypothesis=response)
            nli_score = windowed["score"]
            n_windows = windowed["n_windows"]
            nli_method = windowed["method"]
        else:
            nli_score = nli_score_whole

        elapsed = time.perf_counter() - start

        return {
            "retrieval_score": retrieval_score,
            "nli_score": nli_score,
            "nli_score_whole": nli_score_whole,
            "nli_mean_score": nli_mean_score,
            "n_claims": n_claims,
            "n_windows": n_windows,
            "nli_method": nli_method,
            "latency_ms": round(elapsed * 1000, 2),
        }

    # ==================================================================
    # Shared-Index Retrieval (Experiment 2 - Realistic Retrieval)
    # ==================================================================

    def build_index(self, passages: list, batch_size: int = 64):
        """Build a FAISS index from an arbitrary list of passages.

        Args:
            passages: List of text passages to index
            batch_size: Encoding batch size

        Returns:
            faiss.IndexFlatIP index
        """
        all_embeddings = []
        for i in range(0, len(passages), batch_size):
            batch = passages[i:i + batch_size]
            emb = self._encode(batch)
            all_embeddings.append(emb)

        embeddings = np.vstack(all_embeddings)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        return index

    def retrieve_from_index(
        self, query: str, index, passages: list, k: int = 2
    ) -> dict:
        """Retrieve top-k passages from a given FAISS index.

        Args:
            query: Search query
            index: FAISS index to search
            passages: Original passages (aligned with index)
            k: Number of results

        Returns:
            dict with context, retrieval_score, documents
        """
        query_emb = self._encode([query], is_query=True)
        scores, indices = index.search(query_emb, k)

        raw_score = float(scores[0][0])
        retrieval_score = (raw_score + 1) / 2  # [-1, 1] -> [0, 1]

        documents = [passages[int(idx)] for idx in indices[0]
                     if 0 <= int(idx) < len(passages)]
        context = "\n\n".join(documents)

        return {
            "context": context,
            "retrieval_score": round(retrieval_score, 4),
            "documents": documents,
        }
