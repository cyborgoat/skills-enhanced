---
name: pptx-enhanced
description: Build compact, polished .pptx decks from a JSON spec or HTML slides, at low, medium or high information density. Covers KPI/chart slides, tables, product comparison matrices, pros/cons evaluations, pricing, timelines, mixed-content panel pages, Tech Insight report pages (summary, landscape, deep dive, benchmark, scorecard, risk matrix), and technical diagrams (UML class, sequence, ER, state, architecture) as editable native shapes or Mermaid images. Use for any request to create or restyle a PowerPoint, deck, slides, or an insight/research report in slide form.
license: MIT
compatibility: Requires Node.js 22+. Python 3.10+ for validation utilities; Chromium for HTML workflows; LibreOffice and Poppler for optional thumbnails. Mermaid rendering may require network access.
---

# pptx-enhanced

Editorial Light theme (white, red titles, gold highlights, slate support). Slides are compact: content fills the slide and text adapts to the amount of content.

## Workflow

1. Plan the deck: one message per slide; pick a page type for each (table below). **Ask the user for density** (`low` / `medium` / `high`) unless stated; default `medium`, reports default `high`. For diagrams also ask native vs Mermaid once.
2. Write a deck spec (JSON): `{ "density": "medium", "slides": [ { "type": "kpi", "title": "...", ... } ] }`. Data shapes: `references/layouts.md`.
3. Build: `node scripts/build-deck.js deck.json out.pptx` (run from this directory or use absolute paths). It also lints the file for PowerPoint "Repair" triggers and fails if it finds any.
4. Validate (below), fix, rebuild.
5. Deliver the `.pptx` and the spec. Working examples: `node examples/build.js` (`example.pptx`, `insight-report.pptx`, `density-demo.pptx`).

## Page types

| Need | `type` |
|---|---|
| Opening, divider, agenda, closing | `title`, `section`, `agenda`, `closing` |
| Text points, 2-4 cards, quote, code walkthrough | `bullets`, `columns`, `quote`, `codeExplain` |
| Numbers and trends | `kpi` (tiles + chart), `chart` (bar, hbar, line, area, pie, doughnut, radar) |
| Tabular data | `table` |
| Option comparison | `comparison` (matrix), `prosCons` (with score chart, facts table, stats, image or diagram), `beforeAfter`, `pricingCards` |
| Process and time | `process`, `timeline` |
| Diagrams | `diagram` with `kind`: `sequence`, `class`, `er`, `state`, `flow`, `architecture` |
| Anything mixed (chart + table + text + image + diagram) | `panels` with a layout string |
| Tech Insight report | `insightSummary`, `landscape`, `techDeepDive`, `benchmark`, `scorecard`, `riskMatrix`, `sources` (`references/insight-report.md`) |
| Hand-written slide | `html` (see `html2pptx.md`) |

Every slide accepts `title`, `subtitle`, `notes` (speaker notes), `density` (override), `kicker` (section label), `takeaway` (headline bar), `source` (footer). Inline markup: `**bold**`.

## Density

`low`: big type, airy, 3-4 items per card. `medium`: balanced. `high`: 9.5-11.5pt body, tight gaps, up to 3 extra panels on composed slides, 16-row tables. Set per deck (`"density"` or `"preset": "tech-insight"`) and override per slide. The build warns when text or a table may not fit; shorten, split the slide, or lower the density.

## Diagrams

`mode`: `native` (editable PowerPoint shapes, default up to ~10 nodes) or `mermaid` (PNG, for dense layouts, needs network). Details: `references/visuals.md`.

## Rules

- Prefer tables, charts and diagrams over prose; every slide should earn its space.
- Body text 9.5pt or larger (9pt for table, chart and diagram labels).
- Colours and fonts come from `default-pptx-config.json`; override per deck with `"theme": {"colors": {...}}`.
- Hand-written HTML or raw PptxGenJS: read `html2pptx.md` and `references/pptxgenjs.md`. PptxGenJS colours never take `#`, and `rectRadius` is only valid on `roundRect` shapes (otherwise PowerPoint repairs the file and drops shapes).
- Images in `panels`/`prosCons` are local files (png, jpg, gif, svg) or data URIs; nothing is fetched from the web.
- Animations: for processes the user wants demonstrated, add a short GIF/video with a static fallback (`references/visuals.md`).

## Validation

- Build fails on overflow, wrong dimensions, and PowerPoint repair triggers (`node scripts/lint-pptx.js out.pptx`).
- `python scripts/inventory.py --issues-only out.pptx issues.json`: flags under ~0.2in are usually estimates.
- `python scripts/thumbnail.py out.pptx thumbs --cols 4` needs LibreOffice and Poppler. If absent, say so, and ask the user to open the deck once in PowerPoint to confirm it opens without a repair prompt.

## Setup

Run these commands from this skill's installed directory. Node.js 22+ and Python 3.10+ are recommended.

```bash
npm install && npm run install-browsers && pip install -r requirements.txt
brew install libreoffice poppler   # optional, for thumbnails
```

References: `references/layouts.md` data shapes · `references/insight-report.md` report storyline · `references/visuals.md` diagrams, images, animation · `references/pptxgenjs.md` charts, tables, shapes · `references/validation.md` fixes · `html2pptx.md` HTML slide rules.
