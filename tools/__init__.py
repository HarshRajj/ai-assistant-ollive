"""
Tool registry — imports and exposes all available tools.
"""

from tools.calculator import calculator_tool
from tools.web_search import web_search_tool
from tools.datetime_tool import datetime_tool

TOOL_REGISTRY: dict[str, dict] = {
    "calculator": {
        "fn": calculator_tool,
        "description": "Evaluate a mathematical expression safely.",
        "example": "What is 15 * 23 + 7?",
        "keywords": ["calculate", "compute", "what is", "×", "*", "+", "-", "/", "^", "sqrt", "math"],
    },
    "web_search": {
        "fn": web_search_tool,
        "description": "Search the web for current information via DuckDuckGo.",
        "example": "Search for latest AI news",
        "keywords": ["search", "look up", "find", "latest", "current", "news", "who is", "what happened"],
    },
    "datetime": {
        "fn": datetime_tool,
        "description": "Get the current date, time, and timezone information.",
        "example": "What time is it now?",
        "keywords": ["time", "date", "today", "now", "current date", "what day"],
    },
}

__all__ = ["TOOL_REGISTRY", "calculator_tool", "web_search_tool", "datetime_tool"]
