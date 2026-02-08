# dataviz-enhanced — Data Visualization Generator

A Claude Code skill that transforms data into publication-quality, Tufte-inspired visualizations with optional anomaly highlighting.

## When to Use This Skill

Use this skill when the user asks you to:

- Create charts, graphs, or plots from data
- Visualize CSV, JSON, Excel, or tabular data
- Generate publication-quality figures for reports or papers
- Highlight outliers or anomalies in data visually
- Compare multiple data series in a single chart
- Produce a grid of charts for review

## Skill Contents

```
dataviz-enhanced/
├── SKILL.md                    # This file
├── README.md                   # Quick-start for humans
├── default-viz-config.json     # Theme, palettes, chart defaults, highlight styles
├── requirements.txt            # Python dependencies
└── scripts/
    ├── parse_input.py          # Structured file → normalized CSV/JSON
    ├── generate_chart.py       # Core visualization engine (data → SVG/PNG/PDF)
    ├── detect_highlights.py    # Anomaly detection → highlights JSON
    └── preview_grid.py         # Arrange multiple charts into a review grid
```

## Setup

Install Python dependencies:

```bash
pip install -r dataviz-enhanced/requirements.txt
```

Required: Python 3.10+. No Node.js or system dependencies needed.

## Workflow

Follow these steps in order when generating a visualization:

### Step 1: Identify Input Format

Determine the format of the user's data:

| Format | Action |
|--------|--------|
| CSV, TSV, JSON, Excel (.xlsx), YAML | Use `parse_input.py` to normalize |
| Markdown table, HTML table | Use `parse_input.py` to extract |
| Unstructured text/prose | **You (Claude) extract the data** into a CSV/JSON file. Scripts do NOT handle prose. |
| Inline data in the prompt | **You (Claude) write it** to a CSV/JSON file first |

### Step 2: Parse Structured Data

For structured inputs, normalize to clean CSV or JSON:

```bash
python dataviz-enhanced/scripts/parse_input.py <input_file> <output_file> [--format csv|json] [--sheet NAME]
```

**Arguments:**
- `input_file` — Path to source data (CSV, TSV, JSON, Excel, Markdown, HTML, YAML)
- `output_file` — Path for normalized output
- `--format csv|json` — Output format (default: inferred from output extension)
- `--sheet NAME` — Excel sheet name (default: first sheet)

**What it does:**
- Detects format from file extension
- Parses and normalizes the DataFrame (cleans column names, auto-detects types, drops empty rows/cols)
- Outputs clean CSV or JSON ready for charting

**For unstructured text:** Skip this step. Read the text yourself, extract the data, and write it to a CSV or JSON file directly.

### Step 3: Generate Chart

Use the core engine to produce the visualization:

```bash
python dataviz-enhanced/scripts/generate_chart.py <data> <output> --type TYPE --x COL --y COL [options]
```

**Required arguments:**
- `data` — Input data file (CSV, JSON, or Excel)
- `output` — Output image file (PNG, SVG, or PDF)
- `--type TYPE` — Chart type (see chart type reference below)
- `--x COL` — X-axis column name
- `--y COL` — Y-axis column name (comma-separated for multi-series)

**Optional arguments:**
- `--title TEXT` — Chart title (rendered in Georgia, bold, left-aligned)
- `--subtitle TEXT` — Subtitle below title
- `--xlabel TEXT` — X-axis label (default: column name)
- `--ylabel TEXT` — Y-axis label (default: column name)
- `--palette NAME` — Color palette: `colorblind` (default), `sequential`, `diverging`, `categorical`, `monochrome`
- `--color COL` — Column for color grouping (scatter, bubble)
- `--size COL` — Column for size encoding (bubble)
- `--group COL` — Column for faceting (small_multiples)
- `--trend linear|polynomial` — Add trend line with R² annotation
- `--degree N` — Polynomial degree for trend line (default: 2)
- `--highlights FILE` — Path to highlights JSON from detect_highlights.py
- `--stacked` — Use stacked area chart
- `--bins N` — Number of bins for histogram
- `--figsize W H` — Figure size in inches (default: 10 6)
- `--dpi N` — Output resolution (default: 150)
- `--config FILE` — Path to custom config JSON

