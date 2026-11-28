"""S2 Tunnel v1 - ENVIRONMENT MODEL (environment-modeler; only this role edits this file).

build(ctx) -> list of NEW objects authored in TRACK SPACE (Blender X = lateral m, + right; Y = track distance d m; Z = height above the
track centre line; tunnel axis at Z = 2.3, drum radius 4.2), linked into collection "S2V1_TRACK", every object tagged obj["s2v1_part"].
The assembly (s2v1_render.py) bends each object into world space exactly like the game.

Pieces (all procedural, numpy + bpy data API, idempotent - rebuilt from scratch on every run):
  drum       game meshes (smooth cylinder r 4.2, clean 0-1 UVs, inward normals) 40.2-62 m and 62-80 m
  drum_hp    bake sources: the same shell with REAL through-perforations (bevelled stadium slots in rows following the curvature,
             sheet thickness 4.5 cm) + a dark backing shell 0.3 m behind (material slot 1). Not for export.
  band       thick rounded violet bands (lathe of a sculpted D profile with stepped flanges)
  band_lip   separate luminous lip tubes on the bands (crest + front shoulder)
  gold_ring  the big bulb ring (d 52.5) and the smaller second ring (d 74): multi-step filleted profile (back flange, inner roll,
             recessed bulb channel, raised outer roll)
  bulb_socket / bulb   cups + glass bulbs set in the channel of each gold ring
  star       neon stars = round tubes swept along a rounded 5-point outline wrapped onto the drum (obj["s2v1_color"])
  star_glow  the filled star backplate under each tube (wrapped onto the drum)
Old tunnel: instead of hiding whole old collections (REPLACES), build() deletes only the old tunnel faces whose track distance lies in
[D0, D1] (in memory, never saved) - the old tunnel beyond d 80 (where the exported track frames end) stays as the deep core.
Drum render view: a render_pre handler shows drum_hp (with the drum's material in slot 0) until a drum bake exists in
Tools/Blender/work/s2v1/bakes/ (drum*normal*), then the game mesh; force with env S2V1_DRUM_VIEW = hp | game.
"""
import glob
import math
import os

import bpy
import numpy as np

AXIS_Z = 2.3
R_WALL = 4.2
D0, D1 = 40.2, 80.0
REPLACES = []                     # old tunnel is trimmed by distance instead (see trim_old)
TRIM_OLD = ["CTX_old_tunnel_wall", "CTX_old_tunnel_rings", "CTX_old_tunnel_stars"]
BAKES = "C:/Users/josia/thanksgiving/Tools/Blender/work/s2v1/bakes"

# ---------------------------------------------------------------- layout (track space), measured on the ORIGINAL through R2
# screen radii around the near vanishing centre (707, 212): band A lip 256 px, band B 207 px, gold ring 1 bulbs ~123 px, gold ring 2 ~63 px
BANDS = [  # (name, d centre, half width, depth, lips)
    ("A", 41.05, 0.50, 0.40, ("crest", "front")),
    ("B", 43.70, 0.36, 0.30, ("crest",)),
    ("C", 72.80, 0.34, 0.28, ("crest",)),
    ("D", 79.55, 0.36, 0.30, ("crest",)),
]
GOLD = [  # (name, d centre, scale of the profile, bulbs, bulb radius)
    ("G1", 52.50, 1.00, 28, 0.085),
    ("G2", 74.40, 0.92, 24, 0.080),
]
STARS = [  # (name, d, angle deg (0 top, + right), size m (tip to tip), colour, roll deg)
    ("Y_UL", 41.9, -52, 1.10, "yellow", 0),
    ("Y_UR", 40.75, 64, 1.15, "yellow", 0),
    ("C_L", 49.2, -49, 1.15, "cyan", 0),
    ("C_R", 44.9, 71, 1.20, "cyan", 0),
    ("P_R", 41.0, 100, 0.95, "pink", 0),
    ("Y_s", 64.0, 62, 1.00, "yellow", 0),
    ("P_s", 67.8, 112, 1.05, "pink", 0),
]
# perforation zones (between the elements; each zone has its own tile grid, its seams lie under a band / ring)
SLOT_BIG = dict(pu=0.62, pv=0.50, hu=0.21, hv=0.13, n=2.3)      # big ovals near the door
SLOT_DASH = dict(pu=0.50, pv=0.38, hu=0.17, hv=0.055, n=2.8)     # the rows of small dashes deeper in

