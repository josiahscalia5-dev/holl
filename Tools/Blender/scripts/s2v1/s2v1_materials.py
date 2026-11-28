"""S2 Tunnel v1 - MATERIALS (materials-artist; only this role edits this file).

apply(ctx)  - called by the assembly (s2v1_render.py) after s2v1_env.build(): assigns the M_S2v1_* materials
              * to the modeler's tagged parts via C.parts(ctx, tag) (drum, drum_hp, band, band_lip, gold_ring, bulb_socket, bulb,
                star, star_glow, other = star stems), never by object name;
              * to the untextured Unity CONTEXT (door hatch, left machinery, the old deep tunnel beyond d 80) by MATERIAL BASE NAME,
                on OBJECT-linked slots (the shared context materials are never edited; CTX_water / foam / bubbles / pickups / mascot
                and the chevrons in CTX_context belong to the water-fx-artist and are not touched).
bake()      - run headless:  bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_materials.py s2v1_mat_bake
              rebuilds the modeler's track-space parts (s2v1_env.build in an empty scene), bakes the drum_hp perforated shell into the
              drum game meshes (Cycles: tangent normal + material-ID mask, texture-workflow bake_maps.py) and derives the Unity-ready maps
              with numpy into Tools/Blender/work/s2v1/bakes/:
                drum_<A|B>_basecolor.png  sRGB   base colour (metal / slot colour, brushed streaks, panel tone, cavity AO, edge polish)
                drum_<A|B>_ms.png         linear R = metallic, A = smoothness (URP Lit "Metallic Alpha" layout)
                drum_<A|B>_normal.png     linear tangent normal, OpenGL (+Y) = Unity convention (baked + soft rim from the slot mask)
                drum_<A|B>_ao.png         linear cavity AO (already multiplied into basecolor; optional Occlusion map)
                drum_<A|B>_curv.png       linear curvature (0.5 = flat, > 0.5 convex rims) - edge-wear source
                drum_<A|B>_mask.png       linear 1 = metal, 0 = slot (raw bake)
              The env's render_pre handler shows the drum GAME mesh (with these maps) as soon as bakes/drum*normal* exists.
Colours: hex = sRGB display values; Blender gets them linearised. Emission strengths are authored for the 'Standard' view transform
(strength 1 = the hex on screen; > 1 feeds bloom). The lighting-artist owns the final emission scale: every emissive material carries
mat["s2v1_emit_default"] and mat["s2v1_emit_kind"] (bulb | lip | neon | glow | gold | context) so it can be rescaled by kind.
Nothing here samples reference pixels: all colours are typed-in measured medians from the bwk-s2-cinematic-look skill.
"""
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "C:/Users/josia/thanksgiving"
BAKES = ROOT + "/Tools/Blender/work/s2v1/bakes"
BAKE_SKILL = ROOT + "/.claude/skills/texture-workflow/scripts/bake_maps.py"
LOG = "MAT"

