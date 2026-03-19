/**
 * render-mermaid - Render Mermaid diagram definitions to PNG or SVG images
 *
 * Uses Playwright (already a project dependency) with CDN-loaded mermaid.js
 * to render .mmd definitions into themed PNG or SVG files for embedding in HTML slides.
 *
 * USAGE (CLI):
 *   node render-mermaid.js <input.mmd> <output.png|output.svg> [--width 800] [--theme dark]
 *   node render-mermaid.js --def "graph LR; A-->B" output.png
 *
 * USAGE (Module):
 *   const { renderMermaid, renderMermaidFile } = require('./render-mermaid');
 *   await renderMermaid('graph LR; A-->B', 'output.png', { width: 800 });
 *   await renderMermaidFile('input.mmd', 'output.png');
 *
 * OPTIONS:
 *   --width   Target PNG width in pixels (default: 800)
 *   --theme   Mermaid theme: 'default' | 'dark' | 'neutral' | 'forest' (default: 'neutral')
 *   --bg      Background color (default: 'transparent')
 *   --def     Pass Mermaid definition as a string instead of a file
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Crimson Dark palette for custom theming
const THEME_COLORS = {
  primary: '#C62828',
  primaryDark: '#8E0000',
  primaryLight: '#FFCDD2',
  secondary: '#FFB300',
  secondaryLight: '#FFF8E1',
  accent: '#E53935',
  background: '#1A1A2E',
  text: '#FFFFFF',
  textMedium: '#B0BEC5',
  border: '#3D3D5C',
};

/**
 * Render a Mermaid diagram definition string to a PNG or SVG file.
 *
 * @param {string} definition  - Mermaid diagram definition (e.g. "graph LR; A-->B")
 * @param {string} outputPath  - Path to write the output PNG or SVG
 * @param {object} [options]
 * @param {number} [options.width=800]       - Target PNG width in pixels
 * @param {string} [options.theme='neutral'] - Mermaid theme name
 * @param {string} [options.bg='transparent'] - Background color
 * @param {object} [options.themeVariables]  - Custom mermaid themeVariables overrides
 * @returns {Promise<string>} outputPath
 */
async function renderMermaid(definition, outputPath, options = {}) {
  const {
    width = 800,
    theme = 'neutral',
    bg = 'transparent',
    themeVariables = {},
  } = options;

  // Merge defaults into themeVariables when using the 'base' theme
  const vars = theme === 'base' ? {
    primaryColor: THEME_COLORS.primaryLight,
    primaryBorderColor: THEME_COLORS.primary,
    primaryTextColor: THEME_COLORS.text,
    secondaryColor: THEME_COLORS.secondaryLight,
    secondaryBorderColor: THEME_COLORS.secondary,
    secondaryTextColor: '#5D4037',
    tertiaryColor: '#FFFFFF',
    lineColor: THEME_COLORS.primary,
    textColor: '#37474F',
    mainBkg: '#FFFFFF',
    nodeBorder: THEME_COLORS.primary,
    clusterBkg: '#FFFFFF',
    edgeLabelBackground: '#FFFFFF',
    fontFamily: 'Arial',
    fontSize: '18px',
    ...themeVariables,
  } : themeVariables;

  const mermaidConfig = JSON.stringify({
    theme: Object.keys(vars).length > 0 ? 'base' : theme,
    themeVariables: Object.keys(vars).length > 0 ? vars : undefined,
  });

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ deviceScaleFactor: 3 });

    // Set a generous viewport to avoid clipping
    await page.setViewportSize({ width: Math.max(1400, Math.round(width / 1.5)), height: 2200 });

    const html = `<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"><\/script>
  <style>
    body { margin: 0; padding: 16px; background: ${bg}; }
    #container { display: inline-block; }
  </style>
</head>
<body>
  <div id="container">
    <pre class="mermaid">${escapeHtml(definition)}</pre>
  </div>
  <script>
    mermaid.initialize(${mermaidConfig});
  <\/script>
</body>
</html>`;

    await page.setContent(html, { waitUntil: 'networkidle' });

    // Wait for mermaid to finish rendering (SVG appears inside .mermaid)
    await page.waitForSelector('.mermaid svg', { timeout: 15000 });

    // Small extra wait for any transitions
    await page.waitForTimeout(300);

    // Get the bounding box of the rendered SVG
    const svgElement = await page.$('.mermaid svg');
    const box = await svgElement.boundingBox();

    if (!box || box.width === 0 || box.height === 0) {
      throw new Error('Mermaid rendered an empty diagram. Check your definition syntax.');
    }

    const svgMarkup = await page.$eval('.mermaid svg', (svg, background) => {
      const clone = svg.cloneNode(true);
      const width = svg.getAttribute('width') || svg.viewBox.baseVal.width || svg.getBoundingClientRect().width;
      const height = svg.getAttribute('height') || svg.viewBox.baseVal.height || svg.getBoundingClientRect().height;
      const viewBox = svg.getAttribute('viewBox');

      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      clone.setAttribute('width', String(width));
      clone.setAttribute('height', String(height));

      if (!viewBox) {
        clone.setAttribute('viewBox', `0 0 ${width} ${height}`);
      }

      if (background && background !== 'transparent') {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', '0');
        rect.setAttribute('y', '0');
        rect.setAttribute('width', '100%');
        rect.setAttribute('height', '100%');
        rect.setAttribute('fill', background);
        clone.insertBefore(rect, clone.firstChild);
      }

      return clone.outerHTML;
    }, bg);

    // Ensure output directory exists
    const outDir = path.dirname(path.resolve(outputPath));
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    if (path.extname(outputPath).toLowerCase() === '.svg') {
      fs.writeFileSync(outputPath, svgMarkup, 'utf8');
      return outputPath;
    }

    // Rasterize from the browser render instead of the raw SVG string.
    const padding = 12;
    const screenshotBuffer = await page.screenshot({
      clip: {
        x: Math.max(0, box.x - padding),
        y: Math.max(0, box.y - padding),
        width: box.width + padding * 2,
        height: box.height + padding * 2,
      },
      omitBackground: bg === 'transparent',
    });

    try {
      const sharp = require('sharp');
      const buf = await sharp(screenshotBuffer)
        .resize({ width, withoutEnlargement: false })
        .png()
        .toBuffer();
      fs.writeFileSync(outputPath, buf);
    } catch {
      fs.writeFileSync(outputPath, screenshotBuffer);
    }

    return outputPath;
  } finally {
    await browser.close();
  }
}

