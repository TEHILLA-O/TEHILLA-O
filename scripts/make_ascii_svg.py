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

# Longer ramp = more midtone steps on dark skin (avoids solid @ face)
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

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


def image_to_grid(path: Path, cols: int = 112) -> list[str]:
    from PIL import Image  # type: ignore

    img = Image.open(path).convert("L")
    w, h = img.size
    # Slightly taller cells so facial features get more rows
    aspect = 0.55
    rows = max(12, int(cols * (h / w) * aspect))
    img = img.resize((cols, rows), Image.Resampling.LANCZOS)
    px = img.load()
    out = []
    n = len(RAMP) - 1
    for y in range(rows):
        line = []
        for x in range(cols):
            v = px[x, y]
            # paper plate / turtleneck highlights -> empty
            if v >= 248:
                line.append(" ")
                continue
            # Linear map: bright -> sparse, dark -> dense.
            # Gamma > 1 softens crush so dark-skin midtones keep variety.
            t = max(0.0, min(1.0, (255 - v) / 255.0))
            t = t ** 1.15
            idx = int(round(t * n))
            line.append(RAMP[idx])
        out.append("".join(line).rstrip())
    return out


def write_svg(grid: list[str], out: Path, *, light: bool = False) -> None:
    # monospace metrics
    # denser grid for portrait detail
    font_size = 7 if light else 8
    char_w = 4.4 if light else 4.8
    line_h = 9 if light else 10
    pad = 14
    cols = max((len(r) for r in grid), default=1)
    width = int(pad * 2 + cols * char_w)
    height = int(pad * 2 + len(grid) * line_h + 8)

    bg = "#f0f3f6" if light else "#0d1117"
    fg = "#0d1117" if light else "#c9d1d9"
    cursor = "#0969da" if light else "#58a6ff"
    border = "#d0d7de" if light else "#30363d"

    texts = []
    for i, row in enumerate(grid):
        y = pad + (i + 1) * line_h
        delay = 0.04 + i * 0.035
        clip_id = f"c{i}"
        texts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{y - line_h}" width="0" height="{line_h + 2}">'
            f'<animate attributeName="width" from="0" to="{width}" begin="{delay:.3f}s" dur="0.25s" fill="freeze"/>'
            f"</rect></clipPath>"
            f'<text x="{pad}" y="{y}" class="ascii" clip-path="url(#{clip_id})">'
            f"{_xml_escape(row)}</text>"
            f'<rect x="{pad}" y="{y - line_h + 2}" width="5" height="{line_h - 2}" class="cursor" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;0" begin="{delay:.3f}s" dur="0.25s" fill="freeze"/>'
            f'<animate attributeName="x" from="{pad}" to="{width - pad - 5}" begin="{delay:.3f}s" dur="0.25s" fill="freeze"/>'
            f"</rect>"
        )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .bg {{ fill: {bg}; stroke: {border}; stroke-width: 1; }}
    .ascii {{
      fill: {fg};
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: {font_size}px;
      white-space: pre;
    }}
    .cursor {{ fill: {cursor}; }}
  </style>
  <rect class="bg" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"/>
  {''.join(texts)}
</svg>
"""
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out} ({len(grid)} rows, light={light})")


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-image", type=Path, default=None)
    ap.add_argument("--light", action="store_true", help="Force light paper card")
    ap.add_argument("--dark", action="store_true", help="Force dark card")
    args = ap.parse_args()
    if args.from_image:
        grid = image_to_grid(args.from_image)
        # Portraits default to light paper for readable face detail
        light = False if args.dark else True
    else:
        grid = monogram_grid()
        light = args.light and not args.dark
    write_svg(grid, OUT, light=light)


if __name__ == "__main__":
    main()
