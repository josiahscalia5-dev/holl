"""Round 7 (2026-11-26) hall + portal assets, measured from the approved video frames (owner brief: whole-level scenery).

S1/S2 opening hall (reference 0.00-2.00 s, 4K crops in Captures/agents/hall/crop_s1_*.png):
  SM_HallConsole_r7   pink washing-machine console: gold-framed blue screen with a cyan neon T-shirt icon, round yellow /
                      blue / pink buttons with gold rims, stacks of folded pink / white / blue towels on top, gold rail below
  SM_BrushRoller_r7   big fluffy brush roller: dense bristle discs in bands pink / lilac / pink / white / sky-blue / white /
                      pink / blue with a lilac flange (spins in Unity about its X axis)
  SM_BrushRollerArm_r7  its static gold hub + gold L-arm hanging it from above (same origin)
  SM_GoldValves_r7    polished gold machinery: pipes, flanges, two valve wheels, a pressure gauge
  SM_CyanPipeArch_r7  glowing cyan glass pipes: three concentric arches (glass shell + glowing water core)
  SM_HallPillar_r7    lavender-pink tower with gold bands, a gold-rimmed cream paw emblem and a gold elbow pipe on top
  SM_MouthRing_r7     the tunnel mouth = washing-machine door: thick polished gold ring with 20 warm bulbs + lips
  SM_MouthWall_r7     the machine front wall around the mouth (closes the hall, lavender-pink with gold trims)
S7 portal finale (reference 12.75-15.00 s, crop_s7_portal.png):
  SM_Starburst_r7     golden starburst: bright core, 76 tapered rays of mixed length, 44 four-point sparkles (gold + pink)
  SM_CyanPipeCurve_r7 transparent cyan glass pipe curving down from the chamber wall toward the slide (water core)

Convention (Docs/AssetSpec.md): Blender Z up, display faces toward Blender +Y (= toward the oncoming player in Unity
when placed with the track's flat rotation). Material slot names are the Unity remap keys (shared project materials).
Run: Tools/blender_run.sh Tools/Blender/scripts/build_hall_assets.py hall_r7
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bwk_common as C  # noqa: E402

REVIEW = os.path.join(C.ROOT, "Captures", "agents", "hall")
random.seed(20261126)
PI = math.pi
PARTS = []


def make_materials():
    M = {}
    M["pink"] = C.material("M_MachinePink", "#E84AA3", 0.05, 0.25)
    M["lav"] = C.material("M_MachineLavender", "#D3A6E0", 0.1, 0.3)
    M["gold"] = C.material("M_Gold", "#E6BE8D", 1.0, 0.2)
    M["screen"] = C.material("M_Screen", "#1C3570", 0.0, 0.2, emission="#2B5FB0", emission_strength=1.0)
    M["cyan"] = C.material("M_Neon_Cyan", "#00D8FF", 0.0, 0.3, emission="#00D8FF", emission_strength=6.0)
    M["by"] = C.material("M_ButtonYellow", "#FFD21A", 0.0, 0.2, emission="#FFB000", emission_strength=0.6)
    M["bc"] = C.material("M_ButtonCyan", "#2AA8FF", 0.0, 0.2, emission="#1A7CFF", emission_strength=0.6)
    M["bp"] = C.material("M_ButtonPink", "#FF4FA0", 0.0, 0.2, emission="#FF2F90", emission_strength=0.6)
    M["brp"] = C.material("M_BrushPink", "#E463B1", 0.0, 0.9)
    M["brw"] = C.material("M_BrushWhite", "#FFF6FF", 0.0, 0.9)
    M["brb"] = C.material("M_BrushBlue", "#6FD3FF", 0.0, 0.9)
    M["glass"] = C.material("M_Glass", "#B9F0FF", 0.0, 0.05, alpha=0.3)
    M["water"] = C.material("M_PipeWater", "#1FD2FF", 0.0, 0.1, emission="#1FD2FF", emission_strength=4.0)
    M["bulb"] = C.material("M_Bulb", "#FFB060", 0.0, 0.2, emission="#FF9A40", emission_strength=14.0)
    M["core"] = C.material("M_PortalCore", "#FFE2A0", 0.0, 0.2, emission="#FFC860", emission_strength=12.0)
    M["npink"] = C.material("M_Neon_Pink", "#FF4FA0", 0.0, 0.3, emission="#FF4FA0", emission_strength=6.0)
    M["white"] = C.material("M_PlasticWhite", "#FFF0DC", 0.0, 0.25)
    return M


# ------------------------------------------------------------------ primitive helpers (every part baked to world space)
def take(o, mat):
    o.data.materials.clear()
    o.data.materials.append(mat)
    C.select_only([o])
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    PARTS.append(o)
    return o


def cyl(mat, r, depth, loc, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    return take(bpy.context.active_object, mat)


def tor(mat, R, r, loc, rot=(0, 0, 0), seg=48, mseg=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=mseg,
                                     location=loc, rotation=rot)
    return take(bpy.context.active_object, mat)


def sph(mat, r, loc, scale=(1, 1, 1), seg=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = scale
    return take(o, mat)


def box(mat, size, loc, bevel=0.0, rot=(0, 0, 0), segs=3):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    C.select_only([o])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = segs
        b.limit_method = 'NONE'
    return take(o, mat)


def tube(mat, pts, r, res=3, name="tube"):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q[0], q[1], q[2], 1.0)
    sp.use_endpoint_u = True
    sp.order_u = 3
    sp.resolution_u = 10
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    C.select_only([o])
    bpy.ops.object.convert(target='MESH')
    return take(bpy.context.view_layer.objects.active, mat)


def flat_mesh(name, faces_by_mat, mats):
    """faces_by_mat: list of (mat_index, [Vector,...]) polygons in the XZ plane; normals forced toward +Y."""
    bm = bmesh.new()
    for mi, poly in faces_by_mat:
        vs = [bm.verts.new(p) for p in poly]
        f = bm.faces.new(vs)
        f.material_index = mi
        f.normal_update()
        if f.normal.y < 0:
            f.normal_flip()
    o = C.mesh_from_bmesh(name, bm)
    for m in mats:
        o.data.materials.append(m)
    PARTS.append(o)
    return o


def finish(name, group="Machinery", smooth=50.0):
    global PARTS
    o = C.join(PARTS, name)
    PARTS = []
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    C.select_only([o])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    if smooth:
        C.shade_smooth(o, smooth)
    C.export_fbx([o], C.model_path(group, name))
    print("CHECK %s tris %d dims %s" % (name, C.tri_count(o), tuple(round(v, 2) for v in o.dimensions)))
    return o


# ------------------------------------------------------------------ assets
def build_console(M):
    # body: rounded pink box 3.6 x 1.3 x 1.8 (front +Y), slightly wider top lip
    box(M["pink"], (3.6, 1.3, 1.8), (0, 0, 0.9), bevel=0.22, segs=4)
    box(M["pink"], (3.8, 1.45, 0.22), (0, 0, 1.86), bevel=0.1, segs=3)
    # gold-framed screen on the left of the front face
    box(M["gold"], (1.42, 0.12, 1.0), (-0.85, 0.66, 1.0), bevel=0.08, segs=3)
    box(M["screen"], (1.2, 0.1, 0.8), (-0.85, 0.7, 1.0), bevel=0.04, segs=2)
    # cyan neon T-shirt outline (reference icon), drawn on the screen
    s = 0.33
    shirt = [(-0.25, 0.32), (-0.09, 0.36), (0.0, 0.3), (0.09, 0.36), (0.25, 0.32), (0.42, 0.14), (0.3, 0.03), (0.2, 0.12),
             (0.2, -0.36), (-0.2, -0.36), (-0.2, 0.12), (-0.3, 0.03), (-0.42, 0.14), (-0.25, 0.32)]
    pts = [(-0.85 + x * s * 2.0, 0.78, 1.0 + z * s * 2.0) for x, z in shirt]
    cu = bpy.data.curves.new("shirt", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.025
    cu.bevel_resolution = 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q[0], q[1], q[2], 1.0)
    o = bpy.data.objects.new("shirt", cu)
    bpy.context.scene.collection.objects.link(o)
    C.select_only([o])
    bpy.ops.object.convert(target='MESH')
    take(bpy.context.view_layer.objects.active, M["cyan"])
    # round buttons with gold rims (yellow, blue, pink)
    for x, key in ((0.35, "by"), (0.85, "bc"), (1.33, "bp")):
        cyl(M[key], 0.19, 0.16, (x, 0.68, 0.95), rot=(PI / 2, 0, 0), verts=28)
        sph(M[key], 0.17, (x, 0.75, 0.95), scale=(1, 0.45, 1))
        tor(M["gold"], 0.2, 0.035, (x, 0.74, 0.95), rot=(PI / 2, 0, 0), seg=32, mseg=8)
    # stacks of folded towels on top (pink / white / blue), soft rounded slabs
    for sx, cols in ((-1.15, ("brp", "brw", "brp", "brw")), (-0.05, ("brb", "brw", "brb")), (1.05, ("brp", "brb", "brw", "brp"))):
        for i, key in enumerate(cols):
            box(M[key], (0.95, 0.66, 0.17), (sx + random.uniform(-0.04, 0.04), random.uniform(-0.05, 0.05), 2.07 + i * 0.18),
                bevel=0.07, segs=3, rot=(0, 0, random.uniform(-0.06, 0.06)))
    # gold rail under the console and a gold post at its side
    cyl(M["gold"], 0.09, 5.2, (0, 0.75, 0.12), rot=(0, PI / 2, 0))
    cyl(M["gold"], 0.09, 5.2, (0, 0.75, -0.3), rot=(0, PI / 2, 0))
    cyl(M["gold"], 0.13, 2.6, (1.95, 0.55, 0.9))
    sph(M["gold"], 0.17, (1.95, 0.55, 2.2))
    return finish("SM_HallConsole_r7")


def build_roller(M):
    """Fluffy brush roller, axis along Blender X, centre at the origin, radius ~1.3 m, length ~3.1 m."""
    slots = [M["brp"], M["lav"], M["brw"], M["brb"], M["gold"]]
    idx = {"brp": 0, "lav": 1, "brw": 2, "brb": 3}
    bands = [("brp", 0.38), ("lav", 0.1), ("brp", 0.36), ("brw", 0.34), ("brb", 0.4), ("brw", 0.3), ("brp", 0.4), ("brb", 0.34)]
    total = sum(w for _, w in bands)
    R1 = 1.28
    bm = bmesh.new()
    x = -total / 2
    for b, (key, w) in enumerate(bands):
        mi = idx[key]
        rb = (0.8 if key == "lav" else 0.86) * R1
        # solid colour body of the band
        ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=36, radius1=rb, radius2=rb, depth=w,
                                    matrix=Matrix.Translation((x + w / 2, 0, 0)) @ Matrix.Rotation(PI / 2, 4, 'Y'))
        for f in {f for v in ret["verts"] for f in v.link_faces}:
            f.material_index = mi
        if key != "lav":
            nr = max(3, int(w / 0.075))
            nt = 46
            for j in range(nr):
                u = (j + 0.5) / nr
                xx = x + u * w
                round_ = 1.0 - 0.2 * (2 * u - 1) ** 2
                for k in range(nt):
                    a = 2 * PI * (k + 0.5 * (j % 2)) / nt + random.uniform(-0.03, 0.03)
                    d = Vector((0, math.cos(a), math.sin(a)))
                    t = Vector((0, -math.sin(a), math.cos(a)))
                    ax = Vector((1, 0, 0))
                    L = R1 * round_ * random.uniform(0.95, 1.06)
                    base = Vector((xx, 0, 0)) + d * (rb * 0.92)
                    tip = Vector((xx + random.uniform(-0.03, 0.03), 0, 0)) + d * L
                    wb, wt = 0.03, random.uniform(0.045, 0.065)
                    vb = [bm.verts.new(base + ax * sx * wb + t * st * wb) for sx, st in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                    vt = [bm.verts.new(tip + ax * sx * wt * 0.8 + t * st * wt) for sx, st in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                    for i in range(4):
                        f = bm.faces.new((vb[i], vb[(i + 1) % 4], vt[(i + 1) % 4], vt[i]))
                        f.material_index = mi
                    f = bm.faces.new(vt)
                    f.material_index = mi
        x += w
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = C.mesh_from_bmesh("roller_body", bm)
    for m in slots:
        o.data.materials.append(m)
    PARTS.append(o)
    # gold hub, lilac flange, axle caps and the gold L-arm (hub on the -X end = Unity +X / right end)
    hx = -total / 2
    # the spinning part (bristles, lilac flange, far axle cap) and the static gold hub + L-arm share one origin, so
    # Unity spins SM_BrushRoller_r7 about its own X axis while SM_BrushRollerArm_r7 stays put (reference: rollers spin)
    cyl(M["lav"], 0.78, 0.12, (hx - 0.08, 0, 0), rot=(0, PI / 2, 0), verts=40)
    tor(M["gold"], 0.44, 0.06, (hx - 0.12, 0, 0), rot=(0, PI / 2, 0), seg=32, mseg=8)
    cyl(M["gold"], 0.16, 0.25, (total / 2 + 0.1, 0, 0), rot=(0, PI / 2, 0))
    body = finish("SM_BrushRoller_r7", smooth=60.0)
    cyl(M["gold"], 0.44, 0.55, (hx - 0.4, 0, 0), rot=(0, PI / 2, 0), verts=32)
    cyl(M["gold"], 0.3, 0.2, (hx - 0.75, 0, 0), rot=(0, PI / 2, 0), verts=28)
    tube(M["gold"], [(hx - 0.8, 0, 0), (hx - 1.15, 0, 0), (hx - 1.2, 0, 0.5), (hx - 1.2, 0, 1.6), (hx - 1.2, 0, 3.2)], 0.17)
    cyl(M["gold"], 0.26, 0.14, (hx - 1.2, 0, 3.15))
    arm = finish("SM_BrushRollerArm_r7", smooth=60.0)
    return body, arm


def build_valves(M):
    g = M["gold"]
    cyl(g, 0.16, 3.6, (0, 0, 1.8))
    for z in (0.4, 1.6, 2.9):
        cyl(g, 0.24, 0.1, (0, 0, z), verts=28)
    cyl(g, 0.13, 2.6, (1.3, 0, 1.0), rot=(0, PI / 2, 0))
    cyl(g, 0.13, 1.9, (-0.95, 0, 2.3), rot=(0, PI / 2, 0))
    tube(g, [(2.6, 0, 1.0), (2.95, 0, 1.0), (3.0, 0, 1.4), (3.0, 0, 2.4)], 0.13)
    tube(g, [(-1.9, 0, 2.3), (-2.25, 0, 2.3), (-2.3, 0, 1.9), (-2.3, 0, 0.0)], 0.13)
    for px in (0.9, 2.1, -0.6, -1.5):
        cyl(g, 0.2, 0.09, (px, 0, 1.0 if px > 0 else 2.3), rot=(0, PI / 2, 0), verts=28)
    for cx, cz, r in ((1.55, 1.0, 0.42), (-1.1, 2.3, 0.36)):
        tor(g, r, 0.05, (cx, 0.42, cz), rot=(PI / 2, 0, 0), seg=40, mseg=8)
        for k in range(4):
            cyl(g, 0.025, 2 * r, (cx, 0.42, cz), rot=(0, k * PI / 4, 0), verts=8)  # spokes in the wheel plane (XZ)
        sph(g, 0.08, (cx, 0.42, cz))
        cyl(g, 0.05, 0.42, (cx, 0.21, cz), rot=(PI / 2, 0, 0), verts=12)
    # pressure gauge with a cream face and a pink needle
    cyl(M["white"], 0.32, 0.1, (0, 0.24, 3.15), rot=(PI / 2, 0, 0), verts=32)
    tor(g, 0.33, 0.055, (0, 0.28, 3.15), rot=(PI / 2, 0, 0), seg=40, mseg=8)
    box(M["bp"], (0.04, 0.03, 0.24), (0.05, 0.3, 3.2), rot=(0, -0.6, 0))
    return finish("SM_GoldValves_r7")


def build_arch(M):
    for R, y in ((1.3, 0.0), (1.68, -0.05), (2.06, -0.1)):
        leg = 1.4
        pts = [(-R, y, -leg)]
        for i in range(13):
            a = PI * i / 12
            pts.append((-R * math.cos(a), y, R * math.sin(a)))
        pts.append((R, y, -leg))
        tube(M["glass"], pts, 0.15, res=3)
        tube(M["water"], pts, 0.095, res=2)
        for sx in (-R, R):
            cyl(M["gold"], 0.2, 0.12, (sx, y, -leg + 0.05), verts=24)
    return finish("SM_CyanPipeArch_r7", smooth=60.0)


def build_pillar(M):
    cyl(M["lav"], 1.0, 6.4, (0, 0, 3.2), verts=40)
    for z in (0.25, 1.55, 4.75, 6.25):
        tor(M["gold"], 1.02, 0.08, (0, 0, z), seg=48, mseg=10)
    cyl(M["white"], 0.56, 0.14, (0, 1.0, 3.15), rot=(PI / 2, 0, 0), verts=36)
    tor(M["gold"], 0.6, 0.08, (0, 1.06, 3.15), rot=(PI / 2, 0, 0), seg=40, mseg=10)
    sph(M["gold"], 0.2, (0, 1.1, 3.0), scale=(1.25, 0.35, 1.0))
    for dx, dz in ((-0.29, 3.22), (-0.11, 3.36), (0.11, 3.36), (0.29, 3.22)):
        sph(M["gold"], 0.085, (dx, 1.1, dz), scale=(1.0, 0.4, 1.25))
    tube(M["gold"], [(0, 0, 6.3), (0, 0, 6.9), (0.25, 0, 7.15), (1.2, 0, 7.15)], 0.17)
    return finish("SM_HallPillar_r7")


def build_mouth_ring(M):
    R = 5.4
    tor(M["gold"], R, 0.42, (0, 0, 0), rot=(PI / 2, 0, 0), seg=120, mseg=16)
    tor(M["gold"], R - 0.46, 0.13, (0, 0.12, 0), rot=(PI / 2, 0, 0), seg=120, mseg=10)
    tor(M["gold"], R + 0.47, 0.12, (0, -0.05, 0), rot=(PI / 2, 0, 0), seg=120, mseg=10)
    for i in range(20):
        a = 2 * PI * (i + 0.5) / 20
        sph(M["bulb"], 0.2, (R * math.cos(a), 0.42, R * math.sin(a)), seg=14, rings=7)
        cyl(M["gold"], 0.13, 0.08, (R * math.cos(a), 0.36, R * math.sin(a)), rot=(PI / 2, 0, 0), verts=16)
    return finish("SM_MouthRing_r7", smooth=60.0)


def build_mouth_wall(M):
    R0, R1, n = 5.85, 19.0, 72
    faces = []
    for i in range(n):
        a0, a1 = 2 * PI * i / n, 2 * PI * (i + 1) / n
        faces.append((0, [Vector((R0 * math.cos(a0), 0, R0 * math.sin(a0))), Vector((R1 * math.cos(a0), 0, R1 * math.sin(a0))),
                          Vector((R1 * math.cos(a1), 0, R1 * math.sin(a1))), Vector((R0 * math.cos(a1), 0, R0 * math.sin(a1)))]))
    flat_mesh("mouth_wall", faces, [M["lav"]])
    tor(M["gold"], 7.2, 0.1, (0, 0.05, 0), rot=(PI / 2, 0, 0), seg=120, mseg=8)
    tor(M["pink"], 6.3, 0.32, (0, 0.0, 0), rot=(PI / 2, 0, 0), seg=120, mseg=12)
    return finish("SM_MouthWall_r7", smooth=40.0)


def build_starburst(M):
    faces = []
    # core disc (fan) radius 1.5
    n = 40
    for i in range(n):
        a0, a1 = 2 * PI * i / n, 2 * PI * (i + 1) / n
        faces.append((0, [Vector((0, 0.02, 0)), Vector((1.5 * math.cos(a0), 0.02, 1.5 * math.sin(a0))),
                          Vector((1.5 * math.cos(a1), 0.02, 1.5 * math.sin(a1)))]))
    # rays: tapered blades of mixed length (every 4th long) behind the core
    nr = 76
    for i in range(nr):
        a = 2 * PI * i / nr + random.uniform(-0.02, 0.02)
        long_ = i % 4 == 0
        L = random.uniform(5.2, 7.2) if long_ else random.uniform(2.4, 4.6)
        w = random.uniform(0.16, 0.26) if long_ else random.uniform(0.08, 0.16)
        d = Vector((math.cos(a), 0, math.sin(a)))
        t = Vector((-math.sin(a), 0, math.cos(a)))
        y = Vector((0, random.uniform(-0.05, 0.0), 0))
        faces.append((0, [d * 0.9 + t * w + y, d * L + y, d * 0.9 - t * w + y]))
    # sparkles: four-point stars in front of the rays (gold, every 5th pink)
    for i in range(44):
        r = random.uniform(1.2, 5.8)
        a = random.uniform(0, 2 * PI)
        c = Vector((r * math.cos(a), random.uniform(0.15, 0.9), r * math.sin(a)))
        s = random.uniform(0.08, 0.3) * (1.6 if i < 6 else 1.0)
        mi = 1 if i % 5 == 0 else 0
        pts = []
        for k in range(8):
            ang = k * PI / 4
            rr = s if k % 2 == 0 else s * 0.22
            pts.append(c + Vector((rr * math.cos(ang), 0, rr * math.sin(ang))))
        for k in range(8):
            faces.append((mi, [c, pts[k], pts[(k + 1) % 8]]))
    flat_mesh("starburst", faces, [M["core"], M["npink"]])
    return finish("SM_Starburst_r7", group="Lighting", smooth=0)


def build_pipe_curve(M):
    pts = [(0, 0, 2.6), (-0.15, 0.25, 2.45), (-0.6, 0.7, 1.7), (-1.05, 1.2, 0.9), (-1.4, 1.8, 0.35), (-1.6, 2.6, 0.15),
           (-1.7, 3.3, 0.12)]
    tube(M["glass"], pts, 0.28, res=3)
    tube(M["water"], pts, 0.18, res=2)
    tor(M["gold"], 0.3, 0.07, (0, 0, 2.55), seg=32, mseg=8)
    cyl(M["gold"], 0.36, 0.16, (0, 0, 2.72), verts=28)
    return finish("SM_CyanPipeCurve_r7", smooth=60.0)


# ------------------------------------------------------------------ previews (next to the reference crops)
def lineup_preview(objs, path, cam, target, lens, res):
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.hide_render = o not in objs
    C.render_preview(path, cam, target, lens=lens, resolution=res, light_scale=4.0)


def main():
    C.reset_scene()
    C.ensure_dir(REVIEW)
    M = make_materials()
    console = build_console(M)
    roller, roller_arm = build_roller(M)
    valves = build_valves(M)
    arch = build_arch(M)
    pillar = build_pillar(M)
    ring = build_mouth_ring(M)
    wall = build_mouth_wall(M)
    burst = build_starburst(M)
    pipe = build_pipe_curve(M)
    try:
        bpy.context.scene.eevee.taa_render_samples = 16
    except Exception:
        pass
    # hall lineup (front, as the player meets them)
    console.location = (-7.0, 0, 0)
    for o in (roller, roller_arm):
        o.location = (-2.2, 1.0, 4.2)
        o.rotation_euler = (0, 0, math.radians(-35))
    valves.location = (2.6, 0, 0)
    arch.location = (-6.6, -1.5, 3.6)
    pillar.location = (7.6, 0, 0)
    lineup_preview([console, roller, roller_arm, valves, arch, pillar], os.path.join(REVIEW, "pv_hall_r7.png"),
                   (0.0, 17.0, 4.2), (0.0, 0.0, 2.4), 30.0, (1280, 640))
    for o in (console, roller, roller_arm, valves, arch, pillar):
        o.location = (0, 0, 0)
        o.rotation_euler = (0, 0, 0)
    # portal: ring + starburst + curving cyan pipe on the left (screen left = Blender +X when seen from +Y)
    burst.location = (0, -0.6, 0)
    pipe.location = (6.2, 1.0, -3.4)
    lineup_preview([ring, burst, pipe], os.path.join(REVIEW, "pv_portal_r7.png"), (0.0, 19.0, 0.5), (0.0, 0.0, 0.0), 35.0,
                   (1152, 648))
    C.save_work("hall_r7_assets.blend")
    print("DONE hall r7 assets")


main()
