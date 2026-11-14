#!/usr/bin/env python3
"""Arrange multiple chart images into a review grid.

Usage:
    python preview_grid.py <img1> [img2 ...] <output> [--cols 3] [--padding 20] [--bg white]

Examples:
    python preview_grid.py chart1.png chart2.png chart3.png grid.png
    python preview_grid.py chart1.png chart2.png chart3.png chart4.png grid.png --cols 2
    python preview_grid.py *.png grid.png --cols 4 --padding 30
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_grid(image_paths: list[Path], output_path: Path, cols: int = 3,
                padding: int = 20, bg_color: str = "white",
                label: bool = True) -> None:
    """Arrange images into a grid and save."""
    images = []
    for p in image_paths:
        if not p.exists():
            print(f"Warning: Skipping missing file: {p}", file=sys.stderr)
            continue
        try:
            img = Image.open(p)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            images.append((p.stem, img))
        except Exception as e:
            print(f"Warning: Could not open {p}: {e}", file=sys.stderr)

    if not images:
        print("Error: No valid images to arrange.", file=sys.stderr)
        sys.exit(1)

    n = len(images)
    rows = (n + cols - 1) // cols

    # Compute uniform cell size (scale all images to fit the largest)
    max_w = max(img.width for _, img in images)
    max_h = max(img.height for _, img in images)

    label_h = 30 if label else 0
    cell_w = max_w + padding
    cell_h = max_h + padding + label_h

    grid_w = cols * cell_w + padding
    grid_h = rows * cell_h + padding

    grid = Image.new("RGB", (grid_w, grid_h), bg_color)
    draw = ImageDraw.Draw(grid)

    # Try to use a clean font for labels
    try:
        font = ImageFont.truetype("Arial", 14)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except OSError:
            font = ImageFont.load_default()

    for i, (name, img) in enumerate(images):
        row, col_idx = divmod(i, cols)
        x = col_idx * cell_w + padding
        y = row * cell_h + padding

        # Scale image to fit cell while preserving aspect ratio
        scale = min(max_w / img.width, max_h / img.height)
        if scale < 1:
            new_w = int(img.width * scale)
            new_h = int(img.height * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        # Center in cell
        offset_x = (max_w - img.width) // 2
        offset_y = (max_h - img.height) // 2

        # Paste (handle transparency)
        if img.mode == "RGBA":
            grid.paste(img, (x + offset_x, y + offset_y + label_h), mask=img)
        else:
            grid.paste(img, (x + offset_x, y + offset_y + label_h))

        # Draw label
        if label:
            text = name[:40]
            draw.text((x + 4, y + 4), text, fill="#333333", font=font)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output_path, quality=95)
    print(f"Grid saved to {output_path} ({n} images, {cols}x{rows})")


def main():
    parser = argparse.ArgumentParser(
        description="Arrange multiple chart images into a review grid."
    )
    parser.add_argument("images", nargs="+", type=Path,
                        help="Image files (last argument is output if --output not given)")
    parser.add_argument("--output", "-o", type=Path, help="Output image path")
    parser.add_argument("--cols", type=int, default=3, help="Number of columns (default: 3)")
    parser.add_argument("--padding", type=int, default=20, help="Padding between images in pixels")
    parser.add_argument("--bg", default="white", help="Background color (default: white)")
    parser.add_argument("--no-labels", action="store_true", help="Disable filename labels")

    args = parser.parse_args()

    # If --output not given, treat last positional arg as output
    if args.output:
        input_images = args.images
        output = args.output
    else:
        if len(args.images) < 2:
            print("Error: Need at least one input image and one output path.", file=sys.stderr)
            sys.exit(1)
        input_images = args.images[:-1]
        output = args.images[-1]

    create_grid(
        image_paths=input_images,
        output_path=output,
        cols=args.cols,
        padding=args.padding,
        bg_color=args.bg,
        label=not args.no_labels,
    )


if __name__ == "__main__":
    main()
