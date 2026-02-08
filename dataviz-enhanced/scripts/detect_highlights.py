#!/usr/bin/env python3
"""Detect anomalies and notable datapoints for chart highlighting.

Methods: Z-score, IQR, min/max, changepoint (sliding-window mean-shift).
Outputs a highlights JSON file compatible with generate_chart.py --highlights.

Usage:
    python detect_highlights.py <data> <output_json> [--column COL] [--methods zscore iqr minmax changepoint]

Examples:
    python detect_highlights.py data.csv highlights.json --column revenue
    python detect_highlights.py data.csv highlights.json --column sales --methods zscore iqr
    python detect_highlights.py data.csv highlights.json --column price --threshold 2.0
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def detect_zscore(values: np.ndarray, threshold: float = 2.5) -> list[dict]:
    """Detect outliers using Z-score method (|z| > threshold)."""
    mean = np.nanmean(values)
    std = np.nanstd(values)
    if std == 0:
        return []

    highlights = []
    for i, v in enumerate(values):
        if np.isnan(v):
            continue
        z = (v - mean) / std
        if abs(z) > threshold:
            severity = "high" if abs(z) > threshold + 1 else "medium"
            direction = "above" if z > 0 else "below"
            highlights.append({
                "index": int(i),
                "value": float(v),
                "reason": f"Z-score outlier ({direction} mean)",
                "method": "zscore",
                "z_score": round(float(z), 2),
                "severity": severity,
                "label": f"z={z:.1f}",
                "suggested_style": "halo_ring" if severity == "high" else "color_shift",
            })
    return highlights


def detect_iqr(values: np.ndarray, multiplier: float = 1.5) -> list[dict]:
    """Detect outliers using IQR (interquartile range) fences."""
    clean = values[~np.isnan(values)]
    if len(clean) < 4:
        return []

    q1 = np.percentile(clean, 25)
    q3 = np.percentile(clean, 75)
    iqr = q3 - q1
    if iqr == 0:
        return []

    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    highlights = []
    for i, v in enumerate(values):
        if np.isnan(v):
            continue
        if v < lower or v > upper:
            direction = "above Q3" if v > upper else "below Q1"
            distance = (v - upper) / iqr if v > upper else (lower - v) / iqr
            severity = "high" if distance > 1.0 else "medium"
            highlights.append({
                "index": int(i),
                "value": float(v),
                "reason": f"IQR outlier ({direction})",
                "method": "iqr",
                "severity": severity,
                "label": f"{v:.1f}",
                "suggested_style": "annotation_arrow",
            })
    return highlights


def detect_minmax(values: np.ndarray) -> list[dict]:
    """Detect global minimum and maximum values."""
    clean = values[~np.isnan(values)]
    if len(clean) == 0:
        return []

    highlights = []
    min_val = np.min(clean)
    max_val = np.max(clean)

    for i, v in enumerate(values):
        if np.isnan(v):
            continue
        if v == max_val:
            highlights.append({
                "index": int(i),
                "value": float(v),
                "reason": "Global maximum",
                "method": "minmax",
                "severity": "low",
                "label": f"Max: {v:.1f}",
                "suggested_style": "annotation_arrow",
            })
            break  # Only first occurrence

    for i, v in enumerate(values):
        if np.isnan(v):
            continue
        if v == min_val:
            highlights.append({
                "index": int(i),
                "value": float(v),
                "reason": "Global minimum",
                "method": "minmax",
                "severity": "low",
                "label": f"Min: {v:.1f}",
                "suggested_style": "annotation_arrow",
            })
            break

    return highlights


def detect_changepoint(values: np.ndarray, window: int = 5, threshold: float = 2.0) -> list[dict]:
    """Detect changepoints using sliding-window mean-shift."""
    n = len(values)
    if n < window * 2 + 1:
        return []

    highlights = []
    for i in range(window, n - window):
        if np.isnan(values[i]):
            continue
        left = values[max(0, i - window):i]
        right = values[i + 1:i + 1 + window]
        left_clean = left[~np.isnan(left)]
        right_clean = right[~np.isnan(right)]

        if len(left_clean) < 2 or len(right_clean) < 2:
            continue

        left_mean = np.mean(left_clean)
        right_mean = np.mean(right_clean)
        pooled_std = np.sqrt(
            (np.var(left_clean) * len(left_clean) + np.var(right_clean) * len(right_clean))
            / (len(left_clean) + len(right_clean))
        )

        if pooled_std == 0:
            continue

        shift = abs(right_mean - left_mean) / pooled_std
        if shift > threshold:
            direction = "increase" if right_mean > left_mean else "decrease"
            highlights.append({
                "index": int(i),
                "value": float(values[i]),
                "reason": f"Changepoint ({direction})",
                "method": "changepoint",
                "shift_magnitude": round(float(shift), 2),
                "severity": "high" if shift > threshold + 1 else "medium",
                "label": f"Shift: {direction}",
                "suggested_style": "band_shade",
            })

    return highlights


def deduplicate(highlights: list[dict]) -> list[dict]:
    """Remove duplicate highlights at the same index, keeping highest severity."""
    severity_order = {"high": 3, "medium": 2, "low": 1}
    seen = {}
    for hl in highlights:
        idx = hl["index"]
        if idx not in seen or severity_order.get(hl["severity"], 0) > severity_order.get(seen[idx]["severity"], 0):
            seen[idx] = hl
    return sorted(seen.values(), key=lambda h: h["index"])


def main():
    parser = argparse.ArgumentParser(
        description="Detect anomalies and notable datapoints for chart highlighting."
    )
    parser.add_argument("data", type=Path, help="Input data file (CSV, JSON)")
    parser.add_argument("output", type=Path, help="Output highlights JSON file")
    parser.add_argument("--column", help="Column to analyze (default: first numeric column)")
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["zscore", "iqr", "minmax", "changepoint"],
        default=["zscore", "iqr", "minmax", "changepoint"],
        help="Detection methods to apply",
    )
    parser.add_argument("--threshold", type=float, default=2.5,
                        help="Z-score threshold (default: 2.5)")
    parser.add_argument("--iqr-multiplier", type=float, default=1.5,
                        help="IQR fence multiplier (default: 1.5)")
    parser.add_argument("--window", type=int, default=5,
                        help="Changepoint sliding window size (default: 5)")

    args = parser.parse_args()

    if not args.data.exists():
        print(f"Error: Data file not found: {args.data}", file=sys.stderr)
        sys.exit(1)

    # Load data
    ext = args.data.suffix.lower()
    if ext == ".json":
        df = pd.read_json(args.data)
    else:
        df = pd.read_csv(args.data)

    # Select column
    if args.column:
        if args.column not in df.columns:
            print(f"Error: Column '{args.column}' not found. Available: {list(df.columns)}", file=sys.stderr)
            sys.exit(1)
        col = args.column
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            print("Error: No numeric columns found in data.", file=sys.stderr)
            sys.exit(1)
        col = numeric_cols[0]
        print(f"Auto-selected column: {col}")

    values = df[col].astype(float).values

    # Run detectors
    all_highlights = []
    methods = {
        "zscore": lambda v: detect_zscore(v, threshold=args.threshold),
        "iqr": lambda v: detect_iqr(v, multiplier=args.iqr_multiplier),
        "minmax": detect_minmax,
        "changepoint": lambda v: detect_changepoint(v, window=args.window),
    }

    for method_name in args.methods:
        detector = methods[method_name]
        results = detector(values)
        all_highlights.extend(results)
        if results:
            print(f"  {method_name}: found {len(results)} highlight(s)")

    # Deduplicate and sort
    highlights = deduplicate(all_highlights)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(highlights, f, indent=2)

    print(f"Wrote {len(highlights)} highlights to {args.output}")


if __name__ == "__main__":
    main()
