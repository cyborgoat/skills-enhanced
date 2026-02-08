---
name: corporate-pptx-generator
description: Generate professional PowerPoint presentations with consistent corporate styling using predefined slide layouts and a configurable JSON theme. Use this when users want to create PowerPoint presentations with corporate branding, specific layout templates, or consistent formatting across slides.
license: Complete terms in LICENSE.txt
---

# Corporate PowerPoint Generator Skill

Generate professional PowerPoint presentations with consistent corporate styling using predefined slide layouts and a configurable JSON theme.

## Overview

This skill creates PowerPoint presentations using an HTML-to-PPTX workflow with a corporate HUAWEI red theme. The styling, colors, fonts, and layouts are fully configurable via a JSON configuration file.

## When to Use This Skill

Use this skill when the user wants to:
- Create a PowerPoint presentation with corporate styling
- Generate slides following specific layout templates (overview, challenges, methodology, comparison, etc.)
- Build presentations with consistent branding and formatting

## Skill Contents

This is a **standalone skill** with all dependencies included:

```
.claude/skills/corporate-pptx-generator/
├── SKILL.md                      # This file - main skill documentation
├── default-pptx-config.json      # Default theme configuration (colors, fonts, layouts)
├── html2pptx.md                  # HTML slide creation rules and constraints
├── package.json                  # Node.js dependencies
├── requirements.txt              # Python dependencies
└── scripts/
    ├── html2pptx.js              # HTML to PowerPoint conversion script
    ├── thumbnail.py              # Generate slide thumbnail grids for validation
    └── inventory.py              # Extract text inventory from presentations
```

## Setup Instructions

### 1. Install Node.js Dependencies

Navigate to the skill folder and install npm packages:

```bash
cd .claude/skills/corporate-pptx-generator
npm install
npm run install-browsers  # Install Playwright Chromium for HTML rendering
```

### 2. Install Python Dependencies

```bash
pip install -r .claude/skills/corporate-pptx-generator/requirements.txt
```

### 3. System Requirements

- **LibreOffice** (for PDF conversion in thumbnail generation): `brew install libreoffice` (macOS) or `apt install libreoffice` (Linux)
- **Poppler** (for pdftoppm): `brew install poppler` (macOS) or `apt install poppler-utils` (Linux)

## Configuration

The default configuration is in [`default-pptx-config.json`](default-pptx-config.json) in this skill's folder.

### Color Theme (Default: Corporate Red)

| Color Role | Hex Code | Usage |
|------------|----------|-------|
| primary | #C8102E | Main accent, headers, borders |
| primaryDark | #8B0000 | Darker emphasis |
| primaryLight | #FFE5E5 | Light backgrounds, content boxes |
| secondary | #FFB3B3 | Secondary backgrounds |
| accent | #E60012 | Highlights |
| background | #FFFFFF | Main slide background |
| backgroundAlt | #FFF5F5 | Alternate section backgrounds |
| text.dark | #1A1A1A | Main body text |
| text.onPrimary | #FFFFFF | Text on red backgrounds |
| text.highlight | #C8102E | Emphasized text |

### Font Styles

| Style | Size | Weight | Usage |
|-------|------|--------|-------|
| title | 32pt | Bold | Slide titles |
| subtitle | 24pt | Bold | Subtitles |
| sectionHeader | 18pt | Bold | Section headers (white on red) |
| contentHeader | 16pt | Bold | Content headers (red text) |
| body | 12pt | Normal | Body text |
| caption | 10pt | Normal | Small annotations |
| label | 11pt | Bold | Labels, tags |

## Workflow

### Step 1: Load Configuration

```javascript
const fs = require('fs');
const path = require('path');

// Load the default config from skill folder
const configPath = path.join(__dirname, 'default-pptx-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Or load custom config if provided by user
function loadConfig(customPath = null) {
  if (customPath && fs.existsSync(customPath)) {
    return JSON.parse(fs.readFileSync(customPath, 'utf8'));
  }
  return JSON.parse(fs.readFileSync(configPath, 'utf8'));
}
```

### Step 2: Create HTML Slides

For each slide, create an HTML file following the corporate design patterns below. See [`html2pptx.md`](html2pptx.md) for detailed HTML creation rules.

**CRITICAL HTML Rules**:
- Body dimensions: `width: 720pt; height: 405pt` for 16:9
- ALL text MUST be in `<p>`, `<h1>`-`<h6>`, `<ul>`, or `<ol>` tags
- Use web-safe fonts only: Arial, Helvetica, Times New Roman, Georgia, Verdana
- Backgrounds/borders/shadows only work on `<div>` elements
- NEVER use CSS gradients - rasterize as PNG first

