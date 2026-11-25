"""Bubble Wash Kingdom - hero mascot MODEL (no rig yet). Blender 5.3, headless, deterministic.

Run from the project root:
  blender --background --factory-startup --python Tools/Blender/scripts/build_mascot_model.py

Outputs
  Tools/Blender/work/mascot_model.blend                               hand-off file (rig + fur shells)
  Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_model.fbx  static check export (no armature)
  Docs/AssetPreviews/SK_Mascot_model_back.png / _front.png / _34.png  (900x900, EEVEE)

Objects (every origin = ground point between the feet, identity transforms, collection "SK_Mascot_model"):
  Body, Eye.L, Eye.R, Catchlight.L1/.L2/.R1/.R2, Mouth (+tiny nose), Tongue, Arm.L, Arm.R,
  Foot.L, Foot.R, Tail, Beanie, PomPom, StarBadge
Axes (Docs/AssetSpec.md): meters, Z up, he faces -Y, his right = -X, his left = +X. 1 BW = 0.85 m.
Body colour attribute "Col" (byte, corner): rgb = tint (white, rosy blush, darker bottom),
alpha = suggested fur-length mask (0 under the beanie and on the eyes/mouth/nose, 1 elsewhere).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import bwk_common as C  # noqa: E402

# ------------------------------------------------------------------ proportions (meters)
BODY_C = Vector((0.0, 0.0, 0.49))          # body centre
BODY_W, BODY_D, BODY_H = 0.85, 0.78, 0.84  # width (1 BW), depth, height
BODY_EGG = 0.10                            # >0: fuller toward the bottom
BODY_SEG = 15                              # quad sphere: 6*15*15 quads = 2700 tris

HAT_TILT = math.radians(-3.0)              # rotation about X: front edge up, crown leans back
HAT_R = Matrix.Rotation(HAT_TILT, 3, 'X')
HAT_R_INV = HAT_R.transposed()
HAT_AXIS = HAT_R @ Vector((0.0, 0.0, 1.0))
CUFF_BOTTOM_A = 74.0                       # deg from the hat axis: lowest point of the cuff roll
STRIPE_A = (53.6, 43.0)                    # main lavender band just above the cuff (alpha range)
CROWN_RINGS = [58.0, 53.6, 48.3, 43.0, 37.0, 31.0, 25.0, 19.5, 14.0, 9.0, 4.5]
TOP_STRIPE_A, TOP_STRIPE_HW = 27.0, 3.2    # extra front stripe (fades out toward the back)
TOP_STRIPE_FULL, TOP_STRIPE_END = 70.0, 125.0
RIB_AMP = 0.0035
CUFF_SEG = 80                              # 40 knit ribs
CUFF_PROFILE = [  # (alpha deg, offset from body surface, rib weight): roll under -> outer face -> tuck
    (71.5, -0.006, 0.0), (73.3, 0.008, 0.0), (74.3, 0.024, 0.0), (74.4, 0.040, 0.2), (73.6, 0.053, 0.6),
    (72.0, 0.060, 1.0), (68.0, 0.065, 1.0), (62.5, 0.066, 1.0), (57.5, 0.063, 1.0), (54.6, 0.056, 0.6),
    (53.4, 0.045, 0.2), (53.0, 0.031, 0.0), (53.6, 0.022, 0.0)]
CUFF_OFF = 0.065                           # nominal outer offset (star conforms to it)
STAR_A, STAR_PHI, STAR_ROT = 61.0, 33.0, -12.0   # on the cuff, 33 deg toward HIS LEFT (+X)
STAR_RO, STAR_RI = 0.080, 0.035
POMPOM_R, POMPOM_SINK = 0.18, 0.55

EYE_X, EYE_Z = 0.155, 0.52                 # eye centres on the front surface
EYE_H, EYE_RS, EYE_VS = 0.025, 0.12, 1.06  # protrusion, cap sphere radius, vertical stretch
EYE_SEG = 32
IRIS_R, PUPIL_IN, PUPIL_DOWN = 0.072, 0.014, 0.007   # UV radius 0.5 = IRIS_R; pupil toward the nose
MOUTH_Z, MOUTH_W, MOUTH_H, MOUTH_N = 0.39, 0.13, 0.105, 28
NOSE_Z = 0.462
BLUSH_X, BLUSH_Z, BLUSH_R = 0.235, 0.405, 0.058
ARM_Z = 0.50
ARM_PROFILE = [(-0.07, 0.050), (0.0, 0.058), (0.06, 0.062), (0.115, 0.066), (0.16, 0.063),
               (0.188, 0.052), (0.204, 0.034), (0.212, 0.0)]
FOOT_X, FOOT_Y, FOOT_TILT, FOOT_YAW = 0.21, 0.06, 64.0, 10.0
FOOT_HALF = (0.08, 0.11, 0.05)             # half width, half length, half height
PAD_LAYOUT = [(0.0, 0.024, 0.037, 0.029, 0.010),        # big pad (heel side, +Y local)
              (-0.036, -0.038, 0.015, 0.017, 0.0075),    # 3 toe beans (toes = -Y local)
              (0.0, -0.056, 0.016, 0.018, 0.0075),
              (0.036, -0.038, 0.015, 0.017, 0.0075)]
TAIL_R, TAIL_Z = 0.07, 0.335

WHITE = (1.0, 1.0, 1.0, 1.0)
PAD_PINK = (0.98, 0.64, 0.73, 1.0)         # Col tint (sRGB) for pads / beans
BLUSH_COL = (1.0, 0.70, 0.72)              # Col tint (sRGB) at the blush centre

BODY_BVH = None


# ------------------------------------------------------------------ small utilities
def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def set_byte_col(item, c):
    c = tuple(c) if len(c) == 4 else tuple(c) + (1.0,)
    try:
        item.color_srgb = c
    except AttributeError:
        item.color = (C.srgb_to_linear(c[0]), C.srgb_to_linear(c[1]), C.srgb_to_linear(c[2]), c[3])


def set_material_indices(me, idx):
    try:
        me.polygons.foreach_set("material_index", idx)
    except Exception:
        attr = me.attributes.get("material_index") or me.attributes.new("material_index", 'INT', 'FACE')
        attr.data.foreach_set("value", idx)


def sph_uv(d):
    """Spherical UV: u = 0.5 at the front (-Y), increasing toward +X, seam at the back; v bottom->top."""
    d = Vector(d).normalized()
    u = 0.5 + math.atan2(d.x, -d.y) / (2.0 * math.pi)
    v = 1.0 - math.acos(max(-1.0, min(1.0, d.z))) / math.pi
    return (u, v)


def frame_from(ez, up=Vector((0.0, 0.0, 1.0))):
    """Right-handed frame (ex, ey, ez) with ez given and ey as close to `up` as possible."""
    ez = Vector(ez).normalized()
    ex = Vector(up).cross(ez)
    if ex.length < 1e-6:
        ex = Vector((0.0, 1.0, 0.0)).cross(ez)
    ex.normalize()
    return ex, ez.cross(ex), ez


class MeshData:
    """Mesh accumulator: verts, faces + per-face material index, per-corner UVs and colours."""

    def __init__(self):
        self.v, self.f, self.m, self.uv, self.col = [], [], [], [], []

    def vert(self, co):
        self.v.append(Vector(co))
        return len(self.v) - 1

    def face(self, idx, mat=0, uv=None, col=None):
        idx = tuple(idx)
        self.f.append(idx)
        self.m.append(mat)
        self.uv.append(list(uv) if uv else [(0.0, 0.0)] * len(idx))
        self.col.append(list(col) if col else [WHITE] * len(idx))
        return len(self.f) - 1

    def extend(self, other):
        off = len(self.v)
        self.v += [v.copy() for v in other.v]
        for f, m, uv, col in zip(other.f, other.m, other.uv, other.col):
            self.f.append(tuple(i + off for i in f))
            self.m.append(m)
            self.uv.append(list(uv))
            self.col.append(list(col))
        return self

    def transform(self, mat4):
        self.v = [mat4 @ v for v in self.v]
        return self

    def set_uv(self, fn, wrap=True):
        out = []
        for f in self.f:
            uvs = [list(fn(i)) for i in f]
            if wrap:
                us = [p[0] for p in uvs]
                if max(us) - min(us) > 0.5:
                    for p in uvs:
                        if p[0] < 0.5:
                            p[0] += 1.0
            out.append([tuple(p) for p in uvs])
        self.uv = out
        return self

    def set_col(self, fn):
        self.col = [[fn(i, k) for i in f] for k, f in enumerate(self.f)]
        return self

    def tris(self):
        return sum(len(f) - 2 for f in self.f)

    def bvh(self):
        return BVHTree.FromPolygons([tuple(v) for v in self.v], self.f)

    def to_object(self, name, mats, collection):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        for m in mats:
            me.materials.append(m)
        set_material_indices(me, self.m)
        uvl = me.uv_layers.new(name="UVMap")
        cl = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
        for poly, uvs, cols in zip(me.polygons, self.uv, self.col):
            for li, uv, c in zip(poly.loop_indices, uvs, cols):
                uvl.data[li].uv = uv
                set_byte_col(cl.data[li], c)
        me.update()
        obj = bpy.data.objects.new(name, me)
        collection.objects.link(obj)
        return obj


def cube_sphere(n):
    """Equal-angle quad sphere, n x n quads per cube face, outward winding.
    Returns (unit vertices, quads, cube-face tag per quad: 0 +X, 1 -X, 2 +Y, 3 -Y, 4 +Z, 5 -Z)."""
    verts, index, quads, tags = [], {}, [], []

    def vid(p):
        key = (round(p.x, 6), round(p.y, 6), round(p.z, 6))
        i = index.get(key)
        if i is None:
            i = index[key] = len(verts)
            verts.append(p)
        return i

    axes = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, -1, 0), (0, 0, 1)),
            ((0, 1, 0), (-1, 0, 0), (0, 0, 1)), ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
            ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (0, 1, 0), (1, 0, 0))]
    for tag, (nn, aa, bb) in enumerate(axes):
        nv, av, bv = Vector(nn), Vector(aa), Vector(bb)
        grid = []
        for i in range(n + 1):
            a = math.tan(-math.pi / 4 + i * (math.pi / 2) / n)
            grid.append([vid((nv + av * a + bv * math.tan(-math.pi / 4 + j * (math.pi / 2) / n)).normalized())
                         for j in range(n + 1)])
        for i in range(n):
            for j in range(n):
                quads.append((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
                tags.append(tag)
    return verts, quads, tags


def bridge(md, r0, r1, mat, v0=0.0, v1=0.0):
    """Quads between ring r0 (lower along the profile) and r1; rings CCW about the profile axis -> outward."""
    n = len(r0)
    for j in range(n):
        k = (j + 1) % n
        md.face((r0[j], r0[k], r1[k], r1[j]), mat,
                [(j / n, v0), ((j + 1) / n, v0), ((j + 1) / n, v1), (j / n, v1)])


def fan_top(md, ring, pole, mat, v0=0.0, v1=1.0):
    n = len(ring)
    for j in range(n):
        k = (j + 1) % n
        md.face((ring[j], ring[k], pole), mat, [(j / n, v0), ((j + 1) / n, v0), ((j + 0.5) / n, v1)])


def ellipsoid(centre, ex, ey, ez, rx, ry, rz, seg=8, rings=4, mat=0, col=WHITE):
    """Low-poly UV ellipsoid in the right-handed frame (ex, ey, ez); planar UVs on (ex, ey)."""
    md = MeshData()
    centre = Vector(centre)
    bottom = md.vert(centre - ez * rz)
    rs = []
    for i in range(1, rings):
        th = math.pi * (1.0 - i / rings)
        rs.append([md.vert(centre + ex * (rx * math.sin(th) * math.cos(2 * math.pi * j / seg))
                           + ey * (ry * math.sin(th) * math.sin(2 * math.pi * j / seg))
                           + ez * (rz * math.cos(th))) for j in range(seg)])
    top = md.vert(centre + ez * rz)
    for j in range(seg):
        k = (j + 1) % seg
        md.face((bottom, rs[0][k], rs[0][j]), mat, col=[col] * 3)
    for a, b in zip(rs, rs[1:]):
        for j in range(seg):
            k = (j + 1) % seg
            md.face((a[j], a[k], b[k], b[j]), mat, col=[col] * 4)
    for j in range(seg):
        k = (j + 1) % seg
        md.face((rs[-1][j], rs[-1][k], top), mat, col=[col] * 3)
    md.set_uv(lambda i: (0.5 + (md.v[i] - centre).dot(ex) / (2 * rx),
                         0.5 + (md.v[i] - centre).dot(ey) / (2 * ry)), wrap=False)
    return md


# ------------------------------------------------------------------ body surface queries
def ray(bvh, origin, direction):
    hit = bvh.ray_cast(Vector(origin), Vector(direction).normalized())
    if hit[0] is None:
        raise RuntimeError("ray missed the body: %s %s" % (tuple(origin), tuple(direction)))
    return hit[0]


def body_dist(d):
    return (ray(BODY_BVH, BODY_C, d) - BODY_C).length


def front_frame(x, z, eps=0.025):
    """Point on the front (-Y) body surface at (x, z) and its smoothed outward normal."""
    def fp(xx, zz):
        return ray(BODY_BVH, (xx, 0.0, zz), (0.0, -1.0, 0.0))
    tx = (fp(x + eps, z) - fp(x - eps, z)).normalized()
    tz = (fp(x, z + eps) - fp(x, z - eps)).normalized()
    return fp(x, z), tx.cross(tz).normalized()


def face_frame(n, blend):
    """Feature frame: forward = surface normal blended toward -Y; ex ~ +X, ey ~ up."""
    f = n.lerp(Vector((0.0, -1.0, 0.0)), blend).normalized()
    ex = (Vector((1.0, 0.0, 0.0)) - f * f.x).normalized()
    return f, ex, f.cross(ex)


def hat_dir(alpha_deg, psi):
    a = math.radians(alpha_deg)
    return HAT_R @ Vector((math.sin(a) * math.cos(psi), math.sin(a) * math.sin(psi), math.cos(a)))


def hat_point(alpha_deg, psi, off):
    d = hat_dir(alpha_deg, psi)
    return BODY_C + d * (body_dist(d) + off)


def crown_off(alpha):
    t = max(0.0, 1.0 - alpha / 53.0)
    return 0.030 + 0.034 * t * t


def hat_v(alpha):
    return min(1.0, max(0.0, (CUFF_BOTTOM_A - alpha) / CUFF_BOTTOM_A))


def hat_alpha_of(p):
    """Angle (deg) of a world point from the hat axis, seen from the body centre."""
    d = HAT_R_INV @ (Vector(p) - BODY_C).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, d.z))))


# ------------------------------------------------------------------ materials (preview look; Unity remaps by slot name)
def _inp(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def _bump(nt, bsdf, height_socket, strength, distance=0.02):
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    _inp(bp, "Distance", distance)
    nt.links.new(height_socket, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return bp


def _noise_bump(nt, bsdf, scale, strength, distance=0.02):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    _inp(nz, "Detail", 6.0)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    return _bump(nt, bsdf, nz.outputs["Fac"], strength, distance)


def _col_tint(nt, bsdf):
    base = tuple(bsdf.inputs["Base Color"].default_value)[:3]
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = 'MULTIPLY'
    mul.inputs[0].default_value = base
    nt.links.new(attr.outputs["Color"], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs["Base Color"])


def _uv_ribs(nt, bsdf, ribs, strength):
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = ribs * 2.0 * math.pi
    nt.links.new(sep.outputs[0], mul.inputs[0])
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = 'SINE'
    nt.links.new(mul.outputs[0], sn.inputs[0])
    _bump(nt, bsdf, sn.outputs[0], strength, 0.004)


def _eye_shader(nt, bsdf):
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = 'SUBTRACT'
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    nt.links.new(uv.outputs["UV"], sub.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = 'LENGTH'
    nt.links.new(sub.outputs[0], ln.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = C.hex_rgba("#100810")
    cr.elements[1].position = 1.0
    cr.elements[1].color = C.hex_rgba("#F8F1F3")
    for pos, hx in ((0.17, "#140A12"), (0.215, "#2F1A2B"), (0.36, "#4B2C45"), (0.45, "#7A5C86"),
                    (0.485, "#2A1424"), (0.512, "#F8F1F3")):
        e = cr.elements.new(pos)
        e.color = C.hex_rgba(hx)
    nt.links.new(ln.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


def build_materials():
    M = {
        "Fur": C.material("M_Fur", "#E8679D", roughness=0.85),
        "PomPom": C.material("M_PomPom", "#7A32C6", roughness=0.9),
        "EyeIris": C.material("M_EyeIris", "#3A2236", roughness=0.08, coat=1.0),
        "EyeHighlight": C.material("M_EyeHighlight", "#FFFFFF", roughness=0.2, emission="#FFFFFF",
                                   emission_strength=1.5),
        "Mouth": C.material("M_Mouth", "#5A1A28", roughness=0.55),
        "Tongue": C.material("M_Tongue", "#F27C9A", roughness=0.4, coat=0.2),
        "PawPad": C.material("M_PawPad", "#FFF1F5", roughness=0.55),
        "HatKnit": C.material("M_HatKnit", "#5E22B0", roughness=0.9),
        "HatCuff": C.material("M_HatCuff", "#521C9C", roughness=0.9),
        "HatStripe": C.material("M_HatStripe", "#B48FD8", roughness=0.9),
        "StarBadge": C.material("M_StarBadge", "#FFCB1C", roughness=0.35, coat=0.4),
    }
    for key in ("Fur", "PawPad"):
        nt = M[key].node_tree
        bsdf = nt.nodes["Principled BSDF"]
        _col_tint(nt, bsdf)
        _inp(bsdf, "Sheen Weight", 0.5 if key == "Fur" else 0.2)
        _inp(bsdf, "Sheen Roughness", 0.4)
        if key == "Fur":
            _inp(bsdf, "Sheen Tint", C.hex_rgba("#FFB0D0"))
            _noise_bump(nt, bsdf, 160.0, 0.35, 0.01)
    for key, ribs in (("HatKnit", 64.0), ("HatCuff", 80.0), ("HatStripe", 64.0)):
        nt = M[key].node_tree
        bsdf = nt.nodes["Principled BSDF"]
        _inp(bsdf, "Sheen Weight", 0.15)
        _uv_ribs(nt, bsdf, ribs, 0.35)
    nt = M["PomPom"].node_tree
    bsdf = nt.nodes["Principled BSDF"]
    _inp(bsdf, "Sheen Weight", 0.3)
    _inp(bsdf, "Sheen Tint", C.hex_rgba("#C9A0FF"))
    _noise_bump(nt, bsdf, 240.0, 0.9, 0.01)
    # yarn-like light/dark variation (preview only)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 45.0
    _inp(nz, "Detail", 4.0)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = C.hex_rgba("#5A1F9E")
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = C.hex_rgba("#8E4FDA")
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt = M["EyeIris"].node_tree
    bsdf = nt.nodes["Principled BSDF"]
    _eye_shader(nt, bsdf)
    _inp(bsdf, "Coat Roughness", 0.03)
    return M


# ------------------------------------------------------------------ body
def build_body():
    dirs, quads, _ = cube_sphere(BODY_SEG)
    pts = [Vector((p.x * (1.0 - BODY_EGG * p.z), p.y * (1.0 - BODY_EGG * p.z), p.z)) for p in dirs]
    sx = max(abs(v.x) for v in pts)
    sy = max(abs(v.y) for v in pts)
    sz = max(abs(v.z) for v in pts)
    md = MeshData()
    for v in pts:
        md.vert((v.x / sx * BODY_W / 2, v.y / sy * BODY_D / 2, BODY_C.z + v.z / sz * BODY_H / 2))
    for q in quads:
        md.face(q, 0)
    md.set_uv(lambda i: sph_uv(dirs[i]))
    return md


def paint_body(md, eye_pts, mouth_pt, nose_pt, blush_pts):
    """Col.rgb = tint (white, rosy blush, darker bottom); Col.a = suggested fur-length mask."""
    def col(i, _k):
        p = md.v[i]
        g = 1.0 - 0.18 * smoothstep(0.34, 0.06, p.z)
        rgb = [g, g, g]
        for bp in blush_pts:
            w = 0.95 * math.exp(-((p - bp).length / BLUSH_R) ** 2)
            rgb = [c * (1.0 - w) + b * w for c, b in zip(rgb, BLUSH_COL)]
        a = smoothstep(CUFF_BOTTOM_A - 6.0, CUFF_BOTTOM_A + 1.0, hat_alpha_of(p))
        for ep in eye_pts:
            a *= smoothstep(0.08, 0.12, (p - ep).length)
        a *= smoothstep(0.075, 0.11, (p - mouth_pt).length)
        a *= smoothstep(0.02, 0.045, (p - nose_pt).length)
        return (rgb[0], rgb[1], rgb[2], a)
    md.set_col(col)


# ------------------------------------------------------------------ arms
def prof_r(profile, h):
    for (h0, r0), (h1, r1) in zip(profile, profile[1:]):
        if h0 <= h <= h1:
            return r0 + (r1 - r0) * (h - h0) / (h1 - h0)
    return profile[-1][1]


def build_arm(side):
    """side +1 = Arm.L (+X, his left), -1 = Arm.R. Fur capsule + white palm + 3 pink beans."""
    root = ray(BODY_BVH, (0.0, 0.0, ARM_Z), (side, 0.0, 0.0))
    d = Vector((side * 1.0, 0.06, 0.52)).normalized()     # out, slightly back, ~27 deg up
    ex, ey, ez = frame_from(d)
    md = MeshData()
    seg = 14
    rings = []
    for h, r in ARM_PROFILE[:-1]:
        rings.append([md.vert(root + ez * h + (ex * math.cos(2 * math.pi * j / seg)
                                              + ey * math.sin(2 * math.pi * j / seg)) * r) for j in range(seg)])
    tip = md.vert(root + ez * ARM_PROFILE[-1][0])
    for a, b in zip(rings, rings[1:]):
        bridge(md, a, b, 0)
    fan_top(md, rings[-1], tip, 0)
    md.set_uv(lambda i: sph_uv(md.v[i] - (root + ez * 0.07)))
    pd = Vector((0.0, -1.0, 0.0))
    pd = (pd - d * pd.dot(d)).normalized()          # palm faces forward
    hp = 0.135
    palm_c = root + d * hp + pd * (prof_r(ARM_PROFILE, hp) - 0.004)
    pex = d.cross(pd)
    md.extend(ellipsoid(palm_c, pex, d, pd, 0.036, 0.040, 0.011, seg=10, rings=5, mat=1, col=WHITE))
    hb = 0.188
    for ang in (-34.0, 0.0, 34.0):
        n = Matrix.Rotation(math.radians(ang), 3, d) @ pd
        c = root + d * hb + n * (prof_r(ARM_PROFILE, hb) + 0.001)
        bey = (d - n * d.dot(n)).normalized()
        md.extend(ellipsoid(c, bey.cross(n), bey, n, 0.012, 0.011, 0.006, seg=8, rings=4, mat=1, col=PAD_PINK))
    return md


# ------------------------------------------------------------------ feet
def foot_shape(p):
    e = 0.85
    sx = math.copysign(abs(p.x) ** e, p.x)
    sy = math.copysign(abs(p.y) ** e, p.y)
    sz = math.copysign(abs(p.z) ** e, p.z) if p.z >= 0 else -(abs(p.z) ** 0.55)
    w = FOOT_HALF[0] * (1.0 + 0.12 * (-p.y))        # a little wider at the toes (-Y)
    return Vector((sx * w, sy * FOOT_HALF[1], sz * FOOT_HALF[2]))


def build_foot(side):
    """Rounded oval foot, toes -Y; cube face -Z = flat sole (M_PawPad white) with big pad + 3 toe beans."""
    foot = MeshData()
    dirs, quads, tags = cube_sphere(4)
    for p in dirs:
        foot.vert(foot_shape(p))
    for q, t in zip(quads, tags):
        foot.face(q, 1 if t == 5 else 0)
    foot.set_uv(lambda i: sph_uv(dirs[i]))
    fb = foot.bvh()
    ez, ex = Vector((0.0, 0.0, -1.0)), Vector((1.0, 0.0, 0.0))
    ey = ez.cross(ex)
    for (px, py, rx, ry, rz) in PAD_LAYOUT:
        hit = ray(fb, (px, py, 0.0), (0.0, 0.0, -1.0))
        big = rx > 0.02
        foot.extend(ellipsoid(hit + Vector((0.0, 0.0, rz * 0.25)), ex, ey, ez, rx, ry, rz,
                              seg=10 if big else 8, rings=5 if big else 4, mat=1, col=PAD_PINK))
    m = (Matrix.Translation((side * FOOT_X, FOOT_Y, 0.0))
         @ Matrix.Rotation(math.radians(side * FOOT_YAW), 4, 'Z')
         @ Matrix.Rotation(math.radians(FOOT_TILT), 4, 'X'))
    foot.transform(m)
    zmin = min(v.z for v in foot.v)
    foot.transform(Matrix.Translation((0.0, 0.0, -zmin)))
    return foot


# ------------------------------------------------------------------ tail
def build_tail():
    md = MeshData()
    dirs, quads, _ = cube_sphere(4)
    back = ray(BODY_BVH, (0.0, 0.0, TAIL_Z), (0.0, 1.0, 0.0))
    c = back + Vector((0.0, TAIL_R * 0.45, 0.0))
    for p in dirs:
        n = noise.noise(p * 2.5 + Vector((3.1, 7.7, 1.3)))
        md.vert(c + p * TAIL_R * (1.0 + 0.10 * n))
    for q in quads:
        md.face(q, 0)
    md.set_uv(lambda i: sph_uv(dirs[i]))
    return md


# ------------------------------------------------------------------ face: eyes, catchlights, mouth, tongue, nose
def build_eye(side):
    """side +1 = Eye.L (+X), -1 = Eye.R. Glossy cap; planar UV: (0.5,0.5) = pupil, radius 0.5 = iris edge."""
    S, n = front_frame(side * EYE_X, EYE_Z)
    f, ex, ey = face_frame(n, 0.4)
    hc = EYE_H - EYE_RS
    beta_max = math.radians(50.0)
    md, local, rings = MeshData(), [], []
    nr = 6
    for i in range(nr):
        b = beta_max * (1.0 - i / nr)
        r, h = EYE_RS * math.sin(b), hc + EYE_RS * math.cos(b)
        ring = []
        for j in range(EYE_SEG):
            ps = math.pi / 2 + 2 * math.pi * j / EYE_SEG
            lx, ly = r * math.cos(ps), r * math.sin(ps) * EYE_VS
            ring.append(md.vert(S + ex * lx + ey * ly + f * h))
            local.append((lx, ly))
        rings.append(ring)
    apex = md.vert(S + f * EYE_H)
    local.append((0.0, 0.0))
    for a, b in zip(rings, rings[1:]):
        bridge(md, a, b, 0)
    fan_top(md, rings[-1], apex, 0)
    px, py = -side * PUPIL_IN, -PUPIL_DOWN
    md.set_uv(lambda i: (0.5 + (local[i][0] - px) / (2 * IRIS_R), 0.5 + (local[i][1] - py) / (2 * IRIS_R)),
              wrap=False)
    return md, dict(S=S, f=f, ex=ex, ey=ey, hc=hc, px=px, py=py, side=side)


def build_catchlight(eye, lx, ly, radius, seg, nrings):
    """White disc hugging the eye cap 2.5 mm above its surface, centred at eye-local (lx, ly)."""
    S, f, ex, ey, hc = eye["S"], eye["f"], eye["ex"], eye["ey"], eye["hc"]
    uy = ly / EYE_VS
    dz = math.sqrt(max(EYE_RS ** 2 - lx * lx - uy * uy, 1e-8))
    d0 = Vector((lx, uy, dz)).normalized()
    t1, t2, _ = frame_from(d0, Vector((0.0, 1.0, 0.0)))
    rr = EYE_RS + 0.0025
    gmax = radius / EYE_RS

    def to_world(lp):
        return S + ex * lp.x + ey * (lp.y * EYE_VS) + f * (lp.z + hc)

    md, uvs, rings = MeshData(), [], []
    for k in range(nrings, 0, -1):
        g = gmax * k / nrings
        ring = []
        for j in range(seg):
            ps = 2 * math.pi * j / seg
            ring.append(md.vert(to_world((d0 * math.cos(g) + (t1 * math.cos(ps) + t2 * math.sin(ps))
                                          * math.sin(g)) * rr)))
            uvs.append((0.5 + 0.5 * k / nrings * math.cos(ps), 0.5 + 0.5 * k / nrings * math.sin(ps)))
        rings.append(ring)
    centre = md.vert(to_world(d0 * rr))
    uvs.append((0.5, 0.5))
    for a, b in zip(rings, rings[1:]):
        bridge(md, a, b, 0)
    fan_top(md, rings[-1], centre, 0)
    md.set_uv(lambda i: uvs[i], wrap=False)
    return md


def mouth_outline(n, w, h):
    """D-shaped open smile with a small cat-lip notch at the top centre; CCW seen from the front."""
    n_top = n // 2
    pts = []
    for i in range(n_top):
        x = -w / 2 + w * i / n_top
        xn = x / (w / 2)
        pts.append((x, h / 2 - 0.010 * math.exp(-(x / 0.013) ** 2) + 0.004 * xn * xn))
    nb = n - n_top
    for i in range(nb):
        a = math.pi * i / nb
        pts.append(((w / 2) * math.cos(a), h / 2 + 0.004 - h * (math.sin(a) ** 0.85)))
    pts.reverse()
    return pts


def build_mouth():
    """Mouth = recessed dark smile (soft M_Fur lip ring rising out of the face) + tiny nose; Tongue separate."""
    S, n = front_frame(0.0, MOUTH_Z)
    f, ex, ey = face_frame(n, 0.3)
    outline = mouth_outline(MOUTH_N, MOUTH_W, MOUTH_H)
    ring_sh = [(1.22, -0.004), (1.09, 0.007), (1.0, 0.0115), (0.90, 0.0065), (0.64, 0.0035), (0.30, 0.003)]

    def place(x, y, h):
        return ray(BODY_BVH, S + ex * x + ey * y + f * 0.3, -f) + f * h

    md, loc, rings = MeshData(), [], []
    for s, h in ring_sh:
        ring = []
        for (x, y) in outline:
            ring.append(md.vert(place(x * s, y * s, h)))
            loc.append((x * s, y * s))
        rings.append(ring)
    centre = md.vert(place(0.0, 0.0, 0.003))
    loc.append((0.0, 0.0))
    for k, mat in enumerate((1, 1, 0, 0, 0)):          # 0 = M_Mouth, 1 = M_Fur (lip ring)
        bridge(md, rings[k], rings[k + 1], mat)
    fan_top(md, rings[-1], centre, 0)
    md.set_uv(lambda i: (0.5 + loc[i][0] / (1.3 * MOUTH_W), 0.5 + loc[i][1] / (1.3 * MOUTH_W)), wrap=False)
    tongue = ellipsoid(place(0.0, -MOUTH_H / 2 + 0.031, 0.0025), ex, ey, f, 0.035, 0.023, 0.0085,
                       seg=12, rings=6, mat=0)
    # tiny rounded inverted-triangle nose (M_Mouth), part of the Mouth object
    sn, nn = front_frame(0.0, NOSE_Z)
    fn, exn, eyn = face_frame(nn, 0.3)
    nose = ellipsoid(Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)),
                     Vector((0.0, 0.0, 1.0)), 0.017, 0.0105, 0.0075, seg=10, rings=5, mat=0)
    out = []
    for v in nose.v:
        x = v.x * (1.0 + 0.55 * (v.y / 0.0105)) if v.y < 0 else v.x
        out.append(sn + exn * x + eyn * v.y + fn * (v.z + 0.001))
    nose.v = out
    md.extend(nose)
    return md, tongue, S, sn


# ------------------------------------------------------------------ beanie, pom-pom, star badge
def build_beanie():
    """Crown (knit + lavender bands) + separate folded ribbed cuff band + tapered front stripe.
    Material indices: 0 M_HatKnit, 1 M_HatCuff, 2 M_HatStripe. UV: u around (seam at the back), v 0..1 up."""
    KNIT, CUFF, STRIPE = 0, 1, 2
    psi0 = math.pi / 2
    crown = MeshData()
    seg = 48
    rings = [[crown.vert(hat_point(a, psi0 + 2 * math.pi * j / seg, crown_off(a))) for j in range(seg)]
             for a in CROWN_RINGS]
    pole = crown.vert(hat_point(0.0, 0.0, crown_off(0.0)))
    for k in range(len(rings) - 1):
        a0, a1 = CROWN_RINGS[k], CROWN_RINGS[k + 1]
        mat = STRIPE if (a0 <= STRIPE_A[0] + 1e-6 and a1 >= STRIPE_A[1] - 1e-6) else KNIT
        bridge(crown, rings[k], rings[k + 1], mat, hat_v(a0), hat_v(a1))
    fan_top(crown, rings[-1], pole, KNIT, hat_v(CROWN_RINGS[-1]), 1.0)

    # extra lavender stripe high on the dome: full width over the front, tapering to nothing at the back
    strip = MeshData()
    cols = []
    K = 40
    for c in range(K + 1):
        phi = math.radians(TOP_STRIPE_END * (2.0 * c / K - 1.0))
        psi = phi - math.pi / 2
        w = TOP_STRIPE_HW * smoothstep(TOP_STRIPE_END, TOP_STRIPE_FULL, abs(math.degrees(phi)))
        u = 0.5 + phi / (2 * math.pi)
        alphas = (TOP_STRIPE_A,) if w < 1e-3 else (TOP_STRIPE_A + w, TOP_STRIPE_A - w)
        cols.append([(strip.vert(hat_point(a, psi, crown_off(a) + 0.003)), u, hat_v(a)) for a in alphas])
    for c in range(K):
        a_col, b_col = cols[c], cols[c + 1]
        items = [a_col[0], b_col[0], b_col[-1], a_col[-1]]
        uniq = []
        for it in items:
            if not uniq or uniq[-1][0] != it[0]:
                uniq.append(it)
        if len(uniq) > 1 and uniq[0][0] == uniq[-1][0]:
            uniq.pop()
        strip.face([it[0] for it in uniq], STRIPE, [(it[1], it[2]) for it in uniq])

    cuff = MeshData()
    seg2 = CUFF_SEG
    crings = []
    for (a, off, rw) in CUFF_PROFILE:
        crings.append([cuff.vert(hat_point(a, psi0 + 2 * math.pi * j / seg2,
                                           off + RIB_AMP * rw * (1.0 if j % 2 == 0 else -1.0)))
                       for j in range(seg2)])
    for k in range(len(crings) - 1):
        bridge(cuff, crings[k], crings[k + 1], CUFF, hat_v(CUFF_PROFILE[k][0]), hat_v(CUFF_PROFILE[k + 1][0]))
    beanie = MeshData().extend(crown).extend(strip).extend(cuff)
    return beanie, cuff


def build_pompom():
    md = MeshData()
    dirs, quads, _ = cube_sphere(9)
    top = hat_point(0.0, 0.0, crown_off(0.0))
    c = top + HAT_AXIS * (POMPOM_R * (1.0 - POMPOM_SINK))
    for p in dirs:
        n1 = noise.noise(p * 2.0 + Vector((11.3, 2.9, 5.1)))
        n2 = noise.noise(p * 5.5 + Vector((1.7, 8.2, 3.3)))
        n3 = noise.noise(p * 11.0 + Vector((4.4, 0.6, 9.9)))
        md.vert(c + p * POMPOM_R * (1.0 + 0.06 * n1 + 0.04 * n2 + 0.02 * n3))
    for q in quads:
        md.face(q, 0)
    md.set_uv(lambda i: sph_uv(dirs[i]))
    return md, c


def star_outline():
    """Classic 5-point star (tip up) with corners rounded by two Chaikin passes; CCW."""
    pts = []
    for k in range(10):
        th = math.pi / 2 + k * math.pi / 5
        r = STAR_RO if k % 2 == 0 else STAR_RI
        pts.append(Vector((r * math.cos(th), r * math.sin(th))))
    for _ in range(2):
        nxt = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            nxt += [p * 0.75 + q * 0.25, p * 0.25 + q * 0.75]
        pts = nxt
    return pts


def build_star():
    """Puffy yellow star conforming to the cuff on HIS LEFT front (+X side)."""
    psi_s = math.radians(STAR_PHI) - math.pi / 2
    off = CUFF_OFF

    def surf(a, ps):
        return hat_point(a, ps, off)

    p0 = surf(STAR_A, psi_s)
    rel = p0 - BODY_C
    r_hor = (rel - HAT_AXIS * rel.dot(HAT_AXIS)).length
    r_mer = rel.length
    rot = Matrix.Rotation(math.radians(STAR_ROT), 2)
    outline = star_outline()
    ring_sh = [(1.0, -0.006), (1.0, 0.004), (0.93, 0.011), (0.76, 0.017), (0.50, 0.0205)]
    md, uvs, rings = MeshData(), [], []

    def place(x, y, h):
        q = rot @ Vector((x, y))
        a = STAR_A - math.degrees(q.y / r_mer)
        ps = psi_s + q.x / r_hor
        d = 0.004
        t_psi = surf(a, ps + d) - surf(a, ps - d)
        t_up = surf(a - math.degrees(d), ps) - surf(a + math.degrees(d), ps)
        return surf(a, ps) + t_psi.cross(t_up).normalized() * h

    for s, h in ring_sh:
        ring = []
        for p in outline:
            ring.append(md.vert(place(p.x * s, p.y * s, h)))
            uvs.append((0.5 + p.x * s / (2 * STAR_RO), 0.5 + p.y * s / (2 * STAR_RO)))
        rings.append(ring)
    centre = md.vert(place(0.0, 0.0, 0.022))
    uvs.append((0.5, 0.5))
    for a, b in zip(rings, rings[1:]):
        bridge(md, a, b, 0)
    fan_top(md, rings[-1], centre, 0)
    md.set_uv(lambda i: uvs[i], wrap=False)
    return md


# ------------------------------------------------------------------ assembly, checks, export, previews
def min_gap(md_a, md_b):
    bvh = md_b.bvh()
    return min(bvh.find_nearest(v)[3] for v in md_a.v)


def main():
    global BODY_BVH
    C.reset_scene()
    M = build_materials()
    coll = bpy.data.collections.new("SK_Mascot_model")
    bpy.context.scene.collection.children.link(coll)

    body = build_body()
    BODY_BVH = body.bvh()
    eyes = {}
    for side, tag in ((1, "L"), (-1, "R")):
        eyes[tag] = build_eye(side)
    lights = {}
    for tag, (_md, info) in eyes.items():
        inner = -info["side"]                          # local x direction toward the nose
        px, py = info["px"], info["py"]
        lights[tag + "1"] = build_catchlight(info, px + inner * 0.010, py + 0.038, 0.020, 14, 2)
        lights[tag + "2"] = build_catchlight(info, px - inner * 0.026, py - 0.028, 0.0095, 10, 1)
    mouth, tongue, mouth_pt, nose_pt = build_mouth()
    blush_pts = [front_frame(s * BLUSH_X, BLUSH_Z)[0] for s in (1, -1)]
    paint_body(body, [eyes["L"][1]["S"], eyes["R"][1]["S"]], mouth_pt, nose_pt, blush_pts)
    arms = {"L": build_arm(1), "R": build_arm(-1)}
    feet = {"L": build_foot(1), "R": build_foot(-1)}
    tail = build_tail()
    beanie, cuff = build_beanie()
    pompom, pp_c = build_pompom()
    star = build_star()

    parts = [
        ("Body", body, [M["Fur"]]),
        ("Eye.L", eyes["L"][0], [M["EyeIris"]]),
        ("Eye.R", eyes["R"][0], [M["EyeIris"]]),
        ("Catchlight.L1", lights["L1"], [M["EyeHighlight"]]),
        ("Catchlight.L2", lights["L2"], [M["EyeHighlight"]]),
        ("Catchlight.R1", lights["R1"], [M["EyeHighlight"]]),
        ("Catchlight.R2", lights["R2"], [M["EyeHighlight"]]),
        ("Mouth", mouth, [M["Mouth"], M["Fur"]]),
        ("Tongue", tongue, [M["Tongue"]]),
        ("Arm.L", arms["L"], [M["Fur"], M["PawPad"]]),
        ("Arm.R", arms["R"], [M["Fur"], M["PawPad"]]),
        ("Foot.L", feet["L"], [M["Fur"], M["PawPad"]]),
        ("Foot.R", feet["R"], [M["Fur"], M["PawPad"]]),
        ("Tail", tail, [M["Fur"]]),
        ("Beanie", beanie, [M["HatKnit"], M["HatCuff"], M["HatStripe"]]),
        ("PomPom", pompom, [M["PomPom"]]),
        ("StarBadge", star, [M["StarBadge"]]),
    ]
    objs = []
    total = 0
    for name, md, mats in parts:
        o = md.to_object(name, mats, coll)
        C.apply_transforms(o)
        C.shade_smooth(o, 180.0)
        objs.append(o)
        n = C.tri_count(o)
        total += n
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        print("TRIS %s %d  bbox x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]" % (
            name, n, min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb),
            min(v.z for v in bb), max(v.z for v in bb)))
    print("TRIS SK_Mascot_model %d" % total)
    allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    print("CHECK overall x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]" % (
        min(v.x for v in allv), max(v.x for v in allv), min(v.y for v in allv), max(v.y for v in allv),
        min(v.z for v in allv), max(v.z for v in allv)))
    print("CHECK gap eye.L-cuff %.4f  eye.R-cuff %.4f" % (min_gap(eyes["L"][0], cuff), min_gap(eyes["R"][0], cuff)))
    print("CHECK gap arm.L-cuff %.4f  star-centre z %.3f  pompom centre %s" % (
        min_gap(arms["L"], cuff), sum(v.z for v in star.v) / len(star.v), tuple(round(c, 3) for c in pp_c)))
    for tag in ("L", "R"):
        info = eyes[tag][1]
        print("CHECK eye.%s centre %s forward %s" % (tag, tuple(round(c, 3) for c in info["S"]),
                                                     tuple(round(c, 3) for c in info["f"])))

    C.export_fbx(objs, C.model_path("Characters", "SK_Mascot_model"))
    C.save_work("mascot_model")
    print("SAVED", C.work_path("mascot_model"))

    render_view(C.preview_path("SK_Mascot_model_back"), (0.0, 2.4, 1.3), (0.0, 0.0, 0.5))
    render_view(C.preview_path("SK_Mascot_model_front"), (0.0, -2.6, 0.75), (0.0, 0.0, 0.6))
    render_view(C.preview_path("SK_Mascot_model_34"), (1.85, -1.95, 1.1), (0.0, 0.0, 0.6))
    print("MASCOT_MODEL_DONE")


def render_view(path, cam_loc, target, lens=50.0, res=(900, 900)):
    """Spec preview look (EEVEE, Standard, #2A1B4A) with the warm key / cool fill / pink rim placed relative
    to the camera, so the gameplay back view is not lit only by the pink rim of the fixed front rig."""
    scene = bpy.context.scene
    engine = C.setup_preview_scene()
    t, cam = Vector(target), Vector(cam_loc)
    fwd = t - cam
    fwd.z = 0.0
    fwd.normalize()
    right = fwd.cross(Vector((0.0, 0.0, 1.0))).normalized()
    up = Vector((0.0, 0.0, 1.0))
    tag = os.path.splitext(os.path.basename(path))[0]
    temp = [C._light("Key_" + tag, 'AREA', 600.0, "#FFE7C2", t - fwd * 3.0 + right * 2.5 + up * 3.0, t, 2.5),
            C._light("Fill_" + tag, 'AREA', 250.0, "#BFD8FF", t - fwd * 2.0 - right * 3.0 + up * 1.5, t, 3.0),
            C._light("Rim_" + tag, 'AREA', 500.0, "#FF8AD8", t + fwd * 3.5 + up * 2.5, t, 2.0)]
    cam_data = bpy.data.cameras.new("Cam_" + tag)          # unique camera per view (no stale view reuse)
    cam_data.lens = lens
    cam_obj = bpy.data.objects.new("Cam_" + tag, cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = cam
    cam_obj.rotation_euler = (t - cam).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam_obj
    temp.append(cam_obj)
    bpy.context.view_layer.update()
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", engine, path)
    for o in temp:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)


main()