PH = {  # flat placeholder colours by tag (materials-artist owns the real materials)
    "drum": ((0.388, 0.310, 0.608), 0.9, 0.3, 0.0),
    "slot": ((0.06, 0.045, 0.10), 0.0, 0.8, 0.0),
    "band": ((0.48, 0.36, 0.75), 0.3, 0.35, 0.0),
    "band_lip": ((0.87, 0.82, 0.90), 0.0, 0.3, 6.0),
    "gold_ring": ((0.78, 0.58, 0.31), 1.0, 0.22, 0.0),
    "bulb_socket": ((0.55, 0.36, 0.17), 1.0, 0.3, 0.0),
    "bulb": ((0.95, 0.85, 0.51), 0.0, 0.1, 12.0),
    "star_yellow": ((0.94, 0.84, 0.44), 0.0, 0.2, 10.0),
    "star_cyan": ((0.35, 0.79, 0.86), 0.0, 0.2, 10.0),
    "star_pink": ((0.88, 0.45, 0.71), 0.0, 0.2, 10.0),
    "star_glow": ((0.55, 0.45, 0.70), 0.0, 0.5, 0.6),
}


def srgb_to_lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def ph_mat(key):
    name = "S2V1_PH_" + key
    m = bpy.data.materials.get(name)
    if m:
        return m
    col, met, rough, emit = PH[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    lin = srgb_to_lin(col) + (1.0,)
    b.inputs["Base Color"].default_value = lin
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    if emit > 0:
        b.inputs["Emission Color"].default_value = lin
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = lin
    return m


# ---------------------------------------------------------------- generic mesh helpers
def cyl(theta, r, d):
    """track-space point(s) on a cylinder around the tunnel axis: angle theta (0 top, + right), radius r, distance d."""
    return np.stack([r * np.sin(theta), d, AXIS_Z + r * np.cos(theta)], -1)


def make_obj(name, verts, faces, part, mats, coll, loop_uv=None, mat_idx=None, smooth=True, sharp_deg=None):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in np.asarray(verts, dtype=np.float64)], [], [tuple(int(i) for i in f) for f in faces])
    if loop_uv is not None and len(loop_uv) == len(me.loops):
        uv = me.uv_layers.new(name="UVMap")
        uv.data.foreach_set("uv", np.asarray(loop_uv, dtype=np.float32).ravel())
    for m in mats:
        me.materials.append(m)
    if mat_idx is not None:
        me.polygons.foreach_set("material_index", np.asarray(mat_idx, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.full(len(me.polygons), smooth, dtype=bool))
    if smooth and sharp_deg:
        try:
            me.set_sharp_from_angle(angle=math.radians(sharp_deg))
        except Exception:
            pass
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob["s2v1_part"] = part
    return ob


def orient(ob, want="in"):
    """make the face normals point toward the tunnel axis ("in") or away from the solid's centre line ("out" = closed solids).
    For lathed closed solids "out" means: normals point away from the profile's own centroid (recalc via bmesh)."""
    import bmesh
    me = ob.data
    if want == "solid":
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free(); me.update()
        return
    n = np.empty(len(me.polygons) * 3); me.polygons.foreach_get("normal", n); n = n.reshape(-1, 3)
    c = np.empty(len(me.polygons) * 3); me.polygons.foreach_get("center", c); c = c.reshape(-1, 3)
    radial = np.stack([c[:, 0], np.zeros(len(c)), c[:, 2] - AXIS_Z], -1)
    s = (n * radial).sum(1)
    inward = (s < 0).mean()
    if (want == "in" and inward < 0.5) or (want == "out" and inward > 0.5):
        me.flip_normals(); me.update()


def grid_faces(nj, ni, wrap_j=True, wrap_i=False, uv_u=None, uv_v=None):
    """quad faces over a (nj, ni) vertex grid (index j*ni + i) + per-loop UVs from u(j') / v(i') (j' up to nj for the seam)."""
    faces, uvs = [], []
    jmax = nj if wrap_j else nj - 1
    imax = ni if wrap_i else ni - 1
    for j in range(jmax):
        j1 = (j + 1) % nj
        for i in range(imax):
            i1 = (i + 1) % ni
            faces.append((j * ni + i, j * ni + i1, j1 * ni + i1, j1 * ni + i))
            if uv_u is not None:
                uvs += [(uv_u[j], uv_v[i]), (uv_u[j], uv_v[i + 1]), (uv_u[j + 1], uv_v[i + 1]), (uv_u[j + 1], uv_v[i])]
    return faces, (np.array(uvs) if uvs else None)


def fillet(pts, radii, n=4, closed=True):
    """replace polygon corners by circular arcs (radius per vertex, 0 = sharp); 2D points (a, b)."""
    P = [np.array(p, dtype=np.float64) for p in pts]
    out = []
    N = len(P)
    for k in range(N):
        if not closed and (k == 0 or k == N - 1):
            out.append(P[k]); continue
        p0, p1, p2 = P[k - 1], P[k], P[(k + 1) % N]
        r = radii[k]
        if r <= 0:
            out.append(p1); continue
        u1 = p0 - p1; l1 = np.linalg.norm(u1); u1 /= l1
        u2 = p2 - p1; l2 = np.linalg.norm(u2); u2 /= l2
        cosang = float(np.clip(u1 @ u2, -1, 1)); ang = math.acos(cosang)
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(p1); continue
        t = min(r / math.tan(ang / 2), 0.45 * l1, 0.45 * l2)
        rr = t * math.tan(ang / 2)
        A = p1 + u1 * t; B = p1 + u2 * t
        bis = (u1 + u2); bis /= np.linalg.norm(bis)
        cen = p1 + bis * (rr / math.sin(ang / 2))
        a0 = math.atan2(*(A - cen)[::-1]); a1 = math.atan2(*(B - cen)[::-1])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for s in range(n + 1):
            a = a0 + da * s / n
            out.append(cen + rr * np.array([math.cos(a), math.sin(a)]))
    return out


def lathe(name, prof, d0, nseg, part, mats, coll, urep=8.0, closed=True, normals="solid", sharp_deg=50):
    """revolve a 2D profile [(dy, r), ...] around the tunnel axis at track distance d0."""
    prof = np.asarray(prof, dtype=np.float64)
    ni = len(prof)
    th = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    V = np.zeros((nseg, ni, 3))
    for i, (dy, r) in enumerate(prof):
        V[:, i] = cyl(th, r, d0 + dy)
    seg = np.linalg.norm(np.diff(np.vstack([prof, prof[:1]]) if closed else prof, axis=0), axis=1)
    vv = np.concatenate([[0], np.cumsum(seg)]); vv /= vv[-1]
    uu = np.linspace(0, urep, nseg + 1)
    faces, uv = grid_faces(nseg, ni, True, closed, uu, vv)
    ob = make_obj(name, V.reshape(-1, 3), faces, part, mats, coll, loop_uv=uv, sharp_deg=sharp_deg)
    orient(ob, normals)
    return ob


# ---------------------------------------------------------------- drum: game mesh + perforated bake source
def drum_game(name, da, db, coll, nseg=128, step=0.5):
    nrow = max(2, int(round((db - da) / step)) + 1)
    th = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    ds = np.linspace(da, db, nrow)
    V = np.zeros((nseg, nrow, 3))
    for i, d in enumerate(ds):
        V[:, i] = cyl(th, R_WALL, d)
    faces, uv = grid_faces(nseg, nrow, True, False, np.linspace(0, 1, nseg + 1), np.linspace(0, 1, nrow))
    ob = make_obj(name, V.reshape(-1, 3), faces, "drum", [ph_mat("drum")], coll, loop_uv=uv)
    orient(ob, "in")
    return ob


BOUND = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (3, 4), (2, 4), (1, 4), (0, 4), (0, 3), (0, 2), (0, 1)]


