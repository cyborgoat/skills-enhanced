# Validation

1. **Build** (`build-deck.js` / `html2pptx.js`) rejects wrong slide size, body overflow, CSS gradients, and backgrounds/borders on text elements. It then runs `lint-pptx.js` and fails if the file contains patterns that make PowerPoint show "found a problem... Repair" (which silently drops shapes).
2. **Lint**: `node scripts/lint-pptx.js out.pptx`. Checks for: `adj` guides on shapes that do not support them (`rectRadius` on anything but `roundRect`), out-of-range corner radii, NaN/undefined values, negative sizes, invalid arrow or dash types.
3. **Inventory**: `python scripts/inventory.py --issues-only out.pptx issues.json`. Flags under ~0.2in are usually line-height estimates; investigate larger overflow or overlap between text boxes.
4. **Thumbnails**: `python scripts/thumbnail.py out.pptx thumbs --cols 4` (needs LibreOffice and Poppler). If missing, report that, rely on 1-3, and ask the user to open the deck once in PowerPoint.

Build warnings (`warning: panel ... may overflow`, `table ... may overflow`) are estimates; treat them as a prompt to shorten text, split the slide, or lower the density.

## Common fixes

- Overflow: cut copy or split the slide before reducing font size.
- Sparse slide: add content (a second panel, a table, a stat strip) or use a denser type; or raise `density`.
- Diagram crowded: drop to ~10 nodes, keep edges between neighbouring layers, or use `mode: "mermaid"`.
- Tables wrap: widen the column with `colW`, shorten cells, or use `fontSize`.
- Images: always contained; supply a wide image for wide panels or use `fit: "cover"`.
- CJK text: fewer words, wider columns.
- PptxGenJS: table `margin` is inches, text-box `margin` is points; `rectRadius` only on `roundRect`.
