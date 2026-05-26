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

# ---------------------------------------------------------------------------
# API Keys  (OpenAI key is resolved at runtime via sidebar → env fallback;
#             see app.py `resolve_openai_key()`)
# ---------------------------------------------------------------------------
HF_TOKEN: str = os.getenv("HF_TOKEN", "")

# ---------------------------------------------------------------------------
# Model Identifiers  (configurable — change here to swap models)
# ---------------------------------------------------------------------------
OSS_MODEL_ID: str = "Qwen/Qwen2.5-7B-Instruct"
FRONTIER_MODEL_NAME: str = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# Shared System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = (
    "You are a helpful, harmless, and honest AI personal assistant called Ollive. "
    "Answer user questions accurately and concisely. If you are unsure, say so. "
    "Never produce harmful, biased, or misleading content."
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimate token count from text using the word→token heuristic.

    OpenAI's rule of thumb: ~1.33 tokens per English word.
    """
    return int(len(text.split()) * 1.33)
