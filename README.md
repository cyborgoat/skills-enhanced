# Enhanced Claude Skills

A collection of enhanced Claude skills that extend Claude's capabilities with specialized workflows, tools, and integrations.

## About This Repository

This repository contains custom Claude skills that can be installed in your `.claude/skills/` directory to give Claude additional capabilities. Each skill is a self-contained package with its own dependencies, scripts, and documentation.

## Available Skills

### 🎨 [Corporate PowerPoint Generator](./corporate-pptx-generator/)

Generate professional PowerPoint presentations with consistent corporate styling using predefined slide layouts and configurable JSON themes.

**Features:**
- HTML-to-PPTX conversion workflow
- Configurable themes (colors, fonts, layouts)
- Multiple slide layout templates (overview, challenges, methodology, comparison, etc.)
- Automated slide thumbnail generation for validation
- Text inventory extraction from presentations

**Technologies:** Node.js (Playwright, PptxGenJS), Python (python-pptx, Pillow)

## Installation

### Quick Start

1. Clone this repository:
```bash
git clone <repository-url> skills-enhanced
cd skills-enhanced
```

2. Choose a skill and navigate to its folder:
```bash
cd corporate-pptx-generator
```

3. Install dependencies:
```bash
# Node.js dependencies
npm install
npm run install-browsers

# Python dependencies
pip install -r requirements.txt
```

4. Copy the skill to your Claude skills directory:
```bash
# From the skill folder
cp -r ../corporate-pptx-generator ~/.claude/skills/
```

### Alternative: Direct Installation

You can also copy individual skill folders directly to your `~/.claude/skills/` directory and install dependencies there.

## Usage

Once installed, simply mention the skill's capability when chatting with Claude:

- "Create a PowerPoint presentation about..." (triggers corporate-pptx-generator)
- "Generate slides for..." (triggers corporate-pptx-generator)

Each skill's README or SKILL.md contains detailed usage instructions.

## Repository Structure

```
skills-enhanced/
├── README.md                      # This file
├── .gitignore                     # Git ignore patterns
└── <skill-name>/                  # Individual skill folders
    ├── SKILL.md                   # Skill documentation
    ├── package.json               # Node.js dependencies (if applicable)
    ├── requirements.txt           # Python dependencies (if applicable)
    └── scripts/                   # Utility scripts
```

## Contributing

Each skill should be:
- **Self-contained**: Include all necessary dependencies and scripts
- **Well-documented**: Provide clear setup and usage instructions
- **Tested**: Ensure all scripts and workflows function correctly
- **Configurable**: Use JSON or configuration files for customization

## Requirements

- **Node.js**: v16+ (for skills using JavaScript/TypeScript)
- **Python**: 3.8+ (for skills using Python)
- **Claude Desktop**: Latest version with skills support

## License

MIT License - see [LICENSE](LICENSE) file for details

## Skills Roadmap

Future skills planned:
- [ ] Document analyzer and summarizer
- [ ] Data visualization generator
- [ ] Code documentation generator
- [ ] Meeting notes formatter

---

**Note**: These are custom skills developed independently and are not officially affiliated with Anthropic.
