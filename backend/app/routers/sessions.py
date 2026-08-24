import datetime as dt
from backend.app.dependencies import require_onboarded
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..db import get_db
from ..models import Thread, Session as SessionRow, User
from ..services.llm import generate_reply
from ..services.style_profile import build_style_profile
from ..config import settings

router = APIRouter(prefix="/sessions")

MODES = {"unsaid", "replay", "question", "goodbye", "free"}

class StartSession(BaseModel):
    thread_id: str
    mode: str

@router.post("/start")
def start_session(body: StartSession, db=Depends(get_db), user: User = Depends(require_onboarded)):
    if body.mode not in MODES:
        raise HTTPException(400, "invalid mode")

    thread = db.get(Thread, body.thread_id)
    if not thread:
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
    return {"session_id": s.id, "repeat_use_checkin": checkin}

class Send(BaseModel):
    session_id: str
    text: str

@router.post("/send")
async def send(body: Send, db=Depends(get_db), user: User = Depends(require_onboarded)):
    s = db.get(SessionRow, body.session_id)
    if not s or s.ended_at:
        raise HTTPException(400, "session closed")

    # Time-box enforcement (7.2)
    elapsed = (dt.datetime.now(dt.timezone.utc) - s.started_at).total_seconds()
    if elapsed > settings.default_session_limit:
        s.ended_at = dt.datetime.now(dt.timezone.utc)
        s.end_reason = "timebox"
        db.commit()
        raise HTTPException(409, detail={"code": "timebox_reached"})

    thread = db.get(Thread, s.thread_id)
    system_prompt = build_system_prompt_from_thread(thread)
    result = await generate_reply(system_prompt, s.transcript, body.text)

    s.transcript.append({"role": "user", "content": body.text})
    s.transcript.append({"role": "assistant", "content": result["text"]})

    if result["crisis_redirect"]:
        s.ended_at = dt.datetime.now(dt.timezone.utc)
        s.end_reason = "crisis_redirect"  # 100% correct handling metric (3.2)
    db.commit()

    return {
        "reply": result["text"],
        "crisis_resources_shown": result["crisis_redirect"],
        "time_remaining_sec": max(0, int(settings.default_session_limit - elapsed)),
    }
