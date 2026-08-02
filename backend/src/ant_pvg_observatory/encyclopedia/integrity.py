"""فحوص تكامل مستودع الموسوعة.

تقارن حالة كل نتيجة بين وسم المخطوط وسجلات النتائج وسياسة الاعتماد، وتتحقق
من الاستشهادات الببليوغرافية ومن إسنادات طبقة المعرفة المعيارية. لا تعرف
قاعدة بيانات: تُرجع قائمة ملاحظات، ويتولى مستدعيها تخزينها.
"""
import collections
import re

from .parsing import MODEL_KINDS, bib_keys, policy_base, registry_citable, registry_status


def check_model_notes(notes, results_by_id, add):
    """فحوص طبقة المعرفة المعيارية.

    الغرض مزدوج: ضمان أن كل إسناد إلى الموسوعة صحيح، وتحويل الملاحظات غير
    المسنَدة إلى قائمة فجوات تغطية مرشَّحة بدل تركها معلَّقة.
    """
    seen = set()
    for n in notes:
        if n['note_id'] in seen:
            add('MODEL_NOTE_DUPLICATE_ID', 'HIGH', n['note_id'],
                f"معرّف ملاحظة مكرر في {n['source_file']}.")
        seen.add(n['note_id'])
        if n['kind'] not in MODEL_KINDS:
            add('MODEL_NOTE_KIND_UNKNOWN', 'LOW', n['note_id'],
                f"نوع الملاحظة {n['kind']} خارج المفردات المعتمدة.")
        for a in n['anchors']:
            r = results_by_id.get(a)
            if not r:
                add('MODEL_NOTE_ANCHOR_UNKNOWN', 'HIGH', n['note_id'],
                    f'الملاحظة تُسنِد إلى {a} وهو غير موجود في سجل نتائج الموسوعة.')
            elif not r['citable']:
                add('MODEL_NOTE_ANCHOR_NONCITABLE', 'MEDIUM', n['note_id'],
                    f'الملاحظة تُسنِد إلى {a} وحالته لا تسمح بالاستشهاد؛ '
                    'الإسناد صالح للتوجيه لا للاعتماد.')
        if n['gap'] in ('yes', 'partial'):
            add('MODEL_NOTE_COVERAGE_GAP', 'INFO', n['note_id'],
                ('فجوة تغطية كاملة: ' if n['gap'] == 'yes' else 'تغطية جزئية: ')
                + n['title'])
        elif not n['anchors']:
            add('MODEL_NOTE_UNANCHORED', 'LOW', n['note_id'],
                'ملاحظة بلا إسناد إلى الموسوعة وغير موسومة فجوةً؛ تحتاج مراجعة.')


def run_checks(chapters, registries, policy, bib, cited, claims):
    f = []
    undeclared = collections.Counter()

    def add(code, sev, subject, detail):
        f.append({'code': code, 'severity': sev, 'subject': subject, 'detail': detail})

    tex_results = [r for ch in chapters for r in ch['results'] if r['result_id']]
    tex_ids = {r['result_id'] for r in tex_results}

    for rid in sorted(tex_ids - set(registries)):
        add('TEX_ID_NOT_IN_REGISTRY', 'HIGH', rid,
            'المعرّف يظهر في المخطوط ولا يوجد له سطر في أي سجل نتائج، '
            'فهو غير قابل للاستشهاد بحسب قاعدة الاعتماد الخارجي.')
    for rid in sorted(set(registries) - tex_ids):
        add('REGISTRY_ID_NOT_IN_TEX', 'MEDIUM', rid,
            'المعرّف مسجَّل في سجل النتائج ولا يقابله \\resultid في المخطوط.')

    for rid, entries in sorted(registries.items()):
        base = registry_status(entries)
        bases = {frozenset(policy_base(st, policy)) for st, _, _, _ in entries if st}
        if len(bases - {frozenset()}) > 1:
            add('REGISTRY_STATUS_CONFLICT', 'CRITICAL', rid,
                'حالة متضاربة بين السجلات: ' +
                '، '.join(f'{st} في {fn}' for st, _, _, fn in entries if st))
        for st, _, _, fn in entries:
            if not st:
                add('REGISTRY_STATUS_ABSENT', 'MEDIUM', rid,
                    f'سطر السجل في {fn} لا يحمل حالة علمية قابلة للقراءة الآلية.')
            elif policy and not policy_base(st, policy):
                add('STATUS_NOT_IN_POLICY', 'MEDIUM', rid,
                    f'الحالة {st} في {fn} لا تتضمن أي حالة من الحالات الخمس '
                    'المعرَّفة في سياسة اعتماد النتائج.')
            for tok in (t.strip() for t in (st or '').split('/')):
                if tok and policy and tok not in policy:
                    undeclared[tok] += 1

    by_id = {}
    for r in tex_results:
        by_id.setdefault(r['result_id'], r)
    for rid, r in sorted(by_id.items()):
        raw = '/'.join(sorted(registry_status(registries.get(rid, []))))
        base = policy_base(raw, policy)
        if r['tex_status'] and base and r['tex_status'] not in base:
            add('TEX_REGISTRY_STATUS_MISMATCH', 'HIGH', rid,
                f"وسم المخطوط {r['tex_status']} يناقض حالة السجل {raw}")
        if r['result_id'] and not r['tex_status']:
            add('TEX_STATUS_MISSING', 'LOW', rid,
                'النتيجة تحمل معرّفًا في المخطوط بلا وسم حالة صريح.')

    known = bib_keys(bib)
    for k in sorted(cited - known):
        add('CITE_KEY_MISSING', 'HIGH', k,
            'مفتاح استشهاد مستعمل في المخطوط ولا يقابله مدخل ولا مرادف في أي ملف .bib.')
    alias_of = {a: k for k, e in bib.items() for a in (e.get('aliases') or [])}
    for k in sorted(set(bib) - cited):
        if any(a in cited for a in (bib[k].get('aliases') or [])):
            continue
        add('BIB_UNCITED', 'INFO', k,
            'مدخل ببليوغرافي غير مستشهد به صراحة (يظهر عبر \\nocite{*} فقط).')
    for a in sorted(cited & set(alias_of)):
        add('CITE_KEY_ALIAS_USED', 'LOW', a,
            f'المخطوط يستشهد بمفتاح مرادف يحلّه biber إلى {alias_of[a]}؛ '
            'صحيح لكن توحيد المفتاح أوضح.')

    for c in claims:
        for rid in set(re.findall(r'ANT-[A-Z]+-\d+-\d+',
                                  ' '.join(str(c.get(k) or '') for k in
                                           ('evidence', 'dependencies', 'literature_matches')))):
            entries = registries.get(rid, [])
            if not entries:
                add('CLAIM_CITES_UNKNOWN_RESULT', 'CRITICAL', c['claim_id'],
                    f'الادعاء يستند إلى {rid} وهو غير موجود في سجل النتائج.')
            elif not registry_citable(entries):
                add('CLAIM_CITES_NONCITABLE', 'CRITICAL', c['claim_id'],
                    f'الادعاء يستند إلى {rid} وحالته ' +
                    ('/'.join(sorted(registry_status(entries))) or 'غير محددة') +
                    ' وهي لا تسمح بالاستشهاد الخارجي.')

    for tok, n in sorted(undeclared.items(), key=lambda kv: -kv[1]):
        add('UNDECLARED_STATUS_VOCABULARY', 'INFO', tok,
            f'وسم حالة مستعمل {n} مرة في السجلات وغير موصوف في '
            'docs/RESULT_STATUS_POLICY.md.')
    return f

