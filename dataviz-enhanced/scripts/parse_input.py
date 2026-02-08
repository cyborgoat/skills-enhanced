#!/usr/bin/env python3
"""Parse structured/semi-structured files into normalized CSV or JSON.

Supports: CSV, TSV, JSON, Excel (.xlsx/.xls), Markdown tables, HTML tables, YAML.
Does NOT handle unstructured prose — that is Claude's job.

Usage:
    python parse_input.py <input_file> <output_file> [--format csv|json] [--sheet NAME]
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml
from bs4 import BeautifulSoup


def detect_format(filepath: Path) -> str:
    """Detect input format from file extension."""
    ext = filepath.suffix.lower()
    fmt_map = {
        ".csv": "csv",
        ".tsv": "tsv",
        ".json": "json",
        ".xlsx": "excel",
        ".xls": "excel",
        ".md": "markdown",
        ".markdown": "markdown",
        ".html": "html",
        ".htm": "html",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    fmt = fmt_map.get(ext)
    if not fmt:
        print(f"Error: Unsupported file extension '{ext}'", file=sys.stderr)
        print(f"Supported: {', '.join(sorted(fmt_map.keys()))}", file=sys.stderr)
        sys.exit(1)
    return fmt


def parse_csv(filepath: Path, delimiter: str = ",") -> pd.DataFrame:
    """Parse CSV or TSV file."""
    return pd.read_csv(filepath, delimiter=delimiter)


def parse_json(filepath: Path) -> pd.DataFrame:
    """Parse JSON file — handles array-of-objects or {columns: [...], data: [...]}."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        if "data" in data and "columns" in data:
            return pd.DataFrame(data["data"], columns=data["columns"])
        if "data" in data and isinstance(data["data"], list):
            return pd.DataFrame(data["data"])
        return pd.DataFrame([data])
    print("Error: JSON structure not recognized as tabular data.", file=sys.stderr)
    sys.exit(1)


def parse_excel(filepath: Path, sheet_name: str | None = None) -> pd.DataFrame:
    """Parse Excel file with optional sheet selection."""
    return pd.read_excel(filepath, sheet_name=sheet_name or 0, engine="openpyxl")


def parse_markdown(filepath: Path) -> pd.DataFrame:
    """Extract the first table from a Markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.strip().split("\n")

    table_lines = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if "|" in stripped and stripped.startswith("|"):
            in_table = True
            table_lines.append(stripped)
        elif in_table:
            break

    if len(table_lines) < 2:
        print("Error: No Markdown table found in file.", file=sys.stderr)
        sys.exit(1)

    def split_row(row: str) -> list[str]:
        cells = row.strip().strip("|").split("|")
        return [c.strip() for c in cells]

    headers = split_row(table_lines[0])

    # Skip separator row (---|----|---)
    data_start = 1
    if re.match(r"^[\s|:\-]+$", table_lines[1]):
        data_start = 2

    rows = [split_row(line) for line in table_lines[data_start:]]
    return pd.DataFrame(rows, columns=headers)


def parse_html(filepath: Path) -> pd.DataFrame:
    """Extract the first <table> from an HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    table = soup.find("table")
    if not table:
        print("Error: No <table> element found in HTML file.", file=sys.stderr)
        sys.exit(1)

    headers = []
    header_row = table.find("thead")
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
    else:
        first_row = table.find("tr")
        if first_row:
            ths = first_row.find_all("th")
            if ths:
                headers = [th.get_text(strip=True) for th in ths]

    rows = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells and cells != headers:
            rows.append(cells)

    if headers:
        return pd.DataFrame(rows, columns=headers)
    return pd.DataFrame(rows)


def parse_yaml(filepath: Path) -> pd.DataFrame:
    """Parse YAML file — expects a list of objects."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict) and "data" in data:
        return pd.DataFrame(data["data"])
    print("Error: YAML structure not recognized as tabular data.", file=sys.stderr)
    sys.exit(1)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a DataFrame: clean column names, auto-detect types, handle missing values."""
    # Clean column names
    df.columns = [
        re.sub(r"[^\w]", "_", str(c).strip()).strip("_").lower() for c in df.columns
    ]

    # Remove fully empty rows and columns
    df = df.dropna(how="all").dropna(axis=1, how="all")

    # Auto-convert types
    for col in df.columns:
        # Try numeric
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() > 0.5 * len(df):
            df[col] = converted
            continue
        # Try datetime
        try:
            dt = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            if dt.notna().sum() > 0.5 * len(df):
                df[col] = dt
                continue
        except Exception:
            pass
        # Keep as string, strip whitespace
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})

    return df.reset_index(drop=True)


def write_output(df: pd.DataFrame, output_path: Path, fmt: str) -> None:
    """Write DataFrame to CSV or JSON."""
    if fmt == "csv":
        df.to_csv(output_path, index=False)
    elif fmt == "json":
        df.to_json(output_path, orient="records", indent=2, date_format="iso")
    else:
        print(f"Error: Unknown output format '{fmt}'", file=sys.stderr)
        sys.exit(1)
    print(f"Wrote {len(df)} rows x {len(df.columns)} cols to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse structured data files into normalized CSV or JSON."
    )
    parser.add_argument("input_file", type=Path, help="Path to input data file")
    parser.add_argument("output_file", type=Path, help="Path to output file")
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default=None,
        help="Output format (default: inferred from output extension)",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        help="Excel sheet name (default: first sheet)",
    )
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Determine output format
    out_fmt = args.format
    if not out_fmt:
        ext = args.output_file.suffix.lower()
        if ext == ".json":
            out_fmt = "json"
        else:
            out_fmt = "csv"

    # Parse input
    input_fmt = detect_format(args.input_file)
    parsers = {
        "csv": lambda p: parse_csv(p, ","),
        "tsv": lambda p: parse_csv(p, "\t"),
        "json": parse_json,
        "excel": lambda p: parse_excel(p, args.sheet),
        "markdown": parse_markdown,
        "html": parse_html,
        "yaml": parse_yaml,
    }

    print(f"Parsing {args.input_file} as {input_fmt}...")
    df = parsers[input_fmt](args.input_file)
    df = normalize(df)
    write_output(df, args.output_file, out_fmt)


if __name__ == "__main__":
    main()
