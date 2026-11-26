"""Bubble Wash Kingdom - corrected ending of the cinematic intro (hybrid clean-plate composite, agent 5).

Headless, deterministic.  Every path comes from environment variables so no private image is ever referenced from a
tracked file; all outputs that contain footage pixels go to Captures/cinematic/ (gitignored).

  BWK_STAGE        plate | scene | render | encode | assemble   (comma list allowed, e.g. "plate,scene,render")
  BWK_FRAMES_DIR   folder with the original frames fr_<frame>_<time>s.png (Reference/intro_handoff/frames/all_11s_end)
  BWK_VIDEO        the original intro mp4 (assemble stage only; read, never modified)
  BWK_OUT          output folder (e.g. Captures/cinematic/test_v1)
  BWK_MASCOT       mascot .blend (default: Tools/Blender/work/mascot_v4/READY.json if present, else the stand-in
                   Tools/Blender/work/mascot_rig.blend)
  BWK_RANGE        scene frames to render, "a-b" (scene frame == original video frame index, 0-based)
  BWK_RES          output percentage of 720x1280 (default 75 -> 540x960)
  BWK_SAMPLES      EEVEE samples (default 16)
  BWK_END          last frame of the new ending (default 407 = 17.0 s)

Timeline (24 fps, frame numbers of the original video):
  0-317    original footage, untouched (last frame without any pixel of the wrong mascot)
  318-324  original pixels with the faint star / hat hint in the towel gap painted out (stage "plate")
  325-END  Blender comp: clean plate (painted 324) camera-projected on proxies, top towel lifted by the mascot,
           camera push-in continued as a focal-length animation.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
W, H = 720, 1280
FPS = 24
CUT_LAST_ORIG = 317
PAINT_FIRST, PAINT_LAST = 318, 324
SHOT_FIRST = 325
VFOV = math.radians(58.0)
F_PX = (H / 2) / math.tan(VFOV / 2)
SENSOR_H = 24.0
BASE_LENS = (SENSOR_H / 2) / math.tan(VFOV / 2)

STAGES = [s.strip() for s in os.environ.get("BWK_STAGE", "plate,scene").split(",") if s.strip()]
FRAMES_DIR = os.environ.get("BWK_FRAMES_DIR", os.path.join(ROOT, "Reference", "intro_handoff", "frames", "all_11s_end"))
OUT = os.path.abspath(os.environ.get("BWK_OUT", os.path.join(ROOT, "Captures", "cinematic", "test_v1")))
PLATE_DIR = os.path.join(OUT, "plate")
BLEND_OUT = os.path.join(ROOT, "Tools", "Blender", "work", "intro_ending.blend")
END = int(os.environ.get("BWK_END", "407"))
RES = int(os.environ.get("BWK_RES", "75"))
SAMPLES = int(os.environ.get("BWK_SAMPLES", "16"))


def log(*a):
    print("[intro]", *a, flush=True)


# ---------------------------------------------------------------------------------------------- image helpers
def load_px(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3].copy()


def save_px(arr, path):
    h, w, _ = arr.shape
    img = bpy.data.images.new("tmp_out", w, h, alpha=False)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(arr, 0.0, 1.0)
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def frame_file(n):
    import glob
    hits = glob.glob(os.path.join(FRAMES_DIR, "fr_%04d_*.png" % n))
    if not hits:
        raise FileNotFoundError("original frame %d not found in %s" % (n, FRAMES_DIR))
    return hits[0]


def shift_max(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out = np.maximum(out, np.roll(np.roll(m, dy, 0), dx, 1))
    return out


def box_blur(m, r):
    out = np.zeros_like(m)
    n = 0
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out += np.roll(np.roll(m, dy, 0), dx, 1)
            n += 1
    return out / n


# ---------------------------------------------------------------------------------------------- stage: plate
# The wrong mascot's beanie (dark purple knit with a dim yellow star) is visible in the shadow gap under the top
# towel from frame 318.  Paint it out: key the yellow star, fill it and the knit with the gap's own shadow colour.
GAP_ROI = (250, 760, 390, 840)   # x0, y0, x1, y1 (top-down pixels of the 720x1280 frame)


def paint_gap(a):
    x0, y0, x1, y1 = GAP_ROI
    roi = a[y0:y1, x0:x1].copy()
    r, g, b = roi[..., 0], roi[..., 1], roi[..., 2]
    luma = 0.3 * r + 0.59 * g + 0.11 * b
    star = (((r + g) * 0.5 - b) > 0.05) & (r > 0.22) & (g > 0.18) & (luma < 0.75)
    knit = (luma < 0.30) & (b > r * 0.9)                 # dark purple knit / shadow
    m = shift_max(star.astype(np.float32), 3)
    m = np.clip(box_blur(m, 2) * 1.5, 0.0, 1.0)
    dark = (m < 0.01) & (luma < 0.28)
    fill = np.median(roi[dark], axis=0) if dark.sum() > 20 else np.array([0.18, 0.14, 0.22], np.float32)
    # smooth the knit texture (its rib pattern could still read as a beanie): blend toward a blurred version
    blur = np.stack([box_blur(roi[..., c], 3) for c in range(3)], -1)
    k = np.clip(box_blur(knit.astype(np.float32), 2), 0, 1)[..., None] * 0.7
    roi = roi * (1 - k) + blur * k
    roi = roi * (1 - m[..., None]) + fill[None, None, :] * m[..., None]
    # feather the ROI border back into the original
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
    e = np.minimum.reduce([xx, yy, (x1 - x0 - 1) - xx, (y1 - y0 - 1) - yy]).astype(np.float32)
    fe = np.clip(e / 6.0, 0, 1)[..., None]
    out = a.copy()
    out[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - fe) + roi * fe
    return out, int(star.sum()), int(knit.sum())


def stage_plate():
    os.makedirs(PLATE_DIR, exist_ok=True)
    for n in range(PAINT_FIRST, PAINT_LAST + 1):
        a = load_px(frame_file(n))
        p, ns, nk = paint_gap(a)
        save_px(p, os.path.join(PLATE_DIR, "plate_%04d.png" % n))
        log("plate %d: star px %d, knit px %d, max change %.3f" % (n, ns, nk, float(np.abs(p - a).max())))
    log("CHECK plates written to", PLATE_DIR)


# ---------------------------------------------------------------------------------------------- geometry helpers
def scr_to_world(sx, sy, d):
    """Screen pixel (top-down) + depth along +Y -> world point for the base camera at the origin looking +Y."""
    return Vector(((sx - W / 2) / F_PX * d, d, (H / 2 - sy) / F_PX * d))


def world_to_uv(p):
    return ((p.x / p.y) * F_PX / W + 0.5, (p.z / p.y) * F_PX / H + 0.5)


def pile_depth(sx, sy):
    """Proxy depth of the towel pile surface (the pile faces the camera, its top recedes)."""
    t = np.clip((sy - 560.0) / 720.0, 0.0, 1.2)
    d = 0.62 - 0.22 * t
    d += 0.05 * ((sx - 360.0) / 420.0) ** 2
    return d


GAP_Y = 790.0           # front edge of the top towel at the emergence point (screen y)
GAP_X0, GAP_X1 = 170.0, 470.0
EMERGE = (345.0, 792.0)


def gap_edge(sx):
    """Screen y of the top towel's free front edge (only between GAP_X0 and GAP_X1; outside it the towel is
    tucked into the pile)."""
    return GAP_Y - 18.0 * ((sx - 330.0) / 160.0) ** 2


def make_grid(name, x0, x1, y0, y1, nx, ny, depth_fn, keep=None):
    verts, uvs, idx = [], [], {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            sx = x0 + (x1 - x0) * i / nx
            sy = y0 + (y1 - y0) * j / ny
            if keep is not None and not keep(sx, sy):
                continue
            idx[(i, j)] = len(verts)
            p = scr_to_world(sx, sy, depth_fn(sx, sy))
            verts.append(p)
            uvs.append(world_to_uv(p))
    faces = []
    for j in range(ny):
        for i in range(nx):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k in idx for k in q):
                faces.append([idx[k] for k in reversed(q)])
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    uvl = me.uv_layers.new(name="proj")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uvl.data[li].uv = uvs[vi]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for poly in me.polygons:
        poly.use_smooth = True
    # rest normals for the relighting ratio
    me.update()
    a = me.attributes.new("rest_n", 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set("vector", [c for v in me.vertices for c in v.normal])
    return ob


# ---------------------------------------------------------------------------------------------- materials
def plate_material(name, img, mode, shadow_empty=None):
    """mode: 'backdrop' (pure plate) | 'towel' (plate x relight ratio x contact shadow) | 'under' (dark gap)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    emi = N.new("ShaderNodeEmission")
    emi.inputs["Strength"].default_value = 1.0
    L.new(emi.outputs[0], out.inputs["Surface"])
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "proj"
    tex = N.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = 'Linear'
    tex.extension = 'EXTEND'
    L.new(uv.outputs[0], tex.inputs[0])
    col = tex.outputs["Color"]
    if mode == 'backdrop':
        L.new(col, emi.inputs["Color"])
        return m

    def vmath(op, a, b=None):
        n = N.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (tuple, list)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs["Value"] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else n.outputs["Vector"]

    def fmath(op, a, b=None, clamp=False):
        n = N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    def mixc(fac, a, b, blend='MULTIPLY'):
        n = N.new("ShaderNodeMix")
        n.data_type = 'RGBA'
        n.blend_type = blend
        n.inputs[0].default_value = 1.0
        if isinstance(fac, (int, float)):
            n.inputs[0].default_value = fac
        else:
            L.new(fac, n.inputs[0])
        for sock, v in ((6, a), (7, b)):
            if isinstance(v, (tuple, list)):
                n.inputs[sock].default_value = v
            else:
                L.new(v, n.inputs[sock])
        return n.outputs[2]

    geo = N.new("ShaderNodeNewGeometry")
    rest = N.new("ShaderNodeAttribute")
    rest.attribute_type = 'GEOMETRY'
    rest.attribute_name = "rest_n"
    Ldir = tuple(Vector((0.0, -0.45, 1.0)).normalized())
    lam_now = fmath('ADD', 0.35, fmath('MULTIPLY', 0.65, fmath('MAXIMUM', vmath('DOT_PRODUCT', geo.outputs["Normal"], Ldir), 0.0)))
    lam_rest = fmath('ADD', 0.35, fmath('MULTIPLY', 0.65, fmath('MAXIMUM', vmath('DOT_PRODUCT', rest.outputs["Vector"], Ldir), 0.0)))
    ratio = fmath('MINIMUM', fmath('DIVIDE', lam_now, lam_rest), 1.35)
    back = fmath('SUBTRACT', 1.0, fmath('MULTIPLY', geo.outputs["Backfacing"], 0.55))
    f = fmath('MULTIPLY', ratio, back)
    if shadow_empty is not None:
        tc = N.new("ShaderNodeTexCoord")
        tc.object = shadow_empty
        r = vmath('LENGTH', tc.outputs["Object"])
        sh = N.new("ShaderNodeMapRange")
        sh.interpolation_type = 'SMOOTHSTEP'
        sh.inputs["From Min"].default_value = 0.55
        sh.inputs["From Max"].default_value = 1.6
        sh.inputs["To Min"].default_value = 0.6
        sh.inputs["To Max"].default_value = 1.0
        L.new(r, sh.inputs["Value"])
        # shadow strength animated by the empty's custom 'amount' is approximated by its scale: tiny = no shadow
        f = fmath('MULTIPLY', f, sh.outputs["Result"])
    if mode == 'under':
        under = N.new("ShaderNodeAttribute")
        under.attribute_type = 'GEOMETRY'
        under.attribute_name = "under"
        dk = fmath('SUBTRACT', 1.0, fmath('MULTIPLY', under.outputs["Fac"], 0.62))
        f = fmath('MULTIPLY', f, dk)
        col = mixc(fmath('MULTIPLY', under.outputs["Fac"], 0.5), col, (0.55, 0.42, 0.75, 1.0))
    fc = N.new("ShaderNodeCombineColor")
    for i in range(3):
        L.new(f, fc.inputs[i])
    L.new(mixc(1.0, col, fc.outputs[0]), emi.inputs["Color"])
    return m


