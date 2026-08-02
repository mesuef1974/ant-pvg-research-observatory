"""إنفاذ قاعدة الاعتماد الخارجي على الادعاءات.

القاعدة معلنة في ``docs/RESULT_STATUS_POLICY.md`` بمستودع الموسوعة: لا يجوز
لمشروع آخر الاستشهاد بنتيجة إلا إذا ظهرت في سجل النتائج بحالة تسمح بذلك.

هنا تصير القاعدة قيدًا منفَّذًا لا نصًّا يُرجى الالتزام به. القاعدة غير
المنفَّذة قاعدة غير موجودة: الواجهة التي تعرض ``KNOWN`` خيارًا متاحًا ستُنتج
ادعاءات بهذه الحالة، مهما قالت الوثائق.
"""

from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    ClaimStatus,
    EncyclopediaResult,
    GateReference,
    GateRelation,
    GateVerdict,
    LiteratureGate,
    ModelSynthesisNote,
    PvgResult,
    ReadingStatus,
    SourceLayer,
)

_RESULT_KEY = re.compile(r"ANT-[A-Z]+-\d+-\d+")
_NOTE_KEY = re.compile(r"MS-[A-Z]+-\d+")
_PVG_KEY = re.compile(r"\b(?:PVG-[A-Z]+-\d+|PVFC-\d+|ADD-\d+)\b")

#: حالات الادعاء التي تعني أن المعلومة موثقة، فتستوجب إسنادًا.
ANCHORED_STATUSES = frozenset({ClaimStatus.KNOWN, ClaimStatus.KNOWN_EQUIVALENT})

#: حالات تزعم أن العبارة مبرهنة، سواء في الأدبيات أو هنا.
PROOF_ASSERTING_STATUSES = ANCHORED_STATUSES | {ClaimStatus.PROVED_HERE}


def _fail(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
    )


def referenced_result_keys(*texts: str | None) -> set[str]:
    return set(_RESULT_KEY.findall(" ".join(t or "" for t in texts)))


def referenced_note_keys(*texts: str | None) -> set[str]:
    return set(_NOTE_KEY.findall(" ".join(t or "" for t in texts)))


def enforce_citation_policy(
    session: Session,
    *,
    statement: str,
    claim_status: ClaimStatus,
    source_layer: SourceLayer,
    evidence_note: str | None = None,
    novelty_note: str | None = None,
) -> None:
    """يرفض الادعاء المخالف بـ 422 قبل أن يُكتب في القاعدة.

    ثلاث قواعد مستقلة:

    1. كل معرّف ``ANT-*`` مذكور يجب أن يكون مسجَّلًا وحالته تسمح بالاستشهاد.
    2. طبقة ``MODEL_SYNTHESIS`` لا يُستشهد بها بحال، فذكر ملاحظة منها إسنادًا
       مرفوض حتى لو كانت الملاحظة موجودة.
    3. لا تُرفع حالة الادعاء إلى ``KNOWN`` بلا إسناد أصلًا.
    """
    blob = f"{statement}\n{evidence_note or ''}\n{novelty_note or ''}"

    result_keys = referenced_result_keys(blob)
    for key in sorted(result_keys):
        row = session.scalars(
            select(EncyclopediaResult).where(EncyclopediaResult.result_key == key)
        ).one_or_none()
        if row is None:
            _fail(
                f"المعرّف {key} غير موجود في سجل نتائج الموسوعة. "
                "شغّل الاستيراد أو صحّح المعرّف."
            )
        if not row.citable:
            _fail(
                f"المعرّف {key} حالته {row.registry_status or 'غير محددة'} "
                "ولا تسمح سياسة اعتماد النتائج بالاستشهاد به."
            )

    for key in sorted(referenced_note_keys(blob)):
        exists = session.scalars(
            select(ModelSynthesisNote).where(ModelSynthesisNote.note_key == key)
        ).one_or_none()
        if exists is not None:
            _fail(
                f"الملاحظة {key} من طبقة MODEL_SYNTHESIS، وسلطتها "
                "UNVERIFIED_UNTIL_SOURCED فلا يجوز الاستناد إليها. "
                "استبدلها بنتيجة معتمدة من الموسوعة أو بمرجع خارجي موثق."
            )

    pvg_keys = sorted(set(_PVG_KEY.findall(blob)))
    for key in pvg_keys:
        row = session.scalars(
            select(PvgResult).where(PvgResult.result_key == key)
        ).one_or_none()
        if row is None:
            _fail(
                f"المعرّف {key} غير موجود في سجل نتائج PVG. "
                "شغّل استيراد المدونة أو صحّح المعرّف."
            )
        # الحالة غير المبرهنة تُذكر بحرية؛ المرفوض أن يُبنى عليها ادعاءُ برهان.
        if not row.is_proven and claim_status in PROOF_ASSERTING_STATUSES:
            _fail(
                f"النتيجة {key} حالتها «{row.status}» وليست برهانًا — "
                "والأرشيف نفسه يقول لا يحل الفحص محل البرهان. "
                "أنزل حالة الادعاء إلى FINITE_VERIFIED أو OPEN."
            )

    if claim_status in ANCHORED_STATUSES and not result_keys:
        # KNOWN تعني «معروف في الأدبيات». وطبقة PVG غير منشورة، فمهما بلغت
        # قوة نتيجتها لا تجعل العبارة معروفةً عند أحد سوانا.
        if pvg_keys:
            _fail(
                f"الإسناد الوحيد هنا نتيجةُ PVG ({'، '.join(pvg_keys)})، وهي "
                "طبقة داخلية غير منشورة فلا تُثبت أن العبارة معروفة في "
                "الأدبيات. استعمل PROVED_HERE، أو أضف مرجعًا منشورًا."
            )
        _fail(
            "لا يجوز رفع ادعاء إلى حالة موثقة دون إسناد إلى نتيجة معتمدة في "
            "الموسوعة أو إلى مرجع خارجي موثق."
        )

    if source_layer is SourceLayer.MODEL_SYNTHESIS and claim_status in ANCHORED_STATUSES:
        _fail(
            "لا تنتقل معلومة من طبقة MODEL_SYNTHESIS إلى حالة موثقة إلا بتغيير "
            "طبقتها إلى مصدر موثق أولًا."
        )


