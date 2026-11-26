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
RES = 0.0095          # metaball polygonisation step (m): milk strands are 5-9 cm thick (round, fused holes)
TARGET_TRIS = 9000    # per crown frame after decimation
SEED = 20261125


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ================================================================== crown shape
# Reference f_001.75-f_003.00 (zoomed): the splash beside each foot is a LACE NET of thick milky strands (cells with
# large holes, fused rounded joints, beads on the rim, tendrils ending in drops) rising from a solid root, plus lace
# loops lying on the water that spread outward / back toward the camera. Built from capsule metaballs along the
# edges of a clipped Voronoi diagram on the crown wall (smaller cells near the root -> almost solid sheet there,
# big holes near the rim) + a flat Voronoi lace skirt on the water. Twelve looping frames (periodic site jitter).
SLEN = 1.3           # metres of wall along the root curve
# Round 3 (owner: "milky splash crowns on both sides", reference f_003.00s): a TALL milky sheet with round fused holes
# (thick 5-9 cm strands, small cells near the water -> almost solid there, bigger holes up top), fingers + drops on the rim.


def base(s):
    """Root line on the water: from the foot outward and back toward the camera."""
    return Vector((0.03 + 0.50 * s + 0.10 * s * s, -0.08 + 0.95 * s, 0.0))


def height(s):
    """Crown silhouette: rises beside the foot, peak ~0.8 m at s ~ 0.42 (outer side), lower tail toward the camera."""
    return 0.12 + 0.60 * math.exp(-((s - 0.42) / 0.30) ** 2) + 0.10 * (1.0 - s)


LEAN = Vector((0.42, 0.18, 1.0)).normalized()    # the sheet rises outward and slightly back


def wall(s, v, sway=0.0):
    h = height(s)
    p = base(s) + LEAN * (v * h)
    p.x += 0.26 * h * v * v + sway * v             # lip curls outward at the top
    return p


def outward(s):
    """Horizontal unit vector on the water pointing away from the mascot, perpendicular to the root curve."""
    d = base(min(1.0, s + 0.01)) - base(max(0.0, s - 0.01))
    o = Vector((d.y, -d.x, 0.0))
    if o.x < 0:
        o = -o
    return o.normalized()


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


def poisson(rng, n_try, inside, sample, mind):
    pts = []
    for _ in range(n_try):
        q = sample()
        if not inside(q):
            continue
        dq = mind(q)
        ok = True
        for p in pts:
            if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 < dq * dq:
                ok = False
                break
        if ok:
            pts.append(q)
    return pts