# ---------------------------------------------------------------------------------------------- mascot
def mascot_source():
    env = os.environ.get("BWK_MASCOT")
    if env:
        return env, "env"
    ready = os.path.join(ROOT, "Tools", "Blender", "work", "mascot_v4", "READY.json")
    if os.path.exists(ready):
        with open(ready) as f:
            info = json.load(f)
        for k in ("blend", "blend_path", "file", "path"):
            if k in info and str(info[k]).endswith(".blend"):
                p = info[k] if os.path.isabs(info[k]) else os.path.join(ROOT, info[k])
                return p, "v4"
    return os.path.join(ROOT, "Tools", "Blender", "work", "mascot_rig.blend"), "stand-in"


READY = os.path.join(ROOT, "Tools", "Blender", "work", "mascot_v4", "READY.json")


def load_v4(path):
    """Agent 1's v4 model (no armature yet): every listed object is parented to an animatable control empty at its
    ground origin; each eye (+ catchlights) gets a pivot empty at the eye centre for blinks (READY.json face note)."""
    with open(READY) as f:
        info = json.load(f)
    lm_path = os.path.join(os.path.dirname(READY), "mascot_v4_landmarks.json")
    lm = json.load(open(lm_path)) if os.path.exists(lm_path) else {}
    names = set(info.get("objects") or [])
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if not names or n in names]
    sc = bpy.context.scene
    obs = [o for o in dst.objects if o is not None]
    for o in obs:
        sc.collection.objects.link(o)
        if o.animation_data:
            o.animation_data_clear()
    ctrl = bpy.data.objects.new("MascotCtrl", None)
    sc.collection.objects.link(ctrl)
    bpy.context.view_layer.update()
    for o in obs:
        if o.parent is None or o.parent not in obs:
            mw = o.matrix_world.copy()
            o.parent = ctrl
            o.matrix_world = mw
    pivots = []
    bpy.context.view_layer.update()
    for tag in ("L", "R"):
        S = (lm.get("eyes", {}).get(tag, {}) or {}).get("S")
        eye = bpy.data.objects.get("Eye." + tag)
        if S is None or eye is None:
            continue
        pv = bpy.data.objects.new("EyePivot." + tag, None)
        sc.collection.objects.link(pv)
        pv.parent = ctrl
        pv.location = S
        bpy.context.view_layer.update()
        for o in obs:
            if o.name == "Eye." + tag or o.name.startswith("Catchlight." + tag):
                if o.parent is not None and o.parent.name.startswith("Eye."):
                    continue
                mw = o.matrix_world.copy()
                o.parent = pv
                o.matrix_world = mw
        pivots.append(pv)
    hat = lm.get("hat", {})
    height = (hat.get("pom_c", [0, 0, 1.378])[2] + hat.get("pom_r", 0.27))
    log("v4 objects %d, eye pivots %d, height %.3f" % (len(obs), len(pivots), height))
    return ctrl, pivots, height, [o.type for o in obs]


