#!/usr/bin/env python3
import argparse, json, mimetypes, os, re, sqlite3, sys, threading, webbrowser
from contextlib import closing
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timezone

import ingest
from ingest import normalize_ar

ROOT = Path(__file__).resolve().parent
DB = ROOT/'data'/'observatory.db'
STATIC = ROOT/'static'

SCHEMA = '''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS sources(
 id INTEGER PRIMARY KEY, source_type TEXT NOT NULL, title TEXT NOT NULL,
 path TEXT, authority TEXT NOT NULL, status TEXT NOT NULL,
 metadata_json TEXT DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chapters(
 id INTEGER PRIMARY KEY, number INTEGER, title TEXT NOT NULL,
 tex_path TEXT NOT NULL, volume TEXT, char_count INTEGER, ingested_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS units(
 id INTEGER PRIMARY KEY, chapter_id INTEGER NOT NULL REFERENCES chapters(id),
 ord INTEGER NOT NULL, kind TEXT NOT NULL, heading TEXT,
 text TEXT NOT NULL, text_norm TEXT NOT NULL, blocks TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS units_fts USING fts5(
 text_norm, content='units', content_rowid='id',
 tokenize="unicode61 remove_diacritics 2");
CREATE TRIGGER IF NOT EXISTS units_ai AFTER INSERT ON units BEGIN
 INSERT INTO units_fts(rowid,text_norm) VALUES(new.id,new.text_norm); END;
CREATE TRIGGER IF NOT EXISTS units_ad AFTER DELETE ON units BEGIN
 INSERT INTO units_fts(units_fts,rowid,text_norm) VALUES('delete',old.id,old.text_norm); END;
CREATE TABLE IF NOT EXISTS results(
 id INTEGER PRIMARY KEY, result_id TEXT UNIQUE NOT NULL, kind TEXT, title TEXT,
 chapter INTEGER, tex_status TEXT, registry_status TEXT, registry_files TEXT,
 source_note TEXT, citable INTEGER NOT NULL DEFAULT 0, label TEXT,
 statement TEXT, tex_path TEXT, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bib_entries(
 id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, entry_type TEXT, title TEXT,
 author TEXT, year TEXT, journal TEXT, doi TEXT, url TEXT, bib_file TEXT,
 cited INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS model_notes(
 id INTEGER PRIMARY KEY, note_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
 kind TEXT, domain TEXT, anchors TEXT, literature_hint TEXT,
 is_gap INTEGER NOT NULL DEFAULT 0, body TEXT NOT NULL, body_norm TEXT NOT NULL,
 blocks TEXT, source_file TEXT, updated_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS model_notes_fts USING fts5(
 body_norm, content='model_notes', content_rowid='id',
 tokenize="unicode61 remove_diacritics 2");
CREATE TRIGGER IF NOT EXISTS mnotes_ai AFTER INSERT ON model_notes BEGIN
 INSERT INTO model_notes_fts(rowid,body_norm) VALUES(new.id,new.body_norm); END;
CREATE TRIGGER IF NOT EXISTS mnotes_ad AFTER DELETE ON model_notes BEGIN
 INSERT INTO model_notes_fts(model_notes_fts,rowid,body_norm)
 VALUES('delete',old.id,old.body_norm); END;
CREATE TABLE IF NOT EXISTS integrity_findings(
 id INTEGER PRIMARY KEY, code TEXT NOT NULL, severity TEXT NOT NULL,
 subject TEXT, detail TEXT, checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims(
 id INTEGER PRIMARY KEY, claim_id TEXT UNIQUE NOT NULL, statement TEXT NOT NULL,
 domain TEXT, source_layer TEXT NOT NULL, status TEXT NOT NULL,
 evidence TEXT, dependencies TEXT, literature_matches TEXT,
 novelty_status TEXT, last_reviewed TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS references_tbl(
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, authors TEXT, year TEXT, venue TEXT,
 doi TEXT, url TEXT, reading_status TEXT NOT NULL, notes TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS literature_gates(
 id INTEGER PRIMARY KEY, gate_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
 question TEXT NOT NULL, status TEXT NOT NULL, keywords TEXT,
 scope TEXT, verdict TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gate_references(
 gate_id INTEGER REFERENCES literature_gates(id), reference_id INTEGER REFERENCES references_tbl(id),
 relation TEXT, coverage TEXT, PRIMARY KEY(gate_id,reference_id)
);
CREATE TABLE IF NOT EXISTS links(
 id INTEGER PRIMARY KEY, from_type TEXT, from_id TEXT, relation TEXT,
 to_type TEXT, to_id TEXT, note TEXT
);
CREATE INDEX IF NOT EXISTS idx_units_chapter ON units(chapter_id,ord);
CREATE INDEX IF NOT EXISTS idx_results_chapter ON results(chapter);
CREATE INDEX IF NOT EXISTS idx_findings_sev ON integrity_findings(severity);
'''

