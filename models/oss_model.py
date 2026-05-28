"""
Open-Source model client — Qwen 2.5 with dual-backend support.

Backend A: ``hf_space``      — Deployed HF Space Gradio API (default)
Backend B: ``hf_inference``  — HuggingFace Serverless Inference API (fallback)

Provides:
  - ``query_oss_model(messages, placeholder, ...)``
    Queries the model, optionally writes result into a Streamlit placeholder,
    logs an observability trace, and returns metrics.
  - ``query_oss_model_headless(messages, ...)``
    Non-streaming variant for the evaluation pipeline (no placeholder).
"""

import time
import json
import urllib.request
import urllib.parse

from config import OSS_MODEL_ID, SYSTEM_PROMPT, HF_TOKEN, OSS_BACKEND, HF_SPACE_URL, estimate_tokens
from core.observability import make_trace, log_trace


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_messages(messages: list[dict]) -> list[dict]:
    """Prepend the system prompt to a list of user/assistant messages."""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]


def _query_hf_space(
    messages: list[dict],
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> tuple[str, float, int, bool]:
    """Call the deployed HF Space Gradio REST API.

    Returns:
        (text, latency_s, tokens, guardrail_triggered)
    """
    payload = json.dumps({
        "data": [
            json.dumps(messages),
            max_tokens,
            temperature,
        ]
    }).encode("utf-8")

    url = f"{HF_SPACE_URL.rstrip('/')}/run/predict"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ollive-ai-arena/1.0",
        },
        method="POST",
    )

    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    latency = time.perf_counter() - t0

    # Gradio wraps result in {"data": [result_dict]}
    result = body.get("data", [{}])[0]
    if isinstance(result, str):
        result = json.loads(result)

    text = result.get("text", "(empty response)")
    tokens = result.get("tokens", estimate_tokens(text))
    guardrail = result.get("guardrail_triggered", False)
    return text, latency, tokens, guardrail


def _query_hf_inference(messages: list[dict]) -> tuple[str, float, int]:
    """HuggingFace Serverless Inference API fallback."""
    from huggingface_hub import InferenceClient

    hf_messages = _build_messages(messages)
    client = InferenceClient(model=OSS_MODEL_ID, token=HF_TOKEN or None)
    t0 = time.perf_counter()
    result = client.chat_completion(
        messages=hf_messages,
        max_tokens=512,
        temperature=0.7,
    )
    latency = time.perf_counter() - t0
    text = result.choices[0].message.content.strip() if result.choices else "(empty response)"
    return text, latency, estimate_tokens(text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def query_oss_model(
    messages: list[dict],
    placeholder=None,
    eval_run_id: str = "",
    category: str = "",
    tools_enabled: bool = False,
) -> tuple[str, float, int]:
    """Query the OSS model (HF Space or HF Inference) with observability.

    Args:
        messages:      Conversation history (user/assistant dicts).
        placeholder:   Optional ``st.empty()`` container.
        eval_run_id:   ID for the current evaluation batch (for tracing).
        category:      Eval category label (for tracing).
        tools_enabled: If True, tool-use context injection is applied upstream.

    Returns:
        (full_text, latency_seconds, estimated_tokens)
    """
    prompt_preview = messages[-1]["content"] if messages else ""
    backend = OSS_BACKEND
    error = False
    error_msg = ""
    guardrail_triggered = False
    text = ""
    latency = 0.0
    tokens = 0

    try:
        if backend == "hf_space":
            try:
                text, latency, tokens, guardrail_triggered = _query_hf_space(messages)
            except Exception as e:
                # Fallback to HF Inference if Space is unavailable
                if HF_TOKEN:
                    backend = "hf_inference (fallback)"
                    text, latency, tokens = _query_hf_inference(messages)
                else:
                    raise e

        elif backend == "hf_inference":
            if not HF_TOKEN:
                text = "⚠️ HF_TOKEN not set in .env. Required for HF Inference backend."
                error = True
                error_msg = text
            else:
                text, latency, tokens = _query_hf_inference(messages)
        else:
            text = f"⚠️ Unknown OSS_BACKEND: {backend}"
            error = True
            error_msg = text

    except Exception as e:
        latency = time.perf_counter()
        text = f"⚠️ OSS model error: {e}"
        error = True
        error_msg = str(e)

    if placeholder is not None:
        if error:
            placeholder.error(text)
        else:
            placeholder.markdown(text)

    # Log observability trace
    trace = make_trace(
        model=OSS_MODEL_ID.split("/")[-1],
        model_type="oss",
        prompt=prompt_preview,
        latency_s=latency,
        tokens_out=tokens,
        eval_run_id=eval_run_id,
        guardrail_triggered=guardrail_triggered,
        guardrail_layer="input" if guardrail_triggered else "",
        error=error,
        error_message=error_msg,
        category=category,
        backend=backend,
    )
    try:
        log_trace(trace)
    except Exception:
        pass  # Never let observability break inference

    return text, latency, tokens


def query_oss_model_headless(
    messages: list[dict],
    eval_run_id: str = "",
    category: str = "",
) -> tuple[str, float, int]:
    """Non-streaming query for the evaluation pipeline."""
    return query_oss_model(
        messages,
        placeholder=None,
        eval_run_id=eval_run_id,
        category=category,
    )
