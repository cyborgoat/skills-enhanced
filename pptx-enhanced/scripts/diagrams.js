/**
 * Native, editable diagram helpers (PptxGenJS shapes, text boxes, tables, lines).
 * All coordinates are inches. Every helper has the signature
 *   fn(slide, pptx, area {x,y,w,h}, data, theme?)
 * and fills the area: sequence, classDiagram, erDiagram, flow, stateDiagram, architecture.
 */
const { loadTheme, hex } = require('./theme');

const textW = (s, pt = 10) => String(s).length * 0.072 * (pt / 10);
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const sum = (a) => a.reduce((s, v) => s + v, 0);

function ctx(slide, pptx, area, theme) {
  return { slide, pptx, area, T: theme || loadTheme() };
}

// ---------- primitives ----------
function box(c, x, y, w, h, text, o = {}) {
  const { T } = c;
  const shape = o.shape || c.pptx.ShapeType.roundRect;
  // rectRadius writes an "adj" guide: valid only on roundRect, PowerPoint "repairs" the slide otherwise
  const radius = shape === c.pptx.ShapeType.roundRect ? { rectRadius: Math.min(o.r ?? 0.06, Math.min(w, h) / 2) } : {};
  c.slide.addText(text ?? '', {
    shape, x, y, w, h, ...radius,
    fill: { color: hex(o.fill || T.primaryLight) },
    line: { color: hex(o.line || T.primary), width: o.lw ?? 1, dashType: o.dash || 'solid' },
    fontFace: T.font, fontSize: o.size || 10, bold: !!o.bold, color: hex(o.color || T.ink),
    align: o.align || 'center', valign: o.valign || 'middle', margin: o.margin ?? 3, fit: 'none',
  });
}

function label(c, text, cx, cy, o = {}) {
  const size = o.size || 9;
  const w = textW(text, size) + 0.14, h = 0.2;
  c.slide.addText(String(text), {
    x: cx - w / 2, y: cy - h / 2, w, h, fontFace: c.T.font, fontSize: size, color: hex(o.color || c.T.mid),
    align: 'center', valign: 'middle', margin: 0, wrap: false,
    ...(o.fill === false ? {} : { fill: { color: hex(o.fill || c.T.bg) } }),
  });
}

function line(c, x1, y1, x2, y2, o = {}) {
  const dx = x2 - x1, dy = y2 - y1;
  if (Math.abs(dx) < 1e-4 && Math.abs(dy) < 1e-4) return;
  c.slide.addShape(c.pptx.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(dx), h: Math.abs(dy),
    flipH: dx < 0, flipV: dy < 0,
    line: {
      color: hex(o.color || c.T.accent), width: o.width ?? 1.25, dashType: o.dash || 'solid',
      beginArrowType: o.begin || undefined, endArrowType: o.end || undefined,
    },
  });
}

function poly(c, pts, o = {}) {
  for (let i = 0; i < pts.length - 1; i++) {
    const last = i === pts.length - 2, first = i === 0;
    line(c, pts[i].x, pts[i].y, pts[i + 1].x, pts[i + 1].y, {
      ...o, end: last ? o.end : undefined, begin: first ? o.begin : undefined,
    });
  }
}

// Position for an edge label: above a horizontal run, to the right of a vertical one
function labelPos(pts, text, size = 9) {
  const m = midOfLongest(pts);
  let best = 0, bi = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const l = Math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y);
    if (l > best) { best = l; bi = i; }
  }
  const horizontal = Math.abs(pts[bi + 1].y - pts[bi].y) < Math.abs(pts[bi + 1].x - pts[bi].x);
  return horizontal ? { x: m.x, y: m.y - (best < textW(text, size) + 0.14 ? 0.4 : 0.14) } : { x: m.x + textW(text, size) / 2 + 0.1, y: m.y };
}

