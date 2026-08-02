from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Document, DocumentPage, ExtractionStatus, SourceLayer

_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
_WHITESPACE = re.compile(r"\s+")
_ARABIC_EQUIVALENTS = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ـ": "",
    }
)


@dataclass(frozen=True, slots=True)
class PageSearchResult:
    document_id: int
    document_title: str
    source_layer: SourceLayer
    page_number: int
    snippet: str
    char_count: int
    extraction_status: ExtractionStatus


@dataclass(frozen=True, slots=True)
class PageSearchResponse:
    query: str
    total: int
    limit: int
    offset: int
    results: list[PageSearchResult]


def _search_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = _ARABIC_DIACRITICS.sub("", normalized)
    normalized = normalized.translate(_ARABIC_EQUIVALENTS)
    return _WHITESPACE.sub("", normalized)


def _snippet(text: str, query: str, radius: int = 120) -> str:
    folded_text = text.casefold()
    folded_query = query.casefold()
    match_start = folded_text.find(folded_query)

    if match_start < 0:
        for token in query.split():
            match_start = folded_text.find(token.casefold())
            if match_start >= 0:
                folded_query = token.casefold()
                break

    if match_start < 0:
        return text[: radius * 2].strip()

    start = max(match_start - radius, 0)
    end = min(match_start + len(folded_query) + radius, len(text))
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def _candidate_rows(
    session: Session,
    document_id: int | None,
    source_layer: SourceLayer | None,
) -> list[tuple[DocumentPage, Document]]:
    statement = (
        select(DocumentPage, Document)
        .join(Document, Document.id == DocumentPage.document_id)
        .where(DocumentPage.extraction_status == ExtractionStatus.EXTRACTED)
    )
    if document_id is not None:
        statement = statement.where(Document.id == document_id)
    if source_layer is not None:
        statement = statement.where(Document.source_layer == source_layer)

    return list(
        session.execute(
            statement.order_by(Document.id, DocumentPage.page_number)
        ).all()
    )


def search_pages(
    session: Session,
    *,
    query: str,
    document_id: int | None = None,
    source_layer: SourceLayer | None = None,
    limit: int = 20,
    offset: int = 0,
) -> PageSearchResponse:
    normalized_query = query.strip()
    query_key = _search_key(normalized_query)

    matching_rows = [
        (page, document)
        for page, document in _candidate_rows(session, document_id, source_layer)
        if query_key in _search_key(page.text)
    ]
    paged_rows = matching_rows[offset : offset + limit]

    results = [
        PageSearchResult(
            document_id=document.id,
            document_title=document.title,
            source_layer=document.source_layer,
            page_number=page.page_number,
            snippet=_snippet(page.text, normalized_query),
            char_count=page.char_count,
            extraction_status=page.extraction_status,
        )
        for page, document in paged_rows
    ]
    return PageSearchResponse(
        query=normalized_query,
        total=len(matching_rows),
        limit=limit,
        offset=offset,
        results=results,
    )
