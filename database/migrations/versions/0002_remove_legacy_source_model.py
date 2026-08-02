"""Remove the legacy source table relationship from documents.

Revision ID: 0002_remove_legacy_source_model
Revises: 0001_library_schema
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0002_remove_legacy_source_model"
down_revision: str | Sequence[str] | None = "0001_library_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    tables = _table_names()
    if "documents" in tables and "source_id" in _column_names("documents"):
        with op.batch_alter_table("documents", recreate="always") as batch_op:
            batch_op.drop_column("source_id")

    tables = _table_names()
    if "sources" in tables:
        op.drop_table("sources")


def downgrade() -> None:
    # Re-introducing the abandoned source model would require fabricating source
    # rows and relationships. The cleanup is intentionally irreversible.
    pass
