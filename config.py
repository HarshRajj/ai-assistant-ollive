"""
Centralized configuration for the Ollive AI Benchmarking Arena.

All environment variables, model identifiers, API endpoints, and shared
constants live here so every other module can simply
``from config import ...``.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent
EVAL_LOG_PATH: Path = PROJECT_ROOT / "eval_log.jsonl"
TRACES_LOG_PATH: Path = PROJECT_ROOT / "traces.jsonl"
SESSIONS_DIR: Path = PROJECT_ROOT / "sessions"

# ---------------------------------------------------------------------------
# API Keys  (OpenAI key is resolved at runtime via sidebar → env fallback;
#             see app.py `resolve_openai_key()`)
# ---------------------------------------------------------------------------
HF_TOKEN: str = os.getenv("HF_TOKEN", "")

# ---------------------------------------------------------------------------
# Model Identifiers  (configurable — change here to swap models)
# ---------------------------------------------------------------------------
OSS_MODEL_ID: str = "Qwen/Qwen2.5-0.5B-Instruct"
FRONTIER_MODEL_NAME: str = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# OSS Backend selection
#   "hf_inference"  — HuggingFace Serverless Inference API (default)
#   "hf_space"      — Deployed HF Space Gradio endpoint (public, free)
# ---------------------------------------------------------------------------
OSS_BACKEND: str = os.getenv("OSS_BACKEND", "hf_space")

# Public HF Space URL for the OSS model
# Set HF_SPACE_URL in .env to override (e.g. for a custom/GPU space).
HF_SPACE_URL: str = os.getenv(
    "HF_SPACE_URL",
    "https://HarshRajj-ollive-oss.hf.space",
)

# ---------------------------------------------------------------------------
# Shared System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = (
    "You are a helpful, harmless, and honest AI personal assistant called Ollive. "
    "Answer user questions accurately and concisely. If you are unsure, say so. "
    "Never produce harmful, biased, or misleading content."
)

# ---------------------------------------------------------------------------
# Memory configuration
# ---------------------------------------------------------------------------
MEMORY_WINDOW_SIZE: int = 10       # max turns kept in sliding window
MEMORY_SUMMARY_THRESHOLD: int = 8  # turns before summarization kicks in

# ---------------------------------------------------------------------------
# Cost data (USD per 1K tokens — estimates as of 2025)
# ---------------------------------------------------------------------------
COST_TABLE: list[dict] = [
    {
        "Model": "Qwen2.5-0.5B-Instruct",
        "Platform": "HF Spaces (Free CPU)",
        "Type": "OSS",
        "Avg Latency (s)": "10–25",
        "Cost / 1K tokens": "$0.00",
        "Cost / Month @ 100K tok": "$0.00",
        "Notes": "Free tier; shared CPU; cold-start ~30s",
    },
    {
        "Model": "Qwen2.5-0.5B-Instruct",
        "Platform": "HF Spaces (Pro GPU T4)",
        "Type": "OSS",
        "Avg Latency (s)": "1–3",
        "Cost / 1K tokens": "~$0.001",
        "Cost / Month @ 100K tok": "~$0.10",
        "Notes": "$9/mo HF Pro; T4 GPU; fast inference",
    },
    {
        "Model": "Qwen2.5-0.5B-Instruct",
        "Platform": "Modal (A10G, serverless)",
        "Type": "OSS",
        "Avg Latency (s)": "0.5–1.5",
        "Cost / 1K tokens": "~$0.0006",
        "Cost / Month @ 100K tok": "~$0.06",
        "Notes": "$0.000612/s A10G; pay-per-use",
    },
    {
        "Model": "Qwen2.5-0.5B-Instruct",
        "Platform": "RunPod (RTX 3090)",
        "Type": "OSS",
        "Avg Latency (s)": "0.3–1.0",
        "Cost / 1K tokens": "~$0.0004",
        "Cost / Month @ 100K tok": "~$0.04",
        "Notes": "$0.22/hr spot; very cheap for sustained load",
    },
    {
        "Model": "Qwen2.5-0.5B-Instruct",
        "Platform": "Replicate",
        "Type": "OSS",
        "Avg Latency (s)": "1–4",
        "Cost / 1K tokens": "~$0.0015",
        "Cost / Month @ 100K tok": "~$0.15",
        "Notes": "$0.0002/sec; coldboot adds ~5s",
    },
    {
        "Model": "gpt-4o-mini",
        "Platform": "OpenAI API",
        "Type": "Frontier",
        "Avg Latency (s)": "1–3",
        "Cost / 1K tokens": "$0.00015 in / $0.0006 out",
        "Cost / Month @ 100K tok": "~$0.075",
        "Notes": "Official API; SLA 99.9%; per-token billing",
    },
]

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimate token count from text using the word→token heuristic.

    OpenAI's rule of thumb: ~1.33 tokens per English word.
    """
    return int(len(text.split()) * 1.33)
