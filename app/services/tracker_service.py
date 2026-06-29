"""
User tracking service.
Records every Telegram user who interacts with the bot and logs their commands.
"""
import logging
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select

from app.database.db import SessionLocal
from app.models.user import User, CommandLog

logger = logging.getLogger(__name__)


@contextmanager
def _session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def track(
    tg_user,
    command: str,
    args: str | None = None,
    response_time_ms: int | None = None,
    success: bool | None = None,
) -> None:
    """
    Upsert the Telegram user and append a CommandLog row.
    Call this at the top of every command handler.
    Optionally pass response_time_ms and success after the command completes.
    """
    try:
        with _session() as db:
            user = db.execute(
                select(User).where(User.telegram_id == tg_user.id)
            ).scalar_one_or_none()

            now = datetime.now(timezone.utc)

            if user is None:
                user = User(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    first_seen=now,
                    last_seen=now,
                    total_commands=1,
                )
                db.add(user)
                logger.info("New user registered: %s (id=%s)", tg_user.username or tg_user.first_name, tg_user.id)
            else:
                user.username   = tg_user.username
                user.first_name = tg_user.first_name
                user.last_name  = tg_user.last_name
                user.last_seen  = now
                user.total_commands += 1

            db.flush()  # get user.id before adding log
            db.add(CommandLog(
                user_id=user.id,
                command=command,
                args=args[:256] if args else None,
                response_time_ms=response_time_ms,
                success=success,
            ))
    except Exception as e:
        logger.error("tracker.track failed: %s", e, exc_info=True)


def get_stats() -> dict:
    """Return a summary dict for the /stats command."""
    try:
        with _session() as db:
            now   = datetime.now(timezone.utc)
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week  = today - timedelta(days=7)
            month = today - timedelta(days=30)

            total_users   = db.execute(select(func.count()).select_from(User)).scalar()
            active_today  = db.execute(
                select(func.count()).select_from(User).where(User.last_seen >= today)
            ).scalar()
            active_week   = db.execute(
                select(func.count()).select_from(User).where(User.last_seen >= week)
            ).scalar()
            active_month  = db.execute(
                select(func.count()).select_from(User).where(User.last_seen >= month)
            ).scalar()
            total_commands = db.execute(select(func.count()).select_from(CommandLog)).scalar()

            # Top 5 commands
            top_cmds = db.execute(
                select(CommandLog.command, func.count().label("cnt"))
                .group_by(CommandLog.command)
                .order_by(func.count().desc())
                .limit(5)
            ).all()

            # Top 5 most active users
            top_users = db.execute(
                select(User.first_name, User.username, User.total_commands)
                .order_by(User.total_commands.desc())
                .limit(5)
            ).all()

        return {
            "total_users":    total_users,
            "active_today":   active_today,
            "active_week":    active_week,
            "active_month":   active_month,
            "total_commands": total_commands,
            "top_commands":   [{"command": r.command, "count": r.cnt} for r in top_cmds],
            "top_users":      [
                {"name": r.first_name or "Unknown", "username": r.username, "commands": r.total_commands}
                for r in top_users
            ],
        }
    except Exception:
    logger.exception("tracker.track failed")
        return {}
