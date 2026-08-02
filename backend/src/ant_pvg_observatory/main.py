from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import ensure_schema, get_session
from .encyclopedia import ingestion
from .encyclopedia.search import search_corpus
from .governance import enforce_citation_policy, enforce_gate_closure
from .indexing import index_document_pages, list_document_pages
from .library import import_local_pdf
from .models import (
    BibliographyEntry,
    Claim,
    Document,
    EncyclopediaChapter,
    EncyclopediaResult,
    EncyclopediaUnit,
    ExtractionStatus,
    GateReference,
    GateVerdict,
    IntegrityFinding,
    KnowledgeLink,
    LiteratureGate,
    ModelSynthesisNote,
    ObservatoryReference,
    ReadingStatus,
    SourceFile,
    SourceLayer,
)
from .research_io import export_research_layer
from .schemas import (
    BibliographyEntryView,
    ChapterView,
    ClaimCreate,
    ClaimUpdate,
    ClaimView,
    DashboardView,
    DocumentPageView,
    DocumentView,
    EncyclopediaImportRequest,
    EncyclopediaImportSummaryView,
    GateCreate,
    GateReferenceLink,
    GateReferenceView,
    GateUpdate,
    GateView,
    IntegrityFindingView,
    KnowledgeLinkCreate,
    KnowledgeLinkView,
    LocalDocumentImport,
    ModelSynthesisNoteView,
    PageIndexSummary,
    PageSearchResponseView,
    ReferenceCreate,
    ReferenceUpdate,
    ReferenceView,
    ResultView,
    SourceCorpusImportRequest,
    SourceCorpusImportSummaryView,
    SourceFileView,
    UnifiedSearchResponseView,
    UnitView,
)
from .search import search_pages
from .source_corpus import import_encyclopedia_source, list_source_files


def _mint_key(prefix: str) -> str:
    """مفتاح مقروء ومتفرّد.

    الطابع الزمني وحده لا يكفي: دقة الساعة على Windows قد تبلغ أجزاء من
    الألف من الثانية، فإنشاءان متتاليان يتصادمان على قيد التفرّد.
    """
    return f"{prefix}-{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"


SessionDependency = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema()
    settings.library_root.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, version="0.4.0-dev", lifespan=lifespan)

#: جذر الملفات الساكنة. الواجهة تُقدَّم من الخادم نفسه، فلا حاجة إلى ثانٍ.
STATIC_ROOT = Path(__file__).resolve().parents[3] / "static"


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


@app.get(
    "/api/search/corpus",
    response_model=UnifiedSearchResponseView,
    tags=["search"],
)
def search_unified(
    session: SessionDependency,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    source_layer: SourceLayer | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 40,
) -> UnifiedSearchResponseView:
    """بحث عبر الطبقات الثلاث. كل نتيجة تحمل طبقتها وقابليتها للاستشهاد."""
    return UnifiedSearchResponseView.model_validate(
        search_corpus(session, query=q, source_layer=source_layer, limit=limit)
    )


@app.get("/api/claims", response_model=list[ClaimView], tags=["governance"])
def list_claims(session: SessionDependency) -> list[Claim]:
    return list(session.scalars(select(Claim).order_by(Claim.id.desc())))


@app.post(
    "/api/claims",
    response_model=ClaimView,
    status_code=201,
    tags=["governance"],
)
def create_claim(payload: ClaimCreate, session: SessionDependency) -> Claim:
    """ينشئ ادعاءً بعد إنفاذ قاعدة الاعتماد الخارجي."""
    enforce_citation_policy(
        session,
        statement=payload.statement,
        claim_status=payload.status,
        source_layer=payload.source_layer,
        evidence_note=payload.evidence_note,
        novelty_note=payload.novelty_note,
    )
    claim = Claim(
        claim_key=payload.claim_key or _mint_key("CLAIM"),
        statement=payload.statement,
        source_layer=payload.source_layer,
        status=payload.status,
        evidence_note=payload.evidence_note,
        novelty_note=payload.novelty_note,
    )
    session.add(claim)
    session.commit()
    session.refresh(claim)
    return claim


