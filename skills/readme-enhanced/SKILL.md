---
name: readme-enhanced
description: Write or improve the README.md of an open-source project from verified facts. Inspects the repo (manifests, scripts, licence, CI, structure), drafts a README in minimal, standard or comprehensive style, and lints it for broken links, missing sections, leftover placeholders, commands that do not exist in the project, and stale claims. Use when asked to write, rewrite, review, shorten or check a README or a project's landing page.
license: Complete terms in LICENSE
---

# readme-enhanced

Facts come from the repository, the story comes from the user, and every command and claim is checked. Never invent features, benchmarks, users, versions or badges. Standard library only (Python 3.9+), no installs.

## Workflow

1. **Inspect.** `python scripts/inspect_project.py <project> facts.json` (add `--repo owner/name` when there is no git remote). Read `project_type`, `commands` (each with its source file), `license`, `ci`, `packages`, `script_files`, `readme`.
2. **Existing README?** Run the linter first to see what is wrong, then improve it in place and keep the author's voice and anything still true. Rewrite from scratch only if asked.
3. **Ask once**, only what the facts cannot say: style (default `standard`), confirm the project type, the one-sentence pitch and audience, status (stable, beta, experimental), whether a screenshot, GIF or demo exists.
4. **Scaffold.** `python scripts/scaffold_readme.py facts.json README.md --style standard` writes what the facts support and marks the rest `<!-- ASK: ... -->`. An existing README is never overwritten (the draft goes to `README.draft.md` with a list of missing sections). Use `--registry` only if the package is published.
5. **Write the narrative.** Replace every ASK marker: a one- or two-sentence pitch (what, for whom, why), features as outcomes, a real usage example whose output you ran, diagrams as Mermaid (GitHub renders them). Guidance: `references/principles.md`, `references/sections.md`.
6. **Lint.** `python scripts/lint_readme.py README.md --style standard`. Fix every error; fix or justify each warning. Add `--check-links` online to test external URLs.
7. **Verify.** With the user's permission run the install and one usage command in a temporary copy; otherwise at least `--help` or a syntax check. Say which you did.
8. **Report** assumptions, what you could not verify, and missing companion files (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG). Offer to write them; do not add them unasked.

## Styles

| Style | For | Sections | Badges | Lines |
|---|---|---|---|---|
| `minimal` | scripts, experiments, small tools | title, description, install, usage, license | 3 | 90 |
| `standard` (default) | most open-source projects | adds features, requirements, configuration, development, contributing | 5 | 260 |
| `comprehensive` | large or widely used projects, monorepos | adds table of contents, how it works, packages, structure, roadmap, security, support | 6 | 520 |

Project types (`cli`, `library`, `service`, `web-app`, `framework`, `data-ml`, `claude-skill`, `monorepo`, `docs`) change section order and wording; override with `--type`.

## Rules

- First screen (about 25 lines) answers what it is, who it is for, and why, then shows a result or a two-minute start.
- Commands are copy-pasteable (no `$` prompts), say which directory they run in, and exist in the project. Show real output.
- At most 3-6 badges, all pointing at this repository. No adjectives like "powerful" or "blazing"; state facts.
- Relative links for files in the repo. Past the style's line cap, link to `docs/` instead of growing.
- Changing the README means re-running the linter; the same check can run in CI.

## Scripts

| Script | Purpose |
|---|---|
| `inspect_project.py` | repo to `facts.json` (no network, never runs project code) |
| `scaffold_readme.py` | facts to a README draft with ASK markers |
| `lint_readme.py` | README plus project to findings (`--json`, `--strict`; exit 1 on errors) |

Config (styles, section aliases, thresholds): `default-readme-config.json`. Examples and self-test: `python examples/build.py`. Badge snippets: `references/badges.md`.
