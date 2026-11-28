"""S2 Tunnel v1 - WATER / FX module (water-fx-artist). Contract: apply(ctx) - runs after s2v1_materials, before s2v1_lighting.

Works on the Unity context collections (already in Blender world space):
  CTX_water   : slide modules (material slots M_Water | M_RailBand_r8 | M_RailTube_r8 | M_SlideShell) -> water + glossy rails
  CTX_foam    : foam banks (M_Foam_v2, M_Foam_v2_Shade, M_Foam) -> soft subsurface soap foam
  CTX_bubbles : soap bubbles (M_Bubble) -> iridescent thin film; glass pipes (M_Glass / M_PipeWater*) -> glass + glowing liquid
  CTX_pickups : coins (M_Coin) -> polished gold, gems (M_Gem) -> violet crystal
  CTX_mascot  : CrownL / CrownR (M_FX_Milk_v3) -> milky translucent splash crowns + rounded tips + detached droplets (new objects
                in collection S2V1_WFX), mascot bubbles (M_Bubble), and an untextured mascot -> neutral rose plush placeholder
                (the character team owns the real mascot)
  CTX_context : chevrons (M_Arrow) -> glowing cyan boost chevrons on the water (they sit on the water surface)
Never edits shared materials in place: every look is a NEW material WFX_* assigned to the slots of the objects above only.
Everything is procedural (no reference pixels). Unity transfer notes: Captures/s2v1/NOTES_water.md.
"""
import math
import random

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

LOG = "CHECK water"


