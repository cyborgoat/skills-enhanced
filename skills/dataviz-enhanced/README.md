# dataviz-enhanced

Claude Code skill that turns data into clean, publication-quality charts. Built on **Altair (Vega-Lite)**: every chart is a declarative spec, rendered to PNG, SVG or PDF without a browser, or exported as interactive HTML or the JSON spec.

- 13 chart types: line, timeseries, bar, hbar, scatter, bubble, histogram, box, heatmap, pie, donut, area, small multiples
- Two looks: `tufte` (colourblind-safe default) and `editorial` (matches `pptx-enhanced` decks); `slide` and `report` size presets
- Anomaly detection (robust z-score on detrended values, IQR, min/max, level shifts) drawn as highlights
- Input: CSV/TSV (delimiter and decimal-comma detection), JSON, Excel, YAML, Markdown and HTML tables; `1,200` / `1.2%` / `$3.1` become numbers
- Data reduction for big data: `--top`, `--agg --groupby`, `--max-categories`

## Install

```bash
npx skills add cyborgoat/skills-enhanced --skill dataviz-enhanced
```

## Quick start

Run from the installed skill directory using your Python environment.

```bash
pip install -r requirements.txt            # Python 3.10+
python scripts/parse_input.py data.xlsx clean.csv
python scripts/generate_chart.py clean.csv chart.png --type bar --x product --y revenue --title "Revenue"
python scripts/detect_highlights.py clean.csv hl.json --column revenue
python scripts/generate_chart.py clean.csv line.png --type line --x date --y revenue --highlights hl.json
python scripts/preview_grid.py chart.png line.png grid.png --cols 2
python examples/build.py                   # example charts in examples/out/
```

For slides: `--theme editorial --preset slide --figsize 5.6 3.2` (size = the slide slot, in inches), then reference the PNG from a `pptx-enhanced` `panels` slide.

## Layout

```
SKILL.md                    skill entry (workflow, chart table, options)
default-viz-config.json     themes, presets, palettes, chart defaults, highlight styles
requirements.txt
scripts/generate_chart.py   chart engine (Altair)
scripts/parse_input.py      files to clean CSV/JSON
scripts/dataio.py           shared loading helpers (delimiters, numeric cleanup)
scripts/detect_highlights.py  anomaly detection
scripts/preview_grid.py     contact sheet of several charts
examples/                   data, build.py, output charts, demo deck spec
```

MIT licensed.
