/**
 * Page-type templates. Each template: (data, T) => { html, post? }
 *   html  compact 720x405pt slide for html2pptx
 *   post  async (slide, pptx, placeholders, env) adds charts / tables / diagrams / images
 * T.dn holds the density tokens (low | medium | high). Data shapes: references/layouts.md
 */
const diagrams = require('./diagrams');

const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// **bold** inline markup
const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
const arr = (v) => (Array.isArray(v) ? v : v == null ? [] : [v]);
const hx = (c) => String(c).replace('#', '');
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// ---------- geometry ----------
// Body area (pt) left under the title block, taking kicker / takeaway / source into account
const geom = (T, d) => {
  const n = T.dn;
  const top = n.top + (d.kicker ? n.kicker + 3 : 0) + n.title * 1.2 + (d.subtitle ? n.sub * 1.3 + 2 : 0) + 8 + 1 + 8 + (d.takeaway ? n.take * 1.4 + 14 + 8 : 0);
  const bottom = n.bottom + (d.source ? n.src + 6 : 0);
  return { bw: 720 - 2 * n.margin, bh: 405 - top - bottom, gap: n.gap };
};
const colW = (g, n) => (g.bw - g.gap * (n - 1)) / n;

// Largest font size (pt) in [min,max] at which the texts fit width x height
const estHeight = (T, texts, widthPt, s) => texts.reduce((h, t) => h + Math.max(1, Math.ceil((String(t).length * s * 0.47) / widthPt)) * s * 1.2 + s * T.dn.li, 0);
const fitSize = (T, texts, widthPt, heightPt, o = {}) => {
  const min = o.min ?? T.dn.bodyMin, max = o.max ?? T.dn.bodyMax;
  for (let s = max; s > min; s -= 0.5) if (estHeight(T, texts, widthPt, s) <= heightPt) return s;
  return min;
};
const warnFit = (T, title, texts, w, h, s) => {
  if (estHeight(T, texts, w, s) > h * 1.05) console.warn(`warning: panel "${title || '(untitled)'}" text may overflow at ${s}pt (${T.level} density); shorten it, split the slide, or use a lower density`);
};

