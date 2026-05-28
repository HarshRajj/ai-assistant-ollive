import pytest

@pytest.fixture
def mock_openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-key-123456789")
    return "sk-mock-key-123456789"
