"""
tools.py — All tool logic in one place.

Three tools are available:
  - calculator  Safe arithmetic evaluation (no eval())
  - web_search  DuckDuckGo Instant Answer API (no API key needed)
  - datetime    Current date and time

Entry point for the rest of the app:
    from tools import detect_and_run

    annotation, context = detect_and_run("What is 15 * 23?")
    # annotation = "calculator"
    # context    = "[Tool result]: ..."
"""

import re
import math
import datetime
import urllib.request
import urllib.parse
import json
from typing import Optional

# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

def _calculator(query: str) -> str:
    """Safely evaluate a math expression found in the query string."""
    # Normalize operators
    expr = query.replace("^", "**").replace("×", "*").replace("÷", "/")

    # Handle sqrt(x) before extraction
    expr = re.sub(
        r"sqrt\(([^)]+)\)",
        lambda m: str(math.sqrt(float(m.group(1)))),
        expr,
    )

    # Extract the math expression (digits, operators, parens, dots)
    match = re.search(r"[\d][\d\s\+\-\*\/\(\)\.\^\%e]*", expr)
    if not match:
        return "Could not find a math expression."
    expr = match.group(0).strip().rstrip("?.,;")

    # Only allow safe characters
    if not re.match(r"^[\d\s\+\-\*\/\(\)\.\%\*e]+$", expr):
        return "Unsupported characters in expression."

    try:
        result = eval(compile(expr, "<string>", "eval"), {"__builtins__": {}}, {})  # noqa: S307
        result = float(result)
        formatted = f"{int(result):,}" if result == int(result) else f"{result:,.6g}"
        return f"**Calculator**: `{expr.strip()}` = **{formatted}**"
    except ZeroDivisionError:
        return "Division by zero."
    except Exception as e:
        return f"Could not evaluate: {e}"


# ---------------------------------------------------------------------------
# Web Search (DuckDuckGo Instant Answer — free, no API key)
# ---------------------------------------------------------------------------

def _web_search(query: str) -> str:
    """Search using DuckDuckGo Instant Answer API."""
    # Strip trigger words
    clean = query.strip()
    for prefix in ("search for", "look up", "find", "search:"):
        if clean.lower().startswith(prefix):
            clean = clean[len(prefix):].strip()
            break

    params = urllib.parse.urlencode({"q": clean, "format": "json", "no_html": 1, "skip_disambig": 1})
    url = f"https://api.duckduckgo.com/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ollive-ai/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        result = (
            data.get("Abstract")
            or data.get("Answer")
            or (data["RelatedTopics"][0].get("Text") if data.get("RelatedTopics") else "")
        )
        if result:
            source = data.get("AbstractURL") or "DuckDuckGo"
            return f"**Web Search**: {result.strip()}\n   _Source: {source}_"
        return f"**Web Search**: No instant answer found for `{clean}`."
    except Exception as e:
        return f"**Web Search**: Failed — {e}"


# ---------------------------------------------------------------------------
# DateTime
# ---------------------------------------------------------------------------

def _datetime(_query: str = "") -> str:
    """Return current date and time."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return (
        f"**Date & Time**: "
        f"`{now.strftime('%A, %B %d %Y')}` — "
        f"`{now.strftime('%H:%M:%S UTC')}`"
    )


# ---------------------------------------------------------------------------
# Tool registry + intent detection
# ---------------------------------------------------------------------------

# (tool_name, regex_triggers, function)
_TOOLS: list[tuple[str, list[str], callable]] = [
    ("datetime", [
        r"\bwhat\s+(time|date|day)\b",
        r"\bcurrent\s+(time|date)\b",
        r"\btoday\b",
        r"\bright now\b.*\btime\b",
    ], _datetime),

    ("calculator", [
        r"[\d]+\s*[\+\-\*\/\^×÷]\s*[\d]+",          # bare expression like "15 * 23"
        r"\b(calculate|compute|what\s+is)\b.*\d",     # "what is 2+2"
        r"\b(sqrt|square\s+root|sum|product)\b",
    ], _calculator),

    ("web_search", [
        r"\b(search|look\s+up|find\s+info|search\s+for)\b",
        r"\blatest\s+(news|updates?)\b",
        r"\bcurrent\s+(news|events?|status)\b",
    ], _web_search),
]


def detect_and_run(text: str) -> tuple[Optional[str], str]:
    """Detect if a tool is needed, run it, and return the context to inject.

    Returns:
        (tool_name | None, context_string)
        context_string is "" if no tool was triggered.
    """
    lower = text.lower()
    for name, patterns, fn in _TOOLS:
        for pat in patterns:
            if re.search(pat, lower):
                result = fn(text)
                context = (
                    f"[Tool used: {name}]\n"
                    f"Result: {result}\n\n"
                    f"Use this result to answer: {text}"
                )
                return name, context
    return None, ""
