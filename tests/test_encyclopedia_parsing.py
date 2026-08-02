"""اختبارات وحدة المجال: تحليل LaTeX والسجلات والببليوغرافيا والمعرفة المعيارية.

وحدة نقية لا تلمس قاعدة بيانات، فتُختبر بلا تهيئة ولا تركيبات.
"""

from pathlib import Path

from ant_pvg_observatory.encyclopedia import parsing


def test_normalize_ar_folds_hamza_alef_maqsura_and_diacritics() -> None:
    assert parsing.normalize_ar("الأَعْداد الأوليّة") == parsing.normalize_ar(
        "الاعداد الاوليه"
    )
    assert parsing.normalize_ar("مُبَرْهَنَة") == parsing.normalize_ar("مبرهنه")
    assert "ـ" not in parsing.normalize_ar("مبــرهنة")


def test_parse_blocks_preserves_display_math_and_environments() -> None:
    tex = (
        "نكتب\n"
        "\\[\n\\zeta(s)=\\sum_{n\\ge1}n^{-s}.\n\\]\n"
        "\\begin{theorem}[استمرار زيتا]\n"
        "\\label{thm:x}\n\\resultid{ANT-THM-06-01}\n\\provedhere\n"
        "تمتد \\(\\zeta\\) إلى \\(\\Re(s)>0\\).\n"
        "\\end{theorem}\n"
        "\\begin{proof}\nبرهان قصير.\n\\end{proof}\n"
    )
    blocks = parsing.parse_blocks(tex)
    kinds = [b["t"] for b in blocks]
    assert kinds == ["p", "math", "env", "env"]
    assert "\\zeta(s)" in blocks[1]["tex"]

    theorem = blocks[2]
    assert theorem["env"] == "theorem"
    assert theorem["label"] == "مبرهنة"
    assert theorem["result_id"] == "ANT-THM-06-01"
    assert theorem["status"] == "PROVED-HERE"
    assert theorem["title"] == "استمرار زيتا"
    assert blocks[3]["env"] == "proof"

    # الرياضيات السطرية تبقى كما هي داخل الفقرة
    inner = theorem["blocks"][0]
    assert "\\(\\Re(s)>0\\)" in inner["text"]


def test_parse_blocks_keeps_align_wrapper_so_ampersand_stays_valid() -> None:
    blocks = parsing.parse_blocks(
        "\\begin{align*}\na &= b\\\\\n&= c\n\\end{align*}\n"
    )
    assert blocks[0]["t"] == "math"
    assert blocks[0]["tex"].startswith("\\begin{align*}")
    assert blocks[0]["tex"].endswith("\\end{align*}")


def test_clean_math_strips_index_macros_and_maps_project_macro() -> None:
    cleaned = parsing.clean_math(
        "\\zeta(s)\n\\symbolindex{دالة زيتا}\n\\textenglish{DEFERRED}"
    )
    assert "\\symbolindex" not in cleaned
    assert "\\textenglish" not in cleaned
    assert "\\text{DEFERRED}" in cleaned


def _write_encyclopedia(root: Path) -> None:
    (root / "manuscript").mkdir(parents=True)
    chapters = root / "volumes" / "volume-01" / "chapters"
    chapters.mkdir(parents=True)
    (root / "manuscript" / "main.tex").write_text(
        "\\input{manuscript/preamble}\n"
        "\\input{volumes/volume-01/chapters/chapter-01-alpha}\n"
        "\\input{volumes/volume-01/chapters/chapter-01-alpha-batch-02}\n"
        "\\input{volumes/volume-01/chapters/chapter-09-omega}\n",
        encoding="utf-8",
    )
    (chapters / "chapter-01-alpha.tex").write_text(
        "\\chapter{الفصل الأول}\n\\section{مقدمة}\nنص.\n"
        "\\begin{theorem}\n\\resultid{ANT-THM-01-01}\n\\provedhere\nعبارة.\n"
        "\\end{theorem}\n",
        encoding="utf-8",
    )
    # ملف دفعة بلا \chapter: امتداد للفصل السابق لا فصل جديد
    (chapters / "chapter-01-alpha-batch-02.tex").write_text(
        "\\section{تتمة}\n"
        "\\begin{lemma}\n\\resultid{ANT-LEM-01-01}\n\\citedresult\nعبارة.\n"
        "\\end{lemma}\n",
        encoding="utf-8",
    )
    # الاسم يوحي بالفصل التاسع، والترتيب في main.tex يجعله الثاني
    (chapters / "chapter-09-omega.tex").write_text(
        "\\chapter{الفصل الثاني}\n\\section{خاتمة}\nنص.\n", encoding="utf-8"
    )


