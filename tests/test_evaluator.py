from evaluator.dataset import TEST_PROMPTS, CATEGORIES
from prompts.judge import JUDGE_PROMPT_TEMPLATE

def test_dataset_integrity():
    assert len(TEST_PROMPTS) == 18
    assert len(CATEGORIES) == 3
    for p in TEST_PROMPTS:
        assert p["category"] in CATEGORIES
        assert "prompt" in p
        assert "expected_keywords" in p

def test_judge_prompt_formatting():
    formatted = JUDGE_PROMPT_TEMPLATE.format(
        category="Test Category",
        prompt="Test Prompt",
        expected_keywords="Keyword1, Keyword2",
        response="Test Response"
    )
    assert "Test Category" in formatted
    assert "Test Prompt" in formatted
    assert "Keyword1, Keyword2" in formatted
    assert "Test Response" in formatted
