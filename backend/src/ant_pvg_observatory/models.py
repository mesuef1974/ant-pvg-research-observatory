from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
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
    #: بحث المؤلف نفسه: داخلي ومنقح لكن غير منشور ولا مُراجَع خارجيًا.
    PVG_RESEARCH = "PVG_RESEARCH"


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


class EncyclopediaChapter(Base):
    """فصل من الموسوعة. ليس ملفًا: الفصل السابع مقسَّم على خمسة ملفات مصدر."""

    __tablename__ = "encyclopedia_chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(1000))
    volume: Mapped[str | None] = mapped_column(String(200), index=True)
    tex_paths: Mapped[str] = mapped_column(Text)
    char_count: Mapped[int] = mapped_column(Integer)
    revision: Mapped[str] = mapped_column(String(100), index=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    units: Mapped[list[EncyclopediaUnit]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="EncyclopediaUnit.ordinal",
    )


class EncyclopediaUnit(Base):
    """وحدة نصية قابلة للاسترجاع: قسم من فصل، بكتله المهيكلة ونصه المطبَّع."""

    __tablename__ = "encyclopedia_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("encyclopedia_chapters.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, index=True)
    heading: Mapped[str | None] = mapped_column(String(1000))
    text: Mapped[str] = mapped_column(Text)
    search_text: Mapped[str] = mapped_column(Text)
    blocks_json: Mapped[str] = mapped_column(Text)
    text_sha256: Mapped[str] = mapped_column(String(64), index=True)

    chapter: Mapped[EncyclopediaChapter] = relationship(back_populates="units")


