const ENCYCLOPEDIA_ROOT = 'D:/analytic-number-theory-encyclopedia-ar';
const app = document.querySelector('#app');
const viewTitle = document.querySelector('#viewTitle');

const TITLES = {
  dashboard: 'لوحة القيادة', search: 'البحث الموحد', results: 'نتائج الموسوعة',
  model: 'المعرفة المعيارية', integrity: 'تكامل الحوكمة', claims: 'سجل الادعاءات',
  gates: 'بوابات الأدبيات', refs: 'المراجع', graph: 'شبكة المعرفة',
  pvg: 'مدونة بحث PVG', reader: 'قارئ الموسوعة',
};
const NOTE_KINDS = {
  method: 'طريقة', context: 'سياق', caveat: 'محذور', heuristic: 'حدس',
  gap: 'فجوة', definition: 'تعريف', theorem: 'مبرهنة',
};
const COUNT_LABELS = {
  chapters: 'فصول', units: 'وحدات نصية', results: 'نتائج معرَّفة',
  citable: 'قابلة للاستشهاد', bib: 'مراجع ببليوغرافية',
  model_notes: 'ملاحظات معيارية', coverage_gaps: 'فجوات تغطية',
  claims: 'ادعاءات', gates: 'بوابات', findings: 'ملاحظات تكامل',
};
/** يصيّر Markdown السجلات: عناوين وجداول وقوائم واقتباسات وشيفرة.
 *  مُصغَّر عمدًا — سجلات البوابات تكتبها أنت بصيغة معروفة، ولا داعي لمكتبة
 *  كاملة تُضاف إلى أصول تعمل دون اتصال. */
function renderMarkdown(md) {
  const inline = t => esc(t)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,
      (m, txt, href) => /^https?:\/\//.test(href)
        ? `<a href="${esc(href)}" target="_blank" rel="noopener">${txt}</a>` : txt);

  const out = [];
  const lines = md.split('\n');
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    if (/^```/.test(line)) {
      const buf = [];
      for (i++; i < lines.length && !/^```/.test(lines[i]); i++) buf.push(lines[i]);
      i++;
      out.push(`<pre class="tex-pre">${esc(buf.join('\n'))}</pre>`);
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      const level = Math.min(heading[1].length + 2, 6);
      out.push(`<h${level} class="sec-head">${inline(heading[2])}</h${level}>`);
      i++;
      continue;
    }
    if (/^\s*\|/.test(line) && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1] || '')) {
      const cells = l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => inline(c.trim()));
      const head = cells(line);
      i += 2;
      const body = [];
      for (; i < lines.length && /^\s*\|/.test(lines[i]); i++) body.push(cells(lines[i]));
      out.push(`<div class="tablewrap"><table>
        <thead><tr>${head.map(c => `<th>${c}</th>`).join('')}</tr></thead>
        <tbody>${body.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody>
      </table></div>`);
      continue;
    }
    if (/^\s*>/.test(line)) {
      const buf = [];
      for (; i < lines.length && /^\s*>/.test(lines[i]); i++) buf.push(lines[i].replace(/^\s*>\s?/, ''));
      out.push(`<blockquote>${inline(buf.join(' '))}</blockquote>`);
      continue;
    }
    const listMatch = /^\s*([-*]|\d+\.)\s+/;
    if (listMatch.test(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const items = [];
      for (; i < lines.length && listMatch.test(lines[i]); i++) {
        items.push(`<li>${inline(lines[i].replace(listMatch, ''))}</li>`);
      }
      out.push(`<${ordered ? 'ol' : 'ul'}>${items.join('')}</${ordered ? 'ol' : 'ul'}>`);
      continue;
    }
    if (/^\s*---+\s*$/.test(line)) { out.push('<hr>'); i++; continue; }
    if (!line.trim()) { i++; continue; }

    const para = [];
    for (; i < lines.length && lines[i].trim()
           && !/^(#{1,4}\s|\s*\||\s*>|```|\s*---+\s*$)/.test(lines[i])
           && !listMatch.test(lines[i]); i++) para.push(lines[i]);
    out.push(`<p>${inline(para.join(' '))}</p>`);
  }
  return out.join('');
}