// ---------- html building blocks ----------
const shell = (T, d, body, o = {}) => {
  const n = T.dn, m = n.margin;
  const head = `<div style="flex:none;margin:${n.top}pt ${m}pt 0 ${m}pt">
  ${d.kicker ? `<p style="font-size:${n.kicker}pt;font-weight:bold;color:${T.hi};margin-bottom:2pt">${esc(String(d.kicker).toUpperCase())}</p>` : ''}
  <h1 style="font-size:${n.title}pt;font-weight:bold;color:${T.primary}">${esc(d.title)}</h1>
  ${d.subtitle ? `<p style="font-size:${n.sub}pt;color:${T.mid};margin-top:2pt">${esc(d.subtitle)}</p>` : ''}
</div>
<div style="flex:none;margin:8pt ${m}pt 0 ${m}pt;height:1pt;background:${T.line}"></div>
${d.takeaway ? `<div style="flex:none;margin:8pt ${m}pt 0 ${m}pt;background:${T.secondaryLight};border-left:4pt solid ${T.secondary};padding:${Math.round(n.take * 0.35)}pt 10pt"><p style="font-size:${n.take}pt;font-weight:bold;color:${T.ink}">${rich(d.takeaway)}</p></div>` : ''}`;
  const foot = d.source ? `<div style="flex:none;margin:0 ${m}pt ${n.bottom}pt ${m}pt"><p style="font-size:${n.src}pt;color:${T.light}">${esc(d.source)}</p></div>` : '';
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html{background:${o.bg || T.bg}}
body{width:720pt;height:405pt;margin:0;padding:0;background:${o.bg || T.bg};font-family:Arial,sans-serif;display:flex;flex-direction:column}
h1,h2,h3,p,ul,ol{margin:0}
ul,ol{padding-left:14pt}
</style></head><body>${o.bare ? body : `${head}
<div style="flex:1;min-height:0;display:flex;flex-direction:${o.col || o.center ? 'column' : 'row'};${o.center ? 'justify-content:center;' : ''}gap:${n.gap}pt;margin:${n.gap}pt ${m}pt ${d.source ? 4 : n.bottom}pt ${m}pt">${body}</div>${foot}`}
</body></html>`;
};

const row = (T, inner, minH = 0, gap) => `<div style="flex:none;display:flex;flex-direction:row;gap:${gap ?? T.dn.gap}pt;${minH ? `min-height:${Math.round(minH)}pt` : ''}">${inner}</div>`;
const card = (T, inner, o = {}) =>
  `<div style="background:${o.bg || T.alt};${o.accent ? `border-top:3pt solid ${o.accent};` : `border:${o.bw || 1}pt solid ${o.border || T.line};`}border-radius:${o.accent ? 0 : 6}pt;padding:${o.pad || T.dn.pad};flex:${o.flex ?? 1};min-width:0;${o.style || ''}">${inner}</div>`;
const list = (T, items, size, color) =>
  `<ul style="font-size:${size}pt;color:${color || T.ink}">${arr(items).map((i) => `<li style="margin-bottom:${Math.round(size * T.dn.li)}pt">${rich(i)}</li>`).join('')}</ul>`;
const cardTitle = (T, t, color, size) => { const s = size ?? T.dn.cardTitle; return `<p style="font-size:${s}pt;font-weight:bold;color:${color || T.ink};margin-bottom:${Math.round(s * 0.3)}pt">${esc(t)}</p>`; };
const accents = (T) => [T.primary, T.secondary, T.accent, T.primaryDark];
const placeholder = (id, extra = '') => `<div id="${id}" class="placeholder" style="flex:1;min-width:0;min-height:0;${extra}"></div>`;
const callout = (T, label, text) => `<div style="flex:none;background:${T.secondary};border-radius:4pt;padding:${Math.round(T.dn.take * 0.5)}pt 12pt;display:flex;gap:10pt;align-items:center">
  <p style="font-size:${T.dn.take}pt;font-weight:bold;color:${T.ink}">${esc(label)}</p><p style="font-size:${T.dn.take}pt;color:${T.ink}">${rich(text)}</p></div>`;
const circle = (T, n, size, bg) => `<div style="flex:none;width:${size}pt;height:${size}pt;border-radius:50%;background:${bg || T.primary};display:flex;align-items:center;justify-content:center"><p style="font-size:${Math.round(size * 0.45)}pt;font-weight:bold;color:${T.onPrimary};text-align:center">${esc(n)}</p></div>`;
const asideBlock = (T, d, title, items, w) => {
  const g = geom(T, d), width = w ?? T.dn.aside;
  const sz = fitSize(T, arr(items), width - 24, g.bh * 0.8, { min: T.dn.bodyMin, max: Math.min(T.dn.bodyMax, 13) });
  return card(T, `${cardTitle(T, title, T.primary, sz + 1.5)}${list(T, items, sz)}`, { flex: 'none', style: `width:${width}pt;align-self:flex-start` });
};
const statTile = (T, s, o = {}) => card(T, `<p style="font-size:${T.dn.kicker}pt;font-weight:bold;color:${T.mid}">${esc(String(s.label).toUpperCase())}</p>
  <p style="font-size:${o.size ?? T.dn.stat}pt;font-weight:bold;color:${T.primary}">${esc(s.value)}</p>
  ${s.delta ? `<p style="font-size:${T.dn.kicker + 0.5}pt;font-weight:bold;color:${T.hi}">${esc(s.delta)}</p>` : ''}`, { pad: o.pad || T.dn.pad });

// ---------- native chart / table helpers ----------
function addChart(slide, pptx, area, spec, T) {
  const typeMap = { bar: 'BAR', hbar: 'BAR', line: 'LINE', area: 'AREA', pie: 'PIE', doughnut: 'DOUGHNUT', radar: 'RADAR' };
  const type = spec.type || 'bar';
  const series = spec.series.map((s) => ({ name: s.name, labels: spec.labels, values: s.values }));
  const multi = series.length > 1, round = type === 'pie' || type === 'doughnut';
  const fs = T.dn.chart;
  const palette = [T.primary, T.accent, T.secondary, '9AA5B1', T.primaryDark].map(hx);
  const o = {
    x: area.x, y: area.y, w: area.w, h: area.h, chartColors: round ? palette.slice(0, spec.labels.length) : palette.slice(0, series.length),
    catAxisLabelFontSize: fs, valAxisLabelFontSize: fs, catAxisLabelFontFace: T.font, valAxisLabelFontFace: T.font,
    showLegend: multi || round, legendPos: round ? 'r' : 'b', legendFontSize: fs, legendFontFace: T.font,
    valGridLine: { color: hx(T.subtle), size: 0.75 }, catGridLine: { style: 'none' },
    dataLabelFontSize: fs, dataLabelColor: hx(T.ink),
    showTitle: !!spec.title, title: spec.title, titleFontSize: fs + 2, titleColor: hx(T.ink), titleFontFace: T.font,
  };
  if (type === 'bar' || type === 'hbar') Object.assign(o, { barDir: type === 'hbar' ? 'bar' : 'col', barGapWidthPct: 60 });
  if (type === 'line') Object.assign(o, { lineSize: 2.5, lineDataSymbolSize: 7 });
  if (type === 'radar') Object.assign(o, { radarStyle: 'marker', catGridLine: { color: hx(T.subtle), size: 0.75 }, showValue: false });
  if (round) Object.assign(o, { showPercent: true, showValue: false, dataLabelColor: 'FFFFFF', dataLabelFontBold: true });
  else if (!multi && type !== 'radar' && spec.dataLabels !== false) Object.assign(o, { showValue: true, dataLabelPosition: type === 'line' ? 't' : 'outEnd' });
  if (spec.xTitle) Object.assign(o, { showCatAxisTitle: true, catAxisTitle: spec.xTitle, catAxisTitleFontSize: fs });
  if (spec.yTitle) Object.assign(o, { showValAxisTitle: true, valAxisTitle: spec.yTitle, valAxisTitleFontSize: fs });
  if (spec.min != null) o.valAxisMinVal = spec.min;
  if (spec.max != null) o.valAxisMaxVal = spec.max;
  slide.addChart(pptx.charts[typeMap[type]], series, o);
}

// header: string[]; rows: (cell[] | {group})[]; cell: string | number | boolean | {text,fill,color,bold}
function addTable(slide, pptx, area, spec, T) {
  const n = T.dn, nCols = spec.header.length;
  if (spec.rows.length > n.tableRows) console.warn(`warning: table has ${spec.rows.length} rows; "${T.level}" density suggests at most ${n.tableRows}`);
  const nRows = spec.rows.length + 1;
  const fs = spec.fontSize || (nRows <= 6 ? n.tableMax : nRows <= 10 ? (n.tableMin + n.tableMax) / 2 : n.tableMin);
  const align = spec.align || spec.header.map((_, i) => (i === 0 ? 'left' : 'center'));
  const hl = spec.highlightCol;
  const cell = (v, ci, ri) => {
    const o = { align: align[ci], bold: ci === 0 && spec.firstColBold !== false, color: hx(T.ink) };
    if (ri % 2 === 1 && spec.zebra !== false) o.fill = { color: hx(T.alt) };
    if (ci === hl) o.fill = { color: hx(T.secondaryLight) };
    let text = v;
    if (v && typeof v === 'object') { text = v.text; if (v.fill) o.fill = { color: hx(v.fill) }; if (v.color) o.color = hx(v.color); if (v.bold != null) o.bold = v.bold; }
    if (text === true) { text = '●'; o.color = hx(T.accent); o.bold = false; }
    else if (text === false || text === '-') { text = '–'; o.color = hx(T.light); o.bold = false; }
    return { text: String(text ?? ''), options: o };
  };
  const head = spec.header.map((h, ci) => ({ text: String(h), options: {
    bold: true, align: align[ci], fill: { color: hx(ci === hl ? T.secondary : T.primary) }, color: hx(ci === hl ? T.onSecondary : T.onPrimary) } }));
  let ri = 0;
  const body = spec.rows.map((r) => {
    if (r && r.group) { ri = 0; return [{ text: r.group, options: { colspan: nCols, bold: true, align: 'left', color: hx(T.primary), fill: { color: hx(T.primaryLight) } } }]; }
    const cells = r.map((v, ci) => cell(v, ci, ri));
    ri++;
    return cells;
  });
  const rows = [head, ...body];
  const weights = spec.colW || spec.header.map((_, i) => (i === 0 ? 1.6 : 1));
  const tot = weights.reduce((s, v) => s + v, 0);
  const colWs = weights.map((v) => (v / tot) * area.w);
  // PowerPoint grows a row when its text wraps; estimate that so the table stays inside its area
  const rowNeed = (r, f) => (r[0] && r[0].options && r[0].options.colspan) ? 0.0 : Math.max(...r.map((c, ci) => {
    const lines = Math.max(1, Math.ceil((String(c.text).length * f * 0.47) / 72 / Math.max(0.2, colWs[ci] - 0.18)));
    return (lines * f * 1.2) / 72 + 0.09;
  }));
  const base = Math.min(spec.maxRowH || n.tableRowMax, Math.max(n.tableRowMin, area.h / rows.length));
  const heights = (f) => rows.map((r) => Math.max(base, rowNeed(r, f)));
  let f = fs;
  while (heights(f).reduce((a, v) => a + v, 0) > area.h && f > 8.5) f -= 0.5;
  const rowH = heights(f);
  if (rowH.reduce((a, v) => a + v, 0) > area.h * 1.03) console.warn(`warning: table (${rows.length} rows) may overflow its area at ${f}pt; cut rows or shorten cells`);
  slide.addTable(rows, {
    x: area.x, y: area.y, w: area.w, colW: colWs, rowH,
    fontFace: T.font, fontSize: f, valign: 'middle', margin: [0, 0.08, 0, 0.08], // table margins are inches
    border: { type: 'solid', pt: 0.75, color: hx(T.line) },
  });
}

const matrixSpec = (d) => ({
  header: ['', ...d.products],
  rows: d.rows.map((r) => (r.group ? r : [r.name, ...r.values])),
  highlightCol: d.recommended != null ? d.recommended + 1 : undefined,
  colW: d.colW || [1.7, ...d.products.map(() => 1)],
});

function drawDiagram(slide, pptx, area, dg, T, env) {
  if ((dg.mode || 'native') === 'mermaid') return env.addMermaid(slide, area, dg.mermaid);
  const fn = { sequence: diagrams.sequence, class: diagrams.classDiagram, er: diagrams.erDiagram, flow: diagrams.flow, state: diagrams.stateDiagram, architecture: diagrams.architecture }[dg.kind];
  if (!fn) throw new Error(`Unknown diagram kind "${dg.kind}"`);
  return fn(slide, pptx, area, dg.data, T);
}

// ---------- panel engine ----------
// Layout grammar: rows ";" · columns "|" · stacked panels "/" · numbers are panel indexes. "0|1/2" = one tall panel left, two stacked right.
const PRESETS = { '2x1': '0|1', '3x1': '0|1|2', '2x2': '0/2|1/3', '1+2': '0|1/2', '2+1': '0/1|2', '1+3': '0|1/2/3', '3+1': '0/1/2|3', '1/2': '0;1|2', '2/1': '0|1;2', '3x2': '0/3|1/4|2/5' };
const parseLayout = (s) => (PRESETS[s] || s).split(';').map((r) => r.split('|').map((c) => c.split('/').map(Number)));

const frame = (T, p, inner, o = {}) => `<div style="flex:1;min-height:0;min-width:0;display:flex;flex-direction:column;background:${o.bg || T.alt};border:1pt solid ${o.border || T.line};border-radius:6pt;padding:${T.dn.pad}">
  ${p.title ? `<p style="flex:none;font-size:${T.dn.panelTitle}pt;font-weight:bold;color:${o.titleColor || T.primary};margin-bottom:${Math.round(T.dn.panelTitle * 0.35)}pt">${esc(p.title)}</p>` : ''}${inner}</div>`;
const fill = (inner) => `<div style="flex:1;min-height:0;display:flex;flex-direction:column;justify-content:flex-start">${inner}</div>`;

// usable text box inside a panel frame (padding + title row), in pt
const innerBox = (T, z, indent = 0) => {
  const [py, px] = T.dn.pad.split(' ').map(parseFloat);
  return { w: z.w - 2 * px - 2 - indent, h: z.h - 2 * py - 2 - (T.dn.panelTitle * 1.3 + 4) };
};
const panelMax = (T) => Math.min(T.dn.bodyMax + 1.5, 15);
const TAGS = (T) => ({ adopt: [T.primary, T.onPrimary], trial: [T.accent, T.onPrimary], assess: [T.secondary, T.onSecondary], hold: ['D7DEE8', T.mid] });

// Each kind: (T, p, id, size{w,h}) => { html, post? }
const KINDS = {
  chart: (T, p, id) => ({ html: frame(T, p, placeholder(id)), post: (s, pp, phs) => addChart(s, pp, phs.find((x) => x.id === id), p.chart || p, T) }),
  table: (T, p, id) => ({ html: frame(T, p, placeholder(id)), post: (s, pp, phs) => addTable(s, pp, phs.find((x) => x.id === id), { header: p.header || p.columns, rows: p.rows, align: p.align, colW: p.colW, highlightCol: p.highlightCol, fontSize: p.fontSize, maxRowH: p.maxRowH }, T) }),
  diagram: (T, p, id) => ({ html: frame(T, p, placeholder(id)), post: (s, pp, phs, env) => drawDiagram(s, pp, phs.find((x) => x.id === id), p.diagram || p, T, env) }),
  image: (T, p, id) => ({ html: frame(T, p, placeholder(id)), post: (s, pp, phs, env) => env.addImage(s, phs.find((x) => x.id === id), p.path, p.fit) }),
  bullets: (T, p, id, z) => {
    const { w, h } = innerBox(T, z, 14), sz = z.size ?? fitSize(T, arr(p.items), w, h, { max: panelMax(T) });
    warnFit(T, p.title, arr(p.items), w, h, sz);
    return { html: frame(T, p, fill(list(T, p.items, sz)), { titleColor: p.color || T.primary }) };
  },
  text: (T, p, id, z) => {
    const paras = arr(p.text), { w, h } = innerBox(T, z), sz = z.size ?? fitSize(T, paras, w, h, { max: panelMax(T) });
    warnFit(T, p.title, paras, w, h, sz);
    return { html: frame(T, p, fill(paras.map((t) => `<p style="font-size:${sz}pt;color:${T.ink};margin-bottom:${Math.round(sz * T.dn.li)}pt">${rich(t)}</p>`).join(''))) };
  },
  stats: (T, p, id, z) => {
    const st = arr(p.stats), size = clamp(Math.min(T.dn.stat, (z.w / st.length) / 5), 14, T.dn.stat);
    return { html: frame(T, p, fill(row(T, st.map((s) => statTile(T, s, { size, pad: '5pt 8pt' })).join(''), 0, 6))) };
  },
  callout: (T, p) => ({ html: callout(T, p.label || 'NOTE', p.text) }),
  chips: (T, p) => {
    const tg = TAGS(T), fs = Math.max(9, T.dn.bodyMin);
    const chips = arr(p.items).map((i) => {
      const it = typeof i === 'string' ? { name: i } : i, [bg, fg] = it.tag ? tg[it.tag] || [T.bg, T.ink] : [T.bg, T.ink];
      return `<div style="background:${bg};border:1pt solid ${it.tag ? bg : T.line};border-radius:9pt;padding:2pt 8pt"><p style="font-size:${fs}pt;color:${fg};font-weight:${it.tag ? 'bold' : 'normal'}">${esc(it.name)}</p></div>`;
    }).join('');
    return { html: frame(T, p, `<div style="display:flex;flex-direction:row;flex-wrap:wrap;gap:5pt;align-content:flex-start">${chips}</div>${p.note ? `<p style="font-size:${T.dn.src}pt;color:${T.mid};margin-top:6pt">${esc(p.note)}</p>` : ''}${p.points ? `<div style="margin-top:8pt">${list(T, p.points, Math.max(9, T.dn.bodyMin))}</div>` : ''}`) };
  },
  scorecard: (T, p, id) => ({
    html: frame(T, p, placeholder(id)),
    post: (s, pp, phs) => {
      const a = phs.find((x) => x.id === id), items = p.items, max = p.max || 5;
      const rh = Math.min(0.36, a.h / items.length), lw = a.w * 0.38, vw = 0.4, bw = a.w - lw - vw - 0.1;
      const fs = clamp(T.dn.bodyMin, 9, 11);
      items.forEach((it, i) => {
        const y = a.y + i * rh + (a.h - rh * items.length) / 2, bh = Math.min(0.14, rh * 0.45);
        s.addText(it.name, { x: a.x, y, w: lw, h: rh, fontFace: T.font, fontSize: fs, color: hx(T.ink), valign: 'middle', align: 'left', margin: 0 });
        s.addShape(pp.ShapeType.rect, { x: a.x + lw + 0.05, y: y + (rh - bh) / 2, w: bw, h: bh, fill: { color: hx(T.subtle) }, line: { color: hx(T.subtle), width: 0 } });
        s.addShape(pp.ShapeType.rect, { x: a.x + lw + 0.05, y: y + (rh - bh) / 2, w: Math.max(0.02, bw * (it.score / (it.max || max))), h: bh, fill: { color: hx(it.color || T.primary) }, line: { color: hx(it.color || T.primary), width: 0 } });
        s.addText(String(it.score), { x: a.x + a.w - vw, y, w: vw, h: rh, fontFace: T.font, fontSize: fs, bold: true, color: hx(T.ink), valign: 'middle', align: 'right', margin: 0 });
      });
    },
  }),
};

// Compose panels into html + post. spec: { layout, panels, rowFlex, colFlex }
function composePanels(T, d, spec, g = geom(T, d)) {
  const rows = parseLayout(spec.layout || PRESETS['2x1']);
  const panels = spec.panels;
  const rowFlex = spec.rowFlex || rows.map(() => 1), gap = T.dn.gap;
  const rsum = rowFlex.reduce((s, v) => s + v, 0);
  const posts = [];
  const html = rows.map((cols, ri) => {
    const cf = cols.map((stack, ci) => (spec.colFlex && rows.length === 1 ? spec.colFlex[ci] : Math.max(...stack.map((i) => panels[i].w || 1))));
    const csum = cf.reduce((s, v) => s + v, 0);
    const rowH = (g.bh - gap * (rows.length - 1)) * rowFlex[ri] / rsum;
    const cells = cols.map((stack, ci) => {
      const w = (g.bw - gap * (cols.length - 1)) * cf[ci] / csum;
      const hs = stack.map((i) => panels[i].h || 1), hsum = hs.reduce((s, v) => s + v, 0);
      // text panels stacked in one column share the smallest fitted size so they look consistent
      const textual = stack.filter((i) => panels[i].kind === 'bullets' || panels[i].kind === 'text');
      const stackSize = textual.length > 1 ? Math.min(...textual.map((i) => {
        const q = panels[i], zz = { w, h: (rowH - gap * (stack.length - 1)) * (q.h || 1) / hsum };
        const b = innerBox(T, zz, q.kind === 'bullets' ? 14 : 0);
        return fitSize(T, q.kind === 'bullets' ? arr(q.items) : arr(q.text), b.w, b.h, { max: panelMax(T) });
      })) : undefined;
      const inner = stack.map((i, si) => {
        const p = panels[i], id = `p${i}`;
        const k = KINDS[p.kind];
        if (!k) throw new Error(`Unknown panel kind "${p.kind}". Known: ${Object.keys(KINDS).join(', ')}`);
        const r = k(T, p, id, { w, h: (rowH - gap * (stack.length - 1)) * hs[si] / hsum, size: textual.includes(i) ? stackSize : undefined });
        if (r.post) posts.push(r.post);
        return p.kind === 'callout' ? r.html : `<div style="flex:${hs[si]};min-height:0;display:flex;flex-direction:column">${r.html}</div>`;
      }).join('');
      return `<div style="flex:${cf[ci]};min-width:0;display:flex;flex-direction:column;gap:${gap}pt">${inner}</div>`;
    }).join('');
    return `<div style="flex:${rowFlex[ri]};min-height:0;display:flex;flex-direction:row;gap:${gap}pt">${cells}</div>`;
  }).join('');
  return { html, post: async (s, p, phs, env) => { for (const f of posts) await f(s, p, phs, env); } };
}

const withPanels = (T, d, spec, extra = '') => {
  const r = composePanels(T, d, spec);
  return { html: shell(T, d, r.html + extra, { col: true }), post: r.post };
};
const verdictBar = (T, d) => (d.verdict ? callout(T, d.verdict.label || 'VERDICT', d.verdict.text) : '');

// ---------- templates ----------
const T_ = {};

T_.title = (d, T) => {
  const hs = arr(d.highlights);
  const right = hs.length
    ? `<div style="flex:none;width:210pt;background:${T.primary};padding:0 22pt;display:flex;flex-direction:column;justify-content:center;gap:14pt">
        ${hs.map((h) => `<div><p style="font-size:10pt;font-weight:bold;color:${T.secondary}">${esc(h.label)}</p><p style="font-size:12pt;color:${T.onPrimary};margin-top:2pt">${esc(h.text)}</p></div>`).join('')}</div>`
    : `<div style="flex:none;width:36pt;background:${T.primary}"></div>`;
  const body = `<div style="flex:1;display:flex;flex-direction:row">
    <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 40pt">
      <div style="width:48pt;height:5pt;background:${T.secondary}"></div>
      <h1 style="font-size:34pt;font-weight:bold;color:${T.primary};margin-top:14pt">${esc(d.title)}</h1>
      ${d.subtitle ? `<p style="font-size:15pt;color:${T.mid};margin-top:10pt">${esc(d.subtitle)}</p>` : ''}
      ${d.meta ? `<p style="font-size:10.5pt;color:${T.light};margin-top:22pt">${esc(d.meta)}</p>` : ''}
    </div>${right}</div>`;
  return { html: shell(T, d, body, { bare: true }) };
};

T_.section = (d, T) => ({ html: shell(T, d, `<div style="flex:1;display:flex;flex-direction:row;align-items:center;padding:0 50pt;gap:24pt">
  ${d.number != null ? `<p style="font-size:64pt;font-weight:bold;color:${T.secondary}">${esc(d.number)}</p>` : ''}
  <div style="flex:1"><h1 style="font-size:30pt;font-weight:bold;color:${T.onPrimary}">${esc(d.title)}</h1>
  ${d.subtitle ? `<p style="font-size:14pt;color:${T.primaryLight};margin-top:8pt">${esc(d.subtitle)}</p>` : ''}</div></div>`, { bare: true, bg: T.primary }) });

T_.agenda = (d, T) => {
  const items = d.items.map((i) => (typeof i === 'string' ? { title: i } : i));
  const two = items.length > 4, half = two ? Math.ceil(items.length / 2) : items.length;
  const big = Math.min(15, T.dn.bodyMax + (half <= 4 ? 0 : -2));
  const rowEl = (it, n) => `<div style="flex:none;background:${T.alt};border:1pt solid ${T.line};border-radius:6pt;padding:${Math.round(big * 0.7)}pt 12pt;display:flex;flex-direction:row;align-items:center;gap:12pt">
    ${circle(T, n + 1, Math.round(big * 1.8))}<div style="flex:1"><p style="font-size:${big}pt;font-weight:bold;color:${T.ink}">${esc(it.title)}</p>${it.text ? `<p style="font-size:${big - 3}pt;color:${T.mid};margin-top:1pt">${esc(it.text)}</p>` : ''}</div></div>`;
  const col = (a, off) => `<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:${T.dn.gap}pt">${a.map((it, i) => rowEl(it, off + i)).join('')}</div>`;
  return { html: shell(T, d, two ? col(items.slice(0, half), 0) + col(items.slice(half), half) : col(items, 0)) };
};

