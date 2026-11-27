"""Bubble Wash Kingdom - MASTER milk splash crowns v4 (water/FX owner, Screen S2 pass 7, owner 2026-11-27 items 04 + s13).

Owner: "the latest splashes still look like rigid clusters of white fingers" (26480 sheets: rigid white comb / picket fence
beside the mascot). Reference (private, never in tracked files) f_03.00s at the washing-machine door: milky spray FANNING
OUTWARD from both sides of the seated mascot - a connected curved milk base hugging the outer side of each foot, from which
THIN curved liquid strands arc outward + up and fall back under gravity, BRANCH into side fingers, carry beads along their
length (Plateau-Rayleigh pinching), end in round beads and throw SEPARATE droplets of varied size; the right spray is taller
and wider (up-right to ~1 m beside the foot) with a low arm sweeping outward along the water toward the camera; the left
one is smaller. Front frames (f_04.50-14.25 s) keep a low V bow opening forward from the feet (same strand language).

v3 (build_fx_crown_v3.py) = thick capsule posts in rows -> the comb. v4 = stochastic branching ballistic strands:
  base sheet (capsules water -> rim, rim balls) -> 2-level branching strands (6 capsules each, gravity-bent, lateral wobble,
  forks 25-45 deg, beads) -> tip beads -> detached droplets continuing the arc -> loose droplet cloud.
Authored in Unity RUNNER-LOCAL metres (x right, y up from the water, z forward), converted to the Blender export frame
(Unity (x, y, z) = Blender (-x, -z, y), bwk_common.export_fbx axis_forward -Z / axis_up Y) -> SM_FX_CrownV4_L / _R, placed in
Unity with no offset / yaw / scale (SceneBuilder.WaterFX BuildCrownsV2 prefers V4 > V3). Metaballs (liquid blending at the
roots and forks), polygonised at 6 mm, decimated to MAX_TRIS (mobile: ~9k tris per side, one pair, always near the camera).

Previews (no reference pixels): Docs/AssetPreviews/FX_CrownV4_rear.png (R2 rear comparison camera) + _front.png (R4 front).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_crown_v4.py fx_crown_v4     (BWK_FX_QUICK=1: no export)
Revert: delete Assets/BubbleWashKingdom/Art/Models/FX/SM_FX_CrownV4_*.fbx (V3 takes over again).
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
RES = 0.0085           # polygonizer cell (m): v4c strands 5-7 cm across get 6-8 cells
MAX_TRIS = 12000
GRAV = 0.13            # downward bend per segment (x u): v4a 0.30 fell back too soon; p1 (0.17) read too low


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
    """Rotate about the up axis (Unity left-handed: positive = toward +x from +z)."""
    a = math.radians(deg)
    return (v[0] * math.cos(a) + v[2] * math.sin(a), v[1], -v[0] * math.sin(a) + v[2] * math.cos(a))


def dir_from(az_deg, el_deg):
    """Unit direction: azimuth in the water plane (0 = +z forward, 90 = +x right), elevation above the water."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    return (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))


class Elems:
    def __init__(self):
        self.items = []   # (type, centre_unity, radius_vis, half_len, dir_unity)

    def ball(self, c, r):
        if c[1] < -0.01:
            c = (c[0], -0.01, c[2])          # never below the water plane
        self.items.append(("BALL", c, r, 0.0, None))

    def capsule(self, a, b, r):
        c = tuple((a[i] + b[i]) * 0.5 for i in range(3))
        d = tuple(b[i] - a[i] for i in range(3))
        hl = 0.5 * math.sqrt(sum(x * x for x in d))
        if hl < 1e-4:
            self.ball(c, r)
            return
        self.items.append(("CAPSULE", c, r, hl, norm(d)))


def strand(E, rng, p, d, L, r, depth, droplets=True):
    """One liquid strand from p along d (runner-local), length L, radius r: gravity-bent arc of 6 capsules with a lateral
    wobble and beads, a round tip bead, forks (depth > 0) and separate droplets continuing the arc."""
    n = 6
    seg = L / n
    side_w = rng.uniform(-0.35, 0.35)
    fork_at = rng.randint(2, 4) if depth > 0 else -1
    bead_at = {rng.randint(1, 4)} if rng.random() < 0.7 else set()
    a = p
    for k in range(n):
        u = (k + 1) / n
        rr = r * (1.0 - 0.32 * u)
        # gravity bends the strand down along its length; a slow sideways wobble keeps it from reading as a straight post
        d = norm(add(add(d, (0.0, -1.0, 0.0), GRAV * u), rot_y((d[0], 0.0, d[2]), 90.0), side_w * 0.25))
        b = add(a, d, seg)
        if b[1] < 0.004:                          # strands that fall back to the water slide along it
            b = (b[0], 0.004, b[2])
        E.capsule(a, b, rr)
        if k in bead_at:
            E.ball(b, rr * rng.uniform(1.35, 1.6))
        if k == fork_at:
            sgn = rng.choice((-1.0, 1.0))
            fd = norm(add(rot_y(d, sgn * rng.uniform(25.0, 45.0)), (0.0, 1.0, 0.0), rng.uniform(-0.1, 0.35)))
            strand(E, rng, b, fd, L * rng.uniform(0.38, 0.6), rr * 0.82, depth - 1, droplets)
        a = b
    E.ball(add(a, d, 0.006), r * rng.uniform(1.45, 1.8))      # round bead on the tip
    if droplets:
        q, dd = a, d
        gap = rng.uniform(0.035, 0.06)
        for j in range(rng.choice((0, 1, 1, 2, 2, 3))):        # separate droplets flying on along the arc, shrinking
            dd = norm(add(dd, (0.0, -1.0, 0.0), 0.22))
            q = add(q, dd, gap * (1.0 + 0.45 * j))
            if q[1] < 0.01:
                break
            E.ball(q, r * (1.05 - 0.2 * j) * rng.uniform(0.85, 1.15))