const NODE_TYPES = {
  result: 'نتيجة', claim: 'ادعاء', gate: 'بوابة',
  reference: 'مرجع', model_note: 'ملاحظة معيارية',
};
const LINK_RELATIONS = [
  'DEPENDS-ON', 'CITES', 'SUPPORTED-BY', 'GENERALIZES',
  'SPECIALIZES', 'CONTRADICTS', 'RELATES-TO',
];

function nodeBadges(x) {
  return [
    `<span class="badge">${esc(NODE_TYPES[x.node_type] || x.node_type)}</span>`,
    x.exists ? '' : '<span class="badge no">طرف معلَّق</span>',
    x.status ? `<span class="badge">${esc(x.status)}</span>` : '',
    x.citable === false ? '<span class="badge no">لا يُستشهد به</span>'
      : x.citable === true ? '<span class="badge ok">قابل للاستشهاد</span>' : '',
  ].join('');
}

function edgeRow(e) {
  const arrow = e.direction === 'outgoing' ? '←' : '→';
  return `<div class="row edge${e.exists ? '' : ' dangling'}">
    <h4>${arrow} ${esc(e.relation)} — ${esc(e.key)}</h4>
    ${e.label ? `<p>${esc(e.label)}</p>` : ''}
    ${e.note ? `<p class="muted">${esc(e.note)}</p>` : ''}
    <div class="meta">${nodeBadges(e)}</div></div>`;
}

async function graph() {
  const links = await api('/api/links');
  app.innerHTML = `
    <div class="panel"><h3>استكشاف الجوار</h3><div class="searchbar">
      <input id="gk" placeholder="مفتاح العقدة، مثل CLAIM-0001 أو ANT-THM-06-01">
      <select id="gt"><option value="">استنتج النوع</option>
        ${Object.entries(NODE_TYPES).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select>
      <button class="action" id="ggo">اعرض</button>
    </div><p class="muted">كل طرف يُحلّ إلى كائنه، فيظهر إن كان معلَّقًا أو غير قابل
    للاستشهاد.</p></div>
    <div id="hood" class="panel"><p class="muted">اختر عقدة.</p></div>

    <div class="panel"><h3>إضافة رابط</h3><div class="formgrid">
      <select id="lft">${Object.entries(NODE_TYPES).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select>
      ${field('lfk', 'مفتاح المصدر')}
      <select id="lr">${LINK_RELATIONS.map(r => `<option>${r}</option>`).join('')}</select>
      <select id="ltt">${Object.entries(NODE_TYPES).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select>
      ${field('ltk', 'مفتاح الهدف')}
      ${field('ln', 'ملاحظة')}
      <button id="ladd" class="action wide">أضف</button>
    </div><p id="lerr" class="err"></p></div>

    <div class="panel"><h3>اشتقاق من نصوص الادعاءات</h3>
      <p class="muted">يستخرج روابط <code>DEPENDS-ON</code> من معرّفات
      <code>ANT-*</code> المذكورة في الادعاءات. عمل صريح لا تلقائي: ذكرُ معرّف في
      نص ليس إعلانَ اعتماد.</p>
      <button id="lderive" class="action">اشتق الروابط</button></div>

    <div class="panel"><h3>كل الروابط (${links.length})</h3><div class="table">
      ${links.map(l => `<div class="row"><h4>${esc(l.from_key)} —${esc(l.relation)}→ ${esc(l.to_key)}</h4>
        ${l.note ? `<p class="muted">${esc(l.note)}</p>` : ''}
        <div class="meta"><span class="badge">${esc(NODE_TYPES[l.from_type] || l.from_type)}</span>
        <span class="badge">${esc(NODE_TYPES[l.to_type] || l.to_type)}</span></div></div>`).join('')
        || '<p class="muted">لا روابط بعد.</p>'}
    </div></div>`;

  const show = async () => {
    const key = $('gk').value.trim();
    if (!key) return;
    const t = $('gt').value ? `&node_type=${$('gt').value}` : '';
    try {
      const d = await api(`/api/links/neighbourhood?key=${encodeURIComponent(key)}${t}`);
      $('hood').innerHTML = `
        <h3>${esc(d.node.key)}</h3>
        ${d.node.label ? `<p>${esc(d.node.label)}</p>` : ''}
        <div class="meta">${nodeBadges(d.node)}</div>
        <h4 class="sec-head">صادر (${d.outgoing.length})</h4>
        <div class="table">${d.outgoing.map(edgeRow).join('') || '<p class="muted">لا شيء.</p>'}</div>
        <h4 class="sec-head">وارد (${d.incoming.length})</h4>
        <div class="table">${d.incoming.map(edgeRow).join('') || '<p class="muted">لا شيء.</p>'}</div>`;
      typeset($('hood'));
    } catch (e) { $('hood').innerHTML = `<p class="err">${esc(e.message)}</p>`; }
  };
  $('ggo').onclick = show;
  $('gk').onkeydown = e => { if (e.key === 'Enter') show(); };

  $('ladd').onclick = async () => {
    $('lerr').textContent = '';
    try {
      await api('/api/links', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_type: $('lft').value, from_key: $('lfk').value.trim(),
          relation: $('lr').value,
          to_type: $('ltt').value, to_key: $('ltk').value.trim(),
          note: $('ln').value || null,
        }),
      });
      render();
    } catch (e) { $('lerr').textContent = e.message; }
  };
  $('lderive').onclick = async () => {
    try {
      const r = await api('/api/links/derive-from-claims', { method: 'POST' });
      alert(r.created ? `اشتُق ${r.created} رابطًا.` : 'لا روابط جديدة.');
      render();
    } catch (e) { alert(e.message); }
  };
}

