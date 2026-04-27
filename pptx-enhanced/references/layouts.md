# Layout Catalog

Use these as starting points. Keep each slide sparse enough to pass the converter overflow checks.

## Common Shell

```html
<style>
html { background: #FFFFFF; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column; position: relative;
}
h1, h2, h3, p, ul, ol { margin: 0; }
</style>
<div style="padding: 14pt 30pt 4pt 30pt;">
  <h1 style="font-size: 22pt; font-weight: bold; color: #C62828;">Slide Title</h1>
  <p style="font-size: 10pt; color: #7B8794; margin-top: 3pt;">Subtitle</p>
</div>
<div style="margin: 4pt 30pt 0 30pt; height: 1pt; background: #D7DEE8;"></div>
```

## Layout Options

| Layout | Use For | Structure |
|---|---|---|
| `title` | Opening, section divider | Large title, short subtitle, simple visual signal |
| `threeColumn` | Three concepts or capabilities | 3 equal cards with label, title, body |
| `twoColumnSplit` | Compare two domains | 2 columns with cards or key-value rows |
| `comparison` | Before/after or old/new | Left/right columns, contrasting headers |
| `timeline` | Roadmap or evolution | 3-5 phases with dates and short descriptions |
| `horizontalProcess` | Workflow or lifecycle | 3-5 editable shape steps with arrows |
| `problemSolution` | Problem framing | Problem panel plus numbered solution steps |
| `centralHub` | System components | Center concept with 3-4 surrounding cards |
| `quadrant` | Prioritization matrix | 2x2 grid plus short interpretation panel |
| `funnel` | Progressive narrowing | Vertical stages with a final outcome |
| `supplyChain` | Pipeline | 4-6 sequential stages with details below |
| `businessModel` | Strategy transition | Old model, new model, strategic callout |
| `challengeTable` | Risks and mitigations | Header row plus 3-5 compact rows |
| `closingSlide` | Summary | One central takeaway plus 2-3 supporting points |

## Spacing Defaults

- Side margin: `30pt`.
- Title area: about `40-45pt` high.
- Content top padding after divider: `12-18pt`.
- Card radius: `6pt`; padding: `10-12pt`.
- Bottom callout: `bottom: 12pt`; keep regular content above `bottom: 62pt`.
- Columns: `10-16pt` gap for dense slides, `20pt` for roomy slides.

## Density Limits

- Maximum 3 cards per column.
- Maximum 5 table rows.
- Maximum 5 process steps in one row.
- Body copy: 1-3 short lines per card.
- If a slide needs more content, split it rather than shrinking text below `9pt`.

## Bottom Callout

```html
<div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #FFB300; border-radius: 4pt; padding: 7pt 15pt; display: flex; gap: 10pt;">
  <p style="font-size: 11pt; font-weight: bold; color: #1F2937;">KEY IDEA</p>
  <p style="font-size: 9pt; color: #1F2937;">Short takeaway for the slide.</p>
</div>
```
