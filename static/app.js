const app = document.querySelector('#app');
const viewTitle = document.querySelector('#viewTitle');

const TITLES = {
  dashboard: 'لوحة القيادة', search: 'البحث الموحد', results: 'نتائج الموسوعة',
  integrity: 'تكامل الحوكمة', claims: 'سجل الادعاءات', gates: 'بوابات الأدبيات',
  refs: 'المراجع', reader: 'قارئ الموسوعة',
};
const COUNT_LABELS = {
  chapters: 'فصول', units: 'وحدات نصية', results: 'نتائج معرَّفة',
  citable: 'قابلة للاستشهاد', bib: 'مراجع ببليوغرافية', claims: 'ادعاءات',
  gates: 'بوابات', findings: 'ملاحظات تكامل',
};
const SEVERITY = { CRITICAL: 'حرج', HIGH: 'مرتفع', MEDIUM: 'متوسط', LOW: 'منخفض', INFO: 'إخباري' };

let current = 'dashboard';

const esc = s => (s ?? '').toString().replace(/[&<>"']/g,
  m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));

async function api(url, opt) {
  const r = await fetch(url, opt);
  const j = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
  if (!r.ok) throw new Error(j.error || r.status);
  return j;
}

const layerClass = x => x === 'ENCYCLOPEDIA' ? 'enc' : x === 'LITERATURE' ? 'lit' : 'model';

// --------------------------------------------------- إظهار الرياضيات (KaTeX)

const KATEX_OPTS = {
  delimiters: [
    { left: '\\[', right: '\\]', display: true },
    { left: '$$', right: '$$', display: true },
    { left: '\\(', right: '\\)', display: false },
  ],
  throwOnError: false, errorColor: '#ff9db1', strict: false,
};

/** يُظهِر الرياضيات داخل عنصر. يعمل بلا شبكة لأن KaTeX مُضمَّن محليًا. */
function typeset(el) {
  if (!el || typeof renderMathInElement !== 'function') return;
  el.querySelectorAll('.math-display[data-tex]').forEach(node => {
    try {
      katex.render(node.dataset.tex, node, { ...KATEX_OPTS, displayMode: true });
    } catch (e) { node.textContent = node.dataset.tex; }
  });
  try { renderMathInElement(el, KATEX_OPTS); } catch (e) { /* يبقى النص الخام */ }
}

/** يحوّل كتل الوحدة المهيكلة إلى HTML: فقرات، معادلات، قوائم، وبيئات مسمّاة. */
function blocksHtml(blocks) {
  return (blocks || []).map(b => {
    switch (b.t) {
      case 'p':
        return `<p>${esc(b.text)}</p>`;
      case 'math':
        return `<div class="math-display" data-tex="${esc(b.tex)}"></div>`;
      case 'pre':
        return `<pre class="tex-pre">${esc(b.text)}</pre>`;
      case 'list':
        return `<${b.ordered ? 'ol' : 'ul'}>${
          b.items.map(i => `<li>${blocksHtml(i)}</li>`).join('')}</${b.ordered ? 'ol' : 'ul'}>`;
      case 'env': {
        const meta = [
          b.result_id ? `<span class="badge">${esc(b.result_id)}</span>` : '',
          b.status ? `<span class="badge">${esc(b.status)}</span>` : '',
        ].join('');
        return `<section class="env env-${esc(b.env)}">
          <h5>${esc(b.label)}${b.title ? ` — ${esc(b.title)}` : ''}${meta}</h5>
          ${blocksHtml(b.blocks)}</section>`;
      }
      default:
        return '';
    }
  }).join('');
}

function badges(x) {
  const b = [];
  if (x.layer || x.source_layer)
    b.push(`<span class="tag ${layerClass(x.layer || x.source_layer)}">${esc(x.layer || x.source_layer)}</span>`);
  if (x.status) b.push(`<span class="badge">${esc(x.status)}</span>`);
  if (x.novelty_status) b.push(`<span class="badge">${esc(x.novelty_status)}</span>`);
  if (x.citable !== undefined)
    b.push(`<span class="badge ${x.citable ? 'ok' : 'no'}">${x.citable ? 'قابلة للاستشهاد' : 'غير قابلة للاستشهاد'}</span>`);
  return `<div class="meta">${b.join('')}</div>`;
}

