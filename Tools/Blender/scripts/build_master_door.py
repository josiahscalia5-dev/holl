"""Round 8 MASTER-ASSET wave (asset artist, 2026-11-26): ONE premium master washing-machine door = library assets 11 + 12.

Built from scratch (no v2 geometry reused) from Reference/asset_library 11 (ornate gold sock chamber) + 12 (colourful socks
and rainbow insert), 4K frames 7-11 s. Real-world metres, Blender front = -Y (FRONT), up = +Z, hinge on the viewer's LEFT
(-X) and latch on the right (+X) like SM_ChamberWindow_v2, so SceneBuilder.Environment.cs keeps its placement / mirroring.
  frame    thick polished gold band: lathed multi-step rounded profile (outer rope lip, cove, big bead apex h 0.25,
           inner cove, inner ring bead, dark inner lip), outer r 2.36 / glass r 1.70; 16 domed bolts on the bead apex,
           36 small ornate studs on the outer lip, two baroque scrolls beside the hinge
  hinge    REAL hinge: 3-knuckle barrel with dark knuckle gaps and ball finials, two bolted straps over the bead, a deep
           wall bracket; latch = mount block + swept C-grip + keeper
  chamber  GENUINE recess: drum cylinder (0.33 m) + bowl back (0.62 m at the centre) behind a glass disc with thickness
           (domed front, flat back, rim); lavender housing cylinder 1.1 m deep (hides the gap to the curved tunnel wall)
  interior 7 glossy raised rainbow arches (half-round bands following the bowl, vertex colours) around a dark inner drum
           with a lavender lip (reference: rainbow wraps the dark drum, centre toward the latch side), turquoise water
           pool, soft foam lumps piled at the bottom + floating suds
  socks    5 separate 3D socks (sweep: ribbed cuff, leg, heel bend + bulge, flattened foot, toe cap; stripes / heel / toe /
           cuff in vertex colours): blue, orange, green, yellow-orange, purple
LOD1 (~40 % of LOD0) = same construction with fewer segments and no studs / bolts reduced. Vertex colours are stored
LINEAR (the BWK/Soft shaders read them as linear albedo).
Exports: Assets/BubbleWashKingdom/Art/Models/Machinery/SM_WashDoor_Master.fbx (root SM_WashDoor_Master: WashDoor_LOD0,
WashDoor_LOD1, Sock_0..4). Slots = Unity material names: M_Gold, M_GoldDark, M_Glass, M_ChamberDrum, M_DrumRim, M_Foam,
M_DoorRainbow_r8 (LOD meshes), M_DoorSock_r8 (socks).
Kit parts (Asset Browser-marked) -> Tools/Blender/library/BWK_Kit.blend (merged with what is already there).
Review renders (no reference pixels) -> BWK_DOOR_REVIEW (default Captures/agents/assets/r8m): door_ref_angle.png,
door_rear_angle.png, door_front.png; preview Docs/AssetPreviews/SM_WashDoor_Master.png.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_master_door.py master_door
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from mathutils import Vector, Euler  # noqa: E402

import bwk_common as C  # noqa: E402

# build_machinery helpers (MB, lathe, sweep, ...) WITHOUT running its main(): exec the source minus the last call
_MP = os.path.join(HERE, "build_machinery.py")
_SRC = open(_MP, encoding="utf-8").read().rstrip()
assert _SRC.endswith("main()")
BM = {"__name__": "bwk_machinery_helpers", "__file__": _MP}
exec(compile(_SRC[: -len("main()")], _MP, "exec"), BM)
MB, lathe, sweep, path_frames, circle2 = BM["MB"], BM["lathe"], BM["sweep"], BM["path_frames"], BM["circle2"]
catmull_rom, rounded_box = BM["catmull_rom"], BM["rounded_box"]
X_AXIS, Y_AXIS, Z_AXIS, FRONT, TAU = BM["X_AXIS"], BM["Y_AXIS"], BM["Z_AXIS"], BM["FRONT"], BM["TAU"]

ROOT = C.ROOT
REVIEW = os.environ.get("BWK_DOOR_REVIEW", os.path.join(ROOT, "Captures", "agents", "assets", "r8m"))
KIT = os.path.join(ROOT, "Tools", "Blender", "library", "BWK_Kit.blend")
NOEXPORT = os.environ.get("BWK_DOOR_NOEXPORT") == "1"

GLASS_R = 1.70          # glass / drum radius
DRUM_D = 0.36           # drum cylinder depth behind the glass plane
SLOTS = ["M_Gold", "M_GoldDark", "M_Glass", "M_ChamberDrum", "M_DrumRim", "M_Foam", "M_DoorRainbow_r8"]
G, GD, GL, DR, RIM, FM, RB = range(7)


def lin(hex_color):
    r, g, b, a = C.hex_rgba(hex_color)
    return (r, g, b, 1.0)


def arc(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def P(x, h, z):
    """door point: x right, h toward the viewer (Blender -Y), z up"""
    return Vector((x, -h, z))


# ================================================================== frame
def frame_profile(q):
    n_big = 14 if q else 8
    n_sm = 4 if q else 2
    prof, mats = [], []

    def add(points, m):
        for p in points:
            if prof and abs(prof[-1][0] - p[0]) < 1e-6 and abs(prof[-1][1] - p[1]) < 1e-6:
                continue
            prof.append(p)
            mats.append(m)
    add([(1.70, -0.12), (2.29, -0.12)], GD)                       # flat back
    add(arc(2.29, -0.065, 0.055, 0.055, -90, 0, n_sm), GD)        # back outer fillet
    add([(2.345, -0.01)], G)
    add(arc(2.30, 0.0, 0.05, 0.055, 0, 180, n_sm * 2), G)         # outer rope lip (apex h 0.055)
    add(arc(2.225, 0.0, 0.025, 0.03, 0, -180, n_sm), GD)          # cove (contact darkening)
    add(arc(2.005, 0.0, 0.195, 0.25, 0, 180, n_big), G)           # BIG rounded bead (apex h 0.25)
    add(arc(1.795, 0.0, 0.015, 0.02, 0, -180, n_sm), GD)          # inner cove
    add(arc(1.745, 0.0, 0.035, 0.065, 0, 180, n_sm * 2), G)       # inner ring bead next to the glass
    add([(1.70, -0.035)], GD)                                     # dark inner lip down to the back
    # material of segment i (prof[i] -> prof[i+1]); the closing segment (last -> first) = GD
    seg = mats[1:] + [GD]
    return prof, seg


def build_frame(mb, q):
    prof, seg = frame_profile(q)
    lathe(mb, prof, G, 96 if q else 40, (0, 0, 0), FRONT, X_AXIS, closed=True, mats=seg)


def build_bolts(mb, q):
    bolt = [(0.048, -0.03), (0.048, 0.004), (0.038, 0.024), (0.02, 0.034), (0.0, 0.037)]
    ks = range(16) if q else range(0, 16, 2)
    for k in ks:
        phi = math.radians(11.25 + 22.5 * k)
        c = P(2.005 * math.cos(phi), 0.238, 2.005 * math.sin(phi))
        lathe(mb, bolt, G, 10 if q else 6, c, FRONT, X_AXIS)


def build_studs(mb, q):
    if not q:
        return
    ball = [(0.0, -0.03), (0.022, -0.022), (0.03, 0.0), (0.022, 0.022), (0.0, 0.03)]
    for k in range(36):
        phi = math.radians(5.0 + 10.0 * k)
        if abs(math.degrees(phi) - 180.0) < 22 or (math.degrees(phi) < 12 or math.degrees(phi) > 348):
            continue                                                 # hinge / latch
        c = P(2.30 * math.cos(phi), 0.062, 2.30 * math.sin(phi))
        lathe(mb, ball, G, 6, c, FRONT, X_AXIS)


def build_scrolls(mb, q):
    scroll = [(1.47, 0.00), (1.60, 0.02), (1.72, 0.10), (1.80, 0.22), (1.80, 0.34), (1.73, 0.42), (1.64, 0.42),
              (1.59, 0.36), (1.60, 0.29), (1.66, 0.27), (1.70, 0.31)]
    ball = [(0.0, -0.05), (0.04, -0.035), (0.055, 0.0), (0.04, 0.035), (0.0, 0.05)]
    for th_deg, sgn in ((140.0, -1.0), (220.0, 1.0)):
        th = math.radians(th_deg)
        er = Vector((math.cos(th), 0.0, math.sin(th)))
        et = Vector((-math.sin(th), 0.0, math.cos(th))) * sgn
        sc = 1.25
        pts = catmull_rom([er * (2.22 + (a - 1.47) * sc) + et * (b * sc) + Vector((0.0, -0.05, 0.0))
                           for a, b in scroll], 3 if q else 1)
        n = len(pts)
        tr = 0.07
        profs = [circle2(tr - tr * 0.5 * i / (n - 1), 8 if q else 5) for i in range(n)]
        sweep(mb, path_frames(pts, lambda i: Y_AXIS), None, G, closed_prof=True, profs=profs, swap_uv=True)
        lathe(mb, ball, G, 8 if q else 5, pts[-1], (pts[-1] - pts[-2]).normalized())


def build_hinge(mb, q):
    """real hinge on the viewer's left: knuckle barrel + ball finials, bolted straps over the bead, wall bracket"""
    hx, hh = -2.64, 0.27
    barrel = [(0.0, -0.64), (0.045, -0.635), (0.07, -0.61), (0.078, -0.58), (0.06, -0.55), (0.05, -0.535),
              (0.11, -0.52), (0.122, -0.50), (0.122, -0.19), (0.112, -0.175), (0.092, -0.17), (0.092, -0.15),
              (0.112, -0.145), (0.122, -0.13), (0.122, 0.13), (0.112, 0.145), (0.092, 0.15), (0.092, 0.17),
              (0.112, 0.175), (0.122, 0.19), (0.122, 0.50), (0.11, 0.52), (0.05, 0.535), (0.06, 0.55),
              (0.078, 0.58), (0.07, 0.61), (0.045, 0.635), (0.0, 0.64)]
    bm = [G, G, G, G, GD, GD, G, G, G, GD, GD, GD, G, G, G, GD, GD, GD, G, G, G, GD, GD, G, G, G, G]
    lathe(mb, barrel, G, 20 if q else 10, P(hx, hh, 0.0), Z_AXIS, X_AXIS, mats=bm)
    # bolted straps from the bead to the barrel (z +-0.33)
    for zz in (-0.33, 0.33):
        rounded_box(mb, P(-2.30, 0.27, zz), (0.66, 0.075, 0.20), 0.032, 2 if q else 1, G)
        for xx in (-2.08, -2.40):
            lathe(mb, [(0.036, -0.02), (0.036, 0.004), (0.028, 0.018), (0.0, 0.026)], GD, 8 if q else 5,
                  P(xx, 0.305, zz), FRONT, X_AXIS)
    # wall bracket behind the barrel, deep into the tunnel wall
    rounded_box(mb, P(hx - 0.02, -0.30, 0.0), (0.20, 1.10, 0.92), 0.04, 2 if q else 1, GD)


