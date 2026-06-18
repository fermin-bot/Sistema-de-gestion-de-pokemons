"""Repositorio de acceso a Pokémon."""

from __future__ import annotations

from sqlalchemy import func, select

from database.engine import get_session
from models.pokemon import Pokemon


class PokemonRepository:
    def count(self) -> int:
        with get_session() as session:
            return session.scalar(select(func.count()).select_from(Pokemon)) or 0

    def list_recent(self, limit: int = 10) -> list[Pokemon]:
        with get_session() as session:
            return list(
                session.scalars(
                    select(Pokemon).order_by(Pokemon.scanned_at.desc()).limit(limit)
                ).all()
            )

    def add(self, pokemon: Pokemon) -> Pokemon:
        with get_session() as session:
            session.add(pokemon)
            session.commit()
            session.refresh(pokemon)
            return pokemon
