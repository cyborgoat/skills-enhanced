# Page types and data shapes

Spec: `{ "title"?, "author"?, "density"?: "low|medium|high", "preset"?: "tech-insight", "theme"?: {"colors": {...}}, "slides": [ {type, ...} ] }`.
Every slide also takes `title`, `subtitle`, `notes`, `density` (override), `kicker` (small section label above the title), `takeaway` (headline bar under the title) and `source` (9pt footer). Strings accept `**bold**`.
Layout is automatic: text size adapts to the amount of content, blocks are centred, charts/tables/diagrams fill the body. Add content or switch type rather than adding spacing.

## Structure

| type | data |
|---|---|
| `title` | `title, subtitle, meta, highlights: [{label, text}]` (right panel, up to 4) |
| `section` | `title, subtitle, number` |
| `agenda` | `items: [string \| {title, text}]` (2 columns when more than 4) |
| `closing` | `statement, points: [string \| {title, text}]` |

## Content

| type | data |
|---|---|
| `bullets` | `bullets: [..]`, optional `aside: {title, items}` |
| `columns` (`twoColumn`, `threeColumn`) | `columns: [{label, title, text, items, stat: {value, label}}]` 2-4 cards |
| `quote` | `quote, author, role` |
| `codeExplain` | `code` (string or lines), `points: [string \| {title, text}]` |
| `process` | `steps: [{title, text, items}]` 3-5, optional `callout: {label, text}` |
| `timeline` (`roadmap`) | `phases: [{date, title, text, items, status: "now"}]` 3-5 |

## Numbers

| type | data |
|---|---|
| `kpi` | `stats: [{label, value, delta}]` 3-4, `chart`, optional `insights: [..]`, `insightsTitle` |
| `chart` | `chart`, optional `insights` |

`chart`: `{type: "bar"\|"hbar"\|"line"\|"area"\|"pie"\|"doughnut"\|"radar", labels: [..], series: [{name, values}], title, xTitle, yTitle, min, max, dataLabels}`. Native, editable. One series = single colour with value labels; several = legend.

## Tables and comparison

| type | data |
|---|---|
| `table` | `columns: [..], rows: [[..]], align: [..], colW: [..] (ratios), highlightCol, note, fontSize` |
| `comparison` | `products: [..], rows: [{name, values: [..]} \| {group}], recommended: index, verdict: {label, text}`; optional `chart`, `insights: [..]` make it a multi-panel page |
| `prosCons` | `pros: {title?, items}, cons: {items}, verdict`; optional extras, capped by density (low 0, medium 2, high 3): `scores` (radar chart: `{labels, series}`), `facts: {title, columns, rows, colW}`, `stats: [{label, value, delta}]`, `diagram: {kind, mode, data}`, `image: {path, fit}` |
| `beforeAfter` | `before: {title, items}, after: {title, items}` |
| `pricingCards` | `plans: [{name, price, unit, tagline, badge, highlight, features: [..]}]` 2-4 |

Cell values: text, number, `true` (● yes), `false` (– no), or `{text, fill, color, bold}`. Up to ~9 rows and 6 columns per slide.

## Diagrams

`{type: "diagram", kind, mode: "native"\|"mermaid", data, mermaid, notes: [..], notesTitle, caption}`. `notes` adds a side panel. Mermaid mode takes a `mermaid` definition string instead of `data`.

