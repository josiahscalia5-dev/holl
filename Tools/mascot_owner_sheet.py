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


# ------------------------------------------------------------------------------------------------------------------------
# ACCEPT mode (lead 6d001969 2026-11-27 17:40, owner 17:35 section 4H "before committing the new mascot to another full game build,
# show one complete comparison sheet": original reference, new front / side / rear / three-quarter, fur close-up, knitted hat +
# pom-pom close-up, mascot inside actual Unity gameplay, compared with s2p10e, s2p10f and any newer version; owner 17:45: the
# ORIGINAL Google Flow crops in Reference/google_flow_pack_1735/ are authoritative).
#   python -I Tools/mascot_owner_sheet.py --accept OUT.png NEW_DIR ["NEW LABEL"] [BEFORE_MASCOT_DIR] [name=DIR,name=DIR,...]
#   NEW_DIR = an AgentPreviewBatch -bwkMascotViews output (mascot/M1..M4 + R2_vs_reference_16x9.png + hero_vs_reference_9x16.png)
#   BEFORE_MASCOT_DIR default Captures/lead/mascot_before_s2p10g (the s2p10g mascot alone, same cameras)
#   versions default s2p10e=Captures/compare/build_s2p10e,s2p10f=Captures/compare/build_s2p10f,s2p10g=Captures/compare/build_s2p10g
FLOW = "Reference/google_flow_pack_1735/Crops"
SHEET_W = 2100


def fit_box(img, w, h):
    ih, iw = img.shape[:2]
    sc = min(w / iw, h / ih)
    nw, nh = max(1, int(round(iw * sc))), max(1, int(round(ih * sc)))
    r = fit_w(img, nw)
    if r.shape[0] < nh:
        r = np.concatenate([r, np.repeat(r[-1:], nh - r.shape[0], 0)], 0)
    out = np.full((h, w, 3), BG, np.uint8)
    y0, x0 = (h - nh) // 2, (w - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = r[:nh, :nw]
    return out


def tile_row(tiles, ratio=1.0):
    n = len(tiles)
    tw = (SHEET_W - GAP * (n - 1)) // n
    th = int(round(tw * ratio))
    cells = []
    for t in tiles:
        cells.append(fit_box(t, tw, th) if t is not None else np.full((th, tw, 3), BG, np.uint8))
        cells.append(np.full((th, GAP, 3), BG, np.uint8))
    row = np.concatenate(cells[:-1], axis=1)
    if row.shape[1] < SHEET_W:
        row = np.concatenate([row, np.full((th, SHEET_W - row.shape[1], 3), BG, np.uint8)], axis=1)
    return row


def mascot_bbox(img):
    """Mascot-alone renders have a flat backdrop: bbox of the pixels that differ from the median border colour."""
    border = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]]).astype(np.float32)
    bg = np.median(border, axis=0)
    d = np.abs(img.astype(np.float32) - bg).sum(axis=2)
    ys, xs = np.nonzero(d > 45)
    if len(xs) < 50:
        return 0, 0, img.shape[1], img.shape[0]
    return (int(np.percentile(xs, 0.3)), int(np.percentile(ys, 0.3)),
            int(np.percentile(xs, 99.7)) + 1, int(np.percentile(ys, 99.7)) + 1)


def load_view(d, n):
    for p in (os.path.join(d, "mascot", n + ".png"), os.path.join(d, n + ".png")):
        if os.path.exists(p):
            return read_png(p)[:, :, :3]
    return None


def mascot_tile(img):
    if img is None:
        return None
    x0, y0, x1, y1 = mascot_bbox(img)
    pad = int(0.06 * max(x1 - x0, y1 - y0))
    return img[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]


def closeups(rear, front):
    """hat + pom-pom = upper half of the REAR mascot bbox, fur = the back below the brim, face = lower part of the FRONT bbox."""
    out = {"hat": None, "fur": None, "face": None}
    if rear is not None:
        x0, y0, x1, y1 = mascot_bbox(rear)
        w, h = x1 - x0, y1 - y0
        out["hat"] = rear[y0:y0 + int(0.52 * h), x0 + int(0.18 * w):x1 - int(0.18 * w)]
        out["fur"] = rear[y0 + int(0.56 * h):y0 + int(0.86 * h), x0 + int(0.28 * w):x1 - int(0.28 * w)]
    if front is not None:
        x0, y0, x1, y1 = mascot_bbox(front)
        w, h = x1 - x0, y1 - y0
        out["face"] = front[y0 + int(0.42 * h):y1, x0 + int(0.12 * w):x1 - int(0.12 * w)]
    return out


