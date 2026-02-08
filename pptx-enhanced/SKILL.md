# Enhanced PowerPoint Generator Skill

Generate professional PowerPoint presentations with a modern tech-blueprint visual style featuring deep teal blue headers, warm amber accents, subtle technical grid details, and clean editorial layouts. This enhanced skill encourages generating SVG diagrams for visual content, supports multiple image formats (SVG, PNG, JPG, GIF), and can produce animated GIFs using Manim for instructional visuals.

## Overview

This skill creates PowerPoint presentations using an HTML-to-PPTX workflow with a tech-blueprint theme inspired by modern optical intelligence / autonomous networks presentations. The styling, colors, fonts, and layouts are fully configurable via a JSON configuration file.

**Enhanced capabilities:**
- **SVG Diagram Generation**: Prefer generating SVG diagrams programmatically for flowcharts, architecture diagrams, network topologies, and technical illustrations - then rasterize to PNG for embedding
- **Multi-format Image Support**: Embed SVG (rasterized), PNG, JPG, and GIF images in slides
- **Animated GIF Generation**: Use Manim (Community Edition) to create animated GIFs for process explanations, step-by-step instructions, and visual demonstrations

## When to Use This Skill

Use this skill when the user wants to:
- Create a PowerPoint presentation with a modern, technical, editorial aesthetic
- Generate slides following specific layout templates (comparison, timeline, process flow, etc.)
- Build presentations with clean teal-blue and amber-accent branding
- Include custom diagrams, illustrations, or animated visuals in slides

## Skill Contents

This is a **standalone skill** with all dependencies included:

```
.claude/skills/pptx-enhanced/
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
cd .claude/skills/pptx-generator-enhanced
npm install
npm run install-browsers  # Install Playwright Chromium for HTML rendering
```

### 2. Install Python Dependencies

```bash
pip install -r .claude/skills/pptx-enhanced/requirements.txt
```

### 3. System Requirements

- **LibreOffice** (for PDF conversion in thumbnail generation): `brew install libreoffice` (macOS) or `apt install libreoffice` (Linux)
- **Poppler** (for pdftoppm): `brew install poppler` (macOS) or `apt install poppler-utils` (Linux)

## Configuration

The default configuration is in [`default-pptx-config.json`](default-pptx-config.json) in this skill's folder.

### Color Theme (Default: Tech Blueprint)

| Color Role | Hex Code | Usage |
|------------|----------|-------|
| primary | #0D4F6E | Main accent - headers, borders, section labels |
| primaryDark | #083A52 | Darker emphasis areas |
| primaryLight | #D6E8F0 | Light blue card/box backgrounds |
| secondary | #D4842A | Warm amber - callouts, highlights, accent boxes |
| secondaryLight | #FBF0E0 | Light amber for callout backgrounds |
| accent | #3B9FD6 | Bright blue for diagrams, links, interactive elements |
| background | #F0F4F8 | Main slide background (light cool gray) |
| backgroundAlt | #E8ECF1 | Alternate/section backgrounds |
| cardBackground | #FFFFFF | White card surfaces |
| text.dark | #1A2332 | Main titles and headings |
| text.medium | #4A5568 | Body text |
| text.light | #718096 | Captions, annotations |
| text.onPrimary | #FFFFFF | Text on teal backgrounds |
| text.highlight | #D4842A | Emphasized text (amber) |

### Font Styles

| Style | Size | Weight | Usage |
|-------|------|--------|-------|
| title | 22-24pt | Bold | Slide titles (reduce to 20pt for long titles) |
| subtitle | 10-12pt | Normal | Subtitles, section descriptors |
| sectionHeader | 14-16pt | Bold | Section headers (white on teal) |
| contentHeader | 10-12pt | Bold | Content headers (teal text), card titles |
| body | 9-10pt | Normal | Body text (**minimum 9pt for readability**) |
| caption | 9pt | Normal | Small annotations (**never below 8.5pt**) |
| label | 10pt | Bold | Labels, tags, uppercase headers |
| mono | 10pt | Normal | Technical/code annotations (Courier New) |

> ⚠️ **Critical**: Never use text smaller than 8.5pt in any slide. For Chinese text, the effective minimum is 9pt because CJK characters render wider and need more space. Text at 7-8pt is unreadable when projected.

## Workflow

### Step 1: Load Configuration

```javascript
const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, 'default-pptx-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
```

### Step 2: Create HTML Slides

For each slide, create an HTML file following the tech-blueprint design patterns below. See [`html2pptx.md`](html2pptx.md) for detailed HTML creation rules.

**CRITICAL HTML Rules**:
- Body dimensions: `width: 720pt; height: 405pt` for 16:9
- ALL text MUST be in `<p>`, `<h1>`-`<h6>`, `<ul>`, or `<ol>` tags
- Use web-safe fonts only: Arial, Helvetica, Courier New, Georgia, Verdana
- Backgrounds/borders/shadows only work on `<div>` elements
- NEVER use CSS gradients - rasterize as PNG first

### Step 3: Convert to PowerPoint

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./.claude/skills/pptx-enhanced/scripts/html2pptx');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';

const { slide, placeholders } = await html2pptx('slide1.html', pptx);

await pptx.writeFile('presentation.pptx');
```

### Step 4: Validate Output

```bash
python .claude/skills/pptx-enhanced/scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```

---

## Slide Layout Templates

### Design System: Common Elements

#### Slide Background

All slides use a light cool-gray background with an optional subtle technical grid decoration in the corners for depth.

```html
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
  position: relative;
}
</style>
```

#### Title Area (Most Content Slides)

Bold dark title with an optional lighter subtitle below. A thin teal horizontal line separates the title from content.

```html
<!-- Title Area -->
<div class="title-area" style="padding: 14pt 30pt 4pt 30pt;">
  <h1 style="font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0;">
    Slide Title Here
  </h1>
  <p style="font-size: 10pt; color: #4A5568; margin: 3pt 0 0 0;">
    Subtitle or descriptor text
  </p>
</div>
<div style="margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E;"></div>
```

> 📐 **Spacing Note**: Title area uses 14pt top padding (not 25pt) to maximize content space. The title+subtitle+divider should occupy ~40-45pt total height.

#### Bottom Callout Bar

An amber/orange or teal callout bar at the bottom of the slide for key takeaways or application notes.

```html
<!-- Bottom Callout Bar (Amber) -->
<div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #D4842A; border-radius: 4pt; padding: 7pt 15pt; display: flex; align-items: center; gap: 10pt;">
  <p style="font-size: 11pt; font-weight: bold; color: #FFFFFF; margin: 0;">KEY TAKEAWAY</p>
  <p style="font-size: 9pt; color: #FFFFFF; margin: 0;">Summary text describing the main insight from this slide.</p>
</div>

<!-- Bottom Callout Bar (Teal) -->
<div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #0D4F6E; border-radius: 4pt; padding: 7pt 15pt; display: flex; align-items: center; gap: 10pt;">
  <p style="font-size: 11pt; font-weight: bold; color: #D4842A; margin: 0;">LABEL</p>
  <p style="font-size: 9pt; color: #FFFFFF; margin: 0;">Description text here.</p>
</div>
```

> 📐 **Spacing Note**: Bottom bar at `bottom: 12pt` with `padding: 7pt 15pt` occupies ~35pt of height. Content above must end at least 50pt from the slide bottom (y=355pt in 405pt slide). Use `bottom: 10-12pt` (not 15pt) to maximize available space.

#### Section Label (Uppercase)

Used for column headers and category labels.

```html
<p style="font-size: 12pt; font-weight: bold; color: #0D4F6E; text-transform: uppercase; letter-spacing: 1pt; margin: 0;">
  THE SECTION LABEL
</p>
```

---

### Layout 1: Title Slide (`title`)

Hero opening slide with large bold title on the left and subtitle below.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column; justify-content: center;
}
</style>
</head>
<body>
  <h1 style="font-size: 36pt; font-weight: bold; color: #1A2332; margin: 0 0 8pt 50pt; line-height: 1.2;">
    From Connectivity<br>to Cognition
  </h1>
  <p style="font-size: 18pt; font-weight: bold; color: #0D4F6E; margin: 0 0 20pt 50pt;">
    Empowering Networks with Agentic AI
  </p>
  <div style="margin: 0 50pt; height: 2pt; background: #0D4F6E; width: 200pt;"></div>
  <p style="font-size: 10pt; color: #718096; margin: 15pt 0 0 50pt;">
    STRATEGY: 2026 COMMERCIAL TEAM
  </p>
  <p style="font-size: 10pt; color: #718096; margin: 3pt 0 0 50pt;">
    DOMAIN: OPTICAL NETWORKS
  </p>
</body>
</html>
```

---

### Layout 2: Two Column Split (`twoColumnSplit`)