T_.closing = (d, T) => {
  const g = geom(T, d), pts = arr(d.points).map((p) => (typeof p === 'string' ? { text: p } : p));
  const sz = fitSize(T, pts.map((p) => p.text), colW(g, pts.length || 1) - 24, g.bh * 0.4);
  const body = `<div style="flex:none;background:${T.primaryLight};border-left:5pt solid ${T.primary};padding:${Math.round(T.dn.title * 1.4)}pt 24pt">
      <p style="font-size:${Math.round(T.dn.title * 1.3)}pt;font-weight:bold;color:${T.primary}">${esc(d.statement)}</p></div>
    ${row(T, pts.map((p, i) => card(T, `${p.title ? cardTitle(T, p.title, T.ink, sz + 1.5) : ''}<p style="font-size:${sz}pt;color:${T.ink}">${rich(p.text)}</p>`, { accent: accents(T)[i % 4] })).join(''), g.bh * 0.28)}`;
  return { html: shell(T, d, body, { center: true }) };
};

T_.bullets = (d, T) => {
  const g = geom(T, d), items = arr(d.bullets), w = d.aside ? g.bw * 0.65 : g.bw;
  const sz = fitSize(T, items, w, g.bh * 0.9, { max: Math.min(18, T.dn.bodyMax + 2) });
  const main = `<div style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center"><ul style="font-size:${sz}pt;color:${T.ink}">${items.map((b) => `<li style="margin-bottom:${Math.round(sz * 0.6)}pt">${rich(b)}</li>`).join('')}</ul></div>`;
  return { html: shell(T, d, main + (d.aside ? asideBlock(T, d, d.aside.title, d.aside.items) : '')) };
};

