"""اختبارات تصدير الطبقة البحثية واستيرادها.

الغرض المحمي هنا واحد: ألّا يوجد عمل بحثي في قاعدة بيانات غير متتبَّعة وحدها.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ant_pvg_observatory.db import Base
from ant_pvg_observatory.models import (
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
from ant_pvg_observatory.research_io import (
    FORMAT_VERSION,
    export_research_layer,
    import_research_layer,
    read_import,
    write_export,
)
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session


def _engine():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _populate(session: Session) -> None:
    gate = LiteratureGate(
        gate_key="GATE-0001",
        title="بوابة اختبار",
        research_question="هل يوجد تمثيل موحد؟",
        status="REVIEW-IN-PROGRESS",
        verdict="PARTIAL",
    )
    reference = ObservatoryReference(
        reference_key="REF-0001",
        title="ورقة مرجعية",
        authors="مؤلف",
        year="2024",
        reading_status=ReadingStatus.FULLY_READ,
        notes="ملاحظة قراءة",
    )
    session.add_all([gate, reference])
    session.flush()
    session.add_all(
        [
            GateReference(
                gate_id=gate.id,
                reference_id=reference.id,
                relation=GateRelation.COVERS,
                coverage_note="يغطي السؤال",
            ),
            Claim(
                claim_key="CLAIM-0001",
                statement="ادعاء استكشافي",
                source_layer=SourceLayer.MODEL_SYNTHESIS,
                status=ClaimStatus.CANDIDATE_GAP,
                evidence_note="دليل",
                novelty_note="NOT-FOUND-YET",
            ),
            KnowledgeLink(
                from_type="claim",
                from_key="CLAIM-0001",
                relation="DEPENDS-ON",
                to_type="result",
                to_key="ANT-THM-06-01",
                note="يعتمد على الاستمرار",
            ),
        ]
    )
    session.commit()


@pytest.fixture()
def populated() -> Session:
    with Session(_engine()) as session:
        _populate(session)
        yield session


def test_export_captures_every_hand_entered_layer(populated: Session) -> None:
    payload = export_research_layer(populated)

    assert payload["format_version"] == FORMAT_VERSION
    assert [c["claim_key"] for c in payload["claims"]] == ["CLAIM-0001"]
    assert [g["gate_key"] for g in payload["gates"]] == ["GATE-0001"]
    assert [r["reference_key"] for r in payload["references"]] == ["REF-0001"]
    assert payload["gate_references"][0] == {
        "gate_key": "GATE-0001",
        "reference_key": "REF-0001",
        "relation": "COVERS",
        "coverage_note": "يغطي السؤال",
    }
    assert payload["links"][0]["to_key"] == "ANT-THM-06-01"


def test_gate_links_travel_by_key_not_by_row_id(populated: Session) -> None:
    """المعرفات الرقمية تتغير بإعادة البناء، فالربط بها يكسر الاسترجاع."""
    payload = export_research_layer(populated)
    serialized = json.dumps(payload, ensure_ascii=False)

    assert "gate_id" not in serialized
    assert "reference_id" not in serialized


def test_export_is_deterministic(populated: Session, tmp_path: Path) -> None:
    first = export_research_layer(populated)
    second = export_research_layer(populated)

    # الطابع الزمني وحده يتغير؛ ما عداه ثابت فتكون فروق Git ذات معنى
    first.pop("exported_at")
    second.pop("exported_at")
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )


def test_restore_into_an_empty_database(populated: Session, tmp_path: Path) -> None:
    path, counts = write_export(populated, tmp_path / "research-layer.json")
    assert counts.claims == 1 and counts.gate_references == 1

    with Session(_engine()) as fresh:
        report = read_import(fresh, path)

        assert report.created.claims == 1
        assert report.created.gates == 1
        assert report.created.references == 1
        assert report.created.gate_references == 1
        assert report.created.links == 1
        assert report.skipped_links == 0

        gate = fresh.scalars(select(LiteratureGate)).one()
        assert gate.gate_key == "GATE-0001"
        assert gate.verdict == "PARTIAL"
        link = fresh.scalars(select(GateReference)).one()
        assert link.relation is GateRelation.COVERS
        reference = fresh.scalars(select(ObservatoryReference)).one()
        assert reference.reading_status is ReadingStatus.FULLY_READ


def test_import_is_idempotent_and_never_duplicates(populated: Session) -> None:
    payload = export_research_layer(populated)

    first = import_research_layer(populated, payload)
    second = import_research_layer(populated, payload)

    assert first.created.claims == 0 and first.updated.claims == 1
    assert second.updated.claims == 1
    for model in (Claim, LiteratureGate, ObservatoryReference, GateReference, KnowledgeLink):
        assert populated.scalar(select(func.count()).select_from(model)) == 1


def test_import_updates_changed_fields(populated: Session) -> None:
    payload = export_research_layer(populated)
    payload["references"][0]["reading_status"] = "VERIFIED"
    payload["gates"][0]["verdict"] = "NOT-FOUND-YET"

    import_research_layer(populated, payload)

    assert (
        populated.scalars(select(ObservatoryReference)).one().reading_status
        is ReadingStatus.VERIFIED
    )
    assert populated.scalars(select(LiteratureGate)).one().verdict == "NOT-FOUND-YET"


def test_import_never_deletes_what_the_file_omits(populated: Session) -> None:
    """الاستيراد استرجاع ودمج لا مزامنة تدميرية."""
    payload = export_research_layer(populated)
    payload["claims"] = []

    import_research_layer(populated, payload)

    assert populated.scalar(select(func.count()).select_from(Claim)) == 1


def test_dangling_gate_link_is_skipped_not_fatal(populated: Session) -> None:
    payload = export_research_layer(populated)
    payload["gate_references"].append(
        {
            "gate_key": "GATE-MISSING",
            "reference_key": "REF-0001",
            "relation": "COVERS",
            "coverage_note": None,
        }
    )

    report = import_research_layer(populated, payload)

    assert report.skipped_links == 1
    assert populated.scalar(select(func.count()).select_from(GateReference)) == 1


def test_unknown_format_version_is_refused(populated: Session) -> None:
    payload = export_research_layer(populated)
    payload["format_version"] = FORMAT_VERSION + 1

    with pytest.raises(ValueError, match="صيغة ملف غير مدعومة"):
        import_research_layer(populated, payload)
