from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class SourceLayer(StrEnum):
    ENCYCLOPEDIA = "ENCYCLOPEDIA"
    MODEL_SYNTHESIS = "MODEL_SYNTHESIS"
    LITERATURE = "LITERATURE"


class ClaimStatus(StrEnum):
    KNOWN = "KNOWN"
    KNOWN_EQUIVALENT = "KNOWN-IN-EQUIVALENT-FORM"
    SPECIALIZATION = "SPECIALIZATION-OF-KNOWN"
    MODEL_SYNTHESIS = "MODEL-SYNTHESIS"
    LITERATURE_UNCLEAR = "LITERATURE-UNCLEAR"
    NOT_FOUND_YET = "NOT-FOUND-YET"
    CANDIDATE_GAP = "CANDIDATE-GAP"
    PROVED_HERE = "PROVED-HERE"
    FINITE_VERIFIED = "FINITE-VERIFIED"
    OPEN = "OPEN"
    RETRACTED = "RETRACTED"


class ExtractionStatus(StrEnum):
    PENDING = "PENDING"
    EXTRACTED = "EXTRACTED"
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    source_layer: Mapped[SourceLayer] = mapped_column(Enum(SourceLayer), index=True)
    local_path: Mapped[str | None] = mapped_column(String(2000), unique=True)
    sha256: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    media_type: Mapped[str] = mapped_column(String(120), default="application/pdf")
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    import_status: Mapped[str] = mapped_column(String(40), default="IMPORTED", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    claims: Mapped[list[Claim]] = relationship(back_populates="document")
    pages: Mapped[list[DocumentPage]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentPage.page_number",
    )


class DocumentPage(Base):
    __tablename__ = "document_pages"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "page_number",
            name="uq_document_pages_document_page",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, default="")
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    text_sha256: Mapped[str] = mapped_column(String(64), index=True)
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus),
        index=True,
    )
    extraction_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="pages")


class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    repository: Mapped[str] = mapped_column(String(300), index=True)
    revision: Mapped[str] = mapped_column(String(100), index=True)
    path: Mapped[str] = mapped_column(String(2000), unique=True, index=True)
    order_index: Mapped[int] = mapped_column(Integer, index=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    line_count: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    source_layer: Mapped[SourceLayer] = mapped_column(
        Enum(SourceLayer), default=SourceLayer.ENCYCLOPEDIA, index=True
    )
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sections: Mapped[list[SourceSection]] = relationship(
        back_populates="source_file",
        cascade="all, delete-orphan",
        order_by="SourceSection.start_line",
    )


class SourceSection(Base):
    __tablename__ = "source_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_file_id: Mapped[int] = mapped_column(
        ForeignKey("source_files.id", ondelete="CASCADE"), index=True
    )
    heading_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(1000), index=True)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    text_sha256: Mapped[str] = mapped_column(String(64), index=True)

    source_file: Mapped[SourceFile] = relationship(back_populates="sections")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    statement: Mapped[str] = mapped_column(Text)
    source_layer: Mapped[SourceLayer] = mapped_column(Enum(SourceLayer), index=True)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), index=True)
    evidence_note: Mapped[str | None] = mapped_column(Text)
    novelty_note: Mapped[str | None] = mapped_column(Text)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document | None] = relationship(back_populates="claims")


class LiteratureGate(Base):
    __tablename__ = "literature_gates"

    id: Mapped[int] = mapped_column(primary_key=True)
    gate_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    research_question: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="OPEN", index=True)
    verdict: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