T_.columns = (d, T) => {
  const g = geom(T, d), ac = accents(T), n = d.columns.length, w = colW(g, n) - 26;
  const sz = Math.min(...d.columns.map((c) => fitSize(T, [...arr(c.items), ...(c.text ? [c.text] : [])], w, g.bh * T.dn.fill - (c.stat ? 70 : 30), { max: Math.min(16, T.dn.bodyMax) })));
  const cols = d.columns.map((c, i) => card(T, [
    c.label ? `<p style="font-size:${T.dn.kicker}pt;font-weight:bold;color:${T.hi};margin-bottom:3pt">${esc(String(c.label).toUpperCase())}</p>` : '',
    c.stat ? `<p style="font-size:${T.dn.stat + 6}pt;font-weight:bold;color:${T.primary}">${esc(c.stat.value)}</p><p style="font-size:${T.dn.kicker + 0.5}pt;color:${T.mid};margin-bottom:6pt">${esc(c.stat.label)}</p>` : '',
    c.title ? cardTitle(T, c.title, T.ink, sz + 2) : '',
    c.text ? `<p style="font-size:${sz}pt;color:${T.ink}">${rich(c.text)}</p>` : '',
    c.items ? list(T, c.items, sz) : '',
  ].join(''), { accent: ac[i % 4], pad: `${parseInt(T.dn.pad) + 2}pt ${parseInt(T.dn.pad.split(' ')[1]) + 2}pt` })).join('');
  return { html: shell(T, d, row(T, cols, g.bh * T.dn.fill), { center: true }) };
};
T_.twoColumn = T_.columns; T_.threeColumn = T_.columns;

