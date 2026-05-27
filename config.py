"""
Centralized configuration for the Ollive AI Benchmarking Arena.
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

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
HF_TOKEN: str = os.getenv("HF_TOKEN", "")

# ---------------------------------------------------------------------------
# Model identifiers
# ---------------------------------------------------------------------------
OSS_MODEL_ID: str = "Qwen/Qwen2.5-0.5B-Instruct"
FRONTIER_MODEL_NAME: str = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# OSS backend
#   "hf_space"     — deployed HF Space Gradio endpoint (default)
#   "hf_inference" — HuggingFace Serverless Inference API (fallback)
# ---------------------------------------------------------------------------
OSS_BACKEND: str = os.getenv("OSS_BACKEND", "hf_space")
HF_SPACE_URL: str = os.getenv(
    "HF_SPACE_URL",
    "https://HarshRajj-ollive-oss.hf.space",
)

# ---------------------------------------------------------------------------
# Shared system prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = (
    "You are a helpful, harmless, and honest AI personal assistant called Ollive. "
    "Answer user questions accurately and concisely. If you are unsure, say so. "
    "Never produce harmful, biased, or misleading content."
)

# ---------------------------------------------------------------------------
# Memory settings
# ---------------------------------------------------------------------------
MEMORY_WINDOW_SIZE: int = 10        # max turns kept in full
MEMORY_SUMMARY_THRESHOLD: int = 8   # summarize older turns beyond this

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimate token count: ~1.33 tokens per English word (OpenAI heuristic)."""
    return int(len(text.split()) * 1.33)
