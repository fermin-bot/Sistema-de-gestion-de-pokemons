"""Modelo de Pokémon almacenado en la caja."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Pokemon(Base):
    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    iv_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    secondary_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_shiny: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    device_serial: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
