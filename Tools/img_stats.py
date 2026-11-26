"""Objective colour / exposure metrics for a hero side-by-side (LEFT = reference, RIGHT = our Unity render).

Usage (Blender's bundled Python has numpy; no PIL needed):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/img_stats.py Captures/compare/hero_vs_reference_9x16.png
Works on any CaptureTools side-by-side (two equal halves separated by a 12 px gap). Prints, for the whole frame and
for fixed screen regions of the 9:16 hero framing, mean brightness V, saturation S, luminance percentiles and the
dark / saturated pixel fractions, reference vs ours, plus a coarse 0-10 "palette match" (Lab distance of 24x42 thumbnails).
Numbers are a guide for exposure / palette work; the owner judges by eye.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png  # noqa: E402

GAP = 12
# name: (x0, y0, x1, y1) as fractions of one 9:16 half (hero framing: mascot centred, tunnel ahead above him)
REGIONS = {
    "frame": (0.00, 0.00, 1.00, 1.00),
    "walls_upper_left": (0.00, 0.03, 0.30, 0.40),
    "walls_upper_right": (0.70, 0.03, 1.00, 0.40),
    "tunnel_ahead": (0.30, 0.10, 0.70, 0.30),
    "hat_zone": (0.30, 0.32, 0.70, 0.55),
    "body_zone": (0.30, 0.55, 0.70, 0.75),
    "sides_mid": (0.00, 0.40, 0.25, 0.75),
    "bottom_water_fx": (0.00, 0.78, 1.00, 1.00),
}


def halves(img):
    h, w = img.shape[:2]
    half = (w - GAP) // 2
    return img[:, :half, :3], img[:, half + GAP:half + GAP + half, :3]


def hsv(rgb):
    c = rgb.astype(np.float32) / 255.0
    mx, mn = c.max(-1), c.min(-1)
    s = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    return mx, s


def lum(rgb):
    c = rgb.astype(np.float32) / 255.0
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def to_lab(rgb):
    c = rgb.astype(np.float32) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], np.float32)
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883], np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def thumb(rgb, tw=24, th=42):
    h, w = rgb.shape[:2]
    ys = (np.arange(th + 1) * h // th)
    xs = (np.arange(tw + 1) * w // tw)
    out = np.zeros((th, tw, 3), np.float32)
    for j in range(th):
        for i in range(tw):
            out[j, i] = rgb[ys[j]:ys[j + 1], xs[i]:xs[i + 1]].reshape(-1, 3).mean(0)
    return out


def stats(rgb):
    v, s = hsv(rgb)
    l = lum(rgb)
    mean = rgb.reshape(-1, 3).mean(0)
    return {
        "V": v.mean(), "S": s.mean(), "L10": np.percentile(l, 10), "L50": np.percentile(l, 50), "L90": np.percentile(l, 90),
        "dark": (v < 0.35).mean(), "sat": (s > 0.55).mean(), "rgb": "#%02x%02x%02x" % tuple(int(x) for x in mean),
    }


def crop(img, r):
    h, w = img.shape[:2]
    return img[int(r[1] * h):int(r[3] * h), int(r[0] * w):int(r[2] * w)]


def main(path):
    ref, ours = halves(read_png(path))
    print("%-18s %-28s %-28s" % ("region", "REFERENCE  V   S   L50 dark sat", "OURS       V   S   L50 dark sat"))
    for name, r in REGIONS.items():
        a, b = stats(crop(ref, r)), stats(crop(ours, r))
        fmt = lambda d: "%s %.2f %.2f %.2f %.2f %.2f" % (d["rgb"], d["V"], d["S"], d["L50"], d["dark"], d["sat"])
        print("%-18s %-28s %-28s" % (name, fmt(a), fmt(b)))
    ta, tb = to_lab(thumb(ref)), to_lab(thumb(ours))
    de = np.sqrt(((ta - tb) ** 2).sum(-1)).mean()
    print("palette distance (mean dE of 24x42 thumbnails): %.1f  -> coarse palette match %.1f/10" % (de, max(0.0, 10.0 - de / 5.0)))


if __name__ == "__main__":
    main(sys.argv[1])
