# dataviz-enhanced

Publication-quality, Tufte-inspired data visualizations with optional anomaly highlighting. A Claude Code skill for generating charts from structured data (CSV, JSON, Excel) or unstructured text.

## Features

- 13 chart types: line, bar, hbar, scatter, histogram, heatmap, box, pie, donut, area, bubble, timeseries, small multiples
- Tufte-inspired minimal styling: no chart junk, clean typography, accessible colors
- Anomaly detection with Z-score, IQR, min/max, and changepoint methods
- Highlight overlays: halo rings, color shifts, annotations, glow effects, bands
- Multi-format input: CSV, TSV, JSON, Excel, Markdown tables, HTML tables, YAML
- Multi-format output: PNG, SVG, PDF
- 5 color palettes including a colorblind-safe default (Wong 2011)
- Statistical annotations: trend lines, R², confidence bands
- Preview grid for comparing multiple charts

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Parse input data
python scripts/parse_input.py data.xlsx clean_data.csv

# Generate a chart
python scripts/generate_chart.py clean_data.csv chart.png --type bar --x category --y value --title "My Chart"

# Detect anomalies (optional)
python scripts/detect_highlights.py clean_data.csv highlights.json --column value

# Re-generate with highlights
python scripts/generate_chart.py clean_data.csv chart.png --type line --x date --y value --highlights highlights.json

# Create a review grid of multiple charts
python scripts/preview_grid.py chart1.png chart2.png chart3.png grid.png --cols 3
```

## File Structure

```
dataviz-enhanced/
├── SKILL.md                    # Full skill documentation
├── README.md                   # This file
├── default-viz-config.json     # Theme, palettes, chart defaults
├── requirements.txt            # Python dependencies
└── scripts/
    ├── parse_input.py          # Data file → normalized CSV/JSON
    ├── generate_chart.py       # Data → chart (SVG/PNG/PDF)
    ├── detect_highlights.py    # Anomaly detection → highlights JSON
    └── preview_grid.py         # Multiple images → review grid
```

## Color Palettes

| Name | Colors | Use Case |
|------|--------|----------|
| `colorblind` | Wong (2011) 8-color | Default — accessible |
| `sequential` | Blue gradient | Ordered data |
| `diverging` | Red ↔ Blue | Data with midpoint |
| `categorical` | High contrast | Nominal categories |
| `monochrome` | Grayscale | Print-friendly |

## Workflow

1. **Parse** structured data with `parse_input.py`
2. **Generate** chart with `generate_chart.py`
3. **Detect** anomalies with `detect_highlights.py` (optional)
4. **Re-generate** chart with `--highlights` flag (optional)
5. **Review** multiple charts with `preview_grid.py` (optional)

See [SKILL.md](SKILL.md) for full documentation, all CLI options, and chart type examples.

## License

MIT
