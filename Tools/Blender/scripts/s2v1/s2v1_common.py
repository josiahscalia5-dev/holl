"""S2 Tunnel v1 - shared foundation (LEAD-owned; specialists import it, never edit it - propose changes in your report).

Coordinates
- Unity world: left-handed, Y up. Blender world: right-handed, Z up. Mapping (a mirror): (x, y, z)_unity -> (x, z, y)_blender.
- TRACK SPACE (how the team AUTHORS the new tunnel): Blender X = lateral (m, + = right of the track), Y = track distance d (m, e.g.
  door at 40.0), Z = height above the track centre line (m; the tunnel axis is at Z = 2.3, radius 4.2). `to_world_mesh()` bends a
  track-space mesh exactly like the game's SplineMeshDeformer (BendChunks, useBank false):
      world_unity = pos(d) + flatRight(d) * x + flatUp(d) * z        (d = Y)
  so what renders here is where Unity will put it, and the same straight module exports to Unity later.
- Cameras: the game's own R2 comparison camera (= the original 3.00 s framing) and the unchanged gameplay rig at several distances,
  exported from Unity by S2v1Export.ExportBatch (Tools/Blender/work/s2v1/unity_export/s2_layout.json).
"""
import json
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = "C:/Users/josia/thanksgiving"
WORK = ROOT + "/Tools/Blender/work/s2v1"
EXPORT = WORK + "/unity_export"
CAPT = ROOT + "/Captures/s2v1"
REF_720 = ROOT + "/Reference/frames4k_720/f_03.00s.png"
REF_4K = ROOT + "/Reference/frames4k/f_03.00s.png"
TUNNEL_R, TUNNEL_C, DOOR_D = 4.2, 2.3, 40.0

_layout = None
_frames = None


def layout():
    global _layout
    if _layout is None:
        with open(EXPORT + "/s2_layout.json", encoding="utf-8") as f:
            _layout = json.load(f)
    return _layout


def u2b(v):
    return (v[0], v[2], v[1])


def _frame_arrays():
    global _frames
    if _frames is None:
        fr = layout()["frames"]
        _frames = {k: np.array([f[k] for f in fr], dtype=np.float64) for k in ("pos", "fwd", "flatUp", "flatRight")}
        _frames["d"] = np.array([f["d"] for f in fr], dtype=np.float64)
    return _frames


def frame_at(d):
    """Track frame (Unity world) at distance d: linear interpolation of the 0.25 m samples (vectors re-normalised)."""
    F = _frame_arrays()
    ds = F["d"]
    d = float(np.clip(d, ds[0], ds[-1]))
    i = int(np.clip(np.searchsorted(ds, d) - 1, 0, len(ds) - 2))
    t = (d - ds[i]) / (ds[i + 1] - ds[i])
    out = {}
    for k in ("pos", "fwd", "flatUp", "flatRight"):
        v = F[k][i] * (1 - t) + F[k][i + 1] * t
        out[k] = v if k == "pos" else v / np.linalg.norm(v)
    return out


def track_to_world_unity(P):
    """P: (N, 3) track-space points (x lateral, y = d, z height) -> (N, 3) Unity world."""
    F = _frame_arrays()
    ds = F["d"]
    d = np.clip(P[:, 1], ds[0], ds[-1])
    i = np.clip(np.searchsorted(ds, d) - 1, 0, len(ds) - 2)
    t = ((d - ds[i]) / (ds[i + 1] - ds[i]))[:, None]
    lerp = lambda k: F[k][i] * (1 - t) + F[k][i + 1] * t
    pos, up, right = lerp("pos"), lerp("flatUp"), lerp("flatRight")
    up /= np.linalg.norm(up, axis=1, keepdims=True)
    right /= np.linalg.norm(right, axis=1, keepdims=True)
    return pos + right * P[:, 0:1] + up * P[:, 2:3]


def track_to_blender(P):
    W = track_to_world_unity(np.asarray(P, dtype=np.float64).reshape(-1, 3))
    return W[:, [0, 2, 1]]


