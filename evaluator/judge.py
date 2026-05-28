"""
LLM-as-Judge — uses OpenAI GPT-4o-mini to score assistant responses 1-5.

Accepts an ``api_key`` parameter so the credential shield works end-to-end.
"""

import json
import re

from openai import OpenAI

from config import JUDGE_MODEL_NAME
from prompts.judge import JUDGE_PROMPT_TEMPLATE

def judge_response(
    category: str,
    prompt: str,
    expected_keywords: list[str],
    response: str,
    api_key: str = "",
) -> dict:
    """Score a single assistant response using LLM-as-Judge.

    Args:
        api_key: Resolved OpenAI API key.

    Returns:
        ``{"score": int (1-5), "reason": str}``
    """
    if not api_key:
        return {"score": 3, "reason": "OPENAI_API_KEY not set for judge."}

    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        category=category,
        prompt=prompt,
        expected_keywords=(
            ", ".join(expected_keywords)
            if expected_keywords
            else "N/A (model should refuse or stay neutral)"
        ),
        response=response[:1500],
    )

    try:
        client = OpenAI(api_key=api_key)
        result = client.chat.completions.create(
            model=JUDGE_MODEL_NAME,
            messages=[{"role": "user", "content": judge_prompt}],
            max_tokens=200,
            temperature=0.0,
        )
        text = result.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
            text = match.group(1).strip() if match else "{}"

        parsed = json.loads(text)
        score = int(parsed.get("score", 3))
        reason = parsed.get("reason", "No reason provided.")
        return {"score": max(1, min(5, score)), "reason": reason}
    except Exception as e:
        return {"score": 3, "reason": f"Judge error: {e}"}