def build_latch(mb, q):
    rounded_box(mb, P(2.06, 0.24, 0.0), (0.22, 0.12, 0.62), 0.045, 2 if q else 1, G)       # mount block on the bead
    path = catmull_rom([P(2.12, 0.30, 0.27), P(2.38, 0.40, 0.25), P(2.48, 0.42, 0.0), P(2.38, 0.40, -0.25),
                        P(2.12, 0.30, -0.27)], 4 if q else 2)
    sweep(mb, path_frames(path, lambda i: Y_AXIS), circle2(0.048, 10 if q else 6), G, closed_prof=True,
          swap_uv=True, cap0=True, cap1=True)
    for zz in (0.27, -0.27):
        lathe(mb, [(0.0, -0.05), (0.06, -0.04), (0.075, 0.0), (0.06, 0.04), (0.0, 0.05)], G, 10 if q else 6,
              P(2.12, 0.30, zz), FRONT, X_AXIS)
    rounded_box(mb, P(2.58, -0.05, 0.0), (0.16, 0.50, 0.34), 0.04, 2 if q else 1, GD)        # keeper on the wall


# ================================================================== glass, chamber, housing
def bowl_h(rho):
    """depth of the drum back (h, negative) at distance rho from the axis"""
    pts = [(GLASS_R, -DRUM_D), (1.62, -0.46), (1.40, -0.53), (1.0, -0.58), (0.5, -0.61), (0.0, -0.62)]
    rho = min(max(rho, 0.0), GLASS_R)
    for (r0, h0), (r1, h1) in zip(pts, pts[1:]):
        if r1 <= rho <= r0:
            t = (rho - r1) / (r0 - r1)
            return h1 + (h0 - h1) * t
    return -0.62


