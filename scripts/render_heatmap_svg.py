#!/usr/bin/env python3
"""Render data/contributions.json as an animated contrib-heatmap.svg"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL = 11
GAP = 3
PAD = 16
FOOTER_H = 48
LEGEND_H = 28


def week_index(iso_date: str, first: str) -> int:
    d0 = datetime.strptime(first, "%Y-%m-%d").date()
    d1 = datetime.strptime(iso_date, "%Y-%m-%d").date()
    # align to week of first day (GitHub weeks start Sunday)
    return (d1.toordinal() - d0.toordinal()) // 7


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"Missing {DATA}; run fetch_contributions.py first")

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    days = payload["days"]
    if not days:
        raise SystemExit("No contribution days found")

    first = days[0]["date"]
    # weekday of first date: Mon=0 … Sun=6 -> GitHub uses Sun=0
    wd0 = (datetime.strptime(first, "%Y-%m-%d").weekday() + 1) % 7

    # grid: weeks columns, rows 0=Sun … 6=Sat
    cells = []
    max_week = 0
    for i, d in enumerate(days):
        # absolute day offset from first calendar cell
        offset = i  # days list is contiguous from GitHub
        # Prefer date math for robustness
        di = datetime.strptime(d["date"], "%Y-%m-%d").date()
        d_first = datetime.strptime(first, "%Y-%m-%d").date()
        # Find Sunday on/before first
        sunday0 = d_first.toordinal() - wd0
        delta = di.toordinal() - sunday0
        week = delta // 7
        dow = delta % 7
        max_week = max(max_week, week)
        level = max(0, min(5, int(d.get("level", 0))))
        if d.get("count", 0) > 0 and level == 0:
            level = 1
        cells.append((week, dow, level, d["date"], d.get("count", 0)))

    weeks = max_week + 1
    grid_w = weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = PAD * 2 + grid_w
    height = PAD + grid_h + LEGEND_H + FOOTER_H

    rects = []
    for week, dow, level, date_s, count in cells:
        x = PAD + week * (CELL + GAP)
        y = PAD + dow * (CELL + GAP)
        delay = (week + dow) * 0.018
        color = PALETTE[level]
        rects.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" '
            f'fill="{color}" opacity="0">'
            f"<title>{date_s}: {count}</title>"
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" dur="0.35s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="-6 -6" to="0 0" '
            f'begin="{delay:.3f}s" dur="0.35s" fill="freeze"/>'
            f"</rect>"
        )

    total = payload.get("total_contributions", 0)
    streak = payload.get("current_streak", 0)
    longest = payload.get("longest_streak", 0)
    legend_y = PAD + grid_h + 14
    legend_x = PAD + grid_w - (6 * (CELL + 4) + 70)

    legend_boxes = []
    for i, c in enumerate(PALETTE):
        lx = legend_x + 40 + i * (CELL + 4)
        legend_boxes.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
        )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .bg {{ fill: #0d1117; }}
    .label {{ fill: #8b949e; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; }}
    .footer {{ fill: #c9d1d9; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }}
  </style>
  <rect class="bg" width="100%" height="100%" rx="8"/>
  {''.join(rects)}
  <text class="label" x="{PAD}" y="{legend_y + 10}">Less</text>
  {''.join(legend_boxes)}
  <text class="label" x="{legend_x + 40 + 6 * (CELL + 4) + 6}" y="{legend_y + 10}">More</text>
  <text class="footer" x="{PAD}" y="{height - 18}">{total:,} contributions in the last year · streak {streak} · best streak {longest}</text>
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT} ({weeks} weeks)")


if __name__ == "__main__":
    main()