def base_sheet(E, rng, s, cx, cz, rad, a0, a1, h0, h1, n, r):
    """Connected curved milk base hugging the outer side of a foot: an arc of capsules from the water up to a leaning rim
    (rim balls make the rounded lip). Returns the rim points + their outward normals (strand roots)."""
    rim = []
    for j in range(n):
        u = j / (n - 1)
        ang = a0 + (a1 - a0) * u                             # azimuth around the foot (0 = forward, 90 = outward)
        o = dir_from(s * ang, 0.0)
        bx, bz = cx + o[0] * rad, cz + o[2] * rad
        h = h0 + (h1 - h0) * math.sin(math.pi * u) + rng.uniform(-0.012, 0.012)
        top = add((bx, h, bz), o, 0.45 * h)
        E.capsule((bx, 0.012, bz), top, r)
        E.ball(top, r * 1.18)
        rim.append((top, o, ang))
    return rim


def crown_side(s, seed, big):
    """Master crown of one side (s = +1 travel-right, -1 travel-left), runner-local metres; big = the reference's larger
    right-hand spray (taller, wider, with the low arm sweeping toward the camera)."""
    rng = random.Random(seed)
    E = Elems()
    k = 1.0 if big else 0.8
    fx, fz = s * 0.22, 0.10                                  # foot centre (sole pads face the rear camera)
    # 1) connected curved base: from beside the toes (az 20) round the outer side to behind the heel (az 160)
    rim = base_sheet(E, rng, s, fx, fz, 0.16, 15.0, 165.0, 0.07, 0.22 * k, 14, 0.034)
    # 2) main spray: strands from the rim fanning outward, rising 25-70 deg and falling back, longer at the outer side
    n_main = 8 if big else 6
    for i in range(n_main):
        top, o, ang = rim[min(len(rim) - 1, int((i + rng.uniform(0.15, 0.85)) * len(rim) / n_main))]
        az = s * (ang + rng.uniform(-18.0, 18.0))
        el = rng.uniform(42.0, 78.0)
        L = rng.uniform(0.3, 0.5) * k * (1.15 if 60.0 < ang < 130.0 else 0.9)
        strand(E, rng, top, dir_from(az, el), L, rng.uniform(0.026, 0.036), 2 if rng.random() < 0.75 else 1)
    # 3) low WAKE arm (rear view, reference lower right): a thin band lying on the water sweeping outward + back toward the
    #    camera from behind the foot, its rim breaking into low strands that skim outward
    n_w = 9 if big else 6
    wl = 0.95 * k
    for j in range(n_w):
        u = (j + 0.5) / n_w
        p = (fx + s * (0.12 + 0.7 * u * wl), 0.0, fz - 0.10 - 0.42 * u * wl)
        h = (0.05 + 0.03 * rng.random()) * (1.0 - 0.5 * u)
        E.capsule((p[0], 0.006, p[2]), (p[0] + s * 0.02, h, p[2]), 0.022)
        if j % 2 == 0 or rng.random() < 0.4:
            az = s * rng.uniform(100.0, 150.0)
            strand(E, rng, (p[0] + s * 0.02, h, p[2]), dir_from(az, rng.uniform(18.0, 48.0)), rng.uniform(0.16, 0.3) * k,
                   rng.uniform(0.018, 0.024), 1)
    for j in range(n_w * 2):                                 # the band itself: capsules along the water, broken by gaps
        if j > 2 and rng.random() < 0.3:
            continue
        u0, u1 = j / (n_w * 2), (j + 1) / (n_w * 2)
        a = (fx + s * (0.12 + 0.7 * u0 * wl), 0.012, fz - 0.10 - 0.42 * u0 * wl)
        b = (fx + s * (0.12 + 0.7 * u1 * wl), 0.012, fz - 0.10 - 0.42 * u1 * wl)
        E.capsule(a, b, 0.022 * (1.0 - 0.45 * u0))
    # 4) low BOW arm (front comparison cameras): a V opening forward from the toes, strands fanning outward-forward
    n_b = 7 if big else 6
    bl = 1.0 * k
    for j in range(n_b * 2):
        u0, u1 = j / (n_b * 2), (j + 1) / (n_b * 2)
        a = (fx + s * (0.06 + 0.55 * u0 * bl), 0.012, fz + 0.12 + 0.95 * u0 * bl)
        b = (fx + s * (0.06 + 0.55 * u1 * bl), 0.012, fz + 0.12 + 0.95 * u1 * bl)
        E.capsule(a, b, 0.026 * (1.0 - 0.4 * u0))
    for j in range(n_b):
        u = (j + 0.5) / n_b
        p = (fx + s * (0.06 + 0.55 * u * bl), 0.0, fz + 0.12 + 0.95 * u * bl)
        h = 0.07 * (1.0 - 0.45 * u) + 0.02 * rng.random()
        E.capsule((p[0], 0.006, p[2]), (p[0] + s * 0.02, h, p[2]), 0.024)
        az = s * rng.uniform(40.0, 85.0)
        strand(E, rng, (p[0] + s * 0.02, h, p[2]), dir_from(az, rng.uniform(25.0, 55.0)), rng.uniform(0.16, 0.3) * k,
               rng.uniform(0.018, 0.024), 1)
    # 6) SIDE RISERS (p3 08:09: from the rear camera the strands rising at the feet hide behind the body - ours rose ~40-60 px
    #    above the soles vs the reference ~120 px beside the body to arm height): roots beside the body edge (|x| .42-.62,
    #    z .02 -> -.25 toward the camera) joined to the foot base by a low milk band, steep strands leaning outward
    n_s = 6 if big else 4
    prev = (fx + s * 0.16, 0.012, fz - 0.02)
    for j in range(n_s):
        u = (j + 0.5) / n_s
        root = (s * (0.42 + 0.2 * u * k), 0.0, 0.02 - 0.27 * u)
        E.capsule(prev, (root[0], 0.012, root[2]), 0.026 * (1.0 - 0.3 * u))
        prev = (root[0], 0.012, root[2])
        h = 0.06 + 0.04 * rng.random()
        E.capsule((root[0], 0.006, root[2]), (root[0] + s * 0.02, h, root[2]), 0.03)
        strand(E, rng, (root[0] + s * 0.02, h, root[2]), dir_from(s * rng.uniform(80.0, 140.0), rng.uniform(44.0, 70.0)),
               rng.uniform(0.32, 0.5) * k, rng.uniform(0.024, 0.032), 2 if rng.random() < 0.6 else 1)
    # 5) loose droplet cloud around the spray (varied sizes, never on the lane centre)
    for _ in range(26 if big else 18):
        az = s * rng.uniform(20.0, 160.0)
        dist = rng.uniform(0.25, 0.85) * k
        o = dir_from(az, 0.0)
        c = (fx + o[0] * dist, rng.uniform(0.06, 0.5) * k, fz + o[2] * dist)
        E.ball(c, rng.uniform(0.012, 0.03))
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


