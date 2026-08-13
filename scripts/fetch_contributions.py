#!/usr/bin/env python3
"""Fetch public GitHub contribution calendar HTML (no token) -> data/contributions.json"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "tehilla-o")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contributions.json"

# Approximate activity when GitHub omits data-count
LEVEL_COUNT = {0: 0, 1: 1, 2: 3, 3: 6, 4: 9, 5: 12}


def parse_level(cell) -> int:
    for attr in ("data-level", "data-contribution-level"):
        if cell.has_attr(attr):
            try:
                return int(cell[attr])
            except ValueError:
                pass
    # class like ContributionCalendar-day … level-2
    for c in cell.get("class", []):
        if c.startswith("ContributionCalendar-level-") or c.startswith("level-"):
            try:
                return int(c.rsplit("-", 1)[-1])
            except ValueError:
                pass
    return 0


def main() -> None:
    url = f"https://github.com/users/{USERNAME}/contributions"
    resp = requests.get(
        url,
        headers={"User-Agent": "tehilla-o-profile-art"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    for cell in soup.select("td.ContributionCalendar-day, rect.ContributionCalendar-day"):
        d = cell.get("data-date")
        if not d:
            continue
        level = parse_level(cell)
        count = None
        if cell.has_attr("data-count"):
            try:
                count = int(cell["data-count"])
            except ValueError:
                count = None
        if count is None:
            count = LEVEL_COUNT.get(level, 0)
        days.append(
            {
                "date": d,
                "count": count,
                "level": level,
            }
        )

    days.sort(key=lambda x: x["date"])

    # derived stats
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda x: x["count"], default=None)
    monthly: dict[str, int] = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    # streaks (count > 0)
    current_streak = 0
    longest_streak = 0
    run = 0
    today = date.today().isoformat()
    for d in days:
        if d["count"] > 0:
            run += 1
            longest_streak = max(longest_streak, run)
        else:
            run = 0
    # current streak from the end
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["count"] > 0:
            current_streak += 1
        else:
            if d["date"] == today:
                continue
            break

    payload = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best,
        "monthly_totals": dict(sorted(monthly.items())),
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(days)} days, {total} contributions)")


if __name__ == "__main__":
    main()
