"""Bubble Wash Kingdom - hero mascot MODEL (no rig). Blender 5.3, headless, deterministic.

Run from the project root (normally through build_mascot_all.py, which also runs the rig):
  blender --background --factory-startup --python Tools/Blender/scripts/build_mascot_model.py

Outputs
  Tools/Blender/work/mascot_model.blend + mascot_model.json   hand-off to build_mascot_rig.py. The json lists every
                                                               landmark the rig needs (no duplicated constants).
  Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_model.fbx   static check export (no armature)
  Docs/AssetPreviews/SK_Mascot_model_back.png / _front.png / _34.png   (skipped with BWK_QUICK=1)

Design (owner brief + approved video, rear gameplay view first): a round pink plush ball that dominates, a SNUG
beanie about as wide as the body (tall deep-ribbed cuff ~35-40 %, pale stripe ~13 %, squat violet ribbed dome),
a pom-pom ~45 % of the hat width, big stubby raised arms with paw pads, stubby pink legs in a wide V-sit ending in
big cream-white paws (toes up, pointing forward) that peek out on both sides from behind, a soft tail puff.

Objects (identity transforms, origin = ground point under the body, collection "SK_Mascot_model"):
  Body, Eye.L, Eye.R, Catchlight.L1/.L2/.R1/.R2, Mouth (+tiny nose), Tongue, Arm.L, Arm.R, Leg.L, Leg.R (leg + paw),
  Tail, Beanie, PomPom, StarBadge
Axes: meters, Z up, he faces -Y, his right = -X, his left = +X. 1 BW = 0.85 m. The legs are modelled seated.
Colour attribute "Col" (byte, corner). Fur parts: rgb = tint (blush, darker bottom), alpha = coat selector read by
BWK/Fur (1 = pink coat, 0 = cream-white paw fur). M_PawPad parts: rgb = pad colour (white palm/sole, pink beans).
UV0 on fur parts: 1 UV unit = 2.64 m around (u) and 1.32 m along (v) on every part, so BWK/Fur strands have the
same size everywhere (the shader doubles u for square strands). Seams sit where the rear camera never looks.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import bwk_common as C  # noqa: E402

QUICK = os.environ.get("BWK_QUICK", "") == "1"

# ------------------------------------------------------------------ body (meters)
BODY_C = Vector((0.0, 0.0, 0.57))          # body centre
BODY_W, BODY_D, BODY_H = 0.85, 0.82, 1.00  # width (1 BW), depth, height: an upright plush egg, so the fluffy back
                                           # below the beanie is the dominant mass (reference: ~0.75 hat widths)
BODY_EGG = 0.15                            # >0: fuller toward the bottom
BODY_SEG = 16                              # quad sphere: 6*16*16 quads = 3072 tris
FUR_U, FUR_V = 2.64, 1.32                  # metres per fur UV unit (around, along)

# ------------------------------------------------------------------ beanie (surface of revolution about the hat axis)
# Hat frame: origin BODY_C, axis tilted HAT_TILT about X (negative = front edge up, crown leans back). Profile points
# are (u, r): u = height along the axis, r = radius toward his side (x); around the axis r is scaled by hat_ell(psi)
# so the hat follows the body's slightly oval cross-section. psi = 0 -> +X, +90 deg -> back (+Y), -90 deg -> front.
HAT_TILT = -5.0
HAT_LIFT = 0.045                           # every hat profile u is lifted this much (taller body, cuff clears it)
HAT_DEPTH = 0.94
CUFF_BOTTOM_A = 72.0                       # deg from the hat axis: line where the cuff tucks into the fur
CUFF_RIBS, CROWN_RIBS = 96, 72             # geometric knit ribs around (BWK/Character _StitchU must match)
CUFF_RIB_AMP, CROWN_RIB_AMP = 0.0075, 0.0045
CUFF_PROFILE = [  # (u, r, rib weight): roll under -> tall ribbed outer face -> top roll -> tucks inside
    (0.093, 0.428, 0.0), (0.089, 0.445, 0.1), (0.096, 0.459, 0.5), (0.113, 0.466, 0.9), (0.147, 0.469, 1.0),
    (0.193, 0.470, 1.0), (0.233, 0.468, 1.0), (0.262, 0.463, 0.9), (0.280, 0.454, 0.5), (0.289, 0.442, 0.2),
    (0.290, 0.431, 0.0), (0.282, 0.421, 0.0)]
STRIPE_U = (0.287, 0.370)                  # pale ribbed band right above the cuff (~9 % of the hat width)
DOME_U0, DOME_H, DOME_R, DOME_EXP = 0.370, 0.235, 0.436, 1.8    # round slouchy dome (superellipse exponent)
TOP_STRIPE_PHI, TOP_STRIPE_HW = 47.0, 5.5  # extra pale stripe on the dome front (deg of the dome angle), fades out
TOP_STRIPE_FULL, TOP_STRIPE_END = 45.0, 78.0    # ... over the front only (deg from the front): never seen from behind
STAR_U, STAR_PHI, STAR_ROT = 0.192, 33.0, -12.0  # star badge on the cuff, 33 deg toward HIS LEFT (+X)
STAR_RO, STAR_RI = 0.072, 0.032
POMPOM_R, POMPOM_LIFT = 0.232, 0.42        # pom-pom radius; centre this many radii above the dome top
POMPOM_SEG = 12

# ------------------------------------------------------------------ face (unchanged design)
EYE_X, EYE_Z = 0.155, 0.585                # eye centres on the front surface
EYE_H, EYE_RS, EYE_VS = 0.025, 0.12, 1.06  # protrusion, cap sphere radius, vertical stretch
EYE_SEG = 32
IRIS_R, PUPIL_IN, PUPIL_DOWN = 0.072, 0.014, 0.007   # UV radius 0.5 = IRIS_R; pupil toward the nose
MOUTH_Z, MOUTH_W, MOUTH_H, MOUTH_N = 0.455, 0.13, 0.105, 28
NOSE_Z = 0.528
BLUSH_X, BLUSH_Z, BLUSH_R = 0.235, 0.47, 0.058

# ------------------------------------------------------------------ arms: big stubby mitts, raised out to the sides
ARM_Z = 0.520                              # root height on the body side (just under the cuff)
ARM_UP, ARM_BACK = 42.0, 0.02              # rest direction: 30 deg above horizontal, slightly back
ARM_SEG = 20
ARM_PROFILE = [(-0.10, 0.068), (-0.05, 0.078), (0.0, 0.083), (0.06, 0.086), (0.12, 0.088), (0.18, 0.090),
               (0.225, 0.090), (0.258, 0.084), (0.283, 0.070), (0.300, 0.050), (0.311, 0.026), (0.315, 0.0)]
PALM_H, PALM_SIZE = 0.215, (0.050, 0.056, 0.012)      # palm pad (along arm, size across / along / thickness)
ARM_BEANS = [(-48.0, 0.275), (-16.0, 0.290), (16.0, 0.290), (48.0, 0.275)]   # (angle around from palm, h)
BEAN_SIZE = (0.0155, 0.0145, 0.0075)
PALM_FACING = Vector((0.0, 0.55, 0.85))    # palm/beans face up and a little back (seen by the rear camera)

# ------------------------------------------------------------------ legs (modelled seated): wide V-sit, toes up
HIP = Vector((0.21, -0.08, 0.200))         # hip joint inside the lower body (his left; mirrored for the right)
ANKLE = Vector((0.50, -0.20, 0.120))       # wide V-sit: the paws sit beside the low body and peek out from behind
LEG_SEG, LEG_R0, LEG_R1 = 18, 0.088, 0.072 # around, radius at hip / ankle
TOE_YAW, TOE_PITCH = 26.0, 58.0            # toes splay outward / point up (sole faces forward-down)
PAW_HALF = (0.112, 0.140, 0.070)           # half width (lateral), half length (heel->toe), half thickness
PAW_FWD = 0.062                            # paw centre ahead of the ankle along the toe direction
PAW_SEG = 7
SOLE_PADS = [(0.0, -0.042, 0.040, 0.044, 0.010),         # big pad (heel side): (lat, along, r_lat, r_along, h)
             (-0.056, 0.040, 0.018, 0.020, 0.008), (-0.020, 0.062, 0.018, 0.020, 0.008),
             (0.020, 0.062, 0.018, 0.020, 0.008), (0.056, 0.040, 0.018, 0.020, 0.008)]
TAIL_R, TAIL_Z, TAIL_OUT = 0.060, 0.25, 0.05   # tail puff radius, height, centre offset (radii) behind the surface

WHITE = (1.0, 1.0, 1.0, 1.0)
PAD_PINK = (0.97, 0.56, 0.68, 1.0)         # Col (sRGB) for pads / beans on M_PawPad
SOLE_WHITE = (1.0, 0.97, 0.98, 1.0)
PALM_COL = (1.0, 0.80, 0.86, 1.0)         # light pink palm pad on the raised arms (seen from behind)
BLUSH_COL = (1.0, 0.70, 0.72)              # Col tint (sRGB) at the blush centre

HAT_R = Matrix.Rotation(math.radians(HAT_TILT), 3, 'X')
HAT_R_INV = HAT_R.transposed()
HAT_AXIS = HAT_R @ Vector((0.0, 0.0, 1.0))
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


def sph_uv_frame(d, pole, zero_dir, radius):
    """Fur UV on a sphere-like part: u around `pole` (seam where d = -zero_dir), v from the -pole to the +pole,
    scaled by radius so that one UV unit is FUR_U (u) / FUR_V (v) metres like on the body."""
    d = Vector(d).normalized()
    pole = Vector(pole).normalized()
    z0 = Vector(zero_dir)
    z0 = (z0 - pole * z0.dot(pole)).normalized()
    side = pole.cross(z0)
    u = 0.5 + math.atan2(d.dot(side), d.dot(z0)) / (2.0 * math.pi)
    v = 1.0 - math.acos(max(-1.0, min(1.0, d.dot(pole)))) / math.pi
    return (u * uv_period(radius), v * radius * math.pi / FUR_V)


def uv_period(radius):
    """u span of one full turn around a part of this radius (the set_uv wrap period)."""
    return radius * 2.0 * math.pi / FUR_U


def frame_from(ez, up=Vector((0.0, 0.0, 1.0))):
    """Right-handed frame (ex, ey, ez) with ez given and ey as close to `up` as possible."""
    ez = Vector(ez).normalized()
    ex = Vector(up).cross(ez)
    if ex.length < 1e-6:
        ex = Vector((0.0, 1.0, 0.0)).cross(ez)
    ex.normalize()
    return ex, ez.cross(ex), ez


def vlist(v):
    return [round(float(c), 6) for c in v]


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

    def set_uv(self, fn, wrap=True, period=1.0):
        out = []
        for f in self.f:
            uvs = [list(fn(i)) for i in f]
            if wrap:
                us = [p[0] for p in uvs]
                if max(us) - min(us) > 0.5 * period:
                    for p in uvs:
                        if p[0] < 0.5 * period:
                            p[0] += period
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


def bridge(md, r0, r1, mat, v0=0.0, v1=0.0, u_scale=1.0):
    """Quads between ring r0 (lower along the profile) and r1; rings CCW about the profile axis -> outward."""
    n = len(r0)
    for j in range(n):
        k = (j + 1) % n
        md.face((r0[j], r0[k], r1[k], r1[j]), mat,
                [(u_scale * j / n, v0), (u_scale * (j + 1) / n, v0), (u_scale * (j + 1) / n, v1),
                 (u_scale * j / n, v1)])


def fan_top(md, ring, pole, mat, v0=0.0, v1=1.0, u_scale=1.0):
    n = len(ring)
    for j in range(n):
        k = (j + 1) % n
        md.face((ring[j], ring[k], pole), mat,
                [(u_scale * j / n, v0), (u_scale * (j + 1) / n, v0), (u_scale * (j + 0.5) / n, v1)])


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


def inside_body(p):
    """Positive = p is inside the body (depth below the surface along the ray from the centre)."""
    d = Vector(p) - BODY_C
    L = d.length
    hit = BODY_BVH.ray_cast(BODY_C, d / L)
    return -1.0 if hit[0] is None else hit[3] - L


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


def hat_ell(psi):
    return 1.0 / math.sqrt(math.cos(psi) ** 2 + (math.sin(psi) / HAT_DEPTH) ** 2)


def hat_pt(u, r, psi):
    """World point of hat-frame profile coordinates (u along the axis, r radial x-radius) at angle psi."""
    e = r * hat_ell(psi)
    return BODY_C + HAT_R @ Vector((e * math.cos(psi), e * math.sin(psi), u + HAT_LIFT))


def hat_alpha_of(p):
    """Angle (deg) of a world point from the hat axis, seen from the body centre."""
    d = HAT_R_INV @ (Vector(p) - BODY_C).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, d.z))))


def dome_ur(phi_deg):
    """Squat superellipse dome: phi 0 = rim (stripe top), 90 = top of the hat."""
    p = math.radians(phi_deg)
    e = 2.0 / DOME_EXP
    return DOME_U0 + DOME_H * (math.sin(p) ** e), DOME_R * (math.cos(p) ** e)


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
        "Fur": C.material("M_Fur", "#EE7898", roughness=0.85),
        "PomPom": C.material("M_PomPom", "#7A3CC8", roughness=0.9),
        "EyeIris": C.material("M_EyeIris", "#3A2236", roughness=0.08, coat=1.0),
        "EyeHighlight": C.material("M_EyeHighlight", "#FFFFFF", roughness=0.2, emission="#FFFFFF",
                                   emission_strength=1.5),
        "Mouth": C.material("M_Mouth", "#5A1A28", roughness=0.55),
        "Tongue": C.material("M_Tongue", "#F27C9A", roughness=0.4, coat=0.2),
        "PawPad": C.material("M_PawPad", "#FFFFFF", roughness=0.5),
        "HatKnit": C.material("M_HatKnit", "#7034C0", roughness=0.9),
        "HatCuff": C.material("M_HatCuff", "#6A2EB6", roughness=0.9),
        "HatStripe": C.material("M_HatStripe", "#EDE3FA", roughness=0.9),
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
    for key, ribs in (("HatKnit", 0.0), ("HatCuff", 0.0), ("HatStripe", 0.0)):
        nt = M[key].node_tree
        bsdf = nt.nodes["Principled BSDF"]
        _inp(bsdf, "Sheen Weight", 0.25)
        _inp(bsdf, "Sheen Tint", C.hex_rgba("#E8D8FF"))
        _noise_bump(nt, bsdf, 900.0, 0.25, 0.002)      # yarn fuzz (the ribs are geometry)
    nt = M["PomPom"].node_tree
    bsdf = nt.nodes["Principled BSDF"]
    _inp(bsdf, "Sheen Weight", 0.3)
    _inp(bsdf, "Sheen Tint", C.hex_rgba("#C9A0FF"))
    _noise_bump(nt, bsdf, 240.0, 0.9, 0.01)
    nt = M["EyeIris"].node_tree
    bsdf = nt.nodes["Principled BSDF"]
    _eye_shader(nt, bsdf)
    _inp(bsdf, "Coat Roughness", 0.03)
    return M


# ------------------------------------------------------------------ body
BODY_POLE, BODY_ZERO = Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0))   # poles at the arm roots, seam underneath


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
    md.set_uv(lambda i: sph_uv_frame(dirs[i], BODY_POLE, BODY_ZERO, 0.46), period=uv_period(0.46))
    return md


def paint_body(md, blush_pts):
    """Col.rgb = tint (white, rosy blush, slightly darker bottom); Col.a = 1 (pink coat)."""
    def col(i, _k):
        p = md.v[i]
        g = 1.0 - 0.16 * smoothstep(0.34, 0.06, p.z)
        rgb = [g, g, g]
        for bp in blush_pts:
            w = 0.95 * math.exp(-((p - bp).length / BLUSH_R) ** 2)
            rgb = [c * (1.0 - w) + b * w for c, b in zip(rgb, BLUSH_COL)]
        return (rgb[0], rgb[1], rgb[2], 1.0)
    md.set_col(col)


# ------------------------------------------------------------------ arms
def prof_r(profile, h):
    for (h0, r0), (h1, r1) in zip(profile, profile[1:]):
        if h0 <= h <= h1:
            return r0 + (r1 - r0) * (h - h0) / (h1 - h0)
    return profile[-1][1]


def arm_frame(side):
    root = ray(BODY_BVH, (0.0, 0.0, ARM_Z), (side, 0.0, 0.0))
    a = math.radians(ARM_UP)
    d = Vector((side * math.cos(a), ARM_BACK, math.sin(a))).normalized()
    pd = PALM_FACING - d * PALM_FACING.dot(d)
    return root, d, pd.normalized()


def build_arm(side):
    """side +1 = Arm.L (+X, his left), -1 = Arm.R. Fur mitt (rings along the arm, seam underneath) + white palm
    pad + 4 pink beans on the palm side (up/back: visible from the rear camera)."""
    root, d, pd = arm_frame(side)
    under = -pd                                  # seam on the side facing away from the camera
    ex = under
    ey = d.cross(ex).normalized()
    md = MeshData()
    rings, hs = [], []
    for h, r in ARM_PROFILE[:-1]:
        rings.append([md.vert(root + d * h + (ex * math.cos(2 * math.pi * j / ARM_SEG)
                                              + ey * math.sin(2 * math.pi * j / ARM_SEG)) * r)
                      for j in range(ARM_SEG)])
        hs.append(h)
    tip = md.vert(root + d * ARM_PROFILE[-1][0])
    ru = 2.0 * math.pi * 0.087 / FUR_U          # u span around the arm (same strand size as the body)
    vv = [h / FUR_V for h in hs] + [ARM_PROFILE[-1][0] / FUR_V]
    for k, (a, b) in enumerate(zip(rings, rings[1:])):
        bridge(md, a, b, 0, vv[k], vv[k + 1], ru)
    fan_top(md, rings[-1], tip, 0, vv[len(rings) - 1], vv[-1], ru)
    fur_faces = len(md.f)
    fur_verts = len(md.v)
    palm_c = root + d * PALM_H + pd * (prof_r(ARM_PROFILE, PALM_H) - 0.004)
    pex = d.cross(pd)
    md.extend(ellipsoid(palm_c, pex, d, pd, PALM_SIZE[0], PALM_SIZE[1], PALM_SIZE[2], seg=12, rings=5, mat=1,
                        col=PALM_COL))
    beans = []
    for ang, hb in ARM_BEANS:
        n = Matrix.Rotation(math.radians(ang), 3, d) @ pd
        c = root + d * hb + n * (prof_r(ARM_PROFILE, hb) - 0.001)
        bey = (d - n * d.dot(n)).normalized()
        md.extend(ellipsoid(c, bey.cross(n), bey, n, BEAN_SIZE[0], BEAN_SIZE[1], BEAN_SIZE[2], seg=8, rings=4,
                            mat=1, col=PAD_PINK))
        beans.append(c)
    md.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0) if md.m[k] == 0 else md.col[k][0])
    info = dict(root=vlist(root), dir=vlist(d), palm_dir=vlist(pd), palm_c=vlist(palm_c),
                beans=[vlist(b) for b in beans], length=ARM_PROFILE[-1][0], fur_verts=fur_verts,
                fur_faces=fur_faces)
    return md, info


# ------------------------------------------------------------------ legs + paws (seated V-sit)
def paw_frame(side):
    yaw, pitch = math.radians(TOE_YAW), math.radians(TOE_PITCH)
    th = Vector((side * math.sin(yaw), -math.cos(yaw), 0.0))           # horizontal toe direction
    lat = Vector((side * math.cos(yaw), math.sin(yaw), 0.0))           # outward lateral axis
    t = (th * math.cos(pitch) + Vector((0.0, 0.0, 1.0)) * math.sin(pitch)).normalized()   # heel -> toe
    s = (th * math.sin(pitch) - Vector((0.0, 0.0, 1.0)) * math.cos(pitch)).normalized()   # sole normal
    return t, lat, s


def paw_shape(p):
    """Unit cube-sphere point -> paw local (lat, along, up-from-sole): rounded bean, flatter sole, wider toes."""
    e = 0.86
    sx = math.copysign(abs(p.x) ** e, p.x)
    sy = math.copysign(abs(p.y) ** e, p.y)
    sz = math.copysign(abs(p.z) ** e, p.z) if p.z >= 0 else -(abs(p.z) ** 0.62)
    w = PAW_HALF[0] * (1.0 + 0.10 * p.y)                  # a little wider at the toes (+along)
    return Vector((sx * w, sy * PAW_HALF[1], sz * PAW_HALF[2]))


def build_leg(side):
    """Leg.<tag>: pink fur leg capsule hip -> ankle (seam inside) + cream-white fur paw (Col.a = 0) with a sole
    big pad + 4 toe beans (M_PawPad, pink). Paw local frame: x = lateral (out), y = heel->toe, z = up from sole."""
    hip = Vector((side * HIP.x, HIP.y, HIP.z))
    ank = Vector((side * ANKLE.x, ANKLE.y, ANKLE.z))
    t, lat, s = paw_frame(side)
    md = MeshData()
    axis = (ank - hip).normalized()
    L = (ank - hip).length
    ex = (Vector((0.0, 0.0, -1.0)) - axis * axis.z).normalized()     # seam underneath
    ey = axis.cross(ex).normalized()
    rings = []
    n_r = 7
    ru = 2.0 * math.pi * 0.08 / FUR_U
    hs = [-0.06 + (L + 0.08) * i / (n_r - 1) for i in range(n_r)]
    for h in hs:
        f = min(1.0, max(0.0, h / L))
        r = LEG_R0 + (LEG_R1 - LEG_R0) * f
        rings.append([md.vert(hip + axis * h + (ex * math.cos(2 * math.pi * j / LEG_SEG)
                                                + ey * math.sin(2 * math.pi * j / LEG_SEG)) * r)
                      for j in range(LEG_SEG)])
    for k in range(n_r - 1):
        bridge(md, rings[k], rings[k + 1], 0, hs[k] / FUR_V, hs[k + 1] / FUR_V, ru)
    leg_faces = len(md.f)
    leg_verts = len(md.v)
    # paw: rounded bean in its own frame, toes up, sole facing forward-down
    centre = ank + t * PAW_FWD - s * 0.006
    zf = -s                                     # paw local +z = away from the sole (dorsal)
    ax = t.cross(zf).normalized()               # right-handed (ax, t, zf) on both sides -> outward winding
    paw = MeshData()
    dirs, quads, _tags = cube_sphere(PAW_SEG)
    for p in dirs:
        q = paw_shape(p)
        paw.vert(centre + ax * q.x + t * q.y + zf * q.z)
    for qd in quads:
        paw.face(qd, 0)
    paw.set_uv(lambda i: sph_uv_frame(dirs[i], Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, -1.0)), 0.11),
               period=uv_period(0.11))
    paw.set_col(lambda i, k: (1.0, 1.0, 1.0, 0.0))
    paw_bvh = paw.bvh()
    md.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0))
    md.extend(paw)
    fur_faces = len(md.f)
    fur_verts = len(md.v)
    pads = []
    px = t.cross(s).normalized()                # right-handed (px, t, s): pads bulge out of the sole
    for (plat, palong, rl, ra, h) in SOLE_PADS:
        o = centre + px * plat + t * palong
        hit = paw_bvh.ray_cast(o, s)                                   # from inside out through the sole
        if hit[0] is None:
            raise RuntimeError("pad ray missed the paw")
        pc = hit[0] + s * (h * 0.15)
        big = rl > 0.03
        md.extend(ellipsoid(pc, px, t, s, rl, ra, h, seg=12 if big else 8, rings=5 if big else 4, mat=1,
                            col=PAD_PINK))
        pads.append(pc)
    toe = centre + t * PAW_HALF[1]
    heel = centre - t * PAW_HALF[1]
    info = dict(hip=vlist(hip), ankle=vlist(ank), toe=vlist(toe), heel=vlist(heel), paw_c=vlist(centre),
                toe_dir=vlist(t), lat=vlist(lat), sole_n=vlist(s), pads=[vlist(p) for p in pads],
                leg_faces=leg_faces, leg_verts=leg_verts, fur_faces=fur_faces, fur_verts=fur_verts)
    return md, info


# ------------------------------------------------------------------ tail
def build_tail():
    md = MeshData()
    dirs, quads, _ = cube_sphere(5)
    back = ray(BODY_BVH, (0.0, 0.0, TAIL_Z), (0.0, 1.0, 0.0))
    c = back + Vector((0.0, TAIL_R * TAIL_OUT, 0.0))
    for p in dirs:
        n = noise.noise(p * 2.5 + Vector((3.1, 7.7, 1.3)))
        md.vert(c + Vector((p.x, p.y * 0.92, p.z)) * TAIL_R * (1.0 + 0.06 * n))
    for q in quads:
        md.face(q, 0)
    md.set_uv(lambda i: sph_uv_frame(dirs[i], Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)), TAIL_R),
              period=uv_period(TAIL_R))
    md.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0))
    return md, dict(base=vlist(back), c=vlist(c), r=TAIL_R)


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
    md.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0))
    return md, tongue, S, sn


# ------------------------------------------------------------------ beanie, pom-pom, star badge
def profile_normal(pts, k):
    """Outward normal (dr, du) of a (u, r) profile at point k (direction rotated -90 deg in the (r, u) plane)."""
    a = pts[max(0, k - 1)]
    b = pts[min(len(pts) - 1, k + 1)]
    du, dr = b[0] - a[0], b[1] - a[1]
    n = Vector((du, -dr))                       # (r, u) components
    return n.normalized() if n.length > 1e-9 else Vector((1.0, 0.0))


def rib_ring(md, u, r, n_ru, psi0, segs, amp):
    """Ring of the hat surface with alternating rib offsets (crest at odd j, matching BWK/Character's knit)."""
    ring = []
    for j in range(segs):
        psi = psi0 + 2.0 * math.pi * j / segs
        o = amp * (1.0 if j % 2 == 1 else -1.0)
        ring.append(md.vert(hat_pt(u + n_ru.y * o, r + n_ru.x * o, psi)))
    return ring


def arc_v(pts):
    """Cumulative arc length along a (u, r) profile, normalised later by the caller."""
    out, acc = [0.0], 0.0
    for a, b in zip(pts, pts[1:]):
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        out.append(acc)
    return out


def build_beanie():
    """Crown (hidden collar + pale stripe band + squat ribbed dome) + separate folded ribbed cuff + extra pale stripe
    on the dome front. Material indices: 0 M_HatKnit, 1 M_HatCuff, 2 M_HatStripe.
    UV: u around (seam at the back, 0..1), v = arc length along the profile in metres (knit rows are even)."""
    KNIT, CUFF, STRIPE = 0, 1, 2
    psi0 = math.pi / 2                          # seam at the back
    # ---- crown profile (u, r, material of the band above this point)
    prof = [(0.240, 0.418, STRIPE), (0.272, 0.440, STRIPE), (STRIPE_U[0], 0.451, STRIPE), (0.313, 0.451, STRIPE),
            (0.343, 0.446, STRIPE), (STRIPE_U[1], DOME_R, KNIT)]
    for phi in (10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 69.0, 77.0, 84.0):
        u, r = dome_ur(phi)
        prof.append((u, r, KNIT))
    top_u = DOME_U0 + DOME_H + HAT_LIFT
    pts = [(p[0], p[1]) for p in prof]
    arcs = arc_v(pts + [(top_u, 0.0)])
    crown = MeshData()
    rings = []
    for k, (u, r, _m) in enumerate(prof):
        amp = CROWN_RIB_AMP * min(1.0, r / 0.25) * (0.0 if k == 0 else 1.0)
        rings.append(rib_ring(crown, u, r, profile_normal(pts, k), psi0, 2 * CROWN_RIBS, amp))
    pole = crown.vert(BODY_C + HAT_AXIS * top_u)
    for k in range(len(rings) - 1):
        bridge(crown, rings[k], rings[k + 1], prof[k][2], arcs[k], arcs[k + 1])
    fan_top(crown, rings[-1], pole, KNIT, arcs[len(rings) - 1], arcs[-1])

    # ---- extra pale stripe high on the dome: full width over the front, tapering to nothing at the back
    strip = MeshData()
    cols = []
    K = 48
    for c in range(K + 1):
        phi_f = math.radians(TOP_STRIPE_END * (2.0 * c / K - 1.0))     # angle from the front centre
        psi = phi_f - math.pi / 2
        w = TOP_STRIPE_HW * smoothstep(TOP_STRIPE_END, TOP_STRIPE_FULL, abs(math.degrees(phi_f)))
        u_uv = (psi - psi0) / (2.0 * math.pi) % 1.0
        angs = (TOP_STRIPE_PHI,) if w < 1e-3 else (TOP_STRIPE_PHI - w, TOP_STRIPE_PHI + w)
        col = []
        for a in angs:
            u, r = dome_ur(a)
            n = profile_normal([dome_ur(a - 1.0), (u, r), dome_ur(a + 1.0)], 1)
            col.append((strip.vert(hat_pt(u + n.y * 0.0045, r + n.x * 0.0045, psi)), u_uv, a / 90.0 * 0.15))
        cols.append(col)
    for c in range(K):
        a_col, b_col = cols[c], cols[c + 1]
        items = [a_col[0], b_col[0], b_col[-1], a_col[-1]]
        uniq = []
        for it in items:
            if not uniq or uniq[-1][0] != it[0]:
                uniq.append(it)
        if len(uniq) > 1 and uniq[0][0] == uniq[-1][0]:
            uniq.pop()
        if len(uniq) >= 3:
            strip.face([it[0] for it in uniq], STRIPE, [(it[1], it[2]) for it in uniq])

    # ---- folded cuff: tucks into the fur at CUFF_BOTTOM_A, rolls out into a tall deep-ribbed band
    cuff = MeshData()
    segs = 2 * CUFF_RIBS
    cpts = [(p[0], p[1]) for p in CUFF_PROFILE]
    carcs = arc_v(cpts)
    crings = []
    tuck = []
    for j in range(segs):                      # tuck ring exactly on the body (2 mm out)
        psi = psi0 + 2.0 * math.pi * j / segs
        d = hat_dir(CUFF_BOTTOM_A, psi)
        tuck.append(cuff.vert(BODY_C + d * (body_dist(d) + 0.002)))
    crings.append(tuck)
    for k, (u, r, rw) in enumerate(CUFF_PROFILE):
        crings.append(rib_ring(cuff, u, r, profile_normal(cpts, k), psi0, segs, CUFF_RIB_AMP * rw))
    vv = [-0.01] + carcs
    for k in range(len(crings) - 1):
        bridge(cuff, crings[k], crings[k + 1], CUFF, vv[k], vv[k + 1])
    beanie = MeshData().extend(crown).extend(strip).extend(cuff)
    beanie.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0))
    return beanie, cuff, top_u


