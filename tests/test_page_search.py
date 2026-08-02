from ant_pvg_observatory.db import Base
from ant_pvg_observatory.models import (
    Document,
    DocumentPage,
    ExtractionStatus,
    SourceLayer,
)
from ant_pvg_observatory.search import search_pages
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def _add_document(
    session: Session,
    *,
    title: str,
    source_layer: SourceLayer,
    pages: list[str],
) -> Document:
    document = Document(
        title=title,
        source_layer=source_layer,
        local_path=f"{title}.pdf",
        sha256=(title.encode("utf-8").hex() + "0" * 64)[:64],
        media_type="application/pdf",
        page_count=len(pages),
        file_size_bytes=1,
        import_status="IMPORTED",
    )
    session.add(document)
    session.flush()

    for page_number, text in enumerate(pages, start=1):
        session.add(
            DocumentPage(
                document_id=document.id,
                page_number=page_number,
                text=text,
                char_count=len(text),
                word_count=len(text.split()),
                text_sha256=(str(page_number) * 64)[:64],
                extraction_status=ExtractionStatus.EXTRACTED,
                extraction_error=None,
            )
        )
    session.commit()
    return document


def test_search_pages_supports_arabic_filters_and_pagination() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        encyclopedia = _add_document(
            session,
            title="encyclopedia",
            source_layer=SourceLayer.ENCYCLOPEDIA,
            pages=[
                "مقدمة في نظرية الأعداد التحليلية",
                "تعرف دالة فون مانغولد ويرمز لها بالرمز Λ",
                "تظهر دالة فون مانغولد في الصيغة الصريحة",
            ],
        )
        _add_document(
            session,
            title="paper",
            source_layer=SourceLayer.LITERATURE,
            pages=["A paper mentioning دالة فون مانغولد once."],
        )

        all_results = search_pages(session, query="فون مانغولد", limit=2)
        assert all_results.total == 3
        assert len(all_results.results) == 2
        assert all_results.results[0].document_id == encyclopedia.id
        assert "فون مانغولد" in all_results.results[0].snippet

        second_page = search_pages(
            session,
            query="فون مانغولد",
            limit=2,
            offset=2,
        )
        assert second_page.total == 3
        assert len(second_page.results) == 1
        assert second_page.results[0].source_layer is SourceLayer.LITERATURE

        filtered = search_pages(
            session,
            query="فون مانغولد",
            document_id=encyclopedia.id,
            source_layer=SourceLayer.ENCYCLOPEDIA,
        )
        assert filtered.total == 2
        assert [result.page_number for result in filtered.results] == [2, 3]


def test_search_pages_is_case_insensitive_for_latin_text() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _add_document(
            session,
            title="latin",
            source_layer=SourceLayer.LITERATURE,
            pages=["Prime Zeta Function and Euler products"],
        )

        response = search_pages(session, query="prime zeta")
        assert response.total == 1
        assert response.results[0].page_number == 1
