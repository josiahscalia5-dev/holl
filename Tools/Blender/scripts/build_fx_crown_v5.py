"""Bubble Wash Kingdom - MASTER milk splash crowns v5 (water/FX owner, Screen S2 pass 9, owner 10:48 / 12:08 briefs).

Owner: "natural outward-fanning milky splash crowns with separate droplets" / "rebuild cheap assets properly"; library crop 18
(Milky_splash_crown, private): SMOOTH cartoon milk - a connected curved band hugging the outer side of each foot, from which
smooth tapering fingers fan OUTWARD (sideways, up, and low along the water toward the camera), each ending in a round BULB
tip, a few forking into a short Y near the end, plus separate round droplets flung on along the arcs. Our v4 (p3 12:15) read
as a lumpy popcorn fan: thick posts with beads along every strand, a 26-ball droplet cloud and a 10 % decimation of the
metaball surface. v5 = same runner-local frame / origin / names pattern as v4 (SM_FX_CrownV5_L / _R, SceneBuilder.WaterFX
prefers V5 > V4 > V3), but:
  - fingers: 7 capsules, smooth taper (1 -> .5 of the root radius), gravity arc, NO mid-strand beads, bulb tip 1.8-2.1 x;
  - fan layout from the reference: outer side fingers (az 40-175, el 18-60), tall risers beside the body (rear camera: up to
    arm height), long low skimming arms toward the camera, a small forward bow for the front cameras;
  - only ~8-10 loose droplets per side, all varied in size; polygonised finer (7.5 mm) with fewer elements, so the decimation
    to MAX_TRIS keeps ~25-30 % of the surface instead of 10 %.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_crown_v5.py fx_crown_v5     (BWK_FX_QUICK=1: no export)
Previews (no reference pixels): Docs/AssetPreviews/FX_CrownV5_rear.png (R2 rear comparison camera) + _front.png.
Revert: delete Assets/BubbleWashKingdom/Art/Models/FX/SM_FX_CrownV5_*.fbx (V4 takes over again).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bwk_common as C  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

GROUP = "FX"
QUICK = os.environ.get("BWK_FX_QUICK", "") == "1"
K_VIS = 0.575          # visible radius / metaball radius (isolated element, stiffness 2, threshold 0.6)
RES = 0.009            # polygonizer cell (m): v5b fingers 5-8 cm across get 6-9 cells, bulbs 8-9 cm get 9-10
MAX_TRIS = 12500
GRAV = 0.11            # downward bend per segment (x u)


def U(x, y, z):
    return Vector((-x, -z, y))


def uvec(v):
    return U(v[0], v[1], v[2])


def norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def rot_y(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) + v[2] * math.sin(a), v[1], -v[0] * math.sin(a) + v[2] * math.cos(a))


def dir_from(az_deg, el_deg):
    """Unit direction: azimuth in the water plane (0 = +z forward, 90 = +x right), elevation above the water."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    return (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))


class Elems:
    def __init__(self):
        self.items = []

    def ball(self, c, r):
        if c[1] < -0.01:
            c = (c[0], -0.01, c[2])
        self.items.append(("BALL", c, r, 0.0, None))

    def capsule(self, a, b, r):
        c = tuple((a[i] + b[i]) * 0.5 for i in range(3))
        d = tuple(b[i] - a[i] for i in range(3))
        hl = 0.5 * math.sqrt(sum(x * x for x in d))
        if hl < 1e-4:
            self.ball(c, r)
            return
        self.items.append(("CAPSULE", c, r, hl, norm(d)))


