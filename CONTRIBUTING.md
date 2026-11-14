# Contributing skills

Place each skill in `skills/<skill-name>/`. Follow the [Agent Skills specification](https://agentskills.io/specification).

Each skill must include:

- `SKILL.md` with YAML frontmatter: a unique `name` matching the directory and a description of what it does and when to use it.
- `README.md` with installation, runtime dependencies, and usage examples.
- `LICENSE` so the license travels with independent installations.
- All scripts, references, templates, and assets needed by its workflow.

Use lowercase letters, numbers, and single hyphens in names (maximum 64 characters). Keep descriptions within 1,024 characters and skill instructions focused; put longer reference material in `references/`. Add `compatibility` when the skill needs a particular runtime, system package, or target project.

Resolve bundled resources relative to the installed skill directory. Document any target repository requirements and optional integrations with sibling skills. Do not assume the entire library is installed. Keep credentials, local environments, dependency directories, and temporary files out of the repository.

Add the skill to the root README catalog. No npm package, root `SKILL.md`, or registry manifest is needed for this layout.

## Validate

Run from the repository root:

```bash
python3 -m pip install PyYAML
python3 scripts/validate-skills.py
npx skills add . --list
```

For an installation smoke test, use a temporary project directory so the test does not alter your normal agent configuration:

```bash
# Replace the source path with the absolute path to your checkout
mkdir -p /tmp/skills-enhanced-install-check
cd /tmp/skills-enhanced-install-check
npx skills add /absolute/path/to/skills-enhanced --skill '*' -a claude-code -y
```

Verify that each installed skill includes its entry point, license, and referenced resources. Run the changed skill's documented examples when modifying executable workflows.

Once changes are pushed to GitHub, check remote discovery:

```bash
npx skills add cyborgoat/skills-enhanced --list
```
