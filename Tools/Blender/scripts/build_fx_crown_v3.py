"""Bubble Wash Kingdom - MASTER milk splash crowns v3 (water/FX owner, Screen ALL pass 4, owner 21:33 sheet 18).

Reference (private, never in tracked files): the front section frames f_04.50s / f_06.75s / f_08.25s / f_11.25s show two
big OPAQUE MILKY-WHITE crowns at the bottom of the frame: a thick curved milk band lying on the water in a V that opens
toward the camera from the mascot's feet, breaking into rounded fingers that lean outward and end in round bead bulbs,
with separate round droplets; the rear frames (f_01.25-3.25 s) show the same milk rising beside the feet. Asset sheet 18:
"broad curved smooth white splash rim with rounded branching tips and separated droplets; not flat lace sheets".

One master pair for every camera (gameplay rear rig + front comparison cameras): authored in Unity RUNNER-LOCAL metres
(x = travel-right, y = up from the water, z = forward), converted here to the Blender export frame (Unity (x, y, z) =
Blender (-x, -z, y) with bwk_common.export_fbx: axis_forward -Z, axis_up Y) -> SM_FX_CrownV3_L / _R (placed in Unity with no
offset / yaw / scale). Built from metaballs (liquid blending: band capsules -> finger capsule chains -> bead balls), then
decimated (mobile: ~7k tris per side, always near the camera, no LOD needed).

Previews (no reference pixels): Docs/AssetPreviews/FX_CrownV3_front.png (R4 front comparison camera) and _rear.png (R2 rear).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_crown_v3.py fx_crown_v3     (BWK_FX_QUICK=1: no export)
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
RES = 0.0095           # polygonizer cell (m): fingers ~4 cm across get ~5 cells
MAX_TRIS = 8000


def U(x, y, z):
    """Unity runner-local -> Blender export frame."""
    return Vector((-x, -z, y))


def uvec(v):
    return U(v[0], v[1], v[2])


def norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u * u * u * p0[i] + 3 * u * u * t * p1[i] + 3 * u * t * t * p2[i] + t * t * t * p3[i] for i in range(3))


class Elems:
    def __init__(self):
        self.items = []   # (type, centre_unity, radius_vis, half_len, dir_unity)

    def ball(self, c, r):
        self.items.append(("BALL", c, r, 0.0, None))

    def capsule(self, a, b, r):
        c = tuple((a[i] + b[i]) * 0.5 for i in range(3))
        d = tuple(b[i] - a[i] for i in range(3))
        hl = 0.5 * math.sqrt(sum(x * x for x in d))
        self.items.append(("CAPSULE", c, r, hl, norm(d)))


def crown_arm(E, rng, s, P, n_f, h0, h1, L0, L1, rad0, rad1, band_r, back_lean=0.0):
    """One crown arm: a low curved milk band on the water along the Bezier P (Unity runner-local), its rim breaking into
    n_f rounded fingers that lean outward (away from the lane centre) and end in bead bulbs; forks + droplets.
    h / L / rad interpolate from the start (0, at the foot) to the end (1) of the arm."""
    p0, p1, p2, p3 = P
    n_band = 56
    roots = sorted(min(0.97, max(0.03, (k + 0.5) / n_f + rng.uniform(-0.025, 0.025))) for k in range(n_f))

    def tangent(t):
        a = bez(p0, p1, p2, p3, max(0.0, t - 0.01))
        b = bez(p0, p1, p2, p3, min(1.0, t + 0.01))
        return norm((b[0] - a[0], 0.0, b[2] - a[2]))

    def outward(t):
        d = tangent(t)
        o = (d[2], 0.0, -d[0])                    # perpendicular in the water plane ...
        if o[0] * s < 0:
            o = (-o[0], 0.0, -o[2])               # ... pointing away from the lane centre line
        return norm(add(o, (0.0, 0.0, -1.0), back_lean))

    def band_h(t):
        base = h0 + (h1 - h0) * t
        bump = max(math.exp(-((t - r) / 0.03) ** 2) for r in roots)   # the band rises into each finger root (U gaps)
        return base * (0.55 + 0.45 * bump)

    for i in range(n_band):
        t = i / (n_band - 1)
        p = bez(p0, p1, p2, p3, t)
        h = band_h(t)
        o = outward(t)
        top = add(add(p, (0, h, 0)), o, 0.42 * h)
        E.capsule(add(p, (0, 0.012, 0)), top, band_r)
        E.ball(top, band_r * 1.2)                              # rounded rim along the top edge
    for k, r0 in enumerate(roots):
        p = bez(p0, p1, p2, p3, r0)
        h = band_h(r0)
        o = outward(r0)
        d = tangent(r0)
        a = add(add(p, (0, h, 0)), o, 0.42 * h)
        L = (L0 + (L1 - L0) * r0) * rng.uniform(0.8, 1.2)
        rad = rad0 + (rad1 - rad0) * r0
        fan = rng.uniform(-1.0, 1.0)            # p2: parallel posts read as a fence -> fingers fan out along the arm
        for seg in range(3):
            dirv = norm(add(add((0, 1.0, 0), o, 1.25 - seg * 0.4), d, fan * (0.9 - 0.2 * seg)))
            nb = add(a, dirv, L / 3.0)
            E.capsule(a, nb, rad * (1.45 - 0.3 * seg))
            a = nb
            if seg == 1 and rng.random() < 0.38:              # fork: a short side finger with its own bead
                fd = norm(add(add((0, 0.8, 0), o, 0.9), d, rng.choice((-1, 1)) * 0.9))
                fb = add(a, fd, L * 0.42)
                E.capsule(a, fb, rad * 0.85)
                E.ball(add(fb, fd, 0.012), rad * 1.5)
        tipd = norm(add((0, 1.0, 0), o, 0.4))
        E.ball(add(a, tipd, 0.016), rad * 1.65)               # round bead bulb on the finger tip
        if rng.random() < 0.55:                               # separated droplet beyond the tip
            E.ball(add(a, tipd, 0.085 + rng.uniform(0.0, 0.05)), rad * rng.uniform(0.8, 1.2))
    for _ in range(max(3, n_f * 3 // 4)):                     # loose round droplets thrown outward beside the arm
        t = rng.uniform(0.05, 0.95)
        p = bez(p0, p1, p2, p3, t)
        c = add(add(p, (0, band_h(t) + rng.uniform(0.12, 0.3), 0)), outward(t), rng.uniform(0.08, 0.26))
        E.ball(c, rng.uniform(0.018, 0.032))


def crown_side(s, seed):
    """Master crown of one side (s = +1 travel-right, -1 travel-left), runner-local metres."""
    rng = random.Random(seed)
    E = Elems()
    # BOW arm (front frames f_04.50-14.25 s): from beside the foot outward-forward, the V opening toward the front camera
    # and reaching the bottom corners; low lacy band (p1: a solid wall crossed 2-3 scan lines vs the reference 7-9)
    crown_arm(E, rng, s, ((s * 0.17, 0.0, -0.06), (s * 0.40, 0.0, 0.30), (s * 0.78, 0.0, 0.86), (s * 1.18, 0.0, 1.52)),
              9, 0.13, 0.085, 0.24, 0.15, 0.027, 0.023, 0.025)
    # WAKE arm (rear frames f_01.25-3.25 s, p1: R2 milk coverage 4 % vs reference 10 % - the bow arm hides behind the
    # body): from beside the sole backward-outward toward the gameplay camera, tall fingers at the foot, lower behind
    # (p3 hero_mouth 9:16: fingers leaning back toward the camera read as antler combs + the arm crowded the chevron tip ->
    #  no back lean (fingers rise up / outward like the reference), arm 0.8 -> 0.62 m long)
    crown_arm(E, rng, s, ((s * 0.24, 0.0, 0.02), (s * 0.34, 0.0, -0.18), (s * 0.45, 0.0, -0.38), (s * 0.56, 0.0, -0.62)),
              6, 0.17, 0.07, 0.30, 0.15, 0.027, 0.022, 0.024, back_lean=0.0)
    # riser beside the foot: a milk sheet climbing beside the sole, opening outward, 4 thick fingers up to the hands
    n_r = 14
    rim = []
    for j in range(n_r):
        u = j / (n_r - 1)
        ang = -0.9 + 1.5 * u
        cx, cz = s * (0.30 + 0.07 * math.cos(ang)), -0.02 + 0.17 * math.sin(ang)
        h = 0.15 + 0.10 * math.sin(math.pi * u)
        o = norm((s * math.cos(ang), 0.0, 0.45 * math.sin(ang)))
        top = add((cx, h, cz), o, 0.55 * h)
        E.capsule((cx, 0.015, cz), top, 0.023)
        E.ball(top, 0.029)
        rim.append((top, o))
    for j in (1, 4, 8, 11):
        top, o = rim[j]
        L = rng.uniform(0.2, 0.3)
        a = top
        for seg in range(3):
            dv = norm(add((0, 1.0, 0), o, 0.85 - 0.25 * seg))
            nb = add(a, dv, L / 3.0)
            E.capsule(a, nb, 0.025 - 0.002 * seg)
            a = nb
        E.ball(add(a, dv, 0.016), 0.04)
        if rng.random() < 0.6:
            E.ball(add(a, dv, 0.09 + rng.uniform(0, 0.05)), rng.uniform(0.018, 0.03))
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
    if raw > MAX_TRIS:
        C.select_only([obj])
        mod = obj.modifiers.new("dec", 'DECIMATE')
        mod.ratio = MAX_TRIS / raw
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


def yaw_pitch(fwd, yaw_deg, pitch_up_deg):
    """Unity (left-handed) yaw about +Y (positive = turn right) then pitch up."""
    y = math.radians(yaw_deg)
    x, z = fwd[0] * math.cos(y) + fwd[2] * math.sin(y), -fwd[0] * math.sin(y) + fwd[2] * math.cos(y)
    hor = math.sqrt(x * x + z * z)
    el = math.atan2(fwd[1], hor) + math.radians(pitch_up_deg)
    return (x / hor * math.cos(el), math.sin(el), z / hor * math.cos(el))


def unity_euler_fwd(ex, ey):
    """Forward of a Unity euler (x pitch down +, y yaw right +), roll ignored."""
    p, y = math.radians(ex), math.radians(ey)
    return (math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p))


def main():
    C.reset_scene()
    C.setup_preview_scene("#3A3488", 0.55)
    milk = C.material("M_FX_Milk_v3", "#EEF8FB", roughness=0.18, coat=0.4)
    bsdf = milk.node_tree.nodes.get("Principled BSDF")
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.3
        bsdf.inputs["Subsurface Radius"].default_value = C.hex_rgba("#9CC8F0")[:3]
        bsdf.inputs["Subsurface Scale"].default_value = 0.02
    objs = []
    for side, s, seed in (("L", -1.0, 31), ("R", 1.0, 57)):
        name = "SM_FX_CrownV3_" + side
        E = crown_side(s, seed)
        obj, raw = build_mesh(name, E, milk)
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
        zs = [v.co.z for v in obj.data.vertices]
        print("CHECK %s %d tris (raw %d), %d elems, unity x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
            name, C.tri_count(obj), raw, len(E.items), -max(xs), -min(xs), min(zs), max(zs), -max(ys), -min(ys)))
        if not QUICK:
            C.export_fbx([obj], C.model_path(GROUP, name))
        objs.append(obj)
    # preview stand-ins (not exported): mascot body, feet, water
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
    C._light("Fill", 'AREA', 90, "#8FB0FF", t + Vector((0.0, 0.0, -0.3)) + Vector((2.0, 0.0, 0.6)), t, 3.0)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    # R4-like front comparison camera (CaptureTools: 2.6 ahead, 1.3 up, 0.3 right, aim mascot +0.6, then yaw 9.1 / pitch 2.9 up)
    pos = (0.3, 1.3, 2.6)
    f0 = norm((0 - pos[0], 0.6 - pos[1], 0 - pos[2]))
    front = look_cam("CamFront", pos, yaw_pitch(f0, 9.1, 2.9), 52.0)
    # R2 rear S2 camera (measured runner-local: pos (0.376, 0.652, -2.844), euler (358.74, 351.13, 354.61))
    rear = look_cam("CamRear", (0.376, 0.652, -2.844), unity_euler_fwd(-1.26, -8.87), 58.0)
    for cam, tag in ((front, "front"), (rear, "rear")):
        scene.camera = cam
        scene.render.filepath = C.preview_path("FX_CrownV3_" + tag)
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", scene.render.filepath)
    print("DONE crown v3")


main()