@app.patch(
    "/api/claims/{claim_key}",
    response_model=ClaimView,
    tags=["governance"],
)
def update_claim(
    claim_key: str,
    payload: ClaimUpdate,
    session: SessionDependency,
) -> Claim:
    """يحدّث ادعاءً. الحالة الناتجة تُفحص كاملةً لا الحقول المتغيرة وحدها."""
    claim = session.scalars(
        select(Claim).where(Claim.claim_key == claim_key)
    ).one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail="الادعاء غير موجود")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="لا حقول قابلة للتعديل في الطلب")

    merged = {
        "statement": changes.get("statement", claim.statement),
        "source_layer": changes.get("source_layer", claim.source_layer),
        "status": changes.get("status", claim.status),
        "evidence_note": changes.get("evidence_note", claim.evidence_note),
        "novelty_note": changes.get("novelty_note", claim.novelty_note),
    }
    enforce_citation_policy(
        session,
        statement=merged["statement"],
        claim_status=merged["status"],
        source_layer=merged["source_layer"],
        evidence_note=merged["evidence_note"],
        novelty_note=merged["novelty_note"],
    )
    for field, value in merged.items():
        setattr(claim, field, value)
    session.commit()
    session.refresh(claim)
    return claim


@app.get("/api/dashboard", response_model=DashboardView, tags=["system"])
def dashboard(session: SessionDependency) -> DashboardView:
    """ملخّص واحد للوحة القيادة بدل عشرة طلبات منفصلة."""
    def count(model) -> int:
        return session.scalar(select(func.count()).select_from(model)) or 0

    severity_rows = session.execute(
        select(IntegrityFinding.severity, func.count())
        .group_by(IntegrityFinding.severity)
    ).all()
    status_rows = session.execute(
        select(
            func.coalesce(
                EncyclopediaResult.registry_status,
                EncyclopediaResult.tex_status,
                "غير محدد",
            ).label("status"),
            func.count(),
        )
        .group_by("status")
        .order_by(func.count().desc())
    ).all()
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    top = sorted(
        session.scalars(
            select(IntegrityFinding)
            .where(IntegrityFinding.severity.in_(["CRITICAL", "HIGH"]))
            .limit(20)
        ),
        key=lambda f: order.get(f.severity, 9),
    )[:8]
    revision = session.scalar(select(EncyclopediaChapter.revision).limit(1))

    return DashboardView(
        counts={
            "chapters": count(EncyclopediaChapter),
            "units": count(EncyclopediaUnit),
            "results": count(EncyclopediaResult),
            "citable": session.scalar(
                select(func.count())
                .select_from(EncyclopediaResult)
                .where(EncyclopediaResult.citable.is_(True))
            )
            or 0,
            "bib": count(BibliographyEntry),
            "model_notes": count(ModelSynthesisNote),
            "coverage_gaps": session.scalar(
                select(func.count())
                .select_from(ModelSynthesisNote)
                .where(ModelSynthesisNote.is_gap.is_(True))
            )
            or 0,
            "claims": count(Claim),
            "gates": count(LiteratureGate),
            "findings": count(IntegrityFinding),
        },
        severity={row[0]: row[1] for row in severity_rows},
        revision=revision,
        by_status=[{"s": row[0], "n": row[1]} for row in status_rows],
        top_findings=[IntegrityFindingView.model_validate(f) for f in top],
        recent_claims=[
            ClaimView.model_validate(c)
            for c in session.scalars(select(Claim).order_by(Claim.id.desc()).limit(6))
        ],
        gates=[
            GateView.model_validate(g)
            for g in session.scalars(
                select(LiteratureGate).order_by(LiteratureGate.id.desc()).limit(6)
            )
        ],
    )


@app.get("/api/gates", response_model=list[GateView], tags=["governance"])
def list_gates(session: SessionDependency) -> list[LiteratureGate]:
    return list(
        session.scalars(select(LiteratureGate).order_by(LiteratureGate.id.desc()))
    )