def append_mascot(path):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    arm, meshes = None, []
    for ob in dst.objects:
        if ob is None:
            continue
        if ob.type in ('MESH', 'ARMATURE', 'CURVES', 'EMPTY'):
            bpy.context.scene.collection.objects.link(ob)
        if ob.type == 'ARMATURE' and arm is None:
            arm = ob
        if ob.type == 'MESH':
            meshes.append(ob)
    return arm, meshes


def stand_in_fur(obj):
    """Same look as the rig's preview fur (Voronoi strands on the existing shell layers, pushed along the normal)."""
    me = obj.data
    if "ShellUV" not in me.uv_layers and "ShellUV" not in me.attributes:
        log("no ShellUV on", obj.name, "- fur skipped")
        return
    if "bwk_rest" not in me.attributes:
        a = me.attributes.new("bwk_rest", 'FLOAT_VECTOR', 'POINT')
        a.data.foreach_set("vector", [c for v in me.vertices for c in v.co])
    ng = bpy.data.node_groups.new("BWK_FurPush", 'GeometryNodeTree')
    ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, l = ng.nodes, ng.links
    gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    at = n.new("GeometryNodeInputNamedAttribute")
    at.data_type = 'FLOAT_VECTOR'
    at.inputs["Name"].default_value = "ShellUV"
    sep = n.new("ShaderNodeSeparateXYZ")
    m1 = n.new("ShaderNodeMath")
    m1.operation = 'MULTIPLY'
    m2 = n.new("ShaderNodeMath")
    m2.operation = 'MULTIPLY'
    m2.inputs[1].default_value = 0.030
    nrm = n.new("GeometryNodeInputNormal")
    sc = n.new("ShaderNodeVectorMath")
    sc.operation = 'SCALE'
    sp = n.new("GeometryNodeSetPosition")
    l.new(gi.outputs[0], sp.inputs["Geometry"])
    l.new(next(s for s in at.outputs if s.type == 'VECTOR' and s.enabled), sep.inputs[0])
    l.new(sep.outputs[0], m1.inputs[0])
    l.new(sep.outputs[1], m1.inputs[1])
    l.new(m1.outputs[0], m2.inputs[0])
    l.new(nrm.outputs["Normal"], sc.inputs[0])
    l.new(m2.outputs[0], sc.inputs["Scale"])
    l.new(sc.outputs["Vector"], sp.inputs["Offset"])
    l.new(sp.outputs["Geometry"], go.inputs[0])
    mod = obj.modifiers.new("FurPush", 'NODES')
    mod.node_group = ng
    for mname, root, tip, proot, ptip, dens, rad, sheen in (
            ("M_Fur", "#D9607F", "#FFB3C4", "#E9DCE4", "#FFFFFF", 420.0, 0.47, "#FFC6DA"),
            ("M_PomPom", "#5A2AA6", "#B88BF0", "#5A2AA6", "#B88BF0", 380.0, 0.5, "#D9B8FF")):
        mat = bpy.data.materials.get(mname)
        if mat is not None:
            fur_material(mat, root, tip, proot, ptip, dens, rad, sheen)


