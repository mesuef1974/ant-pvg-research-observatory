"""كنسة ألياف الجمع ADD-01 … ADD-04، وتسجيل ما بقي بلا فحص.

هذه النتائج تختلف عن سابقاتها اختلافًا مهمًّا: مؤثراتها من بناء الأرشيف نفسه
(``D_{N,r}``، ``J_{N;r}``)، فلا سابقة لها في الأدبيات تُطلب. السؤال ليس «هل
هذا معروف» بل «هل هذا صحيح» — وهذا يُفحص لا يُبحَث عنه.

ولذلك حالتها ``PROVED-HERE``: مبرهنة هنا، مفحوصة هنا، ولا جِدّة تُدَّعى لها.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ant_pvg_observatory.db import SessionLocal  # noqa: E402
from ant_pvg_observatory.models import (  # noqa: E402
    Claim,
    ClaimStatus,
    GateVerdict,
    KnowledgeLink,
    LiteratureGate,
    SourceLayer,
)
from sqlalchemy import select  # noqa: E402

GATES = [
    dict(
        gate_key="GATE-ADD-FIBER-001",
        title="ألياف الجمع: الحفظ، والالتفاف، ورتب قنوات الفرق",
        research_question=(
            "أربع نتائج على ليف الجمع G_N = {(ν(a), ν(N−a))}:\n"
            "ADD-01: التقييم على الليف تقابلٌ فلا تُفقد معلومة.\n"
            "ADD-02: هوية التفاف الليف.\n"
            "ADD-03: rank D_{N,r} = min(N−1, r/gcd(2,r)).\n"
            "ADD-04: rank J_{N;r} = min(N−1, L/gcd(2,L))، L=lcm(r_i).\n"
            "المؤثرات من بناء الأرشيف، فالسؤال عن الصحة لا عن السابقة."
        ),
        status="CLOSED",
        verdict=GateVerdict.NOT_FOUND_YET,
    ),
]

CLAIMS = [
    dict(
        claim_key="CLAIM-ADD-01",
        statement=(
            "ι_N : {(a,b) : a+b=N} → G_N، (a,b) ↦ (ν(a),ν(b))، تقابلٌ واحد "
            "لواحد؛ فتمثيل ليف الجمع في PVG ليس ضغطًا للمعلومة (ADD-01)."
        ),
        status=ClaimStatus.PROVED_HERE,
        evidence_note=(
            "تتبع مباشرةً من حقن خريطة التقييم، وهي CLAIM-PVG-FND-01 المسنَدة "
            "إلى CashwellEverett1959RingOfNTFunctions. راجع GATE-ADD-FIBER-001."
        ),
        novelty_note=(
            "لا جِدّة: نتيجةٌ في سطر من تقابلٍ عمره 67 سنة. وقيمتها **سلبية "
            "نافعة**: تمنع وهمًا محتملًا بأن الانتقال إلى إحداثيات PVG يضغط "
            "المسألة الجمعية أو يبسّطها. لا يفعل — يعيد ترميزها."
        ),
    ),
    dict(
        claim_key="CLAIM-ADD-02",
        statement=(
            "هوية التفاف الليف: (f *₊ g)(N) = ∫_{G_N} f̂(x)ĝ(y) dμ_N(x,y) "
            "حيث μ_N = Σ_a δ_{(ν(a),ν(N−a))} (ADD-02)."
        ),
        status=ClaimStatus.PROVED_HERE,
        evidence_note=(
            "‏μ_N مُعرَّفة مجموعَ كتل ديراك على نقاط الليف، فالتكامل عليها هو "
            "المجموع نفسه. الأرشيف يصرّح: «هذه ترجمة دقيقة، وليست تقديرًا "
            "تقاربيًا». راجع GATE-ADD-FIBER-001."
        ),
        novelty_note=(
            "لا جِدّة ولم تُدَّع. تغييرُ ترميز لا مبرهنة، والأرشيف يقولها. "
            "وقيمتها تنظيمية: تكتب المجموع الجمعي بلغة القياس على الليف، فتفتح "
            "الباب لأدوات تحليلية — ولم تُدخل بعدُ أيَّ أداة."
        ),
    ),
    dict(
        claim_key="CLAIM-ADD-03",
        statement=(
            "rank D_{N,r} = min(N−1, r/gcd(2,r))، ومنه D_{N,r} حقني ⟺ "
            "r/gcd(2,r) ≥ N−1 (ADD-03)."
        ),
        status=ClaimStatus.PROVED_HERE,
        evidence_note=(
            "العمودان a وb يتطابقان ⟺ 2(a−b) ≡ 0 (mod r)، فعدد الأعمدة "
            "المتمايزة هو min(N−1, r/gcd(2,r)). **فُحص: 437 حالة من 437** "
            "(N من 3 إلى 25، r من 1 إلى 19، رتبة عددية) — "
            "scripts/verify_addition_fiber_ranks.py. راجع GATE-ADD-FIBER-001."
        ),
        novelty_note=(
            "المؤثر D_{N,r} من بناء الأرشيف، فلا سابقة تُطلب ولا جِدّة تُدَّعى: "
            "NOT-FOUND-YET هنا خاليةٌ من المعنى. المطلوب الصحةُ وحدها، وقد "
            "فُحصت."
        ),
    ),
    dict(
        claim_key="CLAIM-ADD-04",
        statement=(
            "للمعايير r₁,…,r_s وL=lcm(rᵢ): rank J_{N;r} = min(N−1, "
            "L/gcd(2,L))؛ ولا يُساوى المؤثر المشترك J بالمكدَّس M لأن الهوامش "
            "قد تفقد اقتران المعلومات (ADD-04)."
        ),
        status=ClaimStatus.PROVED_HERE,
        evidence_note=(
            "**فُحص: 119 حالة من 119** (N من 3 إلى 19، سبع مجموعات معايير "
            "منها (3,5) و(6,10) و(3,4,5)) — "
            "scripts/verify_addition_fiber_ranks.py. راجع GATE-ADD-FIBER-001."
        ),
        novelty_note=(
            "لا جِدّة تُدَّعى. والتمييز بين J المشترك وM المكدَّس هو المضمون "
            "الحقيقي هنا، وهو تحذيرٌ منهجي صحيح: الهوامش ليست الاقتران."
        ),
    ),
]

LINKS = [
    ("claim", "CLAIM-ADD-01", "DEPENDS-ON", "pvg_result", "ADD-01"),
    ("claim", "CLAIM-ADD-02", "DEPENDS-ON", "pvg_result", "ADD-02"),
    ("claim", "CLAIM-ADD-03", "DEPENDS-ON", "pvg_result", "ADD-03"),
    ("claim", "CLAIM-ADD-04", "DEPENDS-ON", "pvg_result", "ADD-04"),
    ("claim", "CLAIM-ADD-01", "EXAMINED-BY", "gate", "GATE-ADD-FIBER-001"),
    ("claim", "CLAIM-ADD-02", "EXAMINED-BY", "gate", "GATE-ADD-FIBER-001"),
    ("claim", "CLAIM-ADD-03", "EXAMINED-BY", "gate", "GATE-ADD-FIBER-001"),
    ("claim", "CLAIM-ADD-04", "EXAMINED-BY", "gate", "GATE-ADD-FIBER-001"),
    ("claim", "CLAIM-ADD-01", "SUPPORTS", "claim", "CLAIM-ADD-05"),
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
        for spec in GATES:
            key = spec.pop("gate_key")
            count("بوابة", _sync(session, LiteratureGate, "gate_key", key, spec))
        session.flush()

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
