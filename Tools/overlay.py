"""Silhouette / composition overlay from a CaptureTools side-by-side (LEFT half = reference, RIGHT half = our render).

Writes one image with three panels of the same size:
  1. 50/50 blend of reference and ours (where shapes sit, how big they are),
  2. our render with the reference's edges drawn in cyan (geometry / silhouette mismatches),
  3. the reference with OUR edges drawn in magenta.
Output contains reference pixels, so it must go to Captures/ only (gitignored, private).

Usage (Blender's bundled Python has numpy; no system Python on this PC):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/overlay.py SIDE_BY_SIDE.png OUT.png [SCALE]
SCALE (default 0.5) shrinks each panel to keep the file small.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

GAP = 12


def halves(img):
    half = (img.shape[1] - GAP) // 2
    return img[:, :half, :3].astype(np.float32), img[:, half + GAP:half + GAP + half, :3].astype(np.float32)


def resize(img, scale):
    if scale == 1.0:
        return img
    h, w = img.shape[:2]
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    ys = np.minimum(((np.arange(nh) + 0.5) / scale).astype(int), h - 1)
    xs = np.minimum(((np.arange(nw) + 0.5) / scale).astype(int), w - 1)
    # box-average 2x2 neighbourhoods when shrinking to avoid aliasing in the edge maps
    acc = img[ys][:, xs].copy()
    if scale < 1.0:
        ys1, xs1 = np.minimum(ys + 1, h - 1), np.minimum(xs + 1, w - 1)
        acc = (acc + img[ys1][:, xs] + img[ys][:, xs1] + img[ys1][:, xs1]) * 0.25
    return acc


def blur(gray, r=2):
    k = np.ones(2 * r + 1, np.float32) / (2 * r + 1)
    g = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, gray)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, g)


def edges(img):
    gray = blur(img @ np.array([0.299, 0.587, 0.114], np.float32), 2)
    gx = np.zeros_like(gray); gy = np.zeros_like(gray)
    gx[:, 1:-1] = gray[:, 2:] - gray[:, :-2]
    gy[1:-1, :] = gray[2:, :] - gray[:-2, :]
    mag = np.hypot(gx, gy)
    thr = np.percentile(mag, 88)
    return np.clip((mag - thr) / (thr + 1e-3), 0.0, 1.0)


def tint(base, mask, colour, strength=0.9):
    c = np.array(colour, np.float32)
    a = (mask * strength)[..., None]
    return base * (1.0 - a) + c * a


def main(src, out, scale=0.5):
    ref, ours = halves(read_png(src))
    ref, ours = resize(ref, scale), resize(ours, scale)
    blend = 0.5 * ref + 0.5 * ours
    ours_with_ref = tint(ours * 0.75, edges(ref), (0, 255, 255))
    ref_with_ours = tint(ref * 0.75, edges(ours), (255, 0, 220))
    h = ref.shape[0]
    gap = np.full((h, GAP, 3), 24, np.float32)
    img = np.concatenate([blend, gap, ours_with_ref, gap, ref_with_ours], axis=1)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    write_png(out, np.clip(img, 0, 255).astype(np.uint8))
    print("wrote", out, img.shape[1], "x", img.shape[0])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.5)
