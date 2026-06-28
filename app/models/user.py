"""
User and CommandLog models for tracking bot usage.
"""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Telegram identity
    telegram_id: Mapped[int]  = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username:    Mapped[str | None] = mapped_column(String(64))
    first_name:  Mapped[str | None] = mapped_column(String(64))
    last_name:   Mapped[str | None] = mapped_column(String(64))

    # Activity
    first_seen:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_seen:      Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    total_commands: Mapped[int]      = mapped_column(Integer, default=0)

    logs: Mapped[list["CommandLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} username={self.username}>"


class CommandLog(Base):
    __tablename__ = "command_logs"

    id:         Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:    Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    command:    Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    args:       Mapped[str | None] = mapped_column(String(256))
    timestamp:  Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="logs")

    def __repr__(self) -> str:
        return f"<CommandLog command={self.command} user_id={self.user_id}>"
