"""Bubble Wash Kingdom - milk splash crowns v6 from a TRELLIS.2 image-to-3D result (lead 5190fd9a, 2026-11-27).

Owner 13:40 (new account): "use specialized 3D generation technology ... test the most promising alternative on ONE important
asset" + known problem "water splashes resemble white noodles rather than realistic milky water".
Input: Captures/trellis/splash_right/out_s0/model.glb = Microsoft TRELLIS.2 (MIT licence, free hosted demo, owner-approved)
generated from ONE isolated RGBA cutout of the right milk crown in library crop 18 (private reference). The geometry is
reference-derived, so the FBX files stay LOCAL in Assets/BubbleWashKingdom/Art/Projected/FX/ (gitignored, never pushed);
SceneBuilder.WaterFX prefers V6 > V5 only when those files exist (public clones keep V5).

Steps: import GLB -> join -> drop the baked texture (Unity renders it with M_FX_Milk_v3) -> merge / clean -> orient (TRELLIS
front = the rear gameplay camera's view) -> fit into the right crown's runner-local box beside the right foot -> soften ->
decimate for mobile -> mirror for the left crown -> export + rear / front previews in the build_fx_crown_v5.py proxy scene,
next to the current V5 pair rendered with the same cameras.
Run: BWK_FX_QUICK=1 (previews only) bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_crown_v6_trellis.py fx_crown_v6
Env: BWK_GLB, BWK_PV (preview dir), BWK_TRIS (per side, default 9000), BWK_X0 / BWK_X1 (runner x range of the right crown),
BWK_ZC (runner z centre), BWK_LEAN (deg the sheet leans back, away from the camera).
Revert: delete Assets/BubbleWashKingdom/Art/Projected/FX/SM_FX_CrownV6_*.fbx (V5 takes over again).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bwk_common as C  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

ROOT = "C:/Users/josia/thanksgiving"
GLB = os.environ.get("BWK_GLB", ROOT + "/Captures/trellis/splash_right/out_s0/model.glb")
OUT_DIR = ROOT + "/Assets/BubbleWashKingdom/Art/Projected/FX"
PV_DIR = os.environ.get("BWK_PV", ROOT + "/Captures/trellis/splash_right")
QUICK = os.environ.get("BWK_FX_QUICK", "") == "1"
MAX_TRIS = int(os.environ.get("BWK_TRIS", "9000"))
X0, X1 = float(os.environ.get("BWK_X0", "0.16")), float(os.environ.get("BWK_X1", "1.00"))
ZC = float(os.environ.get("BWK_ZC", "0.06"))
LEAN = float(os.environ.get("BWK_LEAN", "0"))
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


def import_trellis(milk):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLB)
    meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in [o for o in bpy.data.objects if o not in before and o.type != "MESH"]:
        for c in list(o.children):
            mw = c.matrix_world.copy()
            c.parent = None
            c.matrix_world = mw
    obj = C.join(meshes, "SM_FX_CrownV6_R") if len(meshes) > 1 else meshes[0]
    obj.name = obj.data.name = "SM_FX_CrownV6_R"
    for o in [o for o in bpy.data.objects if o not in before and o != obj]:
        bpy.data.objects.remove(o, do_unlink=True)
    C.apply_transforms(obj, location=True)
    raw = C.tri_count(obj)
    obj.data.materials.clear()
    obj.data.materials.append(milk)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    # keep only the biggest connected piece (TRELLIS can leave tiny floaters) - loose droplets of a real size are kept
    bm.verts.ensure_lookup_table()
    seen, pieces = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            a = stack.pop()
            comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        pieces.append(comp)
    pieces.sort(key=len, reverse=True)
    big = len(pieces[0])
    drop = [v for comp in pieces[1:] if len(comp) < max(60, big * 0.004) for v in comp]
    if drop:
        bmesh.ops.delete(bm, geom=drop, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    print("CHECK trellis raw %d tris, %d pieces (largest %d verts), dropped %d floater verts" % (raw, len(pieces), big, len(drop)))
    return obj


def fit_right(obj):
    # TRELLIS front (glTF +Z) arrives as Blender -Y; the rear gameplay camera sits on Blender +Y (runner z < 0): turn 180 deg
    # about Z, which also maps image-right to Blender -X = runner +x (the right crown stays on the right).
    obj.matrix_world = Matrix.Rotation(math.pi, 4, 'Z') @ obj.matrix_world
    C.apply_transforms(obj, location=True)
    mn, mx = bbox(obj)
    width = mx.x - mn.x                                   # runner x extent (Blender -X)
    s = (X1 - X0) / max(1e-6, width)
    obj.scale = (s, s, s)
    C.apply_transforms(obj)
    mn, mx = bbox(obj)
    # runner x in [X0, X1]  ->  Blender x in [-X1, -X0];  bottom on the water line;  depth centred on runner z = ZC
    obj.location = Vector((-X1 - mn.x, -ZC - (mn.y + mx.y) / 2.0, Y0 - mn.z))
    C.apply_transforms(obj, location=True)
    if abs(LEAN) > 1e-3:
        # lean the sheet back (top away from the camera) about its own bottom edge
        mn, mx = bbox(obj)
        pivot = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
        obj.matrix_world = (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(-LEAN), 4, 'X')
                            @ Matrix.Translation(-pivot) @ obj.matrix_world)
        C.apply_transforms(obj, location=True)
    mn, mx = bbox(obj)
    print("CHECK fitted scale %.4f, unity x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
        s, -mx.x, -mn.x, mn.z, mx.z, -mx.y, -mn.y))


def soften_and_decimate(obj):
    sm = obj.modifiers.new("Soften", 'SMOOTH')
    sm.factor, sm.iterations = 0.5, 4
    C.select_only([obj])
    bpy.ops.object.modifier_apply(modifier=sm.name)
    tris = C.tri_count(obj)
    if tris > MAX_TRIS:
        d = obj.modifiers.new("Decimate", 'DECIMATE')
        d.ratio = MAX_TRIS / float(tris)
        d.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=d.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    print("CHECK %s %d tris (from %d)" % (obj.name, C.tri_count(obj), tris))


def mirrored_left(right):
    left = right.copy()
    left.data = right.data.copy()
    left.name = left.data.name = "SM_FX_CrownV6_L"
    bpy.context.scene.collection.objects.link(left)
    right.data.calc_loop_triangles()
    n_r = right.data.polygons[0].normal.copy()
    left.scale = (-1.0, 1.0, 1.0)                       # Blender X = -runner x: mirror right -> left
    C.apply_transforms(left)
    # a mirror must keep the faces pointing outward: compare one face normal with the mirrored right normal and flip the
    # winding only if applying the negative scale did not already do it
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
    for o in out:
        mn, mx = bbox(o)
        print("CHECK V5 import %s unity x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (o.name, -mx.x, -mn.x, mn.z, mx.z, -mx.y, -mn.y))
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
    right = import_trellis(milk)
    fit_right(right)
    soften_and_decimate(right)
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
    pos = (0.3, 1.3, 2.6)
    f0 = norm((0 - pos[0], 0.6 - pos[1], 0 - pos[2]))
    front = look_cam("CamFront", pos, yaw_pitch(f0, 9.1, 2.9), 52.0)
    for show_v6, tag in ((True, "V6"), (False, "V5")):
        if not show_v6 and not v5:
            continue
        for o in (left, right):
            o.hide_render = not show_v6
        for o in v5:
            o.hide_render = show_v6
        for cam, view in ((rear, "rear"), (front, "front")):
            scene.camera = cam
            scene.render.filepath = "%s/FX_Crown%s_%s.png" % (PV_DIR, tag, view)
            bpy.ops.render.render(write_still=True)
            print("PREVIEW", scene.render.filepath)
    print("DONE crown v6 trellis")


main()
