"""Bubble Wash Kingdom - FX group (Blender 5.3, headless, deterministic): 3D milk splash meshes.

  SM_FX_Crown_00 .. _11   one seamless looping animation (12 frames) of the milky crown splash that fans out of the
                          water beside the mascot's foot (reference f_003.00s + owner correction 03: a CURVED milky SHEET
                          with ROUND holes of varied size, thick rounded rims, scalloped top edge with fingers / beads,
                          flying droplets). Built from metaballs (smooth liquid unions), polygonised, decimated.
                          LEFT-side splash; Unity mirrors it (scale x -1) for the right side.
                          Asset axes: +X = outward (mascot's left), +Y = backward (toward the camera), Z up.
                          Origin = placed by Unity at runner-local (-CrownRootX, 0, CrownRootZ) (SceneBuilder.WaterFX),
                          just outside / ahead of the left foot. Slot M_FX_Milk.
  SM_FX_Droplet           milk droplet, radius 0.5 sphere slightly stretched along the travel axis (-Y)   M_FX_Milk
  SM_FX_BubbleLow         low-poly soap bubble sphere r 0.5 for small bubble particles                    M_Bubble

Preview: Docs/AssetPreviews/FX_SplashCrown_r3.png = both crowns seen through the owner-approved hero camera
(2.75 / 1.3 / 10 / 58, measured runner-local pose) around a stand-in mascot (Blender render only, no reference pixels).
Prints PREVIEW-BBOX lines = screen coverage of each crown (x, y from the top-left of the 9:16 frame).
Env BWK_FX_QUICK=1: build frames 0 and 6 only, no export (placement check).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_splash.py <log>
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bwk_common as C  # noqa: E402

GROUP = "FX"
FRAMES = 12
RES = 0.0068          # metaball polygonisation step (m)
TARGET_TRIS = 11000   # per crown frame after decimation
SEED = 20261126
QUICK = os.environ.get("BWK_FX_QUICK", "") == "1"

# Unity placement (keep in sync with SceneBuilder.WaterFX CrownRootX / CrownRootZ) and the measured hero camera
CROWN_ROOT_X, CROWN_ROOT_Z = 0.40, -0.05
HERO_CAM_POS = (-0.099, 0.768, -2.640)          # runner-local, Unity axes (mirrored track build 05:48)
HERO_CAM_EULER = (1.52, 3.62, 5.74)             # Unity euler degrees (z, x, y order)
HERO_FOV = 58.0


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


class Elems:
    """Metaball element list for one frame: balls and capsules."""

    def __init__(self):
        self.items = []

    def ball(self, p, r):
        if r > 0.004:
            self.items.append(("B", Vector(p), None, r))

    def cap(self, a, b, r):
        if r > 0.004 and (b - a).length > 1e-4:
            self.items.append(("C", Vector(a), Vector(b), r))

    def chain(self, pts, radii):
        for (a, ra), (b, rb) in zip(zip(pts, radii), zip(pts[1:], radii[1:])):
            self.cap(a, b, 0.5 * (ra + rb))


# ================================================================== crown shape (round 3: perforated milk SHEET)
# Each crown is a curved, continuous milky sheet fanning out of the water beside a foot: solid near the water, perforated
# by ROUND holes (bigger toward the top) with thick rounded rims, an irregular scalloped top edge with fingers and droplet
# beads, flying drops. Metaball SHEET = dense balls on a curved fan surface (skipped inside the holes) + capsule rings
# around each hole (thick rims) + rim chain / fingers / beads / drops. Foot centre in asset space ~(-0.10, 0.25, 0.17).
# Two sheets per crown, both facing the hero camera (round holes stay round on screen):
#  CURTAIN: rises from the water just outside the foot and runs OUTWARD (lateral), leaning back toward the camera with
#           an outward-curling lip (fills the frame beside the foot, screen y ~.58-.80);
#  SKIRT:   a low perforated sheet thrown back toward the camera from the curtain's outer end, curling in UNDER the foot
#           on screen (y ~.80-.90) while staying below the sole.
SHEETS = [
    dict(name="curtain",
         root=((-0.05, 0.14), (0.14, 0.24), (0.34, 0.32), (0.54, 0.40)),
         fan=((0.05, 0.30, 0.95), (0.16, 0.30, 0.94), (0.30, 0.30, 0.90), (0.46, 0.34, 0.82)),
         flen=(0.40, 0.72, 0.80, 0.62), flare=0.34, hole=(0.024, 0.090), solid=0.12, fingers=13, roll=0.024, drops=3.0),
    dict(name="skirt",
         root=((0.44, 0.44), (0.30, 0.66), (0.12, 0.84), (-0.06, 0.96)),
         fan=((0.40, 0.22, 0.89), (0.22, 0.26, 0.94), (0.10, 0.30, 0.95), (0.0, 0.32, 0.95)),
         flen=(0.32, 0.22, 0.13, 0.07), flare=0.22, hole=(0.018, 0.046), solid=0.16, fingers=7, roll=0.012, drops=1.0),
]
SHEET_STEP = 0.019     # metaball grid spacing on the sheet (m)
SHEET_R = 0.0125       # sheet ball radius -> ~3.5 cm thick milky sheet
RIM_R = 0.0165         # hole rim capsule radius -> thick rounded rims


def cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def lin(vals, s):
    n = len(vals) - 1
    x = max(0.0, min(0.9999, s)) * n
    i = int(x)
    return lerp(vals[i], vals[i + 1], x - i)


class Sheet:
    def __init__(self, spec):
        self.root = [Vector((x, y, 0.0)) for (x, y) in spec["root"]]
        self.fan = [Vector(d).normalized() for d in spec["fan"]]
        self.flen = spec["flen"]
        self.flare = spec["flare"]
        self.hole = spec["hole"]
        self.solid = spec["solid"]
        self.fingers = spec["fingers"]
        self.name = spec["name"]
        self.roll = spec.get("roll", 0.024)
        self.drops = spec.get("drops", 3.0)
        tot, prev = 0.0, self.rootp(0.0)
        for k in range(1, 101):
            p = self.rootp(k / 100)
            tot += (p - prev).length
            prev = p
        self.Stot = tot

    def rootp(self, s):
        pts = self.root
        n = len(pts) - 1
        x = max(0.0, min(0.9999, s)) * n
        i = int(x)
        return cr(pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n, i + 2)], x - i)

    def fan_dir(self, s):
        n = len(self.fan) - 1
        x = max(0.0, min(0.9999, s)) * n
        i = int(x)
        return self.fan[i].lerp(self.fan[i + 1], x - i).normalized()

    def outward(self, s):
        d = self.fan_dir(s)
        o = Vector((d.x, d.y, 0.0))
        return o.normalized() if o.length > 1e-4 else Vector((1, 0, 0))

    def point(self, s, v, sway=0.0):
        p = self.rootp(s) + self.fan_dir(s) * v
        o = self.outward(s)
        return p + (o * self.flare + Vector((0, 0, -0.10))) * v * v + o * (sway * v)

    def fan_len(self, s):
        return lin(self.flen, s)


def sheet_elements(E, sh, rng, tau, salt):
    tw = 2.0 * math.pi * tau
    Stot = sh.Stot
    ph1, ph2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)

    def top(S):                                    # scalloped top edge (metres along the fan)
        s = S / Stot
        return sh.fan_len(s) * (1.0 + 0.12 * math.sin(S * 23.0 + ph1 + tw) + 0.07 * math.sin(S * 51.0 + ph2 - 1.3 * tw)
                                + 0.05 * math.sin(S * 9.0 - tw))

    def P(S, V):
        s = S / Stot
        sw = 0.025 * math.sin(tw + s * 5.0 + salt)
        p = sh.point(s, V, sw)
        # liquid undulation across the sheet face (the sheet never reads as a flat slab), travelling with the loop
        a = sh.point(min(1.0, s + 0.01), V, sw) - sh.point(max(0.0, s - 0.01), V, sw)
        b = sh.point(s, V + 0.01, sw) - sh.point(s, max(0.0, V - 0.01), sw)
        n = a.cross(b)
        if n.length > 1e-8:
            n.normalize()
            amp = smoothstep(0.0, 0.12, V)
            p = p + n * amp * (0.020 * math.sin(S * 17.0 + V * 11.0 + tw + salt) + 0.010 * math.sin(S * 31.0 - V * 7.0 - 1.3 * tw))
        return p

    holes = []
    hmin, hmax = sh.hole
    for _ in range(4000):
        S = rng.uniform(0.0, Stot)
        V = rng.uniform(0.03, 0.75)
        t = top(S)
        if V > t * 1.05:
            continue
        vf = V / max(0.05, t)
        if vf < sh.solid:
            continue
        r = lerp(hmin, hmax, vf ** 0.9) * rng.uniform(0.65, 1.2)
        if all((S - S2) ** 2 + (V - V2) ** 2 >= (r + r2 + 0.028) ** 2 for (S2, V2, r2, _a) in holes):
            holes.append((S, V, r, rng.uniform(0, 6.28)))
    live = [(S + 0.008 * math.sin(tw + a), V + 0.012 * math.sin(tw + a * 1.7), r * (1.0 + 0.08 * math.sin(tw + a * 2.3)))
            for (S, V, r, a) in holes]            # periodic: holes drift on the sheet and breathe

    def in_hole(S, V, pad=0.0):
        for (Sh, Vh, rh) in live:
            if (S - Sh) ** 2 + (V - Vh) ** 2 < (rh + pad) ** 2:
                return True
        return False

    n_sheet = 0
    S = 0.0
    while S <= Stot:
        t = top(S)
        V = 0.0
        while V <= t:
            if not in_hole(S, V):
                E.ball(P(S, V), SHEET_R * (1.15 if V < 0.04 else 1.0))
                n_sheet += 1
            V += SHEET_STEP
        S += SHEET_STEP
    for (Sh, Vh, rh) in live:                     # thick rounded rims around every hole
        n = max(8, int(2 * math.pi * rh / 0.022))
        pts, keep = [], []
        for k in range(n + 1):
            a = 2 * math.pi * k / n
            Sr, Vr = Sh + (rh + 0.004) * math.cos(a), Vh + (rh + 0.004) * math.sin(a)
            pts.append((Sr, Vr))
            keep.append(0.0 <= Sr <= Stot and 0.0 <= Vr <= top(min(Stot, max(0.0, Sr))) + 0.01)
        rr = RIM_R * rng.uniform(0.85, 1.2) * (1.0 + 0.25 * min(1.0, rh / 0.07))
        for k in range(n):
            if keep[k] and keep[k + 1]:
                E.cap(P(*pts[k]), P(*pts[k + 1]), rr)
    m = 60                                        # top edge rim chain + beads on the crests
    prev = None
    for k in range(m + 1):
        S = Stot * k / m
        V = top(S)
        cur = None if in_hole(S, V, 0.004) else P(S, V)
        if cur is not None and prev is not None:
            E.cap(prev, cur, 0.019)
        prev = cur
    for k in range(1, m):
        S0, S1, S2 = Stot * (k - 1) / m, Stot * k / m, Stot * (k + 1) / m
        if top(S1) > top(S0) and top(S1) >= top(S2) and not in_hole(S1, top(S1), 0.004):
            E.ball(P(S1, top(S1)), rng.uniform(0.026, 0.036))
    nb = 30                                       # solid root roll where the sheet leaves the water
    E.chain([sh.rootp(k / nb) + Vector((0, 0, 0.010)) for k in range(nb + 1)],
            [sh.roll * (1.0 + 0.3 * math.sin(k * 0.9 + tw + salt)) for k in range(nb + 1)])
    for j in range(sh.fingers):                   # fingers: grow, pinch off a drop, retract
        S0 = Stot * (0.05 + 0.88 * (j + rng.uniform(0.2, 0.8)) / sh.fingers)
        phase = rng.uniform(0, 1)
        lmax = rng.uniform(0.07, 0.19)
        r_root, r_tip = rng.uniform(0.016, 0.022), rng.uniform(0.024, 0.036)
        age = (tau + phase) % 1.0
        grow = smoothstep(0.0, 0.5, age) * (1.0 - smoothstep(0.62, 1.0, age))
        s0 = S0 / Stot
        root = P(S0, top(S0) * 0.97)
        tip_dir = (sh.point(s0, top(S0) + 0.05) - sh.point(s0, top(S0))).normalized()
        tip_dir = (tip_dir + Vector((0, 0, 0.35)) + sh.outward(s0) * 0.25).normalized()
        L = lmax * grow
        if L > 0.012:
            pts, rad = [], []
            for k in range(6):
                t = k / 5
                pts.append(root + tip_dir * (L * t) + Vector((0, 0, -0.10 * t * t * L / 0.15)))
                rad.append(lerp(r_root, r_root * 0.6, t) * min(1.0, grow * 1.6))
            E.chain(pts, rad)
            E.ball(pts[-1] + tip_dir * 0.008, r_tip * min(1.0, grow * 1.4))
        if age > 0.55:
            a = (age - 0.55) / 0.45
            tip = root + tip_dir * lmax
            vel = tip_dir * 0.7 + sh.outward(s0) * 0.3
            E.ball(tip + vel * a * 0.3 + Vector((0, 0, -0.5 * a * a * 0.3)), r_tip * 0.9 * (1.0 - a) ** 0.5)
    for j in range(int(sh.drops * sh.fingers)):    # loose droplets on ballistic arcs (periodic)
        S0 = rng.uniform(0.04, 0.95) * Stot
        phase = rng.uniform(0, 1)
        r0 = rng.uniform(0.010, 0.028)
        s0 = S0 / Stot
        vel = sh.outward(s0) * rng.uniform(0.4, 1.0) + Vector((0, rng.uniform(-0.1, 0.4), rng.uniform(0.6, 1.2)))
        age = (tau + phase) % 1.0
        start = P(S0, top(S0) * rng.uniform(0.7, 1.0))
        tt = age * 0.38
        p = start + vel * tt + Vector((0, 0, -4.9 * tt * tt))
        if p.z > 0.02:
            E.ball(p, r0 * math.sin(math.pi * age) ** 0.5)
    return n_sheet, len(live)


def build_crown_elements(tau):
    """All metaball elements for loop phase tau in [0, 1). Structure is seeded; motion is periodic in tau."""
    E = Elems()
    info = []
    for k, spec in enumerate(SHEETS):
        rng = random.Random(SEED + 101 * k)
        n_sheet, n_holes = sheet_elements(E, Sheet(spec), rng, tau, 1.7 * k)
        info.append("%s %d balls %d holes" % (spec["name"], n_sheet, n_holes))
    print("crown tau %.2f: %s, %d elements" % (tau, ", ".join(info), len(E.items)))
    return E.items


def crown_mesh(frame, mat):
    tau = frame / FRAMES
    fam = "MBCROWN%02d" % frame                  # unique metaball family per frame (no '.' suffix)
    mb = bpy.data.metaballs.new(fam)
    mb.resolution = RES
    mb.render_resolution = RES
    mb.threshold = 0.6
    ob = bpy.data.objects.new(fam, mb)
    bpy.context.scene.collection.objects.link(ob)
    X = Vector((1.0, 0.0, 0.0))
    items = build_crown_elements(tau)
    for kind, a, b, r in items:
        if kind == "B":
            e = mb.elements.new(type='BALL')
            e.co = a
        else:
            e = mb.elements.new(type='CAPSULE')
            d = b - a
            e.co = (a + b) * 0.5
            e.size_x = d.length * 0.5
            e.rotation = X.rotation_difference(d.normalized())
        e.radius = r * 1.75                       # visible radius ~ r for an isolated element
        e.stiffness = 2.0
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    name = "SM_FX_Crown_%02d" % frame
    me.name = name
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    print("frame %d: %d elements, %d raw tris" % (frame, len(items), tris))
    if tris > TARGET_TRIS:
        C.select_only([obj])
        mod = obj.modifiers.new("dec", 'DECIMATE')
        mod.ratio = TARGET_TRIS / tris
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(obj, [mat])
    box_uv(obj)
    return obj, tris


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


# ================================================================== droplet + low bubble
def build_droplet(mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.5)
    for v in bm.verts:
        # head round toward travel (-Y), slightly pointed tail behind (+Y)
        if v.co.y > 0:
            v.co.y *= 1.0 + 0.45 * (v.co.y / 0.5) ** 2
            v.co.x *= 1.0 - 0.18 * (v.co.y / 0.725)
            v.co.z *= 1.0 - 0.18 * (v.co.y / 0.725)
    obj = C.mesh_from_bmesh("SM_FX_Droplet", bm)
    for p in obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(obj, [mat])
    box_uv(obj)
    return obj


def build_bubble_low(mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=10, radius=0.5)
    obj = C.mesh_from_bmesh("SM_FX_BubbleLow", bm)
    for p in obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(obj, [mat])
    box_uv(obj)
    return obj


# ================================================================== hero-camera preview (Unity runner-local -> Blender)
def u2b(v):
    """Unity runner-local (x right, y up, z forward) -> preview world (x = -ux, y = -uz, z = uy)."""
    return Vector((-v[0], -v[2], v[1]))


def hero_camera():
    ex, ey, ez = (math.radians(a) for a in HERO_CAM_EULER)
    rx = Matrix(((1, 0, 0), (0, math.cos(ex), -math.sin(ex)), (0, math.sin(ex), math.cos(ex))))
    ry = Matrix(((math.cos(ey), 0, math.sin(ey)), (0, 1, 0), (-math.sin(ey), 0, math.cos(ey))))
    rz = Matrix(((math.cos(ez), -math.sin(ez), 0), (math.sin(ez), math.cos(ez), 0), (0, 0, 1)))
    R = ry @ rx @ rz
    right, up, fwd = R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0)), R @ Vector((0, 0, 1))
    m = Matrix((u2b(right), u2b(up), -u2b(fwd))).transposed()
    cd = bpy.data.cameras.new("HeroCam")
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(HERO_FOV)
    cam = bpy.data.objects.new("HeroCam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.matrix_world = Matrix.Translation(u2b(HERO_CAM_POS)) @ m.to_4x4()
    bpy.context.scene.camera = cam
    return cam


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


def hero_preview(crown_l, crown_r):
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    C.setup_preview_scene("#2A1B5A", 0.9)
    water = bpy.data.meshes.new("water")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=8)
    bm.to_mesh(water)
    wo = bpy.data.objects.new("water", water)
    scene.collection.objects.link(wo)
    wo.location = (0, -4, 0)
    wo.data.materials.append(C.material("PV_Water", "#1B5FCB", roughness=0.08))
    pink = C.material("PV_Mascot", "#F07AA0", roughness=0.7)
    cream = C.material("PV_Feet", "#FFE6EE", roughness=0.7)
    ellipsoid("PV_Body", u2b((0.0, 0.62, 0.05)), (0.50, 0.46, 0.52), pink)       # stand-in mascot (not shipped)
    for sx in (-1, 1):
        ellipsoid("PV_Foot", u2b((0.30 * sx, 0.17, -0.30)), (0.11, 0.06, 0.15), cream)
    # left crown: asset (ax, ay, az) -> Unity (-ax + rootL.x, az, -ay + rootZ) -> preview (ax + X, ay - rootZ, az)
    crown_l.location = (CROWN_ROOT_X, -CROWN_ROOT_Z, 0.0)
    crown_r.location = (-CROWN_ROOT_X, -CROWN_ROOT_Z, 0.0)
    crown_r.scale = (-1.0, 1.0, 1.0)
    for o in (crown_l, crown_r):
        o.hide_render = False
    cam = hero_camera()
    C.add_studio_lights(target=(0, 0, 0.4), scale=1.4)
    sun = bpy.data.lights.new("Sun", 'SUN')
    sun.energy = 2.0
    so = bpy.data.objects.new("Sun", sun)
    scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(160))
    scene.render.resolution_x, scene.render.resolution_y = 540, 960
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    for tag, o in (("L", crown_l), ("R", crown_r)):
        mw = o.matrix_world
        xs, ys = [], []
        for v in o.data.vertices:
            p = world_to_camera_view(scene, cam, mw @ v.co)
            if p.z > 0 and 0 <= p.x <= 1 and 0 <= p.y <= 1:
                xs.append(p.x)
                ys.append(1.0 - p.y)
        if xs:
            xs.sort()
            ys.sort()
            q = lambda a, f: a[int(f * (len(a) - 1))]  # noqa: E731
            print("PREVIEW-BBOX %s x %.2f-%.2f (p5-p95 %.2f-%.2f)  y %.2f-%.2f (p5-p95 %.2f-%.2f)  on-screen verts %d/%d" % (
                tag, xs[0], xs[-1], q(xs, .05), q(xs, .95), ys[0], ys[-1], q(ys, .05), q(ys, .95), len(xs), len(o.data.vertices)))
    for tag, p in (("footL", (-0.30, 0.17, -0.30)), ("footR", (0.30, 0.17, -0.30)), ("body", (0, 0.62, 0.05))):
        q = world_to_camera_view(scene, cam, u2b(p))
        print("PREVIEW-PT %s screen (%.2f, %.2f)" % (tag, q.x, 1 - q.y))
    scene.render.resolution_x, scene.render.resolution_y = 540, 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = C.preview_path("FX_SplashCrown_r3")
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", C.preview_path("FX_SplashCrown_r3"))


def main():
    C.reset_scene()
    milk = C.material("M_FX_Milk", "#F4F8FF", roughness=0.18, coat=0.4)
    bub = C.material("M_Bubble", "#FFFFFF", roughness=0.02, alpha=0.15)
    report = []
    crowns = {}
    for f in ([0, 6] if QUICK else range(FRAMES)):
        obj, raw = crown_mesh(f, milk)
        crowns[f] = obj
        obj.hide_render = True
        report.append("%-16s %6d tris (raw %6d)  dims %s" % (obj.name, C.tri_count(obj), raw, tuple(round(d, 3) for d in obj.dimensions)))
        if not QUICK:
            C.export_fbx([obj], C.model_path(GROUP, obj.name))
    if not QUICK:
        for o in (build_droplet(milk), build_bubble_low(bub)):
            report.append("%-16s %6d tris  dims %s" % (o.name, C.tri_count(o), tuple(round(d, 3) for d in o.dimensions)))
            C.export_fbx([o], C.model_path(GROUP, o.name))
            o.hide_render = True
    print("\n".join("CHECK " + r for r in report))
    # Unity shows frame 0 on the left crown and frame FRAMES/2 (mirrored) on the right in still captures
    hero_preview(crowns[0], crowns[6])
    print("DONE build_fx_splash")


if __name__ == "__main__":
    main()