def perforated(name, da, db, coll, spec, blank_fn=None, depth=0.045, bevel=0.010):
    """drum shell da..db with real through-slots: tile grid (Nu around x Nv along), each tile = 16-vertex boundary on a shared lattice
    + a superellipse slot rim, bevel ring and through-wall ring. Blank tiles (blank_fn) are fanned flat."""
    circ = 2 * math.pi * R_WALL
    Nu = int(round(circ / spec["pu"])); Nv = max(1, int(round((db - da) / spec["pv"])))
    pu_ang = 2 * math.pi / Nu; pv = (db - da) / Nv
    hu, hv, ne = spec["hu"], spec["hv"], spec["n"]
    LU, LV = 4 * Nu, 4 * Nv + 1
    gu, gv = np.meshgrid(np.arange(LU), np.arange(LV), indexing="ij")
    used = (gu % 4 == 0) | (gv % 4 == 0)
    lid = -np.ones((LU, LV), dtype=np.int64)
    lid[used] = np.arange(used.sum())
    lat = cyl(gu[used] * pu_ang / 4, R_WALL, da + gv[used] * pv / 4)
    verts = [lat]; nv = len(lat)
    faces = []; mat = []
    # superellipse rim param aligned with the boundary sequence (corner (0,0) = 225 deg)
    psi = np.radians(225 + 22.5 * np.arange(16))
    c, s = np.cos(psi), np.sin(psi)
    ex = 2.0 / ne
    rim_u = hu * np.sign(c) * np.abs(c) ** ex
    rim_v = hv * np.sign(s) * np.abs(s) ** ex
    rings = [(0.0, 0.0), (bevel, bevel * 0.8), (bevel * 1.4, depth)]   # (inset m, depth m)
    for iu in range(Nu):
        for iv in range(Nv):
            b_ids = [lid[(4 * iu + a) % LU, 4 * iv + b] for a, b in BOUND]
            thc = (iu + 0.5) * pu_ang; dc = da + (iv + 0.5) * pv
            if blank_fn is not None and blank_fn(iu, iv, Nu, Nv, thc, dc):
                verts.append(cyl(np.array([thc]), R_WALL, np.array([dc])))
                cid = nv; nv += 1
                for k in range(16):
                    faces.append((b_ids[k], b_ids[(k + 1) % 16], cid)); mat.append(0)
                continue
            prev = b_ids
            for ri, (inset, dep) in enumerate(rings):
                sc_u = max(hu - inset, 0.01) / hu; sc_v = max(hv - inset, 0.01) / hv
                ru = rim_u * sc_u; rv = rim_v * sc_v
                P = cyl(thc + ru / R_WALL, R_WALL + dep, dc + rv)
                ids = list(range(nv, nv + 16)); verts.append(P); nv += 16
                for k in range(16):
                    k1 = (k + 1) % 16
                    faces.append((prev[k], prev[k1], ids[k1], ids[k])); mat.append(0 if ri == 0 else 1 if ri == 2 else 0)
                prev = ids
    V = np.vstack(verts)
    ob = make_obj(name, V, faces, "drum_hp", [ph_mat("drum"), ph_mat("slot")], coll, mat_idx=mat, sharp_deg=70)
    orient(ob, "in")
    # dark backing shell behind the perforations (part of the bake source)
    nseg = 96; th = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    BV = np.stack([cyl(th, R_WALL + 0.30, da), cyl(th, R_WALL + 0.30, db)], 1).reshape(-1, 3)
    bf, _ = grid_faces(nseg, 2, True, False)
    bk = make_obj(name + "_backing", BV, bf, "drum_hp", [ph_mat("drum"), ph_mat("slot")], coll, mat_idx=[1] * len(bf))
    orient(bk, "in")
    return [ob, bk], Nu * Nv


