# S2 Tunnel v1 - ASSEMBLY + RENDER (LEAD-owned; every specialist renders through this, nobody edits it - propose changes).
# Opens the cached Unity context (Tools/Blender/work/s2v1/context.blend), runs the team's modules in order and renders the game's cameras:
#   s2v1_env.py       (environment-modeler)  build(ctx) -> list of TRACK-SPACE objects (X lateral, Y = track distance d, Z height);
#                                            optional REPLACES = [context collections to hide, e.g. "CTX_old_tunnel_wall"]
#   s2v1_materials.py (materials-artist)     apply(ctx)
#   s2v1_water.py     (water-fx-artist)      apply(ctx)
#   s2v1_lighting.py  (lighting-artist)      apply(ctx)   (engine, samples, view transform, world, lights, compositor)
# ctx = {"scene", "world_objects" (bent copies of the env objects), "track_objects", "C" (s2v1_common), "tag", "out_dir"}.
# A module that is missing or raises is reported and skipped (the others still render) - read the log.
# Env vars: TAG (output folder name, default time stamp), CAMERAS (comma list, default "R2_16x9,RIG_d33.5_9x16,RIG_d38.5_9x16,
# RIG_d44.0_9x16"), SCALE (render scale, default 1.0; 0.5 = fast), SHOW_OLD=1 (keep the old Unity tunnel visible), SAVE_BLEND=1
# (save the assembled scene as Tools/Blender/work/s2v1/assembled_<TAG>.blend).
# Outputs: Captures/s2v1/renders/<TAG>/<camera>.png, SHEET_R2.png (ORIGINAL | Unity current | v1), SHEET_RIG.png (Unity current |
# v1 at each rig distance), metrics_R2.txt (Tools/s2_look_metrics.py). Reference pixels stay in Captures/ (gitignored).
# Run: TAG=my_test bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_render.py s2v1_my_test
import contextlib
import importlib.util
import io
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

TAG = os.environ.get("TAG") or time.strftime("r%H%M%S")
CAMS = [c.strip() for c in (os.environ.get("CAMERAS") or "R2_16x9,RIG_d33.5_9x16,RIG_d38.5_9x16,RIG_d44.0_9x16").split(",") if c.strip()]
SCALE = float(os.environ.get("SCALE") or 1.0)
OUT = C.CAPT + "/renders/" + TAG
os.makedirs(OUT, exist_ok=True)
UNITY_R2 = "C:/Users/josia/thanksgiving/Captures/lead/s2_projection/R2_current_1280x720.png"
UNITY_RIG = "C:/Users/josia/thanksgiving/Captures/lead/s2_projection/prev_v1/current_rig_d%s_9x16.png"


def load_module(name):
    path = os.path.join(HERE, name + ".py")
    if not os.path.exists(path):
        print("ASSEMBLY module %s: not present (skipped)" % name)
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


t_start = time.time()
if not os.path.exists(C.WORK + "/context.blend"):
    C.build_context(save=True)
bpy.ops.wm.open_mainfile(filepath=C.WORK + "/context.blend")
sc = bpy.context.scene
ctx = {"scene": sc, "world_objects": [], "track_objects": [], "C": C, "tag": TAG, "out_dir": OUT}

env = load_module("s2v1_env")
if env is not None:
    try:
        t0 = time.time()
        track_objs = env.build(ctx) or []
        ctx["track_objects"] = track_objs
        wc = C.coll("S2V1_WORLD")
        for o in track_objs:
            ctx["world_objects"].append(C.to_world_mesh(o, collection=wc))
        tc = bpy.data.collections.get("S2V1_TRACK")
        for o in track_objs:                      # the track-space sources never render
            o.hide_render = True; o.hide_viewport = True
        if os.environ.get("SHOW_OLD") != "1":
            for cname in getattr(env, "REPLACES", ["CTX_old_tunnel_wall", "CTX_old_tunnel_rings", "CTX_old_tunnel_stars"]):
                c = bpy.data.collections.get(cname)
                if c:
                    c.hide_render = True
        print("ASSEMBLY env: %d objects bent to world in %.1f s" % (len(track_objs), time.time() - t0))
    except Exception:
        print("ASSEMBLY env FAILED:\n" + traceback.format_exc())

for name in ("s2v1_materials", "s2v1_water", "s2v1_lighting"):
    mod = load_module(name)
    if mod is None:
        continue
    try:
        t0 = time.time(); mod.apply(ctx); print("ASSEMBLY %s.apply OK (%.1f s)" % (name, time.time() - t0))
    except Exception:
        print("ASSEMBLY %s FAILED:\n%s" % (name, traceback.format_exc()))

if sc.render.engine not in ("BLENDER_EEVEE", "CYCLES"):          # lighting module absent -> neutral default
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
if os.environ.get("SAVE_BLEND") == "1":
    bpy.ops.wm.save_as_mainfile(filepath=C.WORK + "/assembled_%s.blend" % TAG, copy=True)

done = []
for cam in CAMS:
    if "CAM_" + cam not in bpy.data.objects:
        print("ASSEMBLY camera %s unknown (have: %s)" % (cam, ", ".join(sorted(C.cameras()))))
        continue
    t0 = time.time()
    C.render_camera(cam, OUT + "/%s.png" % cam, scale=SCALE)
    print("PREVIEW %s/%s.png (%.1f s, engine %s)" % (OUT, cam, time.time() - t0, sc.render.engine))
    done.append(cam)

# comparison sheets (numbers + images stay in Captures/)
try:
    from img_crop import read_png, write_png

    def fit(a, h):
        ys = np.linspace(0, a.shape[0] - 1, h).astype(int); xs = np.linspace(0, a.shape[1] - 1, int(round(a.shape[1] * h / a.shape[0]))).astype(int)
        return a[ys][:, xs]
    gap = lambda h: np.full((h, 10, 3), 24, np.uint8)
    if "R2_16x9" in done:
        parts = [fit(np.asarray(read_png(p))[..., :3], 720) for p in (C.REF_720, UNITY_R2, OUT + "/R2_16x9.png") if os.path.exists(p)]
        row = parts[0]
        for p in parts[1:]:
            row = np.concatenate([row, gap(720), p], 1)
        write_png(OUT + "/SHEET_R2.png", row)
        import s2_look_metrics as M
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            M.main([OUT + "/R2_16x9.png"])
        open(OUT + "/metrics_R2.txt", "w").write(buf.getvalue())
        print("PREVIEW %s/SHEET_R2.png  (ORIGINAL | Unity current | v1)" % OUT)
        for line in buf.getvalue().splitlines()[:10]:
            print("CHECK metrics " + line)
    rows = []
    for cam in done:
        if not cam.startswith("RIG_d"):
            continue
        d = cam.split("_d")[1].split("_")[0]
        u = UNITY_RIG % d
        b = fit(np.asarray(read_png(OUT + "/%s.png" % cam))[..., :3], 960)
        rows.append(np.concatenate([fit(np.asarray(read_png(u))[..., :3], 960), gap(960), b], 1) if os.path.exists(u) else b)
    if rows:
        sheet = rows[0]
        for r in rows[1:]:
            sheet = np.concatenate([sheet, np.full((960, 30, 3), 70, np.uint8), r], 1)
        write_png(OUT + "/SHEET_RIG.png", sheet)
        print("PREVIEW %s/SHEET_RIG.png  (per distance: Unity current | v1)" % OUT)
except Exception:
    print("ASSEMBLY sheets FAILED:\n" + traceback.format_exc())
print("DONE assembly %s: %d cameras in %.1f s" % (TAG, len(done), time.time() - t_start))
