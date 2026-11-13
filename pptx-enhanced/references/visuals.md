# Visuals

| Need | Use |
|---|---|
| Sequence, class, ER, state, flow, layered architecture | `diagram` slide, `mode: "native"` (editable shapes) |
| Dense graphs, Gantt, mind maps, anything the native layout cannot place | `diagram` slide, `mode: "mermaid"` (PNG) |
| Chart | `chart` / `kpi` slide (native PowerPoint chart) |
| Screenshot, photo | PNG/JPG via `<img>` in an `html` slide |
| Custom illustration | SVG rasterised to PNG with Sharp |
| Demonstration of a process or algorithm | short GIF/video plus a static fallback slide |

If the user has not chosen native or Mermaid, ask once. Default: native up to ~10 nodes.

## Native diagrams (`scripts/diagrams.js`)

`sequence`, `classDiagram`, `erDiagram`, `flow`, `stateDiagram`, `architecture`, all `fn(slide, pptx, area {x,y,w,h in inches}, data, theme?)`. Use them directly from PptxGenJS code, for example on a placeholder:

```js
const { architecture } = require('./scripts/diagrams');
const { slide, placeholders } = await html2pptx('slide.html', pptx);
architecture(slide, pptx, placeholders[0], { layers, edges });
```

Data shapes are in `layouts.md`. They draw rounded boxes, text, tables (ER) and arrow lines only, so everything stays editable. Layout is layered and automatic; shapes fill the area.

## Mermaid (`scripts/render-mermaid.js`)

Needs network access (loads mermaid from a CDN) and Playwright Chromium. Uses the deck palette by default.

```bash
node scripts/render-mermaid.js flow.mmd flow.png --width 1600
```

Use `flowchart TD` for tall areas and `LR` for wide ones. Split diagrams above ~10 nodes.

## Raster rules

- SVG: explicit `width`/`height`, Arial, escape `&`, no emoji; rasterise at 1000-1600px width.
- Gradients and icons must be rasterised first; CSS gradients do not convert.
- Always give `<img>` a `max-height` so it cannot overflow the slide.

## Animation

For demonstrative content (workflow, algorithm, state transition, before/after), generate a 3-10 second GIF or video and keep a static fallback frame. Pick the quickest tool that is installed:

| Tool | Good for |
|---|---|
| Manim | maths, algorithms, structured processes |
| Motion Canvas, Remotion | programmatic explainer videos |
| GSAP / canvas / SVG + Playwright capture + FFmpeg | UI flows and diagrams, no extra install |
| FFCreatorLite, Theatre.js, Mo.js | quick Node-side video or keyframed motion |
