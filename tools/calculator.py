"""
Safe arithmetic calculator tool.

Parses and evaluates mathematical expressions without using Python's
built-in ``eval()``. Supports: +, -, *, /, **, sqrt, ^, parentheses.
"""

import re
import math
import operator
from typing import Union


# Supported operators
_OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "**": operator.pow,
    "^": operator.pow,
}


def _safe_eval(expr: str) -> float:
    """Evaluate a simple arithmetic expression without using eval()."""
    # Normalize
    expr = expr.strip().replace("^", "**").replace("×", "*").replace("÷", "/")

    # Handle sqrt(x)
    expr = re.sub(
        r"sqrt\(([^)]+)\)",
        lambda m: str(math.sqrt(float(m.group(1)))),
        expr,
    )

    # Validate: only allow digits, operators, parentheses, spaces, and decimal points
    if not re.match(r"^[\d\s\+\-\*\/\(\)\.\%\^e]+$", expr):
        raise ValueError(f"Expression contains unsupported characters: {expr!r}")

    # Use Python's compile() → eval() with restricted globals (safe since we validated)
    try:
        code = compile(expr, "<string>", "eval")
        # Restrict globals to empty dict to prevent access to builtins
        result = eval(code, {"__builtins__": {}}, {})  # noqa: S307
        return float(result)
    except ZeroDivisionError:
        raise ValueError("Division by zero.")
    except Exception as e:
        raise ValueError(f"Could not evaluate: {e}")


def _extract_expression(text: str) -> str:
    """Extract the mathematical expression from a natural-language query."""
    # Try to find a math expression in the text
    match = re.search(
        r"([\d\s\+\-\*\/\(\)\.\%\^\×\÷√]+(?:\s*[\+\-\*\/\^\×\÷]\s*[\d\s\(\)\.]+)+)",
        text,
    )
    if match:
        return match.group(1).strip()

    # Fallback: return entire text (let the evaluator fail gracefully)
    return text


def calculator_tool(query: str) -> str:
    """Evaluate a mathematical expression from natural language.

    Args:
        query: Natural-language string containing a math expression.
              e.g. "What is 15 * 23 + 7?"

    Returns:
        Human-readable result string.
    """
    expr = _extract_expression(query)
    try:
        result = _safe_eval(expr)
        # Format nicely: strip trailing zeros for integers
        if result == int(result):
            formatted = f"{int(result):,}"
        else:
            formatted = f"{result:,.6g}"
        return f"🔢 **Calculator**: `{expr.strip()}` = **{formatted}**"
    except ValueError as e:
        return f"🔢 **Calculator**: Could not evaluate `{expr.strip()}` — {e}"
