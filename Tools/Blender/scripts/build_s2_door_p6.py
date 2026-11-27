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
  SM_DoorHatch_s2     LOD0 / LOD1 (v2, see build_hatch): fat glossy violet torus rim rho 4.20-5.30 (crest in front of the
                      gold) + copper bead + polished gold band rho 5.62-6.62 (convex front) + dark-gold rope lip + thin
                      violet outer bezel + 16 big warm bulbs in gold cups. Slots M_Gold, M_GoldDark, M_HatchViolet_s2
                      (MaterialLibrary.Assets.cs), M_Bulb.
  SM_LedRim_s2        LOD0 / LOD1 (v2): fat glossy violet tube rim + 48 pink LED domes (first ring inside the door).
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

SLOTS = ["M_Gold", "M_GoldDark", "M_HatchViolet_s2", "M_Bulb", "M_RimLight"]
GOLD, GDARK, VIOLET, BULB, LED = range(5)
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
# v2 (06:50, measured on the lead build lead_s2p6 R2 still vs f_03.00s, 720p): the reference hatch left of the door is
# ~120 px from the outer gold edge to the inner violet edge (ours v1 ~90 px) and its violet rim is a FAT glossy torus
# (~35-40 px wide on the left, ~120 px on the right where the camera sees it face-on; ours v1 ~15 px, set back behind the
# gold and lit like the lavender drum wall). v2: violet rim = a rounded D-section torus rho 4.20-5.30 with its crest
# (h 0.40) IN FRONT of the gold face, copper bead rho 5.29-5.63, gold band rho 5.62-6.62 (convex front), dark-gold rope
# lip + a thin violet outer bezel (the reference's lilac band left of the gold); 16 big warm bulbs on the band crest.
# Violet slot = M_HatchViolet_s2 (glossy deep violet, MaterialLibrary.Assets.cs) instead of the pale M_DrumRim.
def build_hatch(q):
    mb = MB()
    seg = 160 if q else 64
    # fat glossy violet drum rim (CCW: back edge -> outer side -> crest -> inner side rolling back into the drum r 4.2)
    rim = [(4.12, -1.00), (5.30, -1.00), (5.30, -0.30), (5.24, -0.02), (5.14, 0.18), (4.98, 0.33), (4.78, 0.40),
           (4.58, 0.37), (4.42, 0.25), (4.31, 0.06), (4.25, -0.20), (4.20, -0.50), (4.15, -0.80)]
    lathe(mb, rim, VIOLET, seg, axis=AXIS, closed=True)
    # copper bead between the violet rim and the gold band
    lathe(mb, circle_prof(5.46, 0.17, 0.12, 12 if q else 6), GDARK, seg, axis=AXIS, closed=True)
    # polished gold hatch band: flat back, convex front bulging toward the camera (highlights on both halves)
    front = []
    for k in range(11):
        t = k / 10.0
        front.append((6.62 - 1.00 * t, 0.02 + 0.30 * math.sin(math.pi * t) ** 0.8))
    band = [(5.62, -0.30), (6.58, -0.30), (6.63, -0.12)] + front + [(5.62, -0.10)]
    lathe(mb, band, GOLD, seg, axis=AXIS, closed=True)
    # outer dark-gold rope lip + thin violet bezel outside it
    lathe(mb, circle_prof(6.68, 0.08, -0.04, 10 if q else 6), GDARK, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(6.86, 0.12, -0.10, 10 if q else 6), VIOLET, seg, axis=AXIS, closed=True)
    # 16 big warm bulbs in gold cups on the band crest (rho 6.12)
    cup = [(0.0, -0.03), (0.255, -0.03), (0.26, 0.04), (0.235, 0.09), (0.19, 0.065), (0.0, 0.065)]
    for x, z in ring_points(6.12, 16):
        lathe(mb, cup, GDARK, 20 if q else 10, origin=(x, 0.29, z), axis=AXIS)
        lathe(mb, ellipsoid_prof(0.21, 0.16, 8 if q else 4), BULB, 18 if q else 8, origin=(x, 0.40, z), axis=AXIS)
    return mb


# ------------------------------------------------------------------ violet LED drum rim (first ring inside the door)
# Reference f_03.00s: right inside the hatch a FAT glossy violet rim with many small pink-white LEDs frames the tunnel
# (on-screen r ~211 px); ours = SM_DrumRim (0.28 m bead, 24 lamps, lavender like the wall) read as loose pink dots.
# SM_LedRim_s2: rounded violet tube (centre rho 3.95, r 0.30 -> apex rho 3.65, same clearance as SM_DrumRim) on a short
# back web into the wall (rho 4.30), 48 LED domes on the front-inner face (rho 3.74, h 0.22). Slots M_HatchViolet_s2,
# M_RimLight (the existing pink LED emissive).
def build_ledrim(q):
    mb = MB()
    seg = 128 if q else 48
    lathe(mb, circle_prof(3.95, 0.30, 0.0, 18 if q else 8), VIOLET, seg, axis=AXIS, closed=True)
    lathe(mb, [(4.02, -0.62), (4.30, -0.62), (4.30, 0.02), (4.02, -0.10)], VIOLET, seg, axis=AXIS, closed=True)
    for x, z in ring_points(3.74, 48):
        lathe(mb, ellipsoid_prof(0.075, 0.06, 6 if q else 3), LED, 12 if q else 6, origin=(x, 0.22, z), axis=AXIS)
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
            C.material("M_HatchViolet_s2", "#6A36C8", 0.35, 0.16),
            C.material("M_Bulb", "#FFB060", 0.0, 0.2, emission="#FF9A40", emission_strength=6.0),
            C.material("M_RimLight", "#FF6AD0", 0.0, 0.3, emission="#FF4FC4", emission_strength=5.0)]


def compact(mb, mats):
    """Keep only the material slots this mesh uses (no empty submeshes in Unity); remaps mb.fmat in place."""
    used = sorted(set(mb.fmat))
    remap = {o: n for n, o in enumerate(used)}
    mb.fmat = [remap[i] for i in mb.fmat]
    return [mats[i] for i in used]


def export(name, short, builder, mats, cam, target, lens):
    b0, b1 = builder(1), builder(0)
    m0, m1 = compact(b0, mats), compact(b1, mats)
    lod0 = b0.build(short + "_LOD0", m0)
    lod1 = b1.build(short + "_LOD1", m1)
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
    r2, m0_, m1_ = export("SM_MarqueeRing_s2", "MarqueeRing", build_marquee, mats, (0.6, 9.0, -0.6), (-0.4, 0.0, 0.8), 20.0)
    for o in (m0_, m1_):
        o.hide_render = True
    export("SM_LedRim_s2", "LedRim", build_ledrim, mats, (0.6, 9.0, -0.6), (-0.4, 0.0, 0.8), 20.0)
    C.save_work("s2_door_p6.blend")
    print("DONE")


main()
