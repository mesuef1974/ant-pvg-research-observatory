"""اختبارات البحث الموحّد عبر الطبقات الثلاث."""

from pathlib import Path

import pytest
from ant_pvg_observatory.db import Base
from ant_pvg_observatory.encyclopedia import ingestion
from ant_pvg_observatory.encyclopedia.search import rebuild_fts, search_corpus
from ant_pvg_observatory.models import SourceLayer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


@pytest.fixture()
def corpus(tmp_path: Path) -> Session:
    root = tmp_path / "encyclopedia"
    (root / "manuscript").mkdir(parents=True)
    (root / "docs").mkdir()
    chapters = root / "volumes" / "volume-01" / "chapters"
    chapters.mkdir(parents=True)

    (root / "manuscript" / "main.tex").write_text(
        "\\input{volumes/volume-01/chapters/chapter-01-zeta}\n", encoding="utf-8"
    )
    (chapters / "chapter-01-zeta.tex").write_text(
        "\\chapter{دالة زيتا}\n"
        "\\section{المعادلة الوظيفية}\n"
        "تحقق دالة زيتا المعادلة الوظيفية على الأعداد الأولية.\n"
        "\\begin{theorem}[المعادلة الوظيفية]\n"
        "\\resultid{ANT-THM-01-01}\n\\provedhere\nعبارة.\n\\end{theorem}\n",
        encoding="utf-8",
    )
    (root / "docs" / "RESULTS_REGISTRY.md").write_text(
        "| المعرّف | النتيجة | الملف | الحالة | المصدر |\n|---|---|---|---|---|\n"
        "| `ANT-THM-01-01` | المعادلة الوظيفية | الفصل 1 | `PROVED-HERE` | برهان |\n",
        encoding="utf-8",
    )
    (root / "manuscript" / "bibliography.bib").write_text(
        "@book{Titchmarsh1986,\n  author = {E. C. Titchmarsh},\n"
        "  title  = {The Theory of the Riemann Zeta-Function},\n  year = {1986}\n}\n",
        encoding="utf-8",
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        ingestion.import_encyclopedia(session, repository_root=root)
        yield session


def test_arabic_search_matches_regardless_of_hamza_and_diacritics(
    corpus: Session,
) -> None:
    with_hamza = search_corpus(corpus, query="الأعداد الأولية")
    without_hamza = search_corpus(corpus, query="الاعداد الاوليه")

    assert with_hamza.total > 0
    # التطبيع نفسه يُطبَّق على الفهرس والاستعلام، فيتطابقان
    assert {r.key for r in with_hamza.results if r.kind == "unit"} == {
        r.key for r in without_hamza.results if r.kind == "unit"
    }


def test_results_carry_their_layer_and_citability(corpus: Session) -> None:
    response = search_corpus(corpus, query="المعادلة الوظيفية")

    assert response.total > 0
    assert all(isinstance(r.layer, SourceLayer) for r in response.results)
    result_rows = [r for r in response.results if r.kind == "result"]
    assert result_rows and result_rows[0].citable is True


def test_model_synthesis_hits_are_never_citable(corpus: Session) -> None:
    response = search_corpus(corpus, query="عائق التكافؤ")
    notes = [r for r in response.results if r.layer is SourceLayer.MODEL_SYNTHESIS]

    assert notes, "المتوقع أن تُطابق ملاحظات معيارية مشحونة"
    assert all(note.citable is False for note in notes)


def test_layer_filter_restricts_results(corpus: Session) -> None:
    response = search_corpus(
        corpus, query="زيتا", source_layer=SourceLayer.ENCYCLOPEDIA
    )
    assert response.total > 0
    assert all(r.layer is SourceLayer.ENCYCLOPEDIA for r in response.results)


def test_empty_query_returns_nothing_instead_of_everything(corpus: Session) -> None:
    assert search_corpus(corpus, query="!!!").total == 0


def test_rebuilding_the_index_is_repeatable(corpus: Session) -> None:
    before = search_corpus(corpus, query="زيتا").total
    rebuild_fts(corpus)
    rebuild_fts(corpus)
    assert search_corpus(corpus, query="زيتا").total == before
    assert corpus.execute(text("PRAGMA integrity_check")).scalar() == "ok"
