from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import HTTPException, status
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import Document
from .schemas import LocalDocumentImport


def _resolve_library_path(relative_path: Path) -> Path:
    root = settings.library_root.resolve()
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document path must remain inside the configured library root.",
        )
    if not candidate.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document does not exist in the local library.",
        )
    if candidate.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The current importer accepts PDF documents only.",
        )
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_local_pdf(session: Session, payload: LocalDocumentImport) -> Document:
    path = _resolve_library_path(payload.relative_path)
    file_hash = _sha256(path)

    existing = session.scalar(select(Document).where(Document.sha256 == file_hash))
    if existing is not None:
        return existing

    try:
        page_count = len(PdfReader(str(path)).pages)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to read PDF metadata: {exc}",
        ) from exc

    document = Document(
        title=payload.title or path.stem,
        source_layer=payload.source_layer,
        local_path=str(path.relative_to(settings.library_root.resolve())),
        sha256=file_hash,
        page_count=page_count,
        file_size_bytes=path.stat().st_size,
        media_type="application/pdf",
        import_status="IMPORTED",
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document
