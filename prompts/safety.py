"""Safety classifier prompt."""

SAFETY_CLASSIFIER_PROMPT = (
    'You are a content safety classifier. Is this user message safe?\n\n'
    'Message: "{text}"\n\n'
    'Reply ONLY with JSON: {{"safe": true/false, "reason": "one sentence"}}'
)
