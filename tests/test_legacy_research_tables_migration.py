"""انحدار: ترقية قاعدة MVP الموروثة لا تفقد الادعاءات ولا البوابات.

المعمارية تشترط أن أي هجرة تمسّ بيانات MVP الموروثة تحمل اختبار انحدار.
والسبب المباشر هنا واقعة: الهجرة 0001 تتبنّى الجداول **بالاسم لا بالشكل**،
فبقيت قواعد الإصدار الأول تحمل ``claims(claim_id)`` و``literature_gates(gate_id)``
ولم يكتشف ذلك شيء حتى استُعملت تلك الجداول فعلًا.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# مخطط الإصدار الأول كما كان في الخادم القياسي المسحوب.
LEGACY_SCHEMA = """
CREATE TABLE claims(
 id INTEGER PRIMARY KEY, claim_id TEXT UNIQUE NOT NULL, statement TEXT NOT NULL,
 domain TEXT, source_layer TEXT NOT NULL, status TEXT NOT NULL,
 evidence TEXT, dependencies TEXT, literature_matches TEXT,
 novelty_status TEXT, last_reviewed TEXT, created_at TEXT NOT NULL);
CREATE TABLE literature_gates(
 id INTEGER PRIMARY KEY, gate_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
 question TEXT NOT NULL, status TEXT NOT NULL, keywords TEXT,
 scope TEXT, verdict TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE gate_references(
 gate_id INTEGER, reference_id INTEGER, relation TEXT, coverage TEXT,
 PRIMARY KEY(gate_id, reference_id));
CREATE TABLE links(
 id INTEGER PRIMARY KEY, from_type TEXT, from_id TEXT, relation TEXT,
 to_type TEXT, to_id TEXT, note TEXT);
"""


def _upgrade(database: Path) -> None:
    environment = os.environ.copy()
    environment["ANT_PVG_DATABASE_URL"] = f"sqlite:///{database.as_posix()}"
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def legacy_database(tmp_path: Path) -> Path:
    database = tmp_path / "observatory.db"
    with sqlite3.connect(database) as connection:
        connection.executescript(LEGACY_SCHEMA)
        connection.execute(
            "INSERT INTO claims(claim_id, statement, domain, source_layer, status,"
            " evidence, dependencies, literature_matches, novelty_status,"
            " last_reviewed, created_at)"
            " VALUES('CLAIM-0001', 'عبارة الادعاء', 'PVFC', 'LITERATURE',"
            " 'KNOWN-IN-EQUIVALENT-FORM', 'دليل', 'تبعية', 'مطابقة', 'NOT-NOVEL',"
            " '2026-01-01', '2026-01-01')"
        )
        connection.execute(
            "INSERT INTO literature_gates(gate_id, title, question, status,"
            " keywords, scope, verdict, created_at, updated_at)"
            " VALUES('GATE-0001', 'عنوان البوابة', 'السؤال البحثي', 'OPEN',"
            " 'كلمات', 'نطاق', 'REVIEW-IN-PROGRESS', '2026-01-01', '2026-01-01')"
        )
    return database


def test_legacy_claims_survive_the_upgrade(legacy_database: Path) -> None:
    _upgrade(legacy_database)

    with sqlite3.connect(legacy_database) as connection:
        row = connection.execute(
            "SELECT claim_key, statement, source_layer, status, evidence_note,"
            "       novelty_note FROM claims"
        ).fetchone()

    assert row[0] == "CLAIM-0001"
    assert row[1] == "عبارة الادعاء"
    assert row[2] == "LITERATURE"
    assert row[3] == "KNOWN_EQUIVALENT"
    # المجال والتبعيات والمطابقات لا موضع لها في المخطط الحالي، فتُحفظ في الدليل
    assert "دليل" in row[4] and "PVFC" in row[4] and "تبعية" in row[4]
    assert row[5] == "NOT-NOVEL"


def test_legacy_gates_survive_with_their_scope_and_keywords(
    legacy_database: Path,
) -> None:
    _upgrade(legacy_database)

    with sqlite3.connect(legacy_database) as connection:
        row = connection.execute(
            "SELECT gate_key, title, research_question, status, verdict"
            "  FROM literature_gates"
        ).fetchone()

    assert row[0] == "GATE-0001"
    assert row[1] == "عنوان البوابة"
    assert "السؤال البحثي" in row[2]
    # فقدُهما صامتين أسوأ من إبقائهما في غير موضعهما تمامًا
    assert "نطاق" in row[2] and "كلمات" in row[2]
    assert row[3] == "OPEN"
    assert row[4] == "REVIEW-IN-PROGRESS"


def test_legacy_link_tables_are_replaced_by_the_current_shape(
    legacy_database: Path,
) -> None:
    _upgrade(legacy_database)

    with sqlite3.connect(legacy_database) as connection:
        gate_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(gate_references)")
        }
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert "coverage_note" in gate_columns and "coverage" not in gate_columns
    assert "knowledge_links" in tables
    assert "links" not in tables
    # لا بقايا من جداول التبنّي المؤقتة
    assert not {t for t in tables if t.endswith("_legacy_mvp")}


def test_a_populated_legacy_link_table_refuses_to_be_dropped(tmp_path: Path) -> None:
    """الإسقاط مشروط بخلوّ الجدول، ولا يُفترض الخلوّ افتراضًا."""
    database = tmp_path / "observatory.db"
    with sqlite3.connect(database) as connection:
        connection.executescript(LEGACY_SCHEMA)
        connection.execute(
            "INSERT INTO links(from_type, from_id, relation, to_type, to_id)"
            " VALUES('claim', 'CLAIM-0001', 'DEPENDS-ON', 'result', 'ANT-THM-06-01')"
        )

    with pytest.raises(subprocess.CalledProcessError) as failure:
        _upgrade(database)

    assert "يلزم ترحيلها يدويًا" in failure.value.stderr


def test_upgrade_is_repeatable_on_an_already_adopted_database(
    legacy_database: Path,
) -> None:
    _upgrade(legacy_database)
    _upgrade(legacy_database)  # لا يسقط عند إعادة التشغيل

    with sqlite3.connect(legacy_database) as connection:
        assert (
            connection.execute("SELECT count(*) FROM claims").fetchone()[0] == 1
        )
