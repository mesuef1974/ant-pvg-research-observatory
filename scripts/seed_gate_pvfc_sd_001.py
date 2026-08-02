#!/usr/bin/env python3
"""يحمّل بوابة PVFC–Selberg–Delange ومراجعها من سجلها الدائم.

السجل الدائم هو ``docs/gates/GATE-PVFC-SD-001.md``؛ هذا السكربت يضعه في قاعدة
البيانات ليصير قابلًا للتصفح والربط. ولا يُزرع في إقلاع التطبيق: البيانات
البحثية ليست جزءًا من المخطط.

    python scripts/seed_gate_pvfc_sd_001.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ant_pvg_observatory.db import SessionLocal  # noqa: E402
from ant_pvg_observatory.models import (  # noqa: E402
    GateReference,
    GateRelation,
    GateVerdict,
    LiteratureGate,
    ObservatoryReference,
    ReadingStatus,
)
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

GATE_KEY = "GATE-PVFC-SD-001"

GATE = {
    "title": "مؤثرات انتقال الألياف وأبراج Selberg–Delange",
    "research_question": (
        "هل يوجد في الأدبيات تمثيل موحد لانتقالات الألياف على جميع معاملات "
        "Selberg–Delange، بحيث يُعطى برج المعاملات التقاربية بمؤثرات رفع/خفض "
        "على بنية دوال متناظرة مخصَّصة عند x_p = p^{-s}؟"
    ),
    # يبقى قيد المراجعة: المسح الأول غير شامل، وبنود المتابعة في السجل الدائم.
    "status": "REVIEW-IN-PROGRESS",
    "verdict": GateVerdict.PARTIAL.value,
}

# حالة القراءة DISCOVERED مقصودة: لم يُقرأ أيٌّ منها بعد، والمرصد يمنع بذلك
# إغلاق البوابة بحكم KNOWN.
REFERENCES = [
    {
        "reference_key": "Weising2024ArtinSymmetricFunctions",
        "title": "Artin Symmetric Functions",
        "authors": "Milo Bechtloff Weising",
        "year": "2024",
        "venue": "arXiv:2409.09643v3 — نسخة أولية، لا مرجع دورية",
        "doi": "10.48550/arXiv.2409.09643",
        "url": "https://arxiv.org/abs/2409.09643",
        "reading_status": ReadingStatus.DISCOVERED,
        "notes": (
            "أقرب إطار وجدته إلى CLAIM-0001: حلقة دوال متناظرة مفهرسة بالمثاليات "
            "الأولية، وفكّ في أساس Hall–Littlewood، وتحويلات Mellin إلى جداءات "
            "دوال L لأرتين. نسخة أولية — لا تُعامل معاملة المحكَّم."
        ),
        "relation": GateRelation.PARTIAL,
        "coverage_note": (
            "يغطي طرف الدوال المتناظرة المخصَّصة عند الأوليات، ولا يمسّ معاملات "
            "Selberg–Delange."
        ),
    },
    {
        "reference_key": "Jing1991VertexOperators",
        "title": "Vertex operators and Hall-Littlewood symmetric functions",
        "authors": "Naihuan Jing",
        "year": "1991",
        "venue": "Advances in Mathematics — محكَّم",
        "url": "https://doi.org/10.1016/0001-8708(91)90072-F",
        "reading_status": ReadingStatus.DISCOVERED,
        "notes": (
            "المؤثر القياسي الذي يُلحق جزءًا بالتقسيم. يجعل «مؤثر انتقال بين "
            "ألياف» مفهومًا معروفًا منذ 1991، فالجِدّة المحتملة في التخصيص "
            "العددي لا في وجود المؤثر."
        ),
        "relation": GateRelation.PARTIAL,
        "coverage_note": "يغطي طرف المؤثرات، ولا يمسّ التخصيص عند x_p = p^{-s}.",
    },
    {
        "reference_key": "BretecheTenenbaum2020Remarks",
        "title": "Remarks on the Selberg–Delange method",
        "authors": "Régis de la Bretèche, Gérald Tenenbaum",
        "year": "2020",
        "venue": "Acta Arithmetica — محكَّم",
        "reading_status": ReadingStatus.DISCOVERED,
        "notes": "أحدث معالجة للفروض التي تُنتج تقديرات حادة. لا بنية مؤثرات.",
        "relation": GateRelation.ADJACENT,
        "coverage_note": "يعالج التقديرات التقاربية لا بنية برج المعاملات.",
    },
    {
        "reference_key": "GranvilleKoukoulopoulos2017BeyondLSD",
        "title": "Beyond the LSD method for the partial sums of multiplicative functions",
        "authors": "Andrew Granville, Dimitris Koukoulopoulos",
        "year": "2017",
        "venue": "The Ramanujan Journal — محكَّم",
        "reading_status": ReadingStatus.DISCOVERED,
        "notes": "حدود طريقة Landau–Selberg–Delange حين يضعف حد الخطأ على الأوليات.",
        "relation": GateRelation.ADJACENT,
        "coverage_note": "يحدّ نطاق الطريقة، ولا يقدّم تمثيلًا موحدًا.",
    },
    {
        "reference_key": "Macdonald1995SymmetricFunctions",
        "title": "Symmetric Functions and Hall Polynomials",
        "authors": "I. G. Macdonald",
        "year": "1995",
        "venue": "Oxford University Press — كتاب معياري",
        "reading_status": ReadingStatus.DISCOVERED,
        "notes": (
            "الفصل الخامس: تماثل Satake وربط الأساس المتناظر بالعوامل المحلية. "
            "الجذر الأقدم للإطار كله، ويلزم فحصه قراءةً مباشرة."
        ),
        "relation": GateRelation.PARTIAL,
        "coverage_note": "الأصل النظري للتخصيص عند الأوليات.",
    },
]


def seed(session: Session) -> tuple[int, int]:
    gate = session.scalars(
        select(LiteratureGate).where(LiteratureGate.gate_key == GATE_KEY)
    ).one_or_none()
    if gate is None:
        gate = LiteratureGate(gate_key=GATE_KEY, **GATE)
        session.add(gate)
    else:
        for field, value in GATE.items():
            setattr(gate, field, value)
    session.flush()

    linked = 0
    for entry in REFERENCES:
        fields = {k: v for k, v in entry.items() if k not in ("relation", "coverage_note")}
        reference = session.scalars(
            select(ObservatoryReference).where(
                ObservatoryReference.reference_key == fields["reference_key"]
            )
        ).one_or_none()
        if reference is None:
            reference = ObservatoryReference(**fields)
            session.add(reference)
        else:
            for field, value in fields.items():
                setattr(reference, field, value)
        session.flush()

        link = session.get(GateReference, (gate.id, reference.id))
        if link is None:
            link = GateReference(gate_id=gate.id, reference_id=reference.id)
            session.add(link)
        link.relation = entry["relation"]
        link.coverage_note = entry["coverage_note"]
        linked += 1

    session.commit()
    return 1, linked


def main() -> None:
    with SessionLocal() as session:
        gates, references = seed(session)
    print(f"بوابات: {gates} | مراجع مربوطة: {references}")
    print("السجل الدائم: docs/gates/GATE-PVFC-SD-001.md")


if __name__ == "__main__":
    main()
