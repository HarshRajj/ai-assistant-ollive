"""
Content-safety guardrails — 3-layer pipeline.

Layer 1  Pattern matching   Fast keyword/phrase block list (jailbreaks, injections).
Layer 2  Semantic check     Expanded keyword set covering paraphrased harmful intent.
Layer 3  LLM meta-judge     GPT-4o-mini binary safety classifier (optional, opt-in).

Public API
----------
check_input_safety(text, openai_key="", run_llm_layer=False) -> GuardrailResult
check_output_safety(text)                                     -> GuardrailResult
"""

import re
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class GuardrailResult:
    """Result returned by every guardrail check."""
    safe: bool
    layer: str      # "" | "pattern" | "semantic" | "llm" | "output"
    reason: str
    latency_ms: float


GUARDRAIL_ALERT = "[Safety Layer Triggered: Input Blocked due to Risk Pattern]"

# ---------------------------------------------------------------------------
# Layer 1 — Exact jailbreak / prompt-injection phrases
# ---------------------------------------------------------------------------

BLOCKED_PATTERNS: list[str] = [
    # Classic jailbreak commands
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore your instructions",
    "bypass system",
    "override your safety",
    "disregard your programming",
    "pretend you have no rules",
    "act as an unrestricted",
    "you are now",
    "jailbreak",
    "do anything now",
    "developer mode",
    "dan mode",
    "evil mode",
    "no restrictions",
    "without ethical guidelines",
    "forget all constraints",
    "sudo",
]

# ---------------------------------------------------------------------------
# Layer 2 — Semantic keyword expansion (paraphrased harmful intents)
# Covers what layer 1 misses without needing an ML model.
# ---------------------------------------------------------------------------

HARMFUL_INTENT_PHRASES: list[str] = [
    # Hacking / cybercrime
    "hack into", "brute force", "sql injection", "bypass authentication",
    "write malware", "create a virus", "reverse engineer",
    # Weapons / physical harm
    "make a bomb", "build explosives", "synthesize drugs", "make poison",
    "how to stab", "how to shoot", "build a weapon",
    # Illegal activity
    "how to steal", "pick a lock", "forge documents", "identity theft",
    "phishing email", "launder money", "evade police",
    # Abuse / exploitation
    "stalk someone", "spy on someone", "doxx", "child abuse",
]


def _layer1_check(text: str) -> Optional[GuardrailResult]:
    t0 = time.perf_counter()
    lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower:
            return GuardrailResult(
                safe=False,
                layer="pattern",
                reason=f'{GUARDRAIL_ALERT} — matched: "{pattern}"',
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
    return None


def _layer2_check(text: str) -> Optional[GuardrailResult]:
    t0 = time.perf_counter()
    lower = text.lower()
    for phrase in HARMFUL_INTENT_PHRASES:
        if phrase in lower:
            return GuardrailResult(
                safe=False,
                layer="semantic",
                reason=f"Harmful intent detected: '{phrase}'",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
    return None


def _layer3_check(text: str, openai_key: str) -> Optional[GuardrailResult]:
    """LLM meta-judge — binary safety classifier."""
    t0 = time.perf_counter()
    try:
        from openai import OpenAI
        import json as _json
        from config import JUDGE_MODEL_NAME
        from prompts.safety import SAFETY_CLASSIFIER_PROMPT

        prompt = SAFETY_CLASSIFIER_PROMPT.format(text=text[:400])
        client = OpenAI(api_key=openai_key)
        resp = client.chat.completions.create(
            model=JUDGE_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if "```" in raw:
            m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
            raw = m.group(1).strip() if m else "{}"
        parsed = _json.loads(raw)
        if not parsed.get("safe", True):
            return GuardrailResult(
                safe=False,
                layer="llm",
                reason=f"LLM safety judge: {parsed.get('reason', '')}",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
    except Exception:
        pass  # Never let the guardrail itself crash
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_input_safety(
    text: str,
    openai_key: str = "",
    run_llm_layer: bool = False,
) -> GuardrailResult:
    """Run the 3-layer input guardrail pipeline.

    Args:
        text:          User input text.
        openai_key:    Optional OpenAI key (required for layer 3).
        run_llm_layer: If True, run the LLM judge even when layers 1-2 pass.

    Returns:
        GuardrailResult with safe=True if all layers pass.
    """
    t0 = time.perf_counter()

    result = _layer1_check(text)
    if result:
        return result

    result = _layer2_check(text)
    if result:
        return result

    if run_llm_layer and openai_key:
        result = _layer3_check(text, openai_key)
        if result:
            return result

    return GuardrailResult(
        safe=True, layer="", reason="",
        latency_ms=round((time.perf_counter() - t0) * 1000, 2),
    )


# Unsafe output phrases — post-generation filter
UNSAFE_OUTPUT_KEYWORDS: list[str] = [
    "i'll help you hack",
    "here's how to make a bomb",
    "here is how to synthesize",
    "step-by-step instructions to harm",
    "here are instructions for illegal",
]


def check_output_safety(text: str) -> GuardrailResult:
    """Post-generation filter for known harmful phrases in model output."""
    t0 = time.perf_counter()
    lower = text.lower()
    for kw in UNSAFE_OUTPUT_KEYWORDS:
        if kw in lower:
            return GuardrailResult(
                safe=False,
                layer="output",
                reason="Response filtered by output safety layer.",
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
    return GuardrailResult(
        safe=True, layer="", reason="",
        latency_ms=round((time.perf_counter() - t0) * 1000, 2),
    )