T_.kpi = (d, T) => {
  const tiles = d.stats.map((s) => statTile(T, s)).join('');
  const ins = d.insights ? asideBlock(T, d, d.insightsTitle || 'Takeaways', d.insights) : '';
  const body = `${row(T, tiles)}<div style="flex:1;min-height:0;display:flex;flex-direction:row;gap:${T.dn.gap}pt">${placeholder('chart')}${ins}</div>`;
  return { html: shell(T, d, body, { col: true }), post: (s, p, ph) => addChart(s, p, ph.find((x) => x.id === 'chart'), d.chart, T) };
};

T_.chart = (d, T) => {
  const ins = d.insights ? asideBlock(T, d, d.insightsTitle || 'Takeaways', d.insights, 210) : '';
  return { html: shell(T, d, placeholder('chart') + ins), post: (s, p, ph) => addChart(s, p, ph.find((x) => x.id === 'chart'), d.chart, T) };
};

T_.table = (d, T) => ({
  html: shell(T, d, `${placeholder('tbl')}${d.note ? `<p style="flex:none;font-size:${T.dn.src}pt;color:${T.mid}">${esc(d.note)}</p>` : ''}`, { col: true }),
  post: (s, p, ph) => addTable(s, p, ph.find((x) => x.id === 'tbl'), { header: d.columns, rows: d.rows, align: d.align, colW: d.colW, highlightCol: d.highlightCol, fontSize: d.fontSize }, T),
});

