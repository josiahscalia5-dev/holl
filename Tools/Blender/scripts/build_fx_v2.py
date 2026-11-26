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
_E = os.environ.get
SHOT_F = float(_E("BWK_FX_CAM_F", "700.0"))           # focal length in pixels (h-FOV 84.9 deg, v-FOV 54.4 deg)
SHOT_PITCH = float(_E("BWK_FX_CAM_PITCH", "10.5"))    # deg down: tunnel vanishing point at y ~230
SHOT_CAM_H = float(_E("BWK_FX_CAM_H", "1.14"))        # m above the water
SHOT_ROLL = float(_E("BWK_FX_CAM_ROLL", "0.0"))       # deg about the view axis (+ = camera right axis tilts up: scene turns clockwise)
SHOT_BODY_PX = (float(_E("BWK_FX_BODY_U", "530")), float(_E("BWK_FX_BODY_V", "415")))
SHOT_BODY_DEPTH = float(_E("BWK_FX_BODY_DEPTH", "2.6"))  # axial depth of the mascot body centre (~1 m wide body = 270 px)
# (the env-var overrides let the crowns be re-solved through the environment agent's camera.json in one run)
SHOT_FEET_PX = (600.0, 575.0)                         # feet / water contact between the soles
CROWN_WALL_A, CROWN_WALL_B = 0.75, 0.40               # elliptic crown wall around the feet (lateral, depth semi-axes)
MB_K = float(os.environ.get("BWK_FX_MBK", "0.68"))    # measured balls + in-between balls -> IoU .924 vs the reference mask (.80: .870)
RES_V2 = 0.0045


class ShotCam:
    """Reference camera model in world space: camera at (0, 0, H) looking along +Y, pitched down."""

    def __init__(self):
        p = math.radians(SHOT_PITCH)
        self.C = Vector((0.0, 0.0, SHOT_CAM_H))
        self.fwd = Vector((0.0, math.cos(p), -math.sin(p)))
        right = Vector((1.0, 0.0, 0.0))
        up = Vector((0.0, math.sin(p), math.cos(p)))
        q = math.radians(SHOT_ROLL)
        self.right = right * math.cos(q) + up * math.sin(q)
        self.up = up * math.cos(q) - right * math.sin(q)

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


def crown_v2(cam, M, F, balls, name, mat, sigma_px=32.0):
    """Measured balls -> 3D. First-hit depths (wall / water) are smoothed across the screen (Gaussian, sigma_px) so
    neighbouring balls never jump in depth (each ball stays on its own camera ray: the silhouette is unchanged), then
    connected neighbours get in-between balls wherever the 3D spacing exceeds .45 x radius (no beaded tubes)."""
    n = len(balls)
    t0, walls = [], 0
    for (u, v, r_px) in balls:
        q, r_m, wall = embed_ball(cam, M, F, u, v, r_px)
        d = cam.ray(u, v)
        t0.append((q + M - cam.C).dot(cam.fwd) / d.dot(cam.fwd))
        walls += wall
    uv = [(b[0], b[1]) for b in balls]
    t = list(t0)
    for _ in range(2):
        tn = []
        for i in range(n):
            sw = st = 0.0
            for j in range(n):
                dd = (uv[i][0] - uv[j][0]) ** 2 + (uv[i][1] - uv[j][1]) ** 2
                if dd < 9 * sigma_px * sigma_px:
                    w = math.exp(-dd / (2 * sigma_px * sigma_px)) * (0.5 + balls[j][2] / 20.0)
                    sw += w
                    st += w * t[j]
            tn.append(st / sw)
        t = tn
    pts, rads = [], []
    for i, (u, v, r_px) in enumerate(balls):
        d = cam.ray(u, v)
        ti = t[i]
        for _ in range(2):                       # never below the water: clamp to the ray's water hit
            r_m = r_px * ti / SHOT_F
            tw = (cam.C.z - 0.55 * r_m) / -d.z
            ti = min(ti, tw)
        r_m = r_px * ti / SHOT_F
        pts.append(cam.C + d * ti - M)
        rads.append(r_m)
    elems = [(p, r) for p, r in zip(pts, rads)]
    added = 0
    for i in range(n):
        for j in range(i + 1, n):
            ds = math.hypot(uv[i][0] - uv[j][0], uv[i][1] - uv[j][1])
            if ds > 0.75 * (balls[i][2] + balls[j][2]):
                continue                         # not touching on screen
            d3 = (pts[j] - pts[i]).length
            step = 0.45 * min(rads[i], rads[j])
            k = int(d3 / max(step, 1e-4))
            for m in range(1, k):
                f = m / k
                elems.append((pts[i].lerp(pts[j], f), rads[i] + (rads[j] - rads[i]) * f))
                added += 1
    zs = [p.z for p in pts]
    print("crown %s: %d balls (%d first-hit on the wall), +%d in-between, depth smoothing sigma %.0f px, z %.2f..%.2f m, r %.3f..%.3f m" % (
        name, n, walls, added, sigma_px, min(zs), max(zs), min(rads), max(rads)))
    # in-between balls overlap more than the .45 r screen spacing -> slightly smaller field radius keeps tube widths
    return metaballs_to_mesh(name, [(p, r * 1.75 * MB_K, 2.0) for p, r in elems], RES_V2, 0.6, mat, 12000)