class EncyclopediaResult(Base):
    """نتيجة معرَّفة ANT-* بحالتها في المخطوط وفي سجلات النتائج.

    ``citable`` قرار محسوب من السجل وسياسة الاعتماد، وعليه يتوقف قبول أي
    ادعاء يستند إلى هذه النتيجة.
    """

    __tablename__ = "encyclopedia_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_key: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str | None] = mapped_column(String(1000))
    chapter_number: Mapped[int | None] = mapped_column(Integer, index=True)
    tex_status: Mapped[str | None] = mapped_column(String(60))
    registry_status: Mapped[str | None] = mapped_column(String(200))
    registry_files: Mapped[str | None] = mapped_column(Text)
    source_note: Mapped[str | None] = mapped_column(Text)
    citable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    label: Mapped[str | None] = mapped_column(String(300))
    statement: Mapped[str | None] = mapped_column(Text)
    tex_path: Mapped[str | None] = mapped_column(String(2000))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BibliographyEntry(Base):
    """مدخل ببليوغرافي. ``aliases`` مفاتيح biber المرادفة في حقل ids."""

    __tablename__ = "bibliography_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    entry_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(Text)
    year: Mapped[str | None] = mapped_column(String(20), index=True)
    journal: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String(300))
    url: Mapped[str | None] = mapped_column(String(2000))
    aliases: Mapped[str | None] = mapped_column(Text)
    bib_file: Mapped[str] = mapped_column(String(300), index=True)
    cited: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class ModelSynthesisNote(Base):
    """ملاحظة من طبقة المعرفة المعيارية.

    سلطتها ``UNVERIFIED_UNTIL_SOURCED`` بحكم البنية، ولا يجوز الاستشهاد بها
    بحال. ``is_gap`` يعني أن الموضوع معياري ولا تغطيه الموسوعة.
    """

    __tablename__ = "model_synthesis_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    note_key: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(1000))
    kind: Mapped[str] = mapped_column(String(40), index=True)
    domain: Mapped[str | None] = mapped_column(String(300), index=True)
    anchors: Mapped[str | None] = mapped_column(Text)
    literature_hint: Mapped[str | None] = mapped_column(Text)
    is_gap: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    body: Mapped[str] = mapped_column(Text)
    search_text: Mapped[str] = mapped_column(Text)
    blocks_json: Mapped[str] = mapped_column(Text)
    source_file: Mapped[str] = mapped_column(String(300), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IntegrityFinding(Base):
    """ملاحظة تكامل ناتجة عن فحص آلي للموسوعة أو لطبقات المرصد."""

    __tablename__ = "integrity_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    subject: Mapped[str | None] = mapped_column(String(300), index=True)
    detail: Mapped[str] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ReadingStatus(StrEnum):
    """حالة قراءة المرجع. الاكتشاف ليس قراءة، والقراءة ليست تحققًا."""

    DISCOVERED = "DISCOVERED"
    ABSTRACT_READ = "ABSTRACT-READ"
    FULLY_READ = "FULLY-READ"
    VERIFIED = "VERIFIED"


class GateRelation(StrEnum):
    """علاقة المرجع بسؤال البوابة."""

    COVERS = "COVERS"
    PARTIAL = "PARTIAL"
    ADJACENT = "ADJACENT"
    CONTRADICTS = "CONTRADICTS"
    NOT_RELEVANT = "NOT-RELEVANT"


class GateVerdict(StrEnum):
    """حكم البوابة على سؤالها."""

    NOT_ASSESSED = "NOT-ASSESSED"
    KNOWN = "KNOWN"
    EQUIVALENT = "EQUIVALENT"
    PARTIAL = "PARTIAL"
    NOT_FOUND_YET = "NOT-FOUND-YET"


class ObservatoryReference(Base):
    """مرجع في سجل المرصد، مستقل عن ببليوغرافيا الموسوعة.

    ``bibliography_key`` وصلة اختيارية إلى مدخل في الموسوعة حين يكون المرجع
    نفسه مستشهدًا به هناك، فلا يُكرَّر التوثيق.
    """

    __tablename__ = "observatory_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str | None] = mapped_column(Text)
    year: Mapped[str | None] = mapped_column(String(20), index=True)
    venue: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String(300), index=True)
    url: Mapped[str | None] = mapped_column(String(2000))
    reading_status: Mapped[ReadingStatus] = mapped_column(
        Enum(ReadingStatus), default=ReadingStatus.DISCOVERED, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
    bibliography_key: Mapped[str | None] = mapped_column(String(200), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    gate_links: Mapped[list[GateReference]] = relationship(
        back_populates="reference", cascade="all, delete-orphan"
    )


class GateReference(Base):
    """ربط مرجع ببوابة أدبيات، بعلاقة صريحة ومدى تغطية.

    هذا الجدول هو موضع القيمة في البوابة: البوابة بلا مراجع مربوطة سؤال بلا
    مسح، وحكمها حينئذ رأي لا نتيجة مراجعة.
    """

    __tablename__ = "gate_references"

    gate_id: Mapped[int] = mapped_column(
        ForeignKey("literature_gates.id", ondelete="CASCADE"), primary_key=True
    )
    reference_id: Mapped[int] = mapped_column(
        ForeignKey("observatory_references.id", ondelete="CASCADE"), primary_key=True
    )
    relation: Mapped[GateRelation] = mapped_column(Enum(GateRelation), index=True)
    coverage_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    gate: Mapped[LiteratureGate] = relationship()
    reference: Mapped[ObservatoryReference] = relationship(back_populates="gate_links")


class KnowledgeLink(Base):
    """رابط صريح بين كائنين في المرصد.

    الطرفان يُعرَّفان بنوعٍ ومفتاحٍ نصي لا بمفتاح أجنبي، لأن الأنواع متغايرة
    (نتيجة، ادعاء، بوابة، مرجع، ملاحظة معيارية) ولأن الرابط قد يسبق وجود
    الطرف الآخر في القاعدة.
    """

    __tablename__ = "knowledge_links"
    __table_args__ = (
        UniqueConstraint(
            "from_type", "from_key", "relation", "to_type", "to_key",
            name="uq_knowledge_link",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    from_type: Mapped[str] = mapped_column(String(40), index=True)
    from_key: Mapped[str] = mapped_column(String(200), index=True)
    relation: Mapped[str] = mapped_column(String(60), index=True)
    to_type: Mapped[str] = mapped_column(String(40), index=True)
    to_key: Mapped[str] = mapped_column(String(200), index=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EvidenceRecord(Base):
    """صف من سجل أدلة أو خريطة برهان في مستودع الموسوعة.

    هذه الملفات هي عمل التحقق الببليوغرافي الذي يسبق تأليف الفصل: لكل مصدر
    صياغةٌ مسموح بها وموضعٌ في المصدر وحكمٌ على درجة التحقق. المرصد يقرأها
    ولا يعيد إنتاجها، فتصير حالة التحقق قابلة للاستعلام والفحص الآلي.
    """

    __tablename__ = "evidence_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_number: Mapped[int | None] = mapped_column(Integer, index=True)
    document_kind: Mapped[str] = mapped_column(String(40), index=True)
    source_file: Mapped[str] = mapped_column(String(300), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    columns_json: Mapped[str] = mapped_column(Text)
    statement: Mapped[str | None] = mapped_column(Text)
    source_note: Mapped[str | None] = mapped_column(Text)
    verdict: Mapped[str | None] = mapped_column(String(300), index=True)
    doi: Mapped[str | None] = mapped_column(String(300), index=True)
    cutoff_date: Mapped[str | None] = mapped_column(String(40))
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PvgDocument(Base):
    """مستند من مدونة بحث PVG، بكتله المهيكلة وبصمته."""

    __tablename__ = "pvg_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(1000))
    body: Mapped[str] = mapped_column(Text)
    search_text: Mapped[str] = mapped_column(Text)
    blocks_json: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    char_count: Mapped[int] = mapped_column(Integer)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PvgResult(Base):
    """نتيجة معرَّفة في مدونة PVG.

    ``is_proven`` محسوب من مفردات حالة المدونة نفسها: ``FINITE-VERIFIED`` و
    ``INTERPRETATION`` و``HYPOTHESIS`` ليست براهين، والأرشيف يعلن ذلك بنفسه.
    """

    __tablename__ = "pvg_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_key: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    statement: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(200), index=True)
    is_proven: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    source_file: Mapped[str] = mapped_column(String(300), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
