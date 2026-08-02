"""اختبارات إنفاذ قاعدة الاعتماد الخارجي على الادعاءات."""

from pathlib import Path

import pytest
from ant_pvg_observatory.db import Base, get_session
from ant_pvg_observatory.encyclopedia import ingestion
from ant_pvg_observatory.main import app
from ant_pvg_observatory.models import Claim
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    root = tmp_path / "encyclopedia"
    (root / "manuscript").mkdir(parents=True)
    (root / "docs").mkdir()
    chapters = root / "volumes" / "volume-01" / "chapters"
    chapters.mkdir(parents=True)
    (root / "manuscript" / "main.tex").write_text(
        "\\input{volumes/volume-01/chapters/chapter-01-zeta}\n", encoding="utf-8"
    )
    (chapters / "chapter-01-zeta.tex").write_text(
        "\\chapter{دالة زيتا}\n\\section{قسم}\n"
        "\\begin{theorem}\n\\resultid{ANT-THM-01-01}\n\\provedhere\nعبارة.\n"
        "\\end{theorem}\n"
        "\\begin{lemma}\n\\resultid{ANT-LEM-01-01}\n\\deferredresult{لاحقًا}\n"
        "عبارة.\n\\end{lemma}\n",
        encoding="utf-8",
    )
    (root / "docs" / "RESULTS_REGISTRY.md").write_text(
        "| المعرّف | النتيجة | الملف | الحالة | المصدر |\n|---|---|---|---|---|\n"
        "| `ANT-THM-01-01` | عبارة | الفصل 1 | `PROVED-HERE` | برهان |\n"
        "| `ANT-LEM-01-01` | عبارة | الفصل 1 | `DEFERRED` | مؤجلة |\n",
        encoding="utf-8",
    )

    # StaticPool ضروري: قاعدة الذاكرة تُنشأ لكل اتصال على حدة بدونه
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session(engine) as setup:
        ingestion.import_encyclopedia(setup, repository_root=root)

    def override():
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app) as test_client:
        test_client.engine = engine
        yield test_client
    app.dependency_overrides.clear()


def test_claim_anchored_to_a_citable_result_is_accepted(client: TestClient) -> None:
    response = client.post(
        "/api/claims",
        json={
            "statement": "ادعاء مسنَد",
            "status": "KNOWN",
            "source_layer": "ENCYCLOPEDIA",
            "evidence_note": "يستند إلى ANT-THM-01-01",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "KNOWN"


def test_claim_anchored_to_a_deferred_result_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/claims",
        json={
            "statement": "ادعاء مسنَد إلى مؤجلة",
            "status": "KNOWN",
            "source_layer": "ENCYCLOPEDIA",
            "evidence_note": "يستند إلى ANT-LEM-01-01",
        },
    )
    assert response.status_code == 422
    assert "DEFERRED" in response.json()["detail"]


def test_claim_with_unknown_result_key_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/claims",
        json={
            "statement": "ادعاء",
            "evidence_note": "يستند إلى ANT-THM-99-99",
        },
    )
    assert response.status_code == 422
    assert "ANT-THM-99-99" in response.json()["detail"]


def test_known_status_without_any_anchor_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/claims",
        json={
            "statement": "ادعاء بلا إسناد",
            "status": "KNOWN",
            "source_layer": "ENCYCLOPEDIA",
        },
    )
    assert response.status_code == 422


def test_model_synthesis_note_cannot_be_used_as_evidence(client: TestClient) -> None:
    notes = client.get("/api/model-synthesis/notes").json()
    assert notes
    response = client.post(
        "/api/claims",
        json={
            "statement": "ادعاء يستند إلى ملاحظة معيارية",
            "status": "MODEL-SYNTHESIS",
            "evidence_note": f"يستند إلى {notes[0]['note_key']}",
        },
    )
    assert response.status_code == 422
    assert "UNVERIFIED_UNTIL_SOURCED" in response.json()["detail"]


def test_model_synthesis_layer_cannot_hold_a_documented_status(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/claims",
        json={
            "statement": "ادعاء",
            "status": "KNOWN",
            "source_layer": "MODEL_SYNTHESIS",
            "evidence_note": "يستند إلى ANT-THM-01-01",
        },
    )
    assert response.status_code == 422


def test_patch_revalidates_the_resulting_state_not_only_the_change(
    client: TestClient,
) -> None:
    created = client.post(
        "/api/claims",
        json={"statement": "ادعاء استكشافي", "status": "MODEL-SYNTHESIS"},
    )
    assert created.status_code == 201
    key = created.json()["claim_key"]

    # الترقية وحدها مرفوضة: الحالة الناتجة بلا إسناد
    promoted = client.patch(f"/api/claims/{key}", json={"status": "KNOWN"})
    assert promoted.status_code == 422

    # الترقية مع إسناد صالح مقبولة
    anchored = client.patch(
        f"/api/claims/{key}",
        json={
            "status": "KNOWN",
            "source_layer": "ENCYCLOPEDIA",
            "evidence_note": "يستند إلى ANT-THM-01-01",
        },
    )
    assert anchored.status_code == 200
    assert anchored.json()["status"] == "KNOWN"


def test_rejected_claims_are_never_written(client: TestClient) -> None:
    client.post(
        "/api/claims",
        json={"statement": "مرفوض", "status": "KNOWN", "source_layer": "ENCYCLOPEDIA"},
    )
    with Session(client.engine) as session:
        assert not session.scalars(
            select(Claim).where(Claim.statement == "مرفوض")
        ).all()
