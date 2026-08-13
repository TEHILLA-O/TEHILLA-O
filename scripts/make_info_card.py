#!/usr/bin/env python3
"""Neofetch-style animated info card SVG for tehilla-o."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC", "0") == "1"

ROWS = [
    ("User", "tehilla-o"),
    ("Now", "ML systems · automation · SaaS hardening"),
    ("Focus", "Cheap, scalable pipelines that ship"),
    ("Stack", "Python · TS · React · Docker · PyTorch"),
    ("Projects", "cv.omnites.dev"),
    ("Open to", "ML / automation collaborations"),
]


def main() -> None:
    width, height = 490, 280
    row_svgs = []
    for i, (k, v) in enumerate(ROWS):
        y = 78 + i * 28
        delay = 0.12 + i * 0.14
        if STATIC:
            row_svgs.append(
                f"<g>"
                f'<text x="28" y="{y}" class="key">{k}</text>'
                f'<text x="120" y="{y}" class="val">{v}</text>'
                f"</g>"
            )
        else:
            row_svgs.append(
                f'<g opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{delay}s" dur="0.4s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" from="0 10" to="0 0" '
                f'begin="{delay}s" dur="0.4s" fill="freeze"/>'
                f'<text x="28" y="{y}" class="key">{k}</text>'
                f'<text x="120" y="{y}" class="val">{v}</text>'
                f"</g>"
            )

    title_block = (
        f'<text class="title" x="28" y="58">TEHILLA-O</text>'
        if STATIC
        else (
            '<text class="title" x="28" y="58" opacity="0">'
            '<animate attributeName="opacity" from="0" to="1" begin="0.05s" dur="0.3s" fill="freeze"/>'
            "TEHILLA-O</text>"
        )
    )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .panel {{ fill: #0d1117; stroke: #30363d; stroke-width: 1; }}
    .bar {{ fill: #161b22; }}
    .dot-r {{ fill: #ff5f56; }}
    .dot-y {{ fill: #ffbd2e; }}
    .dot-g {{ fill: #27c93f; }}
    .title {{ fill: #58a6ff; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }}
    .key {{ fill: #3fb950; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; font-weight: 700; }}
    .val {{ fill: #c9d1d9; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }}
    .prompt {{ fill: #8b949e; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; }}
  </style>
  <rect class="panel" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"/>
  <rect class="bar" x="0.5" y="0.5" width="{width - 1}" height="36" rx="10"/>
  <rect class="bar" x="0.5" y="20" width="{width - 1}" height="16"/>
  <circle class="dot-r" cx="18" cy="18" r="5"/>
  <circle class="dot-y" cx="36" cy="18" r="5"/>
  <circle class="dot-g" cx="54" cy="18" r="5"/>
  <text class="prompt" x="74" y="22">tehilla-o@github — whoami</text>
  {title_block}
  {''.join(row_svgs)}
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