function midOfLongest(pts) {
  let best = 0, bi = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const l = Math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y);
    if (l > best) { best = l; bi = i; }
  }
  return { x: (pts[bi].x + pts[bi + 1].x) / 2, y: (pts[bi].y + pts[bi + 1].y) / 2 };
}

// ---------- layered layout (shared by flow, state, class, ER) ----------
// nodes: [{id,w,h}], edges: [{from,to}] oriented upper->lower. dir: 'TB' | 'LR'.
function layered(nodes, edges, dir, area, opt = {}) {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const valid = edges.filter((e) => byId.has(e.from) && byId.has(e.to) && e.from !== e.to);
  const out = new Map(nodes.map((n) => [n.id, []]));
  valid.forEach((e) => out.get(e.from).push(e.to));
  const state = {}, back = new Set();
  const visit = (id) => {
    state[id] = 1;
    for (const t of out.get(id)) { if (state[t] === 1) back.add(`${id}>${t}`); else if (!state[t]) visit(t); }
    state[id] = 2;
  };
  nodes.forEach((n) => { if (!state[n.id]) visit(n.id); });

  const preds = new Map(nodes.map((n) => [n.id, []]));
  valid.forEach((e) => { if (!back.has(`${e.from}>${e.to}`)) preds.get(e.to).push(e.from); });
  const rank = {};
  const rk = (id) => (rank[id] ??= preds.get(id).length ? 1 + Math.max(...preds.get(id).map(rk)) : 0);
  nodes.forEach((n) => rk(n.id));
  nodes.forEach((n) => { // sources sit just above their nearest target
    if (!preds.get(n.id).length && out.get(n.id).length) {
      const m = Math.min(...out.get(n.id).filter((t) => !back.has(`${n.id}>${t}`)).map((t) => rank[t]));
      if (Number.isFinite(m) && m - 1 > rank[n.id]) rank[n.id] = m - 1;
    }
  });
  const R = Math.max(...Object.values(rank)) + 1;
  const ranks = Array.from({ length: R }, () => []);
  nodes.forEach((n) => ranks[rank[n.id]].push(n));
  const pos = {};
  ranks[0].forEach((n, i) => { pos[n.id] = i; });
  for (let r = 1; r < R; r++) {
    const bary = (n) => { const p = preds.get(n.id); return p.length ? sum(p.map((q) => pos[q] ?? 0)) / p.length : 1e3; };
    ranks[r].sort((a, b) => bary(a) - bary(b));
    ranks[r].forEach((n, i) => { pos[n.id] = i; });
  }

  const TB = dir === 'TB';
  const nBack = back.size;
  const reserve = nBack ? 0.14 + 0.14 * nBack : 0;
  const Au = TB ? area.h : area.w;
  const Av = (TB ? area.w : area.h) - reserve;
  const du = (n) => (TB ? n.h : n.w), dv = (n) => (TB ? n.w : n.h);
  const thick = ranks.map((r) => Math.max(...r.map(du)));
  const minGap = opt.minGap ?? 0.32;
  const f = Math.max(0.6, Math.min(1, Au / (sum(thick) + (R - 1) * minGap)));
  const gap = R > 1 ? clamp((Au - sum(thick) * f) / (R - 1), minGap * f, opt.maxGap ?? 1.0) : 0;
  const total = sum(thick) * f + (R - 1) * gap;
  let u = (Au - total) / 2;
  const rect = {}, rankEnd = [];
  ranks.forEach((r, ri) => {
    const th = thick[ri] * f;
    const cell = Av / r.length;
    r.forEach((n, i) => {
      const nu = du(n) * f, nv = Math.min(dv(n) * f, cell * 0.92);
      const uc = u + th / 2, vc = (i + 0.5) * cell;
      rect[n.id] = TB
        ? { x: area.x + vc - nv / 2, y: area.y + uc - nu / 2, w: nv, h: nu, uc, vc, du: nu, dv: nv, f }
        : { x: area.x + uc - nu / 2, y: area.y + vc - nv / 2, w: nu, h: nv, uc, vc, du: nu, dv: nv, f };
    });
    rankEnd.push(u + th);
    u += th + gap;
  });

  const P = (uu, vv) => (TB ? { x: area.x + vv, y: area.y + uu } : { x: area.x + uu, y: area.y + vv });
  const vMax = Math.max(...nodes.map((n) => rect[n.id].vc + rect[n.id].dv / 2));
  let bi = 0;
  const routes = valid.map((e) => {
    const s = rect[e.from], t = rect[e.to];
    let pts, isBack = false;
    if (back.has(`${e.from}>${e.to}`)) {
      isBack = true;
      const off = vMax + 0.14 + 0.14 * bi++;
      pts = [P(s.uc, s.vc + s.dv / 2), P(s.uc, off), P(t.uc, off), P(t.uc, t.vc + t.dv / 2)];
    } else {
      const su = s.uc + s.du / 2, tu = t.uc - t.du / 2;
      const mid = rankEnd[rank[e.from]] + gap / 2;
      pts = su === tu ? [P(su, s.vc), P(tu, t.vc)]
        : [P(su, s.vc), P(mid, s.vc), P(mid, t.vc), P(tu, t.vc)];
    }
    return { ...e, pts, isBack };
  });
  return { rect, routes, dir };
}

