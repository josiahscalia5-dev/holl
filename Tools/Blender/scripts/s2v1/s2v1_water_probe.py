"""water-fx-artist probe (no render): which surfaces does the R2 camera ray hit at given pixels? (finds z-fighting pairs)
Run: bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_water_probe.py s2v1_water_probe"""
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s2v1_common as C  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=C.WORK + "/context.blend")
sc = bpy.context.scene
cam = bpy.data.objects["CAM_R2_16x9"]
W, H = cam["bwk_w"], cam["bwk_h"]
sc.render.resolution_x, sc.render.resolution_y = W, H
dg = bpy.context.evaluated_depsgraph_get()
fr = cam.data.view_frame(scene=sc)              # 4 corners in camera space: tr, br, bl, tl
tr, br, bl, tl = fr
mw = cam.matrix_world
origin = mw.translation
for (px, py) in ((300, 320), (330, 300), (360, 330), (250, 340), (200, 300), (420, 320)):   # 640x360 pixel coords
    u, v = px / 640.0, py / 360.0
    top = tl.lerp(tr, u); bot = bl.lerp(br, u)
    p_cam = top.lerp(bot, v)
    d = (mw.to_3x3() @ p_cam).normalized()
    o = origin.copy()
    hits = []
    travelled = 0.0
    for _ in range(8):
        ok, loc, nrm, idx, ob, _m = sc.ray_cast(dg, o, d, distance=60.0)
        if not ok:
            break
        dist = (loc - origin).length
        slot = ob.material_slots[ob.data.polygons[idx].material_index].material.name if ob.type == "MESH" and ob.material_slots else "-"
        hits.append("%s[%s] %.3f m n.z %.2f" % (ob.name[:34], slot, dist, nrm.z))
        o = loc + d * 0.0005
    print("CHECK probe px (%d,%d): %s" % (px, py, " | ".join(hits)))
for ob in bpy.data.objects:
    if ob.type == "MESH" and any(s.material and s.material.name.startswith("M_Arrow") for s in ob.material_slots):
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = [round(min(p[i] for p in bb), 2) for i in range(3)]; hi = [round(max(p[i] for p in bb), 2) for i in range(3)]
        print("CHECK probe chevron %s verts %d bbox %s .. %s" % (ob.name[:40], len(ob.data.vertices), lo, hi))
