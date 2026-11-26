"""Bubble Wash Kingdom - FX group (Blender 5.3, headless, deterministic): 3D milk splash meshes.

  SM_FX_Crown_00 .. _11   one seamless looping animation (12 frames) of the milky bow-wave crown that rises beside
                          the mascot's feet (reference f_001.75-f_003.00: opaque milky-white lace splash rising about a
                          third of the body, thick rounded tendrils ending in droplets, lace holes, small detached
                          drops). Built from metaballs (smooth liquid unions), polygonised, decimated.
                          LEFT-side splash; Unity mirrors it (scale x -1) for the right side.
                          Origin = splash root on the water surface at the outer side of the foot.
                          Blender axes: +X = outward (mascot's left), +Y = backward (toward the camera), Z up.
                          Slot M_FX_Milk.
  SM_FX_Droplet           milk droplet, radius 0.5 sphere slightly stretched along the travel axis (-Y)   M_FX_Milk
  SM_FX_BubbleLow         low-poly soap bubble sphere r 0.5 for small bubble particles                    M_Bubble

Preview: Docs/AssetPreviews/FX_SplashCrown.png (Blender render only).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_splash.py <log>
"""
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
FRAMES = 12
RES = 0.0105          # metaball polygonisation step (m)
TARGET_TRIS = 7000    # per crown frame after decimation
SEED = 20261125


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ================================================================== crown shape
def base(s):
    """Root line on the water: from the foot outward and back toward the camera."""
    return Vector((0.04 + 0.40 * s + 0.10 * s * s, -0.04 + 1.02 * s, 0.0))


def height(s):
    """Crown silhouette: quick rise beside the foot, peak at s ~ 0.28, long low tail toward the camera."""
    return 0.07 + 0.43 * math.exp(-((s - 0.27) / 0.25) ** 2) + 0.09 * (1.0 - s)


LEAN = Vector((0.55, 0.28, 1.0)).normalized()     # the sheet rises outward and slightly back


def wall(s, v, sway=0.0):
    h = height(s)
    p = base(s) + LEAN * (v * h)
    p.x += 0.2 * h * v * v + sway * v              # lip curls outward at the top
    return p


class Balls:
    """Metaball element list for one frame."""

    def __init__(self):
        self.items = []

    def ball(self, p, r):
        if r > 0.004:
            self.items.append((Vector(p), r))

    def chain(self, pts, radii, step=0.42):
        """Balls along a polyline, spaced <= step * radius so the chain fuses into a smooth tube."""
        for (a, ra), (b, rb) in zip(zip(pts, radii), zip(pts[1:], radii[1:])):
            seg = (b - a).length
            rmin = max(0.006, min(ra, rb))
            n = max(1, int(math.ceil(seg / (step * rmin))))
            for k in range(n):
                t = k / n
                self.ball(a.lerp(b, t), lerp(ra, rb, t))
        self.ball(pts[-1], radii[-1])