def build_glass(mb, q):
    prof = [(0.0, -0.03), (GLASS_R + 0.012, -0.03), (GLASS_R + 0.012, 0.0)]
    for r in (1.45, 1.1, 0.7, 0.35):
        prof.append((r, 0.07 * (1.0 - (r / (GLASS_R + 0.012)) ** 2)))
    prof.append((0.0, 0.07))
    lathe(mb, prof, GL, 64 if q else 32, (0, 0, 0), FRONT, X_AXIS,
          uv_fn=lambda p: (0.5 + p.x / (2 * GLASS_R), 0.5 + p.z / (2 * GLASS_R)))


def build_chamber(mb, q):
    # drum cylinder + bowl back, normals facing the viewer / the axis
    prof = [(GLASS_R + 0.005, -0.03), (GLASS_R + 0.005, -0.20), (GLASS_R, -DRUM_D), (1.62, -0.46), (1.40, -0.53),
            (1.0, -0.58), (0.5, -0.61), (0.0, -0.62)]
    lathe(mb, prof, DR, 64 if q else 32, (0, 0, 0), FRONT, X_AXIS, u_span=6.0)
    # lavender housing cylinder behind the frame back (hides the gap to the curved wall)
    hous = [(2.30, -1.25), (2.30, -0.11)]
    lathe(mb, hous, RIM, 64 if q else 32, (0, 0, 0), FRONT, X_AXIS, u_span=6.0)


