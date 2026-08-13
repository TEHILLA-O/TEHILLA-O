#!/usr/bin/env python3
"""
Animated ASCII SVG.

- Default: big monogram "T" (no photo needed).
- Optional photo mode: python make_ascii_svg.py --from-image source-prepped.png
  (requires pillow; run prep_photo.py first).
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tehilla-ascii.svg"

RAMP = " .:-=+*#%@"  # fewer steps, stronger jumps = more contrast

# 7x5 block letter "T" for monogram fallback
GLYPH_T = [
    "#####",
    "  #  ",
    "  #  ",
    "  #  ",
    "  #  ",
    "  #  ",
    "  #  ",
]


def monogram_grid(scale: int = 6) -> list[str]:
    rows: list[str] = []
    for line in GLYPH_T:
        scaled = "".join(ch * scale for ch in line)
        for _ in range(scale // 2 or 1):
            # pad sides for portrait feel
            rows.append((" " * (scale * 2)) + scaled + (" " * (scale * 2)))
    # title under monogram
    label = "TEHILLA-O"
    pad = max(0, (len(rows[0]) - len(label)) // 2)
    rows.append("")
    rows.append(" " * pad + label)
    return rows


def image_to_grid(path: Path, cols: int = 96) -> list[str]:
    from PIL import Image  # type: ignore

    img = Image.open(path).convert("L")
    w, h = img.size
    aspect = 0.52
    rows = max(12, int(cols * (h / w) * aspect))
    img = img.resize((cols, rows), Image.Resampling.LANCZOS)
    px = img.load()
    out = []
    n = len(RAMP) - 1
    for y in range(rows):
        line = []
        for x in range(cols):
            v = px[x, y]
            # hard contrast: crush near-white to space, stretch the rest
            if v >= 245:
                line.append(" ")
                continue
            # gamma < 1 => midtones darker => denser glyphs on face
            t = max(0.0, min(1.0, (255 - v) / 255.0))
            t = t ** 0.72
            idx = int(round(t * n))
            line.append(RAMP[idx])
        out.append("".join(line).rstrip())
    return out


def write_svg(grid: list[str], out: Path) -> None:
    # monospace metrics
    font_size = 9
    char_w = 5.4
    line_h = 11
    pad = 16
    cols = max(len(r) for r in grid) if grid else 1
    width = int(pad * 2 + cols * char_w)
    height = int(pad * 2 + len(grid) * line_h + 8)

    texts = []
    for i, row in enumerate(grid):
        y = pad + (i + 1) * line_h
        delay = 0.05 + i * 0.045
        # row wipe via clipPath + animate
        clip_id = f"c{i}"
        texts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{y - line_h}" width="0" height="{line_h + 2}">'
            f'<animate attributeName="width" from="0" to="{width}" begin="{delay:.3f}s" dur="0.28s" fill="freeze"/>'
            f"</rect></clipPath>"
            f'<text x="{pad}" y="{y}" class="ascii" clip-path="url(#{clip_id})">'
            f"{_xml_escape(row)}</text>"
            # tiny cursor block
            f'<rect x="{pad}" y="{y - line_h + 2}" width="6" height="{line_h - 2}" class="cursor" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;0" begin="{delay:.3f}s" dur="0.28s" fill="freeze"/>'
            f'<animate attributeName="x" from="{pad}" to="{width - pad - 6}" begin="{delay:.3f}s" dur="0.28s" fill="freeze"/>'
            f"</rect>"
        )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .bg {{ fill: #0d1117; }}
    .ascii {{
      fill: #c9d1d9;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: {font_size}px;
      white-space: pre;
    }}
    .cursor {{ fill: #58a6ff; }}
  </style>
  <rect class="bg" width="100%" height="100%" rx="10"/>
  {''.join(texts)}
</svg>
"""
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out} ({len(grid)} rows)")


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-image", type=Path, default=None)
    args = ap.parse_args()
    if args.from_image:
        grid = image_to_grid(args.from_image)
    else:
        grid = monogram_grid()
    write_svg(grid, OUT)


if __name__ == "__main__":
    main()
