#!/usr/bin/env python3
"""Draft a README from verified project facts.

Writes only what the facts support (title, badges, requirements, install, run and test commands,
structure, licence). Everything a human must supply becomes an explicit `<!-- ASK: ... -->` marker,
which `lint_readme.py` reports as an error until it is replaced.

Usage:
    python scaffold_readme.py facts.json README.md [--style minimal|standard|comprehensive] [--type TYPE] [--registry]

If the output file already exists it is left alone and the draft goes to <name>.draft.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import anchors, heading_matches, load_config, style_of

LANG_FENCE = {"Python": "python", "JavaScript": "javascript", "TypeScript": "typescript", "Rust": "rust", "Go": "go", "Java": "java",
              "Ruby": "ruby", "PHP": "php", "C": "c", "C++": "cpp", "C#": "csharp", "Shell": "bash", "Kotlin": "kotlin", "Swift": "swift"}


def ask(text: str) -> str:
    return f"<!-- ASK: {text} -->"


class Ctx:
    def __init__(self, facts: dict, config: dict, style: str, ptype: str, registry: bool):
        self.f, self.config, self.style, self.ptype, self.registry = facts, config, style, ptype, registry
        self.st = style_of(config, style)
        self.repo = facts.get("repo", {})
        self.notes: list = []

    @property
    def url(self):
        return self.repo.get("url")

    @property
    def branch(self):
        return self.repo.get("default_branch") or "main"

    def cmds(self, *kinds):
        return [c for c in self.f.get("commands", []) if c["kind"] in kinds]

    def file_link(self, name: str) -> str:
        """Relative link for a file in this project, else the repo-root file on the host."""
        if (Path(self.f["root"]) / name).exists():
            return name
        if self.url:
            sub = self.repo.get("subdir")
            return f"{self.url}/blob/{self.branch}/{name}"
        return name


def fence(lang: str, lines: list) -> str:
    return f"```{lang}\n" + "\n".join(lines) + "\n```"


def first_sentence(text: str, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    m = re.match(r"^(.+?[.!?])(\s|$)", text)
    s = m.group(1) if m else text
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


# ----------------------------------------------------------------------------- sections

def s_title(c: Ctx):
    return f"# {c.f['name']}"


def s_badges(c: Ctx):
    badges = []
    lic = c.f.get("license", {})
    spdx = lic.get("spdx") or c.f.get("license_declared")
    if spdx:
        badges.append(f"[![License: {spdx}](https://img.shields.io/badge/License-{spdx.replace('-', '--')}-blue.svg)]({c.file_link(lic['file']) if lic.get('file') else '#license'})")
    if c.url and "github.com" in c.url:
        for wf in [w for w in c.f.get("ci", []) if w["provider"] == "github-actions"][:2]:
            fn = Path(wf["file"]).name
            badges.append(f"[![{wf['name']}]({c.url}/actions/workflows/{fn}/badge.svg)]({c.url}/actions/workflows/{fn})")
    py = c.f.get("runtime", {}).get("python")
    if py and (m := re.search(r"(\d+\.\d+)", py)):
        badges.append(f"![Python {m.group(1)}+](https://img.shields.io/badge/python-{m.group(1)}%2B-blue)")
    nd = c.f.get("runtime", {}).get("node")
    if nd and (m := re.search(r"(\d+)", nd)):
        badges.append(f"![Node {m.group(1)}+](https://img.shields.io/badge/node-{m.group(1)}%2B-green)")
    if c.registry:
        name = c.f["name"]
        eco = {e["ecosystem"] for e in c.f.get("ecosystems", [])}
        if "node" in eco:
            badges.append(f"[![npm](https://img.shields.io/npm/v/{name})](https://www.npmjs.com/package/{name})")
        if "python" in eco:
            badges.append(f"[![PyPI](https://img.shields.io/pypi/v/{name})](https://pypi.org/project/{name}/)")
        if "rust" in eco:
            badges.append(f"[![crates.io](https://img.shields.io/crates/v/{name})](https://crates.io/crates/{name})")
    badges = badges[: c.st["maxBadges"]]
    return " ".join(badges) if badges else None


def s_description(c: Ctx):
    d = (c.f.get("description") or "").strip()
    if c.ptype == "claude-skill" or not d or len(d) > 220:
        hint = f" (manifest says: {first_sentence(d, 90)})" if d else ""
        c.notes.append("description: needs a human one-sentence pitch")
        return ask("one-sentence pitch: what it is, for whom, why it is useful" + hint)
    c.notes.append(f"description taken from {next((e['ecosystem'] for e in c.f.get('ecosystems', [])), 'manifest')} manifest")
    return d if d.endswith((".", "!", "?")) else d + "."


def s_highlights(c: Ctx):
    return f"## {c.config['sections']['highlights']['title']}\n\n- " + ask("3-5 bullets: what it does for the user (outcomes, not implementation)")


def s_requirements(c: Ctx):
    rt = c.f.get("runtime", {})
    items = []
    if rt.get("python"):
        items.append(f"Python {rt['python'].lstrip('>=~^ ')}+" if re.match(r"^[>=~^ ]*\d", rt["python"]) else f"Python {rt['python']}")
    if rt.get("node"):
        items.append(f"Node.js {rt['node'].lstrip('>=~^ ')}+")
    if rt.get("go"):
        items.append(f"Go {rt['go']}+")
    if c.f.get("has", {}).get("docker") and c.ptype in ("service", "web-app"):
        items.append("Docker (optional)")
    if not items:
        return None
    return "## Requirements\n\n" + "\n".join(f"- {i}" for i in items)


def s_install(c: Ctx):
    lines = []
    if c.url:
        lines.append(f"git clone {c.url}.git")
        repo_dir = c.repo.get("name") or c.f["name"]
        lines.append(f"cd {repo_dir}/{c.repo['subdir']}" if c.repo.get("subdir") else f"cd {repo_dir}")
    installs = c.cmds("install")
    if not installs:
        if lines:
            c.notes.append("install: no install command detected; add the real one")
            lines.append(ask("install command"))
        else:
            return "## Installation\n\n" + ask("how to install (no manifest or repository URL detected)")
    lines += [i["cmd"] for i in installs]
    body = fence("bash", lines)
    out = f"## Installation\n\n{body}"
    if c.registry:
        eco = {e["ecosystem"]: e for e in c.f.get("ecosystems", [])}
        reg = [f"pip install {c.f['name']}" if "python" in eco else None, f"npm install {c.f['name']}" if "node" in eco else None, f"cargo install {c.f['name']}" if "rust" in eco else None]
        reg = [r for r in reg if r]
        if reg:
            out += "\n\nOr from the package registry:\n\n" + fence("bash", reg[:1])
    if c.ptype == "claude-skill":
        out += f"\n\nThen make the skill available to Claude Code by copying the folder into your skills directory:\n\n" + fence("bash", [f"cp -r {c.f['name']} ~/.claude/skills/"])
    return out


def s_usage(c: Ctx):
    title = c.config["projectTypes"].get(c.ptype, {}).get("usageTitle", "Usage")
    out = [f"## {title}"]
    runs = c.cmds("run", "dev") if c.ptype in ("service", "web-app") else c.cmds("run", "example")
    sf = [s for s in c.f.get("script_files", []) if s.get("summary")]
    if c.ptype == "claude-skill":
        out.append(f"Ask Claude in natural language, or invoke the skill directly:\n\n" + fence("text", [f"/{c.f['name']} " + "<what you want>"]) + "\n\n" + ask("two or three example requests and what the user gets"))
        if sf:
            out.append("The skill bundles these scripts:\n\n| Script | What it does |\n|---|---|\n" + "\n".join(f"| `{s['path']}` | {s['summary']} |" for s in sf))
    elif c.ptype == "cli":
        bins = [e.get("bin") for e in c.f.get("ecosystems", []) if e.get("bin")]
        py = [k for e in c.f.get("ecosystems", []) for k in (e.get("scripts") or {}) if e["ecosystem"] == "python"]
        name = (bins[0][0] if bins and bins[0] else None) or (py[0] if py else c.f["name"])
        out.append(fence("bash", [f"{name} --help"]) + "\n\n" + ask(f"a real invocation of `{name}` and its actual output (paste it)"))
    elif c.ptype == "library":
        lang = LANG_FENCE.get((c.f.get("languages") or [{}])[0].get("language", ""), "text")
        out.append(ask("shortest useful code sample that shows the result (verify it runs)") + "\n\n" + fence(lang, ["# example goes here"]))
    elif runs:
        out.append(fence("bash", [r["cmd"] for r in runs[:4]]))
    else:
        out.append(ask("how to run it and what to expect"))
    examples = [r["cmd"] for r in c.cmds("example")]
    if examples and c.ptype in ("claude-skill", "library", "cli"):
        out.append("Try the bundled example:\n\n" + fence("bash", examples[:1]))
    return "\n\n".join(out)


def s_configuration(c: Ctx):
    env, cfg = c.f.get("env_vars", []), c.f.get("config_files", [])
    if not env and not cfg:
        return None
    out = ["## Configuration"]
    if cfg:
        out.append("Defaults live in " + ", ".join(f"[`{x}`]({x})" for x in cfg) + ".")
    if env:
        out.append("| Variable | Example |\n|---|---|\n" + "\n".join(f"| `{e['name']}` | `{e['example']}` |" for e in env))
    return "\n\n".join(out)


def s_development(c: Ctx):
    dev = [x["cmd"] for x in c.cmds("setup-dev", "test", "lint", "build")]
    if not dev:
        return None
    return "## Development\n\n" + fence("bash", dev[:6])


def s_architecture(c: Ctx):
    return "## How it works\n\n" + ask("3-5 sentences on the design, ideally with a Mermaid flowchart (GitHub renders ```mermaid blocks)")


def s_packages(c: Ctx):
    pk = c.f.get("packages", [])
    if not pk:
        return None
    rows = "\n".join(f"| [`{p['name']}`]({p['path']}/) | {first_sentence(p.get('description') or '', 110).replace('|', '/') or ''} |" for p in pk)
    return "## Packages\n\n| Package | Description |\n|---|---|\n" + rows


def s_structure(c: Ctx):
    tree = c.f.get("tree", [])
    if not tree:
        return None
    lines = [f"{c.f['name']}/"]
    for i, e in enumerate(tree[:18]):
        last = i == len(tree[:18]) - 1
        lines.append(("└── " if last else "├── ") + e["path"])
        for j, ch in enumerate(e["children"][:5]):
            lines.append(("    " if last else "│   ") + ("└── " if j == len(e["children"][:5]) - 1 else "├── ") + ch)
    return "## Project structure\n\n" + fence("text", lines)


def s_roadmap(c: Ctx):
    return "## Roadmap\n\n" + ask("3-5 honest next steps, or delete this section")


def s_contributing(c: Ctx):
    comp = c.f.get("companion", {})
    text = "Contributions are welcome."
    if comp.get("contributing"):
        text += f" Please read the [contributing guide]({c.file_link('CONTRIBUTING.md')}) first."
    elif c.url:
        text += f" Open an [issue]({c.url}/issues) to discuss a change, then send a pull request."
        c.notes.append("no CONTRIBUTING file: consider adding one")
    dev = [x["cmd"] for x in c.cmds("test")]
    if dev:
        text += "\n\nRun the checks before you open a pull request:\n\n" + fence("bash", dev[:2])
    return "## Contributing\n\n" + text


def s_security(c: Ctx):
    if c.f.get("companion", {}).get("security"):
        return f"## Security\n\nPlease report vulnerabilities as described in the [security policy]({c.file_link('SECURITY.md')})."
    return None


def s_support(c: Ctx):
    return f"## Support\n\nQuestions and bug reports: [open an issue]({c.url}/issues)." if c.url else None


def s_license(c: Ctx):
    lic = c.f.get("license", {})
    spdx = lic.get("spdx") or c.f.get("license_declared")
    if not spdx:
        c.notes.append("license: none detected, a LICENSE file is needed")
        return "## License\n\n" + ask("choose a licence and add a LICENSE file")
    link = c.file_link(lic["file"]) if lic.get("file") else "LICENSE"
    holder = f" © {lic['year']} {lic['holder']}" if lic.get("holder") and lic.get("year") else ""
    return f"## License\n\nReleased under the [{spdx} License]({link}).{holder}".rstrip()


RENDER = {"title": s_title, "badges": s_badges, "description": s_description, "highlights": s_highlights, "requirements": s_requirements,
          "install": s_install, "usage": s_usage, "configuration": s_configuration, "development": s_development, "architecture": s_architecture,
          "packages": s_packages, "structure": s_structure, "roadmap": s_roadmap, "contributing": s_contributing, "security": s_security,
          "support": s_support, "license": s_license}


def order_sections(c: Ctx) -> list:
    """Style order, with the project type's preferred sections moved together (in its order) to where the first one sat."""
    secs = list(c.st["sections"])
    if c.ptype == "monorepo" and "packages" not in secs:
        secs.insert(secs.index("highlights" if "highlights" in secs else "description") + 1, "packages")
    prefer = [k for k in c.config["projectTypes"].get(c.ptype, {}).get("order", []) if k in secs]
    if not prefer:
        return secs
    first = min(secs.index(k) for k in prefer)
    rest = [k for k in secs if k not in prefer]
    before = len([k for k in secs[:first] if k not in prefer])
    return rest[:before] + prefer + rest[before:]