RAINBOW_C = (0.70, -0.15)       # rainbow / inner-drum centre (x, z): toward the latch side, slightly low
RAINBOW = ["#9A62E6", "#4A86F0", "#3FD0E0", "#7EDB5A", "#FFE04A", "#FF9A3D", "#FF5A8C"]   # inner -> outer


def build_interior(mb, q):
    cx, cz = RAINBOW_C
    # inner dark drum lip (lavender torus on the back wall) at radius 1.0 around the rainbow centre
    lip_pts = []
    for k in range(48 if q else 24):
        a = TAU * k / (48 if q else 24)
        x, z = cx + 1.0 * math.cos(a), cz + 1.0 * math.sin(a)
        rho = math.hypot(x, z)
        if rho > GLASS_R - 0.08:
            x, z = x * (GLASS_R - 0.08) / rho, z * (GLASS_R - 0.08) / rho
        lip_pts.append(P(x, bowl_h(math.hypot(x, z)) + 0.035, z))
    sweep(mb, path_frames(lip_pts, lambda i: FRONT, closed=True), circle2(0.05, 8 if q else 5), RIM,
          closed_path=True, closed_prof=True)
    # 7 raised glossy rainbow arches following the bowl (half-round, vertex colours), clipped by the drum wall
    step = 5.0 if q else 10.0
    prof = [(0.018 + 0.042 * math.cos(t), 0.05 * math.sin(t)) for t in
            [TAU * k / (10 if q else 6) for k in range(10 if q else 6)]]
    for b, hexc in enumerate(RAINBOW):
        R = 1.06 + 0.112 * b
        col = lin(hexc)
        run = []
        a = -60.0
        runs = []
        while a <= 240.0 + 1e-6:
            x = cx + R * math.cos(math.radians(a))
            z = cz + R * math.sin(math.radians(a))
            rho = math.hypot(x, z)
            if rho <= GLASS_R - 0.07 and z > -1.25:
                run.append(P(x, bowl_h(rho) + 0.008, z))
            else:
                if len(run) >= 3:
                    runs.append(run)
                run = []
            a += step
        if len(run) >= 3:
            runs.append(run)
        for pts in runs:
            sweep(mb, path_frames(pts, lambda i: FRONT), prof, RB, closed_prof=True, cap0=True, cap1=True,
                  col_fn=lambda p, c=col: c)
    # turquoise water pool at the bottom (glossy, vertex colour gradient), behind the foam
    cols = 28 if q else 14
    top, deep = lin("#8FE6F5"), lin("#2E9BD8")
    grid = []
    for i in range(cols + 1):
        x = -GLASS_R + 2 * GLASS_R * i / cols
        zt = -0.78 + 0.05 * math.sin(3.1 * x + 0.6)
        zb = -math.sqrt(max((GLASS_R - 0.01) ** 2 - x * x, 0.0))
        if zb >= zt - 0.02:
            grid.append(None)
            continue
        row = []
        for j in range(4):
            t = j / 3.0
            z = zt + (zb - zt) * t
            h = -0.30 - 0.06 * t
            c = tuple(top[k] + (deep[k] - top[k]) * t for k in range(3)) + (1.0,)
            row.append(mb.v(P(x, h, z), c))
        grid.append(row)
    for i in range(cols):
        a, b2 = grid[i], grid[i + 1]
        if a is None or b2 is None:
            continue
        for j in range(3):
            mb.f([a[j], b2[j], b2[j + 1], a[j + 1]], RB, [(i / cols, j / 3), ((i + 1) / cols, j / 3),
                                                         ((i + 1) / cols, (j + 1) / 3), (i / cols, (j + 1) / 3)],
                 ref=FRONT)