# ----------------------------------------------------------------------------------------------------------- helpers
def srgb(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (lin[0], lin[1], lin[2], a)


def base_name(mat):
    return mat.name.split(".")[0] if mat else ""


def coll_objs(name):
    c = bpy.data.collections.get(name)
    return [o for o in c.all_objects if o.type == "MESH"] if c else []


def setin(node, name, val):
    s = node.inputs.get(name)
    if s is not None:
        try:
            s.default_value = val
        except Exception:
            pass
    return s


class NT:
    """Tiny node-tree builder."""

    def __init__(self, name, render="DITHERED"):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        for n in list(self.t.nodes):
            self.t.nodes.remove(n)
        self.out = self.t.nodes.new("ShaderNodeOutputMaterial")
        self.out.location = (900, 0)
        try:
            m.surface_render_method = render
        except Exception:
            pass
        self.x = 0

    def n(self, typ, **inputs):
        nd = self.t.nodes.new(typ)
        nd.location = (self.x, -len(self.t.nodes) * 40)
        for k, v in inputs.items():
            setin(nd, k, v)
        return nd

    def link(self, a, b):
        self.t.links.new(a, b)

    def math(self, op, a, b=None, clamp=False):
        nd = self.n("ShaderNodeMath")
        nd.operation = op
        nd.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                self.link(v, nd.inputs[i])
        return nd.outputs[0]

    def mix(self, a, b, fac, blend="MIX"):
        nd = self.n("ShaderNodeMix")
        nd.data_type = "RGBA"
        nd.blend_type = blend
        for sock, v in ((nd.inputs[0], fac), (nd.inputs[6], a), (nd.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = v
            else:
                self.link(v, sock)
        return nd.outputs[2]

    def ramp(self, fac, stops, interp="LINEAR"):
        nd = self.n("ShaderNodeValToRGB")
        cr = nd.color_ramp
        cr.interpolation = interp
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        cr.elements[0].position, cr.elements[0].color = stops[0]
        for p, c in stops[1:]:
            e = cr.elements.new(p)
            e.color = c
        if isinstance(fac, (int, float)):
            nd.inputs[0].default_value = fac
        else:
            self.link(fac, nd.inputs[0])
        return nd

    def noise(self, vec, scale, detail=2.0, rough=0.5, distortion=0.0):
        nd = self.n("ShaderNodeTexNoise")
        try:
            nd.noise_dimensions = "3D"
        except Exception:
            pass
        setin(nd, "Scale", scale); setin(nd, "Detail", detail); setin(nd, "Roughness", rough)
        setin(nd, "Distortion", distortion)
        self.link(vec, nd.inputs["Vector"])
        return nd.outputs["Fac"]

    def vec(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                self.link(v, nd.inputs[i])
        return nd.outputs[0]

    def attr(self, name, kind="GEOMETRY"):
        nd = self.n("ShaderNodeAttribute")
        nd.attribute_type = kind
        nd.attribute_name = name
        return nd

    def sep(self, v):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.link(v, nd.inputs[0])
        return nd.outputs

    def smooth(self, x, a, b):
        """smoothstep(a, b, x) as a Map Range node (clamped)."""
        nd = self.n("ShaderNodeMapRange")
        nd.interpolation_type = "SMOOTHSTEP"
        nd.clamp = True
        nd.inputs["From Min"].default_value = a
        nd.inputs["From Max"].default_value = b
        self.link(x, nd.inputs["Value"])
        return nd.outputs["Result"]

    def principled(self, **kw):
        p = self.n("ShaderNodeBsdfPrincipled")
        for k, v in kw.items():
            name = k.replace("_", " ")
            if isinstance(v, bpy.types.NodeSocket):
                self.link(v, p.inputs[name])
            else:
                setin(p, name, v)
        return p


def assign(objs, wanted, mat):
    """Point every slot whose material base name is in `wanted` to `mat` (object-level link -> no shared mesh / material edits)."""
    n = 0
    for o in objs:
        for s in o.material_slots:
            if base_name(s.material) in wanted:
                s.link = "OBJECT"
                s.material = mat
                n += 1
    return n


# ----------------------------------------------------------------------------------------------- measurement
def uv_stats(obj, mat_names):
    """Per material: faces, u / v range, metres per u and per v (edge-based medians, world space)."""
    me = obj.data
    if not me.uv_layers:
        return {}
    nl, nv, npoly = len(me.loops), len(me.vertices), len(me.polygons)
    co = np.empty(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(nv, 3)
    lv = np.empty(nl, dtype=np.int64); me.loops.foreach_get("vertex_index", lv)
    uv = np.empty(nl * 2); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(nl, 2)
    ls = np.empty(npoly, dtype=np.int64); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npoly, dtype=np.int64); me.polygons.foreach_get("loop_total", lt)
    mi = np.empty(npoly, dtype=np.int64); me.polygons.foreach_get("material_index", mi)
    pl = np.repeat(np.arange(npoly), lt)
    idx = np.arange(nl)
    nxt = ls[pl] + (idx - ls[pl] + 1) % lt[pl]
    duv = uv[nxt] - uv[idx]
    dl = np.linalg.norm(co[lv[nxt]] - co[lv[idx]], axis=1)
    out = {}
    for i, s in enumerate(obj.material_slots):
        nm = base_name(s.material)
        if nm not in mat_names:
            continue
        sel_l = mi[pl] == i
        if not sel_l.any():
            continue
        u, v = uv[sel_l, 0], uv[sel_l, 1]
        du, dv, d = np.abs(duv[sel_l, 0]), np.abs(duv[sel_l, 1]), dl[sel_l]
        along = (du < 1e-5) & (dv > 1e-5)
        across = (dv < 1e-5) & (du > 1e-5)
        mpv = float(np.median(d[along] / dv[along])) if along.any() else float("nan")
        mpu = float(np.median(d[across] / du[across])) if across.any() else float("nan")
        out[nm] = dict(faces=int((mi == i).sum()), u=(float(u.min()), float(u.max())), v=(float(v.min()), float(v.max())),
                       m_per_u=mpu, m_per_v=mpv)
    return out


def track_coords(objs, C, attr="wfx_trk"):
    """Per-vertex TRACK-SPACE coordinates (lateral m, + right | track distance d m | height m above the centre line) stored as the
    POINT attribute `attr` -> every flow pattern is seam-free across modules and independent of the per-module UV layouts (the
    curved modules' rail-band UVs are unusable: 47.9 m per u). Same numbers the game's SplineMeshDeformer uses (Unity: UV2 / UV3)."""
    F = C._frame_arrays()
    ds = F["d"]
    sw = [0, 2, 1]                                   # Unity (x, y, z) -> Blender (x, z, y)
    pos, fw, up, rt = (F[k][:, sw] for k in ("pos", "fwd", "flatUp", "flatRight"))
    out = {}
    for o in objs:
        me = o.data
        n = len(me.vertices)
        if n == 0:
            continue
        co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(n, 3)
        M = np.array(o.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        idx = np.empty(n, dtype=np.int64)
        for s in range(0, n, 4096):
            dd = ((co[s:s + 4096, None, :] - pos[None]) ** 2).sum(-1)
            idx[s:s + 4096] = dd.argmin(1)
        d = ds[idx] + ((co - pos[idx]) * fw[idx]).sum(1)
        valid = (d > ds[0] + 0.25) & (d < ds[-1] - 0.25)       # the exported frames only cover d 20..80
        d = np.clip(d, ds[0], ds[-1])
        i = np.clip(np.searchsorted(ds, d) - 1, 0, len(ds) - 2)
        t = ((d - ds[i]) / (ds[i + 1] - ds[i]))[:, None]
        P = pos[i] * (1 - t) + pos[i + 1] * t
        R = rt[i] * (1 - t) + rt[i + 1] * t; R /= np.linalg.norm(R, axis=1, keepdims=True)
        U = up[i] * (1 - t) + up[i + 1] * t; U /= np.linalg.norm(U, axis=1, keepdims=True)
        lat = ((co - P) * R).sum(1)
        h = ((co - P) * U).sum(1)
        if (~valid).any() and me.uv_layers:
            # outside the exported frames (far modules up the tunnel / behind the camera): fall back to the module UVs
            # (water u = across, ~3.6 m per u; v ~ 4 m) - rails there get a constant pink (they are tiny on screen)
            nl = len(me.loops)
            lv = np.empty(nl, dtype=np.int64); me.loops.foreach_get("vertex_index", lv)
            uv = np.empty(nl * 2); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(nl, 2)
            vu = np.zeros((n, 2)); vu[lv] = uv
            bad = ~valid
            lat[bad] = (vu[bad, 0] - 0.5) * 3.0
            d[bad] = vu[bad, 1] * 4.0
        a = me.attributes.get(attr) or me.attributes.new(attr, "FLOAT_VECTOR", "POINT")
        a.data.foreach_set("vector", np.stack([lat, d, h], 1).astype(np.float32).ravel())
        out[o.name] = (lat, d, h, valid)
    return out


def lift_chevrons(chevrons, water, clear=0.02):
    """The near chevron's arm lies ON the banked water surface -> z-fighting speckles. Raise every chevron island so its top
    surface clears the water by `clear` m (raycast down onto the M_Water faces). In Unity the chevrons are drawn over the water."""
    verts, polys = [], []
    for o in water:
        me = o.data
        mw = o.matrix_world
        wi = {i for i, m in enumerate(o.data.materials) if base_name(m) == "M_Water"}   # mesh materials (slots are WFX_* by now)
        base = len(verts)
        verts.extend(mw @ v.co for v in me.vertices)
        polys.extend([base + i for i in p.vertices] for p in me.polygons if p.material_index in wi)
    if not polys:
        return 0
    bvh = BVHTree.FromPolygons(verts, polys)
    down = Vector((0, 0, -1))
    n_lift = 0
    for o in chevrons:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bm.verts.ensure_lookup_table()
        seen = set()
        mw = o.matrix_world
        for v0 in bm.verts:
            if v0.index in seen:
                continue
            isl, stack = [], [v0]
            seen.add(v0.index)
            while stack:
                v = stack.pop(); isl.append(v)
                for e in v.link_edges:
                    w = e.other_vert(v)
                    if w.index not in seen:
                        seen.add(w.index); stack.append(w)
            gaps = []
            for v in isl:
                p = mw @ v.co
                hit = bvh.ray_cast(p + Vector((0, 0, 0.6)), down, 2.0)
                if hit[0] is not None:
                    gaps.append(p.z - hit[0].z)
            if len(gaps) < 3:
                continue
            top = float(np.percentile(gaps, 90))
            if top < clear and top > -0.5:
                dz = clear - top
                for v in isl:
                    v.co.z += dz
                n_lift += 1
        bm.to_mesh(o.data); bm.free()
        o.data.update()
    return n_lift


def per_material_lat(o, lat, names):
    """|lateral| 2 / 98 percentiles of the vertices of every material slot whose base name is in `names`."""
    me = o.data
    npoly, nl = len(me.polygons), len(me.loops)
    mi = np.empty(npoly, dtype=np.int64); me.polygons.foreach_get("material_index", mi)
    lt = np.empty(npoly, dtype=np.int64); me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nl, dtype=np.int64); me.loops.foreach_get("vertex_index", lv)
    lm = np.repeat(mi, lt)
    res = {}
    for i, s in enumerate(o.material_slots):
        nm = base_name(s.material)
        if nm in names:
            vi = np.unique(lv[lm == i])
            if len(vi):
                al = np.abs(lat[vi])
                al = al[np.isfinite(al)]
                if len(al) > 8:
                    res[nm] = (float(np.percentile(al, 2)), float(np.percentile(al, 98)))
    return res


# ------------------------------------------------------------------------------------------------- materials
# Pass 03 principle (measured on the ORIGINAL 720p frame, Captures/s2v1/NOTES_water.md): every look is EMISSION-LED = the emission
# colour is the target on-screen sRGB colour at strength ~1 under the Standard view transform, the base colour is dark, so lights
# only add gloss / highlights (robust to the lighting module, and the same split maps to Unity URP: emissive albedo + specular).
def trk(b):
    a = b.attr("wfx_trk")
    s = b.sep(a.outputs["Vector"])
    return s[0], s[1], s[2]                               # lateral, d, height


def mat_water():
    """Deep blue-turquoise glossy water; SOFT WIDE low-contrast light bands along the flow (no thin scratch lines).
    ORIGINAL lower-half water: p10 #3788CD, p50 #4AABDD, p90 #D9FCF8 (the p90 = soft white-cyan bands / chevron glow)."""
    b = NT("WFX_Water", render="DITHERED")
    lat, d, h = trk(b)
    prm = b.sep(b.attr("wfx_p", "OBJECT").outputs["Vector"])           # x = water half width (m)
    t = b.math("DIVIDE", b.math("ABSOLUTE", lat), b.math("MAXIMUM", prm[0], 0.5), clamp=True)   # 0 centre .. 1 rail
    # gently meandering flow lines (bands are not ruler-straight)
    warp = b.noise(b.vec(b.math("MULTIPLY", lat, 0.35), b.math("MULTIPLY", d, 0.035), 1.7), 1.0, detail=1.0)
    latw = b.math("ADD", lat, b.math("MULTIPLY", b.math("SUBTRACT", warp, 0.5), 0.55))
    n1 = b.noise(b.vec(b.math("MULTIPLY", latw, 1.3), b.math("MULTIPLY", d, 0.045), 0.0), 1.0, detail=1.2, rough=0.4)
    n2 = b.noise(b.vec(b.math("MULTIPLY", latw, 2.4), b.math("MULTIPLY", d, 0.07), 9.1), 1.0, detail=0.8, rough=0.35)
    band1 = b.smooth(n1, 0.47, 0.68)                  # wide turquoise bands ~0.5 m x ~20 m
    band2 = b.smooth(n2, 0.52, 0.72)                  # soft white-cyan sheen bands (orig p90 #D9F0F7)
    edge = b.smooth(t, 0.35, 1.0)
    body = b.mix(srgb("#3497DC"), srgb("#2364C6"), edge)                       # turquoise-blue centre -> deep blue at the rails
    body = b.mix(body, srgb("#5CCCF2"), b.math("MULTIPLY", band1, 0.62))
    body = b.mix(body, srgb("#CDF5FC"), b.math("MULTIPLY", band2, 0.62))
    body = b.mix(body, srgb("#C27AD8"), b.math("MULTIPLY", b.smooth(t, 0.86, 1.0), 0.18))   # rail / tunnel pink-violet reflection
    # elongated ripples -> stretched glossy highlights along the flow
    # pass 05: LOW-frequency swell only (detail 0) - the detail-2 ripples made sparkling white specular 'snow' under the lights
    rip = b.noise(b.vec(b.math("MULTIPLY", lat, 1.4), b.math("MULTIPLY", d, 0.12), 2.1), 1.0, detail=0.0, rough=0.5)
    bump = b.n("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.10; bump.inputs["Distance"].default_value = 0.04
    b.link(rip, bump.inputs["Height"])
    dark = b.mix(body, (0.0, 0.0, 0.0, 1.0), 0.8)
    p = b.principled(Base_Color=dark, Roughness=0.06, IOR=1.33, Coat_Weight=0.0, Coat_Roughness=0.04,   # pass 06: ONE reflection closure
                     Emission_Color=body, Emission_Strength=1.0, Specular_IOR_Level=0.6)
    b.link(bump.outputs["Normal"], p.inputs["Normal"])
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_rail_band():
    """Glossy hot-pink rail band: bright pink-white lip at the water, pink body, a golden-orange light stripe, magenta outer edge,
    long soft light streaks along the flow. ORIGINAL rails: p10 #D36494, p50 #E483AA / #EB79B2, p90 #F2BBD1."""
    b = NT("WFX_RailBand")
    lat, d, h = trk(b)
    prm = b.sep(b.attr("wfx_p", "OBJECT").outputs["Vector"])           # y, z = band |lateral| range (m)
    t = b.math("DIVIDE", b.math("SUBTRACT", b.math("ABSOLUTE", lat), prm[1]),
               b.math("MAXIMUM", b.math("SUBTRACT", prm[2], prm[1]), 0.05), clamp=True)
    stripes = b.ramp(t, [(0.00, srgb("#FFCDE8")), (0.06, srgb("#F27FB6")), (0.30, srgb("#E46BA6")),
                         (0.42, srgb("#FA9C88")), (0.50, srgb("#FFC46E")), (0.58, srgb("#FA9C8A")),
                         (0.70, srgb("#E870AE")), (0.88, srgb("#D25A9E")), (1.00, srgb("#C24A96"))], "EASE").outputs[0]
    warp = b.noise(b.vec(b.math("MULTIPLY", lat, 0.5), b.math("MULTIPLY", d, 0.03), 4.4), 1.0, detail=1.0)
    tw = b.math("ADD", t, b.math("MULTIPLY", b.math("SUBTRACT", warp, 0.5), 0.25))
    st = b.smooth(b.noise(b.vec(b.math("MULTIPLY", tw, 7.0), b.math("MULTIPLY", d, 0.05), 3.3), 1.0, detail=1.0, rough=0.4), 0.52, 0.74)
    col = b.mix(stripes, srgb("#FFC9E6"), b.math("MULTIPLY", st, 0.55))
    sh = b.smooth(b.noise(b.vec(b.math("MULTIPLY", tw, 5.0), b.math("MULTIPLY", d, 0.06), 8.8), 1.0, detail=1.0), 0.55, 0.75)
    col = b.mix(col, srgb("#C24796"), b.math("MULTIPLY", sh, 0.35))           # darker magenta streaks for contrast (p10)
    dark = b.mix(col, (0.0, 0.0, 0.0, 1.0), 0.7)
    p = b.principled(Base_Color=dark, Roughness=0.07, Coat_Weight=1.0, Coat_Roughness=0.03, Specular_IOR_Level=0.7,
                     Emission_Color=col, Emission_Strength=1.0)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_rail_tube():
    """Round pink rail tube: hot pink with a bright pink-white crest (the original's glossy top highlight)."""
    b = NT("WFX_RailTube")
    geo = b.n("ShaderNodeNewGeometry")
    nz = b.sep(geo.outputs["Normal"])[2]
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    crest = b.smooth(nz, 0.55, 0.95)
    col = b.mix(srgb("#D9479C"), srgb("#FF8CC8"), crest)
    col = b.mix(col, srgb("#FFE0F2"), b.math("MULTIPLY", b.smooth(nz, 0.85, 1.0), 0.6))
    dark = b.mix(col, (0.0, 0.0, 0.0, 1.0), 0.7)
    p = b.principled(Base_Color=dark, Roughness=0.06, Coat_Weight=1.0, Coat_Roughness=0.02, Specular_IOR_Level=0.8,
                     Emission_Color=col, Emission_Strength=1.0)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_slide_shell():
    b = NT("WFX_SlideShell")
    p = b.principled(Base_Color=srgb("#5A1E52"), Roughness=0.14, Coat_Weight=0.7, Coat_Roughness=0.05,
                     Emission_Color=srgb("#B83E96"), Emission_Strength=0.85)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_foam(shade=False):
    """Soft rounded soap foam: bright white tops, pink-lavender undersides (ORIGINAL foam p10 #CD94B5, p50 #E2D5E2, p90 #F2ECF0),
    subsurface softness + sheen (not plastic). Form shading from the world normal so it reads under any light."""
    b = NT("WFX_Foam" + ("_Shade" if shade else ""))
    geo = b.n("ShaderNodeNewGeometry")
    nz = b.sep(geo.outputs["Normal"])[2]
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    top = b.smooth(nz, -0.35, 0.75)
    col = b.mix(srgb("#C9A0C2"), srgb("#F3EFF5"), top)
    col = b.mix(col, srgb("#B4A8E2"), b.math("MULTIPLY", b.smooth(lw.outputs["Facing"], 0.55, 1.0), 0.30))   # cool rim
    if shade:
        col = b.mix(col, srgb("#B98AB4"), 0.25)
    dark = b.mix(col, (0.0, 0.0, 0.0, 1.0), 0.55)
    p = b.principled(Base_Color=dark, Roughness=0.42, Subsurface_Weight=0.5, Subsurface_Radius=(0.9, 0.8, 1.0),
                     Subsurface_Scale=0.08, Sheen_Weight=0.4, Sheen_Tint=srgb("#FFD3F0"), Sheen_Roughness=0.4,
                     Specular_IOR_Level=0.45, Emission_Color=col, Emission_Strength=0.9)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_bubble():
    """Iridescent thin-film soap bubble: nearly clear centre, rainbow film toward the rim, sharp white highlights."""
    b = NT("WFX_Bubble", render="BLENDED")
    b.m.use_backface_culling = False
    try:
        b.m.use_transparency_overlap = True
    except Exception:
        pass
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    geo = b.n("ShaderNodeNewGeometry")
    swirl = b.noise(geo.outputs["Position"], 6.0, detail=2.0, rough=0.5, distortion=1.5)
    f = b.math("ADD", b.math("MULTIPLY", lw.outputs["Facing"], 1.0), b.math("MULTIPLY", swirl, 0.35))
    film = b.ramp(f, [(0.10, srgb("#FFD9F2")), (0.30, srgb("#FF9AD8")), (0.45, srgb("#FFE58A")),
                      (0.60, srgb("#8FF0FF")), (0.75, srgb("#B59BFF")), (0.90, srgb("#FF8FD0")),
                      (1.00, srgb("#9FE8FF"))]).outputs[0]
    rim = b.ramp(lw.outputs["Facing"], [(0.25, (0, 0, 0, 1)), (0.95, (1, 1, 1, 1))], "EASE").outputs[0]
    gl = b.n("ShaderNodeBsdfGlossy"); setin(gl, "Roughness", 0.02); b.link(film, gl.inputs["Color"])
    em = b.n("ShaderNodeEmission"); b.link(film, em.inputs["Color"]); em.inputs["Strength"].default_value = 0.9
    add = b.n("ShaderNodeAddShader"); b.link(gl.outputs[0], add.inputs[0]); b.link(em.outputs[0], add.inputs[1])
    tr = b.n("ShaderNodeBsdfTransparent")
    mx = b.n("ShaderNodeMixShader")
    b.link(b.math("ADD", b.math("MULTIPLY", rim, 0.75), 0.12, clamp=True), mx.inputs[0])
    b.link(tr.outputs[0], mx.inputs[1]); b.link(add.outputs[0], mx.inputs[2])
    b.link(mx.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_droplet():
    """Clear water droplet (small round bubbles on the water): mostly transparent, bright rim + highlight."""
    b = NT("WFX_Droplet", render="BLENDED")
    b.m.use_backface_culling = True
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    rim = b.ramp(lw.outputs["Facing"], [(0.3, (0, 0, 0, 1)), (0.95, (1, 1, 1, 1))], "EASE").outputs[0]
    gl = b.n("ShaderNodeBsdfGlossy"); setin(gl, "Roughness", 0.02); setin(gl, "Color", srgb("#E8FBFF"))
    em = b.n("ShaderNodeEmission"); setin(em, "Color", srgb("#BFF2FF")); em.inputs["Strength"].default_value = 1.1
    add = b.n("ShaderNodeAddShader"); b.link(gl.outputs[0], add.inputs[0]); b.link(em.outputs[0], add.inputs[1])
    tr = b.n("ShaderNodeBsdfTransparent")
    mx = b.n("ShaderNodeMixShader")
    b.link(b.math("ADD", b.math("MULTIPLY", rim, 0.8), 0.1, clamp=True), mx.inputs[0])
    b.link(tr.outputs[0], mx.inputs[1]); b.link(add.outputs[0], mx.inputs[2])
    b.link(mx.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_milk():
    """Milky white translucent splash (ORIGINAL crown region p50 #BDD9E5, p90 #DBF3F5 = bluish milk, not paper white): bright
    blue-white tops, cool translucent blue where thin / grazing (the water shows through), glossy wet coat + dithered alpha edges."""
    b = NT("WFX_Milk", render="DITHERED")
    b.m.use_backface_culling = False
    geo = b.n("ShaderNodeNewGeometry")
    nz = b.sep(geo.outputs["Normal"])[2]
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    edge = b.smooth(lw.outputs["Facing"], 0.35, 0.92)
    col = b.mix(srgb("#B9D3EA"), srgb("#F2F8FD"), b.smooth(nz, -0.4, 0.8))          # form: lit tops, cooler undersides
    col = b.mix(col, srgb("#78B2E4"), b.math("MULTIPLY", edge, 0.62))                  # thin / grazing = translucent blue
    dark = b.mix(col, (0.0, 0.0, 0.0, 1.0), 0.55)
    p = b.principled(Base_Color=dark, Roughness=0.08, Subsurface_Weight=0.6, Subsurface_Radius=(0.6, 0.8, 1.0),
                     Subsurface_Scale=0.05, Coat_Weight=1.0, Coat_Roughness=0.02, Specular_IOR_Level=0.9,
                     Emission_Color=col, Emission_Strength=0.92,
                     Alpha=b.math("SUBTRACT", 0.96, b.math("MULTIPLY", edge, 0.38)))
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_gold_coin():
    """Polished gold paw coin (ORIGINAL coin: bright yellow #F2C64E faces, orange-gold #B97A2E rim / shade, pale-yellow highlights).
    Emission-led yellow so a violet environment never turns the metal brown; metallic coat for the sharp highlights."""
    b = NT("WFX_CoinGold")
    geo = b.n("ShaderNodeNewGeometry")
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
    face = b.smooth(lw.outputs["Facing"], 0.15, 0.75)                 # 0 = facing the camera, 1 = grazing rim
    nz = b.sep(geo.outputs["Normal"])[2]
    col = b.mix(srgb("#EAB646"), srgb("#A96A22"), face)
    col = b.mix(col, srgb("#FFE08A"), b.math("MULTIPLY", b.smooth(nz, 0.5, 0.95), 0.45))   # upper bevel catches the tunnel light
    p = b.principled(Base_Color=srgb("#7A5418"), Metallic=1.0, Roughness=0.16, Coat_Weight=0.5, Coat_Roughness=0.04,
                     Emission_Color=col, Emission_Strength=0.9)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_gem():
    b = NT("WFX_Gem")
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    col = b.mix(srgb("#B24CF2"), srgb("#5E1AA8"), b.smooth(lw.outputs["Facing"], 0.2, 0.9))
    p = b.principled(Base_Color=srgb("#3A0C66"), Roughness=0.04, IOR=2.0, Coat_Weight=1.0, Specular_IOR_Level=1.0,
                     Emission_Color=col, Emission_Strength=0.95)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_glass():
    b = NT("WFX_Glass", render="BLENDED")
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    gl = b.n("ShaderNodeBsdfGlossy"); setin(gl, "Roughness", 0.03); setin(gl, "Color", srgb("#F3E8FF"))
    tr = b.n("ShaderNodeBsdfTransparent"); setin(tr, "Color", srgb("#EBDDFF"))
    mx = b.n("ShaderNodeMixShader")
    b.link(b.math("ADD", b.math("MULTIPLY", lw.outputs["Facing"], 0.6), 0.08, clamp=True), mx.inputs[0])
    b.link(tr.outputs[0], mx.inputs[1]); b.link(gl.outputs[0], mx.inputs[2])
    b.link(mx.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_emit(name, hexcol, strength, base_hex=None):
    b = NT(name)
    p = b.principled(Base_Color=srgb(base_hex or hexcol), Roughness=0.2, Emission_Color=srgb(hexcol),
                     Emission_Strength=strength)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_chevron():
    """Glowing cyan boost chevron (ORIGINAL p10 #36B7D5, p50 #AEFAF5, p90 #C8FDF8): pale luminous cyan core, saturated cyan edges."""
    b = NT("WFX_Chevron")
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    geo = b.n("ShaderNodeNewGeometry")
    nz = b.sep(geo.outputs["Normal"])[2]
    col = b.mix(srgb("#86F2F4"), srgb("#1DBEE0"), b.smooth(lw.outputs["Facing"], 0.3, 0.85))
    col = b.mix(srgb("#0E9FD0"), col, b.smooth(nz, 0.6, 0.9))                         # bevels / sides = saturated cyan
    p = b.principled(Base_Color=srgb("#06323C"), Roughness=0.22, Coat_Weight=0.2, Specular_IOR_Level=0.3,
                     Emission_Color=col, Emission_Strength=1.2)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_plush(name, hexcol, sheen_hex, rough=0.75, emit=0.55):
    """PLACEHOLDER only (character team owns the mascot): emission-led plush colour with a soft facing-based form."""
    b = NT(name)
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    col = b.mix(srgb(hexcol), srgb(sheen_hex), b.math("MULTIPLY", b.smooth(lw.outputs["Facing"], 0.5, 1.0), 0.45))
    p = b.principled(Base_Color=b.mix(col, (0.0, 0.0, 0.0, 1.0), 0.5), Roughness=rough, Subsurface_Weight=0.25,
                     Subsurface_Radius=(1.0, 0.5, 0.5), Subsurface_Scale=0.03, Sheen_Weight=0.6, Sheen_Tint=srgb(sheen_hex),
                     Sheen_Roughness=0.35, Specular_IOR_Level=0.3, Emission_Color=col, Emission_Strength=emit)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def untextured(mat):
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        return True
    return not any(n.type == "TEX_IMAGE" for n in mat.node_tree.nodes)


# ---------------------------------------------------------------------------------------------- crowns + drops
def sphere_mesh(name, seg=20, rings=12):
    me = bpy.data.meshes.get(name)
    if me:
        return me
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me); bm.free()
    return me


def add_drop(coll, me, mat, loc, r, name, squash=1.0):
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.scale = (r, r, r * squash)
    coll.objects.link(o)
    if not me.materials:
        me.materials.append(mat)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = mat
    o["s2v1_part"] = "wfx"
    return o


def occludes(p, cams, bvh, eps=0.04):
    """True if point p would be drawn over the mascot from any camera (the ray cam->p continues into the mascot)."""
    for cpos in cams:
        d = (p - cpos)
        dist = d.length
        hit = bvh.ray_cast(cpos, d.normalized(), dist + 3.0)
        if hit[0] is not None and hit[3] > dist - eps:
            return True
        # also too close to the body surface
    near = bvh.find_nearest(p)
    return near[0] is not None and near[3] < 0.05


def bvh_of(objs, dg):
    """One world-space BVH over several objects (evaluated meshes)."""
    verts, polys = [], []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        base = len(verts)
        verts.extend(o.matrix_world @ v.co for v in me.vertices)
        polys.extend([base + i for i in p.vertices] for p in me.polygons)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys) if polys else None


def build_fx(ctx, mascot, crowns, milk, drop_mat, bub_mat, shield=()):
    """shield = extra objects (near coins) that droplets must never be drawn over, like the mascot."""
    sc = ctx["scene"]
    coll = bpy.data.collections.get("S2V1_WFX") or bpy.data.collections.new("S2V1_WFX")
    if coll.name not in sc.collection.children:
        sc.collection.children.link(coll)
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = bvh_of(([mascot] if mascot else []) + list(shield), dg)
    cams = [o.matrix_world.translation.copy() for o in bpy.data.objects if o.type == "CAMERA" and o.name.startswith("CAM_")]
    me_drop = sphere_mesh("WFX_sphere", 20, 12)
    me_drop.materials.clear(); me_drop.materials.append(milk)
    rng = random.Random(7)
    mc = None
    if mascot:
        bb = [mascot.matrix_world @ Vector(c) for c in mascot.bound_box]
        mc = sum(bb, Vector()) / 8.0
    # track frame at the mascot
    C = ctx["C"]
    right = Vector((1, 0, 0)); fwd = Vector((0, 1, 0)); up = Vector((0, 0, 1))
    try:
        cam = bpy.data.objects["CAM_R2_16x9"]
        right = (cam.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
        fwd = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))); fwd.z = 0; fwd.normalize()
    except KeyError:
        pass
    n_tip = n_det = n_rej = 0
    for cr in crowns:
        me = cr.data
        co = np.array([cr.matrix_world @ v.co for v in me.vertices])
        if len(co) == 0:
            continue
        zmin, zmax = co[:, 2].min(), co[:, 2].max()
        h = zmax - zmin
        ctr = Vector(co.mean(axis=0))
        side = 1.0 if mc is None or (ctr - mc).dot(right) >= 0 else -1.0
        # rounded tips: highest vertex per 7 cm cell among the top 35 % of the crown
        top = co[co[:, 2] > zmin + 0.65 * h]
        cells = {}
        for p in top:
            k = (int(math.floor(p[0] / 0.07)), int(math.floor(p[1] / 0.07)))
            if k not in cells or p[2] > cells[k][2]:
                cells[k] = p
        tips = list(cells.values())
        rng.shuffle(tips)
        for p in tips[:10]:
            v = Vector(p)
            r = rng.uniform(0.012, 0.02)
            if bvh and occludes(v, cams, bvh):
                n_rej += 1
                continue
            add_drop(coll, me_drop, milk, v + Vector((0, 0, r * 0.3)), r, "WFX_CrownTip")
            n_tip += 1
        # detached droplets thrown up / outward from the tips (few, small, close to the crown like the original)
        for i in range(9):
            base = Vector(rng.choice(tips)) if tips else ctr
            off = right * side * rng.uniform(0.06, 0.32) + up * rng.uniform(0.03, 0.2) - fwd * rng.uniform(0.0, 0.25)
            p = base + off
            r = rng.uniform(0.012, 0.03)
            if bvh and occludes(p, cams, bvh):
                n_rej += 1
                continue
            add_drop(coll, me_drop, milk, p, r, "WFX_Droplet", squash=rng.uniform(0.9, 1.25))
            n_det += 1
    # small clear water bubbles over the water around / in front of him (lower half of the frame)
    n_b = 0
    if mc is not None:
        me_b = sphere_mesh("WFX_sphere_clear", 24, 14)
        me_b.materials.clear(); me_b.materials.append(drop_mat)
        zw = min((min((cr.matrix_world @ Vector(c)).z for c in cr.bound_box) for cr in crowns), default=mc.z - 0.3)
        for i in range(90):
            lat = rng.uniform(-1.6, 1.6)
            if abs(lat) < 0.3:
                continue
            p = mc + right * lat - fwd * rng.uniform(-0.2, 2.2)
            p.z = zw + rng.uniform(0.03, 0.32)
            r = rng.uniform(0.02, 0.055)
            if bvh and occludes(p, cams, bvh):
                n_rej += 1
                continue
            add_drop(coll, me_b, drop_mat, p, r, "WFX_WaterBubble")
            n_b += 1
            if n_b >= 24:
                break
    print("%s fx: crown tips %d, detached droplets %d, water bubbles %d, rejected (over mascot) %d" % (LOG, n_tip, n_det, n_b, n_rej))
    return coll


# ----------------------------------------------------------------------------------------------------- apply
def apply(ctx):
    C = ctx["C"]
    water = coll_objs("CTX_water")
    foam = coll_objs("CTX_foam")
    bubbles = coll_objs("CTX_bubbles")
    pickups = coll_objs("CTX_pickups")
    mascot_c = coll_objs("CTX_mascot")
    context = coll_objs("CTX_context")
    print("%s collections: water %d foam %d bubbles %d pickups %d mascot %d context %d" % (
        LOG, len(water), len(foam), len(bubbles), len(pickups), len(mascot_c), len(context)))

    # ---- track-space coordinates on every slide module (seam-free flow patterns) + per-module widths as OBJECT attributes
    tc = track_coords(water, C)
    for o in water:
        if o.name not in tc:
            continue
        lat, _d, _h, valid = tc[o.name]
        if valid.mean() > 0.3:
            r = per_material_lat(o, np.where(valid, lat, np.nan), {"M_Water", "M_RailBand_r8", "M_RailTube_r8", "M_SlideShell"})
            w_half = r.get("M_Water", (0.0, 1.45))[1]
            b0, b1 = r.get("M_RailBand_r8", (1.41, 1.77))
        else:
            r = {}
            w_half, b0, b1 = 1.5, -2.0, 50.0             # far module (UV fallback): constant pink rail, t ~ 0.07
        o["wfx_p"] = (float(w_half), float(b0), float(b1))
        dd = tc[o.name][1]
        print("%s slide %s d %.1f..%.1f |lat| %s" % (LOG, o.name[:24], float(dd.min()), float(dd.max()),
              " ".join("%s %.2f..%.2f" % (k.replace("M_", ""), a, b) for k, (a, b) in sorted(r.items()))))
    n = assign(water, {"M_Water"}, mat_water())
    n += assign(water, {"M_RailBand_r8", "M_RailPink"}, mat_rail_band())
    n += assign(water, {"M_RailTube_r8"}, mat_rail_tube())
    n += assign(water, {"M_SlideShell"}, mat_slide_shell())
    print("%s slide slots %d" % (LOG, n))

    n = assign(foam, {"M_Foam_v2", "M_Foam"}, mat_foam())
    n += assign(foam, {"M_Foam_v2_Shade"}, mat_foam(shade=True))
    print("%s foam slots %d" % (LOG, n))

    bub = mat_bubble()
    n = assign(bubbles + mascot_c, {"M_Bubble"}, bub)
    n2 = assign(bubbles, {"M_Glass"}, mat_glass())
    n2 += assign(bubbles, {"M_PipeWaterPink", "M_PinkLiquid_p5"}, mat_emit("WFX_PipeLiquidPink", "#FF5FC8", 1.2, "#5A1440"))
    n2 += assign(bubbles, {"M_PipeWaterCyan"}, mat_emit("WFX_PipeLiquidCyan", "#4FE3F2", 1.2, "#0C4450"))
    print("%s bubble slots %d, pipe slots %d" % (LOG, n, n2))

    n = assign(pickups, {"M_Coin", "M_Gold", "M_GoldDark"}, mat_gold_coin())
    n += assign(pickups, {"M_Gem"}, mat_gem())
    print("%s pickup slots %d" % (LOG, n))

    chev = [o for o in context if any(base_name(sl.material) == "M_Arrow" for sl in o.material_slots)]
    print("%s chevrons lifted above the water: %d islands" % (LOG, lift_chevrons(chev, water)))
    n = assign(context, {"M_Arrow"}, mat_chevron())
    print("%s chevron slots %d" % (LOG, n))

    # ---- mascot placeholder (only if untextured) + crowns + droplets
    body = next((o for o in mascot_c if "SK_Mascot_Body" in o.name), None)
    crowns = [o for o in mascot_c if "Crown" in o.name]
    for o in mascot_c:
        if "ContactShadow" in o.name:
            o.hide_render = True               # Unity decal quad (untextured here); EEVEE casts real shadows
    if body is not None and all(untextured(s.material) for s in body.material_slots):
        fur = mat_plush("WFX_PH_Fur", "#E9809F", "#FFC4D8", rough=0.8)
        pairs = {
            "M_Fur_v5": fur,
            "M_PawPad_v5": mat_plush("WFX_PH_Pad", "#F29AB0", "#FFFFFF", rough=0.6),
            "M_HatKnit_v5": mat_plush("WFX_PH_HatKnit", "#7B40C6", "#B88BF2", rough=0.85),
            "M_HatCuff_v5": mat_plush("WFX_PH_HatCuff", "#6C34B8", "#B88BF2", rough=0.85),
            "M_HatStripe_v5": mat_plush("WFX_PH_HatStripe", "#F2D2E6", "#FFFFFF", rough=0.85),
            "M_PomPom_v5": mat_plush("WFX_PH_PomPom", "#9152DA", "#C9A2FF", rough=0.9),
            "M_StarBadge": mat_plush("WFX_PH_Badge", "#FFD447", "#FFFFFF", rough=0.4),
        }
        dark = mat_plush("WFX_PH_Dark", "#2A1A2E", "#806080", rough=0.3, emit=0.0)
        for s in body.material_slots:
            nm = base_name(s.material)
            s.link = "OBJECT"
            s.material = pairs.get(nm, dark if nm in ("M_EyeIris", "M_Mouth") else fur)
        print("%s mascot: untextured -> rose plush placeholder (%d slots)" % (LOG, len(body.material_slots)))
    milk = mat_milk()
    n = assign(crowns, {"M_FX_Milk_v3"}, milk)
    for cr in crowns:
        # liquid read: relax the faceted V7 sheet and round every edge / tip (look test; Unity would get the re-exported mesh)
        sm = cr.modifiers.new("WFX_relax", "SMOOTH"); sm.factor = 0.6; sm.iterations = 4
        so = cr.modifiers.new("WFX_body", "SOLIDIFY"); so.thickness = 0.012; so.offset = 0.0   # liquid sheets have a body
        sd = cr.modifiers.new("WFX_round", "SUBSURF"); sd.levels = sd.render_levels = 1
        for f in cr.data.polygons:
            f.use_smooth = True
    for cr in crowns:
        bb = [cr.matrix_world @ Vector(c) for c in cr.bound_box]
        lo = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb)))
        hi = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
        print("%s crown %s bbox %s .. %s verts %d" % (LOG, cr.name, tuple(round(x, 2) for x in lo), tuple(round(x, 2) for x in hi), len(cr.data.vertices)))
    if body is not None:
        bb = [body.matrix_world @ Vector(c) for c in body.bound_box]
        print("%s mascot bbox %s .. %s" % (LOG, tuple(round(min(p[i] for p in bb), 2) for i in range(3)), tuple(round(max(p[i] for p in bb), 2) for i in range(3))))
    near_coins = []
    if body is not None:
        bc = sum((body.matrix_world @ Vector(c) for c in body.bound_box), Vector()) / 8.0
        near_coins = [o for o in pickups if (sum((o.matrix_world @ Vector(c) for c in o.bound_box), Vector()) / 8.0 - bc).length < 7.0]
    build_fx(ctx, body, crowns, milk, mat_droplet(), bub, shield=near_coins)
    preview_light_if_no_lighting(ctx)


def preview_light_if_no_lighting(ctx):
    """ONLY while the lighting-artist's s2v1_lighting.py does not exist (it owns engine, view transform, world, lights): a neutral
    preview so the water / gold / foam materials can be judged. Pass 03 fix: the assembly's 'Standard' fallback never triggers
    (context.blend is already EEVEE -> factory AgX, which desaturated everything in water_01/02) and the old uniform world at 0.9
    flooded the closed tunnel -> now Standard view, a DARK violet world, raytraced reflections, a few soft area lights."""
    import os
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "s2v1_lighting.py")):
        return
    sc = ctx["scene"]
    try:
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        sc.view_settings.exposure = 0.0
        sc.view_settings.gamma = 1.0
    except Exception as e:
        print("%s preview view transform: %s" % (LOG, e))
    ee = getattr(sc, "eevee", None)
    for k, v in (("use_raytracing", True), ("ray_tracing_method", "SCREEN"), ("use_shadows", True),
                 ("taa_render_samples", 32)):
        try:
            setattr(ee, k, v)
        except Exception:
            pass
    try:
        ee.ray_tracing_options.resolution_scale = "1"
    except Exception:
        pass
    w = bpy.data.worlds.new("WFX_TEMP_world")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = srgb("#2A1A52"); bg.inputs[1].default_value = 0.35
    sc.world = w
    cam = bpy.data.objects.get("CAM_R2_16x9")
    if cam is None:
        return
    m3 = cam.matrix_world.to_3x3()
    fwd = (m3 @ Vector((0, 0, -1))).normalized(); upv = (m3 @ Vector((0, 1, 0))).normalized()
    rgt = (m3 @ Vector((1, 0, 0))).normalized()
    base = cam.matrix_world.translation
    for name, off, col, e, size in (("WFX_TEMP_key", fwd * 2.0 + upv * 2.6, "#FFE6F4", 160.0, 2.5),
                                    ("WFX_TEMP_door", fwd * 9.0 + upv * 2.0, "#FFC870", 350.0, 4.0),
                                    ("WFX_TEMP_L", fwd * 4.0 + upv * 1.6 - rgt * 2.6, "#C08CFF", 120.0, 2.0),
                                    ("WFX_TEMP_R", fwd * 4.0 + upv * 1.6 + rgt * 2.6, "#FF9AD8", 120.0, 2.0),
                                    ("WFX_TEMP_core", fwd * 22.0 + upv * 1.0, "#A88BFF", 500.0, 5.0)):
        ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.color = srgb(col)[:3]; ld.size = size
        if name == "WFX_TEMP_key":
            ld.specular_factor = 0.2       # its mirror image on the water + the mascot's soft-shadow noise = speckled patch (water_04/05)
        lo = bpy.data.objects.new(name, ld); sc.collection.objects.link(lo)
        lo.location = base + off
        lo.rotation_euler = (-upv).to_track_quat("-Z", "Y").to_euler()
    print("%s TEMP preview light (no s2v1_lighting.py yet): Standard view, dark world, raytracing" % LOG)
