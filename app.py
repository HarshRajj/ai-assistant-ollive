"""
Ollive AI Benchmarking Arena — Entry Point
==========================================
A Streamlit application comparing an Open-Source LLM (Qwen 2.5) with a
Frontier model (OpenAI GPT-4o-mini) in a split-screen arena.

Run with:  uv run streamlit run app.py
"""

import os
import streamlit as st

from config import OSS_MODEL_ID, FRONTIER_MODEL_NAME
from ui import inject_css, render_arena_page, render_eval_page

# ---------------------------------------------------------------------------
# Page configuration (must be the first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Ollive AI Arena",
    page_icon="🫒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject premium CSS
inject_css()

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "guardrail_log" not in st.session_state:
    st.session_state.guardrail_log = []

# ---------------------------------------------------------------------------
# Hybrid Credential Shield  (sidebar → env var fallback)
# ---------------------------------------------------------------------------

def resolve_openai_key() -> str:
    """Resolve the OpenAI API key with multi-tier fallback.

    Priority:
      1. User-provided key in the sidebar password field (volatile, in-memory only).
      2. Server-side OPENAI_API_KEY from environment variables.
    """
    sidebar_key = st.session_state.get("_openai_key_input", "")
    if sidebar_key:
        return sidebar_key
    return os.environ.get("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🫒 Ollive Arena")
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["🏟️ Arena", "📊 Evaluation Dashboard"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ---- Credential Shield UI ----
    st.markdown("**🔑 Credentials**")
    st.text_input(
        "OpenAI API Key",
        type="password",
        key="_openai_key_input",
        placeholder="sk-... (optional if env var set)",
        help="Entered key is stored in volatile session memory only — never written to disk.",
    )

    resolved_key = resolve_openai_key()
    if resolved_key:
        st.caption("🟢 OpenAI key configured")
    else:
        st.caption("🔴 OpenAI key missing — enter above or set `OPENAI_API_KEY` env var")

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    st.markdown("**Models**")
    st.caption(f"🔓 OSS: `{OSS_MODEL_ID.split('/')[-1]}`")
    st.caption(f"🔒 Frontier: `{FRONTIER_MODEL_NAME}`")

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    st.caption("Built for the Ollive AI take-home assessment.")

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------

if page == "🏟️ Arena":
    render_arena_page(openai_key=resolved_key)
elif page == "📊 Evaluation Dashboard":
    render_eval_page(openai_key=resolved_key)