@app.post(
    "/api/gates", response_model=GateView, status_code=201, tags=["governance"]
)
def create_gate(payload: GateCreate, session: SessionDependency) -> LiteratureGate:
    gate = LiteratureGate(
        gate_key=payload.gate_key or _mint_key("GATE"),
        title=payload.title,
        research_question=payload.research_question,
        status=payload.status,
        verdict=payload.verdict,
    )
    session.add(gate)
    session.commit()
    session.refresh(gate)
    return gate


@app.patch("/api/gates/{gate_key}", response_model=GateView, tags=["governance"])
def update_gate(
    gate_key: str, payload: GateUpdate, session: SessionDependency
) -> LiteratureGate:
    gate = session.scalars(
        select(LiteratureGate).where(LiteratureGate.gate_key == gate_key)
    ).one_or_none()
    if gate is None:
        raise HTTPException(status_code=404, detail="البوابة غير موجودة")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="لا حقول قابلة للتعديل في الطلب")
    merged_status = changes.get("status", gate.status)
    merged_verdict = changes.get("verdict", gate.verdict)
    enforce_gate_closure(
        session,
        gate=gate,
        status=merged_status,
        verdict=GateVerdict(merged_verdict) if merged_verdict else None,
    )
    for field, value in changes.items():
        setattr(gate, field, value)
    session.commit()
    session.refresh(gate)
    return gate


# ---------------------------------------------------------- سجل مراجع المرصد


def _reference_or_404(session: Session, reference_key: str) -> ObservatoryReference:
    reference = session.scalars(
        select(ObservatoryReference).where(
            ObservatoryReference.reference_key == reference_key
        )
    ).one_or_none()
    if reference is None:
        raise HTTPException(status_code=404, detail="المرجع غير موجود")
    return reference


def _gate_or_404(session: Session, gate_key: str) -> LiteratureGate:
    gate = session.scalars(
        select(LiteratureGate).where(LiteratureGate.gate_key == gate_key)
    ).one_or_none()
    if gate is None:
        raise HTTPException(status_code=404, detail="البوابة غير موجودة")
    return gate


@app.get("/api/references", response_model=list[ReferenceView], tags=["literature"])
def list_references(
    session: SessionDependency,
    reading_status: ReadingStatus | None = None,
) -> list[ObservatoryReference]:
    statement = select(ObservatoryReference).order_by(ObservatoryReference.id.desc())
    if reading_status is not None:
        statement = statement.where(
            ObservatoryReference.reading_status == reading_status
        )
    return list(session.scalars(statement))


@app.post(
    "/api/references",
    response_model=ReferenceView,
    status_code=201,
    tags=["literature"],
)
def create_reference(
    payload: ReferenceCreate, session: SessionDependency
) -> ObservatoryReference:
    reference = ObservatoryReference(
        reference_key=payload.reference_key or _mint_key("REF"),
        **payload.model_dump(exclude={"reference_key"}),
    )
    session.add(reference)
    session.commit()
    session.refresh(reference)
    return reference


@app.patch(
    "/api/references/{reference_key}",
    response_model=ReferenceView,
    tags=["literature"],
)
def update_reference(
    reference_key: str, payload: ReferenceUpdate, session: SessionDependency
) -> ObservatoryReference:
    reference = _reference_or_404(session, reference_key)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="لا حقول قابلة للتعديل في الطلب")
    for field, value in changes.items():
        setattr(reference, field, value)
    session.commit()
    session.refresh(reference)
    return reference


# ------------------------------------------------- ربط المراجع بالبوابات


@app.get(
    "/api/gates/{gate_key}/references",
    response_model=list[GateReferenceView],
    tags=["governance"],
)
def list_gate_references(
    gate_key: str, session: SessionDependency
) -> list[GateReferenceView]:
    gate = _gate_or_404(session, gate_key)
    links = session.scalars(
        select(GateReference).where(GateReference.gate_id == gate.id)
    ).all()
    return [
        GateReferenceView(
            reference_key=link.reference.reference_key,
            title=link.reference.title,
            reading_status=link.reference.reading_status,
            relation=link.relation,
            coverage_note=link.coverage_note,
        )
        for link in links
    ]


