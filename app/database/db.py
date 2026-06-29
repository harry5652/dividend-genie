"""
Database engine and session factory.
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

from app.config import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def _migrate() -> None:
    """Add new columns to existing tables when they are missing (idempotent)."""
    is_sqlite = "sqlite" in config.DATABASE_URL
    migrations = [
        # (table, column, sql_type)
        ("command_logs", "response_time_ms", "INTEGER"),
        ("command_logs", "success",          "BOOLEAN"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                if is_sqlite:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                else:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                    ))
                conn.commit()
                logger.info("Migration applied: %s.%s (%s)", table, column, col_type)
            except Exception as exc:
                conn.rollback()
                msg = str(exc).lower()
                # Duplicate-column errors are expected on re-runs — ignore them
                if any(kw in msg for kw in ("already exists", "duplicate column", "dupcolumn")):
                    logger.debug("Column %s.%s already exists, skipping.", table, column)
                else:
                    # Unexpected error — fail loudly so schema drift doesn't hide at runtime
                    logger.error(
                        "Migration failed for %s.%s: %s", table, column, exc, exc_info=True
                    )
                    raise


def init_db() -> None:
    """Create all tables if they do not exist yet, and apply lightweight migrations."""
    from app.models import user  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)
    _migrate()


def get_db():
    """Context-manager style session. Use with `with get_db() as db:`."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