def finger(E, rng, p, d, L, r, fork=0.0, drops=True, grav=GRAV, curl=0.0, taper=0.3, path=None):
    """One smooth milk finger from p along d: 7 gently tapering capsules (v5b: 1 -> .7, the reference's fat cartoon fingers)
    on a gravity arc with a gentle sideways sweep, a round bulb on the tip, an optional short stubby side finger near the
    end (probability fork), a few separate droplets flung on along the arc. curl > 0 lifts the far end. path (list) receives
    (point, radius) per segment end so neighbouring fingers can be webbed together."""
    n = 7
    seg = L / n
    side_w = rng.uniform(-0.28, 0.28)
    fork_at = rng.randint(3, 5) if rng.random() < fork else -1
    a = p
    rr = r
    for k in range(n):
        u = (k + 1) / n
        rr = r * (1.0 - taper * u)
        d = norm(add(add(add(d, (0.0, -1.0, 0.0), grav * u), (0.0, 1.0, 0.0), curl * u * u),
                     rot_y((d[0], 0.0, d[2]), 90.0), side_w * 0.2))
        b = add(a, d, seg)
        if b[1] < 0.006:
            b = (b[0], 0.006, b[2])
        E.capsule(a, b, rr)
        if path is not None:
            path.append((b, rr))
        if k == fork_at:
            sgn = rng.choice((-1.0, 1.0))
            fd = norm(add(rot_y(d, sgn * rng.uniform(30.0, 55.0)), (0.0, 1.0, 0.0), rng.uniform(0.05, 0.35)))
            finger(E, rng, b, fd, L * rng.uniform(0.2, 0.32), rr * 0.9, 0.0, False, grav, 0.0, 0.15)
        a = b
    bulb = rr * rng.uniform(1.4, 1.65)
    E.ball(add(a, d, rr * 0.5), bulb)                       # round bulb tip (crop 18)
    if drops:
        q, dd = add(a, d, rr * 0.5), d
        gap = bulb * rng.uniform(2.4, 3.4)
        for j in range(rng.choice((0, 0, 1, 1, 2))):
            dd = norm(add(dd, (0.0, -1.0, 0.0), 0.2))
            q = add(q, dd, gap * (1.0 + 0.5 * j))
            if q[1] < 0.015:
                break
            E.ball(q, bulb * rng.uniform(0.5, 0.8) * (1.0 - 0.2 * j))


def web(E, pa, pb, upto=3):
    """Milk webbing between two neighbouring fingers' first segments (crop 18: the fingers grow out of one connected sheet,
    scalloped between them): rows of overlapping balls bridging the two paths, dipping between the fingers."""
    for k in range(min(upto, len(pa), len(pb))):
        (a, ra), (b, rb) = pa[k], pb[k]
        gapl = math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))
        rw = 0.85 * min(ra, rb) * (1.0 - 0.18 * k)
        m = max(1, int(gapl / (rw * 1.1)))
        for t in range(1, m):
            f = t / m
            sag = math.sin(math.pi * f) * 0.35 * rw * (k + 1)       # scalloped edge: the web dips between the fingers
            c = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f - sag, a[2] + (b[2] - a[2]) * f)
            E.ball(c, rw)


def base_band(E, rng, s, cx, cz, rad, a0, a1, h0, h1, n, r):
    """Connected curved milk band hugging the outer side of a foot (water -> leaning rounded lip). Returns rim points."""
    rim = []
    for j in range(n):
        u = j / (n - 1)
        ang = a0 + (a1 - a0) * u
        o = dir_from(s * ang, 0.0)
        bx, bz = cx + o[0] * rad, cz + o[2] * rad
        h = h0 + (h1 - h0) * math.sin(math.pi * u) + rng.uniform(-0.01, 0.01)
        top = add((bx, h, bz), o, 0.4 * h)
        E.capsule((bx, 0.012, bz), top, r)
        E.ball(top, r * 1.12)
        rim.append((top, o, ang))
    return rim


