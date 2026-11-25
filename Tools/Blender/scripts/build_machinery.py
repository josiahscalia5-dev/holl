"""Bubble Wash Kingdom - washing-machine machinery and side chambers, group "Machinery" (Blender 5.3, headless).

Builds, exports (FBX -> Assets/BubbleWashKingdom/Art/Models/Machinery/) and previews:

  SM_Porthole           side washing chamber set into the tunnel wall, like a washing-machine door: gold frame
                        r 1.25-1.55 x 0.25 (chunky double bead, 12 domed bolts), hinge block (-X), handle (+X),
                        domed glass, drum r 1.22 x 0.9 (normals inward, 3 lifters, door seal) closed by a swirl disc
                        M_Gold, M_GoldDark, M_Glass, M_DrumWall, M_ChamberSwirl       origin frame centre, faces -Y
  SM_BrushRoller        purple core r 0.25 x 3.2 along X with end flanges + 9 tufted bristle discs r ~1.15
                        (pink / blue / white), colour attribute Col = root shade      origin centre, rotation axis X
                        M_MetalPurple, M_BrushPink, M_BrushBlue, M_BrushWhite
  SM_ControlPanel       rounded pink console 2.4 x 1.4 x 0.8: gold-framed screen with a raised glowing t-shirt icon,
                        3 domed buttons, gold dial, 2 status lights, lavender plinth / lid / trim
                        M_MachinePink, M_MachineLavender, M_Screen, M_ButtonCyan, M_ButtonYellow, M_ButtonPink, M_Gold
  SM_Agitator           tapered column 3.0 m with flared skirt, 4 curved spiral fins, gold cap
                        M_PlasticWhite, M_MachineLavender, M_Gold                     origin base, axis Z
  SM_GoldPipe_Straight  2 m along -Y, r 0.14, bolted flanges at both ends            M_Gold  origin at the y = 0 end
  SM_GoldPipe_Elbow     90 deg, r 0.14, bend r 0.42: starts at (0,0,0) heading -Y, ends at (0,-0.5,0.5) heading +Z
                        flanges at both ends                                          M_Gold
  SM_ValveWheel         gold hand wheel r 0.3, 5 spokes, axis Y (faces -Y), stem along +Y   M_Gold, M_GoldDark
  SM_Pillar             lavender column r 0.55 x 6.0, 3 gold bands, gold medallion with a raised paw print on -Y
                        M_MachineLavender, M_Gold, M_GoldDark                         origin base

Every surface is revolved or swept from analytic profiles (deterministic, seeded tufts); smooth shading with
sharp edges above 40 degrees. Conventions (Docs/AssetSpec.md): meters, Z up, front = -Y, right side = -X.

Run from the project root:
  blender --background --factory-startup --python Tools/Blender/scripts/build_machinery.py
Optional: set BWK_REVIEW_DIR=<folder> to also render extra close-up review images there.
"""
import bisect
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bwk_common as C  # noqa: E402

GROUP = "Machinery"
TAU = 2.0 * math.pi
V_TILE = 4.0                      # v = meters / 4 where the spec asks for it (drum wall, pipes)
X_AXIS, Y_AXIS, Z_AXIS = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0))
FRONT = Vector((0.0, -1.0, 0.0))  # asset front
DRUM_U_SPAN = 16.0 / 56.0         # porthole drum u range: same perforation size as SM_Tunnel_Module (56 per u)
REVIEW_DIR = os.environ.get("BWK_REVIEW_DIR")
ASSET_NAMES = ["SM_Porthole", "SM_BrushRoller", "SM_ControlPanel", "SM_Agitator", "SM_GoldPipe_Straight",
               "SM_GoldPipe_Elbow", "SM_ValveWheel", "SM_Pillar"]


# ================================================================== mesh building
def newell(pts):
    n = Vector((0.0, 0.0, 0.0))
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    return n


