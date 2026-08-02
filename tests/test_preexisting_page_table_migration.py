from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path


LATEST_REVISION = "0005_structured_source_corpus"


def _run_alembic(database_path: Path, revision: str) -> None:
    environment = os.environ.copy()
    environment["ANT_PVG_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    subprocess.run(
        ["alembic", "upgrade", revision],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
    )


def test_migration_adopts_preexisting_document_pages_table(tmp_path: Path) -> None:
    database_path = tmp_path / "preexisting-pages.db"
    _run_alembic(database_path, "0003_canonicalize_document_metadata")

    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE document_pages (
                id INTEGER PRIMARY KEY,
                document_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                text TEXT NOT NULL DEFAULT '',
                char_count INTEGER NOT NULL DEFAULT 0,
                word_count INTEGER NOT NULL DEFAULT 0,
                text_sha256 VARCHAR(64) NOT NULL,
                extraction_status VARCHAR(16) NOT NULL,
                extraction_error TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                CONSTRAINT uq_document_pages_document_page
                    UNIQUE(document_id, page_number)
            );
            """
        )

    _run_alembic(database_path, "head")

    with sqlite3.connect(database_path) as connection:
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()
        indexes = {
            row[1]
            for row in connection.execute("PRAGMA index_list(document_pages)")
        }
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert revision == (LATEST_REVISION,)
    assert "ix_document_pages_document_id" in indexes
    assert "ix_document_pages_text_sha256" in indexes
    assert "ix_document_pages_extraction_status" in indexes
    assert "source_files" in tables
    assert "source_sections" in tables
