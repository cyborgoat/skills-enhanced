# Sections by style and project type

## Styles
| Section | minimal | standard | comprehensive |
|---|---|---|---|
| Title, badges, description | yes | yes | yes |
| Table of contents | | if 9+ sections | yes |
| Features / highlights | | yes | yes |
| Requirements | | yes | yes |
| Installation, Usage | yes | yes | yes |
| Configuration | | if env vars or config files | yes |
| How it works (architecture) | | | yes |
| Packages / Project structure | | | yes |
| Development | | yes | yes |
| Roadmap | | | yes |
| Contributing | | yes | yes |
| Security, Support | | | yes |
| License | yes | yes | yes |

## By project type (what leads, what to add)
- **library**: install, then a short code sample that shows the result; link the API reference.
- **cli**: install, the command with real output, a flags table or `--help` excerpt, exit codes if scripts rely on them.
- **service / web-app**: requirements and configuration (env vars table) before running; ports; a screenshot for apps; Docker line if supported.
- **framework**: a hello-world under ten lines; link concepts and guides rather than explaining them.
- **data-ml**: data, model and hardware requirements; a results table; how to reproduce; licence of data and weights.
- **claude-skill**: how to install the skill (copy into `~/.claude/skills/`), what to ask Claude, a table of bundled scripts, requirements.
- **monorepo**: a packages table (name, one line, link) first; shared setup once.
- **docs**: how to build and preview locally, how to contribute a page.

## Section notes
- **Title**: the project name; a logo or banner is optional and needs alt text.
- **Description**: formula "X is a <category> that <does Y> for <audience>. Unlike <alternative>, it <difference>." Keep it under about 40 words.
  Weak: "A powerful, flexible toolkit for all your data needs." Better: "textstats counts words, sentences and reading time in plain text, with no dependencies."
- **Features**: 3-5 outcomes for the user, not implementation details.
- **Installation**: from source first; registry line only if published; platform notes where they differ.
- **Usage**: the smallest example that shows a result, with its real output.
- **Configuration**: a table of variables or options with defaults, only those that exist (`.env.example` is the source).
- **Development**: how to set up, test and lint, using the commands the project already has.
- **Contributing**: link CONTRIBUTING if present; otherwise say how to open an issue and run the tests.
- **License**: the SPDX name, a link to LICENSE, the holder.
