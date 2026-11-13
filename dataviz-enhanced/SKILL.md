---
name: dataviz-enhanced
description: Turn tabular data (CSV, TSV, JSON, Excel, YAML, Markdown/HTML tables) into clean, publication-quality charts, with anomaly detection and highlighting. Use when asked to chart, plot or visualize data, compare series, find outliers or trends, or make charts for a report or slide deck. Built on Altair (Vega-Lite); outputs PNG, SVG, PDF, interactive HTML, or the Vega-Lite JSON spec.
license: Complete terms in LICENSE
---

# dataviz-enhanced

Minimal-ink charts (Tufte-style) with one emphasis colour, direct value labels and no chart junk. Two looks: `tufte` (default, colourblind-safe) and `editorial` (red, slate and gold, matches `pptx-enhanced` decks).

## Setup

```bash
pip install -r dataviz-enhanced/requirements.txt   # Python 3.10+; no browser or system libraries needed
```

## Workflow

1. **Data.** Structured file: `python scripts/parse_input.py in.xlsx clean.csv` (detects `, ; tab |` delimiters and decimal commas, turns `1,200` / `1.2%` / `$3.1` into numbers, parses dates). Text, prose or inline numbers: write the table to a CSV yourself.
2. **Choose the chart** from the table below. Reduce big data first (`--top`, `--agg`, `--max-categories`); never plot 60 raw categories.
3. **Anomalies (optional).** `python scripts/detect_highlights.py clean.csv hl.json --column revenue`, then add `--highlights hl.json`.
4. **Generate.** `python scripts/generate_chart.py clean.csv out.png --type line --x date --y revenue --title "..."`
5. **Review.** Look at the image. `python scripts/preview_grid.py a.png b.png grid.png --cols 3` compares several. Iterate on type, palette, labels.

## Chart types

| `--type` | Use for | Notes |
|---|---|---|
| `line`, `timeseries` | trends (timeseries parses dates) | several `--y` columns = several lines; `--trend linear` adds R² and a 95% band |
| `bar`, `hbar` | comparisons, rankings | one series = one colour with value labels; several `--y` = grouped bars; `hbar` for long labels |
| `scatter`, `bubble` | relationships | `--color COL` groups, `--size COL` (bubble), `--trend` |
| `histogram`, `box` | distributions | `--bins N`; box groups by `--x` |
| `heatmap` | matrix or correlation | `--x` and `--y` = pivot of the other numeric column; omit `--y` for a correlation matrix |
| `pie`, `donut` | part of a whole (few slices) | small slices merge into "Other" |
| `area` | volume over time | `--stacked` for composition |
| `small_multiples` | same metric across groups | `--group COL` |

## Options

`--title --subtitle --xlabel --ylabel` · `--palette NAME` · `--theme tufte|editorial` · `--preset report|slide` · `--figsize W H` (inches) · `--dpi N` · `--order a,b,c` (category order) · `--config file.json` (merged over `default-viz-config.json`).
Data reduction: `--top N --bottom N --agg mean|sum|median|count|min|max --groupby COL --sort-by COL --sort-order asc|desc --max-categories N`.
Output by extension: `.png .svg .pdf .html` (interactive) `.json` (Vega-Lite spec, reusable on the web).
Palettes: `colorblind` (default), `categorical`, `monochrome`, `sequential`, `diverging`, `editorial`, `editorial_sequential`, `editorial_diverging`.

## Highlights

`detect_highlights.py` methods: `zscore` and `iqr` (on detrended values, so outliers on a rising line are found), `minmax`, `changepoint` (level shifts; single spikes are ignored). Default: all four. Row numbers refer to the file given to the detector, so do not combine `--highlights` with `--top`/`--agg` that reorder rows. Styles: `halo_ring`, `color_shift`, `size_boost`, `glow`, `annotation_arrow`, `band_shade`, `marker_change`, `combo`.

## Charts for slides and reports

- For `pptx-enhanced`: `--theme editorial --preset slide`, then use the PNG in a `panels` slide (`{"kind": "image", "path": "chart.png"}`). **Render at the slot size**: `--figsize` = the panel's width and height in inches (about 5.6 x 3.2 for a main panel, 4.4 x 1.9 for a quarter), otherwise text shrinks below 6pt. Omit `--title` when the slide or panel already has one.
- Charts should make one point: use an action title, `--top` for rankings, `--highlights` for the thing to look at.
- Do not smooth lines or invent values. Mention estimates in a subtitle.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Column 'X' not found` | Names are cleaned (`.` `:` `[` become `_`); run `parse_input.py` and check the header |
| `--y is required` | All types except `histogram` and `heatmap` need `--y` |
| Too many categories | `--top N`, `--max-categories N`, or `--type hbar` |
| Dates shown as text | Use `--type timeseries` or `parse_input.py` first |
| Numbers read as text | Run `parse_input.py` (cleans `%`, `$`, thousands separators) |
| `Unknown theme/preset` | Themes: tufte, editorial. Presets: report, slide |
| Text too small in a deck | Lower `--figsize` to the panel size (see above) |

Examples: `python examples/build.py` writes `examples/out/` (report charts, slide charts, grids, and a demo deck if `pptx-enhanced` is installed).
