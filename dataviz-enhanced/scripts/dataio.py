"""Shared data loading helpers: delimiter sniffing, decimal commas, numeric-string cleanup."""

import csv
import re
import warnings
from pathlib import Path

import pandas as pd

_CURRENCY = re.compile(r"[$€£¥]")
_US_THOUSANDS = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")
_EU_THOUSANDS = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$")
_DECIMAL_COMMA = re.compile(r"^-?\d+,\d+$")
_NUMBER = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")


def read_csv_smart(path: Path, delimiter: str | None = None) -> pd.DataFrame:
    """Read CSV/TSV, detecting , ; tab | delimiters and decimal commas (e.g. '1,5' with ';')."""
    path = Path(path)
    if delimiter is None:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    decimal = "."
    if delimiter != ",":
        text = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
        if re.search(r"\d,\d", text) and not re.search(r"\d\.\d", text):
            decimal = ","
    return pd.read_csv(path, sep=delimiter, decimal=decimal, encoding="utf-8-sig")


def clean_numeric(series: pd.Series) -> pd.Series:
    """Convert text like '1,200', '$3.1', '1.2%', '(45)', '1.234,5' to numbers.

    Returns the converted series when at least 80% of non-empty values are numeric,
    otherwise the original series. Percent signs are dropped (1.2% -> 1.2).
    """
    if pd.api.types.is_numeric_dtype(series):
        return series
    raw = series.dropna().astype(str).str.strip()
    raw = raw[raw != ""]
    if raw.empty:
        return series

    def conv(v: str):
        s = _CURRENCY.sub("", v.replace("−", "-")).replace("%", "").replace(" ", "").replace(" ", "")
        if s.startswith("(") and s.endswith(")"):
            s = "-" + s[1:-1]
        if _US_THOUSANDS.match(s):
            s = s.replace(",", "")
        elif _EU_THOUSANDS.match(s):
            s = s.replace(".", "").replace(",", ".")
        elif _DECIMAL_COMMA.match(s):
            s = s.replace(",", ".")
        return float(s) if _NUMBER.match(s) else None

    converted = series.map(lambda v: conv(str(v).strip()) if pd.notna(v) else None)
    ok = converted.notna().sum()
    if ok >= 0.8 * len(raw):
        out = pd.to_numeric(converted, errors="coerce")
        return out.astype("int64") if out.notna().all() and (out % 1 == 0).all() else out
    return series


def to_datetime_if_dates(series: pd.Series) -> pd.Series:
    """Parse as datetime when more than half of the values look like dates."""
    if pd.api.types.is_numeric_dtype(series):
        return series
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dt = pd.to_datetime(series, errors="coerce")
    return dt if dt.notna().sum() > 0.5 * len(series) else series
