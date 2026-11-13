#!/usr/bin/env node
/**
 * Static checks for patterns that make PowerPoint show the "Repair" prompt (and drop shapes).
 *   node scripts/lint-pptx.js deck.pptx      exit 1 on errors
 *   const { lintPptx } = require('./lint-pptx'); const { errors, warnings } = await lintPptx('deck.pptx');
 */
const fs = require('fs');
const JSZip = require('jszip');

// Preset geometries that accept a single "adj" guide
const ADJ_OK = new Set(['roundRect', 'triangle', 'rightArrow', 'leftArrow', 'chevron', 'homePlate']);
const ARROWS = new Set(['none', 'triangle', 'stealth', 'diamond', 'oval', 'arrow']);
const DASHES = new Set(['solid', 'dot', 'dash', 'lgDash', 'dashDot', 'lgDashDot', 'lgDashDotDot', 'sysDash', 'sysDot', 'sysDashDot', 'sysDashDotDot']);

async function lintPptx(file) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const errors = [], warnings = [];
  const slides = Object.keys(zip.files).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f))
    .sort((a, b) => parseInt(a.match(/(\d+)\.xml/)[1]) - parseInt(b.match(/(\d+)\.xml/)[1]));
  for (const f of slides) {
    const n = f.match(/slide(\d+)\.xml/)[1];
    const xml = await zip.file(f).async('string');
    const at = (msg) => `slide ${n}: ${msg}`;

    if (/="[^"]*(NaN|undefined|Infinity)[^"]*"/.test(xml)) errors.push(at('attribute contains NaN/undefined/Infinity'));

    const adj = {};
    for (const m of xml.matchAll(/<a:prstGeom prst="(\w+)"><a:avLst>(.*?)<\/a:avLst>/g)) {
      if (/name="adj\d?"/.test(m[2]) && !ADJ_OK.has(m[1])) adj[m[1]] = (adj[m[1]] || 0) + 1;
      for (const v of m[2].matchAll(/fmla="val (-?\d+)"/g)) {
        if (m[1] === 'roundRect' && (+v[1] < 0 || +v[1] > 50000)) errors.push(at(`roundRect adj ${v[1]} outside 0-50000`));
      }
    }
    for (const [g, c] of Object.entries(adj)) errors.push(at(`${c} <${g}> shape(s) carry an "adj" guide that ${g} does not support (rectRadius on a non-roundRect shape)`));

    for (const m of xml.matchAll(/<a:ext cx="(-?\d+)" cy="(-?\d+)"/g)) {
      if (+m[1] < 0 || +m[2] < 0) errors.push(at(`negative extent ${m[1]}x${m[2]}`));
    }
    // zero-size shape that is not a line/connector
    for (const m of xml.matchAll(/<p:sp>.*?<\/p:sp>/gs)) {
      const sp = m[0];
      const e = sp.match(/<a:ext cx="(\d+)" cy="(\d+)"/);
      const g = sp.match(/<a:prstGeom prst="(\w+)"/);
      if (e && g && g[1] !== 'line' && (+e[1] === 0 || +e[2] === 0)) warnings.push(at(`zero-size <${g[1]}> shape`));
    }
    for (const m of xml.matchAll(/<a:(?:head|tail)End type="(\w+)"/g)) if (!ARROWS.has(m[1])) errors.push(at(`invalid arrow type "${m[1]}"`));
    for (const m of xml.matchAll(/<a:prstDash val="(\w+)"/g)) if (!DASHES.has(m[1])) errors.push(at(`invalid dash "${m[1]}"`));
  }
  return { errors: [...new Set(errors)], warnings: [...new Set(warnings)], slides: slides.length };
}

module.exports = { lintPptx };

if (require.main === module) {
  const file = process.argv[2];
  if (!file) { console.error('Usage: node lint-pptx.js deck.pptx'); process.exit(1); }
  lintPptx(file).then(({ errors, warnings, slides }) => {
    warnings.forEach((w) => console.warn('warning:', w));
    errors.forEach((e) => console.error('ERROR:', e));
    console.log(errors.length ? `${errors.length} error(s) in ${slides} slides` : `OK: ${slides} slides, no PowerPoint repair triggers found`);
    process.exit(errors.length ? 1 : 0);
  });
}
