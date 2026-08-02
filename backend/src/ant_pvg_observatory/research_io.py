"""تصدير الطبقة البحثية واستيرادها.

قاعدة البيانات مُشتقّة في معظمها: الفصول والنتائج والببليوغرافيا تُعاد بناؤها
من مستودع الموسوعة في أي لحظة. لكن **الطبقة البحثية ليست مُشتقّة**: الادعاءات
والبوابات والمراجع وأحكامها وروابطها تُدخَل يدويًا ولا توجد إلا في ملف قاعدة
غير متتبَّع في Git. فقدانه فقدانٌ للعمل بلا أثر.

هذه الوحدة تجعل تلك الطبقة **نصًّا خاضعًا لـGit**: تصدير إلى JSON مرتَّب
ترتيبًا ثابتًا فتكون الفروق قابلة للقراءة، واستيراد يعيدها.

التصدير حتمي تمامًا: الترتيب مثبَّت، ولا طابع زمني في الملف إطلاقًا — لا طوابع
الإنشاء والتحديث ولا تاريخ التصدير نفسه. تاريخ التصدير يسجّله إيداع Git، ووضعه
في الملف كان سيُنتج فرقًا يوميًا بلا تغيّر في المحتوى.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Claim,
    ClaimStatus,
    GateReference,
    GateRelation,
    KnowledgeLink,
    LiteratureGate,
    ObservatoryReference,
    ReadingStatus,
    SourceLayer,
)

#: يُرفع عند أي تغيير غير متوافق في شكل الملف المُصدَّر.
FORMAT_VERSION = 1

DEFAULT_EXPORT_PATH = Path("exports/research-layer.json")


@dataclass(frozen=True, slots=True)
class ResearchLayerCounts:
    claims: int
    gates: int
    references: int
    gate_references: int
    links: int


@dataclass(frozen=True, slots=True)
class ImportReport:
    created: ResearchLayerCounts
    updated: ResearchLayerCounts
    #: موجود سلفًا بالقيم نفسها. يُفصل عن ``updated`` لأن «حُدِّث» تعني تغيّرًا.
    unchanged: ResearchLayerCounts
    skipped_links: int


def _apply(target, fields: dict) -> bool:
    """يضبط الحقول ويُرجع ما إذا تغيّر شيء فعلًا."""
    changed = False
    for field, value in fields.items():
        if getattr(target, field) != value:
            setattr(target, field, value)
            changed = True
    return changed


def _claim_row(claim: Claim) -> dict:
    return {
        "claim_key": claim.claim_key,
        "statement": claim.statement,
        "source_layer": claim.source_layer.value,
        "status": claim.status.value,
        "evidence_note": claim.evidence_note,
        "novelty_note": claim.novelty_note,
    }


def _gate_row(gate: LiteratureGate) -> dict:
    return {
        "gate_key": gate.gate_key,
        "title": gate.title,
        "research_question": gate.research_question,
        "status": gate.status,
        "verdict": gate.verdict,
    }


def _reference_row(reference: ObservatoryReference) -> dict:
    return {
        "reference_key": reference.reference_key,
        "title": reference.title,
        "authors": reference.authors,
        "year": reference.year,
        "venue": reference.venue,
        "doi": reference.doi,
        "url": reference.url,
        "reading_status": reference.reading_status.value,
        "notes": reference.notes,
        "bibliography_key": reference.bibliography_key,
    }


def export_research_layer(session: Session) -> dict:
    """يُرجع الطبقة البحثية كاملةً بترتيب ثابت."""
    claims = session.scalars(select(Claim).order_by(Claim.claim_key)).all()
    gates = session.scalars(
        select(LiteratureGate).order_by(LiteratureGate.gate_key)
    ).all()
    references = session.scalars(
        select(ObservatoryReference).order_by(ObservatoryReference.reference_key)
    ).all()
    gate_key_by_id = {gate.id: gate.gate_key for gate in gates}
    reference_key_by_id = {ref.id: ref.reference_key for ref in references}

    gate_links = [
        {
            # الربط بالمفاتيح لا بالمعرفات الرقمية: المعرفات تتغير بإعادة البناء.
            "gate_key": gate_key_by_id[link.gate_id],
            "reference_key": reference_key_by_id[link.reference_id],
            "relation": link.relation.value,
            "coverage_note": link.coverage_note,
        }
        for link in session.scalars(select(GateReference)).all()
        if link.gate_id in gate_key_by_id and link.reference_id in reference_key_by_id
    ]
    gate_links.sort(key=lambda row: (row["gate_key"], row["reference_key"]))

    links = [
        {
            "from_type": link.from_type,
            "from_key": link.from_key,
            "relation": link.relation,
            "to_type": link.to_type,
            "to_key": link.to_key,
            "note": link.note,
        }
        for link in session.scalars(select(KnowledgeLink)).all()
    ]
    links.sort(
        key=lambda row: (
            row["from_type"], row["from_key"], row["relation"],
            row["to_type"], row["to_key"],
        )
    )

    return {
        "format_version": FORMAT_VERSION,
        "claims": [_claim_row(c) for c in claims],
        "gates": [_gate_row(g) for g in gates],
        "references": [_reference_row(r) for r in references],
        "gate_references": gate_links,
        "links": links,
    }


def write_export(session: Session, path: Path | None = None) -> tuple[Path, ResearchLayerCounts]:
    path = Path(path or DEFAULT_EXPORT_PATH)
    payload = export_research_layer(session)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path, ResearchLayerCounts(
        claims=len(payload["claims"]),
        gates=len(payload["gates"]),
        references=len(payload["references"]),
        gate_references=len(payload["gate_references"]),
        links=len(payload["links"]),
    )


def import_research_layer(session: Session, payload: dict) -> ImportReport:
    """يستورد الطبقة البحثية. متكافئ التنفيذ: يُحدِّث الموجود ولا يُكرّره.

    لا يحذف شيئًا: الاستيراد استرجاع ودمج، لا مزامنة تدميرية. حذف سجل من
    الملف لا يحذفه من القاعدة، وهو سلوك مقصود يمنع الفقد بالخطأ.
    """
    version = payload.get("format_version")
    if version != FORMAT_VERSION:
        raise ValueError(
            f"صيغة ملف غير مدعومة: {version}؛ المتوقَّع {FORMAT_VERSION}."
        )

    keys = ("claims", "gates", "references", "gate_references", "links")
    created = dict.fromkeys(keys, 0)
    updated = dict.fromkeys(keys, 0)
    unchanged = dict.fromkeys(keys, 0)

    for row in payload.get("claims", []):
        claim = session.scalars(
            select(Claim).where(Claim.claim_key == row["claim_key"])
        ).one_or_none()
        fields = {
            "statement": row["statement"],
            "source_layer": SourceLayer(row["source_layer"]),
            "status": ClaimStatus(row["status"]),
            "evidence_note": row.get("evidence_note"),
            "novelty_note": row.get("novelty_note"),
        }
        if claim is None:
            session.add(Claim(claim_key=row["claim_key"], **fields))
            created["claims"] += 1
        else:
            target = claim
            if _apply(target, fields):
                updated["claims"] += 1
            else:
                unchanged["claims"] += 1

    for row in payload.get("gates", []):
        gate = session.scalars(
            select(LiteratureGate).where(LiteratureGate.gate_key == row["gate_key"])
        ).one_or_none()
        fields = {
            "title": row["title"],
            "research_question": row["research_question"],
            "status": row["status"],
            "verdict": row.get("verdict"),
        }
        if gate is None:
            session.add(LiteratureGate(gate_key=row["gate_key"], **fields))
            created["gates"] += 1
        else:
            target = gate
            if _apply(target, fields):
                updated["gates"] += 1
            else:
                unchanged["gates"] += 1

    for row in payload.get("references", []):
        reference = session.scalars(
            select(ObservatoryReference).where(
                ObservatoryReference.reference_key == row["reference_key"]
            )
        ).one_or_none()
        fields = {
            "title": row["title"],
            "authors": row.get("authors"),
            "year": row.get("year"),
            "venue": row.get("venue"),
            "doi": row.get("doi"),
            "url": row.get("url"),
            "reading_status": ReadingStatus(row["reading_status"]),
            "notes": row.get("notes"),
            "bibliography_key": row.get("bibliography_key"),
        }
        if reference is None:
            session.add(
                ObservatoryReference(reference_key=row["reference_key"], **fields)
            )
            created["references"] += 1
        else:
            target = reference
            if _apply(target, fields):
                updated["references"] += 1
            else:
                unchanged["references"] += 1

    session.flush()

    gate_ids = {
        gate.gate_key: gate.id
        for gate in session.scalars(select(LiteratureGate)).all()
    }
    reference_ids = {
        ref.reference_key: ref.id
        for ref in session.scalars(select(ObservatoryReference)).all()
    }

    skipped = 0
    for row in payload.get("gate_references", []):
        gate_id = gate_ids.get(row["gate_key"])
        reference_id = reference_ids.get(row["reference_key"])
        if gate_id is None or reference_id is None:
            skipped += 1
            continue
        link = session.get(GateReference, (gate_id, reference_id))
        fields = {
            "relation": GateRelation(row["relation"]),
            "coverage_note": row.get("coverage_note"),
        }
        if link is None:
            link = GateReference(gate_id=gate_id, reference_id=reference_id, **fields)
            session.add(link)
            created["gate_references"] += 1
        elif _apply(link, fields):
            updated["gate_references"] += 1
        else:
            unchanged["gate_references"] += 1

    for row in payload.get("links", []):
        existing = session.scalars(
            select(KnowledgeLink).where(
                KnowledgeLink.from_type == row["from_type"],
                KnowledgeLink.from_key == row["from_key"],
                KnowledgeLink.relation == row["relation"],
                KnowledgeLink.to_type == row["to_type"],
                KnowledgeLink.to_key == row["to_key"],
            )
        ).one_or_none()
        if existing is None:
            session.add(KnowledgeLink(**row))
            created["links"] += 1
        elif _apply(existing, {"note": row.get("note")}):
            updated["links"] += 1
        else:
            unchanged["links"] += 1

    session.commit()
    return ImportReport(
        created=ResearchLayerCounts(**created),
        updated=ResearchLayerCounts(**updated),
        unchanged=ResearchLayerCounts(**unchanged),
        skipped_links=skipped,
    )


def read_import(session: Session, path: Path | None = None) -> ImportReport:
    path = Path(path or DEFAULT_EXPORT_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"لا يوجد ملف تصدير في {path}")
    return import_research_layer(
        session, json.loads(path.read_text(encoding="utf-8"))
    )
