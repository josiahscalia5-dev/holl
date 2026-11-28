"""S2 Tunnel v1 - LIGHTING (lighting-artist). apply(ctx) is called LAST by s2v1_render.py (after env, materials, water).

Owns: render engine + samples, view transform, world, lights LGT_S2v1_*, reflection probes PRB_S2v1_*, emission STRENGTHS of the
light-carrying parts (bulb, band_lip, star, star_glow + the context emitters M_Bulb / M_Rim* / M_Neon_* / M_Vanish* ...), distance fog
(= Unity linear fog, done as mist pass + compositor mix) and the compositor grade (Glare bloom on emitters only, saturation).
Look (the ORIGINAL 3.00 s frame): the bulbs, band lips, neon stars and a small cool core accent ARE the light; polished metal reflects
them; deep violet shade between; the core stays DARK SATURATED VIOLET (r 25-80 px L* 38-45 #68479D). No three-point rig, no white fog.

Every value is chosen so it maps 1:1 to Unity URP mobile (see Captures/s2v1/NOTES_lighting.md 'Unity mapping'); the module writes the
exact light list with Unity world positions / colours / intensities / ranges to <render dir>/lights_unity.json.
Env override for quick tests: S2V1_LIGHT_<KEY>=<number> overrides a numeric entry of P (e.g. S2V1_LIGHT_FOG_END=160).
"""
import json
import math
import os

import bpy
import numpy as np
from mathutils import Vector

LOG = "LIGHT"

P = {
    # render
    "samples": 32,                 # EEVEE TAA samples (review 64)
    "view": "Standard",            # Unity parity: URP Tonemapping None + HDR bloom; team materials are authored as emission = sRGB target
    "exposure": 0.0,
    # world = Unity Environment Lighting (Ambient Color) + skybox reflection fallback
    "world_hex": "#24163F", "world_strength": 0.6,
    # distance fog = Unity linear fog (RenderSettings.fogMode Linear, fogStartDistance / fogEndDistance, fogColor)
    "fog_start": 12.0, "fog_end": 140.0, "fog_hex": "#6A48A6",
    # bloom = URP Bloom (threshold in linear here; URP threshold is gamma: 0.9 lin ~ 0.95 gamma)
    "bloom_threshold": 0.9, "bloom_strength": 0.55, "bloom_size": 0.55, "saturation": 1.06,
    # emission strengths (Blender multiplier; Unity HDR intensity = log2(strength))
    "emit_bulb": 3.0, "emit_band_lip": 1.35, "emit_star": 2.6, "emit_star_glow": 0.6,
    "emit_ctx_bulb": 3.0, "emit_ctx_rim": 1.1, "emit_ctx_neon": 2.4, "emit_ctx_core": 2.0,
    # emitter-motivated point lights (Blender W per ring = total, split over the sectors; no shadows = Unity mobile additional lights)
    "g1_total_w": 220.0, "g1_sectors": 8, "g2_total_w": 120.0, "g2_sectors": 6,
    "lipA_total_w": 160.0, "lip_total_w": 70.0, "lip_sectors": 8,
    "door_total_w": 260.0, "door_sectors": 6,
    "star_w": 22.0, "core_w": 160.0,
    # motivated foreground: machine-hall ceiling glow above the mascot + warm spill out of the door (both soft area lights)
    "hall_w": 150.0, "door_glow_w": 300.0,
}
for _k in list(P):
    _v = os.environ.get("S2V1_LIGHT_" + _k.upper())
    if _v is not None and isinstance(P[_k], (int, float)):
        P[_k] = type(P[_k])(float(_v))

COL = {
    "bulb": "#FFC56A", "door": "#FFC870", "lip": "#D9C0F4", "core": "#9DB2FF",
    "yellow": "#FFD860", "cyan": "#48D8F0", "pink": "#FF6EC0",
    "hall": "#FFE2F2", "door_glow": "#FFCB7A",
}
AXIS_Z, R_WALL = 2.3, 4.2


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _set(obj, attr, val, tag=""):
    try:
        setattr(obj, attr, val)
        return True
    except Exception as e:  # property names move between Blender versions - log, never fail
        print("%s note: %s.%s not set (%s)" % (LOG, tag or type(obj).__name__, attr, e))
        return False


