// Theme tokens read from default-pptx-config.json. Shared by templates, diagrams and mermaid.
const cfg = require('../default-pptx-config.json');

// level: 'low' | 'medium' | 'high' (information density). T.dn holds that level's tokens.
function loadTheme(overrides = {}, level) {
  const c = { ...cfg.theme.colors, ...(overrides.colors || {}) };
  const t = c.text, b = c.border;
  const lv = level || cfg.density.default;
  const dn = cfg.density.levels[lv];
  if (!dn) throw new Error(`Unknown density "${lv}". Use ${Object.keys(cfg.density.levels).join(', ')}`);
  return {
    cfg, level: lv, dn,
    primary: c.primary, primaryDark: c.primaryDark, primaryLight: c.primaryLight,
    secondary: c.secondary, secondaryLight: c.secondaryLight, accent: c.accent,
    bg: c.background, alt: c.backgroundAlt,
    ink: t.dark, mid: t.medium, light: t.light, onPrimary: t.onPrimary, onSecondary: t.onSecondary, hi: t.highlight,
    line: b.primary, subtle: b.subtle, gold: b.secondary,
    font: cfg.theme.fonts.body.family,
  };
}

const hex = (s) => String(s).replace('#', '');

module.exports = { loadTheme, hex, cfg };
