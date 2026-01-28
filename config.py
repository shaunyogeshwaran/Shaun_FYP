"""
AFLHR Lite - Configuration Module
Centralized configuration, model IDs, and knowledge base.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =============================================================================
# Model IDs
# =============================================================================
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VERIFIER_MODEL = "FacebookAI/roberta-large-mnli"
GENERATOR_MODEL = "llama-3.1-8b-instant"  # Groq model ID

# =============================================================================
# Threshold Defaults (calibrate after first run)
# =============================================================================
DEFAULT_PIVOT = 0.75
DEFAULT_STRICT_THRESHOLD = 0.95
DEFAULT_LENIENT_THRESHOLD = 0.70

# =============================================================================
# Knowledge Base
# =============================================================================
# Topic A: University of Westminster (3 paragraphs)
# Topic B: AI Hallucinations (2 paragraphs)
# Topic C: Climate of Sri Lanka - Distractor (1 paragraph)

KNOWLEDGE_BASE = [
    # --- Topic A: University of Westminster ---
    """The University of Westminster was founded in 1838 as the Royal Polytechnic Institution,
    making it the first polytechnic in the United Kingdom. It was established by Sir George
    Cayley, a pioneer of aeronautics, with the aim of demonstrating new technologies and
    inventions to the public. The institution was granted a Royal Charter by Queen Victoria
    in 1839, reflecting its significance in promoting scientific education and innovation
    during the Victorian era.""",

    """The University of Westminster operates four campuses across London: Regent Street,
    Cavendish, Marylebone, and Harrow. The historic Regent Street campus is located in the
    heart of London's West End, near Oxford Circus. The Cavendish campus houses the Faculty
    of Science and Technology, while Marylebone focuses on Architecture and the Built
    Environment. The Harrow campus, located in northwest London, specializes in media,
    arts, and design programs.""",

    """The University of Westminster has a rich history of technological firsts. In 1896,
    the Lumière brothers held the first public demonstration of moving pictures in the UK
    at the Royal Polytechnic Institution. The university was granted full university status
    in 1992 under the Further and Higher Education Act. Today, it serves approximately
    19,000 students from over 160 countries and offers more than 300 undergraduate and
    postgraduate courses.""",

    # --- Topic B: AI Hallucinations ---
    """AI hallucination refers to the phenomenon where artificial intelligence models,
    particularly large language models (LLMs), generate outputs that appear plausible
    but are factually incorrect, nonsensical, or completely fabricated. Unlike human
    hallucinations which involve perceiving things that aren't there, AI hallucinations
    occur when models confidently produce false information as if it were true. This
    happens because LLMs are trained to predict likely word sequences rather than to
    verify factual accuracy.""",

    """There are several types of AI hallucinations. Factual hallucinations occur when
    models generate incorrect facts, dates, or statistics. Entity hallucinations happen
    when models reference non-existent people, places, or organizations. Attribution
    errors occur when models incorrectly attribute quotes or actions to the wrong sources.
    Fabricated citations are particularly problematic in academic contexts, where models
    may invent scholarly references that do not exist. These hallucinations pose significant
    risks in applications requiring factual accuracy.""",

    # --- Topic C: Climate of Sri Lanka (Distractor) ---
    """Sri Lanka has a tropical monsoon climate characterized by warm temperatures throughout
    the year and distinct wet and dry seasons. The island experiences two monsoon periods:
    the southwest monsoon from May to September affecting the western and southern regions,
    and the northeast monsoon from December to February impacting the northern and eastern
    areas. Average temperatures range from 27°C to 30°C in coastal areas, while the central
    highlands are cooler at around 15°C to 20°C. Annual rainfall varies significantly across
    regions, from 900mm in the driest areas to over 5,000mm in the wettest zones.""",
]

# =============================================================================
# Offline Mode Mock Response
# =============================================================================
OFFLINE_MOCK_RESPONSE = "Based on the available information, this is a mock response generated in offline mode. The verification system will still analyze this response against the retrieved context."

# =============================================================================
# System Prompts
# =============================================================================
GENERATION_SYSTEM_PROMPT = """You are a precise assistant. Answer the question using ONLY the context provided. Be concise."""
