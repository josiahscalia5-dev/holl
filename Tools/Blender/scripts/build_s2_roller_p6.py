"""Screen S2 pass 6 (asset artist, 2026-11-27): bristle sleeve for the S2 door roller (owner sheet S2/03 "Roller & foam":
replace the flat-looking roller surface with dense soft pink bristles; judge gap #3 "denser roller (strand cards / shells)").

The reference f_03.00s roller (upper-left corner) reads as dense pink bristle clumps whose tips form a JAGGED lower edge;
ours (SM_BrushRoller_s2 = smooth band body + BWK/Fur shells) reads as a smooth plush tube. SM_RollerBristle_s2 adds real
geometry: tapered 4-sided bristle spikes rooted inside the band body (asset rho 0.86) whose tips reach rho 1.16-1.42
(beyond the fur shells -> spiky silhouette), coloured per S2 band (build_hall_assets.S2_ROLLER_BANDS order: pink /
lavender / pink / white / pink / cyan / pink / white / pink), each spike = deep root segment + light tip segment.
Same asset frame as SM_BrushRoller_s2 (axis X, centred, 2.62 m long): SceneBuilder.Hall places it as a CHILD of the
spinning roller body (identity local transform), so it turns with it.
LOD0 2700 spikes (~31k tris) / LOD1 800 spikes (v2: thinner, more of them). Slots M_BristlePink_s2, M_BristlePinkTip_s2, M_BristleWhite_s2,
M_BristleCyan_s2 (MaterialLibrary.Assets.cs, self-lit like the roller fur).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_roller_p6.py s2_roller_p6
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bwk_common as C  # noqa: E402

_MP = os.path.join(HERE, "build_machinery.py")
_SRC = open(_MP, encoding="utf-8").read().rstrip()
assert _SRC.endswith("main()")
BM = {"__name__": "bwk_machinery_helpers", "__file__": _MP}
exec(compile(_SRC[: -len("main()")], _MP, "exec"), BM)
MB = BM["MB"]  # noqa: F841 (shared helper import, kept for parity with build_s2_door_p6)

PINK, PTIP, WHITE, CYAN = range(4)
BANDS = [("p", 0.38), ("l", 0.1), ("p", 0.36), ("w", 0.3), ("p", 0.42), ("c", 0.16), ("p", 0.4), ("w", 0.2), ("p", 0.3)]
TOTAL = sum(w for _, w in BANDS)


def band_at(x):
    x0 = -TOTAL / 2
    for key, w in BANDS:
        if x < x0 + w:
            return key
        x0 += w
    return BANDS[-1][0]


def build(n, seed):
    rnd = random.Random(seed)
    co, faces, fmat = [], [], []

    def v(p):
        co.append(Vector(p))
        return len(co) - 1

    for _ in range(n):
        x = rnd.uniform(-TOTAL / 2 + 0.04, TOTAL / 2 - 0.04)
        key = band_at(x)
        if key == "l":          # lavender groove: few short bristles
            if rnd.random() < 0.7:
                continue
        a = rnd.uniform(0.0, 2.0 * math.pi)
        radial = Vector((0.0, math.cos(a), math.sin(a)))
        tang = Vector((0.0, -math.sin(a), math.cos(a)))
        axis = Vector((1.0, 0.0, 0.0))
        # direction: radial with a small random tilt + a slight sweep against the spin
        d = (radial + tang * rnd.uniform(-0.22, 0.1) + axis * rnd.uniform(-0.15, 0.15)).normalized()
        r_root, r_mid = 0.86, 1.10       # v2: longer deep-pink body, short light tip (soft tips, not pencil points)
        tip_len = rnd.uniform(1.16, 1.42) - r_root
        if key == "l":
            tip_len *= 0.7
        root = Vector((x, 0, 0)) + radial * r_root
        mid = root + d * (r_mid - r_root) * 1.0
        tip = root + d * tip_len
        w0 = rnd.uniform(0.02, 0.034)       # v2: half as thick (v1 0.04-0.062 read as hard pencil spikes)
        w1 = w0 * 0.8
        # cross-section frame
        s1 = tang - d * tang.dot(d)
        s1.normalize()
        s2 = d.cross(s1)
        rot = rnd.uniform(0, math.pi / 2)
        e1 = s1 * math.cos(rot) + s2 * math.sin(rot)
        e2 = d.cross(e1)
        ring0 = [v(root + (e1 * cx + e2 * cy) * w0) for cx, cy in ((1, 0), (0, 1), (-1, 0), (0, -1))]
        ring1 = [v(mid + (e1 * cx + e2 * cy) * w1) for cx, cy in ((1, 0), (0, 1), (-1, 0), (0, -1))]
        t = v(tip)
        root_mat = {"p": PINK, "l": PINK, "w": WHITE, "c": CYAN}[key]
        tip_mat = {"p": PTIP, "l": PTIP, "w": WHITE, "c": CYAN}[key]
        for k in range(4):
            k1 = (k + 1) % 4
            faces.append([ring0[k], ring0[k1], ring1[k1], ring1[k]])
            fmat.append(root_mat)
            faces.append([ring1[k], ring1[k1], t])
            fmat.append(tip_mat)
    return co, faces, fmat


def make(name, n, seed, mats):
    co, faces, fmat = build(n, seed)
    me = bpy.data.meshes.new(name)
    me.from_pydata([c[:] for c in co], [], faces)
    me.validate()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    C.assign_materials(obj, mats)
    me.polygons.foreach_set("material_index", fmat)
    me.uv_layers.new(name="UVMap")
    me.shade_smooth()
    return obj


def main():
    C.reset_scene()
    mats = [C.material("M_BristlePink_s2", "#E2368C", 0.0, 0.55),
            C.material("M_BristlePinkTip_s2", "#FF8CC8", 0.0, 0.5),
            C.material("M_BristleWhite_s2", "#FFF0FA", 0.0, 0.5),
            C.material("M_BristleCyan_s2", "#7CD0F4", 0.0, 0.5)]
    lod0 = make("RollerBristle_LOD0", 2700, 7, mats)
    lod1 = make("RollerBristle_LOD1", 800, 11, mats)
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    d = lod0.dimensions
    print("CHECK SM_RollerBristle_s2 tris LOD0 %d LOD1 %d dims %.2f x %.2f x %.2f" % (t0, t1, d.x, d.y, d.z))
    lod1.hide_render = True
    try:
        C.render_preview(C.preview_path("SM_RollerBristle_s2"), camera_location=(1.5, -5.0, 1.2), target=(0.0, 0.0, 0.0),
                         lens=40.0, resolution=(900, 600))
        print("PREVIEW", C.preview_path("SM_RollerBristle_s2"))
    except Exception as e:  # noqa: BLE001
        print("CHECK preview failed:", e)
    lod1.hide_render = False
    root = bpy.data.objects.new("SM_RollerBristle_s2", None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lod0, lod1):
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_RollerBristle_s2"))
    print("DONE")


main()
