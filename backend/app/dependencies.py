"""Auth dependency. Every route that touches threads/sessions requires:
   1. A valid JWT from the auth provider.
   2. An onboarding_acknowledged_at timestamp (5.5 acknowledgment gate).
   3. birthdate_confirmed_18_plus = True (7.6)."""

import jwt, datetime as dt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as OrmSession
from .config import settings
from .db import get_db
from .models import User

def current_user(request: Request, db: OrmSession = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401)
    try:
        claims = jwt.decode(auth.removeprefix("Bearer "),
                            settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401)

    user = db.get(User, claims["sub"])
    if not user:
        # First login: create the row; gates below still apply before any feature access
        user = User(id=claims["sub"])
        db.add(user)
        db.commit()
    return user

def require_onboarded(user: User = Depends(current_user)) -> User:
    """Blocks all product routes until both gates are satisfied."""
    now = dt.datetime.now(dt.timezone.utc)
    if not user.birthdate_confirmed_18_plus:
        raise HTTPException(403, detail={"code": "age_gate_required"})
    if not user.onboarding_acknowledged_at or \
       now - user.onboarding_acknowledged_at > dt.timedelta(days=180):
        raise HTTPException(403, detail={"code": "onboarding_required"})
    return user
