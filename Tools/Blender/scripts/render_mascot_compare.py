"""Character turnaround renders: the SAME cameras for two rigged mascot versions (preview only, exports nothing).

Usage (headless, through the heavy lock):
  BWK_CMP_TAGS="v4,v5" bash Tools/blender_run.sh Tools/Blender/scripts/render_mascot_compare.py mascot_compare
Env:
  BWK_CMP_TAGS     comma list of versions; each <tag> renders Tools/Blender/work/mascot_v4/mascot_<tag>_rig.blend
  BWK_CMP_VERIFY   optional FBX path to re-import and list (bones / takes / materials) after the renders
Writes our renders only (no reference pixels): Docs/AssetPreviews/SK_Mascot_<tag>_cmp_{rear,front,threequarter,side}.png.
Cameras (mascot frame: faces -Y, +X = his left), matched by eye to the approved views:
  rear         = the effective gameplay hero camera of build_mascot_rig.py (HERO_CAM, f_03.00s framing)
  front        = straight in front at brim height (reference sheet 03)
  threequarter = 38 deg toward his right, slightly above (reference sheet 05)
  side         = build_mascot_rig.py SIDE_CAM direction (no reference view; travel = left)
The Blender fur here is the rig's PREVIEW fur (fixed colours); Unity materials are judged in the Unity candidate.
"""
import importlib.util
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bwk_common as C  # noqa: E402

WORK = os.path.join(C.ROOT, "Tools", "Blender", "work", "mascot_v4")
os.environ.setdefault("BWK_RIG_MODEL_JSON", os.path.join(WORK, "mascot_v4_game.json"))
_spec = importlib.util.spec_from_file_location("bwk_mascot_rig_lib", os.path.join(HERE, "build_mascot_rig.py"))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)          # __name__ != "__main__": the rig's main() does not run

VIEWS = {
    "rear": ((0.0, 2.566, 1.039), (0.0, 0.0, 0.50), 50.0, (0.0, 0.0, 0.55)),
    "front": ((0.0, -2.70, 1.00), (0.0, 0.0, 0.52), 50.0, (0.0, -0.1, 0.55)),
    "threequarter": ((-1.662, -2.128, 1.05), (0.0, 0.0, 0.52), 50.0, (0.0, -0.1, 0.55)),
    "side": ((2.75, -0.30, 0.80), (0.0, -0.10, 0.50), 48.0, (0.0, -0.1, 0.55)),
}


def main():
    tags = [t.strip() for t in os.environ.get("BWK_CMP_TAGS", "v4,v5").split(",") if t.strip()]
    for tag in tags:
        blend = os.path.join(WORK, "mascot_%s_rig.blend" % tag)
        bpy.ops.wm.open_mainfile(filepath=blend)
        arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
        print("CHECK", tag, "armature", arm.name, "action", arm.animation_data.action.name if arm.animation_data
              and arm.animation_data.action else None)
        bpy.context.scene.frame_set(7)          # Slide f7 = the Unity hero capture sample (0.25 s)
        R.add_floor()
        R.setup_preview_fur(bpy.data.objects["SK_Mascot_Body"])
        for view, (cam, look, lens, subject) in VIEWS.items():
            R.render(C.preview_path("SK_Mascot_%s_cmp_%s" % (tag, view)), cam, look, lens, (700, 700),
                     label="%s - %s" % (tag, view), subject=subject, samples=32)
    fbx = os.environ.get("BWK_CMP_VERIFY", "")
    if fbx:
        R.verify_fbx(fbx)
    print("COMPARE_DONE")


main()
