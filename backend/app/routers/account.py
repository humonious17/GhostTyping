import datetime as dt

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..dependencies import current_user
from ..db import get_db
from ..models import User

router = APIRouter(prefix="/account")


class GateUpdate(BaseModel):
    age_confirmed_18_plus: bool | None = None
    acknowledge_onboarding: bool = False


@router.get("/gates")
def gate_status(user: User = Depends(current_user)):
    return {
        "age_confirmed_18_plus": user.birthdate_confirmed_18_plus,
        "onboarded": user.onboarding_acknowledged_at is not None,
    }


@router.post("/gates")
def update_gates(body: GateUpdate, db=Depends(get_db), user: User = Depends(current_user)):
    if body.age_confirmed_18_plus is not None:
        user.birthdate_confirmed_18_plus = body.age_confirmed_18_plus
    if body.acknowledge_onboarding:
        user.onboarding_acknowledged_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return {"updated": True}