const READING = ['DISCOVERED', 'ABSTRACT-READ', 'FULLY-READ', 'VERIFIED'];
const RELATIONS = ['COVERS', 'PARTIAL', 'ADJACENT', 'CONTRADICTS', 'NOT-RELEVANT'];
// حالات القراءة التي تكفي لإسناد حكم بوابة؛ يطابقها الخادم في governance.py
const READ_ENOUGH = ['FULLY-READ', 'VERIFIED'];
const SEVERITY = { CRITICAL: 'حرج', HIGH: 'مرتفع', MEDIUM: 'متوسط', LOW: 'منخفض', INFO: 'إخباري' };

let current = 'dashboard';

const esc = s => (s ?? '').toString().replace(/[&<>"']/g,
  m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));

async function api(url, opt) {
  const r = await fetch(url, opt);
  const j = await r.json().catch(() => null);
  if (!r.ok) {
    // FastAPI يضع سبب الرفض في detail، وهو نص القاعدة التي مُنعت المخالفة بها.
    const detail = j && (j.detail ?? j.error);
    throw new Error(
      typeof detail === 'string' ? detail
        : Array.isArray(detail) ? detail.map(d => d.msg || JSON.stringify(d)).join('؛ ')
        : `HTTP ${r.status}`);
  }
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
  if (x.novelty_note) b.push(`<span class="badge">${esc(x.novelty_note)}</span>`);
  if (x.citable !== undefined)
    b.push(`<span class="badge ${x.citable ? 'ok' : 'no'}">${x.citable ? 'قابلة للاستشهاد' : 'غير قابلة للاستشهاد'}</span>`);
  return `<div class="meta">${b.join('')}</div>`;
}

const row = (x, body = '') =>
  `<div class="row"><h4>${esc(x.title || x.claim_key || x.gate_key || x.result_key || 'نتيجة')}</h4>${body}${badges(x)}</div>`;

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
    <div class="panel"><h3>مصدر الموسوعة</h3><div class="table">
      <div class="row"><h4>مراجعة Git للمصدر</h4>
        <p class="path">${esc(d.revision || 'لم يُستورد بعد')}</p></div>
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
    const d = await api(`/api/search/corpus?q=${encodeURIComponent($('q').value)}${$('layer').value === 'ALL' ? '' : '&source_layer=' + $('layer').value}`);
    $('results').innerHTML = `<h3>${d.results.length} نتيجة</h3><div class="table">${
      d.results.map(x => row(x, `<p>${esc(x.snippet || '')}</p>${
        x.chapter_number ? `<small>الفصل ${esc(x.chapter_number)}</small>` : ''}`)).join('') ||
      '<p class="muted">لا نتائج.</p>'}</div>`;
    typeset($('results'));
  };
  $('go').onclick = run;
  $('q').onkeydown = e => { if (e.key === 'Enter') run(); };
  $('q').focus();
}

