from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .models import Document, DocumentPage, ExtractionStatus, SourceLayer


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


def _snippet(text: str, query: str, radius: int = 120) -> str:
    folded_text = text.casefold()
    folded_query = query.casefold()
    match_start = folded_text.find(folded_query)
    if match_start < 0:
        return text[: radius * 2].strip()

    start = max(match_start - radius, 0)
    end = min(match_start + len(query) + radius, len(text))
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def _base_query(
    query: str,
    document_id: int | None,
    source_layer: SourceLayer | None,
) -> Select[tuple[DocumentPage, Document]]:
    statement = (
        select(DocumentPage, Document)
        .join(Document, Document.id == DocumentPage.document_id)
        .where(DocumentPage.extraction_status == ExtractionStatus.EXTRACTED)
        .where(func.lower(DocumentPage.text).contains(query.casefold()))
    )
    if document_id is not None:
        statement = statement.where(Document.id == document_id)
    if source_layer is not None:
        statement = statement.where(Document.source_layer == source_layer)
    return statement


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
    statement = _base_query(normalized_query, document_id, source_layer)

    total = session.scalar(
        select(func.count()).select_from(statement.order_by(None).subquery())
    ) or 0

    rows = session.execute(
        statement.order_by(Document.id, DocumentPage.page_number)
        .offset(offset)
        .limit(limit)
    ).all()

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
        for page, document in rows
    ]
    return PageSearchResponse(
        query=normalized_query,
        total=total,
        limit=limit,
        offset=offset,
        results=results,
    )
