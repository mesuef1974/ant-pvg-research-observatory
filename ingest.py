#!/usr/bin/env python3
"""استيراد الموسوعة من مستودع المصدر (LaTeX + سجلات النتائج + BibTeX).

المصدر المعتمد هو مستودع `analytic-number-theory-encyclopedia-ar` وليس ملف PDF.
استخراج النص من PDF العربي يعطي نصًا معكوسًا بلا فواصل كلمات، فيتعذر البحث.
أما مصدر LaTeX فهو UTF-8 نظيف ويحمل بنية النتائج ومعرفاتها الثابتة.
"""
import collections, json, os, re, sqlite3, unicodedata
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------- موضع المصدر

DEFAULT_ROOTS = [
    Path(r'D:/analytic-number-theory-encyclopedia-ar'),
    Path(__file__).resolve().parent.parent/'analytic-number-theory-encyclopedia-ar',
]

def encyclopedia_root():
    env = os.environ.get('ANT_ENCYCLOPEDIA_ROOT')
    cands = [Path(env)] if env else []
    cands += DEFAULT_ROOTS
    for p in cands:
        if (p/'manuscript'/'main.tex').exists():
            return p
    raise FileNotFoundError(
        'لم يُعثر على مستودع الموسوعة. حدد المسار في متغير البيئة ANT_ENCYCLOPEDIA_ROOT.')

def now():
    return datetime.now(timezone.utc).isoformat()

# ------------------------------------------------------------ تطبيع نص عربي

_DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED]')

def normalize_ar(s):
    """توحيد الهمزات والألف المقصورة والتاء المربوطة وحذف التشكيل والتطويل.

    يُطبَّق على نص الفهرسة وعلى نص الاستعلام معًا حتى يتطابقا.
    """
    s = unicodedata.normalize('NFKC', s)
    s = _DIACRITICS.sub('', s).replace('\u0640', '')
    s = re.sub('[\u0623\u0625\u0622\u0671]', '\u0627', s)
    s = (s.replace('\u0649', '\u064A')
          .replace('\u0624', '\u0648')
          .replace('\u0626', '\u064A')
          .replace('\u0629', '\u0647'))
    return s.lower()

# ------------------------------------------------------------- تجريد LaTeX

_MATH_MARK = ' [معادلة] '
_DROP_ARG = ('label|resultid|personindex|theoremindex|symbolindex|index'
             '|nocite|citep|citet|cite|ref|eqref|input|include|bibliography')
_MATH_ENVS = 'align\\*?|equation\\*?|gather\\*?|multline\\*?|aligned|cases|pmatrix|bmatrix|tabular|array'

