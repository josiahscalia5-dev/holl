"""S2 Tunnel v1 -> Unity TRANSFER EXPORT (LEAD-owned; lead a557ee90 2026-11-27, owner 22:33 "my actual game is the Unity version:
selectively transfer genuinely superior Blender assets into an ISOLATED Unity test scene"). Specialists never edit this file.

Builds the team's v1 environment exactly like the assembly (s2v1_render.py): s2v1_env.build(ctx) in TRACK space -> bent to world with
the game's own mapping (s2v1_common.to_world_mesh) -> s2v1_materials.apply(ctx) / s2v1_lighting.apply(ctx) when present, then writes
for Unity (Assets/BubbleWashKingdom/Scripts/Editor/S2v1TestScene.cs reads it):
  OUT/manifest.json      parts (name, s2v1_part tag, colour, mesh file, tris, Unity-world bounds), materials (Principled / Emission values,
                         linked image textures, procedural flags), lights, world + render settings, the replaced track range, source info
  OUT/meshes/<name>.bwkm raw mesh in UNITY WORLD coordinates (left-handed, Y up): positions, normals, uv0 [, uv1], submeshes per material
  OUT/textures/<file>    every image a material uses (bakes), copied
Coordinates: Blender world (x, y, z) -> Unity world (x, z, y) = a mirror -> triangle winding reversed (a, c, b) so front faces stay front.

Run (heavy, foreground, through the lock):
  OUT=Tools/Blender/work/s2v1/unity_v1/<name> bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_export_unity.py s2v1_export_unity
Env: OUT (default Tools/Blender/work/s2v1/unity_v1/latest), SRC (a Captures/s2v1/renders/<TAG>/_src folder = export exactly that preserved
     state, e.g. the BEST one; default = the live modules), CONTEXT (1 = open context.blend first like the assembly, needed when
     materials / lighting touch context objects; default 1), PARTS (comma list of s2v1_part tags to export; default all but drum_hp),
     SKIP_MODULES (comma list, e.g. s2v1_materials,s2v1_lighting = geometry-only export that never runs a module which might bake
     while its artist works).
.bwkm layout (little-endian): b"BWKM", int32 version 1, int32 vertexCount, int32 flags (1 = uv0, 2 = uv1), float32 pos[3n], float32 nrm[3n],
  [float32 uv0[2n]], [float32 uv1[2n]], int32 submeshCount, per submesh: int32 materialIndex (manifest "materials"), int32 indexCount,
  uint32 indices[indexCount].
"""
import importlib.util
import json
import os
import shutil
import struct
import sys
import time
import traceback

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("SRC") or ""
MODDIR = SRC if SRC and os.path.isdir(SRC) else HERE
sys.path.insert(0, HERE)
if MODDIR != HERE:
    sys.path.insert(0, MODDIR)
sys.path.insert(0, "C:/Users/josia/thanksgiving/Tools")
import s2v1_common as C  # noqa: E402

ROOT = C.ROOT
OUT = os.environ.get("OUT") or (C.WORK + "/unity_v1/latest")
if not os.path.isabs(OUT):
    OUT = os.path.join(ROOT, OUT)
OUT = OUT.replace("\\", "/")
PARTS = [p.strip() for p in (os.environ.get("PARTS") or "").split(",") if p.strip()]
CONTEXT = os.environ.get("CONTEXT", "1") != "0"
SKIP_MODULES = {m.strip() for m in (os.environ.get("SKIP_MODULES") or "").split(",") if m.strip()}
SKIP_PARTS = {"drum_hp"}


def load_module(name):
    path = os.path.join(MODDIR, name + ".py")
    if not os.path.exists(path):
        print("EXPORT module %s: not present in %s (skipped)" % (name, MODDIR))
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def b2u(a):
    """(N, 3) Blender world -> Unity world (x, z, y)."""
    return a[:, [0, 2, 1]]


