from sqlalchemy.engine import Engine
from sqlmodel import create_engine, Session
import contextlib
from typing import Generator

from app.settings.db import db_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    _engine = create_engine(db_settings.database_url, echo=True, pool_pre_ping=True)
    return _engine


@contextlib.contextmanager
def sync_session() -> Generator[Session, None, None]:
    engine = get_engine()
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