// Product matrix. With chart / insights it becomes a multi-panel page.
T_.comparison = (d, T) => {
  const m = matrixSpec(d);
  if (!d.chart && !d.insights) {
    return { html: shell(T, d, `${placeholder('tbl')}${verdictBar(T, d)}`, { col: true }), post: (s, p, ph) => addTable(s, p, ph.find((x) => x.id === 'tbl'), m, T) };
  }
  const panels = [{ kind: 'table', ...m, w: 2.2 }];
  if (d.chart) panels.push({ kind: 'chart', chart: d.chart, title: d.chart.title ? undefined : d.chartTitle });
  if (d.insights) panels.push({ kind: 'bullets', title: d.insightsTitle || 'Takeaways', items: d.insights });
  const layout = panels.length === 3 ? '0|1/2' : '0|1';
  return withPanels(T, d, { layout, panels }, verdictBar(T, d));
};
T_.comparisonMatrix = T_.comparison;

// Pros / cons, optionally with scores chart, facts table, image, diagram or stats. Extra panels are capped by density.
T_.prosCons = (d, T) => {
  const extras = [];
  if (d.scores) extras.push({ kind: 'chart', chart: { type: 'radar', ...d.scores }, title: d.scores.title ? undefined : 'Scores by criterion' });
  if (d.facts) extras.push({ kind: 'table', header: d.facts.columns, rows: d.facts.rows, colW: d.facts.colW, title: d.facts.title || 'Key facts', w: 1.2, h: 1.8 });
  if (d.diagram) extras.push({ kind: 'diagram', diagram: d.diagram, title: d.diagram.title });
  if (d.image) extras.push({ kind: 'image', path: d.image.path || d.image, fit: d.image.fit, title: d.image.title });
  if (d.stats) extras.push({ kind: 'stats', stats: d.stats });
  const use = extras.slice(0, T.dn.extras);
  const panels = [{ kind: 'bullets', title: d.pros.title || 'Pros', items: d.pros.items, color: T.accent }, { kind: 'bullets', title: d.cons.title || 'Cons', items: d.cons.items, color: T.primary }, ...use];
  const layout = { 0: '0|1', 1: '0/1|2', 2: '0/1|2|3', 3: '0/1|2|3/4' }[use.length] || '0/1|2|3/4';
  const colFlex = use.length === 0 ? [1, 1] : use.length === 1 ? [1, 1.3] : use.length === 2 ? [1.1, 1, 1] : [1, 1, 0.95];
  return withPanels(T, d, { layout, panels, colFlex }, verdictBar(T, d));
};

T_.beforeAfter = (d, T) => {
  const g = geom(T, d), w = (g.bw - 26) / 2 - 26;
  const longer = arr(d.before.items).length >= arr(d.after.items).length ? arr(d.before.items) : arr(d.after.items);
  const sz = fitSize(T, longer, w, g.bh * T.dn.fill - 40, { max: Math.min(17, T.dn.bodyMax + 1) });
  const mk = (x, accent, bg, def) => card(T, `${cardTitle(T, x.title || def, accent, sz + 2)}${list(T, x.items, sz)}`, { accent, bg, pad: `${parseInt(T.dn.pad) + 3}pt ${parseInt(T.dn.pad.split(' ')[1]) + 3}pt` });
  const mid = `<div style="flex:none;width:26pt;display:flex;align-items:center;justify-content:center"><p style="font-size:22pt;font-weight:bold;color:${T.primary}">&#8594;</p></div>`;
  return { html: shell(T, d, row(T, mk(d.before, T.light, T.alt, 'Before') + mid + mk(d.after, T.primary, T.primaryLight, 'After'), g.bh * T.dn.fill) + verdictBar(T, d), { center: true }) };
};

T_.pricingCards = (d, T) => {
  const g = geom(T, d), n = d.plans.length, w = colW(g, n) - 28;
  const sz = Math.min(...d.plans.map((p) => fitSize(T, p.features, w, g.bh * T.dn.fill - 90, { max: Math.min(15, T.dn.bodyMax) })));
  const cards = d.plans.map((p) => card(T, `
    ${p.badge ? `<p style="font-size:${T.dn.kicker}pt;font-weight:bold;color:${T.hi}">${esc(String(p.badge).toUpperCase())}</p>` : ''}
    <p style="font-size:${T.dn.cardTitle + 1.5}pt;font-weight:bold;color:${T.ink}">${esc(p.name)}</p>
    <p style="font-size:${T.dn.stat + 8}pt;font-weight:bold;color:${T.primary};margin-top:2pt">${esc(p.price)}</p>
    <p style="font-size:${T.dn.kicker + 1}pt;color:${T.mid};margin:0 0 8pt 0">${esc([p.unit, p.tagline].filter(Boolean).join(' · '))}</p>
    ${list(T, p.features, sz)}`, p.highlight ? { bg: T.secondaryLight, border: T.secondary, bw: 2 } : {})).join('');
  return { html: shell(T, d, row(T, cards, g.bh * T.dn.fill), { center: true }) };
};

T_.timeline = (d, T) => {
  const g = geom(T, d), n = d.phases.length, w = colW(g, n) - 24;
  const sz = Math.min(...d.phases.map((p) => fitSize(T, [...arr(p.items), ...(p.text ? [p.text] : [])], w, g.bh * T.dn.fill - 60, { max: Math.min(16, T.dn.bodyMax) })));
  const ph = d.phases.map((p) => `<div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:6pt">
    <div style="flex:none;background:${p.status === 'now' ? T.secondary : T.primary};border-radius:4pt;padding:4pt 10pt"><p style="font-size:${sz}pt;font-weight:bold;color:${p.status === 'now' ? T.onSecondary : T.onPrimary}">${esc(p.date)}</p></div>
    ${card(T, `${cardTitle(T, p.title, T.ink, sz + 2)}${p.text ? `<p style="font-size:${sz}pt;color:${T.ink}">${rich(p.text)}</p>` : ''}${p.items ? list(T, p.items, sz) : ''}`, { ...(p.status === 'now' ? { border: T.secondary, bw: 2 } : {}), style: `min-height:${Math.round(g.bh * T.dn.fill * 0.75)}pt` })}</div>`).join('');
  return { html: shell(T, d, row(T, ph), { center: true }) };
};
T_.roadmap = T_.timeline;

