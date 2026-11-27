"""Screen S2 pass 10 (asset artist, owner 12:08 "rebuild cheap / inaccurate assets properly"): two master rebuilds.

1) SM_DoorHatch_s2 v3 (same name / LOD child names / asset frame as v2 in build_s2_door_p6.py, so SceneBuilder.Hall and
   CaptureTools find it unchanged; outer edge rho 6.98 kept = the Hall.cs pivot `hatchOuter`).
   Judge gap #1 (s2p9): the approved frame shows a MASSIVE thick glossy gold torus framing the left (x ~240-330) and right
   (x ~1180-1280) with big warm bulbs on its flanks and only a narrow violet inner rim with a bright crest; ours (v2) =
   a 1.1 m wide flat-lit violet torus (right side 1075-1270 px) inside a 1 m shallow gold band (bulge 0.30 m), no gold on
   the right of the frame. Crop 06 (entrance arch): fat rounded gold torus, darker bronze inner flank, bright outer crest,
   big bulbs on the outer band. v3 profile (rho, h; h = toward the player):
     violet inner rim   rho 4.18-4.98, rounded D, crest h 0.32 (0.8 m wide, was 1.1) + a thin pale CREST bead (new slot
                        M_HatchCrest_s2) on its crest = the bright highlight line of the reference
     bronze groove      rho 4.92-5.16 (dark gold shadow line between violet and gold)
     main gold torus    ellipse section rho 5.07-6.03, h -0.40..+0.75 (fat, round: strong curved highlights)
     bronze groove      rho 5.98-6.14
     bulb band          rho 6.08-6.78, convex front h <= 0.48, 16 BIG warm bulbs (r .26) in deep gold sockets + collars
     flange             stepped bevelled dark-gold flange rho 6.74-6.98 back to h -1.0 + 64 bolt heads
   = gold starts 0.55 m further in than v2 (right flank gold enters the frame), violet narrower, gold depth 1.15 m.
2) SM_RollerDrum_s2 v2 (same name / LOD names / asset frame as p9: axis X, 2.62 m, hub end +X): judge gap #2 "fringed
   pink DONUT with a hole; ref = large dense fluffy pink shaggy brush, white tips, no background through it". v2 = closed
   capsule core + CLUMPS of 6 curved strands (root -> bent mid -> tip, swept back tangentially, tips flaring) covering the
   cylinder AND both rounded end domes (the end R2 sees is a fluffy hemisphere, not an annulus), longer strands
   (0.50-0.82 m), pink-dominant bands with light tips. LOD0 ~70k tris (< 65k verts), LOD1 single spikes ~17k.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_p10.py s2_p10
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bwk_common as C  # noqa: E402

_DP = os.path.join(HERE, "build_s2_door_p6.py")
_DSRC = open(_DP, encoding="utf-8").read().rstrip()
assert _DSRC.endswith("main()")
D = {"__name__": "bwk_door_p6", "__file__": _DP}
exec(compile(_DSRC[: -len("main()")], _DP, "exec"), D)
MB, lathe, circle_prof, ellipsoid_prof, ring_points, compact = (D[k] for k in ("MB", "lathe", "circle_prof", "ellipsoid_prof",
                                                                                 "ring_points", "compact"))
GOLD, GDARK, VIOLET, BULB, LED, CREST = range(6)
TAU = 2.0 * math.pi
AXIS = (0.0, 1.0, 0.0)


def ellipse_prof(rc, hc, a, b, n):
    return [(rc + a * math.cos(TAU * k / n), hc + b * math.sin(TAU * k / n)) for k in range(n)]


def build_hatch_v3(q):
    mb = MB()
    seg = 176 if q else 64
    # narrow glossy violet inner rim, rounded crest in front (h .32), rolling back into the drum
    rim = [(4.18, -0.95), (4.98, -0.95), (4.98, -0.35), (4.95, -0.06), (4.89, 0.12), (4.79, 0.24), (4.66, 0.31),
           (4.52, 0.32), (4.39, 0.27), (4.29, 0.14), (4.22, -0.08), (4.19, -0.45)]
    lathe(mb, rim, VIOLET, seg, axis=AXIS, closed=True)
    # bright crest bead along the violet crest (the reference's highlight line)
    lathe(mb, circle_prof(4.56, 0.045, 0.335, 8 if q else 4), CREST, seg, axis=AXIS, closed=True)
    # dark bronze groove between violet and gold
    lathe(mb, circle_prof(5.04, 0.12, 0.02, 12 if q else 6), GDARK, seg, axis=AXIS, closed=True)
    # main fat rounded gold torus (ellipse section: round front, deep back)
    lathe(mb, ellipse_prof(5.55, 0.17, 0.48, 0.58, 28 if q else 12), GOLD, seg, axis=AXIS, closed=True)
    # second bronze groove
    lathe(mb, circle_prof(6.06, 0.08, 0.16, 10 if q else 5), GDARK, seg, axis=AXIS, closed=True)
    # outer bulb band: flat back, convex front (h <= .48)
    front = []
    for k in range(13):
        t = k / 12.0
        front.append((6.78 - 0.70 * t, 0.06 + 0.42 * math.sin(math.pi * t) ** 0.7))
    band = [(6.08, -0.55), (6.78, -0.55)] + front + [(6.08, -0.20)]
    lathe(mb, band, GOLD, seg, axis=AXIS, closed=True)
    # stepped bevelled dark-gold flange to the wall (outer edge rho 6.98 = Hall.cs hatchOuter)
    flange = [(6.70, -1.00), (6.98, -1.00), (6.98, -0.42), (6.95, -0.30), (6.88, -0.24), (6.86, -0.10), (6.82, -0.02),
              (6.76, 0.02), (6.72, -0.20)]
    lathe(mb, flange, GDARK, seg, axis=AXIS, closed=True)
    # 64 bolt heads on the flange step
    if q:
        for x, z in ring_points(6.91, 64, 0.25):
            lathe(mb, ellipsoid_prof(0.040, 0.030, 4), GOLD, 8, origin=(x, -0.24, z), axis=AXIS)
    # 16 BIG warm bulbs in deep gold sockets with a collar on the bulb band crest (rho 6.43, h ~.48)
    sock = [(0.0, -0.04), (0.33, -0.04), (0.34, 0.05), (0.31, 0.13), (0.27, 0.15), (0.25, 0.08), (0.0, 0.08)]
    collar = circle_prof(0.285, 0.035, 0.15, 8 if q else 4)
    for x, z in ring_points(6.43, 16):
        lathe(mb, sock, GDARK, 24 if q else 10, origin=(x, 0.40, z), axis=AXIS)
        if q:
            lathe(mb, collar, GOLD, 24, origin=(x, 0.40, z), axis=AXIS, closed=True)
        lathe(mb, ellipsoid_prof(0.255, 0.20, 10 if q else 4), BULB, 20 if q else 8, origin=(x, 0.53, z), axis=AXIS)
    return mb


def hatch_materials():
    return [C.material("M_Gold", "#E8B04A", 1.0, 0.18),
            C.material("M_GoldDark", "#B8782C", 1.0, 0.25),
            C.material("M_HatchViolet_s2", "#6A36C8", 0.35, 0.16),
            C.material("M_Bulb", "#FFB060", 0.0, 0.2, emission="#FF9A40", emission_strength=6.0),
            C.material("M_RimLight", "#FF6AD0", 0.0, 0.3, emission="#FF4FC4", emission_strength=5.0),
            C.material("M_HatchCrest_s2", "#E8C8FF", 0.3, 0.12, emission="#C8A0FF", emission_strength=1.5)]


def export_hatch():
    mats = hatch_materials()
    b0, b1 = build_hatch_v3(1), build_hatch_v3(0)
    m0, m1 = compact(b0, mats), compact(b1, mats)
    lod0 = b0.build("DoorHatch_LOD0", m0)
    lod1 = b1.build("DoorHatch_LOD1", m1)
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    d = lod0.dimensions
    print("CHECK SM_DoorHatch_s2 v3 tris LOD0 %d LOD1 %d (%.0f %%) dims %.2f x %.2f x %.2f verts %d"
          % (t0, t1, 100.0 * t1 / t0, d.x, d.y, d.z, len(lod0.data.vertices)))
    lod1.hide_render = True
    for tag, cam, tgt, lens in (("", (1.2, 8.3, -1.0), (-0.8, 0.0, 0.6), 18.0),          # ~R2
                                ("_side", (-9.5, 3.0, 1.5), (-5.6, 0.0, 0.5), 30.0),   # side / grazing: solid depth
                                ("_top", (0.0, 4.0, 10.5), (0.0, 0.0, 5.6), 28.0)):    # from above
        try:
            p = C.preview_path("SM_DoorHatch_s2" + tag)
            C.render_preview(p, camera_location=cam, target=tgt, lens=lens, resolution=(1000, 700))
        except Exception as e:  # noqa: BLE001
            print("CHECK preview failed:", e)
    lod1.hide_render = False
    root = bpy.data.objects.new("SM_DoorHatch_s2", None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lod0, lod1):
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_DoorHatch_s2"))
    return root, lod0, lod1


# ------------------------------------------------------------------ roller drum v2
PINK, PTIP, WHITE, CYAN = range(4)
L = 2.62
BANDS = [("p", 0.80), ("w", 0.20), ("p", 0.34), ("c", 0.18), ("p", 0.46), ("w", 0.20), ("p", 0.44)]
CORE_R, CORE_X = 0.80, 1.15


def band_at(x):
    x0 = -L / 2
    for key, w in BANDS:
        if x < x0 + w:
            return key
        x0 += w
    return BANDS[-1][0]


class Mesh:
    def __init__(self):
        self.co, self.faces, self.fmat = [], [], []

    def v(self, p):
        self.co.append(Vector(p))
        return len(self.co) - 1


def core(m, seg):
    prof = [(-1.30, 0.0), (-1.29, 0.30), (-1.26, 0.55), (-1.20, 0.74), (-CORE_X, CORE_R), (CORE_X, CORE_R), (1.20, 0.74),
            (1.26, 0.55), (1.29, 0.30), (1.30, 0.0)]
    rings = []
    for x, r in prof:
        if r == 0.0:
            rings.append([m.v((x, 0.0, 0.0))])
            continue
        rings.append([m.v((x, r * math.cos(TAU * k / seg), r * math.sin(TAU * k / seg))) for k in range(seg)])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            k1 = (k + 1) % seg
            if len(a) == 1:
                m.faces.append([a[0], b[k1], b[k]])
            elif len(b) == 1:
                m.faces.append([a[k], a[k1], b[0]])
            else:
                m.faces.append([a[k], a[k1], b[k1], b[k]])
            m.fmat.append(PINK)


def frame(d):
    e1 = d.orthogonal().normalized()
    return e1, d.cross(e1).normalized()


def strand(m, root, d, bend, length, w0, key, sides, blunt=False):
    """curved strand: root ring -> mid ring (bent by `bend`) -> tip point. sides 3 (LOD0) / 4 (LOD1).
    pass 10 v3 (blunt=True, s2p10 R2: the pointed 3-sided spikes read as a dark spiky starburst with the violet wall
    between them; crop 02 = soft THICK locks with rounded pale tips): root -> mid (.86 w) -> blunt tip ring (.5 w) + cap."""
    mid = root + d * (length * 0.62)
    tip = mid + (d + bend).normalized() * (length * 0.38)
    dm = (tip - root).normalized()
    root_mat = {"p": PINK, "w": WHITE, "c": CYAN}[key]
    tip_mat = {"p": PTIP, "w": WHITE, "c": CYAN}[key]
    if blunt:
        dt = (tip - mid).normalized()
        rings = []
        for c, w, dd in ((root, w0, d), (mid, w0 * 0.86, dm), (tip, w0 * 0.5, dt)):
            e1, e2 = frame(dd)
            rings.append([m.v(c + (e1 * math.cos(TAU * k / sides) + e2 * math.sin(TAU * k / sides)) * w) for k in range(sides)])
        r0, r1, r2 = rings
        for k in range(sides):
            k1 = (k + 1) % sides
            m.faces.append([r0[k], r0[k1], r1[k1], r1[k]])
            m.fmat.append(root_mat)
            m.faces.append([r1[k], r1[k1], r2[k1], r2[k]])
            m.fmat.append(tip_mat)
        m.faces.append(list(r2))
        m.fmat.append(tip_mat)
        return
    rings = []
    for c, w, dd in ((root, w0, d), (mid, w0 * 0.72, dm)):
        e1, e2 = frame(dd)
        rings.append([m.v(c + (e1 * math.cos(TAU * k / sides) + e2 * math.sin(TAU * k / sides)) * w) for k in range(sides)])
    t = m.v(tip)
    r0, r1 = rings
    for k in range(sides):
        k1 = (k + 1) % sides
        m.faces.append([r0[k], r0[k1], r1[k1], r1[k]])
        m.fmat.append(root_mat)
        m.faces.append([r1[k], r1[k1], t])
        m.fmat.append(tip_mat)


def sample_surface(rnd):
    """area-uniform point on the capsule core: (root, outward normal, tangent around the axis, x)."""
    cyl = 2 * CORE_X * TAU * CORE_R
    cap = 2 * TAU * CORE_R * CORE_R * 0.8  # flattened hemispheres
    if rnd.random() < cyl / (cyl + cap):
        x = rnd.uniform(-CORE_X, CORE_X)
        a = rnd.uniform(0.0, TAU)
        n = Vector((0.0, math.cos(a), math.sin(a)))
        return Vector((x, 0.0, 0.0)) + n * (CORE_R - 0.04), n, Vector((0.0, -math.sin(a), math.cos(a))), x
    s = rnd.choice((-1.0, 1.0))
    th = math.acos(rnd.uniform(0.0, 1.0))          # 0 = axis pole, pi/2 = rim
    a = rnd.uniform(0.0, TAU)
    n = Vector((s * math.cos(th), math.sin(th) * math.cos(a), math.sin(th) * math.sin(a))).normalized()
    root = Vector((s * CORE_X, 0.0, 0.0)) + Vector((n.x * 0.15 / 0.8, n.y, n.z)) * (CORE_R - 0.05)
    tang = Vector((0.0, -math.sin(a), math.cos(a)))
    return root, n, tang, s * (CORE_X + 0.1)


def build_roller(n_clumps, per, seed, seg, sides, wscale=1.0, blunt=False):
    rnd = random.Random(seed)
    m = Mesh()
    core(m, seg)
    for _ in range(n_clumps):
        root, n, tang, x = sample_surface(rnd)
        key = band_at(max(-L / 2 + 0.01, min(L / 2 - 0.01, x)))
        on_end = abs(x) > CORE_X
        length = rnd.uniform(0.50, 0.82) * (0.85 if on_end else 1.0)
        base = (n + tang * rnd.uniform(-0.22, 0.05)).normalized()
        sweep = tang * rnd.uniform(-0.55, -0.15) + n * 0.15        # swept back + a soft flop at the tips
        for i in range(per):
            jit = Vector((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06)))
            d = (base + Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12)))).normalized()
            bend = sweep + Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25)))
            w0 = rnd.uniform(0.034, 0.052) * (1.6 if per == 1 else 1.0) * wscale
            strand(m, root + jit, d, bend, length * rnd.uniform(0.8, 1.15), w0, key, sides, blunt)
    return m


def make(name, m, mats):
    me = bpy.data.meshes.new(name)
    me.from_pydata([c[:] for c in m.co], [], m.faces)
    me.validate()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    C.assign_materials(obj, mats)
    me.polygons.foreach_set("material_index", m.fmat)
    me.uv_layers.new(name="UVMap")
    me.shade_smooth()
    return obj


def export_roller():
    mats = [C.material("M_BristlePink_s2", "#E2368C", 0.0, 0.55),
            C.material("M_BristlePinkTip_s2", "#FF8CC8", 0.0, 0.5),
            C.material("M_BristleWhite_s2", "#FFF0FA", 0.0, 0.5),
            C.material("M_BristleCyan_s2", "#7CD0F4", 0.0, 0.5)]
    # v3 (pass 10 resume 13:50, lead "thicker clumps"): 1200 clumps x 5 THICK blunt locks (1.45x wider, rounded pale
    # tips) = ~78k tris LOD0 instead of 1350 x 6 thin pointed spikes (the violet wall showed between them)
    lod0 = make("RollerDrum_LOD0", build_roller(1200, 5, 31, 40, 3, wscale=1.45, blunt=True), mats)
    lod1 = make("RollerDrum_LOD1", build_roller(1700, 1, 37, 16, 4, wscale=1.2), mats)
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    d = lod0.dimensions
    print("CHECK SM_RollerDrum_s2 v2 tris LOD0 %d LOD1 %d verts LOD0 %d dims %.2f x %.2f x %.2f"
          % (t0, t1, len(lod0.data.vertices), d.x, d.y, d.z))
    lod1.hide_render = True
    for tag, cam in (("", (2.0, -5.5, 1.4)), ("_end", (-5.2, -2.6, 1.0))):
        try:
            C.render_preview(C.preview_path("SM_RollerDrum_s2" + tag), camera_location=cam, target=(0.0, 0.0, 0.0),
                             lens=40.0, resolution=(900, 600))
        except Exception as e:  # noqa: BLE001
            print("CHECK preview failed:", e)
    lod1.hide_render = False
    root = bpy.data.objects.new("SM_RollerDrum_s2", None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lod0, lod1):
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_RollerDrum_s2"))
    return root, lod0, lod1


def main():
    C.reset_scene()
    if not os.environ.get("P10_ROLLER_ONLY"):
        r, h0, h1 = export_hatch()
        for o in (r, h0, h1):
            o.hide_render = True
            o.hide_viewport = True
    export_roller()
    C.save_work("s2_p10.blend")
    print("DONE")


main()
