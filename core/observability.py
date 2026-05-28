"""
Observability module — structured inference tracing for both models.

Provides:
  - ``InferenceTrace`` dataclass: one record per model call.
  - ``log_trace()``  — append a trace to traces.jsonl (thread-safe).
  - ``load_traces()`` — return all traces as a DataFrame.
  - Latency percentile helpers: p50, p90, p99.
  - Error rate computation.
"""

import json
import uuid
import hashlib
import datetime
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import pandas as pd

from config import TRACES_LOG_PATH

# Thread-safe file write lock
_write_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Trace dataclass
# ---------------------------------------------------------------------------

@dataclass
class InferenceTrace:
    """One record per model inference call."""

    trace_id: str
    eval_run_id: str          # groups traces from one eval batch
    timestamp: str            # ISO-8601 UTC
    model: str                # e.g. "Qwen2.5-0.5B-Instruct" or "gpt-4o-mini"
    model_type: str           # "oss" | "frontier"
    prompt_hash: str          # SHA-256 of the raw prompt (privacy-preserving)
    prompt_preview: str       # first 80 chars of the prompt
    latency_s: float          # end-to-end latency in seconds
    tokens_out: int           # estimated output token count
    tokens_per_second: float  # throughput estimate
    guardrail_triggered: bool # was a safety layer activated?
    guardrail_layer: str      # which layer triggered ("", "input", "output", "llm")
    error: bool               # did the call return an error?
    error_message: str        # error text if error=True
    score: Optional[int]      # LLM-as-Judge score (1-5), None if not judged
    category: str             # eval category ("Hallucination Rate", etc.) or ""
    backend: str              # "hf_space" | "hf_inference" | "openai"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def new_eval_run_id() -> str:
    """Generate a unique ID for one evaluation batch."""
    return str(uuid.uuid4())[:8]


def make_trace(
    *,
    model: str,
    model_type: str,
    prompt: str,
    latency_s: float,
    tokens_out: int,
    eval_run_id: str = "",
    guardrail_triggered: bool = False,
    guardrail_layer: str = "",
    error: bool = False,
    error_message: str = "",
    score: Optional[int] = None,
    category: str = "",
    backend: str = "",
) -> InferenceTrace:
    """Construct an InferenceTrace from raw inference data."""
    prompt_bytes = prompt.encode("utf-8")
    return InferenceTrace(
        trace_id=str(uuid.uuid4()),
        eval_run_id=eval_run_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model=model,
        model_type=model_type,
        prompt_hash=hashlib.sha256(prompt_bytes).hexdigest()[:16],
        prompt_preview=prompt[:80].replace("\n", " "),
        latency_s=round(latency_s, 4),
        tokens_out=tokens_out,
        tokens_per_second=round(tokens_out / latency_s, 2) if latency_s > 0 else 0.0,
        guardrail_triggered=guardrail_triggered,
        guardrail_layer=guardrail_layer,
        error=error,
        error_message=error_message[:200] if error_message else "",
        score=score,
        category=category,
        backend=backend,
    )


def log_trace(trace: InferenceTrace) -> None:
    """Append a trace record to traces.jsonl (thread-safe)."""
    with _write_lock:
        with open(TRACES_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(trace), ensure_ascii=False) + "\n")


def load_traces() -> pd.DataFrame:
    """Load all traces from traces.jsonl as a DataFrame.

    Returns an empty DataFrame if the file doesn't exist or is empty.
    """
    if not TRACES_LOG_PATH.exists():
        return pd.DataFrame()
    records = []
    with open(TRACES_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Analytics helpers
# ---------------------------------------------------------------------------

def latency_percentiles(df: pd.DataFrame, model_type: str = "oss") -> dict:
    """Return p50, p90, p99 latency for a given model_type."""
    col = "latency_s"
    subset = df[df["model_type"] == model_type][col].dropna()
    if subset.empty:
        return {"p50": 0.0, "p90": 0.0, "p99": 0.0}
    return {
        "p50": round(float(subset.quantile(0.50)), 3),
        "p90": round(float(subset.quantile(0.90)), 3),
        "p99": round(float(subset.quantile(0.99)), 3),
    }


def error_rate(df: pd.DataFrame, model_type: str = "oss") -> float:
    """Return the fraction of calls that returned an error."""
    subset = df[df["model_type"] == model_type]
    if subset.empty:
        return 0.0
    return round(float(subset["error"].mean()), 4)


def guardrail_rate(df: pd.DataFrame) -> float:
    """Return the fraction of calls where a guardrail was triggered."""
    if df.empty:
        return 0.0
    return round(float(df["guardrail_triggered"].mean()), 4)
