"""Owner mascot sheet (lead 2026-11-27 17:00, owner 16:55 "show me mascot-only front / side / rear previews, mascot in
gameplay, direct comparison against my approved frame"). One labelled PNG, three rows:
  1. the mascot ALONE: rear | side | front (+ three-quarter when present) - CaptureTools M1..M4 renders
  2. R2 (comparison camera) mascot crop: approved frame | BEFORE build | AFTER
  3. portrait gameplay (hero 9x16) mascot crop: approved (crop) | BEFORE | AFTER
Inputs are CaptureTools side-by-sides (LEFT half = reference, RIGHT half = render): *_vs_reference_16x9.png / _9x16.png.
Output belongs in Captures/ (it shows reference pixels).

Usage (Blender's bundled Python):
  python -I Tools/mascot_owner_sheet.py OUT.png MASCOT_DIR BEFORE_DIR AFTER_DIR "BEFORE LABEL" "AFTER LABEL"
  MASCOT_DIR holds M1_mascot_rear.png, M2_mascot_side_right.png, M3_mascot_front.png [, M4_mascot_three_quarter.png];
  BEFORE_DIR / AFTER_DIR hold R2_vs_reference_16x9.png and hero_vs_reference_9x16.png.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402
from labeled_sheet import caption_bar, fit_w, BG  # noqa: E402

GAP = 10


def halves(path):
    im = read_png(path)[:, :, :3]
    w = im.shape[1]
    h = (w - 12) // 2
    return im[:, :h], im[:, h + 12:h + 12 + h]


def mascot_box(img, box):
    x0, y0, x1, y1 = box
    return img[y0:y1, x0:x1]


def hstack(tiles, h):
    out = []
    for t in tiles:
        th = t.shape[0]
        if th != h:
            t = fit_w(t, max(1, int(round(t.shape[1] * h / th))))[:h]
        out.append(t)
        out.append(np.full((h, GAP, 3), BG, np.uint8))
    return np.concatenate(out[:-1], axis=1)


def main(out, mdir, bdir, adir, blabel, alabel):
    rows = []
    # 1) mascot alone: centre crop of each 1280x720 render
    names = [("M1_mascot_rear", "REAR"), ("M2_mascot_side_right", "SIDE"), ("M3_mascot_front", "FRONT"),
             ("M4_mascot_three_quarter", "THREE-QUARTER")]
    tiles, caps = [], []
    for n, cap in names:
        p = os.path.join(mdir, n + ".png")
        if os.path.exists(p):
            im = read_png(p)[:, :, :3]
            tiles.append(im[40:680, 320:960])
            caps.append(cap)
    if tiles:
        rows.append(("MASCOT ALONE: " + " || ".join(caps) if len(caps) == 1 else " || ".join(caps), hstack(tiles, 640)))
    # 2) R2 mascot crop (the same box on all three: the R2 camera is solved on the reference landmarks)
    ref, before = halves(os.path.join(bdir, "R2_vs_reference_16x9.png"))
    _, after = halves(os.path.join(adir, "R2_vs_reference_16x9.png"))
    box = (380, 150, 900, 640)
    rows.append((f"APPROVED FRAME (LANDSCAPE) || {blabel} || {alabel}",
                 hstack([mascot_box(x, box) for x in (ref, before, after)], box[3] - box[1])))
    # 3) portrait gameplay: lower-middle box with the mascot (reference = the centre crop of the approved frame)
    pref, pb = halves(os.path.join(bdir, "hero_vs_reference_9x16.png"))
    _, pa = halves(os.path.join(adir, "hero_vs_reference_9x16.png"))
    pbox = (60, 560, 660, 1180)
    rows.append((f"PORTRAIT GAMEPLAY: APPROVED (CROP) || {blabel} || {alabel}",
                 hstack([mascot_box(x, pbox) for x in (pref, pb, pa)], pbox[3] - pbox[1])))
    width = 2100
    px = max(2, width // 500)
    blocks = []
    for cap, img in rows:
        blocks.append(caption_bar(cap, width, px))
        blocks.append(fit_w(img, width))
        blocks.append(np.full((GAP, width, 3), BG, np.uint8))
    sheet = np.concatenate(blocks[:-1], axis=0)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    write_png(out, sheet)
    print("wrote", out, sheet.shape[1], "x", sheet.shape[0])


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 6:
        raise SystemExit(__doc__)
    main(*a[:6])