const row = (x, body = '') =>
  `<div class="row"><h4>${esc(x.title || x.claim_id || x.gate_id || x.result_id || 'نتيجة')}</h4>${body}${badges(x)}</div>`;

function field(id, ph, tag = 'input', extra = '') {
  return tag === 'textarea'
    ? `<textarea id="${id}" class="${extra}" placeholder="${ph}"></textarea>`
    : `<input id="${id}" class="${extra}" placeholder="${ph}">`;
}

const $ = id => document.getElementById(id);

// ------------------------------------------------------------------- العروض

async function dashboard() {
  const d = await api('/api/dashboard');
  const sev = Object.entries(d.severity || {})
    .map(([k, v]) => `<span class="badge sev-${k}">${SEVERITY[k] || k}: ${v}</span>`).join(' ');
  app.innerHTML = `
    <div class="cards">${Object.entries(d.counts).map(([k, v]) =>
      `<div class="card"><strong>${v}</strong><small>${COUNT_LABELS[k] || k}</small></div>`).join('')}</div>
    <div class="panel"><h3>طبقات المصادر</h3><div class="table">
      ${d.sources.map(s => row(s, `<p>${esc(s.authority)}</p>${s.path ? `<p class="path">${esc(s.path)}</p>` : ''}`)).join('')}
    </div></div>
    <div class="panel"><h3>تكامل الحوكمة ${sev}</h3><div class="table">
      ${d.top_findings.length
        ? d.top_findings.map(f => `<div class="row"><h4>${esc(f.subject)}</h4>
            <p>${esc(f.detail)}</p><div class="meta">
            <span class="badge sev-${f.severity}">${SEVERITY[f.severity] || f.severity}</span>
            <span class="badge">${esc(f.code)}</span></div></div>`).join('')
        : '<p class="muted">لا ملاحظات حرجة.</p>'}
    </div></div>
    <div class="panel"><h3>حالات النتائج</h3><div class="table">
      ${d.by_status.slice(0, 12).map(s =>
        `<div class="row inline"><span>${esc(s.s)}</span><b>${s.n}</b></div>`).join('')}
    </div></div>
    <div class="panel"><h3>الادعاءات الأخيرة</h3><div class="table">
      ${d.recent_claims.map(x => row(x, `<p>${esc(x.statement)}</p>`)).join('') || '<p class="muted">لا ادعاءات.</p>'}
    </div></div>`;
}

function searchView() {
  app.innerHTML = `
    <div class="panel"><div class="searchbar">
      <input id="q" placeholder="ابحث في الموسوعة والنتائج والادعاءات والأدبيات">
      <select id="layer"><option>ALL</option><option>ENCYCLOPEDIA</option>
        <option>MODEL_SYNTHESIS</option><option>LITERATURE</option></select>
      <button class="action" id="go">بحث</button>
    </div><p class="muted">البحث يطبّع الهمزات والتشكيل، فيتطابق «الأعداد» مع «الأعداد».</p></div>
    <div id="results" class="panel"><h3>النتائج</h3></div>`;
  const run = async () => {
    const d = await api(`/api/search?q=${encodeURIComponent($('q').value)}&layer=${$('layer').value}`);
    $('results').innerHTML = `<h3>${d.results.length} نتيجة</h3><div class="table">${
      d.results.map(x => row(x, `<p>${esc(x.snippet || '')}</p>${
        x.chapter ? `<small>الفصل ${esc(x.chapter)}</small>` : ''}`)).join('') ||
      '<p class="muted">لا نتائج.</p>'}</div>`;
  };
  $('go').onclick = run;
  $('q').onkeydown = e => { if (e.key === 'Enter') run(); };
  $('q').focus();
}