// ---------- flow / state ----------
function flow(slide, pptx, area, data, theme) {
  const c = ctx(slide, pptx, area, theme), { T } = c;
  const nodes = data.nodes.map((n) => {
    const nd = typeof n === 'string' ? { id: n, label: n } : { label: n.id, ...n };
    const kind = nd.shape || 'box';
    const tw = textW(nd.label || '');
    if (kind === 'start' || kind === 'end') return { ...nd, kind, w: 0.24, h: 0.24 };
    if (kind === 'diamond') return { ...nd, kind, w: clamp(tw * 1.4 + 0.3, 1.3, 2.4), h: 0.8 };
    return { ...nd, kind, w: clamp(tw + 0.3, 1.0, 2.2), h: 0.5 };
  });
  const lw = Math.max(0, ...data.edges.map((e) => (e.label ? textW(e.label, 9) + 0.25 : 0)));
  const L = layered(nodes, data.edges.map((e) => ({ ...e })), data.dir || 'LR', area, { minGap: clamp(lw, 0.32, 1.0), maxGap: 1.3 });
  L.routes.forEach((r) => poly(c, r.pts, { color: T.accent, end: 'triangle', dash: r.dashed ? 'dash' : 'solid' }));
  nodes.forEach((n) => {
    const r = L.rect[n.id], size = clamp(10 * r.f, 9, 10);
    if (n.kind === 'start') return box(c, r.x, r.y, r.w, r.h, '', { shape: pptx.ShapeType.ellipse, fill: T.ink, line: T.ink });
    if (n.kind === 'end') return box(c, r.x, r.y, r.w, r.h, '', { shape: pptx.ShapeType.ellipse, fill: T.bg, line: T.ink, lw: 3 });
    if (n.kind === 'diamond') return box(c, r.x, r.y, r.w, r.h, n.label, { shape: pptx.ShapeType.diamond, fill: T.secondaryLight, line: T.secondary, size, bold: true });
    const round = n.kind === 'pill' ? r.h / 2 : 0.07;
    box(c, r.x, r.y, r.w, r.h, n.label, { fill: n.fill || T.primaryLight, line: n.line || T.primary, size, bold: true, r: round });
  });
  L.routes.forEach((r) => { if (r.label) { const m = labelPos(r.pts, r.label); label(c, r.label, m.x, m.y, { fill: false }); } });
}

