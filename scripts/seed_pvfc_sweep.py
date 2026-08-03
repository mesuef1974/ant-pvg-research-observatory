"""كنسة PVFC، الجولة الأولى: النواة الجبرية PVFC-01 … PVFC-05.

هذه الطبقة المميِّزة، وقد كُنست ببطء ونتيجةً نتيجة لا دفعةً واحدة.

والأرشيف نفسه يعلن في رأس الفصل ``NOVELTY NOT ESTABLISHED``، ويفصل في بنده
العاشر ما هو ``CLASSICAL`` عمّا هو ``PVFC-SPECIFIC ORGANIZATION``. فالمسح هنا
يؤكّد تصنيفه ويزيده دقّة: يسمّي الواقعة الكلاسيكية بعينها لكل نتيجة.

PVFC-06 و07 و08 وألياف الجمع ADD-01…04 خارج هذه الجولة، ولم تُفحص.
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
        reference_key="Savage2021SymmetricFunctionsNotes",
        title="Symmetric Functions (ملاحظات محاضرات)",
        authors="Alistair Savage",
        year=2021,
        venue="جامعة أوتاوا — ملاحظات محاضرات، **غير محكَّمة**",
        url="https://alistairsavage.ca/symfunc/notes/Savage-SymmetricFunctions.pdf",
        # VERIFIED: قُرئت الفقرات المستشهَد بها في الملف الأصلي حرفًا بحرف.
        reading_status=ReadingStatus.VERIFIED,
        notes=(
            "قُرئ البند 2.1 (ص20–22) في الملف الأصلي. المعادلة (2.3) تعرّف "
            "الدالة الأحادية المتناظرة m_λ := Σ_{α∈λ𝔖_n} x^α، والملاحظة 2.1.1 "
            "تشدّد على عدّ الحدود مرّةً واحدة. والقضية 2.1.2 مع النتيجة 2.1.3 "
            "تثبتان أن {m_λ} أساسٌ على ℤ لحلقة الدوال المتناظرة.\n"
            "**غير محكَّمة** — ملاحظات تدريس. تصلح إسنادًا لواقعة مقرَّرة مثل "
            "هذه، ولا تصلح لادعاء دقيق. والمرجع المعياري Macdonald أو Doubilet "
            "لا يزال بندَ متابعة."
        ),
    ),
    dict(
        reference_key="Doubilet1972SymmetricFunctionsOccupancy",
        title=(
            "On the Foundations of Combinatorial Theory VII: Symmetric Functions "
            "through the Theory of Distribution and Occupancy"
        ),
        authors="Peter Doubilet",
        year=1972,
        venue="Studies in Applied Mathematics 51، ص377–395 — محكَّم",
        reading_status=ReadingStatus.DISCOVERED,
        notes=(
            "لم يُقرأ (محجوب). المرجع المعياري لمصفوفات الانتقال بين أُسُس "
            "الدوال المتناظرة عبر دالة موبيوس لشبكة التقسيمات — وهو الموضع "
            "الطبيعي لصيغة PVFC-01. بند متابعة أولوي."
        ),
    ),
    dict(
        reference_key="Stanley1988DifferentialPosets",
        title="Differential posets",
        authors="Richard P. Stanley",
        year=1988,
        venue="Journal of the American Mathematical Society 1(4) — محكَّم",
        reading_status=ReadingStatus.DISCOVERED,
        notes=(
            "لم يُقرأ. شبكة يونغ مجموعةٌ جزئية الترتيب تفاضلية، ومؤثّرا الصعود "
            "والهبوط U وD متضايفان مع DU−UD=I. هذا الموضع الطبيعي لـPVFC-03 "
            "(L=U*، K=U*U≥0) ولـPVFC-04. والأرشيف نفسه يدرج «differential "
            "posets وشبكة يونغ» في برنامجه المفتوح (الفصل 17). بند متابعة."
        ),
    ),
]

CLAIMS = [
    dict(
        claim_key="CLAIM-PVFC-01",
        statement=(
            "‏D_λ(s) = Σ_{n∈F_λ} n^{-s} تُعطى باحتواء–استبعاد على تقسيمات "
            "مواضع الأجزاء بدلالة P(ks) (PVFC-01)."
        ),
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "‏D_λ هي **الدالة الأحادية المتناظرة** m_λ مقيَّمةً عند x_p=p^{-s}. "
            "فُحص: 27 حالة من 27، تسعةُ تقسيمات وثلاث قيم لـs "
            "(scripts/verify_pvfc_symmetric.py). و{m_λ} أساسٌ كلاسيكي على ℤ — "
            "Savage2021SymmetricFunctionsNotes، البند 2.1 المعادلة (2.3) "
            "والنتيجة 2.1.3 (قُرئت). وصيغةُ الاحتواء–الاستبعاد نفسها هي انتقالُ "
            "الأساس الأحادي إلى مجاميع القوى عبر موبيوس شبكة التقسيمات."
        ),
        novelty_note=(
            "لا جِدّة في الجبر، والأرشيف يعلنها: رأسُ الفصل "
            "«NOVELTY NOT ESTABLISHED»، وبندُه العاشر يصنّف «تحويل القواعد بين "
            "الدوال الأحادية ومجاميع القوى» CLASSICAL صراحةً.\n"
            "الإضافةُ هنا **تسمية دقيقة**: ليست الصيغة شبيهةً بانتقال الأساس، "
            "بل هي هو، بتخصيص x_p=p^{-s}. وما يبقى خاصًّا بالمشروع هو الربط: "
            "أن لكل رأس λ ليفًا من الأعداد ودالةَ عدّ π_λ(x)."
        ),
    ),
    dict(
        claim_key="CLAIM-PVFC-02",
        statement=(
            "قانون الانتقال: P(rs)D_λ = (m_r+1)D_{sort(λ,r)} + "
            "Σ_j (m_{j+r}+1) D_{R_{j→j+r}λ} (PVFC-02)."
        ),
        status=ClaimStatus.KNOWN_EQUIVALENT,
        evidence_note=(
            "هذا بعينه مفكوكُ الجداء p_r·m_λ في الأساس الأحادي، مخصَّصًا عند "
            "x_p=p^{-s}: حدُّ الولادة هو إضافة جزء جديد، وحدود الرفع هي زيادة "
            "جزء قائم. فُحص: 48 حالة من 48، ثمانيةُ تقسيمات وثلاث قيم لـr "
            "وقيمتان لـs (scripts/verify_pvfc_symmetric.py). "
            "راجع Savage2021SymmetricFunctionsNotes وGATE-PVFC-SD-001."
        ),
        novelty_note=(
            "لا جِدّة في القاعدة. ومعاملاتها — كما يقول الأرشيف — «ناتجة من "
            "مضاعفات الأجزاء المتساوية، وليست معاملات تجريبية»، وهو وصفٌ صحيح "
            "لمعاملات مفكوك كلاسيكي. المرجع المعياري "
            "Doubilet1972SymmetricFunctionsOccupancy، ولم يُقرأ بعد."
        ),
    ),
    dict(
        claim_key="CLAIM-PVFC-04",
        statement=(
            "مؤثرات الأنماط الصورية تحقق [D,B]=I و[L,R]=y₁∂_{y₁}، "
            "و[B,B]=[T,T]=0 و[T_r,B_a]=B_{a+r} (PVFC-04)."
        ),
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "‏B=y₁ وD=∂_{y₁} يولّدان جبر هايزنبرغ، و[D,B]=I علاقتُه المعرِّفة. "
            "والأرشيف يصرّح في بنده الثامن: «هذه مؤثرات تقسيمات كلاسيكية في "
            "جوهرها؛ محتوى PVFC هو تخصصها إلى الألياف وسلاسل ديريشليه». "
            "راجع Stanley1988DifferentialPosets وGATE-PVFC-SD-001."
        ),
        novelty_note=(
            "لا جِدّة ولم تُدَّع — تصريحُ الأرشيف نفسه، ومؤثرات الصعود والهبوط "
            "مصنَّفة CLASSICAL في بنده العاشر.\n"
            "ومع ذلك **ليست KNOWN**: تصريحُ المؤلف عن عمله تقديرُه هو، لا "
            "شهادةُ أدبيات. والمرجع المسمَّى (Stanley 1988) لم يُقرأ. وحين "
            "رُفعت هذه إلى KNOWN-IN-EQUIVALENT-FORM رفضتها الحوكمة، فأُنزلت — "
            "لا لأن القاعدة قاسية بل لأنها محقّة. علاقةُ هايزنبرغ مقرَّرة، "
            "وقراءةُ مصدر لها عملُ دقائق، ولم يُنجَز بعد."
        ),
    ),
    dict(
        claim_key="CLAIM-PVFC-03",
        statement=(
            "تحت الجداء الداخلي الموزون w(λ)=∏_r m_r(λ)!: يكون L=U* ومن ثم "
            "K=U*U ≥ 0 (PVFC-03)."
        ),
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "النتيجة صحيحة. وتضايفُ مؤثّرَي الصعود والهبوط تحت الجداء الداخلي "
            "الطبيعي على التقسيمات هو **بنية المجموعات التفاضلية جزئية "
            "الترتيب** — شبكة يونغ نموذجُها، وDU−UD=I علامتُها. راجع "
            "Stanley1988DifferentialPosets وGATE-PVFC-SD-001."
        ),
        novelty_note=(
            "الترجيح أن التضايف كلاسيكي، والأرشيف يدرج «differential posets "
            "وشبكة يونغ» في برنامجه المفتوح فيعرف الوجهة. ولم أقرأ Stanley "
            "1988 فلا تُرفع. وما قد يبقى خاصًّا هو الوزن w(λ)=∏m_r! بعينه: "
            "هل هو جداء Hall الداخلي المألوف أم آخر؟ بند متابعة."
        ),
    ),
    dict(
        claim_key="CLAIM-PVFC-05",
        statement="وحدة birth–jet مغلقة (PVFC-05).",
        status=ClaimStatus.LITERATURE_UNCLEAR,
        evidence_note=(
            "النتيجة مبرهنة داخليًا. وانغلاقُ الوحدة تحت مؤثّرَي الولادة "
            "والرفع مسألةُ تمثيلٍ لجبر المؤثرات في CLAIM-PVFC-04، فوجهتُها "
            "نفسها. راجع GATE-PVFC-SD-001."
        ),
        novelty_note=(
            "لم يبلغها المسح بعمق. لا يُدَّعى لها جِدّة ولا تُنفى: بند متابعة "
            "صريح، ومحلُّه الطبيعي أدبيات تمثيلات جبر هايزنبرغ على فضاء فوك "
            "المتناظر."
        ),
    ),
]

LINKS = [
    ("claim", "CLAIM-PVFC-01", "DEPENDS-ON", "pvg_result", "PVFC-01"),
    ("claim", "CLAIM-PVFC-02", "DEPENDS-ON", "pvg_result", "PVFC-02"),
    ("claim", "CLAIM-PVFC-03", "DEPENDS-ON", "pvg_result", "PVFC-03"),
    ("claim", "CLAIM-PVFC-04", "DEPENDS-ON", "pvg_result", "PVFC-04"),
    ("claim", "CLAIM-PVFC-05", "DEPENDS-ON", "pvg_result", "PVFC-05"),
    ("claim", "CLAIM-PVFC-01", "EXAMINED-BY", "gate", "GATE-PVFC-SD-001"),
    ("claim", "CLAIM-PVFC-02", "EXAMINED-BY", "gate", "GATE-PVFC-SD-001"),
    ("claim", "CLAIM-PVFC-03", "EXAMINED-BY", "gate", "GATE-PVFC-SD-001"),
    ("claim", "CLAIM-PVFC-04", "EXAMINED-BY", "gate", "GATE-PVFC-SD-001"),
    ("claim", "CLAIM-PVFC-05", "EXAMINED-BY", "gate", "GATE-PVFC-SD-001"),
]

GATE_REFS = [
    ("GATE-PVFC-SD-001", "Savage2021SymmetricFunctionsNotes", GateRelation.PARTIAL,
     "يُسند كون {m_λ} أساسًا كلاسيكيًا، وهو ما يجعل D_λ تخصيصَ عنصرِ أساس لا "
     "كائنًا جديدًا. غير محكَّم، فلا يحمل أكثر من ذلك."),
    ("GATE-PVFC-SD-001", "Doubilet1972SymmetricFunctionsOccupancy", GateRelation.ADJACENT,
     "الموضع المعياري لصيغة PVFC-01 (انتقال الأساس عبر موبيوس شبكة "
     "التقسيمات). لم يُقرأ — بند متابعة أولوي."),
    ("GATE-PVFC-SD-001", "Stanley1988DifferentialPosets", GateRelation.ADJACENT,
     "الموضع الطبيعي لـPVFC-03 وPVFC-04. لم يُقرأ."),
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
