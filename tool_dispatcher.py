"""
Tool dispatcher — intent detection and tool execution.

Provides:
  - ``detect_tool_intent(text)``  → (tool_name | None, extracted_query)
  - ``dispatch_tool(tool_name, query)`` → result_string
  - ``build_tool_context(text)`` → (tool_annotation, injected_context | "")
"""

import re
from typing import Optional

from tools import TOOL_REGISTRY


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

# Ordered intent patterns: (tool_name, regex_patterns)
_INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    ("datetime", [
        r"\bwhat\s+(time|date|day)\b",
        r"\bcurrent\s+(time|date|datetime)\b",
        r"\btoday['s]*\s+(date|day)\b",
        r"\bwhat\s+day\s+is\s+it\b",
        r"\bwhat['s]+\s+today\b",
        r"\bright\s+now\b.*\btime\b",
    ]),
    ("calculator", [
        r"\b(calculate|compute|eval|solve|what\s+is)\b.*[\d\+\-\*\/\^×÷]",
        r"[\d]+\s*[\+\-\*\/\^×÷]\s*[\d]+",
        r"\b(sum|product|quotient|remainder|sqrt|square\s+root)\b",
        r"\bmath\b.*\b[\d]+\b",
        r"\bhow\s+much\s+is\b.*[\d]+",
    ]),
    ("web_search", [
        r"\b(search|look\s+up|find\s+info|search\s+for)\b",
        r"\blatest\s+(news|updates?|info|information)\b",
        r"\bwhat\s+(is|are)\s+the\s+latest\b",
        r"\bcurrent\s+(news|events?|status)\b",
        r"\bwho\s+is\s+the\s+(current|new|latest)\b",
    ]),
]


def detect_tool_intent(text: str) -> tuple[Optional[str], str]:
    """Detect if the user's message should trigger a tool call.

    Returns:
        (tool_name, cleaned_query) — tool_name is None if no tool matches.
    """
    lower = text.lower()
    for tool_name, patterns in _INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, lower):
                return tool_name, text
    return None, text


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def dispatch_tool(tool_name: str, query: str) -> str:
    """Call the named tool with the given query.

    Args:
        tool_name: Key in TOOL_REGISTRY.
        query:     The original user query.

    Returns:
        Formatted result string from the tool.
    """
    if tool_name not in TOOL_REGISTRY:
        return f"⚠️ Unknown tool: `{tool_name}`"
    try:
        return TOOL_REGISTRY[tool_name]["fn"](query)
    except Exception as e:
        return f"⚠️ Tool `{tool_name}` error: {e}"


# ---------------------------------------------------------------------------
# High-level helper used by model callers
# ---------------------------------------------------------------------------

def build_tool_context(text: str) -> tuple[Optional[str], str]:
    """Detect intent, run the tool, and return annotation + context string.

    Args:
        text: Raw user message.

    Returns:
        (tool_annotation, context_to_inject)
        - ``tool_annotation``: short string like "calculator" or None
        - ``context_to_inject``: the tool result to prepend to the prompt,
          or "" if no tool was used.
    """
    tool_name, query = detect_tool_intent(text)
    if tool_name is None:
        return None, ""

    result = dispatch_tool(tool_name, query)
    context = (
        f"[Tool: {TOOL_REGISTRY[tool_name]['description']}]\n"
        f"Tool Result: {result}\n\n"
        f"Use the above tool result to help answer the user's question: {text}"
    )
    return tool_name, context