function stateDiagram(slide, pptx, area, data, theme) {
  const nodes = data.states.map((s) => (typeof s === 'string' ? { id: s, label: s, shape: 'pill' } : { shape: 'pill', ...s }));
  const edges = [];
  data.transitions.forEach((t) => {
    let from = t.from, to = t.to;
    if (from === '[*]') { from = '__start'; if (!nodes.find((n) => n.id === from)) nodes.unshift({ id: from, label: '', shape: 'start' }); }
    if (to === '[*]') { to = '__end'; if (!nodes.find((n) => n.id === to)) nodes.push({ id: to, label: '', shape: 'end' }); }
    edges.push({ from, to, label: t.label });
  });
  flow(slide, pptx, area, { nodes, edges, dir: data.dir || 'LR' }, theme);
}

// ---------- UML class ----------
function classDiagram(slide, pptx, area, data, theme) {
  const c = ctx(slide, pptx, area, theme), { T } = c;
  const LH = 0.165;
  const nodes = data.classes.map((k) => {
    const attrs = k.attrs || [], methods = k.methods || [];
    const lines = [k.name, ...attrs, ...methods];
    const w = clamp(Math.max(...lines.map((s) => textW(s, 9))) + 0.3, 1.4, 2.6);
    const hh = k.stereotype ? 0.42 : 0.28;
    const ah = Math.max(1, attrs.length) * LH + 0.08, mh = Math.max(1, methods.length) * LH + 0.08;
    return { ...k, id: k.name, attrs, methods, w, h: hh + ah + mh, hh, ah, mh };
  });
  const REL = {
    inherit: { upper: 'to' }, implement: { upper: 'to', dash: true },
    compose: { upper: 'from', marker: 'diamond', fill: true }, aggregate: { upper: 'from', marker: 'diamond' },
    assoc: { upper: 'from', arrow: true }, depend: { upper: 'from', arrow: true, dash: true },
  };
  const rels = (data.relations || []).map((r) => {
    const spec = REL[r.type || 'assoc'] || REL.assoc;
    const up = spec.upper === 'to' ? r.to : r.from, lo = spec.upper === 'to' ? r.from : r.to;
    return { ...r, spec, from: up, to: lo };
  });
  const L = layered(nodes, rels, 'TB', area, { maxGap: 0.9 });
  L.routes.forEach((r) => {
    const sp = r.spec, pts = r.pts.map((p) => ({ ...p }));
    const o = { color: T.accent, dash: sp.dash ? 'dash' : 'solid' };
    const vertical = !r.isBack;
    if (vertical && (r.type === 'inherit' || r.type === 'implement' || sp.marker === 'diamond')) {
      const mh = sp.marker === 'diamond' ? 0.2 : 0.14, mw = sp.marker === 'diamond' ? 0.14 : 0.16;
      const p0 = pts[0];
      pts[0] = { x: p0.x, y: p0.y + mh };
      poly(c, pts, o);
      box(c, p0.x - mw / 2, p0.y, mw, mh, '', {
        shape: sp.marker === 'diamond' ? pptx.ShapeType.diamond : pptx.ShapeType.triangle,
        fill: sp.fill ? T.accent : T.bg, line: T.accent, lw: 1,
      });
    } else {
      poly(c, pts, { ...o, end: sp.arrow || r.isBack ? 'arrow' : undefined });
    }
    if (r.label) { const m = labelPos(r.pts, r.label); label(c, r.label, m.x, m.y, { fill: false }); }
  });
  nodes.forEach((n) => {
    const r = L.rect[n.id], s = r.f;
    const hh = n.hh * s, ah = n.ah * s, mh = n.mh * s;
    const txt = (arr, y, h) => c.slide.addText(arr.join('\n'), {
      x: r.x + 0.04, y, w: r.w - 0.08, h, fontFace: T.font, fontSize: clamp(9 * s, 8.5, 9), color: hex(T.ink),
      align: 'left', valign: 'top', margin: [1, 2, 0, 2], fit: 'none',
    });
    box(c, r.x, r.y, r.w, hh, '', { shape: pptx.ShapeType.rect, fill: T.primaryLight, line: T.primary });
    c.slide.addText(n.stereotype ? [
      { text: `«${n.stereotype}»`, options: { fontSize: 8.5, italic: true, color: hex(T.mid), breakLine: true } },
      { text: n.name, options: { fontSize: 10.5, bold: true, color: hex(T.ink) } },
    ] : n.name, { x: r.x, y: r.y, w: r.w, h: hh, fontFace: T.font, fontSize: 10.5, bold: true, color: hex(T.ink), align: 'center', valign: 'middle', margin: 0 });
    box(c, r.x, r.y + hh, r.w, ah, '', { shape: pptx.ShapeType.rect, fill: T.bg, line: T.primary });
    txt(n.attrs, r.y + hh, ah);
    box(c, r.x, r.y + hh + ah, r.w, mh, '', { shape: pptx.ShapeType.rect, fill: T.bg, line: T.primary });
    txt(n.methods, r.y + hh + ah, mh);
  });
}