# ------------------------------------------------------------------ foam v2: banks of many small bubbles
# Reference 8.00-8.25 s (4K crops in Captures/agents/waterfx/shot0825/ref_foam_sheet_0800_4k.png):
#  right wall bank = cumulus mounds of many small rounded bubbles (17-33 px at 720p, ~0.08-0.2 m), bright white tops,
#  faint blue-lavender shading, irregular bumpy silhouette, 0.3-0.45 m tall; near-water foam on the left = separate
#  flattened domes / pillows (height ~0.6 x width) in small groups. Metaballs with low stiffness keep every bubble
#  readable as its own rounded bump while the contacts fuse smoothly.
def foam_bank_elems(rng, length, depth, height, n_bub, rmin, rmax):
    """Dense mound: a solid core of big overlapping balls + many small bubbles half-sunk into its surface (cauliflower
    crest of distinct rounded bumps, bigger bubbles low, smaller on the crest), irregular crest line."""
    core = []
    nc = max(3, int(length / 0.22))
    for i in range(nc):
        x = (i + 0.5) / nc * length - length * 0.5 + rng.uniform(-0.04, 0.04)
        taper = math.sqrt(max(0.05, 1 - (2 * x / length) ** 2))
        R = height * rng.uniform(0.62, 0.95) * (0.55 + 0.45 * taper)
        core.append((Vector((x, rng.uniform(-0.08, 0.08) * depth, R * 0.35)), R, 1.0))
    el = [(c, r) for c, r, _ in core]
    for i in range(n_bub):
        c, R, _ = core[rng.randrange(len(core))]
        th = rng.uniform(0, 2 * math.pi)
        ph = math.acos(rng.uniform(-0.15, 1.0))          # upper hemisphere + a little below the equator
        dirv = Vector((math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th) * (depth / length + 0.55), math.cos(ph)))
        dirv.normalize()
        up = max(0.0, dirv.z)
        r = rng.uniform(rmin, rmax) * (1.0 - 0.45 * up)    # smaller bubbles on the crest
        pos = c + dirv * (R - 0.15 * r)
        if pos.z < r * 0.25:
            pos.z = r * 0.25
        el.append((pos, r))
    return el


def foam_pillows_elems(rng, n):
    """Near-water foam pillows: flattened domes (height ~0.6 x width), single or 2-3 merged in a row."""
    el = []
    x = -0.45
    for i in range(n):
        w = rng.uniform(0.07, 0.11)                       # dome half-width
        x += w * rng.uniform(1.1, 1.9)
        y = rng.uniform(-0.18, 0.18)
        el.append((Vector((x, y, 0.08 * w)), w))
        if rng.random() < 0.5:                            # a smaller dome fused to it
            el.append((Vector((x + w * 0.9, y + rng.uniform(-0.05, 0.05), 0.05 * w)), w * 0.7))
        x += w
    return el