async function results() {
  const d = await api('/api/results');
  app.innerHTML = `
    <div class="panel"><div class="searchbar">
      <input id="rq" placeholder="ترشيح بالمعرّف أو العنوان">
      <select id="rc"><option value="">كل حالات الاستشهاد</option>
        <option value="1">قابلة للاستشهاد</option><option value="0">غير قابلة</option></select>
      <button class="action" id="rgo">ترشيح</button>
    </div></div>
    <div class="panel"><div id="rlist" class="table"></div></div>`;
  const draw = () => {
    const t = $('rq').value.trim(), c = $('rc').value;
    const f = d.filter(x =>
      (!t || (x.result_id + ' ' + (x.title || '')).includes(t)) &&
      (c === '' || String(x.citable) === c));
    $('rlist').innerHTML = `<p class="muted">${f.length} من ${d.length}</p>` + f.map(x => row(
      { title: x.result_id, citable: x.citable },
      `<p><b>${esc(x.title || '—')}</b></p>
       <p>${esc((x.statement || '').slice(0, 300))}</p>
       <div class="meta"><span class="badge">الفصل ${esc(x.chapter)}</span>
        <span class="badge">${esc(x.kind)}</span>
        <span class="badge">مخطوط: ${esc(x.tex_status || '—')}</span>
        <span class="badge">سجل: ${esc(x.registry_status || '—')}</span></div>`)).join('');
  };
  $('rgo').onclick = draw;
  $('rq').onkeydown = e => { if (e.key === 'Enter') draw(); };
  draw();
}

async function integrity() {
  const d = await api('/api/integrity');
  app.innerHTML = `
    <div class="panel"><h3>ملخص الفحوص</h3><div class="table">
      ${d.by_code.sort((a, b) => b.n - a.n).map(c =>
        `<div class="row inline"><span><span class="badge sev-${c.severity}">${SEVERITY[c.severity] || c.severity}</span>
          ${esc(c.code)}</span><b>${c.n}</b></div>`).join('')}
    </div></div>
    <div class="panel"><h3>الملاحظات (${d.findings.length})</h3><div class="table">
      ${d.findings.map(f => `<div class="row"><h4>${esc(f.subject)}</h4>
        <p>${esc(f.detail)}</p><div class="meta">
        <span class="badge sev-${f.severity}">${SEVERITY[f.severity] || f.severity}</span>
        <span class="badge">${esc(f.code)}</span></div></div>`).join('')}
    </div></div>`;
}

const STATUSES = ['MODEL-SYNTHESIS', 'KNOWN', 'KNOWN-IN-EQUIVALENT-FORM',
  'CANDIDATE-GAP', 'PROVED-HERE', 'OPEN'];