def blank_bottom(margin_rows=1):
    def fn(iu, iv, Nu, Nv, thc, dc):
        a = (math.degrees(thc) + 180) % 360 - 180
        if abs(a) > 128:                     # under the slide / foam: no holes (cheaper, never seen)
            return True
        if iv < margin_rows or iv >= Nv - margin_rows:   # clean margin next to the bands / rings
            return True
        return iu % 7 == 6                   # a narrow plain column every 7 slots (the original's grouped rows)
    return fn


# ---------------------------------------------------------------- bands, lips
def band_profile(hw, dep, flange=0.08):
    rw = R_WALL
    pts = [(-hw - flange, rw + 0.08), (-hw - flange, rw - 0.03), (-hw, rw - 0.07)]
    # rounded D bulge: superellipse from the front shoulder to the back shoulder
    n = 16
    for k in range(1, n):
        a = math.pi * k / n
        x = -math.cos(a); y = math.sin(a)
        pts.append((hw * np.sign(x) * abs(x) ** 0.75, rw - 0.07 - (dep - 0.07) * y ** 0.6))
    pts += [(hw, rw - 0.07), (hw + flange, rw - 0.03), (hw + flange, rw + 0.08)]
    radii = [0, 0.015, 0.03] + [0] * (n - 1) + [0.03, 0.015, 0]
    return fillet(pts, radii, n=3)


