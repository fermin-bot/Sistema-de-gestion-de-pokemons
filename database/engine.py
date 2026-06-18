"""Motor y sesión de base de datos."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from models.pokemon import Base, Pokemon
from utils.logging import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def init_database(database_path: Path) -> None:
    """Inicializa el motor SQLite y crea las tablas si no existen."""
    global _engine, _session_factory

    database_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{database_path.as_posix()}", future=True)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    logger.info("Database ready at %s", database_path)


def get_session() -> Session:
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _session_factory()


def count_pokemon() -> int:
    with get_session() as session:
        return session.scalar(select(func.count()).select_from(Pokemon)) or 0
