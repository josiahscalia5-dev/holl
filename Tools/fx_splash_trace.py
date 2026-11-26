"""Measure the milky crown splashes of a reference frame and turn them into metaball skeletons (round 6, shot 8.25 s).

Segments the white splash pixels of each wing inside hand-set regions (excluding feet, chevron, foam), computes the exact
Euclidean distance transform, keeps the medial-axis ridge (centres of maximal inscribed circles) and thins it to a ball
list (x, y, r in reference pixels). The Blender build (build_fx_splash.py, BWK_FX_MODE=v2) back-projects the balls
through the reference camera model so the 3D milk reproduces the measured silhouette and tube thickness exactly.

Usage (Blender's bundled Python, numpy only):
  python -I Tools/fx_splash_trace.py FRAME.png OUT.json [DEBUG_DIR]
FRAME = a 1280x720 reference frame (Reference/frames4k_720/f_08.25s.png). OUT = shape data only (no pixels), tracked in
Tools/Blender/scripts/data/. DEBUG_DIR gets mask images WITH reference pixels -> only Captures/ (private).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

# regions per wing (1280x720 frame coords): box, plus exclusion circles (feet) and the chevron rule
WINGS = {
    "L": {"box": (262, 515, 548, 720), "excl_circles": [(562, 540, 50)], "excl_boxes": [(262, 515, 336, 600)]},
    "R": {"box": (640, 492, 1005, 720), "excl_circles": [(683, 498, 47)], "excl_boxes": []},
}
# glowing chevron under the mascot (its white-cyan core has the milk's colour): triangle apex / base corners
CHEVRON = ((612, 592), (440, 720), (812, 720))


def splash_mask(img):
    f = img.astype(np.int32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(-1), f.min(-1)
    white = (mn > 150) & (b > 175) & ((mx - mn) < 72)
    cyan = (g - r > 34) & (g > 232)            # glowing chevron core / rim (cyan-white, greener than the milk)
    return white & ~cyan


def in_triangle(xx, yy, tri):
    (x1, y1), (x2, y2), (x3, y3) = tri
    def side(ax, ay, bx, by):
        return (xx - bx) * (ay - by) - (ax - bx) * (yy - by)
    d1, d2, d3 = side(x1, y1, x2, y2), side(x2, y2, x3, y3), side(x3, y3, x1, y1)
    neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
    pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
    return ~(neg & pos)


def majority(m):
    """3x3 majority filter (removes speckle, fills pinholes)."""
    p = np.pad(m, 1).astype(np.int32)
    h, w = m.shape
    acc = sum(p[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    return acc >= 5


def edt(mask):
    """Exact Euclidean distance from every inside pixel to the nearest outside pixel (brute force, small masks)."""
    h, w = mask.shape
    pad = np.zeros((h + 2, w + 2), bool)
    pad[1:-1, 1:-1] = mask
    inner = pad[1:-1, 1:-1]
    nb = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    border = np.argwhere(inner & ~nb).astype(np.float32)        # inside pixels touching the outside
    pts = np.argwhere(inner).astype(np.float32)
    d = np.zeros((h, w), np.float32)
    if len(border) == 0:
        return d
    out = np.empty(len(pts), np.float32)
    for s in range(0, len(pts), 2048):
        p = pts[s:s + 2048]
        dd = ((p[:, None, :] - border[None, :, :]) ** 2).sum(-1)
        out[s:s + 2048] = np.sqrt(dd.min(1)) + 0.5
    d[pts[:, 0].astype(int), pts[:, 1].astype(int)] = out
    return d


def ridge_balls(d, min_r=2.5, spacing=0.45):
    """Medial-axis balls: ridge pixels of the distance map, thinned greedily (largest first, spacing x radius)."""
    h, w = d.shape
    pad = np.pad(d, 1)
    nbmax = np.zeros_like(d)
    cnt_higher = np.zeros(d.shape, np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            nbv = pad[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx]
            nbmax = np.maximum(nbmax, nbv)
            cnt_higher += (nbv > d + 0.35)
    # ridge: no more than 2 neighbours clearly higher (a crest line has higher pixels only along itself, if any)
    ridge = (d >= min_r) & (cnt_higher <= 1)
    ys, xs = np.nonzero(ridge)
    order = np.argsort(-d[ys, xs])
    acc = []
    for i in order:
        x, y, r = float(xs[i]), float(ys[i]), float(d[ys[i], xs[i]])
        ok = True
        for (ax, ay, ar) in acc:
            if (ax - x) ** 2 + (ay - y) ** 2 < (spacing * max(ar, r)) ** 2:
                ok = False
                break
        if ok:
            acc.append((x, y, r))
    return acc


def main():
    src, out = sys.argv[1], sys.argv[2]
    dbg = sys.argv[3] if len(sys.argv) > 3 else None
    img = read_png(src)[:, :, :3]
    H, W = img.shape[:2]
    m_all = splash_mask(img)
    res = {"source_frame": os.path.basename(src), "frame_size": [W, H], "wings": {}}
    vis = (img.astype(np.float32) * 0.35).astype(np.uint8) if dbg else None
    for name, spec in WINGS.items():
        x0, y0, x1, y1 = spec["box"]
        m = np.zeros((H, W), bool)
        m[y0:y1, x0:x1] = m_all[y0:y1, x0:x1]
        yy, xx = np.mgrid[0:H, 0:W]
        for (cx, cy, cr) in spec["excl_circles"]:
            m &= (xx - cx) ** 2 + (yy - cy) ** 2 > cr * cr
        for (bx0, by0, bx1, by1) in spec["excl_boxes"]:
            m[by0:by1, bx0:bx1] = False
        m &= ~in_triangle(xx, yy, CHEVRON)
        m = majority(majority(m))
        if dbg:
            write_png(os.path.join(dbg, "trace_bin_%s_%s.png" % (name, os.path.splitext(os.path.basename(src))[0])),
                      (m[:, :, None] * np.array([255, 255, 255])).astype(np.uint8))
        sub = m[y0:y1, x0:x1]
        d = edt(sub)
        balls = ridge_balls(d)
        balls = [(x + x0, y + y0, r) for (x, y, r) in balls]
        cols = img[m].astype(np.float32)
        lum = cols @ np.array([0.2126, 0.7152, 0.0722])
        q = np.percentile(lum, [10, 50, 90])
        stats = {}
        for tag, lo, hi in (("shade_p0_20", 0, 20), ("mid_p40_60", 40, 60), ("core_p80_100", 80, 100)):
            a, b = np.percentile(lum, [lo, hi])
            sel = cols[(lum >= a) & (lum <= b)].mean(0)
            stats[tag] = "#%02X%02X%02X" % tuple(int(v) for v in sel)
        ys, xs = np.nonzero(m)
        res["wings"][name] = {
            "pixels": int(m.sum()), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "radius_px_p50_p90_max": [float(np.percentile([b[2] for b in balls], 50)), float(np.percentile([b[2] for b in balls], 90)), float(max(b[2] for b in balls))],
            "colors": stats, "lum_p10_p50_p90": [float(v) for v in q],
            "balls": [[round(x, 1), round(y, 1), round(r, 2)] for (x, y, r) in balls]}
        print("wing %s: %d px, bbox %s, %d balls, r p50/p90/max %s, colours %s" % (
            name, m.sum(), res["wings"][name]["bbox"], len(balls), ["%.1f" % v for v in res["wings"][name]["radius_px_p50_p90_max"]], stats))
        if dbg:
            vis[m] = (255, 255, 255)
            for (x, y, r) in balls:
                vis[int(y), int(x)] = (255, 0, 80)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote", out)
    if dbg:
        write_png(os.path.join(dbg, "trace_mask_%s.png" % os.path.splitext(os.path.basename(src))[0]), vis[470:720, 240:1020])


if __name__ == "__main__":
    main()
