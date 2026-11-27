"""Video look-match LUT for the IN-UNITY grade preview (owner 2026-11-26 21:15 / 21:25: "preview reference-based colour
grading, cinematic lighting and controlled soft glow measured from my original video ... show before-and-after renders
before permanently applying the grade"; "do not use colour grading to disguise inadequate geometry or materials").

Same fit as Tools/look_match_preview.py (per-channel quantile matching in CIE Lab between the owner's reference frames and
our matched Unity stills) but written as a 32x32x32 URP Color Lookup strip (1024 x 32 PNG, sRGB in -> sRGB out; URP applies
the user LUT after tonemapping) for CaptureTools' GradePreview, plus an identity LUT (sanity check: must change nothing).
Fit and display sections are disjoint (fit S1 / S3 / S4 / S6, shown S2 / S5 / S7 = the owner's 21:33 section frames), so the
preview cannot copy the frames it is judged on. Prints the palette distance the LUT alone gives on the shown sections.

Usage (Blender's bundled Python): python -I Tools/look_lut.py STILLS_DIR OUT_DIR [strength 0..1, default 0.85]
Output OUT_DIR/lut_video_look.png, lut_identity.png (no reference pixels in them, but keep them in Captures/ with the rest).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import look_match_preview as L  # noqa: E402
from img_crop import write_png  # noqa: E402

FIT = [("f_00.75s.png", "01_hall_start_16x9.png"), ("f_04.50s.png", "R3_front_S3_like_5s_16x9.png"),
       ("f_06.75s.png", "R4_front_S4_like_7s_16x9.png"), ("f_11.25s.png", "R6_front_S6_like_11s_16x9.png")]
SHOW = [("f_03.00s.png", "R2_rear_S2_like_3s_16x9.png"), ("f_08.25s.png", "R5_front_S5_like_8s_16x9.png"),
        ("f_14.25s.png", "10_finale_16x9.png")]
N = 32


def lut_strip(fn):
    """URP strip layout: x = blue slice * N + red, y from the BOTTOM = green (PNG rows run top-down)."""
    g = np.arange(N) / (N - 1.0)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    out = fn(np.stack([r, gg, b], -1).reshape(-1, 3)).reshape(N, N, N, 3)   # [blue, green, red]
    strip = np.zeros((N, N * N, 3))
    for bi in range(N):
        strip[:, bi * N:(bi + 1) * N, :] = out[bi][::-1]
    return strip


def main():
    stills, out = sys.argv[1], sys.argv[2]
    strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
    os.makedirs(out, exist_ok=True)
    src, ref = [], []
    for rf, ours in FIT:
        p = os.path.join(stills, ours)
        if not os.path.exists(p):
            print("fit pair missing:", ours)
            continue
        src.append(L.rgb2lab(L.load(p, 4)).reshape(-1, 3))
        ref.append(L.rgb2lab(L.load(os.path.join(L.REF, rf), 4)).reshape(-1, 3))
    maps = L.fit_maps(np.concatenate(src), np.concatenate(ref))

    def grade(rgb):
        return L.lab2rgb(L.apply_maps(L.rgb2lab(rgb), maps, strength))

    for name, fn in (("lut_identity.png", lambda rgb: rgb), ("lut_video_look.png", grade)):
        write_png(os.path.join(out, name), (np.clip(lut_strip(fn), 0, 1) * 255 + 0.5).astype(np.uint8))
        print("wrote", os.path.join(out, name))
    for rf, ours in SHOW:
        p = os.path.join(stills, ours)
        if not os.path.exists(p):
            continue
        cur = L.load(p)[::2, ::2]
        ref_lab = L.rgb2lab(L.load(os.path.join(L.REF, rf), 2))
        d0 = L.palette_delta(ref_lab, L.rgb2lab(cur))
        d1 = L.palette_delta(ref_lab, L.rgb2lab(grade(cur)))
        print(f"{ours}: palette dE mean {d0[0]:.1f} -> {d1[0]:.1f}, spread {d0[1]:.1f} -> {d1[1]:.1f} "
              f"(LUT only, strength {strength}; lower = closer to the video)")


if __name__ == "__main__":
    main()
