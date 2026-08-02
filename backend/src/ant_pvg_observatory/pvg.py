"""قراءة مدونة بحث PVG وحوكمة نتائجها.

هذه الطبقة الرابعة، وسلطتها ``INTERNAL_UNPUBLISHED``. لا تُوضع في
``ENCYCLOPEDIA`` لأن تلك محكومة بسياسة اعتماد ومراجعة مستقلة، ولا في
``LITERATURE`` لأنها غير منشورة، ولا في ``MODEL_SYNTHESIS`` لأنها ليست
مولَّدة بل بحث المؤلف.

المدونة تحمل مفردات حالة خاصة بها، والأهم أن بعضها **ليس برهانًا**: الأرشيف
نفسه يقول «لا يحل الفحص محل البرهان». فالمرصد يفرض ذلك بدل أن يرجوه.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .encyclopedia.parsing import blocks_text, normalize_ar, parse_blocks

PVG_DIR = Path(__file__).resolve().parents[3] / "knowledge" / "pvg"
VISUALS_DIR = Path(__file__).resolve().parents[3] / "static" / "pvg"

#: معرّفات نتائج PVG: PVG-FND-01، PVFC-07، ADD-03.
RESULT_KEY = re.compile(r"\b(PVG-[A-Z]+-\d+|PVFC-\d+|ADD-\d+)\b")

#: حالات تعني أن النتيجة مبرهنة، فيجوز الاستناد إليها داخليًا.
PROVEN_MARKERS = frozenset({"PROVED", "IDENTITY", "REFORMULATION"})

#: حالات صريحة بأنها ليست برهانًا. الأرشيف يعلنها بنفسه.
NOT_A_PROOF = frozenset({
    "FINITE-VERIFIED",
    "INTERPRETATION",
    "HYPOTHESIS",
    "OPEN",
    "REJECTED",
    "FORMALLY-DERIVED",
    "CONJECTURAL",
})


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def status_tokens(status: str | None) -> list[str]:
    """يفكّ الحالة المركّبة إلى وسومها. المطابقة على الوسم لا على النص:

    ``INTERPRETATION`` سلسلة فرعية من ``REINTERPRETATION``، فالمطابقة النصية
    تصنّف ``PROVED/REINTERPRETATION`` غيرَ مبرهنة وهي مبرهنة.
    """
    if not status:
        return []
    return [t for t in re.split(r"[/\s]+", status.upper()) if t]


def is_proven(status: str | None) -> bool:
    """هل الحالة تعني برهانًا؟

    ``FORMALLY-DERIVED`` اشتقاق رمزي مشروط بإطار، و``FINITE-VERIFIED`` فحص
    حاسوبي في مجال منتهٍ. كلاهما قيّم، وكلاهما ليس برهانًا — وهذا نصّ الأرشيف
    لا تشدُّدًا من المرصد.
    """
    tokens = status_tokens(status)
    if not tokens:
        return False
    if any(token in NOT_A_PROOF for token in tokens):
        return False
    return any(token in PROVEN_MARKERS for token in tokens)


def _registry_rows(text: str) -> list[dict]:
    rows, headers = [], None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            headers = None
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if headers is None:
            headers = cells
            continue
        key = RESULT_KEY.fullmatch(cells[0].strip("`"))
        if not key:
            continue
        status = None
        for cell in cells[1:]:
            match = re.fullmatch(r"`([A-Z][A-Z /-]+)`", cell)
            if match:
                status = match.group(1).strip()
        rows.append(
            {
                "result_key": key.group(1),
                "statement": cells[1] if len(cells) > 1 else None,
                "status": status,
            }
        )
    return rows


def parse_corpus(directory: Path | None = None) -> dict:
    """يقرأ مستندات PVG ونتائجها المعرَّفة.

    المستندات تُفكَّك بالمحلل نفسه الذي يقرأ الموسوعة، فتُحفظ المعادلات
    والبنية ويُصيَّر النص بالطريقة نفسها.
    """
    directory = Path(directory or PVG_DIR)
    if not directory.is_dir():
        return {"documents": [], "results": [], "manifest": []}

    documents, results, seen = [], [], set()
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = ""
        heading = re.search(r"^#\s+(.+)$", text, re.M)
        if heading:
            title = heading.group(1).strip()
        blocks = parse_blocks(text)
        body = blocks_text(blocks)
        documents.append(
            {
                "slug": path.stem,
                "title": title or path.stem,
                "body": body,
                "search_text": normalize_ar(f"{title}\n{blocks_text(blocks, math=False)}"),
                "blocks_json": json.dumps(blocks, ensure_ascii=False),
                "sha256": _sha256(text),
                "char_count": len(text),
                "mentioned_keys": sorted(set(RESULT_KEY.findall(text))),
            }
        )
        for row in _registry_rows(text):
            if row["result_key"] in seen:
                continue
            seen.add(row["result_key"])
            results.append({**row, "source_file": path.name})

    manifest_path = directory / "MANIFEST.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else []
    )
    return {"documents": documents, "results": results, "manifest": manifest}


def verify_manifest(directory: Path | None = None) -> list[dict]:
    """يقارن بصمات MANIFEST.json بالملفات الفعلية.

    الأرشيف يحمل بصمته بنفسه؛ تجاهلها إهدارٌ لضمانة موجودة.
    """
    directory = Path(directory or PVG_DIR)
    manifest_path = directory / "MANIFEST.json"
    if not manifest_path.is_file():
        return []
    findings = []
    for entry in json.loads(manifest_path.read_text(encoding="utf-8")):
        path = directory / entry["file"]
        if not path.is_file():
            findings.append({"file": entry["file"], "issue": "MISSING"})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            findings.append(
                {"file": entry["file"], "issue": "DIGEST-MISMATCH",
                 "expected": entry["sha256"][:12], "actual": digest[:12]}
            )
    return findings


def list_visuals(directory: Path | None = None) -> list[dict]:
    """المرئيات التفاعلية. مستقلة تمامًا وتعمل دون اتصال، فتُقدَّم كما هي."""
    directory = Path(directory or VISUALS_DIR)
    if not directory.is_dir():
        return []
    return [
        {"name": path.name, "url": f"/pvg/{path.name}", "bytes": path.stat().st_size}
        for path in sorted(directory.glob("*.html"))
    ]


def check_corpus(corpus: dict, manifest_findings: list[dict], add) -> None:
    """فحوص مدونة PVG."""
    for finding in manifest_findings:
        add(
            "PVG_MANIFEST_MISMATCH", "HIGH", finding["file"],
            f"بصمة الملف لا تطابق MANIFEST.json ({finding['issue']}).",
        )

    known = {row["result_key"] for row in corpus["results"]}
    for result in corpus["results"]:
        if not result["status"]:
            add(
                "PVG_RESULT_STATUS_MISSING", "MEDIUM", result["result_key"],
                "نتيجة في السجل بلا حالة قابلة للقراءة الآلية.",
            )
        elif not is_proven(result["status"]):
            add(
                "PVG_RESULT_NOT_A_PROOF", "INFO", result["result_key"],
                f"الحالة «{result['status']}» ليست برهانًا؛ "
                "لا يجوز الاستناد إليها في ادعاء موثق.",
            )

    mentioned: set[str] = set()
    for document in corpus["documents"]:
        mentioned |= set(document["mentioned_keys"])
    for key in sorted(mentioned - known):
        add(
            "PVG_RESULT_UNREGISTERED", "MEDIUM", key,
            "معرّف مذكور في المدونة ولا سطر له في سجل النتائج.",
        )


def import_pvg_corpus(session) -> dict:
    """يستوعب مدونة PVG ويعيد حصيلتها.

    متكافئ التنفيذ: يمسح ثم يعيد البناء، فإعادة التشغيل على مدونة لم تتغير
    تعطي الحالة نفسها.
    """
    from sqlalchemy import delete

    from .models import PvgDocument, PvgResult

    corpus = parse_corpus()
    manifest_findings = verify_manifest()

    session.execute(delete(PvgResult))
    session.execute(delete(PvgDocument))
    for document in corpus["documents"]:
        session.add(
            PvgDocument(
                slug=document["slug"],
                title=document["title"],
                body=document["body"],
                search_text=document["search_text"],
                blocks_json=document["blocks_json"],
                sha256=document["sha256"],
                char_count=document["char_count"],
            )
        )
    for result in corpus["results"]:
        session.add(
            PvgResult(
                result_key=result["result_key"],
                statement=result["statement"],
                status=result["status"],
                is_proven=is_proven(result["status"]),
                source_file=result["source_file"],
            )
        )
    session.commit()
    return {
        "document_count": len(corpus["documents"]),
        "result_count": len(corpus["results"]),
        "proven_count": sum(
            1 for r in corpus["results"] if is_proven(r["status"])
        ),
        "manifest_entries": len(corpus["manifest"]),
        "manifest_mismatches": len(manifest_findings),
        "visual_count": len(list_visuals()),
    }
