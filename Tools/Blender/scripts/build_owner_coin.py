"""Lead 3c2b09a2 2026-11-27 (owner 13:15 "locate and reuse all my previously downloaded Meshy GLB assets"):
the owner's own Meshy gold paw-print coin -> game coin SM_Coin_Meshy (mobile budget, project gold materials).

Source (private, owner download, never committed): Tools/Blender/work/owner_glbs/claudia/Paw_Print_Gold_Coin_LIGHT.glb
Output (gitignored, local only): Assets/BubbleWashKingdom/Art/Projected/OwnerGLB/SM_Coin_Meshy.fbx
  - decimated 34k -> ~BWK_COIN_TRIS (default 4800) triangles, centred, 0.64 m across like SM_Coin (face normal on Blender Y)
  - two project materials like SM_Coin: M_Coin (raised paw + rim) / M_GoldDark (recessed field), chosen per face from the
    brightness of the Meshy base-colour texture (its baked relief shading becomes our two-tone gold)
  - preview renders: Captures/lead/owner_glbs/coin_lowpoly_{front,3q}.png
Run: Tools/blender_run.sh Tools/Blender/scripts/build_owner_coin.py owner_coin
If the source file is missing the script exits cleanly and the game keeps the procedural SM_Coin (SceneBuilder fallback).
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

SRC = os.path.join(C.ROOT, "Tools", "Blender", "work", "owner_glbs", "claudia", "Paw_Print_Gold_Coin_LIGHT.glb")
OUT_DIR = os.path.join(C.ROOT, "Assets", "BubbleWashKingdom", "Art", "Projected", "OwnerGLB")
PREV_DIR = os.path.join(C.ROOT, "Captures", "lead", "owner_glbs")
TARGET_TRIS = int(os.environ.get("BWK_COIN_TRIS", "4800"))
DIAMETER = 0.64   # SM_Coin: R 0.32


def base_color_pixels(obj):
    """(h, w, 4) float array of the image feeding the Principled BSDF Base Color (rows top -> bottom), or None."""
    for slot in obj.material_slots:
        m = slot.material
        if not m or not m.use_nodes:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None or not bsdf.inputs["Base Color"].is_linked:
            continue
        node = bsdf.inputs["Base Color"].links[0].from_node
        while node is not None and node.type != "TEX_IMAGE":   # skip mix / multiply nodes the importer may add
            ins = [i for i in node.inputs if i.is_linked]
            node = ins[0].links[0].from_node if ins else None
        if node is not None and node.image is not None:
            img = node.image
            w, h = img.size
            px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
            return px
    return None


def main():
    if not os.path.exists(SRC):
        print("CHECK owner coin GLB missing - nothing exported (the game keeps SM_Coin):", SRC)
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PREV_DIR, exist_ok=True)
    scene = C.reset_scene()
    bpy.ops.import_scene.gltf(filepath=SRC)
    meshes = [o for o in scene.objects if o.type == "MESH"]
    assert len(meshes) == 1, [o.name for o in meshes]
    obj = meshes[0]
    C.select_only([obj])
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(scene.objects):
        if o is not obj:
            bpy.data.objects.remove(o, do_unlink=True)
    tex = base_color_pixels(obj)
    n0 = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    # the Meshy GLB is a triangle soup (every triangle has its own vertices); weld first or the collapse decimation
    # removes whole triangles and shatters the coin (first run 13:20). UVs are per loop, so seams keep their UVs.
    bm = bmesh.new(); bm.from_mesh(obj.data)
    nv = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    print(f"CHECK welded {nv} -> {len(bm.verts)} vertices")
    bm.to_mesh(obj.data); bm.free(); obj.data.update()

    # decimate to the mobile budget (collapse keeps UVs; the relief survives as geometry for BWK/Gold's normal shading)
    mod = obj.modifiers.new("Decimate", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = min(1.0, TARGET_TRIS / max(1, n0))
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # centre + scale: diameter (X / Z extent) -> 0.64 m, thickness along Y like SM_Coin
    me = obj.data
    co = np.array([v.co[:] for v in me.vertices])
    lo, hi = co.min(0), co.max(0)
    centre = (lo + hi) * 0.5
    s = DIAMETER / max(hi[0] - lo[0], hi[2] - lo[2])
    for v in me.vertices:
        v.co = (Vector(v.co) - Vector(centre)) * s
    thickness = (hi[1] - lo[1]) * s

    # two-tone project gold from the Meshy texture brightness (sampled at each face's UV centroid)
    m_hi = bpy.data.materials.new("M_Coin"); m_hi.diffuse_color = (1.0, 0.72, 0.18, 1)
    m_lo = bpy.data.materials.new("M_GoldDark"); m_lo.diffuse_color = (0.55, 0.33, 0.08, 1)
    C.assign_materials(obj, [m_hi, m_lo])
    dark = 0
    if tex is not None and me.uv_layers.active is not None:
        h, w = tex.shape[:2]
        uv = me.uv_layers.active.data
        lum = []
        for p in me.polygons:
            u = sum(uv[i].uv[0] for i in p.loop_indices) / p.loop_total
            v = sum(uv[i].uv[1] for i in p.loop_indices) / p.loop_total
            x = min(w - 1, max(0, int((u % 1.0) * w)))
            y = min(h - 1, max(0, int((v % 1.0) * h)))   # Blender pixel rows run bottom -> top like UV v
            r, g, b = tex[y, x, :3]
            lum.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        lum = np.array(lum)
        cut = np.percentile(lum, 35)
        for p, l in zip(me.polygons, lum):
            p.material_index = 1 if l < cut else 0
            dark += int(l < cut)
    else:
        print("CHECK no base-colour texture / UVs - single material M_Coin")
    C.shade_smooth(obj, 50.0)
    obj.name = obj.data.name = "SM_Coin_Meshy"
    n1 = sum(len(p.vertices) - 2 for p in me.polygons)
    print(f"CHECK SM_Coin_Meshy: {n0} -> {n1} triangles, diameter {DIAMETER} m, thickness {thickness:.3f} m, "
          f"scale {s:.4f}, dark faces {dark}/{len(me.polygons)}")
    C.export_fbx([obj], os.path.join(OUT_DIR, "SM_Coin_Meshy.fbx"))

    # quick preview (geometry + material split) for the lead
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    for mat, col, met, rough in ((m_hi, (1.0, 0.70, 0.20, 1), 1.0, 0.25), (m_lo, (0.50, 0.30, 0.07, 1), 1.0, 0.4)):
        mat.use_nodes = True
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = col
        bsdf.inputs["Metallic"].default_value = met
        bsdf.inputs["Roughness"].default_value = rough
    world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.45, 0.40, 0.55, 1)
    for name, rot, en in (("Key", (50, 0, 35), 4.0), ("Fill", (65, 0, -120), 1.5), ("Rim", (110, 0, 180), 2.5)):
        ld = bpy.data.lights.new(name, "SUN"); ld.energy = en
        lo_ = bpy.data.objects.new(name, ld); scene.collection.objects.link(lo_)
        lo_.rotation_euler = [math.radians(a) for a in rot]
    cd = bpy.data.cameras.new("Cam"); cd.lens = 60
    cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = 384
    for tag, az, el in (("front", 0, 5), ("3q", 38, 15)):
        a, e = math.radians(az), math.radians(el)
        cam.location = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 1.35
        cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(PREV_DIR, f"coin_lowpoly_{tag}.png")
        bpy.ops.render.render(write_still=True)
    print("DONE build_owner_coin")


main()