#: أحكام تعني أن المسألة موجودة في الأدبيات، فتستوجب مرجعًا مقروءًا يغطيها.
COVERAGE_VERDICTS = frozenset({GateVerdict.KNOWN, GateVerdict.EQUIVALENT})

#: حالات القراءة التي تكفي لإسناد حكم بوابة. الاكتشاف وقراءة المستخلص لا تكفيان.
READ_ENOUGH = frozenset({ReadingStatus.FULLY_READ, ReadingStatus.VERIFIED})

_CLOSED_PREFIX = "CLOSED"


def enforce_gate_closure(
    session: Session,
    *,
    gate: LiteratureGate,
    status: str,
    verdict: GateVerdict | None,
) -> None:
    """يمنع إغلاق بوابة بحكم لا تسنده مراجع مقروءة.

    البوابة عملية مراجعة لا رأي. وحكم ``KNOWN`` أو ``EQUIVALENT`` يقول إن
    المسألة موجودة في الأدبيات، فيلزمه مرجع واحد على الأقل مربوط بعلاقة
    ``COVERS`` وحالة قراءته ``FULLY-READ`` أو ``VERIFIED``.

    والحكم ``NOT-FOUND-YET`` لا يستوجب ذلك بطبيعته — لكنه أيضًا **ليس جِدّة**:
    هو واقعة عن مسحنا لا عن العالم.
    """
    if not status.upper().startswith(_CLOSED_PREFIX):
        return

    if verdict in (None, GateVerdict.NOT_ASSESSED):
        _fail(
            "لا تُغلق البوابة بحكم غير مُقيَّم. سجّل حكمًا صريحًا: "
            "KNOWN أو EQUIVALENT أو PARTIAL أو NOT-FOUND-YET."
        )

    if verdict not in COVERAGE_VERDICTS:
        return

    supporting = session.scalars(
        select(GateReference).where(
            GateReference.gate_id == gate.id,
            GateReference.relation == GateRelation.COVERS,
        )
    ).all()
    if not supporting:
        _fail(
            f"الحكم {verdict.value} يقول إن المسألة موجودة في الأدبيات، "
            "ولا يوجد مرجع مربوط بالبوابة بعلاقة COVERS."
        )
    if not any(link.reference.reading_status in READ_ENOUGH for link in supporting):
        _fail(
            f"الحكم {verdict.value} يستوجب مرجعًا مقروءًا. المراجع المربوطة "
            "بعلاقة COVERS حالتها DISCOVERED أو ABSTRACT-READ، والاطلاع على "
            "المستخلص لا يكفي لإسناد حكم."
        )
