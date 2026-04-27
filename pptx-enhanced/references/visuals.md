# Visuals And Animation

Prefer visuals over placeholder boxes. Choose the format based on whether the user should be able to edit the result in PowerPoint and whether motion helps explain the idea.

## Decision Guide

| Need | Preferred Approach |
|---|---|
| Simple workflow, architecture, hub, process | Editable HTML/PptxGenJS shapes |
| Chart or data graphic | Editable PptxGenJS chart when possible |
| Dense sequence, ER, state, or class diagram | Mermaid rendered to PNG |
| Custom illustration or precise visual composition | SVG rendered to PNG |
| Screenshot or product capture | PNG/JPG |
| Demonstrative concept, transition, algorithm, or process | Short animation/video/GIF |

## Editable Static Diagrams

For workflow diagrams, prefer editable PowerPoint shapes before raster images.

Use HTML shapes when the converter can handle the layout:

```html
<div style="display: flex; gap: 14pt; align-items: center;">
  <div style="width: 120pt; height: 52pt; background: #FFF1F1; border: 1pt solid #C62828; border-radius: 6pt;">
    <p style="font-size: 11pt; font-weight: bold; color: #1F2937; text-align: center; margin-top: 15pt;">Input</p>
  </div>
  <p style="font-size: 18pt; color: #4E6E8E;">&#8594;</p>
  <div style="width: 120pt; height: 52pt; background: #FFF8E1; border: 1pt solid #FFB300; border-radius: 6pt;">
    <p style="font-size: 11pt; font-weight: bold; color: #1F2937; text-align: center; margin-top: 15pt;">Process</p>
  </div>
</div>
```

Use PptxGenJS for diagrams that need precise editable shapes, connectors, or charts after HTML conversion:

```javascript
slide.addShape(pptx.ShapeType.roundRect, {
  x: 1.0, y: 2.0, w: 1.8, h: 0.7,
  fill: { color: 'FFF1F1' },
  line: { color: 'C62828', width: 1 },
  rectRadius: 0.08,
});
slide.addText('Input', {
  x: 1.0, y: 2.18, w: 1.8, h: 0.25,
  fontFace: 'Arial', fontSize: 11, bold: true,
  color: '1F2937', align: 'center',
});
slide.addShape(pptx.ShapeType.line, {
  x: 2.95, y: 2.35, w: 0.7, h: 0,
  line: { color: '4E6E8E', width: 2, beginArrowType: 'none', endArrowType: 'triangle' },
});
```

## Animation Policy

When the content is demonstrative, generate a short animation by default unless the user asks for a static-only deck.

Good animation candidates:

- Step-by-step workflows and pipelines.
- Algorithms, state transitions, queues, routing, token generation, or model inference.
- Before/after transformations.
- Physical, spatial, or timing concepts.
- Product interaction flows.

Keep animations short: usually `3-10` seconds. Embed as GIF or video when supported by the target deck workflow, and include a static fallback frame or static summary slide.

## Animation Tooling

Any reliable animation stack is acceptable. Pick the fastest tool that fits the content and local environment.

Options:

- Manim for mathematical, algorithmic, and structured process animations.
- Motion Canvas for educational, technical, and programmatic scene-building videos.
- Theatre.js for detailed keyframe sequence editing and motion graphics.
- FFCreatorLite for fast server-side video generation and automation in Node.js.
- GSAP for high-performance browser animations that can be captured to video.
- Mo.js for shape-heavy motion graphics and lightweight visual effects.
- Remotion, Three.js, or Canvas/SVG in a browser for other JS-driven animation needs.
- Playwright or Puppeteer screen capture for browser-based animated scenes.
- FFmpeg for assembling frames, converting formats, trimming, or optimizing output.
- Python image/video packages when they are already available and simpler for the job.

The tool is less important than the result: short, legible, theme-consistent, and directly relevant.

## JavaScript Animation Selection

| Library | Best For | Typical Workflow |
|---|---|---|
| Motion Canvas | Educational and technical videos | Programmatic scene building, then render video |
| Theatre.js | Detailed motion graphics | Keyframe sequence editing, then export/capture |
| FFCreatorLite | Fast server-side videos | Compose scenes in Node.js, render directly |
| GSAP | High-performance web animation | Animate DOM/SVG/canvas, capture with Playwright/FFmpeg |
| Mo.js | Motion graphics and shapes | Build shape animation, capture from browser |

Use these libraries when they are already installed or can be installed for the project. If not, Manim or a small browser canvas animation may be faster and more reliable.

## Raster Fallback

Use raster images when editability is not practical or the visual would take too long to build as native shapes.

- SVG diagrams: generate SVG, rasterize with Sharp, embed as PNG.
- Mermaid diagrams: render with `scripts/render-mermaid.js`, embed as PNG.
- Gradients and visual effects: rasterize first; CSS gradients do not convert reliably.
- Icons: rasterize SVG icons to PNG unless an editable PowerPoint symbol is easier.

## Mermaid

Use Mermaid for complex layouts where coordinates would be tedious.

```bash
node pptx-enhanced/scripts/render-mermaid.js flow.mmd workspace/flow.png --width 800 --theme base
```

Use theme colors in Mermaid `style` directives. Split diagrams above about 8-10 nodes across multiple slides.

## SVG Rules

- Use explicit SVG `width` and `height`.
- Use `Arial`.
- Escape `&` as `&amp;`.
- Avoid emoji in SVG text.
- Rasterize around `800-1200px` width for clean PPT output.

## Embedding

```html
<img src="workspace/diagram.png" style="width: 500pt; height: auto; max-height: 220pt;">
```

Always set a max height so images cannot push content beyond the slide body.
