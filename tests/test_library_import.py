from pathlib import Path

from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ant_pvg_observatory.config import settings
from ant_pvg_observatory.db import Base
from ant_pvg_observatory.library import import_local_pdf
from ant_pvg_observatory.models import SourceLayer
from ant_pvg_observatory.schemas import LocalDocumentImport


def _write_pdf(path: Path, pages: int = 2) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as stream:
        writer.write(stream)


def test_import_local_pdf_and_deduplicate(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    pdf_path = library_root / "volume-01.pdf"
    _write_pdf(pdf_path)
    monkeypatch.setattr(settings, "library_root", library_root)

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    payload = LocalDocumentImport(
        relative_path=Path("volume-01.pdf"),
        source_layer=SourceLayer.ENCYCLOPEDIA,
        title="Analytic Number Theory Encyclopedia — Volume 1",
    )

    with Session(engine) as session:
        first = import_local_pdf(session, payload)
        second = import_local_pdf(session, payload)

        assert first.id == second.id
        assert first.page_count == 2
        assert first.file_size_bytes > 0
        assert first.local_path == "volume-01.pdf"
        assert first.source_layer is SourceLayer.ENCYCLOPEDIA
