"""
AFLHR Lite - Core Engine Module
Handles retrieval, generation, and verification logic.
"""

import os
# Disable MPS and tokenizer parallelism to prevent segfaults
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from config import (
    EMBEDDING_MODEL,
    VERIFIER_MODEL,
    GENERATOR_MODEL,
    GROQ_API_KEY,
    KNOWLEDGE_BASE,
    GENERATION_SYSTEM_PROMPT,
    OFFLINE_MOCK_RESPONSE,
)


class AFLHREngine:
    """
    Adaptive Framework for LLM Hallucination Reduction - Lite Version

    Two-layer pipeline:
    1. RAG Layer: Retrieval with confidence scoring
    2. Verification Layer: NLI-based verification with dynamic thresholds
    """

    def __init__(self):
        """Initialize models and build the knowledge base index."""
        print("Initializing AFLHR Engine...")

        # Use CPU to avoid MPS segfaults
        self.device = torch.device("cpu")
        print("Using CPU for all models (stable mode)")

        # Load embedding model using transformers directly (avoids sentence-transformers segfault)
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embed_tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        self.embed_model = AutoModel.from_pretrained(EMBEDDING_MODEL)
        self.embed_model.to(self.device)
        self.embed_model.eval()

        # Load NLI verifier model
        print(f"Loading verifier model: {VERIFIER_MODEL}")
        self.tokenizer = AutoTokenizer.from_pretrained(VERIFIER_MODEL)
        self.verifier_model = AutoModelForSequenceClassification.from_pretrained(VERIFIER_MODEL)
        self.verifier_model.to(self.device)
        self.verifier_model.eval()

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

        print("AFLHR Engine initialized successfully!")

    def _encode(self, texts: list) -> np.ndarray:
        """
        Generate embeddings using mean pooling (replicates SentenceTransformer behavior).

        Args:
            texts: List of strings to encode

        Returns:
            Normalized embeddings as numpy array
        """
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
        query_embedding = self._encode([query])

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

    def verify(self, premise: str, hypothesis: str) -> float:
        """
        Verify the hypothesis against the premise using NLI.

        Args:
            premise: The retrieved context (evidence)
            hypothesis: The generated response (claim to verify)

        Returns:
            Entailment probability (0-1)
        """
        # Tokenize with truncation to prevent overflow
        # CRITICAL: truncation="only_first" truncates premise, keeps hypothesis intact
        inputs = self.tokenizer(
            premise,
            hypothesis,
            return_tensors="pt",
            truncation="only_first",
            max_length=512,
            padding=True
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Run inference
        with torch.no_grad():
            outputs = self.verifier_model(**inputs)
            logits = outputs.logits

            # Apply softmax to get probabilities
            # RoBERTa-MNLI output order: [contradiction, neutral, entailment]
            probabilities = torch.softmax(logits, dim=1)

            # Extract entailment probability (index 2)
            entailment_prob = probabilities[0][2].item()

        return round(entailment_prob, 4)

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
        - Low retrieval confidence → Strict threshold (be skeptical)
        - High retrieval confidence → Lenient threshold (trust evidence)

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
            reasoning = "Low retrieval confidence → applying strict verification"
        else:
            threshold = lenient_threshold
            mode = "LENIENT"
            reasoning = "High retrieval confidence → trusting evidence quality"

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
