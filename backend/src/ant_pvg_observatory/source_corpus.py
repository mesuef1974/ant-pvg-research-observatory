from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import SourceFile, SourceLayer, SourceSection

_INPUT_PATTERN = re.compile(r"\\input\{([^}]+)\}")
_HEADING_PATTERN = re.compile(
    r"^\s*\\(?P<kind>chapter|section|subsection|subsubsection)\*?\{(?P<title>.*)\}\s*$"
)
_REPOSITORY = "mesuef1974/analytic-number-theory-encyclopedia-ar"


@dataclass(frozen=True, slots=True)
class SourceImportSummary:
    repository: str
    revision: str
    file_count: int
    section_count: int


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_revision(root: Path) -> str:
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


def _chapter_paths(root: Path) -> list[Path]:
    main_path = root / "manuscript" / "main.tex"
    if not main_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected directory does not contain manuscript/main.tex.",
        )

    main_text = main_path.read_text(encoding="utf-8")
    paths: list[Path] = []
    for match in _INPUT_PATTERN.finditer(main_text):
        relative = Path(match.group(1))
        if relative.as_posix() == "manuscript/preamble":
            continue
        candidate = root / relative
        if candidate.suffix == "":
            candidate = candidate.with_suffix(".tex")
        if candidate.is_file():
            paths.append(candidate)
    return paths


def _sections(text: str) -> list[tuple[str, str, int, int, str]]:
    lines = text.splitlines()
    headings: list[tuple[str, str, int]] = []
    for number, line in enumerate(lines, start=1):
        match = _HEADING_PATTERN.match(line)
        if match:
            headings.append((match.group("kind"), match.group("title").strip(), number))

    if not headings:
        return [("file", "النص الكامل", 1, max(len(lines), 1), text)]

    sections: list[tuple[str, str, int, int, str]] = []
    for index, (kind, title, start_line) in enumerate(headings):
        end_line = headings[index + 1][2] - 1 if index + 1 < len(headings) else len(lines)
        section_text = "\n".join(lines[start_line - 1 : end_line]).strip()
        sections.append((kind, title, start_line, end_line, section_text))
    return sections


def import_encyclopedia_source(
    session: Session,
    *,
    repository_root: Path,
) -> SourceImportSummary:
    root = repository_root.expanduser().resolve()
    chapter_paths = _chapter_paths(root)
    if not chapter_paths:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No chapter files referenced by manuscript/main.tex were found.",
        )

    revision = _git_revision(root)
    session.execute(delete(SourceSection))
    session.execute(delete(SourceFile))

    section_count = 0
    for order_index, path in enumerate(chapter_paths, start=1):
        text = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(root).as_posix()
        source_file = SourceFile(
            repository=_REPOSITORY,
            revision=revision,
            path=relative_path,
            order_index=order_index,
            sha256=_sha256(text),
            line_count=len(text.splitlines()),
            text=text,
            source_layer=SourceLayer.ENCYCLOPEDIA,
        )
        session.add(source_file)
        session.flush()

        for kind, title, start_line, end_line, section_text in _sections(text):
            session.add(
                SourceSection(
                    source_file_id=source_file.id,
                    heading_type=kind,
                    title=title,
                    start_line=start_line,
                    end_line=end_line,
                    text=section_text,
                    text_sha256=_sha256(section_text),
                )
            )
            section_count += 1

    session.commit()
    return SourceImportSummary(
        repository=_REPOSITORY,
        revision=revision,
        file_count=len(chapter_paths),
        section_count=section_count,
    )


def list_source_files(session: Session) -> list[SourceFile]:
    return list(session.scalars(select(SourceFile).order_by(SourceFile.order_index)))