def flow(name):
    p = os.path.join(FLOW, name)
    return read_png(p)[:, :, :3] if os.path.exists(p) else None


def accept_main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    out, ndir = argv[0], argv[1]
    nlabel = argv[2] if len(argv) > 2 else "NEW"
    bdir = argv[3] if len(argv) > 3 else "Captures/lead/mascot_before_s2p10g"
    vers = argv[4] if len(argv) > 4 else ("s2p10e=Captures/compare/build_s2p10e,s2p10f=Captures/compare/build_s2p10f,"
                                          "s2p10g=Captures/compare/build_s2p10g")
    versions = [v.split("=", 1) for v in vers.split(",") if "=" in v]
    names = ["M1_mascot_rear", "M2_mascot_side_right", "M3_mascot_front", "M4_mascot_three_quarter"]
    rows = []
    rows.append(("ORIGINAL GOOGLE FLOW VIDEO (AUTHORITATIVE): REAR 3.00 S || FRONT 4.00 S || ANGLED 7.50 S || ANGLED REAR 0.00 S",
                 tile_row([flow("mascot_rear_03s.png"), flow("mascot_front_04s.png"), flow("mascot_angled_07_5s.png"),
                           flow("mascot_angled_rear_00s.png")], 1.0)))
    before = [load_view(bdir, n) for n in names]
    new = [load_view(ndir, n) for n in names]
    rows.append(("S2P10G (BEFORE), MASCOT ALONE: REAR || SIDE || FRONT || THREE-QUARTER", tile_row([mascot_tile(x) for x in before], 1.0)))
    rows.append((f"{nlabel}, MASCOT ALONE: REAR || SIDE || FRONT || THREE-QUARTER", tile_row([mascot_tile(x) for x in new], 1.0)))
    cb, cn = closeups(before[0], before[2]), closeups(new[0], new[2])
    rows.append((f"CLOSE-UPS: ORIGINAL FUR + HAT || S2P10G HAT || {nlabel} HAT || S2P10G FUR || {nlabel} FUR",
                 tile_row([flow("fur_and_hat_03s.png"), cb["hat"], cn["hat"], cb["fur"], cn["fur"]], 1.15)))
    rows.append((f"FACE: ORIGINAL 4.00 S || S2P10G || {nlabel}",
                 tile_row([flow("face_and_paws_04s.png"), cb["face"], cn["face"]], 0.8)))
    box, pbox = (380, 150, 900, 640), (60, 560, 660, 1180)
    r2, pt = [], []
    ref = pref = None
    for _, d in versions + [("new", ndir)]:
        p = os.path.join(d, "R2_vs_reference_16x9.png")
        q = os.path.join(d, "hero_vs_reference_9x16.png")
        if os.path.exists(p):
            a, b = halves(p)
            ref = a if ref is None else ref
            r2.append(mascot_box(b, box))
        else:
            r2.append(None)
        if os.path.exists(q):
            a, b = halves(q)
            pref = a if pref is None else pref
            pt.append(mascot_box(b, pbox))
        else:
            pt.append(None)
    labels = " || ".join(["APPROVED"] + [n.upper() for n, _ in versions] + [nlabel])
    rows.append((f"IN-GAME R2 (LANDSCAPE): {labels}",
                 tile_row([mascot_box(ref, box) if ref is not None else None] + r2, (box[3] - box[1]) / (box[2] - box[0]))))
    rows.append((f"IN-GAME PORTRAIT GAMEPLAY: {labels}",
                 tile_row([mascot_box(pref, pbox) if pref is not None else None] + pt, (pbox[3] - pbox[1]) / (pbox[2] - pbox[0]))))
    px = max(2, SHEET_W // 500)
    blocks = []
    for cap, img in rows:
        # row title on its own bar (text before the first ':'), then one label per tile
        title, _, labs = cap.partition(":")
        if labs.strip():
            blocks.append(caption_bar(title.strip(), SHEET_W, px))
            blocks.append(caption_bar(labs.strip(), SHEET_W, max(2, px - 1)))
        else:
            blocks.append(caption_bar(cap, SHEET_W, max(2, px - 1)))
        blocks.append(img)
        blocks.append(np.full((GAP, SHEET_W, 3), BG, np.uint8))
    sheet = np.concatenate(blocks[:-1], axis=0)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    write_png(out, sheet)
    print("wrote", out, sheet.shape[1], "x", sheet.shape[0])


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--accept":
        accept_main(a[1:])
        raise SystemExit(0)
    if len(a) < 6:
        raise SystemExit(__doc__)
    main(*a[:6])
