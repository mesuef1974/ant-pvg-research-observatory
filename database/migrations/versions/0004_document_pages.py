"""Add governed page-level PDF extraction storage.

Revision ID: 0004_document_pages
Revises: 0003_canonicalize_document_metadata
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0004_document_pages"
down_revision: str | Sequence[str] | None = "0003_canonicalize_document_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_table() -> None:
    op.create_table(
        "document_pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text_sha256", sa.String(length=64), nullable=False),
        sa.Column("extraction_status", sa.String(length=16), nullable=False),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "document_id",
            "page_number",
            name="uq_document_pages_document_page",
        ),
    )


def _create_missing_indexes() -> None:
    inspector = inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("document_pages")}
    specifications = (
        ("ix_document_pages_document_id", ["document_id"]),
        ("ix_document_pages_text_sha256", ["text_sha256"]),
        ("ix_document_pages_extraction_status", ["extraction_status"]),
    )
    for name, columns in specifications:
        if name not in indexes:
            op.create_index(name, "document_pages", columns)


def upgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "document_pages" not in tables:
        _create_table()
    _create_missing_indexes()


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "document_pages" not in tables:
        return

    indexes = {
        index["name"]
        for index in inspect(op.get_bind()).get_indexes("document_pages")
    }
    for name in (
        "ix_document_pages_extraction_status",
        "ix_document_pages_text_sha256",
        "ix_document_pages_document_id",
    ):
        if name in indexes:
            op.drop_index(name, table_name="document_pages")
    op.drop_table("document_pages")
