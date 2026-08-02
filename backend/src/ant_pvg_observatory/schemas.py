from pathlib import Path

from pydantic import BaseModel, Field

from .models import SourceLayer


class LocalDocumentImport(BaseModel):
    relative_path: Path
    source_layer: SourceLayer
    title: str | None = Field(default=None, max_length=500)


class DocumentView(BaseModel):
    id: int
    title: str
    source_layer: SourceLayer
    local_path: str
    sha256: str
    media_type: str
    page_count: int
    file_size_bytes: int
    import_status: str

    model_config = {"from_attributes": True}
