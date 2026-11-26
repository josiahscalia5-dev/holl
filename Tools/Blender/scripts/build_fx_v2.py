"""Bubble Wash Kingdom - round 6 shot-matched water FX for the 8.25 s reconstruction test (Blender 5.3, headless).

NEW assets only (the level keeps SM_FX_Crown_xx / SM_Foam_A-C):
  SM_FX_Crown_v2_L / _R   the two thick milky crown splashes of reference frame 8.25 s (L / R = screen side in that front
                          shot; L sits at the mascot's right foot). MEASURED, not designed: Tools/fx_splash_trace.py segments
                          the milk in the reference frame, takes the exact distance transform and keeps the medial-axis balls
                          (data/fx_crown_v2_f0825.json: pixel centres + radii). Every ball is back-projected through the
                          reference camera model onto a crown surface (an elliptic wall of liquid standing around the feet,
                          water plane outside it) and becomes a metaball whose radius = measured radius x depth / focal, so the
                          thick round tubes, bulb tips, webbed junctions and drops reproduce the reference silhouette.
                          Axes = runner-local (Blender +X = runner LEFT, +Y = runner BACKWARD, Z up, FBX -> Unity (-x, z, -y));
                          pivot = runner origin (water surface under the body centre): zero offset under the runner for the
                          front shot. Slot M_FX_Milk_v2.
  SM_Foam_v2_Bank / _Mound / _Puffs   foam from many small bubble spheres (build_foam_v2). Slot M_Foam_v2.
Previews (Blender renders only, no reference pixels): Docs/AssetPreviews/FX_Crown_v2_shot0825.png, FX_Foam_v2.png.
Env: BWK_FX_OUT=<dir> also writes silhouette masks there (Captures/agents/waterfx/shot0825), BWK_FX_QUICK=1 no export,
BWK_FX_ONLY=crown|foam builds one group.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_v2.py <log>
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bwk_common as C  # noqa: E402

GROUP = "FX"
QUICK = os.environ.get("BWK_FX_QUICK", "") == "1"
ONLY = os.environ.get("BWK_FX_ONLY", "")
OUT = os.environ.get("BWK_FX_OUT", "")
V2_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fx_crown_v2_f0825.json")

# ------------------------------------------------------------------ reference camera model, frame 8.25 s (1280x720)
SHOT_W, SHOT_H_PX = 1280, 720
SHOT_F = 700.0             # focal length in pixels (h-FOV 84.9 deg, v-FOV 54.4 deg)
SHOT_PITCH = 10.5          # deg down: tunnel vanishing point at y ~230
SHOT_CAM_H = 1.14          # m above the water
SHOT_BODY_PX, SHOT_BODY_DEPTH = (530.0, 415.0), 2.6   # mascot body centre: ~1 m wide body = 270 px
SHOT_FEET_PX = (600.0, 575.0)                         # feet / water contact between the soles
CROWN_WALL_A, CROWN_WALL_B = 0.75, 0.40               # elliptic crown wall around the feet (lateral, depth semi-axes)
MB_K = float(os.environ.get("BWK_FX_MBK", "0.80"))    # ridge balls spaced .45 r -> tube radius ~= measured radius
RES_V2 = 0.0045


class ShotCam:
    """Reference camera model in world space: camera at (0, 0, H) looking along +Y, pitched down."""

    def __init__(self):
        p = math.radians(SHOT_PITCH)
        self.C = Vector((0.0, 0.0, SHOT_CAM_H))
        self.fwd = Vector((0.0, math.cos(p), -math.sin(p)))
        self.right = Vector((1.0, 0.0, 0.0))
        self.up = Vector((0.0, math.sin(p), math.cos(p)))

    def ray(self, u, v):
        """Direction whose component along fwd is 1 (so the ray parameter = axial depth)."""
        return self.fwd + self.right * ((u - SHOT_W * 0.5) / SHOT_F) - self.up * ((v - SHOT_H_PX * 0.5) / SHOT_F)

    def water(self, u, v, z=0.0):
        d = self.ray(u, v)
        t = (self.C.z - z) / -d.z
        return self.C + d * t, t


def shot_frame():
    cam = ShotCam()
    body = cam.C + cam.ray(*SHOT_BODY_PX) * SHOT_BODY_DEPTH
    M = Vector((body.x, body.y, 0.0))
    feet, _ = cam.water(*SHOT_FEET_PX)
    return cam, M, body, feet


def embed_ball(cam, M, F, u, v, r_px):
    """Back-project one measured ball onto the crown surface; returns (point relative to M, radius m, on_wall)."""
    d = cam.ray(u, v)
    Cp = cam.C
    r_m = r_px * 2.2 / SHOT_F
    wall = False
    for _ in range(3):
        zt = 0.55 * r_m
        hit, t, wall = None, None, False
        a2, b2 = CROWN_WALL_A ** 2, CROWN_WALL_B ** 2
        ox, oy = Cp.x - F.x, Cp.y - F.y
        A = d.x * d.x / a2 + d.y * d.y / b2
        B = 2 * (ox * d.x / a2 + oy * d.y / b2)
        Cc = ox * ox / a2 + oy * oy / b2 - 1.0
        disc = B * B - 4 * A * Cc
        if disc > 0:
            t1 = (-B - math.sqrt(disc)) / (2 * A)
            if t1 > 0 and Cp.z + d.z * t1 >= zt:
                hit, t, wall = Cp + d * t1, t1, True
        if hit is None:
            t = (Cp.z - zt) / -d.z
            hit = Cp + d * t
        r_m = r_px * t / SHOT_F
    return hit - M, r_m, wall


def box_uv(obj, scale=1.0):
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > max(abs(n.x), abs(n.y)):
                u, v = co.x, co.y
            elif abs(n.x) > abs(n.y):
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            uv.data[li].uv = (u * scale, v * scale)


def metaballs_to_mesh(name, elems, res, threshold, mat, max_tris):
    """elems: (co, radius, stiffness) tuples -> decimated smooth mesh object."""
    mb = bpy.data.metaballs.new("MB_" + name)
    mb.resolution = res
    mb.render_resolution = res
    mb.threshold = threshold
    ob = bpy.data.objects.new("MB_" + name, mb)
    bpy.context.scene.collection.objects.link(ob)
    for co, rad, stiff in elems:
        e = mb.elements.new(type='BALL')
        e.co = co
        e.radius = rad
        e.stiffness = stiff
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    me.name = name
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    raw = C.tri_count(obj)
    if raw > max_tris:
        C.select_only([obj])
        mod = obj.modifiers.new("dec", 'DECIMATE')
        mod.ratio = max_tris / raw
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(obj, [mat])
    box_uv(obj, 2.0)
    return obj, raw


def crown_v2(cam, M, F, balls, name, mat):
    elems, nwall, zs, rs = [], 0, [], []
    for (u, v, r_px) in balls:
        q, r_m, wall = embed_ball(cam, M, F, u, v, r_px)
        nwall += wall
        zs.append(q.z)
        rs.append(r_m)
        elems.append((q, r_m * 1.75 * MB_K, 2.0))
    print("crown %s: %d balls (%d on the wall), z %.2f..%.2f m, r %.3f..%.3f m" % (
        name, len(balls), nwall, min(zs), max(zs), min(rs), max(rs)))
    return metaballs_to_mesh(name, elems, RES_V2, 0.6, mat, 12000)


# ------------------------------------------------------------------ foam v2: banks of many small bubbles
# Reference 8.00-8.25 s (4K crops in Captures/agents/waterfx/shot0825/ref_foam_sheet_0800_4k.png):
#  right wall bank = cumulus mounds of many small rounded bubbles (17-33 px at 720p, ~0.08-0.2 m), bright white tops,
#  faint blue-lavender shading, irregular bumpy silhouette, 0.3-0.45 m tall; near-water foam on the left = separate
#  flattened domes / pillows (height ~0.6 x width) in small groups. Metaballs with low stiffness keep every bubble
#  readable as its own rounded bump while the contacts fuse smoothly.
def foam_bank_elems(rng, length, depth, height, n, rmin, rmax):
    """Mound of n bubbles: bigger ones low in the core, small ones on the crest and edges, irregular crest line."""
    el = []
    crest = [rng.uniform(0.55, 1.0) for _ in range(7)]
    for i in range(n):
        x = rng.uniform(-0.5, 0.5) * length
        k = (x / length + 0.5) * 6
        j = min(5, int(k))
        hmax = height * (crest[j] + (crest[j + 1] - crest[j]) * (k - j))
        hmax *= math.sqrt(max(0.0, 1 - (2 * x / length) ** 2)) ** 0.6       # mound tapers at both ends
        y = rng.gauss(0, 0.28) * depth
        prof = max(0.0, 1 - (2 * y / depth) ** 2)
        zt = hmax * prof
        z = rng.uniform(0.0, 1.0) ** 0.7 * zt
        # radius: large near the core / water line, small on the crest and the edges
        edge = min(1.0, z / max(zt, 1e-3))
        r = rmax - (rmax - rmin) * (0.35 + 0.65 * edge) * rng.uniform(0.6, 1.0)
        el.append((Vector((x, y, max(z, r * 0.3))), r))
    # crest bubbles: small round bumps sitting on the top surface (the bubbly silhouette)
    for i in range(int(n * 0.35)):
        x = rng.uniform(-0.48, 0.48) * length
        k = (x / length + 0.5) * 6
        j = min(5, int(k))
        hmax = height * (crest[j] + (crest[j + 1] - crest[j]) * (k - j)) * math.sqrt(max(0.0, 1 - (2 * x / length) ** 2)) ** 0.6
        y = rng.gauss(0, 0.2) * depth
        r = rng.uniform(rmin, rmin + 0.45 * (rmax - rmin))
        el.append((Vector((x, y, hmax * max(0.0, 1 - (2 * y / depth) ** 2) + r * 0.2)), r))
    return el


def foam_puffs_elems(rng, n):
    """Near-water pillows: flattened domes in a small group (each dome = a squashed cluster of 3-5 balls)."""
    el = []
    for i in range(n):
        cx, cy = rng.uniform(-0.45, 0.45), rng.uniform(-0.25, 0.25)
        w = rng.uniform(0.07, 0.13)
        for k in range(rng.randint(3, 5)):
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(0.0, 0.5) * w
            el.append((Vector((cx + d * math.cos(a), cy + d * math.sin(a) * 0.8, w * 0.12)), w * rng.uniform(0.55, 0.8)))
    return el


def foam_mesh(name, elems, mat, max_tris, squash=1.0):
    scaled = []
    for co, r in elems:
        scaled.append((Vector((co.x, co.y, co.z * squash)), r * 1.75 * 0.92, 1.2))
    obj, raw = metaballs_to_mesh(name, scaled, 0.008, 0.55, mat, max_tris)
    # sit on the water: nothing below z = 0
    for v in obj.data.vertices:
        if v.co.z < 0:
            v.co.z = 0.0
    return obj, raw


def build_foam_v2(mat):
    rng = random.Random(20261126)
    objs = []
    o, raw = foam_mesh("SM_Foam_v2_Bank", foam_bank_elems(rng, 1.6, 0.55, 0.36, 150, 0.035, 0.1), mat, 9000)
    objs.append((o, raw))
    o, raw = foam_mesh("SM_Foam_v2_Mound", foam_bank_elems(rng, 0.8, 0.45, 0.30, 70, 0.03, 0.085), mat, 5000)
    objs.append((o, raw))
    o, raw = foam_mesh("SM_Foam_v2_Puffs", foam_puffs_elems(rng, 6), mat, 4000, squash=1.0)
    for v in o.data.vertices:            # flatten the pillows: height ~0.6 x width
        v.co.z *= 0.62
    objs.append((o, raw))
    return objs


# ------------------------------------------------------------------ previews
def ellipsoid(name, loc, scale, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    o = C.mesh_from_bmesh(name, bm)
    o.location = loc
    o.scale = scale
    for p in o.data.polygons:
        p.use_smooth = True
    C.assign_materials(o, [mat])
    return o


def water_plane(size=6, loc=(0, -1.5, 0)):
    wm = bpy.data.meshes.new("PV_Water")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size)
    bm.to_mesh(wm)
    wo = bpy.data.objects.new("PV_Water", wm)
    bpy.context.scene.collection.objects.link(wo)
    wo.location = loc
    wo.data.materials.append(C.material("PV_Water", "#1A4FA8", roughness=0.12))
    return wo


def shot_camera_object(cam, M):
    cd = bpy.data.cameras.new("ShotCam0825")
    cd.sensor_fit = 'HORIZONTAL'
    cd.angle_x = 2 * math.atan(SHOT_W * 0.5 / SHOT_F)
    co = bpy.data.objects.new("ShotCam0825", cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = cam.C - M
    co.rotation_euler = (math.radians(90 - SHOT_PITCH), 0.0, 0.0)
    bpy.context.scene.camera = co
    return co


def render(path, w, h):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", path)


def mask_pass(objs, path, w, h):
    """Silhouette pass: the given assets only, flat white on black (IoU against the reference mask)."""
    scene = bpy.context.scene
    white = C.material("PV_MaskWhite", "#000000", emission="#FFFFFF", emission_strength=1.0)
    hidden, saved = [], []
    for o in list(scene.objects):
        if o.type == 'MESH' and o not in objs and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    for o in objs:
        saved.append(list(o.data.materials))
        o.data.materials.clear()
        o.data.materials.append(white)
    lights = [o for o in scene.objects if o.type == 'LIGHT' and not o.hide_render]
    for o in lights:
        o.hide_render = True
    bg = scene.world.node_tree.nodes.get("Background")
    old = bg.inputs[1].default_value
    bg.inputs[1].default_value = 0.0
    vt = scene.view_settings.view_transform
    scene.view_settings.view_transform = 'Standard'
    render(path, w, h)
    bg.inputs[1].default_value = old
    scene.view_settings.view_transform = vt
    for o in hidden + lights:
        o.hide_render = False
    for o, mats in zip(objs, saved):
        o.data.materials.clear()
        for m in mats:
            o.data.materials.append(m)


def setup_lights():
    scene = bpy.context.scene
    C.add_studio_lights(target=(0, -0.4, 0.3), scale=1.3)
    sun = bpy.data.lights.new("Sun", 'SUN')
    sun.energy = 2.5
    so = bpy.data.objects.new("Sun", sun)
    scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(35), 0, math.radians(200))


def main_v2():
    C.reset_scene()
    C.setup_preview_scene("#3B2F86", 0.9)
    report = []
    cam, M, body, feet = shot_frame()
    crowns = []
    if ONLY in ("", "crown"):
        milk = C.material("M_FX_Milk_v2", "#EAF7F9", roughness=0.24, coat=0.3)
        data = json.load(open(V2_DATA))
        print("SHOT model: runner origin M world (%.2f, %.2f), body z %.2f, feet rel M (%.2f, %.2f), camera rel M (%.2f, %.2f, %.2f)" % (
            M.x, M.y, body.z, feet.x - M.x, feet.y - M.y, -M.x, -M.y, SHOT_CAM_H))
        for side in ("L", "R"):
            name = "SM_FX_Crown_v2_" + side
            obj, raw = crown_v2(cam, M, feet, data["wings"][side]["balls"], name, milk)
            crowns.append(obj)
            report.append("%-18s %6d tris (raw %6d) dims %s loc-bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
                name, C.tri_count(obj), raw, tuple(round(d, 3) for d in obj.dimensions),
                min(v.co.x for v in obj.data.vertices), max(v.co.x for v in obj.data.vertices),
                min(v.co.y for v in obj.data.vertices), max(v.co.y for v in obj.data.vertices),
                min(v.co.z for v in obj.data.vertices), max(v.co.z for v in obj.data.vertices)))
            if not QUICK:
                C.export_fbx([obj], C.model_path(GROUP, name))
    foams = []
    if ONLY in ("", "foam"):
        foam = C.material("M_Foam_v2", "#F6F8FC", roughness=0.35, coat=0.2)
        for o, raw in build_foam_v2(foam):
            foams.append(o)
            report.append("%-18s %6d tris (raw %6d) dims %s" % (o.name, C.tri_count(o), raw, tuple(round(d, 3) for d in o.dimensions)))
            if not QUICK:
                C.export_fbx([o], C.model_path(GROUP, o.name))
    print("\n".join("CHECK " + r for r in report))
    setup_lights()
    water_plane()
    if crowns:
        pink = C.material("PV_Mascot", "#F07AA0", roughness=0.8)
        cream = C.material("PV_Feet", "#FFF2F6", roughness=0.7)
        stand = [ellipsoid("PV_Body", body - M, (0.48, 0.44, 0.46), pink)]
        for (u, v) in ((560.0, 540.0), (683.0, 498.0)):
            stand.append(ellipsoid("PV_Foot", cam.C + cam.ray(u, v) * 2.15 - M, (0.12, 0.06, 0.12), cream))
        for o in foams:
            o.hide_render = True
        shot_camera_object(cam, M)
        render(C.preview_path("FX_Crown_v2_shot0825"), SHOT_W, SHOT_H_PX)
        if OUT:
            mask_pass(crowns, os.path.join(OUT, "v2_crown_mask.png"), SHOT_W, SHOT_H_PX)
        for o in crowns + stand:
            o.hide_render = True
    if foams:
        # foam sheet: the three assets in a row on the water, seen from a front three-quarter camera at the reference's angle
        xs = (-1.25, 0.25, 1.15)
        for o, x in zip(foams, xs):
            o.hide_render = False
            o.location = (x, 0.0, 0.0)
        C.add_camera((0.0, -3.4, 1.35), (0.0, 0.0, 0.12), lens=42)
        render(C.preview_path("FX_Foam_v2"), 1280, 560)
    print("DONE build_fx_v2")


if __name__ == "__main__":
    main_v2()
