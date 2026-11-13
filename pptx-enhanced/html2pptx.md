# HTML slides and the html2pptx converter

`scripts/html2pptx.js` renders an HTML file in Chromium and maps the layout to PowerPoint objects. `build-deck.js` uses it for every slide; use it directly for hand-written pages (`{type: "html"}`) or custom post-processing.

## Slide HTML rules

- `body`: `width: 720pt; height: 405pt` (16:9; 4:3 is `720pt x 540pt`, 16:10 `720pt x 450pt`). Match `pptx.layout`. Use `display: flex` on `body`.
- **All text must be inside `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>`.** Text directly in a `<div>` or `<span>` is dropped.
- Lists: real `<ul>/<ol>`, never typed bullets.
- Inline formatting: `<b>`, `<i>`, `<u>`, `<br>`, and `<span>` with `font-weight`, `font-style`, `text-decoration`, `color` only (no margin, padding or font-size).
- Backgrounds, borders, border-radius and outer box-shadows work on `<div>` only. `border-left/right/top/bottom` become line shapes. No CSS gradients: rasterise them first.
- Fonts: Arial (or other web-safe: Helvetica, Times New Roman, Georgia, Courier New, Verdana, Tahoma, Trebuchet MS). Colours: `#rrggbb`.
- Flexbox is fine; positions come from the rendered layout. Use `margin` for spacing.
- `<img>`: PNG, JPG, GIF. Give a `max-height`.
- `<div class="placeholder" id="x" style="flex:1">` reserves space and is returned as `{id, x, y, w, h}` for charts, tables or diagrams.

Compact shell used by the templates (copy for custom slides):

```html
<style>
html{background:#fff}
body{width:720pt;height:405pt;margin:0;background:#fff;font-family:Arial,sans-serif;display:flex;flex-direction:column}
h1,p,ul{margin:0}
</style>
<div style="margin:14pt 24pt 0"><h1 style="font-size:20pt;color:#C62828">Title</h1></div>
<div style="margin:8pt 24pt 0;height:1pt;background:#D7DEE8"></div>
<div style="flex:1;min-height:0;display:flex;gap:10pt;margin:10pt 24pt 14pt"><!-- content --></div>
```

Editable workflow from shapes:

```html
<div style="display:flex;gap:10pt;align-items:center">
  <div style="width:120pt;padding:10pt;background:#FFF1F1;border:1pt solid #C62828;border-radius:6pt"><p style="font-size:11pt;font-weight:bold;text-align:center">Input</p></div>
  <p style="font-size:18pt;color:#4E6E8E">&#8594;</p>
  <div style="width:120pt;padding:10pt;background:#FFF8E1;border:1pt solid #FFB300;border-radius:6pt"><p style="font-size:11pt;font-weight:bold;text-align:center">Process</p></div>
</div>
```

## API

```js
const pptxgen = require('pptxgenjs');
const html2pptx = require('./scripts/html2pptx');   // path from the skill directory

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';
const { slide, placeholders } = await html2pptx('slide.html', pptx);   // options: { tmpDir, slide }
slide.addChart(pptx.charts.BAR, data, placeholders[0]);                // see references/pptxgenjs.md
await pptx.writeFile({ fileName: 'out.pptx' });
```

Returns `{ slide, placeholders }`. All validation errors are collected and thrown together:

1. HTML body size equals the presentation layout.
2. Content does not overflow the body or sit too close to the bottom edge.
3. No CSS gradients.
4. No backgrounds, borders or shadows on text elements.

Playwright-managed Chromium is used; set `PPTX_ENHANCED_USE_SYSTEM_CHROME=1` to use system Chrome instead.
