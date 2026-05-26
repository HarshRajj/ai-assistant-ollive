"""
Content-safety guardrails for input and output filtering.

Provides:
  - ``check_input_safety(text)`` — blocks jailbreak / prompt-injection patterns.
  - ``check_output_safety(text)`` — post-generation filter for harmful content.
"""

# ---------------------------------------------------------------------------
# Blocked input patterns (jailbreak / prompt injection / adversarial vectors)
# ---------------------------------------------------------------------------
BLOCKED_PATTERNS: list[str] = [
    # Explicit jailbreak commands (spec-required)
    "ignore previous instructions",
    "bypass system",
    "sudo",
    # Extended adversarial patterns
    "ignore all previous instructions",
    "ignore your instructions",
    "you are now",
    "act as an unrestricted",
    "pretend you have no rules",
    "disregard your programming",
    "override your safety",
    "jailbreak",
    "do anything now",
    "developer mode",
]

# ---------------------------------------------------------------------------
# Unsafe output keywords
# ---------------------------------------------------------------------------
UNSAFE_OUTPUT_KEYWORDS: list[str] = [
    "I'll help you hack",
    "here's how to make a bomb",
    "here is how to synthesize",
    "step-by-step instructions to harm",
    "here are instructions for illegal",
]

# Guardrail alert message (matches spec wording exactly)
GUARDRAIL_ALERT = "[Safety Layer Triggered: Input Blocked due to Risk Pattern]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_input_safety(text: str) -> tuple[bool, str]:
    """Check user input for jailbreak / prompt-injection attempts.

    Returns:
        (is_safe, reason)  — ``is_safe`` is False when the input is blocked.
    """
    lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower:
            return False, f'{GUARDRAIL_ALERT} — matched: "{pattern}"'
    return True, ""


def check_output_safety(text: str) -> tuple[bool, str]:
    """Post-generation filter that catches known harmful phrases.

    Returns:
        (is_safe, reason)  — ``is_safe`` is False when the output is filtered.
    """
    lower = text.lower()
    for kw in UNSAFE_OUTPUT_KEYWORDS:
        if kw.lower() in lower:
            return False, "Response was filtered by the output safety layer."
    return True, ""
