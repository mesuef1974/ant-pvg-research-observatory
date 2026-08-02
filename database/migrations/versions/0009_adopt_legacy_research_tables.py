"""Adopt the legacy MVP claims and literature gates, preserving their rows.

Revision ID: 0009_adopt_legacy_research_tables
Revises: 0008_evidence_records
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0009_adopt_legacy_research_tables"
down_revision: str | Sequence[str] | None = "0008_evidence_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: حالات الادعاء في نسخة MVP وما يقابلها في المُعدَّد الحالي.
_CLAIM_STATUS = {
    "MODEL-SYNTHESIS": "MODEL_SYNTHESIS",
    "KNOWN": "KNOWN",
    "KNOWN-IN-EQUIVALENT-FORM": "KNOWN_EQUIVALENT",
    "SPECIALIZATION-OF-KNOWN": "SPECIALIZATION",
    "LITERATURE-UNCLEAR": "LITERATURE_UNCLEAR",
    "NOT-FOUND-YET": "NOT_FOUND_YET",
    "CANDIDATE-GAP": "CANDIDATE_GAP",
    "PROVED-HERE": "PROVED_HERE",
    "FINITE-VERIFIED": "FINITE_VERIFIED",
    "OPEN": "OPEN",
    "RETRACTED": "RETRACTED",
}
_SOURCE_LAYER = {
    "ENCYCLOPEDIA": "ENCYCLOPEDIA",
    "LITERATURE": "LITERATURE",
    "MODEL_SYNTHESIS": "MODEL_SYNTHESIS",
    "MODEL-SYNTHESIS": "MODEL_SYNTHESIS",
}


def _columns(table: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table)}


def _needs_adoption(table: str, legacy_column: str) -> bool:
    tables = set(inspect(op.get_bind()).get_table_names())
    return table in tables and legacy_column in _columns(table)


def _adopt_claims() -> None:
    """يعيد بناء ``claims`` بشكل ORM وينقل صفوف MVP إليه.

    الهجرة 0001 تتبنّى الجداول بالاسم لا بالشكل، فبقيت قواعد MVP تحمل
    ``claim_id`` و``evidence`` و``novelty_status``. وهذه أول هجرة تصالح الشكل،
    وتنقل البيانات بدل إسقاطها: الادعاءات مُدخَلة يدويًا ولا تُشتق من شيء.
    """
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT claim_id, statement, domain, source_layer, status, evidence,"
            "       dependencies, literature_matches, novelty_status"
            "  FROM claims"
        )
    ).fetchall()

    op.rename_table("claims", "claims_legacy_mvp")
    op.create_table(
        "claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source_layer", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("novelty_note", sa.Text(), nullable=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id")),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_claims_claim_key", "claims", ["claim_key"], unique=True)
    op.create_index("ix_claims_source_layer", "claims", ["source_layer"])
    op.create_index("ix_claims_status", "claims", ["status"])

    for row in rows:
        # المجال والتبعيات لا موضع لهما في المخطط الحالي، فيُحفظان داخل
        # الدليل بدل أن يضيعا صامتين.
        evidence = "\n".join(
            part
            for part in (
                row.evidence,
                f"المجال: {row.domain}" if row.domain else None,
                f"التبعيات: {row.dependencies}" if row.dependencies else None,
                f"مطابقات الأدبيات: {row.literature_matches}"
                if row.literature_matches
                else None,
            )
            if part
        )
        bind.execute(
            sa.text(
                "INSERT INTO claims"
                " (claim_key, statement, source_layer, status, evidence_note, novelty_note)"
                " VALUES (:key, :statement, :layer, :status, :evidence, :novelty)"
            ),
            {
                "key": row.claim_id,
                "statement": row.statement,
                "layer": _SOURCE_LAYER.get(row.source_layer, "MODEL_SYNTHESIS"),
                "status": _CLAIM_STATUS.get(row.status, "MODEL_SYNTHESIS"),
                "evidence": evidence or None,
                "novelty": row.novelty_status,
            },
        )
    op.drop_table("claims_legacy_mvp")


def _adopt_gates() -> None:
    """يعيد بناء ``literature_gates`` بشكل ORM وينقل صفوف MVP إليه.

    حقلا ``keywords`` و``scope`` لا موضع لهما في المخطط الحالي، فيُضمّان إلى
    نص السؤال البحثي: فقدُهما صامتين أسوأ من إبقائهما في غير موضعهما تمامًا.
    """
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT gate_id, title, question, status, keywords, scope, verdict"
            "  FROM literature_gates"
        )
    ).fetchall()

    op.rename_table("literature_gates", "literature_gates_legacy_mvp")
    op.create_table(
        "literature_gates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gate_key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("research_question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="OPEN"),
        sa.Column("verdict", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_literature_gates_gate_key", "literature_gates", ["gate_key"], unique=True
    )
    op.create_index("ix_literature_gates_status", "literature_gates", ["status"])

    for row in rows:
        question = "\n".join(
            part
            for part in (
                row.question,
                f"النطاق: {row.scope}" if row.scope else None,
                f"الكلمات المفتاحية: {row.keywords}" if row.keywords else None,
            )
            if part
        )
        bind.execute(
            sa.text(
                "INSERT INTO literature_gates"
                " (gate_key, title, research_question, status, verdict)"
                " VALUES (:key, :title, :question, :status, :verdict)"
            ),
            {
                "key": row.gate_id,
                "title": row.title,
                "question": question or row.title,
                "status": row.status or "OPEN",
                "verdict": row.verdict,
            },
        )
    op.drop_table("literature_gates_legacy_mvp")


def upgrade() -> None:
    if _needs_adoption("claims", "claim_id"):
        _adopt_claims()
    if _needs_adoption("literature_gates", "gate_id"):
        _adopt_gates()


def downgrade() -> None:
    # لا يُفبرَك تراجع يعيد اختراع أعمدة MVP المهجورة؛ الشكل الحالي هو المعتمد.
    pass
