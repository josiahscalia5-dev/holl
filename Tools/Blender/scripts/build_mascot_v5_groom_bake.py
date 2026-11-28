"""Bubble Wash Kingdom - SK_Mascot_v5 body GROOM + BAKE (S2 pass 10h, owner 2026-11-27 17:20 METHOD).

Owner: "groom real fur + knit hat in Blender, BAKE them into textures for a smooth plush body in Unity (no procedural cone
fur)". This script grooms the v5 game body (Tools/Blender/work/mascot_v4/mascot_v5_game.blend, written by
build_mascot_v4.py BWK_V4_MODE=gamemodel_v5) with ~120k fine plush strands and bakes them with Cycles (selected-to-active,
cage extrusion ~ the pile height) into the body's OWN equirect UV space (UV0 'UVMap' u / 0.92 = one revolution, v 0..1):

  Assets/BubbleWashKingdom/Art/Textures/Characters/T_MascotV5_GroomAlbedo.png   RGB = strand albedo (sRGB), A = groom AO
  Assets/BubbleWashKingdom/Art/Textures/Characters/T_MascotV5_GroomNormal.png   tangent-space normal (OpenGL +Y, high-passed)

Groom: dense soft pile 1.6-3.2 cm, combed down / slightly outward like the approved 3.00 s rear view, gentle clumping
(never cones / locks / scales), strands are thin V-profile ribbons (3 verts per ring: the smooth normals give round
fibres), warm rose-salmon roots -> light pink tips, cream-pink toward the seat. The groom itself never ships: only the
two baked maps go to Unity (BWK_Fur _GroomMix path, MaterialLibrary.Character.cs M_Fur_v5).
Proof renders (private): Captures/agents/character/screen_S2_p10h/blender_{front,side,rear}.png = groomed high-poly
(left) next to the baked smooth low-poly (right), same lights.

Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_mascot_v5_groom_bake.py p10h_groom
Env: BWK_GROOM_N (strands, 120000), BWK_GROOM_W / _H (map size, 2048 x 1024), BWK_GROOM_RENDERS (1 = proof renders).
"""
import json
import math
import os
import struct
import sys
import time
import zlib

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT = r"C:/Users/josia/thanksgiving"
SRC = ROOT + "/Tools/Blender/work/mascot_v4/mascot_v5_game.blend"
SRC_JSON = ROOT + "/Tools/Blender/work/mascot_v4/mascot_v5_game.json"
TEX_DIR = ROOT + "/Assets/BubbleWashKingdom/Art/Textures/Characters"
PREV_DIR = ROOT + "/Captures/agents/character/" + os.environ.get("BWK_GROOM_OUT", "screen_S2_p10i")
N = int(os.environ.get("BWK_GROOM_N", "120000"))
W = int(os.environ.get("BWK_GROOM_W", "2048"))
H = int(os.environ.get("BWK_GROOM_H", "2048"))
RENDERS = os.environ.get("BWK_GROOM_RENDERS", "1") == "1"
U_PERIOD = 0.92            # body UV u span of one revolution (build_mascot_v4.py body_uv: pi * 0.46 / (pi / 2))
EXTRUDE = 0.040            # bake cage extrusion (m) > tallest groom point above the skin
LAMBERT_R = 0.985          # p10i: seam-free groom layout = Lambert azimuthal equal-area disk centred on the SEAT pole
                           # (from UV0: phi = 2 pi u / 0.92, colatitude = pi v); the only cut (disk rim) = the crown pole
                           # under the beanie. BWK_Fur computes the same per vertex (_GroomMix path).
SEED = 1027

