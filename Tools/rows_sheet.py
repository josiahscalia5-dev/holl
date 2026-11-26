"""Stack rows of images into one sheet; every row has its own height (mixes 16:9 reference frames and 9:16 game frames).
Stdlib + numpy (Blender's bundled Python), no PIL. Output belongs in Captures/ (gitignored) when it shows reference pixels.

Usage: python -I Tools/rows_sheet.py OUT.png ROW_HEIGHT img1.png img2.png ... -- ROW_HEIGHT img.png ... [-- ...]
Example (reference row 300 px high, recordings 480 px high):
  python -I Tools/rows_sheet.py Captures/milestones/x.png 300 ref0.png ref1.png -- 480 old0.png old1.png -- 480 new0.png new1.png
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

BG = (20, 12, 36)
GAP = 8


def fit_h(img, th):
    h, w, _ = img.shape
    tw = max(1, int(round(w * th / h)))
    ys = (np.arange(th) * h / th).astype(int)
    xs = (np.arange(tw) * w / tw).astype(int)
    ys1 = np.minimum(ys + max(1, h // th // 2), h - 1)
    xs1 = np.minimum(xs + max(1, w // tw // 2), w - 1)
    f = img[..., :3].astype(np.float32)
    return ((f[ys][:, xs] + f[ys1][:, xs] + f[ys][:, xs1] + f[ys1][:, xs1]) / 4).astype(np.uint8)


def main(argv):
    out, rest = argv[0], argv[1:]
    rows, cur = [], []
    for a in rest:
        if a == "--":
            if cur:
                rows.append(cur)
            cur = []
        else:
            cur.append(a)
    if cur:
        rows.append(cur)
    built = []
    for r in rows:
        th = int(r[0])
        tiles = [fit_h(read_png(p), th) for p in r[1:]]
        w = sum(t.shape[1] for t in tiles) + GAP * (len(tiles) - 1)
        row = np.full((th, w, 3), BG, dtype=np.uint8)
        x = 0
        for t in tiles:
            row[:, x:x + t.shape[1]] = t
            x += t.shape[1] + GAP
        built.append(row)
    W = max(r.shape[1] for r in built)
    H = sum(r.shape[0] for r in built) + GAP * (len(built) - 1)
    sheet = np.full((H, W, 3), BG, dtype=np.uint8)
    y = 0
    for r in built:
        sheet[y:y + r.shape[0], :r.shape[1]] = r
        y += r.shape[0] + GAP
    write_png(out, sheet)
    print(f"wrote {out} {W} x {H}")


if __name__ == "__main__":
    main(sys.argv[1:])
