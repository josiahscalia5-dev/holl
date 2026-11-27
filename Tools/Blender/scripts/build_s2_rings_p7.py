"""Screen S2 pass 7 (asset artist, 2026-11-27): DIFFERENTIATED inner marquee ring masters for the S2 door view (judge gap #2
"inner rings are identical hoops - the reference VARIES ring thickness, spacing and profile"; owner 06:58 s4/s5 "ring
SPACING + differentiated THICKNESS + rounded profiles (no identical hoops)").

Measured on the private reference f_03.00s (720p, R2 comparison camera ~32.25 m, 1 px ~ 0.0308 m at 20 m depth):
  ring 1 (first gold marquee ring inside the LED rim): on-screen r ~147 px, band median ~19 px (~0.55-0.6 m) = a THICK
          rounded gold band with big warm bulbs seated ON the band (bulb ~10 px = r ~0.15 m), ~18 bulbs on the upper half
  ring 2 (entrance gate): r ~93 px, visibly thinner band (~10 px at ~29 m = ~0.36 m) with smaller distinct bulbs
  ring 3+: thinner again (the p6 master SM_MarqueeRing_s2, 0.26 m band) receding to the bright far end
Ours (lead_s2p7): every ring < 90 m = the same thin p6 master (band median 6 px) -> identical hoops.

Assets (same frame / slots as build_s2_door_p6.py: Blender Z up, ring in the XZ plane, axis Y, display face +Y):
  SM_MarqueeRing_s2a  THICK: rounded convex gold band rho 3.70-4.30 between an outer rope bead and an inner dark-gold
                      bead, a recessed dark-gold channel line, 36 big bulbs (r 0.15) in deep cups ON the band crest.
                      LOD0 / LOD1 (no cups).
  SM_MarqueeRing_s2b  MEDIUM: rounded band rho 3.84-4.22 + beads, 40 bulbs (r 0.115) in cups. LOD0 / LOD1.
  (thin = the p6 SM_MarqueeRing_s2, unchanged)
Slots M_Gold, M_GoldDark, M_Bulb (existing project materials; emission / gold values belong to the metal agent).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_rings_p7.py s2_rings_p7
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

GOLD, GDARK, BULB = range(3)
TAU = 2.0 * math.pi
AXIS = (0.0, 1.0, 0.0)


def circle_prof(R, r, h, n):
    return [(R + r * math.cos(TAU * k / n), h + r * math.sin(TAU * k / n)) for k in range(n)]


def ellipsoid_prof(rb, hb, n):
    return [(rb * math.cos(-math.pi / 2 + math.pi * k / n), hb * math.sin(-math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]


def ring_points(rho, count, phase=0.5):
    for i in range(count):
        a = TAU * (i + phase) / count
        yield rho * math.cos(a), rho * math.sin(a)


def rounded_band(r_in, r_out, back, crest, n=12):
    """Closed CCW (rho, h) section: flat back at h=back, convex rounded front peaking at h=crest mid-band."""
    pts = [(r_in, back), (r_out, back)]
    for k in range(n + 1):
        t = k / n
        rho = r_out - (r_out - r_in) * t
        pts.append((rho, back * 0.25 + (crest - back * 0.25) * math.sin(math.pi * t) ** 0.6))
    return pts


def build_ring(q, r_in, r_out, crest, bead_out, bead_in, n_bulbs, bulb_r, cup_r):
    mb = MB()
    seg = 128 if q else 48
    mid = 0.5 * (r_in + r_out)
    lathe(mb, rounded_band(r_in, r_out, -0.16, crest, 12 if q else 6), GOLD, seg, axis=AXIS, closed=True)
    # outer polished rope bead + inner dark-gold bead (layered rim profile)
    lathe(mb, circle_prof(r_out + bead_out * 0.6, bead_out, 0.0, 10 if q else 5), GOLD, seg, axis=AXIS, closed=True)
    lathe(mb, circle_prof(r_in - bead_in * 0.5, bead_in, 0.02, 10 if q else 5), GDARK, seg, axis=AXIS, closed=True)
    if q:   # recessed dark channel lines either side of the bulb row (mechanical seam detail, LOD0 only)
        for off in (-0.36, 0.36):
            lathe(mb, circle_prof(mid + off * (r_out - r_in), 0.018, crest * 0.75, 6), GDARK, seg, axis=AXIS, closed=True)
    cup = [(0.0, -0.02), (cup_r, -0.02), (cup_r * 1.04, 0.035), (cup_r * 0.9, 0.07), (cup_r * 0.72, 0.05), (0.0, 0.05)]
    for x, z in ring_points(mid, n_bulbs):
        if q:
            lathe(mb, cup, GDARK, 14, origin=(x, crest - 0.02, z), axis=AXIS)
        lathe(mb, ellipsoid_prof(bulb_r, bulb_r * 0.78, 6 if q else 3), BULB, 14 if q else 6, origin=(x, crest + 0.05, z), axis=AXIS)
    return mb


def build_a(q):
    return build_ring(q, 3.70, 4.30, 0.20, 0.07, 0.06, 36, 0.15, 0.19)


def build_b(q):
    return build_ring(q, 3.84, 4.22, 0.15, 0.055, 0.045, 40, 0.115, 0.145)


def make_materials():
    return [C.material("M_Gold", "#E8B04A", 1.0, 0.18),
            C.material("M_GoldDark", "#B8782C", 1.0, 0.25),
            C.material("M_Bulb", "#FFB060", 0.0, 0.2, emission="#FF9A40", emission_strength=6.0)]


def compact(mb, mats):
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
    ra, a0, a1 = export("SM_MarqueeRing_s2a", "MarqueeRing", build_a, mats, (0.6, 9.0, -0.6), (-0.4, 0.0, 0.8), 20.0)
    # both masters keep the child names MarqueeRing_LOD0 / _LOD1 (SceneBuilder HallLods): remove the first set before
    # building the second so Blender does not rename the new objects to *.001
    for o in (a0, a1, ra):
        bpy.data.objects.remove(o, do_unlink=True)
    export("SM_MarqueeRing_s2b", "MarqueeRing", build_b, mats, (0.6, 9.0, -0.6), (-0.4, 0.0, 0.8), 20.0)
    C.save_work("s2_rings_p7.blend")
    print("DONE")


main()