def detex(s):
    """يحوّل مصدر LaTeX إلى نص عادي بلا رياضيات — لحقول الببليوغرافيا.

    نصوص الفصول لا تمر من هنا؛ لها ``parse_blocks`` الذي يحفظ البنية.
    """
    inline = lambda m: ' '
    s = re.sub(r'(?<!\\)%.*', '', s)
    s = re.sub(r'\\(?:' + _DROP_ARG + r')\s*(?:\[[^\]]*\])?\s*\{[^{}]*\}', ' ', s)
    s = re.sub(r'\\\[.*?\\\]', _MATH_MARK, s, flags=re.S)
    s = re.sub(r'\\\(.*?\\\)', inline, s, flags=re.S)
    s = re.sub(r'\$\$.*?\$\$', _MATH_MARK, s, flags=re.S)
    s = re.sub(r'\$[^$]*\$', inline, s)
    s = re.sub(r'\\begin\{(' + _MATH_ENVS + r')\}.*?\\end\{\1\}', _MATH_MARK, s, flags=re.S)
    s = re.sub(r'\\(?:begin|end)\s*\{[^}]*\}(?:\[[^\]]*\])?', ' ', s)
    s = re.sub(r'\\[a-zA-Z]+\*?\s*(?:\[[^\]]*\])?', ' ', s)
    s = re.sub(r'\\[^a-zA-Z]', ' ', s)
    s = s.replace('{', ' ').replace('}', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def _balanced(s, i, op='{', cl='}'):
    """يُرجع (المحتوى, موضع ما بعد القوس المغلق) بدءًا من قوس مفتوح في i."""
    if i >= len(s) or s[i] != op:
        return None, i
    d, j = 0, i
    while j < len(s):
        if s[j] == op:
            d += 1
        elif s[j] == cl:
            d -= 1
            if d == 0:
                return s[i+1:j], j+1
        j += 1
    return None, i

# -------------------------------------------- تفكيك LaTeX إلى كتل مهيكلة

# بيئات تُعرض كبطاقة مستقلة بعنوان عربي.
ENV_LABEL = {
    'theorem': 'مبرهنة', 'proposition': 'قضية', 'lemma': 'مبرهنة مساعدة',
    'corollary': 'نتيجة', 'definition': 'تعريف', 'conjecture': 'حدسية',
    'openproblem': 'مسألة مفتوحة', 'remark': 'ملاحظة', 'example': 'مثال',
    'exercise': 'تمرين', 'proof': 'برهان',
}
LIST_ENVS = {'itemize': False, 'enumerate': True, 'description': False}
DISPLAY_ENVS = ('align*', 'align', 'equation*', 'equation', 'gather*', 'gather',
                'multline*', 'multline', 'eqnarray*', 'eqnarray')

# أوامر نصية يُحتفظ بمحتواها ويُحذف الأمر نفسه.
_TEXT_CMDS = ('textbf|textit|emph|texttt|textsc|textenglish|text|mbox|underline'
              '|textrm|textsf|LTR|RTL')
_META_CMDS = ('label|resultid|personindex|theoremindex|symbolindex|index'
              '|provedhere|deferredresult|conditionalresult|openresult'
              '|addcontentsline|nocite')


def clean_inline(s):
    """ينظّف نصًّا سطريًّا مع الإبقاء على الرياضيات السطرية كما هي."""
    holes = []

    def stash(m):
        holes.append(m.group(0))
        return f'\0{len(holes)-1}\0'

    s = re.sub(r'(?<!\\)%.*', '', s)
    s = re.sub(r'\\\(.*?\\\)|(?<!\\)\$[^$]+\$', stash, s, flags=re.S)
    s = re.sub(r'\\(?:' + _META_CMDS + r')\s*(?:\[[^\]]*\])?\s*(?:\{[^{}]*\})?', ' ', s)
    s = re.sub(r'\\citedresult\s*(?:\[[^\]]*\])?', ' ', s)
    s = re.sub(r'\\(?:no)?cite[a-zA-Z]*\s*(?:\[[^\]]*\]\s*)*\{([^{}]*)\}',
               lambda m: '[' + m.group(1) + ']', s)
    s = re.sub(r'\\(?:eq)?ref\s*\{[^{}]*\}', ' ', s)
    for _ in range(4):   # أوامر نصية متداخلة
        s2 = re.sub(r'\\(?:' + _TEXT_CMDS + r')\s*\{([^{}]*)\}', r'\1', s)
        if s2 == s:
            break
        s = s2
    s = re.sub(r'\\[a-zA-Z]+\*?\s*(?:\[[^\]]*\])?', ' ', s)
    s = re.sub(r'\\[^a-zA-Z]', ' ', s)
    s = s.replace('{', ' ').replace('}', ' ')
    s = re.sub(r'\0(\d+)\0', lambda m: holes[int(m.group(1))], s)
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()


def clean_math(tex):
    """يزيل أوامر الفهرسة والوسم التي تتخلل الرياضيات فتُفشل المُصيِّر."""
    tex = re.sub(r'(?<!\\)%.*', '', tex)
    tex = re.sub(r'\\(?:' + _META_CMDS + r')\s*(?:\[[^\]]*\])?\s*\{[^{}]*\}', '', tex)
    tex = re.sub(r'\\(?:no)?cite[a-zA-Z]*\s*(?:\[[^\]]*\]\s*)*\{[^{}]*\}', '', tex)
    # ماكرو خاص بالمشروع لا يعرفه المُصيِّر؛ يقابله \text القياسي.
    tex = re.sub(r'\\textenglish\b', r'\\text', tex)
    return tex.strip()


def _paragraphs(s):
    for part in re.split(r'\n\s*\n', s):
        txt = clean_inline(part)
        if txt:
            yield {'t': 'p', 'text': txt}


def parse_blocks(s, depth=0):
    """يفكّك مصدر LaTeX إلى كتل: فقرات، رياضيات معروضة، قوائم، وبيئات مسمّاة."""
    blocks, pos = [], 0
    if depth > 6:
        return list(_paragraphs(s))
    pattern = re.compile(
        r'\\begin\{(' + '|'.join(
            [re.escape(e) for e in ENV_LABEL]
            + [re.escape(e) for e in LIST_ENVS]
            + [re.escape(e) for e in DISPLAY_ENVS]
            + ['center', 'tabular']) + r')\}'
        r'|\\\[')
    while True:
        m = pattern.search(s, pos)
        if not m:
            break
        blocks.extend(_paragraphs(s[pos:m.start()]))
        if m.group(0) == r'\[':
            end = s.find(r'\]', m.end())
            end = len(s) if end < 0 else end
            blocks.append({'t': 'math', 'tex': clean_math(s[m.end():end])})
            pos = end + 2
            continue
        env = m.group(1)
        close = f'\\end{{{env}}}'
        end = s.find(close, m.end())
        end = len(s) if end < 0 else end
        inner, pos = s[m.end():end], end + len(close)

        if env in DISPLAY_ENVS:
            # يجب الإبقاء على غلاف البيئة، وإلا صار محرف المحاذاة & خطأ صياغيًا.
            blocks.append({'t': 'math', 'env': env,
                           'tex': f'\\begin{{{env}}}{clean_math(inner)}\\end{{{env}}}'})
        elif env in LIST_ENVS:
            items = [parse_blocks(x, depth + 1)
                     for x in re.split(r'\\item\s*', inner)[1:]]
            blocks.append({'t': 'list', 'ordered': LIST_ENVS[env],
                           'items': [i for i in items if i]})
        elif env in ('center', 'tabular'):
            blocks.extend(parse_blocks(inner, depth + 1) if env == 'center'
                          else [{'t': 'pre', 'text': clean_inline(inner)}])
        else:
            title = ''
            body = inner
            if body[:1] == '[':
                title, after = _balanced(body, 0, '[', ']')
                title, body = clean_inline(title or ''), body[after:]
            rid = re.search(r'\\resultid\{(ANT-[A-Z]+-\d+-\d+)\}', body)
            st = None
            for macro, val in STATUS_MACRO.items():
                if re.search(r'\\' + macro + r'\b', body):
                    st = val
                    break
            blocks.append({'t': 'env', 'env': env, 'label': ENV_LABEL[env],
                           'title': title, 'result_id': rid.group(1) if rid else None,
                           'status': st, 'blocks': parse_blocks(body, depth + 1)})
    blocks.extend(_paragraphs(s[pos:]))
    return blocks


def blocks_text(blocks, math=True):
    """يسطّح الكتل إلى نص للعرض المختصر وللفهرسة."""
    out = []
    for b in blocks:
        t = b['t']
        if t == 'p':
            out.append(b['text'] if math else re.sub(r'\\\(.*?\\\)|\$[^$]+\$', ' ', b['text']))
        elif t == 'pre':
            out.append(b['text'])
        elif t == 'math':
            out.append(b['tex'] if math else ' ')
        elif t == 'list':
            out += [blocks_text(i, math) for i in b['items']]
        elif t == 'env':
            head = b['label'] + (f" ({b['title']})" if b['title'] else '')
            out.append(head + '. ' + blocks_text(b['blocks'], math))
    return re.sub(r'[ \t]+', ' ', '\n'.join(x for x in out if x.strip())).strip()


# ------------------------------------------------------- قراءة فصول LaTeX

RESULT_ENVS = ('theorem', 'proposition', 'lemma', 'corollary', 'definition',
               'conjecture', 'openproblem', 'remark', 'example', 'exercise')

KIND_AR = {'theorem': 'مبرهنة', 'proposition': 'قضية', 'lemma': 'مبرهنة مساعدة',
           'corollary': 'نتيجة', 'definition': 'تعريف', 'conjecture': 'حدسية',
           'openproblem': 'مسألة مفتوحة', 'remark': 'ملاحظة', 'example': 'مثال',
           'exercise': 'تمرين'}

STATUS_MACRO = {'provedhere': 'PROVED-HERE', 'citedresult': 'CITED',
                'deferredresult': 'DEFERRED', 'conditionalresult': 'CONDITIONAL',
                'openresult': 'OPEN'}

def chapter_files(root):
    """ترتيب الفصول كما يُدرجها main.tex لا كما يرتبها نظام الملفات."""
    main = (root/'manuscript'/'main.tex').read_text(encoding='utf-8')
    out = []
    for m in re.finditer(r'\\input\{(volumes/[^}]+)\}', main):
        rel = m.group(1)
        p = root/(rel if rel.endswith('.tex') else rel + '.tex')
        if p.exists():
            out.append(p)
    return out

def parse_chapter(path, root):
    raw = path.read_text(encoding='utf-8')
    m = re.search(r'\\chapter\s*\{', raw)
    title = ''
    if m:
        title = clean_inline(_balanced(raw, m.end()-1)[0] or '')
    rel = path.relative_to(root).as_posix()
    volume = rel.split('/')[1] if rel.startswith('volumes/') else ''
    num = None
    mn = re.search(r'chapter-(\d+)', path.name)
    if mn:
        num = int(mn.group(1))

    sections = []
    marks = [(mm.start(), mm.end()) for mm in re.finditer(r'\\section\s*\{', raw)]
    if not marks:
        sections.append(('', raw))
    else:
        if marks[0][0] > 0:
            sections.append(('مقدمة الفصل', raw[:marks[0][0]]))
        for i, (st, en) in enumerate(marks):
            head, after = _balanced(raw, en-1)
            end = marks[i+1][0] if i+1 < len(marks) else len(raw)
            sections.append((clean_inline(head or ''), raw[after:end]))

    results = []
    for env in RESULT_ENVS:
        for mm in re.finditer(r'\\begin\{' + env + r'\}', raw):
            j = mm.end()
            head = ''
            if j < len(raw) and raw[j] == '[':
                head, j = _balanced(raw, j, '[', ']')
                head = clean_inline(head or '')
            close = raw.find('\\end{' + env + '}', j)
            body = raw[j:close if close > 0 else len(raw)]
            rid = re.search(r'\\resultid\{(ANT-[A-Z]+-\d+-\d+)\}', body)
            lab = re.search(r'\\label\{([^}]+)\}', body)
            st = None
            for macro, val in STATUS_MACRO.items():
                if re.search(r'\\' + macro + r'\b', body):
                    st = val
                    break
            results.append({
                'result_id': rid.group(1) if rid else None,
                'kind': env, 'title': head, 'label': lab.group(1) if lab else None,
                'tex_status': st, 'chapter': num,
                'statement': blocks_text(parse_blocks(body))[:4000], 'tex_path': rel,
            })
    return {'number': num, 'title': title, 'tex_path': rel, 'volume': volume,
            'char_count': len(raw), 'sections': sections, 'results': results}

# ------------------------------------------------------ سياسة الحالات والسجلات

def parse_policy(root):
    p = root/'docs'/'RESULT_STATUS_POLICY.md'
    if not p.exists():
        return set()
    return set(re.findall(r'`([A-Z][A-Z-]+)`', p.read_text(encoding='utf-8')))

# وسوم الاعتماد التحريري، وهي منفصلة عن الحالة العلمية للنتيجة.
ADOPTION_TOKENS = {'ACTIVE', 'CITABLE', 'NOT-CITABLE', 'REVIEWED', 'OWNER-ADOPTED',
                   'AUTHORED-DRAFT', 'MERGED', 'COMPLETE'}
_TOKEN = re.compile(r'^`?([A-Z][A-Z-]*(?:\s*/\s*[A-Z][A-Z-]*)*)`?$')


def parse_registries(root):
    """يُرجع {result_id: [(status, adoption, note, registry_file)]}.

    تتعايش في المستودع صيغتان لجدول السجل: صيغة الفصول ≤ 18 تضع الحالة بين
    علامتي `` ` `` في عمود مستقل، وصيغة الفصول ≥ 19 تكتبها نصًّا عاريًا وتضيف
    عمود اعتماد مثل ``ACTIVE / CITABLE``. يقرأ المحلل الصيغتين معًا.
    """
    out = {}
    for f in sorted((root/'docs').glob('RESULTS_REGISTRY*.md')):
        for line in f.read_text(encoding='utf-8').splitlines():
            if not line.strip().startswith('|'):
                continue
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cols) < 3:
                continue
            m = re.fullmatch(r'`?(ANT-[A-Z]+-\d+-\d+)`?', cols[0])
            if not m:
                continue
            sci, adopt = [], []
            for c in cols[1:]:
                mm = _TOKEN.match(c)
                if not mm:
                    continue
                for tok in (t.strip() for t in mm.group(1).split('/')):
                    (adopt if tok in ADOPTION_TOKENS else sci).append(tok)
            out.setdefault(m.group(1), []).append(
                ('/'.join(sci) or None, '/'.join(adopt) or None, cols[-1], f.name))
    return out