// ---------- ER ----------
function erDiagram(slide, pptx, area, data, theme) {
  const c = ctx(slide, pptx, area, theme), { T } = c;
  const RH = 0.2, HH = 0.27;
  const nodes = data.entities.map((e) => {
    const fields = e.fields.map((f) => (typeof f === 'string' ? { name: f } : f));
    const nameW = Math.max(textW(e.name, 10) - 0.4, ...fields.map((f) => textW(f.name, 9) * 1.1)) + 0.3;
    const typeW = Math.max(0.5, ...fields.map((f) => textW(f.type || '', 9) * 1.1)) + 0.3;
    const cols = [0.36, nameW, typeW];
    return { ...e, id: e.name, fields, cols, w: sum(cols), h: HH + fields.length * RH };
  });
  const rels = (data.relations || []).map((r) => ({ ...r }));
  const L = layered(nodes, rels, data.dir || 'LR', area, { minGap: 0.6, maxGap: 1.4 });
  L.routes.forEach((r) => {
    poly(c, r.pts, { color: T.accent, width: 1.25 });
    const [a, b] = String(r.card || '1:N').split(':');
    const p0 = r.pts[0], p1 = r.pts[1], pn = r.pts[r.pts.length - 1], pm = r.pts[r.pts.length - 2];
    const along = (p, q, d, off) => { // point d inches from p toward q, offset perpendicular by off
      const dx = q.x - p.x, dy = q.y - p.y, l = Math.hypot(dx, dy) || 1;
      return { x: p.x + (dx / l) * d - (dy / l) * off, y: p.y + (dy / l) * d + (dx / l) * off };
    };
    const A = along(p0, p1, 0.16, -0.12), B = along(pn, pm, 0.16, 0.12);
    label(c, a, A.x, A.y, { fill: false, color: T.hi, size: 9 });
    label(c, b, B.x, B.y, { fill: false, color: T.hi, size: 9 });
    if (r.label) { const m = labelPos(r.pts, r.label); label(c, r.label, m.x, m.y, { fill: false }); }
  });
  nodes.forEach((n) => {
    const r = L.rect[n.id];
    const rows = [[{ text: n.name, options: { colspan: 3, fill: { color: hex(T.primary) }, color: hex(T.onPrimary), bold: true, align: 'center', fontSize: 10 } }]];
    n.fields.forEach((f) => rows.push([
      { text: f.key || '', options: { bold: true, color: hex(T.hi), align: 'center', fill: { color: hex(T.bg) } } },
      { text: f.name, options: { align: 'left', bold: f.key === 'PK', fill: { color: hex(T.bg) } } },
      { text: f.type || '', options: { align: 'left', color: hex(T.mid), fill: { color: hex(T.bg) } } },
    ]));
    const k = r.w / n.w;
    c.slide.addTable(rows, {
      x: r.x, y: r.y, w: r.w, colW: n.cols.map((v) => v * k), rowH: [HH, ...n.fields.map(() => RH)].map((v) => v * (r.h / n.h)),
      fontFace: T.font, fontSize: 9, color: hex(T.ink), valign: 'middle', margin: [0, 0.04, 0, 0.04], // inches
      border: { type: 'solid', pt: 0.75, color: hex(T.line) }, fill: { color: hex(T.bg) },
    });
  });
}