T_.process = (d, T) => {
  const g = geom(T, d), n = d.steps.length, w = colW(g, n) - 40;
  const sz = Math.min(...d.steps.map((s) => fitSize(T, [...(s.text ? [s.text] : []), ...arr(s.items)], w, g.bh * T.dn.fill - 70, { max: Math.min(15, T.dn.bodyMax) })));
  const steps = d.steps.map((s, i) => `${i ? `<div style="flex:none;width:14pt;display:flex;align-items:center;justify-content:center"><p style="font-size:16pt;color:${T.accent}">&#8594;</p></div>` : ''}${card(T, `${circle(T, i + 1, 24, accents(T)[i % 3])}<p style="font-size:${sz + 2}pt;font-weight:bold;color:${T.ink};margin-top:8pt">${esc(s.title)}</p>${s.text ? `<p style="font-size:${sz}pt;color:${T.mid};margin-top:4pt">${rich(s.text)}</p>` : ''}${s.items ? list(T, s.items, sz) : ''}`, { style: `min-height:${Math.round(g.bh * T.dn.fill * 0.7)}pt` })}`).join('');
  return { html: shell(T, d, row(T, steps, 0, 0) + (d.callout ? callout(T, d.callout.label || 'TIP', d.callout.text) : ''), { center: true }) };
};

T_.quote = (d, T) => {
  const g = geom(T, d);
  return { html: shell(T, d, `<div style="flex:none;width:6pt;background:${T.secondary}"></div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 10pt">
    <p style="font-size:${fitSize(T, [d.quote], g.bw - 60, g.bh * 0.6, { min: 14, max: 26 })}pt;font-style:italic;color:${T.ink}">${esc(d.quote)}</p>
    <p style="font-size:12pt;font-weight:bold;color:${T.primary};margin-top:14pt">${esc(d.author || '')}</p>
    ${d.role ? `<p style="font-size:10.5pt;color:${T.mid}">${esc(d.role)}</p>` : ''}</div>`) };
};

T_.codeExplain = (d, T) => {
  const g = geom(T, d), lines = Array.isArray(d.code) ? d.code : String(d.code).split('\n');
  const cs = lines.length <= 8 ? 13 : lines.length <= 12 ? 12 : lines.length <= 18 ? 10.5 : 9.5;
  const code = lines.map((l) => {
    const indent = l.length - l.trimStart().length; // leading spaces are trimmed by the converter, so indent with a margin
    return `<p style="font-family:'Courier New';font-size:${cs}pt;color:#E5E7EB;line-height:1.4;margin-left:${(indent * cs * 0.6).toFixed(1)}pt">${l.trim().length ? esc(l.trim()) : '&nbsp;'}</p>`;
  }).join('');
  const pts = arr(d.points), sz = fitSize(T, pts.map((p) => (typeof p === 'string' ? p : `${p.title} ${p.text}`)), g.bw * 0.4, g.bh * 0.85);
  const li = pts.map((p) => `<li style="margin-bottom:${Math.round(sz * 0.6)}pt">${typeof p === 'string' ? rich(p) : `<b>${esc(p.title)}</b> ${rich(p.text)}`}</li>`).join('');
  return { html: shell(T, d, `<div style="flex:1.3;min-width:0;background:${T.ink};border-radius:6pt;padding:12pt 14pt;align-self:flex-start">${code}</div>
    <div style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center"><ol style="font-size:${sz}pt;color:${T.ink}">${li}</ol></div>`) };
};

T_.diagram = (d, T) => {
  const notes = d.notes ? asideBlock(T, d, d.notesTitle || 'Notes', d.notes, Math.min(180, T.dn.aside)) : '';
  const cap = d.caption ? `<p style="flex:none;font-size:${T.dn.src}pt;color:${T.mid}">${esc(d.caption)}</p>` : '';
  const body = `<div style="flex:1;min-height:0;display:flex;flex-direction:row;gap:${T.dn.gap}pt">${placeholder('dia')}${notes}</div>${cap}`;
  return { html: shell(T, d, body, { col: true }), post: async (s, p, ph, env) => drawDiagram(s, p, ph.find((x) => x.id === 'dia'), d, T, env) };
};

// Generic mixed-content grid
T_.panels = (d, T) => withPanels(T, d, { layout: d.layout || '2x1', panels: d.panels, rowFlex: d.rowFlex, colFlex: d.colFlex }, verdictBar(T, d));

// ---------- Tech Insight report types ----------
T_.insightSummary = (d, T) => {
  const g = geom(T, d), f = d.findings;
  const sz = fitSize(T, f.map((x) => x.text || ''), g.bw * 0.62, (g.bh * 0.85) / f.length - 20, { max: Math.min(14, T.dn.bodyMax) });
  const rows = f.map((x, i) => `<div style="flex:1;min-height:0;background:${T.alt};border:1pt solid ${T.line};border-radius:6pt;padding:${T.dn.pad};display:flex;flex-direction:row;align-items:center;gap:${T.dn.gap + 4}pt">
    ${circle(T, i + 1, Math.round(T.dn.cardTitle * 2), accents(T)[i % 3])}
    <div style="flex:1;min-width:0"><p style="font-size:${sz + 1.5}pt;font-weight:bold;color:${T.ink}">${esc(x.title)}</p>${x.text ? `<p style="font-size:${sz}pt;color:${T.mid};margin-top:2pt">${rich(x.text)}</p>` : ''}</div>
    ${x.stat ? `<div style="flex:none;width:${Math.round(g.bw * 0.17)}pt;background:${T.bg};border:1pt solid ${T.line};border-radius:4pt;padding:4pt 6pt"><p style="font-size:${T.dn.stat}pt;font-weight:bold;color:${T.primary};text-align:center">${esc(x.stat.value)}</p><p style="font-size:${T.dn.kicker}pt;color:${T.mid};text-align:center">${esc(x.stat.label)}</p></div>` : ''}</div>`).join('');
  const body = `<div style="flex:1;min-height:0;display:flex;flex-direction:column;gap:${T.dn.gap}pt">${rows}</div>${d.sowhat ? callout(T, d.sowhat.label || 'SO WHAT', d.sowhat.text) : ''}`;
  return { html: shell(T, d, body, { col: true }) };
};

T_.techDeepDive = (d, T) => {
  const c = d.concept || {}, left = [];
  if (c.text) left.push({ kind: 'text', title: c.title || 'Concept', text: c.text });
  if (c.bullets) left.push({ kind: 'bullets', title: c.text ? 'Key points' : (c.title || 'Concept'), items: c.bullets });
  left[0].w = 1;
  const L = left.length;
  const visual = d.image ? { kind: 'image', path: d.image.path || d.image, fit: d.image.fit, title: d.image.title } : { kind: 'diagram', diagram: d.diagram, title: d.diagram?.title };
  const panels = [...left, { ...visual, w: 1.6 }];
  let layout = `${left.map((_, i) => i).join('/')}|${L}`, rowFlex;
  if (d.metrics) { panels.push({ kind: 'stats', stats: d.metrics }); layout += `;${L + 1}`; rowFlex = [3.4, 1]; }
  return withPanels(T, d, { layout, panels, rowFlex });
};

T_.benchmark = (d, T) => {
  const panels = [{ kind: 'chart', chart: d.chart, w: 1.3 }, { kind: 'table', title: d.table.title || 'Results', header: d.table.columns, rows: d.table.rows, colW: d.table.colW, align: d.table.align, highlightCol: d.table.highlightCol, maxRowH: 0.4 }];
  if (d.findings) panels.push({ kind: 'bullets', title: d.findingsTitle || 'Findings', items: d.findings });
  const extra = d.method ? `<p style="flex:none;font-size:${T.dn.src}pt;color:${T.mid}"><b>Method.</b> ${rich(d.method)}</p>` : '';
  return withPanels(T, d, { layout: panels.length === 3 ? '0|1/2' : '0|1', panels }, extra);
};

T_.scorecard = (d, T) => {
  const scale = d.scale || 5, cs = d.criteria, opts = d.options;
  const wsum = cs.reduce((s, c) => s + (c.weight ?? 1), 0);
  const totals = opts.map((_, oi) => cs.reduce((s, c) => s + c.scores[oi] * (c.weight ?? 1), 0) / wsum);
  const best = Math.max(...totals);
  const rows = cs.map((c) => {
    const mx = Math.max(...c.scores);
    return [c.name, c.weight != null ? `${Math.round((c.weight / wsum) * 100)}%` : '', ...c.scores.map((s) => ({ text: s, bold: s === mx, fill: s === mx ? T.secondaryLight : undefined }))];
  });
  rows.push(['Weighted total', '100%', ...totals.map((t) => ({ text: t.toFixed(1), bold: true, color: T.primary, fill: t === best ? T.secondaryLight : T.primaryLight }))]);
  const panels = [
    { kind: 'table', title: `Weighted scores (1-${scale})`, header: ['Criterion', 'Weight', ...opts], rows, colW: [1.8, 0.6, ...opts.map(() => 0.8)], w: 1.4, maxRowH: 0.42 },
    { kind: 'chart', title: 'Profile', chart: { type: 'radar', labels: cs.map((c) => c.name), series: opts.map((o, i) => ({ name: o, values: cs.map((c) => c.scores[i]) })) } },
  ];
  const rec = d.recommendation ? callout(T, d.recommendation.label || 'RECOMMENDATION', d.recommendation.text) : '';
  return withPanels(T, d, { layout: '0|1', panels }, rec);
};

T_.riskMatrix = (d, T) => {
  const lv = (v) => (typeof v === 'number' ? (v >= 4 ? 3 : v === 3 ? 2 : 1) : { high: 3, medium: 2, med: 2, low: 1 }[String(v).toLowerCase()] || 1);
  const name = (n) => ['', 'Low', 'Medium', 'High'][n];
  const tone = (n) => ({ fill: [null, T.alt, T.secondaryLight, T.primaryLight][n], color: [null, T.mid, T.hi, T.primary][n] });
  const counts = [0, 0, 0, 0];
  const rows = d.risks.map((r) => {
    const l = lv(r.likelihood), i = lv(r.impact), sev = l * i >= 6 ? 3 : l * i >= 3 ? 2 : 1;
    counts[sev]++;
    return [r.risk, { text: name(l), ...tone(l) }, { text: name(i), ...tone(i) }, { text: name(sev), bold: true, ...tone(sev) }, r.mitigation || '', r.owner || ''];
  });
  const panels = [
    { kind: 'stats', stats: [{ label: 'High risks', value: String(counts[3]) }, { label: 'Medium', value: String(counts[2]) }, { label: 'Low', value: String(counts[1]) }], h: 1 },
    { kind: 'table', header: ['Risk', 'Likelihood', 'Impact', 'Severity', 'Mitigation', 'Owner'], rows, colW: [2, 0.8, 0.8, 0.8, 3, 0.9], align: ['left', 'center', 'center', 'center', 'left', 'left'], h: 5, maxRowH: 0.5 },
  ];
  const showStats = T.level !== 'low';
  return withPanels(T, d, showStats ? { layout: '0;1', panels, rowFlex: [1, 5] } : { layout: '0', panels: [panels[1]] }, d.summary ? callout(T, 'SUMMARY', d.summary) : '');
};

T_.landscape = (d, T) => {
  const cats = d.categories, n = cats.length;
  const panels = cats.map((c) => ({ kind: 'chips', title: c.name, items: c.items, note: c.note, points: c.points }));
  const layout = n <= 4 ? panels.map((_, i) => i).join('|') : `${[...Array(Math.ceil(n / 2)).keys()].join('|')};${[...Array(n - Math.ceil(n / 2)).keys()].map((i) => i + Math.ceil(n / 2)).join('|')}`;
  const tg = TAGS(T);
  const legend = d.legend === false ? '' : `<div style="flex:none;display:flex;flex-direction:row;gap:8pt;align-items:center"><p style="font-size:${T.dn.src}pt;color:${T.mid}">Maturity:</p>${['adopt', 'trial', 'assess', 'hold'].map((k) => `<div style="background:${tg[k][0]};border-radius:8pt;padding:1pt 8pt"><p style="font-size:${T.dn.src}pt;font-weight:bold;color:${tg[k][1]}">${k}</p></div>`).join('')}</div>`;
  return withPanels(T, d, { layout, panels }, legend);
};

T_.sources = (d, T) => {
  const g = geom(T, d), items = arr(d.items), cols = d.columns || (items.length > 12 ? 3 : 2);
  const per = Math.ceil(items.length / cols), fs = fitSize(T, items.slice(0, per).map((x) => `[00] ${x}`), colW(g, cols) - 8, g.bh * 0.9, { min: T.dn.src, max: panelMax(T) });
  const col = (a, off) => `<div style="flex:1;min-width:0">${a.map((s, i) => `<p style="font-size:${fs}pt;color:${T.ink};margin-bottom:${Math.round(fs * 0.5)}pt"><b>[${off + i + 1}]</b> ${rich(s)}</p>`).join('')}</div>`;
  const cs = []; for (let c = 0; c < cols; c++) cs.push(col(items.slice(c * per, (c + 1) * per), c * per));
  return { html: shell(T, d, cs.join('')) };
};

const render = (spec, T) => {
  const fn = T_[spec.type];
  if (!fn) throw new Error(`Unknown slide type "${spec.type}". Known: ${Object.keys(T_).join(', ')}`);
  return fn(spec, T);
};

module.exports = { render, types: Object.keys(T_), panelKinds: Object.keys(KINDS), addChart, addTable };