def torus(name, d, R, rt, nseg, nt, part, mats, coll, dy_dir=None):
    th = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    ph = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    V = np.zeros((nseg, nt, 3))
    for i, p in enumerate(ph):
        V[:, i] = cyl(th, R + rt * math.cos(p), d + rt * math.sin(p))
    faces, uv = grid_faces(nseg, nt, True, True, np.linspace(0, 16, nseg + 1), np.linspace(0, 1, nt + 1))
    ob = make_obj(name, V.reshape(-1, 3), faces, part, mats, coll, loop_uv=uv)
    orient(ob, "solid")
    return ob


def build_band(name, d, hw, dep, lips, coll):
    prof = band_profile(hw, dep)
    objs = [lathe("S2V1_band_" + name, prof, d, 112, "band", [ph_mat("band")], coll, urep=12.0)]
    crest_r = R_WALL - dep
    for lip in lips:
        if lip == "crest":
            dy, r, rt = -0.10 * hw, crest_r + 0.012, 0.042
        else:   # front shoulder: on the bulge facing the camera
            dy, r, rt = -0.78 * hw, R_WALL - 0.07 - (dep - 0.07) * 0.55, 0.036
        objs.append(torus("S2V1_bandlip_%s_%s" % (name, lip), d + dy, r, rt, 112, 8, "band_lip", [ph_mat("band_lip")], coll))
    return objs


# ---------------------------------------------------------------- gold rings, sockets, bulbs
def gold_profile(s):
    """multi-step polished ring profile (dy, r); front = -dy (toward the camera). s scales the radial depth / width."""
    rw = R_WALL
    w = lambda x: x * s
    pts = [
        (0.36 * s, rw + 0.08),            # back, behind the wall
        (0.36 * s, rw - 0.06),            # back flange
        (0.24 * s, rw - w(0.10)),
        (0.22 * s, rw - w(0.46)),         # back face down
        (0.12 * s, rw - w(0.58)),         # inner roll (back)
        (-0.16 * s, rw - w(0.60)),        # inner face
        (-0.30 * s, rw - w(0.54)),        # inner raised lip (front)
        (-0.30 * s, rw - w(0.44)),
        (-0.22 * s, rw - w(0.41)),        # step down into the bulb channel
        (-0.22 * s, rw - w(0.15)),        # channel floor (bulbs sit here)
        (-0.32 * s, rw - w(0.12)),        # outer raised roll
        (-0.32 * s, rw - w(0.02)),
        (-0.24 * s, rw + 0.00),
        (-0.24 * s, rw + 0.08),
    ]
    radii = [0, 0.03, 0.04, 0.05, 0.07, 0.07, 0.04, 0.035, 0.02, 0.02, 0.035, 0.04, 0.02, 0]
    return fillet(pts, radii, n=4), (-0.22 * s, rw - w(0.28))   # profile, bulb seat (dy, r)