### Step 3: Convert to PowerPoint

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./.claude/skills/corporate-pptx-generator/scripts/html2pptx');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';

// Convert each HTML slide
const { slide, placeholders } = await html2pptx('slide1.html', pptx);

await pptx.writeFile('presentation.pptx');
```

### Step 4: Validate Output

```bash
python .claude/skills/corporate-pptx-generator/scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```

---

## Slide Layout Templates

### Common Elements

#### Header with Logo (All Slides)

```html
<!-- Logo and Title Header -->
<div style="position: absolute; left: 20pt; top: 20pt; display: flex; align-items: center; gap: 12pt;">
  <p style="font-size: 28pt; font-weight: bold; color: #C8102E; margin: 0;">A+</p>
  <div style="width: 3pt; height: 40pt; background: #C8102E;"></div>
  <h1 style="font-size: 32pt; font-weight: bold; color: #1A1A1A; margin: 0;">Slide Title Here</h1>
</div>
```

#### Section Number Badge (Top-Right)

```html
<!-- Section Number Badge -->
<div style="position: absolute; right: 0; top: 0; width: 48pt; height: 28pt; background: #C8102E; display: flex; align-items: center; justify-content: center;">
  <p style="color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0;">I.2</p>
</div>
```

---

### Layout 1: Title Slide (`title`)

Opening slide with large centered title and subtitle.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
}
</style>
</head>
<body>
  <h1 style="font-size: 44pt; font-weight: bold; color: #1A1A1A; margin: 0 0 20pt 0; text-align: center;">
    Presentation Title
  </h1>
  <p style="font-size: 24pt; color: #4A4A4A; margin: 0; text-align: center;">
    Subtitle or Date
  </p>
</body>
</html>
```

---

### Layout 2: Overview/Framework (`overview`)

