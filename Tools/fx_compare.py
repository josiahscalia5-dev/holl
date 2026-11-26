"""Side-by-side + silhouette IoU of a Blender shot preview against the reference (round 6 water/FX shot tests).

Usage: python -I Tools/fx_compare.py REF.png PREVIEW.png OUT_SHEET.png X0 Y0 X1 Y1 [MASK_PREVIEW.png REFMASK1.png ...]
Writes reference crop | preview crop (| mask overlay: white = both, cyan = reference only, magenta = ours only).
Output contains reference pixels -> Captures/ only.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

ref, pv, out = sys.argv[1], sys.argv[2], sys.argv[3]
x0, y0, x1, y1 = map(int, sys.argv[4:8])
R = read_png(ref)[:, :, :3]
P = read_png(pv)[:, :, :3]
tiles = [R[y0:y1, x0:x1], P[y0:y1, x0:x1]]
if len(sys.argv) > 9:
    pm = read_png(sys.argv[8])[:, :, :3].mean(-1) > 128
    rm = np.zeros(pm.shape, bool)
    for f in sys.argv[9:]:
        rm |= read_png(f)[:, :, :3].mean(-1) > 128
    inter, union = (pm & rm).sum(), (pm | rm).sum()
    print("IoU %.3f  (ref %d px, ours %d px, both %d, ref-only %d, ours-only %d)" % (
        inter / max(union, 1), rm.sum(), pm.sum(), inter, (rm & ~pm).sum(), (pm & ~rm).sum()))
    ov = np.zeros(R.shape, np.uint8)
    ov[rm & pm] = (255, 255, 255)
    ov[rm & ~pm] = (0, 220, 255)
    ov[pm & ~rm] = (255, 0, 200)
    tiles.append(ov[y0:y1, x0:x1])
gap = 6
h = y1 - y0
sheet = np.full((h, sum(t.shape[1] for t in tiles) + gap * (len(tiles) - 1), 3), 20, np.uint8)
x = 0
for t in tiles:
    sheet[:, x:x + t.shape[1]] = t
    x += t.shape[1] + gap
write_png(out, sheet)
print("wrote", out, sheet.shape)