def parse_bib(root):
    entries = {}
    for f in sorted((root/'manuscript').glob('*.bib')):
        txt = f.read_text(encoding='utf-8')
        for m in re.finditer(r'@(\w+)\s*\{\s*([^,\s]+)\s*,', txt):
            key = m.group(2)
            start = m.end()
            depth, j = 1, start
            while j < len(txt) and depth:
                if txt[j] == '{':
                    depth += 1
                elif txt[j] == '}':
                    depth -= 1
                j += 1
            body = txt[start:j-1]
            def field(name):
                fm = re.search(name + r'\s*=\s*', body, re.I)
                if not fm:
                    return ''
                k = fm.end()
                if k < len(body) and body[k] == '{':
                    return detex(_balanced(body, k)[0] or '')
                fm2 = re.match(r'"([^"]*)"|([^,\n]*)', body[k:])
                return detex((fm2.group(1) or fm2.group(2) or '').strip())
            entries[key] = {
                'key': key, 'entry_type': m.group(1).lower(), 'title': field('title'),
                'author': field('author'), 'year': field('year'),
                'journal': field('journal') or field('booktitle') or field('publisher'),
                'doi': field('doi'), 'url': field('url'), 'bib_file': f.name,
            }
    return entries

def cite_keys(root):
    keys = set()
    for p in chapter_files(root):
        txt = p.read_text(encoding='utf-8')
        for m in re.finditer(r'\\(?:no)?cite[a-zA-Z]*\s*(?:\[[^\]]*\]\s*)*\{([^{}]*)\}', txt, re.S):
            for k in m.group(1).split(','):
                k = k.strip()
                if k and re.fullmatch(r'[\w:.+-]+', k):
                    keys.add(k)
    return keys

