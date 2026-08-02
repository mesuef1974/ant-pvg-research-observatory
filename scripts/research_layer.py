#!/usr/bin/env python3
"""تصدير الطبقة البحثية أو استيرادها.

    python scripts/research_layer.py export
    python scripts/research_layer.py import
    python scripts/research_layer.py export --path exports/backup-2026-08.json

التصدير حتمي: تشغيله مرتين على قاعدة لم تتغير يعطي الملف نفسه، فالفروق في
Git تعكس تغيّر البحث لا تغيّر الوقت.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ant_pvg_observatory.db import SessionLocal  # noqa: E402
from ant_pvg_observatory.research_io import (  # noqa: E402
    DEFAULT_EXPORT_PATH,
    read_import,
    write_export,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "import"])
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_EXPORT_PATH,
        help=f"مسار ملف الطبقة البحثية (افتراضيًا {DEFAULT_EXPORT_PATH})",
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        if args.action == "export":
            path, counts = write_export(session, args.path)
            print(f"صُدِّر إلى {path}")
            print(
                f"  ادعاءات: {counts.claims} | بوابات: {counts.gates} | "
                f"مراجع: {counts.references} | روابط بوابات: {counts.gate_references} | "
                f"روابط معرفة: {counts.links}"
            )
        else:
            report = read_import(session, args.path)
            print(f"استُورد من {args.path}")
            for label, counts in (
                ("أُنشئ", report.created),
                ("تغيّر", report.updated),
                ("بلا تغيير", report.unchanged),
            ):
                print(
                    f"  {label:9}: ادعاءات {counts.claims} | بوابات {counts.gates} | "
                    f"مراجع {counts.references} | روابط بوابات {counts.gate_references} | "
                    f"روابط معرفة {counts.links}"
                )
            if report.skipped_links:
                print(
                    f"  تُخُطّي {report.skipped_links} رابط بوابة لغياب طرفه."
                )


if __name__ == "__main__":
    main()
