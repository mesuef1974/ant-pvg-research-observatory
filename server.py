#!/usr/bin/env python3
import argparse, json, mimetypes, os, re, sqlite3, sys, threading, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

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
CREATE TABLE IF NOT EXISTS documents(
 id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id),
 title TEXT NOT NULL, file_name TEXT, page_count INTEGER, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pages(
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id),
 page_no INTEGER NOT NULL, text TEXT NOT NULL,
 UNIQUE(document_id,page_no)
);
CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(text, content='pages', content_rowid='id', tokenize='unicode61');
CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN INSERT INTO pages_fts(rowid,text) VALUES(new.id,new.text); END;
CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN INSERT INTO pages_fts(pages_fts,rowid,text) VALUES('delete',old.id,old.text); END;
CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN INSERT INTO pages_fts(pages_fts,rowid,text) VALUES('delete',old.id,old.text); INSERT INTO pages_fts(rowid,text) VALUES(new.id,new.text); END;
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
 id INTEGER PRIMARY KEY, from_type TEXT, from_id TEXT, relation TEXT, to_type TEXT, to_id TEXT, note TEXT
);
'''

def now(): return datetime.now(timezone.utc).isoformat()

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c

def init_db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with conn() as c:
        c.executescript(SCHEMA)
        if not c.execute('SELECT 1 FROM sources LIMIT 1').fetchone():
            c.execute('INSERT INTO sources(source_type,title,path,authority,status,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)',
                      ('ENCYCLOPEDIA','الموسوعة الشاملة في نظرية الأعداد التحليلية - المجلد الأول','imports/encyclopedia_vol1.pdf','INTERNAL_CURATED','IMPORTED','{}',now()))
            c.execute('INSERT INTO sources(source_type,title,path,authority,status,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)',
                      ('MODEL_SYNTHESIS','المعرفة الرياضية المعيارية والاستدلال','', 'UNVERIFIED_UNTIL_SOURCED','ACTIVE','{}',now()))
            c.execute('INSERT INTO sources(source_type,title,path,authority,status,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)',
                      ('LITERATURE','الأدبيات الخارجية الموثقة','', 'EXTERNAL_VERIFIED','ACTIVE','{}',now()))
        if not c.execute('SELECT 1 FROM literature_gates LIMIT 1').fetchone():
            c.execute('INSERT INTO literature_gates(gate_id,title,question,status,keywords,scope,verdict,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                      ('GATE-PVFC-SD-001','بوابة مؤثرات الألياف وأبراج Selberg-Delange','هل يوجد في الأدبيات تمثيل موحد لانتقالات الألياف على جميع معاملات Selberg-Delange؟','OPEN','Selberg-Delange; monomial symmetric functions; vertex operators; jets; coefficient towers','PVFC birth/merge operators and asymptotic coefficient towers','REVIEW-IN-PROGRESS',now(),now()))
        if not c.execute('SELECT 1 FROM claims LIMIT 1').fetchone():
            seeds=[
              ('CLAIM-0001','D_λ(s) هو تخصص للدالة المتناظرة الأحادية m_λ عند x_p=p^{-s}.','PVFC / symmetric functions','LITERATURE','KNOWN-IN-EQUIVALENT-FORM','يتطلب مرجعًا أصليًا للدوال المتناظرة وربطًا صريحًا بالتخصص الأولي','','','NOT-NOVEL'),
              ('CLAIM-0002','الحامل التوافقي للألياف المنتهية هو multislice/Schreier orbit.','PVFC / combinatorics','LITERATURE','KNOWN-IN-EQUIVALENT-FORM','أدبيات multislice وSchreier graphs','','','NOT-NOVEL'),
              ('CLAIM-0003','انتقالات الألياف قد تحمل تمثيلًا مثلثيًا على أبراج Selberg-Delange.','PVFC / analytic number theory','MODEL_SYNTHESIS','CANDIDATE-GAP','لا يوجد تطابق موحد مؤكد حتى الآن','','','NOVELTY-UNCERTIFIED'),
            ]
            for x in seeds:
                c.execute('INSERT INTO claims(claim_id,statement,domain,source_layer,status,evidence,dependencies,literature_matches,novelty_status,last_reviewed,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(*x,now(),now()))

def import_pdf(pdf_path:Path):
    from pypdf import PdfReader
    init_db()
    with conn() as c:
        src=c.execute("SELECT id FROM sources WHERE source_type='ENCYCLOPEDIA' ORDER BY id LIMIT 1").fetchone()['id']
        doc=c.execute('SELECT id FROM documents WHERE file_name=?',(pdf_path.name,)).fetchone()
        if doc: return {'status':'already_imported','document_id':doc['id']}
        reader=PdfReader(str(pdf_path))
        cur=c.execute('INSERT INTO documents(source_id,title,file_name,page_count,created_at) VALUES(?,?,?,?,?)',
                      (src,'الموسوعة الشاملة في نظرية الأعداد التحليلية - المجلد الأول',pdf_path.name,len(reader.pages),now()))
        did=cur.lastrowid
        for i,p in enumerate(reader.pages,1):
            txt=p.extract_text() or ''
            c.execute('INSERT INTO pages(document_id,page_no,text) VALUES(?,?,?)',(did,i,txt))
        return {'status':'imported','document_id':did,'pages':len(reader.pages)}

def rows(q,params=()):
    with conn() as c: return [dict(r) for r in c.execute(q,params).fetchall()]

def one(q,params=()):
    with conn() as c:
        r=c.execute(q,params).fetchone(); return dict(r) if r else None

def json_body(h):
    n=int(h.headers.get('Content-Length','0')); return json.loads(h.rfile.read(n) or b'{}')

def send_json(h,obj,code=200):
    b=json.dumps(obj,ensure_ascii=False).encode(); h.send_response(code); h.send_header('Content-Type','application/json; charset=utf-8'); h.send_header('Content-Length',str(len(b))); h.end_headers(); h.wfile.write(b)

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt,*args): pass
    def do_GET(self):
        u=urlparse(self.path)
        if u.path.startswith('/api/'):
            try: return self.api_get(u)
            except Exception as e: return send_json(self,{'error':str(e)},500)
        p=(STATIC/('index.html' if u.path=='/' else u.path.lstrip('/'))).resolve()
        if not str(p).startswith(str(STATIC.resolve())) or not p.exists(): self.send_error(404); return
        data=p.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(str(p))[0] or 'application/octet-stream'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        u=urlparse(self.path)
        try:
            if u.path=='/api/claims':
                d=json_body(self); cid=d.get('claim_id') or f"CLAIM-{int(datetime.now().timestamp())}"
                with conn() as c: c.execute('INSERT INTO claims(claim_id,statement,domain,source_layer,status,evidence,dependencies,literature_matches,novelty_status,last_reviewed,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(cid,d['statement'],d.get('domain',''),d.get('source_layer','MODEL_SYNTHESIS'),d.get('status','MODEL-SYNTHESIS'),d.get('evidence',''),d.get('dependencies',''),d.get('literature_matches',''),d.get('novelty_status','UNCERTIFIED'),now(),now()))
                return send_json(self,{'ok':True,'claim_id':cid},201)
            if u.path=='/api/references':
                d=json_body(self)
                with conn() as c: c.execute('INSERT INTO references_tbl(title,authors,year,venue,doi,url,reading_status,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(d['title'],d.get('authors',''),d.get('year',''),d.get('venue',''),d.get('doi',''),d.get('url',''),d.get('reading_status','DISCOVERED'),d.get('notes',''),now()))
                return send_json(self,{'ok':True},201)
            if u.path=='/api/gates':
                d=json_body(self); gid=d.get('gate_id') or f"GATE-{int(datetime.now().timestamp())}"
                with conn() as c: c.execute('INSERT INTO literature_gates(gate_id,title,question,status,keywords,scope,verdict,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',(gid,d['title'],d['question'],d.get('status','OPEN'),d.get('keywords',''),d.get('scope',''),d.get('verdict','NOT-ASSESSED'),now(),now()))
                return send_json(self,{'ok':True,'gate_id':gid},201)
            if u.path=='/api/import':
                return send_json(self,import_pdf(ROOT/'imports'/'encyclopedia_vol1.pdf'))
            self.send_error(404)
        except Exception as e: send_json(self,{'error':str(e)},500)
    def api_get(self,u):
        q=parse_qs(u.query)
        if u.path=='/api/dashboard':
            return send_json(self,{
              'sources':rows('SELECT source_type,title,authority,status FROM sources ORDER BY id'),
              'counts':{
                'documents':one('SELECT count(*) n FROM documents')['n'],
                'pages':one('SELECT count(*) n FROM pages')['n'],
                'claims':one('SELECT count(*) n FROM claims')['n'],
                'references':one('SELECT count(*) n FROM references_tbl')['n'],
                'gates':one('SELECT count(*) n FROM literature_gates')['n']},
              'recent_claims':rows('SELECT * FROM claims ORDER BY id DESC LIMIT 6'),
              'gates':rows('SELECT * FROM literature_gates ORDER BY id DESC LIMIT 6')})
        if u.path=='/api/search':
            term=(q.get('q') or [''])[0].strip(); layer=(q.get('layer') or ['ALL'])[0]
            out=[]
            if term:
                try:
                    qq=' '.join(re.findall(r'[\w\u0600-\u06FF]+',term))
                    for r in rows('''SELECT pages.page_no,pages.text,documents.title FROM pages_fts JOIN pages ON pages_fts.rowid=pages.id JOIN documents ON pages.document_id=documents.id WHERE pages_fts MATCH ? LIMIT 30''',(qq,)):
                        pos=r['text'].lower().find(term.lower()); r['snippet']=(r['text'][max(0,pos-140):pos+360] if pos>=0 else r['text'][:500]); r['layer']='ENCYCLOPEDIA'; out.append(r)
                except sqlite3.OperationalError: pass
                for r in rows('SELECT claim_id,statement,status,source_layer,evidence FROM claims WHERE statement LIKE ? OR evidence LIKE ? LIMIT 30',(f'%{term}%',f'%{term}%')):
                    r['snippet']=r['statement']; r['layer']=r['source_layer']; out.append(r)
                for r in rows('SELECT title,authors,year,reading_status,notes,url FROM references_tbl WHERE title LIKE ? OR notes LIKE ? LIMIT 30',(f'%{term}%',f'%{term}%')):
                    r['snippet']=r['notes']; r['layer']='LITERATURE'; out.append(r)
            if layer!='ALL': out=[x for x in out if x.get('layer')==layer]
            return send_json(self,{'query':term,'results':out[:60]})
        if u.path=='/api/claims': return send_json(self,rows('SELECT * FROM claims ORDER BY id DESC'))
        if u.path=='/api/references': return send_json(self,rows('SELECT * FROM references_tbl ORDER BY id DESC'))
        if u.path=='/api/gates': return send_json(self,rows('SELECT * FROM literature_gates ORDER BY id DESC'))
        if u.path=='/api/pages':
            n=int((q.get('page') or ['1'])[0]); return send_json(self,one('SELECT pages.page_no,pages.text,documents.title FROM pages JOIN documents ON pages.document_id=documents.id WHERE pages.page_no=? ORDER BY documents.id LIMIT 1',(n,)) or {})
        self.send_error(404)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,default=8765); ap.add_argument('--no-browser',action='store_true'); ap.add_argument('--rebuild',action='store_true'); args=ap.parse_args()
    if args.rebuild and DB.exists(): DB.unlink()
    init_db(); import_pdf(ROOT/'imports'/'encyclopedia_vol1.pdf')
    url=f'http://127.0.0.1:{args.port}'
    if not args.no_browser: threading.Timer(.8,lambda:webbrowser.open(url)).start()
    print(f'ANT-PVG Local Observatory running at {url}')
    ThreadingHTTPServer(('127.0.0.1',args.port),H).serve_forever()
if __name__=='__main__': main()
