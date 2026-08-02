"""طبقة PVG: قراءة المدونة، وتصنيف البرهان، وحوكمة الاستناد إليها.

المدونة الحقيقية اليوم نتائجها كلها من عائلة ``PROVED``، فقاعدة «ما ليس
برهانًا لا يُبنى عليه» خاملة عليها. والقاعدة الخاملة لا تُترك بلا اختبار،
وإلا انكسرت صامتةً أول ما تُضاف نتيجة ``FINITE-VERIFIED``. فتُختبر هنا
بمدونة اصطناعية تحمل الحالات التي يعلنها جدول التعريفات في الأرشيف.
"""

from pathlib import Path

import pytest
from ant_pvg_observatory import pvg
from ant_pvg_observatory.db import Base, get_session
from ant_pvg_observatory.governance import enforce_citation_policy
from ant_pvg_observatory.main import app
from ant_pvg_observatory.models import ClaimStatus, PvgResult, SourceLayer
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

CORPUS = """# مدونة اختبارية

| المعرّف | النتيجة | الحالة |
|---|---|---|
| `PVG-FND-01` | متطابقة أساسية | `PROVED` |
| `PVG-FND-02` | إعادة قراءة | `PROVED/REINTERPRETATION` |
| `PVFC-07` | فُحصت حاسوبيًا حتى حدٍّ منتهٍ | `FINITE-VERIFIED` |
| `PVFC-08` | قراءة هندسية | `INTERPRETATION` |
| `ADD-03` | اشتقاق رمزي مشروط بإطار | `FORMALLY-DERIVED` |

ويُذكر هنا `PVG-CALC-99` بلا سطر في السجل.
"""


@pytest.fixture()
def corpus_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "pvg"
    directory.mkdir()
    (directory / "01_RESULTS.md").write_text(CORPUS, encoding="utf-8")
    return directory


# ── تصنيف الحالة ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("status", "proven"),
    [
        ("PROVED", True),
        ("IDENTITY", True),
        ("EXACT REFORMULATION", True),
        ("PROVED/CLASSICAL", True),
        # INTERPRETATION سلسلة فرعية من REINTERPRETATION، والمطابقة النصية
        # كانت تصنّف هذه غيرَ مبرهنة وهي مبرهنة.
        ("PROVED/REINTERPRETATION", True),
        ("FINITE-VERIFIED", False),
        ("INTERPRETATION", False),
        ("FORMALLY-DERIVED", False),
        ("HYPOTHESIS", False),
        ("OPEN", False),
        ("REJECTED", False),
        # حالة مركّبة يتنازعها وسمان: غلبة النفي هي الجانب الآمن.
        ("PROVED/HYPOTHESIS", False),
        (None, False),
        ("", False),
    ],
)
def test_status_classification(status: str | None, proven: bool) -> None:
    assert pvg.is_proven(status) is proven


def test_corpus_parses_keys_statuses_and_mentions(corpus_dir: Path) -> None:
    corpus = pvg.parse_corpus(corpus_dir)

    results = {r["result_key"]: r["status"] for r in corpus["results"]}
    assert results == {
        "PVG-FND-01": "PROVED",
        "PVG-FND-02": "PROVED/REINTERPRETATION",
        "PVFC-07": "FINITE-VERIFIED",
        "PVFC-08": "INTERPRETATION",
        "ADD-03": "FORMALLY-DERIVED",
    }
    # المذكور بلا سطر في السجل يُلتقط، ليتمكّن الفحص من الإبلاغ عنه
    assert "PVG-CALC-99" in corpus["documents"][0]["mentioned_keys"]


def test_check_flags_unregistered_and_not_a_proof(corpus_dir: Path) -> None:
    findings: list[tuple] = []
    pvg.check_corpus(
        pvg.parse_corpus(corpus_dir), [],
        lambda code, severity, subject, message: findings.append(
            (code, severity, subject)
        ),
    )

    codes = {(code, subject) for code, _, subject in findings}
    assert ("PVG_RESULT_UNREGISTERED", "PVG-CALC-99") in codes
    assert ("PVG_RESULT_NOT_A_PROOF", "PVFC-07") in codes
    assert ("PVG_RESULT_NOT_A_PROOF", "PVG-FND-01") not in codes