# ------------------------------------------------------------ فحوص التكامل

CITABLE = {'PROVED-HERE', 'CITED', 'CONDITIONAL'}

def registry_status(entries):
    """الحالات العلمية المعلنة للنتيجة عبر كل السجلات التي تذكرها."""
    vals = set()
    for st, _, _, _ in entries:
        if st:
            vals |= {t.strip() for t in st.split('/') if t.strip()}
    return vals


def registry_citable(entries):
    """قابلية الاستشهاد: وسم CITABLE صريح، أو حالة علمية تسمح بها السياسة."""
    adopt = set()
    for _, ad, _, _ in entries:
        if ad:
            adopt |= {t.strip() for t in ad.split('/')}
    if 'NOT-CITABLE' in adopt:
        return False
    return bool(adopt & {'CITABLE'}) or bool(registry_status(entries) & CITABLE)

def policy_base(status, policy):
    """الحالات المعرَّفة في السياسة داخل حالة مركَّبة، بإسقاط المؤهِّلات."""
    if not status:
        return set()
    return {t.strip() for t in status.split('/') if t.strip() in policy}


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

    for k in sorted(cited - set(bib)):
        add('CITE_KEY_MISSING', 'HIGH', k,
            'مفتاح استشهاد مستعمل في المخطوط ولا يقابله مدخل في أي ملف .bib.')
    for k in sorted(set(bib) - cited):
        add('BIB_UNCITED', 'INFO', k,
            'مدخل ببليوغرافي غير مستشهد به صراحة (يظهر عبر \\nocite{*} فقط).')

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

