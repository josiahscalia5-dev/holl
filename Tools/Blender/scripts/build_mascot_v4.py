"""Bubble Wash Kingdom - EXPERIMENTAL hero mascot v4 (owner round 4: new construction method, v3 kept intact).
Blender 5.3, headless, deterministic.

  bash Tools/blender_run.sh Tools/Blender/scripts/build_mascot_v4.py <logname>        (model + renders + READY.json)
  BWK_V4_QUICK=1  fewer fur strands / samples (fast iteration)
  BWK_V4_VIEWS=front,rear,...  subset of views to render (default all)

Why a new construction (v3 = cube-sphere ball + separate tube arms + lathe hat with 44 bold rib tubes kept missing
the approved Google Flow mascot after 3 rounds):
  * body + head + arms = ONE metaball (SDF-style field) union, polygonised: one soft pear-shaped mass with no neck,
    arms growing out of the upper sides with natural fillets. Legs + feet = a second metaball union per side,
    pressed against the seat (distinct white paws, soles toward the rear camera in the W-sit).
  * beanie = lathe profile fitted to the head (folded ribbed cuff ~ body width, pale stripe, round crown dome, extra
    pale band on the front of the crown), 60 shallow geometric ribs + a generated knit V-stitch tile (bump + albedo).
  * fur = Blender HAIR CURVES grown from the body surface (clumps, length noise, combing, paler underside, blush,
    short cream paw fur), pom-pom = radial hair-curve yarn around a dark core.
  * face at the reference proportions: big glossy dark-brown eyes tucked under the cuff (diameter ~0.2 body width),
    catchlights, outer lashes, tiny nose, wide open cat-lip smile with a pink tongue, cheek blush.

Outputs (never touches v3: build_mascot_model.py / build_mascot_rig.py / SK_Mascot*.fbx / mascot_model.blend):
  Tools/Blender/work/mascot_v4/mascot_v4.blend, mascot_v4_landmarks.json, READY.json, knit_tile.png
  Docs/AssetPreviews/SK_Mascot_v4_<view>.png   our renders only (front, threequarter, side, rear, face, hero)
  Captures/agents/character/ref/*.png          PRIVATE reference crops for the comparison sheets (never tracked)
Axes: meters, Z up, he faces -Y, his left = +X. Origin = ground point under the body.
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402

import bwk_common as C  # noqa: E402

QUICK = os.environ.get("BWK_V4_QUICK", "") == "1"
VIEWS = [v for v in os.environ.get("BWK_V4_VIEWS", "").split(",") if v]
OUT = os.path.join(C.WORK, "mascot_v4")
PRIVATE = os.path.join(C.ROOT, "Captures", "agents", "character")
REF = os.path.join(C.ROOT, "Reference")
COLL_NAME = "SK_Mascot_v4"

# ------------------------------------------------------------------ body: metaball union (meters)
# Element field (Blender mball): s * (1 - q^2 / R^2)^3, surface at sum = threshold. With R = 1 / k(s) a lone element's
# surface is exactly its semi-axes; overlapping elements add up (soft union / fillets).
MB_T = 0.6
MB_RES = 0.016


def mb_k(s):
    return math.sqrt(1.0 - (MB_T / s) ** (1.0 / 3.0))


BODY_ELEMS = [  # (centre, semi-axes x/y/z, stiffness): lower belly + upper head -> one soft pear, no neck
    ((0.0, 0.015, 0.415), (0.458, 0.448, 0.415), 5.0),
    ((0.0, -0.005, 0.750), (0.442, 0.425, 0.345), 5.0),
]
# arm = upper arm leaving the body side just under the cuff almost level (clears the cuff bottom roll), then a forearm
# rising ~60 deg outside the cuff radius, ending in a mitt at cuff height (rear hero: paws outside the hat silhouette)
ARM_A, ARM_E, ARM_B, ARM_RAD, ARM_S = (Vector((0.30, -0.005, 0.450)), Vector((0.530, -0.020, 0.560)),
                                       Vector((0.648, -0.030, 0.648)), 0.094, 5.0)
MITT_C, MITT_AX, MITT_S = Vector((0.702, -0.040, 0.708)), (0.112, 0.090, 0.118), 5.0   # along, palm-normal, across
PALM_N = Vector((-0.10, -0.80, 0.45)).normalized()     # palm faces front / up (pads visible from the front)
HIP, ANKLE, LEG_RAD = Vector((0.205, 0.080, 0.200)), Vector((0.285, 0.245, 0.165)), 0.078
PAW_C = Vector((0.318, 0.312, 0.178))
PAW_AX = (0.136, 0.166, 0.082)                          # lateral, heel->toe, thickness
TOE_DIR = Vector((0.22, -0.42, 0.88)).normalized()      # toes up (+ a little forward / out)
SOLE_N0 = Vector((0.18, 0.90, 0.40))                    # soles face back / up toward the rear camera
# FRONT pose (opening / celebration shots, reference 03 / 05): legs forward, soles toward the front camera.
# Built as a second leg set "LegFront.*" (hidden in gameplay renders); the gameplay W-sit set is "Leg.*".
FRONT_LEG = dict(hip=Vector((0.200, -0.150, 0.200)), ankle=Vector((0.270, -0.360, 0.150)),
                 paw_c=Vector((0.300, -0.455, 0.175)), toe=Vector((0.20, 0.30, 0.93)),
                 sole=Vector((0.16, -0.93, 0.33)))
TAIL_C, TAIL_R = Vector((0.0, 0.37, 0.22)), 0.030       # tiny tuft hidden in the fur (rig needs a tail)

# ------------------------------------------------------------------ beanie (lathe about the tilted hat axis)
HAT_O = Vector((0.0, 0.0, 0.700))      # cuff-bottom centre on the axis
HAT_TILT = -6.0                        # deg about X (negative: front edge up, crown leans back)
RIB_N = 58                             # knit ribs around (UV u * 44 = rib index, see knit_uv)
CUFF_AMP, CROWN_AMP = 0.0080, 0.0085   # shallow geometric ribs (the knit tile does the stitches)
ROW_H = 0.024                          # knit row height (m) along the profile
# (h above the cuff bottom, radius, material) material 0 knit crown, 1 cuff, 2 stripe; first point = tuck (set later)
CUFF_PROF = [(h * 0.86, r * 0.935) for h, r in (
    (0.000, 0.500), (0.010, 0.518), (0.032, 0.528), (0.075, 0.532), (0.125, 0.533), (0.172, 0.530),
    (0.205, 0.523), (0.226, 0.511), (0.238, 0.494), (0.236, 0.478))]
STRIPE_PROF = [(0.196, 0.432), (0.212, 0.452), (0.240, 0.460), (0.268, 0.458), (0.286, 0.451)]
DOME_H0, DOME_R0, DOME_H, DOME_E = 0.286, 0.451, 0.228, 2.00
TOP_BAND = (9.0, 9.0)                  # (disabled: the reference has ONE pale stripe)              # extra pale band on the crown FRONT (h range), fades out toward the sides
TOP_BAND_PSI = 70.0                    # +- deg from the front where the band is full width
POM_H, POM_CORE, POM_R = 0.586, 0.150, 0.258   # pom-pom centre (h), dark core radius, yarn tip radius
STAR_H, STAR_PSI, STAR_ROT, STAR_RO, STAR_RI = 0.246, 30.0, -12.0, 0.100, 0.045

# ------------------------------------------------------------------ face (placed on the body surface)
EYE_DX, EYE_R, EYE_PROT = 0.214, 0.116, 0.036           # eye centre x, footprint radius, protrusion
EYE_UNDER = 0.088                      # eye centre this far below the cuff bottom (top tucks under the cuff edge)
IRIS_R, PUPIL_IN, PUPIL_DOWN = 0.107, 0.010, -0.006
NOSE_DZ, MOUTH_TOP_DZ, MOUTH_W, MOUTH_H = 0.068, 0.118, 0.186, 0.124
BLUSH_DX, BLUSH_DZ, BLUSH_R = 0.300, 0.125, 0.085

# ------------------------------------------------------------------ fur (hair curves)
FUR_N = 50000 if QUICK else 150000
FUR_LEN = 0.048
FUR_PTS = 5
FUR_RAD = (0.0024, 0.0005)
CLUMPS = 900 if QUICK else 2000
POM_N = 9000 if QUICK else 24000

COL_FUR = "#DC6A96"           # warm pink coat
COL_FUR_UNDER = "#EEC2DA"     # paler pink-white underside
COL_BLUSH = "#F04C6E"
COL_PAW = "#FFF6F4"
COL_PAD = "#F48FAA"
COL_HAT = "#5D2094"
COL_HAT_DARK = "#2C0B58"
COL_HAT_CROWN = "#4F1A84"
COL_STRIPE = "#D6A2CA"
COL_STRIPE_DARK = "#9A6A9A"
COL_POM = "#7B2FB2"


def hat_rot():
    return Matrix.Rotation(math.radians(HAT_TILT), 3, 'X')


HAT_R = hat_rot()
HAT_AXIS = HAT_R @ Vector((0.0, 0.0, 1.0))


def hat_pt(h, r, psi):
    """psi: 0 = +X (his left), -90 deg = front (-Y), +90 deg = back."""
    return HAT_O + HAT_R @ Vector((r * math.cos(psi), r * math.sin(psi), h))


def hat_local(p):
    q = HAT_R.transposed() @ (Vector(p) - HAT_O)
    return q.z, math.hypot(q.x, q.y), math.atan2(q.y, q.x)


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def np_smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def hexlin(h):
    return np.array(C.hex_rgba(h)[:3], dtype=np.float64)


def frame_z(ez, up=Vector((0.0, 0.0, 1.0))):
    ez = Vector(ez).normalized()
    ex = Vector(up).cross(ez)
    if ex.length < 1e-6:
        ex = Vector((0.0, 1.0, 0.0)).cross(ez)
    ex.normalize()
    return ex, ez.cross(ex), ez


def basis_quat(ex, ey, ez):
    m = Matrix((ex, ey, ez)).transposed()
    return m.to_quaternion()


# ------------------------------------------------------------------ mesh helpers
class MD:
    """Mesh accumulator: verts, faces, material index per face, per-corner UV + colour."""

    def __init__(self):
        self.v, self.f, self.m, self.uv, self.col = [], [], [], [], []

    def vert(self, co):
        self.v.append(Vector(co))
        return len(self.v) - 1

    def face(self, idx, mat=0, uv=None, col=None):
        self.f.append(tuple(idx))
        self.m.append(mat)
        self.uv.append(list(uv) if uv else [(0.0, 0.0)] * len(idx))
        self.col.append(list(col) if col else [(1.0, 1.0, 1.0, 1.0)] * len(idx))

    def extend(self, o):
        off = len(self.v)
        self.v += [v.copy() for v in o.v]
        for f, m, uv, col in zip(o.f, o.m, o.uv, o.col):
            self.f.append(tuple(i + off for i in f))
            self.m.append(m)
            self.uv.append(list(uv))
            self.col.append(list(col))
        return self

    def to_object(self, name, mats, coll):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        for m in mats:
            me.materials.append(m)
        try:
            me.polygons.foreach_set("material_index", self.m)
        except Exception:
            a = me.attributes.get("material_index") or me.attributes.new("material_index", 'INT', 'FACE')
            a.data.foreach_set("value", self.m)
        uvl = me.uv_layers.new(name="UVMap")
        cl = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
        uvs = [c for f in self.uv for p in f for c in p]
        uvl.data.foreach_set("uv", uvs)
        cols = []
        for f in self.col:
            for c in f:
                cols += [C.srgb_to_linear(c[0]), C.srgb_to_linear(c[1]), C.srgb_to_linear(c[2]), c[3]]
        cl.data.foreach_set("color", cols)
        me.update()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        for p in me.polygons:
            p.use_smooth = True
        return ob


def bridge(md, r0, r1, mat):
    n = len(r0)
    for j in range(n):
        k = (j + 1) % n
        md.face((r0[j], r0[k], r1[k], r1[j]), mat)


def ellipsoid(c, ex, ey, ez, rx, ry, rz, seg=12, rings=7, mat=0, col=(1.0, 1.0, 1.0, 1.0)):
    md = MD()
    c = Vector(c)
    bot = md.vert(c - ez * rz)
    rs = []
    for i in range(1, rings):
        th = math.pi * (1.0 - i / rings)
        rs.append([md.vert(c + ex * (rx * math.sin(th) * math.cos(2 * math.pi * j / seg))
                           + ey * (ry * math.sin(th) * math.sin(2 * math.pi * j / seg)) + ez * (rz * math.cos(th)))
                   for j in range(seg)])
    top = md.vert(c + ez * rz)
    for j in range(seg):
        k = (j + 1) % seg
        md.face((bot, rs[0][k], rs[0][j]), mat, col=[col] * 3)
    for a, b in zip(rs, rs[1:]):
        for j in range(seg):
            k = (j + 1) % seg
            md.face((a[j], a[k], b[k], b[j]), mat, col=[col] * 4)
    for j in range(seg):
        k = (j + 1) % seg
        md.face((rs[-1][j], rs[-1][k], top), mat, col=[col] * 3)
    return md


# ------------------------------------------------------------------ materials
def _inp(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def principled(name, hex_col, rough=0.6, coat=0.0, sheen=0.0, sheen_hex="#FFFFFF", spec=0.5, emit=None, emit_s=0.0):
    m = C.material(name, hex_col, roughness=rough, coat=coat, emission=emit, emission_strength=emit_s)
    b = m.node_tree.nodes["Principled BSDF"]
    _inp(b, "Sheen Weight", sheen)
    _inp(b, "Sheen Tint", C.hex_rgba(sheen_hex))
    _inp(b, "Specular IOR Level", spec)
    return m, b


def knit_tile(path, n=128):
    """Knit V-stitch height tile: x across one rib column, y along one row (y up). Saved + packed."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float64) / n
    h = np.zeros((n, n))
    for s in (-1.0, 1.0):
        xc = 0.5 + s * (0.05 + 0.30 * y)
        d = (x - xc) / 0.150
        leg = np.clip(1.0 - d * d, 0.0, 1.0) ** 0.8
        env = np.sin(np.pi * np.clip(y * 0.90 + 0.05, 0.0, 1.0)) ** 0.45
        h = np.maximum(h, leg * env)
    edge = np.clip(np.abs(x - 0.5) * 2.0, 0.0, 1.0)
    col = np.cos(np.pi * (x - 0.5)) ** 0.8                 # rounded rib column
    h = 0.74 * col + 0.26 * h * (1.0 - 0.45 * edge ** 8)
    rng = np.random.default_rng(7)
    h = np.clip(h + rng.normal(0.0, 0.025, h.shape), 0.0, 1.0)
    img = bpy.data.images.new("V4_KnitTile", n, n, alpha=False, float_buffer=False)
    px = np.ones((n, n, 4), dtype=np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = h
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    img.pack()
    try:
        img.colorspace_settings.name = 'Non-Color'
    except Exception:
        pass
    return img


def knit_material(name, hex_col, hex_dark, tile, bump=0.35):
    m, b = principled(name, hex_col, rough=0.92, sheen=0.55, sheen_hex="#E8D8FF", spec=0.25)
    nt = m.node_tree
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    mu = nt.nodes.new("ShaderNodeMath")
    mu.operation = 'MULTIPLY'
    mu.inputs[1].default_value = 44.0
    nt.links.new(sep.outputs[0], mu.inputs[0])
    mv = nt.nodes.new("ShaderNodeMath")
    mv.operation = 'MULTIPLY'
    mv.inputs[1].default_value = 1.0 / ROW_H
    nt.links.new(sep.outputs[1], mv.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(mu.outputs[0], comb.inputs[0])
    nt.links.new(mv.outputs[0], comb.inputs[1])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = tile
    tex.interpolation = 'Linear'
    tex.extension = 'REPEAT'
    nt.links.new(comb.outputs[0], tex.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    for s in mix.inputs:
        if s.identifier == "A_Color":
            s.default_value = C.hex_rgba(hex_dark)
        elif s.identifier == "B_Color":
            s.default_value = C.hex_rgba(hex_col)
    fac = nt.nodes.new("ShaderNodeMapRange")
    fac.inputs["To Min"].default_value = 0.42
    fac.inputs["To Max"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], fac.inputs["Value"])
    nt.links.new(fac.outputs["Result"], [s for s in mix.inputs if s.identifier == "Factor_Float"][0])
    nt.links.new([s for s in mix.outputs if s.identifier == "Result_Color"][0], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    _inp(bp, "Distance", 0.006)
    nt.links.new(tex.outputs["Color"], bp.inputs["Height"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 700.0
    _inp(nz, "Detail", 4.0)
    bp2 = nt.nodes.new("ShaderNodeBump")
    bp2.inputs["Strength"].default_value = 0.25
    _inp(bp2, "Distance", 0.001)
    nt.links.new(nz.outputs["Fac"], bp2.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bp2.inputs["Normal"])
    nt.links.new(bp2.outputs["Normal"], b.inputs["Normal"])
    return m


def eye_material():
    m, b = principled("M_EyeIris", "#2A1418", rough=0.08, coat=1.0, spec=0.6)
    _inp(b, "Coat Roughness", 0.02)
    nt = m.node_tree
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
    cr.elements[0].color = C.hex_rgba("#0B0507")
    cr.elements[1].position = 1.0
    cr.elements[1].color = C.hex_rgba("#F7F0F2")
    for pos, hx in ((0.19, "#0E0608"), (0.235, "#2C171C"), (0.33, "#43272D"), (0.42, "#5F4048"),
                    (0.468, "#24121A"), (0.50, "#1A0C10"), (0.525, "#F2E8EC")):
        e = cr.elements.new(pos)
        e.color = C.hex_rgba(hx)
    nt.links.new(ln.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def fur_strand_material(name, root_mul, tip_mul, rough=0.55):
    m, b = principled(name, "#FFFFFF", rough=rough, sheen=0.4, sheen_hex="#FFD0E0", spec=0.35)
    nt = m.node_tree
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_type = 'GEOMETRY'
    at.attribute_name = "fur_col"
    hi = nt.nodes.new("ShaderNodeHairInfo")
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 0.8
    nt.links.new(hi.outputs["Intercept"], pw.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = root_mul
    mr.inputs["To Max"].default_value = tip_mul
    nt.links.new(pw.outputs[0], mr.inputs["Value"])
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = 'SCALE'
    nt.links.new(at.outputs["Color"], vm.inputs[0])
    nt.links.new(mr.outputs["Result"], vm.inputs["Scale"])
    nt.links.new(vm.outputs["Vector"], b.inputs["Base Color"])
    return m


def build_materials():
    tile = knit_tile(os.path.join(OUT, "knit_tile.png"))
    M = {}
    M["Fur"], b = principled("M_Fur", "#D96880", rough=0.85, sheen=0.5, sheen_hex="#FFB0C8")
    nt = M["Fur"].node_tree
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "Col"
    coat = nt.nodes.new("ShaderNodeMix")
    coat.data_type = 'RGBA'
    for sk in coat.inputs:
        if sk.identifier == "A_Color":
            sk.default_value = C.hex_rgba("#F4E8E8")
        elif sk.identifier == "B_Color":
            sk.default_value = C.hex_rgba("#D96880")
    nt.links.new(at.outputs["Alpha"], [sk for sk in coat.inputs if sk.identifier == "Factor_Float"][0])
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = 'MULTIPLY'
    nt.links.new(at.outputs["Color"], mul.inputs[0])
    nt.links.new([sk for sk in coat.outputs if sk.identifier == "Result_Color"][0], mul.inputs[1])
    nt.links.new(mul.outputs[0], b.inputs["Base Color"])
    M["PawPad"], b = principled("M_PawPad", "#FFFFFF", rough=0.45, sheen=0.3, spec=0.4)
    nt = M["PawPad"].node_tree
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "Col"
    nt.links.new(at.outputs["Color"], b.inputs["Base Color"])
    M["PomPom"], _b = principled("M_PomPom", "#2A0C4C", rough=0.9, sheen=0.3, sheen_hex="#C9A0FF")
    M["EyeIris"] = eye_material()
    M["EyeHighlight"], _b = principled("M_EyeHighlight", "#FFFFFF", rough=0.2, emit="#FFFFFF", emit_s=2.0)
    M["Mouth"], _b = principled("M_Mouth", "#3A0C1A", rough=0.5)
    M["Tongue"], _b = principled("M_Tongue", "#F47C98", rough=0.35, coat=0.25)
    M["Lash"], _b = principled("M_EyeLash", "#1E0E12", rough=0.4)
    M["HatKnit"] = knit_material("M_HatKnit", COL_HAT_CROWN, COL_HAT_DARK, tile)
    M["HatCuff"] = knit_material("M_HatCuff", COL_HAT, COL_HAT_DARK, tile)
    M["HatStripe"] = knit_material("M_HatStripe", COL_STRIPE, COL_STRIPE_DARK, tile, bump=0.30)
    M["StarBadge"], _b = principled("M_StarBadge", "#FFCF1F", rough=0.35, coat=0.5, sheen=0.2)
    M["FurStrand"] = fur_strand_material("M_V4_FurStrands", 0.62, 1.16)
    M["PomStrand"] = fur_strand_material("M_V4_PomStrands", 0.30, 1.10, rough=0.75)
    return M


# ------------------------------------------------------------------ metaball unions
def mball_object(name, elems, coll):
    """elems: list of (kind, centre, quat, size(3), radius_surface or None, stiffness)."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution = MB_RES
    mb.render_resolution = MB_RES
    mb.threshold = MB_T
    for kind, c, q, size, rad, s in elems:
        el = mb.elements.new(type=kind)
        el.co = Vector(c)
        el.stiffness = s
        if q is not None:
            el.rotation = q
        if kind == 'ELLIPSOID':
            el.radius = 1.0 / mb_k(s)
            el.size_x, el.size_y, el.size_z = size
        elif kind == 'CAPSULE':
            el.radius = rad / mb_k(s)
            el.size_x = size[0]
        else:
            el.radius = rad / mb_k(s)
    ob = bpy.data.objects.new(name, mb)
    coll.objects.link(ob)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    if not me.polygons:
        raise RuntimeError("metaball %s produced no mesh" % name)
    return me


def capsule(a, b, rad, s):
    a, b = Vector(a), Vector(b)
    d = b - a
    x = d.normalized()                                  # capsule axis = local X
    y = Vector((0.0, 0.0, 1.0)).cross(x)
    if y.length < 1e-6:
        y = Vector((0.0, 1.0, 0.0)).cross(x)
    y.normalize()
    z = x.cross(y)
    return ('CAPSULE', (a + b) * 0.5, basis_quat(x, y, z), (d.length * 0.5, 0, 0), rad, s)


def mitt_frame(side):
    along = (Vector((side * MITT_C.x, MITT_C.y, MITT_C.z)) - Vector((side * ARM_E.x, ARM_E.y, ARM_E.z))).normalized()
    pn = Vector((side * PALM_N.x, PALM_N.y, PALM_N.z))
    pn = (pn - along * pn.dot(along)).normalized()
    across = along.cross(pn).normalized()
    return along, pn, across


def body_elements():
    els = []
    for c, ax, s in BODY_ELEMS:
        els.append(('ELLIPSOID', c, None, ax, None, s))
    for side in (1, -1):
        a = Vector((side * ARM_A.x, ARM_A.y, ARM_A.z))
        e = Vector((side * ARM_E.x, ARM_E.y, ARM_E.z))
        b = Vector((side * ARM_B.x, ARM_B.y, ARM_B.z))
        els.append(capsule(a, e, ARM_RAD, ARM_S))
        els.append(capsule(e, b, ARM_RAD * 0.97, ARM_S))
        along, pn, across = mitt_frame(side)
        els.append(('ELLIPSOID', (side * MITT_C.x, MITT_C.y, MITT_C.z), basis_quat(along, pn, across),
                    (MITT_AX[0], MITT_AX[1], MITT_AX[2]), None, MITT_S))
    return els


def leg_set(front=False):
    if front:
        return dict(hip=FRONT_LEG["hip"], ankle=FRONT_LEG["ankle"], paw_c=FRONT_LEG["paw_c"],
                    toe=FRONT_LEG["toe"].normalized(), sole=FRONT_LEG["sole"])
    return dict(hip=HIP, ankle=ANKLE, paw_c=PAW_C, toe=TOE_DIR, sole=SOLE_N0)


def mirror(v, side):
    return Vector((side * v.x, v.y, v.z))


def paw_frame(side, front=False):
    ls = leg_set(front)
    toe = mirror(ls["toe"], side).normalized()
    sole = mirror(ls["sole"], side)
    sole = (sole - toe * sole.dot(toe)).normalized()
    dorsal = -sole
    lat = toe.cross(dorsal).normalized()
    if lat.x * side < 0:
        lat = -lat
    return lat, toe, sole


def leg_elements(side, front=False):
    ls = leg_set(front)
    hip, ank, pc = mirror(ls["hip"], side), mirror(ls["ankle"], side), mirror(ls["paw_c"], side)
    lat, toe, sole = paw_frame(side, front)
    ex = lat
    ey = toe
    ez = ex.cross(ey).normalized()
    return [capsule(hip, ank, LEG_RAD, 4.0),
            ('ELLIPSOID', pc, basis_quat(ex, ey, ez), PAW_AX, None, 6.0)]


# ------------------------------------------------------------------ surface queries
class Surf:
    def __init__(self, me):
        self.co = [v.co.copy() for v in me.vertices]
        self.bvh = BVHTree.FromPolygons(self.co, [tuple(p.vertices) for p in me.polygons])

    def ray(self, o, d):
        hit = self.bvh.ray_cast(Vector(o), Vector(d).normalized())
        return hit

    def front_point(self, x, z, eps=0.02):
        def fp(xx, zz):
            h = self.ray((xx, -2.0, zz), (0.0, 1.0, 0.0))
            if h[0] is None:
                raise RuntimeError("front ray missed at %.3f %.3f" % (xx, zz))
            return h[0]
        tx = (fp(x + eps, z) - fp(x - eps, z)).normalized()
        tz = (fp(x, z + eps) - fp(x, z - eps)).normalized()
        return fp(x, z), tx.cross(tz).normalized()

    def nearest(self, p):
        return self.bvh.find_nearest(Vector(p))


def face_frame(n, blend=0.35):
    f = n.lerp(Vector((0.0, -1.0, 0.0)), blend).normalized()
    ex = (Vector((1.0, 0.0, 0.0)) - f * f.x).normalized()
    return f, ex, f.cross(ex)


def body_halfwidth(surf, z):
    h = surf.ray((2.0, 0.0, z), (-1.0, 0.0, 0.0))
    return h[0].x if h[0] is not None else 0.0


# ------------------------------------------------------------------ face parts
def cuff_bottom_z(x, surf):
    """World z of the cuff bottom edge in front of the face at lateral x (hat tilt makes the front edge higher)."""
    psi = math.atan2(-0.95, x / 0.5)
    p = hat_pt(0.0, 0.5, psi)
    return p.z


def build_eye(surf, side, z_e):
    S, n = surf.front_point(side * EYE_DX, z_e)
    f, ex, ey = face_frame(n, 0.45)
    RS = (EYE_R ** 2 + EYE_PROT ** 2) / (2.0 * EYE_PROT)       # cap sphere through the footprint rim
    hc = EYE_PROT - RS
    md, loc = MD(), []
    rings = []
    nr, seg = 8, 40
    bmax = math.asin(min(1.0, EYE_R * 1.02 / RS))
    for i in range(nr):
        b = bmax * (1.0 - i / nr)
        r, h = RS * math.sin(b), hc + RS * math.cos(b)
        ring = []
        for j in range(seg):
            ps = math.pi / 2 + 2 * math.pi * j / seg
            lx, ly = r * math.cos(ps), r * math.sin(ps) * 1.12
            ring.append(md.vert(S + ex * lx + ey * ly + f * (h - 0.004)))
            loc.append((lx, ly))
        rings.append(ring)
    apex = md.vert(S + f * (EYE_PROT - 0.004))
    loc.append((0.0, 0.0))
    for a, b in zip(rings, rings[1:]):
        bridge(md, a, b, 0)
    for j in range(seg):
        k = (j + 1) % seg
        md.face((rings[-1][j], rings[-1][k], apex), 0)
    px, py = -side * PUPIL_IN, -PUPIL_DOWN
    md.uv = [[(0.5 + (loc[i][0] - px) / (2 * IRIS_R), 0.5 + (loc[i][1] - py) / (2 * IRIS_R)) for i in fc] for fc in md.f]
    info = dict(S=S, f=f, ex=ex, ey=ey, RS=RS, hc=hc - 0.004, side=side)
    return md, info


def build_catchlight(eye, lx, ly, radius, seg=18):
    S, f, ex, ey, RS, hc = eye["S"], eye["f"], eye["ex"], eye["ey"], eye["RS"], eye["hc"]

    def on_cap(x, y, lift):
        z = math.sqrt(max(RS * RS - x * x - y * y, 1e-8)) + hc
        return S + ex * x + ey * y + f * (z + lift)
    md = MD()
    c = md.vert(on_cap(lx, ly, 0.003))
    ring = [md.vert(on_cap(lx + radius * math.cos(2 * math.pi * j / seg),
                           ly + radius * 1.1 * math.sin(2 * math.pi * j / seg), 0.0025)) for j in range(seg)]
    for j in range(seg):
        md.face((ring[j], ring[(j + 1) % seg], c), 0)
    md.uv = [[(0.5, 0.5)] * 3 for _ in md.f]
    return md


def build_lashes(eye):
    """3 small dark curved lashes at the OUTER upper corner (reference 03 / 05)."""
    S, f, ex, ey, side = eye["S"], eye["f"], eye["ex"], eye["ey"], eye["side"]
    md = MD()
    out = ex * side
    for k, ang in enumerate((34.0, 52.0, 70.0)):
        a = math.radians(ang)
        base = S + out * (EYE_R * 0.98 * math.cos(a)) + ey * (EYE_R * 1.03 * math.sin(a)) + f * 0.006
        dirv = (out * math.cos(a) * 0.75 + ey * (math.sin(a) * 1.1 + 0.35) + f * 0.22).normalized()
        L = 0.042 - 0.005 * k
        pts = [base, base + dirv * L * 0.5 + ey * 0.004, base + dirv * L + ey * 0.010 + out * 0.004]
        wid = [0.0068, 0.0042, 0.0007]
        rings = []
        for p, w in zip(pts, wid):
            t = (dirv).normalized()
            u = t.cross(f).normalized()
            v = t.cross(u).normalized()
            rings.append([md.vert(p + (u * math.cos(2 * math.pi * j / 5) + v * math.sin(2 * math.pi * j / 5)) * w)
                          for j in range(5)])
        for r0, r1 in zip(rings, rings[1:]):
            bridge(md, r0, r1, 0)
    return md


def mouth_outline(n, w, h):
    """Open smile: cat-lip 'w' top edge (two arcs meeting at a centre peak), round U bottom. CCW from the front."""
    pts = []
    nt = n // 2
    for i in range(nt + 1):
        x = -w / 2 + w * i / nt
        t = abs(x) / (w / 2)
        y = h / 2 - 0.012 * math.sin(math.pi * t) ** 0.9 * (1.0 if t < 1 else 0.0) + 0.005 * (1 - t) ** 6
        pts.append((x, y))
    nb = n - nt - 1
    for i in range(1, nb + 1):
        a = math.pi * i / (nb + 1)
        pts.append(((w / 2) * math.cos(a) * (1.0 - 0.18 * math.sin(a)), h / 2 - h * math.sin(a) ** 0.9))
    pts.reverse()
    return pts


def build_mouth(surf, z_top):
    zc = z_top - MOUTH_H / 2
    S, n = surf.front_point(0.0, zc)
    f, ex, ey = face_frame(n, 0.3)
    outline = mouth_outline(36, MOUTH_W, MOUTH_H)
    ring_sh = [(1.20, -0.004), (1.08, 0.0035), (1.0, 0.0045), (0.92, 0.0035), (0.70, 0.0015), (0.35, -0.001)]

    def place(x, y, h):
        hit = surf.ray(S + ex * x + ey * y + f * 0.3, -f)
        base = hit[0] if hit[0] is not None else S + ex * x + ey * y
        return base + f * h
    md, rings = MD(), []
    for s, h in ring_sh:
        rings.append([md.vert(place(x * s, y * s, h)) for (x, y) in outline])
    centre = md.vert(place(0.0, -0.01, -0.003))
    for k, mat in enumerate((1, 0, 0, 0, 0)):
        bridge(md, rings[k], rings[k + 1], mat)
    for j in range(len(outline)):
        md.face((rings[-1][j], rings[-1][(j + 1) % len(outline)], centre), 0)
    tongue = ellipsoid(place(0.0, -MOUTH_H / 2 + 0.036, 0.001), ex, ey, f, 0.056, 0.034, 0.012, seg=16, rings=8)
    return md, tongue, S, dict(S=S, f=f, ex=ex, ey=ey, zc=zc)


def build_nose(surf, z):
    sn, nn = surf.front_point(0.0, z)
    f, ex, ey = face_frame(nn, 0.3)
    nose = ellipsoid(Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)),
                     Vector((0.0, 0.0, 1.0)), 0.019, 0.012, 0.009, seg=12, rings=6)
    out = []
    for v in nose.v:
        x = v.x * (1.0 + 0.6 * (v.y / 0.012)) if v.y < 0 else v.x
        out.append(sn + ex * x + ey * v.y + f * (v.z + 0.002))
    nose.v = out
    return nose, sn


# ------------------------------------------------------------------ beanie, pom-pom, star
def knit_uv(psi, v):
    return ((psi + math.pi / 2) / (2 * math.pi) % 1.0) * (RIB_N / 44.0), v


def build_beanie(r_tuck):
    """One lathe surface: tuck -> cuff (rolled bottom, ribbed face, top fold) -> stripe -> round crown dome."""
    prof = [(-0.030, r_tuck, 1)] + [(h, r, 1) for h, r in CUFF_PROF] + [(h, r, 2) for h, r in STRIPE_PROF]
    nd = 12
    for i in range(1, nd + 1):
        ph = (math.pi / 2) * i / nd
        e = 2.0 / DOME_E
        prof.append((DOME_H0 + DOME_H * math.sin(ph) ** e, DOME_R0 * math.cos(ph) ** e, 0))
    prof[-1] = (DOME_H0 + DOME_H, 0.0, 0)
    seg = 2 * RIB_N
    md = MD()
    arcs = [0.0]
    for a, b in zip(prof, prof[1:]):
        arcs.append(arcs[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    rings = []
    for k, (h, r, mat) in enumerate(prof):
        if r <= 1e-6:
            rings.append(None)
            continue
        a0, a1 = prof[max(0, k - 1)], prof[min(len(prof) - 1, k + 1)]
        nrm = Vector((a1[0] - a0[0], -(a1[1] - a0[1])))       # (dh, dr) rotated -> outward (r, h) normal
        nrm = Vector((nrm.x, nrm.y))
        nr_r, nr_h = nrm.x, nrm.y
        L = math.hypot(nr_r, nr_h) or 1.0
        nr_r, nr_h = nr_r / L, nr_h / L
        amp = ({1: CUFF_AMP, 2: CUFF_AMP * 0.45}.get(mat, CROWN_AMP)) * min(1.0, r / 0.2) * (0.0 if k == 0 else 1.0)
        ring = []
        for j in range(seg):
            psi = -math.pi / 2 + 2 * math.pi * j / seg
            o = amp * (1.0 if j % 2 == 1 else -1.0)
            ring.append(md.vert(hat_pt(h + nr_h * o, r + nr_r * o, psi)))
        rings.append(ring)
    pole = md.vert(hat_pt(prof[-1][0], 0.0, 0.0))
    for k in range(len(prof) - 1):
        r0, r1 = rings[k], rings[k + 1]
        mat = prof[k + 1][2]
        if r1 is None:
            for j in range(seg):
                jk = (j + 1) % seg
                psi_a, psi_b = -math.pi / 2 + 2 * math.pi * j / seg, -math.pi / 2 + 2 * math.pi * (j + 1) / seg
                ua, ub = knit_uv(psi_a, arcs[k])[0], knit_uv(psi_b, arcs[k])[0]
                if jk == 0:
                    ub = RIB_N / 44.0
                md.face((r0[j], r0[jk], pole), mat, [(ua, arcs[k]), (ub, arcs[k]), ((ua + ub) / 2, arcs[k + 1])])
            continue
        hm = 0.5 * (prof[k][0] + prof[k + 1][0])
        for j in range(seg):
            jk = (j + 1) % seg
            psi_a = -math.pi / 2 + 2 * math.pi * j / seg
            psi_b = psi_a + 2 * math.pi / seg
            ua = knit_uv(psi_a, 0)[0]
            ub = ua + (RIB_N / 44.0) / seg
            m = mat
            if mat == 0 and TOP_BAND[0] <= hm <= TOP_BAND[1]:
                dpsi = abs(math.degrees((psi_a + math.pi / seg) + math.pi / 2))
                dpsi = min(dpsi, 360.0 - dpsi)
                frac = (hm - TOP_BAND[0]) / (TOP_BAND[1] - TOP_BAND[0])
                half = 0.5 * smoothstep(TOP_BAND_PSI + 40.0, TOP_BAND_PSI, dpsi)
                if abs(frac - 0.5) <= half:
                    m = 2
            md.face((r0[j], r0[jk], r1[jk], r1[j]), m, [(ua, arcs[k]), (ub, arcs[k]), (ub, arcs[k + 1]),
                                                         (ua, arcs[k + 1])])
    top_h = prof[-1][0]
    return md, top_h, prof


def build_pompom_core():
    c = hat_pt(POM_H, 0.0, 0.0)
    md = ellipsoid(c, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), POM_CORE, POM_CORE, POM_CORE * 0.97,
                   seg=20, rings=12)
    return md, c


def star_outline():
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


def cuff_r(h):
    """Smooth outer envelope of the beanie profile (cuff face -> stripe -> crown dome) for badges."""
    pts = list(CUFF_PROF[2:8]) + list(STRIPE_PROF[2:])
    for i in range(1, 9):
        ph = (math.pi / 2) * i / 9
        pts.append((DOME_H0 + DOME_H * math.sin(ph) ** (2.0 / DOME_E), DOME_R0 * math.cos(ph) ** (2.0 / DOME_E)))
    for (h0, r0), (h1, r1) in zip(pts, pts[1:]):
        if h0 <= h <= h1:
            return r0 + (r1 - r0) * (h - h0) / (h1 - h0)
    return pts[0][1] if h < pts[0][0] else pts[-1][1]


def build_star():
    psi_s = math.radians(STAR_PSI) - math.pi / 2

    def surf(h, ps):
        return hat_pt(h, cuff_r(h) + CUFF_AMP + 0.002, ps)
    rot = Matrix.Rotation(math.radians(STAR_ROT), 2)
    outline = star_outline()
    ring_sh = [(1.0, -0.006), (1.0, 0.006), (0.93, 0.015), (0.76, 0.023), (0.48, 0.028)]
    md = MD()

    def place(x, y, hh):
        q = rot @ Vector((x, y))
        h = STAR_H + q.y
        ps = psi_s + q.x / 0.53
        d = 0.004
        t_psi = surf(h, ps + d) - surf(h, ps - d)
        t_up = surf(h + d, ps) - surf(h - d, ps)
        return surf(h, ps) + t_psi.cross(t_up).normalized() * hh
    rings = [[md.vert(place(p.x * s, p.y * s, hh)) for p in outline] for s, hh in ring_sh]
    centre = md.vert(place(0.0, 0.0, 0.030))
    for a, b in zip(rings, rings[1:]):
        bridge(md, a, b, 0)
    for j in range(len(outline)):
        md.face((rings[-1][j], rings[-1][(j + 1) % len(outline)], centre), 0)
    return md


# ------------------------------------------------------------------ pads (palms + soles)
def pad_disc(surf, c_out, n, ex, ey, rx, ry, h, col, seg=14):
    """Soft raised pad on a surface: rays from outside along -n give the footprint; dome h above it."""
    md = MD()
    rings = []
    for i, t in enumerate((1.0, 0.75, 0.45)):
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            p = c_out + ex * (rx * t * math.cos(a)) + ey * (ry * t * math.sin(a))
            hit = surf.ray(p + n * 0.3, -n)
            base = hit[0] if hit[0] is not None else p
            ring.append(md.vert(base + n * (h * (1.0 - t * t) ** 0.5 + (0.001 if i == 0 else 0.0) - 0.002)))
        rings.append(ring)
    hit = surf.ray(c_out + n * 0.3, -n)
    top = md.vert((hit[0] if hit[0] is not None else c_out) + n * h)
    for a, b in zip(rings, rings[1:]):
        bridge(md, a, b, 0)
    for j in range(seg):
        md.face((rings[-1][j], rings[-1][(j + 1) % seg], top), 0)
    md.col = [[col] * len(f) for f in md.f]
    return md


# ------------------------------------------------------------------ fur: hair curves from a surface
def mesh_arrays(me):
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tri = np.empty(nt * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    tri = tri.reshape(-1, 3)
    nv = len(me.vertices)
    co = np.empty(nv * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3).astype(np.float64)
    nor = np.empty(nv * 3, dtype=np.float32)
    try:
        me.vertex_normals.foreach_get("vector", nor)
    except Exception:
        me.vertices.foreach_get("normal", nor)
    nor = nor.reshape(-1, 3).astype(np.float64)
    return tri, co, nor


def sample_surface(me, n, seed):
    tri, co, nor = mesh_arrays(me)
    a, b, c = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(tri), size=n, p=area / area.sum())
    r1 = np.sqrt(rng.random(n))
    r2 = rng.random(n)
    wa, wb, wc = 1.0 - r1, r1 * (1.0 - r2), r1 * r2
    P = a[idx] * wa[:, None] + b[idx] * wb[:, None] + c[idx] * wc[:, None]
    N = nor[tri[idx, 0]] * wa[:, None] + nor[tri[idx, 1]] * wb[:, None] + nor[tri[idx, 2]] * wc[:, None]
    N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
    return P, N, float(area.sum())


def normalize_rows(v):
    return v / (np.linalg.norm(v, axis=1)[:, None] + 1e-12)


def noise3(P, scale, off):
    return np.array([noise.noise(Vector((p[0] * scale + off[0], p[1] * scale + off[1], p[2] * scale + off[2])))
                     for p in P])


def make_curves(name, pts, radii, cols, mat, coll):
    n, k, _ = pts.shape
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([k] * n)
    cv.attributes["position"].data.foreach_set("vector", pts.astype(np.float32).ravel())
    rad = cv.attributes.get("radius") or cv.attributes.new("radius", 'FLOAT', 'POINT')
    rad.data.foreach_set("value", radii.astype(np.float32).ravel())
    ca = cv.attributes.new("fur_col", 'FLOAT_COLOR', 'CURVE')
    ca.data.foreach_set("color", np.concatenate([cols, np.ones((n, 1))], axis=1).astype(np.float32).ravel())
    cv.materials.append(mat)
    ob = bpy.data.objects.new(name, cv)
    coll.objects.link(ob)
    return ob


def bezier_pts(P, N, tip, L, k):
    ctrl = P + N * (L[:, None] * 0.42)
    ts = np.linspace(0.0, 1.0, k)
    out = np.empty((len(P), k, 3))
    for i, t in enumerate(ts):
        out[:, i] = (1 - t) ** 2 * P + 2 * (1 - t) * t * ctrl + t * t * tip
    return out



# ------------------------------------------------------------------ simple armature + controls (intro shots, Agent 5)
# Same 17 bone names as the game rig (build_mascot_rig.py). Meshes are skinned (Armature modifier); the hair-curve fur
# follows its skinned surface through Geometry Nodes "Deform Curves on Surface" (root UVs bound to a smart-UV map);
# the pom-pom yarn is bone-parented to "pompom". Rest pose = the modelled seated hero pose.
BONE_NAMES = ['root', 'body', 'head', 'hat', 'hat_tip', 'pompom', 'arm.L', 'hand.L', 'arm.R', 'hand.R',
              'leg.L', 'foot.L', 'leg.R', 'foot.R', 'tail', 'eye.L', 'eye.R']
_DEFORM = {}


def select_only(ob):
    bpy.context.view_layer.update()
    for o in list(bpy.context.view_layer.objects):
        if o is not None:
            o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def smart_uv(ob):
    select_only(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)


def root_uvs(surf_ob, P):
    me = surf_ob.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tv = np.empty(nt * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", tv)
    tv = tv.reshape(-1, 3)
    tl = np.empty(nt * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("loops", tl)
    tl = tl.reshape(-1, 3)
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3).astype(np.float64)
    uv = np.empty(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers["UVMap"].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2).astype(np.float64)
    bvh = BVHTree.FromPolygons([Vector(c) for c in co], [tuple(int(i) for i in t) for t in tv])
    ti = np.zeros(len(P), dtype=np.int64)
    q = np.array(P, dtype=np.float64).copy()
    for i, p in enumerate(P):
        hit = bvh.find_nearest(Vector(p))
        if hit[2] is not None:
            ti[i] = hit[2]
            q[i] = hit[0]
    a, b, c = co[tv[ti, 0]], co[tv[ti, 1]], co[tv[ti, 2]]
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = np.sum(v0 * v0, 1), np.sum(v0 * v1, 1), np.sum(v1 * v1, 1)
    d20, d21 = np.sum(v2 * v0, 1), np.sum(v2 * v1, 1)
    den = d00 * d11 - d01 * d01
    den = np.where(np.abs(den) < 1e-14, 1e-14, den)
    wb = (d11 * d20 - d01 * d21) / den
    wc = (d00 * d21 - d01 * d20) / den
    wa = 1.0 - wb - wc
    return wa[:, None] * uv[tl[ti, 0]] + wb[:, None] * uv[tl[ti, 1]] + wc[:, None] * uv[tl[ti, 2]]


def deform_group():
    if "g" not in _DEFORM:
        ng = bpy.data.node_groups.new("V4_DeformCurvesOnSurface", 'GeometryNodeTree')
        ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
        d = ng.nodes.new("GeometryNodeDeformCurvesOnSurface")
        ng.links.new(gi.outputs[0], d.inputs[0])
        ng.links.new(d.outputs[0], go.inputs[0])
        _DEFORM["g"] = ng
    return _DEFORM["g"]


def bind_curves(cob, surf_ob):
    cv = cob.data
    k = len(cv.points) // max(1, len(cv.curves))
    pos = np.empty(len(cv.points) * 3, dtype=np.float32)
    cv.attributes["position"].data.foreach_get("vector", pos)
    uvs = root_uvs(surf_ob, pos.reshape(-1, k, 3)[:, 0].astype(np.float64))
    cv.surface = surf_ob
    cv.surface_uv_map = "UVMap"
    a = cv.attributes.get("surface_uv_coordinate") or cv.attributes.new("surface_uv_coordinate", 'FLOAT2', 'CURVE')
    a.data.foreach_set("vector", uvs.astype(np.float32).ravel())
    cob.parent = surf_ob
    m = cob.modifiers.new("V4_SurfaceDeform", 'NODES')
    m.node_group = deform_group()


def vgroups(ob, weights):
    n = len(ob.data.vertices)
    for name, w in weights.items():
        vg = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
        w = np.asarray(w, dtype=np.float64)
        if w.ndim == 0:
            vg.add(list(range(n)), float(w), 'REPLACE')
            continue
        for i in np.nonzero(w > 1e-4)[0]:
            vg.add([int(i)], float(w[i]), 'REPLACE')


def obj_co(ob):
    co = np.empty(len(ob.data.vertices) * 3, dtype=np.float32)
    ob.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3).astype(np.float64)


def build_armature(objs, curves, coll, land):
    ad = bpy.data.armatures.new("Armature_v4")
    arm = bpy.data.objects.new("Armature_v4", ad)
    coll.objects.link(arm)
    select_only(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = ad.edit_bones
    up, fwd = Vector((0.0, 0.0, 1.0)), Vector((0.0, -1.0, 0.0))

    def bone(name, h, t, parent=None, roll_up=up):
        b = eb.new(name)
        b.head, b.tail = Vector(h), Vector(t)
        if parent:
            b.parent = eb[parent]
        b.align_roll(roll_up)
        return b
    ax = HAT_AXIS
    pom_c = Vector(land["hat"]["pom_c"])
    bone('root', (0, 0, 0), (0, 0, 0.15), None, fwd)
    bone('body', (0, 0, 0.03), (0, 0, 0.50), 'root', fwd)
    bone('head', (0, 0, 0.50), (0, 0, 0.95), 'body', fwd)
    bone('hat', HAT_O, HAT_O + ax * 0.28, 'head', fwd)
    bone('hat_tip', HAT_O + ax * 0.28, HAT_O + ax * 0.50, 'hat', fwd)
    bone('pompom', pom_c, pom_c + ax * 0.20, 'hat_tip', fwd)
    for side, tag in ((1, 'L'), (-1, 'R')):
        a, b, mc = mirror(ARM_A, side), mirror(ARM_B, side), mirror(MITT_C, side)
        along = (mc - b).normalized()
        bone('arm.' + tag, a, b, 'body')
        bone('hand.' + tag, b, mc + along * 0.10, 'arm.' + tag)
        ls = leg_set(False)
        hip, ank, pc = mirror(ls["hip"], side), mirror(ls["ankle"], side), mirror(ls["paw_c"], side)
        _lat, toe, _sole = paw_frame(side, False)
        bone('leg.' + tag, hip, ank, 'root')
        bone('foot.' + tag, ank, pc + toe * 0.08, 'leg.' + tag)
        e = land["eyes"][tag]
        S, f = Vector(e["S"]), Vector(e["f"]).normalized()
        cen = S + f * e["hc"]
        bone('eye.' + tag, cen, cen + f * 0.08, 'head')
    bone('tail', TAIL_C, TAIL_C + Vector((0.0, 0.10, 0.0)), 'body', up)
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.select_set(False)

    # ---- weights
    def body_w(co):
        W, tot = {}, np.zeros(len(co))
        for side, tag in ((1, 'L'), (-1, 'R')):
            A, Mc = np.array(mirror(ARM_A, side)), np.array(mirror(MITT_C, side))
            d = Mc - A
            t = np.clip(((co - A) @ d) / (d @ d), 0.0, 1.0)
            dist = np.linalg.norm(co - (A + t[:, None] * d), axis=1)
            w = (np_smooth(0.06, 0.32, t) * (1.0 - np_smooth(ARM_RAD * 1.5, ARM_RAD * 2.6, dist))
                 * (side * co[:, 0] > 0.28))
            hand = w * np_smooth(0.60, 0.80, t)
            W['arm.' + tag], W['hand.' + tag] = w - hand, hand
            tot += w
        rest = 1.0 - np.clip(tot, 0.0, 1.0)
        head = np_smooth(0.42, 0.68, co[:, 2]) * rest
        W['head'], W['body'] = head, rest - head
        return W
    vgroups(objs["Body"], body_w(obj_co(objs["Body"])))
    co = obj_co(objs["Beanie"])
    hq = (np.array(HAT_R.transposed()) @ (co - np.array(HAT_O)).T).T[:, 2]
    tip = np_smooth(0.30, 0.46, hq)
    vgroups(objs["Beanie"], {'hat': 1.0 - tip, 'hat_tip': tip})
    vgroups(objs["PomPom"], {'pompom': 1.0})
    vgroups(objs["StarBadge"], {'hat': 1.0})
    for nm in ("Mouth", "Tongue"):
        vgroups(objs[nm], {'head': 1.0})
    vgroups(objs["Tail"], {'tail': 1.0})
    for tag in ("L", "R"):
        for nm in ("Eye." + tag, "Catchlight.%s1" % tag, "Catchlight.%s2" % tag):
            vgroups(objs[nm], {'eye.' + tag: 1.0})
        vgroups(objs["PalmPads." + tag], {'hand.' + tag: 1.0})
    co = obj_co(objs["Lashes"])
    vgroups(objs["Lashes"], {'eye.L': (co[:, 0] > 0).astype(float), 'eye.R': (co[:, 0] <= 0).astype(float)})
    for side, tag in ((1, 'L'), (-1, 'R')):
        ls = leg_set(False)
        hip, pc = np.array(mirror(ls["hip"], side)), np.array(mirror(ls["paw_c"], side))
        co = obj_co(objs["Leg." + tag])
        d = pc - hip
        t = np.clip(((co - hip) @ d) / (d @ d), 0.0, 1.0)
        foot = np_smooth(0.45, 0.75, t)
        vgroups(objs["Leg." + tag], {'leg.' + tag: 1.0 - foot, 'foot.' + tag: foot})
        vgroups(objs["LegFront." + tag], {'body': 1.0})     # front-shot legs simply follow the body
    for nm, o in objs.items():
        o.parent = arm
        m = o.modifiers.new("Armature", 'ARMATURE')
        m.object = arm
    # ---- fur follows the skinned surfaces
    for nm in ("Body", "Leg.L", "Leg.R", "LegFront.L", "LegFront.R"):
        smart_uv(objs[nm])
        objs[nm].add_rest_position_attribute = True
    bind_curves(curves["Fur_Body"], objs["Body"])
    for key in ("Leg.L", "Leg.R", "LegFront.L", "LegFront.R"):
        bind_curves(curves["Fur_" + key], objs[key])
    pf = curves["Fur_PomPom"]
    pf.parent = arm
    pf.parent_type = 'BONE'
    pf.parent_bone = 'pompom'
    bpy.context.view_layer.update()
    pf.matrix_world = Matrix.Identity(4)
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
    print("CHECK armature bones %d: %s" % (len(ad.bones), ",".join(b.name for b in ad.bones)))
    return arm


def pose_test(arm, on=True):
    pb = arm.pose.bones
    for b in pb:
        b.rotation_euler = (0.0, 0.0, 0.0)
        b.scale = (1.0, 1.0, 1.0)
    if on:
        pb['head'].rotation_euler = (math.radians(-6.0), math.radians(18.0), 0.0)
        pb['arm.L'].rotation_euler = (math.radians(28.0), 0.0, 0.0)
        pb['arm.R'].rotation_euler = (math.radians(-20.0), 0.0, 0.0)
        pb['eye.L'].rotation_euler = (0.0, 0.0, math.radians(12.0))
        pb['eye.R'].scale = (1.0, 1.0, 0.15)
        pb['pompom'].rotation_euler = (math.radians(-10.0), 0.0, 0.0)
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ assembly
def main():
    C.reset_scene()
    os.makedirs(OUT, exist_ok=True)
    M = build_materials()
    coll = bpy.data.collections.new(COLL_NAME)
    bpy.context.scene.collection.children.link(coll)
    fur_coll = bpy.data.collections.new(COLL_NAME + "_Fur")
    coll.children.link(fur_coll)

    # ---- body union (body + head + arms)
    me_body = mball_object("V4BodyMB", body_elements(), coll)
    surf = Surf(me_body)
    print("CHECK body verts %d faces %d" % (len(me_body.vertices), len(me_body.polygons)))
    for z in (0.10, 0.25, 0.40, 0.50, 0.60, 0.68, 0.80, 0.95, 1.05):
        h = surf.ray((0.0, -2.0, z), (0.0, 1.0, 0.0))
        print("CHECK body z %.2f half-width %.3f front y %.3f" % (z, body_halfwidth(surf, z) if z < 0.52 or z > 0.92
                                                                   else float('nan'),
                                                                   h[0].y if h[0] is not None else float('nan')))
    zs = [v.co.z for v in me_body.vertices]
    print("CHECK body z range %.3f %.3f" % (min(zs), max(zs)))

    # ---- legs (separate unions, pressed against the seat): gameplay W-sit "Leg" + front-shot "LegFront"
    LEGSETS = (("Leg", False), ("LegFront", True))
    legs = {}
    for prefix, front in LEGSETS:
        for side, tag in ((1, "L"), (-1, "R")):
            legs[prefix + "." + tag] = mball_object("V4%s%sMB" % (prefix, tag), leg_elements(side, front), coll)

    # ---- hat fit: tuck radius from the body just under the cuff bottom
    r_tuck = 9.0
    for k in range(16):
        psi = 2 * math.pi * k / 16
        d = HAT_R @ Vector((math.cos(psi), math.sin(psi), 0.0))
        hit = surf.ray(HAT_O - HAT_AXIS * 0.03, d)
        if hit[0] is not None:
            r_tuck = min(r_tuck, (hit[0] - (HAT_O - HAT_AXIS * 0.03)).length)
    r_tuck -= 0.012
    beanie, top_h, prof = build_beanie(r_tuck)
    # head clearance inside the hat
    worst = 9.0
    for h, r, _m in prof[1:]:
        if r < 0.05:
            continue
        for k in range(24):
            psi = 2 * math.pi * k / 24
            p_axis = HAT_O + HAT_AXIS * h
            d = HAT_R @ Vector((math.cos(psi), math.sin(psi), 0.0))
            if h < 0.26 and abs(math.sin(psi)) < 0.55:
                continue                                   # side sectors of the cuff band: arm roots pass there
            hit = surf.ray(p_axis, d)
            if hit[0] is not None:
                worst = min(worst, r - (hit[0] - p_axis).length)
    print("CHECK hat tuck r %.3f  min clearance hat-outside minus head %.3f (must be > 0.01)  top h %.3f z %.3f" % (
        r_tuck, worst, top_h, hat_pt(top_h, 0, 0).z))

    # ---- face
    zcb = cuff_bottom_z(0.0, surf)
    z_e = zcb - EYE_UNDER
    eyes, lights, lashes = {}, {}, MD()
    for side, tag in ((1, "L"), (-1, "R")):
        md, info = build_eye(surf, side, z_e)
        eyes[tag] = (md, info)
        lights[tag + "1"] = build_catchlight(info, -0.28 * EYE_R, 0.30 * EYE_R, 0.027)
        lights[tag + "2"] = build_catchlight(info, 0.26 * EYE_R, -0.30 * EYE_R, 0.011, 12)
        lashes.extend(build_lashes(info))
    mouth, tongue, mouth_pt, minfo = build_mouth(surf, z_e - MOUTH_TOP_DZ)
    nose, nose_pt = build_nose(surf, z_e - NOSE_DZ)
    print("CHECK face cuff-bottom z %.3f eyes z %.3f nose z %.3f mouth centre z %.3f" % (
        zcb, z_e, z_e - NOSE_DZ, minfo["zc"]))

    # ---- body vertex colours (Col: rgb tint, a = coat 1 pink / 0 cream)
    blush_pts = [surf.front_point(s * BLUSH_DX, z_e - BLUSH_DZ)[0] for s in (1, -1)]
    body = MD()
    body.v = [v.co.copy() for v in me_body.vertices]
    for p in me_body.polygons:
        body.face(tuple(p.vertices), 0)

    def body_col(i):
        p = body.v[i]
        g = 1.0
        rgb = [g, g, g]
        for bp in blush_pts:
            w = 0.9 * math.exp(-((p - bp).length / BLUSH_R) ** 2)
            rgb = [c * (1.0 - w) + t * w for c, t in zip(rgb, (1.0, 0.62, 0.68))]
        under = smoothstep(0.30, 0.05, p.z)
        rgb = [c * (1.0 - 0.5 * under) + 1.0 * 0.5 * under for c in rgb]
        return (rgb[0], rgb[1], rgb[2], 1.0)
    vcol = [body_col(i) for i in range(len(body.v))]
    body.col = [[vcol[i] for i in f] for f in body.f]

    # ---- pads: palms (front) + soles (rear camera)
    pads_arm = {}
    for side, tag in ((1, "L"), (-1, "R")):
        along, pn, across = mitt_frame(side)
        c = Vector((side * MITT_C.x, MITT_C.y, MITT_C.z))
        pk = MD()
        pink = tuple(C.hex_rgba(COL_PAD)[:3]) + (1.0,)
        pink = (0.95, 0.46, 0.60, 1.0)
        pk.extend(pad_disc(surf, c - along * 0.012, pn, across, along, 0.040, 0.036, 0.010, pink))
        for k, (u, w) in enumerate(((-0.040, 0.052), (0.0, 0.066), (0.040, 0.052))):
            pk.extend(pad_disc(surf, c + across * u + along * w, pn, across, along, 0.016, 0.018, 0.008, pink, 10))
        pads_arm[tag] = pk
    leg_surf = {t: Surf(m) for t, m in legs.items()}
    pads_leg, leg_info = {}, {}
    for prefix, front in LEGSETS:
        for side, tag in ((1, "L"), (-1, "R")):
            key = prefix + "." + tag
            lat, toe, sole = paw_frame(side, front)
            pc = mirror(leg_set(front)["paw_c"], side)
            pk = MD()
            pink = (0.95, 0.46, 0.60, 1.0)
            centres = [pc - toe * 0.045]
            pk.extend(pad_disc(leg_surf[key], pc - toe * 0.045, sole, lat, toe, 0.060, 0.052, 0.013, pink))
            for u, w in ((-0.072, 0.040), (-0.026, 0.078), (0.026, 0.078), (0.072, 0.040)):
                q = pc + lat * u + toe * w
                centres.append(q)
                pk.extend(pad_disc(leg_surf[key], q, sole, lat, toe, 0.027, 0.031, 0.011, pink, 12))
            pads_leg[key] = pk
            leg_info[key] = dict(paw_c=pc, toe=toe, sole_n=sole, lat=lat, pads=centres)

    tail = ellipsoid(TAIL_C, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), TAIL_R, TAIL_R, TAIL_R)
    pom_core, pom_c = build_pompom_core()
    star = build_star()

    # ---- objects
    objs = {}

    def add(name, md, mats, collection=coll):
        o = md.to_object(name, mats, collection)
        objs[name] = o
        return o
    add("Body", body, [M["Fur"]])
    for tag in ("L", "R"):
        add("Eye." + tag, eyes[tag][0], [M["EyeIris"]])
        add("Catchlight.%s1" % tag, lights[tag + "1"], [M["EyeHighlight"]])
        add("Catchlight.%s2" % tag, lights[tag + "2"], [M["EyeHighlight"]])
    mouth.extend(nose)                                  # tiny nose = part of the Mouth object (M_Mouth)
    add("Mouth", mouth, [M["Mouth"], M["Fur"]])
    add("Tongue", tongue, [M["Tongue"]])
    add("Lashes", lashes, [M["Lash"]])
    for key, me_leg in legs.items():
        lm = MD()
        lm.v = [v.co.copy() for v in me_leg.vertices]
        for p in me_leg.polygons:
            lm.face(tuple(p.vertices), 0, col=[(1.0, 1.0, 1.0, 0.0)] * len(p.vertices))
        lm.extend(pads_leg[key])
        lm.m = [0] * (len(lm.f) - len(pads_leg[key].f)) + [1] * len(pads_leg[key].f)
        add(key, lm, [M["Fur"], M["PawPad"]])
    for tag in ("L", "R"):
        add("PalmPads." + tag, pads_arm[tag], [M["PawPad"]])
    add("Tail", tail, [M["Fur"]])
    add("Beanie", beanie, [M["HatKnit"], M["HatCuff"], M["HatStripe"]])
    add("PomPom", pom_core, [M["PomPom"]])
    add("StarBadge", star, [M["StarBadge"]])
    for o in objs.values():
        for p in o.data.polygons:
            p.use_smooth = True

    # ---- fur strands on the body union
    t0 = time.time()
    P, N, area = sample_surface(me_body, FUR_N, 11)
    z_e_v = z_e
    keep = np.ones(len(P), dtype=bool)
    Lmul = np.ones(len(P))
    # under the hat: no fur
    Q = (np.array(HAT_R.transposed()) @ (P - np.array(HAT_O)).T).T
    rq = np.hypot(Q[:, 0], Q[:, 1])
    inside = rq < 0.545
    keep &= ~(inside & (Q[:, 2] > 0.004))
    Lmul *= np.where(inside, 0.55 + 0.45 * np_smooth(0.0, -0.06, Q[:, 2]), 1.0)
    # face features
    for tag in ("L", "R"):
        S = np.array(eyes[tag][1]["S"])
        d = np.linalg.norm(P - S, axis=1)
        keep &= d > EYE_R * 1.04
        Lmul *= 0.30 + 0.70 * np_smooth(EYE_R * 1.05, EYE_R * 1.9, d)
    mc = np.array(minfo["S"])
    dm = np.sqrt(((P[:, 0] - mc[0]) / (MOUTH_W * 0.62)) ** 2 + ((P[:, 2] - mc[2]) / (MOUTH_H * 0.60)) ** 2)
    front = P[:, 1] < mc[1] + 0.12
    keep &= ~(front & (dm < 1.0))
    Lmul *= np.where(front, 0.30 + 0.70 * np_smooth(1.0, 1.9, dm), 1.0)
    dn = np.linalg.norm(P - np.array(nose_pt), axis=1)
    keep &= dn > 0.03
    # palm pads
    for side, tag in ((1, "L"), (-1, "R")):
        along, pn, across = mitt_frame(side)
        mc3 = np.array(Vector((side * MITT_C.x, MITT_C.y, MITT_C.z)))
        rel = P - mc3
        on_palm = (rel @ np.array(pn)) > 0.035
        keep &= ~(on_palm & (np.linalg.norm(rel, axis=1) < 0.13))
    # face zone: shorter fur on the front of the head
    face_w = np_smooth(-0.30, -0.42, P[:, 1]) * np_smooth(0.30, 0.42, P[:, 2]) * np_smooth(0.36, 0.28, np.abs(P[:, 0]))
    Lmul *= 1.0 - 0.45 * face_w
    Lmul *= np.where(np.abs(P[:, 0]) > 0.50, 0.55, 1.0)            # shorter plush on the arms / paws
    P, N, Lmul, face_w = P[keep], N[keep], Lmul[keep], face_w[keep]
    n = len(P)
    nz1 = noise3(P, 9.0, (3.1, 7.7, 1.3))
    nz2 = noise3(P, 23.0, (8.2, 1.4, 5.9))
    rng = np.random.default_rng(5)
    L = FUR_LEN * Lmul * (0.80 + 0.26 * nz1 + 0.12 * nz2 + 0.12 * rng.random(n))
    L *= np.where(rng.random(n) < 0.10, 1.22, 1.0)
    L = np.clip(L, 0.006, None)
    # combing: down along the surface + outward from the face centre on the front
    down = np.array([0.0, 0.0, -1.0])
    comb = down - N * (N @ down)[:, None]
    fc = np.array([0.0, -0.45, z_e - 0.10])
    away = P - fc
    away = away - N * np.sum(away * N, axis=1)[:, None]
    comb = normalize_rows(comb + normalize_rows(away) * face_w[:, None] * 1.5 + 1e-6)
    jitter = normalize_rows(rng.normal(0.0, 1.0, (n, 3)))
    D = normalize_rows(N * (0.80 - 0.30 * face_w)[:, None] + comb * 0.85 + jitter * 0.16)
    tip = P + D * L[:, None]
    # clumps: tips converge toward their clump's tip (plush tufts)
    kd = KDTree(CLUMPS)
    cidx = rng.choice(n, size=CLUMPS, replace=False)
    for i, ci in enumerate(cidx):
        kd.insert(Vector(P[ci]), i)
    kd.balance()
    near = np.array([kd.find(Vector(p))[1] for p in P])
    ctip = tip[cidx[near]]
    croot = P[cidx[near]]
    camt = (0.34 + 0.28 * np_smooth(-0.3, 0.6, nz1)) * (1.0 - 0.6 * face_w)
    target = ctip + (P - croot) * 0.45
    tip = tip + (target - tip) * camt[:, None]
    # keep tips above the surface (re-normalise length a little)
    pts = bezier_pts(P, N, tip, L, FUR_PTS)
    radii = np.empty((n, FUR_PTS))
    for i in range(FUR_PTS):
        t = i / (FUR_PTS - 1)
        radii[:, i] = FUR_RAD[0] * (1 - t) ** 0.9 + FUR_RAD[1] * t
    radii *= (0.85 + 0.3 * rng.random(n))[:, None]
    # colours
    base = hexlin(COL_FUR)
    under = hexlin(COL_FUR_UNDER)
    blush = hexlin(COL_BLUSH)
    col = np.tile(base, (n, 1))
    wu = 0.85 * np_smooth(0.36, 0.05, P[:, 2])
    col = col * (1 - wu[:, None]) + under * wu[:, None]
    for bp in blush_pts:
        wb = 0.85 * np.exp(-(np.linalg.norm(P - np.array(bp), axis=1) / (BLUSH_R * 1.05)) ** 2)
        col = col * (1 - wb[:, None]) + blush * wb[:, None]
    col *= (0.90 + 0.12 * (0.5 + 0.5 * nz2) + 0.06 * rng.random(n))[:, None]
    curves = {}
    fur = curves["Fur_Body"] = make_curves("Fur_Body", pts, radii, col, M["FurStrand"], fur_coll)
    print("CHECK fur strands %d of %d (area %.2f m2) in %.1f s" % (n, FUR_N, area, time.time() - t0))

    # ---- short cream fur on the feet (sole pads stay bare)
    for ki, key in enumerate(legs):
        side = 1 if key.endswith("L") else -1
        Pf, Nf, _a = sample_surface(legs[key], 12000 if not QUICK else 4000, 21 + ki)
        li = leg_info[key]
        ok = np.ones(len(Pf), dtype=bool)
        for k, pcen in enumerate(li["pads"]):
            r = 0.070 if k == 0 else 0.037
            ok &= np.linalg.norm(Pf - np.array(pcen), axis=1) > r
        Pf, Nf = Pf[ok], Nf[ok]
        m = len(Pf)
        rngf = np.random.default_rng(31 + side)
        Lf = 0.018 * (0.8 + 0.4 * rngf.random(m))
        Df = normalize_rows(Nf + normalize_rows(rngf.normal(0, 1, (m, 3))) * 0.3)
        tipf = Pf + Df * Lf[:, None]
        ptsf = bezier_pts(Pf, Nf, tipf, Lf, 4)
        rf = np.tile(np.array([0.0022, 0.0016, 0.0010, 0.0004]), (m, 1))
        colf = np.tile(hexlin(COL_PAW), (m, 1)) * (0.93 + 0.07 * rngf.random(m))[:, None]
        curves["Fur_" + key] = make_curves("Fur_" + key, ptsf, rf, colf, M["FurStrand"], fur_coll)

    # ---- pom-pom yarn: radial strands around the dark core
    rngp = np.random.default_rng(9)
    ax = np.array(HAT_AXIS)
    pc = np.array(pom_c)
    ncl = 240 if QUICK else 420
    cdir = normalize_rows(rngp.normal(0, 1, (ncl * 2, 3)))
    cdir = cdir[cdir @ ax > -0.40][:ncl]
    ncl = len(cdir)
    clen = 0.88 + 0.12 * rngp.random(ncl)                  # per-bundle length: soft irregular silhouette
    ctone = 0.80 + 0.32 * rngp.random(ncl)                 # per-bundle tone (yarn plies catch light differently)
    perp = normalize_rows(np.cross(cdir, normalize_rows(rngp.normal(0, 1, (ncl, 3)))))
    m = POM_N
    ci = rngp.integers(0, ncl, m)
    dirs = normalize_rows(cdir[ci] + normalize_rows(rngp.normal(0, 1, (m, 3))) * 0.30)
    dirs = np.where(((dirs @ ax) < -0.45)[:, None], cdir[ci], dirs)
    root = pc + dirs * POM_CORE * 0.55
    Lp = (POM_R - POM_CORE * 0.55) * clen[ci] * (0.86 + 0.18 * rngp.random(m))
    tipp = root + dirs * Lp[:, None]
    ctip = pc + cdir[ci] * (POM_R * clen[ci])[:, None]
    tipp = tipp + (ctip - tipp) * 0.22                     # bundle tips gather (yarn locks, not needles)
    curl = perp[ci] * (0.45 + 0.55 * rngp.random(m))[:, None] - ax[None, :] * 0.20
    tipp = tipp + curl * (Lp * 0.16)[:, None]              # soft curved tips
    ptsp = bezier_pts(root, dirs, tipp, Lp, 5)
    rp = np.tile(np.array([0.0052, 0.0048, 0.0040, 0.0027, 0.0009]), (m, 1)) * (0.8 + 0.4 * rngp.random(m))[:, None]
    colp = np.tile(hexlin(COL_POM), (m, 1)) * (ctone[ci] * (0.92 + 0.12 * rngp.random(m)))[:, None]
    curves["Fur_PomPom"] = make_curves("Fur_PomPom", ptsp, rp, colp, M["PomStrand"], fur_coll)
    print("CHECK pompom strands %d centre %s tip radius %.3f" % (m, tuple(round(c, 3) for c in pom_c), POM_R))

    # ---- landmarks + save
    land = dict(
        version="v4-r4", body_elems=BODY_ELEMS, hat=dict(origin=list(HAT_O), tilt=HAT_TILT, axis=list(HAT_AXIS),
                                                          top_h=top_h, pom_c=list(pom_c), pom_r=POM_R,
                                                          cuff_top_h=CUFF_PROF[-2][0], stripe_h=[STRIPE_PROF[0][0],
                                                                                                 STRIPE_PROF[-1][0]]),
        eyes={t: dict(S=list(eyes[t][1]["S"]), f=list(eyes[t][1]["f"]), hc=eyes[t][1]["hc"]) for t in ("L", "R")},
        mouth_c=list(minfo["S"]), nose_c=list(nose_pt), z_eyes=z_e, cuff_bottom_front_z=zcb,
        arms={t: dict(root=list(Vector((s * ARM_A.x, ARM_A.y, ARM_A.z))), mitt_c=list(Vector((s * MITT_C.x, MITT_C.y,
                                                                                                  MITT_C.z))))
              for s, t in ((1, "L"), (-1, "R"))},
        legs={k: dict(paw_c=list(v["paw_c"]), toe_dir=list(v["toe"]), sole_n=list(v["sole_n"]),
                      pads=[list(p) for p in v["pads"]]) for k, v in leg_info.items()})
    with open(os.path.join(OUT, "mascot_v4_landmarks.json"), "w") as fh:
        json.dump(land, fh, indent=1, default=float)
    allv = [o.matrix_world @ v.co for o in objs.values() for v in o.data.vertices]
    print("CHECK overall x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]" % (
        min(v.x for v in allv), max(v.x for v in allv), min(v.y for v in allv), max(v.y for v in allv),
        min(v.z for v in allv), max(v.z for v in allv)))
    arm = build_armature(objs, curves, coll, land)
    blend = os.path.join(OUT, "mascot_v4.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("SAVED", blend)
    write_ready(blend, objs, arm.name, "rigged v4 (simple armature, game bone names); rest = seated hero pose")
    render_all(objs)
    if not VIEWS or "posetest" in VIEWS:
        leg_pose(True)
        pose_test(arm, True)
        T = Vector((0.0, 0.0, 0.72))
        render_view(os.path.join(PRIVATE, "v4_pose_test.png"),
                    (-5.2 * math.sin(math.radians(40)), -5.2 * math.cos(math.radians(40)), 1.70), T, lens=85.0,
                    samples=24 if QUICK else 48)
        pose_test(arm, False)
        leg_pose(False)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("MASCOT_V4_DONE")


def write_ready(blend, objs, armature, notes):
    ready = dict(
        blend=blend.replace("\\", "/"), collection=COLL_NAME, armature=armature,
        objects=sorted(objs.keys()) + ["Fur_Body", "Fur_Leg.L", "Fur_Leg.R", "Fur_LegFront.L", "Fur_LegFront.R",
                                        "Fur_PomPom"],
        face_controls=("no rig yet: eyes = objects Eye.L/.R + Catchlight.*; blink = scale Eye.* about its centre "
                       "(landmarks json eyes.S) along local Z; mouth = Mouth/Tongue objects" if armature is None else
                       "see controls"),
        bones=BONE_NAMES if armature else [],
        controls=dict(
            head_turn="pose bone 'head' (pivot = ball centre z 0.50): rotation_euler.y = yaw (turn), .x = nod, "
                      ".z = tilt; keep within +-25 deg (the body is one soft mass, no neck)",
            eye_look="pose bones 'eye.L' / 'eye.R' (pivot = eye-cap sphere centre behind the surface): rotation_euler.z "
                     "= look left/right, .x = up/down, +-15 deg (catchlights ride along)",
            blink="pose bones 'eye.L' / 'eye.R': scale.z 1.0 open -> ~0.1 closed (local Z = world up at rest)",
            arm_raise="pose bones 'arm.L' / 'arm.R' (shoulder) rotation_euler.x = raise / lower in the frontal plane, "
                      ".z = forward / back; 'hand.*' bends the paw",
            hat="'hat' / 'hat_tip' / 'pompom' (pom-pom yarn is bone-parented to 'pompom')",
            legs="gameplay W-sit legs 'Leg.*' are skinned to leg.* / foot.*; the front-shot set 'LegFront.*' follows "
                 "'body' (show it with hide_render / hide_viewport like leg_pose() in build_mascot_v4.py)",
            fur="hair curves follow the skinned Body / Leg surfaces via Geometry Nodes 'Deform Curves on Surface' "
                "(Fur_* objects, modifier V4_SurfaceDeform); EEVEE / Cycles render them as strands") if armature
        else {},
        materials="M_Fur, M_HatKnit, M_HatCuff, M_HatStripe, M_PomPom, M_EyeIris, M_EyeHighlight, M_EyeLash, M_Mouth, "
                  "M_Tongue, M_PawPad, M_StarBadge (+ M_V4_FurStrands / M_V4_PomStrands on the hair curves)",
        test_pose="Captures/agents/character/v4_pose_test.png (head 18 deg turn, arms raised/lowered, eye look, "
                  "right blink) - private folder, our render only",
        units="meters, Z up, faces -Y, his left = +X, origin = ground under the body; seated hero pose",
        notes=notes)
    with open(os.path.join(OUT, "READY.json"), "w") as fh:
        json.dump(ready, fh, indent=1)
    print("SAVED", os.path.join(OUT, "READY.json"))


# ------------------------------------------------------------------ renders
HERO_CAM, HERO_PITCH, HERO_VFOV, MASCOT_SCALE, SEAT_DROP = (0.0, 2.566, 1.039), 8.21, 58.0, 0.93, 0.05


def setup_render(samples):
    scene = bpy.context.scene
    C.setup_preview_scene("#2A1B4A", 0.55)
    try:
        scene.eevee.taa_render_samples = samples
    except Exception:
        pass
    for attr, val in (("hair_type", 'STRIP'), ("hair_subdiv", 1)):
        try:
            setattr(scene.render, attr, val)
        except Exception:
            pass
    scene.view_settings.view_transform = 'Standard'
    try:
        scene.view_settings.look = 'None'
    except Exception:
        pass
    return scene


def add_floor():
    me = bpy.data.meshes.new("V4Floor")
    me.from_pydata([(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("V4Floor", me)
    bpy.context.scene.collection.objects.link(ob)
    m, _b = principled("V4Floor", "#3A3F9E", rough=0.35)
    me.materials.append(m)
    return ob


def render_view(path, cam, look, lens=None, vfov=None, res=(900, 900), samples=48, subject=(0.0, 0.0, 0.62)):
    scene = setup_render(samples)
    t, c = Vector(subject), Vector(cam)
    fwd = t - c
    fwd.z = 0.0
    fwd.normalize()
    right = fwd.cross(Vector((0.0, 0.0, 1.0))).normalized()
    up = Vector((0.0, 0.0, 1.0))
    temp = [C._light("V4Key", 'AREA', 430.0, "#FFF0E4", t - fwd * 3.0 - right * 2.2 + up * 2.0, t, 3.0),
            C._light("V4Fill", 'AREA', 230.0, "#D2C8FF", t - fwd * 2.5 + right * 3.0 + up * 1.0, t, 3.5),
            C._light("V4RimP", 'AREA', 700.0, "#FF7FD0", t + fwd * 3.0 + right * 2.0 + up * 2.0, t, 2.0),
            C._light("V4RimV", 'AREA', 600.0, "#9B7BFF", t + fwd * 3.0 - right * 2.2 + up * 1.5, t, 2.0)]
    cd = bpy.data.cameras.new("V4Cam")
    if vfov is not None:
        cd.sensor_fit = 'VERTICAL'
        cd.sensor_height = 24.0
        cd.angle = math.radians(vfov)
    else:
        cd.lens = lens
        cd.sensor_width = 36.0
    co = bpy.data.objects.new("V4Cam", cd)
    scene.collection.objects.link(co)
    co.location = c
    co.rotation_euler = (Vector(look) - c).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = co
    temp.append(co)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = path
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", path)
    for o in temp:
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(d, bpy.types.Camera):
            bpy.data.cameras.remove(d)
        elif isinstance(d, bpy.types.Light):
            bpy.data.lights.remove(d)


FRONT_VIEWS = ("front", "threequarter", "face")


def leg_pose(front):
    """Front shots (opening / celebration) use the legs-forward set; gameplay views the W-sit set."""
    for o in bpy.data.objects:
        nm = o.name
        if "LegFront." in nm:
            o.hide_render = not front
            o.hide_viewport = not front
        elif "Leg." in nm:
            o.hide_render = front
            o.hide_viewport = front


def render_all(objs):
    floor = add_floor()
    T = Vector((0.0, 0.0, 0.72))
    samples = 24 if QUICK else 48
    views = {
        "front": ((0.0, -5.2, 1.75), T, 85.0),
        "threequarter": ((-5.2 * math.sin(math.radians(40)), -5.2 * math.cos(math.radians(40)), 1.70), T, 85.0),
        "side": ((5.2, -0.10, 1.30), T, 85.0),
        "rear": ((0.0, 5.2, 2.00), T, 85.0),
        "face": ((0.0, -3.6, 0.95), Vector((0.0, 0.0, 0.66)), 100.0),
    }
    for name, (cam, look, lens) in views.items():
        if VIEWS and name not in VIEWS:
            continue
        leg_pose(name in FRONT_VIEWS)
        render_view(C.preview_path("SK_Mascot_v4_" + name), cam, look, lens=lens, samples=samples,
                    subject=(0.0, 0.0, 0.62))
    leg_pose(False)
    if not VIEWS or "hero" in VIEWS:
        # Blender hero view: same effective camera as build_mascot_rig.py render_game_view (mascot scaled 0.93 and
        # seated 5 cm lower) -> camera expressed in the unscaled model frame
        cam = Vector(HERO_CAM) / MASCOT_SCALE
        cam.z += SEAT_DROP
        look = cam + Vector((0.0, -math.cos(math.radians(HERO_PITCH)), -math.sin(math.radians(HERO_PITCH))))
        render_view(C.preview_path("SK_Mascot_v4_hero_9x16"), cam, look, vfov=HERO_VFOV, res=(540, 960),
                    samples=samples, subject=(0.0, -0.05, 0.5))
    bpy.data.objects.remove(floor, do_unlink=True)


# ------------------------------------------------------------------ private reference crops (Captures/ only)
REF_CROPS = {   # name: (source relative to Reference/, x0, y0, x1, y1, out_w, out_h)
    "ref_front_03": ("intro_handoff/03_Approved_Mascot_Front.jpg", 420, 160, 840, 580, 600, 600),
    "ref_threequarter_05": ("intro_handoff/05_Approved_Mascot_ThreeQuarter.jpg", 330, 200, 770, 640, 600, 600),
    "ref_rear_04": ("intro_handoff/04_Approved_Mascot_Back.jpg", 420, 140, 860, 580, 600, 600),
    "ref_hero_3s_9x16": ("frames4k_720/f_03.00s.png", 437, 0, 842, 720, 540, 960),
}


def resize_np(img, w, h):
    """Bilinear resize of an (H, W, C) float array."""
    H, W = img.shape[:2]
    ys = (np.arange(h) + 0.5) * H / h - 0.5
    xs = (np.arange(w) + 0.5) * W / w - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, H - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 1)
    y1, x1 = np.clip(y0 + 1, 0, H - 1), np.clip(x0 + 1, 0, W - 1)
    fy, fx = np.clip(ys - y0, 0, 1)[:, None, None], np.clip(xs - x0, 0, 1)[None, :, None]
    a, b, c, d = img[y0][:, x0], img[y0][:, x1], img[y1][:, x0], img[y1][:, x1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def export_ref_crops():
    out_dir = os.path.join(PRIVATE, "ref")
    os.makedirs(out_dir, exist_ok=True)
    for name, (src, x0, y0, x1, y1, w, h) in REF_CROPS.items():
        im = bpy.data.images.load(os.path.join(REF, src), check_existing=False)
        W, H = im.size
        px = np.empty(W * H * 4, dtype=np.float32)
        im.pixels.foreach_get(px)
        arr = px.reshape(H, W, 4)[::-1]                       # top-down
        crop = resize_np(arr[y0:y1, x0:x1].astype(np.float64), w, h)
        out = bpy.data.images.new(name, w, h, alpha=False)
        o = np.ones((h, w, 4), dtype=np.float32)
        o[..., :3] = crop[::-1, :, :3]
        out.pixels.foreach_set(o.ravel())
        out.filepath_raw = os.path.join(out_dir, name + ".png")
        out.file_format = 'PNG'
        out.save()
        print("PREVIEW private ref crop", out.filepath_raw)


if os.environ.get("BWK_V4_MODE", "") == "refs":
    export_ref_crops()
else:
    main()