**Data reduction arguments** (essential for large datasets):
- `--top N` — Show only the top N rows by y-value (descending)
- `--bottom N` — Show only the bottom N rows by y-value (ascending)
- `--agg FUNC` — Aggregation function: `mean`, `sum`, `median`, `count`, `min`, `max` (use with `--groupby`)
- `--groupby COL` — Column to group by before aggregation
- `--sort-by COL` — Column to sort by (default: y-column)
- `--sort-order asc|desc` — Sort direction (default: desc)
- `--max-categories N` — Max categories to display; remaining are grouped as "Other"

### Step 4: (Optional) Detect Anomalies and Highlights

Analyze data for outliers and notable points:

```bash
python dataviz-enhanced/scripts/detect_highlights.py <data> <output_json> [--column COL] [--methods zscore iqr minmax changepoint]
```

**Arguments:**
- `data` — Input data file (CSV, JSON)
- `output_json` — Output highlights JSON file
- `--column COL` — Column to analyze (default: first numeric column)
- `--methods` — Detection methods: `zscore`, `iqr`, `minmax`, `changepoint` (default: all)
- `--threshold N` — Z-score threshold (default: 2.5)
- `--iqr-multiplier N` — IQR fence multiplier (default: 1.5)
- `--window N` — Changepoint window size (default: 5)

Then re-run generate_chart.py with `--highlights`:

```bash
python dataviz-enhanced/scripts/generate_chart.py data.csv chart.png --type line --x date --y price --highlights highlights.json
```

### Step 5: (Optional) Create Preview Grid

Arrange multiple charts into a single review image:

```bash
python dataviz-enhanced/scripts/preview_grid.py <img1> [img2 ...] <output> [--cols 3]
```

**Arguments:**
- Positional: input image files, last one is output (or use `--output`)
- `--cols N` — Grid columns (default: 3)
- `--padding N` — Padding in pixels (default: 20)
- `--bg COLOR` — Background color (default: white)
- `--no-labels` — Disable filename labels

### Step 6: Review and Iterate

After generating charts, review the output. Common adjustments:
- Change chart type if the data story isn't clear
- Adjust palette for better contrast or accessibility
- Add/remove trend lines or highlights
- Change figsize/dpi for different output contexts

---

## Chart Type Reference

### `line`
Best for: trends over ordered categories or time.
```bash
python generate_chart.py data.csv chart.png --type line --x month --y sales
python generate_chart.py data.csv chart.png --type line --x month --y "sales,costs" --title "Revenue vs Costs"
```

### `bar`
Best for: comparing quantities across categories.
```bash
python generate_chart.py data.csv chart.png --type bar --x product --y revenue
python generate_chart.py data.csv chart.png --type bar --x quarter --y "revenue,profit" --title "Quarterly Results"
```

### `hbar`
Best for: ranked comparisons with long category labels.
```bash
python generate_chart.py data.csv chart.png --type hbar --x country --y gdp --title "GDP by Country"
```

### `scatter`
Best for: relationships between two numeric variables.
```bash
python generate_chart.py data.csv chart.png --type scatter --x height --y weight --color gender
python generate_chart.py data.csv chart.png --type scatter --x x --y y --trend linear
```

### `histogram`
Best for: distribution of a single variable.
```bash
python generate_chart.py data.csv chart.png --type histogram --x score --y score --bins 20
```

### `heatmap`
Best for: correlations, cross-tabulations, matrix data.
```bash
python generate_chart.py data.csv chart.png --type heatmap --x col_a --y col_b
```
If `--x` and `--y` are both provided, creates a pivot table heatmap. Otherwise shows a correlation matrix of all numeric columns.

### `box`
Best for: distribution comparison across groups.
```bash
python generate_chart.py data.csv chart.png --type box --x department --y salary
```

### `pie`
Best for: part-of-whole composition (use sparingly, prefer bar charts).
```bash
python generate_chart.py data.csv chart.png --type pie --x category --y amount
```

