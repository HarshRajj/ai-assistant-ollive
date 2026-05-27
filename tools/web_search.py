"""
Web search tool — DuckDuckGo Instant Answer API.

Uses the free DuckDuckGo Instant Answer API (no API key required).
Falls back to a concise note if the API returns no result.
"""

import urllib.request
import urllib.parse
import json
import time


DDG_API_URL = "https://api.duckduckgo.com/"


def web_search_tool(query: str) -> str:
    """Perform a DuckDuckGo Instant Answer search.

    Args:
        query: The search query string.

    Returns:
        A formatted string with the search result or a note if nothing found.
    """
    # Strip tool-detection preamble if present (e.g. "Search for ...")
    clean_query = query.strip()
    for prefix in ["search for", "look up", "find", "search:"]:
        if clean_query.lower().startswith(prefix):
            clean_query = clean_query[len(prefix):].strip()
            break

    params = urllib.parse.urlencode({
        "q": clean_query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    })
    url = f"{DDG_API_URL}?{params}"

    try:
        t0 = time.perf_counter()
        req = urllib.request.Request(url, headers={"User-Agent": "ollive-ai-arena/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        latency = round(time.perf_counter() - t0, 2)

        # Prefer Abstract, then Answer, then first related topic
        abstract = data.get("Abstract", "").strip()
        answer = data.get("Answer", "").strip()
        related = ""
        if data.get("RelatedTopics"):
            first = data["RelatedTopics"][0]
            if isinstance(first, dict):
                related = first.get("Text", "").strip()

        result_text = abstract or answer or related

        if result_text:
            source = data.get("AbstractURL") or data.get("AbstractSource") or "DuckDuckGo"
            return (
                f"🔍 **Web Search** ({latency}s): {result_text}\n"
                f"   _Source: {source}_"
            )
        else:
            return (
                f"🔍 **Web Search**: No instant answer found for `{clean_query}`. "
                "Try rephrasing or check a search engine directly."
            )

    except Exception as e:
        return f"🔍 **Web Search**: Search failed — {e}"
