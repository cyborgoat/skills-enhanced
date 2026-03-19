# pptx-enhanced

Enhanced PowerPoint generation skill with an **Editorial Light** visual theme, 14 layout templates, Mermaid/SVG diagram rendering, and animated GIF capabilities via Manim.

## Features

- **Editorial Light Theme**: White-background presentations with red title typography, warm gold highlights, and slate-neutral supporting tones
- **SVG Diagram Generation**: Programmatically generate flowcharts, architecture diagrams, and technical illustrations
- **Mermaid Diagram Rendering**: Flowcharts, sequence diagrams, ER diagrams, Gantt charts via Playwright + CDN
- **Multi-format Image Support**: Embed SVG (rasterized), PNG, JPG, and GIF images
- **Animated GIF Generation**: Create instructional visuals using Manim Community Edition
- **HTML-to-PPTX Workflow**: Build slides using HTML templates, then convert to PowerPoint
- **Fully Configurable**: Customize colors, fonts, and layouts via JSON configuration

## Quick Start

### Installation

1. **Install Node.js dependencies:**
   ```bash
   cd .claude/skills/pptx-enhanced
   npm install
   npm run install-browsers
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r .claude/skills/pptx-enhanced/requirements.txt
   ```

3. **Install system requirements:**
   - **LibreOffice**: `brew install libreoffice` (macOS) or `apt install libreoffice` (Linux)
   - **Poppler**: `brew install poppler` (macOS) or `apt install poppler-utils` (Linux)

### Basic Usage

Simply invoke the skill in Claude Code:
```
/pptx-enhanced Create a presentation about cloud architecture
```

The skill will guide you through creating professional presentations with the Editorial Light theme.

## Configuration

Default theme configuration is in `default-pptx-config.json`. Customize:
- **Colors**: Red title typography (#C62828), gold accent (#FFB300), white background (#FFFFFF), slate support tones (#4E6E8E / #5B6474)
- **Fonts**: Title, body, caption sizes and weights
- **Layouts**: 14 slide templates and grid systems

## File Structure

```
pptx-enhanced/
├── SKILL.md                   # Main skill documentation
├── README.md                  # This file
├── default-pptx-config.json   # Theme configuration
├── html2pptx.md              # HTML slide creation rules
├── package.json              # Node.js dependencies
├── requirements.txt          # Python dependencies
└── scripts/
    ├── html2pptx.js          # HTML to PowerPoint converter
    ├── render-mermaid.js      # Mermaid diagram → PNG renderer
    ├── thumbnail.py          # Slide thumbnail generator
    └── inventory.py          # Text inventory extractor
```

## Workflow

1. **HTML Creation**: Generate slides as HTML using predefined templates
2. **Conversion**: Use `html2pptx.js` to convert HTML to PowerPoint
3. **Validation**: Generate thumbnail grids with `thumbnail.py` for visual review
4. **Refinement**: Extract text inventory with `inventory.py` for content review

## Theme Colors

| Role | Color | Usage |
|------|-------|-------|
| Primary | #C62828 | Slide titles and restrained emphasis |
| Secondary | #FFB300 | Callouts, highlights, accent boxes |
| Accent | #4E6E8E | Diagrams, data visuals, secondary emphasis |
| Background | #FFFFFF | Main slide background |
| Card | #FFFFFF | Card surfaces with subtle borders |

## Examples

The skill supports various slide layouts:
- Title slides with hero visuals
- Content slides with bullet points
- Comparison tables
- Timeline diagrams
- Process flows
- Technical architecture diagrams
- Full-slide visuals with overlays

See `SKILL.md` for detailed layout specifications and examples.

## License

Part of the Claude Code skills collection.