### `donut`
Best for: part-of-whole with a cleaner look than pie.
```bash
python generate_chart.py data.csv chart.png --type donut --x segment --y users
```

### `area`
Best for: volume/magnitude over time, stacked composition.
```bash
python generate_chart.py data.csv chart.png --type area --x year --y "desktop,mobile,tablet" --stacked
```

### `bubble`
Best for: three-dimensional comparison (x, y, size).
```bash
python generate_chart.py data.csv chart.png --type bubble --x gdp --y life_expectancy --size population --color continent
```

### `timeseries`
Best for: data with date/datetime x-axis (auto-formats dates).
```bash
python generate_chart.py data.csv chart.png --type timeseries --x date --y stock_price --title "AAPL 2024"
```

### `small_multiples`
Best for: comparing the same metric across many groups (faceted).
```bash
python generate_chart.py data.csv chart.png --type small_multiples --x month --y sales --group region
```

---

## Highlight Style Reference

When detect_highlights.py finds anomalies, it assigns a `suggested_style` to each. The styles control how highlights render on the chart:

| Style | Visual | Best For |
|-------|--------|----------|
| `halo_ring` | Concentric ring around point | High-severity outliers |
| `color_shift` | Point color changes to highlight color | Medium-severity outliers |
| `size_boost` | Point is enlarged | Drawing attention without annotation |
| `glow` | Soft glow behind point | Subtle emphasis |
| `annotation_arrow` | Arrow + text label pointing to point | Min/max, labeled points |
| `band_shade` | Shaded vertical band | Changepoints, time ranges |
| `marker_change` | Different marker shape (diamond) | Distinguishing special points |
| `combo` | Multiple styles combined | Maximum emphasis |

---

## Color Palettes

| Name | Description | Use Case |
|------|-------------|----------|
| `colorblind` | Wong (2011) 8-color palette | Default — accessible to all viewers |
| `sequential` | Blue single-hue gradient | Ordered numeric data |
| `diverging` | Red-blue two-hue gradient | Data with meaningful midpoint |
| `categorical` | High-contrast distinct colors | Nominal/categorical data |
| `monochrome` | Grayscale | Print-friendly, formal reports |

---

## Tufte Styling

All charts follow Tufte's principles of data-ink maximization:

- **No top/right spines** — removed to reduce chart junk
- **Subtle dashed gridlines** — faint y-axis grid for readability
- **Clean typography** — Georgia (serif) for titles, Arial (sans) for data labels
- **Left-aligned titles** — more natural reading flow
- **Minimal margins** — maximize data area
- **No unnecessary decoration** — no 3D effects, shadows, or gradients

---

## Configuration

The default config is in `default-viz-config.json`. You can override it per-chart with `--config custom.json`.

Key sections:
- `theme` — Name and description
- `palettes` — Named color arrays
- `chart` — Figure size, DPI, grid, spines, fonts, margins
- `chart_types` — Per-type defaults (line width, bar width, scatter size, etc.)
- `highlights` — Highlight style configurations
- `statistics` — Trend line and annotation styling

---

## Working with Large Datasets

**IMPORTANT:** Before generating any chart, assess the data size and structure. Large datasets (>50 rows with many unique categories) will produce messy, unreadable charts if plotted raw. Always apply data reduction.

### Decision Guide

| Data Shape | Recommended Approach |
|-----------|---------------------|
| Many countries/categories (>15) | Use `--agg mean --groupby COL --top 15` to show top N |
| Time series with many entities | Use `--agg mean --groupby year` or `--type small_multiples --group region` |
| Distribution analysis | Use `histogram` or `box` — these handle large N natively |
| Part-of-whole with many slices | Use `--agg sum --groupby COL` (pie/donut auto-groups small slices into "Other") |
| Comparing groups | Use `box` with `--x group_col` or `scatter` with `--color group_col` |
| Ranked comparisons | Use `hbar` with `--top 20` for clean horizontal bars |

### Data Reduction Examples

