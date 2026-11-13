#!/usr/bin/env python3
"""Lint a README against the project it describes.

Checks structure, links and images, code fences, leftover placeholders, whether the commands shown
exist in the project, badges, licence and companion-file consistency, and claims that no longer match
the repository. Exit code 1 when there are errors (2 for usage errors).

Usage:
    python lint_readme.py README.md [--project DIR] [--style minimal|standard|comprehensive]
                          [--facts facts.json] [--repo owner/name] [--json] [--strict] [--check-links]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from common import anchors, heading_matches, load_config, style_of
from inspect_project import TEXT_EXT, inspect, list_files, read

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+#.-]*)")
LINK = re.compile(r"(!?)\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REFDEF = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)")
IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
SHELL_LANGS = {"", "bash", "sh", "shell", "console", "zsh", "terminal", "shell-session"}
BADGE_HOST = re.compile(r"(img\.shields\.io|badge\.svg|badgen\.net|badge\.fury\.io|codecov\.io/.*graph/badge|badges\.gitter)", re.I)
SPDX_WORDS = [("MIT", r"\bMIT\b"), ("Apache-2.0", r"\bApache[- ]?(License)?[- ]?2(\.0)?\b"), ("GPL-3.0", r"\bGPL[- ]?v?3\b"), ("GPL-2.0", r"\bGPL[- ]?v?2\b"),
              ("LGPL-3.0", r"\bLGPL\b"), ("AGPL-3.0", r"\bAGPL\b"), ("BSD-3-Clause", r"\bBSD[- ]?3\b"), ("BSD-2-Clause", r"\bBSD[- ]?2\b"),
              ("MPL-2.0", r"\bMPL\b"), ("ISC", r"\bISC\b"), ("Unlicense", r"\bUnlicense\b")]
YARN_BUILTIN = {"install", "i", "add", "remove", "dlx", "exec", "init", "create", "update", "upgrade", "link", "global", "why", "ci", "audit", "outdated", "cache", "config", "workspaces", "run"}


class Finding:
    def __init__(self, line: int, severity: str, rule: str, message: str):
        self.line, self.severity, self.rule, self.message = line, severity, rule, message

    def as_dict(self) -> dict:
        return {"line": self.line, "severity": self.severity, "rule": self.rule, "message": self.message}


# ----------------------------------------------------------------------------- parsing

def parse(text: str) -> dict:
    """Split a README into headings, fenced blocks, links, images, inline code, with line numbers."""
    lines = text.splitlines()
    doc = {"lines": lines, "headings": [], "fences": [], "links": [], "images": [], "inline": [], "prose": [], "html_ids": set(), "unclosed": []}
    fence = None
    in_comment = False
    prev_text, prev_no = "", 0  # last prose line, for setext headings ("Title" over "=====")
    for i, raw in enumerate(lines, 1):
        m = FENCE.match(raw)
        if fence:
            if m and m.group(2)[0] == fence["ch"] and len(m.group(2)) >= fence["len"] and not raw.strip().strip(fence["ch"]):
                fence["end"] = i
                doc["fences"].append(fence)
                fence = None
            else:
                fence["body"].append((i, raw))
            continue
        if m:
            fence = {"start": i, "ch": m.group(2)[0], "len": len(m.group(2)), "lang": m.group(3).lower(), "body": []}
            continue
        line = raw
        if in_comment:
            if "-->" in line:
                in_comment = False
                line = line.split("-->", 1)[1]
            else:
                continue
        line = re.sub(r"<!--.*?-->", " ", line)
        if "<!--" in line:
            in_comment = True
            line = line.split("<!--", 1)[0]
        for hid in re.findall(r"""(?:id|name)=["']([^"']+)["']""", line):
            doc["html_ids"].add(hid)
        under = re.match(r"^\s{0,3}(=+|-{3,})\s*$", line)
        if under and prev_text.strip() and not re.match(r"^\s*(#|[-*>|]|\d+\.|<)", prev_text) and prev_no == i - 1:
            doc["headings"].append({"level": 1 if under.group(1)[0] == "=" else 2, "text": prev_text.strip(), "line": prev_no, "setext": True})
            prev_text, prev_no = "", 0
            doc["prose"].append((i, ""))
            continue
        hm = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        h1html = re.match(r"^\s*<h([1-6])[^>]*>(.*?)</h\1>", line, re.I)
        if hm:
            doc["headings"].append({"level": len(hm.group(1)), "text": hm.group(2), "line": i})
        elif h1html:
            doc["headings"].append({"level": int(h1html.group(1)), "text": re.sub(r"<[^>]+>", "", h1html.group(2)), "line": i, "html": True})
        # inline code first, then blank it out so links inside code are ignored
        for cm in re.finditer(r"(?<!`)`([^`\n]+)`(?!`)", line):
            doc["inline"].append((i, cm.group(1)))
        stripped = re.sub(r"(?<!`)`[^`\n]+`(?!`)", lambda mm: " " * len(mm.group(0)), line)
        for lm in LINK.finditer(stripped):
            (doc["images"] if lm.group(1) else doc["links"]).append({"line": i, "text": lm.group(2), "url": lm.group(3)})
        for tag in IMG_TAG.findall(stripped):
            src = re.search(r"""src=["']([^"']+)["']""", tag)
            alt = re.search(r"""alt=["']([^"']*)["']""", tag)
            if src:
                doc["images"].append({"line": i, "text": alt.group(1) if alt else "", "url": src.group(1), "html": True})
        rd = REFDEF.match(line)
        if rd:
            doc["links"].append({"line": i, "text": rd.group(1), "url": rd.group(2)})
        doc["prose"].append((i, stripped))
        prev_text, prev_no = (stripped if stripped.strip() else ""), i
    if fence:
        doc["unclosed"].append(fence["start"])
    return doc


# ----------------------------------------------------------------------------- checks

class Linter:
    def __init__(self, readme: Path, project: Path, style: str, facts: dict, config: dict, check_links: bool):
        self.readme, self.project, self.config, self.facts = readme, project, config, facts
        self.style_name, self.st = style, style_of(config, style)
        self.lc = config["lint"]
        self.text = readme.read_text(encoding="utf-8", errors="replace")
        self.doc = parse(self.text)
        self.out: list = []
        self.check_links = check_links
        self.files = None

    def add(self, line: int, sev: str, rule: str, msg: str):
        self.out.append(Finding(line, sev, rule, msg))

    # -- structure -------------------------------------------------------------
    def structure(self):
        d, st = self.doc, self.st
        h1 = [h for h in d["headings"] if h["level"] == 1]
        if not h1:
            self.add(1, "error", "title", "no H1 title")
        elif len(h1) > 1:
            self.add(h1[1]["line"], "warn", "title", f"{len(h1)} H1 headings; use one")
        prev = 0
        for h in d["headings"]:
            if prev and h["level"] > prev + 1:
                self.add(h["line"], "warn", "heading-level", f"heading jumps from H{prev} to H{h['level']}: '{h['text']}'")
            prev = h["level"]
        seen = {}
        for h in d["headings"]:
            k = (h["level"], h["text"].lower())
            if k in seen:
                self.add(h["line"], "warn", "heading-duplicate", f"duplicate heading '{h['text']}' (also line {seen[k]})")
            seen.setdefault(k, h["line"])
        # one-line description near the top
        desc = self.description()
        if desc is None:
            self.add(h1[0]["line"] if h1 else 1, "error", "description", f"no description paragraph within {self.lc['descriptionWithin']} lines of the top")
        else:
            line, words = desc
            if words > self.lc["descriptionMaxWords"]:
                self.add(line, "warn", "description", f"first paragraph is {words} words; the opening should say what it is in one or two sentences")
        for key in st["required"]:
            if key == "description":
                continue
            if not any(heading_matches(self.config, key, h["text"]) for h in d["headings"]):
                self.add(1, "warn" if key == "contributing" else "error", "section", f"missing a '{self.config['sections'][key]['title']}' section (required by style '{self.style_name}')")
        n = len(d["lines"])
        if n > st["maxLines"]:
            self.add(n, "warn", "length", f"{n} lines exceeds {st['maxLines']} for style '{self.style_name}'; move detail to docs/ and link it")
        h2 = [h for h in d["headings"] if h["level"] == 2]
        has_toc = any(re.search(r"contents|table of contents", h["text"], re.I) for h in d["headings"]) or self.has_anchor_list()
        mode = st.get("toc", "auto")
        if not has_toc and (mode == "required" or (mode == "auto" and len(h2) >= st.get("tocMinHeadings", 9))):
            self.add(1, "warn", "toc", f"{len(h2)} sections and no table of contents")
        if has_toc and mode == "never":
            self.add(1, "info", "toc", "table of contents on a minimal README; usually unnecessary")

    def has_anchor_list(self) -> bool:
        run = 0
        for _, line in self.doc["prose"]:
            if re.match(r"^\s*[-*]\s+\[[^\]]+\]\(#[^)]+\)", line):
                run += 1
                if run >= 4:
                    return True
            elif line.strip():
                run = 0
        return False

    def description(self):
        """First prose paragraph (4+ words) within the first lines; headings, badges, HTML, tables and nav lines are skipped."""
        limit = self.lc["descriptionWithin"]
        for i, line in self.doc["prose"]:
            if i > limit:
                break
            s = line.strip()
            if not s or re.match(r"^#{1,6}\s", s) or re.match(r"^[-*+]\s|^\d+\.\s|^\|", s):
                continue
            if re.match(r"^(!\[[^\]]*\]\([^)]*\)|\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\))(\s*(!\[|\[!\[).*)*$", s):
                continue  # badge or image line
            text = re.sub(r"<[^>]+>", " ", s.lstrip("> "))
            text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
            if text.count(" | ") >= 1 and len(re.findall(r"\]\(", s)) >= 2:
                continue  # navigation line: Docs | API | Community
            words = re.sub(r"[*_`]", "", text).split()
            if len(words) >= 4:
                return i, len(words)
        return None

    # -- links -----------------------------------------------------------------
    def resolve(self, url: str) -> Path:
        target = urllib.parse.unquote(url.split("#", 1)[0].split("?", 1)[0])
        return (self.project / target.lstrip("/")) if target.startswith("/") else (self.readme.parent / target)

    def links(self):
        d = self.doc
        valid = anchors([h["text"] for h in d["headings"]]) | d["html_ids"]
        for item in d["links"] + d["images"]:
            url, line, is_img = item["url"], item["line"], item in d["images"]
            if url.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            if url.startswith("#"):
                if url[1:].lower() not in {v.lower() for v in valid} and not is_img:
                    self.add(line, "error", "anchor", f"link '#{url[1:]}' matches no heading")
                continue
            if re.match(r"^[a-z][a-z0-9+.-]*://", url, re.I):
                host = urllib.parse.urlparse(url).netloc
                if not host or "." not in host and host != "localhost":
                    self.add(line, "error", "url", f"malformed URL '{url}'")
                elif re.search(r"(^|\.)example\.(com|org)$", host):
                    self.add(line, "info", "url", f"placeholder host in '{url}'")
                elif self.check_links and not is_img:
                    self.http_check(url, line)
                continue
            path = self.resolve(url)
            if not path.exists():
                self.add(line, "error", "image-missing" if is_img else "link-missing", f"{'image' if is_img else 'link'} target not found: {url}")
            elif is_img and path.is_file() and path.stat().st_size > self.lc["imageMaxBytes"]:
                self.add(line, "warn", "image-size", f"image {url} is {path.stat().st_size // 1024} KB; compress it or host it elsewhere")
            if is_img and not (item.get("text") or "").strip():
                self.add(line, "warn", "image-alt", f"image {url} has no alt text")
        for item in d["images"]:
            if re.match(r"^https?://", item["url"]) and not (item.get("text") or "").strip() and not BADGE_HOST.search(item["url"]):
                self.add(item["line"], "warn", "image-alt", f"image {item['url'][:60]} has no alt text")

    def http_check(self, url: str, line: int):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "readme-enhanced-lint"})
            with urllib.request.urlopen(req, timeout=8) as r:
                if r.status >= 400:
                    self.add(line, "warn", "link-http", f"{url} returned {r.status}")
        except urllib.error.HTTPError as e:
            if e.code not in (403, 405, 429):
                self.add(line, "warn", "link-http", f"{url} returned {e.code}")
        except (urllib.error.URLError, OSError) as e:
            self.add(line, "warn", "link-http", f"{url} not reachable ({getattr(e, 'reason', e)})")

    # -- code blocks and placeholders ------------------------------------------
    def code(self):
        for start in self.doc["unclosed"]:
            self.add(start, "error", "fence", "code fence is never closed")
        for f in self.doc["fences"]:
            if not f["lang"] and any(b.strip() for _, b in f["body"]):
                self.add(f["start"], "warn", "fence-lang", "code block has no language tag")
            body = [b.strip() for _, b in f["body"] if b.strip() and not b.strip().startswith("#")]
            if f["lang"] in SHELL_LANGS and len(body) >= 1 and all(re.match(r"^\$\s", b) for b in body):
                self.add(f["start"], "info", "prompt", "every command starts with '$ '; leaving it out makes the block copy-pasteable")

    def placeholders(self):
        pats = [re.compile(p, re.I) for p in self.lc["placeholders"]]
        for i, line in enumerate(self.doc["lines"], 1):
            line = re.sub(r"(?<!`)`[^`\n]+`(?!`)", " ", line)  # a marker named inside inline code is documentation, not a leftover
            for p in pats:
                m = p.search(line)
                if m:
                    self.add(i, "error", "placeholder", f"leftover placeholder: '{m.group(0)}'")
                    break

    # -- commands --------------------------------------------------------------
    def project_files(self) -> list:
        if self.files is None:
            self.files = list_files(self.project)
        return self.files

    def commands(self):
        f = self.facts
        node = next((e for e in f.get("ecosystems", []) if e["ecosystem"] == "node"), None)
        make_targets = set(f.get("make_targets", []))
        repo = f.get("repo", {})
        base = self.project  # commands in a README are run from the project root
        cwd, virtual = base, False  # the working directory carries over between consecutive blocks (setup steps)
        blocks = [(fe["start"], fe["body"]) for fe in self.doc["fences"] if fe["lang"] in SHELL_LANGS]
        for start, body in blocks:
            for ln, raw in body:
                s = raw.strip()
                if not s or s.startswith("#") or s.endswith("\\") or "<!--" in s:
                    continue
                s = re.sub(r"^[$>]\s+", "", s)
                for part in re.split(r"\s*(?:&&|;)\s*", s):
                    part = re.sub(r"^(sudo\s+|[A-Z_][A-Z0-9_]*=\S+\s+)+", "", part.split("|")[0].strip())
                    if part:
                        cwd, virtual = self.check_command(ln, part, cwd, base, virtual, node, make_targets, repo)
        for ln, code in self.doc["inline"]:
            m = re.match(r"^(npm run \S+|yarn \S+|pnpm \S+|make \S+|pip3? install -r \S+|python3? \S+\.py)(\s|$)", code.strip())
            if m:
                self.check_command(ln, code.strip(), base, base, False, node, make_targets, repo)

    def toplevel(self):
        if not hasattr(self, "_top"):
            import subprocess
            try:
                r = subprocess.run(["git", "-C", str(self.project), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
                self._top = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
            except (OSError, subprocess.SubprocessError):
                self._top = None
        return self._top

    def need(self, ln: int, cwd: Path, name: str, why: str):
        if not (cwd / name).exists():
            self.add(ln, "error", "command", f"'{why}' but there is no {name} in {self.rel(cwd)}")
            return False
        return True

    def rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.project)) or "."
        except ValueError:
            return str(p)

    def check_command(self, ln, cmd, cwd, base, virtual, node, make_targets, repo):
        parts = cmd.split()
        if not parts:
            return cwd, virtual
        exe, args = parts[0], parts[1:]
        if exe == "git" and args[:1] == ["clone"] and len(args) >= 2:
            m = re.search(r"(?:github\.com|gitlab\.com|bitbucket\.org)[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?$", args[1])
            if m and repo.get("owner") and (m.group(1).lower(), m.group(2).lower()) != (repo["owner"].lower(), (repo.get("name") or "").lower()):
                self.add(ln, "warn", "command", f"git clone points at {m.group(1)}/{m.group(2)} but this repository is {repo['owner']}/{repo.get('name')}")
            return base, True
        if exe == "cd" and args:
            target = args[0].strip("\"'")
            if target in ("~", "-") or target.startswith(("~", "$")):
                return cwd, virtual
            if virtual:  # inside a fresh clone: the repository directory or this project's directory means "the project root"
                if (cwd / target).is_dir():
                    return (cwd / target).resolve(), virtual
                names = {base.name, (repo.get("name") or ""), (repo.get("subdir") or "").split("/")[-1], ""}
                if target.rstrip("/").split("/")[-1] in names:
                    return base, virtual
                self.add(ln, "warn", "command", f"cd {target}: not the repository or project directory")
                return cwd, virtual
            new = (cwd / target).resolve()
            if new.is_dir():
                return new, virtual
            top = self.toplevel()
            if top and (top / target).is_dir():  # a sub-project README may address the repository root
                return (top / target).resolve(), virtual
            if target.rstrip("/") == base.name:
                return base, virtual
            self.add(ln, "error", "command", f"cd {target}: directory not found in {self.rel(cwd)}")
            return cwd, virtual
        pkg = None
        if exe in ("npm", "yarn", "pnpm", "bun"):
            pj = cwd / "package.json"
            if not pj.exists():
                global_or_scaffold = args[:1] in (["init"], ["create"], ["dlx"], ["exec"]) or "-g" in args or "--global" in args
                if not global_or_scaffold:
                    self.add(ln, "error", "command", f"'{cmd}' but there is no package.json in {self.rel(cwd)}")
                return cwd, virtual
            try:
                pkg = json.loads(read(pj))
            except ValueError:
                return cwd, virtual
            scripts = pkg.get("scripts") or {}
            name = None
            if args[:1] == ["run"] and len(args) > 1:
                name = args[1]
            elif exe == "npm" and args[:1] in (["test"], ["start"], ["t"]):
                name = "test" if args[0] in ("test", "t") else "start"
            elif exe in ("yarn", "pnpm", "bun") and args and args[0] not in YARN_BUILTIN and not args[0].startswith("-"):
                name = args[0]
            if name and name not in scripts and not (name == "start" and (cwd / "server.js").exists()):
                self.add(ln, "error", "command", f"'{cmd}': package.json has no script '{name}'")
            return cwd, virtual
        if exe in ("pip", "pip3") and args[:1] == ["install"]:
            if "-r" in args and args.index("-r") + 1 < len(args):
                self.need(ln, cwd, args[args.index("-r") + 1], cmd)
            elif any(a in (".", "-e") for a in args) and any(a == "." or a.startswith(".[") or a.startswith("\".[") for a in args):
                if not any((cwd / n).exists() for n in ("pyproject.toml", "setup.py", "setup.cfg")):
                    self.add(ln, "error", "command", f"'{cmd}' but there is no pyproject.toml or setup.py in {self.rel(cwd)}")
            return cwd, virtual
        if exe in ("python", "python3", "py") and args and args[0].endswith(".py"):
            self.need(ln, cwd, args[0], cmd)
            return cwd, virtual
        if exe in ("node", "bash", "sh", "zsh") and args and re.search(r"\.(m?js|cjs|sh)$", args[0]):
            self.need(ln, cwd, args[0], cmd)
            return cwd, virtual
        if exe.startswith("./") and len(exe) > 2:
            self.need(ln, cwd, exe[2:], cmd)
            return cwd, virtual
        if exe == "make":
            if not (cwd / "Makefile").exists() and not (cwd / "makefile").exists():
                self.add(ln, "error", "command", f"'{cmd}' but there is no Makefile in {self.rel(cwd)}")
            elif args and not args[0].startswith("-") and make_targets and args[0] not in make_targets:
                self.add(ln, "error", "command", f"'{cmd}': Makefile has no target '{args[0]}'")
            return cwd, virtual
        if exe == "cargo" and args and args[0] in ("build", "run", "test", "check", "bench"):
            self.need(ln, cwd, "Cargo.toml", cmd)
        elif exe == "go" and args and args[0] in ("build", "run", "test", "mod"):
            self.need(ln, cwd, "go.mod", cmd)
        elif exe in ("poetry", "uv") and args and args[0] in ("install", "sync", "run", "build"):
            self.need(ln, cwd, "pyproject.toml", cmd)
        elif exe == "docker" and args[:1] == ["build"] and "-f" not in args:
            self.need(ln, cwd, "Dockerfile", cmd)
        elif (exe == "docker-compose" or (exe == "docker" and args[:1] == ["compose"])) and not any((cwd / n).exists() for n in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")):
            self.add(ln, "error", "command", f"'{cmd}' but there is no compose file in {self.rel(cwd)}")
        return cwd, virtual

    # -- badges, licence, companions, staleness --------------------------------
    def badges(self):
        urls, repo = {}, self.facts.get("repo", {})
        for item in self.doc["images"]:
            if not BADGE_HOST.search(item["url"]):
                continue
            if item["url"] in urls:
                self.add(item["line"], "warn", "badge-duplicate", f"badge repeated (first on line {urls[item['url']]})")
            urls.setdefault(item["url"], item["line"])
            m = re.search(r"(?:github\.com|shields\.io/github/[\w-]+)/([\w.-]+)/([\w.-]+)", item["url"])
            slug = (m.group(1).lower(), re.sub(r"\.git$", "", m.group(2).lower())) if m else None
            if slug and repo.get("owner") and repo.get("name") and slug != (repo["owner"].lower(), repo["name"].lower()):
                self.add(item["line"], "error", "badge-slug", f"badge points at {m.group(1)}/{m.group(2)} but the repository is {repo['owner']}/{repo['name']}")
        if len(urls) > self.st["maxBadges"]:
            self.add(min(urls.values()), "warn", "badge-count", f"{len(urls)} badges; style '{self.style_name}' allows {self.st['maxBadges']}. Keep only the ones a reader acts on")

    def consistency(self):
        lic, f = self.facts.get("license", {}), self.facts
        declared = lic.get("spdx") or f.get("license_declared")
        if not lic.get("file") and not f.get("companion", {}).get("license"):
            self.add(1, "warn", "license-file", "no LICENSE file in the project; an open-source README needs one")
        sect = None
        for k, h in enumerate(self.doc["headings"]):
            if heading_matches(self.config, "license", h["text"]):
                end = self.doc["headings"][k + 1]["line"] if k + 1 < len(self.doc["headings"]) else len(self.doc["lines"]) + 1
                sect = (h["line"], "\n".join(self.doc["lines"][h["line"]: end - 1]))
        if sect and declared:
            named = [s for s, pat in SPDX_WORDS if re.search(pat, sect[1])]
            norm = re.sub(r"-(only|or-later)$", "", declared)
            if named and norm not in named:
                self.add(sect[0], "warn", "license-mismatch", f"README says {', '.join(named)} but the project's licence is {declared}")
        text = self.text
        comp = f.get("companion", {})
        mentioned = {"CONTRIBUTING": r"CONTRIBUTING(\.md)?", "CODE_OF_CONDUCT": r"CODE[_ ]OF[_ ]CONDUCT(\.md)?", "SECURITY": r"SECURITY(\.md)?\b", "CHANGELOG": r"CHANGELOG(\.md)?"}
        for key, pat in mentioned.items():
            have = comp.get(key.lower())
            m = re.search(pat, text)
            if m and not have:
                ln = text[: m.start()].count("\n") + 1
                self.add(ln, "warn", "companion-missing", f"README refers to {key} but the project has no such file")
        if self.style_name != "minimal":
            for key in self.lc["companionFiles"]:
                if key == "LICENSE" or comp.get(key.lower()):
                    continue
                if key in ("SECURITY", "CODE_OF_CONDUCT") and self.style_name != "comprehensive":
                    continue
                if not re.search(mentioned.get(key, key), text):
                    self.add(1, self.lc["companionSeverity"].get(key, "info"), "companion-suggest", f"no {key} file; consider adding one (offer to write it)")

    def corpus(self) -> str:
        chunks, total = [], 0
        for rel in self.project_files():
            p = Path(rel)
            if p.name.lower().startswith("readme") or p.suffix.lower() not in TEXT_EXT:
                continue
            t = read(self.project / rel, 300_000)
            total += len(t)
            chunks.append(t.lower() + "\n" + p.name.lower())
            if total > 20_000_000:
                break
        return "\n".join(chunks)

    def stale(self):
        stop = set(self.lc["staleStopwords"])
        corpus = None
        cands = []  # (line, token, why)
        for ln, code in self.doc["inline"]:
            c = code.strip()
            if re.match(r"^(@[\w.-]+/)?[A-Za-z][\w.]*-[\w.-]+$", c) and c.lower() not in stop:  # package-like (hyphenated or scoped)
                cands.append((ln, c, "mentioned"))
            elif re.match(r"^[\w./-]+\.(py|js|mjs|json|md|sh|toml|ya?ml|html|css)$", c) and "*" not in c and "<" not in c:
                cands.append((ln, c, "file"))
        words = self.lc["techLineWords"]
        for ln, line in self.doc["prose"]:
            low = line.lower()
            if any(w in low for w in words):
                clean = re.sub(r"\*\*[^*]*:\*\*|\*\*", "", line)
                clean = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", clean).replace("`", "")
                clean = clean.split(":", 1)[1] if ":" in clean else clean
                for tok in re.split(r"[,;()/]| and | & ", clean):
                    tok = re.sub(r"\.js$", "", tok.strip().strip("*_. ")).strip()
                    if re.match(r"^[A-Za-z][\w+.-]{2,}$", tok) and tok.lower() not in stop:
                        cands.append((ln, tok, "mentioned"))
        if not cands:
            return
        files = {Path(f).name for f in self.project_files()}
        seen = set()
        for ln, tok, kind in cands:
            if (tok, ln) in seen:
                continue
            seen.add((tok, ln))
            if kind == "file":
                if (self.readme.parent / tok).exists() or (self.project / tok).exists() or Path(tok).name in files:
                    continue
                self.add(ln, "warn", "stale-file", f"`{tok}` is referenced but no such file exists in the project")
                continue
            if corpus is None:
                corpus = self.corpus()
            if tok.lower() not in corpus:
                self.add(ln, "warn", "stale-claim", f"'{tok}' appears in the README but nowhere else in the project; remove it or check it is still true")

    def run(self) -> list:
        for step in (self.structure, self.links, self.code, self.placeholders, self.commands, self.badges, self.consistency, self.stale):
            step()
        order = {"error": 0, "warn": 1, "info": 2}
        return sorted(self.out, key=lambda f: (f.line, order[f.severity]))


def main():
    p = argparse.ArgumentParser(description="Lint a README against the project it describes.")
    p.add_argument("readme", type=Path)
    p.add_argument("--project", type=Path, help="project root (default: the README's folder)")
    p.add_argument("--style", default="standard", help="minimal | standard | comprehensive (default: standard)")
    p.add_argument("--facts", type=Path, help="reuse facts.json from inspect_project.py")
    p.add_argument("--repo", help="owner/name when the git remote is missing or wrong")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--strict", action="store_true", help="warnings also fail the run")
    p.add_argument("--check-links", action="store_true", help="HEAD-request external links (needs network)")
    a = p.parse_args()
    if not a.readme.is_file():
        print(f"Error: README not found: {a.readme}", file=sys.stderr)
        sys.exit(2)
    config = load_config()
    style_of(config, a.style)
    project = (a.project or a.readme.parent).resolve()
    facts = json.loads(a.facts.read_text(encoding="utf-8")) if a.facts else inspect(project, a.repo)
    findings = Linter(a.readme.resolve(), project, a.style, facts, config, a.check_links).run()
    errors = sum(f.severity == "error" for f in findings)
    warns = sum(f.severity == "warn" for f in findings)
    if a.json:
        print(json.dumps({"readme": str(a.readme), "style": a.style, "errors": errors, "warnings": warns, "findings": [f.as_dict() for f in findings]}, indent=2))
    else:
        for f in findings:
            print(f"{a.readme.name}:{f.line}: {f.severity:5} [{f.rule}] {f.message}")
        print(f"\n{errors} error(s), {warns} warning(s), {len(findings) - errors - warns} note(s) ({a.style} style)" if findings else f"OK: no findings ({a.style} style)")
    sys.exit(1 if errors or (a.strict and warns) else 0)


if __name__ == "__main__":
    main()
