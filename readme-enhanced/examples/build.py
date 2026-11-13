#!/usr/bin/env python3
"""Regenerate examples/out and check the toolkit end to end:  python3 examples/build.py

Standard library only. Exit code 1 if any check fails.

  1. Scaffold each fixture project (without its README) and lint the draft: the only errors allowed
     are the "fill me in" ones (ASK markers and the description they stand in for).
  2. Lint the finished fixture READMEs: no errors and no warnings.
  3. Lint a deliberately bad README: every rule below must fire.
  4. Inspect, scaffold and lint the real skills in this repository (report only).
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FIX, OUT = HERE / "fixtures", HERE / "out"
REPO_ROOT = HERE.parent.parent
RESULTS = []


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True)


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"  ({detail})" if detail and not ok else ""))


def lint(readme, project, repo, style="standard", facts=None):
    args = [readme, "--project", project, "--repo", repo, "--style", style, "--json"]
    if facts:
        args += ["--facts", facts]
    r = run("lint_readme.py", *args)
    return json.loads(r.stdout), r


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)

    # 1. scaffold drafts
    for name, styles in (("py-lib", ("minimal", "standard", "comprehensive")), ("node-cli", ("standard",)), ("skill", ("standard",))):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / name
            shutil.copytree(FIX / name, proj, ignore=shutil.ignore_patterns("README.md"))
            facts = Path(tmp) / f"{name}.facts.json"
            r = run("inspect_project.py", proj, facts, "--repo", f"acme/{name}")
            check(f"inspect {name}", r.returncode == 0, r.stderr.strip()[-120:])
            data = json.loads(facts.read_text(encoding="utf-8"))
            data["root"] = f"<{name}>"  # keep temporary paths out of the committed examples
            (OUT / f"{name}.facts.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            for style in styles:
                draft = proj / "README.md"  # a README is linted where it lives, so its relative links resolve
                r = run("scaffold_readme.py", facts, draft, "--style", style, "--force")
                check(f"scaffold {name} ({style})", r.returncode == 0 and draft.exists(), r.stderr.strip()[-120:])
                shutil.copy(draft, OUT / f"{name}.scaffold-{style}.md")
                report, _ = lint(draft, proj, f"acme/{name}", style, facts)
                rules = {f["rule"] for f in report["findings"] if f["severity"] == "error"}
                check(f"draft {name} ({style}) has only fill-me-in errors", rules <= {"placeholder", "description"} and "placeholder" in rules, f"errors: {sorted(rules)}")

    # 2. finished READMEs
    for name in ("py-lib", "node-cli", "skill"):
        report, _ = lint(FIX / name / "README.md", FIX / name, f"acme/{name}")
        bad = [f for f in report["findings"] if f["severity"] in ("error", "warn")]
        check(f"finished README {name} is clean", not bad, "; ".join(f"{f['line']} {f['rule']}" for f in bad))

    # 3. the bad README must trip every rule
    report, r = lint(FIX / "bad" / "README.md", FIX / "bad", "acme/bad-demo")
    (OUT / "bad.lint.txt").write_text(run("lint_readme.py", FIX / "bad" / "README.md", "--project", FIX / "bad", "--repo", "acme/bad-demo").stdout, encoding="utf-8")
    found = {f["rule"] for f in report["findings"]}
    expected = {"title", "description", "section", "heading-level", "badge-slug", "badge-count", "badge-duplicate", "placeholder", "stale-claim", "stale-file",
                "fence", "fence-lang", "prompt", "command", "link-missing", "anchor", "image-missing", "image-alt", "companion-missing", "license-mismatch"}
    check("bad README exits 1", r.returncode == 1)
    check("bad README trips every rule", expected <= found, f"missing: {sorted(expected - found)}")
    cmd_msgs = " ".join(f["message"] for f in report["findings"] if f["rule"] == "command")
    check("bad README: nonexistent npm script, requirements file, Makefile and script all caught", all(x in cmd_msgs for x in ("deploy", "requirements-dev.txt", "Makefile", "tools/missing.py")))

    # 4. the real skills in this repository (report only)
    real = OUT / "real"
    real.mkdir()
    for d in ("pptx-enhanced", "dataviz-enhanced", "readme-enhanced"):
        src = REPO_ROOT / d
        if not src.is_dir():
            continue
        facts = real / f"{d}.facts.json"
        run("inspect_project.py", src, facts)
        run("scaffold_readme.py", facts, real / f"{d}.scaffold.md", "--style", "standard", "--force")
        if (src / "README.md").exists():
            (real / f"{d}.lint.txt").write_text(run("lint_readme.py", src / "README.md", "--facts", facts, "--project", src).stdout, encoding="utf-8")
    if (REPO_ROOT / "README.md").exists():
        facts = real / "repo-root.facts.json"
        run("inspect_project.py", REPO_ROOT, facts)
        (real / "repo-root.lint.txt").write_text(run("lint_readme.py", REPO_ROOT / "README.md", "--facts", facts, "--project", REPO_ROOT).stdout, encoding="utf-8")
    check("real skills inspected and linted", (real / "repo-root.lint.txt").exists() or not (REPO_ROOT / "README.md").exists())

    failed = RESULTS.count(False)
    print(f"\n{len(RESULTS) - failed}/{len(RESULTS)} checks passed; output in {OUT}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
