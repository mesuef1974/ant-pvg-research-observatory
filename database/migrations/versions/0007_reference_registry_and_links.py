"""Add the observatory reference registry, gate links, and knowledge links.

Revision ID: 0007_reference_registry_and_links
Revises: 0006_encyclopedia_domain
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_reference_registry_and_links"
down_revision: str | Sequence[str] | None = "0006_encyclopedia_domain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_READING_STATUS = sa.Enum(
    "DISCOVERED",
    "ABSTRACT_READ",
    "FULLY_READ",
    "VERIFIED",
    name="readingstatus",
)
_GATE_RELATION = sa.Enum(
    "COVERS",
    "PARTIAL",
    "ADJACENT",
    "CONTRADICTS",
    "NOT_RELEVANT",
    name="gaterelation",
)


def upgrade() -> None:
    op.create_table(
        "observatory_references",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference_key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", sa.Text(), nullable=True),
        sa.Column("year", sa.String(length=20), nullable=True),
        sa.Column("venue", sa.Text(), nullable=True),
        sa.Column("doi", sa.String(length=300), nullable=True),
        sa.Column("url", sa.String(length=2000), nullable=True),
        sa.Column(
            "reading_status",
            _READING_STATUS,
            nullable=False,
            server_default="DISCOVERED",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("bibliography_key", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    for column in ("reference_key", "year", "doi", "reading_status", "bibliography_key"):
        op.create_index(
            f"ix_observatory_references_{column}", "observatory_references", [column]
        )

    op.create_table(
        "gate_references",
        sa.Column(
            "gate_id",
            sa.Integer(),
            sa.ForeignKey("literature_gates.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "reference_id",
            sa.Integer(),
            sa.ForeignKey("observatory_references.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("relation", _GATE_RELATION, nullable=False),
        sa.Column("coverage_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_gate_references_relation", "gate_references", ["relation"])

    op.create_table(
        "knowledge_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_type", sa.String(length=40), nullable=False),
        sa.Column("from_key", sa.String(length=200), nullable=False),
        sa.Column("relation", sa.String(length=60), nullable=False),
        sa.Column("to_type", sa.String(length=40), nullable=False),
        sa.Column("to_key", sa.String(length=200), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "from_type", "from_key", "relation", "to_type", "to_key",
            name="uq_knowledge_link",
        ),
    )
    for column in ("from_type", "from_key", "relation", "to_type", "to_key"):
        op.create_index(f"ix_knowledge_links_{column}", "knowledge_links", [column])


def downgrade() -> None:
    op.drop_table("knowledge_links")
    op.drop_table("gate_references")
    op.drop_table("observatory_references")
