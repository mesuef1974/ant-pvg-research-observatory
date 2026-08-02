from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _prepare_sqlite_parent() -> None:
    prefix = "sqlite:///"
    if settings.database_url.startswith(prefix):
        path = Path(settings.database_url.removeprefix(prefix))
        path.parent.mkdir(parents=True, exist_ok=True)


_prepare_sqlite_parent()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ensure_schema() -> None:
    """Prepare runtime storage without mutating the database schema.

    Alembic is the sole authority for schema creation and upgrades. Keeping
    application startup free of ``Base.metadata.create_all`` prevents tables
    from appearing before their migration revision is recorded.
    """
    _prepare_sqlite_parent()


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
