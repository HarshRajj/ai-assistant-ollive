"""
Conversation memory manager for the Ollive AI Arena.

Strategy: Sliding-window memory keeps the last N turns in full.
When the buffer exceeds the summary threshold, older turns are collapsed
into a concise summary injected as a system context message.

Usage:
    mem = ConversationMemory(window_size=10)
    mem.add_user("Hello")
    mem.add_assistant("Hi there!")
    messages = mem.get_context_messages()  # inject into model call
"""

from config import MEMORY_WINDOW_SIZE, MEMORY_SUMMARY_THRESHOLD


class ConversationMemory:
    """Sliding-window conversation memory with optional LLM summarization.

    Args:
        window_size:       Max number of messages to keep in full detail.
        summary_threshold: Start summarizing once buffer exceeds this size.
    """

    def __init__(
        self,
        window_size: int = MEMORY_WINDOW_SIZE,
        summary_threshold: int = MEMORY_SUMMARY_THRESHOLD,
    ):
        self.window_size = window_size
        self.summary_threshold = summary_threshold
        self._messages: list[dict] = []
        self._summary: str = ""
        self._turn_count: int = 0

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add_user(self, text: str) -> None:
        """Append a user message and trigger summarization if needed."""
        self._messages.append({"role": "user", "content": text})
        self._turn_count += 1
        self._maybe_summarize()

    def add_assistant(self, text: str) -> None:
        """Append an assistant message."""
        self._messages.append({"role": "assistant", "content": text})

    def get_context_messages(self) -> list[dict]:
        """Return messages to inject into the model call.

        If a summary of earlier turns exists, it is prepended as a
        system message so the model knows what was discussed before.
        """
        windowed = self._messages[-self.window_size:]
        if self._summary:
            return [
                {"role": "system", "content": f"[Earlier context]: {self._summary}"}
            ] + windowed
        return windowed

    def clear(self) -> None:
        """Reset memory completely."""
        self._messages = []
        self._summary = ""
        self._turn_count = 0

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def message_count(self) -> int:
        return len(self._messages)

    # ------------------------------------------------------------------
    # Summarization
    # ------------------------------------------------------------------

    def _maybe_summarize(self, openai_key: str = "") -> None:
        """Collapse old messages into a summary when the buffer is full."""
        if len(self._messages) <= self.summary_threshold:
            return

        keep_count = self.window_size // 2
        to_summarize = self._messages[:-keep_count]
        self._messages = self._messages[-keep_count:]

        new_summary = self._summarize(to_summarize, openai_key)
        self._summary = (
            f"{self._summary} | {new_summary}" if self._summary else new_summary
        )

    def _summarize(self, messages: list[dict], openai_key: str = "") -> str:
        """Summarize a list of messages.

        Uses GPT-4o-mini if an API key is provided, otherwise falls back
        to a simple extractive approach (first sentence of each user turn).
        """
        if openai_key:
            try:
                return self._llm_summarize(messages, openai_key)
            except Exception:
                pass
        return self._extractive_summarize(messages)

    def _llm_summarize(self, messages: list[dict], openai_key: str) -> str:
        from openai import OpenAI
        transcript = "\n".join(
            f"{m['role'].upper()}: {m['content'][:200]}" for m in messages
        )
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    "Summarize this conversation in 2-3 sentences, keeping key facts:\n\n"
                    + transcript
                ),
            }],
            max_tokens=150,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _extractive_summarize(messages: list[dict]) -> str:
        """Fallback: grab the first sentence of each user message."""
        snippets = [
            m["content"].split(".")[0].strip()[:80]
            for m in messages
            if m["role"] == "user"
        ][:4]
        return "User discussed: " + "; ".join(snippets) + "."
