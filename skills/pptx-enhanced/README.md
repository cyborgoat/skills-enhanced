# pptx-enhanced

Claude Code skill that builds compact, editable PowerPoint decks in an **Editorial Light** theme (white, red titles, gold highlights, slate support).

- **~30 page types** from a JSON spec: title, agenda, KPI + chart, tables, product comparison matrix, pros/cons evaluation (score chart, facts, stats), pricing, process, timeline, quote, code walkthrough, closing, and a `panels` grid for mixing charts, tables, images, diagrams and text.
- **Tech Insight report pages**: executive summary, landscape, deep dive, benchmark, weighted scorecard, risk matrix, sources.
- **Information density**: `low`, `medium` or `high` per deck or per slide.
- **Technical diagrams**: sequence, UML class, ER, state, flow and layered architecture as editable native shapes, or Mermaid images for dense layouts.
- **Native charts and tables**, auto-fitted text so slides stay full rather than bulky.
- Escape hatch to hand-written HTML slides (`html2pptx`) and raw PptxGenJS.

## Install

```bash
npx skills add cyborgoat/skills-enhanced --skill pptx-enhanced
```

## Setup

Use Node.js 22+ and Python 3.10+.

```bash
# Run from the installed skill directory (skills/pptx-enhanced in this repository)
npm install && npm run install-browsers
pip install -r requirements.txt
brew install libreoffice poppler   # optional: thumbnail validation
```

## Use

In Claude Code: `/pptx-enhanced Create a deck on our payments architecture`.

Or directly:

```bash
node scripts/build-deck.js examples/deck.json out.pptx
node examples/build.js            # example.pptx, insight-report.pptx, density-demo.pptx
node scripts/lint-pptx.js out.pptx # check for PowerPoint repair triggers (runs on every build)
```

```json
{ "density": "medium", "slides": [
  { "type": "title", "title": "Q4 Review", "subtitle": "Platform team" },
  { "type": "diagram", "title": "Checkout", "kind": "sequence", "mode": "native",
    "data": { "actors": ["Client", "API"], "messages": [{ "from": "Client", "to": "API", "text": "POST /orders" }] } }
] }
```

Data shapes for every type: `references/layouts.md`.

## Layout

```
SKILL.md                    skill entry (workflow, page types, rules)
html2pptx.md                HTML slide rules and converter API
default-pptx-config.json    theme colours, fonts, density tokens
references/                 layouts, insight-report, visuals, pptxgenjs, validation
scripts/build-deck.js       JSON spec to .pptx
scripts/templates.js        page-type templates, panel engine, density
scripts/diagrams.js         native diagram helpers
scripts/html2pptx.js        HTML to PPTX converter
scripts/render-mermaid.js   Mermaid to PNG (themed)
scripts/lint-pptx.js        PowerPoint repair-trigger lint
scripts/inventory.py        text inventory and overflow check
scripts/thumbnail.py        thumbnail grid (LibreOffice + Poppler)
examples/                   showcase decks (deck.json, insight-deck.json, build.js)
```

Customise the palette in `default-pptx-config.json` or per deck with `"theme": {"colors": {...}}`.