# ---------------------------------------------------------------- الاستيراد

def ingest(db_path, root=None):
    root = Path(root) if root else encyclopedia_root()
    chapters = [parse_chapter(p, root) for p in chapter_files(root)]
    registries = parse_registries(root)
    policy = parse_policy(root)
    bib = parse_bib(root)
    cited = cite_keys(root)

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    try:
        claims = [dict(r) for r in c.execute('SELECT * FROM claims')]
        findings = run_checks(chapters, registries, policy, bib, cited, claims)
        ts = now()
        with c:
            for t in ('units_fts', 'units', 'chapters', 'results', 'bib_entries',
                      'integrity_findings'):
                c.execute(f'DELETE FROM {t}')
            for ch in chapters:
                cur = c.execute(
                    'INSERT INTO chapters(number,title,tex_path,volume,char_count,ingested_at)'
                    ' VALUES(?,?,?,?,?,?)',
                    (ch['number'], ch['title'], ch['tex_path'], ch['volume'],
                     ch['char_count'], ts))
                cid = cur.lastrowid
                for i, (head, body) in enumerate(ch['sections'], 1):
                    blocks = parse_blocks(body)
                    txt = blocks_text(blocks)
                    if not txt:
                        continue
                    c.execute(
                        'INSERT INTO units(chapter_id,ord,kind,heading,text,text_norm,blocks)'
                        ' VALUES(?,?,?,?,?,?,?)',
                        (cid, i, 'section', head, txt,
                         normalize_ar((head or '') + '\n' + blocks_text(blocks, math=False)),
                         json.dumps(blocks, ensure_ascii=False)))
                for r in ch['results']:
                    if not r['result_id']:
                        continue
                    entries = registries.get(r['result_id'], [])
                    base = registry_status(entries)
                    c.execute(
                        'INSERT OR REPLACE INTO results(result_id,kind,title,chapter,'
                        'tex_status,registry_status,registry_files,source_note,citable,'
                        'label,statement,tex_path,updated_at)'
                        ' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (r['result_id'], r['kind'], r['title'], r['chapter'],
                         r['tex_status'], '/'.join(sorted(base)) or None,
                         '، '.join(sorted({e[3] for e in entries})) or None,
                         (entries[0][2] if entries else ''),
                         1 if registry_citable(entries) else 0,
                         r['label'], r['statement'], r['tex_path'], ts))
            for k, e in bib.items():
                c.execute(
                    'INSERT INTO bib_entries(key,entry_type,title,author,year,journal,'
                    'doi,url,bib_file,cited) VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (e['key'], e['entry_type'], e['title'], e['author'], e['year'],
                     e['journal'], e['doi'], e['url'], e['bib_file'],
                     1 if k in cited else 0))
            for f in findings:
                c.execute(
                    'INSERT INTO integrity_findings(code,severity,subject,detail,checked_at)'
                    ' VALUES(?,?,?,?,?)',
                    (f['code'], f['severity'], f['subject'], f['detail'], ts))
        return {
            'status': 'ingested', 'root': str(root),
            'chapters': len(chapters),
            'units': c.execute('SELECT count(*) FROM units').fetchone()[0],
            'results': c.execute('SELECT count(*) FROM results').fetchone()[0],
            'bib_entries': len(bib),
            'findings': len(findings),
            'at': ts,
        }
    finally:
        c.close()