def to_world_mesh(obj, name=None, collection=None):
    """Return a NEW object = obj's evaluated mesh (modifiers applied) bent from track space into Blender world (exact game mapping).
    The track-space source stays untouched (author there, render the bent copy)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(obj.matrix_world)
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = track_to_blender(co.reshape(n, 3)).astype(np.float32).ravel()
    me.vertices.foreach_set("co", co)
    me.update()
    # the bend is (locally) a mirror of track space? no: track space (x right, y forward, z up) is right-handed in Blender and the
    # Unity frame (right, up, forward) mapped by u2b is right-handed too, so the winding is kept. Normals: recomputed by Blender.
    out = bpy.data.objects.new(name or (obj.name + "_W"), me)
    (collection or bpy.context.scene.collection).objects.link(out)
    for i, slot in enumerate(obj.material_slots):
        if i < len(out.material_slots):
            out.material_slots[i].material = slot.material
    for k in obj.keys():                      # team tags (e.g. s2v1_part = drum | band | band_lip | gold_ring | bulb | star ...)
        if not k.startswith("_"):
            out[k] = obj[k]
    out["s2v1_source"] = obj.name
    return out


def parts(ctx, part):
    """World objects (bent copies) whose s2v1_part tag == part (materials / lighting use this, never names)."""
    return [o for o in ctx["world_objects"] if o.get("s2v1_part") == part]


def _q_rotate(q, v):
    """Rotate vector v by Unity quaternion q = (x, y, z, w) (Hamilton product, coordinate-system independent algebra)."""
    x, y, z, w = q
    qv = np.array([x, y, z]); v = np.asarray(v, dtype=np.float64)
    t = 2.0 * np.cross(qv, v)
    return v + w * t + np.cross(qv, t)


def make_camera(cam_json, name=None):
    """Blender camera identical to a Unity camera (pose, vertical FOV, aspect)."""
    name = name or ("CAM_" + cam_json["name"])
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.sensor_fit = "VERTICAL"
    cd.angle_y = math.radians(cam_json["vfov"])
    cd.clip_start, cd.clip_end = 0.05, 400.0
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if ob.name not in bpy.context.scene.collection.all_objects:
        bpy.context.scene.collection.objects.link(ob)
    f_u = _q_rotate(cam_json["rot"], (0, 0, 1)); up_u = _q_rotate(cam_json["rot"], (0, 1, 0))
    f_b = Vector(u2b(f_u)).normalized(); up_b = Vector(u2b(up_u)).normalized()
    z = -f_b; x = up_b.cross(z).normalized(); y = z.cross(x).normalized()
    m = Matrix((x, y, z)).transposed()
    ob.matrix_world = Matrix.Translation(Vector(u2b(cam_json["pos"]))) @ m.to_4x4()
    ob["bwk_w"], ob["bwk_h"] = cam_json["w"], cam_json["h"]
    return ob


def cameras():
    return {c["name"]: c for c in layout()["cameras"]}


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def build_context(save=True):
    """Import the Unity S2 context OBJ (Unity world) -> Blender world, one collection per category (CTX_<category>), cache as
    Tools/Blender/work/s2v1/context.blend. Old tunnel parts land in CTX_old_tunnel_* (hide them to see v1)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = EXPORT + "/s2_context_unity_world.obj"
    bpy.ops.wm.obj_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    # obj_import with forward -Z / up Y maps file (x, y, z) -> Blender (x, -z, y); we need (x, z, y): mirror Y
    mirror = Matrix.Scale(-1.0, 4, (0, 1, 0))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in objs:
        o.data.transform(mirror @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        # MEASURED 21:01 (s2v1_context_check.py): without this flip 0 % of the drum's faces pointed into the tunnel (the drum shader
        # culls back faces in Unity, so its faces must point inward) -> flip the polygon winding; the imported per-vertex normals were
        # already mirrored correctly by data.transform, so winding and normals agree afterwards
        o.data.flip_normals()
        o.data.update()
        cat = o.name.split("__")[0]
        c = coll("CTX_" + cat)
        for uc in list(o.users_collection):
            uc.objects.unlink(o)
        c.objects.link(o)
    for name, cj in cameras().items():
        make_camera(cj)
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1280, 720
    if save:
        os.makedirs(WORK, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=WORK + "/context.blend")
    return len(objs)


def render_camera(cam_name, out_path, scale=1.0):
    sc = bpy.context.scene
    ob = bpy.data.objects["CAM_" + cam_name]
    sc.camera = ob
    sc.render.resolution_x = int(ob["bwk_w"] * scale)
    sc.render.resolution_y = int(ob["bwk_h"] * scale)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    return out_path