def build_gold(name, d, s, nb, rb, coll):
    prof, (sdy, sr) = gold_profile(s)
    objs = [lathe("S2V1_gold_" + name, prof, d, 120, "gold_ring", [ph_mat("gold_ring")], coll, urep=10.0, sharp_deg=60)]
    # sockets: small lathed cups, axis = -d (facing the camera), sitting on the channel floor
    cup = fillet([(0.0, rb * 0.06), (0.0, rb * 1.45), (-0.035, rb * 1.42), (-0.045, rb * 1.18), (-0.02, rb * 1.05), (-0.02, rb * 0.06)],
                 [0, 0.008, 0.01, 0.008, 0.005, 0], n=2, closed=False)
    nc = 12
    SV, SF = [], []
    BV, BF = [], []
    sph_lat, sph_lon = 7, 12
    for k in range(nb):
        th = 2 * math.pi * (k + 0.5) / nb
        radial = np.array([math.sin(th), 0.0, math.cos(th)])
        tang = np.array([math.cos(th), 0.0, -math.sin(th)])
        axis = np.array([0.0, -1.0, 0.0])
        base = np.array([0.0, d + sdy, AXIS_Z]) + radial * sr
        # cup (h <= 0 = toward the camera along axis)
        ring_pts = []
        for (h, rho) in cup:
            for m in range(nc):
                a = 2 * math.pi * m / nc
                ring_pts.append(base + axis * (-h) + (radial * math.cos(a) + tang * math.sin(a)) * rho)
        b0 = sum(len(x) for x in SV)
        SV.append(np.array(ring_pts))
        nr = len(cup)
        for i in range(nr - 1):
            for m in range(nc):
                m1 = (m + 1) % nc
                SF.append((b0 + i * nc + m, b0 + i * nc + m1, b0 + (i + 1) * nc + m1, b0 + (i + 1) * nc + m))
        # bulb: uv sphere centred 0.75 rb in front of the channel floor
        cen = base + axis * (rb * 0.75)
        pts = [cen - axis * rb]
        for la in range(1, sph_lat):
            phi = math.pi * la / sph_lat
            for lo in range(sph_lon):
                a = 2 * math.pi * lo / sph_lon
                pts.append(cen + (-axis * math.cos(phi) + (radial * math.cos(a) + tang * math.sin(a)) * math.sin(phi)) * rb)
        pts.append(cen + axis * rb)
        c0 = sum(len(x) for x in BV)
        BV.append(np.array(pts))
        top, bot = c0, c0 + len(pts) - 1
        for lo in range(sph_lon):
            lo1 = (lo + 1) % sph_lon
            BF.append((top, c0 + 1 + lo1, c0 + 1 + lo))
        for la in range(sph_lat - 2):
            r0 = c0 + 1 + la * sph_lon; r1 = r0 + sph_lon
            for lo in range(sph_lon):
                lo1 = (lo + 1) % sph_lon
                BF.append((r0 + lo, r0 + lo1, r1 + lo1, r1 + lo))
        last = c0 + 1 + (sph_lat - 2) * sph_lon
        for lo in range(sph_lon):
            lo1 = (lo + 1) % sph_lon
            BF.append((last + lo, last + lo1, bot))
    so = make_obj("S2V1_sockets_" + name, np.vstack(SV), SF, "bulb_socket", [ph_mat("bulb_socket")], coll, sharp_deg=60)
    orient(so, "solid")
    bo = make_obj("S2V1_bulbs_" + name, np.vstack(BV), BF, "bulb", [ph_mat("bulb")], coll)
    orient(bo, "solid")
    return objs + [so, bo]


# ---------------------------------------------------------------- neon stars (wrapped onto the drum)
def star_outline(size, ri_frac=0.47, n_fil=5):
    Ro = size / 2.0 / 0.95; Ri = Ro * ri_frac
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = Ro if k % 2 == 0 else Ri
        pts.append((r * math.cos(a), r * math.sin(a)))
    radii = [Ro * 0.16 if k % 2 == 0 else Ro * 0.07 for k in range(10)]
    out = fillet(pts, radii, n=n_fil)
    return np.array(out)