async function results() {
  const d = await api('/api/encyclopedia/results');
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
      (!t || (x.result_key + ' ' + (x.title || '')).includes(t)) &&
      (c === '' || String(x.citable ? 1 : 0) === c));
    $('rlist').innerHTML = `<p class="muted">${f.length} من ${d.length}</p>` + f.map(x => row(
      { title: x.result_key, citable: x.citable },
      `<p><b>${esc(x.title || '—')}</b></p>
       <p>${esc((x.statement || '').slice(0, 300))}</p>
       <div class="meta"><span class="badge">الفصل ${esc(x.chapter_number)}</span>
        <span class="badge">${esc(x.kind)}</span>
        <span class="badge">مخطوط: ${esc(x.tex_status || '—')}</span>
        <span class="badge">سجل: ${esc(x.registry_status || '—')}</span></div>`)).join('');
  };
  $('rgo').onclick = draw;
  $('rq').onkeydown = e => { if (e.key === 'Enter') draw(); };
  draw();
}

async function model() {
  const d = await api('/api/model-synthesis/notes');
  const card = n => `<div class="row note${n.is_gap ? ' gap' : ''}">
    <h4>${esc(n.note_key)} — ${esc(n.title)}</h4>
    <div class="note-body">${blocksHtml(JSON.parse(n.blocks_json || '[]'))}</div>
    <div class="meta">
      <span class="tag model">MODEL_SYNTHESIS</span>
      <span class="badge">${esc(NOTE_KINDS[n.kind] || n.kind)}</span>
      <span class="badge no">لا يُستشهد بها</span>
      ${n.is_gap ? '<span class="badge sev-HIGH">فجوة تغطية</span>' : ''}
      ${n.anchors ? `<span class="badge ok">مسنَدة إلى ${esc(n.anchors)}</span>` : ''}
      ${n.literature_hint ? `<span class="badge">تلميح غير محقق: ${esc(n.literature_hint)}</span>` : ''}
    </div></div>`;

  app.innerHTML = `
    <div class="panel warn-panel">
      <h3>طبقة المعرفة المعيارية</h3>
      <p>معرفة رياضية مولَّدة، سلطتها <b>UNVERIFIED_UNTIL_SOURCED</b>. تصلح خريطةً
      تدلّ على الموضع وقائمةَ تحقق قبل البحث وتنبيهًا إلى مزلق. لا تصلح للاستشهاد،
      ويمنع المرصد آليًا استناد أي ادعاء إليها. وأسماء الأوراق المذكورة تلميحات بحث
      غير محققة يجب التثبت منها عبر DOI أو الناشر.</p>
    </div>
    <div class="panel"><h3>حسب المجال</h3><div class="table">
      ${(d.by_domain || []).map(x => `<div class="row inline"><span>${esc(x.domain)}</span>
        <b>${x.n}${x.gaps ? ` <span class="badge sev-HIGH">${x.gaps} فجوة</span>` : ''}</b>
      </div>`).join('')}
    </div></div>
    <div class="panel"><div class="searchbar">
      <select id="nk"><option value="">كل الأنواع</option>
        ${(d.by_kind || []).map(k => `<option value="${esc(k.kind)}">${esc(NOTE_KINDS[k.kind] || k.kind)} (${k.n})</option>`).join('')}</select>
      <select id="ng"><option value="">الكل</option>
        <option value="1">فجوات التغطية فقط</option>
        <option value="0">المسنَدة فقط</option></select>
      <button class="action" id="ngo">ترشيح</button>
    </div></div>
    <div class="panel"><div id="nlist" class="table">${d.map(card).join('')}</div></div>`;

  $('ngo').onclick = () => {
    const k = $('nk').value, g = $('ng').value;
    const f = d.filter(n =>
      (!k || n.kind === k) && (g === '' || String(n.is_gap) === g));
    $('nlist').innerHTML = `<p class="muted">${f.length} من ${d.length}</p>`
      + f.map(card).join('');
    typeset($('nlist'));
  };
}

