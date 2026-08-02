from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import ensure_schema, get_session
from .encyclopedia import ingestion
from .indexing import index_document_pages, list_document_pages
from .library import import_local_pdf
from .models import (
    BibliographyEntry,
    Document,
    EncyclopediaChapter,
    EncyclopediaResult,
    EncyclopediaUnit,
    ExtractionStatus,
    IntegrityFinding,
    ModelSynthesisNote,
    SourceFile,
    SourceLayer,
)
from .schemas import (
    BibliographyEntryView,
    ChapterView,
    DocumentPageView,
    DocumentView,
    EncyclopediaImportRequest,
    EncyclopediaImportSummaryView,
    IntegrityFindingView,
    LocalDocumentImport,
    ModelSynthesisNoteView,
    PageIndexSummary,
    PageSearchResponseView,
    ResultView,
    SourceCorpusImportRequest,
    SourceCorpusImportSummaryView,
    SourceFileView,
    UnitView,
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


@app.post(
    "/api/encyclopedia/import",
    response_model=EncyclopediaImportSummaryView,
    tags=["encyclopedia"],
)
def import_encyclopedia(
    payload: EncyclopediaImportRequest,
    session: SessionDependency,
) -> EncyclopediaImportSummaryView:
    """يستوعب الموسوعة من مصدر LaTeX ويسجّل مراجعة Git وفحوص التكامل."""
    return EncyclopediaImportSummaryView.model_validate(
        ingestion.import_encyclopedia(
            session,
            repository_root=payload.repository_root,
        )
    )


@app.get(
    "/api/encyclopedia/chapters",
    response_model=list[ChapterView],
    tags=["encyclopedia"],
)
def list_chapters(session: SessionDependency) -> list[EncyclopediaChapter]:
    return list(
        session.scalars(
            select(EncyclopediaChapter).order_by(EncyclopediaChapter.number)
        )
    )


@app.get(
    "/api/encyclopedia/units",
    response_model=list[UnitView],
    tags=["encyclopedia"],
)
def list_units(
    session: SessionDependency,
    chapter_id: Annotated[int, Query(gt=0)],
) -> list[EncyclopediaUnit]:
    return list(
        session.scalars(
            select(EncyclopediaUnit)
            .where(EncyclopediaUnit.chapter_id == chapter_id)
            .order_by(EncyclopediaUnit.ordinal)
        )
    )


@app.get(
    "/api/encyclopedia/results",
    response_model=list[ResultView],
    tags=["encyclopedia"],
)
def list_results(
    session: SessionDependency,
    chapter_number: Annotated[int | None, Query(gt=0)] = None,
    citable: bool | None = None,
) -> list[EncyclopediaResult]:
    statement = select(EncyclopediaResult).order_by(
        EncyclopediaResult.chapter_number, EncyclopediaResult.result_key
    )
    if chapter_number is not None:
        statement = statement.where(
            EncyclopediaResult.chapter_number == chapter_number
        )
    if citable is not None:
        statement = statement.where(EncyclopediaResult.citable == citable)
    return list(session.scalars(statement))


@app.get(
    "/api/encyclopedia/bibliography",
    response_model=list[BibliographyEntryView],
    tags=["encyclopedia"],
)
def list_bibliography(session: SessionDependency) -> list[BibliographyEntry]:
    return list(
        session.scalars(select(BibliographyEntry).order_by(BibliographyEntry.entry_key))
    )


@app.get(
    "/api/model-synthesis/notes",
    response_model=list[ModelSynthesisNoteView],
    tags=["model-synthesis"],
)
def list_model_notes(
    session: SessionDependency,
    kind: str | None = None,
    is_gap: bool | None = None,
) -> list[ModelSynthesisNote]:
    """طبقة المعرفة المعيارية. لا يُستشهد بها: ``citable`` ثابتة على False."""
    statement = select(ModelSynthesisNote).order_by(
        ModelSynthesisNote.source_file, ModelSynthesisNote.note_key
    )
    if kind is not None:
        statement = statement.where(ModelSynthesisNote.kind == kind)
    if is_gap is not None:
        statement = statement.where(ModelSynthesisNote.is_gap == is_gap)
    return list(session.scalars(statement))


@app.get(
    "/api/integrity/findings",
    response_model=list[IntegrityFindingView],
    tags=["governance"],
)
def list_integrity_findings(
    session: SessionDependency,
    severity: str | None = None,
    code: str | None = None,
) -> list[IntegrityFinding]:
    statement = select(IntegrityFinding).order_by(
        IntegrityFinding.severity, IntegrityFinding.code
    )
    if severity is not None:
        statement = statement.where(IntegrityFinding.severity == severity)
    if code is not None:
        statement = statement.where(IntegrityFinding.code == code)
    return list(session.scalars(statement))
