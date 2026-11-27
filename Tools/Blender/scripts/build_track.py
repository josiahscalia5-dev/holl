"""Bubble Wash Kingdom - track module group "Track" (Blender 5.3, headless, deterministic).

Builds, exports (FBX -> Assets/BubbleWashKingdom/Art/Models/Track/) and previews:

  SM_Slide_Module      blue water slide channel, 4 m, 24 edge loops    M_Water, M_RailRainbow, M_RailPink, M_SlideShell
  SM_Tunnel_Module     inside of the drum tunnel (r 4.2, centre z 2.3) M_DrumWall (normals inward)
  SM_GlassPipe_Module  glass tube r 0.28 around a glowing core r 0.20  M_Glass, M_PipeWater
  SM_Pipe_Coupler      gold band r 0.33 x 0.12 with 6 hex bolt heads   M_Gold
  SM_Pipe_Elbow        90 degree glass elbow, bend radius 0.8          M_Glass, M_PipeWater
  SM_Ring              thick polished gold band r 3.50-4.26 x 0.33 (r3, was 3.65): inner + outer rolled beads,
                       wide gold trough with 28 warm marquee bulbs half sunk in gold cups         M_Gold, M_GoldDark, M_Bulb
  SM_DrumRim           big rolled lavender drum lip r 3.66-4.26 (short front bevel, long back slope) with 24 soft
                       pink LED lamps (r4: r 0.062), ONE per gold-ring gap at 0.40 of the gap (r3) M_DrumRim, M_RimLight
  SM_Bulb              warm marquee bulb, origin at its base, +Z       M_Bulb (legacy, not placed by BuildRings)

Every surface is swept or revolved from an analytic 2D profile with exact per-vertex normals (stored as
custom split normals), so the curved slide walls, rails and fillets shade perfectly smooth at mobile
triangle counts. Conventions (Docs/AssetSpec.md): meters, Z up, front / travel = -Y, right side = -X.
Bent modules run straight from y = 0 to y = -4 with 24 evenly spaced edge loops (SplineMeshDeformer).

Run from the project root:
  blender --background --factory-startup --python Tools/Blender/scripts/build_track.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bwk_common as C  # noqa: E402

GROUP = "Track"

# ------------------------------------------------------------------ module rules
LENGTH = 4.0      # modules run from y = 0 to y = -4 (front / travel = -Y)
SEGS = 7          # 7 segments = 8 evenly spaced edge loops (0.57 m) - mobile budget, smooth on r >= 15 m curves
V_TILE = 4.0      # v = distance along / 4 m

# ------------------------------------------------------------------ slide cross-section (RunnerController contract)
FLAT = 0.95                     # flat floor |x| <= 0.95 at z = 0 (lead 2026-11-27 corridor: was 1.25 - reference slide ~0.78x narrower)
K = 1.3                         # inner wall z = 1.3 * (|x| - FLAT)^2 (was 0.9)
X_TOP = 1.64                    # wall top |x| = 1.64 (z ~ 0.62), buried inside the rail tube (was 2.10)
A_TOP = X_TOP - FLAT
Z_SPLIT = 0.40                  # M_Water below, M_RailRainbow above
A_SPLIT = math.sqrt(Z_SPLIT / K)
WALL_T = 0.12                   # wall / floor thickness
RAIL_R, RAIL_X, RAIL_Z = 0.30, 1.86, 0.80   # keep FLAT / K / X_TOP / RAIL_* in sync with Assets/BubbleWashKingdom/Scripts/Runtime/Gameplay/SlideProfile.cs
WATER_WALL_SEGS, RAINBOW_SEGS = 12, 4   # 16 profile segments per curved wall
RAIL_SIDES, SHELL_WALL_SEGS = 20, 3

# ------------------------------------------------------------------ tunnel / pipes
TUN_R, TUN_ZC, TUN_SIDES = 4.2, 2.3, 64
GLASS_R, GLASS_SIDES = 0.28, 20
CORE_R, CORE_SIDES = 0.20, 12
CPL_RO, CPL_RI, CPL_HW, CPL_FILLET, CPL_SEGS = 0.33, 0.272, 0.06, 0.018, 32
ELBOW_R, ELBOW_SEGS = 0.8, 12

# ------------------------------------------------------------------ polished gold ring (profile in (rho, y); +y faces
# the approaching player, i.e. Unity -Z after the FBX axis fix). m1 (reference f_003.00s at the hero camera): a slim
# polished band ~0.40 m deep (r 3.80 -> wall) - two rolled beads with a shallow trough between them in which the warm
# marquee bulbs sit, half sunk in gold cups, so the bulbs read as part of the band (no chunky rope / plates / rivets).
RING_SEGS = 84                  # 3 segments per bulb pitch (smooth silhouette at the hero distance)
RING_BULBS = 28                 # reference f_003.00s: ~24-28 warm bulbs per ring (measured at the first two gold rings)
RG_BACK_Y, RG_OUT = -0.12, 4.26           # back face; outer surface buried in the drum wall (r 4.2)
RG_IN_FACE = 3.53                         # inner face (toward the axis) under the inner bead (r3: thicker band)
RG_IB_C, RG_IB_R = (3.60, 0.035), 0.10    # inner polished bead: apex rho 3.50, front y 0.135 (r3: band 0.70 m, was 0.555;
                                          # reference f_003.00s ring 1 band ~57 px at 4K vs ours ~45 px)
RG_CORNER_R = 0.05                        # rounded back-inner corner
RG_FLOOR_Y = 0.05                         # bulb trough rim height
RG_TROUGH = 0.02                          # trough depth below RG_FLOOR_Y at the channel centre
RG_OB_C, RG_OB_R = (4.12, 0.02), 0.075    # outer bead against the wall: front y 0.095
RG_BULB_RHO = 3.875                       # trough centre line (CHECK printed by ring_parts: r3 trough 3.699..4.051)
BULB_R2, BULB_H2 = 0.100, 0.100           # fat warm marquee bulbs (lead m1: reference bulbs read big)
BULB_Y = RG_FLOOR_Y + 0.06                # bulb centre: lower half sunk in the cup
BULB_TILT = math.radians(10.0)            # bulbs lean toward the tunnel axis (gameplay camera)
CUP_RO, CUP_RI, CUP_TOP = 0.118, 0.101, 0.050
PLATES = 0                                # m1: no clamp plates / rivets (clutter at the hero distance)

# ------------------------------------------------------------------ lavender drum rim (nested-drum lips between rings)
# m1: a fat rolled lip (reference f_003.00s: broad glossy lavender bands ~0.45 m deep with soft pink-white glints)
RIM_SEGS, RIM_LEDS = 84, 24           # r4: 24 bigger pink LED lamps (reference: soft pink glows ~15 deg apart)
RIM_C, RIM_R = (3.94, 0.0), 0.28          # rolled bead, apex rho 3.66, front y 0.28 (r3: one big lip per gap reads as
                                          # the reference's broad lavender band, was r 0.24 / apex 3.74)
RIM_FRONT, RIM_BACK = (4.26, 0.14), (4.26, -0.62)   # short front bevel / long back slope meet the wall
RIM_LED_DEG = 128.0                       # soft LED studs on the front-inner face of the bead
RIM_LED_R, RIM_LED_H = 0.062, 0.032       # r4: LED lamp dome radius / height (~11 px at the hero rim, 12 m)

# ------------------------------------------------------------------ legacy single bulb asset
BULB_RX, BULB_HALF_H = 0.085, 0.10          # slightly elongated sphere (1.18 : 1)
BULB_SIDES, BULB_BANDS = 6, 4                  # even band count -> equator ring at r 0.085; ~36 tris (mobile)

# ------------------------------------------------------------------ gameplay layout mirrored from SceneBuilder (previews)
RING_SPACING = 12.75                      # SceneBuilder.GoldRingSpacing (Environment, m1): gold rings
RIMS_PER_GAP = 1                          # r3: ONE big lavender rim per gap (SceneBuilder.RimsPerGap), was 3
RIM_PHASE = 0.40                          # r3: rim at RIM_PHASE of the gap (SceneBuilder.RimPhase): ~12 m ahead in the hero

X_AXIS, Y_AXIS, Z_AXIS = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0))


# ================================================================== mesh building
def newell(points):
    pts = list(points)
    n = Vector((0.0, 0.0, 0.0))
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    return n


class MeshBuilder:
    """Vertices carry an authored normal and UV. Faces are wound to agree with their authored normals."""

    def __init__(self):
        self.co, self.no, self.uv, self.faces, self.mats = [], [], [], [], []

    def vert(self, co, no, uv):
        n = Vector(no)
        if n.length > 1e-12:
            n.normalize()
        self.co.append(Vector(co))
        self.no.append(n)
        self.uv.append((float(uv[0]), float(uv[1])))
        return len(self.co) - 1

    def face(self, idx, mat):
        idx = list(idx)
        ref = Vector((0.0, 0.0, 0.0))
        for i in idx:
            ref += self.no[i]
        if newell(self.co[i] for i in idx).dot(ref) < 0.0:
            idx.reverse()
        self.faces.append(tuple(idx))
        self.mats.append(mat)

    def flat_poly(self, pts, mat, hint, uv_axes):
        """Hard-edged polygon with its own vertices and the face normal (fan-triangulated above 4 corners)."""
        pts = [Vector(p) for p in pts]
        n = newell(pts)
        if n.dot(Vector(hint)) < 0.0:
            pts.reverse()
            n = -n
        n.normalize()
        ua, va = uv_axes
        ids = [self.vert(p, n, (p.dot(ua) * 4.0, p.dot(va) * 4.0)) for p in pts]
        if len(ids) <= 4:
            self.face(ids, mat)
        else:
            for i in range(1, len(ids) - 1):
                self.face((ids[0], ids[i], ids[i + 1]), mat)

    def build(self, name, mats):
        me = bpy.data.meshes.new(name)
        me.from_pydata([c[:] for c in self.co], [], self.faces)
        me.update()
        uvl = me.uv_layers.new(name="UVMap")
        flat = []
        for lp in me.loops:
            flat.extend(self.uv[lp.vertex_index])
        uvl.data.foreach_set("uv", flat)
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        C.assign_materials(obj, mats)
        me.polygons.foreach_set("material_index", self.mats)
        me.shade_smooth()
        me.normals_split_custom_set_from_vertices([n[:] for n in self.no])
        me.update()
        return obj


def sweep(mb, prof, mat, length=LENGTH, segs=SEGS):
    """Sweep an (x, z, nx, nz, u) profile straight along -Y from y = 0 to y = -length; v = distance / 4."""
    rows = []
    for i in range(segs + 1):
        d = length * i / segs
        rows.append([mb.vert((x, -d, z), (nx, 0.0, nz), (u, d / V_TILE)) for (x, z, nx, nz, u) in prof])
    for i in range(segs):
        for j in range(len(prof) - 1):
            mb.face((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]), mat)


def tube(mb, frames, radius, sides, mat, inward=False):
    """Tube along frames (P, X, U, v). u runs around from the bottom (-U) toward -X (the right side) first."""
    rows = []
    for (p, xa, ua, v) in frames:
        row = []
        for k in range(sides + 1):
            psi = 2.0 * math.pi * k / sides
            d = -math.sin(psi) * xa - math.cos(psi) * ua
            row.append(mb.vert(p + radius * d, -d if inward else d, (k / sides, v)))
        rows.append(row)
    for i in range(len(rows) - 1):
        for k in range(sides):
            mb.face((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]), mat)


def straight_frames(zc):
    return [(Vector((0.0, -LENGTH * i / SEGS, zc)), X_AXIS, Z_AXIS, LENGTH * i / SEGS / V_TILE)
            for i in range(SEGS + 1)]


def ring_frame(alpha):
    """Radial / tangent axes at angle alpha around the Y axis: 0 = top (+Z), then clockwise as the player sees it
    (toward -X = the player's right)."""
    er = Vector((-math.sin(alpha), 0.0, math.cos(alpha)))
    t = Vector((-math.cos(alpha), 0.0, -math.sin(alpha)))
    return er, t


def revolve(mb, prof, mat, segs, alpha0=math.pi):
    """Revolve an (rho, y, n_rho, n_y, v) profile around the Y axis; u = 0 at the bottom (seam hidden)."""
    rows = []
    for k in range(segs + 1):
        er, _ = ring_frame(alpha0 + 2.0 * math.pi * k / segs)
        rows.append([mb.vert(er * r + Y_AXIS * y, er * nr + Y_AXIS * ny, (k / segs, v))
                     for (r, y, nr, ny, v) in prof])
    for k in range(segs):
        for j in range(len(prof) - 1):
            mb.face((rows[k][j], rows[k][j + 1], rows[k + 1][j + 1], rows[k + 1][j]), mat)


# ------------------------------------------------------------------ 2D profile helpers (a, b, (na, nb))
def arc_pts(c, r, a0, a1, segs):
    out = []
    for k in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * k / segs)
        n = (math.cos(a), math.sin(a))
        out.append((c[0] + r * n[0], c[1] + r * n[1], n))
    return out


