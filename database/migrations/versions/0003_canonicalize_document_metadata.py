"""Canonicalize document metadata after the legacy retrofit.

Revision ID: 0003_canonicalize_document_metadata
Revises: 0002_remove_legacy_source_model
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0003_canonicalize_document_metadata"
down_revision: str | Sequence[str] | None = "0002_remove_legacy_source_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names() -> set[str]:
    return {
        column["name"]
        for column in inspect(op.get_bind()).get_columns("documents")
    }


def upgrade() -> None:
    columns = _column_names()
    with op.batch_alter_table("documents", recreate="always") as batch_op:
        if "file_name" in columns:
            batch_op.drop_column("file_name")
        batch_op.alter_column(
            "created_at",
            existing_type=sa.Text(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )


def downgrade() -> None:
    # The discarded file_name column duplicated local_path incompletely. It is
    # intentionally not reconstructed.
    pass
