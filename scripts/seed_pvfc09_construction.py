"""يسجّل البناء الصريح لـPVFC-09 ومرجعًا محكَّمًا لميدان أعداد Beurling.

المرجع السابق كان مُدخَلًا بوصفه «ميدانًا لا ورقةً»، وهذا ضعيف. يُستبدل بورقة
محكَّمة بعينها في Acta Arithmetica، وتُضاف إليها **البرهنة البنائية**: بدل
مطاردة استشهادٍ للمبرهنة، أُنشئت الأبجدية التي تزعم وجودها.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ant_pvg_observatory.db import SessionLocal  # noqa: E402
from ant_pvg_observatory.models import (  # noqa: E402
    Claim,
    GateReference,
    GateRelation,
    LiteratureGate,
    ObservatoryReference,
    ReadingStatus,
)
from sqlalchemy import select  # noqa: E402

REF = dict(
    reference_key="DebruyneSchlagePuchtaVindas2016BeurlingExamples",
    title="Some examples in the theory of Beurling's generalized prime numbers",
    authors="Gregory Debruyne, Jan-Christoph Schlage-Puchta, Jasson Vindas",
    year=2016,
    venue="Acta Arithmetica 176، ص101–129 — **محكَّمة**",
    url="https://arxiv.org/abs/1505.04174",
    reading_status=ReadingStatus.ABSTRACT_READ,
    notes=(
        "الملخّص وبيانات النشر فقط. «Several examples of generalized number "
        "systems are constructed to compare various conditions occurring in "
        "the literature for the prime number theorem in the context of "
        "Beurling generalized primes».\n"
        "يُستبدل به المُدخَل السابق Beurling1937GeneralizedPrimes الذي كان "
        "«ميدانًا لا ورقةً» — وهذا ضعفٌ في التسجيل صُحّح. الورقة محكَّمة وحديثة "
        "وتُثبت أن الميدان حيّ، لكنها لا تنصّ على عبارة PVFC-09 بعينها، ولم "
        "تُقرأ. فلا تصلح إسنادًا لحالة موثقة."
    ),
)

EVIDENCE = (
    "المبرهنة صحيحة ومبرهنة داخليًا (PVFC-09)، و**بُنيت أبجدياتُها صراحةً**: "
    "قطعُ الذيل ثم إزاحةُ العناصر، وهما خطوتا برهان الأرشيف نفسه "
    "(scripts/verify_finite_jet_nondiscrimination.py). عند s₀=1.3 وN=6 وm=3:\n"
    "• ε=10⁻³ → أبجدية من 801 عنصرًا غير صحيح، خطأ 9.7×10⁻⁴.\n"
    "• ε=10⁻⁶ → أبجدية من 62946 عنصرًا غير صحيح، خطأ 8.6×10⁻⁷.\n"
    "• ε=10⁻⁹ → **منحطّ**: حدُّ القطع تجاوز قائمة الأوليات المستعملة، فصارت "
    "المقارنة مع القائمة نفسها. يُعلَن ولا يُحتسب.\n"
    "والميدان الذي تقع فيه حيٌّ ومحكَّم: "
    "DebruyneSchlagePuchtaVindas2016BeurlingExamples، Acta Arith. 176 (2016). "
    "راجع GATE-PVFC-JET-001."
)
NOVELTY = (
    "تبقى LITERATURE-UNCLEAR رغم البناء الصريح، وهذا مقصود: **البناء يُظهر أن "
    "المبرهنة صحيحة، ولا يقول شيئًا عن كونها معروفة**. وهما سؤالان مختلفان، "
    "وخلطُهما هو الخطأ الذي بُنيت هذه المنصة لمنعه.\n"
    "ولم أجد ورقةً تنصّ على العبارة بعينها. ومقدّمةُ ميدان Beurling (1937) هي "
    "عينُ خلاصتها — أن السلوك الشبيه بالأوليات ليس خاصًّا بالأوليات — لكن "
    "المقدّمة ليست استشهادًا.\n"
    "وقيمة المبرهنة لا تنقص: سالبةٌ تحدّ مسار البحث بنفسها، وتغلق تمييز "
    "الأوليات بعدد منتهٍ من العزوم في نقطة داخلية. وما بقي مفتوحًا — السلوك "
    "عند s→1⁺ والحدود الموحّدة في N — خارجها تمامًا."
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    with SessionLocal() as session:
        key = REF["reference_key"]
        fields = {k: v for k, v in REF.items() if k != "reference_key"}
        row = session.scalars(
            select(ObservatoryReference).where(
                ObservatoryReference.reference_key == key
            )
        ).one_or_none()
        if row is None:
            session.add(ObservatoryReference(reference_key=key, **fields))
            print("  مرجع أُضيف")
        else:
            for name, value in fields.items():
                setattr(row, name, value)
            print("  مرجع حُدِّث")
        session.flush()

        gate = session.scalars(
            select(LiteratureGate).where(
                LiteratureGate.gate_key == "GATE-PVFC-JET-001"
            )
        ).one()
        ref = session.scalars(
            select(ObservatoryReference).where(
                ObservatoryReference.reference_key == key
            )
        ).one()
        coverage = (
            "ورقة محكَّمة بعينها في ميدان Beurling، تحلّ محلّ المُدخَل السابق "
            "الذي كان «ميدانًا لا ورقةً». لم تُقرأ، ولا تنصّ على PVFC-09 "
            "بعينها، فعلاقتها مجاورة لا مغطّية."
        )
        link = session.get(GateReference, (gate.id, ref.id))
        if link is None:
            session.add(
                GateReference(
                    gate_id=gate.id, reference_id=ref.id,
                    relation=GateRelation.ADJACENT, coverage_note=coverage,
                )
            )
            print("  ربط بوابة أُضيف")
        else:
            link.relation, link.coverage_note = GateRelation.ADJACENT, coverage
            print("  ربط بوابة حُدِّث")

        claim = session.scalars(
            select(Claim).where(Claim.claim_key == "CLAIM-PVFC-09")
        ).one()
        claim.evidence_note, claim.novelty_note = EVIDENCE, NOVELTY
        print(f"  CLAIM-PVFC-09 حُدِّث، والحالة تبقى {claim.status.value}")

        session.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
