"""اختبارات سجل المراجع وربطها بالبوابات وشبكة الروابط."""

import pytest
from ant_pvg_observatory.db import Base, get_session
from ant_pvg_observatory.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _reference(client: TestClient, **overrides) -> str:
    payload = {
        "title": "ورقة اختبار",
        "authors": "مؤلف",
        "year": "2020",
        "reading_status": "DISCOVERED",
    } | overrides
    response = client.post("/api/references", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["reference_key"]


def _gate(client: TestClient) -> str:
    response = client.post(
        "/api/gates",
        json={"title": "بوابة اختبار", "research_question": "هل يوجد تمثيل موحد؟"},
    )
    assert response.status_code == 201, response.text
    return response.json()["gate_key"]


def test_reference_registry_tracks_reading_status(client: TestClient) -> None:
    key = _reference(client)
    assert client.get("/api/references").json()[0]["reading_status"] == "DISCOVERED"

    updated = client.patch(
        f"/api/references/{key}", json={"reading_status": "FULLY-READ"}
    )
    assert updated.status_code == 200
    assert updated.json()["reading_status"] == "FULLY-READ"

    filtered = client.get("/api/references?reading_status=FULLY-READ").json()
    assert [r["reference_key"] for r in filtered] == [key]


def test_linking_a_reference_to_a_gate_is_idempotent(client: TestClient) -> None:
    gate_key, reference_key = _gate(client), _reference(client)

    first = client.post(
        f"/api/gates/{gate_key}/references",
        json={"reference_key": reference_key, "relation": "PARTIAL"},
    )
    assert first.status_code == 201

    # إعادة الربط تُحدِّث العلاقة ولا تُنشئ صفًّا ثانيًا
    second = client.post(
        f"/api/gates/{gate_key}/references",
        json={
            "reference_key": reference_key,
            "relation": "COVERS",
            "coverage_note": "يغطي السؤال كاملًا",
        },
    )
    assert second.status_code == 201
    links = client.get(f"/api/gates/{gate_key}/references").json()
    assert len(links) == 1
    assert links[0]["relation"] == "COVERS"
    assert links[0]["coverage_note"] == "يغطي السؤال كاملًا"


def test_unlinking_removes_only_that_link(client: TestClient) -> None:
    gate_key = _gate(client)
    kept = _reference(client, title="مرجع باقٍ")
    removed = _reference(client, title="مرجع محذوف")
    for key in (kept, removed):
        client.post(
            f"/api/gates/{gate_key}/references",
            json={"reference_key": key, "relation": "ADJACENT"},
        )

    response = client.delete(f"/api/gates/{gate_key}/references/{removed}")
    assert response.status_code == 204
    remaining = client.get(f"/api/gates/{gate_key}/references").json()
    assert [link["reference_key"] for link in remaining] == [kept]
    # المرجع نفسه لم يُحذف من السجل
    assert len(client.get("/api/references").json()) == 2


def test_gate_cannot_close_as_known_without_any_covering_reference(
    client: TestClient,
) -> None:
    gate_key = _gate(client)
    response = client.patch(
        f"/api/gates/{gate_key}",
        json={"status": "CLOSED-COVERED", "verdict": "KNOWN"},
    )
    assert response.status_code == 422
    assert "COVERS" in response.json()["detail"]


def test_gate_cannot_close_as_known_on_an_unread_reference(
    client: TestClient,
) -> None:
    gate_key, reference_key = _gate(client), _reference(client)
    client.post(
        f"/api/gates/{gate_key}/references",
        json={"reference_key": reference_key, "relation": "COVERS"},
    )

    response = client.patch(
        f"/api/gates/{gate_key}",
        json={"status": "CLOSED-COVERED", "verdict": "KNOWN"},
    )
    assert response.status_code == 422
    assert "مقروء" in response.json()["detail"]


def test_gate_closes_as_known_once_a_covering_reference_is_read(
    client: TestClient,
) -> None:
    gate_key = _gate(client)
    reference_key = _reference(client, reading_status="VERIFIED")
    client.post(
        f"/api/gates/{gate_key}/references",
        json={"reference_key": reference_key, "relation": "COVERS"},
    )

    response = client.patch(
        f"/api/gates/{gate_key}",
        json={"status": "CLOSED-COVERED", "verdict": "KNOWN"},
    )
    assert response.status_code == 200
    assert response.json()["verdict"] == "KNOWN"


def test_not_found_yet_closes_without_a_covering_reference(
    client: TestClient,
) -> None:
    """عدم العثور واقعة عن مسحنا، فلا يستوجب مرجعًا يغطي — ولا يعني جِدّة."""
    gate_key = _gate(client)
    response = client.patch(
        f"/api/gates/{gate_key}",
        json={"status": "CLOSED-GAP", "verdict": "NOT-FOUND-YET"},
    )
    assert response.status_code == 200


def test_gate_cannot_close_without_an_explicit_verdict(client: TestClient) -> None:
    gate_key = _gate(client)
    response = client.patch(f"/api/gates/{gate_key}", json={"status": "CLOSED-COVERED"})
    assert response.status_code == 422
    assert "غير مُقيَّم" in response.json()["detail"]


def test_knowledge_links_connect_typed_keys_and_reject_duplicates(
    client: TestClient,
) -> None:
    payload = {
        "from_type": "claim",
        "from_key": "CLAIM-0001",
        "relation": "DEPENDS-ON",
        "to_type": "result",
        "to_key": "ANT-THM-06-01",
        "note": "يعتمد على الاستمرار التحليلي",
    }
    assert client.post("/api/links", json=payload).status_code == 201
    assert client.post("/api/links", json=payload).status_code == 409

    by_source = client.get("/api/links?from_key=CLAIM-0001").json()
    assert len(by_source) == 1
    assert by_source[0]["to_key"] == "ANT-THM-06-01"
    assert client.get("/api/links?from_key=CLAIM-9999").json() == []
