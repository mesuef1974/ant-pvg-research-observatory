from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path


def test_alembic_removes_legacy_source_model(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE sources (
                id INTEGER PRIMARY KEY,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL
            );
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                source_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                file_name TEXT,
                page_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(source_id) REFERENCES sources(id)
            );
            INSERT INTO sources(id, source_type, title)
            VALUES (1, 'ENCYCLOPEDIA', 'Legacy encyclopedia');
            INSERT INTO documents(id, source_id, title, file_name, page_count)
            VALUES (1, 1, 'Legacy volume', 'volume-01.pdf', 292);
            """
        )

    environment = os.environ.copy()
    environment["ANT_PVG_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
    )

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(documents)")
        }
        row = connection.execute(
            "SELECT id, title, page_count FROM documents WHERE id = 1"
        ).fetchone()
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()

    assert "sources" not in tables
    assert "source_id" not in columns
    assert "source_layer" in columns
    assert row == (1, "Legacy volume", 292)
    assert revision == ("0002_remove_legacy_source_model",)
