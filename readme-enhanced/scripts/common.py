"""Shared helpers for the readme-enhanced scripts: config, section matching, GitHub anchors."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "default-readme-config.json"


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def style_of(config: dict, name: str) -> dict:
    if name not in config["styles"]:
        raise SystemExit(f"Error: unknown style '{name}'. Choose from: {', '.join(config['styles'])}")
    return config["styles"][name]


def heading_matches(config: dict, key: str, text: str) -> bool:
    """True when heading `text` plausibly is the section `key` (install, usage, license, ...)."""
    aliases = config["sections"].get(key, {}).get("aliases", [])
    t = re.sub(r"[^\w\s]", "", text.lower()).strip()
    return any(re.search(a, t) for a in aliases)


def slugify(text: str) -> str:
    """GitHub-style heading anchor (without the -1 suffixes for duplicates)."""
    t = re.sub(r"<[^>]+>", "", text)                      # html
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)     # links
    t = re.sub(r"[`*_~]", "", t).strip().lower()
    t = "".join(c for c in t if unicodedata.category(c)[0] in "LNM" or c in " -_")
    return re.sub(r"\s", "-", t)


def anchors(headings: list) -> set:
    """Anchor ids for a list of heading texts, including GitHub's -1, -2 suffixes for repeats."""
    seen: dict = {}
    out = set()
    for h in headings:
        base = slugify(h)
        n = seen.get(base, 0)
        out.add(base if n == 0 else f"{base}-{n}")
        seen[base] = n + 1
    return out
