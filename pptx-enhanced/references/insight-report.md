# Tech Insight report

A dense, evidence-led deck for a technology decision or landscape review. Use `"preset": "tech-insight"` (high density) and give every content slide a `kicker`, a `takeaway` or action title, and a `source`.

## Storyline

| # | Slide | type | Purpose |
|---|---|---|---|
| 1 | Title | `title` | Question, method, answer in the highlights panel |
| 2 | Executive summary | `insightSummary` | Answer first: 3-5 findings with evidence stats and a "so what" |
| 3 | Landscape | `landscape` | Options by category with maturity tags |
| 4+ | Deep dives | `techDeepDive` | One mechanism per slide: text, diagram, metrics |
| | Benchmark | `benchmark` | Chart, results table, findings, method line |
| | Evaluation | `scorecard` | Weighted criteria, totals, radar, recommendation |
| | Comparison | `comparison` / `prosCons` | Feature matrix, or trade-offs with scores and facts |
| | Risks | `riskMatrix` | Likelihood x impact, mitigation, owner |
| | Cost and outlook | `panels` | Chart + image + stats |
| | Roadmap | `timeline` | Phases and owners |
| last | Sources | `sources` | Numbered references |

## Writing rules

- Titles state the claim ("Choose the simplest broker that meets 24-month load"), not the topic.
- Every number has a source line; use `source` on the slide.
- One idea per slide; put a metric strip or stats panel under any diagram.
- Prefer a chart or table to a paragraph. Keep bullets to one line at high density.
- Scorecard weights and scales must be stated on the slide (`subtitle`).
- Show uncertainty: label estimates, and use `method` on benchmarks.

## Density tips

- `high` fits about 60-90 words of text plus a chart and table per slide. If the build warns about overflow, split the slide rather than shrinking text.
- Use `"density": "low"` on the title, summary and closing slides if the audience will present from it.
- `panels` layouts: `"0|1/2"` for chart + table + findings; `"0;1|2"` for a wide header chart with two panels under it; `"0|1|2"` for three-way comparisons.

See `examples/insight-deck.json` for a complete working report.