def hexc(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def fur_material(mat, root_hex, tip_hex, paw_root_hex, paw_tip_hex, density, radius, sheen_hex):
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs[0], out.inputs["Surface"])

    def fm(op, a=None, b=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    def mix(fac, a, b, blend='MIX'):
        n = N.new("ShaderNodeMix")
        n.data_type = 'RGBA'
        n.blend_type = blend
        if isinstance(fac, (int, float)):
            n.inputs[0].default_value = fac
        else:
            L.new(fac, n.inputs[0])
        for s, v in ((6, a), (7, b)):
            if isinstance(v, tuple):
                n.inputs[s].default_value = v
            else:
                L.new(v, n.inputs[s])
        return n.outputs[2]

    uvn = N.new("ShaderNodeUVMap")
    uvn.uv_map = "ShellUV"
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(uvn.outputs["UV"], sep.inputs[0])
    u, v = sep.outputs[0], sep.outputs[1]
    rest = N.new("ShaderNodeAttribute")
    rest.attribute_name = "bwk_rest"
    vor = N.new("ShaderNodeTexVoronoi")
    vor.voronoi_dimensions = '3D'
    vor.feature = 'F1'
    vor.inputs["Scale"].default_value = density
    L.new(rest.outputs["Vector"], vor.inputs["Vector"])
    thr = fm('MULTIPLY', fm('POWER', fm('SUBTRACT', 1.0, u), 0.8), radius)
    strand = fm('MULTIPLY', fm('LESS_THAN', vor.outputs["Distance"], thr), fm('GREATER_THAN', v, 0.02))
    L.new(fm('MAXIMUM', fm('LESS_THAN', u, 0.01), strand), bsdf.inputs["Alpha"])
    grad = fm('POWER', u, 0.7)
    pink = mix(grad, hexc(root_hex), hexc(tip_hex))
    paw = mix(grad, hexc(paw_root_hex), hexc(paw_tip_hex))
    col = N.new("ShaderNodeAttribute")
    col.attribute_name = "Col"
    coat = mix(col.outputs["Alpha"], paw, pink)
    L.new(mix(1.0, coat, col.outputs["Color"], 'MULTIPLY'), bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.6
        bsdf.inputs["Sheen Tint"].default_value = hexc(sheen_hex)
    try:
        mat.surface_render_method = 'DITHERED'
    except Exception:
        pass


# ---------------------------------------------------------------------------------------------- animation
def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def zoom_scale(f):
    """Measured push-in of the original after frame 324: 1 + 0.046 (1 - exp(-dt / 10))."""
    dt = max(0.0, f - PAINT_LAST)
    return 1.0 + 0.046 * (1.0 - math.exp(-dt / 10.0))


# Key times (scene frames).  Lump 325-338, push out 338-356, pop 356-364, blink 364-369, look L 369-381,
# look R 381-393, settle + wide-eyed smile 393-END.
def mascot_state(f):
    """Returns dict: pos offset (camera space metres, relative to the hidden start), body scale, head yaw/pitch,
    blink, towel lift (0..1), arm raise."""
    rise = smooth((f - 336) / 20.0)                     # 0 hidden -> 1 out
    pop = math.sin(math.pi * min(1.0, max(0.0, (f - 352) / 12.0))) * 0.10   # small overshoot
    lump = 0.18 * smooth((f - 325) / 9.0) * (1.0 - smooth((f - 336) / 8.0))
    wig = 0.05 * math.sin((f - 325) * 0.9) * smooth((f - 325) / 6.0) * (1 - smooth((f - 338) / 6.0))
    lift = min(1.0, lump + wig + 0.95 * rise)
    look = 0.0
    if f >= 369:
        look = 24.0 * smooth((f - 369) / 7.0)
    if f >= 381:
        look = 24.0 - 48.0 * smooth((f - 381) / 8.0)
    if f >= 393:
        look = -24.0 + 24.0 * smooth((f - 393) / 8.0)
    blink = 0.0
    for t0 in (364, 397):
        dt = f - t0
        if 0 <= dt <= 5:
            blink = max(blink, [0.0, 0.6, 1.0, 1.0, 0.55, 0.1][int(dt)])
    return {
        "rise": rise, "pop": pop, "lift": lift, "look": look, "blink": blink,
        "pitch": -10.0 * (1 - smooth((f - 350) / 10.0)) + 4.0 * smooth((f - 393) / 8.0),
        "arms": smooth((f - 350) / 10.0),
        "eyes_wide": 0.06 * smooth((f - 393) / 6.0),
    }


def stage_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = RES
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.frame_start, sc.frame_end = SHOT_FIRST, END
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.film_transparent = False
    sc.render.filter_size = 1.0
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass
    plate_path = os.path.join(PLATE_DIR, "plate_%04d.png" % PAINT_LAST)
    img = bpy.data.images.load(plate_path)
    img.colorspace_settings.name = 'sRGB'

    # camera (base pose = original frame 324); push-in continues as a zoom
    cd = bpy.data.cameras.new("ShotCam")
    cd.sensor_fit = 'VERTICAL'
    cd.sensor_height = SENSOR_H
    cd.sensor_width = SENSOR_H * W / H
    cd.clip_start, cd.clip_end = 0.01, 20.0
    cam = bpy.data.objects.new("ShotCam", cd)
    cam.rotation_euler = (math.radians(90), 0.0, 0.0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for f in range(SHOT_FIRST - 1, END + 1):
        cd.lens = BASE_LENS * zoom_scale(f)
        cd.keyframe_insert("lens", frame=f)

    # world: dim lavender ambient
    wo = bpy.data.worlds.new("Drum")
    wo.use_nodes = True
    bg = wo.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.32, 0.27, 0.40, 1.0)
    bg.inputs[1].default_value = 0.55
    sc.world = wo

    # mascot (needed first: the contact-shadow empty follows it)
    mpath, mkind = mascot_source()
    log("mascot source:", mkind, mpath)
    pivots = []
    if mkind == "v4":
        arm, pivots, height, types = load_v4(mpath)
        log("v4 object types", sorted(set(types)))
        S = float(os.environ.get("BWK_MASCOT_SCALE", "%.4f" % (0.165 * 1.42 / height)))
        body_c, shadow_s = 0.45, 0.72
    else:
        arm, meshes = append_mascot(mpath)
        if arm is None:
            raise RuntimeError("no armature in " + mpath)
        arm.animation_data_clear()
        for ob in meshes:
            if ob.animation_data:
                ob.animation_data_clear()
            stand_in_fur(ob)
        S = float(os.environ.get("BWK_MASCOT_SCALE", "0.165"))
        body_c, shadow_s = 0.53, 0.62
    arm.scale = (S, S, S)
    ex, ey = EMERGE
    d_out = pile_depth(ex, ey) + float(os.environ.get("BWK_DOUT", "0.02"))    # body centre depth when out
    y_root = float(os.environ.get("BWK_YROOT", "900"))                          # screen y of the root when out
    p_out = scr_to_world(ex, y_root, d_out)
    p_hide = p_out + Vector((0.0, 0.06, -0.15))
    shadow = bpy.data.objects.new("ContactShadow", None)
    sc.collection.objects.link(shadow)
    shadow.parent = arm
    shadow.location = (0.0, 0.0, body_c)    # body centre in model space
    shadow.empty_display_size = 1.0

    pb = arm.pose.bones if arm.type == 'ARMATURE' else None
    if pb is not None:
        for b in pb:
            b.rotation_mode = 'XYZ'
    for f in range(SHOT_FIRST, END + 1):
        st = mascot_state(f)
        k = st["rise"]
        # forward (out of the gap) leads, rising lags: the hat slides out under the towel edge instead of
        # poking through the cloth
        ky = smooth(min(1.0, k * 1.6))
        loc = Vector((p_hide.x + (p_out.x - p_hide.x) * k, p_hide.y + (p_out.y - p_hide.y) * ky,
                      p_hide.z + (p_out.z - p_hide.z) * k)) + Vector((0.0, 0.0, st["pop"] * 0.05))
        arm.location = loc
        if pb is not None:
            arm.rotation_euler = (math.radians(-6.0 * (1 - k)), 0.0, 0.0)
        else:   # no rig: the whole (ball-shaped) body nods / turns to look around
            arm.rotation_euler = (math.radians(-6.0 * (1 - k) - 0.6 * st["pitch"]), 0.0, math.radians(0.8 * st["look"]))
        arm.keyframe_insert("location", frame=f)
        arm.keyframe_insert("rotation_euler", frame=f)
        # contact shadow fades in with the emergence (tiny scale == no shadow: frame 325 stays == the plate)
        s = shadow_s * max(0.002, smooth((f - 334) / 14.0))
        shadow.scale = (s, s, s)
        shadow.keyframe_insert("scale", frame=f)
        w = 1.0 + st["eyes_wide"]
        eye_scale = (w + 0.05 * st["blink"], w, max(0.08, w - 0.92 * st["blink"]))
        if pb is not None:
            # head bone: local X = nod, local Y (bone axis, up) = look left / right
            pb["head"].rotation_euler = (math.radians(st["pitch"]), math.radians(st["look"]), 0.0)
            pb["head"].keyframe_insert("rotation_euler", frame=f)
            for tag in ("L", "R"):
                e = pb.get("eye." + tag)
                if e is not None:
                    e.scale = (eye_scale[0], 1.0, eye_scale[2])
                    e.keyframe_insert("scale", frame=f)
        for pv in pivots:
            pv.scale = eye_scale
            pv.keyframe_insert("scale", frame=f)

    # proxies: backdrop (whole plate), lower pile (full towel region, darkened where it hides under the top towel),
    # top towel (above the gap edge), lifted by the mascot through a shape key
    back = make_grid("Backdrop", -60, W + 60, -60, H + 60, 2, 2, lambda x, y: 1.6)
    back.data.materials.append(plate_material("M_Backdrop", img, 'backdrop'))

    def lower_depth(sx, sy):
        d = pile_depth(sx, sy)
        if GAP_X0 - 40 < sx < GAP_X1 + 40 and sy < gap_edge(sx) + 4:
            # recess the hidden part behind the top towel so it reads as the gap's back wall
            w = smooth((sx - (GAP_X0 - 40)) / 60.0) * smooth(((GAP_X1 + 40) - sx) / 60.0)
            d += 0.05 * w * smooth((gap_edge(sx) + 4 - sy) / 40.0)
        return d

    lower = make_grid("TowelPile", -40, W + 40, 520, H + 40, 110, 120, lower_depth)
    me = lower.data
    ua = me.attributes.new("under", 'FLOAT', 'POINT')
    vals = []
    for v in me.vertices:
        sy = H / 2 - v.co.z / v.co.y * F_PX
        sx = v.co.x / v.co.y * F_PX + W / 2
        # darken only where the top towel fully covers it at rest (no seam along the jagged towel edge, nothing
        # above the towel's upper boundary): ramps from 0 at 8 px inside the edge to 1 at 40 px
        inside = GAP_X0 - 30 < sx < GAP_X1 + 30
        wv = smooth((gap_edge(sx) - sy - 8.0) / 32.0) * smooth((sy - 560.0) / 20.0) if inside else 0.0
        vals.append(wv)
    ua.data.foreach_set("value", vals)
    lower.data.materials.append(plate_material("M_TowelPile", img, 'under', shadow))

    def top_keep(sx, sy):
        return sy <= gap_edge(sx) + 0.5 or not (GAP_X0 < sx < GAP_X1)

    top = make_grid("TopTowel", GAP_X0 - 120, GAP_X1 + 120, 540, GAP_Y + 6, 90, 70,
                    lambda x, y: pile_depth(x, y) - 0.004, keep=lambda sx, sy: sy <= gap_edge(sx) + 0.5)
    top.data.materials.append(plate_material("M_TopTowel", img, 'towel', shadow))
    top.shape_key_add(name="Basis", from_mix=False)
    lift = top.shape_key_add(name="Lift", from_mix=False)
    c = scr_to_world(ex, gap_edge(ex), pile_depth(ex, gap_edge(ex)))
    for i, v in enumerate(top.data.vertices):
        p = v.co
        dx = (p.x - c.x) / 0.085
        dback = max(0.0, (c.z - p.z) * 0.0 + (p.y - c.y)) / 0.10       # along depth (toward the back)
        dz = max(0.0, (p.z - c.z)) / 0.09                               # up the pile
        r = math.sqrt(dx * dx + 0.5 * dz * dz + 0.6 * dback * dback)
        w = (1.0 - smooth(r)) if r < 1.0 else 0.0
        w = w ** 1.2
        # lift: up and slightly toward the camera (the cloth drapes over the hat), edge rises most
        lift.data[i].co = p + Vector((0.0, -0.02 * w, 0.095 * w))
    for f in range(SHOT_FIRST, END + 1):
        lift.value = mascot_state(f)["lift"]
        lift.keyframe_insert("value", frame=f)

    # lights: soft overhead key, lavender bounce, cool metallic rim from the drum
    def area(name, loc, rot, size, energy, color):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.size = size
        ld.energy = energy
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        ob.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.collection.objects.link(ob)
        return ob

    tgt = p_out + Vector((0.0, 0.0, 0.10))
    area("Key", tgt + Vector((0.05, -0.30, 0.42)), (35.0, 0.0, 0.0), 0.45, 9.0, (1.0, 0.95, 0.97))
    area("Bounce", tgt + Vector((0.0, -0.20, -0.25)), (180.0 - 40.0, 0.0, 0.0), 0.5, 2.2, (0.82, 0.62, 1.0))
    area("Rim", tgt + Vector((0.10, 0.45, 0.25)), (-60.0, 0.0, 0.0), 0.35, 5.0, (0.85, 0.88, 1.0))

    os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    log("CHECK scene saved", BLEND_OUT, "mascot", mkind, "p_out", tuple(round(x, 3) for x in p_out))


def stage_render():
    bpy.ops.wm.open_mainfile(filepath=BLEND_OUT)
    sc = bpy.context.scene
    sc.render.resolution_percentage = RES
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass
    rng = os.environ.get("BWK_RANGE", "%d-%d" % (SHOT_FIRST, SHOT_FIRST + 5))
    if "," in rng:
        frames = [int(x) for x in rng.split(",")]
    else:
        a, b = (int(x) for x in rng.split("-"))
        frames = list(range(a, b + 1))
    a, b = frames[0], frames[-1]
    fdir = os.path.join(OUT, os.environ.get("BWK_FRAMES_SUB", "frames"))
    os.makedirs(fdir, exist_ok=True)
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(fdir, "f_%04d.png" % f)
        bpy.ops.render.render(write_still=True)
        log("rendered", f)
    log("CHECK rendered %d-%d to %s" % (a, b, fdir))


def set_video_output(sc, path):
    s = sc.render.image_settings
    if hasattr(s, "media_type"):
        s.media_type = 'VIDEO'
    s.file_format = 'FFMPEG'
    ff = sc.render.ffmpeg
    ff.format = 'MPEG4'
    ff.codec = 'H264'
    ff.constant_rate_factor = 'HIGH'
    ff.ffmpeg_preset = 'GOOD'
    sc.render.filepath = path


def stage_encode():
    """Encode OUT/frames/f_####.png (range BWK_RANGE) into OUT/test.mp4 (no audio)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    rng = os.environ.get("BWK_RANGE")
    a, b = (int(x) for x in rng.split("-"))
    fdir = os.path.join(OUT, "frames")
    first = os.path.join(fdir, "f_%04d.png" % a)
    probe = bpy.data.images.load(first)
    w, h = probe.size
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.sequence_editor_create()
    st = sc.sequence_editor.strips.new_image("seq", first, 1, 1)
    for f in range(a + 1, b + 1):
        st.elements.append("f_%04d.png" % f)
    sc.frame_start, sc.frame_end = 1, b - a + 1
    sc.view_settings.view_transform = 'Standard'
    sc.render.use_sequencer = True
    out = os.path.join(OUT, os.environ.get("BWK_MP4", "test_v1_%d-%d.mp4" % (a, b)))
    set_video_output(sc, out)
    bpy.ops.render.render(animation=True)
    log("CHECK encoded", out)


def stage_assemble():
    """Original 0-317 (+ its audio) + painted 318-324 + rendered 325-END -> OUT/Intro_Corrected_v1_9x16.mp4."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    video = os.environ["BWK_VIDEO"]
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.fps, sc.render.fps_base = FPS, 1.0
    sc.view_settings.view_transform = 'Standard'
    se = sc.sequence_editor_create()
    mv = se.strips.new_movie("orig", video, 2, 1)
    mv.frame_final_end = 1 + CUT_LAST_ORIG + 1              # scene frame 1 == video frame 0; keep 0..317
    snd = se.strips.new_sound("audio", video, 1, 1)
    pl = se.strips.new_image("paint", os.path.join(PLATE_DIR, "plate_%04d.png" % PAINT_FIRST), 3, PAINT_FIRST + 1)
    for n in range(PAINT_FIRST + 1, PAINT_LAST + 1):
        pl.elements.append("plate_%04d.png" % n)
    fdir = os.path.join(OUT, "frames")
    rn = se.strips.new_image("cg", os.path.join(fdir, "f_%04d.png" % SHOT_FIRST), 4, SHOT_FIRST + 1)
    for n in range(SHOT_FIRST + 1, END + 1):
        rn.elements.append("f_%04d.png" % n)
    for s in (pl, rn):
        s.transform.scale_x = s.transform.scale_y = 1.0
    sc.frame_start, sc.frame_end = 1, END + 1
    sc.render.use_sequencer = True
    out = os.path.join(OUT, os.environ.get("BWK_MP4", "Intro_Corrected_v1_9x16.mp4"))
    set_video_output(sc, out)
    sc.render.ffmpeg.audio_codec = 'AAC'
    sc.render.ffmpeg.audio_bitrate = 192
    sc.render.ffmpeg.audio_mixrate = 48000
    sc.render.ffmpeg.audio_channels = 'STEREO'
    log("audio strip %d frames, movie %d..%d" % (snd.frame_final_duration, mv.frame_final_start, mv.frame_final_end))
    bpy.ops.render.render(animation=True)
    log("CHECK assembled", out)


def fit_h(a, th):
    h, w, _ = a.shape
    tw = int(round(w * th / h))
    ys = np.clip((np.arange(th) + 0.5) * h / th, 0, h - 1).astype(int)
    xs = np.clip((np.arange(tw) + 0.5) * w / tw, 0, w - 1).astype(int)
    if h > th * 1.5:   # box-average when shrinking a lot
        k = int(h // th)
        a = box_blur_rgb(a, max(1, k // 2))
    return a[ys][:, xs]


def box_blur_rgb(a, r):
    return np.stack([box_blur(a[..., c], r) for c in range(3)], -1)


def crop_rel(a, spec):
    """spec 'x0,y0,x1,y1' as fractions of width / height."""
    h, w, _ = a.shape
    x0, y0, x1, y1 = (float(v) for v in spec.split(","))
    return a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


def stage_compare():
    """approved (03 crop) | incorrect (07 crop) | corrected (our frame crop), equal heights, private output."""
    panels = []
    for img_env, crop_env, default in (("BWK_APPROVED", "BWK_APPROVED_CROP", "0.33,0.24,0.66,0.80"),
                                       ("BWK_INCORRECT", "BWK_INCORRECT_CROP", "0.17,0.24,0.83,0.71"),
                                       ("BWK_CORRECTED", "BWK_CORRECTED_CROP", "0.17,0.24,0.83,0.71")):
        a = load_px(os.environ[img_env])
        panels.append(fit_h(crop_rel(a, os.environ.get(crop_env, default)), 720))
    g = 10
    wsum = sum(p.shape[1] for p in panels) + g * (len(panels) - 1)
    S = np.full((720, wsum, 3), 0.06, np.float32)
    x = 0
    for p in panels:
        S[:, x:x + p.shape[1]] = p
        x += p.shape[1] + g
    out = os.environ.get("BWK_COMPARE_OUT", os.path.join(OUT, "compare.png"))
    save_px(S, out)
    log("CHECK compare written", out, S.shape)


if __name__ == "__main__":
    for s in STAGES:
        log("stage", s)
        {"plate": stage_plate, "scene": stage_scene, "render": stage_render, "encode": stage_encode,
         "assemble": stage_assemble, "compare": stage_compare}[s]()
    log("DONE", STAGES)
