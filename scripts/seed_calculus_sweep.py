"""كنسة التفاضل المنفصل والشكل: خمس نتائج بقيت من GATE-PVG-GEO-001.

CALC-01، CALC-02، CALC-03، SHAPE-01، TAU-01. أُدرجت في سؤال البوابة ولم
يبلغها المسح الأول، فتُستكمل هنا.

المرتبتان نفسهما: ما له مصدر مقروء يُرفع، وما وجهتُه معروفة بلا مصدر يبقى
``LITERATURE_UNCLEAR`` مع تسمية المبرهنة بندَ متابعة.
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
    KnowledgeLink,
    LiteratureGate,
    ObservatoryReference,
    ReadingStatus,
    SourceLayer,
)
from sqlalchemy import select  # noqa: E402

REFERENCES = [
    dict(
        reference_key="MarshallOlkinArnold2011Majorization",
        title="Inequalities: Theory of Majorization and Its Applications",
        authors="Albert W. Marshall, Ingram Olkin, Barry C. Arnold",
        year=2011,
        venue="Springer Series in Statistics، الطبعة الثانية — كتاب معياري",
        reading_status=ReadingStatus.DISCOVERED,
        notes=(
            "مُدخَل بوصفه بندَ متابعة لا إسنادًا. المرجع المعياري لتقعّر Schur، "
            "وفيه أن الجداء ∏x_i (والدوال المتناظرة الأولية عمومًا) مقعَّرةٌ "
            "بمعنى Schur على الربع الموجب — وهذه هي المبرهنة التي تختزل إليها "
            "PVG-TAU-01. لم يُقرأ، فلا يصلح إسنادًا."
        ),
    ),
    dict(
        reference_key="CochainComplexAndCubicalCohomology",
        title="بديهية المركّب المشترك d∘d=0 على مركّب المكعّبات",
        authors="أدبيات الطوبولوجيا الجبرية والتفاضل الخارجي المتقطّع",
        year=None,
        venue="نتيجة تعريفية — لم يُثبَّت مصدر بعينه بعد",
        reading_status=ReadingStatus.DISCOVERED,
        notes=(
            "مُدخَل بوصفه بندَ متابعة. \\(d^2=0\\) بديهيةُ المركّب المشترك، "
            "وعلى شبكة \\(\\mathbb Z^k\\) (مركّب مكعّبات) هي واقعة قياسية في "
            "الكوهومولوجيا المكعّبية وحساب التفاضل الخارجي المتقطّع. لم أقرأ "
            "مصدرًا بعينه."
        ),
    ),
]

CLAIMS = [
    dict(
        claim_key="CLAIM-PVG-CALC-02",
        statement=(
            "دالة موجبة f ضربيةٌ ⟺ انعدام انحنائها المختلط اللوغاريتمي "
            "D_pD_q log f = 0 لكل p≠q (PVG-CALC-02)."
        ),
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "انعدامُ الفرق المختلط يعني أن log f ينفصل جمعًا على محاور "
            "الأوليات، أي أن f تُحدَّد كليًا بقيمها على قوى الأوليات. وهذا نصّ "
            "CashwellEverett1959RingOfNTFunctions، البند 6 ص977 (قُرئ): "
            "«α(Πp^a)=Πα(p^a) is multiplicative, α(p^a) being quite arbitrary "
            "for each power a … two multiplicative functions identical on all "
            "such p^a are equal». راجع GATE-PVG-GEO-001."
        ),
        novelty_note=(
            "لا جِدّة. الصياغة بلغة «الانحناء المختلط» تسمّي الشرط المعروف "
            "ولا تضيف إليه؛ وهي النظير المتقطّع لمعيار الانفصال الكلاسيكي "
            "∂²log f/∂x∂y = 0 ⟺ f = g(x)h(y)."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-CALC-03",
        statement=(
            "الفرق الثاني المحوري لدالة القواسم الخام ينعدم: D_p^{+2}τ = 0 "
            "(PVG-CALC-03)."
        ),
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "‏τ(p^a·m)=(a+1)τ(m) عند p∤m، وهي خطّية في a، فالفرق الثاني صفر. "
            "وصيغة τ=∏(a_p+1) مسنَدة في CLAIM-PVG-FND-05 إلى "
            "Haukkanen2016UnitaryDivisorSemilattice. راجع GATE-PVG-GEO-001."
        ),
        novelty_note=(
            "لا جِدّة. وقيمة هذه النتيجة **تصحيحية**: الأرشيف يسجّل أن الادعاء "
            "القديم بسالبية الانحناء المحوري الخام كان خطأ، وأن السالب يظهر "
            "لـlog τ لا لـτ. وتصحيح الذات أنفع من نتيجة جديدة."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-CALC-01",
        statement=(
            "‏d²=0 على شبكة PVG، فدورانُ حقل التدرج حول كل مربع صفر — ولا يصحّ "
            "ذلك لكل حقل، بل للحقول التدرجية وحدها (PVG-CALC-01)."
        ),
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "‏d²=0 بديهيةُ المركّب المشترك، وشبكة الأُسُس ℤ^k مركّبُ مكعّبات. "
            "راجع CochainComplexAndCubicalCohomology وGATE-PVG-GEO-001."
        ),
        novelty_note=(
            "الترجيح القاطع أنها تعريفية لا نتيجة، ولم أقرأ مصدرًا بعينه فلا "
            "تُرفع. وقيمتها هنا **تصحيحية** أيضًا: الأرشيف يسجّل أن الادعاء "
            "القديم بأن كل حقل على PVG عديم الدوران كان خطأ، ويعطي المثال "
            "المضاد V=(−b,a)."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-TAU-01",
        statement=(
            "عند ثبات ω(n)=k وΩ(n)=A، تبلغ τ(n)=∏(a_i+1) أقصاها عند التوزيع "
            "المتوازن (q+1)^r q^{k−r} حيث A=kq+r؛ وlog τ مقعَّرة بمعنى Schur "
            "(PVG-TAU-01، PVG-SHAPE-01)."
        ),
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "تختزل إلى تقعّر Schur للجداء ∏x_i على الربع الموجب، مع كون "
            "التغليب محفوظًا تحت الإزاحة a↦a+1. فُحص استقصاءً تامًّا: "
            "9,681,337 زوجًا مغلِّبًا، k من 2 إلى 5 وΩ حتى 15 — إزاحة التغليب "
            "وتقعّر Schur يصحّان في كل الحالات، والشكل الأمثل يطابق "
            "(q+1)^r q^{k−r} في كل حالة (scripts/verify_tau_majorization.py). "
            "راجع GATE-PVG-GEO-001."
        ),
        novelty_note=(
            "الوجهة معروفة — MarshallOlkinArnold2011Majorization — والأرشيف "
            "يستعمل مصطلح Schur-concave بنفسه، فالجِدّة غير مدَّعاة. ولم أقرأ "
            "الكتاب، فلا تُرفع إلى KNOWN.\n"
            "وملاحظة منهجية: مُلخِّصٌ آلي زعم أثناء المسح أن التغليب لا يُحفظ "
            "تحت الإزاحة، والفحص الاستقصائي أثبت خطأه. مخرَجُ أداةٍ ليس مصدرًا."
        ),
    ),
]

LINKS = [
    ("claim", "CLAIM-PVG-CALC-01", "DEPENDS-ON", "pvg_result", "PVG-CALC-01"),
    ("claim", "CLAIM-PVG-CALC-02", "DEPENDS-ON", "pvg_result", "PVG-CALC-02"),
    ("claim", "CLAIM-PVG-CALC-03", "DEPENDS-ON", "pvg_result", "PVG-CALC-03"),
    ("claim", "CLAIM-PVG-TAU-01", "DEPENDS-ON", "pvg_result", "PVG-TAU-01"),
    ("claim", "CLAIM-PVG-TAU-01", "DEPENDS-ON", "pvg_result", "PVG-SHAPE-01"),
    ("claim", "CLAIM-PVG-CALC-01", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
    ("claim", "CLAIM-PVG-CALC-02", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
    ("claim", "CLAIM-PVG-CALC-03", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
    ("claim", "CLAIM-PVG-TAU-01", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
]

GATE_REFS = [
    ("GATE-PVG-GEO-001", "MarshallOlkinArnold2011Majorization", GateRelation.ADJACENT,
     "الوجهة الصحيحة لـTAU-01/SHAPE-01: تقعّر Schur للجداء. بند متابعة."),
    ("GATE-PVG-GEO-001", "CochainComplexAndCubicalCohomology", GateRelation.ADJACENT,
     "الوجهة الصحيحة لـCALC-01. بند متابعة."),
]


def _sync(session, model, key_field: str, key: str, fields: dict) -> str:
    row = session.scalars(
        select(model).where(getattr(model, key_field) == key)
    ).one_or_none()
    if row is None:
        session.add(model(**{key_field: key}, **fields))
        return "created"
    changed = False
    for name, value in fields.items():
        if getattr(row, name) != value:
            setattr(row, name, value)
            changed = True
    return "updated" if changed else "unchanged"


def main() -> int:
    tally: dict[str, int] = {}

    def count(what: str, outcome: str) -> None:
        tally[f"{what}:{outcome}"] = tally.get(f"{what}:{outcome}", 0) + 1

    with SessionLocal() as session:
        for spec in REFERENCES:
            key = spec.pop("reference_key")
            count("مرجع", _sync(session, ObservatoryReference, "reference_key", key, spec))
        session.flush()

        for gate_key, ref_key, relation, coverage in GATE_REFS:
            gate = session.scalars(
                select(LiteratureGate).where(LiteratureGate.gate_key == gate_key)
            ).one()
            ref = session.scalars(
                select(ObservatoryReference).where(
                    ObservatoryReference.reference_key == ref_key
                )
            ).one()
            existing = session.get(GateReference, (gate.id, ref.id))
            if existing is None:
                session.add(
                    GateReference(
                        gate_id=gate.id, reference_id=ref.id,
                        relation=relation, coverage_note=coverage,
                    )
                )
                count("ربط-مرجع", "created")
            else:
                existing.relation, existing.coverage_note = relation, coverage
                count("ربط-مرجع", "updated")

        for spec in CLAIMS:
            key = spec.pop("claim_key")
            spec["source_layer"] = SourceLayer.PVG_RESEARCH
            count("ادعاء", _sync(session, Claim, "claim_key", key, spec))

        for from_type, from_key, relation, to_type, to_key in LINKS:
            exists = session.scalars(
                select(KnowledgeLink).where(
                    KnowledgeLink.from_type == from_type,
                    KnowledgeLink.from_key == from_key,
                    KnowledgeLink.relation == relation,
                    KnowledgeLink.to_type == to_type,
                    KnowledgeLink.to_key == to_key,
                )
            ).one_or_none()
            if exists is None:
                session.add(
                    KnowledgeLink(
                        from_type=from_type, from_key=from_key, relation=relation,
                        to_type=to_type, to_key=to_key,
                    )
                )
                count("رابط", "created")
            else:
                count("رابط", "unchanged")

        session.commit()

    for label in sorted(tally):
        print(f"  {label:22} {tally[label]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
