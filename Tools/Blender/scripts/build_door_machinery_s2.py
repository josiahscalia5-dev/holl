"""Screen S2 pass 2 (asset artist, 2026-11-26): MASTER blue door machinery left of the washing-machine hatch.

Reference S2 (hero f_03.00s, private): left of the gold hatch rim a dark blue machine housing with panels and a
horizontal polished gold pipe with collars at the rim's mid height. Built from scratch (build_machinery.py helpers):
  housing  bevelled navy box 3.0 x 1.0 x 2.4 m, lighter blue top cap + plinth bands, 4 raised steel-blue panels with
           gold corner rivets, dark vent slots in the lower panels, a gold-bezel gauge in each upper panel
  pipe     polished gold pipe r 0.17 m in front of the housing (lathed along X): 4 rounded collars, an end flange
           with 8 bolts on the hatch side, 3 dark clamp straps holding it to the housing
Convention (Docs/AssetSpec.md, hall r7 set): Blender Z up, display face toward Blender +Y (= asset -Z, toward the
oncoming player in Unity); screen left = Blender +X when seen from +Y, so the pipe's flange end (-X) points at the hatch.
LOD0 / LOD1 (fewer segments, no rivets / bolts). Slots = Unity material names: M_DoorMachineBlue_s2,
M_DoorMachinePanel_s2, M_DoorMachineVent_s2 (MaterialLibrary.Assets.cs), M_Gold (metal domain).
Export: Assets/BubbleWashKingdom/Art/Models/Machinery/SM_DoorMachine_s2.fbx (root: DoorMachine_LOD0 / _LOD1);
preview Docs/AssetPreviews/SM_DoorMachine_s2.png (no reference pixels).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_door_machinery_s2.py door_machinery_s2
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bwk_common as C  # noqa: E402

_MP = os.path.join(HERE, "build_machinery.py")
_SRC = open(_MP, encoding="utf-8").read().rstrip()
assert _SRC.endswith("main()")
BM = {"__name__": "bwk_machinery_helpers", "__file__": _MP}
exec(compile(_SRC[: -len("main()")], _MP, "exec"), BM)
MB, lathe, rounded_box = BM["MB"], BM["lathe"], BM["rounded_box"]

SLOTS = ["M_DoorMachineBlue_s2", "M_DoorMachinePanel_s2", "M_DoorMachineVent_s2", "M_Gold"]
BLUE, PANEL, VENT, GOLD = range(4)
W, D, H = 3.0, 1.0, 2.4          # housing width (X), depth (Y), height (Z)
FY = D * 0.5                     # housing front plane (+Y)
PIPE_Y, PIPE_Z, PIPE_R = FY + 0.30, -0.05, 0.17
PIPE_X0, PIPE_X1 = 2.0, -2.15    # +X = screen left (runs out of frame), -X = toward the hatch


def rivet(mb, x, y, z, r, segs):
    # small domed rivet facing +Y
    prof = [(r, 0.0), (r, 0.012), (r * 0.82, r * 0.55), (r * 0.45, r * 0.85), (0.0, r * 0.95)]
    lathe(mb, prof, GOLD, segs, origin=(x, y, z), axis=(0.0, 1.0, 0.0))


def pipe_profile(q):
    """(r, h) along the pipe axis (h = metres from PIPE_X1 toward PIPE_X0): flange, collars, plain runs."""
    L = PIPE_X0 - PIPE_X1
    prof = [(0.0, 0.0), (0.27, 0.0), (0.285, 0.02), (0.285, 0.07), (0.27, 0.09), (PIPE_R + 0.02, 0.10), (PIPE_R, 0.13)]
    collars = [0.75, 1.75, 2.75, 3.65]
    for c in collars:
        w = 0.07
        prof += [(PIPE_R, c - w - 0.03), (PIPE_R + 0.035, c - w), (PIPE_R + 0.05, c - w * 0.45),
                 (PIPE_R + 0.05, c + w * 0.45), (PIPE_R + 0.035, c + w), (PIPE_R, c + w + 0.03)]
    prof += [(PIPE_R, L - 0.02), (0.0, L)]
    return prof


def build(q):
    mb = MB()
    seg_box = 3 if q else 1
    # housing + top cap + plinth
    rounded_box(mb, (0.0, 0.0, 0.0), (W, D, H), 0.14, seg_box, BLUE)
    rounded_box(mb, (0.0, 0.0, H * 0.5 + 0.06), (W + 0.18, D + 0.14, 0.22), 0.07, seg_box, PANEL)
    rounded_box(mb, (0.0, 0.0, -H * 0.5 - 0.05), (W + 0.2, D + 0.16, 0.26), 0.07, seg_box, PANEL)
    # raised panels: 2 columns x 2 rows, a band left free for the pipe at PIPE_Z
    for px in (-0.72, 0.72):
        for pz, ph in ((0.58, 0.82), (-0.70, 0.66)):
            rounded_box(mb, (px, FY + 0.025, pz), (1.26, 0.07, ph), 0.035, 2 if q else 1, PANEL)
            if q:
                for sx in (-1, 1):
                    for sz in (-1, 1):
                        rivet(mb, px + sx * 0.54, FY + 0.06, pz + sz * (ph * 0.5 - 0.07), 0.032, 8)
        # vent slots in the lower panels
        for k in range(5 if q else 3):
            z = -0.92 + k * (0.105 if q else 0.17)
            rounded_box(mb, (px, FY + 0.07, z), (0.92, 0.03, 0.045), 0.012, 1, VENT)
        # gauge in the upper panels: gold bezel + dark face + needle
        gz = 0.62
        bez = [(0.0, 0.0), (0.2, 0.0), (0.205, 0.04), (0.19, 0.07), (0.165, 0.075), (0.155, 0.05), (0.0, 0.05)]
        lathe(mb, bez, GOLD, 24 if q else 12, origin=(px, FY + 0.06, gz), axis=(0.0, 1.0, 0.0))
        rounded_box(mb, (px + 0.05, FY + 0.12, gz + 0.05), (0.13, 0.015, 0.025), 0.006, 1, VENT)
    # top rivet row on the cap
    if q:
        for k in range(9):
            rivet(mb, -1.4 + k * 0.35, FY + 0.07, H * 0.5 + 0.06, 0.03, 8)
    # gold pipe along X in front of the housing, flange end at the hatch side (-X)
    lathe(mb, pipe_profile(q), GOLD, 32 if q else 14, origin=(PIPE_X1, PIPE_Y, PIPE_Z), axis=(1.0, 0.0, 0.0))
    if q:
        for k in range(8):
            a = 2.0 * math.pi * (k + 0.5) / 8
            y, z = PIPE_Y + math.cos(a) * 0.235, PIPE_Z + math.sin(a) * 0.235
            lathe(mb, [(0.0, 0.0), (0.026, 0.0), (0.026, 0.05), (0.018, 0.065), (0.0, 0.068)], GOLD, 6,
                  origin=(PIPE_X1 + 0.09, y, z), axis=(1.0, 0.0, 0.0))
    # dark clamp straps + standoffs holding the pipe to the housing
    for cx in (1.25, 0.0, -1.25):
        rounded_box(mb, (cx, (FY + PIPE_Y) * 0.5, PIPE_Z), (0.12, PIPE_Y - FY + 0.06, 0.12), 0.02, 1, VENT)
        lathe(mb, [(PIPE_R + 0.005, -0.05), (PIPE_R + 0.03, -0.045), (PIPE_R + 0.03, 0.045), (PIPE_R + 0.005, 0.05)],
              VENT, 20 if q else 10, origin=(cx, PIPE_Y, PIPE_Z), axis=(1.0, 0.0, 0.0))
    return mb


def make_materials():
    return [C.material("M_DoorMachineBlue_s2", "#22307E", 0.2, 0.3),
            C.material("M_DoorMachinePanel_s2", "#5C7CDA", 0.2, 0.35),
            C.material("M_DoorMachineVent_s2", "#141A40", 0.1, 0.6),
            C.material("M_Gold", "#E8B04A", 1.0, 0.18)]


def main():
    C.reset_scene()
    mats = make_materials()
    lod0 = build(1).build("DoorMachine_LOD0", mats)
    lod1 = build(0).build("DoorMachine_LOD1", mats)
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    print("CHECK tris LOD0 %d LOD1 %d (%.0f %%)" % (t0, t1, 100.0 * t1 / t0))
    d = lod0.dimensions
    print("CHECK dims %.2f x %.2f x %.2f m" % (d.x, d.y, d.z))
    lod1.hide_render = True
    try:
        C.render_preview(C.preview_path("SM_DoorMachine_s2"), camera_location=(-3.2, 7.5, -1.2), target=(0.0, 0.3, 0.0),
                         lens=40.0, resolution=(900, 700))
        print("PREVIEW", C.preview_path("SM_DoorMachine_s2"))
    except Exception as e:
        print("CHECK preview failed:", e)
    lod1.hide_render = False
    root = bpy.data.objects.new("SM_DoorMachine_s2", None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lod0, lod1):
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_DoorMachine_s2"))
    C.save_work("door_machinery_s2.blend")
    print("DONE")


main()
