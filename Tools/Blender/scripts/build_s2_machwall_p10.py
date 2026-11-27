"""Screen S2 pass 10 (asset artist, judge gap #4 "left machinery under the roller reads flat purple and empty; the
approved frame has a dark blue machinery wall with lit details, the gold pipe and a bubble", crop 04 + ref x 0-240,
y 150-280: mean RGB ref 103 / 88 / 112 vs ours 129 / 96 / 150 = our corner shows the bare violet wall).
NEW SM_MachineWall_s2: a real 3D slate-blue machinery wall block that stands behind the existing gold pipe / housing
(SM_DoorMachine_s2) in the left corner: deep back slab (0.45 m) + three raised bevelled panels with dark vent slots +
a rounded lighter pilaster next to the hatch + gold trim bar, collars and bolt heads + three small warm indicator lamps.
Display face = Blender +Y (= asset -Z, HallFaceCam). 5.0 x 3.4 m, ~3k tris, one LOD (small on screen, flat-shaded boxes).
Slots reuse the S2 machine materials: M_DoorMachineBlue_s2 (slate-navy paint), M_DoorMachinePanel_s2 (lighter blue),
M_DoorMachineVent_s2 (dark), M_Gold, M_Bulb.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_machwall_p10.py s2_machwall_p10
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402

import bwk_common as C  # noqa: E402


def box(name, size, loc, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    C.apply_transforms(o)
    if bevel > 0:
        m = o.modifiers.new("bev", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = 'ANGLE'
    o.data.materials.append(mat)
    return o


def cyl(name, r, depth, loc, rot, mat, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def ball(name, r, loc, mat, seg=10, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=rings, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def main():
    C.reset_scene()
    blue = C.material("M_DoorMachineBlue_s2", "#3E4478", 0.3, 0.5)
    panel = C.material("M_DoorMachinePanel_s2", "#6C8CE8", 0.3, 0.34)
    vent = C.material("M_DoorMachineVent_s2", "#121838", 0.1, 0.5)
    gold = C.material("M_Gold", "#E8B04A", 1.0, 0.18)
    bulb = C.material("M_Bulb", "#FFB060", 0.0, 0.2, emission="#FF9A40", emission_strength=6.0)
    parts = [box("slab", (5.0, 0.45, 3.4), (0.0, -0.32, 0.0), blue, 0.05)]
    for i, z in enumerate((-1.08, -0.18, 0.72)):
        parts.append(box("panel%d" % i, (3.7, 0.14, 0.80), (-0.45, -0.05, z), blue, 0.045))
        for k in range(3):
            parts.append(box("vent%d_%d" % (i, k), (2.7, 0.05, 0.07), (-0.55, 0.035, z + 0.22 - 0.18 * k), vent, 0.0))
        for bx in (-2.18, 1.28):
            for bz in (z - 0.30, z + 0.30):
                parts.append(ball("bolt", 0.055, (bx, 0.03, bz), gold, 8, 5))
    # rounded lighter pilaster beside the hatch + gold collars
    parts.append(box("pilaster", (0.55, 0.55, 3.4), (1.95, -0.08, 0.0), panel, 0.12))
    for z in (-1.45, 1.45):
        parts.append(box("collar", (0.66, 0.62, 0.14), (1.95, -0.08, z), gold, 0.04))
    # warm indicator lamps on the pilaster
    for z in (0.95, 0.55, 0.15):
        parts.append(ball("lamp", 0.075, (1.95, 0.22, z), bulb, 12, 8))
    # gold trim bar along the top + bottom edge
    for z in (1.64, -1.64):
        parts.append(cyl("trim", 0.055, 5.0, (0.0, -0.06, z), (0.0, 1.5708, 0.0), gold, 12))
    lod0 = C.join(parts, "MachineWall_LOD0")
    for m in list(lod0.modifiers):
        C.select_only([lod0])
        bpy.ops.object.modifier_apply(modifier=m.name)
    t0 = C.tri_count(lod0)
    d = lod0.dimensions
    print("CHECK SM_MachineWall_s2 tris %d dims %.2f x %.2f x %.2f mats %s" % (t0, d.x, d.y, d.z, [m.name for m in lod0.data.materials]))
    for tag, cam in (("", (2.0, 7.5, 0.8)), ("_side", (7.0, 2.5, 1.5))):
        try:
            C.render_preview(C.preview_path("SM_MachineWall_s2" + tag), camera_location=cam, target=(0.0, 0.0, 0.0),
                             lens=35.0, resolution=(900, 600))
        except Exception as e:  # noqa: BLE001
            print("CHECK preview failed:", e)
    root = bpy.data.objects.new("SM_MachineWall_s2", None)
    bpy.context.scene.collection.objects.link(root)
    lod0.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_MachineWall_s2"))
    C.save_work("s2_machwall_p10.blend")
    print("DONE")


main()
