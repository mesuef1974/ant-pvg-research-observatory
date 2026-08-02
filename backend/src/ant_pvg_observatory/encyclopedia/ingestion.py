"""تخزين نتائج تحليل الموسوعة في قاعدة البيانات.

يجمع هذا الملف بين مصدرين كانا منفصلين:

* تتبّع المصدر من ``source_corpus``: بصمة SHA-256 لكل ملف ومراجعة Git للمستودع،
  فيصير كل استيراد قابلًا للنسبة إلى حالة معلومة من المصدر.
* التحليل البنيوي من ``parsing``: كتل مهيكلة تحفظ المعادلات والبيئات المسمّاة،
  ونتائج ``ANT-*`` بحالاتها، والببليوغرافيا، وطبقة المعرفة المعيارية.

الاستيراد متكافئ التنفيذ: إعادة تشغيله على مصدر لم يتغير تعطي الحالة نفسها.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..models import (
    BibliographyEntry,
    EncyclopediaChapter,
    EncyclopediaResult,
    EncyclopediaUnit,
    IntegrityFinding,
    ModelSynthesisNote,
)
from . import integrity, parsing

REPOSITORY = "mesuef1974/analytic-number-theory-encyclopedia-ar"


@dataclass(frozen=True, slots=True)
class EncyclopediaImportSummary:
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


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_revision(root: Path) -> str:
    """مراجعة Git للمصدر، أو علامة صريحة عند تعذّر تحديدها."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "LOCAL-UNRESOLVED"


def _clear(session: Session) -> None:
    for model in (
        IntegrityFinding,
        ModelSynthesisNote,
        BibliographyEntry,
        EncyclopediaResult,
        EncyclopediaUnit,
        EncyclopediaChapter,
    ):
        session.execute(delete(model))


def import_encyclopedia(
    session: Session,
    *,
    repository_root: Path,
    claims: list[dict] | None = None,
) -> EncyclopediaImportSummary:
    root = repository_root.expanduser().resolve()
    chapters = parsing.read_chapters(root)
    registries = parsing.parse_registries(root)
    policy = parsing.parse_policy(root)
    bibliography = parsing.parse_bib(root)
    cited = parsing.cite_keys(root)
    notes = parsing.parse_model_notes()
    revision = git_revision(root)

    findings = integrity.run_checks(
        chapters, registries, policy, bibliography, cited, claims or []
    )
    citable_by_key = {
        result["result_id"]: parsing.registry_citable(
            registries.get(result["result_id"], [])
        )
        for chapter in chapters
        for result in chapter["results"]
        if result["result_id"]
    }
    integrity.check_model_notes(
        notes,
        {key: {"citable": int(value)} for key, value in citable_by_key.items()},
        lambda code, severity, subject, detail: findings.append(
            {
                "code": code,
                "severity": severity,
                "subject": subject,
                "detail": detail,
            }
        ),
    )

    _clear(session)

    unit_count = result_count = 0
    for chapter in chapters:
        row = EncyclopediaChapter(
            number=chapter["number"],
            title=chapter["title"],
            volume=chapter["volume"] or None,
            tex_paths=json.dumps(chapter["files"], ensure_ascii=False),
            char_count=chapter["char_count"],
            revision=revision,
        )
        session.add(row)
        session.flush()

        for ordinal, (heading, body) in enumerate(chapter["sections"], start=1):
            blocks = parsing.parse_blocks(body)
            text = parsing.blocks_text(blocks)
            if not text:
                continue
            session.add(
                EncyclopediaUnit(
                    chapter_id=row.id,
                    ordinal=ordinal,
                    heading=heading or None,
                    text=text,
                    search_text=parsing.normalize_ar(
                        f"{heading or ''}\n{parsing.blocks_text(blocks, math=False)}"
                    ),
                    blocks_json=json.dumps(blocks, ensure_ascii=False),
                    text_sha256=_sha256(text),
                )
            )
            unit_count += 1

        for result in chapter["results"]:
            key = result["result_id"]
            if not key:
                continue
            entries = registries.get(key, [])
            statuses = parsing.registry_status(entries)
            session.add(
                EncyclopediaResult(
                    result_key=key,
                    kind=result["kind"],
                    title=result["title"] or None,
                    chapter_number=result["chapter"],
                    tex_status=result["tex_status"],
                    registry_status="/".join(sorted(statuses)) or None,
                    registry_files="، ".join(sorted({e[3] for e in entries})) or None,
                    source_note=(entries[0][2] if entries else None),
                    citable=bool(citable_by_key.get(key)),
                    label=result["label"],
                    statement=result["statement"],
                    tex_path=result["tex_path"],
                )
            )
            result_count += 1

    known_keys = parsing.bib_keys(bibliography)
    for key, entry in bibliography.items():
        aliases = entry.get("aliases") or []
        session.add(
            BibliographyEntry(
                entry_key=key,
                entry_type=entry["entry_type"],
                title=entry["title"] or None,
                author=entry["author"] or None,
                year=entry["year"] or None,
                journal=entry["journal"] or None,
                doi=entry["doi"] or None,
                url=entry["url"] or None,
                aliases="، ".join(aliases) or None,
                bib_file=entry["bib_file"],
                cited=key in cited or any(alias in cited for alias in aliases),
            )
        )

    for note in notes:
        blocks = parsing.parse_blocks(note["body"])
        body = parsing.blocks_text(blocks)
        session.add(
            ModelSynthesisNote(
                note_key=note["note_id"],
                title=note["title"],
                kind=note["kind"],
                domain=note["domain"] or None,
                anchors="، ".join(note["anchors"]) or None,
                literature_hint=note["literature_hint"] or None,
                is_gap=note["gap"] in ("yes", "partial"),
                body=body,
                search_text=parsing.normalize_ar(
                    f"{note['title']}\n{parsing.blocks_text(blocks, math=False)}"
                ),
                blocks_json=json.dumps(blocks, ensure_ascii=False),
                source_file=note["source_file"],
            )
        )

    for finding in findings:
        session.add(
            IntegrityFinding(
                code=finding["code"],
                severity=finding["severity"],
                subject=finding["subject"],
                detail=finding["detail"],
            )
        )

    session.commit()
    return EncyclopediaImportSummary(
        repository=REPOSITORY,
        revision=revision,
        chapter_count=len(chapters),
        unit_count=unit_count,
        result_count=result_count,
        citable_count=sum(1 for value in citable_by_key.values() if value),
        bibliography_count=len(bibliography),
        model_note_count=len(notes),
        coverage_gap_count=sum(
            1 for note in notes if note["gap"] in ("yes", "partial")
        ),
        finding_count=len(findings),
    )
