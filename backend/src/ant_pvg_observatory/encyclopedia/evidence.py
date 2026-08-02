"""قراءة سجلات الأدلة وخرائط البراهين من مستودع الموسوعة.

هذه الملفات (``docs/*EVIDENCE_LEDGER*.md`` و``docs/*PROOF_MAP*.md``) تحمل عمل
التحقق الببليوغرافي الذي يسبق تأليف الفصل: لكل مصدر صياغةٌ مسموح بها وموضعٌ في
المصدر وحكمٌ على درجة التحقق (``PRIMARY / VERIFIED``، ``LOCATOR-PENDING``، …).

المرصد يقرأها ولا يعيد إنتاجها. القراءة عامة عمدًا: تُلتقط كل صفوف الجداول
بأعمدتها كما هي، ثم تُستخرج الحقول المعروفة بالتعرّف على رؤوس الأعمدة. فتغيّر
تسمية عمود لا يُسقط الاستيراد، بل يُفقد حقلًا واحدًا ويبقى الصف محفوظًا.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

#: عناوين أعمدة تُقرأ حقولًا معروفة. المطابقة بالاحتواء لا بالتساوي.
_STATEMENT_HEADS = ("الصيغة", "النتيجة", "الخطوة", "المضمون", "الادعاء")
_SOURCE_HEADS = ("المصدر", "الموضع", "المرجع")
_VERDICT_HEADS = ("الحكم", "الحالة", "التحقق")

_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
_CUTOFF = re.compile(r"تاريخ القطع[^:]*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
_CHAPTER = re.compile(r"CHAPTER_(\d+)_")
_SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")
#: الحكم وسمٌ لاتيني بأحرف كبيرة؛ ما لا يطابق ذلك عمودٌ آخر التُقط خطأً.
_VERDICT_TOKEN = re.compile(r"[A-Z][A-Z-]{2,}")


def _document_kind(name: str) -> str:
    if "EVIDENCE_LEDGER" in name:
        return "EVIDENCE_LEDGER"
    if "PROOF_MAP" in name:
        return "PROOF_MAP"
    return "OTHER"


def _clean_verdict(value: str | None) -> str | None:
    r"""ينظّف الحكم ويرفض ما ليس وسمًا.

    خلايا الجداول تحمل تنسيق Markdown وأحيانًا رياضيات؛ فبلا هذا الفحص يدخل
    مثل ``\zeta(1/2+it)`` حكمًا وهو عمود آخر التُقط برأس متشابه.
    """
    if not value:
        return None
    cleaned = value.replace("\\`", "").replace("`", "").strip()
    if not _VERDICT_TOKEN.search(cleaned):
        return None
    return cleaned[:300] or None


def _pick(row: dict[str, str], heads: tuple[str, ...]) -> str | None:
    for header, value in row.items():
        if any(head in header for head in heads):
            return value or None
    return None


def _rows(text: str) -> list[dict[str, str]]:
    """يقرأ كل جداول Markdown في الملف، ويربط كل خلية برأس عمودها."""
    out: list[dict[str, str]] = []
    headers: list[str] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            headers = None
            continue
        if _SEPARATOR.match(stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if headers is None:
            headers = cells
            continue
        if len(cells) < 2:
            continue
        out.append(
            {
                headers[i] if i < len(headers) else f"عمود {i + 1}": cell
                for i, cell in enumerate(cells)
            }
        )
    return out


def parse_evidence_documents(root: Path) -> list[dict]:
    """يُرجع صفوف سجلات الأدلة وخرائط البراهين مرتَّبةً ترتيبًا ثابتًا."""
    docs = root / "docs"
    if not docs.is_dir():
        return []

    records: list[dict] = []
    paths = sorted(
        set(docs.glob("*EVIDENCE_LEDGER*.md")) | set(docs.glob("*PROOF_MAP*.md"))
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        chapter = _CHAPTER.search(path.name)
        cutoff = _CUTOFF.search(text)
        for ordinal, row in enumerate(_rows(text), start=1):
            joined = " ".join(row.values())
            doi = _DOI.search(joined)
            records.append(
                {
                    "chapter_number": int(chapter.group(1)) if chapter else None,
                    "document_kind": _document_kind(path.name),
                    "source_file": path.name,
                    "ordinal": ordinal,
                    "columns_json": json.dumps(row, ensure_ascii=False),
                    "statement": _pick(row, _STATEMENT_HEADS),
                    "source_note": _pick(row, _SOURCE_HEADS),
                    "verdict": _clean_verdict(_pick(row, _VERDICT_HEADS)),
                    "doi": doi.group(0).rstrip(".،؛") if doi else None,
                    "cutoff_date": cutoff.group(1) if cutoff else None,
                }
            )
    return records


#: أحكام تعني أن التحقق لم يكتمل بعد.
PENDING_MARKERS = ("PENDING", "WITHHELD", "NOT-AVAILABLE", "UNVERIFIED", "TODO")


def check_evidence_records(records: list[dict], chapter_numbers: set[int], add) -> None:
    """فحوص سجلات الأدلة.

    الغرض إبراز ما أعلنه المؤلف عن نفسه: المواضع التي بقي فيها التحقق ناقصًا.
    هذه ليست أخطاء بل ديون معلنة، ولذلك درجتها إخبارية أو منخفضة.
    """
    for record in records:
        subject = f"{record['source_file']}#{record['ordinal']}"
        verdict = (record["verdict"] or "").upper()
        if any(marker in verdict for marker in PENDING_MARKERS):
            add(
                "EVIDENCE_VERIFICATION_PENDING",
                "LOW",
                subject,
                f"حكم التحقق «{record['verdict']}» يعلن أن التثبت لم يكتمل بعد.",
            )
        if record["chapter_number"] and record["chapter_number"] not in chapter_numbers:
            add(
                "EVIDENCE_CHAPTER_UNKNOWN",
                "MEDIUM",
                subject,
                f"السجل ينسب نفسه إلى الفصل {record['chapter_number']} "
                "وهو غير موجود في المخطوط المستوعَب.",
            )

    covered = {r["chapter_number"] for r in records if r["chapter_number"]}
    for number in sorted(chapter_numbers - covered):
        add(
            "EVIDENCE_LEDGER_ABSENT",
            "INFO",
            f"الفصل {number}",
            "لا سجل أدلة ولا خريطة برهان لهذا الفصل في مستودع الموسوعة.",
        )
