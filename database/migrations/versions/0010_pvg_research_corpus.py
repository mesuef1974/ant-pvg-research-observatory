"""Add the PVG research corpus: documents and identified results.

Revision ID: 0010_pvg_research_corpus
Revises: 0009_adopt_legacy_research_tables
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0010_pvg_research_corpus"
down_revision: str | Sequence[str] | None = "0009_adopt_legacy_research_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()

    if "pvg_documents" not in tables:
        op.create_table(
            "pvg_documents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("slug", sa.String(length=200), nullable=False, unique=True),
            sa.Column("title", sa.String(length=1000), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("search_text", sa.Text(), nullable=False),
            sa.Column("blocks_json", sa.Text(), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("char_count", sa.Integer(), nullable=False),
            sa.Column(
                "imported_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_pvg_documents_slug", "pvg_documents", ["slug"])
        op.create_index("ix_pvg_documents_sha256", "pvg_documents", ["sha256"])

    if "pvg_results" not in tables:
        op.create_table(
            "pvg_results",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("result_key", sa.String(length=60), nullable=False, unique=True),
            sa.Column("statement", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=200), nullable=True),
            sa.Column(
                "is_proven", sa.Boolean(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column("source_file", sa.String(length=300), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        for column in ("result_key", "status", "is_proven", "source_file"):
            op.create_index(f"ix_pvg_results_{column}", "pvg_results", [column])


def downgrade() -> None:
    for table in ("pvg_results", "pvg_documents"):
        if table in _tables():
            op.drop_table(table)
