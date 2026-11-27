"""Screen S2 pass 9 (asset artist, judge gap #5 "upper-left roller = flat fringed DONUT; the reference (01 upper left +
crop 02) is a dense fluffy pink / white bristle DRUM seen from the side, bristles radiating"): NEW roller body master
  SM_RollerDrum_s2  solid closed core (rho 0.80, rounded closed ends: no open annulus = no donut) + dense CLUMPED bristle
                    tufts (LOD0 1150 tufts x 4 = 4600 tapered spikes, LOD1 1300 single spikes) radiating from the core,
                    tips rho 1.22-1.52, the end tufts splayed outward so both ends read rounded and fluffy; pink-dominant
                    bands like crop 02 (deep pink / light pink tips, a white band, a cyan band) - NO BWK/Fur shells (the
                    old body's fur shells rendered as the dark navy spikes in the corner).
Same asset frame as SM_BrushRoller_s2 (axis X, centred, 2.62 m long, hub end +X), so SceneBuilder.Hall swaps it in as the
spinning body (bodyVariant) and the gold hub / arm (SM_BrushRollerArm_r7) stays where it was.
Slots M_BristlePink_s2, M_BristlePinkTip_s2, M_BristleWhite_s2, M_BristleCyan_s2 (MaterialLibrary.Assets.cs, matte self-lit).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_s2_roller_p9.py
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

PINK, PTIP, WHITE, CYAN = range(4)
L = 2.62
# far end (-X, the end R2 sees) -> hub end (+X): pink-dominant, one white and one cyan band (crop 02)
BANDS = [("p", 0.80), ("w", 0.20), ("p", 0.34), ("c", 0.18), ("p", 0.46), ("w", 0.20), ("p", 0.44)]
assert abs(sum(w for _, w in BANDS) - L) < 1e-6


def band_at(x):
    x0 = -L / 2
    for key, w in BANDS:
        if x < x0 + w:
            return key
        x0 += w
    return BANDS[-1][0]


class Mesh:
    def __init__(self):
        self.co, self.faces, self.fmat = [], [], []

    def v(self, p):
        self.co.append(Vector(p))
        return len(self.co) - 1


def core(m, seg):
    """closed capsule-ish core: cylinder rho 0.80 over |x| <= 1.18 + rounded end domes to |x| 1.30."""
    prof = [(-1.30, 0.0), (-1.29, 0.30), (-1.26, 0.55), (-1.20, 0.74), (-1.15, 0.80), (1.15, 0.80), (1.20, 0.74),
            (1.26, 0.55), (1.29, 0.30), (1.30, 0.0)]
    rings = []
    for x, r in prof:
        if r == 0.0:
            rings.append([m.v((x, 0.0, 0.0))])
            continue
        rings.append([m.v((x, r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg))) for k in range(seg)])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            k1 = (k + 1) % seg
            if len(a) == 1:
                m.faces.append([a[0], b[k1], b[k]])
            elif len(b) == 1:
                m.faces.append([a[k], a[k1], b[0]])
            else:
                m.faces.append([a[k], a[k1], b[k1], b[k]])
            m.fmat.append(PINK)


def spike(m, rnd, root, d, length, w0, key):
    tang = d.orthogonal().normalized()
    e1 = tang
    e2 = d.cross(e1).normalized()
    rot = rnd.uniform(0, math.pi / 2)
    e1, e2 = e1 * math.cos(rot) + e2 * math.sin(rot), -e1 * math.sin(rot) + e2 * math.cos(rot)
    mid = root + d * (length * 0.62)
    tip = root + d * length
    w1 = w0 * 0.75
    r0 = [m.v(root + (e1 * cx + e2 * cy) * w0) for cx, cy in ((1, 0), (0, 1), (-1, 0), (0, -1))]
    r1 = [m.v(mid + (e1 * cx + e2 * cy) * w1) for cx, cy in ((1, 0), (0, 1), (-1, 0), (0, -1))]
    t = m.v(tip)
    root_mat = {"p": PINK, "w": WHITE, "c": CYAN}[key]
    tip_mat = {"p": PTIP, "w": WHITE, "c": CYAN}[key]
    for k in range(4):
        k1 = (k + 1) % 4
        m.faces.append([r0[k], r0[k1], r1[k1], r1[k]])
        m.fmat.append(root_mat)
        m.faces.append([r1[k], r1[k1], t])
        m.fmat.append(tip_mat)


def build(n_tufts, per_tuft, seed, seg):
    rnd = random.Random(seed)
    m = Mesh()
    core(m, seg)
    axis = Vector((1.0, 0.0, 0.0))
    for _ in range(n_tufts):
        x = rnd.uniform(-L / 2 + 0.05, L / 2 - 0.05)
        key = band_at(x)
        a = rnd.uniform(0.0, 2.0 * math.pi)
        radial = Vector((0.0, math.cos(a), math.sin(a)))
        tang = Vector((0.0, -math.sin(a), math.cos(a)))
        # end tufts splay outward along the axis (rounded fluffy ends instead of a cut face)
        endness = max(0.0, (abs(x) - 0.95) / 0.36)
        splay = axis * (math.copysign(1.0, x) * endness * 0.9)
        base = (radial + tang * rnd.uniform(-0.18, 0.08) + splay).normalized()
        length = rnd.uniform(0.44, 0.74) * (1.0 - 0.25 * endness)
        root_r = 0.74 if endness < 0.6 else 0.70
        for i in range(per_tuft):
            jit = Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)))
            d = (base + Vector((rnd.uniform(-0.16, 0.16), 0.0, 0.0)) + tang * rnd.uniform(-0.16, 0.16)).normalized()
            root = Vector((x, 0.0, 0.0)) + radial * root_r + jit
            spike(m, rnd, root, d, length * rnd.uniform(0.85, 1.12), rnd.uniform(0.016, 0.026) * (1.25 if per_tuft == 1 else 1.0), key)
    return m


def make(name, m, mats):
    me = bpy.data.meshes.new(name)
    me.from_pydata([c[:] for c in m.co], [], m.faces)
    me.validate()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    C.assign_materials(obj, mats)
    me.polygons.foreach_set("material_index", m.fmat)
    me.uv_layers.new(name="UVMap")
    me.shade_smooth()
    return obj


def main():
    C.reset_scene()
    mats = [C.material("M_BristlePink_s2", "#E2368C", 0.0, 0.55),
            C.material("M_BristlePinkTip_s2", "#FF8CC8", 0.0, 0.5),
            C.material("M_BristleWhite_s2", "#FFF0FA", 0.0, 0.5),
            C.material("M_BristleCyan_s2", "#7CD0F4", 0.0, 0.5)]
    lod0 = make("RollerDrum_LOD0", build(1150, 4, 19, 40), mats)
    lod1 = make("RollerDrum_LOD1", build(1300, 1, 23, 16), mats)
    t0, t1 = C.tri_count(lod0), C.tri_count(lod1)
    d = lod0.dimensions
    print("CHECK SM_RollerDrum_s2 tris LOD0 %d LOD1 %d dims %.2f x %.2f x %.2f" % (t0, t1, d.x, d.y, d.z))
    lod1.hide_render = True
    try:
        C.render_preview(C.preview_path("SM_RollerDrum_s2"), camera_location=(2.0, -5.5, 1.4), target=(0.0, 0.0, 0.0),
                         lens=40.0, resolution=(900, 600))
        print("PREVIEW", C.preview_path("SM_RollerDrum_s2"))
    except Exception as e:  # noqa: BLE001
        print("CHECK preview failed:", e)
    lod1.hide_render = False
    root = bpy.data.objects.new("SM_RollerDrum_s2", None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lod0, lod1):
        o.parent = root
    C.export_fbx([root], C.model_path("Machinery", "SM_RollerDrum_s2"))
    C.save_work("s2_roller_p9.blend")
    print("DONE")


main()
