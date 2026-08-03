"""يرفع PVG-FM-01/02 بعد العثور على مصدر مقروء لبنية DPR1، ويسجّل ثغرة كشفها.

مصفوفة الوجوه ``F = vvᵀ − diag(a²)`` مصفوفةُ **قطرية زائد رتبة واحدة**، ومعادلةُ
الأرشيف الطيفية هي معادلتها السرّية القياسية. والمصدر يكشف شرطًا أغفله الأرشيف:
تمايزُ الأُسُس.
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

REF = dict(
    reference_key="JakovcevicStor2015DPR1Eigen",
    title="Forward stable eigenvalue decomposition of rank-one modifications of diagonal matrices",
    authors="N. Jakovčević Stor, I. Slapničar, J. L. Barlow",
    year=2015,
    venue="arXiv:1405.7537v2 — نسخة أولية؛ والمؤلفون لهم عمل محكَّم في Lin. Alg. Appl. 464 (2015)",
    url="https://arxiv.org/abs/1405.7537",
    reading_status=ReadingStatus.VERIFIED,
    notes=("قُرئت الصفحتان 1–2 في الملف الأصلي. المعادلة (1): A = D + ρ z zᵀ، وتُسمّى "
           "«diagonal-plus-rank-one» (DPR1). والمعادلة (3): «The eigenvalues of A are "
           "the zeros of the secular function … f(λ) = 1 + ρ Σ ζ_i²/(d_i − λ)».\n"
           "وتشترط الورقة صراحةً عدمَ قابلية الاختزال: «ζ_i ≠ 0 … and d_i ≠ d_j, for "
           "all i ≠ j».\n"
           "نسخة أولية، فلا تُرقَّى إلى محكَّمة؛ وهي تُسند المعادلة السرّية إلى مراجع "
           "قياسية (Golub–Van Loan، البند 8.5.3)."),
)

EVIDENCE = (
    "مصفوفة الوجوه F = vvᵀ − diag(a_i²) هي مصفوفة **DPR1**: بوضع D = −diag(a²) "
    "وρ=1 وz=a في المعادلة (1) من JakovcevicStor2015DPR1Eigen. ومعادلةُ الأرشيف "
    "الطيفية 1 = Σ a_i²/(λ+a_i²) هي عينُ المعادلة السرّية (3)، ومتجهُه الذاتي "
    "x_i ∝ a_i/(λ+a_i²) هو عينُ (D−λI)⁻¹z.\n"
    "فُحص: 1620 قيمة ذاتية من 1620 عند تمايز الأُسُس "
    "(scripts/verify_face_matrix_secular.py). والتوقيع والمحدد فُحصا سابقًا "
    "360/360 عبر التطابق F = D_a(J−I)D_a. راجع GATE-PVG-GEO-001."
)
NOVELTY = (
    "لا جِدّة: البنية DPR1 وأدبياتُها قائمة منذ Golub 1973 وBunch–Nielsen–Sorensen "
    "1978، والمعادلة السرّية معياريةٌ فيها. وكانت هذه LITERATURE-UNCLEAR حتى وُجد "
    "المصدر وقُرئ.\n"
    "**والأهمّ ثغرة كشفها المصدر**: الأرشيف يعطي المعادلة الطيفية بلا شرط، وأدبيات "
    "DPR1 تشترط d_i ≠ d_j — أي **تمايز الأُسُس**. فعند تكرار أُسّ بتضاعف m يصير "
    "−a² قيمةً ذاتية بتضاعف m−1، وهي قطبٌ للمعادلة السرّية لا جذر، فلا تحكمها. "
    "فُحص: 291/291. وهذا لا يمسّ التوقيع ولا المحدد، وكلاهما يصحّ مع التكرار."
)

def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    with SessionLocal() as s:
        key = REF.pop("reference_key")
        row = s.scalars(select(ObservatoryReference).where(
            ObservatoryReference.reference_key == key)).one_or_none()
        if row is None:
            s.add(ObservatoryReference(reference_key=key, **REF))
            print("  مرجع أُضيف")
        else:
            for n, v in REF.items():
                setattr(row, n, v)
            print("  مرجع حُدِّث")
        s.flush()
        gate = s.scalars(select(LiteratureGate).where(
            LiteratureGate.gate_key == "GATE-PVG-GEO-001")).one()
        ref = s.scalars(select(ObservatoryReference).where(
            ObservatoryReference.reference_key == key)).one()
        cov = ("يُسند بنية DPR1 والمعادلة السرّية، فيرفع FM-01/02. ويكشف شرط تمايز "
               "الأُسُس الذي أغفله الأرشيف.")
        link = s.get(GateReference, (gate.id, ref.id))
        if link is None:
            s.add(GateReference(gate_id=gate.id, reference_id=ref.id,
                                relation=GateRelation.COVERS, coverage_note=cov))
            print("  ربط بوابة أُضيف")
        else:
            link.relation, link.coverage_note = GateRelation.COVERS, cov
            print("  ربط بوابة حُدِّث")

        c = s.scalars(select(Claim).where(Claim.claim_key == "CLAIM-PVG-FM-01")).one()
        before = c.status.value
        c.status, c.evidence_note, c.novelty_note = (
            ClaimStatus.KNOWN_EQUIVALENT, EVIDENCE, NOVELTY)
        print(f"  CLAIM-PVG-FM-01  {before} -> {c.status.value}")

        # ملاحظة تمايز الأُسُس تُسجَّل في نصّ الادعاء وسجلّ البوابة، لا في
        # IntegrityFinding: ذلك الجدول يُعاد توليده عند كل استيراد فتُمحى.
        s.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
