from pathlib import Path

import pytest
from ant_pvg_observatory.config import settings
from ant_pvg_observatory.db import Base
from ant_pvg_observatory.indexing import index_document_pages
from ant_pvg_observatory.library import import_local_pdf
from ant_pvg_observatory.models import (
    Document,
    DocumentPage,
    ExtractionStatus,
    SourceLayer,
)
from ant_pvg_observatory.schemas import LocalDocumentImport
from fastapi import HTTPException
from pypdf import PdfWriter
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session


def _write_blank_pdf(path: Path, pages: int) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as stream:
        writer.write(stream)


def test_page_indexing_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    pdf_path = library_root / "blank.pdf"
    _write_blank_pdf(pdf_path, pages=2)
    monkeypatch.setattr(settings, "library_root", library_root)

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        document = import_local_pdf(
            session,
            LocalDocumentImport(
                relative_path=Path("blank.pdf"),
                source_layer=SourceLayer.ENCYCLOPEDIA,
                title="Blank test document",
            ),
        )

        first = index_document_pages(session, document.id)
        second = index_document_pages(session, document.id)
        stored_count = session.scalar(select(func.count(DocumentPage.id)))

        assert len(first) == 2
        assert len(second) == 2
        assert stored_count == 2
        assert [page.page_number for page in second] == [1, 2]
        assert all(page.extraction_status is ExtractionStatus.EMPTY for page in second)
        assert all(page.text == "" for page in second)
        assert document.page_count == 2


def test_legacy_document_without_path_cannot_be_indexed() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        document = Document(
            title="Legacy document",
            source_layer=SourceLayer.ENCYCLOPEDIA,
            local_path=None,
            sha256=None,
            media_type="application/pdf",
            page_count=0,
            file_size_bytes=0,
            import_status="LEGACY",
        )
        session.add(document)
        session.commit()

        with pytest.raises(HTTPException) as error:
            index_document_pages(session, document.id)

        assert error.value.status_code == 409
