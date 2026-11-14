# Enhanced Agent Skills

A library of [Agent Skills](https://agentskills.io) for Claude Code, Codex, and other compatible coding agents. Install individual skills directly from GitHub with the [Skills CLI](https://github.com/vercel-labs/skills).

## Install

With Node.js and npm installed, run this from your project:

```bash
npx skills add cyborgoat/skills-enhanced
```

Choose the skills and coding agents interactively. To browse without installing:

```bash
npx skills add cyborgoat/skills-enhanced --list
```

Install a specific skill:

```bash
npx skills add cyborgoat/skills-enhanced --skill pptx-enhanced
npx skills add cyborgoat/skills-enhanced --skill dataviz-enhanced
npx skills add cyborgoat/skills-enhanced --skill readme-enhanced
npx skills add cyborgoat/skills-enhanced --skill product-docs-author
```

Installation defaults to the current project. Use `-g` for availability across projects, `-a` to select an agent, and `-y` to skip confirmation prompts:

```bash
# Global installation for Claude Code
npx skills add cyborgoat/skills-enhanced --skill pptx-enhanced -a claude-code -g -y

# Project installation for Codex
npx skills add cyborgoat/skills-enhanced --skill dataviz-enhanced -a codex -y
```

The CLI installs instructions and bundled files. It does not install runtime dependencies. Follow the selected skill's setup instructions below, running dependency commands from the installed skill directory. No npm publishing or manual download is required.

## Available skills

| Skill | Purpose | Runtime requirements |
| --- | --- | --- |
| [pptx-enhanced](skills/pptx-enhanced/) | Editable PowerPoint decks from JSON or HTML, charts, tables, technical diagrams, and insight reports | Node.js 22+, Python 3.10+ for validation; Chromium for HTML workflows; LibreOffice and Poppler for optional thumbnails |
| [dataviz-enhanced](skills/dataviz-enhanced/) | Altair charts from tabular data, anomaly highlighting, PNG/SVG/PDF and interactive HTML | Python 3.10+ and its bundled requirements |
| [readme-enhanced](skills/readme-enhanced/) | Write and lint open-source READMEs from verified repository facts | Python 3.9+ (standard library only) |
| [product-docs-author](skills/product-docs-author/) | Product documentation structure, routing, frontmatter, and bilingual writing conventions | A target documentation repository; designed for `core-web` conventions |

### PowerPoint setup

From the installed `pptx-enhanced` directory:

```bash
npm install
python3 -m pip install -r requirements.txt

# For HTML slides and browser-based rendering
npm run install-browsers

# Optional thumbnail dependencies on macOS
brew install libreoffice poppler
```

See the [skill README](skills/pptx-enhanced/README.md) for examples and validation.

### Data visualization setup

From the installed `dataviz-enhanced` directory, using your Python environment:

```bash
python3 -m pip install -r requirements.txt
```

See the [skill README](skills/dataviz-enhanced/README.md) for chart examples. No browser installation is required.

### README writer setup

No runtime dependencies beyond Python 3.9+. See the [skill README](skills/readme-enhanced/README.md) for the inspect, scaffold and lint workflow.

### Product documentation setup

No runtime dependencies. Read the [skill README](skills/product-docs-author/README.md) for the expected target repository layout and how to adapt it to another documentation project.

## Use

Ask your coding agent to use the installed skill. In Claude Code, for example:

```text
/pptx-enhanced Create a presentation about cloud architecture
/dataviz-enhanced Create a bar chart of quarterly revenue from this CSV
/readme-enhanced Write a README for this repository
/product-docs-author Review the product documentation structure and frontmatter
```

Invocation varies by agent; each `SKILL.md` contains the workflow and references.

## Update or remove

```bash
npx skills check
npx skills update
npx skills remove pptx-enhanced
```

## Repository layout

```text
skills-enhanced/
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── skills/
    ├── pptx-enhanced/
    │   ├── SKILL.md
    │   ├── LICENSE
    │   ├── README.md
    │   ├── scripts/
    │   ├── references/
    │   └── examples/
    ├── dataviz-enhanced/
    │   ├── SKILL.md
    │   ├── LICENSE
    │   ├── README.md
    │   ├── scripts/
    │   └── examples/
    ├── readme-enhanced/
    │   ├── SKILL.md
    │   ├── LICENSE
    │   ├── README.md
    │   ├── scripts/
    │   └── references/
    └── product-docs-author/
        ├── SKILL.md
        ├── LICENSE
        └── README.md
```

Each directory under `skills/` is independently installable. See [CONTRIBUTING.md](CONTRIBUTING.md) for authoring and installation checks.

## License

[MIT](LICENSE). Each skill bundles a copy of the license so it is included in standalone installations. This project is independently maintained and is not affiliated with coding agent vendors.
