# Validation

Validate every generated deck before delivery.

## Required Checks

The HTML converter validates:

- Slide dimensions match the PowerPoint layout.
- HTML content does not overflow the slide body.
- Large text does not land too close to the bottom edge.
- Unsupported CSS patterns such as gradients are rejected.

Run generation until the converter completes cleanly.

## Text Inventory

Use text inventory to inspect extracted text boxes and detect likely overflow or overlap.

```bash
python pptx-enhanced/scripts/inventory.py output.pptx workspace/inventory.json
python pptx-enhanced/scripts/inventory.py --issues-only output.pptx workspace/inventory-issues.json
```

Treat inventory issues as review signals. Some PowerPoint text-frame warnings can be conservative, so inspect the deck or thumbnails before making large changes.

## Thumbnail Grid

Use thumbnail validation when LibreOffice and Poppler are installed.

```bash
python pptx-enhanced/scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```

If LibreOffice or Poppler is missing, say that thumbnail validation could not run and rely on converter validation plus inventory output.

## Common Fixes

- Reduce card copy before reducing font size.
- Split dense slides into two slides.
- Lower image width or add `max-height`.
- Move summary callouts upward or shorten them.
- Use fewer process steps per row.
- Keep bottom bars at about `35pt` height and leave `50pt` clearance above them.
- For CJK text, use fewer words and wider columns.
