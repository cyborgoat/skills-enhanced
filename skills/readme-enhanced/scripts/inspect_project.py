#!/usr/bin/env python3
"""Collect verified facts about a project, for writing and checking its README.

Reads files only (and `git` metadata); never runs project code and never uses the network.
Every command and fact records the file it came from.

Usage:
    python inspect_project.py <project-dir> <facts.json> [--repo owner/name]
"""
from __future__ import annotations

import argparse
import configparser
import json
import os
import re
import subprocess
import sys
from pathlib import Path

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".tox", "dist", "build", "target", ".idea",
               ".vscode", ".next", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".gradle", "vendor", ".DS_Store"}
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".toml", ".yaml", ".yml", ".md", ".txt", ".cfg", ".ini", ".sh", ".rs", ".go",
            ".java", ".rb", ".php", ".html", ".css", ".mjs", ".cjs", ".lock", ".xml", ".gradle", ".mk", ""}
LANG = {".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".jsx": "JavaScript", ".rs": "Rust", ".go": "Go", ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby", ".php": "PHP", ".c": "C",
        ".h": "C", ".cpp": "C++", ".cs": "C#", ".swift": "Swift", ".sh": "Shell", ".lua": "Lua", ".r": "R", ".jl": "Julia"}
MANIFESTS = ["pyproject.toml", "setup.cfg", "setup.py", "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
             "build.gradle.kts", "composer.json", "SKILL.md"]
SERVER_DEPS = {"express", "fastify", "koa", "hapi", "nestjs", "@nestjs/core", "next", "nuxt", "flask", "fastapi", "django", "starlette",
               "aiohttp", "tornado", "sanic", "rails", "sinatra", "actix-web", "axum", "rocket", "gin", "echo", "fiber", "spring-boot"}
ML_DEPS = {"torch", "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "transformers", "jax", "xgboost", "lightgbm", "numpy",
           "pandas", "huggingface-hub", "datasets"}
FRAMEWORK_WORDS = ("framework", "toolkit", "sdk")


# ----------------------------------------------------------------------------- helpers

def git(root: Path, *args: str):
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def read(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def list_files(root: Path, cap: int = 6000) -> list:
    """Project-relative file paths; git-aware (tracked + untracked, ignoring .gitignore)."""
    out = git(root, "ls-files", "-co", "--exclude-standard")
    if out:
        files = [f for f in out.splitlines() if not set(Path(f).parts) & IGNORE_DIRS]
        return sorted(files)[:cap]
    files = []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in IGNORE_DIRS)
        files += [str(Path(dp, f).relative_to(root)) for f in sorted(fns) if f != ".DS_Store"]
        if len(files) >= cap:
            break
    return files[:cap]


def mini_toml(text: str) -> dict:
    """Small TOML reader for the keys we need (used when tomllib is unavailable, i.e. Python < 3.11)."""
    data: dict = {}
    cur = data
    key_buf = None
    buf = ""

    def parse_val(v: str):
        v = v.strip()
        if v[:1] in "\"'" and v[-1:] == v[:1]:
            return v[1:-1]
        if v in ("true", "false"):
            return v == "true"
        if v.startswith("["):
            return [x.strip().strip("\"'") for x in re.findall(r"\"[^\"]*\"|'[^']*'", v)] or v
        try:
            return float(v) if "." in v else int(v)
        except ValueError:
            return v

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip() if not re.search(r"[\"'].*#.*[\"']", raw) else raw.rstrip()
        if key_buf:
            buf += " " + line.strip()
            if buf.count("[") <= buf.count("]"):
                cur[key_buf] = parse_val(buf)
                key_buf = None
            continue
        m = re.match(r"^\s*\[\[?([^\]]+)\]\]?\s*$", line)
        if m:
            cur = data
            for part in m.group(1).split("."):
                cur = cur.setdefault(part.strip().strip("\"'"), {})
            continue
        m = re.match(r"^\s*([A-Za-z0-9_.\"'-]+)\s*=\s*(.*)$", line)
        if m:
            k, v = m.group(1).strip("\"'"), m.group(2).strip()
            if v.startswith("[") and v.count("[") > v.count("]"):
                key_buf, buf = k, v
            else:
                cur[k] = parse_val(v)
    return data