@app.post(
    "/api/gates/{gate_key}/references",
    response_model=GateReferenceView,
    status_code=201,
    tags=["governance"],
)
def link_gate_reference(
    gate_key: str, payload: GateReferenceLink, session: SessionDependency
) -> GateReferenceView:
    """يربط مرجعًا ببوابة. الربط هو ما يحوّل البوابة من سؤال إلى مراجعة."""
    gate = _gate_or_404(session, gate_key)
    reference = _reference_or_404(session, payload.reference_key)

    link = session.get(GateReference, (gate.id, reference.id))
    if link is None:
        link = GateReference(gate_id=gate.id, reference_id=reference.id)
        session.add(link)
    link.relation = payload.relation
    link.coverage_note = payload.coverage_note
    session.commit()
    return GateReferenceView(
        reference_key=reference.reference_key,
        title=reference.title,
        reading_status=reference.reading_status,
        relation=link.relation,
        coverage_note=link.coverage_note,
    )


@app.delete(
    "/api/gates/{gate_key}/references/{reference_key}",
    status_code=204,
    tags=["governance"],
)
def unlink_gate_reference(
    gate_key: str, reference_key: str, session: SessionDependency
) -> None:
    gate = _gate_or_404(session, gate_key)
    reference = _reference_or_404(session, reference_key)
    link = session.get(GateReference, (gate.id, reference.id))
    if link is None:
        raise HTTPException(status_code=404, detail="الربط غير موجود")
    session.delete(link)
    session.commit()


# ------------------------------------------------------------- شبكة الروابط


@app.get("/api/links", response_model=list[KnowledgeLinkView], tags=["governance"])
def list_links(
    session: SessionDependency,
    from_key: str | None = None,
    to_key: str | None = None,
) -> list[KnowledgeLink]:
    statement = select(KnowledgeLink).order_by(KnowledgeLink.id.desc())
    if from_key is not None:
        statement = statement.where(KnowledgeLink.from_key == from_key)
    if to_key is not None:
        statement = statement.where(KnowledgeLink.to_key == to_key)
    return list(session.scalars(statement))


@app.post(
    "/api/links",
    response_model=KnowledgeLinkView,
    status_code=201,
    tags=["governance"],
)
def create_link(
    payload: KnowledgeLinkCreate, session: SessionDependency
) -> KnowledgeLink:
    existing = session.scalars(
        select(KnowledgeLink).where(
            KnowledgeLink.from_type == payload.from_type,
            KnowledgeLink.from_key == payload.from_key,
            KnowledgeLink.relation == payload.relation,
            KnowledgeLink.to_type == payload.to_type,
            KnowledgeLink.to_key == payload.to_key,
        )
    ).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="الرابط موجود سلفًا")
    link = KnowledgeLink(**payload.model_dump())
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


@app.get("/api/research-layer/export", tags=["governance"])
def export_research(session: SessionDependency) -> dict:
    """الطبقة البحثية كاملةً بترتيب ثابت.

    قراءة فقط. الاسترجاع يجري عبر ``scripts/research_layer.py import`` لأنه
    يكتب في القاعدة، فلا يُعرَّض على واجهة تُفتح بالنقر.
    """
    return export_research_layer(session)


if STATIC_ROOT.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_ROOT / "index.html")

    @app.get("/{asset:path}", include_in_schema=False)
    def static_asset(asset: str) -> FileResponse:
        """يقدّم أصول الواجهة. المسارات خارج مجلد الملفات الساكنة مرفوضة."""
        candidate = (STATIC_ROOT / asset).resolve()
        if not candidate.is_relative_to(STATIC_ROOT) or not candidate.is_file():
            raise HTTPException(status_code=404, detail="غير موجود")
        return FileResponse(candidate)
