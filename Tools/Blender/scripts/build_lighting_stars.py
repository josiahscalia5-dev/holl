"""Lighting agent: thick neon tube star (reference f_003.00s: bold single neon tubes, rounded tips, white-hot only in a
thin core line - the colour / glow comes from BWK/Emissive + bloom in Unity).

  SM_NeonStarTube   chubby rounded 5-point star, ONE fat tube (r 0.08 at outer radius 0.5 m)   slot M_Neon

Conventions as build_props.py (Docs/AssetSpec.md): meters, Z up, star stands in the XZ plane facing +Y, origin = centre.
Exports FBX -> Assets/BubbleWashKingdom/Art/Models/Lighting/, preview -> Docs/AssetPreviews/Lighting_NeonStarTube.png

Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_lighting_stars.py <log>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bwk_common as C  # noqa: E402
from build_props import star_outline, rounded_polygon, resample_closed, tube_loop, xz, box_uv  # noqa: E402

GROUP = "Lighting"


def build_star_tube(mat):
    bm = bmesh.new()
    # chubby star (inner radius ~0.5 of the outer, like the reference's friendly neon stars), well rounded tips
    outline = rounded_polygon(star_outline(0.5, 0.25), lambda i: 0.085 if i % 2 == 0 else 0.05, 7)
    outline = resample_closed(outline, 110)
    tube_loop(bm, outline, 0.08, 12, xz)
    me_obj = C.mesh_from_bmesh("SM_NeonStarTube", bm)
    for p in me_obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(me_obj, [mat])
    C.shade_smooth(me_obj, 85)
    box_uv(me_obj)
    return me_obj


def main():
    C.reset_scene()
    mat = C.material("M_Neon", "#FFC000", roughness=0.25, emission="#FFC000", emission_strength=6.0)
    star = build_star_tube(mat)
    print("tris", C.tri_count(star))
    C.export_fbx([star], C.model_path(GROUP, star.name))
    C.render_preview(C.preview_path("Lighting_NeonStarTube"), camera_location=(0.0, 3.0, 0.0), target=(0.0, 0.0, 0.0),
                     lens=50.0, resolution=(600, 600))
    print("DONE build_lighting_stars")


if __name__ == "__main__":
    main()
