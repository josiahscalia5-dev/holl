"""Owner comparison sheets for the S2 Tunnel v1 UNITY transfer test (lead a557ee90 2026-11-27, owner 22:33: "show me actual Unity
comparison screenshots before accepting any replacement"). Reads the output folder of S2v1TestScene.PreviewBatch
(<dir>/<variant>/R2_16x9.png, R2_bg_16x9.png, rig_dXX.X_9x16.png) and writes labelled sheets (Tools/labeled_sheet.py font):
  <dir>/SHEET_R2_<variant>.png   ORIGINAL 3.00 S || UNITY CURRENT || UNITY TEST <variant>   (+ the same without the mascot)
  <dir>/SHEET_RIG_<variant>.png  portrait gameplay rig: UNITY CURRENT || UNITY TEST per track distance
  <dir>/OWNER_<name>.png         ONE sheet for the owner: R2 row of every variant, then the rig rows of the chosen variant
  <dir>/metrics_R2.txt           Tools/s2_look_metrics.py on every variant's R2 (radial depth profile + palette vs the ORIGINAL)
The sheets contain reference pixels: they stay in Captures/ (gitignored).
Usage (Blender's bundled Python): python -I Tools/s2v1_unity_sheet.py <dir> [--owner VARIANT] [--name NAME]
"""
import contextlib
import glob
import io
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402
from labeled_sheet import BG, caption_bar, fit_w  # noqa: E402

REF = "C:/Users/josia/thanksgiving/Reference/frames4k_720/f_03.00s.png"
GAP = 10


def rgb(p):
    return np.asarray(read_png(p))[..., :3].astype(np.uint8)


def fit_h(img, th):
    h, w, _ = img.shape
    tw = max(1, int(round(w * th / h)))
    ys = (np.arange(th) * h / th).astype(int)
    xs = (np.arange(tw) * w / tw).astype(int)
    return img[ys][:, xs]


def hrow(tiles, h):
    tiles = [fit_h(t, h) for t in tiles]
    out = [tiles[0]]
    for t in tiles[1:]:
        out += [np.full((h, GAP, 3), BG, np.uint8), t]
    return np.concatenate(out, 1)


def block(caption, img, width):
    img = fit_w(img, width)
    px = max(2, width // 600)
    return [caption_bar(caption, width, px), img, np.full((GAP, width, 3), BG, np.uint8)]


def label(v):
    return v.replace("_bwk", " (V1 SHAPES, UNITY MATERIALS)").replace("_urp", " (V1 SHAPES + V1 MATERIALS)").replace("+", " + ").upper()


def main(argv):
    d = argv[0].rstrip("/\\")
    owner = argv[argv.index("--owner") + 1] if "--owner" in argv else None
    name = argv[argv.index("--name") + 1] if "--name" in argv else os.path.basename(d)
    variants = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(d, "*", "R2_16x9.png")))
    if "current" not in variants:
        raise SystemExit("no 'current' variant in " + d)
    tests = [v for v in variants if v != "current"]
    ref = rgb(REF)
    cur = os.path.join(d, "current")
    W = 1920
    for v in tests:
        vd = os.path.join(d, v)
        r2 = hrow([ref, rgb(cur + "/R2_16x9.png"), rgb(vd + "/R2_16x9.png")], 720)
        bg = hrow([ref, rgb(cur + "/R2_bg_16x9.png"), rgb(vd + "/R2_bg_16x9.png")], 720)
        blocks = block("ORIGINAL 3.00 S || UNITY CURRENT (THE GAME) || UNITY TEST: " + label(v), r2, W)
        blocks += block("ORIGINAL 3.00 S || UNITY CURRENT, MASCOT HIDDEN || UNITY TEST, MASCOT HIDDEN", bg, W)
        write_png(os.path.join(d, "SHEET_R2_%s.png" % v), np.concatenate(blocks[:-1], 0))
        rigs = sorted(glob.glob(os.path.join(vd, "rig_d*_9x16.png")))
        if rigs:
            tiles, caps = [], []
            for p in rigs:
                tiles += [rgb(os.path.join(cur, os.path.basename(p))), rgb(p)]
                dd = os.path.basename(p)[5:9]
                caps += ["CURRENT D %s" % dd, "TEST D %s" % dd]
            write_png(os.path.join(d, "SHEET_RIG_%s.png" % v), np.concatenate(block(" || ".join(caps), hrow(tiles, 960), W)[:-1], 0))
    # one owner sheet
    pick = owner if owner in tests else (tests[-1] if tests else None)
    blocks = block("ORIGINAL 3.00 S || UNITY CURRENT (THE GAME)", hrow([ref, rgb(cur + "/R2_16x9.png")], 720), W)
    for v in tests:
        blocks += block("UNITY CURRENT || UNITY TEST: " + label(v), hrow([rgb(cur + "/R2_16x9.png"), rgb(os.path.join(d, v, "R2_16x9.png"))], 720), W)
    if pick:
        rigs = sorted(glob.glob(os.path.join(d, pick, "rig_d*_9x16.png")))
        if rigs:
            tiles, caps = [], []
            for p in rigs:
                tiles += [rgb(os.path.join(cur, os.path.basename(p))), rgb(p)]
                dd = os.path.basename(p)[5:9]
                caps += ["CURRENT %s M" % dd, "TEST %s M" % dd]
            blocks += block("PORTRAIT GAMEPLAY CAMERA (UNCHANGED): " + " || ".join(caps), hrow(tiles, 960), W)
    out = os.path.join(d, "OWNER_%s.png" % name)
    write_png(out, np.concatenate(blocks[:-1], 0))
    import s2_look_metrics as M
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        M.main([os.path.join(d, v, "R2_16x9.png") for v in ["current"] + tests])
    open(os.path.join(d, "metrics_R2.txt"), "w").write(buf.getvalue())
    print("wrote", out, "+ SHEET_R2_* / SHEET_RIG_* for", ", ".join(tests), "+ metrics_R2.txt")


if __name__ == "__main__":
    main(sys.argv[1:])
