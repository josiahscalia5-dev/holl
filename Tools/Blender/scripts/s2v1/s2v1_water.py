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


# ------------------------------------------------------------------------------------------------- materials
def mat_water(fwd, across_m_per_u, u_mid):
    """Deep blue-turquoise glossy water; soft wide low-contrast light bands along the flow (no thin scratch lines)."""
    b = NT("WFX_Water", render="DITHERED")
    tc = b.n("ShaderNodeTexCoord")
    geo = b.n("ShaderNodeNewGeometry")
    sep = b.n("ShaderNodeSeparateXYZ"); b.link(tc.outputs["UV"], sep.inputs[0])
    across = b.math("MULTIPLY", b.math("SUBTRACT", sep.outputs[0], u_mid), across_m_per_u)        # metres from the water centre
    dotn = b.n("ShaderNodeVectorMath"); dotn.operation = "DOT_PRODUCT"
    b.link(geo.outputs["Position"], dotn.inputs[0]); dotn.inputs[1].default_value = fwd
    along = dotn.outputs["Value"]                                                              # metres along the track (world)
    # broad soft bands: ~0.5-0.9 m wide, many metres long (anisotropic noise)
    v1 = b.vec(b.math("MULTIPLY", across, 1.25), b.math("MULTIPLY", along, 0.055), 0.0)
    n1 = b.noise(v1, 1.0, detail=1.5, rough=0.45)
    v2 = b.vec(b.math("MULTIPLY", across, 2.6), b.math("MULTIPLY", along, 0.09), 7.3)
    n2 = b.noise(v2, 1.0, detail=1.0, rough=0.4)
    band1 = b.ramp(n1, [(0.40, (0, 0, 0, 1)), (0.70, (1, 1, 1, 1))], "EASE").outputs[0]
    band2 = b.ramp(n2, [(0.48, (0, 0, 0, 1)), (0.78, (1, 1, 1, 1))], "EASE").outputs[0]
    # depth: turquoise centre, deeper blue toward the rails (the water reads deep and transparent at the sides)
    ac = b.math("ABSOLUTE", across)
    edge = b.ramp(ac, [(0.0, (1, 1, 1, 1)), (0.55, (0.55, 0.55, 0.55, 1)), (1.25, (0, 0, 0, 1))], "EASE").outputs[0]
    body = b.mix(srgb("#0A3D9C"), srgb("#1D8BD9"), edge)
    body = b.mix(body, srgb("#38C6E6"), b.math("MULTIPLY", edge, 0.55))
    body = b.mix(body, srgb("#86DDF4"), b.math("MULTIPLY", band1, 0.38))
    body = b.mix(body, srgb("#B9ECFA"), b.math("MULTIPLY", band2, 0.22))
    # grazing angle: the water reflects the violet / pink tunnel
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fres = b.ramp(lw.outputs["Facing"], [(0.55, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))], "EASE").outputs[0]
    col = b.mix(body, srgb("#7C6FE0"), b.math("MULTIPLY", fres, 0.35))
    # elongated ripples -> stretched soft reflections along the flow
    v3 = b.vec(b.math("MULTIPLY", across, 3.2), b.math("MULTIPLY", along, 0.35), 2.1)
    rip = b.noise(v3, 1.0, detail=2.0, rough=0.5)
    bump = b.n("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.22; bump.inputs["Distance"].default_value = 0.03
    b.link(rip, bump.inputs["Height"])
    p = b.principled(Base_Color=col, Roughness=0.045, IOR=1.33, Coat_Weight=0.6, Coat_Roughness=0.02,
                     Emission_Color=body, Emission_Strength=0.55, Specular_IOR_Level=0.7)
    b.link(bump.outputs["Normal"], p.inputs["Normal"])
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_rail_band(fwd, u0, u1):
    """Glossy hot-pink rail band with a golden-orange racing stripe and soft pink-white streaks along the flow."""
    b = NT("WFX_RailBand")
    tc = b.n("ShaderNodeTexCoord"); geo = b.n("ShaderNodeNewGeometry")
    sep = b.n("ShaderNodeSeparateXYZ"); b.link(tc.outputs["UV"], sep.inputs[0])
    t = b.math("DIVIDE", b.math("SUBTRACT", sep.outputs[0], u0), max(1e-4, u1 - u0))
    # symmetric fold so mirrored left / right bands get the same stripe order (0 = edge, 1 = band middle)
    tf = b.math("SUBTRACT", 1.0, b.math("ABSOLUTE", b.math("MULTIPLY", b.math("SUBTRACT", t, 0.5), 2.0)))
    stripes = b.ramp(tf, [(0.00, srgb("#E03AA8")), (0.22, srgb("#FF4FA0")), (0.48, srgb("#FF6F8E")),
                          (0.62, srgb("#FFB24A")), (0.74, srgb("#FF8A6A")), (0.86, srgb("#FF4F9E")),
                          (1.00, srgb("#F23C9A"))], "EASE").outputs[0]
    dotn = b.n("ShaderNodeVectorMath"); dotn.operation = "DOT_PRODUCT"
    b.link(geo.outputs["Position"], dotn.inputs[0]); dotn.inputs[1].default_value = fwd
    along = dotn.outputs["Value"]
    sv = b.vec(b.math("MULTIPLY", t, 9.0), b.math("MULTIPLY", along, 0.05), 3.3)
    st = b.ramp(b.noise(sv, 1.0, detail=1.0, rough=0.4), [(0.55, (0, 0, 0, 1)), (0.78, (1, 1, 1, 1))], "EASE").outputs[0]
    col = b.mix(stripes, srgb("#FFD7EE"), b.math("MULTIPLY", st, 0.45))
    p = b.principled(Base_Color=col, Roughness=0.08, Coat_Weight=1.0, Coat_Roughness=0.03, Specular_IOR_Level=0.8,
                     Emission_Color=stripes, Emission_Strength=0.42)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_rail_tube():
    b = NT("WFX_RailTube")
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    crest = b.ramp(lw.outputs["Facing"], [(0.0, (1, 1, 1, 1)), (0.35, (0, 0, 0, 1))], "EASE").outputs[0]
    col = b.mix(srgb("#F2238E"), srgb("#FF8CC6"), crest)
    p = b.principled(Base_Color=col, Roughness=0.06, Coat_Weight=1.0, Coat_Roughness=0.02, Specular_IOR_Level=0.9,
                     Emission_Color=col, Emission_Strength=0.38)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_slide_shell():
    b = NT("WFX_SlideShell")
    p = b.principled(Base_Color=srgb("#D63FB0"), Roughness=0.14, Coat_Weight=0.7, Coat_Roughness=0.05,
                     Emission_Color=srgb("#D63FB0"), Emission_Strength=0.18)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_foam(shade=False):
    """Soft rounded soap foam: white with cool lavender-blue shading, subsurface softness, faint pink sheen (not plastic)."""
    b = NT("WFX_Foam" + ("_Shade" if shade else ""))
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    rim = b.ramp(lw.outputs["Facing"], [(0.25, (0, 0, 0, 1)), (0.9, (1, 1, 1, 1))], "EASE").outputs[0]
    base = srgb("#E9E6F6") if shade else srgb("#F7F5FD")
    col = b.mix(base, srgb("#C9C4F0"), b.math("MULTIPLY", rim, 0.55))
    p = b.principled(Base_Color=col, Roughness=0.5, Subsurface_Weight=0.55, Subsurface_Radius=(0.9, 0.8, 1.0),
                     Subsurface_Scale=0.08, Sheen_Weight=0.35, Sheen_Tint=srgb("#FFD3F0"), Sheen_Roughness=0.4,
                     Specular_IOR_Level=0.35, Emission_Color=col, Emission_Strength=0.32 if not shade else 0.24)
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
    """Milky white translucent splash: soft white body, cool blue translucency at thin / grazing parts, glossy wet coat."""
    b = NT("WFX_Milk", render="DITHERED")
    b.m.use_backface_culling = False
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    edge = b.ramp(lw.outputs["Facing"], [(0.2, (0, 0, 0, 1)), (0.85, (1, 1, 1, 1))], "EASE").outputs[0]
    col = b.mix(srgb("#FBFCFF"), srgb("#AEE3F7"), b.math("MULTIPLY", edge, 0.6))
    p = b.principled(Base_Color=col, Roughness=0.12, Subsurface_Weight=0.7, Subsurface_Radius=(0.6, 0.8, 1.0),
                     Subsurface_Scale=0.05, Coat_Weight=1.0, Coat_Roughness=0.03, Specular_IOR_Level=0.8,
                     Emission_Color=col, Emission_Strength=0.55,
                     Alpha=b.math("SUBTRACT", 0.97, b.math("MULTIPLY", edge, 0.3)))
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_gold_coin():
    b = NT("WFX_CoinGold")
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
    rim = b.ramp(lw.outputs["Facing"], [(0.2, (0, 0, 0, 1)), (0.9, (1, 1, 1, 1))], "EASE").outputs[0]
    col = b.mix(srgb("#FFC93C"), srgb("#E8902A"), rim)
    p = b.principled(Base_Color=col, Metallic=1.0, Roughness=0.17, Coat_Weight=0.4, Coat_Roughness=0.05,
                     Emission_Color=srgb("#E9A531"), Emission_Strength=0.35)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_gem():
    b = NT("WFX_Gem")
    p = b.principled(Base_Color=srgb("#9B3BE8"), Roughness=0.05, IOR=2.0, Transmission_Weight=0.35, Coat_Weight=1.0,
                     Emission_Color=srgb("#A847F0"), Emission_Strength=0.6)
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
    """Glowing cyan boost chevron: luminous turquoise glass panel, paler cyan-white toward the facing centre."""
    b = NT("WFX_Chevron")
    lw = b.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    col = b.mix(srgb("#B8FBFF"), srgb("#2FD9EA"), b.ramp(lw.outputs["Facing"], [(0.1, (0, 0, 0, 1)), (0.8, (1, 1, 1, 1))]).outputs[0])
    p = b.principled(Base_Color=col, Roughness=0.1, Coat_Weight=1.0, Emission_Color=col, Emission_Strength=1.6)
    b.link(p.outputs[0], b.out.inputs["Surface"])
    return b.m


def mat_plush(name, hexcol, sheen_hex, rough=0.75, emit=0.12):
    b = NT(name)
    p = b.principled(Base_Color=srgb(hexcol), Roughness=rough, Subsurface_Weight=0.25, Subsurface_Radius=(1.0, 0.5, 0.5),
                     Subsurface_Scale=0.03, Sheen_Weight=0.6, Sheen_Tint=srgb(sheen_hex), Sheen_Roughness=0.35,
                     Specular_IOR_Level=0.3, Emission_Color=srgb(hexcol), Emission_Strength=emit)
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


def build_fx(ctx, mascot, crowns, milk, drop_mat, bub_mat):
    sc = ctx["scene"]
    coll = bpy.data.collections.get("S2V1_WFX") or bpy.data.collections.new("S2V1_WFX")
    if coll.name not in sc.collection.children:
        sc.collection.children.link(coll)
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(mascot, dg) if mascot else None
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
        for p in tips[:14]:
            v = Vector(p)
            r = rng.uniform(0.018, 0.03)
            if bvh and occludes(v, cams, bvh):
                n_rej += 1
                continue
            add_drop(coll, me_drop, milk, v + Vector((0, 0, r * 0.4)), r, "WFX_CrownTip")
            n_tip += 1
        # detached droplets thrown up / outward from the tips
        for i in range(22):
            base = Vector(rng.choice(tips)) if tips else ctr
            off = right * side * rng.uniform(0.04, 0.45) + up * rng.uniform(0.05, 0.42) - fwd * rng.uniform(-0.05, 0.35)
            p = base + off
            r = rng.uniform(0.014, 0.042)
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
        for i in range(60):
            lat = rng.uniform(-1.7, 1.7)
            if abs(lat) < 0.35:
                continue
            p = mc + right * lat - fwd * rng.uniform(-0.2, 2.2)
            p.z = zw + rng.uniform(0.04, 0.5)
            r = rng.uniform(0.02, 0.07)
            if bvh and occludes(p, cams, bvh):
                n_rej += 1
                continue
            add_drop(coll, me_b, drop_mat, p, r, "WFX_WaterBubble")
            n_b += 1
            if n_b >= 26:
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

    # ---- measure the slide UVs (water + rails) and pick the flow direction at the mascot
    stats = {}
    for o in water:
        s = uv_stats(o, {"M_Water", "M_RailBand_r8", "M_RailTube_r8", "M_SlideShell"})
        for k, v in s.items():
            stats.setdefault(k, []).append(v)
            print("%s uv %s %s faces %d u %.3f..%.3f v %.2f..%.2f m/u %.3f m/v %.3f" % (
                LOG, o.name[:26], k, v["faces"], v["u"][0], v["u"][1], v["v"][0], v["v"][1], v["m_per_u"], v["m_per_v"]))

    def med(k, f, default):
        vals = [x[f] for x in stats.get(k, []) if not (isinstance(x[f], float) and math.isnan(x[f]))]
        return float(np.median(vals)) if vals else default

    fr = C.frame_at(34.0)
    fwd = tuple(float(x) for x in C.u2b(fr["fwd"]))
    w_u = [x["u"] for x in stats.get("M_Water", [])]
    u_lo = float(np.median([a for a, _ in w_u])) if w_u else 0.0
    u_hi = float(np.median([b for _, b in w_u])) if w_u else 1.0
    m_per_u = med("M_Water", "m_per_u", 3.6)
    print("%s water u %.3f..%.3f m/u %.3f  fwd %s" % (LOG, u_lo, u_hi, m_per_u, tuple(round(x, 3) for x in fwd)))
    b_u = [x["u"] for x in stats.get("M_RailBand_r8", [])]
    bu0 = float(np.median([a for a, _ in b_u])) if b_u else 0.0
    bu1 = float(np.median([b for _, b in b_u])) if b_u else 1.0

    m_water = mat_water(fwd, m_per_u, 0.5 * (u_lo + u_hi))
    n = assign(water, {"M_Water"}, m_water)
    n += assign(water, {"M_RailBand_r8", "M_RailPink"}, mat_rail_band(fwd, bu0, bu1))
    n += assign(water, {"M_RailTube_r8"}, mat_rail_tube())
    n += assign(water, {"M_SlideShell"}, mat_slide_shell())
    print("%s slide slots %d" % (LOG, n))

    n = assign(foam, {"M_Foam_v2", "M_Foam"}, mat_foam())
    n += assign(foam, {"M_Foam_v2_Shade"}, mat_foam(shade=True))
    print("%s foam slots %d" % (LOG, n))

    bub = mat_bubble()
    n = assign(bubbles + mascot_c, {"M_Bubble"}, bub)
    n2 = assign(bubbles, {"M_Glass"}, mat_glass())
    n2 += assign(bubbles, {"M_PipeWaterPink", "M_PinkLiquid_p5"}, mat_emit("WFX_PipeLiquidPink", "#FF5FC8", 1.4))
    n2 += assign(bubbles, {"M_PipeWaterCyan"}, mat_emit("WFX_PipeLiquidCyan", "#4FE3F2", 1.4))
    print("%s bubble slots %d, pipe slots %d" % (LOG, n, n2))

    n = assign(pickups, {"M_Coin", "M_Gold", "M_GoldDark"}, mat_gold_coin())
    n += assign(pickups, {"M_Gem"}, mat_gem())
    print("%s pickup slots %d" % (LOG, n))

    n = assign(context, {"M_Arrow"}, mat_chevron())
    print("%s chevron slots %d" % (LOG, n))

    # ---- mascot placeholder (only if untextured) + crowns + droplets
    body = next((o for o in mascot_c if "SK_Mascot_Body" in o.name), None)
    crowns = [o for o in mascot_c if "Crown" in o.name]
    for o in mascot_c:
        if "ContactShadow" in o.name:
            o.hide_render = True               # Unity decal quad (untextured here); EEVEE casts real shadows
    if body is not None and all(untextured(s.material) for s in body.material_slots):
        fur = mat_plush("WFX_PH_Fur", "#EE8FA8", "#FFD0E0", rough=0.8)
        pairs = {
            "M_Fur_v5": fur,
            "M_PawPad_v5": mat_plush("WFX_PH_Pad", "#F5A3B5", "#FFFFFF", rough=0.6),
            "M_HatKnit_v5": mat_plush("WFX_PH_HatKnit", "#7A3CC8", "#C9A2FF", rough=0.85),
            "M_HatCuff_v5": mat_plush("WFX_PH_HatCuff", "#6E34BC", "#C9A2FF", rough=0.85),
            "M_HatStripe_v5": mat_plush("WFX_PH_HatStripe", "#F4D9E8", "#FFFFFF", rough=0.85),
            "M_PomPom_v5": mat_plush("WFX_PH_PomPom", "#8A4CDA", "#D9B8FF", rough=0.9),
            "M_StarBadge": mat_plush("WFX_PH_Badge", "#FFD447", "#FFFFFF", rough=0.4, emit=0.3),
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
        bb = [cr.matrix_world @ Vector(c) for c in cr.bound_box]
        lo = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb)))
        hi = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
        print("%s crown %s bbox %s .. %s verts %d" % (LOG, cr.name, tuple(round(x, 2) for x in lo), tuple(round(x, 2) for x in hi), len(cr.data.vertices)))
    if body is not None:
        bb = [body.matrix_world @ Vector(c) for c in body.bound_box]
        print("%s mascot bbox %s .. %s" % (LOG, tuple(round(min(p[i] for p in bb), 2) for i in range(3)), tuple(round(max(p[i] for p in bb), 2) for i in range(3))))
    build_fx(ctx, body, crowns, milk, mat_droplet(), bub)
