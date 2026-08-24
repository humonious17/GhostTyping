import datetime as dt
from backend.app.dependencies import require_onboarded
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..db import get_db
from ..models import Thread, Session as SessionRow, User
from ..services.llm import generate_reply
from ..safety.middleware import build_system_prompt
from ..services.goodbye import GOODBYE_MAX_TURNS, deliver_final_message
from ..services.summary import build_summary
from ..services.analytics import mood_checkin, session_ended
from ..services.mode_prompts import mode_addendum
from ..config import settings
from ..services.analytics import crisis_redirect_served, repeat_checkin_shown, session_started

router = APIRouter(prefix="/sessions")

MODES = {"unsaid", "replay", "question", "goodbye", "free"}


def build_system_prompt_from_thread(thread: Thread) -> str:
    samples = [m["text"] for m in thread.parsed_messages if m["speaker"] == "other"]
    return build_system_prompt(thread.style_profile or {}, samples)

class StartSession(BaseModel):
    thread_id: str
    mode: str

@router.post("/start")
def start_session(body: StartSession, db=Depends(get_db), user: User = Depends(require_onboarded)):
    if body.mode not in MODES:
        raise HTTPException(400, "invalid mode")

    thread = db.get(Thread, body.thread_id)
    if not thread or thread.user_id != user.id:
        raise HTTPException(404)

    # PRD 7.4: hard block standard flow on grief-flagged threads
    if thread.grief_flagged:
        raise HTTPException(409, detail={
            "code": "grief_redirect",
            "message": "This conversation suggests a loss. Ghost Typing isn't built for this yet.",
        })

    # PRD 7.2: free mode gated behind ≥1 completed guided session
    if body.mode == "free":
        done = db.query(SessionRow).filter_by(
            thread_id=thread.id, end_reason="completed").count()
        if done < 1:
            raise HTTPException(403, detail={"code": "free_mode_locked"})

    # inside sessions.py start_session, add:
    if body.mode == "goodbye":
        already_done = db.query(SessionRow).filter_by(
            thread_id=thread.id, mode="goodbye", end_reason="completed").count()
        if already_done > 0:
            raise HTTPException(409, detail={
                "code": "goodbye_already_completed",
                "message": "You've already completed a goodbye for this conversation. "
                        "If you're not ready to let it stay finished, that's worth "
                        "noticing — try a different guided session or revisit your saved summary.",
            })


    # PRD 5.1: below minimum messages → generic reflective mode, no style match
    if len(thread.parsed_messages) < settings.min_messages_for_style:
        raise HTTPException(409, detail={"code": "insufficient_style_data"})

    s = SessionRow(thread_id=thread.id, mode=body.mode)
    db.add(s)
    thread.session_count += 1
    thread.last_active_at = dt.datetime.now(dt.timezone.utc)
    db.commit()

    # PRD 7.2: escalating check-in payload at 3rd/6th session
    checkin = thread.session_count in settings.checkin_at_sessions
    session_started(user.id, body.mode, thread.session_count)
    if checkin:
        repeat_checkin_shown(user.id, thread.session_count)
    return {"session_id": s.id, "repeat_use_checkin": checkin}

class Send(BaseModel):
    session_id: str
    text: str

@router.post("/send")
async def send(body: Send, db=Depends(get_db), user: User = Depends(require_onboarded)):
    s = db.get(SessionRow, body.session_id)
    if not s or s.ended_at:
        raise HTTPException(400, "session closed")

    thread = db.get(Thread, s.thread_id)
    if not thread or thread.user_id != user.id:
        raise HTTPException(404)

    # Time-box enforcement (7.2)
    elapsed = (dt.datetime.now(dt.timezone.utc) - s.started_at).total_seconds()
    if elapsed > settings.default_session_limit:
        s.ended_at = dt.datetime.now(dt.timezone.utc)
        s.end_reason = "timebox"
        db.commit()
        raise HTTPException(409, detail={"code": "timebox_reached"})

    system_prompt = build_system_prompt_from_thread(thread) + "\n\n" + mode_addendum(s.mode)
    result = await generate_reply(system_prompt, s.transcript, body.text)

    s.transcript.append({"role": "user", "content": body.text})
    s.transcript.append({"role": "assistant", "content": result["text"]})

    if result["crisis_redirect"]:
        crisis_redirect_served(user.id)
        s.ended_at = dt.datetime.now(dt.timezone.utc)
        s.end_reason = "crisis_redirect"  # 100% correct handling metric (3.2)
    db.commit()

    payload = {
        "reply": result["text"],
        "crisis_resources_shown": result["crisis_redirect"],
        "time_remaining_sec": max(0, int(settings.default_session_limit - elapsed)),
    }
    if s.mode == "goodbye":
        user_turns = sum(1 for message in s.transcript if message["role"] == "user")
        payload["phase"] = "final_ready" if user_turns >= GOODBYE_MAX_TURNS else "writing"
    return payload


@router.post("/{session_id}/final")
async def deliver_goodbye(session_id: str, db=Depends(get_db), user: User = Depends(require_onboarded)):
    s = db.get(SessionRow, session_id)
    if not s or s.mode != "goodbye" or s.ended_at:
        raise HTTPException(400, "goodbye session is closed or invalid")
    thread = db.get(Thread, s.thread_id)
    if not thread or thread.user_id != user.id:
        raise HTTPException(404)
    result = await deliver_final_message(s, thread)
    db.commit()
    return {"final_message": result["final_message"], "session_closed": True}


@router.get("/{session_id}/summary")
async def session_summary(session_id: str, db=Depends(get_db), user: User = Depends(require_onboarded)):
    s = db.get(SessionRow, session_id)
    if not s or not s.ended_at:
        raise HTTPException(404)
    thread = db.get(Thread, s.thread_id)
    if not thread or thread.user_id != user.id:
        raise HTTPException(404)
    if not s.summary:
        s.summary = await build_summary(s.transcript)
        db.commit()
    return {"summary": s.summary}


class SessionReflection(BaseModel):
    mood_score: int


@router.post("/{session_id}/reflection")
def save_reflection(session_id: str, body: SessionReflection, db=Depends(get_db), user: User = Depends(require_onboarded)):
    s = db.get(SessionRow, session_id)
    if not s or not s.ended_at:
        raise HTTPException(404)
    thread = db.get(Thread, s.thread_id)
    if not thread or thread.user_id != user.id:
        raise HTTPException(404)
    if body.mood_score not in range(1, 6):
        raise HTTPException(422, "mood_score must be between 1 and 5")
    s.mood_checkin = body.mood_score
    mood_checkin(user.id, body.mood_score)
    session_ended(user.id, s.mode, (s.ended_at - s.started_at).total_seconds(), s.end_reason or "user_exit")
    db.commit()
    return {"saved": True}
