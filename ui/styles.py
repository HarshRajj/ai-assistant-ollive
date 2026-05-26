"""
Premium CSS styles for the Ollive AI Playground.

Call ``inject_css()`` once at the top of the Streamlit app to apply.
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
}

/* Chat message styling */
.chat-bubble-user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 6px 0;
    max-width: 85%;
    float: right;
    clear: both;
    box-shadow: 0 2px 12px rgba(102,126,234,0.25);
    animation: fadeInUp 0.3s ease-out;
}

.chat-bubble-assistant {
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    color: #e0e0e0;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 6px 0;
    max-width: 85%;
    float: left;
    clear: both;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(102,126,234,0.18);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label {
    font-size: 0.85rem;
    color: #888;
    margin-top: 4px;
}

/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #aaa;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

/* Divider */
.glow-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
    border: none;
    margin: 24px 0;
    border-radius: 2px;
}

/* Guardrail alert */
.guardrail-alert {
    background: rgba(255, 75, 75, 0.1);
    border-left: 4px solid #ff4b4b;
    padding: 12px 16px;
    border-radius: 0 12px 12px 0;
    margin: 8px 0;
    color: #ff6b6b;
    font-weight: 500;
}
</style>
"""


def inject_css() -> None:
    """Inject the premium CSS into the current Streamlit page."""
    st.markdown(CSS, unsafe_allow_html=True)
