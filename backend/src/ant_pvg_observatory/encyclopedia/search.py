"""بحث موحّد عبر طبقات المصادر الثلاث.

يستعمل الفهرس النصي FTS5 على النص المطبَّع للموسوعة ولطبقة المعرفة المعيارية.
هذا ممكن لأن مصدر LaTeX نظيف الفواصل؛ أما صفحات PDF المستخرجة فتُبحث بمسح خطي
في ``..search`` لأن نصها العربي يأتي ملتصقًا بلا مسافات فلا يقبل التجزيء.

الفهرس بمحتوى خارجي: لا يُحذف منه مباشرةً — يُفرَّغ بـ ``delete-all`` ثم يُعاد
بناؤه، وإلا خرج عن مزامنة جدول المحتوى وأنتج قاعدة تالفة.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import SourceLayer
from .parsing import normalize_ar

_FTS_TABLES = {
    "encyclopedia_units_fts": ("encyclopedia_units", "search_text"),
    "model_synthesis_notes_fts": ("model_synthesis_notes", "search_text"),
}


@dataclass(frozen=True, slots=True)
class UnifiedSearchResult:
    layer: SourceLayer
    kind: str
    key: str
    title: str
    snippet: str
    chapter_number: int | None = None
    citable: bool = False
    is_gap: bool = False
    rank: float = 0.0


@dataclass(frozen=True, slots=True)
class UnifiedSearchResponse:
    query: str
    total: int
    results: list[UnifiedSearchResult]


def ensure_fts(session: Session) -> None:
    """ينشئ جداول الفهرس إن غابت. لا مُشغّلات: يُعاد البناء بعد كل استيراد."""
    for fts, (content, column) in _FTS_TABLES.items():
        session.execute(
            text(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS {fts} USING fts5("
                f"{column}, content='{content}', content_rowid='id',"
                " tokenize=\"unicode61 remove_diacritics 2\")"
            )
        )


def rebuild_fts(session: Session) -> None:
    """يعيد بناء الفهرس من جداول المحتوى بعد الاستيراد."""
    ensure_fts(session)
    for fts in _FTS_TABLES:
        session.execute(text(f"INSERT INTO {fts}({fts}) VALUES('delete-all')"))
        session.execute(text(f"INSERT INTO {fts}({fts}) VALUES('rebuild')"))
    session.commit()


def _match_expression(query: str) -> str:
    tokens = re.findall(r"[\w؀-ۿ]+", normalize_ar(query))
    return " ".join(f'"{token}"' for token in tokens)


def _snippet(body: str, query: str, width: int = 420) -> str:
    haystack, needle = normalize_ar(body), normalize_ar(query)
    position = haystack.find(needle)
    if position < 0:
        for token in needle.split():
            position = haystack.find(token)
            if position >= 0:
                break
    if position < 0:
        return body[:width]
    start = max(0, position - width // 3)
    prefix = "…" if start else ""
    return f"{prefix}{body[start:position + width]}…"


def search_corpus(
    session: Session,
    *,
    query: str,
    source_layer: SourceLayer | None = None,
    limit: int = 40,
) -> UnifiedSearchResponse:
    match = _match_expression(query)
    if not match:
        return UnifiedSearchResponse(query=query, total=0, results=[])

    ensure_fts(session)
    results: list[UnifiedSearchResult] = []

    if source_layer in (None, SourceLayer.ENCYCLOPEDIA):
        rows = session.execute(
            text(
                "SELECT u.id, u.heading, u.text, c.number, c.title,"
                "       bm25(encyclopedia_units_fts) AS rank"
                "  FROM encyclopedia_units_fts f"
                "  JOIN encyclopedia_units u ON u.id = f.rowid"
                "  JOIN encyclopedia_chapters c ON c.id = u.chapter_id"
                " WHERE encyclopedia_units_fts MATCH :match"
                " ORDER BY rank LIMIT :limit"
            ),
            {"match": match, "limit": limit},
        ).all()
        for row in rows:
            results.append(
                UnifiedSearchResult(
                    layer=SourceLayer.ENCYCLOPEDIA,
                    kind="unit",
                    key=str(row[0]),
                    title=f"الفصل {row[3]} — {row[1] or row[4]}",
                    snippet=_snippet(row[2], query),
                    chapter_number=row[3],
                    rank=float(row[5]),
                )
            )

        like = f"%{query}%"
        for row in session.execute(
            text(
                "SELECT result_key, title, statement, chapter_number, citable"
                "  FROM encyclopedia_results"
                " WHERE result_key LIKE :like OR title LIKE :like"
                "    OR statement LIKE :like"
                " ORDER BY chapter_number, result_key LIMIT :limit"
            ),
            {"like": like, "limit": limit},
        ).all():
            results.append(
                UnifiedSearchResult(
                    layer=SourceLayer.ENCYCLOPEDIA,
                    kind="result",
                    key=row[0],
                    title=f"{row[0]} — {row[1] or ''}".strip(" —"),
                    snippet=(row[2] or "")[:400],
                    chapter_number=row[3],
                    citable=bool(row[4]),
                )
            )

    if source_layer in (None, SourceLayer.MODEL_SYNTHESIS):
        for row in session.execute(
            text(
                "SELECT n.note_key, n.title, n.body, n.is_gap,"
                "       bm25(model_synthesis_notes_fts) AS rank"
                "  FROM model_synthesis_notes_fts f"
                "  JOIN model_synthesis_notes n ON n.id = f.rowid"
                " WHERE model_synthesis_notes_fts MATCH :match"
                " ORDER BY rank LIMIT :limit"
            ),
            {"match": match, "limit": limit},
        ).all():
            results.append(
                UnifiedSearchResult(
                    layer=SourceLayer.MODEL_SYNTHESIS,
                    kind="model_note",
                    key=row[0],
                    title=f"{row[0]} — {row[1]}",
                    snippet=_snippet(row[2], query),
                    is_gap=bool(row[3]),
                    citable=False,  # هذه الطبقة لا يُستشهد بها بحال
                    rank=float(row[4]),
                )
            )

    if source_layer in (None, SourceLayer.LITERATURE):
        like = f"%{query}%"
        for row in session.execute(
            text(
                "SELECT entry_key, author, year, title, journal"
                "  FROM bibliography_entries"
                " WHERE entry_key LIKE :like OR title LIKE :like OR author LIKE :like"
                " ORDER BY entry_key LIMIT :limit"
            ),
            {"like": like, "limit": limit},
        ).all():
            results.append(
                UnifiedSearchResult(
                    layer=SourceLayer.LITERATURE,
                    kind="bibliography",
                    key=row[0],
                    title=row[0],
                    snippet=f"{row[1] or ''} ({row[2] or ''}). {row[3] or ''}. "
                    f"{row[4] or ''}".strip(),
                )
            )

    return UnifiedSearchResponse(
        query=query, total=len(results), results=results[:limit]
    )
