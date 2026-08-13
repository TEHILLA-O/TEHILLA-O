#!/usr/bin/env python3
"""
Prep portrait for ASCII — dark-skin aware.

Keeps facial midtones (eyes / nose / lips / cheek light) instead of
crushing skin into a solid silhouette. Studio black is removed via
corner flood-fill so hair silhouette stays.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "source-prepped.png"

DEFAULT_PHOTO = Path(
    r"C:\Users\user\.cursor\projects\c-Users-user-Desktop-live-apps-me-redme\assets"
    r"\c__Users_user_AppData_Roaming_Cursor_User_workspaceStorage_a3fb26917b81007645c2c3ee312bf520"
    r"_images_photo_2026-08-13_21-36-34-e6d14a04-ceb8-4a6a-a8c9-d376936541b6.png"
)


def face_shoulders_crop(img: Image.Image) -> Image.Image:
    w, h = img.size
    left, right = int(w * 0.10), int(w * 0.90)
    top, bottom = int(h * 0.00), int(h * 0.46)
    crop = img.crop((left, top, right, bottom))
    cw, ch = crop.size
    z = 1.10
    nw, nh = int(cw / z), int(ch / z)
    cx, cy = cw // 2, int(ch * 0.36)
    l2 = max(0, cx - nw // 2)
    t2 = max(0, cy - nh // 2)
    return crop.crop((l2, t2, l2 + nw, t2 + nh))


def studio_bg_mask(bgr: np.ndarray) -> np.ndarray:
    """True where studio backdrop is (flood from corners on near-black)."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # seed = very dark pixels (backdrop). Hair is also dark but not reachable
    # from corners without crossing brighter face/collar edges as much —
    # use a modest threshold + morphological close on the flood result only.
    seeds = (gray < 22).astype(np.uint8) * 255
    h, w = gray.shape
    flood = np.zeros((h + 2, w + 2), np.uint8)
    mask = np.zeros_like(gray, dtype=np.uint8)
    for y, x in [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1), (0, w // 2), (h // 2, 0), (h // 2, w - 1)]:
        if seeds[y, x] == 0:
            continue
        tmp = seeds.copy()
        cv2.floodFill(tmp, flood, (x, y), 128, loDiff=8, upDiff=8, flags=4 | (255 << 8))
        mask = np.maximum(mask, (tmp == 128).astype(np.uint8) * 255)
    # grow slightly so hair edge against bg is clean white plate
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
    return mask > 0


def clahe_lab(bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l2, a, b]), cv2.COLOR_LAB2BGR)


def stretch_skin_mids(gray: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """
    Expand the dark-skin luminance band so ASCII gets many glyph steps
    on the face, without bleaching to white.
    """
    out = gray.astype(np.float32)
    subject = ~bg
    if not np.any(subject):
        return gray

    vals = out[subject]
    # percentile window of subject (face + clothes)
    lo, hi = np.percentile(vals, [2, 98])
    if hi - lo < 8:
        hi = lo + 8

    # Map subject tones into a readable band for glyph ramps:
    # deepest shadow ~35, brightest highlight ~235 (turtleneck stays bright)
    mapped = (out - lo) / (hi - lo)
    mapped = np.clip(mapped, 0, 1)
    # slight lift of deep mids (dark skin) without flattening highlights
    mapped = np.power(mapped, 0.78)
    stretched = mapped * 200.0 + 35.0

    result = out.copy()
    result[subject] = stretched[subject]
    result[bg] = 255.0
    return np.clip(result, 0, 255).astype(np.uint8)


def refine(gray: np.ndarray, bg: np.ndarray) -> Image.Image:
    # mild bilateral + unsharp for eyes / nose / mustache edges
    soft = cv2.bilateralFilter(gray, d=5, sigmaColor=35, sigmaSpace=35)
    blur = cv2.GaussianBlur(soft, (0, 0), 1.1)
    sharp = cv2.addWeighted(soft, 1.65, blur, -0.65, 0)
    sharp = np.where(bg, 255, sharp).astype(np.uint8)

    img = Image.fromarray(sharp, mode="L")
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=2))
    arr = np.asarray(img).copy()
    arr[bg] = 255
    return Image.fromarray(arr, mode="L")


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PHOTO
    if not src.exists():
        raise SystemExit(f"Photo not found: {src}")

    print(f"Using {src}")
    rgb = face_shoulders_crop(Image.open(src).convert("RGB"))
    bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)

    bg = studio_bg_mask(bgr)
    enhanced = clahe_lab(bgr)
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    stretched = stretch_skin_mids(gray, bg)
    final = refine(stretched, bg)

    final.save(OUT)
    # quick stats for tuning
    subj = np.asarray(final)[~bg]
    print(
        f"Wrote {OUT} size={final.size} "
        f"subject_mean={subj.mean():.1f} p10={np.percentile(subj,10):.0f} "
        f"p50={np.percentile(subj,50):.0f} p90={np.percentile(subj,90):.0f}"
    )


if __name__ == "__main__":
    main()