def build_star(name, d, ang, size, colour, roll, coll, standoff=0.10):
    th0 = math.radians(ang)
    up_sign = -1.0 if ang > 0 else 1.0      # screen-up on the wall = toward the ceiling along the circumference
    if abs(ang) > 150:
        up_sign = 1.0
    o2 = star_outline(size)
    rl = math.radians(roll)
    rot = np.array([[math.cos(rl), -math.sin(rl)], [math.sin(rl), math.cos(rl)]])
    o2 = o2 @ rot.T
    # 2D (x = across, y = up) -> wall (arc u along the circumference, v along d); up = circumferential toward the ceiling,
    # tilted toward the camera a little so the star reads upright from the gameplay / R2 cameras
    tilt = 0.35 * abs(math.cos(th0))
    across = -1.0 if ang > 0 else 1.0      # screen-right on the right wall = toward the camera (-d)
    du = up_sign * o2[:, 1] * math.cos(tilt)
    dv = -o2[:, 1] * math.sin(tilt) + o2[:, 0] * across
    R = R_WALL - standoff
    C = cyl(th0 + du / R, R, d + dv)                      # centre line on the cylinder
    n = len(C)
    tube_r = 0.040 * size / 1.1
    nt = 8
    V = []
    for i in range(n):
        p = C[i]; T = C[(i + 1) % n] - C[i - 1]; T /= np.linalg.norm(T)
        N = np.array([-p[0], 0.0, AXIS_Z - p[2]]); N /= np.linalg.norm(N)
        N = N - T * (N @ T); N /= np.linalg.norm(N)
        B = np.cross(T, N)
        for m in range(nt):
            a = 2 * math.pi * m / nt
            V.append(p + tube_r * (math.cos(a) * N + math.sin(a) * B))
    faces, uv = grid_faces(n, nt, True, True, np.linspace(0, 6, n + 1), np.linspace(0, 1, nt + 1))
    key = "star_" + colour
    t = make_obj("S2V1_star_" + name, np.array(V), faces, "star", [ph_mat(key)], coll, loop_uv=uv)
    orient(t, "solid")
    t["s2v1_color"] = colour
    # filled backplate (star_glow): fan from the centre, slightly inset, wrapped onto the drum just in front of the wall
    o_in = o2 * 0.93
    du2 = up_sign * o_in[:, 1] * math.cos(tilt); dv2 = -o_in[:, 1] * math.sin(tilt) + o_in[:, 0] * across
    Rg = R_WALL - 0.025
    G = np.vstack([cyl(np.array([th0]), Rg, np.array([d])), cyl(th0 + du2 / Rg, Rg, d + dv2)])
    gf = [(0, 1 + i, 1 + (i + 1) % len(o_in)) for i in range(len(o_in))]
    g = make_obj("S2V1_starglow_" + name, G, gf, "star_glow", [ph_mat("star_glow")], coll)
    orient(g, "in")
    g["s2v1_color"] = colour
    return [t, g]


# ---------------------------------------------------------------- old tunnel trim + drum render view
def trim_old(C, da, db):
    import bmesh
    F = C._frame_arrays()
    pos, fwd, D = F["pos"], F["fwd"], F["d"]
    total = 0
    for cname in TRIM_OLD:
        col = bpy.data.collections.get(cname)
        if not col:
            continue
        for o in col.all_objects:
            if o.type != "MESH":
                continue
            me = o.data
            npoly = len(me.polygons)
            if npoly == 0:
                continue
            cen = np.empty(npoly * 3); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
            cen = (np.array(o.matrix_world) @ np.c_[cen, np.ones(npoly)].T).T[:, :3]
            U = cen[:, [0, 2, 1]]                                     # Blender world -> Unity world
            best = np.zeros(npoly, dtype=np.int64); bestd = np.full(npoly, np.inf)
            for k in range(0, len(D), 1):
                dd = ((U - pos[k]) ** 2).sum(1)
                m = dd < bestd; bestd[m] = dd[m]; best[m] = k
            dest = D[best] + ((U - pos[best]) * fwd[best]).sum(1)
            kill = (dest >= da) & (dest <= db) & (np.sqrt(bestd) < 9.0)
            if not kill.any():
                continue
            bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(kill)[0]], context="FACES_ONLY")
            loose = [v for v in bm.verts if not v.link_faces]
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
            bm.to_mesh(me); bm.free(); me.update()
            total += int(kill.sum())
    return total


