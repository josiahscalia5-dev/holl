"""Reference match per annotated page (owner 2026-11-28: use the installed reference-matching skills WITH the six annotated pages).
Uses .claude/skills/source-part-segmentation (seeded hsv_range masks) and the reference-look-calibration statistics to compare, for
each MATERIAL CLASS the owner's arrows talk about (deep-blue metal, violet metal, gold, turquoise water, pink, white foam, dark holes /
seams, yellow neon), how much of the frame it covers and its hue / saturation / value in the ORIGINAL page frame vs Unity renders.
Works for unmatched cameras too (class coverage = composition-level look), so the front pages P4-P6 can be judged.

  uv run --no-project --with opencv-python-headless --with numpy python Tools/ref_match.py --page P4 \
      --img GAME=Captures/s2art/art06_base/stills_current/R4_front_S4_like_7s_16x9.png \
      --img AFTER=Captures/s2art/bp_A_1/stills_metal_x/R4_front_S4_like_7s_16x9.png --out Captures/refmatch_1128/P4_R4
Writes OUT.md (table + verdicts for the LAST image vs the original) and OUT.png (class maps: original | each image).
Pages: P1 0.50 s, P2 / P3 3.00 s, P4 7.50 s, P5 10.00 s, P6 14.00 s (Reference/frames4k_720/). Images are resized to 1280x720.
"""
import argparse, math, sys
from pathlib import Path
import cv2
import numpy as np

ROOT = Path("C:/Users/josia/thanksgiving")
sys.path.insert(0, str(ROOT / ".claude/skills/source-part-segmentation/scripts"))
from seeded_part_masks import region_mask, threshold_inside  # noqa: E402  (the installed skill)

PAGES = {"P1": "f_00.50s.png", "P2": "f_03.00s.png", "P3": "f_03.00s.png", "P4": "f_07.50s.png", "P5": "f_10.00s.png", "P6": "f_14.00s.png"}
# OpenCV HSV: H 0-179 (= deg / 2), S / V 0-255. Classes follow the owner's words on the pages.
CLASSES = [
    ("deep_blue_metal", "deep-blue metallic tunnel", [102, 64, 38], [131, 255, 191], (40, 90, 255)),
    ("violet_metal", "reflective violet surfaces", [131, 51, 38], [152, 255, 204], (170, 80, 255)),
    ("gold", "thick golden structures", [11, 102, 115], [27, 255, 255], (255, 190, 0)),
    ("turquoise_water", "natural turquoise water", [85, 64, 115], [102, 255, 255], (0, 230, 220)),
    ("pink", "pink rails / roller / fur", [152, 77, 102], [172, 255, 255], (255, 60, 170)),
    ("white_foam", "white foam / splash", [0, 0, 204], [179, 38, 255], (255, 255, 255)),
    ("dark_holes", "dark holes / seams", [0, 0, 0], [179, 255, 64], (30, 30, 30)),
    ("yellow_neon", "yellow neon / lamps", [22, 128, 204], [32, 255, 255], (255, 255, 0)),
]


def load(p):
    p = Path(p)
    p = p if p.is_absolute() else ROOT / p
    img = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"cannot read {p}")
    return cv2.resize(img, (1280, 720)) if img.shape[:2] != (720, 1280) else img


def mask(bgr, lo, hi):
    part = {"bbox": [0, 0, 1280, 720], "mode": "hsv_range", "hsv_min": lo, "hsv_max": hi}
    return threshold_inside(bgr, None, region_mask(bgr.shape, part), part) > 0


def stats(bgr, m):
    n = int(m.sum())
    cov = 100.0 * n / m.size
    if n < 50:
        return {"cover": round(cov, 1), "hue": None}
    hsv = cv2.cvtColor(bgr[m].reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float64)
    ang = hsv[:, 0] * math.pi / 90.0
    w = hsv[:, 1] / 255.0 + 1e-6
    hue = (math.degrees(math.atan2((np.sin(ang) * w).sum(), (np.cos(ang) * w).sum())) + 360) % 360
    return {"cover": round(cov, 1), "hue": round(hue), "sat": round(hsv[:, 1].mean() / 2.55), "val": round(hsv[:, 2].mean() / 2.55)}


def verdict(r, p):
    v = []
    rc, pc = r["cover"], p["cover"]
    if rc >= 1.0 and pc < rc * 0.5:
        v.append(f"MISSING / too little ({pc:.1f} vs {rc:.1f} % of frame)")
    elif pc >= 1.0 and pc > max(rc, 0.5) * 1.8:
        v.append(f"TOO MUCH ({pc:.1f} vs {rc:.1f} %)")
    if r["hue"] is not None and p["hue"] is not None and min(rc, pc) >= 0.8:
        dh = (p["hue"] - r["hue"] + 540) % 360 - 180
        if abs(dh) > 10:
            v.append(f"hue {p['hue']} vs {r['hue']} deg")
        if p["val"] > r["val"] * 1.15:
            v.append(f"too bright ({p['val']} vs {r['val']} %)")
        if p["val"] < r["val"] * 0.85:
            v.append(f"too dark ({p['val']} vs {r['val']} %)")
        if p["sat"] < r["sat"] * 0.8:
            v.append(f"too grey ({p['sat']} vs {r['sat']} %)")
        if p["sat"] > r["sat"] * 1.25:
            v.append(f"oversaturated ({p['sat']} vs {r['sat']} %)")
    return "; ".join(v) if v else "close"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True, choices=sorted(PAGES))
    ap.add_argument("--img", action="append", required=True, help="LABEL=path (Unity render; the LAST one gets the verdicts)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ref = load(ROOT / "Reference/frames4k_720" / PAGES[a.page])
    imgs = [(s.split("=", 1)[0], load(s.split("=", 1)[1])) for s in a.img]
    res = {"ORIGINAL": {c[0]: stats(ref, mask(ref, c[2], c[3])) for c in CLASSES}}
    for lab, im in imgs:
        res[lab] = {c[0]: stats(im, mask(im, c[2], c[3])) for c in CLASSES}
    fmt = lambda s: f"{s['cover']:.1f} % ({s['hue']} / {s['sat']} / {s['val']})" if s["hue"] is not None else f"{s['cover']:.1f} %"
    last = imgs[-1][0]
    lines = [f"# Reference match {a.page} (original {PAGES[a.page][2:7]} s) - cover % of frame (hue deg / sat % / value %)", "",
             "| class (owner's words) | ORIGINAL | " + " | ".join(l for l, _ in imgs) + f" | {last} vs ORIGINAL |",
             "|---|---|" + "---|" * len(imgs) + "---|"]
    for c in CLASSES:
        row = [f"{c[0]} ({c[1]})", fmt(res["ORIGINAL"][c[0]])] + [fmt(res[l][c[0]]) for l, _ in imgs]
        row.append(verdict(res["ORIGINAL"][c[0]], res[last][c[0]]))
        lines.append("| " + " | ".join(row) + " |")
    out = Path(a.out)
    out = out if out.is_absolute() else ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    tiles = []
    for im in [ref] + [i for _, i in imgs]:
        cmap = np.zeros_like(im)
        for c in CLASSES:
            cmap[mask(im, c[2], c[3])] = c[4][::-1]
        tiles.append(cv2.resize(np.concatenate([im, cmap], 0), (480, 540)))
    cv2.imwrite(str(out.with_suffix(".png")), np.concatenate(tiles, 1))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