# الحالات التي تسمح بها سياسة اعتماد النتائج بالاستشهاد الخارجي.
CITABLE = ingest.CITABLE
SEVERITY_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}


def now():
    return datetime.now(timezone.utc).isoformat()


def conn():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with closing(conn()) as c, c:
        c.executescript(SCHEMA)
        if not c.execute('SELECT 1 FROM sources LIMIT 1').fetchone():
            for row in (
                ('ENCYCLOPEDIA', 'الموسوعة الشاملة في نظرية الأعداد التحليلية',
                 'analytic-number-theory-encyclopedia-ar', 'INTERNAL_CURATED', 'PENDING-INGEST'),
                ('MODEL_SYNTHESIS', 'المعرفة الرياضية المعيارية والاستدلال',
                 '', 'UNVERIFIED_UNTIL_SOURCED', 'ACTIVE'),
                ('LITERATURE', 'الأدبيات الخارجية الموثقة',
                 '', 'EXTERNAL_VERIFIED', 'ACTIVE'),
            ):
                c.execute('INSERT INTO sources(source_type,title,path,authority,status,'
                          'metadata_json,created_at) VALUES(?,?,?,?,?,?,?)', (*row, '{}', now()))
        if not c.execute('SELECT 1 FROM literature_gates LIMIT 1').fetchone():
            c.execute('INSERT INTO literature_gates(gate_id,title,question,status,keywords,'
                      'scope,verdict,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                      ('GATE-PVFC-SD-001', 'بوابة مؤثرات الألياف وأبراج Selberg-Delange',
                       'هل يوجد في الأدبيات تمثيل موحد لانتقالات الألياف على جميع معاملات '
                       'Selberg-Delange؟', 'OPEN',
                       'Selberg-Delange; monomial symmetric functions; vertex operators; jets',
                       'PVFC birth/merge operators and asymptotic coefficient towers',
                       'REVIEW-IN-PROGRESS', now(), now()))


def rows(q, params=()):
    with closing(conn()) as c:
        return [dict(r) for r in c.execute(q, params).fetchall()]


def one(q, params=()):
    with closing(conn()) as c:
        r = c.execute(q, params).fetchone()
        return dict(r) if r else None


def json_body(h):
    n = int(h.headers.get('Content-Length', '0') or 0)
    if n > 1 << 20:
        raise ValueError('حجم الطلب كبير')
    return json.loads(h.rfile.read(n) or b'{}')


def send_json(h, obj, code=200):
    b = json.dumps(obj, ensure_ascii=False).encode()
    h.send_response(code)
    h.send_header('Content-Type', 'application/json; charset=utf-8')
    h.send_header('Content-Length', str(len(b)))
    h.end_headers()
    h.wfile.write(b)


class ApiError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


def cited_results(*texts):
    return set(re.findall(r'ANT-[A-Z]+-\d+-\d+', ' '.join(t or '' for t in texts)))