def line_pts(p0, p1, n, segs=1):
    return [(p0[0] + (p1[0] - p0[0]) * k / segs, p0[1] + (p1[1] - p0[1]) * k / segs, n) for k in range(segs + 1)]


def chain(*parts):
    pts = []
    for part in parts:
        pts.extend(part[1:] if pts else part)
    return pts


def with_u(points):
    """Attach a 0..1 parameter proportional to arc length: (a, b, (na, nb)) -> (a, b, na, nb, u)."""
    acc = [0.0]
    for p, q in zip(points, points[1:]):
        acc.append(acc[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    return [(p[0], p[1], p[2][0], p[2][1], acc[i] / acc[-1]) for i, p in enumerate(points)]


def bisect(f, lo, hi, iters=60):
    flo = f(lo)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0.0) == (flo > 0.0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ================================================================== 1. slide module
def wall_len(a):
    """Arc length of z = K a^2 from 0 to a."""
    w = 2.0 * K * a
    return (w * math.sqrt(1.0 + w * w) + math.asinh(w)) / (4.0 * K)


def wall_a(s):
    return bisect(lambda a: wall_len(a) - s, 0.0, 2.0)


def wall_point(a, side):
    """Inner wall point at a = |x| - 1.25 on side +1 (+X, player's left) or -1 (-X, player's right)."""
    slope = 2.0 * K * a
    ln = math.hypot(1.0, slope)
    return side * (FLAT + a), K * a * a, (-side * slope / ln, 1.0 / ln)


def shell_point(a, side):
    """Outer shell = inner surface offset by the wall thickness, normal pointing away from the channel."""
    x, z, n = wall_point(a, side)
    return x - WALL_T * n[0], z - WALL_T * n[1], (-n[0], -n[1])


def rail_seam_angle():
    """Middle of the rail arc hidden inside the wall (between the inner-wall and shell intersections), side +1."""
    def angle_of(pfun):
        a = bisect(lambda a: math.hypot(pfun(a, 1)[0] - RAIL_X, pfun(a, 1)[1] - RAIL_Z) - RAIL_R, 0.5, A_TOP)
        x, z, _ = pfun(a, 1)
        return math.atan2(z - RAIL_Z, x - RAIL_X) % (2.0 * math.pi)
    th_wall, th_shell = angle_of(wall_point), angle_of(shell_point)
    print("CHECK rail hidden arc %.1f..%.1f deg" % (math.degrees(th_wall), math.degrees(th_shell)))
    return 0.5 * (th_wall + th_shell)


def build_slide(mats):
    mb = MeshBuilder()
    s_split, s_top = wall_len(A_SPLIT), wall_len(A_TOP)

    # M_Water: left (+X) water line z = 0.40 -> wall -> flat floor -> wall -> right (-X) water line; u 0..1 L->R
    water = [wall_point(wall_a(s_split * (1.0 - k / WATER_WALL_SEGS)), +1) for k in range(WATER_WALL_SEGS + 1)]
    water += [(0.0, 0.0, (0.0, 1.0)), (-FLAT, 0.0, (0.0, 1.0))]
    water += [wall_point(wall_a(s_split * k / WATER_WALL_SEGS), -1) for k in range(1, WATER_WALL_SEGS + 1)]
    sweep(mb, with_u(water), 0)

    # M_RailRainbow: z = 0.40 water edge (u = 0) up to the rail (u = 1), both sides
    for side in (+1, -1):
        band = [wall_point(wall_a(s_split + (s_top - s_split) * k / RAINBOW_SEGS), side)
                for k in range(RAINBOW_SEGS + 1)]
        sweep(mb, with_u(band), 1)

    # M_RailPink: rail tubes, u around (seam hidden inside the wall), mirrored left / right
    seam = rail_seam_angle()
    for side in (+1, -1):
        prof = []
        for k in range(RAIL_SIDES + 1):
            th = seam - 2.0 * math.pi * k / RAIL_SIDES
            if side < 0:
                th = math.pi - th
            c, s = math.cos(th), math.sin(th)
            prof.append((side * RAIL_X + RAIL_R * c, RAIL_Z + RAIL_R * s, c, s, k / RAIL_SIDES))
        sweep(mb, prof, 2)

    # M_SlideShell: outer U shell from under the left rail, under the floor, up to the right rail
    shell = [shell_point(wall_a(s_top * k / SHELL_WALL_SEGS), +1) for k in range(SHELL_WALL_SEGS, -1, -1)]
    shell += [shell_point(wall_a(s_top * k / SHELL_WALL_SEGS), -1) for k in range(SHELL_WALL_SEGS + 1)]
    sweep(mb, with_u(shell), 3)
    return mb.build("SM_Slide_Module", mats)


# ================================================================== 2-5. tunnel and pipes
def build_tunnel(mats):
    mb = MeshBuilder()
    tube(mb, straight_frames(TUN_ZC), TUN_R, TUN_SIDES, 0, inward=True)
    return mb.build("SM_Tunnel_Module", mats)


def build_glass_pipe(mats):
    mb = MeshBuilder()
    frames = straight_frames(0.0)
    tube(mb, frames, GLASS_R, GLASS_SIDES, 0)
    tube(mb, frames, CORE_R, CORE_SIDES, 1)
    return mb.build("SM_GlassPipe_Module", mats)


def elbow_frames():
    """Starts at the origin heading -Y, bends up: centre of the bend (0, 0, 0.8); ends at (0, -0.8, 0.8) heading +Z."""
    frames = []
    for i in range(ELBOW_SEGS + 1):
        phi = 0.5 * math.pi * i / ELBOW_SEGS
        p = Vector((0.0, -ELBOW_R * math.sin(phi), ELBOW_R * (1.0 - math.cos(phi))))
        u = Vector((0.0, math.sin(phi), math.cos(phi)))       # toward the bend centre; X x U = tangent
        frames.append((p, X_AXIS, u, ELBOW_R * phi / V_TILE))
    return frames


def build_elbow(mats):
    mb = MeshBuilder()
    frames = elbow_frames()
    tube(mb, frames, GLASS_R, GLASS_SIDES, 0)
    tube(mb, frames, CORE_R, CORE_SIDES, 1)
    return mb.build("SM_Pipe_Elbow", mats)


def hex_bolt(mb, alpha, rho0, mat, rc=0.034, h=0.026, cham=0.007, embed=0.004):
    """Hex bolt head standing radially on a surface of radius rho0 around the Y axis (hard-edged facets)."""
    er, t = ring_frame(alpha)

    def hexring(rr, rho):
        return [er * rho + rr * (math.cos(b) * Y_AXIS + math.sin(b) * t)
                for b in (math.radians(30.0 + 60.0 * m) for m in range(6))]

    base, top, cap = hexring(rc, rho0 - embed), hexring(rc, rho0 + h - cham), hexring(rc - cham, rho0 + h)
    axis_c = er * rho0
    for m in range(6):
        m2 = (m + 1) % 6
        side = [base[m], base[m2], top[m2], top[m]]
        mid = sum(side, Vector((0.0, 0.0, 0.0))) / 4.0
        mb.flat_poly(side, mat, mid - axis_c - er * er.dot(mid - axis_c), (t, Y_AXIS))
        bevel = [top[m], top[m2], cap[m2], cap[m]]
        mb.flat_poly(bevel, mat, (top[m] + top[m2]) * 0.5 - er * (rho0 + h - cham) + er * 0.01, (t, Y_AXIS))
    mb.flat_poly(cap, mat, er, (t, Y_AXIS))


def build_coupler(mats):
    mb = MeshBuilder()
    f = CPL_FILLET
    oc_p, oc_m = (CPL_RO - f, CPL_HW - f), (CPL_RO - f, -CPL_HW + f)
    outer = chain(
        line_pts((CPL_RI, CPL_HW), (oc_p[0], CPL_HW), (0.0, 1.0)),          # +Y face
        arc_pts(oc_p, f, 90.0, 0.0, 2),                                     # rounded edge
        line_pts((CPL_RO, oc_p[1]), (CPL_RO, oc_m[1]), (1.0, 0.0)),         # outer band
        arc_pts(oc_m, f, 0.0, -90.0, 2),
        line_pts((oc_m[0], -CPL_HW), (CPL_RI, -CPL_HW), (0.0, -1.0)),       # -Y face
    )
    revolve(mb, with_u(outer), 0, CPL_SEGS)
    revolve(mb, with_u(line_pts((CPL_RI, -CPL_HW), (CPL_RI, CPL_HW), (-1.0, 0.0))), 0, CPL_SEGS)
    for j in range(6):
        hex_bolt(mb, 2.0 * math.pi * j / 6.0, CPL_RO, 0)
    return mb.build("SM_Pipe_Coupler", mats)


# ================================================================== 6-7. premium ring, drum rim and bulb
def lathe_axis(mb, prof, mat, segs, origin, axis, e1):
    """Revolve an (r, h, n_r, n_h, v) profile around `axis` through `origin` (small parts: cups, bulbs, rivets).
    r = 0 points become a single shared pole vertex."""
    A = Vector(axis).normalized()
    e1 = Vector(e1) - A * Vector(e1).dot(A)
    if e1.length < 1e-6:
        e1 = X_AXIS - A * X_AXIS.dot(A) if abs(A.dot(X_AXIS)) < 0.9 else Z_AXIS - A * Z_AXIS.dot(A)
    e1.normalize()
    e2 = A.cross(e1)
    O = Vector(origin)
    poles = {}
    for j, (r, h, nr, nh, v) in enumerate(prof):
        if r < 1e-7:
            poles[j] = mb.vert(O + A * h, A * (1.0 if nh >= 0.0 else -1.0), (0.5, v))
    rows = []
    for k in range(segs + 1):
        phi = 2.0 * math.pi * k / segs
        d = e1 * math.cos(phi) + e2 * math.sin(phi)
        rows.append([poles[j] if j in poles else mb.vert(O + A * h + d * r, d * nr + A * nh, (k / segs, v))
                     for j, (r, h, nr, nh, v) in enumerate(prof)])
    for k in range(segs):
        for j in range(len(prof) - 1):
            q = [rows[k][j], rows[k][j + 1], rows[k + 1][j + 1], rows[k + 1][j]]
            if j in poles:
                q = [rows[k][j], rows[k][j + 1], rows[k + 1][j + 1]]
            elif (j + 1) in poles:
                q = [rows[k][j], rows[k][j + 1], rows[k + 1][j]]
            mb.face(q, mat)


def ellipsoid_prof(rx, hz, bands, z0=0.0):
    """Closed ellipsoid profile from the bottom pole to the top pole (exact ellipse normals)."""
    out = []
    for i in range(bands + 1):
        lat = -0.5 * math.pi + math.pi * i / bands
        c, s = math.cos(lat), math.sin(lat)
        n = Vector((c / rx, s / hz)).normalized()
        out.append((rx * c if 0 < i < bands else 0.0, z0 + hz * s, n.x, n.y, i / bands))
    return out


def dome_prof(r0, h, skirt=0.006, bands=3):
    """Domed rivet / LED stud: short skirt into the surface, then a quarter ellipse to the pole."""
    out = [(r0, -skirt, 1.0, 0.0, 0.0)]
    for i in range(bands + 1):
        t = 0.5 * math.pi * i / bands
        n = Vector((math.cos(t) / r0, math.sin(t) / h)).normalized()
        out.append((r0 * math.cos(t) if i < bands else 0.0, h * math.sin(t), n.x, n.y, (i + 1) / (bands + 1)))
    return out


def rounded_block(mb, center, ex, ey, ez, size, radius, mat, segs=2):
    """Box with all edges rounded (bmesh bevel), smooth vertex normals, oriented by the (ex, ey, ez) axes."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=radius, offset_type='OFFSET',
                    segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    bm.normal_update()
    bm.verts.index_update()
    M = Matrix((tuple(ex), tuple(ey), tuple(ez))).transposed()
    ids = [mb.vert(Vector(center) + M @ v.co, (M @ v.normal).normalized(),
                   (v.co.x / size[0] + 0.5, v.co.y / size[1] + 0.5)) for v in bm.verts]
    for f in bm.faces:
        mb.face([ids[lp.vert.index] for lp in f.loops], mat)
    bm.free()


def tangent_angle(c, r, p, upper):
    """Angle (deg) of the tangent point on circle (c, r) seen from the external point p (upper / lower branch)."""
    dx, dy = p[0] - c[0], p[1] - c[1]
    base, off = math.atan2(dy, dx), math.acos(r / math.hypot(dx, dy))
    return math.degrees(base + off if upper else base - off)


def trough_pts(r0, r1, y0, depth, segs):
    """Concave channel from (r0, y0) to (r1, y0), deepest (y0 - depth) in the middle; normals face +y / the trough
    centre, so the polished gold catches a rolling highlight instead of reading as a flat brown band (r2)."""
    mid, hw = 0.5 * (r0 + r1), 0.5 * (r1 - r0)
    out = []
    for k in range(segs + 1):
        r = r0 + (r1 - r0) * k / segs
        t = (r - mid) / hw
        y = y0 - depth * (1.0 - t * t)
        dy = depth * 2.0 * t / hw                     # dy/dr
        ln = math.hypot(dy, 1.0)
        out.append((r, y, (-dy / ln, 1.0 / ln)))
    return out


def ring_parts():
    """Closed ring cross-section as separately revolved parts (hard creases between parts):
    back face + rounded back-inner corner + inner face | inner rope bead | dark channel floor | outer bead | buried."""
    cx, cy = RG_IB_C
    dy = math.sqrt(RG_IB_R ** 2 - (RG_IN_FACE - cx) ** 2)
    a_in = math.degrees(math.atan2(-dy, RG_IN_FACE - cx)) % 360.0       # ~260: inner face meets the rope bead
    a_fl = math.degrees(math.asin((RG_FLOOR_Y - cy) / RG_IB_R))         # ~-25: rope bead meets the channel floor
    floor0 = cx + RG_IB_R * math.cos(math.radians(a_fl))
    ox, oy = RG_OB_C
    b_fl = 180.0 + math.degrees(math.asin((oy - RG_FLOOR_Y) / RG_OB_R))  # ~214: outer bead meets the floor
    floor1 = ox + RG_OB_R * math.cos(math.radians(b_fl))
    cc = (RG_IN_FACE + RG_CORNER_R, RG_BACK_Y + RG_CORNER_R)
    back_inner = chain(
        line_pts((RG_OUT, RG_BACK_Y), (cc[0], RG_BACK_Y), (0.0, -1.0), 2),
        arc_pts(cc, RG_CORNER_R, -90.0, -180.0, 4),
        line_pts((RG_IN_FACE, cc[1]), (RG_IN_FACE, cy - dy), (-1.0, 0.0), 1),
    )
    parts = [
        (back_inner, 0),
        (arc_pts(RG_IB_C, RG_IB_R, a_in, a_fl, 20), 0),                              # rope bead (polished)
        (trough_pts(floor0, floor1, RG_FLOOR_Y, RG_TROUGH, 8), 0),                   # polished concave channel
        (arc_pts(RG_OB_C, RG_OB_R, b_fl, 0.0, 12), 0),                               # outer bead
        (chain(line_pts((ox + RG_OB_R, oy), (RG_OUT, oy), (0.0, 1.0)),
               line_pts((RG_OUT, oy), (RG_OUT, RG_BACK_Y), (1.0, 0.0))), 1),         # buried in the wall
    ]
    print("CHECK ring inner bead %.1f..%.1f deg, bulb trough rho %.3f..%.3f (width %.3f, centre %.3f vs RG_BULB_RHO %.3f)"
          % (a_in, a_fl, floor0, floor1, floor1 - floor0, 0.5 * (floor0 + floor1), RG_BULB_RHO))
    return parts


def build_ring(mats):
    """mats: M_Gold, M_GoldDark, M_Bulb. Bulbs are part of the ring (one combined draw per material in Unity)."""
    G, GD, BL = 0, 1, 2
    mb = MeshBuilder()
    for prof, mat in ring_parts():
        revolve(mb, with_u(prof), mat, RING_SEGS)
    cup = with_u(chain(
        line_pts((CUP_RI, 0.012), (CUP_RI, CUP_TOP - (CUP_RO - CUP_RI) * 0.5), (-1.0, 0.0)),
        arc_pts(((CUP_RO + CUP_RI) * 0.5, CUP_TOP - (CUP_RO - CUP_RI) * 0.5), (CUP_RO - CUP_RI) * 0.5, 180.0, 0.0, 4),
        line_pts((CUP_RO, CUP_TOP - (CUP_RO - CUP_RI) * 0.5), (CUP_RO, -0.03), (1.0, 0.0)),
    ))
    cup_floor = [(CUP_RI, 0.012, 0.0, 1.0, 0.0), (0.0, 0.012, 0.0, 1.0, 1.0)]
    bulb = ellipsoid_prof(BULB_R2, BULB_H2, 8)
    for j in range(RING_BULBS):
        er, t = ring_frame(2.0 * math.pi * j / RING_BULBS)
        axis = Y_AXIS * math.cos(BULB_TILT) - er * math.sin(BULB_TILT)
        base = er * RG_BULB_RHO + Y_AXIS * RG_FLOOR_Y
        lathe_axis(mb, cup, G, 12, base, axis, t)
        lathe_axis(mb, cup_floor, GD, 12, base, axis, t)
        lathe_axis(mb, bulb, BL, 10, base + axis * (BULB_Y - RG_FLOOR_Y), axis, t)
    rivet = dome_prof(0.021, 0.015)
    for j in range(RING_BULBS if PLATES > 0 else 0):
        alpha = 2.0 * math.pi * (j + 0.5) / RING_BULBS
        er, t = ring_frame(alpha)
        if j % (RING_BULBS // PLATES) == 0:
            # bolted clamp plate bridging the channel (segment joint), two domed bolts on top
            ctr = er * RG_BULB_RHO + Y_AXIS * (RG_FLOOR_Y + 0.032)
            rounded_block(mb, ctr, er, t, Y_AXIS, (0.36, 0.085, 0.075), 0.022, GD)
            for rr in (RG_BULB_RHO - 0.1, RG_BULB_RHO + 0.1):
                lathe_axis(mb, dome_prof(0.019, 0.013), G, 8, er * rr + Y_AXIS * (RG_FLOOR_Y + 0.0695), Y_AXIS, t)
        else:
            lathe_axis(mb, rivet, G, 8, er * RG_OB_C[0] + Y_AXIS * (RG_OB_C[1] + RG_OB_R - 0.003), Y_AXIS, t)
    return mb.build("SM_Ring", mats)


def build_rim(mats):
    """mats: M_DrumRim, M_RimLight. Lavender lip of a drum section: front bevel, rope bead, long back slope."""
    mb = MeshBuilder()
    a_f = tangent_angle(RIM_C, RIM_R, RIM_FRONT, upper=True)
    a_b = tangent_angle(RIM_C, RIM_R, RIM_BACK, upper=False) % 360.0
    nf = (math.cos(math.radians(a_f)), math.sin(math.radians(a_f)))
    nb = (math.cos(math.radians(a_b)), math.sin(math.radians(a_b)))
    pf = (RIM_C[0] + RIM_R * nf[0], RIM_C[1] + RIM_R * nf[1])
    pb = (RIM_C[0] + RIM_R * nb[0], RIM_C[1] + RIM_R * nb[1])
    prof = chain(line_pts(RIM_FRONT, pf, nf, 2), arc_pts(RIM_C, RIM_R, a_f, a_b, 26), line_pts(pb, RIM_BACK, nb, 3))
    revolve(mb, with_u(prof), 0, RIM_SEGS)
    revolve(mb, with_u(line_pts(RIM_BACK, RIM_FRONT, (1.0, 0.0))), 0, RIM_SEGS)       # buried outer face
    a = math.radians(RIM_LED_DEG)
    n2 = (math.cos(a), math.sin(a))
    led = dome_prof(RIM_LED_R, RIM_LED_H, skirt=0.012, bands=3)   # r4: was 0.032 x 0.020 (tiny white dots at 12 m)
    for j in range(RIM_LEDS):
        er, t = ring_frame(2.0 * math.pi * (j + 0.5) / RIM_LEDS)
        p = er * (RIM_C[0] + RIM_R * n2[0]) + Y_AXIS * (RIM_C[1] + RIM_R * n2[1])
        lathe_axis(mb, led, 1, 10, p, er * n2[0] + Y_AXIS * n2[1], t)
    print("CHECK rim bead %.1f..%.1f deg, apex rho %.3f, front y %.3f" % (a_f, a_b, RIM_C[0] - RIM_R,
                                                                        RIM_C[1] + RIM_R))
    return mb.build("SM_DrumRim", mats)


def build_bulb(mats):
    mb = MeshBuilder()
    rings = []
    for i in range(1, BULB_BANDS):
        lat = -0.5 * math.pi + math.pi * i / BULB_BANDS
        cl, sl = math.cos(lat), math.sin(lat)
        row = []
        for k in range(BULB_SIDES + 1):
            lon = 2.0 * math.pi * k / BULB_SIDES
            p = (BULB_RX * cl * math.cos(lon), BULB_RX * cl * math.sin(lon), BULB_HALF_H * (1.0 + sl))
            n = (cl * math.cos(lon) / BULB_RX, cl * math.sin(lon) / BULB_RX, sl / BULB_HALF_H)
            row.append(mb.vert(p, n, (k / BULB_SIDES, i / BULB_BANDS)))
        rings.append(row)
    for k in range(BULB_SIDES):
        b = mb.vert((0.0, 0.0, 0.0), (0.0, 0.0, -1.0), ((k + 0.5) / BULB_SIDES, 0.0))
        mb.face((b, rings[0][k + 1], rings[0][k]), 0)
        t = mb.vert((0.0, 0.0, 2.0 * BULB_HALF_H), (0.0, 0.0, 1.0), ((k + 0.5) / BULB_SIDES, 1.0))
        mb.face((t, rings[-1][k], rings[-1][k + 1]), 0)
    for i in range(len(rings) - 1):
        for k in range(BULB_SIDES):
            mb.face((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]), 0)
    return mb.build("SM_Bulb", mats)


# ================================================================== materials
def make_materials():
    return {
        "M_Water": C.material("M_Water", "#2C93DD", roughness=0.06, coat=0.5),
        "M_RailRainbow": C.material("M_RailRainbow", "#FFB347", roughness=0.18, coat=0.6),
        "M_RailPink": C.material("M_RailPink", "#F26DC2", roughness=0.16, coat=1.0),
        # round 8 (asset artist, library 15 "glossy multicoloured slide rails"): the slide's bank + rail tube slots get
        # their own Unity materials (MaterialLibrary.Assets.cs) - layered candy pink / amber / hot pink, clear-coat gloss
        "M_RailBand_r8": C.material("M_RailBand_r8", "#FFB357", roughness=0.12, coat=1.0),
        "M_RailTube_r8": C.material("M_RailTube_r8", "#FF79B4", roughness=0.1, coat=1.0),
        "M_SlideShell": C.material("M_SlideShell", "#E79AD6", roughness=0.35),
        "M_DrumWall": C.material("M_DrumWall", "#8E5CC4", metallic=0.55, roughness=0.32),
        "M_Glass": C.material("M_Glass", "#D9F6FF", roughness=0.04, alpha=0.22),
        "M_PipeWater": C.material("M_PipeWater", "#59E6FF", roughness=0.1, emission="#3FD8FF",
                                  emission_strength=1.5),
        "M_Gold": C.material("M_Gold", "#F2B54A", metallic=1.0, roughness=0.22),
        "M_GoldDark": C.material("M_GoldDark", "#B5782A", metallic=1.0, roughness=0.38),
        "M_Bulb": C.material("M_Bulb", "#FFF2C6", roughness=0.2, emission="#FFC86B", emission_strength=8.0),
        "M_DrumRim": C.material("M_DrumRim", "#B79CF0", metallic=0.7, roughness=0.18),
        "M_RimLight": C.material("M_RimLight", "#FFF4FF", roughness=0.2, emission="#F6E8FF", emission_strength=6.0),
    }


# ================================================================== checks
def check(obj):
    me = obj.data
    xs, ys, zs = ([v.co[i] for v in me.vertices] for i in range(3))
    loops_y = len(set(round(y, 4) for y in ys))
    cn = me.corner_normals
    bad = 0
    for p in me.polygons:
        avg = Vector((0.0, 0.0, 0.0))
        for li in p.loop_indices:
            avg += cn[li].vector
        if avg.dot(p.normal) <= 0.0:
            bad += 1
    print("CHECK %s bbox x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f] distinctY=%d polys=%d windingBad=%d slots=%s" % (
        obj.name, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), loops_y, len(me.polygons), bad,
        [m.name for m in me.materials]))


def check_slide_profile(obj):
    """Max deviation of the inner floor/wall vertices from the gameplay formula."""
    worst = 0.0
    for p in obj.data.polygons:
        if p.material_index not in (0, 1):
            continue
        for vi in p.vertices:
            co = obj.data.vertices[vi].co
            a = max(0.0, abs(co.x) - FLAT)
            worst = max(worst, abs(co.z - K * a * a))
    print("CHECK slide inner surface max deviation from z = 0.9(|x|-1.25)^2: %.6f m" % worst)


def export(obj, extra=()):
    C.apply_transforms(obj)
    check(obj)
    C.export_fbx([obj], C.model_path(GROUP, obj.name))
    print("TRIS %s %d" % (obj.name, C.tri_count(obj)))


# ================================================================== previews
def math_out(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for sock, val in ((n.inputs[0], a), (n.inputs[1], b)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            sock.default_value = val
        else:
            nt.links.new(val, sock)
    return n.outputs[0]


def ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    for i, (pos, hexc) in enumerate(stops):
        e = els[i] if i < 2 else els.new(pos)
        e.position = pos
        e.color = C.hex_rgba(hexc)
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def uv_xy(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs[0])
    return sep.outputs[0], sep.outputs[1]


def preview_materials(mats):
    """Preview-only shading driven by the authored UVs (exports already done; Unity remaps by slot name)."""
    # rainbow band: water edge (u = 0) cyan -> yellow -> orange -> pink at the rail (u = 1)
    nt = mats["M_RailRainbow"].node_tree
    u, _ = uv_xy(nt)
    col = ramp(nt, u, [(0.0, "#66D9FF"), (0.2, "#A6F5D2"), (0.4, "#FFE45C"), (0.62, "#FF9E45"),
                       (0.82, "#FF5FA2"), (1.0, "#F25CC4")])
    nt.links.new(col, nt.nodes["Principled BSDF"].inputs["Base Color"])
    # water: flow streaks across u (UV) and along world Y (seamless across tiled preview modules; in Unity the
    # deformer rewrites v with the track distance)
    nt = mats["M_Water"].node_tree
    u, _ = uv_xy(nt)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(math_out(nt, 'MULTIPLY', u, 40.0), comb.inputs["X"])
    nt.links.new(math_out(nt, 'MULTIPLY', sep.outputs[1], 0.35), comb.inputs["Y"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.0
    nz.inputs["Detail"].default_value = 2.0
    nt.links.new(comb.outputs[0], nz.inputs["Vector"])
    col = ramp(nt, nz.outputs["Fac"], [(0.42, "#1677D9"), (0.68, "#4FC3F7")])
    bsdf = nt.nodes["Principled BSDF"]
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.14
    # single-sided glass like Unity (avoids blended back-face sorting artifacts in EEVEE)
    glass = mats["M_Glass"]
    glass.use_backface_culling = True
    for attr in ("use_transparency_overlap", "show_transparent_back"):
        if hasattr(glass, attr):
            setattr(glass, attr, False)
    drum_wall_preview_nodes(mats["M_DrumWall"])
    for name, color, rough in (("M_Gold", "#FFC24A", 0.2), ("M_GoldDark", "#C98A2E", 0.3)):
        b = mats[name].node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = C.hex_rgba(color)
        b.inputs["Roughness"].default_value = rough
    # no bloom in the preview render: a softer emission keeps the marquee bulbs warm instead of clipped white
    mats["M_Bulb"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0
    mats["M_RimLight"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0


HERO_D = 105.5                                   # track distance of the Unity hero shot (mascot); preview y = -(d - 105.5)
FIRST_RING_D = 71.5                              # SceneBuilder.FirstRingDistance (Environment, m1): tunnelStart + 9.5 m
BAND_LEN = RING_SPACING / (RIMS_PER_GAP + 1)     # preview drum wall bands (approximate: Unity splits each gap at RIM_PHASE)


def drum_wall_preview_nodes(mat):
    """Preview of the BWK_DrumWall layout from world position: drum sections between the rims, each with 4 staggered
    rows of slots elongated around the drum, plain metal next to every rim (mirrors the Unity shader's band logic)."""
    nt = mat.node_tree
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    ang = math_out(nt, 'ARCTAN2', sep.outputs[0], math_out(nt, 'SUBTRACT', sep.outputs[2], TUN_ZC))
    around = math_out(nt, 'MULTIPLY', ang, TUN_R)
    dist = math_out(nt, 'SUBTRACT', HERO_D - FIRST_RING_D, sep.outputs[1])          # track distance - first ring
    local = math_out(nt, 'MULTIPLY', math_out(nt, 'FRACT', math_out(nt, 'DIVIDE', dist, BAND_LEN)), BAND_LEN)
    z0, z1, rows = 0.45, BAND_LEN - 0.35, 4.0
    pitch_r = (z1 - z0) / rows
    rc = math_out(nt, 'DIVIDE', math_out(nt, 'SUBTRACT', local, z0), pitch_r)
    inzone = math_out(nt, 'MULTIPLY', math_out(nt, 'GREATER_THAN', rc, 0.0), math_out(nt, 'LESS_THAN', rc, rows))
    row_local = math_out(nt, 'MULTIPLY', math_out(nt, 'SUBTRACT', math_out(nt, 'FRACT', rc), 0.5), pitch_r)
    stagger = math_out(nt, 'MULTIPLY', math_out(nt, 'MODULO', math_out(nt, 'FLOOR', rc), 2.0), 0.5)
    pitch_a, slot_len, slot_w = 0.5, 0.34, 0.12
    ac = math_out(nt, 'ADD', math_out(nt, 'DIVIDE', around, pitch_a), stagger)
    a_local = math_out(nt, 'MULTIPLY', math_out(nt, 'SUBTRACT', math_out(nt, 'FRACT', ac), 0.5), pitch_a)
    hx = math_out(nt, 'MAXIMUM', math_out(nt, 'SUBTRACT', math_out(nt, 'ABSOLUTE', a_local),
                                          slot_len * 0.5 - slot_w * 0.5), 0.0)
    sdf = math_out(nt, 'SUBTRACT', math_out(nt, 'SQRT', math_out(nt, 'ADD', math_out(nt, 'POWER', hx, 2.0),
                                                                 math_out(nt, 'POWER', row_local, 2.0))), slot_w * 0.5)
    # outside the zone: push the SDF far positive (plain metal)
    sdf = math_out(nt, 'ADD', sdf, math_out(nt, 'MULTIPLY', math_out(nt, 'SUBTRACT', 1.0, inzone), 1.0))
    col = ramp(nt, sdf, [(0.0, "#170D30"), (0.012, "#3A2470"), (0.02, "#C6B2FF"), (0.05, "#8F78DA"),
                         (0.3, "#8A70D6")])
    bsdf = nt.nodes["Principled BSDF"]
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.45
    bsdf.inputs["Roughness"].default_value = 0.3


def preview_world():
    """Camera sees the spec background (#2A1B4A, set by bwk_common); reflections and ambient see a warm studio
    gradient so metals and water read as polished gold / glossy water instead of mirroring the dark backdrop."""
    world = bpy.data.worlds.get("PreviewWorld") or bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    z01 = math_out(nt, 'MULTIPLY_ADD', sep.outputs[2], 0.5)     # z * 0.5 + 0.5
    z01.node.inputs[2].default_value = 0.5
    col = ramp(nt, z01, [(0.0, "#2A1B4A"), (0.42, "#7A5AB0"), (0.54, "#FFC99E"), (1.0, "#FFF3E2")])
    env = nt.nodes.new("ShaderNodeBackground")
    env.inputs["Strength"].default_value = 0.9
    nt.links.new(col, env.inputs["Color"])
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(env.outputs[0], mix.inputs[1])
    nt.links.new(bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return env


def render_view(name, cam, target, lens, res, light_scale=1.0, spec=1.0, energy=1.0):
    """bwk_common.render_preview with the same warm key / cool fill / pink rim rig and #2A1B4A background, plus
    control over the rig's specular contribution (glossy water otherwise mirrors the area lights as white squares)."""
    scene = bpy.context.scene
    engine = C.setup_preview_scene()
    temp = C.add_studio_lights(target, light_scale)
    for o in temp:
        o.data.specular_factor = spec
        o.data.energy *= energy
    temp.append(C.add_camera(cam, target, lens))
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    path = C.preview_path(name)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", engine, path)
    for o in temp:
        bpy.data.objects.remove(o, do_unlink=True)


def section_cap(coll):
    """Preview-only cut face for the open module end (the exported module stays open so copies tile)."""
    s_top = wall_len(A_TOP)
    inner = [wall_point(wall_a(s_top * (1.0 - k / 16.0)), +1) for k in range(17)]
    inner += [wall_point(wall_a(s_top * k / 16.0), -1) for k in range(17)]
    shell = [shell_point(wall_a(s_top * k / 8.0), -1) for k in range(8, -1, -1)]
    shell += [shell_point(wall_a(s_top * k / 8.0), +1) for k in range(9)]
    verts = [(x, 0.0, z) for (x, z, _) in inner + shell]
    faces = [list(range(len(verts)))]
    for side in (+1, -1):
        base = len(verts)
        verts += [(side * RAIL_X + RAIL_R * math.cos(2 * math.pi * k / 24), 0.001,
                   RAIL_Z + RAIL_R * math.sin(2 * math.pi * k / 24)) for k in range(24)]
        faces.append(list(range(base, base + 24)))
    me = bpy.data.meshes.new("PV_SectionCap")
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        if p.normal.y < 0.0:
            p.flip()
    obj = bpy.data.objects.new("PV_SectionCap", me)
    coll.objects.link(obj)
    me.materials.append(C.material("PV_Cut", "#F6E3F1", roughness=0.6))
    return obj


def new_collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def inst(src, coll, loc=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), matrix=None):
    o = src.copy()
    o.name = "PV_" + src.name
    coll.objects.link(o)
    if matrix is not None:
        o.matrix_world = matrix
    else:
        o.location, o.rotation_euler = loc, rot
    return o


def ring_layout():
    """Preview y (mascot at 0, travel -Y) of the gold rings and lavender rims exactly as BuildRings places them."""
    rings, rims = [], []
    k0 = int(math.floor((HERO_D - FIRST_RING_D) / RING_SPACING)) - 1
    for k in range(k0, k0 + 12):
        d = FIRST_RING_D + k * RING_SPACING
        rings.append(-(d - HERO_D))
        for r in range(1, RIMS_PER_GAP + 1):
            off = RIM_PHASE * RING_SPACING if RIMS_PER_GAP == 1 else r * BAND_LEN
            rims.append(-(d + off - HERO_D))
    return rings, rims


def mascot_proxy(coll):
    """Rough seated mascot stand-in (scale / framing reference only, never exported)."""
    parts = []
    for name, loc, scale, color in (("PV_Body", (0.0, 0.0, 0.46), (0.44, 0.40, 0.44), "#F28BB5"),
                                    ("PV_Hat", (0.0, 0.03, 0.84), (0.37, 0.37, 0.24), "#7B2FD0"),
                                    ("PV_Pom", (0.0, 0.05, 1.13), (0.19, 0.19, 0.19), "#9B4BF0")):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
        o = bpy.context.active_object
        o.name = name
        o.scale = scale
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        o.data.materials.append(C.material(name + "_M", color, roughness=0.8))
        for p in o.data.polygons:
            p.use_smooth = True
        parts.append(o)
    return parts


def gameplay_camera(back, height, pitch_deg, fov_deg):
    """Rear follow camera like RunnerCameraRig: `back` m behind and `height` m above the slide at the mascot,
    looking along the travel direction pitched down; vertical FOV like Unity."""
    loc = Vector((0.0, back, height))
    p = math.radians(pitch_deg)
    target = loc + Vector((0.0, -math.cos(p), -math.sin(p)))
    cam = C.add_camera(loc, target)
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle_y = math.radians(fov_deg)
    cam.data.clip_start = 0.12
    cam.data.clip_end = 120.0
    return cam


def render_cam(name, cam, res, background="#8A6CD0"):
    scene = bpy.context.scene
    C.setup_preview_scene(background)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    path = C.preview_path(name)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", scene.render.engine, path)


def add_light(coll, name, kind, energy, color, loc, target=None, size=1.0, shadow=True, spec=1.0):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    d.specular_factor = spec
    d.color = C.hex_rgba(color)[:3]
    if kind == 'AREA':
        d.size = size
    else:
        d.shadow_soft_size = size
    d.use_shadow = shadow
    o = bpy.data.objects.new(name, d)
    coll.objects.link(o)
    o.location = loc
    if target is not None:
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def show_only(coll):
    for o in bpy.data.objects:
        o.hide_render = coll not in o.users_collection


def render_previews(a):
    scene = bpy.context.scene
    try:
        scene.eevee.use_raytracing = True
    except Exception:
        pass
    env = preview_world()

    # (a) hero gameplay views: rings + rims exactly where BuildRings puts them around the Unity hero distance,
    # through the RunnerCameraRig framings (portrait 2.75 m / 1.3 m / 10 deg / FOV 58, landscape 2.9 / 1.6 / 9 / 52)
    pa = new_collection("PV_Assembly")
    for i in range(-2, 24):
        inst(a["slide"], pa, (0.0, -LENGTH * i, 0.0))
        inst(a["tunnel"], pa, (0.0, -LENGTH * i + LENGTH * 1.0, 0.0)).visible_shadow = False   # as in Unity
    rings, rims = ring_layout()
    for yr in rings:
        if yr > 8.0:
            continue
        inst(a["ring"], pa, (0.0, yr, TUN_ZC))
        for ang in (35.0, 145.0, 215.0, 325.0):
            er, _ = ring_frame(math.radians(ang))
            add_light(pa, "PV_RingGlow", 'POINT', 18.0, "#FFB45A", Vector((0.0, yr + 0.45, TUN_ZC)) + er * 3.3,
                      size=0.3, shadow=False, spec=0.5)
    for yr in rims:
        if yr > 8.0:
            continue
        inst(a["rim"], pa, (0.0, yr, TUN_ZC))
    mascot_proxy(pa)
    sun = add_light(pa, "PV_Key", 'SUN', 2.2, "#FFE6F2", (0.0, 0.0, 10.0), (0.6, -1.2, 0.0), spec=0.6)
    sun.data.angle = math.radians(8.0)
    add_light(pa, "PV_CharWarm", 'POINT', 25.0, "#FFB861", (0.6, -1.2, 2.3), size=0.5, shadow=False, spec=0.4)
    for yd in (-20.0, -40.0, -62.0):
        add_light(pa, "PV_TunnelDeep", 'POINT', 900.0, "#D9C2FF", (0.0, yd, TUN_ZC), size=1.0, shadow=False,
                  spec=0.4)
    env.inputs["Strength"].default_value = 0.75
    show_only(pa)
    cam9 = gameplay_camera(2.75, 1.3, 10.0, 58.0)
    render_cam("Track_hero_9x16", cam9, (720, 1280))
    cam16 = gameplay_camera(2.9, 1.6, 9.0, 52.0)
    render_cam("Track_hero_16x9", cam16, (1280, 720))
    for o in (cam9, cam16):
        bpy.data.objects.remove(o, do_unlink=True)

    # (b) slide cross-section close-up: preview-only cut face + the gameplay profile curve on the open end
    ps = new_collection("PV_Section")
    inst(a["slide"], ps, (0.0, 0.0, 0.0))
    inst(a["slide"], ps, (0.0, -LENGTH, 0.0))
    section_cap(ps)
    cu = bpy.data.curves.new("PV_GameplayProfile", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.007
    sp = cu.splines.new('POLY')
    xs = [X_TOP - 0.05 * i for i in range(int(round(2 * X_TOP / 0.05)) + 1)]
    sp.points.add(len(xs) - 1)
    for pt, x in zip(sp.points, xs):
        a_ = max(0.0, abs(x) - FLAT)
        pt.co = (x, 0.006, K * a_ * a_, 1.0)
    line = bpy.data.objects.new("PV_GameplayProfile", cu)
    ps.objects.link(line)
    cu.materials.append(C.material("PV_ProfileLine", "#FFFFFF", emission="#FFF36B", emission_strength=6.0))
    env.inputs["Strength"].default_value = 0.8
    show_only(ps)
    render_view("Track_slide_section", (1.15, 5.0, 1.75), (0.0, -0.9, 0.2), 35.0, (1280, 720),
                light_scale=0.9, spec=0.3)

    # (c) ring detail: rope bead, dark channel, bulbs in cups, clamp plate; a lavender rim behind it
    pr = new_collection("PV_Ring")
    inst(a["ring"], pr)
    inst(a["rim"], pr, (0.0, -BAND_LEN, 0.0))
    inst(a["tunnel"], pr, (0.0, 2.0, -TUN_ZC))
    inst(a["tunnel"], pr, (0.0, -2.0, -TUN_ZC))
    add_light(pr, "PV_RingFront", 'POINT', 90.0, "#FFE3B0", (0.6, 1.6, 2.2), size=0.5)
    env.inputs["Strength"].default_value = 0.9
    show_only(pr)
    render_view("Track_ring_detail", (0.9, 2.2, 1.2), (-0.35, -0.6, 3.55), 30.0, (1000, 1000))

    # (d) pipes: module + couplers + elbow + vertical module
    pp = new_collection("PV_Pipes")
    inst(a["pipe"], pp)
    inst(a["coupler"], pp, (0.0, 0.0, 0.0))
    inst(a["coupler"], pp, (0.0, -LENGTH, 0.0))
    inst(a["elbow"], pp, (0.0, -LENGTH, 0.0))
    end = Vector((0.0, -LENGTH - ELBOW_R, ELBOW_R))
    inst(a["coupler"], pp, end, (math.pi / 2, 0.0, 0.0))
    inst(a["pipe"], pp, end, (-math.pi / 2, 0.0, 0.0))
    show_only(pp)
    render_view("Track_pipes", (5.3, 1.9, 2.3), (0.0, -2.6, 1.35), 28.0, (1280, 720), spec=0.7)


# ================================================================== FBX round trip
def verify_fbx(names):
    """Re-import every exported FBX into an empty scene and report what Unity will receive."""
    C.reset_scene()
    for name in names:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=C.model_path(GROUP, name), axis_forward='-Z', axis_up='Y')
        new = [o for o in bpy.data.objects if o not in before]
        bpy.context.view_layer.update()
        for o in (o for o in new if o.type == 'MESH'):
            me, mw = o.data, o.matrix_world
            pts = [mw @ v.co for v in me.vertices]
            bb = " ".join("%s[%.3f, %.3f]" % (ax, min(p[i] for p in pts), max(p[i] for p in pts))
                          for i, ax in enumerate("xyz"))
            tris = sum(len(p.vertices) - 2 for p in me.polygons)
            low = min(range(len(pts)), key=lambda i: pts[i].z)
            n_low = Vector((0.0, 0.0, 0.0))
            for lp in me.loops:
                if lp.vertex_index == low:
                    n_low += mw.to_3x3() @ me.corner_normals[lp.index].vector
            print("FBXCHECK %s tris=%d slots=%s uv=%s %s lowestNormalZ=%.2f empties=%d" % (
                o.name, tris, [m.name for m in me.materials], [u.name for u in me.uv_layers], bb,
                n_low.normalized().z, sum(1 for e in new if e.type == 'EMPTY')))
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)


# ================================================================== main
def main():
    C.reset_scene()
    m = make_materials()
    assets = {
        "slide": build_slide([m["M_Water"], m["M_RailBand_r8"], m["M_RailTube_r8"], m["M_SlideShell"]]),
        "tunnel": build_tunnel([m["M_DrumWall"]]),
        "pipe": build_glass_pipe([m["M_Glass"], m["M_PipeWater"]]),
        "coupler": build_coupler([m["M_Gold"]]),
        "elbow": build_elbow([m["M_Glass"], m["M_PipeWater"]]),
    }
    assets["ring"] = build_ring([m["M_Gold"], m["M_GoldDark"], m["M_Bulb"]])
    assets["rim"] = build_rim([m["M_DrumRim"], m["M_RimLight"]])
    assets["bulb"] = build_bulb([m["M_Bulb"]])
    bpy.context.view_layer.update()

    check_slide_profile(assets["slide"])
    # BWK_TRACK_ONLY=ring,rim (env) re-exports only those FBX files (no churn on unchanged modules)
    only = [k for k in os.environ.get("BWK_TRACK_ONLY", "").split(",") if k]
    for key in ("slide", "tunnel", "pipe", "coupler", "elbow", "ring", "rim", "bulb"):
        if only and key not in only:
            continue
        export(assets[key])
    end_p, end_t = elbow_frames()[-1][0], Vector((0.0, 0.0, 1.0))
    print("CHECK elbow end centre (%.3f, %.3f, %.3f) direction (%.0f, %.0f, %.0f)" % (*end_p, *end_t))
    print("CHECK ring bulbs %d at rho %.3f, bulb centre y %.3f, crown y %.3f" % (
        RING_BULBS, RG_BULB_RHO, BULB_Y, BULB_Y + BULB_H2))
    C.save_work("build_track")
    if os.environ.get("BWK_TRACK_NOPREVIEW"):   # r8: slot-only re-export, previews unchanged
        print("BUILD_TRACK_DONE (no previews)")
        return

    preview_materials(m)
    render_previews(assets)
    verify_fbx(["SM_Slide_Module", "SM_Tunnel_Module", "SM_GlassPipe_Module", "SM_Pipe_Coupler", "SM_Pipe_Elbow",
                "SM_Ring", "SM_DrumRim", "SM_Bulb"])
    print("BUILD_TRACK_DONE")


main()
