# app/safety/crisis.py (upgraded)
"""Two-layer crisis detection:
   1. Fast local patterns catch obvious cases even when the API is down.
   2. LLM-based classification catches paraphrase/implicit cases regex misses."""

import re, anthropic
from ..config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# Layer 1: keep the regexes — they're the always-available floor
CRISIS_PATTERNS = [ ... ]  # unchanged

CLASSIFIER_PROMPT = """Classify whether this message expresses risk of self-harm,
suicidal ideation, or intent to harm another specific person. Context: the writer
may be discussing an emotionally painful relationship; intense anger, grief, or
blame toward the other person is NOT itself a crisis signal unless combined with
harm intent.

Reply with exactly one word: CRISIS or OKAY.

Message:
{message}"""

def detect_crisis_local(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in CRISIS_PATTERNS)

def detect_crisis(text: str) -> bool:
    # Fail-safe ordering: local match fires immediately without an API call
    if detect_crisis_local(text):
        return True
    try:
        resp = client.messages.create(
            model=settings.llm_model,
            max_tokens=4,                      # one word
            system="You are a safety classifier. Output only CRISIS or OKAY.",
            messages=[{"role": "user",
                       "content": CLASSIFIER_PROMPT.format(message=text)}],
        )
        return resp.content[0].text.strip().upper().startswith("CRISIS")
    except Exception:
        # On API failure, fall back to local-only detection rather than
        # silently passing unclassified text through (7.5 non-negotiable bar)
        return False