# ------------------------------------------------------------------ palette (sRGB hex; measured targets from bwk-s2-cinematic-look)
# drum metal #634F9B (rendered median), slots #3A2F51, gold #C6934F, bulbs #F3D882, lavender glow #DDD1E5,
# neon yellow #EFD66F / cyan #59CADC / pink #E172B6, dark saturated core #68479D
P = {
    "drum_metal": "#6E58AE",      # base albedo a bit above the rendered median (#634F9B): cavity AO + grazing angles pull it down
    "drum_edge": "#B9A2EC",       # polished convex rims of the perforations (curvature)
    "drum_slot": "#1E1733",       # inside the slots (renders ~#3A2F51 with the lit rim + bloom around it)
    "drum_deep": "#5B4596",       # old deep tunnel beyond d 80 (darker, saturated: the original's core is L* 38-45)
    "band": "#6A4CB8",            # rich violet lacquer body
    "band_emit": "#8E6AD8",       # faint inner glow of the band body (the original's bands glow lavender-violet)
    "lip": "#E3CCF6",             # luminous lavender-pink lip (#DDD1E5 measured)
    "gold": "#E7B064",            # polished gold albedo (renders ~#C6934F in the tunnel)
    "gold_emit": "#B8782F",       # warm self-glow of the gold (the bulbs' bounce in the original)
    "gold_dark": "#B98244",
    "socket": "#8E5C2A",
    "bulb": "#FFD98A",            # warm glass (#F3D882 measured with bloom)
    "neon_yellow": "#F4D85E",
    "neon_cyan": "#4FD0E6",
    "neon_pink": "#EC6CBC",
    "stem": "#3B2E5E",
    "hatch_violet": "#6A3EC2",
    "hatch_crest": "#E2CCFF",
    "machine_blue": "#2C3256",
    "machine_panel": "#6C8CE8",
    "machine_vent": "#121838",
    "hall_lavender": "#C9A6EA",
    "hall_pink": "#FF5AAE",
    "plastic_white": "#ECE6F4",
    "console_pink": "#F07AB8",
    "roller_pink": "#F25FAA",
    "hall_wall": "#3A3A78",
    "core": "#6E48A8",
}
# default emission strengths (Standard view; the lighting-artist may rescale by mat["s2v1_emit_kind"])
EMIT = {"lip": 1.35, "bulb": 2.6, "neon": 1.7, "glow": 0.10, "gold": 0.16, "band": 0.10, "crest": 0.9, "ctx_bulb": 2.4,
        "roller": 0.30, "core": 0.45, "drum": 0.0}


