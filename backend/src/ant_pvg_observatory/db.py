from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
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
    """Create the development schema and upgrade the v0.1 document table in place."""
    Base.metadata.create_all(bind=engine)
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("documents")}
    additions = {
        "media_type": "VARCHAR(120) NOT NULL DEFAULT 'application/pdf'",
        "page_count": "INTEGER NOT NULL DEFAULT 0",
        "file_size_bytes": "INTEGER NOT NULL DEFAULT 0",
        "import_status": "VARCHAR(40) NOT NULL DEFAULT 'IMPORTED'",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE documents ADD COLUMN {name} {definition}"))


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
