"""Bubble Wash Kingdom - prop group "Props" (Blender 5.3, headless, deterministic).

Builds, exports (FBX -> Assets/BubbleWashKingdom/Art/Models/Props/) and previews every small prop the
reference shows along the slide (Reference/key 02 + 04):

  SM_NeonStar      rounded 5-point neon tube star (double line: thick outer tube + thin inner tube)   M_Neon
  SM_StarFilled    puffy bevelled filled star                                                     M_Neon
  SM_Coin          gold paw-print coin: rolled rim, recessed face, raised paw (pad + 4 toes) both faces  M_Coin, M_GoldDark
  SM_Gem           brilliant-cut purple gem (8-fold crown + pavilion, flat facets)                 M_Gem
  SM_Chevron       glowing speed-boost chevron strip on the water (UV: across / along the V), points -Y  M_Arrow
  SM_Foam_A/B/C    cumulus foam clusters (metaball spheres -> mesh), flat underside                M_Foam
  SM_Sock_A/B/C    striped socks (vertex colour stripes in `Col`)                                  M_Fabric
  SM_Towel         folded striped towel                                                            M_Fabric
  SM_Shirt         tiny T-shirt                                                                    M_Fabric
  SM_Bubble        soap bubble sphere r 0.5                                                        M_Bubble

Conventions (Docs/AssetSpec.md): meters, Z up, front / travel = -Y, right side = -X. Stars and coins stand in
the XZ plane (facing the player along Y); chevrons lie in XY. Origins: centres (foam: base centre).

Run from the project root:
  blender --background --factory-startup --python Tools/Blender/scripts/build_props.py
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

GROUP = "Props"
RNG = random.Random(20261125)


# ================================================================== materials (slot names are the contract)
def make_materials():
    return {
        "M_Neon": C.material("M_Neon", "#45D5E5", roughness=0.25, emission="#45D5E5", emission_strength=6.0),
        "M_Coin": C.material("M_Coin", "#F5D45A", metallic=1.0, roughness=0.18),
        "M_GoldDark": C.material("M_GoldDark", "#D99A2E", metallic=1.0, roughness=0.3),
        "M_Gem": C.material("M_Gem", "#C42BE0", metallic=0.1, roughness=0.05, emission="#6A0F80", emission_strength=0.6),
        "M_Arrow": C.material("M_Arrow", "#22EEFF", roughness=0.3, emission="#22EEFF", emission_strength=5.0),
        "M_ArrowRim": C.material("M_ArrowRim", "#F2FFFF", roughness=0.3, emission="#F2FFFF", emission_strength=3.0),
        "M_Foam": C.material("M_Foam", "#FFFFFF", roughness=0.55),
        "M_Fabric": C.material("M_Fabric", "#FFFFFF", roughness=0.9),
        "M_Bubble": C.material("M_Bubble", "#FFFFFF", roughness=0.02, alpha=0.15),
    }


# ================================================================== helpers
def new_obj(name, bm):
    obj = C.mesh_from_bmesh(name, bm)
    return obj


def planar_uv(obj, fn):
    """UV0 'UVMap' from a per-vertex function fn(co) -> (u, v) (every prop needs UV0 for Unity tangents/shaders)."""
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = fn(me.vertices[me.loops[li].vertex_index].co)


def box_uv(obj, scale=1.0):
    def fn(co):
        return (co.x * scale + 0.5, (co.z + co.y * 0.5) * scale + 0.5)
    planar_uv(obj, fn)


def finish(obj, mats, smooth_deg=None):
    C.assign_materials(obj, mats)
    if smooth_deg is not None:
        C.shade_smooth(obj, smooth_deg)
    else:
        for p in obj.data.polygons:
            p.use_smooth = False
    return obj


def star_outline(r_out, r_in, n=5, phase=math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = phase + math.pi * i / n
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r)))
    return pts


def rounded_polygon(pts, radius_fn, segs=6):
    """Fillet every corner of a closed 2D polygon (radius per corner from radius_fn(i))."""
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        d0 = (p0 - p1).normalized()
        d2 = (p2 - p1).normalized()
        ang = math.acos(max(-1.0, min(1.0, d0.dot(d2))))
        r = radius_fn(i)
        t = r / math.tan(ang * 0.5)
        t = min(t, (p0 - p1).length * 0.45, (p2 - p1).length * 0.45)
        r = t * math.tan(ang * 0.5)
        a = p1 + d0 * t
        b = p1 + d2 * t
        bis = (d0 + d2).normalized()
        c = p1 + bis * (r / math.sin(ang * 0.5))
        va, vb = a - c, b - c
        a0 = math.atan2(va.y, va.x)
        a1 = math.atan2(vb.y, vb.x)
        da = a1 - a0
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(segs + 1):
            ak = a0 + da * k / segs
            out.append(c + Vector((math.cos(ak), math.sin(ak))) * r)
    return out


def resample_closed(pts, count):
    """Evenly resample a closed 2D polyline."""
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    lens = [(b - a).length for a, b in segs]
    total = sum(lens)
    out = []
    for k in range(count):
        s = total * k / count
        for idx, ((a, b), ln) in enumerate(zip(segs, lens)):
            if s <= ln or idx == len(segs) - 1:
                t = 0.0 if ln == 0 else min(1.0, s / ln)
                out.append(a.lerp(b, t))
                break
            s -= ln
    return out


def tube_loop(bm, path2d, radius, sides, to3d):
    """Closed tube along a closed 2D path (mapped to 3D by to3d). Returns created verts rows."""
    n = len(path2d)
    rows = []
    for i in range(n):
        p = path2d[i]
        t = (path2d[(i + 1) % n] - path2d[i - 1]).normalized()
        nrm2 = Vector((t.y, -t.x))  # outward for CCW path
        row = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            off2 = nrm2 * (math.cos(a) * radius)
            depth = math.sin(a) * radius
            row.append(bm.verts.new(to3d(p + off2, depth)))
        rows.append(row)
    for i in range(n):
        r0, r1 = rows[i], rows[(i + 1) % n]
        for k in range(sides):
            bm.faces.new((r0[k], r0[(k + 1) % sides], r1[(k + 1) % sides], r1[k]))
    return rows


def xz(p2, depth):
    """2D (x, up) -> Blender XZ plane, depth along -Y (toward the player is +Y)."""
    return Vector((p2.x, -depth, p2.y))


# ================================================================== 1. neon stars
def build_neon_star(M):
    bm = bmesh.new()
    outer = rounded_polygon(star_outline(0.5, 0.23), lambda i: 0.07 if i % 2 == 0 else 0.03, 5)
    outer = resample_closed(outer, 70)
    tube_loop(bm, outer, 0.06, 6, xz)          # thick glowing neon tube (reference stars read bold)
    inner = rounded_polygon(star_outline(0.36, 0.165), lambda i: 0.05 if i % 2 == 0 else 0.02, 4)
    inner = resample_closed(inner, 50)
    tube_loop(bm, inner, 0.024, 5, xz)
    obj = new_obj("SM_NeonStar", bm)
    for f in obj.data.polygons:
        f.use_smooth = True
    finish(obj, [M["M_Neon"]], smooth_deg=80)
    return obj


def build_filled_star(M):
    bm = bmesh.new()
    outline = rounded_polygon(star_outline(0.42, 0.2), lambda i: 0.07 if i % 2 == 0 else 0.03, 4)
    outline = resample_closed(outline, 60)
    # puffy: layered rings that shrink toward a bulged front/back
    layers = [(-0.06, 0.82), (-0.075, 0.93), (-0.08, 1.0), (0.08, 1.0), (0.075, 0.93), (0.06, 0.82)]
    rows = []
    for depth, s in layers:
        rows.append([bm.verts.new(xz(p * s, depth)) for p in outline])
    n = len(outline)
    for j in range(len(rows) - 1):
        for i in range(n):
            bm.faces.new((rows[j][i], rows[j][(i + 1) % n], rows[j + 1][(i + 1) % n], rows[j + 1][i]))
    cf = bm.verts.new(Vector((0, 0.06 + 0.035, 0)))
    cb = bm.verts.new(Vector((0, -0.06 - 0.035, 0)))
    for i in range(n):
        bm.faces.new((cf, rows[0][(i + 1) % n], rows[0][i]))
        bm.faces.new((cb, rows[-1][i], rows[-1][(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_obj("SM_StarFilled", bm)
    finish(obj, [M["M_Neon"]], smooth_deg=70)
    return obj


# ================================================================== 2. paw coin
def orient_outward(bm, faces, center):
    """Flip faces whose normal points toward `center` (for open shells such as raised paw pads)."""
    for f in faces:
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - center) < 0:
            f.normal_flip()


def blob(bm, center, rx, rz, h, y_face, sign, segs=14, rings=3, mat=0):
    """Raised elliptical paw pad (dome) on a coin face at y_face, bulging along sign*Y; sunk 4 mm into the face."""
    rows = []
    for j in range(rings):
        t = j / rings
        s = math.cos(t * math.pi * 0.5)
        dy = math.sin(t * math.pi * 0.5) * h
        rows.append([bm.verts.new(Vector((center.x + math.cos(2 * math.pi * k / segs) * rx * s, y_face + sign * (dy - 0.004),
                                          center.y + math.sin(2 * math.pi * k / segs) * rz * s))) for k in range(segs)])
    top = bm.verts.new(Vector((center.x, y_face + sign * (h - 0.004), center.y)))
    faces = []
    for j in range(rings - 1):
        for k in range(segs):
            faces.append(bm.faces.new((rows[j][k], rows[j][(k + 1) % segs], rows[j + 1][(k + 1) % segs], rows[j + 1][k])))
    for k in range(segs):
        faces.append(bm.faces.new((rows[-1][k], rows[-1][(k + 1) % segs], top)))
    for f in faces:
        f.material_index = mat
    orient_outward(bm, faces, Vector((center.x, y_face - sign * h * 2.0, center.y)))


def build_coin(M):
    R, T, segs, hr = 0.32, 0.075, 30, 0.022
    inner_r = R - 0.06
    rec = T * 0.5 - 0.016
    # closed (r, y) profile: front centre -> recessed face -> raised rim roll -> edge -> back rim -> back centre
    prof = [(inner_r * 0.3, rec), (inner_r * 0.65, rec), (inner_r, rec), (inner_r + 0.014, T * 0.5 + 0.003)]
    for k in range(0, 11):
        a = math.pi * 0.5 - math.pi * k / 10
        prof.append((R - hr + math.cos(a) * hr, math.sin(a) * (T * 0.5 + 0.004 - hr) + (hr if a > 0 else -hr) * abs(math.sin(a))))
    prof += [(inner_r + 0.014, -(T * 0.5 + 0.003)), (inner_r, -rec), (inner_r * 0.65, -rec), (inner_r * 0.3, -rec)]
    face_rows = {0, 1, 2, len(prof) - 4, len(prof) - 3, len(prof) - 2}
    bm = bmesh.new()
    rows = []
    for (r, y) in prof:
        rows.append([bm.verts.new(Vector((math.cos(2 * math.pi * k / segs) * r, y, math.sin(2 * math.pi * k / segs) * r)))
                     for k in range(segs)])
    body = []
    for j in range(len(rows) - 1):
        for k in range(segs):
            f = bm.faces.new((rows[j][k], rows[j + 1][k], rows[j + 1][(k + 1) % segs], rows[j][(k + 1) % segs]))
            f.material_index = 1 if j in face_rows else 0
            body.append(f)
    for row, y in ((rows[0], rec), (rows[-1], -rec)):
        c = bm.verts.new(Vector((0, y, 0)))
        for k in range(segs):
            f = bm.faces.new((row[k], row[(k + 1) % segs], c))
            f.material_index = 1
            body.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=body)
    # paw print (raised gold, both faces): main pad + 4 toe beans
    k = 1.28  # paw fills ~65% of the face like the reference coins
    paw = [((0.0, -0.05 * k), 0.095 * k, 0.078 * k, 0.03), ((-0.105 * k, 0.04 * k), 0.04 * k, 0.05 * k, 0.026),
           ((-0.04 * k, 0.1 * k), 0.04 * k, 0.05 * k, 0.026), ((0.04 * k, 0.1 * k), 0.04 * k, 0.05 * k, 0.026),
           ((0.105 * k, 0.04 * k), 0.04 * k, 0.05 * k, 0.026)]
    for sign in (+1, -1):
        for (cx, cz), rx, rz, h in paw:
            blob(bm, Vector((cx * sign, cz)), rx, rz, h, sign * rec, sign, segs=12 if rx > 0.06 else 9, rings=3, mat=0)
    obj = new_obj("SM_Coin", bm)
    finish(obj, [M["M_Coin"], M["M_GoldDark"]], smooth_deg=50)
    return obj


# ================================================================== 3. gem
def build_gem(M):
    bm = bmesh.new()
    n = 8
    r_girdle, r_table = 0.2, 0.12
    h_crown, h_pav = 0.085, 0.2
    table = [bm.verts.new(Vector((math.cos(2 * math.pi * k / n + math.pi / n) * r_table,
                                  math.sin(2 * math.pi * k / n + math.pi / n) * r_table, h_crown))) for k in range(n)]
    gird = [bm.verts.new(Vector((math.cos(2 * math.pi * k / (2 * n)) * r_girdle,
                                 math.sin(2 * math.pi * k / (2 * n)) * r_girdle, 0.0))) for k in range(2 * n)]
    culet = bm.verts.new(Vector((0, 0, -h_pav)))
    bm.faces.new(table)
    for k in range(n):
        g0, g1, g2 = gird[2 * k], gird[2 * k + 1], gird[(2 * k + 2) % (2 * n)]
        t0, t1 = table[k - 1], table[k]
        bm.faces.new((g0, g1, t1))
        bm.faces.new((g1, g2, t1))
        bm.faces.new((g0, t1, t0))
    for k in range(2 * n):
        bm.faces.new((gird[(k + 1) % (2 * n)], gird[k], culet))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_obj("SM_Gem", bm)
    finish(obj, [M["M_Gem"]])
    return obj


# ================================================================== 4. chevron
def build_chevron(M):
    """Glowing speed-boost chevron lying on the water (XY), apex toward travel (-Y), 45-degree arms, flat arm ends
    (reference f_002.00-f_003.25: thick glowing turquoise / white-cyan arrows). Built as a STRIP so the shader gets
    clean, symmetric UVs: U across the arm (0 outer edge, 0.5 arm centre line, 1 inner edge), V along the V (0 left arm
    end, 0.5 apex, 1 right arm end). BWK/Soft Mode 7 shades only from abs(U-0.5) / abs(V-0.5), so any UV flip is safe.
    A low wall all round gives the lit edge. Size 1.31 x 0.65 m (SceneBuilder scales it)."""
    HD = 0.26                     # arm centre line: apex at y = -HD, arm ends at y = +HD
    T = 0.19                      # arm thickness (perpendicular)
    H = 0.03                      # top height above the water
    COLS = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    ROWS = 8                      # rows per arm
    s2 = math.sqrt(2.0)
    bm = bmesh.new()
    uvs = []

    def vert(p, z, u, v):
        bv = bm.verts.new(Vector((p.x, p.y, z)))
        uvs.append((u, v))
        return bv

    def strip_point(r, c):
        """Row r (0 = left arm end .. ROWS = apex .. 2*ROWS = right arm end), column fraction c (0 outer .. 1 inner)."""
        o = T * 0.5 - c * T                           # offset toward the outer (front) edge
        m = Vector((0.0, -HD - o * s2))               # where the two arms' offset lines meet (mitre)
        side = -1.0 if r < ROWS else 1.0
        f = abs(r - ROWS) / ROWS
        d = Vector((side * 0.70710678, 0.70710678))
        s_end = (HD - m.y) / d.y
        return m + d * (s_end * f)

    nr = 2 * ROWS + 1
    top = [[vert(strip_point(r, c), H, c, r / (2 * ROWS)) for c in COLS] for r in range(nr)]
    centre = [strip_point(r, 0.5) for r in range(nr)]

    def face(vs, want):
        f = bm.faces.new(vs)
        f.normal_update()
        if f.normal.dot(want) < 0:
            f.normal_flip()
        return f

    for r in range(nr - 1):
        for k in range(len(COLS) - 1):
            face((top[r][k], top[r][k + 1], top[r + 1][k + 1], top[r + 1][k]), Vector((0, 0, 1)))
    # walls: outer + inner edge along the whole V, and the two flat arm-end caps (duplicated verts: crisp edges)
    for k, u in ((0, 0.0), (len(COLS) - 1, 1.0)):
        for r in range(nr - 1):
            a, b = strip_point(r, COLS[k]), strip_point(r + 1, COLS[k])
            out = ((a + b) * 0.5 - (centre[r] + centre[r + 1]) * 0.5)
            vs = (vert(a, H, u, r / (2 * ROWS)), vert(b, H, u, (r + 1) / (2 * ROWS)),
                  vert(b, 0.0, u, (r + 1) / (2 * ROWS)), vert(a, 0.0, u, r / (2 * ROWS)))
            face(vs, Vector((out.x, out.y, 0.0)))
    for r, v in ((0, 0.0), (nr - 1, 1.0)):
        for k in range(len(COLS) - 1):
            a, b = strip_point(r, COLS[k]), strip_point(r, COLS[k + 1])
            vs = (vert(a, H, COLS[k], v), vert(b, H, COLS[k + 1], v), vert(b, 0.0, COLS[k + 1], v), vert(a, 0.0, COLS[k], v))
            face(vs, Vector((0.0, 1.0, 0.0)))
    bm.verts.index_update()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for loop in f.loops:
            loop[uv_layer].uv = uvs[loop.vert.index]
    obj = new_obj("SM_Chevron", bm)
    finish(obj, [M["M_Arrow"]])
    return obj


# ================================================================== 5. foam clusters (soap suds)
def _hemi_dirs(n=24, seed=5):
    """Fixed, well spread unit directions over the sphere (fibonacci) for baked ambient occlusion."""
    out = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1.0 - z * z))
        out.append((math.cos(ga * i) * rr, math.sin(ga * i) * rr, z))
    return out


def _bake_ao(points, normals, own, spheres, max_dist=0.45):
    """Ray-traced AO against every other sphere + the ground (z = 0). numpy, returns 0 (buried) .. 1 (open)."""
    import numpy as np
    P = np.array(points, dtype=np.float64)                    # (V, 3)
    N = np.array(normals, dtype=np.float64)                   # (V, 3)
    D = np.array(_hemi_dirs(), dtype=np.float64)              # (K, 3)
    S = np.array([s[:3] for s in spheres], dtype=np.float64)  # (S, 3)
    R = np.array([s[3] for s in spheres], dtype=np.float64)   # (S,)
    cosw = N @ D.T                                            # (V, K)
    w = np.clip(cosw, 0.0, None)
    O = P + N * 0.004
    occ = np.zeros_like(w)
    # ray-sphere: |O + tD - C|^2 = r^2  ->  t^2 + 2 t (D.(O-C)) + |O-C|^2 - r^2 = 0
    for j in range(len(S)):
        mask_v = own != j
        oc = O - S[j]                                          # (V, 3)
        b = oc @ D.T                                           # (V, K)
        c = (oc * oc).sum(1) - R[j] ** 2                       # (V,)
        disc = b * b - c[:, None]
        hit = disc > 0
        t = -b - np.sqrt(np.where(hit, disc, 0.0))
        hitj = hit & (t > 0.0) & (t < max_dist) & mask_v[:, None]
        occ = np.maximum(occ, hitj * (1.0 - np.clip(t / max_dist, 0, 1) * 0.5))
    # ground (the bank top the suds sit on)
    dz = D[:, 2][None, :]
    tg = np.where(dz < -1e-3, -O[:, 2:3] / np.where(dz < -1e-3, dz, -1.0), 1e9)
    occ = np.maximum(occ, ((tg > 0) & (tg < max_dist)) * 0.6)
    ao = 1.0 - (occ * w).sum(1) / np.maximum(w.sum(1), 1e-6)
    return np.clip(ao, 0.0, 1.0)


def build_suds(M, name, seed, spread, count, lod=0):
    """Soap-suds cluster: medium puffs piled into a mound, clusters of smaller bubbles on them and tiny bubbles
    sprinkled over the surface (reference f_003.00s banks: layered soft suds, not rocks). Flat underside, origin at
    the base centre, long along X. Vertex colour 'Col': R = baked crevice AO, G = per-puff random (BWK/Soft Mode 5)."""
    rng = random.Random(seed)
    spheres = []
    for i in range(int(count * 1.5)):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 1) ** 0.75
        x = math.cos(a) * d * spread[0]
        y = math.sin(a) * d * spread[1]
        r = rng.uniform(0.22, 0.40) * (1.2 - 0.45 * d)     # big smooth cloud puffs (reference banks)
        z = r * rng.uniform(0.0, 0.35) + (1 - d) * 0.2
        spheres.append((x, y, z, r))
    prim = list(spheres)
    for (x, y, z, r) in prim:                       # second layer: smaller puffs riding on the big ones
        for _ in range(rng.randint(1, 2) if lod == 0 else 1):
            th = rng.uniform(0, 2 * math.pi)
            ph = rng.uniform(0.15, 1.2)              # mostly upper hemisphere
            dirv = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
            rs = r * rng.uniform(0.45, 0.7)
            c = Vector((x, y, z)) + dirv * (r - rs * 0.3)    # half buried: soft cloud bulges, not lumps
            if c.z > 0.03:
                spheres.append((c.x, c.y, c.z, rs))
    if lod == 0:                                     # tiny bubbles sprinkled over the surface
        base_list = list(spheres)
        for _ in range(int(count * 6)):
            x, y, z, r = base_list[rng.randrange(len(base_list))]
            th = rng.uniform(0, 2 * math.pi)
            ph = rng.uniform(0.0, 1.45)
            dirv = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
            rt = rng.uniform(0.012, 0.03)                 # tiny glossy micro-bubbles on the puffs
            c = Vector((x, y, z)) + dirv * (r + rt * 0.05)
            if c.z > 0.02:
                spheres.append((c.x, c.y, c.z, rt))
    bm = bmesh.new()
    pts, nrm, own, puff = [], [], [], []
    for si, (x, y, z, r) in enumerate(spheres):
        if lod == 0:
            useg = max(6, min(24, int(round(r * 60))))
        else:
            useg = max(5, min(9, int(round(r * 26))))
        sub = bmesh.new()
        bmesh.ops.create_uvsphere(sub, u_segments=useg, v_segments=max(4, useg * 2 // 3), radius=r)
        bmesh.ops.translate(sub, verts=sub.verts, vec=Vector((x, y, z)))
        bmesh.ops.bisect_plane(sub, geom=sub.verts[:] + sub.edges[:] + sub.faces[:], plane_co=(0, 0, 0.0),
                               plane_no=(0, 0, 1), clear_inner=True)
        pr = rng.random()
        for v in sub.verts:
            pts.append(tuple(v.co))
            n = (v.co - Vector((x, y, z)))
            n = n.normalized() if n.length > 1e-6 else Vector((0, 0, 1))
            nrm.append(tuple(n))
            own.append(si)
            puff.append(pr)
        tmp = bpy.data.meshes.new("tmp")
        sub.to_mesh(tmp)
        sub.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    import numpy as np
    ao = _bake_ao(pts, nrm, np.array(own), spheres)
    ao = np.clip(0.18 + 0.82 * ao ** 1.4, 0.0, 1.0)
    out = new_obj(name, bm)
    for p in out.data.polygons:
        p.use_smooth = True
    me = out.data
    ca = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            col = (float(ao[vi]), float(puff[vi]), 0.0, 1.0)
            try:
                ca.data[li].color_srgb = col
            except AttributeError:
                ca.data[li].color = col
    C.assign_materials(out, [M["M_Foam"]])
    planar_uv(out, lambda co: (co.x * 0.5 + 0.5, (co.z + co.y * 0.5) * 0.5 + 0.5))
    return out


def build_suds_meta(M, name, seed, spread, count, lod=0):
    """Soft soap-cloud cluster (reference f_003.00s banks: big satin puffs fused with SOFT crevices, a few tiny glossy
    micro-bubbles on top). The puff layout is the one build_suds uses; the puffs are fused as metaballs (smooth liquid
    fillets instead of hard sphere intersections), polygonised, cut flat underneath and decimated. Tiny bubbles stay
    separate crisp spheres. Vertex colour 'Col': R = baked crevice AO, G = per-puff random (BWK/Soft Mode 5)."""
    import numpy as np
    rng = random.Random(seed)
    spheres = []
    # round 3 (owner: "soft white cumulus puffs, not popcorn"): fewer, BIGGER round puffs, at most one soft bulge each,
    # wide smooth metaball fillets, almost no micro-bubbles
    for i in range(int(count * 0.9)):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 1) ** 0.75
        x = math.cos(a) * d * spread[0]
        y = math.sin(a) * d * spread[1]
        r = rng.uniform(0.30, 0.50) * (1.2 - 0.4 * d)
        z = r * rng.uniform(0.05, 0.3) + (1 - d) * 0.18
        spheres.append((x, y, z, r))
    prim = list(spheres)
    for (x, y, z, r) in prim:                       # one soft cloud bulge on most big puffs
        if rng.random() < 0.65:
            th = rng.uniform(0, 2 * math.pi)
            ph = rng.uniform(0.2, 1.0)
            dirv = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
            rs = r * rng.uniform(0.5, 0.7)
            c = Vector((x, y, z)) + dirv * (r - rs * 0.4)
            if c.z > 0.03:
                spheres.append((c.x, c.y, c.z, rs))
    # --- fused puffs (metaballs)
    mb = bpy.data.metaballs.new("MB_" + name)
    res = 0.022 if lod == 0 else 0.05
    mb.resolution = res
    mb.render_resolution = res
    mb.threshold = 0.6
    mbo = bpy.data.objects.new("MB_" + name, mb)
    bpy.context.scene.collection.objects.link(mbo)
    for (x, y, z, r) in spheres:
        e = mb.elements.new(type='BALL')
        e.co = (x, y, z)
        e.radius = r * 1.46                        # softer field: wide smooth fillets between puffs (cumulus)
        e.stiffness = 4.0                          # visible radius ~ r
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(mbo.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(mbo, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0.0),
                           plane_no=(0, 0, 1), clear_inner=True)
    obj = new_obj(name, bm)
    target = 9000 if lod == 0 else 1400
    tris = C.tri_count(obj)
    if tris > target:
        C.select_only([obj])
        mod = obj.modifiers.new("dec", 'DECIMATE')
        mod.ratio = target / tris
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # --- tiny glossy micro-bubbles sitting on the surface (LOD0 only)
    if lod == 0:
        tb = bmesh.new()
        for _ in range(int(count * 1.2)):
            x, y, z, r = spheres[rng.randrange(len(spheres))]
            th = rng.uniform(0, 2 * math.pi)
            ph = rng.uniform(0.0, 1.3)
            dirv = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
            rt = rng.uniform(0.012, 0.024)
            c = Vector((x, y, z)) + dirv * (r * 0.97 + rt * 0.3)
            if c.z < 0.03:
                continue
            sub = bmesh.new()
            bmesh.ops.create_uvsphere(sub, u_segments=8, v_segments=6, radius=rt)
            bmesh.ops.translate(sub, verts=sub.verts, vec=c)
            tmp = bpy.data.meshes.new("tmp")
            sub.to_mesh(tmp)
            sub.free()
            tb.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
        tobj = new_obj(name + "_tiny", tb)
        obj = C.join([obj, tobj], name)
    for p in obj.data.polygons:
        p.use_smooth = True
    # --- baked crevice AO + per-puff random tint into vertex colours
    me = obj.data
    me.update()
    pts = [tuple(v.co) for v in me.vertices]
    nrm = [tuple(v.normal) for v in me.vertices]
    occl = [(x, y, z, r * 0.82) for (x, y, z, r) in spheres]
    ao = _bake_ao(pts, nrm, np.full(len(pts), -1), occl)
    ao = np.clip(0.4 + 0.6 * ao ** 1.1, 0.0, 1.0)     # soft cumulus crevices (no dark popcorn seams)
    S = np.array([s[:3] for s in spheres])
    P = np.array(pts)
    nearest = np.argmin(((P[:, None, :] - S[None, :, :]) ** 2).sum(2), axis=1)
    prng = random.Random(seed + 99)
    puff_r = [prng.random() for _ in spheres]
    ca = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            col = (float(ao[vi]), float(puff_r[int(nearest[vi])]), 0.0, 1.0)
            try:
                ca.data[li].color_srgb = col
            except AttributeError:
                ca.data[li].color = col
    C.assign_materials(obj, [M["M_Foam"]])
    planar_uv(obj, lambda co: (co.x * 0.5 + 0.5, (co.z + co.y * 0.5) * 0.5 + 0.5))
    return obj


def build_foam(M, name, seed, spread, count, max_tris=2000, useg_override=None):
    """Cumulus foam: overlapping smooth spheres (distinct round puffs like the reference), underside cut flat."""
    rng = random.Random(seed)
    balls = []
    for i in range(count):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 1) ** 0.8
        x = math.cos(a) * d * spread[0]
        y = math.sin(a) * d * spread[1]
        r = rng.uniform(0.26, 0.42) * (1.25 - 0.5 * d)
        z = r * rng.uniform(0.05, 0.4) + (1 - d) * 0.18
        balls.append((x, y, z, r))
    for i in range(count // 2 + 1):
        x, y, z, r = balls[rng.randrange(len(balls))]
        a = rng.uniform(0, 2 * math.pi)
        balls.append((x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, z + r * 0.62, r * rng.uniform(0.5, 0.68)))
    bm = bmesh.new()
    per = max(10, int(max_tris / len(balls) / 2))
    useg = useg_override or max(10, min(16, int(math.sqrt(per * 2))))
    for (x, y, z, r) in balls:
        sub = bmesh.new()
        bmesh.ops.create_uvsphere(sub, u_segments=useg, v_segments=max(6, useg * 2 // 3), radius=r)
        bmesh.ops.translate(sub, verts=sub.verts, vec=Vector((x, y, z)))
        bmesh.ops.bisect_plane(sub, geom=sub.verts[:] + sub.edges[:] + sub.faces[:], plane_co=(0, 0, 0.0),
                               plane_no=(0, 0, 1), clear_inner=True)
        tmp = bpy.data.meshes.new("tmp")
        sub.to_mesh(tmp)
        sub.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    out = new_obj(name, bm)
    for p in out.data.polygons:
        p.use_smooth = True
    C.assign_materials(out, [M["M_Foam"]])
    return out


# ================================================================== 6. laundry
STRIPES = {
    "SM_Sock_A": ["#FF5A8A", "#FFD23F", "#FF5A8A", "#FFFFFF"],
    "SM_Sock_B": ["#47C7FF", "#FFFFFF", "#47C7FF", "#A66BFF"],
    "SM_Sock_C": ["#FF9A3C", "#FFE56B", "#7BE07B", "#FF9A3C"],
}


def color_attr(obj, fn):
    me = obj.data
    ca = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            c = fn(v)
            ca.data[li].color = (c[0], c[1], c[2], 1.0)


def path_tube(name, path, radius_fn, sides=10):
    """Closed-end tube along an open 3D path (list of Vectors)."""
    bm = bmesh.new()
    rows = []
    n = len(path)
    prev_side = None
    for i, p in enumerate(path):
        t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((1, 0, 0)))
        if side.length < 1e-3:
            side = t.cross(Vector((0, 0, 1)))
        side.normalize()
        if prev_side is not None and side.dot(prev_side) < 0:
            side = -side
        prev_side = side
        up = side.cross(t).normalized()
        r = radius_fn(i / (n - 1))
        rows.append([bm.verts.new(p + (side * math.cos(2 * math.pi * k / sides) + up * math.sin(2 * math.pi * k / sides)) * r)
                     for k in range(sides)])
    for i in range(n - 1):
        for k in range(sides):
            bm.faces.new((rows[i][k], rows[i][(k + 1) % sides], rows[i + 1][(k + 1) % sides], rows[i + 1][k]))
    c0 = bm.verts.new(path[0] - (path[1] - path[0]).normalized() * radius_fn(0) * 0.6)
    c1 = bm.verts.new(path[-1] + (path[-1] - path[-2]).normalized() * radius_fn(1) * 0.6)
    for k in range(sides):
        bm.faces.new((c0, rows[0][(k + 1) % sides], rows[0][k]))
        bm.faces.new((c1, rows[-1][k], rows[-1][(k + 1) % sides]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm)


def build_sock(M, name):
    # leg down (z), heel bend, foot forward (-y); 0.42 m tall cartoon sock
    path = []
    for k in range(8):
        path.append(Vector((0, 0, 0.22 - 0.03 * k)))
    for k in range(1, 7):
        a = math.pi * 0.5 * k / 6
        path.append(Vector((0, -0.07 * (1 - math.cos(a)) - 0.0, 0.01 - 0.07 * math.sin(a))))
    for k in range(1, 6):
        path.append(Vector((0, -0.07 - 0.028 * k, -0.06)))
    path = [p + Vector((0, 0.05, -0.0)) for p in path]
    obj = path_tube(name, path, lambda t: 0.062 if t < 0.95 else 0.062 * (1 - (t - 0.95) * 6), sides=10)
    cols = [C.hex_rgba(h) for h in STRIPES[name]]
    toe_col = C.hex_rgba(STRIPES[name][0])

    def fn(v):
        if v.y < -0.02 and v.z < -0.0:
            return toe_col if v.y < -0.13 or v.z < -0.03 and v.y > 0.03 else cols[3]
        band = int(max(0.0, (0.27 - v.z)) / 0.045)
        return cols[band % len(cols)]
    color_attr(obj, fn)
    finish(obj, [M["M_Fabric"]], smooth_deg=80)
    return obj


def build_towel(M):
    bm = bmesh.new()
    w, h, nx, ny = 0.5, 0.32, 10, 7
    rows = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = -w / 2 + w * i / nx
            z = -h / 2 + h * j / ny
            y = 0.04 * math.sin(i / nx * math.pi * 2.2) + 0.03 * math.sin(j / ny * math.pi * 1.4)
            row.append(bm.verts.new(Vector((x, y, z))))
        rows.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.025)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_obj("SM_Towel", bm)
    a, b = C.hex_rgba("#FF7FBF"), C.hex_rgba("#FFFFFF")
    color_attr(obj, lambda v: a if int((v.x + 0.25) / 0.083) % 2 == 0 else b)
    finish(obj, [M["M_Fabric"]], smooth_deg=60)
    return obj


def build_shirt(M):
    bm = bmesh.new()
    outline = [Vector((-0.12, -0.17)), Vector((0.12, -0.17)), Vector((0.12, 0.08)), Vector((0.21, 0.02)),
               Vector((0.26, 0.11)), Vector((0.14, 0.2)), Vector((0.05, 0.2)), Vector((0.0, 0.16)),
               Vector((-0.05, 0.2)), Vector((-0.14, 0.2)), Vector((-0.26, 0.11)), Vector((-0.21, 0.02)),
               Vector((-0.12, 0.08))]
    pts = resample_closed(rounded_polygon(outline, lambda i: 0.02, 2), 64)
    front = [bm.verts.new(Vector((p.x, 0.03, p.y))) for p in pts]
    back = [bm.verts.new(Vector((p.x, -0.03, p.y))) for p in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(pts)
    for i in range(n):
        bm.faces.new((front[i], back[i], back[(i + 1) % n], front[(i + 1) % n]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = new_obj("SM_Shirt", bm)
    a, b = C.hex_rgba("#5FD3FF"), C.hex_rgba("#FFE36B")
    color_attr(obj, lambda v: b if abs(v.z - 0.02) < 0.035 else a)
    finish(obj, [M["M_Fabric"]], smooth_deg=40)
    return obj


# ================================================================== 7. bubble
def build_bubble(M):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=0.5)
    obj = new_obj("SM_Bubble", bm)
    finish(obj, [M["M_Bubble"]], smooth_deg=180)
    return obj


# ================================================================== preview materials (EEVEE look only)
def preview_tweaks(M):
    neon_cols = ["#45D5E5", "#E070D0", "#F8DC6A"]
    return neon_cols


def main():
    C.reset_scene()
    M = make_materials()
    objs = []
    objs.append(build_neon_star(M))
    objs.append(build_filled_star(M))
    objs.append(build_coin(M))
    objs.append(build_gem(M))
    objs.append(build_chevron(M))
    for nm, seed, spread, cnt in (("SM_Foam_A", 11, (0.9, 0.55), 9), ("SM_Foam_B", 23, (1.3, 0.65), 12),
                                  ("SM_Foam_C", 37, (0.55, 0.45), 6)):
        objs.append(build_suds_meta(M, nm, seed, spread, cnt, lod=0))
        objs.append(build_suds_meta(M, nm + "_LOD1", seed, spread, cnt, lod=1))
    for s in ("SM_Sock_A", "SM_Sock_B", "SM_Sock_C"):
        objs.append(build_sock(M, s))
    objs.append(build_towel(M))
    objs.append(build_shirt(M))
    objs.append(build_bubble(M))

    report = []
    for o in objs:
        if not o.data.uv_layers:
            box_uv(o)
        C.apply_transforms(o)
        tris = C.tri_count(o)
        report.append("%-14s %6d tris  dims %s" % (o.name, tris, tuple(round(d, 3) for d in o.dimensions)))
        o.location = (0, 0, 0)
        C.export_fbx([o], C.model_path(GROUP, o.name))
    print("\n".join("CHECK " + r for r in report))

    # ---------------- preview: lay the set out like a shelf, seen from the player side (+Y looking -Y)
    layout = {
        "SM_NeonStar": (-2.4, 0, 1.6), "SM_StarFilled": (-1.2, 0, 1.6), "SM_Coin": (0.0, 0, 1.6),
        "SM_Gem": (1.0, 0, 1.55), "SM_Bubble": (2.2, 0, 1.6),
        "SM_Chevron": (-2.2, 0.3, 0.05), "SM_Foam_A": (-0.6, 0, 0), "SM_Foam_B": (1.2, 0.2, 0), "SM_Foam_C": (2.7, 0, 0),
        "SM_Sock_A": (-2.6, 0, 0.75), "SM_Sock_B": (-1.9, 0, 0.75), "SM_Sock_C": (-1.2, 0, 0.75),
        "SM_Towel": (0.1, 0, 0.85), "SM_Shirt": (0.9, 0, 0.85),
    }
    for o in objs:
        if o.name in layout:
            o.location = layout[o.name]
        elif o.name.endswith("_LOD1"):
            o.hide_render = True
    # neon colours for the preview
    for i, (nm, col) in enumerate((("SM_NeonStar", "#45D5E5"), ("SM_StarFilled", "#F8DC6A"))):
        o = bpy.data.objects[nm]
        m = C.material("PV_" + nm, col, roughness=0.3, emission=col, emission_strength=4.0)
        o.data.materials[0] = m
    # rotate items so the camera (at +Y, looking -Y) sees their faces
    bpy.data.objects["SM_Chevron"].rotation_euler = (math.radians(-35), 0, math.radians(180))
    floor = bpy.data.meshes.new("floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=8)
    bm.to_mesh(floor)
    fo = bpy.data.objects.new("floor", floor)
    bpy.context.scene.collection.objects.link(fo)
    fo.data.materials.append(C.material("PV_Floor", "#3A2A6A", roughness=0.6))
    # fabric vertex colours in the preview
    fab = M["M_Fabric"]
    nt = fab.node_tree
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    C.render_preview(C.preview_path("Props_set"), camera_location=(0.0, 7.5, 2.6), target=(0.0, 0.0, 0.75),
                     lens=40, resolution=(1280, 720), light_scale=2.2)
    print("DONE build_props")


if __name__ == "__main__":
    main()