def foam_mesh(name, elems, mat, max_tris, zscale=1.0, stiff=2.0, k=0.86):
    scaled = [(Vector((co.x, co.y, co.z)), r * 1.75 * k, stiff) for co, r in elems]
    obj, raw = metaballs_to_mesh(name, scaled, 0.007, 0.6, mat, max_tris)
    for v in obj.data.vertices:          # sit on the water: nothing below z = 0; optional flattening (pillows)
        v.co.z = max(0.0, v.co.z) * zscale
    return obj, raw


def bake_foam_colors(obj, elems, seed, max_dist=0.13, n_dirs=26):
    """Round 7 (Unity rendered foam v2 as smooth blobs: BWK/Soft Mode 5 shades crevices ONLY from vertex colour R and the
    v2 meshes had no colour attribute -> AO 1 everywhere). Ray-traced self-AO against the mesh (BVH, cosine-weighted
    hemisphere, max_dist ~ bubble size) -> R = crevice AO, G = per-bubble random tint (nearest bubble centre)."""
    from mathutils.bvhtree import BVHTree
    me = obj.data
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    ga = math.pi * (3.0 - math.sqrt(5.0))
    dirs = []
    for i in range(n_dirs):                       # fibonacci hemisphere (z up), cosine weight applied below
        z = 1.0 - (i + 0.5) / n_dirs
        rr = math.sqrt(max(0.0, 1.0 - z * z))
        dirs.append(Vector((math.cos(ga * i) * rr, math.sin(ga * i) * rr, z)))
    ao = []
    for v in me.vertices:
        n = v.normal.normalized()
        t = n.orthogonal().normalized()
        b = n.cross(t)
        o = v.co + n * 0.003
        occ = 0.0
        wsum = 0.0
        for d in dirs:
            w = d.z
            wd = t * d.x + b * d.y + n * d.z
            hit = tree.ray_cast(o, wd, max_dist)
            if hit[0] is not None:
                occ += w * (1.0 - 0.5 * hit[3] / max_dist)
            elif wd.z < -0.05 and o.z / max(1e-4, -wd.z) < max_dist:   # the water surface under the foam
                occ += w * 0.5
            wsum += w
        ao.append(1.0 - occ / max(wsum, 1e-6))
    centres = [Vector(co) for co, _ in elems]
    prng = random.Random(seed)
    rnd = [prng.random() for _ in centres]
    near = []
    for v in me.vertices:
        best, bi = 1e9, 0
        for i, c in enumerate(centres):
            dd = (v.co - c).length_squared
            if dd < best:
                best, bi = dd, i
        near.append(rnd[bi])
    ca = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            a = max(0.0, min(1.0, 0.18 + 0.82 * ao[vi] ** 1.35))     # visible crevices between the small bubbles
            col = (a, near[vi], 0.0, 1.0)
            try:
                ca.data[li].color_srgb = col
            except AttributeError:
                ca.data[li].color = col
    me.color_attributes.active_color = ca
    lo = sorted(ao)
    print("FOAM-AO %s: %d verts, ao p10 %.2f p50 %.2f p90 %.2f" % (obj.name, len(ao), lo[len(lo) // 10], lo[len(lo) // 2], lo[9 * len(lo) // 10]))


def foam_lod1(obj, elems, seed, ratio=0.3):
    """Mobile LOD1 twin (same pivot / footprint, ~30 % triangles), colours re-baked on the decimated mesh."""
    lod = bpy.data.objects.new(obj.name + "_LOD1", obj.data.copy())
    lod.data.name = obj.name + "_LOD1"
    for a in list(lod.data.color_attributes):
        lod.data.color_attributes.remove(a)
    bpy.context.scene.collection.objects.link(lod)
    C.select_only([lod])
    mod = lod.modifiers.new("dec", 'DECIMATE')
    mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in lod.data.polygons:
        p.use_smooth = True
    bake_foam_colors(lod, elems, seed)
    return lod


def build_foam_v2(mat):
    rng = random.Random(20261126)
    objs = []
    specs = (("SM_Foam_v2_Bank", lambda: foam_bank_elems(rng, 1.6, 0.55, 0.30, 190, 0.035, 0.075), 9000, {}),
             ("SM_Foam_v2_Mound", lambda: foam_bank_elems(rng, 0.8, 0.45, 0.24, 90, 0.03, 0.065), 5000, {}),
             ("SM_Foam_v2_Puffs", lambda: foam_pillows_elems(rng, 4), 3000, {"zscale": 0.62, "k": 0.95}))
    for i, (name, make, tris, kw) in enumerate(specs):
        elems = make()
        o, raw = foam_mesh(name, elems, mat, tris, **kw)
        bake_foam_colors(o, elems, 700 + i)
        objs.append((o, raw, foam_lod1(o, elems, 700 + i)))
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
    co.rotation_mode = 'ZXY'                     # R = Rx(pitch) * Rz(roll): roll about the camera's own view axis first
    co.rotation_euler = (math.radians(90 - SHOT_PITCH), 0.0, math.radians(SHOT_ROLL))
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


def setup_lights(target=(0.0, -0.4, 0.2)):
    """Reference-like soft light: warm key from above the camera (upper left), blue bounce from the water side, cool
    top; dark blue-violet ambient so the milk / foam keep their blue-grey shading (no clipped flat white)."""
    t = Vector(target)
    C._light("Key", 'AREA', 260, "#FFF6EE", t + Vector((-1.6, -2.6, 2.6)), t, 2.2)
    C._light("Fill", 'AREA', 70, "#8FB0FF", t + Vector((1.8, -2.2, 0.35)), t, 2.5)
    C._light("Top", 'AREA', 90, "#E8F0FF", t + Vector((0.4, 0.6, 3.0)), t, 2.0)
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = C.hex_rgba("#3A3488")
    bg.inputs[1].default_value = 0.55


def sss(mat, weight, color):
    """Milky subsurface scattering for the preview material (Unity uses BWK_Soft wrap lighting instead)."""
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = weight
        bsdf.inputs["Subsurface Radius"].default_value = C.hex_rgba(color)[:3]
        bsdf.inputs["Subsurface Scale"].default_value = 0.02


def main_v2():
    C.reset_scene()
    C.setup_preview_scene("#3B2F86", 0.9)
    report = []
    cam, M, body, feet = shot_frame()
    crowns = []
    if ONLY in ("", "crown"):
        milk = C.material("M_FX_Milk_v2", "#E6F5F8", roughness=0.22, coat=0.5)
        sss(milk, 0.25, "#9CC8F0")
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
        foam = C.material("M_Foam_v2", "#F3F5FB", roughness=0.42, coat=0.15)
        sss(foam, 0.2, "#B8C4F0")
        for o, raw, lod in build_foam_v2(foam):
            foams.append(o)
            report.append("%-18s %6d tris (raw %6d) dims %s, LOD1 %d tris" % (o.name, C.tri_count(o), raw, tuple(round(d, 3) for d in o.dimensions), C.tri_count(lod)))
            if not QUICK:
                C.export_fbx([o], C.model_path(GROUP, o.name))
                C.export_fbx([lod], C.model_path(GROUP, lod.name))
            lod.hide_render = True
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
        xs = (-1.2, 0.35, 1.15)
        for o, x in zip(foams, xs):
            o.hide_render = False
            o.location = (x, 0.0, 0.0)
        C.add_camera((0.0, -3.4, 1.35), (0.0, 0.0, 0.12), lens=42)
        render(C.preview_path("FX_Foam_v2"), 1280, 560)
    print("DONE build_fx_v2")


if __name__ == "__main__":
    main_v2()
