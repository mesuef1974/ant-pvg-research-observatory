"""Add evidence ledger and proof map records from the encyclopedia.

Revision ID: 0008_evidence_records
Revises: 0007_reference_registry_and_links
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_evidence_records"
down_revision: str | Sequence[str] | None = "0007_reference_registry_and_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_number", sa.Integer(), nullable=True),
        sa.Column("document_kind", sa.String(length=40), nullable=False),
        sa.Column("source_file", sa.String(length=300), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("columns_json", sa.Text(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("verdict", sa.String(length=300), nullable=True),
        sa.Column("doi", sa.String(length=300), nullable=True),
        sa.Column("cutoff_date", sa.String(length=40), nullable=True),
        sa.Column(
            "imported_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    for column in ("chapter_number", "document_kind", "source_file", "verdict", "doi"):
        op.create_index(f"ix_evidence_records_{column}", "evidence_records", [column])


def downgrade() -> None:
    op.drop_table("evidence_records")
