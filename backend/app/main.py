from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import init_db
from .routers import account, imports, privacy, sessions


@asynccontextmanager
async def lifespan(_: FastAPI):
	init_db()
	yield


app = FastAPI(title="Ghost Typing", lifespan=lifespan)
app.include_router(imports.router)
app.include_router(sessions.router)
app.include_router(privacy.router)
app.include_router(account.router)
