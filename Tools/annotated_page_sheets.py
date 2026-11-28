"""Owner sheets for the 2026-11-28 annotated blueprint: per annotated page ORIGINAL | GAME TODAY | AFTER (16x9 views) + the rear
portrait gameplay view GAME | AFTER. Private output (reference pixels): Captures/ only.
Usage: python -I Tools/annotated_page_sheets.py GAME_STILLS AFTER_STILLS GAME_R2_DIR AFTER_R2_DIR OUT_DIR TAG"""
import os, sys
import numpy as np
ROOT = "C:/Users/josia/thanksgiving"
sys.path.insert(0, ROOT + "/Tools")
from img_crop import read_png, write_png
from labeled_sheet import BG, caption_bar

GS, AS, GR, AR, OUT, TAG = sys.argv[1:7]
REF = ROOT + "/Reference/frames4k_720/"
GAP = 10


def rgb(p):
    p = p if os.path.isabs(p) else ROOT + "/" + p
    return np.asarray(read_png(p))[..., :3].astype(np.uint8)


def fit_h(a, h):
    w = max(1, int(round(a.shape[1] * h / a.shape[0])))
    ys = (np.arange(h) * a.shape[0] / h).astype(int); xs = (np.arange(w) * a.shape[1] / w).astype(int)
    return a[ys][:, xs]


def row(items, h, px=3):
    cols = []
    for path, lab in items:
        try:
            a = fit_h(rgb(path), h)
        except Exception:
            a = np.full((h, int(h * 16 / 9), 3), 30, np.uint8); lab += " (MISSING)"
        col = np.concatenate([caption_bar(lab, a.shape[1], px), a], 0)
        if cols: cols.append(np.full((col.shape[0], GAP, 3), BG, np.uint8))
        cols.append(col)
    return np.concatenate(cols, 1)


def stack(rows, title):
    W = max(r.shape[1] for r in rows)
    out = [caption_bar(title, W, 3)]
    for r in rows:
        if r.shape[1] < W: r = np.concatenate([r, np.full((r.shape[0], W - r.shape[1], 3), BG, np.uint8)], 1)
        out += [np.full((GAP, W, 3), BG, np.uint8), r]
    return np.concatenate(out, 0)


PAGES = [
    ("P1", "ENTRANCE AND MACHINERY (0.50 S)", "f_00.50s.png", [("01_hall_start_16x9.png", "REAR GAMEPLAY 01")],
     [("01_hall_start_9x16.png", "01"), ("02_hall_curve_9x16.png", "02")]),
    ("P2-P3", "S2 HERO FRAME (3.00 S)", "f_03.00s.png", [("R2", "MATCHED REAR R2")],
     [("rig_d38.5_9x16.png", "RIG 38.5"), ("rig_d44.0_9x16.png", "RIG 44")]),
    ("P4", "INSIDE THE DRUM (7.50 S)", "f_07.50s.png", [("R4_front_S4_like_7s_16x9.png", "FRONT R4"), ("C4_front_window_like_7s_16x9.png", "FRONT C4")],
     [("06_tunnel_lane_right_9x16.png", "06"), ("07_chambers_9x16.png", "07")]),
    ("P5", "SIGNATURE LAUNDRY SCENERY (10.00 S)", "f_10.00s.png", [("C2_front_chambers_like_10s_16x9.png", "FRONT C2"), ("R6_front_S6_like_11s_16x9.png", "FRONT R6")],
     [("07_chambers_9x16.png", "07"), ("08_sweep_9x16.png", "08")]),
    ("P6", "GOLDEN DESTINATION (14.00 S)", "f_14.00s.png", [("C3_front_portal_like_14s_16x9.png", "FRONT C3"), ("09_portal_16x9.png", "REAR GAMEPLAY 09")],
     [("09_portal_9x16.png", "09"), ("10_finale_9x16.png", "10 FINALE")]),
]
os.makedirs(OUT if os.path.isabs(OUT) else ROOT + "/" + OUT, exist_ok=True)
for key, name, ref, views, ports in PAGES:
    rows = []
    for v, lab in views:
        if v == "R2":
            g, a = f"{GR}/R2_16x9.png", f"{AR}/R2_16x9.png"
        else:
            g, a = f"{GS}/{v}", f"{AS}/{v}"
        rows.append(row([(REF + ref, f"ORIGINAL {ref[2:7]} S"), (g, f"GAME TODAY - {lab}"), (a, f"{TAG} - {lab}")], 360))
    pp = []
    for v, lab in ports:
        src_g = f"{GR}/{v}" if v.startswith("rig") else f"{GS}/{v}"
        src_a = f"{AR}/{v}" if v.startswith("rig") else f"{AS}/{v}"
        pp += [(src_g, f"GAME {lab}"), (src_a, f"{TAG} {lab}")]
    rows.append(row(pp, 560, 2))
    sheet = stack(rows, f"{key} {name} - YOUR ANNOTATED PAGE vs UNITY (REAR PORTRAIT ROW = REAL GAMEPLAY VIEW)")
    o = f"{OUT}/OWNER_{key}_{TAG}.png"
    write_png(o if os.path.isabs(o) else ROOT + "/" + o, sheet)
    print("wrote", o, sheet.shape)