def crown_side(s, seed, big):
    rng = random.Random(seed)
    E = Elems()
    k = 1.0 if big else 0.82
    fx, fz = s * 0.22, 0.10                                  # foot centre (sole pads face the rear camera)
    # v5c (Unity p4 12:36: v5b read as bundles of white sticks converging on the feet, vs crop 18 / f_03.00s: broad milk SHEETS
    # facing the rear camera with scalloped, bulb-tipped edges): the main spray is ONE webbed fan standing beside the foot in
    # the plane facing the camera (azimuth ~sideways, elevation spread 8-80 deg), its fingers joined by webbing over the first
    # 4 of 7 segments (a sheet that breaks into fat bulb-tipped fingers), on a thick connected band round the outer side
    rim = base_band(E, rng, s, fx, fz, 0.17, 18.0, 172.0, 0.06, 0.2 * k, 16, 0.038)

    def rim_at(u):
        return rim[max(0, min(len(rim) - 1, int(round(u * (len(rim) - 1)))))]

    n_main = 8 if big else 6
    paths = []
    for i in range(n_main):
        f = i / (n_main - 1)
        el = 8.0 + 72.0 * f + rng.uniform(-4.0, 4.0)
        top, o, ang = rim_at(0.42 + 0.3 * f + rng.uniform(-0.04, 0.04))
        az = s * rng.uniform(80.0, 112.0)
        L = rng.uniform(0.34, 0.52) * k * (1.1 if 25.0 < el < 65.0 else 0.92)
        pth = [(top, 0.04)]
        finger(E, rng, top, dir_from(az, el), L, rng.uniform(0.032, 0.04), fork=0.35, path=pth,
               grav=GRAV * (1.3 if el < 30.0 else 1.0))
        paths.append(pth)
    for i in range(len(paths) - 1):
        if rng.random() < 0.15:
            web(E, paths[i], paths[i + 1], 2)                 # an occasional shorter web = a ragged gap in the sheet
        else:
            web(E, paths[i], paths[i + 1], 4)
    # long low arms skimming the water outward + back toward the rear camera, flicking up at the tip (crop 18 lower arms;
    # the reference's right spray reaches the lower right of the frame), webbed to the lowest fan finger
    n_w = 3 if big else 2
    wpaths = []
    for j in range(n_w):
        top, o, ang = rim_at(rng.uniform(0.7, 1.0))
        az = s * rng.uniform(118.0, 150.0)
        pth = [(top, 0.036)]
        finger(E, rng, top, dir_from(az, rng.uniform(5.0, 14.0)), rng.uniform(0.65, 0.95) * k, rng.uniform(0.03, 0.036),
               fork=0.6, grav=0.05, curl=0.26, taper=0.25, path=pth)
        wpaths.append(pth)
    web(E, paths[0], wpaths[0], 3)
    # small forward bow (front comparison cameras): fingers fanning forward-outward from the toes
    n_b = 3 if big else 2
    for j in range(n_b):
        top, o, ang = rim_at(rng.uniform(0.0, 0.25))
        finger(E, rng, top, dir_from(s * rng.uniform(22.0, 62.0), rng.uniform(16.0, 42.0)), rng.uniform(0.24, 0.38) * k,
               rng.uniform(0.028, 0.034), fork=0.3)
    # a few loose rounded droplets of varied size around the spray (never over the lane centre)
    for _ in range(10 if big else 7):
        az = s * rng.uniform(40.0, 160.0)
        dist = rng.uniform(0.4, 0.95) * k
        o = dir_from(az, 0.0)
        c = (fx + o[0] * dist, rng.uniform(0.1, 0.6) * k, fz + o[2] * dist)
        if abs(c[0]) < 0.3:
            continue
        E.ball(c, rng.uniform(0.014, 0.034))
    return E


def build_mesh(name, E, mat):
    mb = bpy.data.metaballs.new("MB_" + name)
    mb.resolution = RES
    mb.render_resolution = RES
    mb.threshold = 0.6
    ob = bpy.data.objects.new("MB_" + name, mb)
    bpy.context.scene.collection.objects.link(ob)
    for kind, c, r, hl, d in E.items:
        e = mb.elements.new(type=kind)
        e.co = uvec(c)
        e.radius = r / K_VIS
        e.stiffness = 2.0
        if kind == "CAPSULE":
            e.size_x = max(hl, 1e-4)
            e.rotation = Vector((1.0, 0.0, 0.0)).rotation_difference(uvec(d).normalized())
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    me.name = name
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    raw = C.tri_count(obj)
    C.select_only([obj])
    # merge the polygoniser's sliver vertices first (cleaner collapse), then decimate to the mobile budget
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=RES * 0.3)
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception as ex:  # pragma: no cover
        print("merge skipped", ex)
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
    cur = C.tri_count(obj)
    if cur > MAX_TRIS:
        mod = obj.modifiers.new("dec", 'DECIMATE')
        mod.ratio = MAX_TRIS / cur
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(obj, [mat])
    return obj, raw