/**
 * Render a .mmd file to PNG or SVG.
 *
 * @param {string} inputPath  - Path to .mmd file
 * @param {string} outputPath - Path to write the output PNG or SVG
 * @param {object} [options]  - Same options as renderMermaid
 * @returns {Promise<string>} outputPath
 */
async function renderMermaidFile(inputPath, outputPath, options = {}) {
  const definition = fs.readFileSync(inputPath, 'utf8');
  return renderMermaid(definition, outputPath, options);
}

/** Escape HTML special characters to safely embed in the page */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// --- CLI ---
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 2 && !args.includes('--help')) {
    console.error('Usage: node render-mermaid.js <input.mmd> <output.png|output.svg> [--width 800] [--theme neutral] [--bg transparent]');
    console.error('       node render-mermaid.js --def "graph LR; A-->B" <output.png> [options]');
    process.exit(1);
  }

  if (args.includes('--help')) {
    console.log(`
render-mermaid - Render Mermaid diagrams to PNG or SVG

Usage:
  node render-mermaid.js <input.mmd> <output.png|output.svg> [options]
  node render-mermaid.js --def "<mermaid definition>" <output.png|output.svg> [options]

Options:
  --width <px>    Target PNG width (default: 800, ignored for SVG output)
  --theme <name>  Mermaid theme: default, dark, neutral, forest, base (default: neutral)
  --bg <color>    Background color or 'transparent' (default: transparent)
  --help          Show this help
    `);
    process.exit(0);
  }

  function getArg(flag, fallback) {
    const idx = args.indexOf(flag);
    return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : fallback;
  }

  const widthOpt = parseInt(getArg('--width', '800'), 10);
  const themeOpt = getArg('--theme', 'neutral');
  const bgOpt = getArg('--bg', 'transparent');

  const defIdx = args.indexOf('--def');
  let definition, outputPath;

  if (defIdx !== -1) {
    definition = args[defIdx + 1];
    // output path is the next positional arg after --def <value>
    outputPath = args.find((a, i) => i !== defIdx && i !== defIdx + 1 && !a.startsWith('--') && (i === 0 || !args[i - 1].startsWith('--')));
    if (!outputPath) {
      // fallback: last non-flag arg
      for (let i = args.length - 1; i >= 0; i--) {
        if (!args[i].startsWith('--') && (i === 0 || !args[i - 1].startsWith('--'))) {
          if (args[i] !== definition) { outputPath = args[i]; break; }
        }
      }
    }
  } else {
    const positional = args.filter((a, i) => !a.startsWith('--') && (i === 0 || !args[i - 1].startsWith('--')));
    if (positional.length < 2) {
      console.error('Error: Need input.mmd and output.png/output.svg paths');
      process.exit(1);
    }
    const inputPath = positional[0];
    outputPath = positional[1];
    definition = fs.readFileSync(inputPath, 'utf8');
  }

  renderMermaid(definition, outputPath, { width: widthOpt, theme: themeOpt, bg: bgOpt })
    .then((out) => console.log(`Rendered: ${out}`))
    .catch((err) => { console.error('Error:', err.message); process.exit(1); });
}

module.exports = { renderMermaid, renderMermaidFile, THEME_COLORS };
