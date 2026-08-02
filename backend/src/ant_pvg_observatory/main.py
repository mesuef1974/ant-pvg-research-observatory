from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import ensure_schema, get_session
from .indexing import index_document_pages, list_document_pages
from .library import import_local_pdf
from .models import Document, ExtractionStatus
from .schemas import (
    DocumentPageView,
    DocumentView,
    LocalDocumentImport,
    PageIndexSummary,
)

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