def lump(mb, c, r, sy, q, mat=FM):
    rings = 7 if q else 4
    segs = 12 if q else 7
    prof = [(r * math.sin(math.pi * k / rings), -r * sy * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    prof[0], prof[-1] = (0.0, prof[0][1]), (0.0, prof[-1][1])
    lathe(mb, prof, mat, segs, c, Z_AXIS, X_AXIS)


def build_foam(mb, q):
    rnd = random.Random(1107)
    # bank piled on the bottom of the drum, in front of the water
    n = 15 if q else 9
    for k in range(n):
        x = -1.42 + 2.84 * k / (n - 1) + rnd.uniform(-0.05, 0.05)
        zb = -math.sqrt(max(1.62 ** 2 - x * x, 0.0))
        r = rnd.uniform(0.20, 0.31)
        z = zb + r * 0.85 + rnd.uniform(0.0, 0.10)
        lump(mb, P(x, -0.17 - rnd.uniform(0.0, 0.06), z), r, 0.82, q)
    # second, higher row (soft crest)
    for k in range(7 if q else 4):
        x = -1.0 + 2.0 * k / (6 if q else 3) + rnd.uniform(-0.08, 0.08)
        zb = -math.sqrt(max(1.5 ** 2 - x * x, 0.0))
        r = rnd.uniform(0.15, 0.22)
        lump(mb, P(x, -0.24, zb + 0.42 + rnd.uniform(0.0, 0.08)), r, 0.85, q)
    # cloud behind the blue sock (top, latch side) + floating suds
    for x, z, r in ((0.55, 1.18, 0.20), (0.82, 1.08, 0.24), (1.08, 0.92, 0.19), (0.30, 1.30, 0.15)):
        lump(mb, P(x, -0.42, z), r, 0.8, q)
    if q:
        for x, z, r in ((-0.85, 0.55, 0.07), (-0.45, 1.05, 0.06), (0.25, 0.05, 0.05), (1.15, 0.35, 0.08),
                        (-1.15, -0.15, 0.06), (0.55, -0.55, 0.05)):
            lump(mb, P(x, -0.26, z), r, 1.0, q)


def build_door(q):
    mb = MB()
    build_frame(mb, q)
    build_bolts(mb, q)
    build_studs(mb, q)
    build_scrolls(mb, q)
    build_hinge(mb, q)
    build_latch(mb, q)
    build_glass(mb, q)
    build_chamber(mb, q)
    build_interior(mb, q)
    build_foam(mb, q)
    return mb


# ================================================================== socks
SOCKS = [
    # name, base, stripe, heel/toe, cuff, location (x, depth behind the glass, z), euler (deg), scale
    ("Sock_0", "#7DB4EE", "#2F62BE", "#2F62BE", "#2F62BE", (0.62, 0.20, 0.86), (8.0, -28.0, 18.0), 1.10),   # blue
    ("Sock_1", "#FF8C30", "#E2552A", "#C9461E", "#FFB347", (-0.22, 0.25, 0.50), (-6.0, 22.0, -15.0), 0.95),  # orange
    ("Sock_2", "#86DE52", "#2FA24A", "#2B8A3C", "#2FA24A", (0.80, 0.17, -0.18), (5.0, -12.0, 20.0), 1.20),   # green
    ("Sock_3", "#FFB62A", None, "#E0661E", "#C8501E", (0.02, 0.15, -0.70), (-4.0, 4.0, -12.0), 1.05),        # yellow-orange
    ("Sock_4", "#A86DE2", None, "#4A63D8", "#6A3CC0", (-0.60, 0.19, -0.58), (6.0, -16.0, 22.0), 1.0),        # purple
]


def build_sock(spec, q):
    name, base, stripe, heel, cuff, loc, eul, sc = spec
    S = 0.62 * sc
    pts, rad = [], []
    # leg (cuff top z .30 -> .00), heel arc, foot, toe (local metres before S)
    nl = 9 if q else 5
    for k in range(nl):
        z = 0.30 - 0.30 * k / (nl - 1)
        pts.append(Vector((0.0, 0.0, z)))
        rad.append(1.0)
    nh = 6 if q else 3
    for k in range(1, nh + 1):
        a = math.radians(180.0 + 90.0 * k / nh)
        pts.append(Vector((0.14 + 0.14 * math.cos(a), 0.0, 0.0 + 0.14 * math.sin(a))))
        rad.append(1.0 + 0.10 * math.sin(math.pi * k / nh))
    nf = 6 if q else 3
    for k in range(1, nf + 1):
        pts.append(Vector((0.14 + 0.24 * k / nf, 0.0, -0.14)))
        rad.append(0.97)
    nt = 4 if q else 2
    for k in range(1, nt + 1):
        t = k / nt
        pts.append(Vector((0.38 + 0.085 * math.sin(t * math.pi / 2), 0.0, -0.14 + 0.01 * t)))
        rad.append(max(math.cos(t * math.pi / 2) ** 0.7, 0.22))
    frames = path_frames(pts, lambda i: Y_AXIS)
    m = 14 if q else 8
    profs = []
    for i, (p, rr) in enumerate(zip(pts, rad)):
        cuffy = p.z > 0.235
        prof = []
        for k in range(m):
            t = TAU * k / m
            rib = 1.0 + (0.05 * math.cos(12 * t) if (cuffy and q) else 0.0) + (0.06 if cuffy else 0.0)
            a = 0.075 * rr * rib * math.cos(t)          # thickness (N = Y)
            b = 0.105 * rr * rib * math.sin(t)          # width in the sock plane
            if i >= nl + nh and b < 0:                  # flattened sole
                b *= 0.75
            prof.append((a, b))
        profs.append(prof)
    cb, cs, ch, cc = lin(base), lin(stripe) if stripe else None, lin(heel), lin(cuff)

    def col(p):
        if p.z > 0.235:
            return cc
        if p.x > 0.355:
            return ch                                   # toe
        if p.z < -0.035 and p.x < 0.12:
            return ch                                   # heel
        if cs and p.z > 0.0 and int((p.z + 1.0) / 0.055) % 2 == 0:
            return cs                                   # leg stripes
        if cs and p.z <= -0.06 and 0.16 < p.x < 0.33 and int((p.x + 1.0) / 0.06) % 2 == 0:
            return cs                                   # foot stripes
        return cb
    mb = MB()
    sweep(mb, frames, None, 0, closed_prof=True, profs=profs, cap0=True, cap1=True, col_fn=col)
    # centre the pivot on the sock, scale to size
    cen = sum(mb.co, Vector()) / len(mb.co)
    mb.co = [(c - cen) * S for c in mb.co]
    obj = mb.build(name, [MATS["M_DoorSock_r8"]], with_col=True)
    obj.location = P(loc[0], -loc[1], loc[2])
    obj.rotation_euler = Euler(tuple(math.radians(e) for e in eul), 'XYZ')
    return obj


# ================================================================== materials (Blender preview; Unity remaps by name)
MATS = {}


def vcol_material(name, roughness, glow=0.0):
    mat = C.material(name, "#FFFFFF", roughness=roughness)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    gam = nt.nodes.new("ShaderNodeGamma")       # the stored colours are linear values written as sRGB bytes
    gam.inputs[1].default_value = 1.0 / 2.2
    nt.links.new(attr.outputs["Color"], gam.inputs[0])
    nt.links.new(gam.outputs[0], bsdf.inputs["Base Color"])
    if glow > 0:
        nt.links.new(gam.outputs[0], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = glow
    if "Coat Weight" in bsdf.inputs and roughness < 0.3:
        bsdf.inputs["Coat Weight"].default_value = 0.6
    return mat


def make_materials():
    MATS["M_Gold"] = C.material("M_Gold", "#E9B65C", metallic=1.0, roughness=0.16)
    MATS["M_GoldDark"] = C.material("M_GoldDark", "#8E5A22", metallic=1.0, roughness=0.32)
    MATS["M_Glass"] = C.material("M_Glass", "#DDEEFF", roughness=0.02, alpha=0.10)
    MATS["M_ChamberDrum"] = C.material("M_ChamberDrum", "#3B2C6E", metallic=0.4, roughness=0.45)
    MATS["M_DrumRim"] = C.material("M_DrumRim", "#B8A2E6", metallic=0.7, roughness=0.28)
    MATS["M_Foam"] = C.material("M_Foam", "#F4F6FC", roughness=0.75)
    MATS["M_DoorRainbow_r8"] = vcol_material("M_DoorRainbow_r8", 0.12, glow=0.25)
    MATS["M_DoorSock_r8"] = vcol_material("M_DoorSock_r8", 0.85, glow=0.1)


# ================================================================== kit + renders
def write_kit(parts):
    os.makedirs(os.path.dirname(KIT), exist_ok=True)
    keep = set(parts)
    names = {o.name for o in parts}
    if os.path.exists(KIT):
        with bpy.data.libraries.load(KIT, link=False, assets_only=False) as (src, dst):
            dst.objects = [n for n in src.objects if n not in names]
        for o in dst.objects:
            if o is not None:
                keep.add(o)
    for o in keep:
        o.asset_mark()
        o.asset_data.tags.new("BWK")
    bpy.data.libraries.write(KIT, keep, fake_user=True, compress=True)
    print("CHECK kit", KIT, sorted(o.name for o in keep))


def kit_parts():
    parts = []
    mb = MB()
    build_frame(mb, 1)
    parts.append(mb.build("Kit_GoldRingProfile", [MATS[n] for n in SLOTS]))
    mb = MB()
    lathe(mb, [(0.048, -0.03), (0.048, 0.004), (0.038, 0.024), (0.02, 0.034), (0.0, 0.037)], G, 10, (0, 0, 0),
          FRONT, X_AXIS)
    parts.append(mb.build("Kit_Bolt", [MATS[n] for n in SLOTS]))
    mb = MB()
    build_hinge(mb, 1)
    parts.append(mb.build("Kit_Hinge", [MATS[n] for n in SLOTS]))
    mb = MB()
    lump(mb, (0, 0, 0), 0.25, 0.82, 1)
    parts.append(mb.build("Kit_FoamLump", [MATS[n] for n in SLOTS]))
    sock = build_sock(("Kit_Sock",) + SOCKS[0][1:5] + ((0, 0, 0), (0, 0, 0), 1.0), 1)
    sock.location = (0, 0, 0)
    sock.rotation_euler = (0, 0, 0)
    parts.append(sock)
    for o in parts:
        bpy.context.scene.collection.objects.unlink(o)
    return parts


def render_views(objs):
    os.makedirs(REVIEW, exist_ok=True)
    holder = bpy.data.objects.new("RenderMirror", None)
    bpy.context.scene.collection.objects.link(holder)
    for o in objs:
        o.parent = holder
    # reference composition: the reference windows show the hinge on the RIGHT (window on the left wall) -> mirror
    holder.scale = (-1.0, 1.0, 1.0)
    bpy.context.view_layer.update()

    def cam_at(deg, dist, z=0.25):
        a = math.radians(deg)
        return (dist * math.sin(a), -dist * math.cos(a), z)
    C.render_preview(os.path.join(REVIEW, "door_ref_angle.png"), cam_at(38.0, 8.2), (0.15, 0, 0.0), lens=50,
                     resolution=(900, 900))
    # rear gameplay camera: travel-right window (mirrored, hinge toward the oncoming camera) seen ~58 deg off its normal
    C.render_preview(os.path.join(REVIEW, "door_rear_angle.png"), cam_at(58.0, 10.0, 0.6), (0.2, 0, 0.0), lens=50,
                     resolution=(900, 900))
    C.render_preview(os.path.join(REVIEW, "door_front.png"), (0.0, -7.6, 0.0), (0.0, 0.0, 0.0), lens=50,
                     resolution=(900, 900))
    C.render_preview(C.preview_path("SM_WashDoor_Master"), cam_at(30.0, 8.6, 0.6), (0.1, 0, 0.0), lens=50,
                     resolution=(900, 900))
    holder.scale = (1.0, 1.0, 1.0)
    for o in objs:
        o.parent = None
    bpy.data.objects.remove(holder, do_unlink=True)


def main():
    C.reset_scene()
    make_materials()
    mats = [MATS[n] for n in SLOTS]
    lod0 = build_door(1).build("WashDoor_LOD0", mats)
    lod1 = build_door(0).build("WashDoor_LOD1", mats)
    socks = [build_sock(s, 1) for s in SOCKS]
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    ts = sum(C.tri_count(s) for s in socks)
    print("CHECK tris LOD0 %d LOD1 %d (%.0f %%) socks %d" % (t0, t1, 100.0 * t1 / t0, ts))
    dims = lod0.dimensions
    print("CHECK dims %.2f x %.2f x %.2f m" % (dims.x, dims.y, dims.z))
    # review renders with LOD0 only
    lod1.hide_render = True
    render_views([lod0] + socks)
    lod1.hide_render = False
    if NOEXPORT:
        print("DONE (no export)")
        return
    root = bpy.data.objects.new("SM_WashDoor_Master", None)
    bpy.context.scene.collection.objects.link(root)
    for o in [lod0, lod1] + socks:
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_WashDoor_Master"))
    try:
        write_kit(kit_parts())
    except Exception as e:  # the kit is a convenience; never fail the export for it
        print("CHECK kit failed:", e)
    C.save_work("master_door.blend")
    print("DONE")


main()