**Top/Bottom N filtering:**
```bash
# Top 15 countries by average cost
python generate_chart.py data.csv chart.png --type bar --x country --y cost \
  --agg mean --groupby country --top 15 --title "Top 15 Most Expensive"

# Bottom 10 cheapest countries
python generate_chart.py data.csv chart.png --type hbar --x country --y cost \
  --agg mean --groupby country --bottom 10 --sort-order asc --title "10 Cheapest"
```

**Aggregation before plotting:**
```bash
# Average cost per year (trend over time)
python generate_chart.py data.csv chart.png --type line --x year --y cost \
  --agg mean --groupby year --title "Average Cost Over Time"

# Total cost by region (pie chart)
python generate_chart.py data.csv chart.png --type pie --x region --y cost \
  --agg sum --groupby region --title "Total Cost by Region"
```

**Max categories with "Other" grouping:**
```bash
# Show top 8 categories, group remainder as "Other"
python generate_chart.py data.csv chart.png --type donut --x category --y amount \
  --agg sum --groupby category --max-categories 8
```

### Auto-Scaling Behavior

The chart engine automatically adjusts for data volume:
- **Figure width** grows for >15 categories in bar/line charts
- **Figure height** grows for >12 items in horizontal bar charts
- **Tick labels** are rotated and truncated to prevent overlap
- **Markers** are suppressed on line charts with >50 points
- **Scatter alpha** is reduced for >200 points to avoid overplotting
- **Legends** move outside the chart when >6 groups; capped at 15 items
- **Pie/donut slices** are auto-grouped into "Other" when >10 slices

---

## Common Workflows

### Basic: CSV → Chart
```bash
python parse_input.py sales.csv clean_sales.csv
python generate_chart.py clean_sales.csv sales_chart.png --type bar --x month --y revenue --title "Monthly Revenue"
```

### Large Dataset: Aggregate → Filter → Chart
```bash
python parse_input.py world_data.xlsx clean.csv
python generate_chart.py clean.csv top_countries.png --type bar --x country --y gdp \
  --agg mean --groupby country --top 15 --title "Top 15 Countries by GDP"
python generate_chart.py clean.csv trend.png --type line --x year --y gdp \
  --agg mean --groupby year --title "Global GDP Trend"
python generate_chart.py clean.csv dist.png --type box --x region --y gdp --title "GDP Distribution by Region"
python preview_grid.py top_countries.png trend.png dist.png review.png --cols 3
```

### With Highlights: Data → Detect → Chart
```bash
python parse_input.py metrics.xlsx clean_metrics.csv
python detect_highlights.py clean_metrics.csv highlights.json --column revenue
python generate_chart.py clean_metrics.csv chart.png --type line --x date --y revenue --highlights highlights.json --title "Revenue with Anomalies"
```

### Multi-chart Review
```bash
python generate_chart.py data.csv bar.png --type bar --x cat --y val
python generate_chart.py data.csv scatter.png --type scatter --x x --y y
python generate_chart.py data.csv hist.png --type histogram --x x --y val
python preview_grid.py bar.png scatter.png hist.png review_grid.png --cols 3
```

### Unstructured Text → Chart
1. Read the user's text file
2. Extract tabular data yourself (Claude's job)
3. Write extracted data to a CSV file
4. Run generate_chart.py on the CSV

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Column 'X' not found` | Check column names with `parse_input.py` first; names are lowercased and cleaned |
| Chart is too small/large | Use `--figsize W H` (in inches) and `--dpi N` |
| Colors are hard to distinguish | Switch palette: `--palette categorical` or `--palette diverging` |
| Dates don't format properly | Use `--type timeseries` which auto-formats date axes |
| Highlights not rendering | Ensure highlights JSON indices match the data file row indices |
| `ModuleNotFoundError` | Run `pip install -r dataviz-enhanced/requirements.txt` |
| SVG output needed | Use `.svg` extension: `chart.svg` — automatically detected |
| Chart looks messy/cluttered | Use `--top N`, `--agg FUNC --groupby COL`, or `--max-categories N` to reduce data |
| Too many legend items | Engine auto-limits to 15 items; use `--top N` or `--max-categories N` to reduce groups |
| Labels overlapping | Engine auto-rotates/truncates; reduce categories with `--top N` for cleaner labels |
