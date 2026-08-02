"""Add the observatory reference registry, gate links, and knowledge links.

Revision ID: 0007_reference_registry_and_links
Revises: 0006_encyclopedia_domain
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

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


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table)}


def _index_if_absent(name: str, table: str, columns: list[str]) -> None:
    existing = {index["name"] for index in inspect(op.get_bind()).get_indexes(table)}
    if name not in existing:
        op.create_index(name, table, columns)


def _drop_legacy(table: str, legacy_column: str) -> None:
    """يُسقط جدولًا موروثًا من نسخة MVP الأولى إن كان بشكلها القديم.

    الهجرة 0001 تتبنّى الجداول **بالاسم لا بالشكل**، فقواعد MVP بقيت تحمل
    ``gate_references(coverage)`` و``links(from_id)``، وهما مختلفان عمّا يتوقعه
    المخطط الحالي. ولم يكن لهذين الجدولين أي واجهة تكتب فيهما في تلك النسخة،
    فهما فارغان — ويُتحقق من ذلك قبل الإسقاط، ولا يُفترض.
    """
    if table not in _tables() or legacy_column not in _columns(table):
        return
    rows = op.get_bind().execute(sa.text(f"SELECT count(*) FROM {table}")).scalar()
    if rows:
        raise RuntimeError(
            f"الجدول الموروث {table} يحمل {rows} صفًّا بالشكل القديم؛ "
            "يلزم ترحيلها يدويًا قبل الترقية."
        )
    op.drop_table(table)


def upgrade() -> None:
    # قد تكون الهجرة طُبِّقت جزئيًا: تعريفات SQLite غير معامَلاتية، فيبقى ما
    # أُنشئ قبل الفشل. لذلك تفحص كل خطوة وجود هدفها أولًا.
    _drop_legacy("gate_references", "coverage")
    _drop_legacy("links", "from_id")
    tables = _tables()

    if "observatory_references" not in tables:
        op.create_table(
            "observatory_references",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "reference_key", sa.String(length=80), nullable=False, unique=True
            ),
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
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
    for column in ("reference_key", "year", "doi", "reading_status", "bibliography_key"):
        _index_if_absent(
            f"ix_observatory_references_{column}", "observatory_references", [column]
        )

    if "gate_references" not in tables:
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
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
    _index_if_absent("ix_gate_references_relation", "gate_references", ["relation"])

    if "knowledge_links" not in tables:
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
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "from_type",
                "from_key",
                "relation",
                "to_type",
                "to_key",
                name="uq_knowledge_link",
            ),
        )
    for column in ("from_type", "from_key", "relation", "to_type", "to_key"):
        _index_if_absent(f"ix_knowledge_links_{column}", "knowledge_links", [column])


def downgrade() -> None:
    for table in ("knowledge_links", "gate_references", "observatory_references"):
        if table in _tables():
            op.drop_table(table)
