#!/usr/bin/env python3
"""Detect anomalies and notable points in a numeric column, for chart highlighting.

Methods
  zscore       robust z-score (median/MAD) of values after removing the local trend
  iqr          Tukey fences on the same detrended values
  minmax       global minimum and maximum
  changepoint  level shifts, found on first differences (single-point spikes are ignored)

Trending series are detrended first (each point is compared with a robust line through its neighbours), so an outlier on a rising or
falling line is found even when it lies inside the overall range. Use --no-detrend to
test the raw values instead.

Usage:
    python detect_highlights.py <data> <output.json> [--column COL] [--methods zscore iqr minmax changepoint]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from dataio import read_csv_smart

SEVERITY = {"high": 3, "medium": 2, "low": 1}


def detrend(values: np.ndarray, k: int = 3) -> np.ndarray:
    """Residuals from a robust line fitted to each point's neighbours (the point itself is left out).

    Uses a Theil-Sen style median slope over +/-k neighbours, so a single outlier or a
    steady trend does not distort the fit. Needs 12+ points, otherwise returns the values.
    """
    n = len(values)
    if n < 12:
        return values
    res = np.full(n, np.nan)
    for i in range(n):
        idx = np.array([j for j in range(max(0, i - k), min(n, i + k + 1)) if j != i and not np.isnan(values[j])])
        if len(idx) < 3:
            continue
        y = values[idx]
        dx = idx[None, :] - idx[:, None]
        dy = y[None, :] - y[:, None]
        slopes = dy[dx > 0] / dx[dx > 0]
        m = np.median(slopes) if len(slopes) else 0.0
        icpt = np.median(y - m * idx)
        res[i] = values[i] - (m * i + icpt)
    return res


def robust_z(x: np.ndarray) -> np.ndarray:
    """(x - median) / (1.4826 * MAD); falls back to the standard deviation when MAD is 0."""
    med = np.nanmedian(x)
    scale = 1.4826 * np.nanmedian(np.abs(x - med))
    if not scale:
        scale = np.nanstd(x)
    return (x - med) / scale if scale else np.zeros_like(x)


def detect_zscore(values: np.ndarray, test: np.ndarray, threshold: float = 3.5) -> list[dict]:
    z = robust_z(test)
    out = []
    for i, zi in enumerate(z):
        if np.isnan(values[i]) or abs(zi) <= threshold:
            continue
        severity = "high" if abs(zi) > threshold + 2 else "medium"
        out.append({
            "index": int(i), "value": float(values[i]),
            "reason": f"Outlier ({'above' if zi > 0 else 'below'} trend)", "method": "zscore",
            "z_score": round(float(zi), 2), "severity": severity, "label": f"z={zi:.1f}",
            "suggested_style": "halo_ring" if severity == "high" else "color_shift",
        })
    return out


def detect_iqr(values: np.ndarray, test: np.ndarray, multiplier: float = 1.5) -> list[dict]:
    clean = test[~np.isnan(test)]
    if len(clean) < 4:
        return []
    q1, q3 = np.percentile(clean, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return []
    lo, hi = q1 - multiplier * iqr, q3 + multiplier * iqr
    out = []
    for i, t in enumerate(test):
        if np.isnan(t) or lo <= t <= hi:
            continue
        distance = (t - hi) / iqr if t > hi else (lo - t) / iqr
        out.append({
            "index": int(i), "value": float(values[i]),
            "reason": f"IQR outlier ({'above' if t > hi else 'below'} fences)", "method": "iqr",
            "severity": "high" if distance > 1.0 else "medium", "label": f"{values[i]:.1f}",
            "suggested_style": "annotation_arrow",
        })
    return out


def detect_minmax(values: np.ndarray) -> list[dict]:
    if np.all(np.isnan(values)):
        return []
    out = []
    for name, idx in (("Max", int(np.nanargmax(values))), ("Min", int(np.nanargmin(values)))):
        out.append({
            "index": idx, "value": float(values[idx]), "reason": f"Global {'maximum' if name == 'Max' else 'minimum'}",
            "method": "minmax", "severity": "low", "label": f"{name}: {values[idx]:.1f}", "suggested_style": "annotation_arrow",
        })
    return out


def detect_changepoint(values: np.ndarray, min_gap: int = 5, threshold: float = 3.0) -> list[dict]:
    """Level shifts: unusually large jumps between neighbours that do not bounce straight back."""
    if len(values) < 8:
        return []
    d = np.diff(values)
    z = robust_z(d)
    cands = []
    for i in range(len(d)):
        if np.isnan(z[i]) or abs(z[i]) <= threshold:
            continue
        # a spike jumps away and back: the neighbouring difference cancels most of it
        for j in (i - 1, i + 1):
            if 0 <= j < len(d) and d[i] * d[j] < 0 and abs(d[i] + d[j]) < 0.5 * max(abs(d[i]), abs(d[j])):
                break
        else:
            cands.append(i)
    out = []
    for i in cands:
        if out and i + 1 - out[-1]["index"] < min_gap:
            if abs(z[i]) > out[-1]["shift_z"]:
                out.pop()
            else:
                continue
        direction = "up" if d[i] > 0 else "down"
        out.append({
            "index": int(i + 1), "value": float(values[i + 1]), "reason": f"Level shift ({direction})", "method": "changepoint",
            "shift_z": round(float(abs(z[i])), 2), "severity": "high" if abs(z[i]) > threshold + 2 else "medium",
            "label": f"Shift {direction}", "suggested_style": "band_shade",
        })
    for h in out:
        h.pop("shift_z", None)
    return out


def deduplicate(highlights: list[dict]) -> list[dict]:
    """One highlight per index: the highest severity wins (first one on ties)."""
    seen: dict[int, dict] = {}
    for h in highlights:
        cur = seen.get(h["index"])
        if cur is None or SEVERITY[h["severity"]] > SEVERITY[cur["severity"]]:
            seen[h["index"]] = h
    return sorted(seen.values(), key=lambda h: h["index"])


def main():
    p = argparse.ArgumentParser(description="Detect anomalies and notable datapoints for chart highlighting.")
    p.add_argument("data", type=Path, help="Input data file (CSV, JSON)")
    p.add_argument("output", type=Path, help="Output highlights JSON file")
    p.add_argument("--column", help="Column to analyze (default: first numeric column)")
    p.add_argument("--methods", nargs="+", choices=["zscore", "iqr", "minmax", "changepoint"],
                   default=["zscore", "iqr", "minmax", "changepoint"], help="Detection methods to apply")
    p.add_argument("--threshold", type=float, default=3.5, help="Robust z-score threshold (default: 3.5)")
    p.add_argument("--iqr-multiplier", type=float, default=1.5, help="IQR fence multiplier (default: 1.5)")
    p.add_argument("--cp-threshold", type=float, default=3.0, help="Level-shift threshold on differences (default: 3.0)")
    p.add_argument("--window", type=int, default=5, help="Minimum spacing between level shifts (default: 5)")
    p.add_argument("--no-detrend", action="store_true", help="Test raw values instead of values minus the local trend")
    a = p.parse_args()

    if not a.data.exists():
        print(f"Error: Data file not found: {a.data}", file=sys.stderr)
        sys.exit(1)
    df = pd.read_json(a.data) if a.data.suffix.lower() == ".json" else read_csv_smart(a.data)

    if a.column:
        if a.column not in df.columns:
            print(f"Error: Column '{a.column}' not found. Available: {list(df.columns)}", file=sys.stderr)
            sys.exit(1)
        col = a.column
    else:
        numeric = df.select_dtypes(include=[np.number]).columns
        if len(numeric) == 0:
            print("Error: No numeric columns found in data.", file=sys.stderr)
            sys.exit(1)
        col = numeric[0]
        print(f"Auto-selected column: {col}")

    values = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
    test = values if a.no_detrend else detrend(values)
    if test is not values:
        print(f"Testing detrended values ({len(values)} points)")

    detectors = {
        "zscore": lambda: detect_zscore(values, test, a.threshold),
        "iqr": lambda: detect_iqr(values, test, a.iqr_multiplier),
        "minmax": lambda: detect_minmax(values),
        "changepoint": lambda: detect_changepoint(values, a.window, a.cp_threshold),
    }
    found = []
    for name in a.methods:
        res = detectors[name]()
        found.extend(res)
        if res:
            print(f"  {name}: found {len(res)} highlight(s)")

    highlights = deduplicate(found)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(highlights, indent=2), encoding="utf-8")
    print(f"Wrote {len(highlights)} highlights to {a.output}")


if __name__ == "__main__":
    main()