def build_toc(body: str) -> str:
    heads = re.findall(r"^## (.+)$", body, re.M)
    ids = list(anchors(heads))
    ordered = [(h, a) for h, a in zip(heads, [x for x in _ordered_anchors(heads)])]
    return "## Table of contents\n\n" + "\n".join(f"- [{h}](#{a})" for h, a in ordered if not h.lower().startswith("table of contents"))


def _ordered_anchors(heads: list) -> list:
    from common import slugify
    seen, out = {}, []
    for h in heads:
        base = slugify(h)
        n = seen.get(base, 0)
        out.append(base if n == 0 else f"{base}-{n}")
        seen[base] = n + 1
    return out


def scaffold(facts: dict, config: dict, style: str, ptype: str | None, registry: bool):
    ptype = ptype or facts.get("project_type", "library")
    c = Ctx(facts, config, style, ptype, registry)
    blocks, toc_at = [], None
    for key in order_sections(c):
        if key == "toc":
            toc_at = len(blocks)
            blocks.append("@@TOC@@")
            continue
        text = RENDER[key](c)
        if text:
            blocks.append(text)
    md = "\n\n".join(blocks)
    if toc_at is not None:
        n_h2 = len(re.findall(r"^## ", md, re.M))
        toc = build_toc(md.replace("@@TOC@@", "")) if n_h2 >= 3 else ""
        md = md.replace("@@TOC@@", toc).replace("\n\n\n", "\n\n")
    return md.strip() + "\n", c


