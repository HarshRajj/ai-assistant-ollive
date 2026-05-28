"""
Conversation memory manager for the Ollive AI Arena.

Uses LangChain's ConversationSummaryBufferMemory to compress older turns 
into a running summary when the buffer exceeds the token cap.
"""

import os
from langchain_classic.memory import ConversationSummaryBufferMemory, ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

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
        self._turn_count = 0

        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            # When an API key is available, use LangChain's SummaryBufferMemory.
            # Max tokens is roughly estimated as threshold * 50 tokens/turn.
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
            self._memory = ConversationSummaryBufferMemory(
                llm=llm,
                max_token_limit=summary_threshold * 50,
                return_messages=True
            )
        else:
            # Fallback without LLM summarization: just keep the last window_size turns
            self._memory = ConversationBufferWindowMemory(
                k=window_size,
                return_messages=True
            )

    def add_user(self, text: str) -> None:
        """Append a user message and trigger summarization if needed."""
        self._memory.chat_memory.add_user_message(text)
        self._turn_count += 1
        if hasattr(self._memory, "prune"):
            self._memory.prune()

    def add_assistant(self, text: str) -> None:
        """Append an assistant message."""
        self._memory.chat_memory.add_ai_message(text)
        if hasattr(self._memory, "prune"):
            self._memory.prune()

    def get_context_messages(self) -> list[dict]:
        """Return messages to inject into the model call.

        Returns a list of dicts: [{"role": "user", "content": "..."}]
        """
        mem_vars = self._memory.load_memory_variables({})
        messages = mem_vars.get("history", [])

        result = []
        for m in messages:
            if isinstance(m, HumanMessage):
                result.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                result.append({"role": "assistant", "content": m.content})
            elif isinstance(m, SystemMessage):
                result.append({"role": "system", "content": f"[Earlier context]: {m.content}"})
            else:
                result.append({"role": "system", "content": m.content})
        return result

    def clear(self) -> None:
        """Reset memory completely."""
        self._memory.clear()
        self._turn_count = 0

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def message_count(self) -> int:
        return len(self._memory.chat_memory.messages)
