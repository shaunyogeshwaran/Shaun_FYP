"""
AFLHR Lite - Streamlit Application
Confidence-Weighted Hallucination Verification Demo
"""

# CRITICAL: Set environment variables BEFORE any other imports
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import streamlit as st
from engine import AFLHREngine
from config import (
    DEFAULT_PIVOT,
    DEFAULT_STRICT_THRESHOLD,
    DEFAULT_LENIENT_THRESHOLD,
    GROQ_API_KEY,
)


# =============================================================================
# Page Configuration
# =============================================================================
st.set_page_config(
    page_title="AFLHR Lite",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# Cache the engine to avoid reloading models on every interaction
# =============================================================================
@st.cache_resource
def load_engine():
    """Load the AFLHR engine (cached to prevent reloading)."""
    try:
        with st.spinner("Loading models... This may take a minute on first run."):
            return AFLHREngine()
    except Exception as e:
        st.error(f"Failed to load engine: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


# =============================================================================
# Sidebar Configuration
# =============================================================================
def render_sidebar():
    """Render the sidebar with configuration options."""
    st.sidebar.header("Configuration")

    # Threshold sliders
    st.sidebar.subheader("Threshold Settings")

    pivot = st.sidebar.slider(
        "Pivot Point",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_PIVOT,
        step=0.05,
        help="Retrieval scores below this use STRICT threshold, above use LENIENT"
    )

    strict_threshold = st.sidebar.slider(
        "Strict Threshold",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_STRICT_THRESHOLD,
        step=0.05,
        help="NLI threshold when retrieval confidence is LOW"
    )

    lenient_threshold = st.sidebar.slider(
        "Lenient Threshold",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_LENIENT_THRESHOLD,
        step=0.05,
        help="NLI threshold when retrieval confidence is HIGH"
    )

    st.sidebar.divider()

    # Offline mode
    offline_mode = st.sidebar.checkbox(
        "Offline Mode",
        value=False if GROQ_API_KEY else True,
        help="Use mock LLM response (RAG + Verification still run)"
    )

    if not GROQ_API_KEY:
        st.sidebar.warning("No API key found. Offline mode enabled.")

    st.sidebar.divider()

    # Debug info section
    st.sidebar.subheader("Debug Info")
    debug_placeholder = st.sidebar.empty()

    return pivot, strict_threshold, lenient_threshold, offline_mode, debug_placeholder


# =============================================================================
# Main UI
# =============================================================================
def main():
    """Main application entry point."""

    # Title
    st.title("AFLHR Lite: Confidence-Weighted Verification")
    st.markdown("""
    *Adaptive Framework for LLM Hallucination Reduction*

    This system uses retrieval confidence to dynamically adjust verification thresholds:
    - **High retrieval confidence** → Lower threshold (trust evidence)
    - **Low retrieval confidence** → Higher threshold (be skeptical)
    """)

    st.divider()

    # Load engine
    engine = load_engine()

    if engine is None:
        st.error("Engine failed to load. Check the error above.")
        st.stop()

    # Render sidebar and get settings
    pivot, strict_threshold, lenient_threshold, offline_mode, debug_placeholder = render_sidebar()

    # Query input
    query = st.text_input(
        "Enter your query:",
        placeholder="e.g., When was the University of Westminster founded?"
    )

    # Verify button
    col_btn, col_status = st.columns([1, 4])
    with col_btn:
        verify_button = st.button("Verify", type="primary", use_container_width=True)

    # Process query
    if verify_button and query:
        with st.spinner("Processing..."):
            # Run the pipeline
            result = engine.run_pipeline(
                query=query,
                pivot=pivot,
                strict_threshold=strict_threshold,
                lenient_threshold=lenient_threshold,
                offline_mode=offline_mode
            )

        # Update debug info
        debug_placeholder.metric(
            "Raw Retrieval Score",
            f"{result['retrieval']['raw_score']:.4f}"
        )

        st.divider()

        # Results in 3 columns
        col1, col2, col3 = st.columns(3)

        # Column 1: RAG Results
        with col1:
            st.subheader("📚 Evidence (RAG)")

            # Retrieval score with color coding
            retrieval_score = result['retrieval']['retrieval_score']
            score_color = "green" if retrieval_score >= pivot else "red"

            st.markdown(f"**Retrieval Confidence:**")
            st.markdown(
                f"<span style='color: {score_color}; font-size: 24px; font-weight: bold;'>"
                f"{retrieval_score:.2%}</span>",
                unsafe_allow_html=True
            )

            mode_text = "LENIENT mode" if retrieval_score >= pivot else "STRICT mode"
            st.caption(f"Score {'≥' if retrieval_score >= pivot else '<'} pivot ({pivot}) → {mode_text}")

            st.markdown("**Retrieved Context:**")
            with st.expander("View retrieved documents", expanded=True):
                for i, doc in enumerate(result['retrieval']['documents']):
                    st.markdown(f"**Document {i+1}:**")
                    st.text(doc[:300] + "..." if len(doc) > 300 else doc)
                    if i < len(result['retrieval']['documents']) - 1:
                        st.divider()

        # Column 2: Generation Results
        with col2:
            st.subheader("🤖 Generation (LLM)")

            if offline_mode:
                st.info("Running in Offline Mode - Mock response used")

            st.markdown("**Generated Response:**")
            st.write(result['generation'])

        # Column 3: Verification Results
        with col3:
            st.subheader("✅ Verification (NLI)")

            verdict = result['verdict']

            # NLI Score
            st.markdown("**Entailment Score:**")
            st.markdown(f"<span style='font-size: 24px; font-weight: bold;'>{verdict['nli_score']:.2%}</span>",
                       unsafe_allow_html=True)

            # Threshold used
            st.markdown("**Threshold Applied:**")
            threshold_text = f"{verdict['threshold']:.2%} ({verdict['mode']})"
            st.markdown(f"`{threshold_text}`")

            st.caption(verdict['reasoning'])

            st.divider()

            # Final verdict badge
            st.markdown("**Final Verdict:**")
            if verdict['status'] == "VERIFIED":
                st.success(f"✅ {verdict['status']}", icon="✅")
                st.balloons()
            else:
                st.error(f"❌ {verdict['status']}", icon="❌")

            # Explanation
            comparison = "≥" if verdict['passed'] else "<"
            st.caption(
                f"NLI Score ({verdict['nli_score']:.2%}) {comparison} "
                f"Threshold ({verdict['threshold']:.2%})"
            )

    elif verify_button and not query:
        st.warning("Please enter a query to verify.")

    # Footer with knowledge base info
    st.divider()
    with st.expander("ℹ️ About the Knowledge Base"):
        st.markdown("""
        This demo uses a curated knowledge base with three topics:

        1. **University of Westminster** - History, campuses, and notable achievements
        2. **AI Hallucinations** - Definition and types of hallucinations in LLMs
        3. **Climate of Sri Lanka** - Weather patterns (distractor topic)

        The system retrieves relevant context and verifies LLM responses against it.
        """)


if __name__ == "__main__":
    main()
