"""يرفع PVFC-03 وPVFC-04 بعد العثور على مصدر محكَّم مفتوح وقراءتِه.

بندُ المتابعة كان: «مصدر مقروء لتضايف مؤثّرَي الصعود والهبوط». وُجد ومُقرئ:
Liu–Smith، *Up- and Down-operators on Young's Lattice*، Electronic Journal of
Combinatorics 28(3) 2021 #P3.30 — **محكَّمة ومفتوحة**.

وهذا يُنهي حالة LITERATURE-UNCLEAR لهاتين، ويُبقيها لأربع أخرى لم أجد لها
مصدرًا مقروءًا بعد جهد معقول: FM-01/02، GLUE-01، CALC-01، TAU-01/SHAPE-01.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ant_pvg_observatory.db import SessionLocal  # noqa: E402
from ant_pvg_observatory.models import (  # noqa: E402
    Claim,
    ClaimStatus,
    GateReference,
    GateRelation,
    LiteratureGate,
    ObservatoryReference,
    ReadingStatus,
)
from sqlalchemy import select  # noqa: E402

REFERENCE = dict(
    reference_key="LiuSmith2021UpDownOperatorsYoung",
    title="Up- and Down-operators on Young's Lattice",
    authors="Ricky Ini Liu, Christian Smith",
    year=2021,
    venue="Electronic Journal of Combinatorics 28(3) #P3.30 — **محكَّمة**، مفتوحة",
    doi="10.37236/10099",
    url="https://doi.org/10.37236/10099",
    # VERIFIED: قُرئت الصفحتان 1–2 في الملف الأصلي بالعين، لا نقلًا عن ملخِّص.
    reading_status=ReadingStatus.VERIFIED,
    notes=(
        "قُرئت الصفحتان 1–2. المقدمة ص1 تنصّ أن مؤثرات Schur «can also be seen "
        "as refinements of the **raising and lowering operators U and D acting "
        "on Young's lattice** as defined by Stanley in his study of "
        "**differential posets**».\n"
        "وص2 تنصّ صراحةً على التضايف: «using the fact that the down-operators "
        "can be thought of as **transposes of the up-operators**». وتُدرج "
        "العلاقات: d_i u_j = u_j d_i لـi≠j، و**d₁u₁ = id**، "
        "وd_{i+1}u_{i+1} = u_i d_i (المبرهنة 1).\n"
        "أي أن تضايف الصعود والهبوط على شبكة يونغ، وعلاقةَ التبديل من نمط "
        "هايزنبرغ، كلاهما مقرَّر في دورية محكَّمة."
    ),
)

CLAIM_UPDATES = {
    "CLAIM-PVFC-03": dict(
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "‏LiuSmith2021UpDownOperatorsYoung، ص2، محكَّمة (قُرئت): مؤثرات "
            "الهبوط **منقولاتُ** مؤثرات الصعود — «the down-operators can be "
            "thought of as transposes of the up-operators». والنقل هو التضايف "
            "تحت الجداء الداخلي الذي تكون فيه التقسيمات أساسًا متعامدًا، ومنه "
            "K=U*U نصفُ معرَّفة موجبة تلقائيًا. وص1 تنسب U وD إلى Stanley في "
            "دراسته للمجموعات التفاضلية جزئية الترتيب. راجع GATE-PVFC-SD-001."
        ),
        novelty_note=(
            "لا جِدّة في التضايف ولا في K≥0: الأول مقرَّر، والثاني يتبعه في "
            "سطر. وكانت هذه `LITERATURE-UNCLEAR` حتى وُجد المصدر وقُرئ.\n"
            "**وما يبقى سؤالًا حقيقيًا** هو الوزن w(λ)=∏_r m_r(λ)! بعينه: هل "
            "هو الجداء الداخلي الذي تكون فيه التقسيمات متعامدة متجانسة، أم "
            "جداء Hall، أم ثالث؟ التضايف يتوقف على هذا الاختيار، والمصدر لا "
            "يحسمه لأنه يعمل بأساس متعامد معياري. بند متابعة دقيق."
        ),
    ),
    "CLAIM-PVFC-04": dict(
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "‏LiuSmith2021UpDownOperatorsYoung، المبرهنة 1 ص2، محكَّمة (قُرئت): "
            "جبر مؤثرات الصعود والهبوط على شبكة يونغ يُقدَّم بعلاقات تربيعية، "
            "منها d_i u_j = u_j d_i لـi≠j و**d₁u₁ = id** — وهي نمطُ [D,B]=I "
            "نفسُه. والأرشيف يصرّح في بنده الثامن أنها «مؤثرات تقسيمات كلاسيكية "
            "في جوهرها». راجع GATE-PVFC-SD-001."
        ),
        novelty_note=(
            "لا جِدّة ولم تُدَّع. والمؤثرات في PVFC مصوغة على ℚ[y_j] لا على "
            "شبكة يونغ مباشرةً، فالتطابق **بنيوي لا حرفي**: الجبر واحد، "
            "والتحقيق مختلف. وهذا كافٍ لـKNOWN-IN-EQUIVALENT-FORM ولا يزيد."
        ),
    ),
}


def main() -> int:
    # الطرفية على ويندوز cp1256 ولا تسع السهم
    sys.stdout.reconfigure(encoding="utf-8")

    with SessionLocal() as session:
        key = REFERENCE["reference_key"]
        fields = {k: v for k, v in REFERENCE.items() if k != "reference_key"}
        row = session.scalars(
            select(ObservatoryReference).where(
                ObservatoryReference.reference_key == key
            )
        ).one_or_none()
        if row is None:
            session.add(ObservatoryReference(reference_key=key, **fields))
            print(f"  مرجع أُضيف           {key}")
        else:
            for name, value in fields.items():
                setattr(row, name, value)
            print(f"  مرجع حُدِّث            {key}")
        session.flush()

        gate = session.scalars(
            select(LiteratureGate).where(
                LiteratureGate.gate_key == "GATE-PVFC-SD-001"
            )
        ).one()
        ref = session.scalars(
            select(ObservatoryReference).where(
                ObservatoryReference.reference_key == key
            )
        ).one()
        link = session.get(GateReference, (gate.id, ref.id))
        coverage = (
            "يُسند تضايف الصعود والهبوط (PVFC-03) وعلاقة التبديل (PVFC-04). "
            "محكَّمة ومقروءة، فترفع الحالتين من LITERATURE-UNCLEAR."
        )
        if link is None:
            session.add(
                GateReference(
                    gate_id=gate.id, reference_id=ref.id,
                    relation=GateRelation.COVERS, coverage_note=coverage,
                )
            )
            print("  ربط بوابة أُضيف")
        else:
            link.relation, link.coverage_note = GateRelation.COVERS, coverage
            print("  ربط بوابة حُدِّث")

        for claim_key, updates in CLAIM_UPDATES.items():
            claim = session.scalars(
                select(Claim).where(Claim.claim_key == claim_key)
            ).one()
            before = claim.status.value
            for name, value in updates.items():
                setattr(claim, name, value)
            print(f"  {claim_key:18} {before} → {claim.status.value}")

        session.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
