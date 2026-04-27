---
name: pptx-enhanced
description: Create, modify, and polish PowerPoint decks with an HTML-to-PPTX workflow, editable slide shapes, configurable themes, validation tools, raster visual fallback, and short animation generation for demonstrative content.
license: Complete terms in LICENSE
---

# pptx-enhanced

Use this skill to generate professional `.pptx` decks from HTML slides. The default visual direction is already set: white editorial slides, red title typography, gold highlights, slate-blue support tones, and clean neutral cards.

## Default Workflow

1. Plan the deck structure and choose a layout per slide from `references/layouts.md`.
2. Create one HTML file per slide using the rules in `html2pptx.md`.
3. Convert each slide with `scripts/html2pptx.js`.
4. Validate with thumbnails when LibreOffice is available, and with text inventory for overflow review.
5. Deliver the `.pptx` plus source HTML and any generated assets.

## Core Rules

- Slide body for 16:9 decks: `width: 720pt; height: 405pt`.
- Set `pptx.layout = 'LAYOUT_16x9'`.
- Put all visible text in `<p>`, `<h1>`-`<h6>`, `<ul>`, or `<ol>`.
- Use web-safe fonts, preferably `Arial`.
- Do not use CSS gradients; rasterize gradients first if required.
- Put backgrounds, borders, rounded corners, and shadows on `<div>` elements.
- Keep body text at least `9pt`; never go below `8.5pt`.
- Leave at least `50pt` between content and any bottom callout bar.

## Editable Visuals First

Prefer editable PowerPoint content for workflow diagrams:

1. Use HTML `<div>` shapes, text, borders, circles, and connector lines when the diagram is simple.
2. Use PptxGenJS `slide.addShape`, `slide.addText`, and `slide.addChart` for diagrams or charts that should remain editable.
3. Use PNG/JPG only for visuals that are hard to express as editable shapes: screenshots, photos, dense Mermaid diagrams, complex SVG illustrations, or decorative textures.

Detailed guidance is in `references/visuals.md`.

## Animations For Demonstrations

When a slide explains a process, algorithm, state transition, product flow, or before/after transformation, generate a short animation by default unless the user asks for static-only output. Manim is fine, but JavaScript stacks such as Motion Canvas, Theatre.js, FFCreatorLite, GSAP, Mo.js, browser canvas, and Playwright/FFmpeg capture are also valid. Keep the animation short, legible, and paired with a static fallback frame or summary slide.

## Minimal Generator Pattern

```javascript
const path = require('path');
const fs = require('fs');
const pptxgen = require('pptxgenjs');
const html2pptx = require('./scripts/html2pptx');

async function buildDeck(slideHtmlFiles, outputPath) {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'pptx-enhanced';
  pptx.theme = {
    headFontFace: 'Arial',
    bodyFontFace: 'Arial',
    lang: 'en-US',
  };

  for (const htmlPath of slideHtmlFiles) {
    await html2pptx(htmlPath, pptx);
  }

  await pptx.writeFile({ fileName: outputPath });
  return outputPath;
}
```

When running from outside the skill directory, import dependencies from `pptx-enhanced/node_modules` or run the generator from `pptx-enhanced/`.

## Validation

Run the converter first; it catches slide dimension mismatches and body overflow.

```bash
python pptx-enhanced/scripts/inventory.py output.pptx workspace/inventory.json
python pptx-enhanced/scripts/inventory.py --issues-only output.pptx workspace/inventory-issues.json
python pptx-enhanced/scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```

`thumbnail.py` requires LibreOffice and Poppler. If they are unavailable, report that and use the converter plus inventory output as the fallback check.

## Reference Files

- `html2pptx.md`: HTML syntax, supported elements, styling constraints, and converter API.
- `references/layouts.md`: compact layout catalog and selection guidance.
- `references/visuals.md`: editable diagrams, raster image fallback, Mermaid/SVG rules.
- `references/validation.md`: validation commands and common fixes.
- `default-pptx-config.json`: theme colors, fonts, and layout metadata.

## Setup

```bash
cd pptx-enhanced
npm install
npm run install-browsers
pip install -r requirements.txt
```

`npm run install-browsers` installs Playwright-managed Chromium. This avoids launching the user's system Chrome app during HTML rendering. If managed Chromium is unavailable and system Chrome is acceptable, set `PPTX_ENHANCED_USE_SYSTEM_CHROME=1`.

Optional validation dependencies:

```bash
brew install libreoffice poppler
```
