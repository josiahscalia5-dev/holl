"""24-asset checklist sheets: owner's library crop | previous build | newest build, per asset, from the SAME capture camera.

Usage (Blender's bundled Python; private output, contains reference pixels -> Captures/ only):
  python -I Tools/asset_checklist.py MAP.json PREV_DIR NEW_DIR OUT_DIR [ROW_H]
MAP.json = {"assets": [{"id": "01", "name": "...", "views": [{"still": "01_hall_start_16x9.png", "box": [x0, y0, x1, y1],
            "bg": false}], "note": "..."}]}  - box in pixels of the still (1280x720 / 720x1280), x1/y1 exclusive;
            bg = true crops PREV_DIR/bg/<still> + NEW_DIR/bg/<still> (mascot hidden) when they exist.
Writes OUT_DIR/A<NN>.png (one row per view: library | previous | newest; coloured header bars: grey = owner library,
orange = previous, green = newest) and OUT_DIR/GROUP_<k>.png (4 assets per sheet, small enough for judges and phones).
"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "Reference", "asset_library", "Original_Crops")
BG = (20, 12, 36)
BARS = [(150, 150, 160), (240, 150, 40), (60, 200, 90)]


def scale_to_h(img, th, max_w):
    h, w, _ = img.shape
    s = min(th / h, max_w / w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    ys = np.minimum((np.arange(nh) / s).astype(int), h - 1)
    xs = np.minimum((np.arange(nw) / s).astype(int), w - 1)
    return img[ys][:, xs]


def panel(img, th, max_w, bar):
    t = scale_to_h(img, th, max_w)
    out = np.full((th + 8, max_w, 3), BG, dtype=np.uint8)
    out[:6, :, :] = bar
    y0, x0 = 8 + (th - t.shape[0]) // 2, (max_w - t.shape[1]) // 2
    out[y0:y0 + t.shape[0], x0:x0 + t.shape[1]] = t
    return out


def crop(path, box):
    img = read_png(path)
    h, w, _ = img.shape
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, x1 = max(0, min(x0, w - 1)), max(1, min(x1, w))
    y0, y1 = max(0, min(y0, h - 1)), max(1, min(y1, h))
    return img[y0:y1, x0:x1]


def lib_image(aid):
    hits = sorted(glob.glob(os.path.join(LIB, aid + "_*.png")))
    return read_png(hits[0]) if hits else np.full((60, 60, 3), 80, dtype=np.uint8)


def hstack(panels, gap=6):
    h = max(p.shape[0] for p in panels)
    w = sum(p.shape[1] for p in panels) + gap * (len(panels) - 1)
    out = np.full((h, w, 3), BG, dtype=np.uint8)
    x = 0
    for p in panels:
        out[:p.shape[0], x:x + p.shape[1]] = p
        x += p.shape[1] + gap
    return out


def vstack(rows, gap=10):
    w = max(r.shape[1] for r in rows)
    h = sum(r.shape[0] for r in rows) + gap * (len(rows) - 1)
    out = np.full((h, w, 3), BG, dtype=np.uint8)
    y = 0
    for r in rows:
        out[y:y + r.shape[0], :r.shape[1]] = r
        y += r.shape[0] + gap
    return out


def main():
    mp, prev, new, outdir = sys.argv[1:5]
    th = int(sys.argv[5]) if len(sys.argv) > 5 else 240
    mw = int(th * 1.75)
    os.makedirs(outdir, exist_ok=True)
    data = json.load(open(mp, encoding="utf-8"))
    sheets, done = [], []
    for a in data["assets"]:
        aid = str(a["id"]).zfill(2)
        rows = []
        lib = lib_image(aid)
        for v in a.get("views", [])[:2]:
            still, box = v["still"], v["box"]
            sub = "bg" if v.get("bg") else ""
            pp, pn = os.path.join(prev, sub, still), os.path.join(new, sub, still)
            if not os.path.exists(pp):
                pp = os.path.join(prev, still)
            if not os.path.exists(pn):
                pn = os.path.join(new, still)
            if not (os.path.exists(pp) and os.path.exists(pn)):
                print("A%s: missing %s" % (aid, still))
                continue
            rows.append(hstack([panel(lib, th, mw, BARS[0]), panel(crop(pp, box), th, mw, BARS[1]),
                                panel(crop(pn, box), th, mw, BARS[2])]))
        if not rows:
            continue
        sheet = vstack(rows)
        out = os.path.join(outdir, "A%s.png" % aid)
        write_png(out, sheet)
        sheets.append(sheet)
        done.append(aid)
    for k in range(0, len(sheets), 4):
        write_png(os.path.join(outdir, "GROUP_%d.png" % (k // 4 + 1)), vstack(sheets[k:k + 4], gap=16))
    print("wrote %d asset sheets (%s) + %d group sheets to %s" % (len(done), " ".join(done), (len(sheets) + 3) // 4, outdir))


if __name__ == "__main__":
    main()
