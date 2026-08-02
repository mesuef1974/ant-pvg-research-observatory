from pathlib import Path

from pydantic import BaseModel, Field

from .models import ClaimStatus, ExtractionStatus, SourceLayer


class LocalDocumentImport(BaseModel):
    relative_path: Path
    source_layer: SourceLayer
    title: str | None = Field(default=None, max_length=500)


class DocumentView(BaseModel):
    id: int
    title: str
    source_layer: SourceLayer
    local_path: str | None
    sha256: str | None
    media_type: str
    page_count: int
    file_size_bytes: int
    import_status: str

    model_config = {"from_attributes": True}


class DocumentPageView(BaseModel):
    id: int
    document_id: int
    page_number: int
    text: str
    char_count: int
    word_count: int
    text_sha256: str
    extraction_status: ExtractionStatus
    extraction_error: str | None

    model_config = {"from_attributes": True}


class PageIndexSummary(BaseModel):
    document_id: int
    page_count: int
    extracted_count: int
    empty_count: int
    failed_count: int


class PageSearchResultView(BaseModel):
    document_id: int
    document_title: str
    source_layer: SourceLayer
    page_number: int
    snippet: str
    char_count: int
    extraction_status: ExtractionStatus

    model_config = {"from_attributes": True}


class PageSearchResponseView(BaseModel):
    query: str
    total: int
    limit: int
    offset: int
    results: list[PageSearchResultView]

    model_config = {"from_attributes": True}


class SourceCorpusImportRequest(BaseModel):
    repository_root: Path


class SourceCorpusImportSummaryView(BaseModel):
    repository: str
    revision: str
    file_count: int
    section_count: int

    model_config = {"from_attributes": True}


class SourceFileView(BaseModel):
    id: int
    repository: str
    revision: str
    path: str
    order_index: int
    sha256: str
    line_count: int
    source_layer: SourceLayer

    model_config = {"from_attributes": True}


class EncyclopediaImportRequest(BaseModel):
    repository_root: Path


class EncyclopediaImportSummaryView(BaseModel):
    repository: str
    revision: str
    chapter_count: int
    unit_count: int
    result_count: int
    citable_count: int
    bibliography_count: int
    model_note_count: int
    coverage_gap_count: int
    finding_count: int

    # model_note_count يصطدم بمجال pydantic المحجوز model_؛ الحقل مقصود بهذا الاسم.
    model_config = {"from_attributes": True, "protected_namespaces": ()}


class ChapterView(BaseModel):
    id: int
    number: int
    title: str
    volume: str | None
    char_count: int
    revision: str

    model_config = {"from_attributes": True}


class UnitView(BaseModel):
    id: int
    chapter_id: int
    ordinal: int
    heading: str | None
    text: str
    blocks_json: str

    model_config = {"from_attributes": True}


class ResultView(BaseModel):
    result_key: str
    kind: str
    title: str | None
    chapter_number: int | None
    tex_status: str | None
    registry_status: str | None
    registry_files: str | None
    source_note: str | None
    citable: bool
    statement: str | None

    model_config = {"from_attributes": True}


class BibliographyEntryView(BaseModel):
    entry_key: str
    entry_type: str
    title: str | None
    author: str | None
    year: str | None
    journal: str | None
    doi: str | None
    url: str | None
    aliases: str | None
    bib_file: str
    cited: bool

    model_config = {"from_attributes": True}


class ModelSynthesisNoteView(BaseModel):
    """ملاحظة معيارية. ``citable`` ثابتة على False: لا يُستشهد بهذه الطبقة."""

    note_key: str
    title: str
    kind: str
    domain: str | None
    anchors: str | None
    literature_hint: str | None
    is_gap: bool
    body: str
    blocks_json: str
    source_file: str
    citable: bool = False

    model_config = {"from_attributes": True}


class IntegrityFindingView(BaseModel):
    code: str
    severity: str
    subject: str | None
    detail: str

    model_config = {"from_attributes": True}


class UnifiedSearchResultView(BaseModel):
    layer: SourceLayer
    kind: str
    key: str
    title: str
    snippet: str
    chapter_number: int | None = None
    citable: bool = False
    is_gap: bool = False
    rank: float = 0.0

    model_config = {"from_attributes": True}


class UnifiedSearchResponseView(BaseModel):
    query: str
    total: int
    results: list[UnifiedSearchResultView]

    model_config = {"from_attributes": True}


class ClaimCreate(BaseModel):
    claim_key: str | None = None
    statement: str = Field(min_length=1)
    source_layer: SourceLayer = SourceLayer.MODEL_SYNTHESIS
    status: ClaimStatus = ClaimStatus.MODEL_SYNTHESIS
    evidence_note: str | None = None
    novelty_note: str | None = None


class ClaimUpdate(BaseModel):
    statement: str | None = Field(default=None, min_length=1)
    source_layer: SourceLayer | None = None
    status: ClaimStatus | None = None
    evidence_note: str | None = None
    novelty_note: str | None = None


class ClaimView(BaseModel):
    id: int
    claim_key: str
    statement: str
    source_layer: SourceLayer
    status: ClaimStatus
    evidence_note: str | None
    novelty_note: str | None

    model_config = {"from_attributes": True}
