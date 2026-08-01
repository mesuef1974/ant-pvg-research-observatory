from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
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


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    source_layer: Mapped[SourceLayer] = mapped_column(Enum(SourceLayer), index=True)
    local_path: Mapped[str | None] = mapped_column(String(2000))
    sha256: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    claims: Mapped[list[Claim]] = relationship(back_populates="document")


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
        DateTime, server_default=func.now(), onupdate=func.now()
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
