#!/usr/bin/env python3
"""Chart engine: data file -> publication-quality chart (Altair / Vega-Lite).

Chart types: line, bar, hbar, scatter, histogram, heatmap, box, pie, donut,
             area, bubble, timeseries, small_multiples

Outputs: .png .svg .pdf (no browser needed), .html (interactive) and .json (the Vega-Lite spec).

Usage:
    python generate_chart.py <data> <output> --type TYPE --x COL --y COL [options]
"""

import argparse
import copy
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
from scipy import stats

from dataio import read_csv_smart, to_datetime_if_dates

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "default-viz-config.json"
PX = 96  # CSS pixels per inch; figsize (inches) * 96 = plot size, dpi / 96 = export scale
NEEDS_Y = {"line", "bar", "hbar", "scatter", "bubble", "area", "timeseries", "pie", "donut", "small_multiples", "box"}
DATE_LIKE = re.compile(r"^\d{4}-\d{1,2}(-\d{1,2})?([ T]\d{1,2}:\d{2})?")

alt.data_transformers.disable_max_rows()


def fail(msg: str, code: int = 1):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# Config, themes, palettes
# ---------------------------------------------------------------------------

def deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def load_config(config_path: Path | None = None, theme: str | None = None, preset: str | None = None) -> dict:
    """Default config, then theme, then preset, then a user --config file (each merged over the last)."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for kind, name in (("themes", theme), ("presets", preset)):
        if name:
            if name not in cfg.get(kind, {}):
                fail(f"Unknown {kind[:-1]} '{name}'. Available: {', '.join(cfg.get(kind, {}))}", 2)
            cfg = deep_merge(cfg, cfg[kind][name])
    if config_path:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = deep_merge(cfg, json.load(f))
    return cfg


def get_palette(config: dict, name: str | None = None) -> list[str]:
    palettes = config.get("palettes", {})
    key = name or config.get("default_palette", "colorblind")
    return palettes.get(key, palettes["colorblind"])["colors"]


def vl_config(config: dict, palette: list[str]) -> dict:
    """Translate the skill config (fonts, spines, grid, palette) into a Vega-Lite config."""
    ch = config.get("chart", {})
    fonts, grid, spines = ch.get("fonts", {}), ch.get("grid", {}), ch.get("spines", {})
    tick, axl, title, sub, leg = (fonts.get(k, {}) for k in ("tick_label", "axis_label", "title", "subtitle", "legend"))
    dash = {"dashed": [4, 4], "dotted": [1, 3]}.get(grid.get("style", "dashed"))
    axis = {
        "labelFont": tick.get("family", "Arial"), "labelFontSize": tick.get("size", 9), "labelColor": tick.get("color", "#4d4d4d"),
        "titleFont": axl.get("family", "Arial"), "titleFontSize": axl.get("size", 11), "titleColor": axl.get("color", "#333333"),
        "titleFontWeight": "normal", "titlePadding": 8, "domainColor": spines.get("color", "#333333"),
        "tickColor": spines.get("color", "#333333"), "domainWidth": spines.get("linewidth", 0.8),
        "gridColor": grid.get("color", "#cccccc"), "gridOpacity": max(grid.get("alpha", 0.3), 0.5), "gridWidth": grid.get("linewidth", 0.5),
        "labelPadding": 4, "labelOverlap": "parity",
    }
    if dash:
        axis["gridDash"] = dash
    return {
        "font": axl.get("family", "Arial"),
        "background": ch.get("background", "#ffffff"),
        "view": {"stroke": None},
        "axis": axis,
        "axisX": {"grid": grid.get("show", True) and grid.get("axis", "y") in ("x", "both")},
        "axisY": {"grid": grid.get("show", True) and grid.get("axis", "y") in ("y", "both")},
        "title": {"anchor": "start", "font": title.get("family", "Georgia"), "fontSize": title.get("size", 16),
                  "fontWeight": title.get("weight", "bold"), "color": title.get("color", "#1a1a1a"), "offset": 14,
                  "subtitleFont": sub.get("family", "Georgia"), "subtitleFontSize": sub.get("size", 12),
                  "subtitleColor": sub.get("color", "#4d4d4d"), "subtitlePadding": 6},
        "legend": {"labelFont": leg.get("family", "Arial"), "labelFontSize": leg.get("size", 9), "labelColor": leg.get("color", "#333333"),
                   "titleFont": leg.get("family", "Arial"), "titleFontSize": leg.get("size", 9), "titleColor": leg.get("color", "#333333"),
                   "orient": "top", "direction": "horizontal", "padding": 0, "symbolType": "stroke", "symbolStrokeWidth": 3},
        "range": {"category": palette},
        "text": {"font": tick.get("family", "Arial")},
    }


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def safe_name(s):
    """Vega field names must not contain . [ ] : or quotes."""
    return re.sub(r"[.\[\]\\:'\"]", "_", s) if isinstance(s, str) else s


def load_df(path: Path) -> pd.DataFrame:
    ext = path.suffix.lower()
    if ext == ".json":
        return pd.read_json(path)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, engine="openpyxl")
    return read_csv_smart(path)


def ftype(df: pd.DataFrame, col: str) -> str:
    """'T' temporal, 'Q' quantitative, 'N' nominal."""
    s = df[col]
    if pd.api.types.is_datetime64_any_dtype(s):
        return "T"
    return "Q" if pd.api.types.is_numeric_dtype(s) else "N"


def as_dates(df: pd.DataFrame, col: str) -> None:
    """Turn a text column of ISO-like dates into datetimes (in place)."""
    if not pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]) \
            and df[col].dropna().astype(str).str.match(DATE_LIKE).mean() > 0.8:
        parsed = to_datetime_if_dates(df[col])
        if pd.api.types.is_datetime64_any_dtype(parsed):
            df[col] = parsed


def reduce_data(df: pd.DataFrame, y_col: str | list[str], **kw) -> pd.DataFrame:
    """groupby+agg -> sort -> top/bottom N -> max_categories ("Other")."""
    y_primary = y_col[0] if isinstance(y_col, list) else y_col
    x_col, groupby, agg_func = kw.get("x_col"), kw.get("groupby"), kw.get("agg")
    top_n, bottom_n, max_categories = kw.get("top"), kw.get("bottom"), kw.get("max_categories")
    sort_by, sort_order = kw.get("sort_by"), kw.get("sort_order", "desc")

    if groupby and agg_func and groupby in df.columns:
        numeric = [c for c in df.select_dtypes(include=[np.number]).columns if c != groupby]
        cols = numeric or ([y_primary] if y_primary in df.columns else [])
        df = df.groupby(groupby, as_index=False)[cols].agg(agg_func)
        if x_col and x_col not in df.columns:
            df = df.rename(columns={groupby: x_col})

    sort_col = sort_by or y_primary
    if sort_col in df.columns and (kw.get("sort_by") or top_n or bottom_n or groupby or max_categories):
        df = df.sort_values(sort_col, ascending=sort_order == "asc").reset_index(drop=True)
    if top_n and sort_col in df.columns:
        df = df.nlargest(top_n, sort_col).sort_values(sort_col, ascending=False).reset_index(drop=True)
    elif bottom_n and sort_col in df.columns:
        df = df.nsmallest(bottom_n, sort_col).sort_values(sort_col, ascending=True).reset_index(drop=True)

    if max_categories and x_col in df.columns and len(df) > max_categories:
        top_df, rest = df.head(max_categories), df.iloc[max_categories:]
        other = {c: (rest[c].sum() if pd.api.types.is_numeric_dtype(df[c]) else "Other") for c in df.columns}
        other[x_col] = "Other"
        df = pd.concat([top_df, pd.DataFrame([other])], ignore_index=True)
    return df


def apply_order(df: pd.DataFrame, x_col: str, order: list[str]) -> pd.DataFrame:
    """Reorder rows so the categories in x_col follow `order` (others last, original order kept)."""
    rank = df[x_col].astype(str).map({v: i for i, v in enumerate(order)}).fillna(len(order))
    return df.assign(_o=rank).sort_values("_o", kind="stable").drop(columns="_o").reset_index(drop=True)


def group_small_slices(df: pd.DataFrame, x_col: str, y_col: str, max_slices: int = 10) -> pd.DataFrame:
    df = df.sort_values(y_col, ascending=False).reset_index(drop=True)
    if len(df) <= max_slices:
        return df
    other = pd.DataFrame([{x_col: "Other", y_col: df.iloc[max_slices - 1:][y_col].sum()}])
    return pd.concat([df.head(max_slices - 1), other], ignore_index=True)


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------

@dataclass
class Ctx:
    x: str
    ys: list
    config: dict
    palette: list
    W: int
    H: int
    kw: dict = field(default_factory=dict)

    @property
    def ct(self) -> dict:
        return self.config.get("chart_types", {})

    @property
    def y(self) -> str:
        return self.ys[0]

    @property
    def fonts(self) -> dict:
        return self.config.get("chart", {}).get("fonts", {})

    @property
    def ink(self) -> str:
        """Dark text colour for labels (not the title colour, which themes may set to an accent)."""
        return self.fonts.get("annotation", {}).get("color", "#333333")


def x_axis(labels, horizontal_title) -> alt.Axis:
    """Category axis: tilt long or numerous labels instead of truncating them."""
    n = len(labels)
    longest = max((len(str(v)) for v in labels), default=0)
    angle = -90 if n > 30 else -45 if (n > 10 or longest > 10) else 0
    return alt.Axis(labelAngle=angle, labelLimit=240, title=horizontal_title, grid=False, ticks=False)


def num_axis(values, **kw) -> alt.Axis:
    """Numeric axis: whole numbers (years, counts) get integer ticks and no thousands separator."""
    v = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if len(v) and (v % 1 == 0).all():
        return alt.Axis(format="d", tickMinStep=1, tickCount=8, **kw)
    return alt.Axis(format="~g", tickCount=8, **kw)


def date_axis(series: pd.Series, title) -> alt.Axis:
    span = (series.max() - series.min()).days if len(series.dropna()) else 0
    fmt = "%Y" if span > 365 * 4 else "%b %Y" if span > 60 else None
    return alt.Axis(grid=False, title=title, format=fmt, tickCount=8 if fmt else alt.Undefined, labelAngle=0)


def x_enc(df: pd.DataFrame, c: Ctx, title, force_t: bool = False, zero: bool = False):
    t = "T" if force_t else ftype(df, c.x)
    if t == "T":
        return alt.X(field=c.x, type="temporal", title=title, axis=date_axis(pd.to_datetime(df[c.x]), title))
    if t == "Q":
        return alt.X(field=c.x, type="quantitative", title=title, scale=alt.Scale(zero=zero, nice=True), axis=num_axis(df[c.x], grid=False, title=title))
    return alt.X(field=c.x, type="nominal", sort=None, axis=x_axis(df[c.x].tolist(), title))


def y_enc(field_name, title, zero: bool = True, domain=None, **kw):
    scale = alt.Scale(domain=domain, nice=False) if domain else (alt.Scale(zero=True, nice=True) if zero else alt.Scale(zero=False, nice=True, padding=12))
    return alt.Y(field=field_name, type="quantitative", title=title, scale=scale, axis=alt.Axis(tickCount=6, title=title), **kw)


def padded_domain(values):
    """Y domain with headroom for value labels; extra room below zero when bars go negative."""
    v = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    lo, hi = float(min(v.min(), 0)), float(max(v.max(), 0))
    pad = (hi - lo) * 0.1 or 1
    return [lo - pad if lo < 0 else 0, hi + pad if hi > 0 else 0]


def series_color(names, palette, show_legend=True, symbol="stroke"):
    return alt.Color("series:N", scale=alt.Scale(domain=list(names), range=[palette[i % len(palette)] for i in range(len(names))]),
                     legend=alt.Legend(title=None, symbolType=symbol, symbolSize=140 if symbol != "stroke" else 100) if show_legend else None)


def long_form(df, c: Ctx) -> pd.DataFrame:
    return df.melt(id_vars=[c.x], value_vars=c.ys, var_name="series", value_name="value")


def labels(c: Ctx):
    k = c.kw
    xl = k.get("xlabel") if k.get("xlabel") is not None else c.x
    yl = k.get("ylabel") if k.get("ylabel") is not None else (c.y if len(c.ys) == 1 else None)
    return (xl or None), (yl or None)


# ---------------------------------------------------------------------------
# Highlights and trend lines (layers)
# ---------------------------------------------------------------------------

def highlight_layers(df: pd.DataFrame, c: Ctx, chart_type: str, highlights: list[dict], force_t: bool = False) -> list:
    hl_cfg = c.config.get("highlights", {})
    horizontal = chart_type == "hbar"
    t = "T" if force_t else ftype(df, c.x)
    cats = df[c.x].tolist()
    y_all = df[c.ys].select_dtypes(include=[np.number])
    y_lo, y_hi = float(y_all.min().min()), float(y_all.max().max())
    y_mid = float(np.nanmedian(df[c.y]))
    rows = []
    for h in highlights:
        i = h.get("index")
        if i is None or not (0 <= i < len(df)):
            continue
        styles = hl_cfg.get("combo", {}).get("styles", ["color_shift", "annotation_arrow"]) if h.get("suggested_style") == "combo" else [h.get("suggested_style", "annotation_arrow")]
        xv = df[c.x].iloc[i]
        yv = float(df[c.y].iloc[i])
        for s in styles:
            rows.append({"x": xv, "y": yv, "label": h.get("label") or f"{yv:g}", "style": s, "above": yv >= y_mid})
    if not rows:
        return []
    hd = pd.DataFrame(rows)
    if t == "T":
        hd["x"] = pd.to_datetime(hd["x"])
    ex, ey = ("y", "x") if horizontal else ("x", "y")
    xtype = "quantitative" if horizontal else {"T": "temporal", "Q": "quantitative", "N": "nominal"}[t]
    ytype = "nominal" if horizontal else "quantitative"
    if horizontal:
        enc_x = alt.X("y:Q")
        enc_y = alt.Y("x:N", scale=alt.Scale(domain=cats))
    else:
        enc_x = alt.X("x:T") if t == "T" else alt.X("x:Q") if t == "Q" else alt.X("x:N", scale=alt.Scale(domain=cats))
        enc_y = alt.Y("y:Q")

    def style_cfg(s):
        return hl_cfg.get(s, {})

    def pts(sub, **mark):
        return alt.Chart(sub).mark_point(**mark).encode(x=enc_x, y=enc_y)

    layers = []
    for s, sub in hd.groupby("style", sort=False):
        sc = style_cfg(s)
        color = sc.get("color", "#D55E00")
        if s == "halo_ring":
            layers.append(pts(sub, filled=False, size=sc.get("size_multiplier", 3.0) * 140, stroke=color, strokeWidth=sc.get("linewidth", 2.0), opacity=0.7))
        elif s == "color_shift":
            layers.append(pts(sub, filled=True, size=120, color=color, opacity=1, stroke="#ffffff", strokeWidth=1.2))
        elif s == "size_boost":
            layers.append(pts(sub, filled=True, size=sc.get("size_multiplier", 2.5) * 70, color=color, opacity=0.85))
        elif s == "glow":
            layers.append(pts(sub, filled=True, size=sc.get("size_multiplier", 5.0) * 100, color=color, opacity=sc.get("alpha", 0.3)))
        elif s == "marker_change":
            layers.append(pts(sub, filled=True, shape="diamond", size=sc.get("size_multiplier", 1.8) * 90, color=hl_cfg.get("color_shift", {}).get("color", color)))
        elif s == "annotation_arrow":
            fs = sc.get("fontsize", c.fonts.get("annotation", {}).get("size", 9))
            bars = chart_type in ("bar", "hbar")
            if not bars:
                layers.append(pts(sub, filled=True, size=70, color=sc.get("color", c.ink), opacity=1))
            for above, grp in sub.groupby("above"):
                layers.append(alt.Chart(grp).mark_text(dy=(-30 if bars and not horizontal else -16 if horizontal else -14) if above else 18, dx=(40 if horizontal else 0), fontSize=fs, fontWeight="bold", color=sc.get("color", c.ink))
                              .encode(x=enc_x, y=enc_y, text="label:N"))
        elif s == "band_shade":
            band = sub.copy()
            lo = min(0.0, y_lo) if chart_type in ("bar", "hbar") else y_lo - 0.02 * (y_hi - y_lo)  # bar bands span from the baseline
            band["lo"], band["hi"] = lo, y_hi + 0.02 * (y_hi - y_lo)
            opacity = max(sc.get("alpha", 0.1), 0.18)
            if horizontal:
                layers.append(alt.Chart(band).mark_bar(color=color, opacity=opacity).encode(y=alt.Y("x:N", scale=alt.Scale(domain=cats)), x=alt.X("lo:Q"), x2="hi:Q"))
            elif t == "N":
                layers.append(alt.Chart(band).mark_bar(color=color, opacity=opacity).encode(x=alt.X("x:N", scale=alt.Scale(domain=cats)), y=alt.Y("lo:Q"), y2="hi:Q"))
            else:
                xs = pd.to_datetime(df[c.x]) if t == "T" else df[c.x].astype(float)
                step = xs.diff().abs().median()
                half = step * 0.4 if t == "T" else float(step) * 0.4
                band["x0"], band["x1"] = band["x"] - half, band["x"] + half
                bt = "temporal" if t == "T" else "quantitative"
                layers.append(alt.Chart(band).mark_rect(color=color, opacity=opacity).encode(x=alt.X("x0", type=bt), x2="x1", y=alt.Y("lo:Q"), y2="hi:Q"))
    return layers


def trend_layers(df: pd.DataFrame, c: Ctx, force_t: bool = False) -> list:
    method = c.kw.get("trend")
    if not method:
        return []
    st = c.config.get("statistics", {})
    tcfg, acfg, bcfg = st.get("trend_line", {}), st.get("annotation", {}), st.get("confidence_band", {})
    is_t = force_t or ftype(df, c.x) == "T"
    xs = pd.to_datetime(df[c.x]) if is_t else pd.to_numeric(df[c.x], errors="coerce")
    x0 = xs.min()
    x_num = ((xs - x0).dt.total_seconds() / 86400).to_numpy() if is_t else xs.to_numpy(dtype=float)
    y_num = pd.to_numeric(df[c.y], errors="coerce").to_numpy(dtype=float)
    m = np.isfinite(x_num) & np.isfinite(y_num)
    x_c, y_c = x_num[m], y_num[m]
    if len(x_c) < 3:
        print("Warning: not enough numeric points for a trend line", file=sys.stderr)
        return []
    grid = np.linspace(x_c.min(), x_c.max(), 120)
    margin = None
    if method == "linear":
        slope, icpt, r, p, _ = stats.linregress(x_c, y_c)
        yl = slope * grid + icpt
        label = f"R²={r ** 2:.3f}, p={p:.2e}"
        n = len(x_c)
        if n > 2 and bcfg.get("alpha", 0.15) > 0:
            se = np.sqrt(np.sum((y_c - (slope * x_c + icpt)) ** 2) / (n - 2))
            margin = stats.t.ppf(0.975, n - 2) * se * np.sqrt(1 / n + (grid - x_c.mean()) ** 2 / np.sum((x_c - x_c.mean()) ** 2))
    else:
        deg = c.kw.get("degree", 2)
        poly = np.poly1d(np.polyfit(x_c, y_c, deg))
        yl = poly(grid)
        ss_tot = np.sum((y_c - y_c.mean()) ** 2)
        r2 = 1 - np.sum((y_c - poly(x_c)) ** 2) / ss_tot if ss_tot else 0
        label = f"R²={r2:.3f} (poly deg={deg})"
    gx = x0 + pd.to_timedelta(grid, unit="D") if is_t else grid
    td = pd.DataFrame({"x": gx, "y": yl})
    xt = "temporal" if is_t else "quantitative"
    color = tcfg.get("color", "#999999")
    layers = []
    if margin is not None:
        band = pd.DataFrame({"x": gx, "lo": yl - margin, "hi": yl + margin})
        layers.append(alt.Chart(band).mark_area(color=bcfg.get("color") or color, opacity=bcfg.get("alpha", 0.15))
                      .encode(x=alt.X("x", type=xt), y=alt.Y("lo:Q"), y2="hi:Q"))
    layers.append(alt.Chart(td).mark_line(color=color, strokeDash=[5, 4], strokeWidth=tcfg.get("linewidth", 1.0) + 0.5, opacity=0.9)
                  .encode(x=alt.X("x", type=xt), y=alt.Y("y:Q")))
    ann = pd.DataFrame({"x": [gx[-1]], "y": [float(np.nanmin(y_c))], "t": [label]})
    layers.append(alt.Chart(ann).mark_text(align="right", baseline="bottom", dx=-4, dy=-4, fontSize=acfg.get("fontsize", 9), color=acfg.get("color", "#666666"))
                  .encode(x=alt.X("x", type=xt), y=alt.Y("y:Q"), text="t:N"))
    return layers


def finish(layers: list, df, c: Ctx, chart_type: str, force_t: bool = False) -> alt.LayerChart:
    """Add trend and highlight layers on top of the base marks."""
    layers = list(layers) + trend_layers(df, c, force_t)
    hp = c.kw.get("highlights")
    if hp:
        with open(hp, "r", encoding="utf-8") as f:
            hl = highlight_layers(df, c, chart_type, json.load(f), force_t)
        is_band = [getattr(l.mark, "type", "") in ("bar", "rect") for l in hl]
        layers = [l for l, b in zip(hl, is_band) if b] + layers + [l for l, b in zip(hl, is_band) if not b]  # bands sit behind the data
    return alt.layer(*layers) if len(layers) > 1 else layers[0]


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def build_line(df, c: Ctx, force_t: bool = False):
    ct = c.ct.get("timeseries" if force_t else "line", {})
    as_dates(df, c.x) if force_t or ftype(df, c.x) == "N" else None
    if force_t:
        df[c.x] = pd.to_datetime(df[c.x], errors="coerce")
    xl, yl = labels(c)
    point = alt.OverlayMarkDef(size=ct.get("markersize", 4) ** 2 * 1.6, filled=True, **({} if len(c.ys) > 1 else {"color": c.palette[0]})) if (len(df) <= 50 and not force_t) else False
    mark = dict(strokeWidth=ct.get("linewidth", 2.0), point=point, interpolate="linear")
    if len(c.ys) > 1:
        base = alt.Chart(long_form(df, c)).mark_line(**mark).encode(
            x=x_enc(df, c, xl, force_t), y=y_enc("value", yl, zero=False), color=series_color(c.ys, c.palette))
    else:
        base = alt.Chart(df).mark_line(color=c.palette[0], **mark).encode(x=x_enc(df, c, xl, force_t), y=y_enc(c.y, yl, zero=False))
    return finish([base], df, c, "line", force_t)


def build_timeseries(df, c: Ctx):
    return build_line(df, c, force_t=True)


def value_labels(df, c: Ctx, xfield, yfield, horizontal=False, long=None):
    cats = df[xfield].tolist()
    """Value labels at bar ends; two layers so negatives sit below / left of the bar."""
    fs = c.fonts.get("annotation", {}).get("size", 9)
    src = long if long is not None else df
    out = []
    for neg in (False, True):
        sub = src[src[yfield] < 0] if neg else src[src[yfield] >= 0]
        if sub.empty:
            continue
        mk = alt.Chart(sub).mark_text(fontSize=fs + 1, fontWeight="bold", color=c.ink,
                                      **({"align": "right" if neg else "left", "dx": -6 if neg else 6} if horizontal else {"baseline": "top" if neg else "bottom", "dy": 6 if neg else -4}))
        if horizontal:
            out.append(mk.encode(y=alt.Y(field=xfield, type="nominal", scale=alt.Scale(domain=cats)), x=alt.X(field=yfield, type="quantitative"), text=alt.Text(field=yfield, type="quantitative", format=",.4~g")))
        else:
            out.append(mk.encode(x=alt.X(field=xfield, type="nominal", scale=alt.Scale(domain=cats)), y=alt.Y(field=yfield, type="quantitative"), text=alt.Text(field=yfield, type="quantitative", format=",.4~g")))
    return out


def build_bar(df, c: Ctx):
    ct = c.ct.get("bar", {})
    xl, yl = labels(c)
    n = len(df)
    if n > 40:
        print(f"Warning: {n} categories on one bar chart; use --top N, --max-categories N or --type hbar for a readable result.", file=sys.stderr)
    if len(c.ys) > 1:
        lf = long_form(df, c)
        bars = alt.Chart(lf).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
            x=alt.X(field=c.x, type="nominal", sort=None, axis=x_axis(df[c.x].tolist(), xl)),
            xOffset=alt.XOffset(field="series", type="nominal"), y=y_enc("value", yl, domain=padded_domain(lf["value"])), color=series_color(c.ys, c.palette, symbol="square"))
        return alt.layer(bars)
    bars = alt.Chart(df).mark_bar(color=c.palette[0], cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        x=alt.X(field=c.x, type="nominal", scale=alt.Scale(domain=df[c.x].tolist()), axis=x_axis(df[c.x].tolist(), xl)), y=y_enc(c.y, yl, domain=padded_domain(df[c.y])))
    layers = [bars] + (value_labels(df, c, c.x, c.y) if n <= 20 else [])
    return finish(layers, df, c, "bar")


def build_hbar(df, c: Ctx):
    xl, yl = labels(c)
    n = len(df)
    c.H = max(c.H, n * 26 + 50)
    bars = alt.Chart(df).mark_bar(color=c.palette[0], cornerRadiusTopRight=3, cornerRadiusBottomRight=3, height={"band": 0.72}).encode(
        y=alt.Y(field=c.x, type="nominal", scale=alt.Scale(domain=df[c.x].tolist()), title=None, axis=alt.Axis(ticks=False, domain=False, labelLimit=320, grid=False)),
        x=alt.X(field=c.y, type="quantitative", title=yl, scale=alt.Scale(domain=padded_domain(df[c.y]), nice=False), axis=alt.Axis(grid=True, tickCount=6, title=yl)))
    layers = [bars] + (value_labels(df, c, c.x, c.y, horizontal=True) if n <= 30 else [])
    return finish(layers, df, c, "hbar")


def group_scale(df, col, palette):
    cats = list(pd.unique(df[col]))
    return alt.Scale(domain=[str(v) for v in cats], range=[palette[i % len(palette)] for i in range(len(cats))])


def build_scatter(df, c: Ctx, bubble: bool = False):
    ct = c.ct.get("bubble" if bubble else "scatter", {})
    xl, yl = labels(c)
    n = len(df)
    opacity = ct.get("alpha", 0.6 if bubble else 0.7)
    if n > 500:
        opacity = min(opacity, 0.4)
    enc = dict(x=x_enc(df, c, xl), y=y_enc(c.y, yl, zero=False))
    if bubble:
        size_col = c.kw.get("size")
        rng = ct.get("size_range", [20, 500])
        enc["size"] = alt.Size(field=size_col, type="quantitative", scale=alt.Scale(range=rng), legend=alt.Legend(title=size_col, orient="right", direction="vertical", symbolType="circle", symbolFillColor="#cccccc")) if size_col else alt.value(90)
    color_col = c.kw.get("color")
    mark = dict(filled=True, opacity=opacity, stroke="#ffffff", strokeWidth=ct.get("edgewidth", 0.5))
    if not bubble:
        mark["size"] = ct.get("size", 40) * (0.6 if n > 500 else 0.8 if n > 200 else 1.0) * 1.3
    if color_col and color_col in df.columns:
        d2 = df.assign(**{color_col: df[color_col].astype(str)})
        enc["color"] = alt.Color(field=color_col, type="nominal", scale=group_scale(d2, color_col, c.palette), legend=alt.Legend(title=None, symbolType="circle"))
        base = alt.Chart(d2).mark_point(**mark).encode(**enc)
    else:
        base = alt.Chart(df).mark_point(color=c.palette[0], **mark).encode(**enc)
    return finish([base], df, c, "scatter")


def build_bubble(df, c: Ctx):
    return build_scatter(df, c, bubble=True)


def build_histogram(df, c: Ctx):
    ct = c.ct.get("histogram", {})
    col = c.ys[0] if c.ys and c.ys[0] else c.x
    xl = c.kw.get("xlabel") if c.kw.get("xlabel") is not None else col
    bins = c.kw.get("bins") or ct.get("bins", 30)
    return alt.Chart(df[[col]].dropna()).mark_bar(color=c.palette[0], opacity=ct.get("alpha", 0.9), binSpacing=1).encode(
        x=alt.X(field=col, type="quantitative", bin=alt.Bin(maxbins=bins), title=xl),
        y=alt.Y("count()", title=c.kw.get("ylabel") or "Count"))


def build_heatmap(df, c: Ctx):
    ct = c.ct.get("heatmap", {})
    if c.x and c.ys and c.ys[0]:
        pv = df.pivot_table(index=c.ys[0], columns=c.x, aggfunc="mean", sort=False)
        if pv.columns.nlevels > 1:
            pv.columns = pv.columns.droplevel(0)
        corr = False
        xt_name, yt_name = c.x, c.ys[0]
    else:
        num = df.select_dtypes(include=[np.number])
        pv = num.corr() if num.shape[1] > 1 else num
        corr = True
        xt_name, yt_name = "column", "row"
    long = pv.reset_index().melt(id_vars=pv.index.name or "index", var_name=xt_name if not corr else "column", value_name="value")
    row_name = pv.index.name or "index"
    if corr:
        long = long.rename(columns={row_name: "row"})
        row_name = "row"
    cols_order = [str(v) for v in pv.columns]
    rows_order = [str(v) for v in pv.index]
    long[row_name] = long[row_name].astype(str)
    long[xt_name if not corr else "column"] = long[xt_name if not corr else "column"].astype(str)
    xf = xt_name if not corr else "column"
    colors = ct.get("corr_colors", ["#2166AC", "#F7F7F7", "#B2182B"]) if corr else ct.get("colors", ["#FFFFCC", "#FD8D3C", "#800026"])
    scale = alt.Scale(range=colors, domain=[-1, 0, 1]) if corr else alt.Scale(range=colors)
    if not corr:
        lo, hi = float(long["value"].min()), float(long["value"].max())
        scale = alt.Scale(range=colors, domain=list(np.linspace(lo, hi, len(colors))))
    fmt = ".2f" if corr else ct.get("fmt", ".1f")
    cell_w = max(40, min(110, int(c.W / max(len(cols_order), 1))))
    rect = alt.Chart(long).mark_rect(stroke="#ffffff", strokeWidth=ct.get("linewidths", 0.5) * 2).encode(
        x=alt.X(field=xf, type="nominal", sort=cols_order, title=None if corr else c.kw.get("xlabel") or c.x, axis=alt.Axis(labelAngle=0, ticks=False, domain=False, grid=False)),
        y=alt.Y(field=row_name, type="nominal", sort=rows_order, title=None if corr else c.kw.get("ylabel") or row_name, axis=alt.Axis(ticks=False, domain=False, grid=False)),
        color=alt.Color("value:Q", scale=scale, legend=alt.Legend(title=None, orient="right", direction="vertical", gradientLength=140)))
    mid = (long["value"].min() + long["value"].max()) / 2 if not corr else 0.5
    text = alt.Chart(long).mark_text(fontSize=c.fonts.get("tick_label", {}).get("size", 9) + 1).encode(
        x=alt.X(field=xf, type="nominal", sort=cols_order), y=alt.Y(field=row_name, type="nominal", sort=rows_order),
        text=alt.Text("value:Q", format=fmt),
        color=alt.condition((alt.datum.value > mid) if not corr else (abs(alt.datum.value) > 0.6), alt.value("#ffffff"), alt.value(c.ink)))
    return alt.layer(rect, text)


def build_box(df, c: Ctx):
    ct = c.ct.get("box", {})
    xl, yl = labels(c)
    if len(c.ys) == 1 and c.x and c.x in df.columns:
        d2 = df[[c.x, c.y]].dropna().copy()
        d2[c.x] = d2[c.x].astype(str)
        order = [str(v) for v in c.kw["order"]] if c.kw.get("order") else sorted(d2[c.x].unique(), key=lambda v: (not v.replace(".", "", 1).isdigit(), float(v) if v.replace(".", "", 1).isdigit() else 0, v))
        enc = dict(x=alt.X(field=c.x, type="nominal", sort=order, title=xl, axis=alt.Axis(labelAngle=0, ticks=False, grid=False)), y=y_enc(c.y, yl, zero=False))
        color = alt.Color(field=c.x, type="nominal", scale=alt.Scale(domain=order, range=[c.palette[i % len(c.palette)] for i in range(len(order))]), legend=None)
        data = d2
    else:
        data = df[c.ys].melt(var_name="series", value_name="value").dropna()
        enc = dict(x=alt.X("series:N", sort=c.ys, title=None, axis=alt.Axis(labelAngle=0, ticks=False)), y=y_enc("value", yl, zero=False))
        color = alt.Color("series:N", scale=alt.Scale(domain=c.ys, range=c.palette[:len(c.ys)]), legend=None)
    return alt.Chart(data).mark_boxplot(extent=1.5, size=ct.get("width", 0.6) * 110, opacity=0.85, median={"color": c.ink, "strokeWidth": 2},
                                        rule={"color": c.ink}, ticks={"size": 16, "color": c.ink}, outliers={"size": 25, "color": c.ink}).encode(color=color, **enc)


def build_pie(df, c: Ctx, donut: bool = False):
    ct = c.ct.get("donut" if donut else "pie", {})
    d = group_small_slices(df[[c.x, c.y]].dropna(), c.x, c.y, c.kw.get("max_categories") or 10)
    d[c.x] = d[c.x].astype(str)
    d["pct"] = d[c.y] / d[c.y].sum()
    d["label"] = d["pct"].map(lambda v: f"{v:.1%}")
    order = d[c.x].tolist()
    R = int(min(c.W, c.H) / 2) - 8
    d["big"] = d["pct"] >= (0.04 if R >= 150 else 0.08)  # label only slices that can hold the text
    r_in = int(R * (1 - ct.get("wedgeprops_width", 0.4) / 0.5 * 0.5)) if donut else 0
    enc_theta = alt.Theta(field=c.y, type="quantitative", stack=True)
    color = alt.Color(field=c.x, type="nominal", sort=order, scale=alt.Scale(domain=order, range=[c.palette[i % len(c.palette)] for i in range(len(order))]),
                      legend=alt.Legend(title=None, orient="right", direction="vertical", symbolType="square"))
    arcs = alt.Chart(d).mark_arc(outerRadius=R, innerRadius=r_in, stroke="#ffffff", strokeWidth=1.5).encode(theta=enc_theta, color=color, order=alt.Order(f"{c.y}:Q", sort="descending"))
    text = alt.Chart(d[d["big"]]).mark_text(radius=(R + r_in) / 2 if donut else R * 0.7, fontSize=c.fonts.get("annotation", {}).get("size", 9) + 2, fontWeight="bold", color="#ffffff").encode(
        theta=enc_theta, text="label:N", order=alt.Order(f"{c.y}:Q", sort="descending"))
    return alt.layer(arcs, text).properties(width=2 * R, height=2 * R)


def build_donut(df, c: Ctx):
    return build_pie(df, c, donut=True)


def build_area(df, c: Ctx):
    ct = c.ct.get("area", {})
    as_dates(df, c.x) if ftype(df, c.x) == "N" else None
    xl, yl = labels(c)
    xe = x_enc(df, c, xl)
    stacked = c.kw.get("stacked") and len(c.ys) > 1
    if len(c.ys) == 1:
        base = alt.Chart(df).mark_area(color=c.palette[0], opacity=0.35, line={"color": c.palette[0], "strokeWidth": ct.get("linewidth", 1.5) + 0.5}).encode(x=xe, y=y_enc(c.y, yl))
        return finish([base], df, c, "area")
    lf = long_form(df, c)
    area = alt.Chart(lf).mark_area(opacity=0.9 if stacked else 0.4, line=not stacked).encode(
        x=xe, y=alt.Y("value:Q", stack="zero" if stacked else None, title=yl, scale=alt.Scale(zero=True)), color=series_color(c.ys, c.palette, symbol="square"),
        order=alt.Order("series:N", sort="ascending") if stacked else alt.value(0))
    return area


def build_small_multiples(df, c: Ctx, nominal_cols: list = None):
    ct = c.ct.get("small_multiples", {})
    g = c.kw.get("group") or c.kw.get("color")
    if not g or g not in df.columns:
        fail("small_multiples requires --group COL", 2)
    as_dates(df, c.x)
    d = df[[c.x, g, c.y]].dropna()
    d = d.groupby([g, c.x], as_index=False, sort=False)[c.y].mean() if d.duplicated([g, c.x]).any() else d
    d[g] = d[g].astype(str)
    n = d[g].nunique()
    cols = min(n, ct.get("max_cols", 4))
    sw, sh = ct.get("subplot_size", [3, 2.5])
    sw, sh = int(sw * PX * 0.8), int(sh * PX * 0.7)
    t = ftype(d, c.x)
    axis = num_axis(d[c.x], grid=False, labelAngle=0, title=None) if t == "Q" else alt.Axis(grid=False, labelAngle=0, title=None, tickCount=4)
    xe = alt.X(field=c.x, type={"T": "temporal", "Q": "quantitative", "N": "ordinal"}[t], title=None, axis=axis)
    line = alt.Chart(d).mark_line(color=c.palette[0], strokeWidth=2).encode(x=xe, y=y_enc(c.y, None, zero=False))
    fonts = c.fonts.get("title", {})
    return line.properties(width=sw, height=sh).facet(
        facet=alt.Facet(field=g, type="nominal", sort=list(pd.unique(d[g])), title=None, header=alt.Header(labelFont=fonts.get("family", "Georgia"), labelFontSize=11, labelFontWeight="bold", labelAnchor="start", labelColor=c.ink)),
        columns=cols)


BUILDERS = {
    "line": build_line, "bar": build_bar, "hbar": build_hbar, "scatter": build_scatter, "histogram": build_histogram,
    "heatmap": build_heatmap, "box": build_box, "pie": build_pie, "donut": build_donut, "area": build_area,
    "bubble": build_bubble, "timeseries": build_timeseries, "small_multiples": build_small_multiples,
}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def generate(data_path: Path, output_path: Path, chart_type: str, x_col: str, y_col: str | None, config: dict, **kw) -> None:
    df = load_df(data_path)
    original_rows = len(df)
    df.columns = [safe_name(str(c)) for c in df.columns]
    x_col = safe_name(x_col)
    for k in ("color", "size", "group", "groupby", "sort_by"):
        kw[k] = safe_name(kw.get(k))
    if chart_type in NEEDS_Y and not y_col:
        fail(f"--y is required for --type {chart_type}", 2)
    ys = [safe_name(s.strip()) for s in y_col.split(",")] if y_col else []

    for name in [x_col] + ys + [kw.get(k) for k in ("color", "size", "group")]:
        if name and name not in df.columns and not (kw.get("groupby") and kw["groupby"] in df.columns):
            fail(f"Column '{name}' not found. Available: {list(df.columns)}")

    if any(kw.get(k) for k in ("agg", "groupby", "top", "bottom", "max_categories", "sort_by")):
        df = reduce_data(df, ys or y_col, x_col=x_col, **{k: v for k, v in kw.items() if k != "x_col"})
        if len(df) < original_rows:
            print(f"Data reduced: {original_rows} → {len(df)} rows", file=sys.stderr)
    order = [s.strip() for s in kw["order"].split(",")] if kw.get("order") else None
    if order and x_col in df.columns:
        df = apply_order(df, x_col, order)
    kw["order"] = order

    chart_cfg = config.get("chart", {})
    fw, fh = kw.get("figsize") or chart_cfg.get("figsize", [10, 6])
    dpi = kw.get("dpi") or chart_cfg.get("dpi", 150)
    W, H = int(fw * PX) - 40, int(fh * PX) - (96 if (kw.get("title") or kw.get("subtitle")) else 40)
    n = len(df)
    if not kw.get("figsize") and chart_type in ("bar", "line", "area", "timeseries") and n > 15:
        W = max(W, int(n * 26))
    palette = get_palette(config, kw.get("palette"))
    c = Ctx(x=x_col, ys=ys, config=config, palette=palette, W=W, H=H, kw=kw)

    chart = BUILDERS[chart_type](df, c)
    props = {}
    if chart_type not in ("pie", "donut", "small_multiples"):
        props.update(width=c.W, height=c.H)
    if kw.get("title") or kw.get("subtitle"):
        props["title"] = alt.TitleParams(text=kw.get("title") or "", subtitle=[kw["subtitle"]] if kw.get("subtitle") else [])
    chart = chart.properties(**props).configure(**vl_config(config, palette))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = output_path.suffix.lstrip(".").lower()
    if fmt in ("png", ""):
        chart.save(str(output_path), format="png", scale_factor=dpi / PX)
    elif fmt in ("svg", "pdf", "html", "json"):
        chart.save(str(output_path), format=fmt)
    else:
        fail(f"Unsupported output format '.{fmt}' (use png, svg, pdf, html or json)", 2)
    print(f"Chart saved to {output_path} ({chart_type}, {len(df)} data points)")


def main():
    p = argparse.ArgumentParser(description="Generate publication-quality charts from structured data.")
    p.add_argument("data", type=Path, help="Input data file (CSV, JSON, Excel)")
    p.add_argument("output", type=Path, help="Output file (.png .svg .pdf .html .json)")
    p.add_argument("--type", required=True, dest="chart_type", choices=list(BUILDERS), help="Chart type")
    p.add_argument("--x", required=True, dest="x_col", help="X-axis column name")
    p.add_argument("--y", dest="y_col", help="Y-axis column(s), comma-separated for multi-series")
    p.add_argument("--title"), p.add_argument("--subtitle")
    p.add_argument("--xlabel"), p.add_argument("--ylabel")
    p.add_argument("--palette", help="Palette name from the config (colorblind, categorical, monochrome, editorial, ...)")
    p.add_argument("--theme", help="Look: tufte (default) or editorial (matches pptx-enhanced decks)")
    p.add_argument("--preset", help="Size preset: report (default) or slide (16:9-friendly, larger text)")
    p.add_argument("--color", help="Column for color grouping (scatter, bubble)")
    p.add_argument("--size", help="Column for size encoding (bubble)")
    p.add_argument("--group", help="Column for faceting (small_multiples)")
    p.add_argument("--order", help="Comma-separated category order for the x column (bar, line, box, heatmap)")
    p.add_argument("--trend", choices=["linear", "polynomial"], help="Add trend line with R²")
    p.add_argument("--degree", type=int, default=2, help="Polynomial degree for the trend line")
    p.add_argument("--highlights", type=Path, help="Highlights JSON from detect_highlights.py")
    p.add_argument("--stacked", action="store_true", help="Stacked area")
    p.add_argument("--bins", type=int, help="Histogram bins")
    p.add_argument("--figsize", nargs=2, type=float, metavar=("W", "H"), help="Figure size in inches")
    p.add_argument("--dpi", type=int, help="PNG resolution")
    p.add_argument("--config", type=Path, help="Custom config JSON merged over the defaults")
    g = p.add_argument_group("data reduction", "Filter, aggregate and limit data before plotting")
    g.add_argument("--top", type=int, metavar="N", help="Keep the top N rows by y")
    g.add_argument("--bottom", type=int, metavar="N", help="Keep the bottom N rows by y")
    g.add_argument("--agg", choices=["mean", "sum", "median", "count", "min", "max"], help="Aggregation (with --groupby)")
    g.add_argument("--groupby", metavar="COL", help="Group by this column before aggregating")
    g.add_argument("--sort-by", dest="sort_by", metavar="COL", help="Sort column (default: y)")
    g.add_argument("--sort-order", dest="sort_order", choices=["asc", "desc"], default="desc")
    g.add_argument("--max-categories", dest="max_categories", type=int, metavar="N", help="Keep N categories, group the rest as 'Other'")
    a = p.parse_args()

    config = load_config(a.config, a.theme, a.preset)
    generate(a.data, a.output, a.chart_type, a.x_col, a.y_col, config,
             title=a.title, subtitle=a.subtitle, xlabel=a.xlabel, ylabel=a.ylabel, palette=a.palette, color=a.color, size=a.size,
             group=a.group, order=a.order, trend=a.trend, degree=a.degree, highlights=a.highlights, stacked=a.stacked, bins=a.bins,
             figsize=a.figsize, dpi=a.dpi, top=a.top, bottom=a.bottom, agg=a.agg, groupby=a.groupby, sort_by=a.sort_by,
             sort_order=a.sort_order, max_categories=a.max_categories)


if __name__ == "__main__":
    main()