def enforce_citation_policy(payload):
    """قاعدة الاعتماد الخارجي: لا يُرفع ادعاء إلى حالة موثقة إلا بإسناد صالح.

    وردت القاعدة في README وفي سياسة اعتماد النتائج، وهنا تصير قيدًا منفَّذًا:
    كل معرّف ANT مذكور في الادعاء يجب أن يكون مسجَّلًا وبحالة تسمح بالاستشهاد.
    """
    refs = cited_results(payload.get('evidence'), payload.get('dependencies'),
                         payload.get('literature_matches'))
    for rid in sorted(refs):
        r = one('SELECT registry_status,citable FROM results WHERE result_id=?', (rid,))
        if not r:
            raise ApiError(f'المعرّف {rid} غير موجود في سجل نتائج الموسوعة. '
                           'شغّل الاستيراد أو صحّح المعرّف.', 422)
        if not r['citable']:
            raise ApiError(f'المعرّف {rid} حالته {r["registry_status"]} ولا تسمح '
                           'سياسة اعتماد النتائج بالاستشهاد به.', 422)
    anchored = bool(refs) or bool((payload.get('literature_matches') or '').strip())
    if payload.get('status') in ('KNOWN', 'KNOWN-IN-EQUIVALENT-FORM') and not anchored:
        raise ApiError('لا يجوز رفع ادعاء إلى KNOWN دون إسناد إلى نتيجة معتمدة في '
                       'الموسوعة أو إلى مرجع خارجي موثق.', 422)


