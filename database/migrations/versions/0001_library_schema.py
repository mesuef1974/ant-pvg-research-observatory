"""Create or upgrade the governed local-library schema.

Revision ID: 0001_library_schema
Revises:
Create Date: 2026-08-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0001_library_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in inspect(op.get_bind()).get_indexes(table_name)}


def _add_document_columns() -> None:
    columns = _column_names("documents")
    additions: tuple[sa.Column, ...] = (
        sa.Column(
            "source_layer",
            sa.String(length=32),
            nullable=False,
            server_default="ENCYCLOPEDIA",
        ),
        sa.Column("local_path", sa.String(length=2000), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "media_type",
            sa.String(length=120),
            nullable=False,
            server_default="application/pdf",
        ),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "import_status",
            sa.String(length=40),
            nullable=False,
            server_default="IMPORTED",
        ),
    )
    for column in additions:
        if column.name not in columns:
            op.add_column("documents", column)


def _create_document_indexes() -> None:
    indexes = _index_names("documents")
    specifications = (
        ("ix_documents_title", ["title"], False),
        ("ix_documents_source_layer", ["source_layer"], False),
        ("ix_documents_sha256", ["sha256"], True),
        ("ix_documents_local_path", ["local_path"], True),
        ("ix_documents_import_status", ["import_status"], False),
    )
    columns = _column_names("documents")
    for name, indexed_columns, unique in specifications:
        if name not in indexes and set(indexed_columns) <= columns:
            op.create_index(name, "documents", indexed_columns, unique=unique)


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "documents" not in tables:
        op.create_table(
            "documents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("source_layer", sa.String(length=32), nullable=False),
            sa.Column("local_path", sa.String(length=2000), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column(
                "media_type",
                sa.String(length=120),
                nullable=False,
                server_default="application/pdf",
            ),
            sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "file_size_bytes", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column(
                "import_status",
                sa.String(length=40),
                nullable=False,
                server_default="IMPORTED",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    else:
        _add_document_columns()

    _create_document_indexes()

    tables = set(inspect(op.get_bind()).get_table_names())
    if "claims" not in tables:
        op.create_table(
            "claims",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("claim_key", sa.String(length=80), nullable=False, unique=True),
            sa.Column("statement", sa.Text(), nullable=False),
            sa.Column("source_layer", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("evidence_note", sa.Text(), nullable=True),
            sa.Column("novelty_note", sa.Text(), nullable=True),
            sa.Column("document_id", sa.Integer(), nullable=True),
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
            sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        )
        op.create_index("ix_claims_claim_key", "claims", ["claim_key"], unique=True)
        op.create_index("ix_claims_source_layer", "claims", ["source_layer"])
        op.create_index("ix_claims_status", "claims", ["status"])

    if "literature_gates" not in tables:
        op.create_table(
            "literature_gates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("gate_key", sa.String(length=80), nullable=False, unique=True),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("research_question", sa.Text(), nullable=False),
            sa.Column(
                "status",
                sa.String(length=40),
                nullable=False,
                server_default="OPEN",
            ),
            sa.Column("verdict", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_literature_gates_gate_key",
            "literature_gates",
            ["gate_key"],
            unique=True,
        )
        op.create_index("ix_literature_gates_status", "literature_gates", ["status"])


def downgrade() -> None:
    # This retrofit migration may preserve pre-existing user data. A destructive
    # automatic downgrade is intentionally not provided.
    pass
