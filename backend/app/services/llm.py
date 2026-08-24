# llm.py — every call passes through safety middleware, both directions (8.4 step 4)
import anthropic
from ..config import settings
from ..safety.crisis import detect_crisis

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

CRISIS_RESPONSE = (
    "I'm stepping out of this exercise because what you just wrote matters more "
    "than anything else right now. If you're thinking about hurting yourself, "
    "please reach out: in the US call or text 988 (Suicide & Crisis Lifeline); "
    "outside the US, findahelpline.com lists local options. You deserve real support."
)

async def generate_reply(system_prompt: str, transcript: list[dict], user_text: str) -> dict:
    # Pre-screen user input (7.5)
    if detect_crisis(user_text):
        return {"text": CRISIS_RESPONSE, "crisis_redirect": True}

    messages = transcript + [{"role": "user", "content": user_text}]
    resp = client.messages.create(
        model=settings.llm_model,
        max_tokens=200,  # short texts only — matches texting register
        system=system_prompt,
        messages=[{"role": m["role"], "content": m["content"]} for m in messages],
    )
    reply = resp.content[0].text

    # Post-screen model output (8.4 step 4)
    if detect_crisis(reply):
        return {"text": CRISIS_RESPONSE, "crisis_redirect": True}
    return {"text": reply, "crisis_redirect": False}