House-shaped framework banner with grid of categorized items.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 20pt; }
.logo { font-size: 28pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 40pt; background: #C8102E; }
.title { font-size: 32pt; font-weight: bold; color: #1A1A1A; margin: 0; }

.framework-title {
  margin: 10pt auto 15pt auto;
  padding: 12pt 40pt;
  background: #FFE5E5;
  border-radius: 8pt 8pt 0 0;
  text-align: center;
}
.framework-title p { font-size: 18pt; font-weight: bold; color: #1A1A1A; margin: 0; }

.content-area { display: flex; flex: 1; padding: 0 20pt 20pt 20pt; gap: 15pt; }

.category-column { width: 100pt; display: flex; flex-direction: column; gap: 10pt; }
.category-box {
  background: #C8102E; padding: 15pt 10pt; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 5pt;
}
.category-box p { color: #FFFFFF; font-size: 12pt; font-weight: bold; margin: 0; }
.category-number { font-size: 16pt; }

.items-grid { flex: 1; display: flex; flex-direction: column; gap: 10pt; }
.item-row { display: flex; gap: 10pt; flex: 1; }
.item-box {
  flex: 1; background: #FFE5E5; border: 2pt solid #C8102E;
  padding: 10pt; display: flex; align-items: center; gap: 8pt;
}
.item-number {
  background: #FFFFFF; border: 1pt solid #C8102E;
  padding: 4pt 8pt; font-size: 11pt; font-weight: bold; color: #C8102E;
}
.item-text { font-size: 11pt; color: #1A1A1A; margin: 0; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Best Practices: Framework Overview</h1>
  </div>

  <div class="framework-title">
    <p>AI-Driven Digital Transformation Framework</p>
  </div>

  <div class="content-area">
    <div class="category-column">
      <div class="category-box">
        <p class="category-number">I</p>
        <p>Customer<br>Segmentation</p>
      </div>
      <div class="category-box">
        <p class="category-number">II</p>
        <p>Product<br>Recommendation</p>
      </div>
    </div>

    <div class="items-grid">
      <div class="item-row">
        <div class="item-box">
          <p class="item-number">I.1</p>
          <p class="item-text">Customer Life Cycle Label System</p>
        </div>
        <div class="item-box">
          <p class="item-number">I.2</p>
          <p class="item-text">Dual-cycle Label System</p>
        </div>
      </div>
      <div class="item-row">
        <div class="item-box">
          <p class="item-number">II.1</p>
          <p class="item-text">Product Recommendation Model</p>
        </div>
        <div class="item-box">
          <p class="item-number">II.2</p>
          <p class="item-text">Product Factor Library</p>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 3: Business Challenges (`challenges`)

Central banner with challenge items arranged around it.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 20pt; }
.logo { font-size: 28pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 40pt; background: #C8102E; }
.title { font-size: 28pt; font-weight: bold; color: #1A1A1A; margin: 0; }

.summary-box {
  margin: 0 30pt 20pt 30pt;
  padding: 15pt 20pt;
  background: #FFF5F5;
  border: 1pt solid #FFB3B3;
  border-radius: 8pt;
  display: flex; align-items: flex-start; gap: 15pt;
}
.summary-icon { font-size: 24pt; color: #C8102E; }
.summary-text { font-size: 12pt; color: #1A1A1A; margin: 0; line-height: 1.5; }

.central-banner {
  margin: 0 auto 20pt auto;
  padding: 12pt 50pt;
  background: #C8102E;
  border-radius: 4pt;
}
.central-banner p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; text-align: center; }

.challenges-container {
  display: flex; justify-content: space-around; padding: 0 30pt;
  flex-wrap: wrap; gap: 20pt;
}
.challenge-item { width: 180pt; text-align: center; }
.challenge-icon {
  width: 50pt; height: 50pt; margin: 0 auto 10pt auto;
  background: #FFE5E5; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.challenge-icon p { font-size: 20pt; color: #C8102E; margin: 0; }
.challenge-title { font-size: 14pt; font-weight: bold; color: #C8102E; margin: 0 0 5pt 0; }
.challenge-desc { font-size: 10pt; color: #4A4A4A; margin: 0; line-height: 1.4; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Market Context & Challenges</h1>
  </div>

  <div class="summary-box">
    <p class="summary-icon">💡</p>
    <p class="summary-text">The market has advanced digital transformation, but competition is intensifying. Traditional operations lack new breakthroughs—a "second growth curve" is urgently needed.</p>
  </div>

  <div class="central-banner">
    <p>Key challenges facing the organization today</p>
  </div>

  <div class="challenges-container">
    <div class="challenge-item">
      <div class="challenge-icon"><p>🏆</p></div>
      <p class="challenge-title">Challenge 1: Competition</p>
      <p class="challenge-desc">Increasing market pressure from new entrants</p>
    </div>
    <div class="challenge-item">
      <div class="challenge-icon"><p>📋</p></div>
      <p class="challenge-title">Challenge 2: Regulation</p>
      <p class="challenge-desc">New compliance requirements affecting operations</p>
    </div>
    <div class="challenge-item">
      <div class="challenge-icon"><p>⚡</p></div>
      <p class="challenge-title">Challenge 3: Technology</p>
      <p class="challenge-desc">Rapid evolution requiring constant adaptation</p>
    </div>
  </div>
</body>
</html>
```

---

### Layout 4: Two Column Comparison (`twoColumnComparison`)

Side-by-side panels with headers and checklists.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 20pt; position: relative; }
.logo { font-size: 28pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 40pt; background: #C8102E; }
.title { font-size: 28pt; font-weight: bold; color: #1A1A1A; margin: 0; }
.section-badge {
  position: absolute; right: 0; top: 0;
  width: 48pt; height: 28pt; background: #C8102E;
  display: flex; align-items: center; justify-content: center;
}
.section-badge p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }

.columns-container { display: flex; gap: 20pt; padding: 0 20pt 20pt 20pt; flex: 1; }

.column { flex: 1; display: flex; flex-direction: column; }
.column-header {
  background: #C8102E; padding: 12pt 15pt; text-align: center;
}
.column-header p { color: #FFFFFF; font-size: 16pt; font-weight: bold; margin: 0; }

.column-subheader {
  background: #FFF5F5; padding: 8pt 15pt; text-align: center;
  border-left: 2pt solid #C8102E; border-right: 2pt solid #C8102E;
}
.column-subheader p { color: #C8102E; font-size: 13pt; font-weight: bold; margin: 0; }

.column-content {
  flex: 1; border: 2pt solid #C8102E; border-top: none;
  background: #FFFFFF; padding: 10pt;
}
.checklist-item {
  padding: 10pt; border-bottom: 1pt dashed #FFB3B3;
}
.checklist-item:last-child { border-bottom: none; }
.check-title { display: flex; align-items: flex-start; gap: 8pt; margin-bottom: 5pt; }
.checkmark { color: #C8102E; font-size: 14pt; font-weight: bold; }
.item-title { font-size: 13pt; font-weight: bold; color: #1A1A1A; margin: 0; }
.item-desc { font-size: 11pt; color: #4A4A4A; margin: 0; padding-left: 22pt; line-height: 1.4; }
.highlight { color: #C8102E; font-weight: bold; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Performance vs Impact Analysis</h1>
    <div class="section-badge"><p>II.1</p></div>
  </div>

  <div class="columns-container">
    <div class="column">
      <div class="column-header"><p>Model Performance</p></div>
      <div class="column-subheader"><p>High-Precision Predictive Capabilities</p></div>
      <div class="column-content">
        <div class="checklist-item">
          <div class="check-title">
            <p class="checkmark">✓</p>
            <p class="item-title">Primary Metric: AUC = 0.78</p>
          </div>
          <p class="item-desc">Indicates strong <span class="highlight">discriminatory power</span>, proving the model's ability to distinguish customers</p>
        </div>
        <div class="checklist-item">
          <div class="check-title">
            <p class="checkmark">✓</p>
            <p class="item-title">Predictive Accuracy</p>
          </div>
          <p class="item-desc">Successfully <span class="highlight">captured complex relationships</span> through correlation coefficients</p>
        </div>
      </div>
    </div>

    <div class="column">
      <div class="column-header"><p>Business Impact</p></div>
      <div class="column-subheader"><p>Driving Efficiency and Excellence</p></div>
      <div class="column-content">
        <div class="checklist-item">
          <div class="check-title">
            <p class="checkmark">✓</p>
            <p class="item-title">Operational Efficiency</p>
          </div>
          <p class="item-desc"><span class="highlight">1 Hour → 3 Minutes (95% Gain)</span> shifting focus to active engagement</p>
        </div>
        <div class="checklist-item">
          <div class="check-title">
            <p class="checkmark">✓</p>
            <p class="item-title">Customer Experience</p>
          </div>
          <p class="item-desc"><span class="highlight">+21% Conversion Rate</span> by presenting relevant products</p>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 5: Methodology/Comparison (`methodology`)

Two-column layout with diagrams for comparing concepts.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 20pt; position: relative; }
.logo { font-size: 28pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 40pt; background: #C8102E; }
.title { font-size: 26pt; font-weight: bold; color: #1A1A1A; margin: 0; }
.section-badge {
  position: absolute; right: 0; top: 0;
  width: 48pt; height: 28pt; background: #C8102E;
  display: flex; align-items: center; justify-content: center;
}
.section-badge p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }

.summary-row {
  display: flex; align-items: flex-start; gap: 15pt;
  margin: 0 20pt 15pt 20pt; padding: 12pt 15pt;
  background: #FFF5F5; border-radius: 4pt;
}
.summary-icon { font-size: 20pt; color: #C8102E; }
.summary-list { margin: 0; padding-left: 20pt; }
.summary-list li { font-size: 11pt; color: #1A1A1A; margin-bottom: 3pt; }

.columns { display: flex; gap: 15pt; padding: 0 20pt 20pt 20pt; flex: 1; }
.column {
  flex: 1; border: 2pt solid #C8102E;
  display: flex; flex-direction: column;
}
.col-header { background: #C8102E; padding: 10pt; text-align: center; }
.col-header p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }
.col-desc { padding: 10pt; background: #FFF5F5; }
.col-desc p { font-size: 10pt; color: #4A4A4A; margin: 0; }
.col-content { flex: 1; padding: 10pt; background: #FFFFFF; }
.diagram-placeholder {
  height: 80pt; background: #FFE5E5; border: 1pt dashed #C8102E;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 10pt;
}
.diagram-placeholder p { color: #C8102E; font-size: 11pt; margin: 0; }
.col-bullets { margin: 0; padding-left: 15pt; }
.col-bullets li { font-size: 10pt; color: #1A1A1A; margin-bottom: 5pt; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Methodology: Dual Cycle Model</h1>
    <div class="section-badge"><p>I.2</p></div>
  </div>

  <div class="summary-row">
    <p class="summary-icon">⚙️</p>
    <ul class="summary-list">
      <li>❖ Customer-Centric Lifecycle: Tie needs to customer's life stages</li>
      <li>❖ Bank-Interaction Lifecycle: Leverage the bank's retail value stream</li>
    </ul>
  </div>

  <div class="columns">
    <div class="column">
      <div class="col-header"><p>Customer's Own Life Cycle</p></div>
      <div class="col-desc">
        <p>► Based on individual life cycle, gain insight into needs at different stages</p>
      </div>
      <div class="col-content">
        <div class="diagram-placeholder" id="left-diagram">
          <p>[Diagram: Life stages chart]</p>
        </div>
        <ul class="col-bullets">
          <li>Students: Study abroad, credit card</li>
          <li>Workplace Novice: Cross-border services</li>
          <li>Senior Customers: Pension services</li>
        </ul>
      </div>
    </div>

    <div class="column">
      <div class="col-header"><p>Life Cycle with Bank</p></div>
      <div class="col-desc">
        <p>► Starting from value flow, mine customer needs based on bank perspective</p>
      </div>
      <div class="col-content">
        <div class="diagram-placeholder" id="right-diagram">
          <p>[Diagram: Bank interaction chart]</p>
        </div>
        <ul class="col-bullets">
          <li>Onboarding Phase: Core basic needs</li>
          <li>Growth Phase: Expanded exploration</li>
          <li>Maturity Phase: Sophisticated needs</li>
        </ul>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 6: Process Flow (`processFlow`)

Flowchart with feature banner and connected nodes.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 20pt; position: relative; }
.logo { font-size: 28pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 40pt; background: #C8102E; }
.title { font-size: 26pt; font-weight: bold; color: #1A1A1A; margin: 0; }
.section-badge {
  position: absolute; right: 0; top: 0;
  width: 48pt; height: 28pt; background: #C8102E;
  display: flex; align-items: center; justify-content: center;
}
.section-badge p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }

.feature-banner {
  display: flex; gap: 10pt; margin: 0 20pt 15pt 20pt;
  padding: 10pt 15pt; background: #FFF5F5; border-radius: 4pt;
}
.feature-item { display: flex; align-items: center; gap: 8pt; }
.feature-check { color: #C8102E; font-size: 14pt; }
.feature-text { font-size: 11pt; color: #C8102E; margin: 0; }

.flow-container {
  flex: 1; padding: 0 20pt 20pt 20pt;
  display: flex; flex-direction: column; align-items: center; gap: 15pt;
}
.flow-row { display: flex; align-items: center; gap: 15pt; }
.flow-node {
  padding: 12pt 20pt; background: #FFE5E5; border: 2pt solid #C8102E;
  border-radius: 6pt; text-align: center; min-width: 100pt;
}
.flow-node p { font-size: 11pt; color: #1A1A1A; margin: 0; }
.flow-node.start, .flow-node.end {
  background: #C8102E;
  border-radius: 20pt;
}
.flow-node.start p, .flow-node.end p { color: #FFFFFF; }
.arrow { font-size: 18pt; color: #C8102E; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Strategy Management: Intelligent Agent</h1>
    <div class="section-badge"><p>IV.4</p></div>
  </div>

  <div class="feature-banner">
    <div class="feature-item">
      <p class="feature-check">✓</p>
      <p class="feature-text">Multi-task intelligent orchestration</p>
    </div>
    <div class="feature-item">
      <p class="feature-check">✓</p>
      <p class="feature-text">Automatic resource calling</p>
    </div>
    <div class="feature-item">
      <p class="feature-check">✓</p>
      <p class="feature-text">Flexible exception handling</p>
    </div>
  </div>

  <div class="flow-container">
    <div class="flow-row">
      <div class="flow-node start"><p>Start</p></div>
    </div>
    <p class="arrow">↓</p>
    <div class="flow-row">
      <div class="flow-node"><p>Step Planning<br>Agent</p></div>
      <p class="arrow">→</p>
      <div class="flow-node"><p>Customer<br>Data</p></div>
      <p class="arrow">→</p>
      <div class="flow-node"><p>Task Assignment<br>Agent</p></div>
    </div>
    <p class="arrow">↓</p>
    <div class="flow-row">
      <div class="flow-node"><p>Marketing Steps<br>& Process</p></div>
      <p class="arrow">→</p>
      <div class="flow-node"><p>Corresponding<br>Tools</p></div>
    </div>
    <p class="arrow">↓</p>
    <div class="flow-row">
      <div class="flow-node end"><p>End</p></div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 7: Horizontal Process (`horizontalProcess`)

Chevron-style left-to-right process with details below.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 20pt; position: relative; }
.logo { font-size: 28pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 40pt; background: #C8102E; }
.title { font-size: 26pt; font-weight: bold; color: #1A1A1A; margin: 0; }
.section-badge {
  position: absolute; right: 0; top: 0;
  width: 48pt; height: 28pt; background: #C8102E;
  display: flex; align-items: center; justify-content: center;
}
.section-badge p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }

.process-header {
  margin: 0 20pt 10pt 20pt;
  padding: 8pt 15pt; background: #C8102E; text-align: center;
}
.process-header p { color: #FFFFFF; font-size: 12pt; font-weight: bold; margin: 0; }

.chevron-row {
  display: flex; margin: 0 20pt 15pt 20pt; gap: 0;
}
.chevron {
  flex: 1; padding: 15pt 10pt 15pt 25pt;
  background: #FFE5E5; position: relative;
  clip-path: polygon(0 0, calc(100% - 15pt) 0, 100% 50%, calc(100% - 15pt) 100%, 0 100%, 15pt 50%);
}
.chevron:first-child {
  clip-path: polygon(0 0, calc(100% - 15pt) 0, 100% 50%, calc(100% - 15pt) 100%, 0 100%);
}
.chevron p { font-size: 10pt; color: #1A1A1A; margin: 0; text-align: center; }

.details-section {
  margin: 0 20pt; padding: 10pt;
  background: #FFF5F5; border: 1pt dashed #C8102E;
}
.details-header { text-align: center; margin-bottom: 10pt; }
.details-header p { font-size: 12pt; font-weight: bold; color: #C8102E; margin: 0; }

.details-grid { display: flex; gap: 10pt; }
.detail-box {
  flex: 1; padding: 10pt; border: 1pt dashed #FFB3B3; background: #FFFFFF;
}
.detail-title { font-size: 11pt; font-weight: bold; color: #C8102E; margin: 0 0 5pt 0; }
.detail-list { margin: 0; padding-left: 12pt; }
.detail-list li { font-size: 9pt; color: #4A4A4A; margin-bottom: 3pt; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Strategy Management: Marketing Process</h1>
    <div class="section-badge"><p>IV.4</p></div>
  </div>

  <div class="process-header">
    <p>Traditional Account Manager Marketing Process</p>
  </div>

  <div class="chevron-row">
    <div class="chevron"><p>Identify<br>Tasks</p></div>
    <div class="chevron"><p>Monitor<br>Situation</p></div>
    <div class="chevron"><p>Collect<br>Information</p></div>
    <div class="chevron"><p>Configure<br>Products</p></div>
    <div class="chevron"><p>Generate<br>Plan</p></div>
    <div class="chevron"><p>Customer<br>Contact</p></div>
  </div>

  <div class="details-section">
    <div class="details-header">
      <p>Changes Productive AI Can Offer</p>
    </div>
    <div class="details-grid">
      <div class="detail-box">
        <p class="detail-title">Business Suggestions</p>
        <ul class="detail-list">
          <li>Customer clue interpretation</li>
          <li>Customer Portrait generation</li>
        </ul>
      </div>
      <div class="detail-box">
        <p class="detail-title">Personalized Assistance</p>
        <ul class="detail-list">
          <li>Auxiliary marketing programs</li>
          <li>Daily Customer Focus</li>
        </ul>
      </div>
      <div class="detail-box">
        <p class="detail-title">Resource Suggestions</p>
        <ul class="detail-list">
          <li>Multi-constraint planning</li>
          <li>Secondary support</li>
        </ul>
      </div>
      <div class="detail-box">
        <p class="detail-title">Multi-Agent</p>
        <ul class="detail-list">
          <li>Agent linkage</li>
          <li>Reusability via API</li>
        </ul>
      </div>
      <div class="detail-box">
        <p class="detail-title">Marketing Review</p>
        <ul class="detail-list">
          <li>Effectiveness feedback</li>
          <li>Interactive review</li>
        </ul>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 8: Numbered Steps (`numberedSteps`)

Sequential numbered steps with arrows.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 20pt; position: relative; }
.logo { font-size: 28pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 40pt; background: #C8102E; }
.title { font-size: 26pt; font-weight: bold; color: #1A1A1A; margin: 0; }
.section-badge {
  position: absolute; right: 0; top: 0;
  width: 48pt; height: 28pt; background: #C8102E;
  display: flex; align-items: center; justify-content: center;
}
.section-badge p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }

.steps-container { flex: 1; padding: 0 30pt 20pt 30pt; }
.steps-row { display: flex; align-items: flex-start; gap: 20pt; margin-bottom: 15pt; }

.step {
  flex: 1; display: flex; gap: 12pt;
  padding: 15pt; background: #FFE5E5; border-radius: 6pt;
}
.step-number {
  width: 35pt; height: 35pt; background: #C8102E; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-number p { color: #FFFFFF; font-size: 16pt; font-weight: bold; margin: 0; }
.step-content { flex: 1; }
.step-title { font-size: 13pt; font-weight: bold; color: #1A1A1A; margin: 0 0 5pt 0; }
.step-desc { font-size: 10pt; color: #4A4A4A; margin: 0; line-height: 1.4; }

.arrow-down {
  display: flex; justify-content: center; margin: 10pt 0;
}
.arrow-down p { font-size: 24pt; color: #C8102E; margin: 0; }

.result-box {
  margin-top: 10pt; padding: 15pt;
  background: #C8102E; border-radius: 6pt; text-align: center;
}
.result-box p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Strategy Automation: Configuration Process</h1>
    <div class="section-badge"><p>III.1</p></div>
  </div>

  <div class="steps-container">
    <div class="steps-row">
      <div class="step">
        <div class="step-number"><p>1</p></div>
        <div class="step-content">
          <p class="step-title">Identify Target Segment</p>
          <p class="step-desc">Circle the target customer segment based on activity preference label</p>
        </div>
      </div>
      <div class="step">
        <div class="step-number"><p>2</p></div>
        <div class="step-content">
          <p class="step-title">Determine Activity Purpose</p>
          <p class="step-desc">Comb the purpose of the activity based on preference threshold</p>
        </div>
      </div>
    </div>

    <div class="arrow-down"><p>↓</p></div>

    <div class="steps-row">
      <div class="step">
        <div class="step-number"><p>3</p></div>
        <div class="step-content">
          <p class="step-title">Locate Activity Information</p>
          <p class="step-desc">Give the activity form that customers like most in the segment</p>
        </div>
      </div>
      <div class="step">
        <div class="step-number"><p>4</p></div>
        <div class="step-content">
          <p class="step-title">Generate Campaign Content</p>
          <p class="step-desc">Automatically generate activities that meet marketing objectives</p>
        </div>
      </div>
    </div>

    <div class="result-box">
      <p>Output: Automatically generated campaigns matching customer preferences</p>
    </div>
  </div>
</body>
</html>
```

---

### Layout 9: Detail Matrix (`detailMatrix`)

Complex table/grid layout for detailed data.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #FFFFFF; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.header { display: flex; align-items: center; gap: 12pt; padding: 15pt 20pt; position: relative; }
.logo { font-size: 24pt; font-weight: bold; color: #C8102E; }
.separator { width: 3pt; height: 35pt; background: #C8102E; }
.title { font-size: 24pt; font-weight: bold; color: #1A1A1A; margin: 0; }
.section-badge {
  position: absolute; right: 0; top: 0;
  width: 48pt; height: 28pt; background: #C8102E;
  display: flex; align-items: center; justify-content: center;
}
.section-badge p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }

.matrix-container { flex: 1; padding: 0 15pt 15pt 15pt; overflow: hidden; }

.matrix-table {
  width: 100%; border-collapse: collapse;
  font-size: 9pt;
}
.matrix-table th {
  background: #C8102E; color: #FFFFFF;
  padding: 8pt 6pt; text-align: center;
  font-weight: bold; border: 1pt solid #8B0000;
}
.matrix-table td {
  padding: 6pt; border: 1pt solid #FFB3B3;
  vertical-align: top;
}
.row-header {
  background: #FFE5E5; font-weight: bold;
  color: #1A1A1A; text-align: center; width: 80pt;
}
.cell-content { color: #4A4A4A; line-height: 1.3; }
.highlight-cell { background: #FFF5F5; }
</style>
</head>
<body>
  <div class="header">
    <p class="logo">A+</p>
    <div class="separator"></div>
    <h1 class="title">Life-Cycle Aware Recommendation Matrix</h1>
    <div class="section-badge"><p>I.3</p></div>
  </div>

  <div class="matrix-container">
    <table class="matrix-table">
      <tr>
        <th></th>
        <th>Onboarding Phase</th>
        <th>Growth Phase</th>
        <th>Maturity Phase</th>
        <th>Decline Phase</th>
      </tr>
      <tr>
        <td class="row-header">Payment & Settlement</td>
        <td class="cell-content">Key matching of rights and interests resources</td>
        <td class="cell-content">Treatment to rights and interests</td>
        <td class="cell-content highlight-cell">Rights and interests to prevent decline</td>
        <td class="cell-content">Low expected return on resources</td>
      </tr>
      <tr>
        <td class="row-header">Investment & Financial</td>
        <td class="cell-content">Customer manager, financial adviser</td>
        <td class="cell-content">Intelligent channel access</td>
        <td class="cell-content">Normal equity allocation</td>
        <td class="cell-content">Intelligent channel access</td>
      </tr>
      <tr>
        <td class="row-header">Credit</td>
        <td class="cell-content">Interest resources, Customer manager</td>
        <td class="cell-content">Treatment to rights</td>
        <td class="cell-content highlight-cell">Normal equity allocation</td>
        <td class="cell-content">Expected return will be low</td>
      </tr>
      <tr>
        <td class="row-header">Channel</td>
        <td class="cell-content">Customer manager, intelligent channel</td>
        <td class="cell-content">Intelligent channel access</td>
        <td class="cell-content">Intelligent channel access</td>
        <td class="cell-content">Intelligent channel access</td>
      </tr>
      <tr>
        <td class="row-header">Service</td>
        <td class="cell-content">Key matching of rights and interests</td>
        <td class="cell-content">Customer manager, intelligent</td>
        <td class="cell-content">Preferential treatment to rights</td>
        <td class="cell-content">Return on resources very low</td>
      </tr>
    </table>
  </div>
</body>
</html>
```

---

## Complete Generation Example

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./.claude/skills/corporate-pptx-generator/scripts/html2pptx');
const fs = require('fs');
const path = require('path');

// Skill folder path
const SKILL_DIR = '.claude/skills/corporate-pptx-generator';

async function generateCorporatePresentation(slidesContent, outputPath, customConfigPath = null) {
  // Load configuration
  const defaultConfigPath = path.join(SKILL_DIR, 'default-pptx-config.json');
  const configPath = customConfigPath || defaultConfigPath;
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

  // Create presentation
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.title = slidesContent.title || 'Corporate Presentation';
  pptx.author = slidesContent.author || 'Generated';

  // Generate HTML files for each slide based on layout type
  for (let i = 0; i < slidesContent.slides.length; i++) {
    const slideData = slidesContent.slides[i];
    const htmlPath = `workspace/slide${i + 1}.html`;

    // Generate HTML based on layout type and slide data
    const html = generateSlideHtml(slideData, config);
    fs.writeFileSync(htmlPath, html);

    // Convert to PowerPoint
    const { slide, placeholders } = await html2pptx(htmlPath, pptx);

    // Add any charts/tables to placeholders if needed
    if (slideData.charts && placeholders.length > 0) {
      for (let j = 0; j < slideData.charts.length && j < placeholders.length; j++) {
        slide.addChart(pptx.charts[slideData.charts[j].type],
          slideData.charts[j].data,
          { ...placeholders[j], ...slideData.charts[j].options }
        );
      }
    }
  }

  // Save presentation
  await pptx.writeFile(outputPath);

  // Generate thumbnail for validation
  // python .claude/skills/corporate-pptx-generator/scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4

  return outputPath;
}

// Example usage
const presentation = {
  title: 'Q4 Business Review',
  author: 'Strategy Team',
  slides: [
    { layout: 'title', title: 'Q4 Business Review', subtitle: 'Digital Transformation Initiative' },
    { layout: 'overview', title: 'Framework Overview', frameworkTitle: 'AI-Driven Transformation', categories: [...] },
    { layout: 'challenges', title: 'Market Challenges', challenges: [...] },
    { layout: 'twoColumnComparison', title: 'Performance vs Impact', sectionNumber: 'II.1', leftPanel: {...}, rightPanel: {...} },
    { layout: 'processFlow', title: 'Implementation Process', sectionNumber: 'IV.4', steps: [...] }
  ]
};

generateCorporatePresentation(presentation, 'quarterly_review.pptx');
```

## Customization

### Creating a Custom Theme

Copy `default-pptx-config.json` and modify:

1. **Colors**: Change hex values in `theme.colors`
2. **Fonts**: Modify font families and sizes in `theme.fonts`
3. **Logo**: Update `logo.text` and colors

### Example Custom Config (Blue Theme)

```json
{
  "theme": {
    "name": "Corporate Blue",
    "colors": {
      "primary": "#1E3A8A",
      "primaryLight": "#DBEAFE",
      "text": {
        "dark": "#1F2937",
        "onPrimary": "#FFFFFF"
      }
    }
  }
}
```

Then pass the custom config path when generating:

```javascript
generateCorporatePresentation(slides, 'output.pptx', 'my-blue-theme.json');
```

## Best Practices

1. **Section Numbering**: Use format "I.1", "II.2" for clear navigation
2. **Content Limits**: Keep bullet points concise (max 5-7 per section)
3. **Visual Hierarchy**: Use headers, sub-headers, and body text appropriately
4. **Color Usage**: Reserve primary purple for headers and emphasis only
5. **White Space**: Maintain adequate margins (0.5" minimum from edges)
6. **Validation**: Always generate thumbnails and inspect before delivery
