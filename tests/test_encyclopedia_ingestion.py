"""اختبارات تخزين الموسوعة: البنية والتكافؤ وتتبّع المصدر."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from ant_pvg_observatory.db import Base
from ant_pvg_observatory.encyclopedia import ingestion
from ant_pvg_observatory.models import (
    BibliographyEntry,
    EncyclopediaChapter,
    EncyclopediaResult,
    EncyclopediaUnit,
    IntegrityFinding,
    ModelSynthesisNote,
)


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def encyclopedia(tmp_path: Path) -> Path:
    root = tmp_path / "encyclopedia"
    (root / "manuscript").mkdir(parents=True)
    (root / "docs").mkdir()
    chapters = root / "volumes" / "volume-01" / "chapters"
    chapters.mkdir(parents=True)

    (root / "manuscript" / "main.tex").write_text(
        "\\input{manuscript/preamble}\n"
        "\\input{volumes/volume-01/chapters/chapter-01-alpha}\n"
        "\\input{volumes/volume-01/chapters/chapter-01-alpha-batch-02}\n",
        encoding="utf-8",
    )
    (chapters / "chapter-01-alpha.tex").write_text(
        "\\chapter{الأسس}\n"
        "\\section{مقدمة}\n"
        "نبدأ من \\(\\zeta(s)\\).\n"
        "\\[\n\\zeta(s)=\\sum_{n\\ge1}n^{-s}.\n\\]\n"
        "\\begin{theorem}[منتج أويلر]\n"
        "\\resultid{ANT-THM-01-01}\n\\provedhere\n"
        "عبارة المبرهنة \\cite{Titchmarsh1986}.\n"
        "\\end{theorem}\n"
        "\\begin{proof}\nبرهان.\n\\end{proof}\n",
        encoding="utf-8",
    )
    (chapters / "chapter-01-alpha-batch-02.tex").write_text(
        "\\section{تتمة}\n"
        "\\begin{lemma}\n\\resultid{ANT-LEM-01-01}\n\\deferredresult{لاحقًا}\n"
        "عبارة.\n\\end{lemma}\n",
        encoding="utf-8",
    )
    (root / "docs" / "RESULT_STATUS_POLICY.md").write_text(
        "| الحالة | المعنى |\n|---|---|\n"
        "| `PROVED-HERE` | برهان مكتمل |\n"
        "| `CITED` | منقولة |\n"
        "| `CONDITIONAL` | مشروطة |\n"
        "| `DEFERRED` | مؤجلة |\n"
        "| `DRAFT` | مسودة |\n",
        encoding="utf-8",
    )
    (root / "docs" / "RESULTS_REGISTRY.md").write_text(
        "| المعرّف | النتيجة | الملف | الحالة | المصدر |\n|---|---|---|---|---|\n"
        "| `ANT-THM-01-01` | منتج أويلر | الفصل 1 | `PROVED-HERE` | برهان داخلي |\n"
        "| `ANT-LEM-01-01` | مساعدة | الفصل 1 | `DEFERRED` | مؤجلة |\n",
        encoding="utf-8",
    )
    (root / "manuscript" / "bibliography.bib").write_text(
        "@book{Titchmarsh1986,\n"
        "  ids    = {titchmarshHeathBrown1986zeta},\n"
        "  author = {E. C. Titchmarsh},\n"
        "  title  = {The Theory of the Riemann Zeta-Function},\n"
        "  year   = {1986}\n}\n",
        encoding="utf-8",
    )
    return root


def test_import_records_structure_and_provenance(
    session: Session, encyclopedia: Path
) -> None:
    summary = ingestion.import_encyclopedia(session, repository_root=encyclopedia)

    assert summary.chapter_count == 1
    assert summary.result_count == 2
    assert summary.citable_count == 1  # المؤجلة لا تُعدّ قابلة للاستشهاد
    assert summary.bibliography_count == 1
    assert summary.revision  # مسجَّلة دائمًا، ولو تعذّر تحديدها
    assert summary.model_note_count >= 50

    chapter = session.scalars(select(EncyclopediaChapter)).one()
    assert chapter.number == 1
    assert chapter.title == "الأسس"
    # ملفا الدفعة اندمجا في فصل واحد
    assert len(json.loads(chapter.tex_paths)) == 2
    assert chapter.revision == summary.revision


def test_units_keep_structured_blocks_with_math_and_environments(
    session: Session, encyclopedia: Path
) -> None:
    ingestion.import_encyclopedia(session, repository_root=encyclopedia)

    unit = session.scalars(
        select(EncyclopediaUnit).where(EncyclopediaUnit.heading == "مقدمة")
    ).one()
    blocks = json.loads(unit.blocks_json)
    kinds = [block["t"] for block in blocks]

    assert "math" in kinds
    assert "env" in kinds
    theorem = next(b for b in blocks if b["t"] == "env" and b["env"] == "theorem")
    assert theorem["result_id"] == "ANT-THM-01-01"
    assert theorem["status"] == "PROVED-HERE"
    # نص البحث مطبَّع وخالٍ من رموز LaTeX
    assert "\\" not in unit.search_text


def test_result_citability_follows_the_registry(
    session: Session, encyclopedia: Path
) -> None:
    ingestion.import_encyclopedia(session, repository_root=encyclopedia)

    results = {
        row.result_key: row for row in session.scalars(select(EncyclopediaResult))
    }
    assert results["ANT-THM-01-01"].citable is True
    assert results["ANT-THM-01-01"].registry_status == "PROVED-HERE"
    assert results["ANT-LEM-01-01"].citable is False
    assert results["ANT-LEM-01-01"].tex_status == "DEFERRED"


def test_biber_alias_counts_as_cited(session: Session, encyclopedia: Path) -> None:
    ingestion.import_encyclopedia(session, repository_root=encyclopedia)

    entry = session.scalars(select(BibliographyEntry)).one()
    assert entry.entry_key == "Titchmarsh1986"
    assert entry.cited is True
    assert "titchmarshHeathBrown1986zeta" in (entry.aliases or "")

    missing = session.scalars(
        select(IntegrityFinding).where(IntegrityFinding.code == "CITE_KEY_MISSING")
    ).all()
    assert not missing


def test_model_notes_are_stored_and_never_citable(
    session: Session, encyclopedia: Path
) -> None:
    ingestion.import_encyclopedia(session, repository_root=encyclopedia)

    notes = list(session.scalars(select(ModelSynthesisNote)))
    assert len(notes) >= 50
    assert any(note.is_gap for note in notes)
    assert all(note.blocks_json for note in notes)
    # لا يوجد عمود قابلية استشهاد لهذه الطبقة أصلًا
    assert not hasattr(ModelSynthesisNote, "citable")


def test_import_is_idempotent(session: Session, encyclopedia: Path) -> None:
    first = ingestion.import_encyclopedia(session, repository_root=encyclopedia)
    second = ingestion.import_encyclopedia(session, repository_root=encyclopedia)

    assert (first.chapter_count, first.unit_count, first.result_count) == (
        second.chapter_count,
        second.unit_count,
        second.result_count,
    )
    for model in (
        EncyclopediaChapter,
        EncyclopediaUnit,
        EncyclopediaResult,
        BibliographyEntry,
    ):
        assert session.scalar(select(func.count()).select_from(model)) == {
            EncyclopediaChapter: 1,
            EncyclopediaUnit: second.unit_count,
            EncyclopediaResult: 2,
            BibliographyEntry: 1,
        }[model]


def test_integrity_findings_are_recorded(session: Session, encyclopedia: Path) -> None:
    summary = ingestion.import_encyclopedia(session, repository_root=encyclopedia)

    assert summary.finding_count > 0
    codes = {
        row.code for row in session.scalars(select(IntegrityFinding))
    }
    # الملاحظات المعيارية تُسنِد إلى معرّفات غير موجودة في هذه الموسوعة المصغَّرة
    assert "MODEL_NOTE_ANCHOR_UNKNOWN" in codes
