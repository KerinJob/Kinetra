from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_Session = None


def init_engine(url: str | None = None):
    global _engine, _Session
    _engine = create_engine(url or get_settings().database_url, pool_pre_ping=True, future=True)
    _Session = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def SessionLocal():
    if _Session is None:
        init_engine()
    return _Session()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
