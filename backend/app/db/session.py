"""SQLAlchemy engine and request-scoped sessions."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache(maxsize=4)
def get_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session]:
    settings = get_settings()
    factory = get_session_factory(settings.database_url)
    with factory() as session:
        yield session
