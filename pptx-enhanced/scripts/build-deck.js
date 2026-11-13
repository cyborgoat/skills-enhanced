#!/usr/bin/env node
/**
 * Build a .pptx from a deck spec.
 *   node scripts/build-deck.js deck.json out.pptx [--html-dir dir]
 * Spec: { title?, author?, density?: low|medium|high, preset?: 'tech-insight', theme?: {colors:{...}}, slides: [{ type, density?, ...data, notes? }] }
 * A slide of { type: "html", file: "my-slide.html" } uses a hand-written html2pptx page.
 * Module: const { buildDeck } = require('./build-deck'); await buildDeck(spec, 'out.pptx', { baseDir });
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
const html2pptx = require('./html2pptx');
const { loadTheme, cfg } = require('./theme');
const { render } = require('./templates');
const { lintPptx } = require('./lint-pptx');

async function placeImage(sl, area, file, fit) {
  const { width, height } = await sharp(file).metadata();
  if (fit === 'cover') return sl.addImage({ path: file, x: area.x, y: area.y, w: area.w, h: area.h, sizing: { type: 'cover', w: area.w, h: area.h } });
  const k = Math.min(area.w / width, area.h / height), w = width * k, h = height * k;
  sl.addImage({ path: file, x: area.x + (area.w - w) / 2, y: area.y + (area.h - h) / 2, w, h });
}

async function buildDeck(spec, outFile, opts = {}) {
  const preset = (cfg.density.presets || {})[spec.preset] || {};
  const deckLevel = spec.density || preset.density;
  const baseDir = opts.baseDir || process.cwd();
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pptx-enhanced-'));
  const htmlDir = opts.htmlDir ? path.resolve(opts.htmlDir) : tmp;
  fs.mkdirSync(htmlDir, { recursive: true });

  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = spec.author || 'pptx-enhanced';
  pptx.title = spec.title || 'Presentation';
  const font = cfg.theme.fonts.body.family;
  pptx.theme = { headFontFace: font, bodyFontFace: font, lang: spec.lang || 'en-US' };

  for (const [i, s] of spec.slides.entries()) {
    const n = String(i + 1).padStart(2, '0');
    const T = loadTheme(spec.theme, s.density || deckLevel); // per-slide density override
    let htmlPath, post;
    if (s.type === 'html') {
      htmlPath = path.resolve(baseDir, s.file);
    } else {
      const r = render(s, T);
      htmlPath = path.join(htmlDir, `slide-${n}-${s.type}.html`);
      fs.writeFileSync(htmlPath, r.html);
      post = r.post;
    }
    let res;
    try {
      res = await html2pptx(htmlPath, pptx, { tmpDir: tmp });
    } catch (e) {
      throw new Error(`Slide ${i + 1} ("${s.title || s.type}", type ${s.type}, ${T.level} density) does not fit: ${e.message.replace(/^.*?: /, '')}\n  Shorten the content, split the slide, or use a higher density for this slide.`);
    }
    const { slide, placeholders } = res;
    if (post) {
      await post(slide, pptx, placeholders, {
        T,
        // Mermaid -> PNG, contained and centred in the placeholder area
        addMermaid: async (sl, area, definition) => {
          const { renderMermaid } = require('./render-mermaid');
          const png = path.join(tmp, `mermaid-${n}.png`);
          await renderMermaid(definition, png, { width: 1600, theme: 'base' });
          await placeImage(sl, area, png, 'contain');
        },
        // Local image (png/jpg/gif/svg) or data URI, 'contain' (default) or 'cover'
        addImage: async (sl, area, file, fit = 'contain') => {
          let src = file;
          if (!String(file).startsWith('data:')) {
            src = path.resolve(baseDir, file);
            if (!fs.existsSync(src)) throw new Error(`Image not found: ${src}`);
            if (/\.svg$/i.test(src)) { const out = path.join(tmp, `img-${n}-${i}.png`); await sharp(src, { density: 300 }).png().toFile(out); src = out; }
          } else {
            const buf = Buffer.from(file.split(',')[1], 'base64');
            src = path.join(tmp, `img-${n}-${i}.png`); await sharp(buf).png().toFile(src);
          }
          await placeImage(sl, area, src, fit);
        },
      });
    }
    if (s.notes) slide.addNotes(s.notes);
  }
  await pptx.writeFile({ fileName: outFile });
  // PowerPoint shows a "Repair" prompt (and drops shapes) for some malformed XML; catch it here
  const { errors, warnings } = await lintPptx(outFile);
  warnings.forEach((w) => console.warn('lint warning:', w));
  if (errors.length) throw new Error(`Generated deck would trigger PowerPoint repair:\n  ${errors.join('\n  ')}`);
  return outFile;
}

module.exports = { buildDeck };

if (require.main === module) {
  const [specPath, out, ...rest] = process.argv.slice(2);
  if (!specPath || !out) { console.error('Usage: node build-deck.js deck.json out.pptx [--html-dir dir]'); process.exit(1); }
  const hi = rest.indexOf('--html-dir');
  const abs = path.resolve(specPath);
  const spec = abs.endsWith('.json') ? JSON.parse(fs.readFileSync(abs, 'utf8')) : require(abs);
  buildDeck(spec, path.resolve(out), { baseDir: path.dirname(abs), htmlDir: hi >= 0 ? rest[hi + 1] : undefined })
    .then((f) => console.log(`Wrote ${f}`))
    .catch((e) => { console.error(e.message); process.exit(1); });
}
