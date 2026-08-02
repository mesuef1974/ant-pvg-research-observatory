from pathlib import Path

from pydantic import BaseModel, Field

from .models import ExtractionStatus, SourceLayer


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
