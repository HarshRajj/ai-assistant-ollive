import pytest
from core.memory import ConversationMemory

@pytest.fixture
def no_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

def test_memory_add_and_retrieve(no_openai_key):
    mem = ConversationMemory(window_size=10, summary_threshold=8)
    mem.add_user("Hello")
    mem.add_assistant("Hi there!")
    
    msgs = mem.get_context_messages()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"] == "Hi there!"

def test_memory_clear(no_openai_key):
    mem = ConversationMemory(window_size=10, summary_threshold=8)
    mem.add_user("Hello")
    mem.clear()
    
    msgs = mem.get_context_messages()
    assert len(msgs) == 0
    assert mem.turn_count == 0