# ------------------------------------------------------------------------------------------------ materials
def _trace_image(sock, depth=0):
    """Follow a linked input back through reroutes / normal-map / simple pass-through nodes to an Image Texture node."""
    if not sock.is_linked or depth > 6:
        return None, None
    node = sock.links[0].from_node
    if node.type == "TEX_IMAGE" and node.image is not None:
        return node, None
    if node.type in ("REROUTE",):
        return _trace_image(node.inputs[0], depth + 1)
    if node.type == "NORMAL_MAP":
        img, _ = _trace_image(node.inputs.get("Color") or node.inputs[1], depth + 1)
        return img, {"normal_strength": float(node.inputs.get("Strength").default_value) if node.inputs.get("Strength") else 1.0}
    return None, node.type


def _val(inp):
    v = inp.default_value
    try:
        return [float(x) for x in v]
    except TypeError:
        return float(v)


def export_image(node, tex_dir):
    img = node.image
    src = bpy.path.abspath(img.filepath_raw or img.filepath or "")
    name = os.path.basename(src) if src else (img.name + ".png")
    dst = os.path.join(tex_dir, name)
    try:
        if src and os.path.exists(src):
            shutil.copy2(src, dst)
        else:                                   # generated / packed image: save a copy
            img.save_render(dst)
    except Exception as e:
        print("EXPORT image %s failed: %s" % (img.name, e))
        return None
    return {"file": "textures/" + name, "colorspace": img.colorspace_settings.name, "size": list(img.size),
            "interpolation": node.interpolation, "extension": node.extension}


def describe_material(mat, tex_dir):
    d = {"name": mat.name if mat else "none", "shader": None, "values": {}, "textures": {}, "procedural": {}, "blend_method":
         getattr(mat, "blend_method", None) if mat else None}
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        if mat is not None:
            d["values"]["Base Color"] = list(mat.diffuse_color)
        return d
    nt = mat.node_tree
    outs = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
    out = next((n for n in outs if n.is_active_output), outs[0] if outs else None)
    if out is None or not out.inputs["Surface"].is_linked:
        return d
    sh = out.inputs["Surface"].links[0].from_node
    d["shader"] = sh.type
    shaders = [sh]
    if sh.type in ("MIX_SHADER", "ADD_SHADER"):                       # record both branches (first Principled wins below)
        shaders = [l.from_node for i in sh.inputs if i.is_linked for l in i.links]
        d["mix"] = [s.type for s in shaders]
        if sh.type == "MIX_SHADER" and not sh.inputs[0].is_linked:
            d["values"]["mix_fac"] = float(sh.inputs[0].default_value)
    for s in shaders:
        if s.type == "BSDF_PRINCIPLED":
            for inp in s.inputs:
                if inp.type not in ("RGBA", "VALUE", "VECTOR") or inp.name in ("Weight",):
                    continue
                if inp.is_linked:
                    node, info = _trace_image(inp)
                    if node is not None:
                        t = export_image(node, tex_dir)
                        if t:
                            if isinstance(info, dict):
                                t.update(info)
                            d["textures"][inp.name] = t
                    else:
                        d["procedural"][inp.name] = info or "linked"
                        if inp.type != "VECTOR":
                            d["values"][inp.name] = _val(inp)       # unlinked default (fallback only)
                elif inp.type != "VECTOR":
                    d["values"][inp.name] = _val(inp)
            break
        if s.type == "EMISSION":
            d["values"].setdefault("Emission Color", _val(s.inputs["Color"]))
            d["values"].setdefault("Emission Strength", _val(s.inputs["Strength"]))
            if s.inputs["Color"].is_linked:
                d["procedural"]["Emission Color"] = "linked"
        if s.type == "BSDF_TRANSPARENT":
            d["values"]["transparent_mix"] = True
    return d