def build_pompom(top_u):
    md = MeshData()
    dirs, quads, _ = cube_sphere(POMPOM_SEG)
    c = BODY_C + HAT_AXIS * (top_u + POMPOM_R * POMPOM_LIFT)
    for p in dirs:
        n1 = noise.noise(p * 2.0 + Vector((11.3, 2.9, 5.1)))
        n2 = noise.noise(p * 5.5 + Vector((1.7, 8.2, 3.3)))
        md.vert(c + p * POMPOM_R * (1.0 + 0.035 * n1 + 0.02 * n2))
    for q in quads:
        md.face(q, 0)
    md.set_uv(lambda i: sph_uv_frame(dirs[i], Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)), POMPOM_R),
              period=uv_period(POMPOM_R))
    md.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0))
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


def cuff_outer_r(u):
    """Outer cuff radius (x) at height u: interpolated on the ribbed outer face of CUFF_PROFILE."""
    face = [(p[0], p[1]) for p in CUFF_PROFILE[2:9]]
    for (u0, r0), (u1, r1) in zip(face, face[1:]):
        if u0 <= u <= u1:
            return r0 + (r1 - r0) * (u - u0) / (u1 - u0)
    return face[-1][1] if u > face[-1][0] else face[0][1]


def build_star():
    """Puffy yellow star conforming to the cuff on HIS LEFT front (+X side)."""
    psi_s = math.radians(STAR_PHI) - math.pi / 2

    def surf(u, ps):
        return hat_pt(u, cuff_outer_r(u) + CUFF_RIB_AMP + 0.002, ps)

    r_hor = cuff_outer_r(STAR_U) * hat_ell(psi_s)
    rot = Matrix.Rotation(math.radians(STAR_ROT), 2)
    outline = star_outline()
    ring_sh = [(1.0, -0.006), (1.0, 0.004), (0.93, 0.011), (0.76, 0.017), (0.50, 0.0205)]
    md, uvs, rings = MeshData(), [], []

    def place(x, y, h):
        q = rot @ Vector((x, y))
        u = STAR_U + q.y
        ps = psi_s + q.x / r_hor
        d = 0.004
        t_psi = surf(u, ps + d) - surf(u, ps - d)
        t_up = surf(u + d, ps) - surf(u - d, ps)
        return surf(u, ps) + t_psi.cross(t_up).normalized() * h

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
    md.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0))
    return md


