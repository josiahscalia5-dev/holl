"""Screen S2 pass 9 (asset artist, judge gap #3 "first rings inside the hatch = rows of small pink-white dots; the
reference has THICK polished gold bands with BIG warm bulbs", crops 06 / 08): new first-ring master
  SM_MarqueeRing_s2c  EXTRA THICK layered gold marquee band: rounded convex band rho 3.58-4.34 (0.76 m, crest 0.30)
                      between a double outer rope bead and a stepped inner dark-gold flange, two recessed seam lines,
                      24 BIG warm bulbs (r 0.21, ~14 px at the R2 depth 18.7 m like the reference's first ring) in deep
                      dark-gold cups + 24 small flange bolts between them. LOD0 / LOD1 (no cups / bolts).
Helpers (lathe, MB, rounded band, materials, export) come from build_s2_rings_p7.py; same pivot / axis (+Y = tunnel
axis) / child names MarqueeRing_LOD0 / _LOD1 as SM_MarqueeRing_s2a, so SceneBuilder.Hall swaps it in by name.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_rings_p9.py
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_P7 = os.path.join(HERE, "build_s2_rings_p7.py")
_SRC = open(_P7, encoding="utf-8").read().rstrip()
assert _SRC.endswith("main()")
R = {"__name__": "bwk_rings_p7", "__file__": _P7}
exec(compile(_SRC[: -len("main()")], _P7, "exec"), R)
C, MB, lathe = R["C"], R["MB"], R["lathe"]
GOLD, GDARK, BULB, AXIS = R["GOLD"], R["GDARK"], R["BULB"], R["AXIS"]
circle_prof, ellipsoid_prof, ring_points, rounded_band = R["circle_prof"], R["ellipsoid_prof"], R["ring_points"], R["rounded_band"]


def build_c(q):
    mb = MB()
    seg = 144 if q else 56
    r_in, r_out, crest = 3.58, 4.34, 0.30
    mid = 0.5 * (r_in + r_out)
    lathe(mb, rounded_band(r_in, r_out, -0.20, crest, 14 if q else 6), GOLD, seg, axis=AXIS, closed=True)
    # double outer rope bead (layered rim) + stepped inner dark-gold flange
    lathe(mb, circle_prof(r_out + 0.06, 0.085, 0.04, 12 if q else 5), GOLD, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(r_out + 0.20, 0.055, -0.04, 10 if q else 4), GDARK, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(r_in - 0.04, 0.075, 0.05, 12 if q else 5), GOLD, seg, axis=AXIS, closed=True)
    lathe(mb, [(r_in - 0.30, -0.18), (r_in - 0.05, -0.18), (r_in - 0.05, -0.04), (r_in - 0.30, -0.06)], GDARK, seg, axis=AXIS, closed=True)
    if q:   # recessed seam lines either side of the bulb row
        for off in (-0.34, 0.34):
            lathe(mb, circle_prof(mid + off * (r_out - r_in), 0.022, crest * 0.78, 6), GDARK, seg, axis=AXIS, closed=True)
    # owner step 2 (2026-11-27 15:50, side-by-side Captures/look/s2_step2_rims_ref_vs_ours.png): the approved frame's first
    # gold ring carries ~30 SMALLER, denser warm bulbs (~8 px at 1280) - ours 24 x r .21 (~15 px) read as a few big
    # lamps -> 32 bulbs r .15 in matching cups
    bulb_r, cup_r, n = 0.15, 0.19, 32
    cup = [(0.0, -0.03), (cup_r, -0.03), (cup_r * 1.06, 0.05), (cup_r * 0.92, 0.10), (cup_r * 0.74, 0.07), (0.0, 0.07)]
    for x, z in ring_points(mid, n):
        if q:
            lathe(mb, cup, GDARK, 16, origin=(x, crest - 0.03, z), axis=AXIS)
        lathe(mb, ellipsoid_prof(bulb_r, bulb_r * 0.82, 7 if q else 3), BULB, 16 if q else 6, origin=(x, crest + 0.07, z), axis=AXIS)
    if q:   # flange bolts between the bulbs on the inner flange
        bolt = [(0.0, 0.0), (0.05, 0.0), (0.05, 0.03), (0.035, 0.05), (0.0, 0.05)]
        for x, z in ring_points(r_in - 0.17, n, phase=0.0):
            lathe(mb, bolt, GOLD, 8, origin=(x, -0.04, z), axis=AXIS)
    return mb


def main():
    C.reset_scene()
    mats = R["make_materials"]()
    R["export"]("SM_MarqueeRing_s2c", "MarqueeRing", build_c, mats, (0.6, 9.0, -0.6), (-0.4, 0.0, 0.8), 20.0)
    C.save_work("s2_rings_p9.blend")
    print("DONE")


main()
