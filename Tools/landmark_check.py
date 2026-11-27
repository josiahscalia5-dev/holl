"""Landmark-disappearance guard (owner 2026-11-27: "Do not allow improvements to one asset to cause another important asset
to disappear from view"; p4 lost the S5 pink glass pipe and the S6 left cyan star without anyone noticing until the judges).

Compares the mascot-hidden comparison stills (<dir>/bg/) of two builds colour class by colour class (gold, pink liquid,
cyan, neon, milky white, rainbow / sock colours) on a 4 x 3 grid per still. A class whose coverage in the whole still drops
by more than DROP (default 40 %) is reported as LOST; a cell that empties while the still's total stays is reported as MOVED.
No reference pixels are read. Usage (Blender's bundled Python):
  python -I Tools/landmark_check.py PREV_STILLS NEW_STILLS [drop 0..1]
Exit code 1 when anything is LOST (after_wave / the lead should look before accepting the build).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png  # noqa: E402

STILLS = ["01_hall_start_16x9.png", "R2_rear_S2_like_3s_16x9.png", "R3_front_S3_like_5s_16x9.png",
          "R4_front_S4_like_7s_16x9.png", "R5_front_S5_like_8s_16x9.png", "R6_front_S6_like_11s_16x9.png",
          "10_finale_16x9.png", "07_chambers_9x16.png", "hero_mouth_9x16.png"]
SECTION = {"01_hall": "S1", "R2_": "S2", "R3_": "S3", "R4_": "S4", "R5_": "S5", "R6_": "S6", "10_fin": "S7",
           "07_cha": "S5 gameplay", "hero_m": "S2 gameplay"}


def hsv(img):
    rgb = img[..., :3].astype(np.float32) / 255.0
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-6
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
    return h, s, mx


def classes(img):
    h, s, v = hsv(img[::2, ::2])
    return {
        "gold": (h >= 33) & (h <= 58) & (s >= 0.45) & (v >= 0.45),
        "pink liquid / pink neon": (h >= 300) & (h <= 345) & (s >= 0.45) & (v >= 0.55),
        "cyan glass / cyan neon": (h >= 172) & (h <= 200) & (s >= 0.40) & (v >= 0.60),
        "bright neon": (s >= 0.35) & (v >= 0.93) & (((h >= 45) & (h <= 65)) | ((h >= 172) & (h <= 200)) | (h >= 300)),
        "milky white": (s < 0.12) & (v >= 0.85),
        "rainbow / sock colours": (s >= 0.5) & (v >= 0.5) & ((h <= 25) | ((h >= 70) & (h <= 160)) | ((h >= 205) & (h <= 240))),
    }


def grid(mask, rows=3, cols=4):
    H, W = mask.shape
    return np.array([[mask[r * H // rows:(r + 1) * H // rows, c * W // cols:(c + 1) * W // cols].mean()
                      for c in range(cols)] for r in range(rows)])


def main():
    prev, new = sys.argv[1], sys.argv[2]
    drop = float(sys.argv[3]) if len(sys.argv) > 3 else 0.40
    lost, moved = [], []
    for f in STILLS:
        pa, na = os.path.join(prev, "bg", f), os.path.join(new, "bg", f)
        if not (os.path.exists(pa) and os.path.exists(na)):
            continue
        sec = next((v for k, v in SECTION.items() if f.startswith(k)), f)
        cp, cn = classes(read_png(pa)), classes(read_png(na))
        for k in cp:
            tp, tn = cp[k].mean() * 100, cn[k].mean() * 100
            if tp >= 0.4 and tn < tp * (1 - drop):
                lost.append(f"LOST  {sec:12s} {f:32s} {k:24s} {tp:5.2f} % -> {tn:5.2f} %")
                continue
            gp, gn = grid(cp[k]) * 100, grid(cn[k]) * 100
            for (r, c) in zip(*np.where((gp >= 3.0) & (gn < gp * (1 - drop) - 1.0))):
                cell = ["top", "middle", "bottom"][r] + "-" + ["left", "centre-left", "centre-right", "right"][c]
                moved.append((gp[r, c] - gn[r, c], f"MOVED {sec:12s} {f:32s} {k:24s} {cell:20s} {gp[r, c]:5.1f} % -> "
                                                    f"{gn[r, c]:5.1f} % (still total {tp:.2f} -> {tn:.2f} %)"))
    print(f"landmark check {prev} -> {new}: {len(lost)} LOST, {len(moved)} emptied cells (biggest 10 shown; coins and "
          f"animated FX move between builds, so check MOVED lines by eye only for landmarks)")
    for line in lost + [m for _, m in sorted(moved, reverse=True)[:10]]:
        print(line)
    sys.exit(1 if lost else 0)


if __name__ == "__main__":
    main()