// ---------- sequence ----------
function sequence(slide, pptx, area, data, theme) {
  const c = ctx(slide, pptx, area, theme), { T } = c;
  const actors = data.actors.map((a) => (typeof a === 'string' ? { id: a, label: a } : { label: a.id, ...a }));
  const n = actors.length, colW = area.w / n, AH = 0.34;
  const cx = {};
  actors.forEach((a, i) => { cx[a.id] = area.x + (i + 0.5) * colW; });
  const msgs = data.messages;
  const step = Math.min(0.62, (area.h - AH - 0.2) / (msgs.length + 0.4));
  const y0 = area.y + AH + 0.12;
  const my = msgs.map((_, i) => y0 + (i + 0.6) * step);
  const bottom = Math.min(area.y + area.h, my[my.length - 1] + 0.3);

  actors.forEach((a) => {
    const w = Math.min(colW * 0.86, Math.max(1.0, textW(a.label, 10) + 0.3));
    line(c, cx[a.id], area.y + AH, cx[a.id], bottom, { color: T.light, width: 0.75, dash: 'dash' });
    box(c, cx[a.id] - w / 2, area.y, w, AH, a.label, { bold: true, size: 10 });
  });

  // activation bars: a sync/async call opens one on the target; closed by that target's next return
  const open = {};
  msgs.forEach((m, i) => {
    const type = m.type || 'sync';
    if (type === 'return') {
      const st = open[m.from]?.pop();
      if (st !== undefined) box(c, cx[m.from] - 0.05, my[st], 0.1, my[i] - my[st], '', { shape: pptx.ShapeType.rect, r: 0, lw: 0.75 });
    } else if (m.from !== m.to) { (open[m.to] ||= []).push(i); }
  });
  Object.entries(open).forEach(([id, arr]) => arr.forEach((st) => box(c, cx[id] - 0.05, my[st], 0.1, Math.min(0.26, bottom - my[st]), '', { shape: pptx.ShapeType.rect, r: 0, lw: 0.75 })));

  msgs.forEach((m, i) => {
    const type = m.type || 'sync', y = my[i];
    if (m.from === m.to) {
      const x = cx[m.from] + 0.05;
      poly(c, [{ x, y }, { x: x + 0.4, y }, { x: x + 0.4, y: y + 0.22 }, { x, y: y + 0.22 }], { color: T.primary, end: 'triangle' });
      c.slide.addText(m.text, { x: x + 0.46, y: y - 0.02, w: textW(m.text, 9.5) + 0.2, h: 0.26, fontFace: T.font, fontSize: 9.5, color: hex(T.ink), align: 'left', valign: 'middle', margin: 0, wrap: false });
      return;
    }
    const dir = Math.sign(cx[m.to] - cx[m.from]);
    const x1 = cx[m.from] + dir * 0.05, x2 = cx[m.to] - dir * 0.05;
    line(c, x1, y, x2, y, { color: type === 'return' ? T.mid : T.primary, width: 1.25, dash: type === 'return' ? 'dash' : 'solid', end: type === 'sync' ? 'triangle' : 'arrow' });
    const w = Math.max(Math.abs(x2 - x1), textW(m.text, 9.5) + 0.1);
    c.slide.addText(m.text, { x: (x1 + x2) / 2 - w / 2, y: y - 0.22, w, h: 0.2, fontFace: T.font, fontSize: 9.5, color: hex(type === 'return' ? T.mid : T.ink), italic: type === 'return', align: 'center', valign: 'bottom', margin: 0, wrap: false });
  });
}

