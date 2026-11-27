"""Screen S2 pass 6 (asset artist, 2026-11-27): MASTER door hatch + layered marquee ring for the S2 door (owner sheet
S2/03 "Gold & drum": match layered gold and purple rim profiles, ring spacing and smaller inner arches, distinct warm bulbs).

Measured on the private reference f_03.00s (4K crops, R2 camera ~8.3 m in front of the door; 1 px ~ 0.0136 m there):
  left of the door  gold hatch band 56 px (~0.76 m) | darker copper bead 23 px (~0.31 m) | thick glossy VIOLET rim
                    67 px (~0.9 m) rolling back into the drum | big warm bulbs ~30 px (r ~0.2 m), ~190 px apart (16 around)
  right of the door the same violet rim (wide, glossy) inside a warm gold band at the frame edge
  inside           violet LED rim (r ~211 px), then THIN gold marquee rings (band ~10-12 px at ~19 m = ~0.33 m) with
                    distinct warm bulbs (~16-18 on the upper half = ~36-40 around), receding to a bright far end
Ours (checkpoint-27): one fat gold torus (81 px, no violet rim) + four identical thick SM_Ring arches (0.76 m bands,
28 bulbs) within 23 m -> "thick identical arches with sparse bulbs".

Assets (Blender Z up, display face toward Blender +Y = asset -Z = toward the oncoming player; ring in the XZ plane, axis Y):
  SM_DoorHatch_s2     LOD0 / LOD1: polished gold hatch band (convex front, rho 5.40-6.06) + dark-gold rope lip + 16 big
                      warm bulbs in gold cups + copper inner bead (rho 5.22) + thick glossy violet drum rim (rho 4.30-5.10,
                      1.2 m deep, rolls back to the drum wall r 4.2) + a thin violet bead. Slots M_Gold, M_GoldDark,
                      M_DrumRim, M_Bulb (existing project materials, metal / environment domains).
  SM_MarqueeRing_s2   LOD0 / LOD1: thin layered gold marquee ring (rho 3.88-4.27, band 0.26 m channel between an outer gold
                      bead and an inner dark-gold bead) with 40 distinct warm bulbs in cups (LOD1: no cups, coarser).
Export: Assets/BubbleWashKingdom/Art/Models/Machinery/<name>.fbx (root empty + <Short>_LOD0 / _LOD1 children);
previews Docs/AssetPreviews/<name>.png (no reference pixels).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_door_p6.py s2_door_p6
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402

import bwk_common as C  # noqa: E402

_MP = os.path.join(HERE, "build_machinery.py")
_SRC = open(_MP, encoding="utf-8").read().rstrip()
assert _SRC.endswith("main()")
BM = {"__name__": "bwk_machinery_helpers", "__file__": _MP}
exec(compile(_SRC[: -len("main()")], _MP, "exec"), BM)
MB, lathe = BM["MB"], BM["lathe"]

SLOTS = ["M_Gold", "M_GoldDark", "M_DrumRim", "M_Bulb"]
GOLD, GDARK, VIOLET, BULB = range(4)
TAU = 2.0 * math.pi
AXIS = (0.0, 1.0, 0.0)


def circle_prof(R, r, h, n):
    """Closed CCW circle in (rho, h): a torus section (normals outward)."""
    return [(R + r * math.cos(TAU * k / n), h + r * math.sin(TAU * k / n)) for k in range(n)]


def ellipsoid_prof(rb, hb, n):
    """Bottom pole -> equator -> top pole (CCW, solid on the left)."""
    return [(rb * math.cos(-math.pi / 2 + math.pi * k / n), hb * math.sin(-math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]


def ring_points(rho, count, phase=0.5):
    for i in range(count):
        a = TAU * (i + phase) / count
        yield rho * math.cos(a), rho * math.sin(a)


# ------------------------------------------------------------------ door hatch
def build_hatch(q):
    mb = MB()
    seg = 160 if q else 64
    # polished gold hatch band: flat back, convex front bulging toward the camera (highlights on both halves)
    front = []
    for k in range(9):
        t = k / 8.0
        front.append((6.05 - 0.65 * t, 0.02 + 0.27 * math.sin(math.pi * t) ** 0.8))
    band = [(5.40, -0.30), (6.02, -0.30), (6.06, -0.12)] + front + [(5.40, -0.10)]
    lathe(mb, band, GOLD, seg, axis=AXIS, closed=True)
    # outer rope lip (dark gold) + copper inner bead
    lathe(mb, circle_prof(6.10, 0.075, -0.06, 10 if q else 6), GDARK, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(5.22, 0.14, 0.02, 12 if q else 6), GDARK, seg, axis=AXIS, closed=True)
    # thick glossy violet drum rim behind the gold, rolling back into the drum wall (r 4.2)
    rim = [(4.12, -1.00), (5.10, -1.00), (5.10, -0.20), (5.03, 0.02), (4.92, 0.14), (4.74, 0.20), (4.56, 0.17),
           (4.43, 0.07), (4.35, -0.10), (4.31, -0.35), (4.25, -0.62), (4.18, -0.82)]
    lathe(mb, rim, VIOLET, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(4.86, 0.05, 0.19, 8 if q else 4), VIOLET, seg, axis=AXIS, closed=True)
    # 16 big warm bulbs in gold cups on the band crest (rho 5.71)
    cup = [(0.0, -0.03), (0.235, -0.03), (0.24, 0.04), (0.215, 0.085), (0.17, 0.06), (0.0, 0.06)]
    for x, z in ring_points(5.71, 16):
        lathe(mb, cup, GDARK, 20 if q else 10, origin=(x, 0.27, z), axis=AXIS)
        lathe(mb, ellipsoid_prof(0.19, 0.15, 8 if q else 4), BULB, 18 if q else 8, origin=(x, 0.37, z), axis=AXIS)
    return mb


# ------------------------------------------------------------------ thin layered marquee ring
def build_marquee(q):
    mb = MB()
    seg = 120 if q else 48
    band = [(3.93, -0.13), (4.17, -0.13), (4.19, 0.02), (4.15, 0.10), (4.06, 0.13), (3.98, 0.12), (3.93, 0.06)]
    lathe(mb, band, GOLD, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(4.22, 0.05, 0.0, 8 if q else 5), GOLD, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(3.90, 0.045, 0.02, 8 if q else 5), GDARK, seg, axis=AXIS, closed=True)
    cup = [(0.0, -0.02), (0.125, -0.02), (0.13, 0.03), (0.11, 0.055), (0.09, 0.04), (0.0, 0.04)]
    for x, z in ring_points(4.06, 40):
        if q:
            lathe(mb, cup, GDARK, 12, origin=(x, 0.12, z), axis=AXIS)
        lathe(mb, ellipsoid_prof(0.10, 0.075, 6 if q else 3), BULB, 12 if q else 6, origin=(x, 0.18, z), axis=AXIS)
    return mb


def make_materials():
    return [C.material("M_Gold", "#E8B04A", 1.0, 0.18),
            C.material("M_GoldDark", "#B8782C", 1.0, 0.25),
            C.material("M_DrumRim", "#7E52C8", 0.3, 0.2),
            C.material("M_Bulb", "#FFB060", 0.0, 0.2, emission="#FF9A40", emission_strength=6.0)]


def export(name, short, builder, mats, cam, target, lens):
    lod0 = builder(1).build(short + "_LOD0", mats)
    lod1 = builder(0).build(short + "_LOD1", mats)
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    d = lod0.dimensions
    print("CHECK %s tris LOD0 %d LOD1 %d (%.0f %%) dims %.2f x %.2f x %.2f" % (name, t0, t1, 100.0 * t1 / t0, d.x, d.y, d.z))
    lod1.hide_render = True
    try:
        C.render_preview(C.preview_path(name), camera_location=cam, target=target, lens=lens, resolution=(1000, 700))
        print("PREVIEW", C.preview_path(name))
    except Exception as e:  # noqa: BLE001
        print("CHECK preview failed:", e)
    lod1.hide_render = False
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lod0, lod1):
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", name))
    return root, lod0, lod1


def main():
    C.reset_scene()
    mats = make_materials()
    # preview from roughly the R2 angle: 8.3 m in front, 1 m up, a little to the right of the axis
    r1, h0, h1 = export("SM_DoorHatch_s2", "DoorHatch", build_hatch, mats, (1.2, 8.3, -1.0), (-0.8, 0.0, 0.6), 18.0)
    for o in (h0, h1):
        o.hide_render = True
    export("SM_MarqueeRing_s2", "MarqueeRing", build_marquee, mats, (0.6, 9.0, -0.6), (-0.4, 0.0, 0.8), 20.0)
    C.save_work("s2_door_p6.blend")
    print("DONE")


main()
