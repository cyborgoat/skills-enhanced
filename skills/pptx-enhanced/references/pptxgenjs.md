# PptxGenJS cheatsheet

Use after `html2pptx` (or standalone) for charts, tables, shapes and images. Slide is 10 x 5.625 in. Placeholders from `html2pptx` are `{id, x, y, w, h}` in inches and can be spread into options.

## Gotchas

- Hex colours **without `#`** (`"C62828"`); a `#` corrupts the file.
- Text-box `margin` is in points; **table `margin` is in inches**.
- Rounded rectangles: `pptx.ShapeType.roundRect` with `rectRadius` in inches.
- Calculate image aspect ratio from the real pixel size; never stretch.
- Pie/doughnut: one series, all categories in `labels`. Scatter: first series holds X values, the rest hold Y.
- Single-series bar/line: one colour, no legend. Several series: one colour each.
- Time axes: under 30 days use daily points, 30-365 monthly, over 365 yearly; a single point means wrong grouping.
- Start a value axis near the minimum when data clusters (`valAxisMinVal`); use 0 for counts.

## Text and shapes

```js
slide.addText([{ text: 'Bold ', options: { bold: true } }, { text: 'normal' }], { x: 1, y: 1, w: 4, h: 0.5, fontFace: 'Arial', fontSize: 12, color: '1F2937' });
slide.addShape(pptx.ShapeType.roundRect, { x: 1, y: 2, w: 3, h: 1, fill: { color: 'FFF1F1' }, line: { color: 'C62828', width: 1 }, rectRadius: 0.08 });
slide.addText('Label', { shape: pptx.ShapeType.roundRect, x: 1, y: 3.2, w: 2, h: 0.5, fill: { color: 'FFF8E1' }, line: { color: 'FFB300' }, align: 'center', valign: 'middle' }); // shape with text
slide.addShape(pptx.ShapeType.line, { x: 1, y: 4, w: 2, h: 0, flipV: false, line: { color: '4E6E8E', width: 1.5, endArrowType: 'triangle' } }); // arrow
```

Lines run top-left to bottom-right; use `flipH` / `flipV` for other directions.

## Charts

```js
slide.addChart(pptx.charts.BAR, [{ name: 'Sales', labels: ['Q1','Q2','Q3'], values: [45, 55, 62] }], {
  ...placeholders[0], barDir: 'col', chartColors: ['C62828'], showLegend: false,
  showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 9,
  showCatAxisTitle: true, catAxisTitle: 'Quarter', showValAxisTitle: true, valAxisTitle: 'Sales ($k)',
  valAxisMinVal: 0, catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
});
```

Types: `BAR` (`barDir: 'col'|'bar'`), `LINE` (`lineSize`, `lineSmooth`), `AREA`, `PIE` / `DOUGHNUT` (`showPercent`, `legendPos`), `SCATTER`, `RADAR`. Palette: `C62828`, `4E6E8E`, `FFB300`, `9AA5B1`, `8E0000`.
`scripts/templates.js` exports `addChart(slide, pptx, area, spec, theme)` and `addTable(...)` with the deck styling.

## Tables

```js
slide.addTable([
  [{ text: 'Product', options: { bold: true, fill: { color: 'C62828' }, color: 'FFFFFF' } }, { text: 'Revenue', options: { bold: true, fill: { color: 'C62828' }, color: 'FFFFFF' } }],
  ['A', '$50M'], ['B', '$35M'],
], { x: 0.5, y: 1, w: 9, colW: [5, 4], rowH: 0.35, fontFace: 'Arial', fontSize: 11, margin: [0, 0.08, 0, 0.08], border: { type: 'solid', pt: 0.75, color: 'D7DEE8' }, valign: 'middle' });
```

Merged cells: `{ text, options: { colspan: 3 } }`. Overflowing tables can set `autoPage: true`.

## Images

```js
const w = h * (imgW / imgH);
slide.addImage({ path: 'chart.png', x: (10 - w) / 2, y: 1.5, w, h });
```