def snippet(text, term, width=420):
    if not term:
        return text[:width]
    hay, needle = normalize_ar(text), normalize_ar(term)
    pos = hay.find(needle)
    if pos < 0:
        for w in needle.split():
            pos = hay.find(w)
            if pos >= 0:
                break
    if pos < 0:
        return text[:width]
    start = max(0, pos - width // 3)
    return ('…' if start else '') + text[start:pos + width] + '…'


def search(term, layer='ALL', limit=60):
    out = []
    if not term.strip():
        return out
    tokens = re.findall(r'[\w؀-ۿ]+', normalize_ar(term))
    if tokens:
        match = ' '.join(f'"{t}"' for t in tokens)
        try:
            for r in rows(
                'SELECT units.id,units.heading,units.text,chapters.number chapter,'
                ' chapters.title chapter_title, bm25(units_fts) rank'
                ' FROM units_fts JOIN units ON units.id=units_fts.rowid'
                ' JOIN chapters ON chapters.id=units.chapter_id'
                ' WHERE units_fts MATCH ? ORDER BY rank LIMIT 40', (match,)):
                out.append({'layer': 'ENCYCLOPEDIA', 'kind': 'unit', 'unit_id': r['id'],
                            'title': f"الفصل {r['chapter']} — {r['heading'] or r['chapter_title']}",
                            'chapter': r['chapter'], 'rank': r['rank'],
                            'snippet': snippet(r['text'], term)})
        except sqlite3.OperationalError as e:
            out.append({'layer': 'ENCYCLOPEDIA', 'title': 'تعذر تنفيذ البحث النصي',
                        'snippet': str(e), 'status': 'SEARCH-ERROR'})
    like = f'%{normalize_ar(term)}%'
    for r in rows('SELECT result_id,kind,title,chapter,registry_status,citable,statement'
                  ' FROM results WHERE result_id LIKE ? OR title LIKE ? OR statement LIKE ?'
                  ' LIMIT 30', (f'%{term}%', f'%{term}%', f'%{term}%')):
        out.append({'layer': 'ENCYCLOPEDIA', 'kind': 'result', 'title': r['result_id'],
                    'status': r['registry_status'], 'citable': r['citable'],
                    'chapter': r['chapter'],
                    'snippet': (r['title'] + ' — ' if r['title'] else '') + (r['statement'] or '')[:400]})
    if tokens:
        try:
            for r in rows(
                'SELECT model_notes.note_id,title,kind,domain,anchors,is_gap,body,'
                ' bm25(model_notes_fts) rank FROM model_notes_fts'
                ' JOIN model_notes ON model_notes.id=model_notes_fts.rowid'
                ' WHERE model_notes_fts MATCH ? ORDER BY rank LIMIT 20', (match,)):
                out.append({'layer': 'MODEL_SYNTHESIS', 'kind': 'model_note',
                            'title': f"{r['note_id']} — {r['title']}",
                            'status': r['kind'].upper(), 'citable': 0,
                            'is_gap': r['is_gap'], 'anchors': r['anchors'],
                            'snippet': snippet(r['body'], term)})
        except sqlite3.OperationalError:
            pass
    for r in rows('SELECT claim_id,statement,status,source_layer,evidence,novelty_status'
                  ' FROM claims WHERE statement LIKE ? OR evidence LIKE ? LIMIT 30',
                  (f'%{term}%', f'%{term}%')):
        out.append({'layer': r['source_layer'], 'kind': 'claim', 'title': r['claim_id'],
                    'status': r['status'], 'novelty_status': r['novelty_status'],
                    'source_layer': r['source_layer'], 'snippet': r['statement']})
    for r in rows('SELECT key,title,author,year,journal FROM bib_entries'
                  ' WHERE key LIKE ? OR title LIKE ? OR author LIKE ? LIMIT 20',
                  (f'%{term}%', f'%{term}%', f'%{term}%')):
        out.append({'layer': 'LITERATURE', 'kind': 'bib', 'title': r['key'],
                    'snippet': f"{r['author']} ({r['year']}). {r['title']}. {r['journal']}"})
    for r in rows('SELECT title,authors,year,reading_status,notes FROM references_tbl'
                  ' WHERE title LIKE ? OR notes LIKE ? LIMIT 20', (f'%{term}%', f'%{term}%')):
        out.append({'layer': 'LITERATURE', 'kind': 'reference', 'title': r['title'],
                    'status': r['reading_status'], 'snippet': r['notes']})
    if layer != 'ALL':
        out = [x for x in out if x.get('layer') == layer]
    return out[:limit]


class H(BaseHTTPRequestHandler):
    server_version = 'ANTObservatory'

    def log_message(self, fmt, *args):
        pass

    # ---------------------------------------------------------------- الوصول
    def _guard_origin(self):
        """الخادم محلي بلا مصادقة، فالكتابة تُقبل فقط من نفس الأصل."""
        origin = self.headers.get('Origin')
        if origin and urlparse(origin).hostname not in ('127.0.0.1', 'localhost'):
            raise ApiError('طلب من أصل خارجي مرفوض', 403)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path.startswith('/api/'):
            return self._dispatch(self.api_get, u)
        return self._serve_static(u)

    def do_POST(self):
        u = urlparse(self.path)
        return self._dispatch(self.api_post, u)

    def do_PATCH(self):
        u = urlparse(self.path)
        return self._dispatch(self.api_patch, u)

    def _dispatch(self, fn, u):
        try:
            fn(u)
        except ApiError as e:
            send_json(self, {'error': str(e)}, e.code)
        except Exception as e:
            send_json(self, {'error': f'{type(e).__name__}: {e}'}, 500)

    def _serve_static(self, u):
        rel = unquote(u.path).lstrip('/') or 'index.html'
        p = (STATIC/rel).resolve()
        if not p.is_relative_to(STATIC.resolve()) or not p.is_file():
            return self.send_error(404)
        data = p.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ------------------------------------------------------------------ POST
    def api_post(self, u):
        self._guard_origin()
        d = json_body(self) if u.path != '/api/ingest' else {}
        if u.path == '/api/ingest':
            init_db()
            res = ingest.ingest(DB, d.get('root'))
            with closing(conn()) as c, c:
                c.execute("UPDATE sources SET status='INGESTED', path=? "
                          "WHERE source_type='ENCYCLOPEDIA'", (res['root'],))
            return send_json(self, res)
        if u.path == '/api/claims':
            if not (d.get('statement') or '').strip():
                raise ApiError('نص الادعاء مطلوب')
            enforce_citation_policy(d)
            cid = d.get('claim_id') or f"CLAIM-{datetime.now():%Y%m%d-%H%M%S-%f}"
            with closing(conn()) as c, c:
                c.execute('INSERT INTO claims(claim_id,statement,domain,source_layer,status,'
                          'evidence,dependencies,literature_matches,novelty_status,'
                          'last_reviewed,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                          (cid, d['statement'], d.get('domain', ''),
                           d.get('source_layer', 'MODEL_SYNTHESIS'),
                           d.get('status', 'MODEL-SYNTHESIS'), d.get('evidence', ''),
                           d.get('dependencies', ''), d.get('literature_matches', ''),
                           d.get('novelty_status', 'UNCERTIFIED'), now(), now()))
            return send_json(self, {'ok': True, 'claim_id': cid}, 201)
        if u.path == '/api/references':
            if not (d.get('title') or '').strip():
                raise ApiError('عنوان المرجع مطلوب')
            with closing(conn()) as c, c:
                c.execute('INSERT INTO references_tbl(title,authors,year,venue,doi,url,'
                          'reading_status,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
                          (d['title'], d.get('authors', ''), d.get('year', ''),
                           d.get('venue', ''), d.get('doi', ''), d.get('url', ''),
                           d.get('reading_status', 'DISCOVERED'), d.get('notes', ''), now()))
            return send_json(self, {'ok': True}, 201)
        if u.path == '/api/gates':
            if not (d.get('title') or '').strip() or not (d.get('question') or '').strip():
                raise ApiError('عنوان البوابة وسؤالها مطلوبان')
            gid = d.get('gate_id') or f"GATE-{datetime.now():%Y%m%d-%H%M%S}"
            with closing(conn()) as c, c:
                c.execute('INSERT INTO literature_gates(gate_id,title,question,status,'
                          'keywords,scope,verdict,created_at,updated_at)'
                          ' VALUES(?,?,?,?,?,?,?,?,?)',
                          (gid, d['title'], d['question'], d.get('status', 'OPEN'),
                           d.get('keywords', ''), d.get('scope', ''),
                           d.get('verdict', 'NOT-ASSESSED'), now(), now()))
            return send_json(self, {'ok': True, 'gate_id': gid}, 201)
        self.send_error(404)

    # ----------------------------------------------------------------- PATCH
    PATCHABLE = {
        'claims': ('claims', 'claim_id',
                   {'status', 'novelty_status', 'evidence', 'dependencies',
                    'literature_matches', 'domain', 'statement'}),
        'gates': ('literature_gates', 'gate_id',
                  {'status', 'verdict', 'scope', 'keywords', 'question', 'title'}),
        'references': ('references_tbl', 'id',
                       {'reading_status', 'notes', 'doi', 'url', 'venue', 'year', 'authors'}),
    }

    def api_patch(self, u):
        self._guard_origin()
        m = re.fullmatch(r'/api/(claims|gates|references)/([^/]+)', unquote(u.path))
        if not m:
            return self.send_error(404)
        table, keycol, allowed = self.PATCHABLE[m.group(1)]
        d = json_body(self)
        fields = {k: v for k, v in d.items() if k in allowed}
        if not fields:
            raise ApiError('لا حقول قابلة للتعديل في الطلب')
        if table == 'claims':
            cur = one('SELECT * FROM claims WHERE claim_id=?', (m.group(2),))
            if not cur:
                raise ApiError('الادعاء غير موجود', 404)
            enforce_citation_policy({**cur, **fields})
        sets = ', '.join(f'{k}=?' for k in fields)
        extra = ', last_reviewed=?' if table == 'claims' else (
            ', updated_at=?' if table == 'literature_gates' else '')
        params = list(fields.values()) + ([now()] if extra else []) + [m.group(2)]
        with closing(conn()) as c, c:
            cur = c.execute(f'UPDATE {table} SET {sets}{extra} WHERE {keycol}=?', params)
            if not cur.rowcount:
                raise ApiError('السجل غير موجود', 404)
        return send_json(self, {'ok': True, 'updated': list(fields)})

    # ------------------------------------------------------------------- GET
    def api_get(self, u):
        q = parse_qs(u.query)
        arg = lambda k, d='': (q.get(k) or [d])[0]

        if u.path == '/api/dashboard':
            sev = rows('SELECT severity,count(*) n FROM integrity_findings'
                       ' GROUP BY severity')
            return send_json(self, {
                'sources': rows('SELECT source_type,title,authority,status,path'
                                ' FROM sources ORDER BY id'),
                'counts': {
                    'chapters': one('SELECT count(*) n FROM chapters')['n'],
                    'units': one('SELECT count(*) n FROM units')['n'],
                    'results': one('SELECT count(*) n FROM results')['n'],
                    'citable': one('SELECT count(*) n FROM results WHERE citable=1')['n'],
                    'bib': one('SELECT count(*) n FROM bib_entries')['n'],
                    'model_notes': one('SELECT count(*) n FROM model_notes')['n'],
                    'coverage_gaps': one('SELECT count(*) n FROM model_notes'
                                         ' WHERE is_gap=1')['n'],
                    'claims': one('SELECT count(*) n FROM claims')['n'],
                    'gates': one('SELECT count(*) n FROM literature_gates')['n'],
                    'findings': one('SELECT count(*) n FROM integrity_findings')['n'],
                },
                'severity': {r['severity']: r['n'] for r in sev},
                'by_status': rows('SELECT coalesce(registry_status,tex_status,"غير محدد") s,'
                                  ' count(*) n FROM results GROUP BY s ORDER BY n DESC'),
                'recent_claims': rows('SELECT * FROM claims ORDER BY id DESC LIMIT 6'),
                'gates': rows('SELECT * FROM literature_gates ORDER BY id DESC LIMIT 6'),
                'top_findings': sorted(
                    rows("SELECT * FROM integrity_findings WHERE severity IN"
                         " ('CRITICAL','HIGH') LIMIT 20"),
                    key=lambda r: SEVERITY_ORDER.get(r['severity'], 9))[:8],
            })
        if u.path == '/api/search':
            term = arg('q').strip()
            return send_json(self, {'query': term,
                                    'results': search(term, arg('layer', 'ALL'))})
        if u.path == '/api/results':
            where, params = [], []
            if arg('status'):
                where.append('coalesce(registry_status,tex_status) LIKE ?')
                params.append(f'%{arg("status")}%')
            if arg('chapter'):
                where.append('chapter=?')
                params.append(self._int(arg('chapter'), 'chapter'))
            if arg('citable'):
                where.append('citable=?')
                params.append(1 if arg('citable') == '1' else 0)
            sql = 'SELECT * FROM results'
            if where:
                sql += ' WHERE ' + ' AND '.join(where)
            return send_json(self, rows(sql + ' ORDER BY chapter, result_id', params))
        if u.path == '/api/integrity':
            where, params = [], []
            if arg('severity'):
                where.append('severity=?')
                params.append(arg('severity'))
            if arg('code'):
                where.append('code=?')
                params.append(arg('code'))
            sql = 'SELECT * FROM integrity_findings'
            if where:
                sql += ' WHERE ' + ' AND '.join(where)
            out = sorted(rows(sql, params),
                         key=lambda r: (SEVERITY_ORDER.get(r['severity'], 9), r['code']))
            return send_json(self, {
                'findings': out,
                'by_code': rows('SELECT code,severity,count(*) n FROM integrity_findings'
                                ' GROUP BY code,severity')})
        if u.path == '/api/chapters':
            return send_json(self, rows(
                'SELECT chapters.*, (SELECT count(*) FROM units WHERE chapter_id=chapters.id) units,'
                ' (SELECT count(*) FROM results WHERE chapter=chapters.number) results'
                ' FROM chapters ORDER BY id'))
        if u.path == '/api/units':
            cid = self._int(arg('chapter_id', '0'), 'chapter_id')
            return send_json(self, rows(
                'SELECT id,ord,heading,text,blocks FROM units WHERE chapter_id=? ORDER BY ord', (cid,)))
        if u.path == '/api/claims':
            return send_json(self, rows('SELECT * FROM claims ORDER BY id DESC'))
        if u.path == '/api/references':
            return send_json(self, rows('SELECT * FROM references_tbl ORDER BY id DESC'))
        if u.path == '/api/bib':
            return send_json(self, rows('SELECT * FROM bib_entries ORDER BY key'))
        if u.path == '/api/model-notes':
            where, params = [], []
            if arg('kind'):
                where.append('kind=?')
                params.append(arg('kind'))
            if arg('gap'):
                where.append('is_gap=?')
                params.append(1 if arg('gap') == '1' else 0)
            sql = 'SELECT * FROM model_notes'
            if where:
                sql += ' WHERE ' + ' AND '.join(where)
            return send_json(self, {
                'notes': rows(sql + ' ORDER BY source_file, note_id', params),
                'by_domain': rows('SELECT domain,count(*) n,'
                                  ' sum(is_gap) gaps FROM model_notes'
                                  ' GROUP BY domain ORDER BY n DESC'),
                'by_kind': rows('SELECT kind,count(*) n FROM model_notes'
                                ' GROUP BY kind ORDER BY n DESC')})
        if u.path == '/api/gates':
            return send_json(self, rows('SELECT * FROM literature_gates ORDER BY id DESC'))
        self.send_error(404)

    @staticmethod
    def _int(v, name):
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ApiError(f'قيمة غير صحيحة للمعامل {name}')