// ---------- architecture (layered bands) ----------
function architecture(slide, pptx, area, data, theme) {
  const c = ctx(slide, pptx, area, theme), { T } = c;
  const layers = data.layers, L = layers.length, gap = 0.2, LW = 0.95;
  const bandH = (area.h - (L - 1) * gap) / L;
  const tones = [[T.primaryLight, T.primary], [T.secondaryLight, T.secondary], ['EEF2F6', T.accent]];
  const rect = {}, layerOf = {};
  layers.forEach((ly, li) => {
    const by = area.y + li * (bandH + gap), [fill, stroke] = tones[li % tones.length];
    box(c, area.x, by, area.w, bandH, '', { shape: pptx.ShapeType.roundRect, fill: T.alt, line: T.line, lw: 0.75, r: 0.06 });
    box(c, area.x, by, LW, bandH, ly.name, { fill: stroke, line: stroke, color: li % 3 === 1 ? T.onSecondary : T.onPrimary, bold: true, size: 10, r: 0.06 });
    const cell = (area.w - LW - 0.1) / ly.nodes.length;
    const nh = clamp(bandH * 0.62, 0.36, 0.7), nw = clamp(cell * 0.82, 0.8, 2.2);
    ly.nodes.forEach((nd, i) => {
      const x = area.x + LW + 0.1 + (i + 0.5) * cell - nw / 2, y = by + (bandH - nh) / 2;
      rect[nd.id] = { x, y, w: nw, h: nh, band: by, bandH };
      layerOf[nd.id] = li;
      nd._fill = fill; nd._stroke = stroke;
    });
  });
  (data.edges || []).forEach((e, k) => {
    const s = rect[e.from], t = rect[e.to];
    if (!s || !t) return;
    let pts;
    if (layerOf[e.from] === layerOf[e.to]) {
      const rt = t.x > s.x;
      pts = [{ x: rt ? s.x + s.w : s.x, y: s.y + s.h / 2 }, { x: rt ? t.x : t.x + t.w, y: t.y + t.h / 2 }];
    } else if (layerOf[e.from] < layerOf[e.to]) {
      const my = s.band + s.bandH + gap / 2;
      pts = [{ x: s.x + s.w / 2, y: s.y + s.h }, { x: s.x + s.w / 2, y: my }, { x: t.x + t.w / 2, y: my }, { x: t.x + t.w / 2, y: t.y }];
    } else {
      const my = s.band - gap / 2;
      pts = [{ x: s.x + s.w / 2, y: s.y }, { x: s.x + s.w / 2, y: my }, { x: t.x + t.w / 2, y: my }, { x: t.x + t.w / 2, y: t.y + t.h }];
    }
    poly(c, pts, { color: T.accent, end: 'triangle', dash: e.dashed ? 'dash' : 'solid' });
    if (e.label) { const m = midOfLongest(pts); label(c, e.label, m.x, m.y, { size: 8.5 }); }
  });
  layers.forEach((ly) => ly.nodes.forEach((nd) => {
    const r = rect[nd.id];
    const txt = nd.sub ? [
      { text: nd.label, options: { bold: true, fontSize: 10, color: hex(T.ink), breakLine: true } },
      { text: nd.sub, options: { fontSize: 8.5, color: hex(T.mid) } },
    ] : nd.label;
    c.slide.addText(txt, {
      shape: pptx.ShapeType.roundRect, x: r.x, y: r.y, w: r.w, h: r.h, rectRadius: 0.06,
      fill: { color: hex(T.bg) }, line: { color: hex(nd._stroke), width: 1.25 },
      fontFace: T.font, fontSize: 10, bold: true, color: hex(T.ink), align: 'center', valign: 'middle', margin: 2,
    });
  }));
}

module.exports = { sequence, classDiagram, erDiagram, flow, stateDiagram, architecture, layered };
