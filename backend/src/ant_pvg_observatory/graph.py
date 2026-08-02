"""شبكة الروابط: حلّ أطرافها، وجوارها، واشتقاقها من نصوص الادعاءات.

الروابط تُخزَّن بنوعٍ ومفتاحٍ نصي لا بمفتاح أجنبي، لأن الأطراف متغايرة الأنواع
وقد يسبق الرابطُ وجودَ طرفه. وثمن ذلك أن الطرف قد يكون معلَّقًا، فهذه الوحدة
تحلّ كل طرف إلى كائنه وتُعلن ما لم يُحَلّ بدل تركه يبدو سليمًا.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from . import pvg
from .models import (
    Claim,
    EncyclopediaResult,
    KnowledgeLink,
    LiteratureGate,
    ModelSynthesisNote,
    ObservatoryReference,
    PvgDocument,
    PvgResult,
)

#: نمط المفتاح لكل نوع، ويُستدل به على النوع حين لا يُصرَّح به.
KEY_PATTERNS: dict[str, re.Pattern[str]] = {
    "result": re.compile(r"^ANT-[A-Z]+-\d+-\d+$"),
    "model_note": re.compile(r"^MS-[A-Z]+-\d+$"),
    "claim": re.compile(r"^CLAIM-"),
    "gate": re.compile(r"^GATE-"),
    "reference": re.compile(r"^REF-"),
    "pvg_result": re.compile(r"^(?:PVG-[A-Z]+-\d+|PVFC-\d+|ADD-\d+)$"),
    # المرئية طرفٌ في الشبكة لا زينة: تُربط بالنتيجة التي ترسمها.
    "visual": re.compile(r"^[\w-]+\.html$"),
}


def infer_type(key: str) -> str | None:
    for kind, pattern in KEY_PATTERNS.items():
        if pattern.match(key):
            return kind
    return None


@dataclass(frozen=True, slots=True)
class ResolvedNode:
    node_type: str
    key: str
    exists: bool
    label: str | None = None
    status: str | None = None
    #: هل يجوز الاستناد إليه؟ ``False`` صريحة لطبقة المعرفة المعيارية.
    citable: bool | None = None


@dataclass(slots=True)
class Neighbourhood:
    node: ResolvedNode
    outgoing: list[dict] = field(default_factory=list)
    incoming: list[dict] = field(default_factory=list)


def resolve_node(session: Session, node_type: str, key: str) -> ResolvedNode:
    """يحلّ طرفًا إلى كائنه. النوع غير المعروف يُعاد غير موجود لا يُخترع له كائن."""
    if node_type == "result":
        row = session.scalars(
            select(EncyclopediaResult).where(EncyclopediaResult.result_key == key)
        ).one_or_none()
        if row:
            return ResolvedNode(
                node_type, key, True,
                label=row.title, status=row.registry_status, citable=bool(row.citable),
            )
    elif node_type == "claim":
        row = session.scalars(
            select(Claim).where(Claim.claim_key == key)
        ).one_or_none()
        if row:
            return ResolvedNode(
                node_type, key, True, label=row.statement[:160], status=row.status.value
            )
    elif node_type == "gate":
        row = session.scalars(
            select(LiteratureGate).where(LiteratureGate.gate_key == key)
        ).one_or_none()
        if row:
            return ResolvedNode(
                node_type, key, True, label=row.title, status=row.verdict
            )
    elif node_type == "reference":
        row = session.scalars(
            select(ObservatoryReference).where(
                ObservatoryReference.reference_key == key
            )
        ).one_or_none()
        if row:
            return ResolvedNode(
                node_type, key, True,
                label=row.title, status=row.reading_status.value,
            )
    elif node_type == "model_note":
        row = session.scalars(
            select(ModelSynthesisNote).where(ModelSynthesisNote.note_key == key)
        ).one_or_none()
        if row:
            # هذه الطبقة لا يُستشهد بها بحال، فتُعلن غير قابلة صراحةً.
            return ResolvedNode(
                node_type, key, True, label=row.title, status=row.kind, citable=False
            )
    elif node_type == "pvg_result":
        row = session.scalars(
            select(PvgResult).where(PvgResult.result_key == key)
        ).one_or_none()
        if row:
            # ``citable`` هنا تعني «يجوز البناء عليها كبرهان»، لا أكثر: حتى
            # المبرهنة منها غير منشورة، فلا ترفع ادعاءً إلى KNOWN.
            return ResolvedNode(
                node_type, key, True,
                label=(row.statement or "")[:160] or key,
                status=row.status,
                citable=bool(row.is_proven),
            )
    elif node_type == "pvg_document":
        row = session.scalars(
            select(PvgDocument).where(PvgDocument.slug == key)
        ).one_or_none()
        if row:
            return ResolvedNode(node_type, key, True, label=row.title)
    elif node_type == "visual":
        if (pvg.VISUALS_DIR / key).is_file():
            return ResolvedNode(node_type, key, True, label=key)
    return ResolvedNode(node_type, key, False)


def _edge(session: Session, link: KnowledgeLink, *, outgoing: bool) -> dict:
    other_type = link.to_type if outgoing else link.from_type
    other_key = link.to_key if outgoing else link.from_key
    other = resolve_node(session, other_type, other_key)
    return {
        "link_id": link.id,
        "relation": link.relation,
        "direction": "outgoing" if outgoing else "incoming",
        "note": link.note,
        "node_type": other.node_type,
        "key": other.key,
        "exists": other.exists,
        "label": other.label,
        "status": other.status,
        "citable": other.citable,
    }


def neighbourhood(session: Session, key: str, node_type: str | None = None) -> Neighbourhood:
    """جوار عقدة: ما يخرج منها وما يدخل إليها، بأطراف محلولة."""
    resolved = resolve_node(session, node_type or infer_type(key) or "unknown", key)
    links = session.scalars(
        select(KnowledgeLink)
        .where(or_(KnowledgeLink.from_key == key, KnowledgeLink.to_key == key))
        .order_by(KnowledgeLink.relation, KnowledgeLink.to_key)
    ).all()
    return Neighbourhood(
        node=resolved,
        outgoing=[_edge(session, link, outgoing=True) for link in links if link.from_key == key],
        incoming=[_edge(session, link, outgoing=False) for link in links if link.to_key == key],
    )


def check_links(session: Session, add) -> None:
    """يُعلن الروابط المعلَّقة والروابط إلى ما لا يجوز الاستناد إليه."""
    for link in session.scalars(select(KnowledgeLink)).all():
        subject = f"{link.from_key} —{link.relation}→ {link.to_key}"
        for node_type, key, side in (
            (link.from_type, link.from_key, "المصدر"),
            (link.to_type, link.to_key, "الهدف"),
        ):
            resolved = resolve_node(session, node_type, key)
            if not resolved.exists:
                add(
                    "LINK_ENDPOINT_MISSING", "MEDIUM", subject,
                    f"طرف {side} «{key}» من نوع {node_type} غير موجود في القاعدة.",
                )
            elif resolved.citable is False and link.relation.upper().startswith(
                ("DEPENDS", "CITES", "SUPPORTED")
            ):
                add(
                    "LINK_TO_NONCITABLE", "HIGH", subject,
                    f"الرابط يجعل «{key}» سندًا، وهو غير قابل للاستشهاد.",
                )


def derive_links_from_claims(session: Session) -> list[KnowledgeLink]:
    """يشتق روابط ``DEPENDS-ON`` من معرّفات ANT المذكورة في نصوص الادعاءات.

    عمل صريح لا تلقائي: ذكرُ معرّف في نص ليس إعلانَ اعتماد، فلا تُنشأ الروابط
    عند حفظ الادعاء. لكن استخراجها عند الطلب يوفّر إعادة الكتابة يدويًا.
    """
    pattern = KEY_PATTERNS["result"]
    result_pattern = re.compile(r"ANT-[A-Z]+-\d+-\d+")
    created: list[KnowledgeLink] = []
    for claim in session.scalars(select(Claim)).all():
        blob = " ".join(
            filter(None, (claim.statement, claim.evidence_note, claim.novelty_note))
        )
        for key in sorted(set(result_pattern.findall(blob))):
            if not pattern.match(key):
                continue
            exists = session.scalars(
                select(KnowledgeLink).where(
                    KnowledgeLink.from_type == "claim",
                    KnowledgeLink.from_key == claim.claim_key,
                    KnowledgeLink.relation == "DEPENDS-ON",
                    KnowledgeLink.to_type == "result",
                    KnowledgeLink.to_key == key,
                )
            ).one_or_none()
            if exists is not None:
                continue
            link = KnowledgeLink(
                from_type="claim",
                from_key=claim.claim_key,
                relation="DEPENDS-ON",
                to_type="result",
                to_key=key,
                note="مُشتق من نص الادعاء",
            )
            session.add(link)
            created.append(link)
    session.commit()
    return created


#: السجلات الدائمة للبوابات: ملفات Markdown خاضعة لـGit بجانب الكود.
GATE_RECORD_DIR = "docs/gates"


def gate_record_path(repo_root, gate_key: str) -> Path | None:
    """مسار السجل الدائم لبوابة، أو ``None`` إن لم يوجد.

    الاحتواء مفروض: المفتاح يأتي من الطلب، فلا يُركَّب في مسار بلا فحص.
    """
    directory = (Path(repo_root).resolve() / GATE_RECORD_DIR).resolve()
    candidate = (directory / f"{gate_key}.md").resolve()
    if not candidate.is_relative_to(directory) or not candidate.is_file():
        return None
    return candidate
