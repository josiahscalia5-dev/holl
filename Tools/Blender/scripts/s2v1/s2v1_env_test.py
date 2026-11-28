"""S2 Tunnel v1 - environment-modeler QUICK TEST (no context.blend): build() in an empty scene, bend to world like the assembly,
report tris / timings, render R2 (+ optional rig cameras) with flat Workbench colours and write
Captures/s2v1/env/test_<TAG>/: <cam>.png, R2_blend.png (50 % over the ORIGINAL, private), R2_pair.png (ORIGINAL | env).
Run: TAG=t01 bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_env_test.py s2v1_env_test
Env: CAMERAS (default R2_16x9), SCALE (default 0.5), S2V1_DRUM_VIEW (hp | game)."""
import os
import sys
import time
import traceback

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "C:/Users/josia/thanksgiving/Tools")
import s2v1_common as C  # noqa: E402

TAG = os.environ.get("TAG") or time.strftime("t%H%M%S")
CAMS = [c for c in (os.environ.get("CAMERAS") or "R2_16x9").split(",") if c]
SCALE = float(os.environ.get("SCALE") or 0.5)
OUT = C.CAPT + "/env/test_" + TAG
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for name, cj in C.cameras().items():
    C.make_camera(cj)
ctx = {"scene": sc, "world_objects": [], "track_objects": [], "C": C, "tag": TAG, "out_dir": OUT}
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("s2v1_env", HERE + "/s2v1_env.py")
env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(env)
t0 = time.time()
try:
    objs = env.build(ctx)
    t1 = time.time()
    wc = C.coll("S2V1_WORLD")
    for o in objs:
        ctx["world_objects"].append(C.to_world_mesh(o, collection=wc))
    for o in objs:
        o.hide_render = True; o.hide_viewport = True
    print("CHECK test build %.1f s, bend %.1f s, %d objects" % (t1 - t0, time.time() - t1, len(objs)))
except Exception:
    print("CHECK test build FAILED:\n" + traceback.format_exc())
    raise

sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "MATERIAL"
sh.show_cavity = False
sh.show_shadows = False
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("W") if sc.world is None else sc.world
sc.world.color = (0.02, 0.02, 0.03)
from img_crop import read_png, write_png  # noqa: E402

for cam in CAMS:
    C.render_camera(cam, OUT + "/%s.png" % cam, scale=SCALE)
    print("PREVIEW %s/%s.png" % (OUT, cam))
if "R2_16x9" in CAMS:
    ref = np.asarray(read_png(C.REF_720))[..., :3].astype(np.float32)
    ren = np.asarray(read_png(OUT + "/R2_16x9.png"))[..., :3].astype(np.float32)
    ys = np.linspace(0, ren.shape[0] - 1, ref.shape[0]).astype(int); xs = np.linspace(0, ren.shape[1] - 1, ref.shape[1]).astype(int)
    ren = ren[ys][:, xs]
    write_png(OUT + "/R2_blend.png", (0.5 * ref + 0.5 * ren).astype(np.uint8))
    write_png(OUT + "/R2_pair.png", np.concatenate([ref, np.full((ref.shape[0], 8, 3), 30, np.float32), ren], 1).astype(np.uint8))
    print("PREVIEW %s/R2_blend.png" % OUT)
print("DONE env test %s in %.1f s" % (TAG, time.time() - t0))