def main():
    p = argparse.ArgumentParser(description="Draft a README from verified project facts.")
    p.add_argument("facts", type=Path, help="facts.json from inspect_project.py")
    p.add_argument("output", type=Path, help="README path to write (an existing file is not overwritten)")
    p.add_argument("--style", default="standard", help="minimal | standard | comprehensive (default: standard)")
    p.add_argument("--type", dest="ptype", help="override the detected project type")
    p.add_argument("--registry", action="store_true", help="add registry install line and badge (only if the package is published)")
    p.add_argument("--force", action="store_true", help="overwrite the output file if it exists")
    a = p.parse_args()

    config = load_config()
    style_of(config, a.style)
    if a.ptype and a.ptype not in config["projectTypes"]:
        sys.exit(f"Error: unknown type '{a.ptype}'. Choose from: {', '.join(config['projectTypes'])}")
    facts = json.loads(a.facts.read_text(encoding="utf-8"))
    md, c = scaffold(facts, config, a.style, a.ptype, a.registry)

    out = a.output
    if out.exists() and not a.force:
        out = out.with_name(out.stem + ".draft" + out.suffix)
        existing = [h["text"] for h in facts.get("readme", {}).get("headings", [])]
        missing = [k for k in c.st["sections"] if k in config["sections"] and config["sections"][k]["aliases"] and not any(heading_matches(config, k, h) for h in existing)]
        print(f"{a.output} exists: wrote the draft to {out} instead. Sections the style expects but the README lacks: {', '.join(missing) or 'none'}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    asks = len(re.findall(r"<!--\s*ASK", md))
    print(f"Wrote {out} (style={a.style}, type={c.ptype}, {len(md.splitlines())} lines, {asks} ASK marker(s) to fill)")
    for n in dict.fromkeys(c.notes):
        print(f"  note: {n}")


if __name__ == "__main__":
    main()