async function claims() {
  const d = await api('/api/claims');
  app.innerHTML = `
    <div class="panel"><h3>إضافة ادعاء</h3><div class="formgrid">
      ${field('st', 'نص الادعاء', 'input', 'wide')}
      ${field('dom', 'المجال')}
      <select id="sl"><option>MODEL_SYNTHESIS</option><option>ENCYCLOPEDIA</option>
        <option>LITERATURE</option></select>
      <select id="cs">${STATUSES.map(s => `<option>${s}</option>`).join('')}</select>
      ${field('nov', 'حالة الجدة')}
      ${field('ev', 'الدليل — اذكر معرّف ANT عند الإسناد إلى الموسوعة', 'textarea', 'wide')}
      <button id="add" class="action wide">إضافة</button>
    </div><p class="muted">لا تُقبل حالة KNOWN دون إسناد إلى نتيجة معتمدة أو مرجع خارجي.</p>
    <p id="cerr" class="err"></p></div>
    <div class="panel"><div class="table">${d.map(x => row(x, `
      <p>${esc(x.statement)}</p><p class="muted">${esc(x.evidence)}</p>
      <div class="inline-form">
        <select data-claim="${esc(x.claim_id)}" class="cstat">
          ${STATUSES.map(s => `<option${s === x.status ? ' selected' : ''}>${s}</option>`).join('')}
        </select>
        <button class="action small csave" data-claim="${esc(x.claim_id)}">حفظ الحالة</button>
      </div>`)).join('') || '<p class="muted">لا ادعاءات.</p>'}</div></div>`;

  $('add').onclick = async () => {
    $('cerr').textContent = '';
    try {
      await api('/api/claims', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          statement: $('st').value, domain: $('dom').value, source_layer: $('sl').value,
          status: $('cs').value, novelty_status: $('nov').value || 'UNCERTIFIED',
          evidence: $('ev').value,
        }),
      });
      render();
    } catch (e) { $('cerr').textContent = e.message; }
  };
  document.querySelectorAll('.csave').forEach(b => b.onclick = async () => {
    const id = b.dataset.claim;
    const sel = document.querySelector(`.cstat[data-claim="${CSS.escape(id)}"]`);
    try {
      await api(`/api/claims/${encodeURIComponent(id)}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: sel.value }),
      });
      render();
    } catch (e) { alert(e.message); }
  });
}

const GATE_STATUSES = ['OPEN', 'REVIEW-IN-PROGRESS', 'CLOSED-COVERED', 'CLOSED-GAP'];

async function gates() {
  const d = await api('/api/gates');
  app.innerHTML = `
    <div class="panel"><h3>فتح بوابة جديدة</h3><div class="formgrid">
      ${field('gt', 'عنوان البوابة')}${field('gq', 'السؤال البحثي')}
      ${field('gk', 'الكلمات المفتاحية', 'input', 'wide')}
      ${field('gs', 'النطاق', 'textarea', 'wide')}
      <button id="ga" class="action wide">فتح البوابة</button>
    </div><p id="gerr" class="err"></p></div>
    <div class="panel"><div class="table">${d.map(x => row(x, `
      <p>${esc(x.question)}</p>
      <p><b>النطاق:</b> ${esc(x.scope)}</p><p><b>الحكم:</b> ${esc(x.verdict)}</p>
      <div class="inline-form">
        <select class="gstat" data-gate="${esc(x.gate_id)}">
          ${GATE_STATUSES.map(s => `<option${s === x.status ? ' selected' : ''}>${s}</option>`).join('')}
        </select>
        <input class="gverd" data-gate="${esc(x.gate_id)}" value="${esc(x.verdict)}" placeholder="الحكم">
        <button class="action small gsave" data-gate="${esc(x.gate_id)}">حفظ</button>
      </div>`)).join('')}</div></div>`;

  $('ga').onclick = async () => {
    $('gerr').textContent = '';
    try {
      await api('/api/gates', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: $('gt').value, question: $('gq').value,
          keywords: $('gk').value, scope: $('gs').value }),
      });
      render();
    } catch (e) { $('gerr').textContent = e.message; }
  };
  document.querySelectorAll('.gsave').forEach(b => b.onclick = async () => {
    const id = b.dataset.gate, sel = q => document.querySelector(`${q}[data-gate="${CSS.escape(id)}"]`);
    try {
      await api(`/api/gates/${encodeURIComponent(id)}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: sel('.gstat').value, verdict: sel('.gverd').value }),
      });
      render();
    } catch (e) { alert(e.message); }
  });
}