| kind | data |
|---|---|
| `sequence` | `actors: [string \| {id, label}], messages: [{from, to, text, type: "sync"\|"async"\|"return"}]` (`from == to` is a self-call; sync calls open activation bars closed by the target's next return) |
| `class` | `classes: [{name, stereotype, attrs: [..], methods: [..]}], relations: [{from, to, type: "inherit"\|"implement"\|"compose"\|"aggregate"\|"assoc"\|"depend", label}]` (`from` is the child for inherit/implement, the owner otherwise) |
| `er` | `entities: [{name, fields: [{name, type, key: "PK"\|"FK"}]}], relations: [{from, to, card: "1:N", label}]` |
| `state` | `states: [string \| {id, label}], transitions: [{from, to, label}]`, `"[*]"` is start/end |
| `flow` | `nodes: [string \| {id, label, shape: "box"\|"pill"\|"diamond"\|"start"\|"end"}], edges: [{from, to, label, dashed}], dir: "LR"\|"TB"` |
| `architecture` | `layers: [{name, nodes: [{id, label, sub}]}], edges: [{from, to, label, dashed}]` |

Keep native diagrams to about 10 nodes and edges between neighbouring layers/ranks (edges skipping a rank can cross nodes). Self-loops are not drawn.

## Escape hatch

`{type: "html", file: "slide.html"}`: your own 720x405pt page (rules in `html2pptx.md`). Charts/tables added to `placeholder` divs need the module API; for that, call `build-deck` from your own script or use PptxGenJS directly.

## Density rules

- Content area is about 672 x 300pt (medium). Aim to fill 70%+ of it.
- Labels 9pt minimum; the build warns when a panel or table may overflow.
- Limits: 6 bullets per card, 4 columns, 5 process steps, 10 diagram nodes; table rows per density above.

## Panels (mixed content)

`{type: "panels", layout, panels: [...], rowFlex?, colFlex?, verdict?}`

Layout string: rows `;`, columns `|`, stacked panels `/`, numbers are panel indexes. `"0|1/2"` = one tall panel left, two stacked right; `"0;1|2"` = one wide panel on top, two below. Presets: `2x1`, `3x1`, `2x2`, `1+2`, `2+1`, `1+3`, `3+1`, `1/2`, `2/1`, `3x2`. A panel's `w` / `h` are relative column / stack weights.

| panel `kind` | data |
|---|---|
| `chart` | `chart` (same shape as above) |
| `table` | `columns, rows, colW, align, highlightCol, maxRowH` |
| `bullets` | `items` |
| `text` | `text` (string or paragraphs) |
| `stats` | `stats: [{label, value, delta}]` |
| `diagram` | `diagram: {kind, mode, data \| mermaid}` |
| `image` | `path` (png/jpg/gif/svg, relative to the spec) or data URI, `fit: "contain"\|"cover"` |
| `scorecard` | `items: [{name, score, max?}]`, `max` (native bars) |
| `chips` | `items: [string \| {name, tag: adopt\|trial\|assess\|hold}], note, points: [..]` |
| `callout` | `label, text` |

All but `callout` accept `title`. Text panels in one column share the smallest fitted font size.

## Tech Insight types

Storyline and tips: `insight-report.md`. All accept `kicker`, `takeaway`, `source`.

| type | data |
|---|---|
| `insightSummary` | `findings: [{title, text, stat: {value, label}}]` 3-5, `sowhat: {label, text}` |
| `landscape` | `categories: [{name, items: [string \| {name, tag}], note, points: [..]}]` 2-6, `legend: false` to hide the tag key |
| `techDeepDive` | `concept: {title, text, bullets}`, `diagram` or `image`, `metrics: [{label, value}]` |
| `benchmark` | `chart`, `table: {title, columns, rows, colW, highlightCol}`, `findings: [..]`, `method` |
| `scorecard` | `options: [..]`, `criteria: [{name, weight, scores: [..]}]`, `scale` (default 5), `recommendation: {label, text}`. Computes weights, weighted totals and a radar chart |
| `riskMatrix` | `risks: [{risk, likelihood, impact, mitigation, owner}]` (levels `Low`/`Medium`/`High` or 1-5), `summary`. Severity is computed and colour-coded |
| `sources` | `items: [..]`, `columns` |

## Density

| | low | medium | high |
|---|---|---|---|
| Body text | 12-18pt | 10-16pt | 9.5-11.5pt (panels up to 13) |
| Title / margin / gap | 22 / 28 / 14pt | 20 / 24 / 10pt | 17 / 18 / 6pt |
| Table rows (suggested max) | 8 | 10 | 16 |
| Extra panels on `prosCons` | 0 | 2 | 3 |
| Use for | talks, exec decks | working decks | reports, handouts |

Tokens live in `default-pptx-config.json` under `density.levels`.