# ------------------------------------------------------------------------------------------------ meshes
def write_mesh(obj, mat_index_of, path):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        me.calc_loop_triangles()
        nlt = len(me.loop_triangles)
        if nlt == 0:
            return 0, None
        mw = np.array(obj.matrix_world, dtype=np.float64)
        nv, nl = len(me.vertices), len(me.loops)
        co = np.empty(nv * 3, np.float64); me.vertices.foreach_get("co", co); co = co.reshape(nv, 3)
        co = (mw[:3, :3] @ co.T).T + mw[:3, 3]
        lv = np.empty(nl, np.int64); me.loops.foreach_get("vertex_index", lv)
        cn = np.empty(nl * 3, np.float64)
        try:
            me.corner_normals.foreach_get("vector", cn)
        except AttributeError:                                         # Blender < 4.1
            me.calc_normals_split(); me.loops.foreach_get("normal", cn)
        cn = cn.reshape(nl, 3)
        nm = np.linalg.inv(mw[:3, :3]).T
        cn = (nm @ cn.T).T
        cn /= np.maximum(np.linalg.norm(cn, axis=1, keepdims=True), 1e-12)
        uvs = []
        for k in range(min(2, len(me.uv_layers))):
            uv = np.empty(nl * 2, np.float64); me.uv_layers[k].data.foreach_get("uv", uv); uvs.append(uv.reshape(nl, 2))
        tl = np.empty(nlt * 3, np.int64); me.loop_triangles.foreach_get("loops", tl); tl = tl.reshape(nlt, 3)
        tm = np.empty(nlt, np.int64); me.loop_triangles.foreach_get("material_index", tm)
        # one Unity vertex per unique (vertex, normal, uv0, uv1) corner
        key = [lv[:, None].astype(np.float64), np.round(cn, 4)] + [np.round(u, 5) for u in uvs]
        K = np.ascontiguousarray(np.concatenate(key, 1))
        _, first, inv = np.unique(K, axis=0, return_index=True, return_inverse=True)
        inv = inv.ravel()
        P = b2u(co[lv[first]]).astype(np.float32)
        N = b2u(cn[first]).astype(np.float32)
        U = [u[first].astype(np.float32) for u in uvs]
        tri = inv[tl]                                                   # (nlt, 3) Unity vertex ids
        tri = tri[:, [0, 2, 1]]                                         # mirror -> reverse winding
        flags = (1 if len(U) > 0 else 0) | (2 if len(U) > 1 else 0)
        subs = []
        slots = [s.material for s in obj.material_slots] or [None]
        for mi in sorted(set(tm.tolist())):
            sel = tri[tm == mi].ravel().astype(np.uint32)
            mat = slots[mi] if mi < len(slots) else None
            subs.append((mat_index_of(mat), sel))
        with open(path, "wb") as f:
            f.write(b"BWKM"); f.write(struct.pack("<iii", 1, len(P), flags))
            f.write(P.tobytes()); f.write(N.tobytes())
            for u in U[:2]:
                f.write(u.tobytes())
            f.write(struct.pack("<i", len(subs)))
            for m, idx in subs:
                f.write(struct.pack("<ii", m, len(idx))); f.write(idx.tobytes())
        bmin, bmax = P.min(0), P.max(0)
        return nlt, {"min": bmin.tolist(), "max": bmax.tolist(), "vertices": int(len(P)), "submeshes": len(subs), "uv_sets": len(U)}
    finally:
        ev.to_mesh_clear()


# ------------------------------------------------------------------------------------------------ main
t_start = time.time()
os.makedirs(OUT + "/meshes", exist_ok=True)
os.makedirs(OUT + "/textures", exist_ok=True)
if CONTEXT and os.path.exists(C.WORK + "/context.blend"):
    bpy.ops.wm.open_mainfile(filepath=C.WORK + "/context.blend")
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, cj in C.cameras().items():
        C.make_camera(cj)
sc = bpy.context.scene
ctx = {"scene": sc, "world_objects": [], "track_objects": [], "C": C, "tag": "export_unity", "out_dir": OUT}
errors = []
env = load_module("s2v1_env")
if env is None:
    raise SystemExit("EXPORT: no s2v1_env.py - nothing to transfer")
