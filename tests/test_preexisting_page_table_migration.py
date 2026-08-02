from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def _run_alembic(database_path: Path, revision: str) -> None:
    environment = os.environ.copy()
    environment["ANT_PVG_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", revision],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
    )


def _head_revision() -> str:
    """يشتق آخر هجرة من ملفات Alembic بدل تثبيتها نصًّا.

    التثبيت النصي يجعل كل هجرة جديدة تُسقط هذا الاختبار لسبب لا علاقة له
    بما يفحصه، فيُدرَّب القارئ على تجاهل الفشل.
    """
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    root = Path(__file__).resolve().parents[1]
    script = ScriptDirectory.from_config(Config(str(root / "alembic.ini")))
    return script.get_current_head()

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

    assert revision == (_head_revision(),)
    assert "ix_document_pages_document_id" in indexes
    assert "ix_document_pages_text_sha256" in indexes
    assert "ix_document_pages_extraction_status" in indexes
    assert "source_files" in tables
    assert "source_sections" in tables
