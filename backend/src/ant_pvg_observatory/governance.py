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

from .models import ClaimStatus, EncyclopediaResult, ModelSynthesisNote, SourceLayer

_RESULT_KEY = re.compile(r"ANT-[A-Z]+-\d+-\d+")
_NOTE_KEY = re.compile(r"MS-[A-Z]+-\d+")

#: حالات الادعاء التي تعني أن المعلومة موثقة، فتستوجب إسنادًا.
ANCHORED_STATUSES = frozenset({ClaimStatus.KNOWN, ClaimStatus.KNOWN_EQUIVALENT})


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

    if claim_status in ANCHORED_STATUSES and not result_keys:
        _fail(
            "لا يجوز رفع ادعاء إلى حالة موثقة دون إسناد إلى نتيجة معتمدة في "
            "الموسوعة أو إلى مرجع خارجي موثق."
        )

    if source_layer is SourceLayer.MODEL_SYNTHESIS and claim_status in ANCHORED_STATUSES:
        _fail(
            "لا تنتقل معلومة من طبقة MODEL_SYNTHESIS إلى حالة موثقة إلا بتغيير "
            "طبقتها إلى مصدر موثق أولًا."
        )
