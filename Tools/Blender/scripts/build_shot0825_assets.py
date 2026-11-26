"""Round 6 (2026-11-26) shot-matched library assets for the 8.25 s reconstruction test (environment agent).

Measured on Reference/frames4k_720/f_08.25s.png (spec: Captures/agents/environment/shot0825/asset_spec.md):
  SM_ChamberWindow_v2   big gold-framed sock chamber window, frame outer r 2.32 / glass r 1.75 (x1.4 porthole units):
                        thick rounded polished band (inner/outer 0.75 like the reference 0.75-0.84), dark inner lip,
                        16 domed rivets, a BIG hinge block + barrel on the viewer's left (-X), latch on the right,
                        big baroque scrolls top-left / bottom-left, chamber drum, swirl disc whose shader "up" (-U) is
                        Blender +Z (BWK/FlowGlow mode 1 = rainbow ARCH over light-blue water, foam bank), 3D foam puffs
                        piled at the bottom inside the glass. Lavender skirt meets an r 4.2 tunnel wall when the window
                        plane is 3.40 m from the axis with Blender Z = world up (side wall, the wall curves around Z).
                        M_Gold, M_GoldDark, M_Glass, M_ChamberDrum, M_ChamberSwirl, M_DrumRim, M_Foam
  SM_GlassPipe_Pink_v2  vertical transparent glass column r 0.5 x 6.0 m (origin = base centre, Z up), glowing pink
                        liquid up to 2.55 m with a meniscus, floating bubbles, gold foot / top collars, a tall gold clamp
                        collar (1.1 x diameter) at 3.2-4.3 m with an arm + block toward +X (the window hinge)
                        M_Glass, M_PipeWaterPink, M_Gold, M_GoldDark, M_Bubble
  SM_NeonStarTube_v2    big neon OUTLINE star, outer r 1.0, chubby inner r 0.47, rounded tips, slim tube r 0.065
                        (reference tube / star radius ~0.06-0.07; v1 was 0.17)        M_Neon (Unity picks pink/cyan/yellow)
Exports FBX -> Assets/BubbleWashKingdom/Art/Models/Machinery/ (window, pipe) and Lighting/ (star). The level keeps v1.
Previews -> Docs/AssetPreviews/Shot0825_*.png (no reference pixels); reference crop sheets are made in Captures/.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_shot0825_assets.py shot0825_assets
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import bwk_common as C  # noqa: E402
from build_props import star_outline, rounded_polygon, resample_closed, tube_loop, xz, box_uv  # noqa: E402

# build_machinery helpers (MB, lathe, sweep, ...) WITHOUT running its main(): exec the source minus the last call
_MP = os.path.join(HERE, "build_machinery.py")
_SRC = open(_MP, encoding="utf-8").read().rstrip()
assert _SRC.endswith("main()")
BM = {"__name__": "bwk_machinery_helpers", "__file__": _MP}
exec(compile(_SRC[: -len("main()")], _MP, "exec"), BM)
MB, lathe, sweep, path_frames, circle2 = BM["MB"], BM["lathe"], BM["sweep"], BM["path_frames"], BM["circle2"]
catmull_rom, rounded_box = BM["catmull_rom"], BM["rounded_box"]
X_AXIS, Y_AXIS, Z_AXIS, FRONT, TAU = BM["X_AXIS"], BM["Y_AXIS"], BM["Z_AXIS"], BM["FRONT"], BM["TAU"]

OUT_PREVIEW = C.preview_path("Shot0825_assets")
REVIEW = os.environ.get("BWK_SHOT_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                                                      "Captures", "agents", "environment", "shot0825"))
S_WIN, PLANE_R, WALL_R = 1.4, 3.40, 4.2


def sphere(mb, centre, r, mat, segs=12, rings=7, sy=1.0):
    prof = [(r * math.sin(math.pi * k / rings), -r * sy * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    prof[0], prof[-1] = (0.0, prof[0][1]), (0.0, prof[-1][1])
    lathe(mb, prof, mat, segs, centre, Z_AXIS, X_AXIS)


# ================================================================== chamber window v2
def build_window_v2(M):
    mb = MB()
    S = S_WIN
    G, GD, GL, DW, SW, SK, FM = range(7)
    O = Vector((0.0, 0.0, 0.0))
    # thick rounded polished band: flat back h -0.14 (r 1.23-1.66), outer wall, big bead (apex h 0.20), dark inner lip
    prof = [(1.23, -0.14), (1.66, -0.14)]
    for k in range(13):
        t = math.pi * k / 12
        prof.append((1.46 + 0.20 * math.cos(t), 0.20 * math.sin(t)))
    for k in range(1, 7):
        t = math.pi * k / 6
        prof.append((1.235 + 0.025 * math.cos(t), 0.045 * math.sin(t)))
    mats = [GD, G] + [G] * 12 + [GD] * 6 + [GD]
    lathe(mb, prof, G, 72, O, FRONT, X_AXIS, closed=True, mats=mats)
    # 16 domed rivets on the bead (skipping the hinge / latch at 180 / 0 deg)
    bolt = [(0.05, -0.03), (0.05, 0.004), (0.04, 0.026), (0.02, 0.036), (0.0, 0.038)]
    for k in range(16):
        phi = math.radians(11.25 + 22.5 * k)
        lathe(mb, bolt, G, 8, (1.46 * math.cos(phi), -0.185, 1.46 * math.sin(phi)), FRONT, X_AXIS)
    # domed glass inside the lip; planar UVs
    sag_r = (1.25 ** 2 + 0.09 ** 2) / (2.0 * 0.09)

    def dome_h(r):
        return 0.10 - (sag_r - math.sqrt(sag_r * sag_r - r * r))
    glass = [(r, dome_h(r)) for r in (1.25, 1.05, 0.8, 0.55, 0.28)] + [(0.0, dome_h(0.0))]
    lathe(mb, glass, GL, 48, O, FRONT, X_AXIS, uv_fn=lambda p: (0.5 + p.x / 2.5, 0.5 + p.z / 2.5))
    seal = [(1.262, -0.012), (1.225, -0.018), (1.192, -0.035), (1.175, -0.065), (1.185, -0.097), (1.212, -0.118),
            (1.228, -0.13)]
    lathe(mb, seal, GD, 48, O, FRONT, X_AXIS)
    dd = 0.34 / S
    lathe(mb, [(1.22, 0.0), (1.22, -dd * 0.5), (1.22, -dd)], DW, 48, O, FRONT, X_AXIS)
    # swirl disc: shader up (-U) = Blender +Z  -> U = 0.5 - z / (2 rd), V = 0.5 + x / (2 rd)
    rd = 1.225

    def disc_h(r):
        return -dd - 0.06 * (1.0 - (r / rd) ** 2) ** 2
    disc = [(r, disc_h(r)) for r in (1.225, 1.0, 0.75, 0.5, 0.25)] + [(0.0, disc_h(0.0))]
    lathe(mb, disc, SW, 48, O, FRONT, X_AXIS, uv_fn=lambda p: (0.5 - p.z / (2.0 * rd), 0.5 + p.x / (2.0 * rd)))
    # 3D foam puffs piled at the bottom inside the drum (flattened toward the glass)
    rnd = random.Random(825)
    for k in range(11):
        x = -0.95 + 1.9 * k / 10 + rnd.uniform(-0.05, 0.05)
        zt = -math.sqrt(max(1.12 ** 2 - x * x, 0.0))
        r = rnd.uniform(0.17, 0.27)
        z = zt + r * 0.75 + rnd.uniform(0.0, 0.12)
        prof = [(r * math.sin(math.pi * j / 6), -r * math.cos(math.pi * j / 6)) for j in range(7)]
        prof[0], prof[-1] = (0.0, prof[0][1]), (0.0, prof[-1][1])
        lathe(mb, prof, FM, 10, (x, dd * 0.55, z), Z_AXIS, X_AXIS, r_mod=None)
    # lavender skirt to the curved side wall: the wall curves around Blender Z (window on a side wall, Z = world up)
    def wall_y(z):
        return math.sqrt(max(WALL_R ** 2 - z * z, 0.0)) - PLANE_R
    n_sk = 72
    rows_sk = []
    for k in range(n_sk):
        ph = TAU * k / n_sk
        c, s_ = math.cos(ph), math.sin(ph)
        y0 = 0.14 * S
        y2 = wall_y(1.80 * S * s_) + 0.05
        pts = [(1.60 * S, y0), (1.67 * S, y0 + 0.30 * (y2 - y0)), (1.74 * S, y0 + 0.68 * (y2 - y0)), (1.80 * S, y2)]
        rows_sk.append([mb.v((r * c / S, y / S, r * s_ / S)) for r, y in pts])
    for k in range(n_sk):
        k1 = (k + 1) % n_sk
        ph = TAU * (k + 0.5) / n_sk
        out = Vector((math.cos(ph), -0.6, math.sin(ph)))
        for j in range(3):
            idx = [rows_sk[k][j], rows_sk[k1][j], rows_sk[k1][j + 1], rows_sk[k][j + 1]]
            mb.f(idx, SK, [(k / n_sk, j / 3.0), (k1 / n_sk, j / 3.0), (k1 / n_sk, (j + 1) / 3.0),
                           (k / n_sk, (j + 1) / 3.0)], ref=out)
    # BIG hinge (viewer's left, -X): rounded block over the band + a barrel with dark knuckle grooves + 2 straps
    rounded_box(mb, (-1.84, -0.04, 0.0), (0.40, 0.34, 0.86), 0.08, 3, G)
    barrel = [(0.0, -0.48), (0.07, -0.475), (0.105, -0.45), (0.12, -0.41), (0.12, -0.17), (0.10, -0.155),
              (0.10, -0.105), (0.12, -0.09), (0.12, 0.09), (0.10, 0.105), (0.10, 0.155), (0.12, 0.17), (0.12, 0.41),
              (0.105, 0.45), (0.07, 0.475), (0.0, 0.48)]
    bmats = [G, G, G, G, GD, GD, GD, G, GD, GD, GD, G, G, G, G]
    lathe(mb, barrel, G, 16, (-2.10, -0.06, 0.0), Z_AXIS, X_AXIS, mats=bmats)
    for zz in (-0.30, 0.30):
        rounded_box(mb, (-1.45, -0.17, zz), (0.55, 0.07, 0.16), 0.03, 2, G)
    # latch (+X): mount block, two dark posts, vertical grip
    rounded_box(mb, (1.72, 0.0, 0.0), (0.18, 0.17, 0.50), 0.05, 3, G)
    for zz in (-0.16, 0.16):
        pts = [Vector((1.78, 0.0, zz)), Vector((1.88, 0.0, zz)), Vector((1.97, 0.0, zz))]
        sweep(mb, path_frames(pts, lambda i: Z_AXIS), circle2(0.036, 8), GD, closed_prof=True, swap_uv=True)
    grip = [(0.0, -0.29), (0.032, -0.282), (0.05, -0.26), (0.058, -0.23), (0.058, 0.23), (0.05, 0.26),
            (0.032, 0.282), (0.0, 0.29)]
    lathe(mb, grip, G, 12, (1.99, 0.0, 0.0), Z_AXIS, X_AXIS)
    # baroque scrolls: big pair on the hinge side (top-left 128 deg / bottom-left 232 deg), small pair on the right
    scroll = [(1.47, 0.00), (1.60, 0.02), (1.72, 0.10), (1.80, 0.22), (1.80, 0.34), (1.73, 0.42), (1.64, 0.42),
              (1.59, 0.36), (1.60, 0.29), (1.66, 0.27), (1.70, 0.31)]
    ball = [(0.0, -0.04), (0.03, -0.03), (0.042, 0.0), (0.03, 0.03), (0.0, 0.04)]
    for th_deg, sgn, sc, tr in ((128.0, -1.0, 1.55, 0.066), (232.0, 1.0, 1.55, 0.066), (52.0, 1.0, 1.0, 0.05),
                                (308.0, -1.0, 1.0, 0.05)):
        th = math.radians(th_deg)
        er = Vector((math.cos(th), 0.0, math.sin(th)))
        et = Vector((-math.sin(th), 0.0, math.cos(th))) * sgn
        pts = catmull_rom([er * (1.58 + (a - 1.47) * sc) + et * (b * sc) + Vector((0.0, -0.05, 0.0)) for a, b in scroll], 2)
        n = len(pts)
        profs = [circle2(tr - tr * 0.5 * i / (n - 1), 7) for i in range(n)]
        sweep(mb, path_frames(pts, lambda i: Y_AXIS), None, G, closed_prof=True, profs=profs, swap_uv=True)
        lathe(mb, ball, G, 8, pts[-1], (pts[-1] - pts[-2]).normalized())
    mb.co = [c * S for c in mb.co]
    names = ["M_Gold", "M_GoldDark", "M_Glass", "M_ChamberDrum", "M_ChamberSwirl", "M_DrumRim", "M_Foam"]
    return mb.build("SM_ChamberWindow_v2", [M[n] for n in names])


# ================================================================== pink glass pipe v2
def build_pink_pipe_v2(M):
    mb = MB()
    GL, LQ, G, GD, BB = range(5)
    H, R = 6.0, 0.5
    zs = [0.25 + (H - 0.5) * k / 8 for k in range(9)]
    lathe(mb, [(R, z) for z in zs], GL, 32, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS)
    # reference: liquid top ~0.6 m below the clamp collar (collar bottom y 220, liquid top y 300, collar 140 px = 1.1 m)
    liq = [(0.0, 0.2), (0.45, 0.2), (0.45, 1.3), (0.45, 2.5), (0.40, 2.56), (0.25, 2.545), (0.0, 2.54)]
    lathe(mb, liq, LQ, 24, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS, v_vals=[h / 2.0 for _, h in liq])
    for z0 in (0.0, H - 0.32):
        lathe(mb, [(0.47, z0), (0.62, z0), (0.65, z0 + 0.04), (0.65, z0 + 0.28), (0.61, z0 + 0.32), (0.47, z0 + 0.32)],
              G, 32, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS, closed=True)
    z0, z1 = 3.2, 4.3
    band = [(0.47, z0), (0.60, z0), (0.645, z0 + 0.025), (0.665, z0 + 0.08), (0.645, z0 + 0.14), (0.60, z0 + 0.16),
            (0.60, z1 - 0.16), (0.645, z1 - 0.14), (0.665, z1 - 0.08), (0.645, z1 - 0.025), (0.60, z1), (0.47, z1)]
    lathe(mb, band, G, 36, (0.0, 0.0, 0.0), Z_AXIS, X_AXIS, closed=True,
          mats=[GD, G, G, G, G, G, G, G, G, G, G, GD])
    zc = 0.5 * (z0 + z1)
    a0, a1 = Vector((0.62, 0.0, zc)), Vector((1.35, 0.0, zc))
    sweep(mb, path_frames([a0, a1], lambda i: Z_AXIS), circle2(0.17, 16), G, closed_prof=True, swap_uv=True)
    lathe(mb, [(0.0, 0.0), (0.27, 0.0), (0.29, 0.03), (0.29, 0.09), (0.25, 0.11), (0.0, 0.11)], G, 16,
          Vector((1.30, 0.0, zc)), X_AXIS, Y_AXIS)
    rounded_box(mb, (1.52, 0.0, zc), (0.36, 0.40, 0.62), 0.07, 3, G)
    rnd = random.Random(8250)
    for k in range(16):
        r = rnd.uniform(0.035, 0.09)
        a = rnd.uniform(0.0, TAU)
        rho = rnd.uniform(0.0, 0.36)
        z = rnd.uniform(0.35, 2.3) if k < 7 else rnd.uniform(2.7, 5.6)
        sphere(mb, (rho * math.cos(a), rho * math.sin(a), z), r, BB, 10, 6)
    names = ["M_Glass", "M_PipeWaterPink", "M_Gold", "M_GoldDark", "M_Bubble"]
    return mb.build("SM_GlassPipe_Pink_v2", [M[n] for n in names])


# ================================================================== neon outline star v2
def build_star_v2(mat):
    bm = bmesh.new()
    outline = rounded_polygon(star_outline(1.0, 0.47), lambda i: 0.10 if i % 2 == 0 else 0.06, 6)
    outline = resample_closed(outline, 150)
    tube_loop(bm, outline, 0.065, 12, xz)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])   # outline winding made the tube inside-out (volume < 0)
    obj = C.mesh_from_bmesh("SM_NeonStarTube_v2", bm)
    for p in obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(obj, [mat])
    C.shade_smooth(obj, 85)
    box_uv(obj)
    return obj


# ================================================================== previews (no reference pixels)
def arch_material(mat):
    """Preview of BWK/FlowGlow mode 1 on the v2 disc UVs: rainbow arch over light-blue water + foam bank."""
    nt = mat.node_tree
    nm = BM["node_math"]
    u, v = BM["uv_xy"](nt)
    qy = nm(nt, 'MULTIPLY', nm(nt, 'SUBTRACT', u, 0.5), -2.0)
    qx = nm(nt, 'MULTIPLY', nm(nt, 'SUBTRACT', v, 0.5), 2.0)
    cy = nm(nt, 'ADD', qy, 0.62)
    ar = nm(nt, 'SQRT', nm(nt, 'ADD', nm(nt, 'MULTIPLY', qx, qx), nm(nt, 'MULTIPLY', cy, cy)))
    bt = nm(nt, 'DIVIDE', nm(nt, 'SUBTRACT', ar, 0.52), 0.78)
    f = nm(nt, 'DIVIDE', nm(nt, 'ADD', bt, 0.1), 1.2)
    col = BM["ramp"](nt, f, [(0.0, "#BFE6FF"), (0.083, "#A35CFF"), (0.25, "#4F86FF"), (0.4, "#4FE07A"),
                            (0.55, "#FFE34D"), (0.7, "#FF9A3C"), (0.85, "#FF5A8C"), (0.917, "#DDF2FF")])
    for n in nt.nodes:
        if n.type == 'VALTORGB' and len(n.color_ramp.elements) > 2:
            n.color_ramp.interpolation = 'CONSTANT'
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["UV"], noise.inputs["Vector"])
    bank = nm(nt, 'SUBTRACT', nm(nt, 'MULTIPLY', noise.outputs["Fac"], 0.95), nm(nt, 'MULTIPLY', nm(nt, 'ADD', qy, 0.38), 0.85))
    bank = nm(nt, 'MULTIPLY', bank, 6.0)
    clampn = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(bank, clampn.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    nt.links.new(clampn.outputs[0], mix.inputs["Factor"])
    nt.links.new(col, mix.inputs[6])
    mix.inputs[7].default_value = (1.0, 1.0, 1.0, 1.0)
    b = BM["bsdf"](mat)
    nt.links.new(mix.outputs[2], b.inputs["Emission Color"])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Strength"].default_value = 0.9


def import_sock(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=C.model_path("Props", name), axis_forward='-Z', axis_up='Y')
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    return new[0] if new else None


def curved_wall(coll, mat):
    mb = MB()
    n_a, n_x = 40, 16
    a0, a1 = math.radians(-60.0), math.radians(60.0)
    rows = []
    for i in range(n_a + 1):
        a = a0 + (a1 - a0) * i / n_a
        rows.append([mb.v((-6.0 + 12.0 * j / n_x, -PLANE_R + WALL_R * math.cos(a), WALL_R * math.sin(a)))
                     for j in range(n_x + 1)])
    for i in range(n_a):
        for j in range(n_x):
            q = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
            uvs = [((a0 + (a1 - a0) * ii / n_a) / TAU, (-6.0 + 12.0 * jj / n_x) / 4.0)
                   for ii, jj in ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))]
            mb.f(q, 0, uvs, ref=Vector((0.0, -1.0, 0.0)))
    return BM["pv_object"](coll, "PV_TunnelWall", mb, mat)


def render_previews(win, pipe, star, M):
    BM["preview_materials"](M)
    arch_material(M["M_ChamberSwirl"])
    foam = BM["bsdf"](M["M_Foam"])
    foam.inputs["Base Color"].default_value = C.hex_rgba("#F4F2FF")
    foam.inputs["Roughness"].default_value = 0.55
    b = BM["bsdf"](M["M_Bubble"])
    b.inputs["Alpha"].default_value = 0.45
    BM["preview_world"]()
    # 1. window + pipe on a curved drum wall, seen from the hinge side ~56 deg off the normal like the 8.25 s frame
    coll = BM["new_collection"]("PV_Window")
    BM["inst"](win, coll)
    BM["inst"](pipe, coll, (-4.15, -0.55, -3.75 * 1.0), (0.0, 0.0, 0.0))
    socks = []
    for name, loc, rot, sc in (("SM_Sock_A", (0.25, 0.10, 0.70), (20.0, 70.0, -25.0), 2.6),
                               ("SM_Sock_B", (0.75, 0.10, -0.25), (-10.0, 80.0, 35.0), 2.6),
                               ("SM_Sock_C", (-0.35, 0.10, -0.55), (15.0, 95.0, 120.0), 2.4)):
        s = import_sock(name)
        if s is None:
            continue
        for c in list(s.users_collection):
            c.objects.unlink(s)
        coll.objects.link(s)
        s.location = loc
        s.rotation_euler = tuple(math.radians(a) for a in rot)
        s.scale = (sc, sc, sc)
        socks.append(s)
        print("CHECK sock %s dims %s" % (name, tuple(round(d, 3) for d in s.dimensions)))
    wallmat = M["M_DrumWall"]
    curved_wall(coll, wallmat)
    BM["show_only"](coll)
    ang = math.radians(56.0)
    BM["render_view"](C.preview_path("Shot0825_ChamberWindow_v2"), (-10.5 * math.sin(ang) - 0.8, -10.5 * math.cos(ang), 0.4),
                      (-1.2, 0.0, 0.0), 30.0, (900, 1100), light_target=(0.0, -1.0, 0.0), light_scale=3.2, energy=0.8)
    BM["render_view"](os.path.join(REVIEW, "pv_window_front.png"), (0.0, -9.0, 0.0), (0.0, 0.0, 0.0), 35.0,
                      (900, 900), light_target=(0.0, -1.0, 0.0), light_scale=3.2, energy=0.8)
    # 2. neon star (emissive pink) on the dark wall colour
    cs = BM["new_collection"]("PV_Star")
    BM["inst"](star, cs)
    pink = C.material("PV_NeonPink", "#FF4FC8", roughness=0.3, emission="#FF6AD5", emission_strength=6.0)
    star.data.materials[0] = pink
    BM["show_only"](cs)
    BM["render_view"](C.preview_path("Shot0825_NeonStar_v2"), (0.0, -5.0, 0.0), (0.0, 0.0, 0.0), 40.0, (700, 700),
                      light_scale=1.5, energy=0.3)
    star.data.materials[0] = M["M_Neon"]


def main():
    C.reset_scene()
    M = BM["make_materials"]()
    M["M_Foam"] = C.material("M_Foam", "#F4F2FF", roughness=0.6)
    M["M_Bubble"] = C.material("M_Bubble", "#E8F4FF", roughness=0.05, alpha=0.35)
    M["M_Neon"] = C.material("M_Neon", "#FF4FC8", roughness=0.25, emission="#FF4FC8", emission_strength=6.0)
    win = build_window_v2(M)
    pipe = build_pink_pipe_v2(M)
    star = build_star_v2(M["M_Neon"])
    bpy.context.view_layer.update()
    for obj, group in ((win, "Machinery"), (pipe, "Machinery"), (star, "Lighting")):
        C.apply_transforms(obj)
        BM["check"](obj)
        C.export_fbx([obj], C.model_path(group, obj.name))
        print("TRIS %s %d" % (obj.name, C.tri_count(obj)))
    os.makedirs(REVIEW, exist_ok=True)
    render_previews(win, pipe, star, M)
    print("DONE build_shot0825_assets")


main()
