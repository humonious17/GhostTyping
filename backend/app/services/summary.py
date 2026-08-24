"""5.3 / US-4 — post-session reflection summary.
Uses the same safety middleware as live sessions. The summary is written
as the USER'S reflection (what they said/felt), not as the ghost speaking —
this keeps it journal-shaped and reduces the export-as-fake-screenshot risk."""

import anthropic
from ..config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SUMMARY_SYSTEM = """You are helping someone reflect on a writing exercise they just completed.
Summarize what THEY expressed in their own words — themes, feelings, unresolved points.
Do NOT quote or reconstruct the simulated responses. Do NOT write as the simulated person.
Keep it under 200 words, plain language, second person."""

async def build_summary(transcript: list[dict]) -> str:
    user_msgs = [m["content"] for m in transcript if m["role"] == "user"]
    resp = client.messages.create(
        model=settings.llm_model,
        max_tokens=300,
        system=SUMMARY_SYSTEM,
        messages=[{"role": "user", "content":
                   "Here is what I wrote during my session:\n\n" + "\n---\n".join(user_msgs)}],
    )
    return resp.content[0].text
