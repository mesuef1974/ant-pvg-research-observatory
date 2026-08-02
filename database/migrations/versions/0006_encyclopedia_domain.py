"""Add the encyclopedia domain: chapters, units, results, bibliography, notes, findings.

Revision ID: 0006_encyclopedia_domain
Revises: 0005_structured_source_corpus
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_encyclopedia_domain"
down_revision: str | Sequence[str] | None = "0005_structured_source_corpus"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "encyclopedia_chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("number", sa.Integer(), nullable=False, unique=True),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("volume", sa.String(length=200), nullable=True),
        sa.Column("tex_paths", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("revision", sa.String(length=100), nullable=False),
        sa.Column(
            "imported_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_encyclopedia_chapters_number", "encyclopedia_chapters", ["number"]
    )
    op.create_index(
        "ix_encyclopedia_chapters_volume", "encyclopedia_chapters", ["volume"]
    )
    op.create_index(
        "ix_encyclopedia_chapters_revision", "encyclopedia_chapters", ["revision"]
    )

    op.create_table(
        "encyclopedia_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chapter_id",
            sa.Integer(),
            sa.ForeignKey("encyclopedia_chapters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=1000), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("blocks_json", sa.Text(), nullable=False),
        sa.Column("text_sha256", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_encyclopedia_units_chapter_id", "encyclopedia_units", ["chapter_id"]
    )
    op.create_index("ix_encyclopedia_units_ordinal", "encyclopedia_units", ["ordinal"])
    op.create_index(
        "ix_encyclopedia_units_text_sha256", "encyclopedia_units", ["text_sha256"]
    )

    op.create_table(
        "encyclopedia_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("result_key", sa.String(length=60), nullable=False, unique=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=1000), nullable=True),
        sa.Column("chapter_number", sa.Integer(), nullable=True),
        sa.Column("tex_status", sa.String(length=60), nullable=True),
        sa.Column("registry_status", sa.String(length=200), nullable=True),
        sa.Column("registry_files", sa.Text(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column(
            "citable", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("label", sa.String(length=300), nullable=True),
        sa.Column("statement", sa.Text(), nullable=True),
        sa.Column("tex_path", sa.String(length=2000), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_encyclopedia_results_result_key", "encyclopedia_results", ["result_key"]
    )
    op.create_index("ix_encyclopedia_results_kind", "encyclopedia_results", ["kind"])
    op.create_index(
        "ix_encyclopedia_results_chapter_number",
        "encyclopedia_results",
        ["chapter_number"],
    )
    op.create_index(
        "ix_encyclopedia_results_citable", "encyclopedia_results", ["citable"]
    )

    op.create_table(
        "bibliography_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_key", sa.String(length=200), nullable=False, unique=True),
        sa.Column("entry_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("year", sa.String(length=20), nullable=True),
        sa.Column("journal", sa.Text(), nullable=True),
        sa.Column("doi", sa.String(length=300), nullable=True),
        sa.Column("url", sa.String(length=2000), nullable=True),
        sa.Column("aliases", sa.Text(), nullable=True),
        sa.Column("bib_file", sa.String(length=300), nullable=False),
        sa.Column("cited", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index(
        "ix_bibliography_entries_entry_key", "bibliography_entries", ["entry_key"]
    )
    op.create_index(
        "ix_bibliography_entries_entry_type", "bibliography_entries", ["entry_type"]
    )
    op.create_index("ix_bibliography_entries_year", "bibliography_entries", ["year"])
    op.create_index(
        "ix_bibliography_entries_bib_file", "bibliography_entries", ["bib_file"]
    )
    op.create_index("ix_bibliography_entries_cited", "bibliography_entries", ["cited"])

    op.create_table(
        "model_synthesis_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("note_key", sa.String(length=60), nullable=False, unique=True),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("domain", sa.String(length=300), nullable=True),
        sa.Column("anchors", sa.Text(), nullable=True),
        sa.Column("literature_hint", sa.Text(), nullable=True),
        sa.Column("is_gap", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("blocks_json", sa.Text(), nullable=False),
        sa.Column("source_file", sa.String(length=300), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_model_synthesis_notes_note_key", "model_synthesis_notes", ["note_key"]
    )
    op.create_index("ix_model_synthesis_notes_kind", "model_synthesis_notes", ["kind"])
    op.create_index(
        "ix_model_synthesis_notes_domain", "model_synthesis_notes", ["domain"]
    )
    op.create_index(
        "ix_model_synthesis_notes_is_gap", "model_synthesis_notes", ["is_gap"]
    )
    op.create_index(
        "ix_model_synthesis_notes_source_file",
        "model_synthesis_notes",
        ["source_file"],
    )

    op.create_table(
        "integrity_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("subject", sa.String(length=300), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column(
            "checked_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_integrity_findings_code", "integrity_findings", ["code"])
    op.create_index("ix_integrity_findings_severity", "integrity_findings", ["severity"])
    op.create_index("ix_integrity_findings_subject", "integrity_findings", ["subject"])


def downgrade() -> None:
    for table in (
        "integrity_findings",
        "model_synthesis_notes",
        "bibliography_entries",
        "encyclopedia_results",
        "encyclopedia_units",
        "encyclopedia_chapters",
    ):
        op.drop_table(table)
