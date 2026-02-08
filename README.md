# Enhanced Claude Skills

A collection of enhanced Claude skills that extend Claude's capabilities with specialized workflows, tools, and integrations.

## About This Repository

This repository contains custom Claude skills that can be installed in your `.claude/skills/` directory to give Claude additional capabilities. Each skill is a self-contained package with its own dependencies, scripts, and documentation.

## Available Skills

### 🎨 [Enhanced PowerPoint Generator](./pptx-enhanced/)

Generate professional PowerPoint presentations with a modern tech-blueprint visual style featuring deep teal headers, warm amber accents, and clean editorial layouts.

**Features:**
- Modern tech-blueprint theme with configurable colors and fonts
- HTML-to-PPTX conversion workflow
- SVG diagram generation and multi-format image support (SVG, PNG, JPG, GIF)
- Animated GIF generation using Manim Community Edition for instructional visuals
- Multiple slide layout templates (title, content, comparison, timeline, process flow, architecture)
- Automated slide thumbnail generation for validation
- Text inventory extraction from presentations

**Technologies:** Node.js (Playwright, PptxGenJS), Python (python-pptx, Manim, Pillow, Poppler)

### 📊 [Data Visualization Generator](./dataviz-enhanced/)

Generate publication-quality, Tufte-inspired data visualizations with optional anomaly highlighting from structured data (CSV, JSON, Excel) or unstructured text.

**Features:**
- 13 chart types: line, bar, hbar, scatter, histogram, heatmap, box, pie, donut, area, bubble, timeseries, small multiples
- Tufte-inspired minimal styling with colorblind-safe default palette (Wong 2011)
- Anomaly detection (Z-score, IQR, min/max, changepoint) with visual highlight overlays
- Multi-format input (CSV, TSV, JSON, Excel, Markdown tables, HTML tables, YAML) and output (PNG, SVG, PDF)
- Statistical annotations: trend lines, R², confidence bands
- Preview grid for comparing multiple charts side-by-side

**Technologies:** Python (matplotlib, seaborn, pandas, scipy, Pillow)

## Installation

### Quick Start

1. Clone this repository:
```bash
git clone <repository-url> skills-enhanced
cd skills-enhanced
```

2. Choose a skill and navigate to its folder:
```bash
cd pptx-enhanced
```

3. Install dependencies:
```bash
# Node.js dependencies
npm install
npm run install-browsers

# Python dependencies
pip install -r requirements.txt

# System dependencies (macOS)
brew install libreoffice poppler
```

4. Copy the skill to your Claude skills directory:
```bash
# From the skill folder
cp -r ../pptx-enhanced ~/.claude/skills/
```

### Alternative: Direct Installation

You can also copy individual skill folders directly to your `~/.claude/skills/` directory and install dependencies there.

## Usage

Once installed, simply invoke the skill in Claude Code:

- `/pptx-enhanced Create a PowerPoint presentation about cloud architecture`
- `/pptx-enhanced Generate slides for technical documentation`
- `/dataviz-enhanced Create a bar chart of quarterly revenue from this CSV`
- `/dataviz-enhanced Visualize the outliers in this sales data`

Each skill's README or SKILL.md contains detailed usage instructions and capabilities.

## Repository Structure

```
skills-enhanced/
├── README.md                      # This file
├── LICENSE                        # License file
├── .gitignore                     # Git ignore patterns
├── pptx-enhanced/                 # PowerPoint generation skill
│   ├── SKILL.md                   # Skill documentation
│   ├── README.md                  # Skill README
│   ├── package.json               # Node.js dependencies
│   ├── requirements.txt           # Python dependencies
│   ├── default-pptx-config.json   # Theme configuration
│   ├── html2pptx.md               # HTML slide creation rules
│   └── scripts/                   # Utility scripts
│       ├── html2pptx.js           # HTML to PowerPoint converter
│       ├── thumbnail.py           # Slide thumbnail generator
│       └── inventory.py           # Text inventory extractor
└── dataviz-enhanced/              # Data visualization skill
    ├── SKILL.md                   # Skill documentation
    ├── README.md                  # Skill README
    ├── requirements.txt           # Python dependencies
    ├── default-viz-config.json    # Theme, palettes, chart defaults
    └── scripts/                   # Utility scripts
        ├── parse_input.py         # Data file → normalized CSV/JSON
        ├── generate_chart.py      # Data → chart (SVG/PNG/PDF)
        ├── detect_highlights.py   # Anomaly detection → highlights JSON
        └── preview_grid.py        # Multiple images → review grid
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
- **System Dependencies** (for pptx-enhanced):
  - **LibreOffice**: For PPTX generation and manipulation
  - **Poppler**: For PDF processing and conversion
  - **Playwright Chromium**: Installed via `npm run install-browsers`

## License

MIT License - see [LICENSE](LICENSE) file for details

## Skills Development

### Current
- [x] Enhanced PowerPoint Generator (pptx-enhanced) - Modern tech-blueprint theme with SVG and animated GIF support

### Roadmap
- [ ] Document analyzer and summarizer
- [x] Data Visualization Generator (dataviz-enhanced) - Tufte-inspired charts with anomaly highlighting
- [ ] Code documentation generator
- [ ] Meeting notes formatter
- [ ] Presentation content optimizer

---

**Note**: These are custom skills developed independently and are not officially affiliated with Anthropic.
