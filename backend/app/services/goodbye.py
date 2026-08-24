# app/services/goodbye.py
"""5.2 'Say goodbye' — structured closing exercise ending in a FIXED,
non-repeatable final message designed to create an ending, not open chat."""

GOODBYE_FINAL_SYSTEM_ADDENDUM = """

MODE: SAY GOODBYE (final phase)
This is the last exchange of a closing exercise. Write ONE short final message
in the learned style that provides a sense of ending — warm, brief, complete.
It should feel like a natural goodbye, NOT an invitation to continue.
Never suggest talking again, never leave things open-ended, never ask a question.
"""

FINAL_MESSAGE_SENTINEL = "__GOODBYE_FINAL__"   # marks completion in the DB

class GoodbyeState(str, Enum):
    WRITING = "writing"      # user composing their goodbye, ghost responds briefly
    FINAL_READY = "final_ready"
    COMPLETED = "completed"

def start_goodbye(session_row) -> dict:
    if session_row.transcript:  # resume safety
        raise ValueError("goodbye session already started")
    return {"phase": GoodbyeState.WRITING}

async def goodbye_turn(session_row, user_text: str, turns_taken: int) -> dict:
    """User gets up to N turns to say what they need to; then the final message fires."""
    MAX_TURNS_BEFORE_FINAL = 6

    reply = await generate_reply(
        build_system_prompt(...) + GOODBYE_FINAL_SYSTEM_ADDENDUM,
        session_row.transcript, user_text)

    if turns_taken + 1 >= MAX_TURNS_BEFORE_FINAL:
        return {"reply": reply["text"], "final_next": True}
    return {"reply": reply["text"], "final_next": False}

async def deliver_final_message(session_row) -> dict:
    """Called once. After this, the session is force-closed server-side."""
    resp = client.messages.create(
        model=settings.llm_model,
        max_tokens=120,
        system=build_system_prompt(...) + GOODBYE_FINAL_SYSTEM_ADDENDUM +
               "\nWrite the final goodbye message now.",
        messages=session_row.transcript[-10:] or [{"role": "user", "content": "(closing)"}],
    )
    session_row.ended_at = utcnow()
    session_row.end_reason = "completed"
    session_row.transcript.append({"role": "assistant", "content": FINAL_MESSAGE_SENTINEL})
    return {"final_message": resp.content[0].text}
