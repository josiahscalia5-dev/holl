"""Bubble Wash Kingdom - milk splash crowns v6 = the approved splash outline INFLATED into a real 3D liquid sheet
(lead 5190fd9a, 2026-11-27).

Why: owner 13:40 known problem "water splashes resemble white noodles rather than realistic milky water"; v2-v5c (metaball
fingers) still read as thin noodle fans in the portrait gameplay frame. The owner also asked to test specialized image-to-3D on
ONE asset: TRELLIS.2 (build_fx_crown_v6_trellis.py, Captures/trellis/splash_right/) turned this stylized single-view splash into
a FLAT 4 %-thick plate lying on the water - unusable. Method used instead (deterministic, local, free): the reference crown's
exact outline (RGBA colour-key cutout of the RIGHT crown in library crop 18, Captures/trellis/splash_right/splash_rgba.png) is
turned into a closed 3D mesh by silhouette inflation: thickness grows with the square root of the distance to the outline
(capped), so the broad milk sheet gets a soft rounded body and every finger becomes a round tube ending in its bulb tip. The
sheet stands beside the foot facing the rear gameplay camera, bends toward the camera at its outer end and leans back a little,
so it reads as a 3D crown from the gameplay rig and the side cameras (not a card). Mirrored for the left crown.
The outline is reference-derived -> the FBX files stay LOCAL in Assets/BubbleWashKingdom/Art/Projected/FX/ (gitignored);
SceneBuilder.WaterFX prefers V6 > V5 only when they exist (public clones keep V5).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_crown_v6.py fx_crown_v6      (BWK_FX_QUICK=1: previews only)
Env: BWK_MASK, BWK_PV, BWK_TRIS (per side), BWK_X0 / BWK_X1 (runner x range), BWK_ZC, BWK_BEND (m toward the camera at the
outer end), BWK_LEAN (deg, top away from the camera), BWK_THICK (thickness gain), BWK_CAP (cells), BWK_CELL (px per cell).
Revert: delete Assets/BubbleWashKingdom/Art/Projected/FX/SM_FX_CrownV6_*.fbx (V5 takes over again).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bwk_common as C  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

ROOT = "C:/Users/josia/thanksgiving"
MASK = os.environ.get("BWK_MASK", ROOT + "/Captures/trellis/splash_right/splash_rgba.png")
OUT_DIR = ROOT + "/Assets/BubbleWashKingdom/Art/Projected/FX"
PV_DIR = os.environ.get("BWK_PV", ROOT + "/Captures/trellis/splash_right")
QUICK = os.environ.get("BWK_FX_QUICK", "") == "1"
MAX_TRIS = int(os.environ.get("BWK_TRIS", "9000"))
X0, X1 = float(os.environ.get("BWK_X0", "0.18")), float(os.environ.get("BWK_X1", "1.08"))
ZC = float(os.environ.get("BWK_ZC", "0.08"))
BEND = float(os.environ.get("BWK_BEND", "0.30"))
LEAN = float(os.environ.get("BWK_LEAN", "8"))
THICK = float(os.environ.get("BWK_THICK", "1.6"))
CAP = float(os.environ.get("BWK_CAP", "12"))
CELL = int(os.environ.get("BWK_CELL", "4"))
Y0 = -0.03   # water line (runner-local y), as V5


def U(x, y, z):
    """runner-local (x right, y up, z forward) -> Blender space, same mapping as build_fx_crown_v5.py."""
    return Vector((-x, -z, y))


def uvec(v):
    return U(v[0], v[1], v[2])


def look_cam(name, pos_u, fwd_u, vfov_deg):
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(vfov_deg)
    co = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = uvec(pos_u)
    co.rotation_euler = uvec(fwd_u).to_track_quat('-Z', 'Y').to_euler()
    return co


def unity_euler_fwd(ex, ey):
    p, y = math.radians(ex), math.radians(ey)
    return (math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p))


def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return (v[0] / l, v[1] / l, v[2] / l)


def yaw_pitch(fwd, yaw_deg, pitch_up_deg):
    y = math.radians(yaw_deg)
    x, z = fwd[0] * math.cos(y) + fwd[2] * math.sin(y), -fwd[0] * math.sin(y) + fwd[2] * math.cos(y)
    hor = math.sqrt(x * x + z * z)
    el = math.atan2(fwd[1], hor) + math.radians(pitch_up_deg)
    return (x / hor * math.cos(el), math.sin(el), z / hor * math.cos(el))


def bbox(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx


def load_mask():
    img = bpy.data.images.load(MASK)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]   # top row first
    a = px[:, :, 3]
    hh, ww = (h // CELL) * CELL, (w // CELL) * CELL
    g = a[:hh, :ww].reshape(hh // CELL, CELL, ww // CELL, CELL).mean(axis=(1, 3))
    inside = g > 0.5
    print("CHECK mask %dx%d px -> grid %dx%d, inside %d cells" % (w, h, inside.shape[1], inside.shape[0], int(inside.sum())))
    return inside


def erode(m, eight):
    p = np.pad(m, 1, constant_values=False)
    out = m & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    if eight:
        out &= p[:-2, :-2] & p[:-2, 2:] & p[2:, :-2] & p[2:, 2:]
    return out


def distance(inside):
    """Erosion depth: 1 on the outline (8-adjacent to outside), growing inward; alternating 8 / 4 rings ~ octagonal metric."""
    d = np.zeros(inside.shape, np.float32)
    cur = inside.copy()
    k = 0
    while cur.any() and k < 200:
        d += cur
        cur = erode(cur, eight=(k % 2 == 0))
        k += 1
    return d


def build_sheet(name, inside, milk):
    rows, cols = inside.shape
    d = distance(inside)
    h_cells = THICK * np.sqrt(np.clip(d - 1.0, 0.0, CAP))          # 0 on the outline -> front and back meet there
    ys, xs = np.nonzero(inside)
    c0, c1 = xs.min(), xs.max()
    r1 = ys.max()
    cell_m = (X1 - X0) / float(c1 - c0 + 1)
    print("CHECK sheet %s: cell %.2f mm, max half-thickness %.1f mm, finger tubes ~%.1f mm" % (
        name, cell_m * 1000.0, float(h_cells.max()) * cell_m * 1000.0, THICK * math.sqrt(3.0) * cell_m * 1000.0))
    lean = math.tan(math.radians(LEAN))
    bm = bmesh.new()
    front, back = {}, {}

    def pos(r, c, side):
        u = (c - c0 + 0.5) / float(c1 - c0 + 1)
        x = X0 + u * (X1 - X0)
        y = Y0 + (r1 - r + 0.5) * cell_m
        z = ZC - BEND * u * u + (y - Y0) * lean
        hz = float(h_cells[r, c]) * cell_m
        return U(x, y, z - side * hz)                              # side +1 = front (toward the rear camera, -z)

    for r, c in zip(ys, xs):
        front[(r, c)] = bm.verts.new(pos(r, c, 1.0))
        back[(r, c)] = front[(r, c)] if d[r, c] <= 1.0 else bm.verts.new(pos(r, c, -1.0))
    for r in range(rows - 1):
        for c in range(cols - 1):
            q = [(r, c), (r, c + 1), (r + 1, c + 1), (r + 1, c)]
            if not all(inside[k] for k in q):
                continue
            try:
                bm.faces.new([front[k] for k in q])
            except ValueError:
                pass
            try:
                bm.faces.new([back[k] for k in reversed(q)])
            except ValueError:
                pass
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = C.mesh_from_bmesh(name, bm)
    obj.data.materials.append(milk)
    # soften the grid steps (the outline stays put at the water line within a few mm)
    sm = obj.modifiers.new("Soften", 'SMOOTH')
    sm.factor, sm.iterations = 0.6, 6
    C.select_only([obj])
    bpy.ops.object.modifier_apply(modifier=sm.name)
    tris = C.tri_count(obj)
    if tris > MAX_TRIS:
        dm = obj.modifiers.new("Decimate", 'DECIMATE')
        dm.ratio = MAX_TRIS / float(tris)
        dm.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dm.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    mn, mx = bbox(obj)
    print("CHECK %s %d tris (from %d), unity x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
        name, C.tri_count(obj), tris, -mx.x, -mn.x, mn.z, mx.z, -mx.y, -mn.y))
    return obj


def mirrored_left(right):
    left = right.copy()
    left.data = right.data.copy()
    left.name = left.data.name = right.name.replace("_R", "_L")
    bpy.context.scene.collection.objects.link(left)
    n_r = right.data.polygons[0].normal.copy()
    left.scale = (-1.0, 1.0, 1.0)                       # Blender X = -runner x: mirror right -> left
    C.apply_transforms(left)
    n_l = left.data.polygons[0].normal
    if n_l.dot(Vector((-n_r.x, n_r.y, n_r.z))) < 0.0:
        bm = bmesh.new()
        bm.from_mesh(left.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(left.data)
        bm.free()
        print("CHECK left crown: winding flipped after the mirror")
    left.data.update()
    return left


def import_v5():
    out = []
    for side in ("L", "R"):
        p = ROOT + "/Assets/BubbleWashKingdom/Art/Models/FX/SM_FX_CrownV5_%s.fbx" % side
        if not os.path.exists(p):
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=p, axis_forward='-Z', axis_up='Y')
        for o in [o for o in bpy.data.objects if o not in before]:
            if o.type == "MESH":
                C.apply_transforms(o, location=True)
                out.append(o)
    return out


def main():
    C.reset_scene()
    C.setup_preview_scene("#3A3488", 0.55)
    milk = C.material("M_FX_Milk_v3", "#EEF8FB", roughness=0.18, coat=0.4)
    bsdf = milk.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.3
        bsdf.inputs["Subsurface Radius"].default_value = C.hex_rgba("#9CC8F0")[:3]
        bsdf.inputs["Subsurface Scale"].default_value = 0.02
    inside = load_mask()
    right = build_sheet("SM_FX_CrownV6_R", inside, milk)
    left = mirrored_left(right)
    if not QUICK:
        C.ensure_dir(OUT_DIR)
        for o in (left, right):
            C.export_fbx([o], OUT_DIR + "/" + o.name + ".fbx")
    v5 = import_v5()
    pink = C.material("PV_Pink", "#F08AB8", roughness=0.8)
    cream = C.material("PV_Cream", "#FFF4F6", roughness=0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.46, location=U(0, 0.52, 0.02))
    bpy.context.active_object.data.materials.append(pink)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=U(sx * 0.22, 0.10, 0.12))
        o = bpy.context.active_object
        o.scale = (1.0, 0.6, 1.0)
        o.data.materials.append(cream)
    bpy.ops.mesh.primitive_plane_add(size=14, location=U(0, 0, 0))
    bpy.context.active_object.data.materials.append(C.material("PV_Water", "#1C8ECC", roughness=0.1))
    t = U(0, 0.3, 0.4)
    C._light("Key", 'AREA', 320, "#FFF6EE", t + Vector((-1.5, -2.5, 3.0)), t, 2.5)
    C._light("Key2", 'AREA', 260, "#FFF6EE", t + Vector((1.5, 2.5, 3.0)), t, 2.5)
    C._light("Fill", 'AREA', 90, "#8FB0FF", t + Vector((2.0, 0.0, 0.3)), t, 3.0)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    rear = look_cam("CamRear", (0.3, 0.9, -3.0), unity_euler_fwd(5.0, -7.0), 50.0)
    side = look_cam("CamSide", (2.6, 0.8, 0.2), (-1.0, -0.15, 0.0), 45.0)
    pos = (0.3, 1.3, 2.6)
    f0 = norm((0 - pos[0], 0.6 - pos[1], 0 - pos[2]))
    front = look_cam("CamFront", pos, yaw_pitch(f0, 9.1, 2.9), 52.0)
    shots = [(True, "V6", rear, "rear"), (True, "V6", side, "side"), (True, "V6", front, "front")]
    if v5:
        shots.append((False, "V5", side, "side"))
    for show_v6, tag, cam, view in shots:
        for o in (left, right):
            o.hide_render = not show_v6
        for o in v5:
            o.hide_render = show_v6
        scene.camera = cam
        scene.render.filepath = "%s/FX_Crown%s_%s.png" % (PV_DIR, tag, view)
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", scene.render.filepath)
    print("DONE crown v6 (inflated outline)")


main()
