from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import ensure_schema, get_session
from .indexing import index_document_pages, list_document_pages
from .library import import_local_pdf
from .models import Document, ExtractionStatus, SourceFile, SourceLayer
from .schemas import (
    DocumentPageView,
    DocumentView,
    LocalDocumentImport,
    PageIndexSummary,
    PageSearchResponseView,
    SourceCorpusImportRequest,
    SourceCorpusImportSummaryView,
    SourceFileView,
)
from .search import search_pages
from .source_corpus import import_encyclopedia_source, list_source_files

SessionDependency = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema()
    settings.library_root.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, version="0.3.0-dev", lifespan=lifespan)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/source-layers", tags=["governance"])
def source_layers() -> list[dict[str, str]]:
    return [
        {
            "key": "ENCYCLOPEDIA",
            "authority": "INTERNAL_CURATED",
            "rule": "Content imported from the governed encyclopedia corpus.",
        },
        {
            "key": "MODEL_SYNTHESIS",
            "authority": "UNVERIFIED_UNTIL_SOURCED",
            "rule": "May suggest links and questions but cannot certify a claim.",
        },
        {
            "key": "LITERATURE",
            "authority": "EXTERNAL_VERIFIED",
            "rule": "Requires traceable bibliographic evidence and reading status.",
        },
    ]


@app.get("/api/documents", response_model=list[DocumentView], tags=["library"])
def list_documents(session: SessionDependency) -> list[Document]:
    return list(session.scalars(select(Document).order_by(Document.id.desc())))


@app.post(
    "/api/documents/import-local",
    response_model=DocumentView,
    status_code=201,
    tags=["library"],
)
def import_document(
    payload: LocalDocumentImport,
    session: SessionDependency,
) -> Document:
    return import_local_pdf(session, payload)


@app.post(
    "/api/documents/{document_id}/index-pages",
    response_model=PageIndexSummary,
    tags=["indexing"],
)
def index_pages(document_id: int, session: SessionDependency) -> PageIndexSummary:
    pages = index_document_pages(session, document_id)
    return PageIndexSummary(
        document_id=document_id,
        page_count=len(pages),
        extracted_count=sum(
            page.extraction_status is ExtractionStatus.EXTRACTED for page in pages
        ),
        empty_count=sum(page.extraction_status is ExtractionStatus.EMPTY for page in pages),
        failed_count=sum(
            page.extraction_status is ExtractionStatus.FAILED for page in pages
        ),
    )


@app.get(
    "/api/documents/{document_id}/pages",
    response_model=list[DocumentPageView],
    tags=["indexing"],
)
def get_document_pages(
    document_id: int,
    session: SessionDependency,
) -> list[DocumentPageView]:
    return list_document_pages(session, document_id)


@app.get(
    "/api/search/pages",
    response_model=PageSearchResponseView,
    tags=["search"],
)
def search_document_pages(
    session: SessionDependency,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    document_id: Annotated[int | None, Query(gt=0)] = None,
    source_layer: SourceLayer | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageSearchResponseView:
    return PageSearchResponseView.model_validate(
        search_pages(
            session,
            query=q,
            document_id=document_id,
            source_layer=source_layer,
            limit=limit,
            offset=offset,
        )
    )


@app.post(
    "/api/source-corpus/import-encyclopedia",
    response_model=SourceCorpusImportSummaryView,
    tags=["source-corpus"],
)
def import_source_corpus(
    payload: SourceCorpusImportRequest,
    session: SessionDependency,
) -> SourceCorpusImportSummaryView:
    return SourceCorpusImportSummaryView.model_validate(
        import_encyclopedia_source(
            session,
            repository_root=payload.repository_root,
        )
    )


@app.get(
    "/api/source-corpus/files",
    response_model=list[SourceFileView],
    tags=["source-corpus"],
)
def get_source_files(session: SessionDependency) -> list[SourceFile]:
    return list_source_files(session)