track_objs = env.build(ctx) or []
ctx["track_objects"] = track_objs
wc = C.coll("S2V1_WORLD")
for o in track_objs:
    ctx["world_objects"].append(C.to_world_mesh(o, collection=wc))
for o in track_objs:
    o.hide_render = True; o.hide_viewport = True
for name in ("s2v1_materials", "s2v1_lighting"):
    if name in SKIP_MODULES:
        print("EXPORT module %s skipped (SKIP_MODULES)" % name)
        continue
    mod = load_module(name)
    if mod is None:
        continue
    try:
        mod.apply(ctx); print("EXPORT %s.apply OK" % name)
    except Exception:
        errors.append(name); print("EXPORT %s FAILED:\n%s" % (name, traceback.format_exc()))
for h in list(bpy.app.handlers.render_pre):                         # the env's drum-view handler decides hp vs game at render time
    try:
        if getattr(h, "__name__", "") == "_drum_view":
            h(sc)
    except Exception:
        pass

materials, mat_ids = [], {}


def mat_index_of(mat):
    key = mat.name if mat else "none"
    if key not in mat_ids:
        mat_ids[key] = len(materials)
        materials.append(describe_material(mat, OUT + "/textures"))
    return mat_ids[key]


parts = []
for o in ctx["world_objects"]:
    tag = o.get("s2v1_part", "other")
    if tag in SKIP_PARTS or (PARTS and tag not in PARTS):
        continue
    fname = "meshes/%s.bwkm" % o.name.replace(" ", "_")
    try:
        ntri, info = write_mesh(o, mat_index_of, OUT + "/" + fname)
    except Exception:
        errors.append(o.name); print("EXPORT mesh %s FAILED:\n%s" % (o.name, traceback.format_exc())); continue
    if not ntri:
        continue
    parts.append({"name": o.name, "source": o.get("s2v1_source"), "part": tag, "color": o.get("s2v1_color"), "file": fname,
                  "tris": ntri, "hide_render": bool(o.hide_render), **info})
    print("EXPORT part %-30s %-12s tris %7d -> %s" % (o.name, tag, ntri, fname))

lights = []
for o in sc.objects:
    if o.type == "LIGHT" and (o.name.startswith("LGT_S2v1") or o.get("s2v1_part")) and not o.hide_render:
        L = o.data
        p = np.array(o.matrix_world.translation)[None, :]
        fwd = np.array(o.matrix_world.to_3x3() @ __import__("mathutils").Vector((0, 0, -1)))[None, :]
        lights.append({"name": o.name, "type": L.type, "pos": b2u(p)[0].tolist(), "dir": b2u(fwd)[0].tolist(),
                       "color": list(L.color), "energy_w": float(L.energy), "radius": float(getattr(L, "shadow_soft_size", 0.0)),
                       "spot_size_deg": float(np.degrees(getattr(L, "spot_size", 0.0))) if L.type == "SPOT" else None,
                       "size": float(getattr(L, "size", 0.0)) if L.type == "AREA" else None})