def voronoi_edges(sites, inside):
    """Voronoi edges (2D) of `sites`, clipped to the region `inside` by bisection. Returns [(a, b)] as 2D tuples."""
    from mathutils.geometry import delaunay_2d_cdt
    co = [Vector((x, y)) for (x, y) in sites]
    out = delaunay_2d_cdt(co, [], [], 0, 1e-6)
    verts, faces = out[0], out[2]
    cc = []
    for f in faces:
        if len(f) != 3:
            cc.append(None)
            continue
        a, b, c = (verts[f[0]], verts[f[1]], verts[f[2]])
        d = 2.0 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))
        if abs(d) < 1e-12:
            cc.append(None)
            continue
        ux = (a.length_squared * (b.y - c.y) + b.length_squared * (c.y - a.y) + c.length_squared * (a.y - b.y)) / d
        uy = (a.length_squared * (c.x - b.x) + b.length_squared * (a.x - c.x) + c.length_squared * (b.x - a.x)) / d
        cc.append((ux, uy))
    owners = {}
    for fi, f in enumerate(faces):
        n = len(f)
        for k in range(n):
            e = tuple(sorted((f[k], f[(k + 1) % n])))
            owners.setdefault(e, []).append(fi)
    edges = []
    for e, fs in owners.items():
        if len(fs) != 2 or cc[fs[0]] is None or cc[fs[1]] is None:
            continue
        p, q = cc[fs[0]], cc[fs[1]]
        ip, iq = inside(p), inside(q)
        if not ip and not iq:
            continue
        if ip != iq:
            lo, hi = (p, q) if ip else (q, p)
            for _ in range(18):
                m = ((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5)
                if inside(m):
                    lo = m
                else:
                    hi = m
            p, q = (p, lo) if ip else (lo, q)
        edges.append((p, q))
    return edges


def build_crown_elements(tau):
    """All metaball elements for loop phase tau in [0, 1). Structure is fixed (seeded); motion is periodic in tau."""
    rng = random.Random(SEED)
    E = Elems()
    tw = 2.0 * math.pi * tau
    taper = lambda s: smoothstep(-0.02, 0.06, s) * smoothstep(1.03, 0.85, s)  # noqa: E731
    rim_ph = rng.uniform(0, 6.28)

    def top(s):
        return 1.0 + 0.10 * math.sin(s * 15.0 + rim_ph + tw) + 0.05 * math.sin(s * 33.0 - tw)

    def Hm(S):                                   # metric wall height at metric position S
        s = max(0.0, min(1.0, S / SLEN))
        return height(s) * top(s)

    def to3d(S, V, sway):
        s = max(0.0, min(1.0, S / SLEN))
        h = height(s)
        return wall(s, V / h, sway)

    # --- wall lace: Poisson sites, denser near the root (almost solid there), big holes toward the rim
    inside_w = lambda q: 0.0 <= q[0] <= SLEN and 0.0 <= q[1] <= Hm(q[0])  # noqa: E731
    base_sites = poisson(rng, 5000, lambda q: 0.0 <= q[0] <= SLEN and 0.0 <= q[1] <= height(q[0] / SLEN) * 1.12,
                         lambda: (rng.uniform(-0.02, SLEN + 0.02), rng.uniform(0.0, 0.95)),
                         lambda q: 0.065 + 0.12 * min(1.0, q[1] / max(0.05, height(min(1.0, max(0.0, q[0] / SLEN))))))
    sites = []
    for (S, V) in base_sites:
        a, b = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
        sites.append((S + 0.011 * math.sin(tw + a), V + 0.009 * math.sin(tw + b)))
    # far ring of sites so the Voronoi cells close at the borders
    for k in range(40):
        S = -0.3 + (SLEN + 0.6) * k / 39
        sites.append((S, -0.25))
        sites.append((S, 1.2))
    for k in range(12):
        V = -0.25 + 1.45 * k / 11
        sites.append((-0.3, V))
        sites.append((SLEN + 0.3, V))
    edge_rng = random.Random(SEED + 7)
    joints = set()
    for (p, q) in voronoi_edges(sites, inside_w):
        S0, V0 = p
        S1, V1 = q
        L = math.hypot(S1 - S0, V1 - V0)
        if L < 0.004:
            continue
        mid_s = max(0.0, min(1.0, 0.5 * (S0 + S1) / SLEN))
        vf = min(1.0, 0.5 * (V0 + V1) / max(0.05, Hm(0.5 * (S0 + S1))))
        r = (0.024 - 0.008 * vf) * (0.55 + 0.45 * taper(mid_s)) * edge_rng.uniform(0.8, 1.25)
        n = max(1, int(math.ceil(L / 0.035)))
        sway = 0.02 * math.sin(tw + mid_s * 6.0)
        pts = [to3d(S0 + (S1 - S0) * k / n, V0 + (V1 - V0) * k / n, sway) for k in range(n + 1)]
        E.chain(pts, [r] * (n + 1))
        # fused, slightly swollen joints where three strands meet (milk lace look)
        for (Sj, Vj), pj in ((p, pts[0]), (q, pts[-1])):
            key = (round(Sj, 3), round(Vj, 3))
            if key not in joints and 0.003 < Vj < Hm(Sj) - 0.003:
                joints.add(key)
                E.ball(pj, r * edge_rng.uniform(1.25, 1.6))

    # --- thick solid root where the sheet leaves the water + rim with beads
    nb = 36
    root_pts = [wall(k / nb, 0.0) + Vector((0, 0, 0.012)) for k in range(nb + 1)]
    E.chain(root_pts, [0.016 * taper(k / nb) + 0.012 for k in range(nb + 1)])
    low_pts = [wall(k / nb, 0.12) for k in range(nb + 1)]
    E.chain(low_pts, [0.012 * taper(k / nb) + 0.006 for k in range(nb + 1)])
    nr = 44
    rim_on = [edge_rng.random() > 0.18 for _ in range(nr)]
    for k in range(nr):
        if not rim_on[k]:
            continue
        s0, s1 = k / nr, (k + 1) / nr
        a = wall(s0, top(s0), 0.02 * math.sin(tw + s0 * 6.0))
        b = wall(s1, top(s1), 0.02 * math.sin(tw + s1 * 6.0))
        E.cap(a, b, 0.016 * (0.5 + 0.5 * taper(0.5 * (s0 + s1))))
    for k in range(13):                              # beads sitting on the rim
        s = (k + edge_rng.uniform(0.2, 0.8)) / 13
        E.ball(wall(s, top(s), 0.02 * math.sin(tw + s * 6.0)), edge_rng.uniform(0.02, 0.03) * (0.6 + 0.4 * taper(s)))

    # --- lace skirt lying on the water: spreads outward and back toward the camera from the root
    def W(s):
        return 0.10 + 0.42 * s

    def skirt_xy(s, d):
        b = base(s)
        o = outward(s)
        return Vector((b.x + o.x * d, b.y + o.y * d, 0.006))

    def inside_k(q):
        s, d = q[0] / SLEN, q[1]
        return 0.03 <= s <= 1.0 and 0.0 <= d <= W(s) * (0.85 + 0.15 * math.sin(s * 9.0 + tw))

    sk_sites = poisson(rng, 2500, lambda q: -0.02 <= q[0] <= 1.05 * SLEN and -0.02 <= q[1] <= W(q[0] / SLEN) + 0.05,
                       lambda: (rng.uniform(0.0, 1.05 * SLEN), rng.uniform(-0.02, 0.6)),
                       lambda q: 0.09 + 0.07 * q[0] / SLEN)    # ~9-16 cm cells
    sk = []
    for (S, d) in sk_sites:
        a = rng.uniform(0, 6.28)
        sk.append((S + 0.01 * math.sin(tw + a), d + 0.012 * math.cos(tw + a * 1.3)))
    for k in range(30):
        S = -0.25 + (SLEN + 0.5) * k / 29
        sk.append((S, -0.3))
        sk.append((S, 1.0))
    for k in range(8):
        d = -0.3 + 1.3 * k / 7
        sk.append((-0.25, d))
        sk.append((SLEN + 0.25, d))
    for (p, q) in voronoi_edges(sk, inside_k):
        s0, d0 = p[0] / SLEN, p[1]
        s1, d1 = q[0] / SLEN, q[1]
        L = math.hypot(q[0] - p[0], d1 - d0)
        if L < 0.004:
            continue
        r = 0.016 * edge_rng.uniform(0.8, 1.3) * (1.0 - 0.35 * (0.5 * (d0 + d1)) / max(0.1, W(0.5 * (s0 + s1))))
        n = max(1, int(math.ceil(L / 0.05)))
        pts = [skirt_xy(s0 + (s1 - s0) * k / n, d0 + (d1 - d0) * k / n) for k in range(n + 1)]
        E.chain(pts, [r] * (n + 1))

    # --- tendrils from the rim: grow, pinch off a droplet, retract (periodic life cycle per tendril)
    nt = 11
    for j in range(nt):
        s0 = 0.04 + 0.86 * (j + rng.uniform(0.2, 0.8)) / nt
        phase = rng.uniform(0, 1)
        lmax = rng.uniform(0.1, 0.24) * (0.6 + 0.8 * math.exp(-((s0 - 0.28) / 0.35) ** 2))
        out = Vector((rng.uniform(0.2, 0.9), rng.uniform(-0.1, 0.5), 1.0)).normalized()
        out = (out + LEAN * 0.6).normalized()
        r_root = rng.uniform(0.014, 0.02)
        r_tip = rng.uniform(0.022, 0.032)
        age = (tau + phase) % 1.0
        grow = smoothstep(0.0, 0.5, age) * (1.0 - smoothstep(0.62, 1.0, age))
        root = wall(s0, top(s0) * 0.98, 0.0)
        L = lmax * grow
        if L > 0.015:
            pts, rad = [], []
            n = 6
            for k in range(n + 1):
                t = k / n
                bend = Vector((0.06 * t * t, 0.03 * t * t, -0.05 * t * t))
                pts.append(root + out * (L * t) + bend * (L / 0.2))
                rad.append(lerp(r_root, r_root * 0.55, t) * min(1.0, grow * 1.6))
            E.chain(pts, rad)
            E.ball(pts[-1] + out * 0.01, r_tip * min(1.0, grow * 1.4))
        if age > 0.5:
            a = (age - 0.5) / 0.5
            tip = root + out * lmax
            vel = out * 0.55 + Vector((0.15, 0.25, 0.25))
            p = tip + vel * a * 0.35 + Vector((0, 0, -0.9 * a * a * 0.35))
            E.ball(p, r_tip * 0.95 * (1.0 - a) ** 0.5)

    # --- loose droplets on ballistic arcs (periodic)
    for j in range(20):
        s0 = rng.uniform(0.03, 0.9)
        phase = rng.uniform(0, 1)
        r0 = rng.uniform(0.012, 0.026)
        vel = Vector((rng.uniform(0.3, 1.0), rng.uniform(0.0, 0.8), rng.uniform(0.5, 1.1)))
        age = (tau + phase) % 1.0
        start = wall(s0, rng.uniform(0.6, 1.0), 0.0)
        tt = age * 0.4
        p = start + vel * tt + Vector((0, 0, -4.9 * tt * tt))
        if p.z > 0.01:
            E.ball(p, r0 * math.sin(math.pi * age) ** 0.5)
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
    C.render_preview(C.preview_path("FX_SplashCrown"), camera_location=(0.35, 5.6, 2.5), target=(0.35, 0.4, 0.25),
                     lens=38, resolution=(1280, 720), light_scale=1.6)
    print("DONE build_fx_splash")


if __name__ == "__main__":
    main()
