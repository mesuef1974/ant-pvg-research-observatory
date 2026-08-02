"""اختبارات شبكة الروابط: حلّ الأطراف، والجوار، والاشتقاق، والفحوص."""

from __future__ import annotations

import pytest
from ant_pvg_observatory import graph
from ant_pvg_observatory.db import Base
from ant_pvg_observatory.models import (
    Claim,
    ClaimStatus,
    EncyclopediaResult,
    KnowledgeLink,
    ModelSynthesisNote,
    SourceLayer,
)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                EncyclopediaResult(
                    result_key="ANT-THM-06-01",
                    kind="theorem",
                    title="استمرار زيتا",
                    chapter_number=6,
                    registry_status="PROVED-HERE",
                    citable=True,
                ),
                EncyclopediaResult(
                    result_key="ANT-LEM-01-01",
                    kind="lemma",
                    title="مساعدة مؤجلة",
                    chapter_number=1,
                    registry_status="DEFERRED",
                    citable=False,
                ),
                ModelSynthesisNote(
                    note_key="MS-ARF-004",
                    title="دوال القسمة وأبعادها",
                    kind="context",
                    body="نص",
                    search_text="نص",
                    blocks_json="[]",
                    source_file="01.md",
                ),
                Claim(
                    claim_key="CLAIM-0001",
                    statement="ادعاء يذكر ANT-THM-06-01 في نصه",
                    source_layer=SourceLayer.MODEL_SYNTHESIS,
                    status=ClaimStatus.CANDIDATE_GAP,
                    evidence_note="ويذكر ANT-LEM-01-01 في دليله",
                ),
            ]
        )
        session.commit()
        yield session


def test_type_is_inferred_from_the_key_shape() -> None:
    assert graph.infer_type("ANT-THM-06-01") == "result"
    assert graph.infer_type("MS-ARF-004") == "model_note"
    assert graph.infer_type("CLAIM-0001") == "claim"
    assert graph.infer_type("GATE-0001") == "gate"
    assert graph.infer_type("REF-0001") == "reference"
    assert graph.infer_type("شيء آخر") is None


def test_resolving_carries_status_and_citability(session: Session) -> None:
    citable = graph.resolve_node(session, "result", "ANT-THM-06-01")
    assert citable.exists and citable.citable is True
    assert citable.status == "PROVED-HERE"

    deferred = graph.resolve_node(session, "result", "ANT-LEM-01-01")
    assert deferred.exists and deferred.citable is False

    note = graph.resolve_node(session, "model_note", "MS-ARF-004")
    # الطبقة المعيارية تُعلن غير قابلة صراحةً لا بالسكوت
    assert note.exists and note.citable is False


def test_missing_endpoint_resolves_as_absent_not_invented(session: Session) -> None:
    missing = graph.resolve_node(session, "result", "ANT-THM-99-99")
    assert missing.exists is False
    assert missing.label is None

    unknown_type = graph.resolve_node(session, "planet", "MARS")
    assert unknown_type.exists is False


def test_neighbourhood_separates_incoming_from_outgoing(session: Session) -> None:
    session.add_all(
        [
            KnowledgeLink(
                from_type="claim", from_key="CLAIM-0001", relation="DEPENDS-ON",
                to_type="result", to_key="ANT-THM-06-01",
            ),
            KnowledgeLink(
                from_type="gate", from_key="GATE-0001", relation="RELATES-TO",
                to_type="claim", to_key="CLAIM-0001",
            ),
        ]
    )
    session.commit()

    hood = graph.neighbourhood(session, "CLAIM-0001")

    assert hood.node.node_type == "claim"
    assert [e["key"] for e in hood.outgoing] == ["ANT-THM-06-01"]
    assert [e["key"] for e in hood.incoming] == ["GATE-0001"]
    assert hood.outgoing[0]["citable"] is True
    # طرف البوابة غير موجود في هذه القاعدة، فيُعلن معلَّقًا
    assert hood.incoming[0]["exists"] is False


def test_derivation_is_explicit_and_idempotent(session: Session) -> None:
    first = graph.derive_links_from_claims(session)
    second = graph.derive_links_from_claims(session)

    assert sorted(link.to_key for link in first) == [
        "ANT-LEM-01-01",
        "ANT-THM-06-01",
    ]
    assert second == []
    assert session.scalars(select(KnowledgeLink)).all().__len__() == 2


def test_checks_flag_dangling_endpoints(session: Session) -> None:
    session.add(
        KnowledgeLink(
            from_type="claim", from_key="CLAIM-0001", relation="RELATES-TO",
            to_type="result", to_key="ANT-THM-99-99",
        )
    )
    session.commit()

    findings: list[tuple[str, str]] = []
    graph.check_links(session, lambda c, s, subj, d: findings.append((c, s)))

    assert ("LINK_ENDPOINT_MISSING", "MEDIUM") in findings


def test_checks_flag_leaning_on_a_noncitable_node(session: Session) -> None:
    session.add(
        KnowledgeLink(
            from_type="claim", from_key="CLAIM-0001", relation="DEPENDS-ON",
            to_type="model_note", to_key="MS-ARF-004",
        )
    )
    session.commit()

    findings: list[tuple[str, str]] = []
    graph.check_links(session, lambda c, s, subj, d: findings.append((c, s)))

    assert ("LINK_TO_NONCITABLE", "HIGH") in findings


def test_a_mere_mention_is_not_an_act_of_leaning(session: Session) -> None:
    """RELATES-TO إلى طبقة غير قابلة للاستشهاد ليس مخالفة: الإشارة ليست استنادًا."""
    session.add(
        KnowledgeLink(
            from_type="claim", from_key="CLAIM-0001", relation="RELATES-TO",
            to_type="model_note", to_key="MS-ARF-004",
        )
    )
    session.commit()

    findings: list[str] = []
    graph.check_links(session, lambda c, s, subj, d: findings.append(c))

    assert "LINK_TO_NONCITABLE" not in findings


def test_gate_record_path_requires_containment(tmp_path) -> None:
    """المفتاح يأتي من الطلب، فلا يُركَّب في مسار بلا فحص احتواء."""
    gates = tmp_path / graph.GATE_RECORD_DIR
    gates.mkdir(parents=True)
    (gates / "GATE-0001.md").write_text("# سجل", encoding="utf-8")
    (tmp_path / "secret.md").write_text("سرّي", encoding="utf-8")

    assert graph.gate_record_path(tmp_path, "GATE-0001") is not None
    assert graph.gate_record_path(tmp_path, "GATE-MISSING") is None
    assert graph.gate_record_path(tmp_path, "../secret") is None
    assert graph.gate_record_path(tmp_path, r"..\secret") is None