world = {}
if sc.world is not None:
    world["color"] = list(sc.world.color)
    if sc.world.use_nodes and sc.world.node_tree:
        bg = next((n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND"), None)
        if bg is not None:
            world["background"] = _val(bg.inputs[0]) if not bg.inputs[0].is_linked else "linked"
            world["strength"] = _val(bg.inputs[1])
render = {"engine": sc.render.engine, "view_transform": sc.view_settings.view_transform, "look": sc.view_settings.look,
          "exposure": sc.view_settings.exposure, "gamma": sc.view_settings.gamma}
glare = []
try:
    nt = sc.compositing_node_group if hasattr(sc, "compositing_node_group") else sc.node_tree
    if nt is not None:
        for n in nt.nodes:
            if n.type == "GLARE":
                glare.append({k: (getattr(n, k) if not hasattr(getattr(n, k), "__len__") or isinstance(getattr(n, k), str) else list(getattr(n, k)))
                              for k in ("glare_type", "quality", "threshold", "mix", "size", "strength", "saturation") if hasattr(n, k)})
except Exception as e:
    glare.append({"error": str(e)})

manifest = {
    "note": "S2 Tunnel v1 transfer export (lead a557ee90, owner 22:33). Meshes in UNITY WORLD coordinates (left-handed, Y up), winding "
            "already reversed for Unity; colours in Blender linear RGB; emission = colour * strength (Blender W/m2-ish units).",
    "built": time.strftime("%Y-%m-%d %H:%M:%S"),
    "source_modules": MODDIR.replace("\\", "/"),
    "module_mtimes": {os.path.basename(p): time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p)))
                      for p in [os.path.join(MODDIR, f) for f in os.listdir(MODDIR)] if p.endswith(".py") and "s2v1_" in p},
    "replaced_d": [getattr(env, "D0", 40.2), getattr(env, "D1", 80.0)],
    "trim_old": getattr(env, "TRIM_OLD", []),
    "trim_from": getattr(env, "TRIM_FROM", {}),
    "parts": parts, "materials": materials, "lights": lights, "world": world, "render": render, "glare": glare,
    "errors": errors, "skipped_modules": sorted(SKIP_MODULES),
}
with open(OUT + "/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)


# flat, fixed-schema copy for Unity's JsonUtility (S2v1TestScene.cs): no dicts, every field always present
def _flat_mat(m):
    v, t = m.get("values", {}), m.get("textures", {})

    def col(k, n):
        x = v.get(k)
        x = [float(a) for a in x][:n] if isinstance(x, list) else [0.0] * n
        return x + [1.0] * (n - len(x))

    num = lambda k, dflt: float(v[k]) if isinstance(v.get(k), (int, float)) and not isinstance(v.get(k), bool) else dflt
    tex = lambda k: (t.get(k) or {}).get("file", "")
    return {"name": m["name"], "shader": m.get("shader") or "", "procedural": ",".join(sorted(m.get("procedural", {}).keys())),
            "base_color": col("Base Color", 4), "metallic": num("Metallic", 0.0), "roughness": num("Roughness", 0.5),
            "emission_color": col("Emission Color", 3), "emission_strength": num("Emission Strength", 0.0), "alpha": num("Alpha", 1.0),
            "coat": num("Coat Weight", 0.0), "transmission": num("Transmission Weight", 0.0),
            "normal_strength": float((t.get("Normal") or {}).get("normal_strength", 1.0)),
            "tex_base": tex("Base Color"), "tex_normal": tex("Normal"), "tex_roughness": tex("Roughness"), "tex_metallic": tex("Metallic"),
            "tex_emission": tex("Emission Color"), "tex_ao": ""}


flat = {"built": manifest["built"], "source_modules": manifest["source_modules"],
        "replaced_d0": float(manifest["replaced_d"][0]), "replaced_d1": float(manifest["replaced_d"][1]),
        "stars_from": float((manifest["trim_from"] or {}).get("CTX_old_tunnel_stars", manifest["replaced_d"][0])),
        "parts": [{"name": p["name"], "part": p["part"], "color": p.get("color") or "", "file": p["file"], "tris": int(p["tris"]),
                   "hide_render": bool(p.get("hide_render"))} for p in parts],
        "materials": [_flat_mat(m) for m in materials]}
with open(OUT + "/manifest_unity.json", "w", encoding="utf-8") as f:
    json.dump(flat, f, indent=1)
by = {}
for p in parts:
    by.setdefault(p["part"], [0, 0]); by[p["part"]][0] += 1; by[p["part"]][1] += p["tris"]
for k, (n, t) in sorted(by.items()):
    print("CHECK export %-12s %3d parts %8d tris" % (k, n, t))
print("CHECK export: %d parts, %d materials, %d lights, errors %s" % (len(parts), len(materials), len(lights), errors or "none"))
print("DONE export %s in %.1f s" % (OUT, time.time() - t_start))