# ------------------------------------------------------------------------------------------------ coordinates
def tb(C, x, d, z):
    """track space (x lateral, d, z height) -> Blender world Vector; beyond the exported frames (d > 80) extrapolate along fwd(80)."""
    if d <= 80.0:
        return Vector(C.track_to_blender(np.array([[x, d, z]], dtype=np.float64))[0])
    f = C.frame_at(80.0)
    w = f["pos"] + f["fwd"] * (d - 80.0) + f["flatRight"] * x + f["flatUp"] * z
    return Vector((w[0], w[2], w[1]))


def to_track(C, Pb):
    """Blender world points (N,3) -> track space (x, d, z) via the nearest exported frame (d 20-80)."""
    F = C._frame_arrays()
    U = np.asarray(Pb, dtype=np.float64)[:, [0, 2, 1]]
    best = np.zeros(len(U), dtype=np.int64); bestd = np.full(len(U), np.inf)
    for k in range(0, len(F["d"])):
        dd = ((U - F["pos"][k]) ** 2).sum(1); m = dd < bestd; bestd[m] = dd[m]; best[m] = k
    rel = U - F["pos"][best]
    return np.stack([(rel * F["flatRight"][best]).sum(1), F["d"][best] + (rel * F["fwd"][best]).sum(1),
                     (rel * F["flatUp"][best]).sum(1)], 1)