def build_crown_balls(tau):
    """All metaball elements for loop phase tau in [0, 1). Structure is fixed (seeded); motion is periodic in tau."""
    rng = random.Random(SEED)
    B = Balls()
    two_pi_t = 2.0 * math.pi * tau

    # --- vertical lace strands (fixed structure, periodic sway / breathing)
    ns = 10
    strands = []
    for i in range(ns):
        s0 = (i + 0.5) / ns + rng.uniform(-0.025, 0.025)
        ph = rng.uniform(0, 2 * math.pi)
        thick = rng.uniform(0.85, 1.2)
        top = rng.uniform(0.82, 1.0)
        strands.append((s0, ph, thick, top))
    for (s0, ph, thick, top) in strands:
        fade = smoothstep(-0.02, 0.07, s0) * smoothstep(1.02, 0.86, s0)
        pts, rad = [], []
        n = 12
        for k in range(n + 1):
            v = k / n * top
            s = s0 + 0.03 * math.sin(v * 3.1 + ph + two_pi_t) + 0.015 * math.sin(two_pi_t * 2 + ph)
            sway = 0.025 * math.sin(two_pi_t + ph + v * 2.0)
            pts.append(wall(s, v, sway))
            rad.append((0.05 - 0.018 * v) * thick * fade)
        B.chain(pts, rad)

    # --- horizontal lace: thick base rim on the water, gated mid strand and top rim -> enclosed holes
    def rim(vfun, rfun, n=48):
        pts, rad = [], []
        for k in range(n + 1):
            s = k / n
            pts.append(wall(s, vfun(s), 0.02 * math.sin(two_pi_t + s * 9.0)))
            rad.append(rfun(s))
        B.chain(pts, rad)

    gate_ph = [rng.uniform(0, 6.28) for _ in range(4)]

    def gate(s, j, lo=0.45, hi=0.75):
        g = 0.5 + 0.5 * math.sin(s * (11.0 + j * 3.0) + gate_ph[j] + 0.6 * math.sin(two_pi_t + j))
        return smoothstep(lo, hi, g)

    taper = lambda s: smoothstep(-0.02, 0.06, s) * smoothstep(1.03, 0.85, s)  # noqa: E731
    rim(lambda s: 0.02, lambda s: 0.062 * taper(s) + 0.01)
    rim(lambda s: 0.42 + 0.1 * math.sin(s * 7.0 + gate_ph[1] + two_pi_t), lambda s: 0.034 * gate(s, 0) * taper(s))
    rim(lambda s: 0.86 + 0.06 * math.sin(s * 9.0 + gate_ph[2] - two_pi_t), lambda s: 0.038 * gate(s, 2, 0.35, 0.65) * taper(s))

    # --- foam skirt where the sheet meets the water (flattened blobs along the root, both sides of the wall)
    for k in range(22):
        s = (k + 0.5) / 22
        for side in (-1.0, 1.0):
            p = base(s) + Vector((side * 0.06 + 0.02 * math.sin(k * 1.7 + two_pi_t), 0.0, 0.012))
            B.ball(p, (0.05 + 0.015 * math.sin(k * 2.3 + two_pi_t)) * taper(s))

    # --- tendrils from the top rim: grow, pinch off a droplet, retract (periodic life cycle per tendril)
    nt = 9
    for j in range(nt):
        s0 = 0.05 + 0.85 * (j + rng.uniform(0.2, 0.8)) / nt
        phase = rng.uniform(0, 1)
        lmax = rng.uniform(0.12, 0.26) * (0.6 + 0.8 * math.exp(-((s0 - 0.3) / 0.35) ** 2))
        out = Vector((rng.uniform(0.2, 0.8), rng.uniform(-0.1, 0.5), 1.0)).normalized()
        out = (out + LEAN * 0.6).normalized()
        r_root = rng.uniform(0.026, 0.036)
        r_tip = rng.uniform(0.034, 0.046)
        age = (tau + phase) % 1.0
        grow = smoothstep(0.0, 0.5, age) * (1.0 - smoothstep(0.62, 1.0, age))
        root = wall(s0, 0.9, 0.0)
        L = lmax * grow
        if L > 0.015:
            pts, rad = [], []
            n = 8
            for k in range(n + 1):
                t = k / n
                bend = Vector((0.06 * t * t, 0.03 * t * t, -0.05 * t * t))   # tips droop outward under gravity
                pts.append(root + out * (L * t) + bend * (L / 0.2))
                rad.append(lerp(r_root, r_root * 0.55, t) * min(1.0, grow * 1.6))
            B.chain(pts, rad)
            # bulbous droplet tip still attached
            B.ball(pts[-1] + out * 0.012, r_tip * min(1.0, grow * 1.4))
        # released drop flying away after the pinch (age 0.5 .. 1.0), shrinking to nothing at the loop end
        if age > 0.5:
            a = (age - 0.5) / 0.5
            tip = root + out * lmax
            vel = out * 0.55 + Vector((0.15, 0.25, 0.25))
            p = tip + vel * a * 0.35 + Vector((0, 0, -0.9 * a * a * 0.35))
            B.ball(p, r_tip * 0.95 * (1.0 - a) ** 0.5)

    # --- loose droplets on ballistic arcs (periodic), small satellite drops
    for j in range(16):
        s0 = rng.uniform(0.05, 0.95)
        phase = rng.uniform(0, 1)
        r0 = rng.uniform(0.016, 0.03)
        vel = Vector((rng.uniform(0.3, 1.1), rng.uniform(0.0, 0.9), rng.uniform(0.6, 1.4)))
        age = (tau + phase) % 1.0
        start = wall(s0, rng.uniform(0.5, 0.95), 0.0)
        tt = age * 0.38
        p = start + vel * tt + Vector((0, 0, -4.9 * tt * tt))
        B.ball(p, r0 * math.sin(math.pi * age) ** 0.5)
    return B.items


def crown_mesh(frame, mat):
    tau = frame / FRAMES
    fam = "MBCROWN%02d" % frame                  # unique metaball family per frame (no '.' suffix)
    mb = bpy.data.metaballs.new(fam)
    mb.resolution = RES
    mb.render_resolution = RES
    mb.threshold = 0.6
    ob = bpy.data.objects.new(fam, mb)
    bpy.context.scene.collection.objects.link(ob)
    for p, r in build_crown_balls(tau):
        e = mb.elements.new(type='BALL')
        e.co = p
        e.radius = r * 1.75                       # visible radius ~0.57 R for an isolated ball
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
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
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


def main():
    C.reset_scene()
    milk = C.material("M_FX_Milk", "#FFFFFF", roughness=0.12, coat=0.3)
    bub = C.material("M_Bubble", "#FFFFFF", roughness=0.02, alpha=0.15)
    report = []
    crowns = []
    for f in range(FRAMES):
        obj, raw = crown_mesh(f, milk)
        crowns.append(obj)
        report.append("%-16s %6d tris (raw %6d)  dims %s" % (obj.name, C.tri_count(obj), raw, tuple(round(d, 3) for d in obj.dimensions)))
        C.export_fbx([obj], C.model_path(GROUP, obj.name))
    for o in (build_droplet(milk), build_bubble_low(bub)):
        report.append("%-16s %6d tris  dims %s" % (o.name, C.tri_count(o), tuple(round(d, 3) for d in o.dimensions)))
        C.export_fbx([o], C.model_path(GROUP, o.name))
        o.hide_render = True
    print("\n".join("CHECK " + r for r in report))

    # ---------------- preview: 4 frames side by side on blue water, seen from behind / above like the gameplay camera
    water = bpy.data.meshes.new("water")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6)
    bm.to_mesh(water)
    wo = bpy.data.objects.new("water", water)
    bpy.context.scene.collection.objects.link(wo)
    wo.data.materials.append(C.material("PV_Water", "#2AA6DC", roughness=0.15))
    shown = [0, 3, 6, 9]
    for i, o in enumerate(crowns):
        if i in shown:
            k = shown.index(i)
            o.location = (-2.1 + k * 1.35, 0.0, 0.0)
        else:
            o.hide_render = True
    C.render_preview(C.preview_path("FX_SplashCrown"), camera_location=(-0.2, 4.2, 2.2), target=(-0.15, 0.4, 0.2),
                     lens=38, resolution=(1280, 720), light_scale=1.6)
    print("DONE build_fx_splash")


if __name__ == "__main__":
    main()