async function integrity() {
  const d = await api('/api/integrity/findings');
  app.innerHTML = `
    <div class="panel"><h3>ملخص الفحوص</h3><div class="table">
      ${(d.by_code || []).sort((a, b) => b.n - a.n).map(c =>
        `<div class="row inline"><span><span class="badge sev-${c.severity}">${SEVERITY[c.severity] || c.severity}</span>
          ${esc(c.code)}</span><b>${c.n}</b></div>`).join('')}
    </div></div>
    <div class="panel"><h3>الملاحظات (${d.length})</h3><div class="table">
      ${d.map(f => `<div class="row"><h4>${esc(f.subject)}</h4>
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
      <p>${esc(x.statement)}</p><p class="muted">${esc(x.evidence_note)}</p>
      <div class="inline-form">
        <select data-claim="${esc(x.claim_key)}" class="cstat">
          ${STATUSES.map(s => `<option${s === x.status ? ' selected' : ''}>${s}</option>`).join('')}
        </select>
        <button class="action small csave" data-claim="${esc(x.claim_key)}">حفظ الحالة</button>
      </div>`)).join('') || '<p class="muted">لا ادعاءات.</p>'}</div></div>`;

  $('add').onclick = async () => {
    $('cerr').textContent = '';
    try {
      await api('/api/claims', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          statement: $('st').value, domain: $('dom').value, source_layer: $('sl').value,
          status: $('cs').value, novelty_note: $('nov').value,
          evidence_note: $('ev').value,
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
const VERDICTS = ['NOT-ASSESSED', 'KNOWN', 'EQUIVALENT', 'PARTIAL', 'NOT-FOUND-YET'];

async function gates() {
  const [d, refsList] = await Promise.all([
    api('/api/gates'), api('/api/references')]);
  const linked = await Promise.all(
    d.map(g => api(`/api/gates/${encodeURIComponent(g.gate_key)}/references`)));

  app.innerHTML = `
    <div class="panel"><h3>فتح بوابة جديدة</h3><div class="formgrid">
      ${field('gt', 'عنوان البوابة')}${field('gq', 'السؤال البحثي')}
      <button id="ga" class="action wide">فتح البوابة</button>
    </div><p class="muted">البوابة بلا مراجع مربوطة سؤال بلا مسح: لا تُغلق بحكم
    <code>KNOWN</code> إلا بمرجع مربوط بعلاقة <code>COVERS</code> وحالته مقروءة.</p>
    <p id="gerr" class="err"></p></div>

    ${d.map((x, i) => `<div class="panel"><h3>${esc(x.title)}</h3>
      <p>${esc(x.research_question)}</p>
      <div class="meta"><span class="badge">${esc(x.gate_key)}</span>
        <span class="badge">${esc(x.status)}</span>
        <span class="badge">${esc(x.verdict || 'NOT-ASSESSED')}</span>
        <span class="badge ${linked[i].length ? 'ok' : 'no'}">${linked[i].length} مرجعًا مربوطًا</span>
      </div>
      <div class="table" style="margin-top:10px">
        ${linked[i].map(l => `<div class="row inline">
          <span>${esc(l.title)}
            <span class="badge">${esc(l.relation)}</span>
            <span class="badge ${READ_ENOUGH.includes(l.reading_status) ? 'ok' : 'no'}">${esc(l.reading_status)}</span>
          </span>
          <button class="action small gunlink" data-gate="${esc(x.gate_key)}"
            data-ref="${esc(l.reference_key)}">فك الربط</button>
        </div>`).join('') || '<p class="muted">لا مراجع مربوطة.</p>'}
      </div>
      <div class="inline-form">
        <select class="glink-ref" data-gate="${esc(x.gate_key)}">
          ${refsList.map(r => `<option value="${esc(r.reference_key)}">${esc(r.title)}</option>`).join('')
            || '<option value="">لا مراجع في السجل</option>'}
        </select>
        <select class="glink-rel" data-gate="${esc(x.gate_key)}">
          ${RELATIONS.map(v => `<option>${v}</option>`).join('')}
        </select>
        <button class="action small glink" data-gate="${esc(x.gate_key)}">ربط مرجع</button>
      </div>
      <div class="inline-form">
        <button class="action small grecord" data-gate="${esc(x.gate_key)}">السجل الدائم</button>
        <select class="gstat" data-gate="${esc(x.gate_key)}">
          ${GATE_STATUSES.map(v => `<option${v === x.status ? ' selected' : ''}>${v}</option>`).join('')}
        </select>
        <select class="gverd" data-gate="${esc(x.gate_key)}">
          ${VERDICTS.map(v => `<option${v === x.verdict ? ' selected' : ''}>${v}</option>`).join('')}
        </select>
        <button class="action small gsave" data-gate="${esc(x.gate_key)}">حفظ</button>
      </div>
      <p class="err" id="gerr-${i}"></p>
      <div class="record" id="grec-${esc(x.gate_key)}"></div>
    </div>`).join('')}`;

  $('ga').onclick = async () => {
    $('gerr').textContent = '';
    try {
      await api('/api/gates', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: $('gt').value, research_question: $('gq').value }),
      });
      render();
    } catch (e) { $('gerr').textContent = e.message; }
  };
  const pick = (cls, key) => document.querySelector(`${cls}[data-gate="${CSS.escape(key)}"]`);
  document.querySelectorAll('.glink').forEach(b => b.onclick = async () => {
    const key = b.dataset.gate;
    const ref = pick('.glink-ref', key).value;
    if (!ref) return alert('أضف مرجعًا إلى السجل أولًا.');
    try {
      await api(`/api/gates/${encodeURIComponent(key)}/references`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reference_key: ref, relation: pick('.glink-rel', key).value }),
      });
      render();
    } catch (e) { alert(e.message); }
  });
  document.querySelectorAll('.gunlink').forEach(b => b.onclick = async () => {
    try {
      const r = await fetch(
        `/api/gates/${encodeURIComponent(b.dataset.gate)}/references/${encodeURIComponent(b.dataset.ref)}`,
        { method: 'DELETE' });
      if (!r.ok) throw new Error('تعذّر فك الربط');
      render();
    } catch (e) { alert(e.message); }
  });
  document.querySelectorAll('.grecord').forEach(b => b.onclick = async () => {
    const key = b.dataset.gate;
    const box = document.getElementById(`grec-${key}`);
    if (box.dataset.open === '1') {
      box.innerHTML = ''; box.dataset.open = '0';
      b.textContent = 'السجل الدائم';
      return;
    }
    try {
      const r = await api(`/api/gates/${encodeURIComponent(key)}/record`);
      box.innerHTML = `<p class="path">${esc(r.path)}</p>${renderMarkdown(r.markdown)}`;
      box.dataset.open = '1';
      b.textContent = 'إخفاء السجل';
      typeset(box);
    } catch (e) {
      box.innerHTML = `<p class="err">${esc(e.message)}</p>`;
      box.dataset.open = '1';
    }
  });
  document.querySelectorAll('.gsave').forEach((b, i) => b.onclick = async () => {
    const key = b.dataset.gate;
    const box = $(`gerr-${i}`);
    if (box) box.textContent = '';
    try {
      await api(`/api/gates/${encodeURIComponent(key)}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: pick('.gstat', key).value, verdict: pick('.gverd', key).value }),
      });
      render();
    } catch (e) { if (box) box.textContent = e.message; else alert(e.message); }
  });
}

async function refs() {
  const [own, bib] = await Promise.all([
    api('/api/references'), api('/api/encyclopedia/bibliography')]);
  const cited = bib.filter(x => x.cited).length;
  app.innerHTML = `
    <div class="panel"><h3>إضافة مرجع إلى سجل المرصد</h3><div class="formgrid">
      ${field('rt', 'العنوان', 'input', 'wide')}${field('ra', 'المؤلفون')}
      ${field('ry', 'السنة')}${field('rv', 'الدورية/الناشر')}
      ${field('rd', 'DOI')}${field('ru', 'الرابط')}
      <select id="rr">${READING.map(x => `<option>${x}</option>`).join('')}</select>
      ${field('rb', 'مفتاح ببليوغرافيا الموسوعة (اختياري)')}
      ${field('rn', 'الملاحظات', 'textarea', 'wide')}
      <button id="radd" class="action wide">إضافة</button>
    </div><p id="rerr" class="err"></p></div>

    <div class="panel"><h3>سجل المرصد (${own.length})</h3><div class="table">
      ${own.map(x => `<div class="row">
        <h4>${esc(x.title)}</h4>
        <p>${esc(x.authors || '')} (${esc(x.year || '')}) — ${esc(x.venue || '')}</p>
        ${x.notes ? `<p class="muted">${esc(x.notes)}</p>` : ''}
        <div class="meta">
          <span class="tag lit">${esc(x.reference_key)}</span>
          <span class="badge ${READ_ENOUGH.includes(x.reading_status) ? 'ok' : 'no'}">${esc(x.reading_status)}</span>
          ${x.doi ? `<span class="badge">${esc(x.doi)}</span>` : ''}
          ${x.bibliography_key ? `<span class="badge">في الموسوعة: ${esc(x.bibliography_key)}</span>` : ''}
        </div>
        <div class="inline-form">
          <select class="rstat" data-ref="${esc(x.reference_key)}">
            ${READING.map(v => `<option${v === x.reading_status ? ' selected' : ''}>${v}</option>`).join('')}
          </select>
          <button class="action small rsave" data-ref="${esc(x.reference_key)}">حفظ حالة القراءة</button>
        </div></div>`).join('') || '<p class="muted">لا مراجع بعد.</p>'}
    </div></div>

    <div class="panel"><h3>ببليوغرافيا الموسوعة (${bib.length})</h3>
      <p class="muted">${cited} مستشهد به، و${bib.length - cited} يظهر عبر
      <code>\nocite{*}</code> فقط.</p>
      <div class="table">
      ${bib.map(x => row({ title: x.entry_key, layer: 'LITERATURE' },
        `<p>${esc(x.author)} (${esc(x.year)}). ${esc(x.title)}. ${esc(x.journal)}</p>
         <div class="meta"><span class="badge">${esc(x.bib_file)}</span>
         <span class="badge ${x.cited ? 'ok' : 'no'}">${x.cited ? 'مستشهد به' : 'غير مستشهد'}</span>
         ${x.aliases ? `<span class="badge">مرادفات: ${esc(x.aliases)}</span>` : ''}</div>`)).join('')}
      </div></div>`;

  $('radd').onclick = async () => {
    $('rerr').textContent = '';
    try {
      await api('/api/references', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: $('rt').value, authors: $('ra').value, year: $('ry').value,
          venue: $('rv').value, doi: $('rd').value, url: $('ru').value,
          reading_status: $('rr').value, notes: $('rn').value,
          bibliography_key: $('rb').value || null,
        }),
      });
      render();
    } catch (e) { $('rerr').textContent = e.message; }
  };
  document.querySelectorAll('.rsave').forEach(b => b.onclick = async () => {
    const key = b.dataset.ref;
    const sel = document.querySelector(`.rstat[data-ref="${CSS.escape(key)}"]`);
    try {
      await api(`/api/references/${encodeURIComponent(key)}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reading_status: sel.value }),
      });
      render();
    } catch (e) { alert(e.message); }
  });
}

