"""كنسة الأسس: فحص 13 نتيجة من الطبقة الكلاسيكية في PVG.

الدافع مباشر: تبيّن أن PVG-FND-01 وPVG-FND-06 منشورتان محكَّمتان منذ 1959.
والنتائج المجاورة لهما بقيت بلا فحص للسبب نفسه الذي أبقاهما — أنها «بديهية».
والبديهي أوّل ما يجب فحصه.

الغرض ليس تأكيد المتوقَّع، بل رسم **الخط الفاصل**: أين تنتهي الصياغة
الكلاسيكية بلغة PVG وأين يبدأ إسهام PVG. بلا هذا الخط كل ادعاء جِدّة مشبوه.

وتُفصَل النتائج إلى مرتبتين بحسب قوة الدليل لا بحسب الترجيح:

- **مسنَدة إلى مصدر مقروء** → ``KNOWN`` أو ``KNOWN_EQUIVALENT``.
- **اختزال إلى مبرهنة كلاسيكية مسمّاة بلا مصدر مقروء** → ``LITERATURE_UNCLEAR``
  مع تسمية المبرهنة بندَ متابعة. الترجيح القوي ليس دليلًا.
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
    GateVerdict,
    KnowledgeLink,
    LiteratureGate,
    ObservatoryReference,
    ReadingStatus,
    SourceLayer,
)
from sqlalchemy import select  # noqa: E402

REFERENCES = [
    dict(
        reference_key="Haukkanen2016UnitaryDivisorSemilattice",
        title="Embedding the unitary divisor meet semilattice in a lattice",
        authors="Pentti Haukkanen",
        year=2016,
        venue="Notes on Number Theory and Discrete Mathematics 22(3), 68–78 — محكَّم",
        url="https://nntdm.net/papers/nntdm-22/NNTDM-22-3-68-78.pdf",
        # VERIFIED لا FULLY-READ: لم أقرأ المقال كلّه، بل تحقّقتُ من الفقرة
        # المستشهَد بها في المصدر الأصلي حرفًا بحرف. وهذا أدقّ من الاثنين،
        # وأصدق من ادّعاء قراءة كاملة لم تقع.
        reading_status=ReadingStatus.VERIFIED,
        notes=(
            "قُرئت المقدمة (ص68–69) قراءةً كاملة في ملف PDF الأصلي؛ وبقيّة "
            "المقال عن القواسم الأحادية وهي خارج غرضنا. المقدمة تنصّ حرفيًا: "
            "«It is well known "
            "that the set ℤ₊ of positive integers is a poset under the usual "
            "divisibility relation. It is likewise well known that the gcd and "
            "the lcm operations serve as the meet and the join on this poset. "
            "Thus ℤ₊ is a lattice under the usual divisibility relation, known "
            "as the divisor lattice. This lattice is distributive.»\n"
            "ولها اسم مستقرّ: **the divisor lattice**. وتكرار «well known» "
            "مرّتين في سطرين هو بنفسه شهادةٌ على كلاسيكيّتها."
        ),
    ),
    dict(
        reference_key="SylvesterInertiaAndCompleteGraphSpectrum",
        title="قانون Sylvester للقصور الذاتي، وطيف مصفوفة جوار الغراف التام",
        authors="J. J. Sylvester (1852) وأدبيات الطيف البياني",
        year=1852,
        venue="نتيجتان كلاسيكيتان — لم يُثبَّت مصدر بعينه بعد",
        reading_status=ReadingStatus.DISCOVERED,
        notes=(
            "مُدخَل بوصفه بندَ متابعة لا إسنادًا. قانون Sylvester: التطابق "
            "المتجانس يحفظ القصور الذاتي. وطيف J−I لغراف K_k هو {k−1، و−1 "
            "بتضاعف k−1}. كلاهما في كل كتاب مقرَّر، ولم أقرأ مصدرًا بعينه، "
            "فلا يصلح إسنادًا لحالة موثقة."
        ),
    ),
]

GATES = [
    dict(
        gate_key="GATE-PVG-FND-002",
        title="أسس PVG الحسابية والشبكية: التقييم، والقسمة ترتيبًا، وصندوق القواسم",
        research_question=(
            "أربع نتائج من طبقة الأسس بقيت بلا فحص بعد أن تبيّن أن "
            "PVG-FND-01 وPVG-FND-06 هما Cashwell–Everett 1959:\n"
            "PVG-FND-02: ℚ_{>0} ≅ ⊕_p ℤ.\n"
            "PVG-FND-03: ν(mn)=ν(m)+ν(n).\n"
            "PVG-FND-04: القسمة ترتيب، وgcd/lcm هما min/max.\n"
            "PVG-FND-05: القواسم نقاط صندوق.\n"
            "هل كلٌّ منها في الأدبيات؟"
        ),
        status="CLOSED",
        verdict=GateVerdict.KNOWN,
        references=[
            ("CashwellEverett1959RingOfNTFunctions", GateRelation.COVERS,
             "البند 14 ص982 يعطي التماثل الوحيد بمتجه الأُسُس ويصرّح بأن الجمع "
             "محفوظ. وFND-03 هي عينُ كون التطابق تماثلَ أحاديات، وFND-02 هي "
             "تتمّته الزمرية على ℚ_{>0}."),
            ("Haukkanen2016UnitaryDivisorSemilattice", GateRelation.COVERS,
             "المقدمة ص68 تنصّ على FND-04 بلفظها، وتسمّيها «the divisor "
             "lattice»، وتصفها بـ«well known» مرّتين. وFND-05 تتبعها مباشرةً: "
             "d|n ⟺ 0 ≤ ν_p(d) ≤ ν_p(n) لكل p، فالقواسم فترةٌ في الشبكة، "
             "وعددُها ∏(a_i+1)=τ(n)."),
        ],
    ),
    dict(
        gate_key="GATE-PVG-GEO-001",
        title="هندسة المخروط والوجوه ومصفوفة الوجوه",
        research_question=(
            "تسع نتائج هندسية على المخروط ℕ₀^k:\n"
            "CONE-01: n²=∏ الإسقاطات الوجهية الثلاثة. CONE-02: إعادة البناء "
            "بجداءات gcd. FACE-01: عمق الوجه min(a,b). GLUE-01: شرط توافق "
            "المحاور المشتركة مكافئ للّصق. FM-01: توقيع (1,k−1,0). "
            "FM-02: صيغة المحدد. CALC-01: d²=0. CALC-02: الضربية تكافئ انعدام "
            "الانحناء المختلط. TAU-01: تعظيم τ عند التوازن.\n"
            "إلى أي مبرهنة كلاسيكية تختزل كلٌّ منها؟"
        ),
        # سُمّيت المبرهنة الكلاسيكية لكل نتيجة، ولم يُقرأ مصدر إلا للشبكة.
        # التسمية ليست استشهادًا، فالحكم PARTIAL.
        status="REVIEW-IN-PROGRESS",
        verdict=GateVerdict.PARTIAL,
        references=[
            ("Haukkanen2016UnitaryDivisorSemilattice", GateRelation.PARTIAL,
             "يغطّي القاعدة الشبكية (gcd=min) التي تتبعها CONE-01/02 وFACE-01 "
             "في سطر واحد، ولا يغطّي GLUE ولا FM ولا CALC ولا TAU."),
            ("SylvesterInertiaAndCompleteGraphSpectrum", GateRelation.ADJACENT,
             "الوجهة الصحيحة لـFM-01/02، وبندُ متابعة لا إسناد."),
        ],
    ),
]

CLAIMS = [
    dict(
        claim_key="CLAIM-PVG-FND-02",
        statement="ℚ_{>0} ≅ ⊕_p ℤ، أي زمرة حرة أبيلية على الأوليات (PVG-FND-02).",
        status=ClaimStatus.KNOWN,
        evidence_note=(
            "CashwellEverett1959RingOfNTFunctions، البند 14 ص982: التوصيف "
            "الوحيد لكل صحيح بمتجه أُسُس منتهي الحامل. وℚ_{>0} تتمّةُ ذلك "
            "الأحادي الزمرية، فيصير المتجه صحيحَ المركّبات. راجع GATE-PVG-FND-002."
        ),
        novelty_note="لا جِدّة ولم تُدَّع. هذه المبرهنة الأساسية في الحساب بلغة الزمر.",
    ),
    dict(
        claim_key="CLAIM-PVG-FND-03",
        statement="ν(mn)=ν(m)+ν(n): التقييم تماثلُ أحاديات (PVG-FND-03).",
        status=ClaimStatus.KNOWN,
        evidence_note=(
            "CashwellEverett1959RingOfNTFunctions، البند 14 ص982: كونُ "
            "n ↦ (a₁,a₂,…) توصيفًا وحيدًا يجعل جمع المتجهات هو ضربَ الأعداد. "
            "راجع GATE-PVG-FND-002."
        ),
        novelty_note=(
            "لا جِدّة. بل هذه صيغةُ تعريف التقييم p-adic نفسِه، فالسؤال عن "
            "سابقتها سؤالٌ عن سابقة التعريف."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-FND-04",
        statement=(
            "القسمة ترتيبٌ جزئي على ℤ₊، وgcd وlcm هما الالتقاء والاتحاد، "
            "أي min وmax على متجهات الأُسُس (PVG-FND-04)."
        ),
        status=ClaimStatus.KNOWN,
        evidence_note=(
            "Haukkanen2016UnitaryDivisorSemilattice، المقدمة ص68، محكَّم: "
            "«the gcd and the lcm operations serve as the meet and the join on "
            "this poset. Thus ℤ₊ is a lattice … known as the divisor lattice. "
            "This lattice is distributive.» راجع GATE-PVG-FND-002."
        ),
        novelty_note=(
            "لا جِدّة. وللبنية اسمٌ مستقرّ في الأدبيات — «the divisor lattice» — "
            "والمصدر يصفها «well known» مرّتين في سطرين."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-FND-05",
        statement=(
            "قواسم n نقاطُ صندوق: B(n)=∏[0,a_p]∩ℤ، وعددُها ∏(a_p+1)=τ(n) "
            "(PVG-FND-05)."
        ),
        status=ClaimStatus.KNOWN,
        evidence_note=(
            "تتبع مباشرةً من Haukkanen2016UnitaryDivisorSemilattice "
            "(ترتيب القسمة مركَّبيّ) مع CashwellEverett1959RingOfNTFunctions "
            "(متجه الأُسُس): d|n ⟺ 0 ≤ ν_p(d) ≤ ν_p(n) لكل p. "
            "راجع GATE-PVG-FND-002."
        ),
        novelty_note=(
            "لا جِدّة. وصيغة τ(n)=∏(a_p+1) في كل مقرَّر في نظرية الأعداد."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-CONE-01",
        statement=(
            "n²=π₂₃(n)π₂₅(n)π₃₅(n)، وn=∏ جداءات gcd الثنائية للإسقاطات "
            "(PVG-CONE-01، PVG-CONE-02)."
        ),
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "صياغةٌ مكافئة لحساب الأُسُس على الشبكة المعروفة في "
            "Haukkanen2016UnitaryDivisorSemilattice: كلُّ أُسٍّ يظهر في وجهين "
            "من الثلاثة بالضبط، فيتضاعف؛ وgcd هو min. الحالة العامة "
            "∏_{وجوه} π_F(n)=n^{k−1}. راجع GATE-PVG-GEO-001."
        ),
        novelty_note=(
            "لا جِدّة. عدُّ ظهور كل أُسٍّ في الوجوه حسابٌ مباشر، والصياغة "
            "الهندسية تسمّيه لا تضيف إليه."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-FACE-01",
        statement=(
            "العمق الوجهي d_{pq}=min(a,b)، وبعد نزع (pq)^d تقع البقية على "
            "أحد المحورين (PVG-FACE-01)."
        ),
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "min على متجهات الأُسُس هو gcd، وهذا نصّ "
            "Haukkanen2016UnitaryDivisorSemilattice. والعمق هو ν_{pq} لأكبر "
            "قوة من الجذر تقسم العدد. راجع GATE-PVG-GEO-001."
        ),
        novelty_note="لا جِدّة. استخراجُ أكبر قوة للجذر عمليةٌ قياسية.",
    ),
    dict(
        claim_key="CLAIM-PVG-GLUE-01",
        statement=(
            "ثلاث نقاط وجهية تلصق إلى نقطة واحدة في المخروط إذا وفقط إذا "
            "اتفقت على المحاور المشتركة (PVG-GLUE-01)."
        ),
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "المبرهنة صحيحة (PVG-GLUE-01). وصياغتها «تتفق على التقاطعات ⟺ "
            "تلصق» هي **شرط الحُزمة** بعينه — معادلُ المُسوّي (equalizer) على "
            "غطاء. والأرشيف يعرف ذلك: بندُه المفتوح هو «صياغة شيقية/حزمية "
            "كاملة للّصق». راجع GATE-PVG-GEO-001."
        ),
        novelty_note=(
            "الترجيح القوي أنها كلاسيكية (بديهية الحُزمة على الأحادي التآلفي "
            "ℕ₀^k في الهندسة التوريّة)، لكنّي لم أقرأ مصدرًا يقولها في هذا "
            "السياق. والترجيح ليس دليلًا. بند متابعة: تثبيت مصدر في نظرية "
            "الأحاديات التآلفية أو الهندسة التوريّة."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-FM-01",
        statement=(
            "لمصفوفة الوجوه F=vvᵀ−diag(a_i²): Inertia(F)=(1,k−1,0)، "
            "وdet F=(−1)^{k+1}(k−1)(∏a_i)² (PVG-FM-01، PVG-FM-02)."
        ),
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "النتيجتان صحيحتان، وتختزلان إلى تطابق واحد: F=D_a(J−I)D_a حيث "
            "D_a=diag(a_i). فـJ−I مصفوفةُ جوار الغراف التام K_k وطيفُها "
            "{k−1، و−1 بتضاعف k−1}، وقانون Sylvester للقصور الذاتي يحفظ "
            "التوقيع تحت التطابق المتجانس (عند a_i≠0)، ومنه المحدد "
            "det(D_a)²·det(J−I). فُحص التطابق والتوقيع والمحدد حاسوبيًا على "
            "360 حالة، k من 2 إلى 7: مطابقة تامة. راجع GATE-PVG-GEO-001."
        ),
        novelty_note=(
            "الاختزال مؤكَّد، والمبرهنتان اللتان يستند إليهما كلاسيكيتان "
            "(Sylvester 1852، وطيف K_k)، لكنّي لم أقرأ مصدرًا بعينه لأيٍّ "
            "منهما — فلا تُرفع إلى KNOWN. والفحص الحاسوبي يؤكّد الاختزال ولا "
            "يحلّ محلّ الاستشهاد: لا يحل الفحص محل البرهان، ولا محل المصدر."
        ),
    ),
]

LINKS = [
    ("claim", "CLAIM-PVG-FND-02", "DEPENDS-ON", "pvg_result", "PVG-FND-02"),
    ("claim", "CLAIM-PVG-FND-03", "DEPENDS-ON", "pvg_result", "PVG-FND-03"),
    ("claim", "CLAIM-PVG-FND-04", "DEPENDS-ON", "pvg_result", "PVG-FND-04"),
    ("claim", "CLAIM-PVG-FND-05", "DEPENDS-ON", "pvg_result", "PVG-FND-05"),
    ("claim", "CLAIM-PVG-CONE-01", "DEPENDS-ON", "pvg_result", "PVG-CONE-01"),
    ("claim", "CLAIM-PVG-CONE-01", "DEPENDS-ON", "pvg_result", "PVG-CONE-02"),
    ("claim", "CLAIM-PVG-FACE-01", "DEPENDS-ON", "pvg_result", "PVG-FACE-01"),
    ("claim", "CLAIM-PVG-GLUE-01", "DEPENDS-ON", "pvg_result", "PVG-GLUE-01"),
    ("claim", "CLAIM-PVG-FM-01", "DEPENDS-ON", "pvg_result", "PVG-FM-01"),
    ("claim", "CLAIM-PVG-FM-01", "DEPENDS-ON", "pvg_result", "PVG-FM-02"),
    ("claim", "CLAIM-PVG-FND-02", "EXAMINED-BY", "gate", "GATE-PVG-FND-002"),
    ("claim", "CLAIM-PVG-FND-03", "EXAMINED-BY", "gate", "GATE-PVG-FND-002"),
    ("claim", "CLAIM-PVG-FND-04", "EXAMINED-BY", "gate", "GATE-PVG-FND-002"),
    ("claim", "CLAIM-PVG-FND-05", "EXAMINED-BY", "gate", "GATE-PVG-FND-002"),
    ("claim", "CLAIM-PVG-CONE-01", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
    ("claim", "CLAIM-PVG-FACE-01", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
    ("claim", "CLAIM-PVG-GLUE-01", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
    ("claim", "CLAIM-PVG-FM-01", "EXAMINED-BY", "gate", "GATE-PVG-GEO-001"),
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

        for spec in GATES:
            refs = spec.pop("references")
            key = spec.pop("gate_key")
            count("بوابة", _sync(session, LiteratureGate, "gate_key", key, spec))
            session.flush()
            gate = session.scalars(
                select(LiteratureGate).where(LiteratureGate.gate_key == key)
            ).one()
            for ref_key, relation, coverage in refs:
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
