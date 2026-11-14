# readme-enhanced

Claude Code skill that writes or improves a project's `README.md` from verified facts instead of guesses.

- **Inspect** a repository: manifests, scripts, licence, CI, structure, existing README (no network, never runs project code).
- **Scaffold** a draft in `minimal`, `standard` or `comprehensive` style; whatever only a human can say becomes an `<!-- ASK: ... -->` marker.
- **Lint** the result: broken links and anchors, missing sections, leftover placeholders, commands that do not exist in the project, wrong badge slugs, licence mismatch, stale claims.

Python 3.9+, standard library only; nothing to install.

## Quick start

```bash
python scripts/inspect_project.py ../my-project facts.json
python scripts/scaffold_readme.py facts.json ../my-project/README.md --style standard
python scripts/lint_readme.py ../my-project/README.md --style standard
python examples/build.py        # self-test and example output in examples/out/
```

In Claude Code, ask: "write a README for this project" or "check my README".

## Layout

```text
SKILL.md                      workflow and rules
default-readme-config.json    styles, project types, lint thresholds
scripts/                      inspect_project.py, scaffold_readme.py, lint_readme.py, common.py
references/                   principles.md, sections.md, badges.md
examples/                     fixtures, finished READMEs, a deliberately bad README, build.py
```

## License

Released under the [MIT License](LICENSE).