def test_read_chapters_merges_batches_and_numbers_by_main_order(tmp_path: Path) -> None:
    root = tmp_path / "enc"
    _write_encyclopedia(root)

    chapters = parsing.read_chapters(root)

    assert [c["number"] for c in chapters] == [1, 2]
    assert [c["title"] for c in chapters] == ["الفصل الأول", "الفصل الثاني"]
    # ملفا الفصل الأول اندمجا، فصار له قسمان ونتيجتان
    assert len(chapters[0]["files"]) == 2
    assert {r["result_id"] for r in chapters[0]["results"]} == {
        "ANT-THM-01-01",
        "ANT-LEM-01-01",
    }
    # رقم الفصل يُشتق من ترتيب main.tex لا من اسم الملف
    assert chapters[1]["number"] == 2
    assert all(r["chapter"] == 1 for r in chapters[0]["results"])


def test_parse_registries_reads_both_table_layouts(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "RESULTS_REGISTRY.md").write_text(
        "| المعرّف | النتيجة | الملف | الحالة | المصدر |\n|---|---|---|---|---|\n"
        "| `ANT-THM-01-01` | عبارة | الفصل 1 | `PROVED-HERE` | برهان داخلي |\n",
        encoding="utf-8",
    )
    (docs / "RESULTS_REGISTRY_CHAPTER_09.md").write_text(
        "| المعرّف | النتيجة | النوع/الحالة | الاعتماد |\n|---|---|---|---|\n"
        "| `ANT-THM-09-01` | عبارة | CITED / EXPLAINED | ACTIVE / CITABLE |\n",
        encoding="utf-8",
    )

    registries = parsing.parse_registries(tmp_path)

    assert parsing.registry_status(registries["ANT-THM-01-01"]) == {"PROVED-HERE"}
    assert parsing.registry_citable(registries["ANT-THM-01-01"]) is True
    # الصيغة الثانية: الحالة نص عارٍ وعمود اعتماد منفصل
    assert parsing.registry_status(registries["ANT-THM-09-01"]) == {"CITED", "EXPLAINED"}
    assert parsing.registry_citable(registries["ANT-THM-09-01"]) is True


def test_parse_bib_reads_biber_ids_aliases(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "bibliography.bib").write_text(
        "@book{Titchmarsh1986,\n"
        "  ids       = {titchmarshHeathBrown1986zeta,titchmarsh1986zeta},\n"
        "  author    = {E. C. Titchmarsh},\n"
        "  title     = {The Theory of the Riemann Zeta-Function},\n"
        "  year      = {1986}\n}\n",
        encoding="utf-8",
    )

    entries = parsing.parse_bib(tmp_path)

    assert entries["Titchmarsh1986"]["author"] == "E. C. Titchmarsh"
    assert "titchmarshHeathBrown1986zeta" in entries["Titchmarsh1986"]["aliases"]
    # المرادف مفتاح مقبول لدى biber، فلا يُعدّ مفقودًا
    assert "titchmarshHeathBrown1986zeta" in parsing.bib_keys(entries)


def test_parse_model_notes_reads_metadata_and_gap_flag(tmp_path: Path) -> None:
    directory = tmp_path / "model_synthesis"
    directory.mkdir()
    (directory / "00-zeta.md").write_text(
        "# المجال: دالة زيتا\n\n"
        "## MS-ZETA-001 — عنوان أول\n"
        "- kind: method\n"
        "- anchors: ANT-THM-06-01, ANT-COR-06-02\n"
        "- literature: Titchmarsh1986\n\n"
        "نص الملاحظة مع \\(\\zeta(s)\\).\n\n"
        "## MS-ZETA-002 — عنوان ثانٍ\n"
        "- kind: gap\n"
        "- gap: yes\n\n"
        "موضوع غير مغطى.\n",
        encoding="utf-8",
    )

    notes = parsing.parse_model_notes(directory)

    assert [n["note_key"] if "note_key" in n else n["note_id"] for n in notes] == [
        "MS-ZETA-001",
        "MS-ZETA-002",
    ]
    assert notes[0]["kind"] == "method"
    assert notes[0]["domain"] == "دالة زيتا"
    assert notes[0]["anchors"] == ["ANT-THM-06-01", "ANT-COR-06-02"]
    assert notes[0]["gap"] == "no"
    assert notes[1]["gap"] == "yes"


def test_shipped_model_notes_are_loadable_and_well_formed() -> None:
    notes = parsing.parse_model_notes()
    assert len(notes) >= 50
    assert all(n["kind"] in parsing.MODEL_KINDS for n in notes)
    keys = [n["note_id"] for n in notes]
    assert len(keys) == len(set(keys))
    assert sum(1 for n in notes if n["gap"] in ("yes", "partial")) >= 10
