#!/usr/bin/env python3
"""Regenerate the example charts: python examples/build.py   (needs requirements.txt installed).

Writes examples/out/: report-style charts (Tufte theme), slide-sized charts (editorial theme, matches
pptx-enhanced) and review grids. If Node and pptx-enhanced are installed it also builds a demo deck.
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
DATA, OUT = HERE / "data", HERE / "out"
OUT.mkdir(exist_ok=True)


def run(script, *args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{script} failed:\n{r.stderr.strip().splitlines()[-1]}")


def chart(name, data, kind, *extra):
    run("generate_chart.py", DATA / data, OUT / f"{name}.png", "--type", kind, *extra)
    print("wrote", OUT / f"{name}.png")


# Anomalies: detect first, then draw them
run("detect_highlights.py", DATA / "monthly.csv", OUT / "highlights.json", "--column", "revenue", "--methods", "zscore", "iqr", "minmax")

# Report style (Tufte theme, default palette)
chart("01-line", "monthly.csv", "line", "--x", "date", "--y", "revenue,costs", "--title", "Revenue vs costs", "--subtitle", "Monthly, 2024-2025")
chart("02-bar", "products.csv", "bar", "--x", "product", "--y", "revenue,profit", "--title", "Revenue and profit by product")
chart("03-top-n", "countries.csv", "hbar", "--x", "country", "--y", "cost", "--agg", "mean", "--groupby", "country", "--top", "10", "--title", "Top 10 by average cost")
chart("04-scatter-trend", "scatter.csv", "scatter", "--x", "x", "--y", "y", "--color", "group", "--trend", "linear", "--title", "Relationship with trend")
chart("05-box", "scatter.csv", "box", "--x", "group", "--y", "y", "--title", "Distribution by group")
chart("06-heatmap", "heat.csv", "heatmap", "--x", "weekday", "--y", "hour", "--title", "Visits by weekday and hour")
chart("07-donut", "products.csv", "donut", "--x", "product", "--y", "revenue", "--title", "Revenue share")
chart("08-stacked-area", "devices.csv", "area", "--x", "year", "--y", "desktop,mobile,tablet", "--stacked", "--title", "Traffic by device (%)")
chart("09-highlights", "monthly.csv", "line", "--x", "date", "--y", "revenue", "--highlights", OUT / "highlights.json", "--title", "Revenue with detected anomalies")
chart("10-small-multiples", "countries.csv", "small_multiples", "--x", "year", "--y", "cost", "--group", "region", "--title", "Average cost by region")
chart("11-timeseries-trend", "monthly.csv", "timeseries", "--x", "date", "--y", "revenue", "--trend", "linear", "--title", "Trend with 95% band")

# Slide style: editorial theme + slide preset (drop straight into pptx-enhanced decks).
# Render each chart at the size of its slide slot (inches), so text stays readable once placed;
# leave off --title when the slide or panel already carries one.
S = ["--theme", "editorial", "--preset", "slide"]
chart("slide-01-line", "monthly.csv", "line", "--x", "date", "--y", "revenue,costs", "--highlights", OUT / "highlights.json", "--figsize", "5.6", "3.2", *S)
chart("slide-02-bar", "products.csv", "hbar", "--x", "product", "--y", "revenue", "--figsize", "4.4", "1.9", *S)
chart("slide-03-heat", "heat.csv", "heatmap", "--x", "weekday", "--y", "hour", "--figsize", "4.4", "1.9", *S)
chart("slide-04-donut", "products.csv", "donut", "--x", "product", "--y", "revenue", "--figsize", "4.4", "1.9", *S)

for grid, pattern, cols in (("grid.png", "[01]*.png", 3), ("grid-slide.png", "slide-*.png", 2)):
    imgs = sorted(OUT.glob(pattern))
    run("preview_grid.py", *imgs, OUT / grid, "--cols", cols)
    print("wrote", OUT / grid)

# Optional: a deck that uses the slide charts (needs Node + pptx-enhanced/node_modules)
deck_tool = HERE.parent.parent / "pptx-enhanced" / "scripts" / "build-deck.js"
if shutil.which("node") and (HERE.parent.parent / "pptx-enhanced" / "node_modules").exists():
    r = subprocess.run(["node", str(deck_tool), str(HERE / "deck-with-charts.json"), str(OUT / "charts-deck.pptx")], capture_output=True, text=True)
    print("wrote", OUT / "charts-deck.pptx") if r.returncode == 0 else print("deck skipped:", r.stderr.strip().splitlines()[-1])
else:
    print("deck skipped (Node or pptx-enhanced not installed)")
