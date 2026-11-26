"""Cut an object out of an image with a hand-traced polygon -> RGBA PNG with a soft transparent background.

Used to prepare ISOLATED crops for the hosted TRELLIS.2 image-to-3D demo (Tools/trellis_client.py), so the demo never
needs its own background-removal step. Input and output images of reference frames stay in Captures/ (private).

Usage ("C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/mask_polygon.py ...):
  mask_polygon.py IN.png OUT_RGBA.png POINTS_FILE [--scale S] [--feather PX] [--preview PREVIEW.png]
POINTS_FILE: "x,y" pairs separated by spaces/newlines (the outline, in order); --scale multiplies them (points traced on
a half-size view -> --scale 2). --feather = soft edge width in pixels (default 2). --preview writes the cutout over grey.
"""
import os
import struct
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402


def polygon_mask(h, w, pts):
    m = np.zeros((h, w), dtype=np.float32)
    xs, ys = pts[:, 0], pts[:, 1]
    x0, y0, x1, y1 = xs, ys, np.roll(xs, -1), np.roll(ys, -1)
    for y in range(h):
        yc = y + 0.5
        hit = ((y0 <= yc) & (y1 > yc)) | ((y1 <= yc) & (y0 > yc))
        if not hit.any():
            continue
        xi = np.sort(x0[hit] + (yc - y0[hit]) * (x1[hit] - x0[hit]) / (y1[hit] - y0[hit]))
        for a, b in zip(xi[0::2], xi[1::2]):
            m[y, max(0, int(np.ceil(a - 0.5))):min(w, int(np.floor(b - 0.5)) + 1)] = 1.0
    return m


def box_blur(m, r):
    if r <= 0:
        return m
    k = 2 * r + 1
    p = np.pad(m, r, mode="edge")
    c = p.cumsum(0); c = np.vstack([np.zeros((1, c.shape[1])), c]); v = (c[k:] - c[:-k]) / k
    c = v.cumsum(1); c = np.hstack([np.zeros((c.shape[0], 1)), c]); return (c[:, k:] - c[:, :-k]) / k


def write_rgba(path, rgba):
    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))   # filter 0 rows
    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__); sys.exit(1)
    src, dst, ptsf = a[0], a[1], a[2]
    opt = {"--scale": "1", "--feather": "2", "--preview": ""}
    for i in range(3, len(a) - 1):
        if a[i] in opt: opt[a[i]] = a[i + 1]
    txt = open(ptsf, encoding="utf-8").read().replace("\n", " ").split()
    pts = np.array([[float(v) for v in p.split(",")] for p in txt if "," in p], dtype=np.float64) * float(opt["--scale"])
    img = read_png(src)[:, :, :3]
    h, w = img.shape[:2]
    m = box_blur(polygon_mask(h, w, pts), int(opt["--feather"]))
    alpha = np.clip(m * 255 + 0.5, 0, 255).astype(np.uint8)
    rgba = np.dstack([img * (alpha[:, :, None] > 0), alpha]).astype(np.uint8)
    write_rgba(dst, rgba)
    print(f"wrote {dst} {w}x{h}, object covers {100 * (alpha > 127).mean():.1f} % of the image")
    if opt["--preview"]:
        g = np.full_like(img, 96, dtype=np.float32)
        f = m[:, :, None]
        write_png(opt["--preview"], (img * f + g * (1 - f)).astype(np.uint8)[::2, ::2])
        print("preview", opt["--preview"])


if __name__ == "__main__":
    main()