def unity_euler_fwd(ex, ey):
    """Forward of a Unity euler (x pitch down +, y yaw right +), roll ignored."""
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
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.3
        bsdf.inputs["Subsurface Radius"].default_value = C.hex_rgba("#9CC8F0")[:3]
        bsdf.inputs["Subsurface Scale"].default_value = 0.02
    for side, s, seed, big in (("L", -1.0, 4471, False), ("R", 1.0, 9127, True)):
        name = "SM_FX_CrownV4_" + side
        E = crown_side(s, seed, big)
        obj, raw = build_mesh(name, E, milk)
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
        zs = [v.co.z for v in obj.data.vertices]
        print("CHECK %s %d tris (raw %d), %d elems, unity x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
            name, C.tri_count(obj), raw, len(E.items), -max(xs), -min(xs), min(zs), max(zs), -max(ys), -min(ys)))
        if not QUICK:
            C.export_fbx([obj], C.model_path(GROUP, name))
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
    C._light("Fill", 'AREA', 90, "#8FB0FF", t + Vector((2.0, 0.0, 0.3)), t, 3.0)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    # R2 rear comparison camera (lead 06:53: back 3.0 / height 0.9 / lat 0.3 / yaw -7 / pitch 5 / vFOV 50)
    rear = look_cam("CamRear", (0.3, 0.9, -3.0), unity_euler_fwd(5.0, -7.0), 50.0)
    # R4-like front comparison camera (2.6 ahead, 1.3 up, 0.3 right, aim mascot +0.6, then yaw 9.1 / pitch 2.9 up)
    pos = (0.3, 1.3, 2.6)
    f0 = norm((0 - pos[0], 0.6 - pos[1], 0 - pos[2]))
    front = look_cam("CamFront", pos, yaw_pitch(f0, 9.1, 2.9), 52.0)
    for cam, tag in ((rear, "rear"), (front, "front")):
        scene.camera = cam
        scene.render.filepath = C.preview_path("FX_CrownV4_" + tag)
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", scene.render.filepath)
    print("DONE crown v4")


main()
