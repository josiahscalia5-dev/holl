"""Tile PNGs into one contact sheet (stdlib + numpy, no PIL). Output belongs in Captures/ (gitignored).
Usage: python -I Tools/contact_sheet.py OUT.png COLS TILE_W IN1.png IN2.png ...
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402


def fit(img, tw):
    h, w, _ = img.shape
    th = int(round(h * tw / w))
    ys = (np.arange(th) * h / th).astype(int); xs = (np.arange(tw) * w / tw).astype(int)
    # box-filter downscale: average a 2x2 neighbourhood of the nearest samples to reduce aliasing
    ys1 = np.minimum(ys + max(1, h // th // 2), h - 1); xs1 = np.minimum(xs + max(1, w // tw // 2), w - 1)
    f = img.astype(np.float32)
    out = (f[ys][:, xs] + f[ys1][:, xs] + f[ys][:, xs1] + f[ys1][:, xs1]) / 4
    return out.astype(np.uint8)


if __name__ == "__main__":
    out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    tiles = [fit(read_png(p), tw) for p in sys.argv[4:]]
    th = max(t.shape[0] for t in tiles); rows = (len(tiles) + cols - 1) // cols; gap = 6
    sheet = np.full((rows * th + (rows - 1) * gap, cols * tw + (cols - 1) * gap, 3), (20, 12, 36), dtype=np.uint8)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet[r * (th + gap):r * (th + gap) + t.shape[0], c * (tw + gap):c * (tw + gap) + tw] = t
    write_png(out, sheet)
    print("wrote", out, sheet.shape[1], "x", sheet.shape[0])
