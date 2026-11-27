"""Screen S2 pass 10 resume (asset artist, owner 13:50 "when repeated tweaks do not improve the portrait frame, change the
method"): SM_RollerFur_s2 = the S2 door roller as a CLOSED shell-fur drum.

Why: three strand-mesh drums (p9 spikes, p10 v2 thin clumps, v3 thick blunt locks) all read as coarse paper spikes / ribbons
with the violet wall between them (corner pink 7-38 % vs ref 72 %), while the S1 hall rollers built with the BWK/Fur shell
technique (SM_BrushRoller_r8, M_RollerFur_r8) render as genuinely soft fluffy brushes in the same light. Crop 02 of the
approved frame = a soft dense candy-pink fur drum with pale tips, no background through it.
v1: the r8 shell layout (skin + 8 coincident shells, UV1.x = shell fraction, UV1.y = fur length mask, LINEAR vertex band colour,
UV0 = strand / tuft cells) on a CLOSED capsule (domed fur ends instead of the r8 annulus caps whose hole read as a donut),
pink-dominant bands with two pale bands, gold axle caps. Same asset frame as SM_RollerDrum_s2 / SM_BrushRoller_r8: axis X,
2.62 m, hub end +X, radius 0.98 at the band peaks. Material slot M_RollerFur_s2 (MaterialLibrary.Assets.cs, BWK/Fur variant)
+ M_Gold.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_rollerfur_p10.py s2_rollerfur_p10
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bwk_common as C  # noqa: E402

PI = math.pi
SHELLS = 9          # skin + 8 fur shells (BWK/Fur coat path, like SM_BrushRoller_r8)
SEG = 40            # around
LC = 6.0            # UV0.x * 2 spans 0..6 around (integer strand / tuft cells -> no seam)
COLS = {"p": "#FF6CB0", "q": "#FF86C2", "w": "#FFE6F4"}
BANDS = [("p", 0.62), ("w", 0.16), ("p", 0.50), ("q", 0.30), ("p", 0.46), ("w", 0.16), ("p", 0.42)]
R_PEAK, R_GROOVE = 0.98, 0.90
DOME_ROWS = 5


def rows_profile():
    """(x, r, nx, nr, band key, fur mask) from the -X pole over the bands to the +X pole (closed capsule)."""
    total = sum(w for _, w in BANDS)
    x0 = -total / 2
    rows = []
    # -X dome: pole -> rim (quarter ellipse, depth 0.34)
    for j in range(DOME_ROWS + 1):
        th = (PI / 2) * j / DOME_ROWS          # 0 at the pole
        r = R_GROOVE * math.sin(th)
        x = x0 - 0.34 * math.cos(th)
        n = Vector((-math.cos(th) / 0.34, math.sin(th) / R_GROOVE, 0.0)).normalized()
        rows.append((x, max(r, 0.0), n.x, n.y, BANDS[0][0], 0.85))
    for b, (key, w) in enumerate(BANDS):
        nseg = 4
        for j in range(1, nseg + 1):
            u = j / nseg
            t = 2.0 * u - 1.0
            bul = math.sqrt(max(0.0, 1.0 - t * t))
            r = R_GROOVE + (R_PEAK - R_GROOVE) * bul
            drdu = (R_PEAK - R_GROOVE) * (-t / max(bul, 0.35)) * 2.0
            drdx = drdu / w
            ln = math.hypot(drdx, 1.0)
            rows.append((x0 + u * w, r, -drdx / ln, 1.0 / ln, key, 1.0))
        x0 += w
    for j in range(DOME_ROWS - 1, -1, -1):
        th = (PI / 2) * j / DOME_ROWS
        r = R_GROOVE * math.sin(th)
        x = x0 + 0.34 * math.cos(th)
        n = Vector((math.cos(th) / 0.34, math.sin(th) / R_GROOVE, 0.0)).normalized()
        rows.append((x, max(r, 0.0), n.x, n.y, BANDS[-1][0], 0.85))
    return rows, total


def build():
    rows, total = rows_profile()
    bm = bmesh.new()
    uv0 = bm.loops.layers.uv.new("UVMap")
    uv1 = bm.loops.layers.uv.new("UVShell")
    keys, tris = [], 0
    lin = {k: tuple(C.srgb_to_linear(int(v[i:i + 2], 16) / 255.0) for i in (1, 3, 5)) + (1.0,) for k, v in COLS.items()}
    # UV0.y = arc length along the profile (the domes get square tuft cells, not radially stretched ones)
    arc = [0.0]
    for a_, b_ in zip(rows[:-1], rows[1:]):
        arc.append(arc[-1] + math.hypot(b_[0] - a_[0], b_[1] - a_[1]))
    for s_ in range(SHELLS):
        h = s_ / (SHELLS - 1)
        grid = []
        for (x, r, nx, nr, key, mask) in rows:
            ring = []
            for k in range(SEG + 1):
                a = 2.0 * PI * k / SEG
                rr = max(r, 1e-4)
                v = bm.verts.new((x, rr * math.cos(a), rr * math.sin(a)))
                v.normal = Vector((nx, nr * math.cos(a), nr * math.sin(a))).normalized()
                ring.append(v)
            grid.append(ring)
        for i in range(len(rows) - 1):
            key = rows[i + 1][4]
            mask = min(rows[i][5], rows[i + 1][5])
            for k in range(SEG):
                quad = (grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k])
                try:
                    f = bm.faces.new(quad)
                except ValueError:
                    continue
                f.material_index = 0
                for lp, (ri, kk) in zip(f.loops, ((i, k), (i, k + 1), (i + 1, k + 1), (i + 1, k))):
                    lp[uv0].uv = (kk / SEG * LC * 0.5, arc[ri])
                    lp[uv1].uv = (h, mask)
                keys.append(key)
                tris += 2
    bm.normal_update()
    o = C.mesh_from_bmesh("RollerFur_s2", bm)
    me = o.data
    ca = me.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    for poly in me.polygons:
        c4 = lin[keys[poly.index]]
        for li in poly.loop_indices:
            ca.data[li].color_srgb = c4
    me.color_attributes.active_color = ca
    me.shade_smooth()
    try:
        me.normals_split_custom_set_from_vertices([v.normal[:] for v in me.vertices])
    except Exception as e:  # noqa: BLE001
        print("WARN custom normals", e)
    fur = C.material("M_RollerFur_s2", "#FFFFFF", 0.0, 0.9)
    try:   # Blender preview only: vertex colour drives the base colour (Unity uses BWK/Fur)
        nt = fur.node_tree
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        at = nt.nodes.new("ShaderNodeVertexColor")
        at.layer_name = "Col"
        nt.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    except Exception as e:  # noqa: BLE001
        print("WARN preview vc", e)
    me.materials.append(fur)
    gold = C.material("M_Gold", "#E8B04A", 1.0, 0.18)
    parts = [o]
    # gold axle stubs at both poles (the static arm SM_BrushRollerArm_r7 holds the hub end)
    for sx in (-1.0, 1.0):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.13, depth=0.30,
                                            location=(sx * (total / 2 + 0.38), 0.0, 0.0), rotation=(0.0, PI / 2, 0.0))
        cyl = bpy.context.active_object
        cyl.data.materials.append(gold)
        parts.append(cyl)
    print("SHELLS rollerfur_s2 %d shells x %d tris, rows %d" % (SHELLS, tris // SHELLS, len(rows)))
    return parts


def main():
    C.reset_scene()
    parts = build()
    for p in parts[1:]:
        p.select_set(True)
    o = parts[0]
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.join()
    o.name = "SM_RollerFur_s2"
    print("CHECK SM_RollerFur_s2 tris %d dims %s" % (C.tri_count(o), tuple(round(v, 2) for v in o.dimensions)))
    try:
        C.render_preview(C.preview_path("SM_RollerFur_s2"), camera_location=(2.0, -5.5, 1.4), target=(0.0, 0.0, 0.0),
                         lens=40.0, resolution=(900, 600))
    except Exception as e:  # noqa: BLE001
        print("CHECK preview failed:", e)
    C.export_fbx([o], C.model_path("Machinery", "SM_RollerFur_s2"))
    C.save_work("s2_rollerfur_p10.blend")
    print("DONE")


main()
