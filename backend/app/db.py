from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .config import settings
from .models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)


def init_db() -> None:
	Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
	db = Session(engine)
	try:
		yield db
	finally:
		db.close()
