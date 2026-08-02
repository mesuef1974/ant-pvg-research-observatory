from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from ant_pvg_observatory.db import Base
from ant_pvg_observatory.models import SourceFile, SourceSection
from ant_pvg_observatory.source_corpus import import_encyclopedia_source


def test_import_encyclopedia_source_follows_main_input_order(tmp_path: Path) -> None:
    root = tmp_path / "encyclopedia"
    (root / "manuscript").mkdir(parents=True)
    chapters = root / "volumes" / "volume-01" / "chapters"
    chapters.mkdir(parents=True)

    (root / "manuscript" / "main.tex").write_text(
        "\\input{manuscript/preamble}\n"
        "\\input{volumes/volume-01/chapters/chapter-01}\n"
        "\\input{volumes/volume-01/chapters/chapter-02}\n",
        encoding="utf-8",
    )
    (chapters / "chapter-01.tex").write_text(
        "\\chapter{الفصل الأول}\nمقدمة\n\\section{تعريف}\nنص التعريف\n",
        encoding="utf-8",
    )
    (chapters / "chapter-02.tex").write_text(
        "\\chapter{الفصل الثاني}\n\\section{نتيجة}\nنص النتيجة\n",
        encoding="utf-8",
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        summary = import_encyclopedia_source(session, repository_root=root)
        files = list(session.scalars(select(SourceFile).order_by(SourceFile.order_index)))
        section_count = session.scalar(select(func.count(SourceSection.id)))

        assert summary.file_count == 2
        assert summary.section_count == 4
        assert [source.path for source in files] == [
            "volumes/volume-01/chapters/chapter-01.tex",
            "volumes/volume-01/chapters/chapter-02.tex",
        ]
        assert files[0].sections[0].title == "الفصل الأول"
        assert files[0].sections[1].start_line == 3
        assert section_count == 4


def test_reimport_replaces_previous_source_snapshot(tmp_path: Path) -> None:
    root = tmp_path / "encyclopedia"
    (root / "manuscript").mkdir(parents=True)
    chapters = root / "volumes" / "v" / "chapters"
    chapters.mkdir(parents=True)
    main = root / "manuscript" / "main.tex"
    chapter = chapters / "chapter.tex"
    main.write_text("\\input{volumes/v/chapters/chapter}\n", encoding="utf-8")
    chapter.write_text("\\chapter{قديم}\nنص\n", encoding="utf-8")

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        import_encyclopedia_source(session, repository_root=root)
        chapter.write_text("\\chapter{جديد}\nنص محدث\n", encoding="utf-8")
        import_encyclopedia_source(session, repository_root=root)

        assert session.scalar(select(func.count(SourceFile.id))) == 1
        assert session.scalar(select(func.count(SourceSection.id))) == 1
        section = session.scalar(select(SourceSection))
        assert section is not None
        assert section.title == "جديد"
