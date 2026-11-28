# S2 Tunnel v1 (LEAD): build the cached context.blend from the Unity export, verify the coordinate mapping, render the R2 camera for an
# alignment check against Unity's own R2 render, and time EEVEE vs Workbench on this laptop.
# Run: bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_context_check.py lead_s2v1_context
import os
import sys
import time

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s2v1_common as C  # noqa: E402

t0 = time.time()
n = C.build_context(save=True)
print("CHECK context objects %d imported + saved in %.1f s" % (n, time.time() - t0))
for c in bpy.data.collections:
    if c.name.startswith("CTX_"):
        nv = sum(len(o.data.vertices) for o in c.objects if o.type == "MESH")
        print("CHECK collection %-26s objects %4d verts %8d" % (c.name, len(c.objects), nv))

# face orientation on the old drum: normals must point INTO the tunnel (towards the axis)
drum = [o for o in bpy.data.collections["CTX_old_tunnel_wall"].objects] if "CTX_old_tunnel_wall" in bpy.data.collections else []
if drum:
    o = drum[0]; me = o.data
    me.calc_loop_triangles() if hasattr(me, "calc_loop_triangles") else None
    nf = len(me.polygons)
    cen = np.empty(nf * 3); nor = np.empty(nf * 3)
    me.polygons.foreach_get("center", cen); me.polygons.foreach_get("normal", nor)
    cen = cen.reshape(-1, 3); nor = nor.reshape(-1, 3)
    # axis point for each face: nearest track frame at the same d is unknown here -> use the frame whose position is closest
    F = C._frame_arrays(); pos_b = F["pos"][:, [0, 2, 1]]; up_b = F["flatUp"][:, [0, 2, 1]]
    axis = pos_b + up_b * C.TUNNEL_C
    k = np.argmin(((cen[::50, None, :] - axis[None, :, :]) ** 2).sum(-1), axis=1)
    to_axis = axis[k] - cen[::50]
    inward = (np.einsum("ij,ij->i", to_axis, nor[::50]) > 0).mean()
    print("CHECK drum faces pointing inward: %.1f %% (want ~100)" % (100 * inward))

# alignment render: Workbench, object-random colours, R2 camera
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.color_type = "RANDOM"
sc.display.shading.light = "STUDIO"
os.makedirs(C.CAPT + "/setup", exist_ok=True)
t0 = time.time()
C.render_camera("R2_16x9", C.CAPT + "/setup/R2_workbench.png")
print("CHECK workbench R2 render %.1f s" % (time.time() - t0))
C.render_camera("RIG_d38.5_9x16", C.CAPT + "/setup/RIG_d38.5_workbench.png")

# EEVEE timing (default materials, no lights except world) - tells the team how fast look iterations can be
try:
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16
    w = bpy.data.worlds.new("W_check"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.03, 0.12, 1)
    t0 = time.time()
    C.render_camera("R2_16x9", C.CAPT + "/setup/R2_eevee_check.png")
    print("CHECK eevee R2 render 16 samples %.1f s" % (time.time() - t0))
except Exception as e:
    print("CHECK eevee FAILED:", repr(e))
print("DONE")
