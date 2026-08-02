from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

from fastapi import HTTPException, status
from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .library import _resolve_library_path
from .models import Document, DocumentPage, ExtractionStatus

_ARABIC_PRESENTATION_FORM_RANGES = (
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
)
_MIRRORED_PUNCTUATION = str.maketrans(
    {
        "(": ")",
        ")": "(",
        "[": "]",
        "]": "[",
        "{": "}",
        "}": "{",
        "<": ">",
        ">": "<",
        "«": "»",
        "»": "«",
    }
)


def _contains_arabic_presentation_forms(text: str) -> bool:
    return any(
        start <= ord(character) <= end
        for character in text
        for start, end in _ARABIC_PRESENTATION_FORM_RANGES
    )


def _restore_visual_rtl_line(line: str) -> str:
    """Convert a visually ordered Arabic PDF line into logical reading order.

    Some Arabic PDFs expose glyph presentation forms in left-to-right visual order.
    NFKC converts those glyphs to canonical Arabic letters, but the character and
    token order still needs reversing. Non-Arabic tokens retain their internal order.
    """
    tokens = re.findall(r"\S+", line)
    restored: list[str] = []
    for token in reversed(tokens):
        if any("\u0600" <= character <= "\u06ff" for character in token):
            token = token[::-1].translate(_MIRRORED_PUNCTUATION)
        restored.append(token)
    return " ".join(restored)


def _normalize_page_text(text: str | None) -> str:
    if not text:
        return ""

    raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized_lines: list[str] = []
    for raw_line in raw_lines:
        had_presentation_forms = _contains_arabic_presentation_forms(raw_line)
        line = unicodedata.normalize("NFKC", raw_line).rstrip()
        if had_presentation_forms and line.strip():
            line = _restore_visual_rtl_line(line)
        normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registered_pdf_path(document: Document) -> Path:
    if not document.local_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Legacy document has no registered local path and cannot be indexed.",
        )
    return _resolve_library_path(Path(document.local_path))


def index_document_pages(session: Session, document_id: int) -> list[DocumentPage]:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document is not registered.",
        )

    path = _registered_pdf_path(document)
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to open PDF for page indexing: {exc}",
        ) from exc

    extracted_pages: list[DocumentPage] = []
    for page_number, page in enumerate(reader.pages, start=1):
        extraction_error: str | None = None
        try:
            text = _normalize_page_text(page.extract_text())
            extraction_status = (
                ExtractionStatus.EXTRACTED if text else ExtractionStatus.EMPTY
            )
        except Exception as exc:
            text = ""
            extraction_status = ExtractionStatus.FAILED
            extraction_error = str(exc)

        extracted_pages.append(
            DocumentPage(
                document_id=document.id,
                page_number=page_number,
                text=text,
                char_count=len(text),
                word_count=len(text.split()),
                text_sha256=_text_sha256(text),
                extraction_status=extraction_status,
                extraction_error=extraction_error,
            )
        )

    session.execute(
        delete(DocumentPage).where(DocumentPage.document_id == document.id)
    )
    session.add_all(extracted_pages)
    document.page_count = len(extracted_pages)
    session.commit()

    return list(
        session.scalars(
            select(DocumentPage)
            .where(DocumentPage.document_id == document.id)
            .order_by(DocumentPage.page_number)
        )
    )


def list_document_pages(session: Session, document_id: int) -> list[DocumentPage]:
    if session.get(Document, document_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document is not registered.",
        )
    return list(
        session.scalars(
            select(DocumentPage)
            .where(DocumentPage.document_id == document_id)
            .order_by(DocumentPage.page_number)
        )
    )
