"""Add structured source files and sections.

Revision ID: 0005_structured_source_corpus
Revises: 0004_document_pages
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_structured_source_corpus"
down_revision: str | Sequence[str] | None = "0004_document_pages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository", sa.String(length=300), nullable=False),
        sa.Column("revision", sa.String(length=100), nullable=False),
        sa.Column("path", sa.String(length=2000), nullable=False, unique=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("line_count", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "source_layer",
            sa.String(length=32),
            nullable=False,
            server_default="ENCYCLOPEDIA",
        ),
        sa.Column(
            "imported_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_source_files_repository", "source_files", ["repository"])
    op.create_index("ix_source_files_revision", "source_files", ["revision"])
    op.create_index("ix_source_files_path", "source_files", ["path"], unique=True)
    op.create_index("ix_source_files_order_index", "source_files", ["order_index"])
    op.create_index("ix_source_files_sha256", "source_files", ["sha256"])
    op.create_index("ix_source_files_source_layer", "source_files", ["source_layer"])

    op.create_table(
        "source_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_file_id", sa.Integer(), nullable=False),
        sa.Column("heading_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_sha256", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_file_id"], ["source_files.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_source_sections_source_file_id", "source_sections", ["source_file_id"]
    )
    op.create_index(
        "ix_source_sections_heading_type", "source_sections", ["heading_type"]
    )
    op.create_index("ix_source_sections_title", "source_sections", ["title"])
    op.create_index(
        "ix_source_sections_text_sha256", "source_sections", ["text_sha256"]
    )


def downgrade() -> None:
    op.drop_index("ix_source_sections_text_sha256", table_name="source_sections")
    op.drop_index("ix_source_sections_title", table_name="source_sections")
    op.drop_index("ix_source_sections_heading_type", table_name="source_sections")
    op.drop_index("ix_source_sections_source_file_id", table_name="source_sections")
    op.drop_table("source_sections")

    op.drop_index("ix_source_files_source_layer", table_name="source_files")
    op.drop_index("ix_source_files_sha256", table_name="source_files")
    op.drop_index("ix_source_files_order_index", table_name="source_files")
    op.drop_index("ix_source_files_path", table_name="source_files")
    op.drop_index("ix_source_files_revision", table_name="source_files")
    op.drop_index("ix_source_files_repository", table_name="source_files")
    op.drop_table("source_files")