Side-by-side sections with labeled headers. Each column has an uppercase section label, content, key-value pairs, and a status line.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.subtitle { font-size: 10pt; color: #4A5568; margin: 3pt 0 0 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.columns { display: flex; gap: 10pt; padding: 6pt 30pt 0 30pt; flex: 1; }
.column { flex: 1; }
.col-label { font-size: 10pt; font-weight: bold; color: #0D4F6E; text-transform: uppercase; letter-spacing: 1pt; margin: 0 0 5pt 0; }
.col-sublabel { font-size: 9pt; color: #718096; margin: 0 0 8pt 0; }

.card {
  background: #FFFFFF; border-radius: 6pt; padding: 6pt 8pt;
  border: 1pt solid #CBD5E0;
}
.kv-row { display: flex; gap: 8pt; margin-bottom: 4pt; }
.kv-label { font-size: 9pt; font-weight: bold; color: #0D4F6E; margin: 0; width: 60pt; }
.kv-value { font-size: 9pt; color: #4A5568; margin: 0; }
.status-line { font-size: 9pt; font-weight: bold; margin: 5pt 0 0 0; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">The Nervous System of the Digital World</h1>
    <p class="subtitle">Current State: Visible but Reactive</p>
  </div>
  <div class="divider"></div>

  <div class="columns">
    <div class="column">
      <p class="col-label">THE ARTERIES | NCE-T</p>
      <div class="card">
        <div class="kv-row">
          <p class="kv-label">Domain:</p>
          <p class="kv-value">Transport (WDM/OTN)</p>
        </div>
        <div class="kv-row">
          <p class="kv-label">Role:</p>
          <p class="kv-value">High Bandwidth, Low Latency</p>
        </div>
        <div class="kv-row">
          <p class="kv-label">Key Value:</p>
          <p class="kv-value">Latency Maps &amp; Bandwidth on Demand</p>
        </div>
        <p class="status-line" style="color: #0D4F6E;">Status: The Highway</p>
      </div>
    </div>

    <div class="column">
      <p class="col-label">THE CAPILLARIES | NCE-FAN</p>
      <div class="card">
        <div class="kv-row">
          <p class="kv-label">Domain:</p>
          <p class="kv-value">Access (FTTH/FTTR)</p>
        </div>
        <div class="kv-row">
          <p class="kv-label">Role:</p>
          <p class="kv-value">User Experience, Wi-Fi Quality</p>
        </div>
        <div class="kv-row">
          <p class="kv-label">Key Value:</p>
          <p class="kv-value">Remote Wi-Fi Tuning &amp; Churn Prediction</p>
        </div>
        <p class="status-line" style="color: #0D4F6E;">Status: The Last Mile</p>
      </div>
    </div>
  </div>

  <!-- Bottom Callout -->
  <div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #FBF0E0; border: 1pt solid #D4842A; border-radius: 4pt; padding: 7pt 15pt; display: flex; align-items: center; gap: 10pt;">
    <p style="font-size: 11pt; font-weight: bold; color: #D4842A; margin: 0;">THE GAP:</p>
    <p style="font-size: 9pt; color: #1A2332; margin: 0;">Current automation is "Reflexive." It manages configuration and alarms but lacks reasoning.</p>
  </div>
</body>
</html>
```

---

### Layout 3: Timeline / Evolution (`timeline`)

Horizontal timeline showing progression across eras or phases.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.timeline { display: flex; gap: 10pt; padding: 8pt 30pt 0 30pt; flex: 1; align-items: flex-start; }
.phase { flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; }

.phase-card {
  width: 92%; background: #FFFFFF; border-radius: 6pt;
  border: 2pt solid #CBD5E0; padding: 8pt; text-align: center;
}
.phase-card.highlighted {
  border-color: #D4842A; background: #FBF0E0;
}
.phase-date { font-size: 12pt; font-weight: bold; color: #0D4F6E; margin: 0 0 8pt 0; }
.phase-title { font-size: 13pt; font-weight: bold; color: #1A2332; margin: 0 0 6pt 0; }
.phase-desc { font-size: 10pt; color: #4A5568; margin: 0; line-height: 1.4; }
.phase-label { font-size: 9pt; color: #718096; margin: 6pt 0 0 0; }

.arrow-connector {
  position: absolute; right: -12pt; top: 50pt;
  font-size: 16pt; color: #0D4F6E;
}
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">Beyond Generation: The Rise of the Agent</h1>
  </div>
  <div class="divider"></div>

  <div class="timeline">
    <div class="phase">
      <div class="phase-card">
        <p class="phase-date">2023: GenAI</p>
        <p class="phase-title">Content Creation</p>
        <p class="phase-desc">The Chatbot writes the email.</p>
        <p class="phase-label">Passive</p>
      </div>
      <p class="arrow-connector">&#8594;</p>
    </div>

    <div class="phase">
      <div class="phase-card">
        <p class="phase-date">2024-2025: Copilots</p>
        <p class="phase-title">Assistance</p>
        <p class="phase-desc">The human prompts, the bot suggests.</p>
        <p class="phase-label">Hybrid</p>
      </div>
      <p class="arrow-connector">&#8594;</p>
    </div>

    <div class="phase">
      <div class="phase-card highlighted">
        <p class="phase-date" style="color: #D4842A;">2026: Agentic AI</p>
        <p class="phase-title">Decision &amp; Action</p>
        <p class="phase-desc">The Agent sends the email, updates the CRM, and schedules the follow-up.</p>
        <p style="font-size: 10pt; font-weight: bold; color: #D4842A; margin: 6pt 0 0 0;">Perceive &gt; Reason &gt; Act &gt; Learn</p>
      </div>
    </div>
  </div>

  <!-- Bottom stat bar -->
  <div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; display: flex; gap: 15pt;">
    <div style="flex: 1; background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 4pt; padding: 10pt; text-align: center;">
      <p style="font-size: 18pt; font-weight: bold; color: #0D4F6E; margin: 0;">$4.35B</p>
      <p style="font-size: 9pt; color: #718096; margin: 3pt 0 0 0;">(2025)</p>
    </div>
    <div style="flex: 1; background: #D4842A; border-radius: 4pt; padding: 10pt; text-align: center;">
      <p style="font-size: 14pt; font-weight: bold; color: #FFFFFF; margin: 0;">327% Enterprise Adoption Growth</p>
    </div>
    <div style="flex: 1; background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 4pt; padding: 10pt; text-align: center;">
      <p style="font-size: 18pt; font-weight: bold; color: #0D4F6E; margin: 0;">$103B</p>
      <p style="font-size: 9pt; color: #718096; margin: 3pt 0 0 0;">(2034)</p>
    </div>
  </div>
</body>
</html>
```

---

### Layout 4: Old vs New Comparison (`comparison`)

Two-column before/after comparison with contrasting headers.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.subtitle { font-size: 10pt; color: #4A5568; margin: 5pt 0 0 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.columns { display: flex; gap: 20pt; padding: 15pt 30pt; flex: 1; }
.column { flex: 1; display: flex; flex-direction: column; }

.col-header { padding: 7pt 15pt; border-radius: 6pt 6pt 0 0; }
.col-header.old { background: #E8ECF1; }
.col-header.new { background: #0D4F6E; }
.col-header p { font-size: 14pt; font-weight: bold; margin: 0; }
.col-header.old p { color: #4A5568; }
.col-header.new p { color: #FFFFFF; }

.col-body {
  flex: 1; background: #FFFFFF; border: 1pt solid #CBD5E0;
  border-top: none; border-radius: 0 0 6pt 6pt; padding: 12pt;
}
.col-body p { font-size: 11pt; color: #4A5568; margin: 0 0 6pt 0; line-height: 1.4; }
.col-body .highlight { color: #D4842A; font-weight: bold; }

.diagram-area {
  height: 70pt; background: #F0F4F8; border: 1pt dashed #CBD5E0;
  border-radius: 4pt; margin-bottom: 10pt;
  display: flex; align-items: center; justify-content: center;
}
.diagram-area p { font-size: 10pt; color: #718096; margin: 0; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">The Parallel Revolution: Why AI Got Smart So Fast</h1>
    <p class="subtitle">From Sequential Processing to Attention Mechanisms</p>
  </div>
  <div class="divider"></div>

  <div class="columns">
    <div class="column">
      <div class="col-header old">
        <p>Old Way: RNN / LSTM</p>
      </div>
      <div class="col-body">
        <div class="diagram-area">
          <p>[Diagram: Sequential processing]</p>
        </div>
        <p>Sequential Processing. Like reading through a straw.</p>
        <p>"Vanishing Gradient" means forgetting the start of the sentence.</p>
        <p style="font-weight: bold; color: #0D4F6E;">Context Window: Limited</p>
      </div>
    </div>

    <div class="column">
      <div class="col-header new">
        <p>New Way: Transformers</p>
      </div>
      <div class="col-body">
        <div class="diagram-area">
          <p>[Diagram: Parallel attention grid]</p>
        </div>
        <p>Parallel Processing. "Attention is All You Need".</p>
        <p>Seeing the whole page at once. Context is maintained globally.</p>
        <p style="font-weight: bold; color: #D4842A;">Context Window: Global (e.g., 32K tokens)</p>
      </div>
    </div>
  </div>

  <!-- Bottom Callout -->
  <div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #0D4F6E; border-radius: 4pt; padding: 7pt 15pt; display: flex; align-items: center; gap: 10pt;">
    <p style="font-size: 12pt; font-weight: bold; color: #D4842A; margin: 0;">BUSINESS IMPACT</p>
    <p style="font-size: 11pt; color: #FFFFFF; margin: 0;">Transformers allow NCE to ingest massive, non-sequential optical network logs and complex topologies that previous architectures could not process.</p>
  </div>
</body>
</html>
```

---

### Layout 5: Funnel / Lifecycle (`funnel`)

Vertical funnel showing transformation through numbered stages.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.funnel-container { flex: 1; display: flex; padding: 15pt 30pt 0 30pt; }
.funnel-visual { width: 250pt; display: flex; flex-direction: column; align-items: center; gap: 0; }

.funnel-stage {
  display: flex; align-items: center; gap: 15pt; width: 100%;
  padding: 10pt 0;
}
.stage-number {
  width: 28pt; height: 28pt; background: #0D4F6E; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stage-number p { color: #FFFFFF; font-size: 14pt; font-weight: bold; margin: 0; }
.stage-content { flex: 1; }
.stage-title { font-size: 13pt; font-weight: bold; color: #1A2332; margin: 0; }
.stage-desc { font-size: 10pt; color: #4A5568; margin: 3pt 0 0 0; }
.stage-label { font-size: 9pt; color: #718096; margin: 3pt 0 0 0; }

.funnel-arrow { text-align: center; }
.funnel-arrow p { font-size: 16pt; color: #0D4F6E; margin: 0; }

.funnel-description {
  flex: 1; padding-left: 30pt; display: flex; flex-direction: column; justify-content: center;
}
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">Training the Brain: The LLM Lifecycle</h1>
  </div>
  <div class="divider"></div>

  <div class="funnel-container">
    <div class="funnel-visual">
      <div class="funnel-stage">
        <div class="stage-number"><p>1</p></div>
        <div class="stage-content">
          <p class="stage-title">Pre-training (Generalist)</p>
          <p class="stage-desc">Reading the internet. Learns grammar and reasoning.</p>
          <p class="stage-label">Foundation Model</p>
        </div>
      </div>
      <div class="funnel-arrow"><p>&#8595;</p></div>
      <div class="funnel-stage">
        <div class="stage-number"><p>2</p></div>
        <div class="stage-content">
          <p class="stage-title">Fine-Tuning (Specialist)</p>
          <p class="stage-desc">Domain Adaptation (SFT/PEFT). Learns "WDM", "OTDR".</p>
          <p class="stage-label">Specialist Model</p>
        </div>
      </div>
      <div class="funnel-arrow"><p>&#8595;</p></div>
      <div class="funnel-stage">
        <div class="stage-number"><p>3</p></div>
        <div class="stage-content">
          <p class="stage-title">RLHF (Professional)</p>
          <p class="stage-desc">Alignment &amp; Safety. Learns values, safety, and business intent.</p>
          <p class="stage-label" style="color: #D4842A; font-weight: bold;">Aligned Product</p>
        </div>
      </div>
    </div>

    <div class="funnel-description">
      <div style="background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 6pt; padding: 15pt;">
        <p style="font-size: 12pt; color: #4A5568; margin: 0; line-height: 1.5;">Each stage narrows the model's capabilities from broad general knowledge to specialized, safe, domain-specific expertise.</p>
      </div>
    </div>
  </div>

  <!-- Bottom Callout -->
  <div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #FBF0E0; border: 2pt solid #D4842A; border-radius: 4pt; padding: 7pt 15pt; text-align: center;">
    <p style="font-size: 12pt; color: #1A2332; margin: 0;">We don't just need a <span style="font-weight: bold;">smart model</span>; we need an <span style="font-weight: bold; color: #D4842A;">ALIGNED</span> model safe for <span style="font-weight: bold; text-decoration: underline;">critical infrastructure</span>.</p>
  </div>
</body>
</html>
```

---

### Layout 6: Central Hub Diagram (`centralHub`)

Central element with radiating connected satellite components.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.hub-layout { flex: 1; display: flex; padding: 15pt 30pt; position: relative; }

.satellite {
  width: 180pt; display: flex; flex-direction: column;
}
.sat-card {
  background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 6pt; padding: 12pt;
}
.sat-title { font-size: 13pt; font-weight: bold; color: #0D4F6E; margin: 0 0 5pt 0; }
.sat-desc { font-size: 10pt; color: #4A5568; margin: 0; line-height: 1.4; }

.center-hub {
  flex: 1; display: flex; align-items: center; justify-content: center;
}
.hub-circle {
  width: 130pt; height: 130pt; background: #0D4F6E; border-radius: 50%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.hub-label { font-size: 10pt; color: #FFFFFF; text-transform: uppercase; letter-spacing: 1pt; margin: 0; }
.hub-title { font-size: 14pt; font-weight: bold; color: #FFFFFF; margin: 3pt 0; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">Giving the Brain Hands: RAG, Tools, and Memory</h1>
  </div>
  <div class="divider"></div>

  <div class="hub-layout">
    <div class="satellite" style="justify-content: flex-start; padding-top: 30pt;">
      <div class="sat-card">
        <p class="sat-title">RAG (Retrieval-Augmented Generation)</p>
        <p class="sat-desc">The Open Book Exam. Fetches real-time manual data/logs to answer accurate queries. Reduces hallucinations.</p>
      </div>
    </div>

    <div class="center-hub">
      <div class="hub-circle">
        <p class="hub-label">THE</p>
        <p class="hub-title">AGENTIC CORE</p>
      </div>
    </div>

    <div class="satellite" style="justify-content: flex-start; padding-top: 30pt;">
      <div class="sat-card">
        <p class="sat-title">Tool Use</p>
        <p class="sat-desc">Action Execution. Calls APIs (e.g., 'get_optical_power()'). The ability to interact with the physical network.</p>
      </div>
    </div>
  </div>

  <!-- Bottom element -->
  <div style="position: absolute; bottom: 45pt; left: 50%; transform: translateX(-50%); width: 200pt;">
    <div class="sat-card" style="background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 6pt; padding: 12pt; text-align: center;">
      <p class="sat-title" style="text-align: center;">Memory</p>
      <p class="sat-desc" style="text-align: center;">Context Retention. Remembering past faults to predict future ones across long troubleshooting sessions.</p>
    </div>
  </div>

  <!-- Bottom Callout -->
  <div style="position: absolute; bottom: 10pt; left: 30pt; right: 30pt; background: #0D4F6E; border-radius: 4pt; padding: 8pt 15pt; display: flex; align-items: center; gap: 10pt;">
    <p style="font-size: 11pt; font-weight: bold; color: #D4842A; margin: 0;">NCE APPLICATION:</p>
    <p style="font-size: 10pt; color: #FFFFFF; margin: 0;">An agent doesn't just guess why a fiber broke; it retrieves the OTDR curve (RAG) and dispatches a ticket (Tool Use).</p>
  </div>
</body>
</html>
```

---

### Layout 7: Quadrant / Matrix Chart (`quadrant`)

2x2 quadrant chart with a highlighted target zone and strategy panel.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.content-area { display: flex; gap: 20pt; padding: 15pt 30pt; flex: 1; }

.quadrant-panel { flex: 1; position: relative; }
.quadrant-box {
  width: 100%; height: 100%; border: 2pt solid #CBD5E0; border-radius: 6pt;
  display: flex; flex-wrap: wrap; overflow: hidden;
}
.q-cell { width: 50%; height: 50%; padding: 12pt; }
.q-cell.highlight { background: #FBF0E0; border: 2pt solid #D4842A; border-radius: 6pt; }
.q-cell p { margin: 0; }
.q-cell .q-title { font-size: 11pt; font-weight: bold; color: #D4842A; }
.q-cell .q-desc { font-size: 9pt; color: #4A5568; margin-top: 4pt; line-height: 1.3; }
.q-cell.bottom-right .q-title { color: #0D4F6E; }

.axis-label-x { font-size: 9pt; color: #718096; margin: 5pt 0 0 0; text-align: center; }
.axis-label-y { font-size: 9pt; color: #718096; margin: 0; }

.strategy-panel { width: 220pt; }
.strategy-card {
  background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 6pt; padding: 15pt;
}
.strategy-header { font-size: 12pt; font-weight: bold; color: #0D4F6E; text-transform: uppercase; margin: 0 0 10pt 0; }
.strategy-item { margin-bottom: 10pt; }
.strategy-label { font-size: 11pt; font-weight: bold; color: #D4842A; margin: 0 0 3pt 0; }
.strategy-desc { font-size: 10pt; color: #4A5568; margin: 0; line-height: 1.4; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">The McKinsey Lesson: Focus on Workflow, Not the Bot</h1>
  </div>
  <div class="divider"></div>

  <div class="content-area">
    <div class="quadrant-panel">
      <p class="axis-label-y" style="position: absolute; left: -5pt; top: 50%; transform: rotate(-90deg) translateX(-50%); transform-origin: left top;">Process Variance &#8594;</p>
      <div class="quadrant-box">
        <div class="q-cell highlight">
          <p class="q-title">AGENTIC AI TARGET ZONE</p>
          <p class="q-desc">Complex Root Cause Analysis. Customer Complaint Resolution. Requires reasoning and context.</p>
        </div>
        <div class="q-cell">
          <p class="q-desc" style="color: #718096;">Low variance, high complexity tasks</p>
        </div>
        <div class="q-cell">
          <p class="q-desc" style="color: #718096;">Low value automation candidates</p>
        </div>
        <div class="q-cell bottom-right">
          <p class="q-title">Rules-Based Automation (RPA)</p>
          <p class="q-desc">Investor onboarding, regulatory disclosures. Predictable logic.</p>
        </div>
      </div>
      <p class="axis-label-x">Process Standardization &#8594;</p>
    </div>

    <div class="strategy-panel">
      <div class="strategy-card">
        <p class="strategy-header">THE STRATEGY: HUMAN-IN-THE-LOOP</p>
        <div class="strategy-item">
          <p class="strategy-label">The Trap:</p>
          <p class="strategy-desc">Building cool agents that don't solve problems.</p>
        </div>
        <div class="strategy-item">
          <p class="strategy-label">The Fix:</p>
          <p class="strategy-desc">Agents act as Orchestrators for high-variance tasks. Humans shift from 'Doing' to 'Reviewing'.</p>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 8: Horizontal Process Flow (`horizontalProcess`)

Left-to-right sequential process with labeled stages and a bottom callout.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 26pt; font-weight: bold; color: #1A2332; margin: 0; }
.subtitle { font-size: 10pt; color: #4A5568; margin: 5pt 0 0 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.process-row { display: flex; gap: 0; padding: 20pt 30pt; align-items: flex-start; }
.process-step { flex: 1; display: flex; flex-direction: column; align-items: center; text-align: center; position: relative; }

.step-header {
  font-size: 12pt; font-weight: bold; text-transform: uppercase;
  letter-spacing: 0.5pt; margin: 0 0 8pt 0;
}
.step-card {
  width: 90%; background: #FFFFFF; border-radius: 6pt;
  border: 1pt solid #CBD5E0; padding: 10pt;
}
.step-icon {
  width: 40pt; height: 40pt; background: #D6E8F0;
  border-radius: 50%; margin: 0 auto 8pt auto;
  display: flex; align-items: center; justify-content: center;
}
.step-icon p { font-size: 16pt; color: #0D4F6E; margin: 0; }
.step-desc { font-size: 10pt; color: #4A5568; margin: 0; line-height: 1.3; }
.step-label { font-size: 9pt; color: #718096; margin: 5pt 0 0 0; }

.step-arrow {
  position: absolute; right: -8pt; top: 60pt;
  font-size: 14pt; color: #0D4F6E;
}
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">Transforming Transport: From 'Pipe' to 'Service'</h1>
    <p class="subtitle">Scenario: The Autonomous Highway for Finance</p>
  </div>
  <div class="divider"></div>

  <div class="process-row">
    <div class="process-step">
      <p class="step-header" style="color: #0D4F6E;">PERCEIVE</p>
      <div class="step-card">
        <div class="step-icon"><p>&#128065;</p></div>
        <p class="step-desc">Bank client requests immediate low-latency line.</p>
      </div>
      <p class="step-arrow">&#8594;</p>
    </div>

    <div class="process-step">
      <p class="step-header" style="color: #0D4F6E;">REASON</p>
      <div class="step-card">
        <div class="step-icon"><p>&#129504;</p></div>
        <p class="step-desc">Agent consults Latency Map (RAG). Calculates path for &lt;1ms latency guarantee.</p>
      </div>
      <p class="step-arrow">&#8594;</p>
    </div>

    <div class="process-step">
      <p class="step-header" style="color: #D4842A;">ACT</p>
      <div class="step-card" style="border-color: #D4842A;">
        <div class="step-icon" style="background: #FBF0E0;"><p>&#9889;</p></div>
        <p class="step-desc">Agent triggers BoD (Bandwidth on Demand) API to auto-provision path.</p>
      </div>
      <p class="step-arrow">&#8594;</p>
    </div>

    <div class="process-step">
      <p class="step-header" style="color: #D4842A;">VALUE</p>
      <div class="step-card" style="border-color: #D4842A;">
        <div class="step-icon" style="background: #FBF0E0;"><p>&#127942;</p></div>
        <p class="step-desc">Sold 'Gold Plated' Service. 15ms guaranteed vs generic connectivity.</p>
      </div>
    </div>
  </div>

  <!-- Bottom Callout -->
  <div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #D4842A; border-radius: 4pt; padding: 7pt 15pt; display: flex; align-items: center; gap: 10pt;">
    <p style="font-size: 12pt; font-weight: bold; color: #FFFFFF; margin: 0;">OPTICAL DOCTOR:</p>
    <p style="font-size: 11pt; color: #FFFFFF; margin: 0;">Agent detects signal degradation at 15.3km and dispatches repair before client notices.</p>
  </div>
</body>
</html>
```

---

### Layout 9: Problem / Solution (`problemSolution`)

Left panel with problem, right panel with numbered solution steps.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 26pt; font-weight: bold; color: #1A2332; margin: 0; }
.subtitle { font-size: 10pt; color: #4A5568; margin: 5pt 0 0 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.content { display: flex; gap: 20pt; padding: 15pt 30pt; flex: 1; }

.problem-panel { flex: 1; }
.panel-label { font-size: 12pt; font-weight: bold; color: #0D4F6E; text-transform: uppercase; letter-spacing: 1pt; margin: 0 0 10pt 0; }
.problem-card { background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 6pt; padding: 15pt; }
.problem-text { font-size: 11pt; color: #4A5568; margin: 0 0 10pt 0; line-height: 1.5; }
.diagram-area {
  height: 80pt; background: #F0F4F8; border: 1pt dashed #CBD5E0;
  border-radius: 4pt; display: flex; align-items: center; justify-content: center;
}
.diagram-area p { font-size: 10pt; color: #718096; margin: 0; }

.solution-panel { flex: 1; }
.solution-step { display: flex; gap: 10pt; margin-bottom: 12pt; }
.step-num {
  width: 24pt; height: 24pt; background: #0D4F6E; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-num p { color: #FFFFFF; font-size: 11pt; font-weight: bold; margin: 0; }
.step-content { flex: 1; }
.step-title { font-size: 12pt; font-weight: bold; color: #1A2332; margin: 0 0 3pt 0; }
.step-desc { font-size: 10pt; color: #4A5568; margin: 0; line-height: 1.4; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">Transforming Access: From 'Complaint' to 'Care'</h1>
    <p class="subtitle">Solving the 'Silent Sufferer' Problem</p>
  </div>
  <div class="divider"></div>

  <div class="content">
    <div class="problem-panel">
      <p class="panel-label">THE PROBLEM</p>
      <div class="problem-card">
        <p class="problem-text">User experience is poor, but no complaint filed yet. Risk of churn is high.</p>
        <div class="diagram-area">
          <p>[Visual: User in poor-quality network]</p>
        </div>
      </div>
    </div>

    <div class="solution-panel">
      <p class="panel-label">THE AGENTIC SOLUTION</p>
      <div class="solution-step">
        <div class="step-num"><p>1</p></div>
        <div class="step-content">
          <p class="step-title">ANALYZE</p>
          <p class="step-desc">Agent reviews telemetry. Identifies 'Quality Poor' users (high attenuation).</p>
        </div>
      </div>
      <div class="solution-step">
        <div class="step-num"><p>2</p></div>
        <div class="step-content">
          <p class="step-title">DIAGNOSE</p>
          <p class="step-desc">Agent distinguishes neighbor interference vs. router placement.</p>
        </div>
      </div>
      <div class="solution-step">
        <div class="step-num"><p>3</p></div>
        <div class="step-content">
          <p class="step-title">ACT</p>
          <p class="step-desc">Auto-optimize channel OR prompt proactive care call: "Move router 2ft left".</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom Value Bar -->
  <div style="position: absolute; bottom: 12pt; left: 30pt; right: 30pt; background: #D4842A; border-radius: 4pt; padding: 7pt 15pt; display: flex; align-items: center; gap: 10pt;">
    <p style="font-size: 12pt; font-weight: bold; color: #FFFFFF; margin: 0;">VALUE DELIVERED</p>
    <p style="font-size: 11pt; color: #FFFFFF; margin: 0;">30-40% reduction in on-site truck rolls. Zero-touch optimization.</p>
  </div>
</body>
</html>
```

---

### Layout 10: Business Model Comparison (`businessModel`)

Old model vs new model with a strategic moat callout.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.models-area { display: flex; gap: 20pt; padding: 15pt 30pt; flex: 1; }

.model-stack { flex: 1; display: flex; flex-direction: column; gap: 8pt; }
.model-label { font-size: 12pt; font-weight: bold; color: #0D4F6E; text-transform: uppercase; margin: 0 0 5pt 0; }

.model-card {
  background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 6pt; padding: 12pt;
}
.model-card.old { border-left: 4pt solid #CBD5E0; }
.model-card.new { border-left: 4pt solid #D4842A; }
.model-heading { font-size: 14pt; font-weight: bold; color: #1A2332; margin: 0 0 5pt 0; }
.model-quote { font-size: 11pt; color: #4A5568; margin: 0 0 5pt 0; font-style: italic; }
.model-detail { font-size: 10pt; color: #4A5568; margin: 0; }

.moat-panel { width: 200pt; }
.moat-card {
  background: #D4842A; border-radius: 6pt; padding: 15pt;
}
.moat-title { font-size: 12pt; font-weight: bold; color: #FFFFFF; text-transform: uppercase; margin: 0 0 8pt 0; }
.moat-desc { font-size: 10pt; color: #FFFFFF; margin: 0; line-height: 1.4; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">Changing the Business Model: Outcome-as-a-Service</h1>
  </div>
  <div class="divider"></div>

  <div class="models-area">
    <div class="model-stack">
      <p class="model-label">OLD MODEL</p>
      <div class="model-card old">
        <p class="model-heading">Selling Network Management</p>
        <p class="model-quote">"You can see your network"</p>
        <p class="model-detail">License Fees</p>
      </div>

      <p class="model-label" style="margin-top: 10pt;">NEW MODEL</p>
      <div class="model-card new">
        <p class="model-heading">Selling Guaranteed Uptime &amp; Autonomous Optimization</p>
        <p class="model-quote">"We run your network"</p>
        <p class="model-detail">Resolved Tickets / SLAs</p>
      </div>
    </div>

    <div class="moat-panel">
      <div class="moat-card">
        <p class="moat-title">STRATEGIC MOAT</p>
        <p class="moat-desc">Generic LLMs lack proprietary data. Fine-tuning on our optical logs creates a barrier to entry competitors cannot cross.</p>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 11: Supply Chain / Pipeline (`supplyChain`)

Chevron-style pipeline with sequential stages and details below each.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; text-align: center; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.pipeline { display: flex; gap: 0; padding: 8pt 30pt 0 30pt; }
.pipe-stage { flex: 1; display: flex; flex-direction: column; align-items: center; }

.chevron-box {
  width: 95%; padding: 15pt 10pt; background: #FFFFFF;
  border: 2pt solid #0D4F6E; border-radius: 4pt;
  text-align: center; position: relative;
}
.chevron-box.alt { border-color: #D4842A; }
.chevron-title { font-size: 11pt; font-weight: bold; color: #0D4F6E; margin: 0; text-transform: uppercase; }
.chevron-box.alt .chevron-title { color: #D4842A; }

.chevron-arrow {
  position: absolute; right: -10pt; top: 50%; transform: translateY(-50%);
  font-size: 14pt; color: #0D4F6E;
}

.pipe-details {
  width: 95%; margin-top: 8pt; padding: 10pt;
  background: #FFFFFF; border: 1pt solid #CBD5E0; border-radius: 4pt;
}
.pipe-details p { font-size: 9pt; color: #4A5568; margin: 0 0 3pt 0; line-height: 1.3; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">The AI Supply Chain: From Data to Deployment</h1>
  </div>
  <div class="divider"></div>

  <div class="pipeline">
    <div class="pipe-stage">
      <div class="chevron-box">
        <p class="chevron-title">DEMAND ANALYSIS</p>
        <p class="chevron-arrow">&#8594;</p>
      </div>
      <div class="pipe-details">
        <p>Define Agent Job Description.</p>
      </div>
    </div>
    <div class="pipe-stage">
      <div class="chevron-box">
        <p class="chevron-title">DATA PREP</p>
        <p class="chevron-arrow">&#8594;</p>
      </div>
      <div class="pipe-details">
        <p>Clean Optical Logs. Tokenization. Remove PII.</p>
      </div>
    </div>
    <div class="pipe-stage">
      <div class="chevron-box alt">
        <p class="chevron-title">TRAINING / TUNING</p>
        <p class="chevron-arrow">&#8594;</p>
      </div>
      <div class="pipe-details">
        <p>GPU Clusters. LoRA (Low-Rank Adaptation). Efficient Fine-Tuning.</p>
      </div>
    </div>
    <div class="pipe-stage">
      <div class="chevron-box alt">
        <p class="chevron-title">EVALUATION</p>
        <p class="chevron-arrow">&#8594;</p>
      </div>
      <div class="pipe-details">
        <p>The "Exam". Benchmarking against human gold standards.</p>
      </div>
    </div>
    <div class="pipe-stage">
      <div class="chevron-box">
        <p class="chevron-title">DEPLOYMENT</p>
      </div>
      <div class="pipe-details">
        <p>Model Weights. Training Logs. Eval Reports.</p>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 12: Three Column Info (`threeColumn`)

Three equal columns with icon area, title, and description.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; text-align: center; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.columns { display: flex; gap: 20pt; padding: 20pt 30pt; flex: 1; }
.col {
  flex: 1; background: #FFFFFF; border: 1pt solid #CBD5E0;
  border-radius: 6pt; padding: 20pt; text-align: center;
  display: flex; flex-direction: column; align-items: center;
}

.col-icon {
  width: 60pt; height: 60pt; background: #D6E8F0;
  border-radius: 8pt; margin-bottom: 12pt;
  display: flex; align-items: center; justify-content: center;
}
.col-icon p { font-size: 24pt; color: #0D4F6E; margin: 0; }

.col-title { font-size: 14pt; font-weight: bold; color: #1A2332; margin: 0 0 5pt 0; }
.col-subtitle { font-size: 11pt; color: #0D4F6E; margin: 0 0 8pt 0; }
.col-desc { font-size: 10pt; color: #4A5568; margin: 0; line-height: 1.4; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">The Horizon: Technical Trends 2026</h1>
  </div>
  <div class="divider"></div>

  <div class="columns">
    <div class="col">
      <div class="col-icon"><p>&#9889;</p></div>
      <p class="col-title">SLMs (Small Language Models)</p>
      <p class="col-subtitle">Edge AI</p>
      <p class="col-desc">Running efficiently on-prem or on-device. Critical for data privacy and latency.</p>
    </div>

    <div class="col">
      <div class="col-icon"><p>&#128279;</p></div>
      <p class="col-title">MAC (Multi-Agent Collaboration)</p>
      <p class="col-subtitle">Swarm Intelligence</p>
      <p class="col-desc">One agent diagnoses, one plans, one reviews. Specialized roles working in concert.</p>
    </div>

    <div class="col">
      <div class="col-icon"><p>&#129504;</p></div>
      <p class="col-title">Reasoning Models</p>
      <p class="col-subtitle">Chain of Thought</p>
      <p class="col-desc">Like DeepSeek-R1. Logic-heavy processing for complex root-cause analysis.</p>
    </div>
  </div>
</body>
</html>
```

---

### Layout 13: Challenge / Mitigation Table (`challengeTable`)

Two-column table layout with icon rows for challenges and their mitigations.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column;
}
.title-area { padding: 14pt 30pt 4pt 30pt; }
.title { font-size: 22pt; font-weight: bold; color: #1A2332; margin: 0; }
.divider { margin: 4pt 30pt 0 30pt; height: 2pt; background: #0D4F6E; }

.table-container { padding: 15pt 30pt; flex: 1; }

.header-row {
  display: flex; background: #0D4F6E; border-radius: 6pt 6pt 0 0; padding: 7pt 15pt;
}
.header-cell { flex: 1; }
.header-cell p { font-size: 13pt; font-weight: bold; color: #FFFFFF; margin: 0; text-transform: uppercase; }

.table-row {
  display: flex; background: #FFFFFF; border-bottom: 1pt solid #E2E8F0; padding: 12pt 15pt;
  align-items: center;
}
.table-row:last-child { border-bottom: none; border-radius: 0 0 6pt 6pt; }
.table-row:nth-child(odd) { background: #FFFFFF; }
.table-row:nth-child(even) { background: #F8FAFC; }

.row-icon {
  width: 35pt; height: 35pt; background: #D6E8F0;
  border-radius: 50%; margin-right: 12pt;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.row-icon p { font-size: 16pt; color: #0D4F6E; margin: 0; }

.challenge-cell { flex: 1; display: flex; align-items: center; }
.challenge-title { font-size: 12pt; font-weight: bold; color: #1A2332; margin: 0; }
.challenge-sub { font-size: 10pt; color: #718096; margin: 2pt 0 0 0; }

.mitigation-cell { flex: 1; }
.mitigation-text { font-size: 11pt; color: #4A5568; margin: 0; }
.mitigation-highlight { color: #D4842A; font-weight: bold; }
</style>
</head>
<body>
  <div class="title-area">
    <h1 class="title">Navigating the Obstacles</h1>
  </div>
  <div class="divider"></div>

  <div class="table-container">
    <div class="header-row">
      <div class="header-cell"><p>Challenge</p></div>
      <div class="header-cell"><p>Mitigation</p></div>
    </div>

    <div class="table-row">
      <div class="challenge-cell">
        <div class="row-icon"><p>&#128274;</p></div>
        <div>
          <p class="challenge-title">Data Privacy</p>
          <p class="challenge-sub">(Sensitive Telco Data)</p>
        </div>
      </div>
      <div class="mitigation-cell">
        <p class="mitigation-text"><span class="mitigation-highlight">On-prem deployment</span>, Small Language Models (SLMs).</p>
      </div>
    </div>

    <div class="table-row">
      <div class="challenge-cell">
        <div class="row-icon"><p>&#9888;</p></div>
        <div>
          <p class="challenge-title">Hallucinations</p>
          <p class="challenge-sub">(Risk of Outage)</p>
        </div>
      </div>
      <div class="mitigation-cell">
        <p class="mitigation-text"><span class="mitigation-highlight">RAG grounding</span>, Strict Evals, Human-in-the-loop.</p>
      </div>
    </div>

    <div class="table-row">
      <div class="challenge-cell">
        <div class="row-icon"><p>&#128736;</p></div>
        <div>
          <p class="challenge-title">Complexity</p>
          <p class="challenge-sub">(Legacy Black Box Equipment)</p>
        </div>
      </div>
      <div class="mitigation-cell">
        <p class="mitigation-text"><span class="mitigation-highlight">Agentic Tool Use (APIs)</span> to bridge the gap.</p>
      </div>
    </div>

    <div class="table-row">
      <div class="challenge-cell">
        <div class="row-icon"><p>&#129309;</p></div>
        <div>
          <p class="challenge-title">Trust</p>
          <p class="challenge-sub">(Skepticism of AI)</p>
        </div>
      </div>
      <div class="mitigation-cell">
        <p class="mitigation-text">Visualizing the <span class="mitigation-highlight">"Reasoning Trace"</span> (Explainability).</p>
      </div>
    </div>
  </div>
</body>
</html>
```

---

### Layout 14: Closing / Summary Slide (`closingSlide`)

Bold central statement with supporting bullet points.

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #F0F4F8; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #F0F4F8; font-family: Arial, sans-serif;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
}
</style>
</head>
<body>
  <h1 style="font-size: 24pt; font-weight: bold; color: #1A2332; margin: 0 50pt 8pt 50pt; text-align: center; line-height: 1.3;">
    The 'Smart Brain' for the Optical World
  </h1>

  <div style="margin: 15pt 50pt; height: 2pt; background: #0D4F6E; width: 120pt;"></div>

  <p style="font-size: 16pt; color: #1A2332; margin: 15pt 60pt; text-align: center; line-height: 1.5;">
    NCE turns the network from a Black Box to a White Box.
  </p>
  <p style="font-size: 16pt; color: #1A2332; margin: 0 60pt 20pt 60pt; text-align: center; line-height: 1.5;">
    Agentic AI turns the White Box into an <span style="font-weight: bold; color: #D4842A;">AUTONOMOUS BOX</span>.
  </p>

  <div style="display: flex; gap: 30pt; margin: 0 60pt;">
    <div style="text-align: center;">
      <p style="font-size: 11pt; color: #0D4F6E; margin: 0;">Focus on <span style="font-weight: bold;">High-Variance</span></p>
      <p style="font-size: 11pt; color: #0D4F6E; margin: 2pt 0 0 0;">Workflows.</p>
    </div>
    <div style="text-align: center;">
      <p style="font-size: 11pt; color: #0D4F6E; margin: 0;">Build <span style="font-weight: bold;">Trust</span> through</p>
      <p style="font-size: 11pt; color: #0D4F6E; margin: 2pt 0 0 0;">Rigorous Evals.</p>
    </div>
    <div style="text-align: center;">
      <p style="font-size: 11pt; color: #0D4F6E; margin: 0;">Sell the <span style="font-weight: bold;">Outcome</span> (Service),</p>
      <p style="font-size: 11pt; color: #0D4F6E; margin: 2pt 0 0 0;">not just the Software.</p>
    </div>
  </div>

  <p style="font-size: 11pt; color: #718096; font-style: italic; margin: 25pt 60pt 0 60pt; text-align: center;">
    We are no longer just building the tracks; we are building the driver.
  </p>
</body>
</html>
```

---

## Complete Generation Example

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./.claude/skills/pptx-enhanced/scripts/html2pptx');
const fs = require('fs');
const path = require('path');

const SKILL_DIR = '.claude/skills/pptx-generator-enhanced';

async function generateTechBlueprintPresentation(slidesContent, outputPath) {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.title = slidesContent.title || 'Tech Blueprint Presentation';
  pptx.author = slidesContent.author || 'Generated';

  for (let i = 0; i < slidesContent.slides.length; i++) {
    const slideData = slidesContent.slides[i];
    const htmlPath = `workspace/slide${i + 1}.html`;

    const html = generateSlideHtml(slideData);
    fs.writeFileSync(htmlPath, html);

    const { slide, placeholders } = await html2pptx(htmlPath, pptx);

    if (slideData.charts && placeholders.length > 0) {
      for (let j = 0; j < slideData.charts.length && j < placeholders.length; j++) {
        slide.addChart(pptx.charts[slideData.charts[j].type],
          slideData.charts[j].data,
          { ...placeholders[j], ...slideData.charts[j].options }
        );
      }
    }
  }

  await pptx.writeFile(outputPath);
  return outputPath;
}

const presentation = {
  title: 'Optical Intelligence for Autonomous Networks',
  author: 'Strategy Team',
  slides: [
    { layout: 'title', title: 'From Connectivity to Cognition', subtitle: 'Empowering NCE with Agentic AI' },
    { layout: 'twoColumnSplit', title: 'The Nervous System', leftColumn: {...}, rightColumn: {...} },
    { layout: 'timeline', title: 'The Rise of the Agent', phases: [...] },
    { layout: 'comparison', title: 'Sequential vs Parallel', old: {...}, new: {...} },
    { layout: 'horizontalProcess', title: 'From Pipe to Service', steps: [...] },
    { layout: 'problemSolution', title: 'From Complaint to Care', problem: {...}, solution: {...} },
    { layout: 'threeColumn', title: 'Technical Trends 2026', columns: [...] },
    { layout: 'challengeTable', title: 'Navigating Obstacles', rows: [...] },
    { layout: 'closingSlide', title: 'The Smart Brain', message: '...' }
  ]
};

generateTechBlueprintPresentation(presentation, 'optical_intelligence.pptx');
```

## Customization

### Creating a Custom Theme

Copy `default-pptx-config.json` and modify:

1. **Colors**: Change hex values in `theme.colors`
2. **Fonts**: Modify font families and sizes in `theme.fonts`

### Example: Adjusting to Green Energy Theme

```json
{
  "theme": {
    "name": "Green Energy",
    "colors": {
      "primary": "#1B5E3B",
      "primaryLight": "#D4EDDA",
      "secondary": "#D4842A",
      "background": "#F0F5F1"
    }
  }
}
```

## Visual Content Generation

### Image Format Decision Guide

When a slide needs a visual element (diagram, illustration, chart, photo), choose the right approach:

| Content Type | Preferred Format | Approach |
|-------------|-----------------|----------|
| Flowcharts, architecture diagrams | **SVG → PNG** | Generate SVG programmatically, rasterize with Sharp |
| Network topologies, system diagrams | **SVG → PNG** | Generate SVG with precise node/edge layout |
| Icons, logos, simple graphics | **SVG → PNG** | Create SVG, rasterize at target resolution |
| Screenshots, photographs | **PNG / JPG** | Use existing files directly |
| Step-by-step process animations | **GIF (Manim)** | Create animated GIF with Manim, embed as image |
| Data flow animations | **GIF (Manim)** | Animate with Manim for clear visual instruction |
| Complex mathematical visuals | **GIF (Manim)** | Leverage Manim's math rendering capabilities |

### SVG Diagram Generation (Preferred for Diagrams)

**ALWAYS prefer generating SVG diagrams** over placeholder text like `[Diagram: ...]` when a slide needs a visual. SVG provides crisp, scalable graphics that look professional at any size.

#### When to Generate SVG Diagrams

- Flowcharts and process flows
- Architecture and system diagrams
- Network topology illustrations
- Comparison visuals (before/after)
- Relationship maps and hierarchies
- Technical schematics
- Decision trees

#### SVG → PNG Workflow

```javascript
const sharp = require('sharp');

// Step 1: Generate SVG string programmatically
function createFlowchartSvg(steps, colors) {
  const boxWidth = 160, boxHeight = 50, gap = 30;
  const totalWidth = steps.length * (boxWidth + gap) - gap;
  const svgHeight = boxHeight + 40;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="${svgHeight}">`;

  steps.forEach((step, i) => {
    const x = i * (boxWidth + gap);
    const fill = colors[i % colors.length];

    // Box
    svg += `<rect x="${x}" y="10" width="${boxWidth}" height="${boxHeight}" rx="8" fill="${fill}" stroke="#0D4F6E" stroke-width="2"/>`;

    // Label
    svg += `<text x="${x + boxWidth/2}" y="${10 + boxHeight/2 + 5}" text-anchor="middle" font-family="Arial" font-size="13" fill="#FFFFFF" font-weight="bold">${step}</text>`;

    // Arrow
    if (i < steps.length - 1) {
      const arrowX = x + boxWidth + 2;
      svg += `<line x1="${arrowX}" y1="${10 + boxHeight/2}" x2="${arrowX + gap - 4}" y2="${10 + boxHeight/2}" stroke="#0D4F6E" stroke-width="2" marker-end="url(#arrowhead)"/>`;
    }
  });

  // Arrowhead marker
  svg += `<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#0D4F6E"/></marker></defs>`;
  svg += `</svg>`;
  return svg;
}

// Step 2: Rasterize SVG to PNG with Sharp
async function svgToPng(svgString, outputPath, width = 800) {
  await sharp(Buffer.from(svgString))
    .resize({ width })
    .png()
    .toFile(outputPath);
  return outputPath;
}

// Step 3: Use in HTML slide
const svg = createFlowchartSvg(['Perceive', 'Reason', 'Act', 'Learn'], ['#0D4F6E', '#0D4F6E', '#D4842A', '#D4842A']);
const diagramPath = await svgToPng(svg, 'workspace/flowchart.png', 600);
// Then in HTML: <img src="workspace/flowchart.png" style="width: 500pt; height: auto;">
```

#### SVG Best Practices

- Use theme colors from `default-pptx-config.json` for consistency
- Set explicit `width` and `height` on the SVG root element
- Use `font-family="Arial"` for text (web-safe font)
- Keep diagrams simple and readable at slide scale
- Target 600-800px width for rasterization (scales well to slide dimensions)
- Use `rx` attribute on rectangles for rounded corners matching the theme (6pt)

#### Common SVG Diagram Patterns

**Hub-and-Spoke Diagram:**
```javascript
function createHubSpokeSvg(center, spokes, primaryColor = '#0D4F6E', accentColor = '#D4842A') {
  const cx = 200, cy = 200, hubR = 50, spokeR = 35;
  const angleStep = (2 * Math.PI) / spokes.length;
  const radius = 140;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">`;

  // Spokes and connections
  spokes.forEach((label, i) => {
    const angle = angleStep * i - Math.PI / 2;
    const sx = cx + radius * Math.cos(angle);
    const sy = cy + radius * Math.sin(angle);

    svg += `<line x1="${cx}" y1="${cy}" x2="${sx}" y2="${sy}" stroke="${primaryColor}" stroke-width="2" stroke-dasharray="4,4"/>`;
    svg += `<circle cx="${sx}" cy="${sy}" r="${spokeR}" fill="#FFFFFF" stroke="${primaryColor}" stroke-width="2"/>`;
    svg += `<text x="${sx}" y="${sy + 4}" text-anchor="middle" font-family="Arial" font-size="10" fill="${primaryColor}">${label}</text>`;
  });

  // Center hub
  svg += `<circle cx="${cx}" cy="${cy}" r="${hubR}" fill="${primaryColor}"/>`;
  svg += `<text x="${cx}" y="${cy + 5}" text-anchor="middle" font-family="Arial" font-size="12" fill="#FFFFFF" font-weight="bold">${center}</text>`;

  svg += `</svg>`;
  return svg;
}
```

**Layered Architecture Diagram:**
```javascript
function createLayerDiagramSvg(layers, width = 500) {
  const layerHeight = 50, gap = 8;
  const totalHeight = layers.length * (layerHeight + gap) - gap + 20;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${totalHeight}">`;

  layers.forEach((layer, i) => {
    const y = 10 + i * (layerHeight + gap);
    const colors = ['#0D4F6E', '#3B9FD6', '#D4842A', '#083A52'];
    const fill = colors[i % colors.length];

    svg += `<rect x="10" y="${y}" width="${width - 20}" height="${layerHeight}" rx="6" fill="${fill}" opacity="0.9"/>`;
    svg += `<text x="${width / 2}" y="${y + layerHeight / 2 + 5}" text-anchor="middle" font-family="Arial" font-size="14" fill="#FFFFFF" font-weight="bold">${layer}</text>`;
  });

  svg += `</svg>`;
  return svg;
}
```

---

### Embedding Images (All Formats)

The HTML slide system supports embedding images in multiple formats. All images are referenced via `<img>` tags in the HTML.

#### Supported Formats

| Format | Usage | Notes |
|--------|-------|-------|
| **PNG** | Diagrams, screenshots, icons | Lossless, supports transparency |
| **JPG** | Photos, complex imagery | Lossy compression, smaller file size |
| **SVG** | Must be rasterized to PNG first | Use Sharp to convert before embedding |
| **GIF** | Animated visuals (Manim output) | Embedded as static first frame in PPTX; use for HTML preview |

#### Image Embedding in HTML Slides

```html
<!-- Fixed size image -->
<img src="workspace/diagram.png" style="width: 300pt; height: 200pt;">

<!-- Auto-height image (maintains aspect ratio via HTML rendering) -->
<img src="workspace/architecture.png" style="width: 400pt; height: auto;">

<!-- Centered image in a flex container -->
<div style="display: flex; justify-content: center; align-items: center; flex: 1;">
  <img src="workspace/network-topology.png" style="width: 500pt; height: auto;">
</div>
```

#### Generating PNG Images with Sharp

```javascript
const sharp = require('sharp');

// From SVG string
async function svgStringToPng(svgString, outputPath, width = 800) {
  await sharp(Buffer.from(svgString)).resize({ width }).png().toFile(outputPath);
}

// Resize an existing image
async function resizeImage(inputPath, outputPath, width) {
  await sharp(inputPath).resize({ width }).toFile(outputPath);
}

// Composite multiple images (e.g., icon on background)
async function compositeImages(basePath, overlayPath, outputPath) {
  await sharp(basePath)
    .composite([{ input: overlayPath, gravity: 'center' }])
    .toFile(outputPath);
}
```

---

### Animated GIF Generation with Manim

Use **Manim Community Edition** to create animated GIFs for slides that need to illustrate processes, transitions, or step-by-step instructions. GIFs are especially useful for:

- Step-by-step process animations (e.g., data pipeline flow)
- Network packet flow visualizations
- Algorithm execution animations
- Before/after transformation sequences
- Mathematical concept demonstrations

#### Setup

Manim is included in `requirements.txt`. Install with:

```bash
pip install -r .claude/skills/pptx-enhanced/requirements.txt
```

#### Basic Manim GIF Workflow

```python
#!/usr/bin/env python3
"""Generate an animated process flow GIF using Manim."""
from manim import *

class ProcessFlow(Scene):
    def construct(self):
        # Theme colors matching the presentation
        PRIMARY = "#0D4F6E"
        ACCENT = "#D4842A"
        BG = "#F0F4F8"

        self.camera.background_color = BG

        # Create process steps
        steps = ["Perceive", "Reason", "Act", "Learn"]
        boxes = VGroup()

        for i, label in enumerate(steps):
            color = ACCENT if i >= 2 else PRIMARY
            box = RoundedRectangle(
                corner_radius=0.15, width=2.2, height=0.8,
                fill_color=color, fill_opacity=1, stroke_color=PRIMARY
            )
            text = Text(label, font="Arial", font_size=24, color=WHITE)
            text.move_to(box)
            group = VGroup(box, text)
            boxes.add(group)

        boxes.arrange(RIGHT, buff=0.5)

        # Animate step by step
        for i, box in enumerate(boxes):
            self.play(FadeIn(box, shift=UP * 0.3), run_time=0.5)
            if i < len(boxes) - 1:
                arrow = Arrow(
                    box.get_right(), boxes[i + 1].get_left(),
                    color=PRIMARY, buff=0.1
                )
                self.play(Create(arrow), run_time=0.3)

        self.wait(1)
```

#### Rendering Manim GIF

```bash
# Render as GIF (low quality for fast iteration)
manim -ql --format=gif process_flow.py ProcessFlow

# Render as GIF (medium quality for presentations)
manim -qm --format=gif process_flow.py ProcessFlow

# Output will be in media/videos/process_flow/
# Move to workspace for embedding
cp media/videos/process_flow/*/ProcessFlow.gif workspace/process-flow.gif
```

#### Embedding Animated GIFs in Slides

GIFs can be embedded in HTML slides for preview. In the final PPTX, they appear as static images (first frame). For full animation support, consider linking to the GIF or using the HTML preview.

```html
<!-- Embed GIF in slide (shows as static in PPTX, animated in HTML preview) -->
<div class="diagram-area" style="height: 200pt; background: #F0F4F8;">
  <img src="workspace/process-flow.gif" style="width: 500pt; height: auto;">
</div>
```

#### Manim Tips for Presentation GIFs

**General:**
- Match colors to the presentation theme (`#0D4F6E`, `#D4842A`, `#F0F4F8`)
- Set `self.camera.background_color` to match slide background
- Keep animations short (3-8 seconds) for clarity
- Use `font="Arial"` for consistency with slides
- Render at medium quality (`-qm`) for good balance of quality and file size
- Use `--format=gif` flag for direct GIF output

**Text Legibility (Critical):**
- **Single-line labels**: Use single-line text for boxes. Multi-line text (e.g., `"Multi-Head\nSelf-Attention"`) jams together in small boxes. Simplify to `"Self-Attention"` or increase box height.
- **Minimum box height for text**: For single-line text at `font_size=12`, minimum box height is `0.42`. For multi-line text, use at least `0.7` per line.
- **Font size to box ratio**: `font_size` in points ÷ 2.5 ≈ minimum box height in Manim units. E.g., `font_size=12` → min height `0.48`.
- **Horizontal spacing**: For token/cell rows, use `buff=0.3-0.4` between items. Below `0.2`, labels overlap.
- **Weight/annotation labels**: Position annotations using alternating offsets (`LEFT * 0.4` for even indices, `RIGHT * 0.4` for odd) to prevent overlap with arrows.
- **Description text**: Place descriptions on the **outer side** of nodes (away from the center of the diagram) to avoid overlapping with connection arrows.
- **Max items per row**: Maximum 5-6 items in a horizontal row. More items cause text overflow.
- **Unicode formulas**: Avoid Unicode superscript characters (⁻⁰·⁰⁷⁶) in `Text()`. They may not render correctly with all fonts. Use `MathTex()` for mathematical formulas, or use plain ASCII approximations.
- **VS/separator labels**: Don't place separator labels at `ORIGIN`—they overlap with content. Offset them to a gap area between sections.

#### Common Manim Animation Patterns

**Data Flow Animation:**
```python
class DataFlow(Scene):
    def construct(self):
        self.camera.background_color = "#F0F4F8"
        nodes = ["Input", "Process", "Output"]
        # ... create nodes and animate data packets flowing between them
```

**Highlight Sequence (for emphasis):**
```python
class HighlightSteps(Scene):
    def construct(self):
        self.camera.background_color = "#F0F4F8"
        items = VGroup(*[
            Text(f"Step {i+1}: {s}", font="Arial", font_size=20, color="#1A2332")
            for i, s in enumerate(["Analyze", "Diagnose", "Act"])
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.4)

        self.play(FadeIn(items))
        for item in items:
            box = SurroundingRectangle(item, color="#D4842A", buff=0.1)
            self.play(Create(box), run_time=0.4)
            self.play(FadeOut(box), run_time=0.3)
        self.wait(0.5)
```

---

## Best Practices

### Layout & Spacing

1. **Title Hierarchy**: Use bold 22-24pt dark titles with 10-11pt subtitles. Reduce to 20pt for long titles.
2. **Title Area Padding**: Use `padding: 14pt 30pt 4pt 30pt` for the title area. The title+subtitle+divider should occupy ~40-45pt total.
3. **Content Area Padding**: Use `padding: 6pt 30pt` for the main content area below the divider.
4. **Bottom Callout Position**: Use `bottom: 12pt` with `padding: 7pt 15pt`. This bar occupies ~35pt. Content must end 50pt above the slide bottom.
5. **Column Gaps**: Use `gap: 10pt` between columns (not 20pt). For tight layouts, 8pt is acceptable.
6. **Card Padding**: Use `padding: 6pt 8pt` inside white cards. Minimum `padding: 5pt 6pt` for dense layouts.
7. **Inter-element Gaps**: Use `gap: 5pt` between stacked cards. Minimum `gap: 3pt` but avoid it—signals content overload.
8. **Side Margins**: Always maintain `30pt` left/right margins from the slide edge.

### Content Density

9. **Maximum Content Per Slide**: A two-column slide should have at most 2-3 cards per column. If you need more, consider splitting across slides.
10. **Body Text Minimum**: **Never below 9pt** for body text. Use `line-height: 1.3-1.35` for readability.
11. **Card Text Lines**: Each card should contain at most 4-5 lines of body text. If more is needed, reduce the text or split the content.
12. **Pipeline/Process Stages**: Maximum 3 stages per row. For 6+ stages, use a 3×2 grid layout instead of a single row.
13. **Table Rows**: Maximum 5-6 data rows per slide. More rows require smaller fonts that hurt readability.

### Visual Design

14. **Amber Accents**: Reserve `#D4842A` for highlights, callout bars, and emphasis only.
15. **White Cards**: Content should sit in white card surfaces (`#FFFFFF`) against the gray background.
16. **Teal Dividers**: Always add a 2pt `#0D4F6E` horizontal line between title and content.
17. **Consistent Spacing**: Apply the same padding/gap values across all slides for visual consistency.
18. **Border-left Accents**: Use `border-left: 4pt solid #COLOR` on cards to visually categorize content.

### Content Generation

19. **Generate Diagrams, Don't Placeholder**: When a slide calls for a visual, generate an SVG diagram rather than leaving placeholder text like `[Diagram: ...]`.
20. **Use Manim for Complex Animations**: When static diagrams aren't sufficient to explain a process, generate an animated GIF with Manim.
21. **Image Quality**: Rasterize SVGs at 1200px width for sharp rendering on slides (use `sharp` library).
22. **Theme Consistency**: Use colors from `default-pptx-config.json` in all generated visuals.

### Avoiding Overflow

23. **Test with Real Content**: Template spacing values are designed for typical content density. Always verify with actual text—especially Chinese text which is wider per character.
24. **Absolute Positioning Conflicts**: Never stack more than 2 layers of `position: absolute` (content flow + bottom bar). Adding a third layer (e.g., a `bottom: 55pt` features section) causes collisions in PPTX.
25. **Image Height**: Use `max-height` constraints on images (e.g., `max-height: 75pt`). Never use `height: auto` without a max-height—image size is unpredictable.
26. **Content-Bottom Bar Gap**: Ensure at least 50pt clearance between the last flow content element and the absolute-positioned bottom bar.

### SVG Generation Rules

27. **No Emoji in SVG XML**: SVG text elements cannot render emoji. Use descriptive text or simple symbols instead.
28. **Escape Special Characters**: Always escape `&` as `&amp;` in SVG XML text.
29. **Error Handling**: Wrap each SVG-to-PNG conversion in try/catch. If one image fails, the rest should still generate.
30. **Consistent Dimensions**: Generate all SVGs at the same width (e.g., 1200px) for uniform appearance.

### Chinese / CJK Text Considerations

31. **Character Width**: Chinese characters are approximately 1.5x wider than Latin characters at the same font size. Reduce text volume by ~30% compared to English content.
32. **Minimum Font Size**: Use 9pt minimum for Chinese body text (8.5pt absolute minimum). Chinese at 7-8pt is unreadable when projected.
33. **Line Height**: Use `line-height: 1.3-1.4` for Chinese text (higher than the 1.2 used for English).
34. **Text Wrapping**: Chinese text wraps at any character boundary, not just spaces. Narrow columns (< 120pt) cause excessive wrapping that looks ugly.
35. **Content Planning**: When designing for CJK audiences, plan for ~60-70% of the English word count per slide.

### Validation

36. **Thumbnail Generation**: Always generate thumbnails and inspect before delivery.
37. **Build Script Pattern**: Use a build script with try/catch per slide so one error doesn't stop the entire build.
38. **Iterative Overflow Fixes**: After fixing overflow, rebuild and verify. Fix all overflow errors in one pass using the multi-error report.
