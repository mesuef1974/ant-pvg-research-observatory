"""اختبارات قراءة سجلات الأدلة وخرائط البراهين."""

from __future__ import annotations

import json
from pathlib import Path

from ant_pvg_observatory.encyclopedia.evidence import (
    check_evidence_records,
    parse_evidence_documents,
)

LEDGER = """# سجل أدلة الفصل التاسع عشر

التاريخ: 2026-07-25
تاريخ القطع الأدبي: 2026-07-25

## السجل التاريخي

| المرحلة | الصيغة المسموح بها | المصدر والموضع | الحكم |
|---|---|---|---|
| Ingham (1937) | الصيغة التقاربية تصح لكل \\(\\theta>5/8\\). | QJM os-8 (1937), 255--266، Theorem 1؛ DOI: 10.1093/qmath/os-8.1.255. | `PRIMARY / VERIFIED` |
| Hoheisel (1930) | وجود ثابت موجب. | السجل الأصلي غير متاح رقميًا. | HISTORICAL / LOCATOR-PENDING |

## جدول آخر بأعمدة مختلفة

| الرمز | القيمة |
|---|---|
| \\(\\theta\\) | \\(7/12\\) |
"""


def _write(tmp_path: Path, name: str, text: str) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / name).write_text(text, encoding="utf-8")
    return tmp_path


def test_parses_rows_with_their_column_headers(tmp_path: Path) -> None:
    root = _write(tmp_path, "CHAPTER_19_EVIDENCE_LEDGER_2026-07-25.md", LEDGER)

    records = parse_evidence_documents(root)

    assert len(records) == 3  # صفّا الجدول الأول وصفّ الجدول الثاني
    first = records[0]
    assert first["chapter_number"] == 19
    assert first["document_kind"] == "EVIDENCE_LEDGER"
    assert first["ordinal"] == 1
    assert first["cutoff_date"] == "2026-07-25"
    assert "Ingham" in json.loads(first["columns_json"])["المرحلة"]


def test_extracts_statement_source_verdict_and_doi(tmp_path: Path) -> None:
    root = _write(tmp_path, "CHAPTER_19_EVIDENCE_LEDGER_2026-07-25.md", LEDGER)

    first = parse_evidence_documents(root)[0]

    assert "الصيغة التقاربية" in first["statement"]
    assert "Theorem 1" in first["source_note"]
    assert first["verdict"] == "PRIMARY / VERIFIED"  # نُزعت العلامات الخلفية
    assert first["doi"] == "10.1093/qmath/os-8.1.255"


def test_non_verdict_columns_are_not_mistaken_for_verdicts(tmp_path: Path) -> None:
    """جدول بأعمدة أخرى يجب ألّا يُنتج حكمًا من خلية رياضية."""
    root = _write(tmp_path, "CHAPTER_19_EVIDENCE_LEDGER_2026-07-25.md", LEDGER)

    third = parse_evidence_documents(root)[2]

    assert third["verdict"] is None


def test_proof_maps_are_read_and_labelled(tmp_path: Path) -> None:
    root = _write(
        tmp_path,
        "CHAPTER_20_PROOF_MAP_2026-07-25.md",
        "| الخطوة | الحالة |\n|---|---|\n| تفكيك | PASS |\n",
    )

    record = parse_evidence_documents(root)[0]

    assert record["document_kind"] == "PROOF_MAP"
    assert record["chapter_number"] == 20
    assert record["verdict"] == "PASS"


def test_missing_docs_directory_is_not_fatal(tmp_path: Path) -> None:
    assert parse_evidence_documents(tmp_path) == []


def test_checks_surface_declared_debts_not_invented_errors() -> None:
    records = [
        {
            "source_file": "CHAPTER_19_EVIDENCE_LEDGER.md",
            "ordinal": 1,
            "verdict": "HISTORICAL / LOCATOR-PENDING",
            "chapter_number": 19,
        },
        {
            "source_file": "CHAPTER_19_EVIDENCE_LEDGER.md",
            "ordinal": 2,
            "verdict": "PRIMARY / VERIFIED",
            "chapter_number": 19,
        },
        {
            "source_file": "CHAPTER_99_EVIDENCE_LEDGER.md",
            "ordinal": 1,
            "verdict": "PASS",
            "chapter_number": 99,
        },
    ]
    findings: list[tuple[str, str, str]] = []
    check_evidence_records(
        records,
        {19, 20},
        lambda code, severity, subject, detail: findings.append(
            (code, severity, subject)
        ),
    )

    codes = [f[0] for f in findings]
    assert codes.count("EVIDENCE_VERIFICATION_PENDING") == 1
    # الفصل 99 غير موجود في المخطوط
    assert "EVIDENCE_CHAPTER_UNKNOWN" in codes
    # الفصل 20 بلا سجل
    absent = [f for f in findings if f[0] == "EVIDENCE_LEDGER_ABSENT"]
    assert [f[2] for f in absent] == ["الفصل 20"]
    # الحكم المكتمل لا يُنتج ملاحظة
    assert all("#2" not in f[2] for f in findings)
