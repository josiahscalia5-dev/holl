"""Turntable preview of an imported GLB (e.g. a TRELLIS.2 result) - front / three-quarter / side / back stills.

Headless: BWK_GLB=<model.glb> BWK_OUT=<out_prefix> bash Tools/blender_run.sh Tools/Blender/scripts/preview_glb.py [log]
glTF front (+Z) becomes Blender -Y after import, so the "front" camera sits on -Y. The GLB is only read as data.
"""
import math
import os

import bpy
from mathutils import Vector

glb, out = os.environ["BWK_GLB"], os.environ["BWK_OUT"]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
mn, mx = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
tris = 0
for o in meshes:
    tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
        mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
center, dims = (mn + mx) / 2, mx - mn
size = max(dims)
print(f"[BWK] glb meshes {len(meshes)} tris {tris} dims {dims.x:.3f} x {dims.y:.3f} x {dims.z:.3f}")

sc = bpy.context.scene
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        continue
if sc.render.engine == "CYCLES":
    sc.cycles.samples = 32
sc.render.resolution_x = sc.render.resolution_y = 640
sc.render.film_transparent = False
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.30, 0.27, 0.40, 1.0); bg.inputs[1].default_value = 1.0
for name, rot, energy in (("Key", (math.radians(50), 0, math.radians(-30)), 3.5), ("Fill", (math.radians(70), 0, math.radians(150)), 1.5)):
    ld = bpy.data.lights.new(name, "SUN"); ld.energy = energy
    lo = bpy.data.objects.new(name, ld); lo.rotation_euler = rot; sc.collection.objects.link(lo)
cd = bpy.data.cameras.new("Cam"); cd.lens = 50
cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
dist = size * 2.6
for label, ang in (("front", 0), ("threequarter", 40), ("side", 90), ("back", 180)):
    a = math.radians(ang)
    cam.location = center + Vector((math.sin(a) * dist, -math.cos(a) * dist, size * 0.15))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{label}.png"
    bpy.ops.render.render(write_still=True)
    print(f"[BWK] wrote {sc.render.filepath}")
