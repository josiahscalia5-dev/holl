"""Makes the mascot model's normals face outward (Unity culls back faces; Blender previews do not).

Closed parts: recalculated outside. Flat front-facing parts (catchlights, mouth): faces turned toward the front (-Y).
Saves Tools/Blender/work/mascot_model.blend in place and re-exports the static Characters/SK_Mascot_model.fbx.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import bwk_common as C  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=C.work_path("mascot_model"))
FRONT_FACING = ("catchlight", "mouth")


def inward_fraction(obj):
    me = obj.data
    center = sum((Vector(v.co) for v in me.vertices), Vector()) / max(1, len(me.vertices))
    inward = 0
    for p in me.polygons:
        if p.normal.dot(p.center - center) < 0:
            inward += 1
    return inward / max(1, len(me.polygons))


for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
    before = inward_fraction(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    if obj.name.lower().startswith(FRONT_FACING):
        for f in bm.faces:
            if f.normal.y > 0:  # facing backward (+Y) -> flip toward the front (-Y)
                f.normal_flip()
    else:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    print(f"NORMALS {obj.name}: inward before {before:.2f} -> after {inward_fraction(obj):.2f}")

bpy.ops.wm.save_as_mainfile(filepath=C.work_path("mascot_model"), compress=True)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
C.export_fbx(meshes, C.model_path("Characters", "SK_Mascot_model"))
print("FIX_NORMALS_DONE")