def look_cam(name, pos_u, fwd_u, vfov_deg):
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(vfov_deg)
    co = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = uvec(pos_u)
    co.rotation_euler = uvec(fwd_u).to_track_quat('-Z', 'Y').to_euler()
    return co


def unity_euler_fwd(ex, ey):
    p, y = math.radians(ex), math.radians(ey)
    return (math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p))


def yaw_pitch(fwd, yaw_deg, pitch_up_deg):
    y = math.radians(yaw_deg)
    x, z = fwd[0] * math.cos(y) + fwd[2] * math.sin(y), -fwd[0] * math.sin(y) + fwd[2] * math.cos(y)
    hor = math.sqrt(x * x + z * z)
    el = math.atan2(fwd[1], hor) + math.radians(pitch_up_deg)
    return (x / hor * math.cos(el), math.sin(el), z / hor * math.cos(el))


def main():
    C.reset_scene()
    C.setup_preview_scene("#3A3488", 0.55)
    milk = C.material("M_FX_Milk_v3", "#EEF8FB", roughness=0.18, coat=0.4)
    bsdf = milk.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.3
        bsdf.inputs["Subsurface Radius"].default_value = C.hex_rgba("#9CC8F0")[:3]
        bsdf.inputs["Subsurface Scale"].default_value = 0.02
    for side, s, seed, big in (("L", -1.0, 5813, False), ("R", 1.0, 7349, True)):
        name = "SM_FX_CrownV5_" + side
        E = crown_side(s, seed, big)
        obj, raw = build_mesh(name, E, milk)
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
        zs = [v.co.z for v in obj.data.vertices]
        print("CHECK %s %d tris (raw %d), %d elems, unity x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
            name, C.tri_count(obj), raw, len(E.items), -max(xs), -min(xs), min(zs), max(zs), -max(ys), -min(ys)))
        if not QUICK:
            C.export_fbx([obj], C.model_path(GROUP, name))
    pink = C.material("PV_Pink", "#F08AB8", roughness=0.8)
    cream = C.material("PV_Cream", "#FFF4F6", roughness=0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.46, location=U(0, 0.52, 0.02))
    bpy.context.active_object.data.materials.append(pink)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=U(sx * 0.22, 0.10, 0.12))
        o = bpy.context.active_object
        o.scale = (1.0, 0.6, 1.0)
        o.data.materials.append(cream)
    bpy.ops.mesh.primitive_plane_add(size=14, location=U(0, 0, 0))
    bpy.context.active_object.data.materials.append(C.material("PV_Water", "#1C8ECC", roughness=0.1))
    t = U(0, 0.3, 0.4)
    C._light("Key", 'AREA', 320, "#FFF6EE", t + Vector((-1.5, -2.5, 3.0)), t, 2.5)
    C._light("Key2", 'AREA', 260, "#FFF6EE", t + Vector((1.5, 2.5, 3.0)), t, 2.5)
    C._light("Fill", 'AREA', 90, "#8FB0FF", t + Vector((2.0, 0.0, 0.3)), t, 3.0)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    rear = look_cam("CamRear", (0.3, 0.9, -3.0), unity_euler_fwd(5.0, -7.0), 50.0)
    pos = (0.3, 1.3, 2.6)
    f0 = norm((0 - pos[0], 0.6 - pos[1], 0 - pos[2]))
    front = look_cam("CamFront", pos, yaw_pitch(f0, 9.1, 2.9), 52.0)
    for cam, tag in ((rear, "rear"), (front, "front")):
        scene.camera = cam
        scene.render.filepath = C.preview_path("FX_CrownV5_" + tag)
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", scene.render.filepath)
    print("DONE crown v5")


main()
