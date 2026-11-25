"""Pipeline smoke test: exports an asymmetric marker to verify Blender->Unity axes and renders a preview.

Marker: a cone pointing to the asset FRONT (-Y), a small cube on the asset RIGHT (-X), a sphere on TOP (+Z).
In Unity (bakeAxisConversion) the cone must point +Z, the cube sit at +X and the sphere at +Y.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bwk_common as C  # noqa: E402

C.reset_scene()
red = C.material("M_TestFront", "#FF3355", roughness=0.4)
green = C.material("M_TestRight", "#33DD66", roughness=0.4)
blue = C.material("M_TestUp", "#3388FF", roughness=0.4)

bpy.ops.mesh.primitive_cone_add(radius1=0.15, depth=0.6, location=(0, -0.3, 0), rotation=(1.5708, 0, 0))
cone = bpy.context.active_object
C.assign_materials(cone, [red])
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(-0.4, 0, 0))
cube = bpy.context.active_object
C.assign_materials(cube, [green])
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 0.4))
sph = bpy.context.active_object
C.assign_materials(sph, [blue])
marker = C.join([cone, cube, sph], "SM_AxisMarker")
C.apply_transforms(marker)
C.export_fbx([marker], C.model_path("_Test", "SM_AxisMarker"))
C.render_preview(C.preview_path("_test_axis"), camera_location=(1.6, -1.8, 1.2), target=(0, 0, 0),
                 lens=40, resolution=(480, 480))
print("TEST_AXIS_DONE")