def world_verts(o, cap=3000):
    n = len(o.data.vertices)
    co = np.empty(n * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(n, 3)
    if n > cap:
        co = co[np.linspace(0, n - 1, cap).astype(int)]
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


# ------------------------------------------------------------------------------------------------ render / world / fog / grade
def setup_render(sc):
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    ee = sc.eevee
    for k, v in (("taa_render_samples", P["samples"]), ("use_raytracing", True), ("ray_tracing_method", "SCREEN"),
                 ("use_shadows", True), ("use_fast_gi", True), ("fast_gi_method", "GLOBAL_ILLUMINATION"),
                 ("fast_gi_distance", 3.0), ("use_volumetric_shadows", False)):
        _set(ee, k, v, "eevee")
    try:
        ro = ee.ray_tracing_options
        _set(ro, "resolution_scale", "2", "rt"); _set(ro, "use_denoise", True, "rt"); _set(ro, "trace_max_roughness", 0.6, "rt")
    except Exception as e:
        print("%s note: ray_tracing_options (%s)" % (LOG, e))
    vs = sc.view_settings
    _set(vs, "view_transform", P["view"], "view"); _set(vs, "look", "None", "view")
    _set(vs, "exposure", P["exposure"], "view"); _set(vs, "gamma", 1.0, "view")
    _set(sc.display_settings, "display_device", "sRGB", "display")


def setup_world(sc):
    w = bpy.data.worlds.new("S2V1_LGT_World")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = srgb(P["world_hex"]) + (1.0,)
    bg.inputs[1].default_value = P["world_strength"]
    ms = w.mist_settings
    ms.start = P["fog_start"]; ms.depth = max(1.0, P["fog_end"] - P["fog_start"]); ms.falloff = "LINEAR"
    sc.world = w
    for vl in sc.view_layers:
        vl.use_pass_mist = True


def _sock(socks, name):
    return next(s for s in socks if s.name == name and getattr(s, "enabled", True))


def setup_compositor(sc):
    tree = bpy.data.node_groups.new("S2V1_LGT_Comp", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    sc.compositing_node_group = tree
    _set(sc.render, "use_compositing", True, "render")
    N, L = tree.nodes, tree.links
    rl = N.new("CompositorNodeRLayers"); rl.location = (-900, 0)
    out = N.new("NodeGroupOutput"); out.location = (900, 0)
    img = _sock(rl.outputs, "Image")
    # 1) Unity-style linear distance fog: lerp(image, fogColor, mist)   (mist = clamp((z - start) / (end - start)))
    try:
        mix = N.new("ShaderNodeMix"); mix.location = (-600, 0)
        mix.data_type, mix.blend_type, mix.clamp_result = "RGBA", "MIX", False
        fac = next(s for s in mix.inputs if s.enabled and s.name == "Factor")
        cols = [s for s in mix.inputs if s.enabled and s.bl_idname == "NodeSocketColor"]
        L.new(_sock(rl.outputs, "Mist"), fac)
        L.new(img, cols[0]); cols[1].default_value = srgb(P["fog_hex"]) + (1.0,)
        img = next(s for s in mix.outputs if s.enabled)
    except Exception as e:
        print("%s fog mix FAILED (%s) - no fog" % (LOG, e))
    # 2) bloom on emitters only (threshold above every lit surface; only emission > ~1 passes)
    g = N.new("CompositorNodeGlare"); g.location = (-300, 0)
    try:
        _sock(g.inputs, "Type").default_value = "Bloom"
    except Exception:
        _set(g, "glare_type", "BLOOM", "glare")
    for nm, v in (("Threshold", P["bloom_threshold"]), ("Strength", P["bloom_strength"]), ("Size", P["bloom_size"])):
        try:
            _sock(g.inputs, nm).default_value = v
        except Exception as e:
            print("%s glare input %s not set (%s)" % (LOG, nm, e))
    try:
        _sock(g.inputs, "Quality").default_value = "High"
    except Exception:
        pass
    L.new(img, _sock(g.inputs, "Image")); img = _sock(g.outputs, "Image")
    # 3) mild saturation (URP Color Adjustments saturation)
    if abs(P["saturation"] - 1.0) > 1e-3:
        hs = N.new("CompositorNodeHueSat"); hs.location = (0, 0)
        _sock(hs.inputs, "Saturation").default_value = P["saturation"]
        L.new(img, _sock(hs.inputs, "Image")); img = _sock(hs.outputs, "Image")
    L.new(img, out.inputs[0])
    print("%s compositor: fog(mist %.0f-%.0f m %s) -> bloom(th %.2f, str %.2f, size %.2f) -> sat %.2f; glare inputs: %s" % (
        LOG, P["fog_start"], P["fog_end"], P["fog_hex"], P["bloom_threshold"], P["bloom_strength"], P["bloom_size"],
        P["saturation"], [s.name for s in g.inputs if s.enabled]))


# ------------------------------------------------------------------------------------------------ emission strengths
def _bsdfs(m):
    if not (m and m.node_tree):
        return []
    return [n for n in m.node_tree.nodes if n.type in ("BSDF_PRINCIPLED", "EMISSION")]


def set_emission(m, strength):
    """set the emission strength of a material (principled / emission nodes, unlinked inputs, non-black colour).
    The materials-artist can opt a material out with m['s2v1_emit_locked'] = True."""
    if m is None or m.get("s2v1_emit_locked"):
        return False
    hit = False
    for n in _bsdfs(m):
        cs = n.inputs.get("Emission Color") if n.type == "BSDF_PRINCIPLED" else n.inputs.get("Color")
        ss = n.inputs.get("Emission Strength") if n.type == "BSDF_PRINCIPLED" else n.inputs.get("Strength")
        if ss is None or ss.is_linked:
            continue
        if cs is not None and not cs.is_linked and max(cs.default_value[:3]) < 1e-4:
            continue
        ss.default_value = strength; hit = True
    return hit


def is_default(m):
    """an untouched OBJ-import material (base 0.8 grey, rough 1, no emission, no textures) = nobody authored it yet"""
    if not (m and m.node_tree):
        return False
    if any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes):
        return False
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None or b.inputs["Base Color"].is_linked:
        return False
    bc = b.inputs["Base Color"].default_value
    return (abs(bc[0] - 0.8) < 0.01 and abs(bc[1] - 0.8) < 0.01 and abs(bc[2] - 0.8) < 0.01
            and b.inputs["Roughness"].default_value > 0.99 and b.inputs["Emission Strength"].default_value < 1e-4)


# Lighting PREVIEW values for context materials NOBODY has authored yet (is_default) - so the light can be judged; any material the
# materials-artist / water-fx-artist authors is never touched. (sRGB base, metallic, roughness, emission hex or None, emission key, alpha)
CTX_PREVIEW = {
    "M_Gold": ("#C6934F", 1.0, 0.22, None, None, 1.0), "M_GoldDark": ("#8A5A2B", 1.0, 0.30, None, None, 1.0),
    "M_Coin": ("#E0AE4A", 1.0, 0.25, None, None, 1.0), "M_HatchCrest_s2": ("#C6934F", 1.0, 0.22, None, None, 1.0),
    "M_DrumWall": ("#634F9B", 0.85, 0.35, None, None, 1.0), "M_DrumWallFlat": ("#5A4A92", 0.7, 0.38, None, None, 1.0),
    "M_DrumWallHall": ("#3E3F82", 0.6, 0.40, None, None, 1.0), "M_DrumRim": ("#7563B4", 0.85, 0.30, None, None, 1.0),
    "M_HatchViolet_s2": ("#6A4FA8", 0.7, 0.30, None, None, 1.0), "M_MetalPurple": ("#634F9B", 0.85, 0.30, None, None, 1.0),
    "M_DoorMachineBlue_s2": ("#4A5BC0", 0.6, 0.35, None, None, 1.0), "M_DoorMachinePanel_s2": ("#6C5AB0", 0.5, 0.40, None, None, 1.0),
    "M_DoorMachineVent_s2": ("#2E2450", 0.3, 0.60, None, None, 1.0), "M_HallLavender_r7": ("#7D6FC0", 0.3, 0.45, None, None, 1.0),
    "M_HallPink_r7": ("#C97AB5", 0.2, 0.45, None, None, 1.0), "M_PlasticWhite": ("#DCD3EA", 0.0, 0.35, None, None, 1.0),
    "M_ConsolePink_r8": ("#E07AB8", 0.1, 0.35, None, None, 1.0), "M_DoorRainbow_r8": ("#E172B6", 0.2, 0.30, None, None, 1.0),
    "M_RollerFur_s2": ("#F07ABE", 0.0, 0.85, None, None, 1.0), "M_BrushPink": ("#F07ABE", 0.0, 0.85, None, None, 1.0),
    "M_BrushBlue": ("#6FA8F0", 0.0, 0.85, None, None, 1.0), "M_BrushWhite": ("#F0E8F5", 0.0, 0.85, None, None, 1.0),
    "M_HatKnit_v5": ("#7B3FC4", 0.0, 0.9, None, None, 1.0), "M_HatCuff_v5": ("#F2D9E8", 0.0, 0.9, None, None, 1.0),
    "M_HatStripe_v5": ("#F2D9E8", 0.0, 0.9, None, None, 1.0), "M_PomPom_v5": ("#8E4FD6", 0.0, 0.9, None, None, 1.0),
    "M_Fur_v5": ("#F08AAE", 0.0, 0.8, None, None, 1.0), "M_PawPad_v5": ("#F5B5C8", 0.0, 0.6, None, None, 1.0),
    # emitters (strength = lighting-owned)
    "M_Bulb": ("#F3D882", 0.0, 0.2, "#F3D882", "emit_ctx_bulb", 1.0), "M_RimSpark_s2": ("#F3D882", 0.0, 0.2, "#F3D882", "emit_ctx_bulb", 1.0),
    "M_RimLight": ("#B9A2E6", 0.0, 0.3, "#B9A2E6", "emit_ctx_rim", 1.0), "M_RimGlow_s2": ("#D2BDEE", 0.0, 0.3, "#D2BDEE", "emit_ctx_rim", 1.0),
    "M_Neon_Cyan": ("#59CADC", 0.0, 0.2, "#59CADC", "emit_ctx_neon", 1.0), "M_Neon_Pink": ("#E172B6", 0.0, 0.2, "#E172B6", "emit_ctx_neon", 1.0),
    "M_Neon_Yellow": ("#EFD66F", 0.0, 0.2, "#EFD66F", "emit_ctx_neon", 1.0), "M_StarFill_Yellow": ("#EFD66F", 0.0, 0.3, "#EFD66F", "emit_ctx_neon", 1.0),
    "M_ButtonCyan": ("#59CADC", 0.0, 0.3, "#59CADC", "emit_ctx_rim", 1.0), "M_ButtonPink": ("#E172B6", 0.0, 0.3, "#E172B6", "emit_ctx_rim", 1.0),
    "M_ButtonYellow": ("#EFD66F", 0.0, 0.3, "#EFD66F", "emit_ctx_rim", 1.0), "M_ConsoleScreen_r8": ("#59CADC", 0.0, 0.3, "#59CADC", "emit_ctx_rim", 1.0),
    "M_VanishCore": ("#A9B8FF", 0.0, 0.5, "#A9B8FF", "emit_ctx_core", 1.0), "M_VanishGlow": ("#6E52C0", 0.0, 0.5, "#6E52C0", "emit_ctx_rim", 0.5),
    "M_PinkHaze": ("#9F4E86", 0.0, 0.5, "#9F4E86", "emit_ctx_rim", 0.25),
    "M_StarGlow_Cyan": ("#2E8FA8", 0.0, 0.5, "#2E8FA8", "emit_ctx_rim", 0.3), "M_StarGlow_Pink": ("#A8407E", 0.0, 0.5, "#A8407E", "emit_ctx_rim", 0.3),
    "M_StarGlow_Yellow": ("#A8862E", 0.0, 0.5, "#A8862E", "emit_ctx_rim", 0.3),
    "M_StarGlowDoor_Cyan": ("#2E8FA8", 0.0, 0.5, "#2E8FA8", "emit_ctx_rim", 0.3), "M_StarGlowDoor_Pink": ("#A8407E", 0.0, 0.5, "#A8407E", "emit_ctx_rim", 0.3),
    "M_StarGlowDoor_Yellow": ("#A8862E", 0.0, 0.5, "#A8862E", "emit_ctx_rim", 0.3),
    "M_Glass": ("#CFC6F0", 0.0, 0.05, None, None, 0.2), "M_Bubble": ("#E6E0FF", 0.0, 0.05, None, None, 0.15),
}


def ctx_materials():
    filled, emit = [], []
    for name, (base, met, rough, ehex, ekey, alpha) in CTX_PREVIEW.items():
        m = bpy.data.materials.get(name)
        if m is None:
            continue
        if is_default(m):
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = srgb(base) + (1.0,)
            b.inputs["Metallic"].default_value = met
            b.inputs["Roughness"].default_value = rough
            if ehex:
                b.inputs["Emission Color"].default_value = srgb(ehex) + (1.0,)
                b.inputs["Emission Strength"].default_value = 1.0
            else:
                b.inputs["Emission Strength"].default_value = 0.0
            if alpha < 1.0:
                b.inputs["Alpha"].default_value = alpha
                _set(m, "surface_render_method", "DITHERED", m.name)
            m["s2v1_light_preview"] = True
            filled.append(name)
        if ekey and set_emission(m, P[ekey]):
            emit.append("%s=%.2f" % (name, P[ekey]))
    print("%s context preview materials (untouched defaults only): %d %s" % (LOG, len(filled), ",".join(filled)))
    print("%s context emitter strengths: %s" % (LOG, " ".join(emit)))


def part_emission(C, ctx):
    rep = {}
    for tag, key in (("bulb", "emit_bulb"), ("band_lip", "emit_band_lip"), ("star", "emit_star"), ("star_glow", "emit_star_glow")):
        mats = {s.material for o in C.parts(ctx, tag) for s in o.material_slots if s.material}
        rep[tag] = sum(1 for m in mats if set_emission(m, P[key]))
    print("%s part emission strengths set: %s" % (LOG, rep))


# ------------------------------------------------------------------------------------------------ lights
LIGHTS = []   # records for lights_unity.json


def add_light(sc, coll, name, kind, loc, hex_, watts, radius=0.15, cutoff=None, shadow=False, spec=1.0, size=None, aim=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = watts
    ld.color = srgb(hex_)
    _set(ld, "use_shadow", shadow, name)
    _set(ld, "specular_factor", spec, name)
    if kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = radius
    if kind == "AREA" and size:
        ld.shape = "DISK"; ld.size = size
    if cutoff:
        _set(ld, "use_custom_distance", True, name); _set(ld, "cutoff_distance", cutoff, name)
    lo = bpy.data.objects.new(name, ld)
    coll.objects.link(lo)
    lo.location = loc
    if aim is not None:
        lo.rotation_euler = Vector(aim).normalized().to_track_quat("-Z", "Y").to_euler()
    u = (loc[0], loc[2], loc[1])
    LIGHTS.append({"name": name, "blender_type": kind, "unity_type": {"POINT": "Point", "SPOT": "Spot", "AREA": "Area(baked) or Spot"}[kind],
                   "unity_pos": [round(v, 3) for v in u], "color": hex_, "blender_w": round(watts, 2),
                   "unity_intensity_est": round(watts / 39.48, 3), "range_m": cutoff, "shadows": shadow})
    return lo


def sector_lights(C, sc, coll, objs, prefix, n_sect, total_w, hex_, inset, dz_cam, cutoff, min_z=0.35):
    """one point light per angular sector of the emitters' vertices (track space), pulled `inset` m toward the axis and `dz_cam` m
    toward the camera; sectors under the slide (z < min_z) are skipped. Returns the number of lights."""
    if not objs:
        return 0
    V = np.concatenate([world_verts(o) for o in objs])
    T = to_track(C, V)
    y = T[:, 2] - AXIS_Z
    r = np.hypot(T[:, 0], y); ang = np.arctan2(T[:, 0], y)
    sect = np.floor((ang + math.pi) / (2 * math.pi) * n_sect).astype(int) % n_sect
    made = []
    for s in range(n_sect):
        m = sect == s
        if m.sum() < 3:
            continue
        a = math.atan2(np.sin(ang[m]).mean(), np.cos(ang[m]).mean())
        rr = max(0.5, float(r[m].mean()) - inset); dd = float(T[m, 1].mean()) - dz_cam
        x, z = rr * math.sin(a), AXIS_Z + rr * math.cos(a)
        if z < min_z:
            continue
        made.append((x, dd, z))
    for i, (x, dd, z) in enumerate(made):
        add_light(sc, coll, "LGT_S2v1_%s_%02d" % (prefix, i), "POINT", tb(C, x, dd, z), hex_, total_w / max(1, len(made)),
                  radius=0.25, cutoff=cutoff)
    return len(made)


def cluster_by_d(C, objs, gap=1.0):
    items = []
    for o in objs:
        T = to_track(C, world_verts(o, 600))
        items.append((float(np.median(T[:, 1])), o))
    items.sort(key=lambda t: t[0])
    groups = []
    for d, o in items:
        if groups and d - groups[-1][0] < gap:
            groups[-1][1].append(o)
        else:
            groups.append([d, [o]])
    return groups


def setup_lights(C, ctx):
    sc = ctx["scene"]
    for o in list(sc.objects):                      # earlier lights / temp previews of any role never stay
        if o.type == "LIGHT" and (o.name.startswith("LGT_S2v1") or o.name.startswith("WFX_TEMP") or o.name.startswith("DBG_")):
            bpy.data.objects.remove(o, do_unlink=True)
    coll = C.coll("S2V1_LIGHTS")
    n = {}
    # 1) gold bulb rings (warm) - by d cluster of the 'bulb' parts (G1 = nearest = the big luxurious ring)
    groups = cluster_by_d(C, C.parts(ctx, "bulb"))
    for gi, (d, objs) in enumerate(groups):
        tot, ns = (P["g1_total_w"], P["g1_sectors"]) if gi == 0 else (P["g2_total_w"], P["g2_sectors"])
        n["gold%d@%.1f" % (gi + 1, d)] = sector_lights(C, sc, coll, objs, "gold%d" % (gi + 1), int(ns), tot, COL["bulb"],
                                                       inset=0.45, dz_cam=0.30, cutoff=5.0)
    # 2) band lips (lavender) - band A (nearest, thick) brighter
    groups = cluster_by_d(C, C.parts(ctx, "band_lip"))
    for gi, (d, objs) in enumerate(groups):
        tot = P["lipA_total_w"] if gi == 0 else P["lip_total_w"] * (1.0 if d < 60 else 0.7)
        ns = int(P["lip_sectors"]) if d < 60 else 5
        n["lip%d@%.1f" % (gi + 1, d)] = sector_lights(C, sc, coll, objs, "lip%d" % (gi + 1), ns, tot, COL["lip"],
                                                      inset=0.55, dz_cam=0.25, cutoff=4.5)
    # 3) door rim bulbs (warm, context SM_DoorHatch) - ring at the door mouth, a bit inside the rim toward the camera
    made = 0
    for i in range(int(P["door_sectors"])):
        a = -math.pi * 0.62 + i * (math.pi * 1.24 / (P["door_sectors"] - 1))   # upper 220 deg of the rim
        x, z = 4.55 * math.sin(a), AXIS_Z + 4.55 * math.cos(a)
        add_light(sc, coll, "LGT_S2v1_door_%02d" % i, "POINT", tb(C, x, 39.4, z), COL["door"], P["door_total_w"] / P["door_sectors"],
                  radius=0.3, cutoff=5.0); made += 1
    n["door"] = made
    # 4) neon stars: one coloured point just in front of each sign
    made = 0
    for o in C.parts(ctx, "star"):
        T = to_track(C, world_verts(o, 800)); c = T.mean(0)
        yv = c[2] - AXIS_Z; rr = math.hypot(c[0], yv); a = math.atan2(c[0], yv)
        rr2 = max(0.5, rr - 0.40)
        x, z = rr2 * math.sin(a), AXIS_Z + rr2 * math.cos(a)
        col = COL.get(str(o.get("s2v1_color", "yellow")), COL["yellow"])
        add_light(sc, coll, "LGT_S2v1_star_%s" % o.get("s2v1_source", o.name).replace("S2V1_", ""), "POINT",
                  tb(C, x, float(c[1]) - 0.25, z), col, P["star_w"], radius=0.2, cutoff=3.5); made += 1
    n["stars"] = made
    # 5) small cool core accent deep in the tunnel (lights the far drum walls a cool blue-violet; core stays dark through the fog)
    add_light(sc, coll, "LGT_S2v1_core", "POINT", tb(C, 0.0, 92.0, AXIS_Z), COL["core"], P["core_w"], radius=0.5, cutoff=14.0)
    # 6) motivated foreground: machine-hall ceiling glow above the mascot, warm spill from the door bulbs onto the water / foam
    add_light(sc, coll, "LGT_S2v1_hall", "AREA", tb(C, 0.3, 32.6, 3.4), COL["hall"], P["hall_w"], size=2.5, spec=0.2, shadow=True,
              aim=tb(C, 0.3, 33.2, 0.0) - tb(C, 0.3, 32.6, 3.4))
    add_light(sc, coll, "LGT_S2v1_doorglow", "AREA", tb(C, 0.0, 39.2, 3.2), COL["door_glow"], P["door_glow_w"], size=4.0, spec=0.35,
              shadow=False, aim=tb(C, 0.0, 37.0, 0.0) - tb(C, 0.0, 39.2, 3.2))
    print("%s lights: %s (+ core, hall, doorglow) total %d" % (LOG, n, len(LIGHTS)))


def setup_probes(C, ctx):
    """sphere reflection probes along the tunnel = Unity box-projected reflection probes (polished metal reflects the emitters)"""
    sc = ctx["scene"]; coll = C.coll("S2V1_LIGHTS"); made = []
    for d, rad in ((44.0, 7.0), (54.0, 7.0), (66.0, 8.0)):
        try:
            pr = bpy.data.lightprobes.new("PRB_S2v1_d%02d" % d, "SPHERE")
            _set(pr, "influence_distance", rad, "probe"); _set(pr, "falloff", 0.6, "probe")
            po = bpy.data.objects.new("PRB_S2v1_d%02d" % d, pr); coll.objects.link(po)
            po.location = tb(C, 0.0, d, AXIS_Z)
            made.append(po.name)
        except Exception as e:
            print("%s probe d %.0f not made (%s)" % (LOG, d, e))
    print("%s reflection probes: %s" % (LOG, made))
    return made


# ------------------------------------------------------------------------------------------------ entry
def apply(ctx):
    C = ctx["C"]; sc = ctx["scene"]
    LIGHTS.clear()
    setup_render(sc)
    setup_world(sc)
    ctx_materials()
    part_emission(C, ctx)
    setup_lights(C, ctx)
    probes = setup_probes(C, ctx)
    setup_compositor(sc)
    try:
        with open(os.path.join(ctx["out_dir"], "lights_unity.json"), "w") as f:
            json.dump({"params": P, "lights": LIGHTS, "probes": probes,
                       "note": "Unity world = Blender (x, z, y); intensity_est = Blender W / 39.48 (URP linear intensity, point)"}, f, indent=1)
    except Exception as e:
        print("%s lights_unity.json not written (%s)" % (LOG, e))
    print("%s done: engine %s, view %s, samples %d, %d lights" % (LOG, sc.render.engine, sc.view_settings.view_transform,
                                                               P["samples"], len(LIGHTS)))