# ------------------------------------------------------------------ assembly, checks, export, previews
def min_gap(md_a, md_b):
    bvh = md_b.bvh()
    return min(bvh.find_nearest(v)[3] for v in md_a.v)


def inward_fraction(md):
    """Fraction of faces whose normal points toward the part centre (sanity check for closed blobs)."""
    c = sum(md.v, Vector()) / len(md.v)
    bad = 0
    for f in md.f:
        a, b, d = md.v[f[0]], md.v[f[1]], md.v[f[2]]
        n = (b - a).cross(d - a)
        fc = sum((md.v[i] for i in f), Vector()) / len(f)
        if n.dot(fc - c) < 0:
            bad += 1
    return bad / max(1, len(md.f))


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
    paint_body(body, blush_pts)
    arms, arm_info = {}, {}
    legs, leg_info = {}, {}
    for side, tag in ((1, "L"), (-1, "R")):
        arms[tag], arm_info[tag] = build_arm(side)
        legs[tag], leg_info[tag] = build_leg(side)
    tail, tail_info = build_tail()
    beanie, cuff, top_u = build_beanie()
    pompom, pp_c = build_pompom(top_u)
    star = build_star()
    for md in (eyes["L"][0], eyes["R"][0], tongue, *lights.values()):
        md.set_col(lambda i, k: (1.0, 1.0, 1.0, 1.0))

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
        ("Leg.L", legs["L"], [M["Fur"], M["PawPad"]]),
        ("Leg.R", legs["R"], [M["Fur"], M["PawPad"]]),
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
    print("CHECK gap arm.L-cuff %.4f  pompom centre %s  hat top u %.3f  hat top z %.3f" % (
        min_gap(arms["L"], cuff), tuple(round(c, 3) for c in pp_c), top_u, (BODY_C + HAT_AXIS * top_u).z))
    for tag in ("L", "R"):
        li = leg_info[tag]
        print("CHECK leg.%s paw centre %s toe %s heel %s" % (tag, li["paw_c"], li["toe"], li["heel"]))
    cuff_in = max(inside_body(v) for v in cuff.v[2 * CUFF_RIBS:])
    print("CHECK cuff outer rings max depth inside body %.4f (must be < 0)" % cuff_in)
    for nm, md in (("Body", body), ("Tail", tail), ("PomPom", pompom)):
        print("CHECK normals %s inward fraction %.3f" % (nm, inward_fraction(md)))
    for tag in ("L", "R"):
        info = eyes[tag][1]
        print("CHECK eye.%s centre %s forward %s" % (tag, tuple(round(c, 3) for c in info["S"]),
                                                     tuple(round(c, 3) for c in info["f"])))

    # hand-off contract for build_mascot_rig.py
    bottom = min(v.z for v in body.v)
    contract = dict(
        BODY_C=vlist(BODY_C), BODY_BOTTOM=[0.0, 0.0, round(bottom, 6)], BODY_HALF=[BODY_W / 2, BODY_D / 2, BODY_H / 2],
        HAT_TILT=HAT_TILT, HAT_AXIS=vlist(HAT_AXIS), CUFF_BOTTOM_A=CUFF_BOTTOM_A,
        hat=dict(top_u=top_u, cuff_top_u=CUFF_PROFILE[9][0] + HAT_LIFT, stripe_u=[u + HAT_LIFT for u in STRIPE_U],
                 dome_u0=DOME_U0 + HAT_LIFT,
                 pompom_c=vlist(pp_c), pompom_r=POMPOM_R),
        arms=arm_info, legs=leg_info, tail=tail_info,
        eyes={t: dict(S=vlist(eyes[t][1]["S"]), f=vlist(eyes[t][1]["f"])) for t in ("L", "R")},
        mouth_c=vlist(mouth_pt), nose_c=vlist(nose_pt),
        star_c=vlist(sum(star.v, Vector()) / len(star.v)),
        counts={n: len(md.v) for n, md, _m in parts})
    os.makedirs(C.WORK, exist_ok=True)
    with open(os.path.join(C.WORK, "mascot_model.json"), "w") as fh:
        json.dump(contract, fh, indent=1)
    print("SAVED", os.path.join(C.WORK, "mascot_model.json"))

    C.export_fbx(objs, C.model_path("Characters", "SK_Mascot_model"))
    C.save_work("mascot_model")
    print("SAVED", C.work_path("mascot_model"))

    if not QUICK:
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