def srgb(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (a,)


def _set(b, name, val):
    s = b.inputs.get(name)
    if s is not None:
        try:
            s.default_value = val
        except Exception:
            pass
    return s


def principled(name, base, metallic=0.0, rough=0.4, coat=0.0, coat_rough=0.05, emit_hex=None, emit=0.0, kind=None,
               spec=0.5, sheen=0.0, unity=None):
    """(re)build a Principled material; returns (mat, bsdf, nodes, links)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (0, 0)
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    _set(b, "Base Color", srgb(base))
    _set(b, "Metallic", metallic)
    _set(b, "Roughness", rough)
    _set(b, "Specular IOR Level", spec)
    if coat > 0:
        _set(b, "Coat Weight", coat); _set(b, "Coat Roughness", coat_rough); _set(b, "Coat IOR", 1.5)
    if sheen > 0:
        _set(b, "Sheen Weight", sheen); _set(b, "Sheen Roughness", 0.4)
    if emit_hex and emit > 0:
        _set(b, "Emission Color", srgb(emit_hex)); _set(b, "Emission Strength", emit)
        m["s2v1_emit_default"] = float(emit)
        m["s2v1_emit_kind"] = kind or "other"
    m.diffuse_color = srgb(base)
    if unity:
        m["s2v1_unity"] = unity
    return m, b, nt.nodes, nt.links


# ------------------------------------------------------------------ tunnel part materials
def mat_drum_procedural(name="M_S2v1_DrumMetal", base=None):
    """drum metal without bakes (also what the env handler copies onto drum_hp slot 0): satin blue-violet metal with fine
    circumferential brushing (noise stretched along the tunnel's circumference in object space) - roughness 0.30."""
    m, b, N, L = principled(name, base or P["drum_metal"], 0.72, 0.30, unity="URP Lit: base %s metallic 0.72 smoothness 0.70" % (base or P["drum_metal"]))
    tc = N.new("ShaderNodeTexCoord"); tc.location = (-900, 0)
    mp = N.new("ShaderNodeMapping"); mp.location = (-700, 0); mp.inputs["Scale"].default_value = (1.0, 40.0, 1.0)
    nz = N.new("ShaderNodeTexNoise"); nz.location = (-500, 0); nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Generated"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.location = (-300, -200)
    mr.inputs["To Min"].default_value = 0.26; mr.inputs["To Max"].default_value = 0.36
    L.new(nz.outputs["Fac"], mr.inputs["Value"]); L.new(mr.outputs["Result"], b.inputs["Roughness"])
    return m


def mat_drum_baked(key):
    """drum game mesh with the baked Unity maps (basecolor sRGB, ms = metallic R / smoothness A, normal OpenGL)."""
    files = {k: "%s/drum_%s_%s.png" % (BAKES, key, k) for k in ("basecolor", "ms", "normal")}
    if not all(os.path.exists(f) for f in files.values()):
        return None
    name = "M_S2v1_DrumMetal_" + key
    m, b, N, L = principled(name, P["drum_metal"], 0.72, 0.30,
                            unity="URP Lit: Base Map drum_%s_basecolor.png (sRGB), Metallic Map drum_%s_ms.png (linear, Source = "
                                  "Metallic Alpha), Normal Map drum_%s_normal.png (OpenGL), no Occlusion (AO is in the base map)"
                                  % (key, key, key))

    def img(k, cs, x, y):
        n = N.new("ShaderNodeTexImage"); n.location = (x, y)
        im = bpy.data.images.load(files[k], check_existing=True)
        im.colorspace_settings.name = cs
        if k == "ms":
            im.alpha_mode = "CHANNEL_PACKED"
        n.image = im
        n.interpolation = "Linear"
        return n
    ib = img("basecolor", "sRGB", -700, 300)
    im = img("ms", "Non-Color", -700, 0)
    inn = img("normal", "Non-Color", -700, -300)
    L.new(ib.outputs["Color"], b.inputs["Base Color"])
    sep = N.new("ShaderNodeSeparateColor"); sep.location = (-400, 50)
    L.new(im.outputs["Color"], sep.inputs["Color"])
    L.new(sep.outputs[0], b.inputs["Metallic"])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.location = (-400, -120)
    inv.inputs[0].default_value = 1.0
    L.new(im.outputs["Alpha"], inv.inputs[1])
    L.new(inv.outputs[0], b.inputs["Roughness"])
    nm = N.new("ShaderNodeNormalMap"); nm.location = (-300, -300); nm.inputs["Strength"].default_value = 1.0
    L.new(inn.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_slot():
    m, *_ = principled("M_S2v1_DrumSlot", P["drum_slot"], 0.0, 0.55,
                       unity="(bake source only) slot interior; in Unity it lives in drum_*_basecolor.png")
    return m


def mat_band():
    """rich violet lacquer: violet metallic-ish body under a clear coat; faint violet self-glow keeps the body saturated
    (the original's bands read luminous violet, never grey)."""
    m, b, N, L = principled("M_S2v1_BandLacquer", P["band"], 0.35, 0.30, coat=1.0, coat_rough=0.05,
                            emit_hex=P["band_emit"], emit=EMIT["band"], kind="band",
                            unity="URP Lit (or BWK_Gold violet palette): base %s metallic 0.35 smoothness 0.70, Clear Coat (Complex "
                                  "Lit) 1.0 / smoothness 0.95, emission %s x %.2f" % (P["band"], P["band_emit"], EMIT["band"]))
    return m


def mat_lip():
    m, *_ = principled("M_S2v1_BandLip", P["lip"], 0.0, 0.25, emit_hex=P["lip"], emit=EMIT["lip"], kind="lip",
                       unity="URP Unlit / BWK_Emissive: colour %s, HDR intensity %.2f (bloom)" % (P["lip"], EMIT["lip"]))
    return m


def mat_gold(name="M_S2v1_GoldPolished", base=None, rough=0.18, emit=None):
    base = base or P["gold"]
    emit = EMIT["gold"] if emit is None else emit
    m, *_ = principled(name, base, 1.0, rough, coat=0.4, coat_rough=0.04, emit_hex=P["gold_emit"], emit=emit, kind="gold",
                       unity="URP Lit / BWK_Gold: base %s metallic 1 smoothness %.2f, emission %s x %.2f, needs a reflection "
                             "probe inside the tunnel" % (base, 1 - rough, P["gold_emit"], emit))
    return m


def mat_socket():
    m, *_ = principled("M_S2v1_BulbSocket", P["socket"], 1.0, 0.32, coat=0.3, coat_rough=0.06,
                       unity="URP Lit: base %s metallic 1 smoothness 0.68" % P["socket"])
    return m


def mat_bulb(name="M_S2v1_BulbGlass", strength=None):
    s = EMIT["bulb"] if strength is None else strength
    m, *_ = principled(name, P["bulb"], 0.0, 0.08, coat=1.0, coat_rough=0.02, emit_hex=P["bulb"], emit=s, kind="bulb",
                       unity="URP Unlit / BWK_Emissive: colour %s, HDR intensity %.2f (bloom halo from URP Bloom)" % (P["bulb"], s))
    return m


def mat_neon(colour):
    hexc = P["neon_" + colour]
    m, *_ = principled("M_S2v1_Neon_" + colour.capitalize(), hexc, 0.0, 0.15, coat=1.0, coat_rough=0.02, emit_hex=hexc,
                       emit=EMIT["neon"], kind="neon",
                       unity="URP Unlit / BWK_Emissive: colour %s, HDR intensity %.2f" % (hexc, EMIT["neon"]))
    return m


def mat_star_glow(colour):
    hexc = P["neon_" + colour]
    m, *_ = principled("M_S2v1_StarGlow_" + colour.capitalize(), P["stem"], 0.4, 0.35, emit_hex=hexc, emit=EMIT["glow"],
                       kind="glow", unity="URP Lit: base %s metallic 0.4 smoothness 0.65, emission %s x %.2f" % (P["stem"], hexc, EMIT["glow"]))
    return m


def mat_stem():
    m, *_ = principled("M_S2v1_StarStem", P["stem"], 0.8, 0.3, unity="URP Lit: base %s metallic 0.8 smoothness 0.7" % P["stem"])
    return m


# ------------------------------------------------------------------ context materials (by imported base name)
def ctx_table():
    """imported Unity material base name -> v1 material (built lazily)."""
    lav_unity = "URP Lit: base %s metallic 0.1 smoothness 0.62" % P["hall_lavender"]
    t = {
        # door hatch (SM_DoorHatch_s2) + machinery gold
        "M_Gold": lambda: mat_gold(),
        "M_GoldDark": lambda: mat_gold("M_S2v1_GoldDark", P["gold_dark"], 0.26, EMIT["gold"] * 0.7),
        "M_Coin": lambda: mat_gold(),
        "M_Bulb": lambda: mat_bulb("M_S2v1_CtxBulb", EMIT["ctx_bulb"]),
        "M_HatchViolet_s2": lambda: principled("M_S2v1_HatchViolet", P["hatch_violet"], 0.45, 0.24, coat=1.0, coat_rough=0.04,
                                               emit_hex=P["band_emit"], emit=EMIT["band"], kind="band",
                                               unity="URP Lit: base %s metallic 0.45 smoothness 0.76 + clear coat" % P["hatch_violet"])[0],
        "M_HatchCrest_s2": lambda: principled("M_S2v1_HatchCrest", P["hatch_crest"], 0.0, 0.2, emit_hex=P["hatch_crest"],
                                              emit=EMIT["crest"], kind="lip",
                                              unity="URP Unlit: %s x %.2f" % (P["hatch_crest"], EMIT["crest"]))[0],
        # left machinery
        "M_DoorMachineBlue_s2": lambda: principled("M_S2v1_MachineBlue", P["machine_blue"], 0.45, 0.32, coat=0.6, coat_rough=0.08,
                                                   unity="URP Lit: base %s metallic 0.45 smoothness 0.68" % P["machine_blue"])[0],
        "M_DoorMachinePanel_s2": lambda: principled("M_S2v1_MachinePanel", P["machine_panel"], 0.35, 0.28, coat=0.5,
                                                    unity="URP Lit: base %s metallic 0.35 smoothness 0.72" % P["machine_panel"])[0],
        "M_DoorMachineVent_s2": lambda: principled("M_S2v1_MachineVent", P["machine_vent"], 0.2, 0.5)[0],
        "M_HallLavender_r7": lambda: principled("M_S2v1_HallLavender", P["hall_lavender"], 0.1, 0.38, coat=0.5, unity=lav_unity)[0],
        "M_HallPink_r7": lambda: principled("M_S2v1_HallPink", P["hall_pink"], 0.05, 0.35, coat=0.5)[0],
        "M_PlasticWhite": lambda: principled("M_S2v1_PlasticWhite", P["plastic_white"], 0.0, 0.3, coat=0.4)[0],
        "M_ConsolePink_r8": lambda: principled("M_S2v1_ConsolePink", P["console_pink"], 0.05, 0.35, coat=0.4)[0],
        "M_RollerFur_s2": lambda: principled("M_S2v1_RollerFur", P["roller_pink"], 0.0, 0.75, sheen=1.0,
                                             emit_hex=P["roller_pink"], emit=EMIT["roller"], kind="context",
                                             unity="BWK_Fur / BWK_Soft: colour %s, self glow %.2f" % (P["roller_pink"], EMIT["roller"]))[0],
        "M_DrumWallHall": lambda: principled("M_S2v1_HallWall", P["hall_wall"], 0.55, 0.36,
                                             unity="URP Lit: base %s metallic 0.55 smoothness 0.64" % P["hall_wall"])[0],
        # old deep tunnel (d > 80): darker saturated violet so the core stays L* 38-45
        "M_DrumWall": lambda: mat_drum_procedural("M_S2v1_DrumDeep", P["drum_deep"]),
        "M_MouthDrum": lambda: mat_drum_procedural("M_S2v1_DrumDeep", P["drum_deep"]),
        "M_DrumRim": lambda: mat_band(),
        "M_RimLight": lambda: mat_lip(),
        "M_RimGlow_s2": lambda: mat_lip(),
        "M_RimSpark_s2": lambda: mat_lip(),
        "M_Neon_Yellow": lambda: mat_neon("yellow"),
        "M_Neon_Cyan": lambda: mat_neon("cyan"),
        "M_Neon_Pink": lambda: mat_neon("pink"),
        "M_StarGlow_Yellow": lambda: mat_star_glow("yellow"),
        "M_StarGlow_Cyan": lambda: mat_star_glow("cyan"),
        "M_StarGlow_Pink": lambda: mat_star_glow("pink"),
        "M_StarGlowDoor_Yellow": lambda: mat_star_glow("yellow"),
        "M_StarGlowDoor_Cyan": lambda: mat_star_glow("cyan"),
        "M_StarGlowDoor_Pink": lambda: mat_star_glow("pink"),
        "M_StarFill_Yellow": lambda: mat_star_glow("yellow"),
        "M_VanishCore": lambda: principled("M_S2v1_Core", P["core"], 0.0, 0.5, emit_hex=P["core"], emit=EMIT["core"], kind="core",
                                           unity="URP Unlit: %s x %.2f (dark saturated core, never white)" % (P["core"], EMIT["core"]))[0],
        "M_VanishGlow": lambda: principled("M_S2v1_Core", P["core"], 0.0, 0.5, emit_hex=P["core"], emit=EMIT["core"], kind="core")[0],
    }
    return t


CTX_COLLS = ("CTX_machinery", "CTX_old_tunnel_wall", "CTX_old_tunnel_rings", "CTX_old_tunnel_stars")


def base_name(m):
    if m is None:
        return None
    n = m.name
    if len(n) > 4 and n[-4] == "." and n[-3:].isdigit():
        n = n[:-4]
    return n


def assign_all(objs, mat):
    for o in objs:
        if o.type != "MESH":
            continue
        if not o.material_slots:
            o.data.materials.append(mat)
        for s in o.material_slots:
            s.material = mat


def apply_context(ctx):
    table = ctx_table()
    built = {}
    n_obj = n_slot = 0
    missing = {}
    for cname in CTX_COLLS:
        c = bpy.data.collections.get(cname)
        if not c:
            continue
        for o in c.all_objects:
            if o.type != "MESH":
                continue
            hit = False
            for s in o.material_slots:
                bn = base_name(s.material)
                if bn in table:
                    if bn not in built:
                        built[bn] = table[bn]()
                    s.link = "OBJECT"
                    s.material = built[bn]
                    n_slot += 1; hit = True
                elif bn:
                    missing[bn] = missing.get(bn, 0) + 1
            n_obj += hit
    print("CHECK %s context: %d slots on %d objects re-materialed; unmapped: %s" % (LOG, n_slot, n_obj, sorted(missing)[:20]))


def apply(ctx):
    C = ctx["C"]
    # drum: baked game material per drum mesh (A = 40.2-62, B = 62-80) or the procedural metal (no bakes / hp view)
    proc = mat_drum_procedural()
    for o in C.parts(ctx, "drum"):
        key = str(o.get("s2v1_source", "")).replace("S2V1_drum_", "")
        mb = mat_drum_baked(key)
        assign_all([o], mb or proc)
        print("CHECK %s drum %s -> %s" % (LOG, o.name, (mb or proc).name))
    slot = mat_slot()
    for o in C.parts(ctx, "drum_hp"):
        if len(o.material_slots) >= 2:
            o.material_slots[0].material = proc
            o.material_slots[1].material = slot
        else:
            assign_all([o], slot)
    assign_all(C.parts(ctx, "band"), mat_band())
    assign_all(C.parts(ctx, "band_lip"), mat_lip())
    assign_all(C.parts(ctx, "gold_ring"), mat_gold())
    assign_all(C.parts(ctx, "bulb_socket"), mat_socket())
    assign_all(C.parts(ctx, "bulb"), mat_bulb())
    for o in C.parts(ctx, "star"):
        assign_all([o], mat_neon(str(o.get("s2v1_color", "yellow"))))
    for o in C.parts(ctx, "star_glow"):
        assign_all([o], mat_star_glow(str(o.get("s2v1_color", "yellow"))))
    assign_all(C.parts(ctx, "other"), mat_stem())
    for part in ("drum", "drum_hp", "band", "band_lip", "gold_ring", "bulb_socket", "bulb", "star", "star_glow", "other"):
        print("CHECK %s part %-12s %d objects" % (LOG, part, len(C.parts(ctx, part))))
    apply_context(ctx)


# ------------------------------------------------------------------ bake (headless entry point)
def _blur(a, rad_u, rad_v, passes=3):
    """separable box blur, wrap along u (axis 1 = around the drum), clamp along v (axis 0)."""
    out = a.astype(np.float32)
    ru, rv = max(0, int(round(rad_u))), max(0, int(round(rad_v)))
    for _ in range(passes):
        if ru:
            acc = np.zeros_like(out)
            for k in range(-ru, ru + 1):
                acc += np.roll(out, k, axis=1)
            out = acc / (2 * ru + 1)
        if rv:
            pad = np.pad(out, ((rv, rv), (0, 0)), mode="edge")
            cs = np.cumsum(np.pad(pad, ((1, 0), (0, 0))), axis=0)
            out = (cs[2 * rv + 1:] - cs[:-2 * rv - 1]) / (2 * rv + 1)
    return out


def _img_arr(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


def _save(name, arr, path, colorspace):
    h, w = arr.shape[:2]
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, w, h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = colorspace
    a = np.ones((h, w, 4), dtype=np.float32)
    a[..., :arr.shape[2]] = np.clip(arr, 0, 1)
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    print("CHECK %s wrote %s (%dx%d, %s)" % (LOG, path, w, h, colorspace))


def _lin2srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def derive_maps(key, nrm_img, msk_img, len_u, len_v):
    """Unity-ready maps from the raw bakes (tangent normal + metal/slot mask). len_u / len_v = metres covered by U / V."""
    N0 = _img_arr(nrm_img)[..., :3] * 2.0 - 1.0
    M = np.clip(_img_arr(msk_img)[..., 0], 0, 1)
    H, W = M.shape
    pu, pv = len_u / W, len_v / H                       # metres per pixel
    rng = np.random.default_rng(4242 + sum(map(ord, key)))
    # soft pressed rim: height = blurred mask (2 cm), depth 2 cm -> extra normal tilt (the baked 1 cm bevel is ~1 px)
    hgt = _blur(M, 0.012 / pu, 0.012 / pv, 3) * 0.020
    dhu = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * pu)
    dhv = np.gradient(hgt, axis=0) / pv
    nx = N0[..., 0] - dhu
    ny = N0[..., 1] - dhv
    nz = np.maximum(N0[..., 2], 0.2)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    NX, NY, NZ = nx / ln, ny / ln, nz / ln
    # curvature (divergence of the normal xy): > 0 = convex rim
    div = (np.roll(NX, -1, 1) - np.roll(NX, 1, 1)) / 2 + np.gradient(NY, axis=0)
    curv = np.clip(0.5 + 2.5 * _blur(div, 1, 1, 1), 0, 1)
    # cavity AO from the slot geometry (inside the slot dark, a soft dark halo on the metal next to it)
    near = _blur(M, 0.03 / pu, 0.03 / pv, 3)
    ao = np.clip(0.15 + 0.85 * (M * (0.55 + 0.45 * near ** 0.6) + (1 - M) * 0.10), 0, 1)
    # brushed circumferential streaks (rows along u vary slowly) + large panel tone variation (~1.5 m)
    rows = _blur(rng.standard_normal((H, 1)).astype(np.float32), 0, 1.5, 2)
    rows = rows / (rows.std() + 1e-6)
    fine = _blur(rng.standard_normal((H, W)).astype(np.float32), 0.10 / pu, 0.6, 2)
    fine = fine / (fine.std() + 1e-6)
    pan = _blur(rng.standard_normal((max(8, H // 64), max(8, W // 64))).astype(np.float32), 2, 2, 2)
    pan = np.kron(pan, np.ones((H // pan.shape[0] + 1, W // pan.shape[1] + 1), dtype=np.float32))[:H, :W]
    pan = _blur(pan, 0.4 / pu, 0.4 / pv, 2); pan = pan / (pan.std() + 1e-6)
    var = 1.0 + 0.035 * rows + 0.025 * fine + 0.05 * pan
    metal = np.array(srgb(P["drum_metal"])[:3], dtype=np.float32)
    edge = np.array(srgb(P["drum_edge"])[:3], dtype=np.float32)
    slot = np.array(srgb(P["drum_slot"])[:3], dtype=np.float32)
    e = np.clip((curv - 0.55) * 3.0, 0, 1)[..., None] * M[..., None]
    base = metal[None, None] * var[..., None]
    base = base * (1 - 0.55 * e) + edge[None, None] * 0.55 * e
    base = base * M[..., None] + slot[None, None] * (1 - M[..., None])
    base = base * (0.30 + 0.70 * ao[..., None])
    met = M * 0.72
    smooth = M * np.clip(0.70 + 0.03 * rows + 0.03 * fine, 0.55, 0.80) + (1 - M) * 0.30
    ms = np.zeros((H, W, 4), dtype=np.float32)
    ms[..., 0] = met; ms[..., 3] = smooth
    nrm = np.stack([NX * 0.5 + 0.5, NY * 0.5 + 0.5, NZ * 0.5 + 0.5], -1)
    _save("drum_%s_basecolor" % key, _lin2srgb(base), "%s/drum_%s_basecolor.png" % (BAKES, key), "sRGB")
    _save("drum_%s_ms" % key, ms, "%s/drum_%s_ms.png" % (BAKES, key), "Non-Color")
    _save("drum_%s_ao" % key, np.repeat(ao[..., None], 3, 2), "%s/drum_%s_ao.png" % (BAKES, key), "Non-Color")
    _save("drum_%s_curv" % key, np.repeat(curv[..., None], 3, 2), "%s/drum_%s_curv.png" % (BAKES, key), "Non-Color")
    _save("drum_%s_mask" % key, np.repeat(M[..., None], 3, 2), "%s/drum_%s_mask.png" % (BAKES, key), "Non-Color")
    _save("drum_%s_normal" % key, nrm, "%s/drum_%s_normal.png" % (BAKES, key), "Non-Color")   # last: the env handler keys on it
    print("CHECK %s drum_%s: metal share %.2f, base mean sRGB %s" % (LOG, key, M.mean(),
          np.round(_lin2srgb(base[M > 0.5].mean(0)) * 255).astype(int).tolist()))


def bake(sizes=None, samples=4):
    import importlib.util
    import runpy
    import time
    sizes = sizes or {"A": 2048, "B": 1024}
    t0 = time.time()
    sys.path.insert(0, HERE)
    import s2v1_common as C
    bpy.ops.wm.read_factory_settings(use_empty=True)
    spec = importlib.util.spec_from_file_location("s2v1_env", os.path.join(HERE, "s2v1_env.py"))
    env = importlib.util.module_from_spec(spec); spec.loader.exec_module(env)
    ctx = {"scene": bpy.context.scene, "world_objects": [], "track_objects": [], "C": C, "tag": "bake", "out_dir": BAKES}
    objs = env.build(ctx)
    for h in list(bpy.app.handlers.render_pre):
        if getattr(h, "__name__", "") == "_drum_view":
            bpy.app.handlers.render_pre.remove(h)
    lows = {str(o.name).replace("S2V1_drum_", ""): o for o in objs if o.get("s2v1_part") == "drum"}
    hps = [o for o in objs if o.get("s2v1_part") == "drum_hp"]
    for o in objs:
        if o.get("s2v1_part") not in ("drum", "drum_hp"):
            bpy.data.objects.remove(o, do_unlink=True)
    white = bpy.data.materials.new("BAKE_white"); white.use_nodes = True
    black = bpy.data.materials.new("BAKE_black"); black.use_nodes = True
    for m, v in ((white, 1.0), (black, 0.0)):
        nt = m.node_tree; nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (v, v, v, 1); em.inputs[1].default_value = 1.0
        out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs["Surface"])
    for h in hps:
        mats = h.data.materials
        if len(mats) >= 2:
            mats[0] = white; mats[1] = black
        else:
            mats[0] = black
    os.makedirs(BAKES + "/raw", exist_ok=True)
    try:
        bpy.context.scene.cycles.device = "CPU"
    except Exception:
        pass
    for key, low in sorted(lows.items()):
        size = sizes.get(key, 1024)
        # normal + emit only (no AO bake: the low drum is coincident with the hp wall and would occlude every AO ray;
        # the cavity AO is derived from the slot mask in derive_maps instead)
        t1 = time.time()
        res = runpy.run_path(BAKE_SKILL, init_globals={"ARGS": {
            "low": low.name, "high": [h.name for h in hps], "maps": ["normal", "emit"], "size": size, "extrusion": 0.02,
            "max_ray_distance": 0.5, "samples": samples, "out_dir": BAKES + "/raw", "overwrite": True}})["result"]
        print("CHECK %s bake %s %dpx in %.1f s -> %s" % (LOG, key, size, time.time() - t1, res.get("images") or res))
        nrm = bpy.data.images.get("T_%s_Normal" % low.name)
        msk = bpy.data.images.get("T_%s_Emit" % low.name)
        # metres covered by the UVs: u = full circumference, v = the drum's d range
        co = np.empty(len(low.data.vertices) * 3); low.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        len_v = float(co[:, 1].max() - co[:, 1].min())
        derive_maps(key, nrm, msk, 2 * math.pi * 4.2, len_v)
    print("DONE %s bake in %.1f s" % (LOG, time.time() - t0))


if __name__ == "__main__":
    bake()