class MB:
    """Mesh builder: shared vertices, per-corner UVs, per-face material index, optional per-vertex colour."""

    def __init__(self):
        self.co, self.vc = [], []
        self.faces, self.fmat, self.fuv = [], [], []

    def v(self, co, col=None):
        self.co.append(Vector(co))
        self.vc.append(col)
        return len(self.co) - 1

    def f(self, idx, mat, uvs, ref=None):
        """Add a face; repeated corners (poles) collapse; `ref` orients the face to agree with that direction."""
        keep_i, keep_uv = [], []
        for i, uv in zip(idx, uvs):
            if i not in keep_i:
                keep_i.append(i)
                keep_uv.append((float(uv[0]), float(uv[1])))
        if len(keep_i) < 3:
            return
        if ref is not None and newell([self.co[i] for i in keep_i]).dot(Vector(ref)) < 0.0:
            keep_i.reverse()
            keep_uv.reverse()
        self.faces.append(tuple(keep_i))
        self.fmat.append(mat)
        self.fuv.append(keep_uv)

    def tris(self):
        return sum(len(f) - 2 for f in self.faces)

    def build(self, name, mats, sharp_deg=40.0, with_col=False, weld=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata([c[:] for c in self.co], [], self.faces)
        if len(me.polygons) != len(self.faces):
            raise RuntimeError("%s: from_pydata dropped faces" % name)
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", [c for uvs in self.fuv for uv in uvs for c in uv])
        if with_col:
            ca = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
            flat = []
            for face in self.faces:
                for i in face:
                    flat.extend(self.vc[i] if self.vc[i] is not None else (1.0, 1.0, 1.0, 1.0))
            ca.data.foreach_set("color_srgb", flat)
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        C.assign_materials(obj, mats)
        me.polygons.foreach_set("material_index", self.fmat)
        if weld:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bm.to_mesh(me)
            bm.free()
        me.shade_smooth()
        if sharp_deg is not None:
            me.set_sharp_from_angle(angle=math.radians(sharp_deg))
        me.update()
        return obj


def arclen_norm(pts2):
    acc = [0.0]
    for a, b in zip(pts2, pts2[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = acc[-1] or 1.0
    return [x / tot for x in acc]


def arclen(pts2):
    acc = [0.0]
    for a, b in zip(pts2, pts2[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return acc


def frame_basis(axis, e1=None):
    """Right-handed (e1, e2, A): e1 x e2 = A."""
    A = Vector(axis).normalized()
    if e1 is None:
        e1 = X_AXIS if abs(A.x) < 0.9 else Y_AXIS
    e1 = (Vector(e1) - A * Vector(e1).dot(A)).normalized()
    return A, e1, A.cross(e1)


def fix_wrap(uvs):
    us = [u for u, _ in uvs]
    if max(us) - min(us) > 0.5:
        return [((u + 1.0) if u < 0.5 else u, v) for u, v in uvs]
    return uvs


def lathe(mb, prof, mat, segs, origin=(0.0, 0.0, 0.0), axis=(0.0, 0.0, 1.0), e1=None, closed=False, mats=None,
          u_span=1.0, v_vals=None, uv_fn=None, col_fn=None, phi0=0.0, r_mod=None):
    """Revolve [(r, h), ...] around `axis` (point = O + A h + (e1 cos phi + e2 sin phi) r).
    The profile runs counter-clockwise in (r right, h up) - solid on its left - so normals face outward.
    r = 0 points become poles. u = around (0..u_span), v = profile arc length 0..1 unless v_vals / uv_fn given."""
    A, e1, e2 = frame_basis(axis, e1)
    O = Vector(origin)
    pts = list(prof) + ([prof[0]] if closed else [])
    if v_vals is None:
        v_vals = arclen_norm(pts)
    rows = []
    for pi, (r, h) in enumerate(prof):
        if r < 1e-7:
            p = O + A * h
            i = mb.v(p, col_fn(p) if col_fn else None)
            rows.append([i] * segs)
            continue
        row = []
        for j in range(segs):
            phi = phi0 + TAU * j / segs
            rr = r * (r_mod(phi, pi) if r_mod else 1.0)
            p = O + A * h + (e1 * math.cos(phi) + e2 * math.sin(phi)) * rr
            row.append(mb.v(p, col_fn(p) if col_fn else None))
        rows.append(row)
    if closed:
        rows.append(rows[0])
    for i in range(len(pts) - 1):
        m = mats[i] if mats is not None else mat
        for j in range(segs):
            j1 = (j + 1) % segs
            idx = [rows[i][j], rows[i][j1], rows[i + 1][j1], rows[i + 1][j]]
            if uv_fn:
                uvs = fix_wrap([uv_fn(mb.co[k]) for k in idx])
            else:
                ua, ub = u_span * j / segs, u_span * (j + 1) / segs
                uvs = [(ua, v_vals[i]), (ub, v_vals[i]), (ub, v_vals[i + 1]), (ua, v_vals[i + 1])]
            mb.f(idx, m, uvs)
    return rows


def sweep(mb, frames, prof, mat, closed_path=False, closed_prof=False, u_vals=None, v_vals=None, cap0=False,
          cap1=False, mats=None, profs=None, uv_fn=None, swap_uv=False, col_fn=None):
    """Sweep a 2D profile along frames [(P, N, B)] with N x B = direction of travel; vertex = P + N a + B b.
    The profile runs counter-clockwise in (a, b) (solid on its left) so normals face outward.
    `profs` gives one profile per frame (same point count). u = along the path, v = across the profile."""
    rows = []
    for fi, (P, N, B) in enumerate(frames):
        pr = profs[fi] if profs is not None else prof
        row = []
        for (a, b) in pr:
            p = P + N * a + B * b
            row.append(mb.v(p, col_fn(p) if col_fn else None))
        rows.append(row)
    pr0 = profs[0] if profs is not None else prof
    nf, npf = len(frames), len(pr0)
    if u_vals is None:
        Ps = [fr[0] for fr in frames] + ([frames[0][0]] if closed_path else [])
        acc = [0.0]
        for a, b in zip(Ps, Ps[1:]):
            acc.append(acc[-1] + (b - a).length)
        u_vals = [x / (acc[-1] or 1.0) for x in acc]
    if v_vals is None:
        v_vals = arclen_norm(list(pr0) + ([pr0[0]] if closed_prof else []))
    path_pairs = [(i, i + 1) for i in range(nf - 1)] + ([(nf - 1, 0)] if closed_path else [])
    prof_pairs = [(k, k + 1) for k in range(npf - 1)] + ([(npf - 1, 0)] if closed_prof else [])
    for pi, (i, i1) in enumerate(path_pairs):
        ua, ub = u_vals[pi], u_vals[pi + 1]
        for ki, (k, k1) in enumerate(prof_pairs):
            va, vb = v_vals[ki], v_vals[ki + 1]
            idx = [rows[i][k], rows[i][k1], rows[i1][k1], rows[i1][k]]
            if uv_fn:
                uvs = [uv_fn(mb.co[q]) for q in idx]
            elif swap_uv:
                uvs = [(va, ua), (vb, ua), (vb, ub), (va, ub)]
            else:
                uvs = [(ua, va), (ua, vb), (ub, vb), (ub, va)]
            mb.f(idx, mats[ki] if mats is not None else mat, uvs)
    for cap, fi, sgn in ((cap0, 0, -1), (cap1, nf - 1, 1)):
        if not cap:
            continue
        P, N, B = frames[fi]
        pr = profs[fi] if profs is not None else prof
        ca = sum(a for a, _ in pr) / npf
        cb = sum(b for _, b in pr) / npf
        c = mb.v(P + N * ca + B * cb)
        span = max(max(abs(a - ca), abs(b - cb)) for a, b in pr) * 2.0 or 1.0
        for k in range(npf):
            k1 = (k + 1) % npf
            idx = [c, rows[fi][k1], rows[fi][k]] if sgn < 0 else [c, rows[fi][k], rows[fi][k1]]
            uvs = []
            for q in idx:
                d = mb.co[q] - P
                uvs.append((0.5 + (d.dot(N) - ca) / span, 0.5 + (d.dot(B) - cb) / span))
            mb.f(idx, mat, uvs)
    return rows


def path_frames(points, up_fn, closed=False):
    """Frames (P, N, B): T from neighbours, N = up_fn(i) made perpendicular to T, B = T x N (so N x B = T)."""
    n = len(points)
    out = []
    for i in range(n):
        if closed:
            t = points[(i + 1) % n] - points[(i - 1) % n]
        else:
            t = points[min(i + 1, n - 1)] - points[max(i - 1, 0)]
        T = t.normalized()
        up = Vector(up_fn(i))
        N = (up - T * up.dot(T)).normalized()
        out.append((points[i], N, T.cross(N)))
    return out


def circle2(r, n, phase=0.0):
    return [(r * math.cos(phase + TAU * k / n), r * math.sin(phase + TAU * k / n)) for k in range(n)]


def chaikin(pts, iters):
    for _ in range(iters):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            out.append(a * 0.75 + b * 0.25)
            out.append(a * 0.25 + b * 0.75)
        pts = out
    return pts


def catmull_rom(points, n_per_seg):
    P = [Vector(p) for p in points]
    ext = [P[0] * 2.0 - P[1]] + P + [P[-1] * 2.0 - P[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(n_per_seg):
            t = k / n_per_seg
            out.append(0.5 * ((p1 * 2.0) + (p2 - p0) * t + (p0 * 2.0 - p1 * 5.0 + p2 * 4.0 - p3) * (t * t)
                              + (p1 * 3.0 - p0 - p2 * 3.0 + p3) * (t * t * t)))
    out.append(P[-1])
    return out


def add_bm(mb, bm, offset, mat, uv_scale=1.0):
    """Copy a bmesh into the builder with box-projected UVs (meters / uv_scale)."""
    bm.verts.index_update()
    bm.normal_update()
    ids = [mb.v(v.co + offset) for v in bm.verts]
    for fc in bm.faces:
        n = fc.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        ia, ib = ((1, 2), (0, 2), (0, 1))[ax]
        idx = [ids[lp.vert.index] for lp in fc.loops]
        mb.f(idx, mat, [(mb.co[i][ia] / uv_scale, mb.co[i][ib] / uv_scale) for i in idx])


def rounded_box(mb, center, size, radius, segs, mat):
    """Box with every edge bevelled (profile 0.5 = round) - soft toy-like plastic blocks."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=radius, offset_type='OFFSET',
                    segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    add_bm(mb, bm, Vector(center), mat)
    bm.free()


def raised_shape(mb, outline, origin, axis, e1, mat, h0, h1, h2, h_top, inset):
    """Raised emblem: closed 2D outline (e1/e2 coords) with a vertical side h0->h1, a rounded inset edge
    h1->h2 and a slightly domed top (fan to h_top)."""
    A, e1, e2 = frame_basis(axis, e1)
    O = Vector(origin)
    pts = [Vector((p[0], p[1])) for p in outline]
    n = len(pts)
    area = sum(pts[i].x * pts[(i + 1) % n].y - pts[(i + 1) % n].x * pts[i].y for i in range(n))
    if area < 0.0:
        pts.reverse()
    nrm = []
    for i in range(n):
        t = (pts[(i + 1) % n] - pts[(i - 1) % n]).normalized()
        nrm.append(Vector((t.y, -t.x)))          # outward for a counter-clockwise outline
    cen = sum(pts, Vector((0.0, 0.0))) / n
    ins = [p - q * inset for p, q in zip(pts, nrm)]

    def p3(p, h):
        return O + e1 * p.x + e2 * p.y + A * h

    rings = [[mb.v(p3(p, h0)) for p in pts], [mb.v(p3(p, h1)) for p in pts], [mb.v(p3(p, h2)) for p in ins]]
    c = mb.v(p3(cen, h_top))

    def uv(i):
        d = mb.co[i] - O
        return (0.5 + d.dot(e1) * 2.0, 0.5 + d.dot(e2) * 2.0)

    for r in range(2):
        for i in range(n):
            i1 = (i + 1) % n
            q = [rings[r][i], rings[r][i1], rings[r + 1][i1], rings[r + 1][i]]
            nn = nrm[i] + nrm[i1]
            ref = e1 * nn.x + e2 * nn.y + A * (0.0 if r == 0 else 0.8)
            mb.f(q, mat, [uv(k) for k in q], ref=ref)
    for i in range(n):
        q = [c, rings[2][i], rings[2][(i + 1) % n]]
        mb.f(q, mat, [uv(k) for k in q], ref=A)


def rounded_rect_path(cx, cz, w, h, rc, cseg, y):
    """Rounded rectangle in the XZ plane at depth y, clockwise as seen from the front (top edge runs toward +X).
    Returns points and in-plane outward normals."""
    pts, nrm = [], []
    corners = ((cx + w / 2 - rc, cz + h / 2 - rc, 90.0, 0.0), (cx + w / 2 - rc, cz - h / 2 + rc, 0.0, -90.0),
               (cx - w / 2 + rc, cz - h / 2 + rc, -90.0, -180.0), (cx - w / 2 + rc, cz + h / 2 - rc, 180.0, 90.0))
    for (ox, oz, a0, a1) in corners:
        for k in range(cseg + 1):
            a = math.radians(a0 + (a1 - a0) * k / cseg)
            nv = Vector((math.cos(a), 0.0, math.sin(a)))
            pts.append(Vector((ox, y, oz)) + nv * rc)
            nrm.append(nv)
    return pts, nrm


# ================================================================== materials
def make_materials():
    """Slot names are the Unity remap contract; colours sampled from the reference frames (median of masked
    patches) or matched to the Track group where the slot is shared (gold, glass, drum wall)."""
    mk = C.material
    return {
        "M_Gold": mk("M_Gold", "#F2B54A", metallic=1.0, roughness=0.22),
        "M_GoldDark": mk("M_GoldDark", "#B5782A", metallic=1.0, roughness=0.38),
        "M_Glass": mk("M_Glass", "#D9F6FF", roughness=0.04, alpha=0.22),
        "M_DrumWall": mk("M_DrumWall", "#8E5CC4", metallic=0.55, roughness=0.32),
        "M_ChamberSwirl": mk("M_ChamberSwirl", "#8FD8FF", roughness=0.2, emission="#8FD8FF", emission_strength=0.8),
        "M_BrushPink": mk("M_BrushPink", "#E162B1", roughness=0.9),
        "M_BrushBlue": mk("M_BrushBlue", "#6CB2D7", roughness=0.9),
        "M_BrushWhite": mk("M_BrushWhite", "#F1EAF6", roughness=0.9),
        "M_MetalPurple": mk("M_MetalPurple", "#7E4FA6", metallic=0.65, roughness=0.3),
        "M_MachinePink": mk("M_MachinePink", "#E86FB3", roughness=0.32, coat=0.6),
        "M_MachineLavender": mk("M_MachineLavender", "#D894D8", roughness=0.35, coat=0.4),
        "M_PlasticWhite": mk("M_PlasticWhite", "#F5EFF8", roughness=0.3, coat=0.4),
        "M_Screen": mk("M_Screen", "#5F86B6", roughness=0.15, emission="#4F82C8", emission_strength=0.5),
        "M_ButtonCyan": mk("M_ButtonCyan", "#63C6F0", roughness=0.15, emission="#4FD6FF", emission_strength=1.2,
                           coat=1.0),
        "M_ButtonYellow": mk("M_ButtonYellow", "#F5DC33", roughness=0.15, emission="#FFD21F",
                             emission_strength=0.7, coat=1.0),
        "M_ButtonPink": mk("M_ButtonPink", "#FF62AE", roughness=0.15, emission="#FF4FA6", emission_strength=0.7,
                           coat=1.0),
    }


def slots(M, names):
    return [M[n] for n in names]


# ================================================================== 1. porthole + side chamber
def build_porthole(M):
    mb = MB()
    G, GD, GL, DW, SW = range(5)
    O = Vector((0.0, 0.0, 0.0))
    # frame ring around -Y (h = -y): flat back on the wall (h = -0.125), outer wall r 1.55, big front bead
    # (apex h = +0.125), V groove, small inner bead that holds the glass, bore r 1.25
    prof = [(1.25, -0.125), (1.55, -0.125)]
    for k in range(11):
        t = math.pi * k / 10
        prof.append((1.435 + 0.115 * math.cos(t), 0.125 * math.sin(t)))
    for k in range(1, 7):
        t = math.pi * k / 6
        prof.append((1.285 + 0.035 * math.cos(t), 0.075 * math.sin(t)))
    lathe(mb, prof, G, 64, O, FRONT, X_AXIS, closed=True)
    # 12 domed bolt heads on the bead apex
    bolt = [(0.048, -0.02), (0.048, 0.008), (0.038, 0.026), (0.018, 0.034), (0.0, 0.035)]
    for k in range(12):
        phi = math.radians(15.0 + 30.0 * k)
        lathe(mb, bolt, G, 8, (1.435 * math.cos(phi), -0.125, 1.435 * math.sin(phi)), FRONT, X_AXIS)
    # slightly domed glass (spherical cap, edge hidden inside the inner bead), planar UVs
    sag_r = (1.28 ** 2 + 0.093 ** 2) / (2.0 * 0.093)

    def dome_h(r):
        return 0.105 - (sag_r - math.sqrt(sag_r * sag_r - r * r))
    glass = [(r, dome_h(r)) for r in (1.28, 1.05, 0.8, 0.55, 0.28)] + [(0.0, dome_h(0.0))]
    lathe(mb, glass, GL, 48, O, FRONT, X_AXIS, uv_fn=lambda p: (0.5 + p.x / 2.56, 0.5 + p.z / 2.56))
    # rolled door seal at the drum mouth (hides the frame / drum gap)
    seal = [(1.262, -0.012), (1.225, -0.018), (1.192, -0.035), (1.175, -0.065), (1.185, -0.097), (1.212, -0.118),
            (1.228, -0.13)]
    lathe(mb, seal, GD, 48, O, FRONT, X_AXIS)
    # drum: r 1.22, y 0 -> 0.9, normals inward; u around (tunnel perforation density), v = depth / 4
    lathe(mb, [(1.22, 0.0), (1.22, -0.45), (1.22, -0.9)], DW, 48, O, FRONT, X_AXIS, u_span=DRUM_U_SPAN,
          v_vals=[0.0, 0.45 / V_TILE, 0.9 / V_TILE])

    def drum_uv(p):
        a = math.atan2(p.z, p.x) % TAU
        return (a / TAU * DRUM_U_SPAN, p.y / V_TILE)
    # 3 lifter ribs inside the drum (washing-machine paddles), tapered ends
    rib = [(0.08, -0.012), (0.07, 0.035), (0.04, 0.075), (0.0, 0.088), (-0.04, 0.075), (-0.07, 0.035),
           (-0.08, -0.012)]
    ys = [0.86, 0.8, 0.68, 0.5, 0.32, 0.2, 0.14]          # back -> front (N x B = -Y = travel)
    sc = [0.0, 0.75, 1.0, 1.0, 1.0, 0.75, 0.0]
    for phi_deg in (90.0, 210.0, 330.0):
        phi = math.radians(phi_deg)
        R = Vector((math.cos(phi), 0.0, math.sin(phi)))
        Tg = Vector((-math.sin(phi), 0.0, math.cos(phi)))
        frames = [(R * 1.22 + Vector((0.0, y, 0.0)), Tg, -R) for y in ys]
        profs = [[(a * (0.6 + 0.4 * s), -0.012 + (b + 0.012) * s) for a, b in rib] for s in sc]
        sweep(mb, frames, None, DW, profs=profs, uv_fn=drum_uv)
    # back disc: shallow whirlpool, faces the viewer, planar UVs with (0.5, 0.5) at the centre
    rd = 1.225

    def disc_h(r):
        return -0.90 - 0.12 * (1.0 - (r / rd) ** 2) ** 2
    disc = [(r, disc_h(r)) for r in (1.225, 1.0, 0.75, 0.5, 0.25)] + [(0.0, disc_h(0.0))]
    lathe(mb, disc, SW, 48, O, FRONT, X_AXIS, uv_fn=lambda p: (0.5 + p.x / (2.0 * rd), 0.5 + p.z / (2.0 * rd)))
    # hinge (-X, the viewer's left): rounded block + barrel with two dark knuckle grooves and domed ends
    rounded_box(mb, (-1.62, 0.0, 0.0), (0.26, 0.20, 0.56), 0.05, 3, G)
    barrel = [(0.0, -0.34), (0.05, -0.336), (0.076, -0.318), (0.085, -0.29), (0.085, -0.13), (0.07, -0.12),
              (0.07, -0.08), (0.085, -0.07), (0.085, 0.07), (0.07, 0.08), (0.07, 0.12), (0.085, 0.13), (0.085, 0.29),
              (0.076, 0.318), (0.05, 0.336), (0.0, 0.34)]
    bmats = [G, G, G, G, GD, GD, GD, G, GD, GD, GD, G, G, G, G]
    lathe(mb, barrel, G, 14, (-1.80, -0.02, 0.0), Z_AXIS, X_AXIS, mats=bmats)
    # handle (+X): mount block, two dark posts, vertical capsule grip
    rounded_box(mb, (1.575, 0.0, 0.0), (0.17, 0.16, 0.46), 0.045, 3, G)
    for zz in (-0.15, 0.15):
        pts = [Vector((1.62, 0.0, zz)), Vector((1.71, 0.0, zz)), Vector((1.80, 0.0, zz))]
        sweep(mb, path_frames(pts, lambda i: Z_AXIS), circle2(0.034, 8), GD, closed_prof=True, swap_uv=True)
    grip = [(0.0, -0.27), (0.03, -0.262), (0.048, -0.24), (0.055, -0.21), (0.055, 0.21), (0.048, 0.24),
            (0.03, 0.262), (0.0, 0.27)]
    lathe(mb, grip, G, 12, (1.82, 0.0, 0.0), Z_AXIS, X_AXIS)
    obj = mb.build("SM_Porthole", slots(M, ["M_Gold", "M_GoldDark", "M_Glass", "M_DrumWall", "M_ChamberSwirl"]))
    return obj


# ================================================================== 2. brush roller
def brush_uv(p, phi_ref=None):
    r = math.hypot(p.y, p.z)
    phi = math.atan2(p.z, p.y)
    if phi_ref is not None:
        phi = phi_ref + ((phi - phi_ref + math.pi) % TAU - math.pi)
    elif phi < 0.0:
        phi += TAU
    return (phi / TAU, min(max((r - 0.25) / 0.95, 0.0), 1.0))


def brush_col(p):
    """Root shade (purple-grey at the core -> white at the tips) for the Col attribute."""
    v = min(max((math.hypot(p.y, p.z) - 0.25) / 0.95, 0.0), 1.0)
    s = v * v * (3.0 - 2.0 * v)
    return (0.56 + 0.44 * s, 0.50 + 0.50 * s, 0.64 + 0.36 * s, 1.0)


def add_tuft(mb, base, d, side, length, w, t, curl, mat, phi_ref):
    """Soft 4-sided bristle clump: base ring (embedded), bulging mid ring, curled tip. 12 triangles."""
    d = d.normalized()
    ax = d.cross(side).normalized()
    side = ax.cross(d).normalized()
    rings = []
    for f, s in ((0.0, 1.0), (0.52, 0.80)):
        c = base + d * (length * f) + curl * (f * f)
        ring = [c + side * (w * s), c + ax * (t * s), c - side * (w * s), c - ax * (t * s)]
        rings.append([mb.v(p, brush_col(p)) for p in ring])
    tip = base + d * length + curl
    tip_id = mb.v(tip, brush_col(tip))
    for k in range(4):
        k1 = (k + 1) % 4
        q = [rings[0][k], rings[0][k1], rings[1][k1], rings[1][k]]
        mb.f(q, mat, [brush_uv(mb.co[i], phi_ref) for i in q])
        tri = [rings[1][k], rings[1][k1], tip_id]
        mb.f(tri, mat, [brush_uv(mb.co[i], phi_ref) for i in tri])


def build_brush_roller(M):
    mb = MB()
    rng = random.Random(20261125)
    MP, PINK, BLUE, WHITE = range(4)
    # core (h = x): axle stubs, end flanges r 0.455 (the lavender-purple ring of the reference), shaft r 0.25
    half = [(0.0, -1.6), (0.15, -1.6), (0.18, -1.575), (0.18, -1.55), (0.43, -1.545), (0.455, -1.52),
            (0.455, -1.49), (0.43, -1.465), (0.25, -1.46)]
    core = half + [(r, -h) for r, h in reversed(half)]
    lathe(mb, core, MP, 20, (0.0, 0.0, 0.0), X_AXIS, Y_AXIS, v_vals=[s / V_TILE for s in arclen(core)])
    # 9 discs: plush lens body + 34 rim tufts (alternating splay) + 2 x 12 shoulder tufts
    body = [(0.245, -0.12), (0.55, -0.155), (0.80, -0.12), (0.93, 0.0), (0.80, 0.12), (0.55, 0.155), (0.245, 0.12)]
    pitch = 2.6 / 8.0
    for k in range(9):
        xc = -1.3 + pitch * k
        mat = (PINK, BLUE, WHITE)[k % 3]
        phase = rng.uniform(0.0, TAU)
        lathe(mb, body, mat, 24, (xc, 0.0, 0.0), X_AXIS, Y_AXIS, phi0=phase, uv_fn=brush_uv, col_fn=brush_col)
        n_rim = 34
        for i in range(n_rim):
            phi = phase + TAU * (i + rng.uniform(-0.3, 0.3)) / n_rim
            Rv = Vector((0.0, math.cos(phi), math.sin(phi)))
            Tv = Vector((0.0, -math.sin(phi), math.cos(phi)))
            a = (0.055 if i % 2 == 0 else -0.055) + rng.uniform(-0.015, 0.015)
            r0 = rng.uniform(0.64, 0.70)
            tilt = (a / 0.055) * 0.10 + rng.uniform(-0.06, 0.06)
            d = (Rv + X_AXIS * tilt + Tv * (0.10 + rng.uniform(-0.05, 0.05))).normalized()
            length = (rng.uniform(1.05, 1.20) - r0) / d.dot(Rv)
            curl = Tv * rng.uniform(0.03, 0.07) + X_AXIS * (a * 0.4)
            add_tuft(mb, Vector((xc + a, 0.0, 0.0)) + Rv * r0, d, Tv, length, rng.uniform(0.085, 0.10),
                     rng.uniform(0.058, 0.07), curl, mat, phi)
        for sgn in (-1.0, 1.0):
            for i in range(12):
                phi = phase + TAU * (i + 0.5 + rng.uniform(-0.25, 0.25)) / 12
                Rv = Vector((0.0, math.cos(phi), math.sin(phi)))
                Tv = Vector((0.0, -math.sin(phi), math.cos(phi)))
                tilt = math.radians(rng.uniform(16.0, 26.0))
                d = (Rv * math.cos(tilt) + X_AXIS * (sgn * math.sin(tilt))
                     + Tv * (0.08 + rng.uniform(-0.04, 0.04))).normalized()
                add_tuft(mb, Vector((xc + sgn * 0.08, 0.0, 0.0)) + Rv * rng.uniform(0.48, 0.58), d, Tv,
                         rng.uniform(0.27, 0.34), 0.09, 0.062, Tv * 0.04 + X_AXIS * (sgn * 0.02), mat, phi)
    return mb.build("SM_BrushRoller", slots(M, ["M_MetalPurple", "M_BrushPink", "M_BrushBlue", "M_BrushWhite"]),
                    with_col=True)


# ================================================================== 3. control panel
def build_control_panel(M):
    mb = MB()
    PINK, LAV, SCR, CY, YE, PK, GO = range(7)
    yf = -0.40                                             # front face of the body
    rounded_box(mb, (0.0, 0.0, 0.71), (2.4, 0.8, 1.22), 0.14, 4, PINK)       # body z 0.10..1.32
    rounded_box(mb, (0.0, 0.0, 0.08), (2.48, 0.88, 0.16), 0.05, 3, LAV)      # plinth
    rounded_box(mb, (0.0, 0.0, 1.345), (2.34, 0.74, 0.11), 0.05, 3, LAV)     # lid, top at z 1.40
    rounded_box(mb, (0.0, yf + 0.002, 0.30), (2.0, 0.035, 0.07), 0.015, 2, LAV)  # front trim bar
    # screen: chunky gold bezel swept around a rounded rectangle, glowing screen, raised t-shirt icon
    sx, sz = -0.50, 0.79
    path, nrm = rounded_rect_path(sx, sz, 0.93, 0.69, 0.13, 6, yf)
    frames = path_frames(path, lambda i: nrm[i], closed=True)
    if frames[0][2].dot(FRONT) < 0.0:
        path.reverse()
        nrm.reverse()
        frames = path_frames(path, lambda i: nrm[i], closed=True)
    bezel = [(0.035, -0.01), (0.035, 0.022), (0.022, 0.045), (0.0, 0.052), (-0.022, 0.045), (-0.035, 0.022),
             (-0.035, -0.01)]
    sweep(mb, frames, bezel, GO, closed_path=True)
    ring, _ = rounded_rect_path(sx, sz, 0.88, 0.64, 0.11, 6, yf - 0.012)
    c = mb.v((sx, yf - 0.012, sz))
    ids = [mb.v(p) for p in ring]

    def scr_uv(p):
        return ((p.x - (sx - 0.44)) / 0.88, (p.z - (sz - 0.32)) / 0.64)
    for i in range(len(ids)):
        tri = [c, ids[i], ids[(i + 1) % len(ids)]]
        mb.f(tri, SCR, [scr_uv(mb.co[q]) for q in tri], ref=FRONT)
    shirt = [(0.0, 0.30), (0.13, 0.42), (0.30, 0.42), (0.52, 0.20), (0.40, 0.06), (0.28, 0.16), (0.28, -0.45),
             (-0.28, -0.45), (-0.28, 0.16), (-0.40, 0.06), (-0.52, 0.20), (-0.30, 0.42), (-0.13, 0.42)]
    pts2 = chaikin([Vector(p) for p in shirt], 2)
    pts3 = [Vector((sx + p.x * 0.42, yf - 0.016, sz + 0.005 + p.y * 0.42)) for p in pts2]
    sweep(mb, path_frames(pts3, lambda i: FRONT, closed=True), circle2(0.016, 6), CY, closed_path=True,
          closed_prof=True, swap_uv=True)
    # three domed glowing buttons in lavender bezels (yellow, cyan, pink - as in the reference)
    bez = [(0.155, -0.01), (0.155, 0.012), (0.147, 0.026), (0.133, 0.03), (0.12, 0.024), (0.116, -0.005)]
    dome = [(0.118, -0.005), (0.117, 0.02), (0.105, 0.05), (0.08, 0.071), (0.045, 0.083), (0.0, 0.087)]
    for bx, mat in ((0.22, YE), (0.55, CY), (0.88, PK)):
        cc = (bx, yf, 0.55)
        lathe(mb, bez, LAV, 24, cc, FRONT, X_AXIS)
        lathe(mb, dome, mat, 24, cc, FRONT, X_AXIS)
    # gold dial: lavender base plate, knurled knob (12 grip flutes), pointer bar
    cc = (0.55, yf, 0.98)
    lathe(mb, [(0.20, -0.01), (0.20, 0.008), (0.19, 0.016), (0.0, 0.016)], LAV, 32, cc, FRONT, X_AXIS)
    knob = [(0.135, 0.01), (0.135, 0.075), (0.128, 0.092), (0.11, 0.10), (0.0, 0.10)]
    lathe(mb, knob, GO, 48, cc, FRONT, X_AXIS,
          r_mod=lambda phi, i: (1.0 - 0.05 * (0.5 + 0.5 * math.cos(12.0 * phi))) if i < 3 else 1.0)
    rounded_box(mb, (0.55, yf - 0.112, 0.98 + 0.055), (0.035, 0.03, 0.10), 0.012, 2, GO)
    # two little status lights beside the dial
    led_bez = [(0.055, -0.01), (0.055, 0.008), (0.048, 0.016), (0.04, 0.012), (0.038, -0.005)]
    led = [(0.04, -0.005), (0.04, 0.012), (0.03, 0.03), (0.015, 0.038), (0.0, 0.04)]
    for lx, mat in ((0.20, CY), (0.90, PK)):
        cc = (lx, yf, 0.98)
        lathe(mb, led_bez, LAV, 16, cc, FRONT, X_AXIS)
        lathe(mb, led, mat, 16, cc, FRONT, X_AXIS)
    return mb.build("SM_ControlPanel", slots(M, ["M_MachinePink", "M_MachineLavender", "M_Screen", "M_ButtonCyan",
                                                "M_ButtonYellow", "M_ButtonPink", "M_Gold"]))


# ================================================================== 4. agitator
def build_agitator(M):
    mb = MB()
    WH, LAV, GO = range(3)
    ctrl = [(0.95, 0.05), (0.91, 0.085), (0.78, 0.125), (0.64, 0.19), (0.545, 0.30), (0.495, 0.45), (0.47, 0.62),
            (0.43, 1.25), (0.38, 1.90), (0.335, 2.40), (0.305, 2.64)]
    n_per = 24
    fine = catmull_rom(ctrl, n_per)
    picks = [0, 24, 36, 48, 60, 72, 84, 96, 120, 144, 168, 192, 216, 240]
    prof = [(0.0, 0.0), (0.92, 0.0), (0.95, 0.022)] + [(fine[i].x, fine[i].y) for i in picks] + [(0.27, 2.672),
                                                                                                 (0.0, 2.68)]
    mats = [LAV if 0.5 * (a[1] + b[1]) < 0.47 else WH for a, b in zip(prof, prof[1:])]
    lathe(mb, prof, WH, 32, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS, mats=mats)
    # fins follow the smooth body surface: meridian arc length table
    acc = [0.0]
    for a, b in zip(fine, fine[1:]):
        acc.append(acc[-1] + (b - a).length)

    def surf(m):
        m = min(max(m, 0.0), acc[-1])
        i = min(max(bisect.bisect_right(acc, m) - 1, 0), len(fine) - 2)
        t = (m - acc[i]) / max(acc[i + 1] - acc[i], 1e-9)
        p = fine[i].lerp(fine[i + 1], t)
        tan = (fine[i + 1] - fine[i]).normalized()
        return p.x, p.y, tan.x, tan.y

    def m_at_z(z):
        i = next(k for k, p in enumerate(fine) if p.y >= z)
        return acc[i]
    m0, m1 = m_at_z(0.10), m_at_z(2.36)
    nseg = 22
    for k in range(4):
        th0 = math.radians(45.0 + 90.0 * k)
        Ps, Ns, profs = [], [], []
        for i in range(nseg + 1):
            s = i / nseg
            R, z, tr, tz = surf(m0 + (m1 - m0) * s)
            th = th0 + math.radians(80.0) * s
            Ps.append(Vector((R * math.cos(th), R * math.sin(th), z)))
            Ns.append(Vector((tz * math.cos(th), tz * math.sin(th), -tr)).normalized())
            if s < 0.12:
                p = 0.12 + 0.08 * (s / 0.12)
            else:
                q = (s - 0.12) / 0.88
                p = 0.20 * (1.0 - q) ** 1.25 - 0.012 * q ** 4
            w = 0.05 - 0.022 * s
            profs.append([(w, -0.02), (w, 0.55 * p), (0.6 * w, 0.92 * p), (0.0, p), (-0.6 * w, 0.92 * p),
                          (-w, 0.55 * p), (-w, -0.02)])
        frames = []
        for i in range(nseg + 1):
            T = (Ps[min(i + 1, nseg)] - Ps[max(i - 1, 0)]).normalized()
            Bv = (Ns[i] - T * Ns[i].dot(T)).normalized()
            frames.append((Ps[i], Bv.cross(T), Bv))            # N = B x T  ->  N x B = T
        sweep(mb, frames, None, LAV, profs=profs, cap0=True)
    cap = [(0.0, 2.60), (0.30, 2.60), (0.318, 2.64), (0.316, 2.70), (0.29, 2.74), (0.25, 2.76), (0.21, 2.84),
           (0.13, 2.91), (0.07, 2.935), (0.07, 2.97), (0.045, 2.995), (0.0, 3.0)]
    lathe(mb, cap, GO, 32, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS)
    return mb.build("SM_Agitator", slots(M, ["M_PlasticWhite", "M_MachineLavender", "M_Gold"]))


# ================================================================== 5. golden plumbing
FLANGE_CAP = [(0.0, 0.0), (0.20, 0.0), (0.22, 0.012), (0.22, 0.046), (0.205, 0.058), (0.16, 0.062), (0.146, 0.068),
              (0.14, 0.08)]
PIPE_R, PIPE_SIDES = 0.14, 16
FLANGE_BOLT = [(0.024, -0.004), (0.024, 0.010), (0.018, 0.019), (0.0, 0.022)]


def flange_bolts(mb, origin, axis, e1, mat):
    """6 domed hex nuts on the inner face of a flange (axis points into the pipe body)."""
    A, e1, e2 = frame_basis(axis, e1)
    for k in range(6):
        phi = math.radians(30.0 + 60.0 * k)
        c = Vector(origin) + A * 0.057 + (e1 * math.cos(phi) + e2 * math.sin(phi)) * 0.183
        lathe(mb, FLANGE_BOLT, mat, 6, c, A, e1, phi0=math.radians(30.0))


def build_pipe_straight(M):
    mb = MB()
    length = 2.0
    mid = [(PIPE_R, 0.08 + (length - 0.16) * k / 8) for k in range(1, 8)]
    prof = FLANGE_CAP + mid + [(r, length - h) for r, h in reversed(FLANGE_CAP)]
    lathe(mb, prof, 0, PIPE_SIDES, (0.0, 0.0, 0.0), FRONT, X_AXIS, v_vals=[s / V_TILE for s in arclen(prof)])
    flange_bolts(mb, (0.0, 0.0, 0.0), FRONT, X_AXIS, 0)
    flange_bolts(mb, (0.0, -length, 0.0), -FRONT, X_AXIS, 0)
    return mb.build("SM_GoldPipe_Straight", slots(M, ["M_Gold"]))


ELBOW_RB, ELBOW_LS, ELBOW_SEGS = 0.42, 0.08, 12


def build_pipe_elbow(M):
    mb = MB()
    rb, ls = ELBOW_RB, ELBOW_LS
    frames, us = [], []
    for i in range(ELBOW_SEGS + 1):
        al = 0.5 * math.pi * i / ELBOW_SEGS
        P = Vector((0.0, -ls - rb * math.sin(al), rb - rb * math.cos(al)))
        T = Vector((0.0, -math.cos(al), math.sin(al)))
        frames.append((P, X_AXIS, T.cross(X_AXIS)))
        us.append((ls + rb * al) / V_TILE)
    sweep(mb, frames, circle2(PIPE_R, PIPE_SIDES), 0, closed_prof=True, u_vals=us, swap_uv=True)
    end = Vector((0.0, -ls - rb, rb + ls))
    lathe(mb, FLANGE_CAP, 0, PIPE_SIDES, (0.0, 0.0, 0.0), FRONT, X_AXIS)
    lathe(mb, FLANGE_CAP, 0, PIPE_SIDES, end, -Z_AXIS, X_AXIS)
    flange_bolts(mb, (0.0, 0.0, 0.0), FRONT, X_AXIS, 0)
    flange_bolts(mb, end, -Z_AXIS, X_AXIS, 0)
    return mb.build("SM_GoldPipe_Elbow", slots(M, ["M_Gold"]), weld=True)


def build_valve_wheel(M):
    mb = MB()
    G, GD = 0, 1
    rim = [(0.265 + 0.036 * math.cos(TAU * k / 10), 0.036 * math.sin(TAU * k / 10)) for k in range(10)]
    lathe(mb, rim, G, 36, (0.0, 0.0, 0.0), FRONT, X_AXIS, closed=True)
    hub = [(0.0, -0.055), (0.06, -0.055), (0.072, -0.043), (0.072, 0.04), (0.06, 0.055), (0.0, 0.055)]
    lathe(mb, hub, G, 24, (0.0, 0.0, 0.0), FRONT, X_AXIS)
    lathe(mb, [(0.04, 0.045), (0.042, 0.072), (0.034, 0.083), (0.0, 0.086)], GD, 6, (0.0, 0.0, 0.0), FRONT, X_AXIS,
          phi0=math.radians(30.0))
    lathe(mb, [(0.034, 0.03), (0.034, 0.27), (0.03, 0.285), (0.0, 0.29)], GD, 12, (0.0, 0.0, 0.0), Y_AXIS, X_AXIS)
    for k in range(5):
        ang = math.radians(90.0 + 72.0 * k)
        d = Vector((math.cos(ang), 0.0, math.sin(ang)))
        pts = [d * 0.05, d * 0.16, d * 0.25]
        profs = [circle2(r, 8) for r in (0.026, 0.020, 0.024)]
        sweep(mb, path_frames(pts, lambda i: Y_AXIS), None, G, closed_prof=True, profs=profs, swap_uv=True)
    return mb.build("SM_ValveWheel", slots(M, ["M_Gold", "M_GoldDark"]))


# ================================================================== 6. pillar
def build_pillar(M):
    mb = MB()
    LAV, G, GD = range(3)
    shaft = [(0.0, 0.0), (0.53, 0.0), (0.55, 0.02), (0.55, 5.98), (0.53, 6.0), (0.0, 6.0)]
    lathe(mb, shaft, LAV, 40, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS, v_vals=[s / V_TILE for s in arclen(shaft)])
    band = [(0.53, -0.13), (0.605, -0.13), (0.632, -0.105), (0.64, -0.06), (0.62, -0.025), (0.62, 0.025),
            (0.64, 0.06), (0.632, 0.105), (0.605, 0.13), (0.53, 0.13)]
    for zc in (0.135, 4.0, 5.62):
        lathe(mb, [(r, zc + h) for r, h in band], G, 40, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS)
    # medallion on the front (-Y): gold rim, recessed dark-gold field, raised gold paw print
    mo = Vector((0.0, -0.60, 4.81))
    med = [(0.0, -0.16), (0.30, -0.16), (0.30, 0.0), (0.296, 0.024), (0.278, 0.041), (0.252, 0.046), (0.232, 0.036),
           (0.226, 0.014), (0.214, 0.006), (0.0, 0.006)]
    lathe(mb, med, G, 40, mo, FRONT, X_AXIS, mats=[G, G, G, G, G, G, G, GD, GD])
    pad = chaikin([Vector(p) for p in ((0.0, 0.062), (0.068, 0.042), (0.104, -0.008), (0.092, -0.052),
                                        (0.045, -0.072), (0.0, -0.062), (-0.045, -0.072), (-0.092, -0.052),
                                        (-0.104, -0.008), (-0.068, 0.042))], 2)
    pad = [(p.x, p.y - 0.040) for p in pad]
    raised_shape(mb, pad, mo, FRONT, X_AXIS, G, 0.0, 0.024, 0.034, 0.037, 0.009)
    for (tx, tz, rot) in ((-0.118, 0.045, 25.0), (-0.044, 0.095, 8.0), (0.044, 0.095, -8.0), (0.118, 0.045, -25.0)):
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        toe = []
        for k in range(16):
            a = TAU * k / 16
            ex, ez = 0.032 * math.cos(a), 0.041 * math.sin(a)
            toe.append((tx + ex * cr - ez * sr, tz + ex * sr + ez * cr))
        raised_shape(mb, toe, mo, FRONT, X_AXIS, G, 0.0, 0.024, 0.034, 0.037, 0.008)
    return mb.build("SM_Pillar", slots(M, ["M_MachineLavender", "M_Gold", "M_GoldDark"]))


# ================================================================== checks + export
def signed_volume(me):
    vol = 0.0
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    return vol


def check(obj):
    me = obj.data
    xs, ys, zs = ([v.co[i] for v in me.vertices] for i in range(3))
    print("CHECK %s bbox x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f] polys=%d verts=%d volume=%.3f slots=%s uv=%s col=%s" % (
        obj.name, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), len(me.polygons), len(me.vertices),
        signed_volume(me), [m.name for m in me.materials], [u.name for u in me.uv_layers],
        [a.name for a in me.color_attributes]))


def check_porthole_normals(obj):
    """Drum faces must point at the axis, the swirl disc and glass toward the viewer (-Y)."""
    me = obj.data
    names = [m.name for m in me.materials]
    bad = {"M_DrumWall": 0, "M_ChamberSwirl": 0, "M_Glass": 0}
    for p in me.polygons:
        nm = names[p.material_index]
        c = p.center
        if nm == "M_DrumWall" and abs(math.hypot(c.x, c.z) - 1.22) < 0.01 and Vector((c.x, 0.0, c.z)).dot(p.normal) > 0:
            bad[nm] += 1
        elif nm in ("M_ChamberSwirl", "M_Glass") and p.normal.y > 0.0:
            bad[nm] += 1
    print("CHECK SM_Porthole facing errors %s" % bad)


def export(obj):
    C.apply_transforms(obj)
    check(obj)
    C.export_fbx([obj], C.model_path(GROUP, obj.name))
    print("TRIS %s %d" % (obj.name, C.tri_count(obj)))


# ================================================================== preview materials + world
def node_math(nt, op, a, b=None):
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


def bsdf(mat):
    return mat.node_tree.nodes["Principled BSDF"]


def preview_materials(M):
    """Preview-only shading (FBX files are already written; Unity remaps the slots by name)."""
    for m in M.values():
        m.use_backface_culling = True                  # flipped faces would show as holes, like in Unity
    for name, color, rough in (("M_Gold", "#FFC24A", 0.24), ("M_GoldDark", "#C98A2E", 0.34)):
        b = bsdf(M[name])
        b.inputs["Base Color"].default_value = C.hex_rgba(color)
        b.inputs["Roughness"].default_value = rough
    glass = M["M_Glass"]
    for attr, val in (("use_transparent_shadow", True), ("use_transparency_overlap", False)):
        if hasattr(glass, attr):
            setattr(glass, attr, val)
    # drum wall: staggered perforation grid (56 per u, 9 per v unit, the Track group's tunnel density)
    nt = M["M_DrumWall"].node_tree
    u, v = uv_xy(nt)
    mu, mv = node_math(nt, 'MULTIPLY', u, 56.0), node_math(nt, 'MULTIPLY', v, 9.0)
    shift = node_math(nt, 'MULTIPLY', node_math(nt, 'MODULO', node_math(nt, 'FLOOR', mv), 2.0), 0.5)
    fu = node_math(nt, 'SUBTRACT', node_math(nt, 'FRACT', node_math(nt, 'ADD', mu, shift)), 0.5)
    fv = node_math(nt, 'SUBTRACT', node_math(nt, 'FRACT', mv), 0.5)
    d = node_math(nt, 'SQRT', node_math(nt, 'ADD', node_math(nt, 'POWER', fu, 2.0), node_math(nt, 'POWER', fv, 2.0)))
    nt.links.new(ramp(nt, d, [(0.17, "#1B1533"), (0.21, "#8E5CC4")]), bsdf(M["M_DrumWall"]).inputs["Base Color"])
    # chamber swirl: rainbow spiral from the planar UVs (centre 0.5, 0.5) + foam rim, emissive
    nt = M["M_ChamberSwirl"].node_tree
    u, v = uv_xy(nt)
    x = node_math(nt, 'MULTIPLY', node_math(nt, 'SUBTRACT', u, 0.5), 2.0)
    y = node_math(nt, 'MULTIPLY', node_math(nt, 'SUBTRACT', v, 0.5), 2.0)
    rho = node_math(nt, 'SQRT', node_math(nt, 'ADD', node_math(nt, 'MULTIPLY', x, x), node_math(nt, 'MULTIPLY', y, y)))
    theta = node_math(nt, 'ARCTAN2', y, x)
    phase = node_math(nt, 'ADD', node_math(nt, 'MULTIPLY', theta, 1.0 / TAU), node_math(nt, 'MULTIPLY', rho, 1.5))
    fac = node_math(nt, 'FRACT', node_math(nt, 'MULTIPLY', phase, 2.0))
    col = ramp(nt, fac, [(0.0, "#FF5C8A"), (0.14, "#FF9E45"), (0.28, "#FFE45C"), (0.42, "#7EE87A"),
                         (0.57, "#4FD6FF"), (0.71, "#5B7CFF"), (0.85, "#B26BFF"), (1.0, "#FF5C8A")])
    foam = ramp(nt, rho, [(0.82, "#000000"), (0.97, "#FFFFFF")])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(foam, sep.inputs[0])
    white = nt.nodes.new("ShaderNodeVectorMath")
    white.operation = 'SUBTRACT'
    white.inputs[0].default_value = (1.0, 1.0, 1.0)
    nt.links.new(col, white.inputs[1])
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = 'SCALE'
    nt.links.new(white.outputs[0], sc.inputs[0])
    nt.links.new(sep.outputs[0], sc.inputs["Scale"])
    add = nt.nodes.new("ShaderNodeVectorMath")
    add.operation = 'ADD'
    nt.links.new(col, add.inputs[0])
    nt.links.new(sc.outputs[0], add.inputs[1])
    b = bsdf(M["M_ChamberSwirl"])
    nt.links.new(add.outputs[0], b.inputs["Base Color"])
    nt.links.new(add.outputs[0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.1
    # brushes: base colour x Col root shade, plus sheen for a fuzzy rim
    for name in ("M_BrushPink", "M_BrushBlue", "M_BrushWhite"):
        nt = M[name].node_tree
        b = bsdf(M[name])
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "Col"
        mul = nt.nodes.new("ShaderNodeVectorMath")
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = tuple(b.inputs["Base Color"].default_value)[:3]
        nt.links.new(attr.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs[0], b.inputs["Base Color"])
        if "Sheen Weight" in b.inputs:
            b.inputs["Sheen Weight"].default_value = 0.8
            b.inputs["Sheen Roughness"].default_value = 0.6


def preview_world():
    """Camera sees the spec background #2A1B4A; reflections / ambient see a warm studio gradient so gold reads as
    polished gold instead of mirroring the dark backdrop."""
    C.setup_preview_scene()
    world = bpy.context.scene.world
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    z01 = node_math(nt, 'MULTIPLY_ADD', sep.outputs[2], 0.5)
    z01.node.inputs[2].default_value = 0.5
    col = ramp(nt, z01, [(0.0, "#2A1B4A"), (0.42, "#7A5AB0"), (0.54, "#FFC99E"), (1.0, "#FFF3E2")])
    env = nt.nodes.new("ShaderNodeBackground")
    env.inputs["Strength"].default_value = 0.8
    nt.links.new(col, env.inputs["Color"])
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(env.outputs[0], mix.inputs[1])
    nt.links.new(bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return env


# ================================================================== preview scenes
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


def pv_object(coll, name, mb, mat):
    obj = mb.build(name, [mat], sharp_deg=None)
    bpy.context.scene.collection.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


def make_floor(coll, size=40.0):
    mb = MB()
    ids = [mb.v((x * size, y * size, 0.0)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    mb.f(ids, 0, [(0, 0), (1, 0), (1, 1), (0, 1)], ref=Z_AXIS)
    return pv_object(coll, "PV_Floor", mb, C.material("PV_Floor", "#34245C", roughness=0.75))


def make_wall(coll, hole=1.32, half=2.4, n=64, y=0.124):
    """Preview-only tunnel wall square with a round hole (hidden behind the frame) for the porthole close-up."""
    mb = MB()
    inner, outer = [], []
    for k in range(n):
        a = TAU * k / n
        dx, dz = math.cos(a), math.sin(a)
        s = half / max(abs(dx), abs(dz))
        inner.append(mb.v((hole * dx, y, hole * dz)))
        outer.append(mb.v((s * dx, y, s * dz)))
    for k in range(n):
        k1 = (k + 1) % n
        q = [inner[k], inner[k1], outer[k1], outer[k]]
        mb.f(q, 0, [(mb.co[i].x / 4.0, mb.co[i].z / 4.0) for i in q], ref=FRONT)
    return pv_object(coll, "PV_Wall", mb, C.material("PV_Wall", "#4C4A79", metallic=0.3, roughness=0.45))


def show_only(coll):
    for o in bpy.data.objects:
        o.hide_render = coll not in o.users_collection


def render_view(path, cam, target, lens, res, light_target=None, light_scale=1.0, energy=1.0, spec=1.0):
    """bwk_common.render_preview rig (warm key / cool fill / pink rim, #2A1B4A background) with extra control."""
    scene = bpy.context.scene
    engine = C.setup_preview_scene()
    temp = C.add_studio_lights(light_target or target, light_scale)
    for o in temp:
        o.data.energy *= energy
        o.data.specular_factor = spec
    temp.append(C.add_camera(cam, target, lens))
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", engine, path)
    for o in temp:
        bpy.data.objects.remove(o, do_unlink=True)


def rot_matrix(cols, loc):
    c0, c1, c2 = (Vector(c) for c in cols)
    m = Matrix(((c0.x, c1.x, c2.x, loc[0]), (c0.y, c1.y, c2.y, loc[1]), (c0.z, c1.z, c2.z, loc[2]),
                (0.0, 0.0, 0.0, 1.0)))
    return m


def render_previews(A):
    scene = bpy.context.scene
    try:
        scene.eevee.use_raytracing = True
    except Exception:
        pass
    env = preview_world()

    # (a) set: control panel + plumbing, brush roller, porthole, agitator, pillar
    ps = new_collection("PV_Set")
    make_floor(ps)
    inst(A["SM_ControlPanel"], ps, (-6.15, -0.5, 0.0), (0.0, 0.0, math.radians(12.0)))
    px, py = -7.65, 0.55
    inst(A["SM_GoldPipe_Straight"], ps, matrix=rot_matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)), (px, py, 0.0)))
    inst(A["SM_GoldPipe_Elbow"], ps, matrix=rot_matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0)), (px, py, 2.0)))
    inst(A["SM_GoldPipe_Straight"], ps, (px + 0.5, py, 2.5), (0.0, 0.0, math.radians(90.0)))
    inst(A["SM_ValveWheel"], ps, (px, py - 0.40, 1.7))
    inst(A["SM_BrushRoller"], ps, (-3.35, 1.3, 4.45), (0.0, 0.0, math.radians(28.0)))
    inst(A["SM_Porthole"], ps, (0.05, 0.0, 1.75))
    inst(A["SM_Agitator"], ps, (3.35, 0.4, 0.0), (0.0, 0.0, math.radians(20.0)))
    inst(A["SM_Pillar"], ps, (6.05, 1.0, 0.0), (0.0, 0.0, math.radians(-20.0)))
    add_light(ps, "PV_ChamberGlow", 'POINT', 60.0, "#CFE6FF", (0.05, 0.55, 1.75), size=0.3, shadow=False, spec=0.2)
    env.inputs["Strength"].default_value = 0.8
    show_only(ps)
    render_view(C.preview_path("Machinery_set"), (-0.75, -16.8, 3.6), (-0.75, 0.6, 2.75), 34.0, (1280, 720),
                light_target=(-0.75, 0.6, 2.5), light_scale=3.2)

    # (b) porthole close-up in a wall section, seen slightly from the right so the chamber depth shows
    pp = new_collection("PV_Porthole")
    inst(A["SM_Porthole"], pp)
    make_wall(pp)
    add_light(pp, "PV_ChamberGlow", 'POINT', 30.0, "#CFE6FF", (0.0, 0.5, 0.0), size=0.3, shadow=False, spec=0.2)
    env.inputs["Strength"].default_value = 0.9
    show_only(pp)
    render_view(C.preview_path("Machinery_porthole"), (1.45, -5.3, 0.85), (-0.05, 0.1, 0.0), 45.0, (1000, 1000),
                light_scale=1.3)

    if not REVIEW_DIR:
        return
    os.makedirs(REVIEW_DIR, exist_ok=True)
    pr = new_collection("PV_Review")
    inst(A["SM_BrushRoller"], pr, (0.0, 0.0, 0.0), (0.0, 0.0, math.radians(28.0)))
    show_only(pr)
    render_view(os.path.join(REVIEW_DIR, "rv_roller.png"), (-1.4, -5.2, -1.2), (0.0, 0.0, 0.0), 40.0, (1000, 1000),
                light_scale=1.4)
    pc = new_collection("PV_Review_Panel")
    inst(A["SM_ControlPanel"], pc)
    show_only(pc)
    render_view(os.path.join(REVIEW_DIR, "rv_panel.png"), (1.1, -4.2, 1.7), (0.0, 0.0, 0.75), 40.0, (1000, 1000),
                light_scale=1.3)
    pa = new_collection("PV_Review_AgPi")
    make_floor(pa)
    inst(A["SM_Agitator"], pa, (-1.0, 0.0, 0.0), (0.0, 0.0, math.radians(20.0)))
    inst(A["SM_Pillar"], pa, (1.2, 0.3, 0.0))
    show_only(pa)
    render_view(os.path.join(REVIEW_DIR, "rv_agitator_pillar.png"), (0.3, -8.5, 3.2), (0.1, 0.0, 2.6), 40.0,
                (1000, 1000), light_scale=2.2)
    pm = new_collection("PV_Review_Med")
    inst(A["SM_Pillar"], pm)
    show_only(pm)
    render_view(os.path.join(REVIEW_DIR, "rv_medallion.png"), (0.5, -2.6, 5.0), (0.0, -0.6, 4.81), 50.0,
                (1000, 1000), light_scale=0.8)
    pq = new_collection("PV_Review_Pipes")
    inst(A["SM_GoldPipe_Straight"], pq, (0.0, 0.0, 0.0))
    inst(A["SM_GoldPipe_Elbow"], pq, (0.0, -2.0, 0.0))
    inst(A["SM_ValveWheel"], pq, (0.9, -0.6, 0.4))
    show_only(pq)
    render_view(os.path.join(REVIEW_DIR, "rv_pipes.png"), (3.2, -3.4, 1.9), (0.2, -1.2, 0.3), 35.0, (1000, 1000),
                light_scale=1.2)


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
            print("FBXCHECK %s tris=%d slots=%s uv=%s col=%s %s" % (
                o.name, tris, [m.name for m in me.materials], [u.name for u in me.uv_layers],
                [a.name for a in me.color_attributes], bb))
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)


# ================================================================== main
def main():
    C.reset_scene()
    M = make_materials()
    A = {}
    for build in (build_porthole, build_brush_roller, build_control_panel, build_agitator, build_pipe_straight,
                  build_pipe_elbow, build_valve_wheel, build_pillar):
        obj = build(M)
        A[obj.name] = obj
    bpy.context.view_layer.update()
    check_porthole_normals(A["SM_Porthole"])
    for name in ASSET_NAMES:
        export(A[name])
    preview_materials(M)
    render_previews(A)
    verify_fbx(ASSET_NAMES)
    print("BUILD_MACHINERY_DONE")


main()
