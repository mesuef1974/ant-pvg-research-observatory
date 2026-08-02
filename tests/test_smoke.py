import subprocess, sys, time, json, urllib.parse, urllib.request, urllib.error
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
CWD = r'D:\ant-pvg-research-observatory\.claude\worktrees\project-review-e411bb'
PORT = '8793'
BASE = 'http://127.0.0.1:' + PORT

p = subprocess.Popen([sys.executable, 'server.py', '--no-browser', '--port', PORT],
                     cwd=CWD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                     encoding='utf-8', errors='replace')
time.sleep(4)

def call(path, method='GET', body=None, headers=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers or ({'Content-Type': 'application/json'} if body is not None else {}))
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or '{}')
    except Exception as e:
        return None, repr(e)

ok = fail = 0
def check(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1; print(f'  ✓ {name}')
    else:
        fail += 1; print(f'  ✗ {name}  {extra}')

try:
    print('== لوحة القيادة ==')
    s, d = call('/api/dashboard')
    check('يستجيب 200', s == 200, s)
    check('26+ فصلًا مستوردًا', d['counts']['chapters'] >= 26, d['counts'])
    check('252 نتيجة', d['counts']['results'] == 252, d['counts']['results'])
    check('يوجد ملاحظات تكامل', d['counts']['findings'] > 0)

    print('\n== البحث العربي ==')
    s, d = call('/api/search?q=' + urllib.parse.quote('الأعداد الأولية'))
    check('نتائج غير صفرية', len(d['results']) > 10, len(d['results']))
    s, d2 = call('/api/search?q=' + urllib.parse.quote('الاعداد الاولية'))
    check('التطبيع يتجاوز الهمزات', len(d2['results']) > 10, len(d2['results']))
    s, d3 = call('/api/search?q=Selberg&layer=ENCYCLOPEDIA')
    check('ترشيح الطبقة يعمل', all(x['layer'] == 'ENCYCLOPEDIA' for x in d3['results']))

    print('\n== إنفاذ سياسة الاستشهاد ==')
    s, d = call('/api/claims', 'POST', {'statement': 'ادعاء اختبار', 'status': 'KNOWN'})
    check('يرفض KNOWN بلا إسناد (422)', s == 422, (s, d))
    s, d = call('/api/claims', 'POST',
                {'statement': 'ادعاء اختبار', 'evidence': 'يستند إلى ANT-THM-99-99'})
    check('يرفض معرّفًا غير موجود (422)', s == 422, (s, d))
    s, d = call('/api/claims', 'POST',
                {'statement': 'ادعاء اختبار مقبول', 'status': 'KNOWN',
                 'evidence': 'يستند إلى ANT-THM-06-01'})
    check('يقبل الإسناد إلى نتيجة معتمدة (201)', s == 201, (s, d))
    cid = d.get('claim_id')

    print('\n== التحديث PATCH ==')
    s, d = call(f'/api/claims/{cid}', 'PATCH', {'status': 'CANDIDATE-GAP'})
    check('يعدّل حالة الادعاء', s == 200, (s, d))
    s, d = call('/api/gates/GATE-PVFC-SD-001', 'PATCH',
                {'status': 'CLOSED-GAP', 'verdict': 'لا تغطية موحدة في الأدبيات'})
    check('يغلق بوابة أدبيات', s == 200, (s, d))
    s, d = call('/api/gates')
    check('الحكم محفوظ', any(g['verdict'].startswith('لا تغطية') for g in d))

    print('\n== الأخطاء والحدود ==')
    s, d = call('/api/units?chapter_id=abc')
    check('معامل غير صحيح ← 400 لا 500', s == 400, (s, d))
    s, d = call('/api/claims', 'POST', {'statement': ''})
    check('نص فارغ مرفوض', s == 400, (s, d))
    s, d = call('/api/claims', 'POST', {'statement': 'من أصل خارجي'},
                {'Content-Type': 'application/json', 'Origin': 'https://evil.example'})
    check('يرفض أصلًا خارجيًا (403)', s == 403, (s, d))

    print('\n== الملفات الساكنة ==')
    for path, want in [('/', 200), ('/app.js', 200), ('/../server.py', 404),
                       ('/%2e%2e/server.py', 404), ('/nope.txt', 404)]:
        try:
            with urllib.request.urlopen(BASE + path, timeout=10) as r:
                got = r.status
        except urllib.error.HTTPError as e:
            got = e.code
        check(f'{path} → {want}', got == want, got)

    print('\n== طبقة المعرفة المعيارية ==')
    s, mn = call('/api/model-notes')
    check('الملاحظات محمَّلة', len(mn['notes']) >= 50, len(mn['notes']))
    check('فجوات التغطية مرصودة',
          sum(n['is_gap'] for n in mn['notes']) >= 10,
          sum(n['is_gap'] for n in mn['notes']))
    check('لكل ملاحظة كتل مهيكلة', all(n['blocks'] for n in mn['notes']))
    s, integ = call('/api/integrity?code=MODEL_NOTE_ANCHOR_UNKNOWN')
    check('كل إسناد إلى الموسوعة صحيح', not integ['findings'],
          [f['subject'] for f in integ['findings']][:5])
    s, d = call('/api/search?q=' + urllib.parse.quote('عائق التكافؤ'))
    ms = [x for x in d['results'] if x['layer'] == 'MODEL_SYNTHESIS']
    check('الملاحظات تظهر في البحث الموحد', ms, len(d['results']))
    check('ولا تُعرض قابلةً للاستشهاد', all(not x.get('citable') for x in ms))
    note_id = mn['notes'][0]['note_id']
    s, d = call('/api/claims', 'POST',
                {'statement': 'ادعاء يستند إلى ملاحظة معيارية', 'status': 'KNOWN',
                 'evidence': f'يستند إلى {note_id}'})
    check('لا يُقبل ادعاء KNOWN مستندًا إلى ملاحظة معيارية', s == 422, (s, d))

    print('\n== ترقيم الفصول ==')
    s, chs = call('/api/chapters')
    check('26 فصلًا لا 31 ملفًا', len(chs) == 26, len(chs))
    check('الترقيم متصل 1..26',
          sorted(c['number'] for c in chs) == list(range(1, 27)),
          sorted(c['number'] for c in chs))
    check('الفصل 26 هو خريطة الجبهات',
          'الجبهات' in next(c['title'] for c in chs if c['number'] == 26))
    s, res = call('/api/results')
    bad = [r['result_id'] for r in res
           if int(r['result_id'].rsplit('-', 2)[1]) != r['chapter']]
    check('رقم فصل كل نتيجة يطابق معرّفها', not bad, bad[:5])

    print('\n== بنية القارئ: المعادلات والبيئات ==')
    kinds, envs, no_blocks = {}, {}, 0

    def walk(bs):
        for b in bs:
            kinds[b['t']] = kinds.get(b['t'], 0) + 1
            if b['t'] == 'env':
                envs[b['env']] = envs.get(b['env'], 0) + 1
                walk(b['blocks'])
            elif b['t'] == 'list':
                for i in b['items']:
                    walk(i)

    placeholder = 0
    for c in chs:
        s, us = call('/api/units?chapter_id=' + str(c['id']))
        for u in us:
            if not u.get('blocks'):
                no_blocks += 1
                continue
            walk(json.loads(u['blocks']))
            if '[معادلة]' in u['text']:
                placeholder += 1
    check('كل وحدة تحمل كتلًا مهيكلة', no_blocks == 0, no_blocks)
    check('المعادلات المعروضة محفوظة', kinds.get('math', 0) > 1000, kinds.get('math'))
    check('لا نائب [معادلة] في نص العرض', placeholder == 0, placeholder)
    check('المبرهنات محفوظة كبيئات', envs.get('theorem', 0) >= 100, envs.get('theorem'))
    check('البراهين محفوظة كبيئات', envs.get('proof', 0) >= 140, envs.get('proof'))
    check('التعريفات والملاحظات محفوظة',
          envs.get('definition', 0) >= 45 and envs.get('remark', 0) >= 80, envs)

    print('\n== أصول KaTeX المضمَّنة ==')
    for asset in ('/vendor/katex/katex.min.js', '/vendor/katex/katex.min.css',
                  '/vendor/katex/auto-render.min.js',
                  '/vendor/katex/fonts/KaTeX_Main-Regular.woff2'):
        try:
            with urllib.request.urlopen(BASE + asset, timeout=10) as r:
                got = r.status
        except urllib.error.HTTPError as e:
            got = e.code
        check(asset.rsplit('/', 1)[-1], got == 200, got)

    print('\n== تكامل الحوكمة ==')
    s, d = call('/api/integrity?severity=CRITICAL')
    check('يرصد تعارض ANT-THM-07-09',
          any(f['subject'] == 'ANT-THM-07-09' for f in d['findings']), d['findings'][:1])
    s, d = call('/api/integrity?code=CITE_KEY_MISSING')
    check('يرصد مفتاح استشهاد مفقود', len(d['findings']) == 1, d['findings'])
finally:
    p.terminate()
    try:
        p.wait(5)
    except Exception:
        p.kill()

print(f'\nنجح {ok} — فشل {fail}')
sys.exit(1 if fail else 0)
