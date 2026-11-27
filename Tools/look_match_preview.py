"""Video look-match PREVIEW (owner 2026-11-26 21:15: "preview it first" - nothing changes in the game without approval).

Fits ONE global colour mapping (per-channel quantile matching in CIE Lab = what a Unity URP Color Lookup LUT can reproduce)
from reference / Unity pairs of some sections, then applies it plus a soft highlight glow (= what URP bloom can reproduce)
to stills of OTHER sections. Fit and display sections are disjoint, so the preview cannot copy the frames it shows.
Prints the palette distance (mean-Lab delta E + Lab spread difference) reference vs current / vs graded on the shown
sections, writes the graded stills and before / after sheets.

Usage (Blender's bundled Python): python -I Tools/look_match_preview.py STILLS_DIR OUT_DIR [strength 0..1] [glow 0..1]
Private output (contains reference pixels): Captures/ only.
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "Reference", "frames4k_720")
FIT = [("f_00.50s.png", "01_hall_start_16x9.png"), ("f_05.00s.png", "R3_front_S3_like_5s_16x9.png"),
       ("f_06.75s.png", "R4_front_S4_like_7s_16x9.png"), ("f_11.00s.png", "R6_front_S6_like_11s_16x9.png")]
SHOW = [("f_03.00s.png", "R2_rear_S2_like_3s_16x9.png"), ("f_08.25s.png", "R5_front_S5_like_8s_16x9.png"),
        ("f_14.50s.png", "10_finale_16x9.png")]
PHONE = ["hero_mouth_9x16.png", "04_tunnel_9x16.png", "07_chambers_9x16.png"]

M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
MINV = np.linalg.inv(M)
WHITE = np.array([0.95047, 1.0, 1.08883])
D = 6.0 / 29.0


def to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def rgb2lab(img):
    xyz = to_lin(img) @ M.T / WHITE
    f = np.where(xyz > D ** 3, np.cbrt(xyz), xyz / (3 * D * D) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab2rgb(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f > D, f ** 3, 3 * D * D * (f - 4 / 29)) * WHITE
    return np.clip(to_srgb(np.clip(xyz @ MINV.T, 0, None)), 0, 1)


def load(path, step=1):
    return read_png(path)[::step, ::step, :3].astype(np.float64) / 255.0


def fit_maps(src_lab, ref_lab, n=513):
    qs = np.linspace(0, 1, n)
    maps = []
    for c in range(3):
        s = np.quantile(src_lab[:, c], qs)
        r = np.quantile(ref_lab[:, c], qs)
        s, idx = np.unique(s, return_index=True)
        maps.append((s, r[idx]))
    return maps


def apply_maps(lab, maps, strength):
    out = lab.copy()
    for c, (s, r) in enumerate(maps):
        out[..., c] = lab[..., c] + strength * (np.interp(lab[..., c], s, r) - lab[..., c])
    return out


def box_blur(img, r):
    if r < 1:
        return img
    out = img
    for axis in (0, 1):
        pad = [(0, 0)] * 3
        pad[axis] = (r + 1, r)
        p = np.pad(out, pad, mode="edge")
        cs = np.cumsum(p, axis=axis)
        n = out.shape[axis]
        hi = np.take(cs, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(cs, np.arange(0, n), axis=axis)
        out = (hi - lo) / (2 * r + 1)
    return out


def gauss(img, sigma):
    r = max(1, int(round(np.sqrt(12 * sigma * sigma / 3 + 1) / 2)))
    for _ in range(3):
        img = box_blur(img, r)
    return img


def glow(img, amount):
    if amount <= 0:
        return img
    lum = img @ np.array([0.2126, 0.7152, 0.0722])
    bright = img * np.clip((lum - 0.62) / 0.38, 0, 1)[..., None]
    s = img.shape[1] * 0.010
    blurred = gauss(bright, s) + 0.6 * gauss(bright, s * 4)
    return 1 - (1 - img) * (1 - np.clip(amount * blurred, 0, 1))


def palette_delta(a_lab, b_lab):
    ma, mb = a_lab.reshape(-1, 3).mean(0), b_lab.reshape(-1, 3).mean(0)
    sa, sb = a_lab.reshape(-1, 3).std(0), b_lab.reshape(-1, 3).std(0)
    return float(np.linalg.norm(ma - mb)), float(np.linalg.norm(sa - sb))


def main():
    stills, out = sys.argv[1], sys.argv[2]
    strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
    amount = float(sys.argv[4]) if len(sys.argv) > 4 else 0.55
    os.makedirs(out, exist_ok=True)
    src, ref = [], []
    for rf, ours in FIT:
        if not os.path.exists(os.path.join(stills, ours)):
            print("fit pair missing:", ours)
            continue
        src.append(rgb2lab(load(os.path.join(stills, ours), 4)).reshape(-1, 3))
        ref.append(rgb2lab(load(os.path.join(REF, rf), 4)).reshape(-1, 3))
    maps = fit_maps(np.concatenate(src), np.concatenate(ref))
    np.save(os.path.join(out, "lab_quantile_maps.npy"), np.array([np.interp(np.linspace(0, 1, 64), np.linspace(0, 1, len(s)), s) for s, _ in maps]))
    sheet, phone = [], []
    for rf, ours in SHOW:
        p = os.path.join(stills, ours)
        if not os.path.exists(p):
            print("show still missing:", ours)
            continue
        cur = load(p)
        graded = glow(lab2rgb(apply_maps(rgb2lab(cur), maps, strength)), amount)
        gp = os.path.join(out, "graded_" + ours)
        write_png(gp, (graded * 255 + 0.5).astype(np.uint8))
        ref_lab = rgb2lab(load(os.path.join(REF, rf), 2))
        d0 = palette_delta(ref_lab, rgb2lab(cur[::2, ::2]))
        d1 = palette_delta(ref_lab, rgb2lab(graded[::2, ::2]))
        print(f"{ours}: palette dE mean {d0[0]:.1f} -> {d1[0]:.1f}, spread {d0[1]:.1f} -> {d1[1]:.1f} (lower = closer to the video)")
        sheet += [os.path.join(REF, rf), p, gp]
    for ours in PHONE:
        p = os.path.join(stills, ours)
        if not os.path.exists(p):
            continue
        graded = glow(lab2rgb(apply_maps(rgb2lab(load(p)), maps, strength)), amount)
        gp = os.path.join(out, "graded_" + ours)
        write_png(gp, (graded * 255 + 0.5).astype(np.uint8))
        phone += [p, gp]
    py = sys.executable
    cs = os.path.join(ROOT, "Tools", "contact_sheet.py")
    if sheet:
        subprocess.run([py, "-I", cs, os.path.join(out, "look_sections.png"), "3", "640"] + sheet, check=False)
    if phone:
        subprocess.run([py, "-I", cs, os.path.join(out, "look_phone.png"), "6", "300"] + phone, check=False)


if __name__ == "__main__":
    main()
