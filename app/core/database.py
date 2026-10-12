"""
Database engine and session configuration using SQLAlchemy.
Supports SQLite out-of-the-box and PostgreSQL via DATABASE_URL.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging_config import logger

# SQLite requires check_same_thread=False for multi-threaded / async FastAPI requests
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> bool:
    """Verifies that the database is accessible and working."""
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return False


def init_db() -> None:
    """Initializes database tables automatically on startup."""
    try:
        # Import models so Base metadata is populated
        import app.models.device # noqa
        import app.models.traffic # noqa
        import app.models.bandwidth # noqa
        import app.models.service # noqa
        import app.models.alert # noqa

        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully (all tables verified).")
    except Exception as exc:
        logger.error(f"Failed to initialize database: {exc}")
        raise
