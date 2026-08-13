#!/usr/bin/env python3
"""
Prep a portrait for ASCII conversion.

Requires (optional deps): pillow, numpy, opencv-python, rembg

Usage:
  python scripts/prep_photo.py path/to/photo.jpg
  # writes source-prepped.png in repo root
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "source-prepped.png"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/prep_photo.py <photo.jpg>")

    src = Path(sys.argv[1])
    if not src.exists():
        raise SystemExit(f"Not found: {src}")

    try:
        import cv2
        import numpy as np
        from PIL import Image
        from rembg import remove
    except ImportError as e:
        raise SystemExit(
            "Install portrait deps: pip install pillow numpy opencv-python rembg\n"
            f"Missing: {e}"
        ) from e

    raw = Path(src).read_bytes()
    cut = remove(raw)
    img = Image.open(__import__("io").BytesIO(cut)).convert("RGBA")

    # composite onto white
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    composed = Image.alpha_composite(bg, img).convert("RGB")

    # CLAHE on L channel via OpenCV
    arr = np.array(composed)
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    rgb = cv2.cvtColor(lab2, cv2.COLOR_LAB2RGB)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    Image.fromarray(gray).save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