async function refs() {
  const [own, bib] = await Promise.all([api('/api/references'), api('/api/bib')]);
  app.innerHTML = `
    <div class="panel"><h3>إضافة مرجع</h3><div class="formgrid">
      ${field('rt', 'العنوان', 'input', 'wide')}${field('ra', 'المؤلفون')}
      ${field('ry', 'السنة')}${field('rv', 'الدورية/الناشر')}
      ${field('rd', 'DOI')}${field('ru', 'الرابط')}
      <select id="rr"><option>DISCOVERED</option><option>ABSTRACT-READ</option>
        <option>FULLY-READ</option><option>VERIFIED</option></select>
      ${field('rn', 'الملاحظات', 'textarea', 'wide')}
      <button id="radd" class="action wide">إضافة</button>
    </div><p id="rerr" class="err"></p></div>
    <div class="panel"><h3>مراجع المرصد (${own.length})</h3><div class="table">
      ${own.map(x => row({ title: x.title, status: x.reading_status },
        `<p>${esc(x.authors)} (${esc(x.year)}) — ${esc(x.venue)}</p><p>${esc(x.notes)}</p>`)).join('')
        || '<p class="muted">لا مراجع بعد.</p>'}</div></div>
    <div class="panel"><h3>ببليوغرافيا الموسوعة (${bib.length})</h3><div class="table">
      ${bib.map(x => row({ title: x.key, layer: 'LITERATURE' },
        `<p>${esc(x.author)} (${esc(x.year)}). ${esc(x.title)}. ${esc(x.journal)}</p>
         <div class="meta"><span class="badge">${esc(x.bib_file)}</span>
         <span class="badge ${x.cited ? 'ok' : 'no'}">${x.cited ? 'مستشهد به' : 'غير مستشهد'}</span>
         ${x.doi ? `<span class="badge">${esc(x.doi)}</span>` : ''}</div>`)).join('')}</div></div>`;

  $('radd').onclick = async () => {
    $('rerr').textContent = '';
    try {
      await api('/api/references', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: $('rt').value, authors: $('ra').value, year: $('ry').value,
          venue: $('rv').value, doi: $('rd').value, url: $('ru').value,
          reading_status: $('rr').value, notes: $('rn').value }),
      });
      render();
    } catch (e) { $('rerr').textContent = e.message; }
  };
}

async function reader() {
  const chs = await api('/api/chapters');
  app.innerHTML = `
    <div class="panel"><div class="searchbar">
      <select id="ch">${chs.map(c =>
        `<option value="${c.id}">الفصل ${c.number ?? '—'} — ${esc(c.title)}</option>`).join('')}</select>
      <select id="sec"></select>
      <button id="load" class="action">عرض</button>
    </div></div>
    <div class="panel"><div id="page" class="reader">اختر فصلًا.</div></div>`;
  let units = [];
  const loadCh = async () => {
    units = await api('/api/units?chapter_id=' + $('ch').value);
    $('sec').innerHTML = units.map((u, i) =>
      `<option value="${i}">${esc(u.heading || 'قسم ' + u.ord)}</option>`).join('');
    show();
  };
  const show = () => {
    const u = units[$('sec').value | 0];
    const page = $('page');
    if (!u) { page.textContent = 'لا نص.'; return; }
    let blocks = null;
    try { blocks = JSON.parse(u.blocks || 'null'); } catch (e) { /* نص خام */ }
    page.innerHTML = blocks
      ? `<h4 class="sec-head">${esc(u.heading || '')}</h4>${blocksHtml(blocks)}`
      : `<pre>${esc(u.text)}</pre>`;
    page.scrollTop = 0;
    typeset(page);
  };
  $('ch').onchange = loadCh;
  $('sec').onchange = show;
  $('load').onclick = show;
  if (chs.length) loadCh(); else $('page').textContent = 'لم تُستورد الموسوعة بعد.';
}

// -------------------------------------------------------------------- التوجيه

const VIEWS = { dashboard, search: searchView, results, integrity, claims, gates, refs, reader };

async function render() {
  viewTitle.textContent = TITLES[current];
  document.querySelectorAll('nav button')
    .forEach(b => b.classList.toggle('active', b.dataset.view === current));
  try {
    await VIEWS[current]();
    typeset(app);   // نصوص النتائج ومقتطفات البحث تحمل رياضيات سطرية أيضًا
  } catch (e) {
    app.innerHTML = `<div class="panel"><p class="err">${esc(e.message)}</p></div>`;
  }
}

document.querySelectorAll('nav button')
  .forEach(b => b.onclick = () => { current = b.dataset.view; render(); });
$('refresh').onclick = render;
$('ingest').onclick = async () => {
  const btn = $('ingest');
  btn.disabled = true; btn.textContent = 'جارٍ الاستيراد…';
  try {
    const r = await api('/api/ingest', { method: 'POST' });
    alert(`تم: ${r.chapters} فصلًا، ${r.units} وحدة، ${r.results} نتيجة، ${r.findings} ملاحظة.`);
    render();
  } catch (e) { alert(e.message); }
  finally { btn.disabled = false; btn.textContent = 'إعادة الاستيراد'; }
};
render();
