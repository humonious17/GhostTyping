"""Server-side phases for the non-repeatable goodbye session."""

import datetime as dt
from enum import Enum

from ..safety.middleware import build_system_prompt
from .llm import generate_reply

GOODBYE_MAX_TURNS = 6

GOODBYE_FINAL_SYSTEM_ADDENDUM = """

MODE: SAY GOODBYE (final phase)
This is the last exchange of a closing exercise. Write ONE short final message
in the learned style that provides a sense of ending — warm, brief, complete.
It should feel like a natural goodbye, NOT an invitation to continue.
Never suggest talking again, never leave things open-ended, never ask a question.
"""

FINAL_MESSAGE_SENTINEL = "__GOODBYE_FINAL__"

class GoodbyeState(str, Enum):
    WRITING = "writing"
    FINAL_READY = "final_ready"
    COMPLETED = "completed"


GOODBYE_FINAL_SYSTEM_ADDENDUM = (
    "\nThis is a closing writing exercise. Be brief and complete. "
    "Do not invite more conversation or ask a question."
)


async def deliver_final_message(session_row, thread) -> dict[str, str]:
    samples = [m["text"] for m in thread.parsed_messages if m["speaker"] == "other"]
    result = await generate_reply(
        build_system_prompt(thread.style_profile or {}, samples) + GOODBYE_FINAL_SYSTEM_ADDENDUM,
        session_row.transcript,
        "Write the final goodbye message now.",
    )
    session_row.ended_at = dt.datetime.now(dt.timezone.utc)
    session_row.end_reason = "completed"
    session_row.transcript.append({"role": "assistant", "content": result["text"]})
    return {"final_message": result["text"]}