def main():
    ap = argparse.ArgumentParser(description='ANT-PVG Local Research Observatory')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--no-browser', action='store_true')
    ap.add_argument('--rebuild', action='store_true', help='حذف القاعدة وإعادة بنائها')
    ap.add_argument('--ingest', action='store_true', help='استيراد الموسوعة ثم الخروج')
    ap.add_argument('--root', help='مسار مستودع الموسوعة')
    args = ap.parse_args()

    if args.rebuild and DB.exists():
        DB.unlink(missing_ok=True)
        for suf in ('-wal', '-shm'):
            DB.with_name(DB.name + suf).unlink(missing_ok=True)
    init_db()

    if args.ingest or args.rebuild or not one('SELECT 1 FROM chapters LIMIT 1'):
        try:
            res = ingest.ingest(DB, args.root)
            with closing(conn()) as c, c:
                c.execute("UPDATE sources SET status='INGESTED', path=? "
                          "WHERE source_type='ENCYCLOPEDIA'", (res['root'],))
            print(f"استيراد: {res['chapters']} فصلًا، {res['units']} وحدة نصية، "
                  f"{res['results']} نتيجة، {res['bib_entries']} مرجعًا، "
                  f"{res['findings']} ملاحظة تكامل.")
        except FileNotFoundError as e:
            print(f'تحذير: {e}', file=sys.stderr)
    if args.ingest:
        return

    url = f'http://127.0.0.1:{args.port}'
    if not args.no_browser:
        threading.Timer(.8, lambda: webbrowser.open(url)).start()
    print(f'ANT-PVG Local Observatory running at {url}')
    ThreadingHTTPServer(('127.0.0.1', args.port), H).serve_forever()


if __name__ == '__main__':
    main()
