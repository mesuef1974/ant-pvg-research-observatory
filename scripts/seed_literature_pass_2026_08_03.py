"""حصيلة مسح أدبيات 2026-08-03: ثلاث بوابات جديدة، ومراجع مقروءة، وادعاءات.

المسح السابق ترك خمسة بنود متابعة، أوّلها وأهمّها قراءة arXiv:2505.18504 كاملةً.
قُرئت، فسقط أحد الاحتمالات وبقي أربعة بنود — والبوابة تبقى PARTIAL بسبب مُعلَن
لا بسبب إهمال.

والأهم أن هذا المسح وجد سابقةً محكَّمة عمرها 67 سنة لنتيجتين من أسس PVG.
عدمُ العثور سابقًا كان واقعةً عن مسحنا لا عن العالم، وهذه الواقعة انتهت.

متكافئ التنفيذ: يُدخل ما غاب ويُحدّث ما تغيّر، وإعادة التشغيل لا تُضاعف.
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

# ── مراجع جديدة كشفها المسح ─────────────────────────────────────────────

REFERENCES = [
    dict(
        reference_key="CashwellEverett1959RingOfNTFunctions",
        title="The ring of number-theoretic functions",
        authors="E. D. Cashwell, C. J. Everett",
        year=1959,
        venue="Pacific Journal of Mathematics 9(4), 975–985 — محكَّم",
        url="https://projecteuclid.org/journals/pacific-journal-of-mathematics/"
            "volume-9/issue-4/The-ring-of-number-theoretic-functions/pjm/1103038878",
        reading_status=ReadingStatus.FULLY_READ,
        notes=(
            "قُرئ المقال نفسه لا ملخّصًا عنه. المقدمة ص975 تنصّ: «The domain Ω is "
            "isomorphic to the domain P of formal power series over F in a "
            "countable set of indeterminates». والبند 14 ص982 يبني التماثل "
            "صراحةً: تُرتَّب الأوليات p₁,p₂,…، ويوصف كل عدد صحيح توصيفًا وحيدًا "
            "بمتجه أُسُس (a₁,a₂,…) منتهي الحامل، ثم α ↦ Σα(n)x₁^{a₁}x₂^{a₂}⋯، "
            "و«addition is preserved, and P(α·β)=P(α)P(β)». وضربُ متسلسلات القوى "
            "هو التفافُ معاملاتها الجمعي. أي أن PVG-FND-01 وPVG-FND-06 مذكورتان "
            "معًا في فقرة واحدة سنة 1959."
        ),
    ),
    dict(
        reference_key="Baez2025DirichletSpecies",
        title="Dirichlet Species and Arithmetic Zeta Functions",
        authors="John C. Baez",
        year=2025,
        venue="Theory and Applications of Categories 44(39), 1316–1336 — محكَّم",
        doi="10.48550/arXiv.2502.01833",
        url="https://arxiv.org/abs/2502.01833",
        reading_status=ReadingStatus.ABSTRACT_READ,
        notes=(
            "الملخّص فقط. تصنيفٌ فئوي لسلاسل ديريشليه عبر أنواع Joyal: كل نوع F "
            "يعطي سلسلة ديريشليه، ودالة زيتا الحسابية لمخطط تنشأ هكذا. مجاور "
            "لإطار PVFC (وWeising يستعمل الأنواع أيضًا)، ولم أتحقق بعد إن كان "
            "يخصّص المتغيرات عند p^{-s}. محكَّم، فيُستشهد به بحذر في حدود ملخّصه."
        ),
    ),
    dict(
        reference_key="MacHenry2010ConvolutionRingSymmetric",
        title="The Convolution Ring of Arithmetic Functions and Symmetric Polynomials",
        authors="Trueman MacHenry, Kieh Wong",
        year=2010,
        venue="arXiv:1009.1892 — نسخة أولية؛ وللمؤلفين عمل محكَّم في Rocky "
              "Mountain J. Math. 42(4) 2012",
        url="https://arxiv.org/abs/1009.1892",
        reading_status=ReadingStatus.DISCOVERED,
        notes=(
            "لم يُقرأ بعد. تمثيل زمرة الدوال الضربية بتقييمات متعدّدات حدود Schur "
            "الخطّافية. الرِّجل الخامسة في GATE-PVFC-SD-001 كانت Elliott 2008؛ "
            "هذا خطّها الموازي. بند متابعة."
        ),
    ),
    dict(
        reference_key="Beurling1937GeneralizedPrimes",
        title="Beurling generalized prime systems (الميدان لا ورقةً بعينها)",
        authors="Arne Beurling وما تلاه",
        year=1937,
        venue="Acta Mathematica 68 — محكَّم؛ وأدبيات متّصلة إلى 2025",
        url="https://cage.ugent.be/~fabrouck/Talks/Introduction_Beurling_g_primes.pdf",
        reading_status=ReadingStatus.ABSTRACT_READ,
        notes=(
            "مُدخَل بوصفه ميدانًا لا ورقةً مفردة، فلا يُستشهد به استشهادًا نقطيًا "
            "قبل تثبيت الورقة المعيّنة. مقدّمةُ الميدان بعينها: أي متتالية "
            "1<p₁≤p₂≤… تُولّد «أعدادًا صحيحة معمَّمة» تحاكي سلوك الأوليات "
            "التحليلي. وهذا يعني أن «السلوك الشبيه بالأوليات ليس خاصًّا "
            "بالأوليات» مقدّمةُ ميدان قائم منذ 1937، لا اكتشافًا."
        ),
    ),
]

# ── ثلاث بوابات ────────────────────────────────────────────────────────

GATES = [
    dict(
        gate_key="GATE-PVG-FND-001",
        title="متجه الأُسُس والتفاف ديريشليه بوصفه التفافًا جمعيًا",
        research_question=(
            "هل تمثيل ℕ≥1 ≅ ⊕_p ℕ₀ بمتجه الأُسُس، وتحوّلُ التفاف ديريشليه "
            "تحته إلى التفاف جمعي على المخروط، موجودان في الأدبيات؟\n"
            "النطاق: حلقة الدوال الحسابية، متسلسلات القوى بعدد قابل للعدّ من "
            "المتغيرات، حلقة Witt/القلائد، الدوال المتناظرة الحسابية."
        ),
        status="CLOSED",
        verdict=GateVerdict.KNOWN,
        references=[
            ("CashwellEverett1959RingOfNTFunctions", GateRelation.COVERS,
             "البند 14 ص982 يبني التماثل نفسه حرفًا بحرف: متجه الأُسُس، ثم "
             "α↦Σα(n)∏x_i^{a_i}، وحفظُ الجمع، وP(α·β)=P(α)P(β). لا فجوة."),
            ("Elliott2008RingStructures", GateRelation.ADJACENT,
             "يمضي أبعد: بنية حلقية عبر متجهات Witt، الجمع فيها التفافُ "
             "ديريشليه. يؤكّد أن الميدان مطروق منذ عقود."),
            ("MacHenry2010ConvolutionRingSymmetric", GateRelation.ADJACENT,
             "خط موازٍ عبر متعدّدات Schur الخطّافية. لم يُقرأ بعد."),
        ],
    ),
    dict(
        gate_key="GATE-PVFC-JET-001",
        title="عدم التمييز بالنفاثة المحدودة وأعداد Beurling المعمَّمة",
        research_question=(
            "PVFC-09 تقول: عند s₀>1 ومستوى N ورتبة اشتقاق m، كلّها منتهية، "
            "توجد أبجدية منتهية غير أولية تقرّب عزوم الأوليات ومشتقاتها ضمن ε — "
            "فلا بصمة أولية محلية مستقرة ذات رتبة محدودة داخل s>1.\n"
            "هل هذا معروف؟ النطاق: أعداد Beurling المعمَّمة، شمولية Voronin، "
            "أمثلة مضادة في نصف مستوى التقارب المطلق."
        ),
        # لم تُقرأ ورقة بعينها، بل مقدّمة الميدان. فالحكم PARTIAL لا
        # EQUIVALENT، والبوابة تبقى مفتوحة حتى تُثبَّت الورقة.
        status="REVIEW-IN-PROGRESS",
        verdict=GateVerdict.PARTIAL,
        references=[
            ("Beurling1937GeneralizedPrimes", GateRelation.COVERS,
             "المبرهنة صحيحة، والميدان الذي تقع فيه قائم منذ 1937 ومقدّمتُه "
             "هي عينُ خلاصتها: السلوك التحليلي الشبيه بالأوليات لا يميّز "
             "الأوليات. بل إن حيلة «إضافة أوليّ مختار مرارًا منتهية للتحكّم "
             "في قيمة زيتا عند نقاط بعينها» تقنيةٌ قياسية هناك، وهي عينُ "
             "حجّة القطع والإزاحة في برهان PVFC-09. وصياغة PVFC-09 أضعف: "
             "نقطة واحدة s₀ ورتبة منتهية، لا سلوك عالمي."),
        ],
    ),
    dict(
        gate_key="GATE-ADD-GOLDBACH-001",
        title="غولدباخ بوصفه تقاطع الليف الجمعي مع المحل الأولي",
        research_question=(
            "ADD-05: G_N ∩ (P₁×P₁) ≠ ∅ حيث P₁={e_p}. هل لهذه الصياغة "
            "الهندسية سابقة، وهل تحمل مضمونًا زائدًا على العبارة الأصلية؟"
        ),
        # لا سابقة وُجدت للصياغة الهندسية بعينها؛ والجِدّة ليست على المحكّ
        # أصلًا لأن الأرشيف يعلنها إعادة صياغة. NOT-FOUND-YET ليست جِدّة.
        status="CLOSED",
        verdict=GateVerdict.NOT_FOUND_YET,
        references=[],
    ),
]

# ── الادعاءات ──────────────────────────────────────────────────────────

CLAIMS = [
    dict(
        claim_key="CLAIM-PVG-FND-01",
        statement=(
            "تمثيل الأعداد الصحيحة الموجبة بمتجه أُسُسها الأولية تماثلٌ "
            "ℕ≥1 ≅ ⊕_p ℕ₀ (PVG-FND-01)."
        ),
        status=ClaimStatus.KNOWN,
        evidence_note=(
            "CashwellEverett1959RingOfNTFunctions، البند 14 ص982، محكَّم: "
            "«every integer n may be written uniquely in the form "
            "n=p₁^{a₁}p₂^{a₂}⋯ and uniquely described by a vector (a₁,a₂,…)». "
            "راجع GATE-PVG-FND-001."
        ),
        novelty_note=(
            "لا جِدّة، ولم تُدَّع. هذه المبرهنة الأساسية في الحساب مصوغةً "
            "بلغة الشبكات، وعمر الصياغة بهذه العبارة 67 سنة على الأقل."
        ),
    ),
    dict(
        claim_key="CLAIM-PVG-FND-06",
        statement=(
            "تحت تمثيل متجه الأُسُس، يصير التفاف ديريشليه التفافًا جمعيًا على "
            "المخروط ⊕_p ℕ₀ (PVG-FND-06)."
        ),
        status=ClaimStatus.KNOWN,
        evidence_note=(
            "CashwellEverett1959RingOfNTFunctions، البند 14 ص982، محكَّم: "
            "«addition is preserved, and P(α·β)=P(α)P(β)» حيث P متسلسلة قوى في "
            "متغيّرات مفهرسة بالأوليات؛ وضربُ متسلسلات القوى هو التفافُ "
            "المعاملات الجمعي. راجع GATE-PVG-FND-001."
        ),
        novelty_note=(
            "لا جِدّة. وهذه أهمّ حصيلة المسح: النتيجة كانت غير مفحوصة، وقد "
            "تبيّن أنها منشورة محكَّمة منذ 1959. عدمُ العثور كان واقعةً عن "
            "مسحنا لا عن العالم."
        ),
    ),
    dict(
        claim_key="CLAIM-PVFC-09",
        statement=(
            "لا توجد بصمة أولية محلية مستقرة ذات رتبة محدودة داخل s>1: عند "
            "s₀ ومستوى N ورتبة m منتهية، تقرّب أبجدية منتهية غير أولية جميع "
            "المشتقات ضمن ε (PVFC-09)."
        ),
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "المبرهنة صحيحة ومبرهنة داخليًا (PVFC-09). ومضمونها يقع في ميدان "
            "أعداد Beurling المعمَّمة القائم منذ 1937، ومقدّمةُ ذلك الميدان هي "
            "عينُ خلاصتها. راجع GATE-PVFC-JET-001."
        ),
        novelty_note=(
            "ليست `KNOWN-IN-EQUIVALENT-FORM` بعد، وإن بدت كذلك: قرأتُ مقدّمة "
            "الميدان لا ورقةً بعينها تنصّ على العبارة. ورفعُها إلى «مكافئة "
            "لمعلوم» قبل قراءة مصدر محدَّد هو الخطأ الذي تمنعه هذه المنصة. "
            "بند المتابعة: تثبيت ورقة Beurling أو خلَف بعينها.\n"
            "وقيمة المبرهنة لا تنقص بذلك: سالبةٌ تحدّ مسار البحث بنفسها وتغلق "
            "تمييز الأوليات بعدد منتهٍ من العزوم. وما بقي مفتوحًا هو السلوك عند "
            "s→1⁺ والحدود الموحّدة في N، وهو خارجها."
        ),
    ),
    dict(
        claim_key="CLAIM-ADD-05",
        statement=(
            "غولدباخ الثنائي للعدد الزوجي N يكافئ G_N ∩ (P₁×P₁) ≠ ∅، حيث "
            "G_N ليفُ الجمع وP₁={e_p} المحلُّ الأولي (ADD-05)."
        ),
        status=ClaimStatus.PROVED_HERE,
        evidence_note=(
            "المكافأة تُفَكّ من التعريف مباشرةً: عضوُ G_N زوجٌ (ν(a),ν(N−a))، "
            "ووقوعه في P₁×P₁ يعني a وN−a أوليّان. الأرشيف نفسه يصرّح: «هذه "
            "إعادة صياغة تامة، لا برهان» (ADD-05). راجع GATE-ADD-GOLDBACH-001."
        ),
        novelty_note=(
            "لا جِدّة ولم تُدَّع، ولذلك ليست `KNOWN`: لم أجد في الأدبيات نصًّا "
            "على هذه الصياغة الهندسية بعينها، وعدمُ العثور ليس جِدّة كما أنه "
            "ليس معرفة. إعادات صياغة غولدباخ جنسٌ مزدحم — هندسية وتحليلية "
            "ومصفوفية — وأيٌّ منها لم يُثبت شيئًا، وهذا هو الدرس. قيمة الصياغة "
            "تنظيمية: تضع السؤال في الإطار الهندسي، ولا تنقل السقف قيد أنملة."
        ),
    ),
]

LINKS = [
    ("claim", "CLAIM-PVG-FND-01", "DEPENDS-ON", "pvg_result", "PVG-FND-01", None),
    ("claim", "CLAIM-PVG-FND-06", "DEPENDS-ON", "pvg_result", "PVG-FND-06", None),
    ("claim", "CLAIM-PVFC-09", "DEPENDS-ON", "pvg_result", "PVFC-09", None),
    ("claim", "CLAIM-ADD-05", "DEPENDS-ON", "pvg_result", "ADD-05", None),
    ("claim", "CLAIM-PVG-FND-01", "EXAMINED-BY", "gate", "GATE-PVG-FND-001", None),
    ("claim", "CLAIM-PVG-FND-06", "EXAMINED-BY", "gate", "GATE-PVG-FND-001", None),
    ("claim", "CLAIM-PVFC-09", "EXAMINED-BY", "gate", "GATE-PVFC-JET-001", None),
    ("claim", "CLAIM-ADD-05", "EXAMINED-BY", "gate", "GATE-ADD-GOLDBACH-001", None),
]

#: المراجع التي قُرئت في هذا المسح وحالتها الجديدة.
READ_NOW = {
    "Weising2025HigherOrderBell": (
        ReadingStatus.FULLY_READ,
        "قُرئ النصّ الكامل (v2، 2025-09-21). الحكم على بند المتابعة الأول في "
        "GATE-PVFC-SD-001: المتغيّرات صورية بحتة، ولا تخصيص عند الأوليات، ولا "
        "ذكر لسلاسل ديريشليه ولا زيتا ولا الدوال الضربية. التخصيص الوحيد "
        "ψ:Λ→ℚ[[p₁]] أحاديُّ المتغيّر. وتظهر مجاميع القواسم σ_{ℓ(μ)-1}(gcd(μ)) "
        "في مفكوك المجاميع القوّية (Prop. 2.15)، وهي مكوّن حسابي لا تخصيصًا "
        "عند الأوليات. ومبرهنة Hardy–Littlewood التوبيرية تُستعمل على معاملات "
        "التقييد لا على دوال حسابية. فالمساحة المتبقية لـCLAIM-0003 لم تسقط "
        "بهذه الورقة. ولا تزال نسخةً أولية بلا مرجع دورية."
    ),
    "Weising2024ArtinSymmetricFunctions": (
        ReadingStatus.ABSTRACT_READ,
        "الملخّص وصفحة arXiv فقط. نسخة أولية بلا مرجع دورية."
    ),
    "BretecheTenenbaum2020Remarks": (
        ReadingStatus.DISCOVERED,
        "لم يُقرأ. طرف Selberg–Delange ناضج وبلا بنية مؤثرات — وهذا حكم مسحٍ "
        "لا حكم قراءة، فيبقى بندَ متابعة."
    ),
    "Macdonald1995SymmetricFunctions": (
        ReadingStatus.DISCOVERED,
        "لم يُقرأ. البند الثاني في متابعة GATE-PVFC-SD-001: الفصل الخامس "
        "(تماثل Satake) قراءةً مباشرة لا نقلًا عن الآخرين. لا يزال مفتوحًا."
    ),
}


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

        for key, (status, note) in READ_NOW.items():
            row = session.scalars(
                select(ObservatoryReference).where(
                    ObservatoryReference.reference_key == key
                )
            ).one_or_none()
            if row is None:
                count("قراءة", "skipped")
                continue
            before = (row.reading_status, row.notes)
            row.reading_status, row.notes = status, note
            count("قراءة", "unchanged" if before == (status, note) else "updated")
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
                ).one_or_none()
                if ref is None:
                    count("ربط-مرجع", "skipped")
                    continue
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

        for from_type, from_key, relation, to_type, to_key, note in LINKS:
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
                        to_type=to_type, to_key=to_key, note=note,
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