def _drum_view(scene, *args):
    mode = os.environ.get("S2V1_DRUM_VIEW", "auto")
    if mode == "auto":
        mode = "game" if glob.glob(BAKES + "/drum*normal*") else "hp"
    world = [o for o in scene.objects if o.get("s2v1_source") and o.get("s2v1_part") in ("drum", "drum_hp")]
    games = [o for o in world if o.get("s2v1_part") == "drum"]
    gmat = games[0].material_slots[0].material if games and games[0].material_slots else None
    for o in world:
        if o.get("s2v1_part") == "drum":
            o.hide_render = (mode == "hp")
        else:
            o.hide_render = (mode != "hp")
            if mode == "hp" and gmat is not None and o.material_slots:
                o.material_slots[0].material = gmat
    print("ENV drum view: %s (%d game, %d hp objects)" % (mode, len(games), len(world) - len(games)))
    if os.environ.get("S2V1_ENV_DEBUG_FILL") == "1" and not any(o.name.startswith("LGT_S2v1") for o in scene.objects):
        import s2v1_common as C
        for i, d in enumerate((35.0, 42.0, 48.0, 55.0, 63.0, 71.0, 78.0)):
            nm = "DBG_env_fill_%d" % i
            if nm in bpy.data.objects:
                continue
            ld = bpy.data.lights.new(nm, "POINT"); ld.energy = 900.0 if d < 50 else 1400.0; ld.color = (0.85, 0.78, 1.0)
            ld.shadow_soft_size = 1.5
            lo = bpy.data.objects.new(nm, ld); scene.collection.objects.link(lo)
            lo.location = tuple(C.track_to_blender(np.array([[0.0, d, AXIS_Z + 0.6]]))[0])
        print("ENV debug fill lights added (no LGT_S2v1_* in the scene)")


def tris(ob):
    me = ob.data
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ---------------------------------------------------------------- build
def build(ctx):
    C = ctx["C"]
    coll = C.coll("S2V1_TRACK")
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    out = []
    # drum game meshes
    out.append(drum_game("S2V1_drum_A", D0, 62.0, coll))
    out.append(drum_game("S2V1_drum_B", 62.0, D1, coll))
    # perforated bake sources per zone (seams under the bands / rings)
    cuts = sorted([D0] + [b[1] for b in BANDS] + [g[1] for g in GOLD] + [D1])
    nslots = 0
    for i in range(len(cuts) - 1):
        a, b = cuts[i], cuts[i + 1]
        if b - a < 0.3:
            continue
        spec = SLOT_BIG if a < 41.5 else SLOT_DASH
        objs, n = perforated("S2V1_drumhp_%02d" % i, a, b, coll, spec, blank_bottom(1 if b - a > 1.5 else 0))
        out += objs; nslots += n
    for name, d, hw, dep, lips in BANDS:
        out += build_band(name, d, hw, dep, lips, coll)
    for name, d, s, nb, rb in GOLD:
        out += build_gold(name, d, s, nb, rb, coll)
    for name, d, ang, size, colour, roll in STARS:
        out += build_star(name, d, ang, size, colour, roll, coll)
    ntrim = trim_old(C, D0, D1)
    # drum view handler (replace an older copy of this function)
    hs = bpy.app.handlers.render_pre
    for h in list(hs):
        if getattr(h, "__name__", "") == "_drum_view":
            hs.remove(h)
    hs.append(_drum_view)
    # report
    by = {}
    for o in out:
        by.setdefault(o["s2v1_part"], []).append(tris(o))
    print("CHECK env: %d objects, old tunnel faces trimmed in d %.1f-%.1f: %d" % (len(out), D0, D1, ntrim))
    for k, v in sorted(by.items()):
        print("CHECK env tris %-12s %3d objs  total %8d  max/obj %7d" % (k, len(v), sum(v), max(v)))
    for o in out:
        print("ENV obj %-28s %-12s tris %7d" % (o.name, o["s2v1_part"], tris(o)))
    return out
