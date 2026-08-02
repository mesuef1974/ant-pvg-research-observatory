"""يربط مدونة PVG بشبكة المعرفة: المرئيات بنتائجها، والمذكرة ببوابتها.

المرئية بلا رابط زينةٌ معلّقة، والقسم 23 بلا رابط بحثٌ لا يعرف أحد أنه جرى.
والمطابقة أدناه مبنية على ما تعرضه كل صفحة فعلًا لا على تشابه الأسماء:
قُرئ نصّ كل مرئية واستُخرج منه المقدار الذي ترسمه.

متكافئ التنفيذ: يُدخل الرابط إن غاب ويترك الموجود، فإعادة التشغيل لا تُضاعف.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ant_pvg_observatory.db import SessionLocal  # noqa: E402
from ant_pvg_observatory.models import KnowledgeLink  # noqa: E402
from sqlalchemy import select  # noqa: E402

#: مرئية ← النتيجة التي ترسمها، مع شاهد من نصّ الصفحة نفسه.
VISUAL_LINKS: list[tuple[str, str, str]] = [
    (
        "pvg_vector_fields_face_2_3.html", "PVG-CALC-02",
        "الصفحة ترسم المشتقة المختلطة f(6n)−f(2n)−f(3n)+f(n) ونمطها "
        "اللوغاريتمي، وهو عين المقدار الذي تنصّ النتيجة على انعدامه.",
    ),
    (
        "pvg_2_3_information_surface_3d.html", "PVG-FACE-01",
        "أحد ارتفاعات السطح هو العمق min(a,b) نصًّا.",
    ),
    (
        "pvg_2_3_information_surface_3d.html", "PVG-CALC-02",
        "ومن ارتفاعاته أيضًا انحناء التفاعل K□.",
    ),
    (
        "pvg_2_3_flow_dynamics.html", "PVG-SHAPE-01",
        "تعرض انتشار الكتلة وحركة مركزها نحو الاتزان على الطبقات.",
    ),
    (
        "pvg_three_faces_2_3_5.html", "PVG-CONE-01",
        "تعرض الوجوه الثلاثة 2–3 و2–5 و3–5 مجتمعةً.",
    ),
    (
        "pvg_three_faces_2_3_5.html", "PVG-GLUE-01",
        "وتُظهر المحاور المشتركة بين الوجوه، وهي موضوع شرط التوافق.",
    ),
    (
        "pvfc_fiber_1_interactive.html", "PVFC-01",
        "الليف الأساسي (1) وأول تفرّع له، مع خيار إظهار معادلة ديريشليه.",
    ),
    (
        "pvfc_fiber_1_3d_interactive.html", "PVFC-01",
        "النسخة ثلاثية الأبعاد من الليف نفسه: (1) إلى (2) أو (1,1).",
    ),
    (
        "pvfc_fiber_levels_1_to_3_3d.html", "PVFC-05",
        "تولّد الألياف بعمليتَي الولادة والرفع، وهما مادة وحدة birth–jet.",
    ),
    (
        "pvfc_fiber_levels_1_to_3_3d.html", "PVFC-06",
        "ومستوياتها الثلاثة تقابل الحد الأول والثاني والثالث. "
        "(تصحيح: نُسبت هذه الصفحة سابقًا إلى PVFC-02 بلا سند من نصّها.)",
    ),
]

#: المذكرة ← البوابة التي فحصت الأدبيات لأجل قسمها 23.
DOCUMENT_LINKS: list[tuple[str, str, str, str]] = [
    (
        "90_SESSION_MEMORY_2026-08-01_v2", "EXAMINES", "GATE-PVFC-SD-001",
        "القسم 23 يوازن بين ما تبيّن وجوده في الأدبيات وما يختلف في مسار "
        "PVG، وهو سؤال البوابة نفسه. حكم البوابة PARTIAL ولا يزال معلّقًا "
        "على قراءة arXiv:2505.18504.",
    ),
]


def _ensure(session, *, from_type, from_key, relation, to_type, to_key, note) -> bool:
    exists = session.scalars(
        select(KnowledgeLink).where(
            KnowledgeLink.from_type == from_type,
            KnowledgeLink.from_key == from_key,
            KnowledgeLink.relation == relation,
            KnowledgeLink.to_type == to_type,
            KnowledgeLink.to_key == to_key,
        )
    ).one_or_none()
    if exists is not None:
        return False
    session.add(
        KnowledgeLink(
            from_type=from_type, from_key=from_key, relation=relation,
            to_type=to_type, to_key=to_key, note=note,
        )
    )
    return True


def main() -> int:
    created = 0
    with SessionLocal() as session:
        for visual, result_key, note in VISUAL_LINKS:
            created += _ensure(
                session, from_type="visual", from_key=visual, relation="DEPICTS",
                to_type="pvg_result", to_key=result_key, note=note,
            )
        for slug, relation, gate_key, note in DOCUMENT_LINKS:
            created += _ensure(
                session, from_type="pvg_document", from_key=slug, relation=relation,
                to_type="gate", to_key=gate_key, note=note,
            )
        session.commit()
        total = len(
            session.scalars(
                select(KnowledgeLink).where(
                    KnowledgeLink.from_type.in_(("visual", "pvg_document"))
                )
            ).all()
        )
    print(f"روابط أُنشئت: {created} | روابط طبقة PVG في الشبكة: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