def load_toml(path: Path) -> dict:
    text = read(path)
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(text)
    except ImportError:
        return mini_toml(text)
    except Exception:
        return mini_toml(text)


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            kv = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
            if kv:
                out[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return out


LICENSES = [
    ("MIT", ["permission is hereby granted, free of charge"]),
    ("Apache-2.0", ["apache license", "version 2.0"]),
    ("AGPL-3.0", ["gnu affero general public license"]),
    ("LGPL-3.0", ["gnu lesser general public license"]),
    ("GPL-3.0", ["gnu general public license", "version 3"]),
    ("GPL-2.0", ["gnu general public license", "version 2"]),
    ("MPL-2.0", ["mozilla public license"]),
    ("BSD-3-Clause", ["redistribution and use in source and binary forms", "neither the name"]),
    ("BSD-2-Clause", ["redistribution and use in source and binary forms"]),
    ("ISC", ["permission to use, copy, modify, and/or distribute this software"]),
    ("Unlicense", ["this is free and unencumbered software"]),
]


def detect_license(root: Path, files: list) -> dict:
    base, inherited = root, False
    name = next((f for f in files if re.match(r"^(LICEN[CS]E|COPYING)(\.\w+)?$", Path(f).name, re.I) and "/" not in f), None)
    if not name:  # a sub-project inherits the licence of the repository that contains it
        top = git(root, "rev-parse", "--show-toplevel")
        if top and Path(top).resolve() != root:
            base = Path(top)
            name = next((f.name for f in base.iterdir() if re.match(r"^(LICEN[CS]E|COPYING)(\.\w+)?$", f.name, re.I)), None)
            inherited = bool(name)
    if not name:
        return {"file": None, "spdx": None, "holder": None}
    text = read(base / name, 40_000)
    low = text.lower()
    spdx = next((s for s, keys in LICENSES if all(k in low for k in keys)), None)
    m = re.search(r"copyright\s*(?:\(c\)|©)?\s*(\d{4}(?:\s*[-,]\s*\d{4})?)\s+(.+)", text, re.I)
    return {"file": name, "spdx": spdx, "holder": m.group(2).strip() if m else None, "year": m.group(1) if m else None,
            "inherited_from_repo_root": inherited}


# ----------------------------------------------------------------------------- ecosystems

def cmd(c: str, kind: str, source: str) -> dict:
    return {"cmd": c, "kind": kind, "source": source}


def inspect_python(root: Path, files: list, facts: dict):
    py = root / "pyproject.toml"
    reqs = [f for f in files if re.match(r"^requirements[\w.-]*\.txt$", f)]
    has_setup = (root / "setup.py").exists() or (root / "setup.cfg").exists()
    if not (py.exists() or reqs or has_setup):
        return None
    eco = {"ecosystem": "python", "deps": [], "scripts": {}}
    proj = {}
    if py.exists():
        d = load_toml(py)
        proj = d.get("project", {}) or {}
        poetry = d.get("tool", {}).get("poetry", {}) if isinstance(d.get("tool"), dict) else {}
        meta = proj or poetry
        facts.update({k: v for k, v in {"name": meta.get("name"), "description": meta.get("description"), "version": meta.get("version")}.items() if v})
        lic = meta.get("license")
        if isinstance(lic, dict):
            lic = lic.get("text") or lic.get("file")
        if lic and isinstance(lic, str):
            facts["license_declared"] = lic
        rp = proj.get("requires-python") or (poetry.get("dependencies", {}) or {}).get("python")
        if rp:
            facts.setdefault("runtime", {})["python"] = str(rp)
        deps = proj.get("dependencies") or []
        if isinstance(deps, list):
            eco["deps"] = [re.split(r"[<>=!~\[; ]", x.strip(), 1)[0] for x in deps if isinstance(x, str)]
        elif isinstance(poetry.get("dependencies"), dict):
            eco["deps"] = [k for k in poetry["dependencies"] if k != "python"]
        scripts = proj.get("scripts") or poetry.get("scripts") or {}
        eco["scripts"] = scripts if isinstance(scripts, dict) else {}
        if (root / "uv.lock").exists():
            facts["commands"].append(cmd("uv sync", "install", "uv.lock"))
        elif poetry:
            facts["commands"].append(cmd("poetry install", "install", "pyproject.toml [tool.poetry]"))
        else:
            facts["commands"].append(cmd("pip install .", "install", "pyproject.toml"))
            facts["commands"].append(cmd('pip install -e ".[dev]"', "setup-dev", "pyproject.toml [project.optional-dependencies]")) if "dev" in (proj.get("optional-dependencies") or {}) else None
    if has_setup and (root / "setup.cfg").exists():
        cp = configparser.ConfigParser()
        cp.read(root / "setup.cfg")
        if cp.has_section("metadata"):
            for k_src, k in (("name", "name"), ("description", "description"), ("version", "version")):
                if cp.get("metadata", k_src, fallback=None):
                    facts.setdefault(k, cp.get("metadata", k_src))
        if cp.has_option("options.entry_points", "console_scripts"):
            for line in cp.get("options.entry_points", "console_scripts").splitlines():
                if "=" in line:
                    eco["scripts"][line.split("=")[0].strip()] = line.split("=")[1].strip()
    if reqs:
        for r in reqs:
            eco["deps"] += [re.split(r"[<>=!~\[; ]", ln.strip(), 1)[0] for ln in read(root / r).splitlines() if ln.strip() and not ln.startswith(("#", "-"))]
        if not facts["commands"] or not any(c["kind"] == "install" for c in facts["commands"]):
            facts["commands"].append(cmd(f"pip install -r {reqs[0]}", "install", reqs[0]))
    elif has_setup and not py.exists():
        facts["commands"].append(cmd("pip install .", "install", "setup.py"))
    for name in eco["scripts"]:
        facts["commands"].append(cmd(f"{name} --help", "run", "pyproject.toml [project.scripts]"))
    if any(f.startswith("tests/") or f.startswith("test/") or re.search(r"(^|/)test_.*\.py$", f) for f in files):
        runner = "pytest" if "pytest" in " ".join(eco["deps"]) or (root / "pytest.ini").exists() or "[tool.pytest" in read(py) else "python -m pytest"
        facts["commands"].append(cmd("tox" if (root / "tox.ini").exists() else runner, "test", "tests/"))
    eco["deps"] = sorted({d.lower() for d in eco["deps"] if d})
    return eco


def inspect_node(root: Path, files: list, facts: dict):
    pj = root / "package.json"
    if not pj.exists():
        return None
    try:
        d = json.loads(read(pj))
    except ValueError:
        return None
    for k in ("name", "description", "version"):
        if d.get(k):
            facts[k] = d[k]
    if d.get("license"):
        facts["license_declared"] = d["license"] if isinstance(d["license"], str) else str(d["license"])
    eng = (d.get("engines") or {}).get("node")
    if eng:
        facts.setdefault("runtime", {})["node"] = eng
    pm = "pnpm" if (root / "pnpm-lock.yaml").exists() else "yarn" if (root / "yarn.lock").exists() else "bun" if (root / "bun.lockb").exists() else "npm"
    run = {"npm": "npm run", "pnpm": "pnpm", "yarn": "yarn", "bun": "bun run"}[pm]
    facts["commands"].append(cmd(f"{pm} install", "install", "package.json"))
    scripts = d.get("scripts") or {}
    for name, body in scripts.items():
        kind = "install" if name.startswith(("install", "setup", "bootstrap")) else "test" if name.startswith("test") else "build" if name.startswith("build") else "lint" if name.startswith(("lint", "format")) else "dev" if name in ("dev", "start", "serve", "watch") else "other"
        c = f"{pm} test" if name == "test" and pm == "npm" else f"{pm} start" if name == "start" and pm == "npm" else f"{run} {name}"
        facts["commands"].append(cmd(c, kind, f"package.json scripts.{name}"))
    bins = d.get("bin")
    bin_names = list(bins) if isinstance(bins, dict) else ([d.get("name")] if bins else [])
    deps = sorted({*(d.get("dependencies") or {}), *(d.get("devDependencies") or {})})
    ws = d.get("workspaces")
    if isinstance(ws, dict):
        ws = ws.get("packages")
    return {"ecosystem": "node", "deps": [x.lower() for x in deps], "scripts": scripts, "bin": bin_names, "workspaces": ws or [], "package_manager": pm}


def inspect_rust(root: Path, files: list, facts: dict):
    ct = root / "Cargo.toml"
    if not ct.exists():
        return None
    d = load_toml(ct)
    pkg = d.get("package", {}) or {}
    for k in ("name", "description", "version"):
        if isinstance(pkg.get(k), str):
            facts[k] = pkg[k]
    if isinstance(pkg.get("license"), str):
        facts["license_declared"] = pkg["license"]
    facts["commands"] += [cmd("cargo build --release", "build", "Cargo.toml"), cmd("cargo test", "test", "Cargo.toml"), cmd("cargo run", "run", "Cargo.toml")]
    has_bin = (root / "src" / "main.rs").exists() or "bin" in d
    return {"ecosystem": "rust", "deps": sorted((d.get("dependencies") or {}).keys()), "bin": [pkg.get("name")] if has_bin else []}


def inspect_go(root: Path, files: list, facts: dict):
    gm = root / "go.mod"
    if not gm.exists():
        return None
    text = read(gm)
    m = re.search(r"^module\s+(\S+)", text, re.M)
    if m:
        facts.setdefault("name", m.group(1).rsplit("/", 1)[-1])
        facts["go_module"] = m.group(1)
    v = re.search(r"^go\s+(\S+)", text, re.M)
    if v:
        facts.setdefault("runtime", {})["go"] = v.group(1)
    facts["commands"] += [cmd("go build ./...", "build", "go.mod"), cmd("go test ./...", "test", "go.mod"), cmd("go run .", "run", "go.mod")]
    return {"ecosystem": "go", "deps": re.findall(r"^\s+(\S+)\s+v", text, re.M), "bin": [facts.get("name")] if any(f == "main.go" for f in files) else []}


def inspect_makefile(root: Path, files: list, facts: dict):
    mk = next((f for f in files if f in ("Makefile", "makefile", "GNUmakefile")), None)
    if not mk:
        return
    targets = [t for t in re.findall(r"^([A-Za-z][\w-]*)\s*:(?!=)", read(root / mk), re.M) if t not in ("PHONY",)]
    facts["make_targets"] = targets
    for t in targets:
        kind = "test" if t.startswith("test") else "build" if t in ("build", "all") else "lint" if t.startswith(("lint", "fmt", "format")) else "install" if t == "install" else "other"
        facts["commands"].append(cmd(f"make {t}", kind, f"{mk}:{t}"))


# ----------------------------------------------------------------------------- repo context

def repo_identity(root: Path, override: str | None) -> dict:
    ident = {"owner": None, "name": None, "url": None, "default_branch": None, "latest_tag": None}
    if override:
        ident["owner"], ident["name"] = override.split("/", 1)
        ident["url"] = f"https://github.com/{override}"
    else:
        remote = git(root, "remote", "get-url", "origin")
        m = re.search(r"(github\.com|gitlab\.com|bitbucket\.org)[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?$", remote or "")
        if m:
            ident.update({"host": m.group(1), "owner": m.group(2), "name": m.group(3), "url": f"https://{m.group(1)}/{m.group(2)}/{m.group(3)}"})
    head = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    ident["default_branch"] = head.split("/", 1)[-1] if head else (git(root, "rev-parse", "--abbrev-ref", "HEAD") or None)
    ident["latest_tag"] = git(root, "describe", "--tags", "--abbrev=0")
    ident["subdir"] = (git(root, "rev-parse", "--show-prefix") or "").strip("/")  # path of this project inside its repo
    return ident


def ci_workflows(root: Path, files: list) -> list:
    out = []
    for f in files:
        if re.match(r"^\.github/workflows/[^/]+\.ya?ml$", f):
            m = re.search(r"^name:\s*(.+)$", read(root / f, 4000), re.M)
            out.append({"file": f, "name": (m.group(1).strip().strip("\"'") if m else Path(f).stem), "provider": "github-actions"})
    for f, prov in ((".gitlab-ci.yml", "gitlab-ci"), (".travis.yml", "travis"), ("azure-pipelines.yml", "azure")):
        if f in files:
            out.append({"file": f, "name": prov, "provider": prov})
    return out


def languages(files: list) -> list:
    counts: dict = {}
    for f in files:
        lang = LANG.get(Path(f).suffix.lower())
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    total = sum(counts.values()) or 1
    return [{"language": k, "files": v, "share": round(v / total, 2)} for k, v in sorted(counts.items(), key=lambda x: -x[1])[:5]]


def file_tree(files: list, depth_limit: int = 30) -> list:
    tops: dict = {}
    for f in files:
        parts = Path(f).parts
        if len(parts) == 1:
            tops.setdefault(parts[0], set())
        else:
            tops.setdefault(parts[0] + "/", set()).add(parts[1] + ("/" if len(parts) > 2 else ""))
    entries = sorted(tops.items(), key=lambda kv: (not kv[0].endswith("/"), kv[0].lower()))[:depth_limit]
    return [{"path": k, "children": sorted(v)[:12]} for k, v in entries]


def existing_readme(root: Path, files: list) -> dict:
    name = next((f for f in files if re.match(r"^readme(\.\w+)?$", f, re.I)), None)
    if not name:
        return {"exists": False}
    text = read(root / name)
    heads, fence = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            heads.append({"level": len(m.group(1)), "text": m.group(2), "line": i})
    return {"exists": True, "file": name, "lines": text.count("\n") + 1, "headings": heads,
            "badges": len(re.findall(r"!\[[^\]]*\]\(https?://[^)]*(shields\.io|badge\.svg|badgen|badge\.fury)[^)]*\)", text))}


def find_packages(root: Path, files: list) -> list:
    """Sub-projects (a manifest in a subdirectory, depth <= 2)."""
    pk = []
    seen = set()
    for f in files:
        p = Path(f)
        if len(p.parts) in (2, 3) and p.name in MANIFESTS and p.parts[0] not in IGNORE_DIRS:
            d = str(p.parent)
            if d in seen or d.startswith(("tests", "test", "examples", "docs", "fixtures")):
                continue
            seen.add(d)
            info = {"path": d, "manifest": p.name, "name": p.parts[-2], "description": None}
            if p.name == "SKILL.md":
                fm = frontmatter(read(root / f, 4000))
                info.update({"name": fm.get("name", info["name"]), "description": fm.get("description"), "type": "claude-skill"})
            elif p.name == "package.json":
                try:
                    j = json.loads(read(root / f))
                    info.update({"name": j.get("name", info["name"]), "description": j.get("description")})
                except ValueError:
                    pass
            elif p.name in ("pyproject.toml", "Cargo.toml"):
                t = load_toml(root / f)
                meta = t.get("project") or t.get("package") or {}
                info.update({"name": meta.get("name", info["name"]), "description": meta.get("description")})
            pk.append(info)
    # prefer SKILL.md when a directory has several manifests
    best = {}
    for x in pk:
        if x["path"] not in best or x["manifest"] == "SKILL.md":
            best[x["path"]] = x
    return sorted(best.values(), key=lambda x: x["path"])


def guess_type(facts: dict, eco: list, root: Path, files: list) -> str:
    if (root / "SKILL.md").exists():
        return "claude-skill"
    deps = {d for e in eco for d in e.get("deps", [])}
    packages = facts.get("packages", [])
    ws = any(e.get("workspaces") for e in eco)
    if ws or len(packages) >= 2 or "cargo workspace" in read(root / "Cargo.toml", 4000).lower() and "[workspace]" in read(root / "Cargo.toml", 4000):
        return "monorepo"
    if any(e.get("bin") or e.get("scripts") and e["ecosystem"] == "python" for e in eco):
        return "cli"
    if deps & SERVER_DEPS or "Dockerfile" in files and (deps & SERVER_DEPS):
        return "web-app" if any(f.endswith((".html", ".tsx", ".jsx", ".vue")) for f in files) else "service"
    if deps & ML_DEPS and len(deps & ML_DEPS) >= 2:
        return "data-ml"
    if any(w in (facts.get("description") or "").lower() for w in FRAMEWORK_WORDS):
        return "framework"
    if any(f.startswith(("docs/", "mkdocs")) for f in files) and not eco:
        return "docs"
    return "library"


def summary_of(text: str, suffix: str):
    """First line of the module docstring (Python) or of the opening header comment (JS, shell)."""
    text = re.sub(r"^#!.*\n", "", text).lstrip()
    if suffix == ".py":
        try:
            import ast
            doc = ast.get_docstring(ast.parse(text))
            return doc.strip().splitlines()[0].strip().rstrip(".") if doc else None
        except (SyntaxError, ValueError):  # file may use newer syntax than this Python: fall back to a regex
            m = re.match(r'^\s*[rRuU]?(?:"""|\'\'\')\s*(.+)', text)
            return m.group(1).strip().rstrip(".") if m and len(m.group(1)) >= 8 else None
    lines = []
    if text.startswith("/*"):
        for ln in text[2:].splitlines():
            ln = re.sub(r"^\s*\*+/?\s?", "", ln).strip()
            if ln.endswith("*/"):
                break
            if ln:
                lines.append(ln)
                break
    else:
        for ln in text.splitlines():
            m = re.match(r"^\s*(?:#|//)\s?(.*)$", ln)
            if not m:
                break
            if m.group(1).strip():
                lines.append(m.group(1).strip())
                break
    if not lines:
        return None
    first = re.sub(r"^[\w.-]+\s+-\s+", "", lines[0])  # "name - description" -> "description"
    return first.rstrip(".") if len(first) >= 8 else None


def script_files(root: Path, files: list) -> list:
    """Runnable files in scripts/ or bin/ with a one-line summary taken from their header."""
    out = []
    for f in files:
        p = Path(f)
        if len(p.parts) == 2 and p.parts[0] in ("scripts", "bin") and p.suffix in (".py", ".js", ".mjs", ".sh", ".ts"):
            out.append({"path": f, "summary": summary_of(read(root / f, 6000), p.suffix)})
    return out


def example_commands(files: list) -> list:
    out = []
    for f in files:
        if re.match(r"^examples?/(build|run|demo|main)\.(py|js|mjs|sh)$", f):
            runner = {"py": "python", "js": "node", "mjs": "node", "sh": "bash"}[f.rsplit(".", 1)[1]]
            out.append(cmd(f"{runner} {f}", "example", f))
    return out


def env_vars(root: Path, files: list) -> list:
    f = next((x for x in files if Path(x).name in (".env.example", ".env.sample", ".env.template")), None)
    if not f:
        return []
    out = []
    for line in read(root / f).splitlines():
        m = re.match(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*)$", line)
        if m:
            out.append({"name": m.group(1), "example": m.group(2).strip()[:40], "source": f})
    return out


CONFIG_SKIP = re.compile(r"(tsconfig|jsconfig|package|pyproject|eslint|prettier|babel|jest|vite|webpack|rollup|tailwind|postcss|renovate|dependabot)", re.I)


def config_files(files: list) -> list:
    return [f for f in files if "/" not in f and re.search(r"config", f, re.I) and f.endswith((".json", ".yaml", ".yml", ".toml", ".ini")) and not CONFIG_SKIP.search(f)]


def inspect(root: Path, repo_override: str | None = None) -> dict:
    root = root.resolve()
    files = list_files(root)
    facts: dict = {"root": str(root), "commands": [], "runtime": {}, "generated_by": "inspect_project.py"}
    eco = [e for e in (inspect_python(root, files, facts), inspect_node(root, files, facts), inspect_rust(root, files, facts), inspect_go(root, files, facts)) if e]
    inspect_makefile(root, files, facts)
    skill = root / "SKILL.md"
    if skill.exists():
        fm = frontmatter(read(skill, 6000))
        if fm.get("name"):
            facts["name"] = fm["name"]  # the skill name wins over a package.json name
        facts["skill"] = fm
        if fm.get("description") and not facts.get("description"):
            facts["description"] = fm["description"]
    facts.setdefault("name", root.name)
    facts["ecosystems"] = eco
    facts["repo"] = repo_identity(root, repo_override)
    facts["license"] = detect_license(root, files)
    facts["ci"] = ci_workflows(root, files)
    facts["languages"] = languages(files)
    facts["tree"] = file_tree(files)
    facts["env_vars"] = env_vars(root, files)
    facts["config_files"] = config_files(files)
    facts["script_files"] = script_files(root, files)
    facts["commands"] += example_commands(files)
    facts["packages"] = find_packages(root, files)
    facts["readme"] = existing_readme(root, files)
    names = {f.lower() for f in (Path(x).name for x in files)}
    facts["companion"] = {k: any(n.startswith(k.lower()) for n in names) for k in ("license", "contributing", "code_of_conduct", "security", "changelog")}
    top = git(root, "rev-parse", "--show-toplevel")
    if top and Path(top).resolve() != root:  # files in the enclosing repo count for a sub-project
        outer = {n.lower() for n in os.listdir(top)}
        for k in ("license", "contributing", "code_of_conduct", "security", "changelog"):
            facts["companion"][k] = facts["companion"][k] or any(n.startswith(k) for n in outer)
    facts["companion"]["issue_templates"] = any(f.startswith(".github/ISSUE_TEMPLATE") for f in files)
    facts["has"] = {"tests": any(re.match(r"^(tests?|spec|__tests__)/", f) for f in files), "docs": any(f.startswith("docs/") for f in files),
                    "examples": any(f.startswith(("examples/", "example/")) for f in files), "docker": any(Path(f).name in ("Dockerfile", "docker-compose.yml", "compose.yaml") for f in files)}
    facts["project_type"] = guess_type(facts, eco, root, files)
    facts["file_count"] = len(files)
    # keep one entry per command string
    seen, uniq = set(), []
    for c in facts["commands"]:
        if c["cmd"] not in seen:
            seen.add(c["cmd"])
            uniq.append(c)
    facts["commands"] = uniq
    return facts


def main():
    p = argparse.ArgumentParser(description="Collect verified facts about a project for README work.")
    p.add_argument("project", type=Path, help="Project directory")
    p.add_argument("output", type=Path, help="Where to write facts.json")
    p.add_argument("--repo", help="owner/name, when the git remote is missing or wrong")
    a = p.parse_args()
    if not a.project.is_dir():
        print(f"Error: not a directory: {a.project}", file=sys.stderr)
        sys.exit(2)
    facts = inspect(a.project, a.repo)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(facts, indent=2, ensure_ascii=False), encoding="utf-8")
    eco = ", ".join(e["ecosystem"] for e in facts["ecosystems"]) or "none detected"
    print(f"{facts['name']}: type={facts['project_type']}, ecosystems={eco}, {len(facts['commands'])} commands, "
          f"license={facts['license']['spdx'] or facts['license_declared'] if 'license_declared' in facts else facts['license']['spdx']}")
    print(f"Wrote {a.output}")


if __name__ == "__main__":
    main()