# colours: LINEAR albedo (picked in sRGB, decoded). Under the tunnel's violet light the p10g salmon coat rendered the
# reference hue (R2 midback a45 b-5 vs 45 / -3); the strands carry depth: deeper rose roots, warm pink body, light tips.
def srgb(h):
    c = np.array([int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# p10i (lead 18:45: 10h albedo mean 228/116/112 = coral): ROSE pink, deeper rose roots, light pink tips, cream-pink seat.
# Unity's violet tunnel light lifts blue (gate s2p10h: albedo #FA8682 rendered 203/106/162 vs reference 207/103/144),
# so blue stays near green here; M_Fur_v5 _GroomTint fine-tunes the rendered hue against the reference boxes.
SKIN = srgb("#9E3E56")
ROOTC = srgb("#C24E66")
MIDC = srgb("#F28482")
TIPC = srgb("#FAC0BC")
SEATC = srgb("#F2CDC8")    # cream-pink toward the seat (approved lower back is lighter cream-pink)
SEAT_V0, SEAT_V1 = 0.30, 0.46   # body v (= polar angle / pi from the seat pole) of the seat blend (BWK_Fur _SeatRange)


def log(*a):
    print("CHECK groom", *a, flush=True)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def vnoise3(P, scale, seed):
    """Cheap smooth 3D value noise (numpy, trilinear on a hashed lattice), values 0..1."""
    q = P * scale + seed * 17.123
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3.0 - 2.0 * f)

    def h(ix, iy, iz):
        n = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0
    out = 0.0
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out


def normalize(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-9)


def write_png(path, arr):
    """arr uint8 (h, w, c) top row first."""
    h, w, c = arr.shape
    raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(h))
    ct = {3: 2, 4: 6}[c]

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def lin2srgb(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


# ------------------------------------------------------------------------------------------------ scene
t0 = time.time()
bpy.ops.wm.open_mainfile(filepath=SRC)
with open(SRC_JSON) as fh:
    CON = json.load(fh)
BODY_C = np.array(CON["BODY_C"])
HAT_AX = np.array(CON["HAT_AXIS"]) / np.linalg.norm(CON["HAT_AXIS"])
CUFF_A = float(CON["CUFF_BOTTOM_A"])
scene = bpy.context.scene
body = bpy.data.objects["Body"]
for o in list(bpy.data.objects):
    if o is not body:
        o.hide_render = True
        o.hide_set(True)
coll = scene.collection

me0 = body.data
nv = len(me0.vertices)
CO = np.zeros(nv * 3); me0.vertices.foreach_get("co", CO); CO = CO.reshape(-1, 3)
NO = np.zeros(nv * 3); me0.vertices.foreach_get("normal", NO); NO = normalize(NO.reshape(-1, 3))
me0.calc_loop_triangles()
TRI = np.zeros(len(me0.loop_triangles) * 3, np.int64); me0.loop_triangles.foreach_get("vertices", TRI); TRI = TRI.reshape(-1, 3)
log("body verts %d tris %d" % (nv, len(TRI)))

# ------------------------------------------------------------------------------------------------ roots
rng = np.random.default_rng(SEED)
A, B, Cc = CO[TRI[:, 0]], CO[TRI[:, 1]], CO[TRI[:, 2]]
area = 0.5 * np.linalg.norm(np.cross(B - A, Cc - A), axis=1)


def sample(n):
    t = rng.choice(len(TRI), size=n, p=area / area.sum())
    r1, r2 = np.sqrt(rng.random(n)), rng.random(n)
    w0, w1, w2 = 1 - r1, r1 * (1 - r2), r1 * r2
    P = A[t] * w0[:, None] + B[t] * w1[:, None] + Cc[t] * w2[:, None]
    Nn = normalize(NO[TRI[t, 0]] * w0[:, None] + NO[TRI[t, 1]] * w1[:, None] + NO[TRI[t, 2]] * w2[:, None])
    return P, Nn


def hat_alpha(P):
    d = normalize(P - BODY_C)
    return np.degrees(np.arccos(np.clip(d @ HAT_AX, -1, 1)))


P, NR = sample(int(N * 1.25))
keep = hat_alpha(P) > CUFF_A - 14.0           # p10i: strands reach 14 deg under the cuff (no jagged hat line)
P, NR = P[keep][:N], NR[keep][:N]
n = len(P)
log("strands %d (area %.2f m2)" % (n, area.sum()))


def comb_dir(P, NR, seed):
    """Combed plush direction in the tangent plane: down the body, a little outward to the sides, slowly swirling."""
    down = np.array([0.0, 0.0, -1.0])
    t = down[None, :] - NR * (NR @ down)[:, None]
    # outward toward the flanks, smooth through the back / front centre line (a sign() flip combed a visible centre parting)
    side = np.zeros_like(P); side[:, 0] = np.tanh((P[:, 0] - BODY_C[0]) / 0.14) * 0.22
    side -= NR * np.sum(side * NR, axis=1, keepdims=True)
    radial = P - BODY_C; radial[:, 2] = 0.0
    radial -= NR * np.sum(radial * NR, axis=1, keepdims=True)
    lt = np.linalg.norm(t, axis=1, keepdims=True)
    t = np.where(lt > 0.25, t, t + normalize(radial) * (0.25 - lt))   # bottom pole: outward
    t = normalize(t + side)
    ang = (vnoise3(P, 6.0, seed) - 0.5) * math.radians(70.0) + (vnoise3(P, 22.0, seed + 3) - 0.5) * math.radians(30.0)
    bt = np.cross(NR, t)
    return normalize(t * np.cos(ang)[:, None] + bt * np.sin(ang)[:, None])


# ------------------------------------------------------------------------------------------------ strands
def strands(P, NR, L, lift0, seed):
    T = comb_dir(P, NR, seed)
    lifts = (lift0, lift0 * 0.62, lift0 * 0.34)
    pts = [P]
    cur = P.copy()
    for k, lf in enumerate(lifts):
        d = normalize(NR * lf[:, None] + T * (1.0 - lf)[:, None])
        cur = cur + d * (L / 3.0)[:, None]
        pts.append(cur)
    return np.stack(pts, axis=1), T          # (n, 4, 3)


lnoise = vnoise3(P, 9.0, 5) * 0.7 + vnoise3(P, 31.0, 9) * 0.3
L = 0.018 + 0.016 * lnoise + rng.normal(0.0, 0.0018, n)
L = np.clip(L, 0.012, 0.038)
face = smoothstep(-0.18, -0.32, P[:, 1]) * smoothstep(0.30, 0.42, P[:, 2]) * smoothstep(0.90, 0.80, P[:, 2])
L *= 1.0 - 0.45 * face                          # short velvet pile on the face (eyes / smile sit on it)
vpol = np.degrees(np.arccos(np.clip(normalize(P - BODY_C)[:, 2] * -1.0, -1, 1))) / 180.0   # 0 = seat pole
seat = 1.0 - smoothstep(SEAT_V0, SEAT_V1, vpol)
L *= 1.0 - 0.25 * seat
lift0 = np.clip(0.42 + (vnoise3(P, 14.0, 11) - 0.5) * 0.30 + rng.normal(0, 0.06, n), 0.25, 0.78)
S, T = strands(P, NR, L, lift0, 21)

# gentle clumping: each strand's tip leans toward its clump guide (~2 cm clumps, strength 0.15-0.45, never closed locks)
nc = max(500, n // 100)        # p10i: ~1200 soft clumps (~5 cm) instead of 4670 (speckle)
ci = rng.choice(n, nc, replace=False)
kd = KDTree(nc)
for j, idx in enumerate(ci):
    kd.insert(Vector(P[idx]), j)
kd.balance()
near = np.array([kd.find(Vector(p))[1] for p in P], np.int64)
cs = np.clip(0.58 + (vnoise3(P, 5.0, 17) - 0.5) * 0.3 + rng.normal(0, 0.05, n), 0.35, 0.80)
clen = 0.85 + 0.30 * rng.random(nc)            # p10i: every clump has its own pile length (soft irregular outline)
S = S[:, :1] + (S - S[:, :1]) * clen[near][:, None, None]
G = S[ci[near]]
for k in (1, 2, 3):
    f = cs * (k / 3.0) ** 1.6
    target = G[:, k] + (S[:, 0] - G[:, 0]) * (1.0 - 0.75 * (k / 3.0))
    S[:, k] = S[:, k] + (target - S[:, k]) * f[:, None]
# keep every point outside the skin (clump pulls / combing can dip below on convex parts)
for k in (1, 2, 3):
    h = np.sum((S[:, k] - S[:, 0]) * NR, axis=1)
    S[:, k] += NR * np.maximum(0.0006 * k - h, 0.0)[:, None]
log("pile length %.1f-%.1f mm (mean %.1f), clumps %d, max height %.1f mm" % (
    L.min() * 1e3, L.max() * 1e3, L.mean() * 1e3, nc, np.max(np.sum((S[:, 3] - S[:, 0]) * NR, axis=1)) * 1e3))

# strand colours (per point): root -> mid -> tip, per-strand / per-clump tone, cream-pink toward the seat
dcl = np.linalg.norm(P - P[ci[near]], axis=1)
cfall = np.clip(1.0 - dcl / 0.035, 0.0, 1.0)      # 1 at the clump centre -> 0 at its parting
tone = np.clip(1.0 + rng.normal(0, 0.025, n) + (vnoise3(P, 4.0, 23) - 0.5) * 0.10 + (rng.random(nc)[near] - 0.5) * 0.10
               + (cfall - 0.5) * 0.10, 0.82, 1.15)
ramp = [ROOTC, ROOTC * 0.35 + MIDC * 0.65, MIDC, TIPC]
cols = np.zeros((n, 4, 4))
for k in range(4):
    c = ramp[k][None, :] * tone[:, None]
    sk = smoothstep(0.0, 1.0, seat)[:, None] * (0.55 + 0.45 * k / 3.0)     # cream-pink seat, strongest at the tips
    cols[:, k, :3] = c * (1.0 - sk) + SEATC[None, :] * tone[:, None] * sk
cols[:, :, 3] = 1.0

# ribbon mesh: V profile (left, raised middle, right) per ring, 2 quads per segment
wid = np.array([0.0048, 0.0042, 0.0030, 0.0014])   # p10i: wider soft strands (6 spp speckle)
Vv = np.zeros((n, 4, 3, 3))
for k in range(4):
    d = S[:, min(k + 1, 3)] - S[:, max(k - 1, 0)]
    d = normalize(d)
    s = normalize(np.cross(d, NR))
    r = normalize(np.cross(s, d))
    r *= np.sign(np.sum(r * NR, axis=1))[:, None]
    w = wid[k] * (0.85 + 0.3 * tone[:, None] - 0.15)
    Vv[:, k, 0] = S[:, k] - s * w * 0.5
    Vv[:, k, 1] = S[:, k] + r * w * 0.42
    Vv[:, k, 2] = S[:, k] + s * w * 0.5
verts = Vv.reshape(-1, 3)
base = (np.arange(n) * 12)[:, None]
quads = []
for k in range(3):
    for j in range(2):
        a = k * 3 + j
        quads.append(np.stack([a, a + 1, a + 4, a + 3], axis=0))
Q = (base[:, None, :] + np.array(quads)[None, :, :]).reshape(-1, 4)
gm = bpy.data.meshes.new("GroomMesh")
gm.vertices.add(len(verts)); gm.vertices.foreach_set("co", verts.ravel())
gm.loops.add(Q.size); gm.loops.foreach_set("vertex_index", Q.ravel())
gm.polygons.add(len(Q)); gm.polygons.foreach_set("loop_start", np.arange(0, Q.size, 4))
gm.update(calc_edges=True)
try:
    gm.polygons.foreach_set("use_smooth", np.ones(len(Q), bool))
except Exception:
    gm.shade_smooth()
ca = gm.color_attributes.new("gcol", 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set("color", np.repeat(cols, 3, axis=1).reshape(-1, 4).ravel())
# depth "AO": how deep in the pile the baked point lies (skin 0.30, strand root 0.48 -> tip 1.0) = soft partings between
# clumps and darker roots; baked as a second colour pass (a Cycles AO bake would see the coincident low-poly as a lid)
dep = 0.64 + 0.36 * (np.arange(4) / 3.0) ** 0.8
dcol = np.ones((n, 4, 4)); dcol[:, :, :3] = dep[None, :, None]
da = gm.color_attributes.new("gdep", 'FLOAT_COLOR', 'POINT')
da.data.foreach_set("color", np.repeat(dcol, 3, axis=1).reshape(-1, 4).ravel())
gm.update()
groom = bpy.data.objects.new("Groom", gm)
coll.objects.link(groom)
log("groom mesh %d verts %d tris (%.0f s)" % (len(verts), len(Q) * 2, time.time() - t0))

# skin under the strands (same surface, 0.4 mm inside): rays that pass between strands see the deep rose skin
skin = body.copy(); skin.data = body.data.copy(); skin.name = "GroomSkin"
coll.objects.link(skin)
for v in skin.data.vertices:
    v.co = v.co - v.normal * 0.0004
skin.hide_render = False; skin.hide_set(False)
body.hide_render = True; body.hide_set(True)   # the original body never occludes / renders (copies do the work)


def mat_attr(name, rough=0.55, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "gcol"
    nt.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 0.25
        bsdf.inputs["Sheen Weight"].default_value = sheen
    except KeyError:
        pass
    return m


def mat_flat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m


groom.data.materials.append(mat_attr("M_GroomStrand", sheen=0.2))
skin.data.materials.clear()
skin.data.materials.append(mat_flat("M_GroomSkin", SKIN))

# ------------------------------------------------------------------------------------------------ bake proxy
bake = body.copy(); bake.data = body.data.copy(); bake.name = "BakeBody"
coll.objects.link(bake)
bake.hide_render = False; bake.hide_set(False)
bme = bake.data
uv0 = bme.uv_layers["UVMap"]
buv = bme.uv_layers.new(name="BakeUV")
arr = np.zeros(len(bme.loops) * 2); uv0.data.foreach_get("uv", arr); arr = arr.reshape(-1, 2)
uv_v = arr[:, 1].copy()
phi = 2.0 * np.pi * arr[:, 0] / U_PERIOD
rr = LAMBERT_R * np.sin(0.5 * np.pi * np.clip(uv_v, 0.0, 1.0))
arr = np.stack([0.5 + 0.5 * rr * np.cos(phi), 0.5 + 0.5 * rr * np.sin(phi)], axis=1)
buv.data.foreach_set("uv", arr.ravel())
log("bake proxy: Lambert layout from UV0 (v range %.3f-%.3f, u range %.3f-%.3f)" % (uv_v.min(), uv_v.max(), phi.min() / 6.2832 * U_PERIOD, phi.max() / 6.2832 * U_PERIOD))
bme.uv_layers["BakeUV"].active = True
bme.uv_layers["BakeUV"].active_render = True
bm_mat = bpy.data.materials.new("M_BakeTarget"); bm_mat.use_nodes = True
bme.materials.clear(); bme.materials.append(bm_mat)
img_node = bm_mat.node_tree.nodes.new("ShaderNodeTexImage")
bm_mat.node_tree.nodes.active = img_node
img_node.select = True

# ------------------------------------------------------------------------------------------------ bake
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
try:
    scene.cycles.use_denoising = False
except AttributeError:
    pass
if scene.world is None:
    scene.world = bpy.data.worlds.new("W")
scene.world.light_settings.distance = 0.012
bk = scene.render.bake
bk.use_selected_to_active = True
bk.cage_extrusion = EXTRUDE
try:
    bk.max_ray_distance = 0.08
except AttributeError:
    pass
bk.margin = 16
try:
    bk.margin_type = 'EXTEND'
except (AttributeError, TypeError):
    pass
bk.use_clear = True
bk.target = 'IMAGE_TEXTURES'
for o in bpy.context.view_layer.objects:
    o.select_set(False)
groom.select_set(True); skin.select_set(True); bake.select_set(True)
bpy.context.view_layer.objects.active = bake


def new_img(name, data):
    im = bpy.data.images.new(name, W, H, alpha=True, float_buffer=True)
    if data:
        im.colorspace_settings.name = 'Non-Color'
    img_node.image = im
    return im


def pixels(im):
    a = np.zeros(W * H * 4, np.float32)
    im.pixels.foreach_get(a)
    return a.reshape(H, W, 4)[::-1]          # top row first


def run_bake(kind, samples, **kw):
    scene.cycles.samples = samples
    t = time.time()
    bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=EXTRUDE, margin=16, use_clear=True, **kw)
    log("bake %s %dx%d %d spp %.0f s" % (kind, W, H, samples, time.time() - t))


im_col = new_img("bake_col", False)
bk.use_pass_direct = False; bk.use_pass_indirect = False; bk.use_pass_color = True
run_bake('DIFFUSE', 16, pass_filter={'COLOR'})
COL = pixels(im_col)
im_nrm = new_img("bake_nrm", True)
bk.normal_space = 'TANGENT'
bk.normal_r, bk.normal_g, bk.normal_b = 'POS_X', 'POS_Y', 'POS_Z'
run_bake('NORMAL', 12, normal_space='TANGENT')
NRM = pixels(im_nrm)
im_ao = new_img("bake_ao", True)
gattr = next(nd for nd in groom.data.materials[0].node_tree.nodes if nd.type == "ATTRIBUTE")
gattr.attribute_name = "gdep"
sk_bsdf = next(nd for nd in skin.data.materials[0].node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
sk_bsdf.inputs["Base Color"].default_value = (0.52, 0.52, 0.52, 1.0)
run_bake('DIFFUSE', 12, pass_filter={'COLOR'})
AO = pixels(im_ao)
gattr.attribute_name = "gcol"
sk_bsdf.inputs["Base Color"].default_value = (SKIN[0], SKIN[1], SKIN[2], 1.0)

# ------------------------------------------------------------------------------------------------ post + write
os.makedirs(TEX_DIR, exist_ok=True)


def blur(x, r):
    """Separable box blur x3 (~gaussian), wraps in u (the map is periodic around the body), clamps in v."""
    for _ in range(3):
        c = np.cumsum(np.concatenate([np.repeat(x[:, :1], r + 1, 1), x, np.repeat(x[:, -1:], r, 1)], axis=1), axis=1)
        x = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
        p = np.concatenate([np.repeat(x[:1], r + 1, 0), x, np.repeat(x[-1:], r, 0)], axis=0)
        c = np.cumsum(p, axis=0)
        x = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
    return x


def pushpull(img, valid):
    """Fill invalid texels from the valid ones (mip pyramid of weighted sums, coarse to fine)."""
    cs, ws = [img * valid[:, :, None]], [valid.astype(np.float64)]
    while min(cs[-1].shape[:2]) > 2:
        c, w = cs[-1], ws[-1]
        cs.append(c[0::2, 0::2] + c[1::2, 0::2] + c[0::2, 1::2] + c[1::2, 1::2])
        ws.append(w[0::2, 0::2] + w[1::2, 0::2] + w[0::2, 1::2] + w[1::2, 1::2])
    est = cs[-1] / np.maximum(ws[-1], 1e-9)[:, :, None]
    for c, w in zip(reversed(cs[:-1]), reversed(ws[:-1])):
        up = np.repeat(np.repeat(est, 2, 0), 2, 1)
        est = np.where((w > 0)[:, :, None], c / np.maximum(w, 1e-9)[:, :, None], up)
    return np.where(valid[:, :, None], img, est)
valid = COL[:, :, 3] > 0.5
log("valid texels %.1f %%" % (100.0 * valid.mean()))
COL = pushpull(COL, valid); NRM = pushpull(NRM, valid); AO = pushpull(AO, valid)
nxy = NRM[:, :, :2] * 2.0 - 1.0
nxy_hp = blur(nxy, 1) - blur(nxy, 24)    # p10i: + 1 px soft blur (no per-texel speckle)               # high-pass: keep the strand / clump relief, drop the global comb tilt
nz = np.sqrt(np.clip(1.0 - np.sum(nxy_hp ** 2, axis=2), 0.05, 1.0))
nrm8 = np.concatenate([(np.clip(nxy_hp * 0.5 + 0.5, 0, 1)), (nz * 0.5 + 0.5)[:, :, None]], axis=2)
ao = AO[:, :, 0]
ao = np.clip(ao, 0, 1)
col = blur(COL[:, :, :3], 1)                 # p10i: soft 1 px blur = plush, not speckle
ao = blur(ao, 1)
alb8 = np.concatenate([lin2srgb(col), ao[:, :, None]], axis=2)
write_png(TEX_DIR + "/T_MascotV5_GroomAlbedo.png", np.round(alb8 * 255).astype(np.uint8))
write_png(TEX_DIR + "/T_MascotV5_GroomNormal.png", np.round(nrm8 * 255).astype(np.uint8))
lin = col.reshape(-1, 3)
log("albedo mean sRGB %s  AO mean %.2f p5 %.2f  normal xy std %.3f (raw tilt mean %.3f %.3f)" % (
    np.round(lin2srgb(lin.mean(0)) * 255).astype(int), ao.mean(), np.percentile(ao, 5), nxy_hp.std(),
    nxy[:, :, 0].mean(), nxy[:, :, 1].mean()))
log("EXPORTED", TEX_DIR + "/T_MascotV5_GroomAlbedo.png", TEX_DIR + "/T_MascotV5_GroomNormal.png", "%.0f s" % (time.time() - t0))
# private inspection copies (shrunk)
os.makedirs(PREV_DIR, exist_ok=True)
write_png(PREV_DIR + "/groom_maps_albedo_ao_normal.png", np.round(np.concatenate([
    lin2srgb(col)[::2, ::2], np.repeat(ao[::2, ::2, None], 3, 2), nrm8[::2, ::2]], axis=0) * 255).astype(np.uint8))

# ------------------------------------------------------------------------------------------------ proof renders
if RENDERS:
    # baked low-poly material: albedo x AO + tangent normal map + soft sheen (what BWK_Fur's groom path does)
    def load_tex(path, data):
        im = bpy.data.images.load(path)
        if data:
            im.colorspace_settings.name = 'Non-Color'
        return im
    lm = bpy.data.materials.new("M_BakedPlush"); lm.use_nodes = True
    nt = lm.node_tree
    bsdf = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "BakeUV"
    ta = nt.nodes.new("ShaderNodeTexImage"); ta.image = load_tex(TEX_DIR + "/T_MascotV5_GroomAlbedo.png", False)
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = load_tex(TEX_DIR + "/T_MascotV5_GroomNormal.png", True)
    for t_ in (ta, tn):
        t_.extension = 'REPEAT'
        nt.links.new(uvn.outputs["UV"], t_.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(ta.outputs["Color"], mul.inputs[6])
    nt.links.new(ta.outputs["Alpha"], mul.inputs[7])
    nt.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.uv_map = "BakeUV"; nm.inputs["Strength"].default_value = 1.0
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.6
    try:
        bsdf.inputs["Sheen Weight"].default_value = 0.35
        bsdf.inputs["Specular IOR Level"].default_value = 0.25
    except KeyError:
        pass
    ta.image.alpha_mode = 'CHANNEL_PACKED'
    bme.materials.clear(); bme.materials.append(lm)
    low = bake
    # lights + cameras
    scene.world.use_nodes = True
    bg = next(nd for nd in scene.world.node_tree.nodes if nd.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.05, 0.035, 0.08, 1.0); bg.inputs["Strength"].default_value = 1.0
    # p10i: lights tinted like the S2 tunnel (lavender key, pink fill, violet back rim) - the game never lights him white
    for nm_, loc, en, lc in (("Key", (-1.6, -2.0, 2.6), 520.0, (0.93, 0.84, 1.0)), ("Fill", (2.2, -1.2, 1.2), 220.0, (1.0, 0.80, 0.88)),
                             ("Back", (0.5, 2.4, 2.2), 420.0, (0.80, 0.72, 1.0)), ("Key2", (1.6, 2.4, 2.6), 380.0, (0.93, 0.84, 1.0))):
        ld = bpy.data.lights.new(nm_, 'AREA'); ld.energy = en; ld.size = 1.5; ld.color = lc
        lo = bpy.data.objects.new(nm_, ld); lo.location = loc; coll.objects.link(lo)
        lo.rotation_euler = (Vector((0.0, 0.0, 0.55)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new("Cam"); cd.type = 'ORTHO'; cd.ortho_scale = 1.42
    cam = bpy.data.objects.new("Cam", cd); coll.objects.link(cam); scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = 420
    scene.render.film_transparent = False
    scene.cycles.samples = 20
    try:
        scene.cycles.use_denoising = True
        scene.cycles.time_limit = 40.0
    except AttributeError:
        pass
    scene.view_settings.view_transform = 'Standard'
    tgt = Vector((0.0, 0.0, 0.50))
    flat_fur = mat_flat("M_ProofFur", MIDC * 0.85)
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name in ("Body", "Groom", "GroomSkin", "BakeBody"):
            continue
        o.hide_render = False
        for i, m in enumerate(o.data.materials):
            if m is not None and m.name.startswith("M_Fur"):
                o.data.materials[i] = flat_fur
    views = {"rear": Vector((0.0, 3.0, 0.62)), "side": Vector((3.0, 0.0, 0.62)), "front": Vector((0.0, -3.0, 0.62))}
    cd.ortho_scale = 1.9; tgt = Vector((0.0, 0.0, 0.62))
    for vn, pos in views.items():
        cam.location = tgt + pos
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        tiles = []
        for mode in ("groom", "baked"):
            groom.hide_render = skin.hide_render = (mode != "groom")
            low.hide_render = (mode != "baked")
            path = PREV_DIR + "/_tmp_%s_%s.png" % (vn, mode)
            scene.render.filepath = path
            t = time.time()
            bpy.ops.render.render(write_still=True)
            log("render %s %s %.0f s" % (vn, mode, time.time() - t))
            im = bpy.data.images.load(path)
            a = np.zeros(420 * 420 * 4, np.float32); im.pixels.foreach_get(a)
            tiles.append(a.reshape(420, 420, 4)[::-1, :, :3])
            bpy.data.images.remove(im)
            os.remove(path)
        sep = np.full((420, 8, 3), 0.2)
        out = np.concatenate([tiles[0], sep, tiles[1]], axis=1)
        write_png(PREV_DIR + "/blender_%s_groom_vs_baked.png" % vn, np.round(np.clip(out, 0, 1) * 255).astype(np.uint8))
        log("PREVIEW", PREV_DIR + "/blender_%s_groom_vs_baked.png" % vn)
log("DONE %.0f s" % (time.time() - t0))
print("GROOM_BAKE_DONE")