async function reader() {
  const chs = await api('/api/encyclopedia/chapters');
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
    units = await api('/api/encyclopedia/units?chapter_id=' + $('ch').value);
    $('sec').innerHTML = units.map((u, i) =>
      `<option value="${i}">${esc(u.heading || 'قسم ' + u.ordinal)}</option>`).join('');
    show();
  };
  const show = () => {
    const u = units[$('sec').value | 0];
    const page = $('page');
    if (!u) { page.textContent = 'لا نص.'; return; }
    let blocks = null;
    try { blocks = JSON.parse(u.blocks_json || 'null'); } catch (e) { /* نص خام */ }
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

// ------------------------------------------------------------------ مدونة PVG

/** طبقة بحثك أنت: داخلية غير منشورة. تُعرض منفصلةً بعلامتها الخاصة لأن
 *  خلطها بالموسوعة أو بالأدبيات هو بعينه ما يمنعه المرصد. */
async function pvg() {
  const [docs, results, visuals] = await Promise.all([
    api('/api/pvg/documents'), api('/api/pvg/results'), api('/api/pvg/visuals'),
  ]);
  const proven = results.filter(r => r.is_proven).length;

  const resultRow = r => `<div class="row">
    <h4>${esc(r.result_key)}</h4>
    <div>${esc(r.statement || '')}</div>
    <div class="meta">
      <span class="tag pvg">PVG_RESEARCH</span>
      <span class="badge">${esc(r.status || 'بلا حالة')}</span>
      ${r.is_proven
        ? '<span class="badge ok">مبرهنة — يجوز البناء عليها بـ PROVED_HERE</span>'
        : '<span class="badge no">ليست برهانًا — لا يُبنى عليها ادعاءُ برهان</span>'}
      <span class="badge">${esc(r.source_file)}</span>
    </div></div>`;

  app.innerHTML = `
    <div class="panel warn-panel">
      <h3>طبقة بحث PVG</h3>
      <p>بحثك أنت، وسلطته <b>INTERNAL_UNPUBLISHED</b>. مبرهنةٌ هنا تعني مبرهنة
      عندنا لا معروفة في الأدبيات، فلا ترفع ادعاءً إلى <code>KNOWN</code> مهما
      كانت قوتها — استعمل <code>PROVED_HERE</code>، أو أضف مرجعًا منشورًا.
      وما حالته <code>FINITE-VERIFIED</code> أو <code>INTERPRETATION</code> أو
      <code>HYPOTHESIS</code> فليس برهانًا، والمرصد يرفض آليًا أن يُبنى عليه
      ادعاءُ برهان: لا يحل الفحص محل البرهان.</p>
    </div>
    <div class="panel"><div class="cards">
      <div class="card"><strong>${docs.length}</strong><small>مستندًا</small></div>
      <div class="card"><strong>${results.length}</strong><small>نتيجة معرَّفة</small></div>
      <div class="card"><strong>${proven}</strong><small>مبرهنة</small></div>
      <div class="card"><strong>${visuals.length}</strong><small>مرئية تفاعلية</small></div>
    </div></div>
    <div class="panel"><h3>المرئيات التفاعلية</h3>
      <p class="muted">تعمل دون اتصال، وكلٌّ منها مربوطة في شبكة المعرفة
      بالنتيجة التي ترسمها.</p>
      <div class="table">${visuals.map(v => `<div class="row inline">
        <a href="${esc(v.url)}" target="_blank" rel="noopener">${esc(v.name)}</a>
        <span class="muted">${Math.round(v.bytes / 1024)} ك.ب</span>
      </div>`).join('')}</div></div>
    <div class="panel"><div class="searchbar">
      <select id="pvgf"><option value="">كل النتائج</option>
        <option value="1">المبرهنة فقط</option>
        <option value="0">ما ليس برهانًا</option></select>
      <button class="action" id="pvggo">ترشيح</button>
    </div>
    <div id="pvglist" class="table">${results.map(resultRow).join('')}</div></div>
    <div class="panel"><h3>المستندات</h3><div class="table">
      ${docs.map(d => `<div class="row inline">
        <span>${esc(d.title)}</span>
        <span class="muted">${d.char_count.toLocaleString('ar')} حرفًا ·
          <code>${esc(d.sha256.slice(0, 12))}</code></span>
      </div>`).join('')}</div></div>`;

  $('pvggo').onclick = () => {
    const f = $('pvgf').value;
    const rows = results.filter(r => f === '' || String(Number(r.is_proven)) === f);
    $('pvglist').innerHTML = `<p class="muted">${rows.length} من ${results.length}</p>`
      + rows.map(resultRow).join('');
    typeset($('pvglist'));
  };
}

// -------------------------------------------------------------------- التوجيه

const VIEWS = { dashboard, search: searchView, results, model, integrity,
                claims, gates, refs, graph, pvg, reader };

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
    const r = await api('/api/encyclopedia/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ repository_root: ENCYCLOPEDIA_ROOT }) });
    alert(`تم: ${r.chapter_count} فصلًا، ${r.unit_count} وحدة، ${r.result_count} نتيجة، ${r.finding_count} ملاحظة.`);
    render();
  } catch (e) { alert(e.message); }
  finally { btn.disabled = false; btn.textContent = 'إعادة الاستيراد'; }
};
render();
