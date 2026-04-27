# pptx-enhanced

Enhanced PowerPoint generation skill with an **Editorial Light** visual theme, modular references, editable PowerPoint shape guidance, raster diagram fallback, and short animation workflows.

## Features

- **Editorial Light Theme**: White-background presentations with red title typography, warm gold highlights, and slate-neutral supporting tones
- **Editable Visuals First**: Build simple workflows and diagrams as PowerPoint-editable HTML/PptxGenJS shapes
- **SVG/Mermaid Fallback**: Render complex diagrams to PNG when editable shapes are impractical
- **Multi-format Image Support**: Embed SVG (rasterized), PNG, JPG, and GIF images
- **Animation Generation**: Create short instructional animations using Manim, JS animation libraries, browser capture, or other suitable tooling
- **HTML-to-PPTX Workflow**: Build slides using HTML templates, then convert to PowerPoint
- **Fully Configurable**: Customize colors, fonts, and layouts via JSON configuration

## Quick Start

### Installation

1. **Install Node.js dependencies:**
   ```bash
   cd pptx-enhanced
   npm install
   npm run install-browsers
   ```
   `install-browsers` installs Playwright-managed Chromium so conversion does not need to launch your system Chrome app.

2. **Install Python dependencies:**
   ```bash
   pip install -r pptx-enhanced/requirements.txt
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
├── references/
│   ├── layouts.md            # Compact layout catalog
│   ├── visuals.md            # Editable diagrams, raster fallback, animation
│   └── validation.md         # Validation workflow and common fixes
├── package.json              # Node.js dependencies
├── requirements.txt          # Python dependencies
└── scripts/
    ├── html2pptx.js          # HTML to PowerPoint converter
    ├── render-mermaid.js      # Mermaid diagram → PNG renderer
    ├── thumbnail.py          # Slide thumbnail generator
    └── inventory.py          # Text inventory extractor
```

## Workflow

1. **Plan**: Pick slide layouts from `references/layouts.md`
2. **Create**: Generate one HTML file per slide using `html2pptx.md`
3. **Visualize**: Use editable shapes first; generate animations for demonstrative content
4. **Convert**: Use `html2pptx.js` to convert HTML to PowerPoint
5. **Validate**: Generate thumbnails when available and inspect text inventory

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

Start with `SKILL.md`, then open only the reference file needed for the task.

## License

Part of the Claude Code skills collection.
