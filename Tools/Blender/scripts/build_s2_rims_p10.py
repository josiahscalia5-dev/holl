"""Screen S2 pass 10 (asset artist, owner 13:25 / lead 13:50 "EXCESSIVE GOLD RINGS"): SM_LedRim_s2 v2.

The approved frame (video 3.00 s) inside the hatch: ONE thick gold bulb ring a few metres in (SM_MarqueeRing_s2c at 50.5 m)
and a thinner amber ring behind it (the gate at 61.7 m), then ALTERNATING violet perforated drum bands whose rims glow
pink-violet with a few tiny sparkle lights, each step slightly smaller. Ours (lead_s2p10) = 5 receding gold bulb rings
(gate + marquee rings at 71.5 / 84.25 m + SM_Ring 97 m) with rows of 48 pink LED dots between them.
SceneBuilder.Environment now places this rim instead of the gold marquee rings at 71.5 / 84.25 m (and keeps it for the
rims between), so this master is the tunnel's violet band step:
  rounded violet step   D-section rho 3.67-4.32 (apex 3.66 >= the old 3.65 clearance), front crest h .24, back web to h -.50
  glow lip              continuous thin pink-violet emissive bead on the inner front edge (rho 3.70) = the glowing rim
  sparkles              20 tiny white-pink emissive domes on the crest (instead of 48 LED dots)
Same name / LOD child names / asset frame as v1 (build_s2_door_p6.py): ring in the XZ plane, axis Y, +Y = toward the
player. Slots M_HatchViolet_s2, M_RimGlow_s2, M_RimSpark_s2 (MaterialLibrary.Assets.cs).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_rims_p10.py s2_rims_p10
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402

import bwk_common as C  # noqa: E402

_DP = os.path.join(HERE, "build_s2_door_p6.py")
_DSRC = open(_DP, encoding="utf-8").read().rstrip()
assert _DSRC.endswith("main()")
D = {"__name__": "bwk_door_p6", "__file__": _DP}
exec(compile(_DSRC[: -len("main()")], _DP, "exec"), D)
MB, lathe, circle_prof, ellipsoid_prof, ring_points, compact = (D[k] for k in ("MB", "lathe", "circle_prof", "ellipsoid_prof",
                                                                                 "ring_points", "compact"))
VIOLET, GLOW, SPARK = range(3)
AXIS = (0.0, 1.0, 0.0)


def build_rim_v2(q):
    mb = MB()
    seg = 128 if q else 48
    # rounded violet band step: inner-back -> outer-back -> outer front -> crest -> inner lip -> back into the drum
    step = [(3.80, -0.50), (4.32, -0.50), (4.32, 0.02), (4.24, 0.13), (4.11, 0.21), (3.96, 0.24), (3.83, 0.21),
            (3.74, 0.13), (3.69, 0.02), (3.68, -0.14), (3.71, -0.30), (3.75, -0.42)]
    lathe(mb, step, VIOLET, seg, axis=AXIS, closed=True)
    # continuous glowing pink-violet lip along the inner front edge
    lathe(mb, circle_prof(3.705, 0.042, 0.08, 8 if q else 4), GLOW, seg, axis=AXIS, closed=True)
    # 20 tiny sparkle lights on the crest
    for x, z in ring_points(3.98, 20, 0.25):
        lathe(mb, ellipsoid_prof(0.05, 0.04, 5 if q else 3), SPARK, 10 if q else 5, origin=(x, 0.235, z), axis=AXIS)
    return mb


def main():
    C.reset_scene()
    mats = [C.material("M_HatchViolet_s2", "#6A36C8", 0.35, 0.16),
            C.material("M_RimGlow_s2", "#F070E0", 0.0, 0.3, emission="#E060F0", emission_strength=4.0),
            C.material("M_RimSpark_s2", "#FFE0F8", 0.0, 0.3, emission="#FFD0F4", emission_strength=6.0)]
    b0, b1 = build_rim_v2(1), build_rim_v2(0)
    m0, m1 = compact(b0, mats), compact(b1, mats)
    lod0 = b0.build("LedRim_LOD0", m0)
    lod1 = b1.build("LedRim_LOD1", m1)
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    d = lod0.dimensions
    print("CHECK SM_LedRim_s2 v2 tris LOD0 %d LOD1 %d (%.0f %%) dims %.2f x %.2f x %.2f" % (t0, t1, 100.0 * t1 / t0, d.x, d.y, d.z))
    lod1.hide_render = True
    for tag, cam, tgt, lens in (("", (0.6, 9.0, -0.6), (-0.4, 0.0, 0.8), 20.0),
                                ("_side", (-7.5, 2.5, 1.2), (-3.9, 0.0, 0.3), 30.0)):
        try:
            C.render_preview(C.preview_path("SM_LedRim_s2" + tag), camera_location=cam, target=tgt, lens=lens, resolution=(900, 640))
        except Exception as e:  # noqa: BLE001
            print("CHECK preview failed:", e)
    lod1.hide_render = False
    root = bpy.data.objects.new("SM_LedRim_s2", None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lod0, lod1):
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_LedRim_s2"))
    C.save_work("s2_rims_p10.blend")
    print("DONE")


main()