def test_manifest_mismatch_is_reported(corpus_dir: Path) -> None:
    """الأرشيف يحمل بصمته بنفسه؛ بصمة كاذبة يجب أن تُكشف لا أن تُصدَّق."""
    (corpus_dir / "MANIFEST.json").write_text(
        '[{"file": "01_RESULTS.md", "sha256": "' + "0" * 64 + '"},'
        ' {"file": "غائب.md", "sha256": "' + "1" * 64 + '"}]',
        encoding="utf-8",
    )

    issues = {f["file"]: f["issue"] for f in pvg.verify_manifest(corpus_dir)}
    assert issues == {"01_RESULTS.md": "DIGEST-MISMATCH", "غائب.md": "MISSING"}


# ── الحوكمة ─────────────────────────────────────────────────────────────


@pytest.fixture()
def session(corpus_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Session:
    monkeypatch.setattr(pvg, "PVG_DIR", corpus_dir)
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        pvg.import_pvg_corpus(db)
        yield db


def _enforce(db: Session, note: str, claim_status: ClaimStatus) -> str | None:
    try:
        enforce_citation_policy(
            db,
            statement="ادعاء اختباري",
            claim_status=claim_status,
            source_layer=SourceLayer.PVG_RESEARCH,
            evidence_note=note,
        )
    except HTTPException as failure:
        return str(failure.detail)
    return None


def test_import_is_idempotent_and_records_proof_status(session: Session) -> None:
    first = pvg.import_pvg_corpus(session)
    second = pvg.import_pvg_corpus(session)
    assert first == second
    assert first["result_count"] == 5
    assert first["proven_count"] == 2

    rows = {r.result_key: r.is_proven for r in session.scalars(select(PvgResult))}
    assert rows == {
        "PVG-FND-01": True,
        "PVG-FND-02": True,
        "PVFC-07": False,
        "PVFC-08": False,
        "ADD-03": False,
    }


def test_unknown_pvg_key_is_rejected(session: Session) -> None:
    detail = _enforce(session, "يستند إلى PVFC-99", ClaimStatus.MODEL_SYNTHESIS)
    assert detail is not None and "PVFC-99" in detail


def test_a_finite_verification_cannot_carry_a_proof_claim(session: Session) -> None:
    """«لا يحل الفحص محل البرهان» — نصُّ الأرشيف، يُنفَّذ لا يُرجى."""
    detail = _enforce(session, "يستند إلى PVFC-07", ClaimStatus.PROVED_HERE)
    assert detail is not None and "FINITE-VERIFIED" in detail


def test_a_non_proof_may_still_be_cited_by_a_modest_claim(session: Session) -> None:
    """المنع على ادعاء البرهان لا على الذكر، وإلا تعطّلت الطبقة كلها."""
    assert _enforce(session, "يستند إلى PVFC-07", ClaimStatus.FINITE_VERIFIED) is None
    assert _enforce(session, "يستند إلى PVFC-08", ClaimStatus.OPEN) is None


def test_pvg_alone_cannot_make_a_claim_known(session: Session) -> None:
    """KNOWN تعني «معروف في الأدبيات»، وPVG طبقة داخلية غير منشورة."""
    detail = _enforce(session, "يستند إلى PVG-FND-01", ClaimStatus.KNOWN)
    assert detail is not None
    assert "PVG-FND-01" in detail and "غير منشورة" in detail


def test_a_proven_pvg_result_supports_proved_here(session: Session) -> None:
    assert _enforce(session, "يستند إلى PVG-FND-01", ClaimStatus.PROVED_HERE) is None


# ── الواجهة ─────────────────────────────────────────────────────────────


@pytest.fixture()
def client(session: Session) -> TestClient:
    factory = sessionmaker(
        bind=session.get_bind(), autoflush=False, expire_on_commit=False
    )

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_session] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_results_endpoint_filters_by_proof_status(client: TestClient) -> None:
    proven = client.get("/api/pvg/results", params={"is_proven": True})
    assert proven.status_code == 200
    assert {r["result_key"] for r in proven.json()} == {"PVG-FND-01", "PVG-FND-02"}

    unproven = client.get("/api/pvg/results", params={"is_proven": False})
    assert {r["result_key"] for r in unproven.json()} == {
        "PVFC-07",
        "PVFC-08",
        "ADD-03",
    }
