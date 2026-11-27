"""Lighting agent: thick neon tube star (reference f_003.00s: bold single neon tubes, rounded tips, white-hot only in a
thin core line - the colour / glow comes from BWK/Emissive + bloom in Unity).

  SM_NeonStarTube   chubby rounded 5-point star, ONE fat tube (r 0.085 at outer radius 0.5 m; round 3: +25 % thicker like the reference)   slot M_Neon
  SM_NeonStarTube_v3   Screen S2 pass 10 (judge gap #6 "near yellow stars large and THICK-stroked"; lead 12:40 "thicker emissive
                    star tubes so the glow cards can shrink"): the v2 outline (outer r 1.0, inner .47, rounded tips) with a
                    tube r 0.11 (v2 0.065: ~4-5 px at 720p vs the reference's ~7-8 px on 70-75 px stars), 16 sides   slot M_Neon

Conventions as build_props.py (Docs/AssetSpec.md): meters, Z up, star stands in the XZ plane facing +Y, origin = centre.
Exports FBX -> Assets/BubbleWashKingdom/Art/Models/Lighting/, preview -> Docs/AssetPreviews/Lighting_NeonStarTube.png

Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_lighting_stars.py <log>   (BWK_STARS_V3=1: only SM_NeonStarTube_v3)
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
    # classic star (inner radius ~0.43 of the outer) with softly rounded tips, like the reference neon stars
    outline = rounded_polygon(star_outline(0.5, 0.215), lambda i: 0.045 if i % 2 == 0 else 0.025, 6)
    outline = resample_closed(outline, 110)
    tube_loop(bm, outline, 0.085, 12, xz)
    me_obj = C.mesh_from_bmesh("SM_NeonStarTube", bm)
    for p in me_obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(me_obj, [mat])
    C.shade_smooth(me_obj, 85)
    box_uv(me_obj)
    return me_obj


def build_star_tube_v3(mat):
    bm = bmesh.new()
    outline = rounded_polygon(star_outline(1.0, 0.47), lambda i: 0.12 if i % 2 == 0 else 0.08, 6)
    outline = resample_closed(outline, 150)
    tube_loop(bm, outline, 0.11, 16, xz)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])   # outline winding makes the tube inside-out (as v2)
    obj = C.mesh_from_bmesh("SM_NeonStarTube_v3", bm)
    for p in obj.data.polygons:
        p.use_smooth = True
    C.assign_materials(obj, [mat])
    C.shade_smooth(obj, 85)
    box_uv(obj)
    return obj


def main():
    v3_only = "--v3" in sys.argv or os.environ.get("BWK_STARS_V3") == "1"   # S2 pass 10: only the new thick master
    if not v3_only:
        C.reset_scene()
        mat = C.material("M_Neon", "#FFC000", roughness=0.25, emission="#FFC000", emission_strength=6.0)
        star = build_star_tube(mat)
        print("tris", C.tri_count(star))
        C.export_fbx([star], C.model_path(GROUP, star.name))
        C.render_preview(C.preview_path("Lighting_NeonStarTube"), camera_location=(0.0, 3.0, 0.0), target=(0.0, 0.0, 0.0),
                         lens=50.0, resolution=(600, 600))
    C.reset_scene()
    mat = C.material("M_Neon", "#FFC000", roughness=0.25, emission="#FFC000", emission_strength=6.0)
    v3 = build_star_tube_v3(mat)
    print("tris v3", C.tri_count(v3), "dims", tuple(round(d, 3) for d in v3.dimensions))
    C.export_fbx([v3], C.model_path(GROUP, v3.name))
    C.render_preview(C.preview_path("Lighting_NeonStarTube_v3"), camera_location=(0.0, 6.0, 0.0), target=(0.0, 0.0, 0.0),
                     lens=50.0, resolution=(600, 600))
    print("DONE build_lighting_stars")


if __name__ == "__main__":
    main()
