"""Bubble Wash Kingdom - hero mascot RIG + FUR SHELLS + ANIMATIONS + FBX. Blender 5.3, headless, deterministic.

Run from the project root (normally through build_mascot_all.py, right after the model):
  blender --background --factory-startup --python Tools/Blender/scripts/build_mascot_rig.py

Input   Tools/Blender/work/mascot_model.blend + mascot_model.json (landmarks written by build_mascot_model.py)
Outputs Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot.fbx   Armature "Armature" + skinned mesh
                                                                      "SK_Mascot_Body", 13 takes (Armature|<Clip>)
        Tools/Blender/work/mascot_rig.blend
        Docs/AssetPreviews/SK_Mascot_game_9x16.png   (Slide at the Unity portrait gameplay camera)
                           SK_Mascot_seated_back.png / _seated_side.png / _front.png / _poses.png (contact sheet)
        Captures/agents/character/SK_Mascot_vs_reference.png (private: approved video frames vs. this rig)
        BWK_QUICK=1 skips the contact sheet, the reference sheet and the FBX re-import check.

OWNER POSE REQUIREMENT (overrides the clip where they differ): during gameplay he SITS on his bottom and slides
FEET-FIRST, the whole body facing the travel direction (-Y), away from the camera that sits slightly above and
behind him. Every riding clip is built around one canonical seated pose:
  * body bone pivot = bottom of the fur ball; body lowered 5 cm and reclined 4 deg; head pitched forward 7 deg so
    the beanie is seen from behind (not from the top) by the rear camera,
  * stubby legs in a wide V-sit, hinged at the hips so the heels rest on the slide, big cream paws with the toes
    up and pointing forward (they peek out on both sides of the ball from behind),
  * big arms raised up and out ("wheee"), palms up/back, tail tucked, beanie / pom-pom trailing slightly.
Legs are children of root (spec hierarchy) but every clip moves them with the body ("legs follow"), plus a floor
clamp so a paw never sinks through the water when he leans.

Axes: meters, Z up, front = -Y, his right = -X, his left = +X.
"""
import json
import math
import os
import struct
import sys
import tempfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import bwk_common as C  # noqa: E402

FPS = 30
ROOT = C.ROOT
QUICK = os.environ.get("BWK_QUICK", "") == "1"
REF_DIR = os.path.join(ROOT, "Reference", "frames")
PRIVATE_OUT = os.path.join(ROOT, "Captures", "agents", "character")     # gitignored: images with reference frames
# temporary contact-sheet cells live outside the project (override with BWK_SCRATCH)
SCRATCH = os.path.join(os.environ.get("BWK_SCRATCH") or tempfile.gettempdir(), "bwk_mascot_rig_cells")

# Optional env overrides (round 5, v4 game candidate). Unset = the original SK_Mascot pipeline, unchanged:
#   BWK_RIG_MODEL_BLEND  input model .blend        (default Tools/Blender/work/mascot_model.blend)
#   BWK_RIG_MODEL_JSON   input landmark contract   (default Tools/Blender/work/mascot_model.json)
#   BWK_RIG_FBX          output FBX                (default Assets/.../Characters/SK_Mascot.fbx)
#   BWK_RIG_WORK_BLEND   output rig .blend         (default Tools/Blender/work/mascot_rig.blend)
#   BWK_RIG_PREVIEW      preview name prefix       (default SK_Mascot -> Docs/AssetPreviews/SK_Mascot_*.png)
MODEL_BLEND = os.environ.get("BWK_RIG_MODEL_BLEND") or C.work_path("mascot_model")
MODEL_JSON = os.environ.get("BWK_RIG_MODEL_JSON") or os.path.join(C.WORK, "mascot_model.json")
FBX_OUT = os.environ.get("BWK_RIG_FBX") or C.model_path("Characters", "SK_Mascot")
WORK_BLEND = os.environ.get("BWK_RIG_WORK_BLEND") or C.work_path("mascot_rig")
PREVIEW_PREFIX = os.environ.get("BWK_RIG_PREVIEW") or "SK_Mascot"


def prev(name):
    """Preview path for a default 'SK_Mascot...' name, re-prefixed by BWK_RIG_PREVIEW."""
    return C.preview_path(PREVIEW_PREFIX + name[len("SK_Mascot"):])


# ------------------------------------------------------------------ model facts (mascot_model.json)
with open(MODEL_JSON) as _fh:
    CONTRACT = json.load(_fh)


def V(x):
    return Vector(tuple(x))


BODY_C = V(CONTRACT["BODY_C"])
BODY_BOTTOM = V(CONTRACT["BODY_BOTTOM"])
HAT_AXIS = V(CONTRACT["HAT_AXIS"]).normalized()
CUFF_BOTTOM_A = CONTRACT["CUFF_BOTTOM_A"]
HAT = CONTRACT["hat"]
POMPOM_C, POMPOM_R = V(HAT["pompom_c"]), HAT["pompom_r"]
ARM_HAND = 0.15           # elbow-ish joint along the arm (hand bone = the mitt)

# ------------------------------------------------------------------ seated riding pose
SEAT_DROP = 0.05          # body lowered so the fur-ball underside rests ~2 cm above the slide surface
SEAT_LEAN = -4.0          # body pitch (negative = recline)
HEAD_PITCH = 6.0          # head (and beanie) nod forward a little: at the approved hero camera the hat reads side-on
FOOT_FLOOR = 0.045        # lowest paw point in the seated pose (round 3: heels lifted a little while sliding,
                          # so the white soles show fully above the water as in the reference; the body still sits)
FOOT_MIN_Z = 0.006        # floor clamp for animated paws
ARM_RAISE_MAX = 26.0      # extra raise above the modelled 30 deg: soft cap + per-frame cuff collision solve
# cuff solve trigger: lower the arm once a probe point is within this depth of the beanie's outer surface (-4 mm =
# v3 / v4 unchanged). Optional contract key 'arm_cuff_tol' (v5: the soft plush mitt may press up to 1.5 cm into
# the brim's rib / fur zone, like the reference's mitts that touch the brim side, instead of dropping 28 deg)
ARM_CUFF_TOL = float(CONTRACT.get('arm_cuff_tol', -0.004))
TILT_RADIUS = 0.40        # effective bottom radius: lift that keeps the bottom on the surface when leaning

# head pivot = ball centre (rotations slide the face over the near-spherical body); hat chain along the hat axis
P_HAT = BODY_C + HAT_AXIS * (HAT["cuff_top_u"] - 0.09)
P_TIP = BODY_C + HAT_AXIS * (HAT["dome_u0"] + 0.03)
P_POM = BODY_C + HAT_AXIS * HAT["top_u"]

# ------------------------------------------------------------------ fur shells
N_SHELLS = 16
V_BODY, V_FACE, V_LIMB, V_PAW, V_TAIL, V_POMPOM = 1.0, 0.35, 0.8, 0.62, 1.0, 1.0
PART_NONE, PART_BODY, PART_TAIL, PART_ARM, PART_LEG, PART_POMPOM = 0, 1, 2, 3, 4, 5
FUR_PARTS = (PART_BODY, PART_TAIL, PART_ARM, PART_LEG)
MASCOT_SCALE = 0.93       # owner round 2: whole mascot ~15 % smaller in the hero frame (armature object scale)
TRI_BUDGET = 150000       # owner: quality first (PC numbers; mobile untested)
PREVIEW_FUR_LEN = 0.030   # preview-only shell push (Unity's shader does this at runtime)

BONES = ['root', 'body', 'head', 'hat', 'hat_tip', 'pompom', 'arm.L', 'hand.L', 'arm.R', 'hand.R',
         'leg.L', 'foot.L', 'leg.R', 'foot.R', 'tail', 'eye.L', 'eye.R']
SIDES = ((1, 'L'), (-1, 'R'))


# ------------------------------------------------------------------ math helpers
def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def ry(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Y')


def rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def rot_pry(r):
    """r = (pitch about X, roll about Y, yaw about Z) in degrees; pitch>0 tips forward (-Y), roll>0 toward +X
    (his left), yaw>0 turns the face toward +X (his left)."""
    return rz(r[2]) @ ry(r[1]) @ rx(r[0])


def tr(v):
    return Matrix.Translation(Vector(v))


def about(pivot, m):
    pivot = Vector(pivot)
    return tr(pivot) @ m @ tr(-pivot)


def diag(sx, sy, sz):
    return Matrix.Diagonal((sx, sy, sz, 1.0))


def s1(x):
    return math.sin(2.0 * math.pi * x)


def c1(x):
    return math.cos(2.0 * math.pi * x)


def track(t, keys):
    """Cubic Hermite through (time, value) keys, Catmull-Rom tangents, flat at both ends."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    i = 0
    while keys[i + 1][0] < t:
        i += 1
    (t0, v0), (t1, v1) = keys[i], keys[i + 1]

    def slope(j):
        if j <= 0 or j >= len(keys) - 1:
            return 0.0
        return (keys[j + 1][1] - keys[j - 1][1]) / (keys[j + 1][0] - keys[j - 1][0])

    h = t1 - t0
    u = (t - t0) / h
    m0, m1 = slope(i) * h, slope(i + 1) * h
    return ((2 * u ** 3 - 3 * u ** 2 + 1) * v0 + (u ** 3 - 2 * u ** 2 + u) * m0
            + (-2 * u ** 3 + 3 * u ** 2) * v1 + (u ** 3 - u ** 2) * m1)


def hat_alpha(p):
    d = (Vector(p) - BODY_C).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, d.dot(HAT_AXIS)))))


def soft_cap(x, cap, knee):
    """Identity below cap - knee, then eases smoothly toward cap (C1 continuous safety limit)."""
    k0 = cap - knee
    if x <= k0:
        return x
    return cap - knee * math.exp(-(x - k0) / knee)


# ------------------------------------------------------------------ model analysis
def analyze(objs):
    info = {}
    body = objs['Body']
    bverts = [v.co.copy() for v in body.data.vertices]
    bfaces = [tuple(p.vertices) for p in body.data.polygons]
    info.update(body_verts=bverts, body_faces=bfaces, body_bvh=BVHTree.FromPolygons(bverts, bfaces))
    A, L, E = CONTRACT['arms'], CONTRACT['legs'], CONTRACT['eyes']
    for key in ('arm_root', 'arm_dir', 'palm_c', 'bean_c', 'arm_rest', 'eye_S', 'eye_f', 'eye_up', 'hip', 'ankle',
                'toe', 'paw_c', 'sole_n', 'pads', 'leg_rest', 'paw_rest', 'leg_verts'):
        info[key] = {}
    for _side, tag in SIDES:
        a = A[tag]
        info['arm_root'][tag] = V(a['root'])
        info['arm_dir'][tag] = V(a['dir']).normalized()
        info['palm_c'][tag] = V(a['palm_c'])
        info['bean_c'][tag] = [V(b) for b in a['beans']]
        av = [v.co.copy() for v in objs['Arm.' + tag].data.vertices]
        info['arm_rest'][tag] = av[:a['fur_verts']]
        e = E[tag]
        f = V(e['f']).normalized()
        info['eye_S'][tag], info['eye_f'][tag] = V(e['S']), f
        info['eye_up'][tag] = (Vector((0.0, 0.0, 1.0)) - f * f.z).normalized()
        g = L[tag]
        for key in ('hip', 'ankle', 'toe', 'paw_c'):
            info[key][tag] = V(g[key])
        info['sole_n'][tag] = V(g['sole_n']).normalized()
        info['pads'][tag] = [V(p) for p in g['pads']]
        lv = [v.co.copy() for v in objs['Leg.' + tag].data.vertices]
        info['leg_rest'][tag] = lv
        info['leg_verts'][tag] = g['leg_verts']
        info['paw_rest'][tag] = lv[g['leg_verts']:g['fur_verts']]
    info['mouth_c'] = V(CONTRACT['mouth_c'])
    info['nose_c'] = V(CONTRACT['nose_c'])
    info['tail_base'] = V(CONTRACT['tail']['base'])
    info['tail_c'] = V(CONTRACT['tail']['c'])
    info['pompom_c'] = POMPOM_C
    bv = [v.co.copy() for v in objs['Beanie'].data.vertices]
    info['beanie_bvh'] = BVHTree.FromPolygons(bv, [tuple(p.vertices) for p in objs['Beanie'].data.polygons])
    info['star_c'] = V(CONTRACT['star_c'])
    return info


def inside_depth(bvh, p, centre=BODY_C):
    """Depth of p below the closed surface hit by a ray from `centre` (positive = inside)."""
    d = Vector(p) - centre
    L = d.length
    if L < 1e-6:
        return 1.0
    hit = bvh.ray_cast(centre, d / L)
    if hit[0] is None:
        return -1.0
    return hit[3] - L


# ------------------------------------------------------------------ pose description
class Pose:
    """Animation parameters (degrees / meters). Defaults = the canonical seated riding pose."""

    def __init__(self):
        self.body_off = Vector((0.0, 0.0, 0.0))
        self.body_rot = [SEAT_LEAN, 0.0, 0.0]          # pitch, roll, yaw about the bottom pivot
        self.body_scl = [1.0, 1.0, 1.0]                # about the bottom pivot (squash / stretch)
        self.head_rot = [HEAD_PITCH, 0.0, 0.0]         # about the ball centre (keep roll within +-2.5)
        self.head_off = Vector((0.0, 0.0, 0.0))
        self.hat_rot = [0.0, 0.0, 0.0]
        self.hat_off = 0.0                             # along the hat axis (comic hat pop)
        self.tip_rot = [-3.0, 0.0, 0.0]
        self.pom_rot = [-5.0, 0.0, 0.0]
        self.pom_sq = 1.0                              # pom-pom squash (<1) / stretch (>1) along the hat axis
        self.arm = {'L': [12.0, -4.0, 0.0], 'R': [12.0, -4.0, 0.0]}   # raise (up), back (toward +Y), twist
        self.hand = {'L': [8.0, 0.0, 0.0], 'R': [8.0, 0.0, 0.0]}      # bend (up), swing (back), twist
        self.leg = {'L': [0.0, 0.0, 0.0], 'R': [0.0, 0.0, 0.0]}       # lift (up), spread (out), twist (toes out)
        self.foot = {'L': [0.0, 0.0, 0.0], 'R': [0.0, 0.0, 0.0]}      # flex (toes down/forward), splay, roll (out)
        self.tail_rot = [12.0, 0.0, 0.0]                               # tuck (down), wag (yaw), roll
        self.eye_scl = {'L': [1.0, 1.0, 1.0], 'R': [1.0, 1.0, 1.0]}  # eye bone local x (width), y (depth), z (height)
        self.floor_clamp = True


def mirrored(P):
    Q = Pose()
    Q.body_off = Vector((-P.body_off.x, P.body_off.y, P.body_off.z))
    Q.head_off = Vector((-P.head_off.x, P.head_off.y, P.head_off.z))
    for a in ('body_rot', 'head_rot', 'hat_rot', 'tip_rot', 'pom_rot'):
        r = getattr(P, a)
        setattr(Q, a, [r[0], -r[1], -r[2]])
    Q.body_scl, Q.hat_off, Q.pom_sq, Q.floor_clamp = list(P.body_scl), P.hat_off, P.pom_sq, P.floor_clamp
    for a in ('arm', 'hand', 'leg', 'foot', 'eye_scl'):
        d = getattr(P, a)
        setattr(Q, a, {'L': list(d['R']), 'R': list(d['L'])})
    Q.tail_rot = [P.tail_rot[0], -P.tail_rot[1], -P.tail_rot[2]]
    return Q


def body_rotm(P):
    return rot_pry(P.body_rot)


def body_lift(rotm):
    up = rotm.to_3x3() @ Vector((0.0, 0.0, 1.0))
    return TILT_RADIUS * (1.0 - max(-1.0, min(1.0, up.z)))


def body_G(P, with_scale=True):
    R = body_rotm(P)
    off = Vector((0.0, 0.0, -SEAT_DROP + body_lift(R))) + P.body_off
    S = diag(*P.body_scl) if with_scale else Matrix.Identity(4)
    return tr(BODY_BOTTOM + off) @ R @ S @ tr(-BODY_BOTTOM)


# ------------------------------------------------------------------ seated leg placement
def seat_legs(info):
    """Canonical seated legs: they ride with the body and hinge at the hips (pitch) until the heel rests on the
    slide surface (lowest paw point = FOOT_FLOOR)."""
    g_seat = body_G(Pose(), with_scale=False)
    seat = {k: {} for k in ('T', 'O', 'hip_rest', 'ankle_rest', 'toe_rest', 'hip_seat', 'ankle_seat', 'dorsal')}
    for _side, tag in SIDES:
        hip = info['hip'][tag]
        pts = info['paw_rest'][tag]

        def lowest(theta, hip=hip, pts=pts):
            m = g_seat @ about(hip, rx(theta))
            return min((m @ v).z for v in pts)

        lo, hi = -30.0, 30.0                   # bisection on whichever direction lowers the paw
        flo, fhi = lowest(lo) - FOOT_FLOOR, lowest(hi) - FOOT_FLOOR
        if flo * fhi > 0.0:
            theta = 0.0
        else:
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                fm = lowest(mid) - FOOT_FLOOR
                if (fm > 0.0) == (flo > 0.0):
                    lo, flo = mid, fm
                else:
                    hi = mid
            theta = 0.5 * (lo + hi)
        T = g_seat @ about(hip, rx(theta))
        seat['T'][tag] = T
        seat['O'][tag] = T @ info['paw_c'][tag]
        seat['hip_rest'][tag] = hip
        seat['ankle_rest'][tag] = info['ankle'][tag]
        seat['toe_rest'][tag] = info['toe'][tag]
        seat['hip_seat'][tag] = T @ hip
        seat['ankle_seat'][tag] = T @ info['ankle'][tag]
        seat['dorsal'][tag] = -info['sole_n'][tag]
        print("SEAT leg.%s hip pitch %.1f deg  paw centre (%.3f %.3f %.3f)  lowest %.3f  ankle_seat (%.3f %.3f %.3f)"
              % (tag, theta, *seat['O'][tag], lowest(theta), *seat['ankle_seat'][tag]))
    seat['body_inv'] = g_seat.inverted()
    return seat


# ------------------------------------------------------------------ armature
def build_armature(info, seat, coll):
    data = bpy.data.armatures.new("Armature")
    arm = bpy.data.objects.new("Armature", data)
    coll.objects.link(arm)
    data.display_type = 'OCTAHEDRAL'
    C.select_only([arm])
    bpy.ops.object.mode_set(mode='EDIT')
    eb = data.edit_bones
    fwd, up = Vector((0.0, -1.0, 0.0)), Vector((0.0, 0.0, 1.0))

    def bone(name, head, tail, parent, roll_to):
        b = eb.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        b.align_roll(Vector(roll_to))
        b.parent = eb[parent] if parent else None
        b.use_connect = False
        b.use_deform = True
        b.inherit_scale = 'FULL'
        return b

    A = HAT_AXIS
    bone('root', (0.0, 0.0, 0.0), (0.0, -0.2, 0.0), None, up)
    bone('body', BODY_BOTTOM, BODY_C, 'root', fwd)
    bone('head', BODY_C, BODY_C + A * 0.40, 'body', fwd)
    bone('hat', P_HAT, P_TIP, 'head', fwd)
    bone('hat_tip', P_TIP, P_POM, 'hat', fwd)
    bone('pompom', P_POM, info['pompom_c'] + A * POMPOM_R, 'hat_tip', fwd)
    for _side, tag in SIDES:
        R0, d = info['arm_root'][tag], info['arm_dir'][tag]
        bone('arm.' + tag, R0 - d * 0.03, R0 + d * ARM_HAND, 'body', up)
        bone('hand.' + tag, R0 + d * ARM_HAND, R0 + d * CONTRACT['arms'][tag]['length'], 'arm.' + tag, up)
    for _side, tag in SIDES:
        bone('leg.' + tag, seat['hip_rest'][tag], seat['ankle_rest'][tag], 'root', seat['dorsal'][tag])
        bone('foot.' + tag, seat['ankle_rest'][tag], seat['toe_rest'][tag], 'leg.' + tag, seat['dorsal'][tag])
    bone('tail', info['tail_base'] - Vector((0.0, 0.02, 0.0)), info['tail_c'] + Vector((0.0, 0.06, 0.0)), 'body', up)
    for _side, tag in SIDES:
        S, f = info['eye_S'][tag], info['eye_f'][tag]
        bone('eye.' + tag, S - f * 0.02, S + f * 0.05, 'head', info['eye_up'][tag])
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    for b in data.bones:
        print("BONE %-8s parent %-8s head (%.3f %.3f %.3f) tail (%.3f %.3f %.3f)" % (
            b.name, b.parent.name if b.parent else "-", *b.head_local, *b.tail_local))
    return arm


# ------------------------------------------------------------------ skin weights
F0 = Vector((0.0, -1.0, -0.10)).normalized()       # face centre direction from the ball centre


def body_weights(p, info):
    """Automatic (procedural) weights over body / head / tail, derived from the bone layout:
    head = face cone + everything under the beanie (pivot at the ball centre, so a head turn slides the face over
    the ball), body = bottom, back below the cuff and a patch around each arm root (arms are children of body),
    tail = soft ring around the tail."""
    d = (p - BODY_C).normalized()
    face = (smoothstep(math.cos(math.radians(64.0)), math.cos(math.radians(46.0)), d.dot(F0))
            * smoothstep(0.20, 0.30, p.z))
    top = smoothstep(CUFF_BOTTOM_A + 12.0, CUFF_BOTTOM_A - 4.0, hat_alpha(p))
    free = 1.0
    for R0 in info['arm_root'].values():
        free *= smoothstep(0.10, 0.24, (p - R0).length)
    w_head = max(face, top) * free
    w_tail = 0.45 * smoothstep(0.16, 0.075, (p - info['tail_c']).length)
    return {'body': max(0.0, 1.0 - w_head - w_tail), 'head': w_head, 'tail': w_tail}


def beanie_weights(p):
    a = hat_alpha(p)
    zone = smoothstep(CUFF_BOTTOM_A + 2.0, 56.0, a)    # cuff bottom stays on the head, crown follows the hat
    tip = 0.7 * smoothstep(34.0, 8.0, a)               # crown top follows hat_tip (carries the pom-pom)
    return {'head': 1.0 - zone, 'hat': max(0.0, zone - tip), 'hat_tip': tip}


def set_weights(obj, fn):
    groups = {}
    for v in obj.data.vertices:
        ws = {b: w for b, w in fn(v.co.copy(), v.index).items() if w > 1e-4}
        tot = sum(ws.values())
        for b, w in ws.items():
            vg = groups.get(b)
            if vg is None:
                vg = groups[b] = obj.vertex_groups.get(b) or obj.vertex_groups.new(name=b)
            vg.add([v.index], w / tot, 'REPLACE')


def assign_weights(objs, info, seat):
    set_weights(objs['Body'], lambda p, i: body_weights(p, info))
    bvh = info['body_bvh']

    def tail_w(p, i):
        wb = 0.5 * smoothstep(-0.005, 0.03, inside_depth(bvh, p))
        return {'tail': 1.0 - wb, 'body': wb}
    set_weights(objs['Tail'], tail_w)
    for name in ('Mouth', 'Tongue'):
        set_weights(objs[name], lambda p, i: {'head': 1.0})
    for _side, tag in SIDES:
        for name in ('Eye.' + tag, 'Catchlight.%s1' % tag, 'Catchlight.%s2' % tag):
            set_weights(objs[name], lambda p, i, t=tag: {'eye.' + t: 1.0})
        R0, d = info['arm_root'][tag], info['arm_dir'][tag]

        def arm_w(p, i, R0=R0, d=d, t=tag):
            w = smoothstep(ARM_HAND - 0.05, ARM_HAND + 0.06, (p - R0).dot(d))
            return {'arm.' + t: 1.0 - w, 'hand.' + t: w}
        set_weights(objs['Arm.' + tag], arm_w)
        hip, ank = info['hip'][tag], info['ankle'][tag]
        axis = (ank - hip).normalized()
        L = (ank - hip).length
        nlv = info['leg_verts'][tag]

        def leg_w(p, i, hip=hip, ank=ank, axis=axis, L=L, nlv=nlv, t=tag):
            if i < nlv:                                    # leg capsule: blends into the paw at the ankle
                w = 0.5 * smoothstep(L - 0.05, L + 0.02, (p - hip).dot(axis))
            else:                                          # paw + pads
                w = 1.0 - 0.35 * smoothstep(0.07, 0.02, (p - ank).length)
            return {'leg.' + t: 1.0 - w, 'foot.' + t: w}
        set_weights(objs['Leg.' + tag], leg_w)
    set_weights(objs['Beanie'], lambda p, i: beanie_weights(p))
    star_w = beanie_weights(info['star_c'])            # uniform: the badge moves rigidly
    set_weights(objs['StarBadge'], lambda p, i: star_w)
    set_weights(objs['PomPom'], lambda p, i: {'pompom': 1.0})


# ------------------------------------------------------------------ fur mask / shell tagging
def ramp_face(r, r0, r1, r2, r3):
    """0 inside r0 (feature covers the skin) -> V_FACE at r1, plateau to r2, -> 1 at r3."""
    if r <= r1:
        return V_FACE * smoothstep(r0, r1, r)
    return V_FACE + (1.0 - V_FACE) * smoothstep(r2, r3, r)


def body_fur_v(p, info):
    v = smoothstep(CUFF_BOTTOM_A - 6.0, CUFF_BOTTOM_A + 1.0, hat_alpha(p))   # none under the beanie
    f = 1.0
    es, ms = CONTRACT.get('eye_scale', 1.0), CONTRACT.get('mouth_scale', 1.0)   # optional (v4 candidate: bigger face)
    for S in info['eye_S'].values():
        f = min(f, ramp_face((p - S).length, 0.068 * es, 0.094 * es, 0.115 * es, 0.175 * es))
    m = info['mouth_c']
    q = math.sqrt(((p.x - m.x) / (0.066 * ms)) ** 2 + ((p.z - m.z - 0.002) / (0.054 * ms)) ** 2
                  + ((p.y - m.y) / (0.07 * ms)) ** 2)
    f = min(f, ramp_face(q, 1.05, 1.32, 1.6, 2.5))
    f = min(f, ramp_face((p - info['nose_c']).length, 0.016, 0.03, 0.04, 0.08))
    return V_BODY * v * f


def tag_fur(objs, info):
    """Per-object attributes consumed by build_shells(): bwk_part (face), bwk_furv / bwk_hide (point)."""
    body_bvh, hat_bvh = info['body_bvh'], info['beanie_bvh']
    for name, obj in objs.items():
        me = obj.data
        mats = [m.name if m else "" for m in me.materials]
        part = [PART_NONE] * len(me.polygons)
        furv = [0.0] * len(me.vertices)
        hide = [0] * len(me.vertices)
        if name == 'Body':
            part = [PART_BODY] * len(me.polygons)
            furv = [body_fur_v(v.co, info) for v in me.vertices]
        elif name == 'Tail':
            part = [PART_TAIL] * len(me.polygons)
            furv = [V_TAIL] * len(me.vertices)
            hide = [1 if inside_depth(body_bvh, v.co) > 0.002 else 0 for v in me.vertices]
        elif name.startswith('Arm.') or name.startswith('Leg.'):
            tag = name[-1]
            arm = name.startswith('Arm.')
            pid = PART_ARM if arm else PART_LEG
            part = [pid if mats[pl.material_index] == "M_Fur" else PART_NONE for pl in me.polygons]
            nlv = info['leg_verts'][tag] if not arm else 0
            sole_k = CONTRACT.get('sole_fur')      # optional (v5 candidate): None = v4 / v3 behaviour unchanged
            for v in me.vertices:
                if arm:
                    w = V_LIMB                             # no palm pads: full fur mitt
                else:
                    w = V_LIMB if v.index < nlv else V_PAW
                    pad_lo = 0.25
                    if sole_k is not None and v.index >= nlv:
                        # v5: the sole side of the paw keeps only a short velvet pile, so the smooth white sole and its
                        # pink pads read from the rear gameplay camera like the reference (owner 2026-11-27 item 05)
                        w *= 1.0 - (1.0 - sole_k) * smoothstep(-0.15, 0.45, v.normal.dot(info['sole_n'][tag]))
                        pad_lo = 0.0
                    for k, pc in enumerate(info['pads'][tag]):
                        r0, r1 = (0.058, 0.082) if k == 0 else (0.024, 0.040)
                        w *= pad_lo + (1.0 - pad_lo) * smoothstep(r0, r1, (v.co - pc).length)
                hide[v.index] = 1 if inside_depth(body_bvh, v.co) > 0.002 else 0
                furv[v.index] = w
        elif name == 'PomPom':
            # dark core = shell fur; the radial yarn fibres (M_PawPad, round 3) are real geometry: no shells
            part = [PART_POMPOM if mats[pl.material_index] == "M_PomPom" else PART_NONE for pl in me.polygons]
            furv = [V_POMPOM] * len(me.vertices)
            hide = [1 if inside_depth(hat_bvh, v.co) > 0.004 else 0 for v in me.vertices]
        a = me.attributes.new("bwk_part", 'INT', 'FACE')
        a.data.foreach_set("value", part)
        a = me.attributes.new("bwk_furv", 'FLOAT', 'POINT')
        a.data.foreach_set("value", furv)
        a = me.attributes.new("bwk_hide", 'INT', 'POINT')
        a.data.foreach_set("value", hide)


def build_shells(obj):
    """N coincident shell copies of the visible fur faces (same positions, weights, UVs, material) + ShellUV.
    Face order = skin, shell 1, ..., shell N so each material's index buffer draws inner -> outer."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    part_l = bm.faces.layers.int.get("bwk_part")
    furv_l = bm.verts.layers.float.get("bwk_furv")
    hide_l = bm.verts.layers.int.get("bwk_hide")
    shell_uv = bm.loops.layers.uv.new("ShellUV")
    for f in bm.faces:
        fur = f[part_l] in FUR_PARTS or f[part_l] == PART_POMPOM
        for lp in f.loops:
            lp[shell_uv].uv = (0.0, lp.vert[furv_l] if fur else 0.0)

    def visible(f):
        return (max(lp.vert[furv_l] for lp in f.loops) > 0.02
                and not all(lp.vert[hide_l] for lp in f.loops))

    groups = {'fur': [f for f in bm.faces if f[part_l] in FUR_PARTS and visible(f)],
              'pompom': [f for f in bm.faces if f[part_l] == PART_POMPOM and visible(f)]}
    stats = {k: sum(len(f.verts) - 2 for f in v) for k, v in groups.items()}
    per_part = {}
    for f in groups['fur']:
        per_part[f[part_l]] = per_part.get(f[part_l], 0) + len(f.verts) - 2
    for k in range(1, N_SHELLS + 1):
        for key in ('fur', 'pompom'):
            faces = groups[key]
            verts = {v for f in faces for v in f.verts}
            edges = {e for f in faces for e in f.edges}
            ret = bmesh.ops.duplicate(bm, geom=list(verts) + list(edges) + faces)
            u = k / float(N_SHELLS)
            for g in ret['geom']:
                if isinstance(g, bmesh.types.BMFace):
                    for lp in g.loops:
                        lp[shell_uv].uv = (u, lp.vert[furv_l])
    bm.to_mesh(me)
    bm.free()
    for nm in ("bwk_part", "bwk_furv", "bwk_hide"):
        if nm in me.attributes:
            me.attributes.remove(me.attributes[nm])
    me.update()
    names = {PART_BODY: "body", PART_TAIL: "tail", PART_ARM: "arms", PART_LEG: "legs"}
    print("SHELLS layers %d  per-layer tris: fur %d (%s)  pompom %d" % (
        N_SHELLS, stats['fur'], ", ".join("%s %d" % (names[k], v) for k, v in sorted(per_part.items())),
        stats['pompom']))
    return stats


# ------------------------------------------------------------------ clips
def with_follow(fn, dur, loop):
    """Overlapping action for hat / hat_tip / pom-pom: they lag the head's world tilt, and the pom-pom squashes
    when the body accelerates up and stretches when it falls."""
    def at(t):
        return fn(t % dur if loop else min(dur, max(0.0, t)))

    def f(t):
        P = fn(t)
        win = 1.0 if loop else 1.0 - smoothstep(dur - 0.14, dur, t)

        def ang(Q):
            return (Q.body_rot[0] + Q.head_rot[0], Q.body_rot[1] + Q.head_rot[1])
        a0 = ang(P)
        for attr, gain, lag in (('hat_rot', 0.18, 0.07), ('tip_rot', 0.40, 0.12), ('pom_rot', 0.85, 0.18)):
            aq = ang(at(t - lag))
            r = getattr(P, attr)
            r[0] += win * gain * (aq[0] - a0[0])
            r[1] += win * gain * (aq[1] - a0[1])
        dz = at(t - 0.10).body_off.z - P.body_off.z
        P.pom_sq *= 1.0 + win * max(-0.14, min(0.14, 2.5 * dz))
        return P
    return f


def blink_amount(t, t0):
    dt = t - t0
    if dt < 0.0 or dt > 0.2:
        return 0.0
    if dt < 0.067:
        return smoothstep(0.0, 0.067, dt)
    if dt < 0.1:
        return 1.0
    return 1.0 - smoothstep(0.1, 0.2, dt)


def clip_idle(t, D=2.0):
    """Seated at the top of the slide: breathing, blink, small happy look around, arms relaxed lower."""
    p = t / D
    P = Pose()
    P.body_scl = [1.0 + 0.010 * s1(p)] * 3
    look = s1(p)
    look = math.copysign(abs(look) ** 0.6, look)
    P.body_rot[0] += 1.2 * s1(p - 0.08)
    P.body_rot[2] += 3.0 * look
    P.head_rot = [4.0 + 1.5 * c1(2 * p), 2.0 * look, 10.0 * look]
    b = blink_amount(t, 1.42)
    for tag in 'LR':
        P.eye_scl[tag] = [1.0 + 0.05 * b, 1.0, 1.0 - 0.9 * b]
    P.arm['L'] = [-8.0 + 4.0 * s1(p + 0.15), -6.0 + 2.0 * s1(2 * p), 0.0]
    P.arm['R'] = [-8.0 + 4.0 * s1(p + 0.15), -6.0 + 2.0 * s1(2 * p + 0.5), 0.0]
    P.hand['L'] = [6.0 + 7.0 * s1(2 * p + 0.3), 0.0, 0.0]
    P.hand['R'] = [6.0 + 7.0 * s1(2 * p + 0.8), 0.0, 0.0]
    P.foot['L'] = [6.0 * s1(2 * p), 3.0 * s1(2 * p + 0.25), 0.0]
    P.foot['R'] = [6.0 * s1(2 * p + 0.5), 3.0 * s1(2 * p + 0.75), 0.0]
    P.tail_rot = [12.0, 12.0 * s1(2 * p), 0.0]
    return P


def clip_slide(t, D=1.0):
    """Seated sliding ("wheee"): gentle bob on the water, big arms up and out balancing with soft waves, paws
    bobbing forward, tail wiggle."""
    p = t / D
    P = Pose()
    # every term is zero (or at its rest value) at t = 0.25 s, the frame the Unity hero capture samples
    P.body_off.z += 0.010 * s1(2 * p + 0.5)
    P.body_rot[0] += 1.2 * s1(2 * p + 0.5)
    P.body_rot[1] += 2.5 * s1(p + 0.75)
    P.body_rot[2] += 1.2 * s1(p + 0.25)
    P.head_rot = [HEAD_PITCH - 1.2 * s1(2 * p + 0.5), -1.2 * s1(p + 0.75), -1.0 * s1(p + 0.25)]
    P.arm['L'] = [4.0 * s1(p + 0.75), 3.0 * s1(2 * p + 0.5), 0.0]
    P.arm['R'] = [-4.0 * s1(p + 0.75), 3.0 * s1(2 * p + 0.5), 0.0]
    P.hand['L'] = [4.0 + 6.0 * s1(2 * p + 0.5), 0.0, 0.0]
    P.hand['R'] = [4.0 - 6.0 * s1(2 * p + 0.5), 0.0, 0.0]
    P.leg['L'] = [1.5 * s1(2 * p + 0.5), 0.0, 0.0]
    P.leg['R'] = [-1.5 * s1(2 * p + 0.5), 0.0, 0.0]
    P.foot['L'] = [3.0 * s1(2 * p + 0.5), 0.0, 0.0]
    P.foot['R'] = [-3.0 * s1(2 * p + 0.5), 0.0, 0.0]
    P.tail_rot = [14.0, 8.0 * s1(2 * p + 0.5), 0.0]
    P.tip_rot, P.pom_rot = [-2.0, 0.0, 0.0], [-3.0 + 2.0 * s1(4 * p), 0.0, 0.0]
    return P


def clip_lean_left(t, D=0.8):
    """Whole seated body rolls ~16 deg to his left from the bottom pivot; outer arm up high, inner arm lower."""
    p = t / D
    P = Pose()
    P.body_rot[1] += 16.0 + 1.5 * s1(p)
    P.body_rot[0] += 1.0 * s1(2 * p)
    P.body_rot[2] += 3.0
    P.body_off.z += 0.006 * s1(2 * p)
    P.head_rot = [HEAD_PITCH, -2.5 + 0.8 * s1(p - 0.1), 4.0]
    P.arm['R'] = [22.0 + 3.0 * s1(2 * p + 0.2), -4.0, 0.0]
    P.arm['L'] = [-14.0 + 3.0 * s1(2 * p), 6.0, 0.0]
    P.hand['R'] = [14.0 + 8.0 * s1(2 * p + 0.4), 0.0, 0.0]
    P.hand['L'] = [-2.0 + 4.0 * s1(2 * p + 0.1), 0.0, 0.0]
    P.leg['R'] = [6.0 + 3.0 * s1(2 * p + 0.3), 2.0, 0.0]
    P.foot['R'] = [4.0 * s1(2 * p + 0.5), 0.0, 0.0]
    P.foot['L'] = [3.0 * s1(2 * p + 0.2), 0.0, 0.0]
    P.tail_rot = [14.0, -10.0, 0.0]
    P.tip_rot, P.pom_rot = [-6.0, -8.0, 0.0], [-9.0, -14.0, 0.0]
    return P


def clip_turn_left(t, D=0.8):
    """Whole body yaws ~12 deg into a left curve and rolls into it; head looks further in; arms asymmetric."""
    p = t / D
    P = Pose()
    P.body_rot[2] += 12.0 + 1.0 * s1(p)
    P.body_rot[1] += 9.0 + 1.5 * s1(2 * p)
    P.body_rot[0] += 1.0 * s1(2 * p + 0.2)
    P.body_off.z += 0.006 * s1(2 * p)
    P.head_rot = [HEAD_PITCH, -2.0, 7.0 + 1.5 * s1(p - 0.1)]
    P.arm['R'] = [20.0 + 3.0 * s1(2 * p + 0.2), -22.0, 0.0]
    P.arm['L'] = [-4.0 + 3.0 * s1(2 * p), 20.0, 0.0]
    P.hand['R'] = [12.0 + 8.0 * s1(2 * p + 0.4), 0.0, 0.0]
    P.hand['L'] = [5.0 * s1(2 * p + 0.1), 0.0, 0.0]
    P.leg['R'], P.leg['L'] = [5.0, 0.0, 0.0], [1.0, 0.0, 0.0]
    P.foot['R'] = [4.0 * s1(2 * p + 0.5), 0.0, 0.0]
    P.foot['L'] = [4.0 * s1(2 * p), 0.0, 0.0]
    P.tail_rot = [14.0, -12.0, 0.0]
    P.tip_rot, P.pom_rot = [-6.0, -5.0, 0.0], [-9.0, -10.0, 0.0]
    return P


def clip_accelerate(t, D=0.6):
    """Downhill / boost: reclines ~12 deg more, paws lifted forward, arms up and back, quick bob, pom-pom streams."""
    p = t / D
    P = Pose()
    P.body_rot[0] = SEAT_LEAN - 9.0 + 1.5 * s1(2 * p)
    P.body_rot[1] += 1.5 * s1(p)
    P.body_off.z += 0.012 * s1(2 * p)
    P.head_rot = [HEAD_PITCH + 5.0 - 1.0 * s1(2 * p + 0.1), -1.0 * s1(p), 0.0]
    for tag, ph in (('L', 0.0), ('R', 0.12)):
        P.arm[tag] = [20.0 + 3.0 * s1(2 * p + 0.25 + ph), 26.0 + 5.0 * s1(2 * p + 0.4 + ph), 0.0]
        P.hand[tag] = [-10.0 + 8.0 * s1(4 * p + ph), 0.0, 0.0]
        P.leg[tag] = [14.0 + 3.0 * s1(2 * p + 0.3 + ph), 0.0, 0.0]
        P.foot[tag] = [-8.0 + 4.0 * s1(2 * p + 0.5 + ph), 0.0, 0.0]
        P.eye_scl[tag] = [1.04, 1.0, 1.08]
    P.tail_rot = [20.0, 4.0 * s1(4 * p), 0.0]
    P.tip_rot, P.pom_rot = [-14.0, 2.0 * s1(2 * p), 0.0], [-24.0 + 5.0 * s1(4 * p), 3.0 * s1(2 * p), 0.0]
    return P


def clip_balance(t, D=1.2):
    """Seated wobble +-10 deg with windmilling arms."""
    p = t / D
    P = Pose()
    P.body_rot[1] += 10.0 * s1(p) + 2.0 * s1(2 * p + 0.1)
    P.body_rot[0] += 3.0 * s1(2 * p + 0.25)
    P.body_rot[2] += 3.0 * s1(p + 0.2)
    P.body_off.z += 0.005 * s1(2 * p)
    P.head_rot = [HEAD_PITCH + 2.0 * s1(2 * p), -2.5 * s1(p - 0.08), 3.0 * s1(p + 0.1)]
    for tag, ph in (('L', 0.0), ('R', 0.5)):
        P.arm[tag] = [6.0 + 16.0 * s1(2 * p + ph), 32.0 * c1(2 * p + ph), 0.0]
        P.hand[tag] = [8.0 + 10.0 * s1(2 * p + ph + 0.2), 0.0, 0.0]
        P.leg[tag] = [4.0 + 8.0 * s1(2 * p + ph + 0.1), 0.0, 0.0]
        P.foot[tag] = [8.0 * s1(2 * p + ph + 0.3), 0.0, 0.0]
        P.eye_scl[tag] = [1.06, 1.0, 1.12]
    P.tail_rot = [12.0, 10.0 * s1(2 * p), 0.0]
    return P


def jump_z(t):
    if t <= 0.12:
        return -0.02 * smoothstep(0.0, 0.12, t)                 # crouch
    if t <= 0.18:
        u = (t - 0.12) / 0.06
        return -0.02 + 0.06 * u * u                              # push off (ends at 2 m/s)
    if t <= 0.70:
        a = t - 0.18
        return 0.04 + 2.0 * a - 4.0 * a * a                      # ballistic, apex 0.29 m at 0.43 s
    if t <= 0.76:
        u = (t - 0.70) / 0.06
        return -0.0016 + (-0.025 + 0.0016) * (1.0 - (1.0 - u) ** 2)   # impact squash
    u = (t - 0.76) / 0.14
    return -0.025 * (1.0 - smoothstep(0.0, 1.0, u)) + 0.010 * math.sin(math.pi * u) * (1.0 - u)


def clip_jump(t, D=0.9):
    """One-shot: push up from seated, tuck (paws pulled in, arms up), open and land back seated."""
    P = Pose()
    P.body_off.z += jump_z(t)
    sq = track(t, [(0.0, 1.0), (0.10, 0.88), (0.19, 1.10), (0.32, 1.03), (0.45, 1.0), (0.66, 1.03),
                   (0.74, 0.84), (0.82, 1.05), (0.9, 1.0)])
    P.body_scl = [1.0 / math.sqrt(sq), 1.0 / math.sqrt(sq), sq]
    P.body_rot[0] += track(t, [(0.0, 0.0), (0.10, 6.0), (0.20, -2.0), (0.45, -6.0), (0.66, -2.0), (0.74, 4.0),
                               (0.82, -1.0), (0.9, 0.0)])
    P.head_rot[0] = track(t, [(0.0, HEAD_PITCH), (0.10, 12.0), (0.22, 3.0), (0.45, 0.0), (0.72, 12.0),
                              (0.82, 6.0), (0.9, HEAD_PITCH)])
    for tag, lag in (('L', 0.0), ('R', 0.02)):
        tt = max(0.0, t - lag)
        P.arm[tag] = [track(tt, [(0.0, 12.0), (0.10, -10.0), (0.22, 20.0), (0.42, 26.0), (0.60, 18.0), (0.72, 4.0),
                                 (0.82, 14.0), (0.9, 12.0)]),
                      track(tt, [(0.0, -4.0), (0.10, 20.0), (0.22, -10.0), (0.42, -22.0), (0.60, -10.0), (0.72, 6.0),
                                 (0.9, -4.0)]), 0.0]
        P.hand[tag] = [track(tt, [(0.0, 8.0), (0.12, -10.0), (0.30, 20.0), (0.45, 24.0), (0.65, 6.0), (0.75, -6.0),
                                  (0.9, 8.0)]), 0.0, 0.0]
        P.leg[tag] = [track(tt, [(0.0, 0.0), (0.10, -3.0), (0.25, 14.0), (0.42, 26.0), (0.60, 12.0), (0.70, 2.0),
                                 (0.76, -2.0), (0.9, 0.0)]),
                      track(tt, [(0.0, 0.0), (0.25, -8.0), (0.42, -12.0), (0.65, -4.0), (0.9, 0.0)]), 0.0]
        P.foot[tag] = [track(tt, [(0.0, 0.0), (0.25, 10.0), (0.42, 16.0), (0.65, 4.0), (0.75, -6.0), (0.9, 0.0)]),
                       0.0, 0.0]
        e = track(t, [(0.0, 1.0), (0.08, 0.7), (0.20, 1.1), (0.45, 1.0), (0.70, 1.0), (0.74, 0.45), (0.84, 1.05),
                      (0.9, 1.0)])
        P.eye_scl[tag] = [1.0 + 0.3 * max(0.0, 1.0 - e), 1.0, e]
    P.tail_rot[0] = track(t, [(0.0, 12.0), (0.22, 0.0), (0.45, 24.0), (0.74, 4.0), (0.9, 12.0)])
    return P


def clip_splash(t, D=0.6):
    """One-shot: seated impact squash, arms flung up, paws kick."""
    P = Pose()
    sq = track(t, [(0.0, 1.0), (0.06, 0.80), (0.16, 1.08), (0.28, 0.96), (0.40, 1.02), (0.50, 0.995), (0.6, 1.0)])
    P.body_scl = [1.0 / math.sqrt(sq), 1.0 / math.sqrt(sq), sq]
    P.body_off.z += track(t, [(0.0, 0.0), (0.06, -0.02), (0.16, 0.03), (0.30, -0.004), (0.42, 0.004), (0.6, 0.0)])
    P.body_rot[0] += track(t, [(0.0, 0.0), (0.06, 5.0), (0.18, -4.0), (0.32, 2.0), (0.6, 0.0)])
    P.head_rot[0] = track(t, [(0.0, HEAD_PITCH), (0.06, 12.0), (0.16, 3.0), (0.30, 9.0), (0.6, HEAD_PITCH)])
    for tag, lag in (('L', 0.0), ('R', 0.015)):
        tt = max(0.0, t - lag)
        P.arm[tag] = [track(tt, [(0.0, 12.0), (0.06, 24.0), (0.16, 26.0), (0.30, 18.0), (0.45, 10.0), (0.6, 12.0)]),
                      track(tt, [(0.0, -4.0), (0.06, 16.0), (0.18, 10.0), (0.6, -4.0)]), 0.0]
        P.hand[tag] = [track(tt, [(0.0, 8.0), (0.06, 24.0), (0.18, 14.0), (0.30, -4.0), (0.45, 8.0), (0.6, 8.0)]),
                       0.0, 0.0]
        P.leg[tag] = [track(tt, [(0.0, 0.0), (0.06, 14.0), (0.18, 8.0), (0.32, -2.0), (0.6, 0.0)]), 0.0, 0.0]
        P.foot[tag] = [track(tt, [(0.0, 0.0), (0.06, 12.0), (0.2, -4.0), (0.6, 0.0)]), 0.0, 0.0]
        e = track(t, [(0.0, 1.0), (0.05, 0.35), (0.14, 1.12), (0.30, 0.98), (0.6, 1.0)])
        P.eye_scl[tag] = [1.0 + 0.25 * max(0.0, 1.0 - e), 1.0, e]
    return P


def clip_bump(t, D=0.5):
    """One-shot: comic bonk wobble while seated (eyes squeezed, hat pops up, damped wobble)."""
    P = Pose()
    env = smoothstep(0.0, 0.04, t) * (1.0 - smoothstep(0.36, 0.5, t)) * math.exp(-5.0 * t)
    w = 2.0 * math.pi
    P.body_rot[0] += -14.0 * env * math.cos(w * 3.0 * t)
    P.body_rot[1] += 10.0 * env * math.sin(w * 4.0 * t)
    P.body_rot[2] += 4.0 * env * math.sin(w * 3.0 * t + 0.6)
    sq = 1.0 - 0.12 * env * max(0.0, math.cos(w * 4.0 * t))
    P.body_scl = [1.0 / math.sqrt(sq), 1.0 / math.sqrt(sq), sq]
    P.head_rot = [HEAD_PITCH + 8.0 * env * math.sin(w * 4.0 * t + 0.5), -2.5 * env * math.sin(w * 4.0 * t + 0.3),
                  6.0 * env * math.sin(w * 3.0 * t)]
    P.hat_off = 0.045 * track(t, [(0.0, 0.0), (0.06, 1.0), (0.16, 0.25), (0.24, 0.55), (0.34, 0.0), (0.5, 0.0)])
    e = track(t, [(0.0, 1.0), (0.03, 0.2), (0.16, 0.2), (0.24, 1.1), (0.34, 1.0), (0.5, 1.0)])
    for tag, ph in (('L', 0.0), ('R', 1.7)):
        P.eye_scl[tag] = [1.0 + 0.15 * max(0.0, 1.0 - e), 1.0, e]
        P.arm[tag] = [12.0 + 14.0 * env * math.sin(w * 5.0 * t + ph),
                      -4.0 + 18.0 * env * math.cos(w * 5.0 * t + ph), 0.0]
        P.hand[tag] = [8.0 + 20.0 * env * math.sin(w * 5.0 * t + ph + 0.8), 0.0, 0.0]
        P.leg[tag] = [14.0 * env * abs(math.sin(w * 4.0 * t + ph)), 0.0, 0.0]
        P.foot[tag] = [12.0 * env * math.sin(w * 5.0 * t + ph), 0.0, 0.0]
    return P


def clip_swim(t, D=0.8):
    """Water pools: pitched forward, doggy-paddle arm strokes (still showing his back), kicking paws."""
    p = t / D
    P = Pose()
    P.floor_clamp = False
    P.body_rot[0] = 18.0 + 3.0 * s1(2 * p)
    P.body_rot[1] += 4.0 * s1(p)
    P.body_rot[2] += 3.0 * s1(p + 0.25)
    P.body_off.z += -0.07 + 0.012 * s1(2 * p + 0.2)
    P.head_rot = [-12.0 - 2.0 * s1(2 * p), -1.5 * s1(p), -2.0 * s1(p + 0.25)]
    for tag, ph in (('L', 0.0), ('R', 0.5)):
        P.arm[tag] = [-10.0 + 16.0 * s1(2 * p + ph), -24.0 + 22.0 * c1(2 * p + ph), 0.0]
        P.hand[tag] = [10.0 * s1(2 * p + ph + 0.25), 0.0, 0.0]
        P.leg[tag] = [-16.0 + 14.0 * s1(2 * p + ph + 0.25), 0.0, 0.0]
        P.foot[tag] = [10.0 * s1(2 * p + ph + 0.4), 0.0, 0.0]
    P.tail_rot = [8.0, 15.0 * s1(2 * p), 0.0]
    P.tip_rot, P.pom_rot = [-6.0, 0.0, 0.0], [-8.0 + 3.0 * s1(2 * p), 0.0, 0.0]
    return P


def clip_celebrate(t, D=1.2):
    """Happy bounce with both arms up (palms turned forward), wiggle, eyes squeezed happy (eye bone scale)."""
    p = t / D
    P = Pose()
    q = (2.0 * p) % 1.0
    hop = 4.0 * q * (1.0 - q)
    contact = math.exp(-(min(q, 1.0 - q) / 0.07) ** 2)
    P.body_off.z += 0.07 * hop
    sq = 1.0 - 0.10 * contact + 0.04 * hop
    P.body_scl = [1.0 / math.sqrt(sq), 1.0 / math.sqrt(sq), sq]
    P.body_rot[1] += 7.0 * s1(p)
    P.body_rot[2] += 8.0 * s1(p + 0.25)
    P.body_rot[0] += 2.0 * s1(2 * p + 0.1)
    P.head_rot = [3.0 - 4.0 * s1(2 * p + 0.1), 2.5 * s1(p - 0.08), -3.0 * s1(p + 0.25)]
    for tag, ph in (('L', 0.0), ('R', 0.5)):
        P.arm[tag] = [22.0 + 4.0 * s1(4 * p + ph * 0.5), -10.0 + 12.0 * s1(2 * p + ph), -70.0]
        P.hand[tag] = [10.0 + 14.0 * s1(4 * p + ph), 0.0, 0.0]
        P.leg[tag] = [8.0 + 10.0 * s1(2 * p + ph), 0.0, 0.0]
        P.foot[tag] = [10.0 * s1(4 * p + ph), 0.0, 0.0]
        # optional contract key (v5, owner 2026-11-27: "squinting slit eyes" in the finish): big open happy eyes
        P.eye_scl[tag] = [1.06, 1.0, 1.06] if CONTRACT.get('celebrate_eye_open') else [1.10, 0.9, 0.22]
    P.tail_rot = [10.0, 18.0 * s1(4 * p), 0.0]
    P.tip_rot, P.pom_rot = [-4.0, 0.0, 0.0], [-6.0, 0.0, 0.0]
    return P


def clip_list():
    raw = [("Idle", 2.0, True, clip_idle), ("Slide", 1.0, True, clip_slide),
           ("LeanLeft", 0.8, True, clip_lean_left),
           ("LeanRight", 0.8, True, lambda t: mirrored(clip_lean_left(t))),
           ("TurnLeft", 0.8, True, clip_turn_left),
           ("TurnRight", 0.8, True, lambda t: mirrored(clip_turn_left(t))),
           ("Accelerate", 0.6, True, clip_accelerate), ("Balance", 1.2, True, clip_balance),
           ("Jump", 0.9, False, clip_jump), ("Splash", 0.6, False, clip_splash), ("Bump", 0.5, False, clip_bump),
           ("Swim", 0.8, True, clip_swim), ("Celebrate", 1.2, True, clip_celebrate)]
    return [(n, d, lp, with_follow(fn, d, lp)) for n, d, lp, fn in raw]


# ------------------------------------------------------------------ pose solver
class Rig:
    def __init__(self, arm, info, seat):
        self.arm, self.info, self.seat = arm, info, seat
        self.rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        self.rest_inv = {k: m.inverted() for k, m in self.rest.items()}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
        self.foot_samples = {tag: info['paw_rest'][tag][::3] for _s, tag in SIDES}
        self.arm_probe = {}
        self.lowered = 0.0                       # max arm raise removed by the cuff collision solve (diagnostic)
        for _s, tag in SIDES:                    # arm surface points outside the body (h > 3 cm) + skin weight
            R0, d = info['arm_root'][tag], info['arm_dir'][tag]
            self.arm_probe[tag] = [(v, smoothstep(ARM_HAND - 0.05, ARM_HAND + 0.06, (v - R0).dot(d)))
                                   for v in info['arm_rest'][tag][::2] if (v - R0).dot(d) > 0.03]

    def solve(self, P):
        I, seat = self.info, self.seat
        G = {'root': Matrix.Identity(4)}
        gb = body_G(P)
        G['body'] = gb
        G['head'] = gb @ tr(BODY_C + P.head_off) @ rot_pry(P.head_rot) @ tr(-BODY_C)
        G['hat'] = G['head'] @ tr(P_HAT + HAT_AXIS * P.hat_off) @ rot_pry(P.hat_rot) @ tr(-P_HAT)
        G['hat_tip'] = G['hat'] @ about(P_TIP, rot_pry(P.tip_rot))
        s = P.pom_sq
        rp = self.rest['pompom']
        G['pompom'] = (G['hat_tip'] @ about(P_POM, rot_pry(P.pom_rot))
                       @ rp @ diag(1.0 / math.sqrt(s), s, 1.0 / math.sqrt(s)) @ self.rest_inv['pompom'])
        gh_inv = G['head'].inverted()
        for side, tag in SIDES:
            R0, d = I['arm_root'][tag], I['arm_dir'][tag]
            ra, bk, tw = P.arm[tag]
            bd, sw, tw2 = P.hand[tag]
            ra = soft_cap(ra, ARM_RAISE_MAX, 6.0)

            def arm_pose(raise_deg, R0=R0, d=d, side=side, bk=bk, tw=tw, bd=bd, sw=sw, tw2=tw2):
                ga = gb @ about(R0 - d * 0.03, rz(side * bk) @ ry(-side * raise_deg)
                                @ Matrix.Rotation(math.radians(side * tw), 4, d))
                gh = ga @ about(R0 + d * ARM_HAND, rz(side * sw) @ ry(-side * bd)
                                @ Matrix.Rotation(math.radians(side * tw2), 4, d))
                return ga, gh

            def cuff_depth(ga, gh, tag=tag):
                return max(hat_depth(gh_inv @ ((ga @ v) * (1.0 - w) + (gh @ v) * w), I['beanie_bvh'])
                           for v, w in self.arm_probe[tag])

            ga, gh = arm_pose(ra)
            if cuff_depth(ga, gh) > ARM_CUFF_TOL:    # arm would touch the beanie cuff: lower it until clear
                lo, hi = ra - 50.0, ra
                for _ in range(8):
                    mid = 0.5 * (lo + hi)
                    if cuff_depth(*arm_pose(mid)) > ARM_CUFF_TOL:
                        hi = mid
                    else:
                        lo = mid
                ga, gh = arm_pose(lo)
                self.lowered = max(self.lowered, ra - lo)
            G['arm.' + tag], G['hand.' + tag] = ga, gh
            re = self.rest['eye.' + tag]
            G['eye.' + tag] = G['head'] @ re @ diag(*P.eye_scl[tag]) @ self.rest_inv['eye.' + tag]
        tk, wg, rl = P.tail_rot
        G['tail'] = gb @ about(self.rest['tail'].translation, rz(wg) @ ry(rl) @ rx(-tk))
        follow = body_G(P, with_scale=False) @ seat['body_inv']        # legs ride with the body
        squash = gb @ seat['body_inv']                                  # ... and with its squash bulge (anchor only)
        for side, tag in SIDES:
            lift, spread, twist = P.leg[tag]
            flex, splay, roll = P.foot[tag]
            anchor = seat['O'][tag]
            bulge = tr((squash @ anchor) - (follow @ anchor))
            hip = about(seat['hip_seat'][tag], rz(side * twist) @ ry(-side * spread) @ rx(-lift))
            gl = bulge @ follow @ hip @ seat['T'][tag]
            gf = (bulge @ follow @ hip @ about(seat['ankle_seat'][tag], rz(side * splay) @ ry(side * roll) @ rx(flex))
                  @ seat['T'][tag])
            if P.floor_clamp:
                zmin = min((gf @ v).z for v in self.foot_samples[tag])
                if zmin < FOOT_MIN_Z:
                    dz = FOOT_MIN_Z - zmin          # paw pressed by the slide: lifts and slides out of the body's way
                    lift_m = tr((side * 1.2 * dz, -0.4 * dz, dz))
                    gl, gf = lift_m @ gl, lift_m @ gf
            G['leg.' + tag], G['foot.' + tag] = gl, gf
        basis = {}
        for b in BONES:
            par = self.parent[b]
            gp_inv = G[par].inverted() if par else Matrix.Identity(4)
            basis[b] = self.rest_inv[b] @ gp_inv @ G[b] @ self.rest[b]
        return basis, G


def apply_pose(arm, basis):
    for b, m in basis.items():
        arm.pose.bones[b].matrix_basis = m


def hat_depth(p, bvh):
    """Depth of a head-space point below the OUTERMOST beanie surface along the ray from the ball centre
    (cuff roll, band and crown), negative = outside / below the cuff edge."""
    d = p - BODY_C
    L = d.length
    dn = d / L
    o, far = BODY_C.copy(), None
    for _ in range(8):
        hit = bvh.ray_cast(o, dn)
        if hit[0] is None:
            break
        far = (hit[0] - BODY_C).length
        o = hit[0] + dn * 1e-4
    return -1.0 if far is None else far - L


def collision_probe(rig, G, arm_data):
    """(arm in beanie, arm in body, paw in body) penetration depths for one posed frame."""
    bvh, hat_bvh = rig.info['body_bvh'], rig.info['beanie_bvh']
    gb_inv, gh_inv = G['body'].inverted(), G['head'].inverted()
    d_hat = d_arm = d_paw = 0.0
    for _side, tag in SIDES:
        ga, gh = G['arm.' + tag], G['hand.' + tag]
        for v, w, h in arm_data[tag]:
            p = (ga @ v) * (1.0 - w) + (gh @ v) * w
            if h > 0.03:
                d_hat = max(d_hat, hat_depth(gh_inv @ p, hat_bvh))
            if h > 0.08:
                d_arm = max(d_arm, inside_depth(bvh, gb_inv @ p))
        gf = G['foot.' + tag]
        for v in rig.foot_samples[tag]:
            q = gb_inv @ (gf @ v)
            d_paw = max(d_paw, inside_depth(bvh, q))
    return d_hat, d_arm, d_paw


def bake_clips(rig, clips):
    arm = rig.arm
    arm.animation_data_create()
    actions = {}
    body_rest = rig.info['body_verts']
    low_idx = [i for i, v in enumerate(body_rest) if v.z < 0.16]
    pom_top = arm.data.bones['pompom'].tail_local.copy()
    arm_data = {}
    for _side, tag in SIDES:
        R0, d = rig.info['arm_root'][tag], rig.info['arm_dir'][tag]
        arm_data[tag] = [(v, smoothstep(ARM_HAND - 0.05, ARM_HAND + 0.06, (v - R0).dot(d)), (v - R0).dot(d))
                         for v in rig.info['arm_rest'][tag][::2]]
    for name, dur, loop, fn in clips:
        n = int(round(dur * FPS))
        frames = []
        zmin_body, zmin_foot, zmax = 9.0, 9.0, -9.0
        hit = [0.0, 0.0, 0.0]
        rig.lowered = 0.0
        for f in range(n + 1):
            t = 0.0 if (loop and f == n) else f / FPS
            P = fn(t)
            basis, G = rig.solve(P)
            frames.append(basis)
            zb = min((G['body'] @ body_rest[i]).z for i in low_idx)
            zf = min(min((G['foot.' + tag] @ v).z for v in rig.foot_samples[tag]) for _s, tag in SIDES)
            zmin_body, zmin_foot = min(zmin_body, zb), min(zmin_foot, zf)
            zmax = max(zmax, (G['pompom'] @ pom_top).z)
            if f % 2 == 0:
                hit = [max(a, b) for a, b in zip(hit, collision_probe(rig, G, arm_data))]
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        slot = act.slots.new(id_type='OBJECT', name="Armature")
        strip = act.layers.new("Layer").strips.new(type='KEYFRAME')
        bag = strip.channelbags.new(slot)
        for b in BONES:
            locs, quats, scls = [], [], []
            prev = None
            for basis in frames:
                loc, q, sc = basis[b].decompose()
                if prev is not None and prev.dot(q) < 0.0:
                    q = -q
                prev = q
                locs.append(loc)
                quats.append(q)
                scls.append(sc)
            for path, seq, comps in (('location', locs, 3), ('rotation_quaternion', quats, 4), ('scale', scls, 3)):
                for ci in range(comps):
                    fc = bag.fcurves.new('pose.bones["%s"].%s' % (b, path), index=ci, group_name=b)
                    fc.keyframe_points.add(len(seq))
                    co = []
                    for fi, val in enumerate(seq):
                        co += [float(fi), float(val[ci])]
                    fc.keyframe_points.foreach_set("co", co)
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'LINEAR'
                    fc.update()
        act.use_frame_range = True
        act.frame_start, act.frame_end = 0.0, float(n)
        act.use_cyclic = loop
        actions[name] = (act, slot)
        print("CLIP %-10s frames 0-%d (%.2f s, %s)  body-bottom zmin %.3f  paw zmin %.3f  pom-pom ztop %.3f  "
              "penetration arm>hat %.3f arm>body %.3f paw>body %.3f  arm lowered by cuff solve %.1f deg" % (
                  name, n, dur, "loop" if loop else "one-shot", zmin_body, zmin_foot, zmax, hit[0], hit[1], hit[2],
                  rig.lowered))
    return actions


def set_action(arm, actions, name, frame=0):
    act, slot = actions[name]
    arm.animation_data.action = act
    arm.animation_data.action_slot = slot
    bpy.context.scene.frame_set(frame)


# ------------------------------------------------------------------ preview helpers (preview-only, after export)
def emission_material(name, hex_color, strength=1.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = C.hex_rgba(hex_color)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return mat


def sock(coll, identifier):
    """Socket by identifier (ShaderNodeMix has several sockets named 'A'/'B'/'Result')."""
    for s in coll:
        if s.identifier == identifier:
            return s
    raise KeyError(identifier)


def preview_fur_material(mat, root_hex, tip_hex, paw_root_hex, paw_tip_hex, density, radius, sheen_hex):
    """Approximates Unity's shell shader: strands = 3D Voronoi cells on the rest position, tapering per shell;
    Col.a selects the coat (1 = pink, 0 = cream paw fur) and Col.rgb tints it."""
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])

    def math_node(op, a=None, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    def mix_rgb(fac, a, b, blend='MIX'):
        m = nt.nodes.new("ShaderNodeMix")
        m.data_type = 'RGBA'
        m.blend_type = blend
        for sid, val in (("A_Color", a), ("B_Color", b)):
            if isinstance(val, tuple):
                sock(m.inputs, sid).default_value = val
            else:
                nt.links.new(val, sock(m.inputs, sid))
        if isinstance(fac, (int, float)):
            sock(m.inputs, "Factor_Float").default_value = fac
        else:
            nt.links.new(fac, sock(m.inputs, "Factor_Float"))
        return sock(m.outputs, "Result_Color")

    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "ShellUV"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uvn.outputs["UV"], sep.inputs[0])
    u, v = sep.outputs[0], sep.outputs[1]
    rest = nt.nodes.new("ShaderNodeAttribute")
    rest.attribute_name = "bwk_rest"
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.voronoi_dimensions = '3D'
    vor.feature = 'F1'
    vor.inputs["Scale"].default_value = density
    nt.links.new(rest.outputs["Vector"], vor.inputs["Vector"])
    thr = math_node('MULTIPLY', math_node('POWER', math_node('SUBTRACT', 1.0, u), 0.8), radius)
    strand = math_node('MULTIPLY', math_node('LESS_THAN', vor.outputs["Distance"], thr), math_node('GREATER_THAN', v, 0.02))
    alpha = math_node('MAXIMUM', math_node('LESS_THAN', u, 0.01), strand)
    nt.links.new(alpha, bsdf.inputs["Alpha"])
    grad = math_node('POWER', u, 0.7)
    pink = mix_rgb(grad, C.hex_rgba(root_hex), C.hex_rgba(tip_hex))
    paw = mix_rgb(grad, C.hex_rgba(paw_root_hex), C.hex_rgba(paw_tip_hex))
    col = nt.nodes.new("ShaderNodeAttribute")
    col.attribute_name = "Col"
    coat = mix_rgb(col.outputs["Alpha"], paw, pink)
    tinted = mix_rgb(1.0, coat, col.outputs["Color"], 'MULTIPLY')
    nt.links.new(tinted, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.6
        bsdf.inputs["Sheen Tint"].default_value = C.hex_rgba(sheen_hex)
    try:
        mat.surface_render_method = 'DITHERED'
    except Exception:
        pass
    try:
        mat.use_transparent_shadow = True
    except Exception:
        pass


def setup_preview_fur(obj):
    me = obj.data
    a = me.attributes.new("bwk_rest", 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set("vector", [c for v in me.vertices for c in v.co])
    ng = bpy.data.node_groups.new("BWK_PreviewFurPush", 'GeometryNodeTree')
    ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = ng.nodes, ng.links
    gin, gout = nodes.new("NodeGroupInput"), nodes.new("NodeGroupOutput")
    attr = nodes.new("GeometryNodeInputNamedAttribute")
    attr.data_type = 'FLOAT_VECTOR'
    attr.inputs["Name"].default_value = "ShellUV"
    sep = nodes.new("ShaderNodeSeparateXYZ")
    m1 = nodes.new("ShaderNodeMath")
    m1.operation = 'MULTIPLY'
    m2 = nodes.new("ShaderNodeMath")
    m2.operation = 'MULTIPLY'
    m2.inputs[1].default_value = PREVIEW_FUR_LEN
    nrm = nodes.new("GeometryNodeInputNormal")
    sc = nodes.new("ShaderNodeVectorMath")
    sc.operation = 'SCALE'
    sp = nodes.new("GeometryNodeSetPosition")
    attr_out = next(s for s in attr.outputs if s.type == 'VECTOR' and s.enabled)
    links.new(gin.outputs[0], sp.inputs["Geometry"])
    links.new(attr_out, sep.inputs[0])
    links.new(sep.outputs[0], m1.inputs[0])
    links.new(sep.outputs[1], m1.inputs[1])
    links.new(m1.outputs[0], m2.inputs[0])
    links.new(nrm.outputs["Normal"], sc.inputs[0])
    links.new(m2.outputs[0], sc.inputs["Scale"])
    links.new(sc.outputs["Vector"], sp.inputs["Offset"])
    links.new(sp.outputs["Geometry"], gout.inputs[0])
    mod = obj.modifiers.new("PreviewFurPush", 'NODES')
    mod.node_group = ng
    preview_fur_material(bpy.data.materials["M_Fur"], "#D9607F", "#FFB3C4", "#E9DCE4", "#FFFFFF", 420.0, 0.47,
                         "#FFC6DA")
    preview_fur_material(bpy.data.materials["M_PomPom"], "#5A2AA6", "#B88BF0", "#5A2AA6", "#B88BF0", 380.0, 0.5,
                         "#D9B8FF")


def add_floor():
    me = bpy.data.meshes.new("PreviewFloor")
    me.from_pydata([(-6.0, -6.0, 0.0), (6.0, -6.0, 0.0), (6.0, 6.0, 0.0), (-6.0, 6.0, 0.0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("PreviewFloor", me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(C.material("PreviewFloor", "#2F5FD0", roughness=0.35))
    return ob


def add_label(cam_obj, text, lens, shift, res):
    cu = bpy.data.curves.new("Label", 'FONT')
    cu.body = text
    cu.align_x, cu.align_y = 'LEFT', 'BOTTOM'
    ob = bpy.data.objects.new("Label", cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = cam_obj
    w = 36.0 / lens
    h = w * res[1] / res[0]
    cu.size = h * 0.085
    ob.location = (shift[0] * w - w / 2 + h * 0.05, shift[1] * w - h / 2 + h * 0.045, -1.0)
    cu.materials.append(emission_material("PreviewLabel", "#FFFFFF", 1.0))
    try:
        ob.visible_shadow = False
    except Exception:
        pass
    return ob


def frame_camera(cam_loc, look_at, centre, height, res):
    """Lens + shift that crop around `centre` while keeping the camera's exact viewing direction."""
    cam = Vector(cam_loc)
    q = (Vector(look_at) - cam).to_track_quat('-Z', 'Y')
    pc = q.to_matrix().transposed() @ (Vector(centre) - cam)
    depth = -pc.z
    aspect = res[0] / res[1]
    lens = depth * (36.0 / aspect) / height
    return lens, (pc.x / depth * lens / 36.0, pc.y / depth * lens / 36.0)


def render(path, cam_loc, look_at, lens, res, shift=(0.0, 0.0), label=None, fmt='PNG',
           subject=(0.0, -0.05, 0.5), samples=48, vfov=None):
    scene = bpy.context.scene
    engine = C.setup_preview_scene()
    try:
        scene.eevee.taa_render_samples = samples
    except Exception:
        pass
    t, cam = Vector(subject), Vector(cam_loc)
    fwd = t - cam
    fwd.z = 0.0
    fwd.normalize()
    right = fwd.cross(Vector((0.0, 0.0, 1.0))).normalized()
    up = Vector((0.0, 0.0, 1.0))
    temp = [C._light("Key", 'AREA', 600.0, "#FFE7C2", t - fwd * 3.0 + right * 2.5 + up * 3.0, t, 2.5),
            C._light("Fill", 'AREA', 250.0, "#BFD8FF", t - fwd * 2.0 - right * 3.0 + up * 1.5, t, 3.0),
            C._light("Rim", 'AREA', 500.0, "#FF8AD8", t + fwd * 3.5 + up * 2.5, t, 2.0)]
    cd = bpy.data.cameras.new("PreviewCam")
    if vfov is not None:
        cd.sensor_fit = 'VERTICAL'
        cd.sensor_height = 24.0
        cd.angle = math.radians(vfov)
        lens = cd.lens
    else:
        cd.lens = lens
        cd.sensor_fit = 'AUTO'
        cd.sensor_width = 36.0
    cd.shift_x, cd.shift_y = shift
    co = bpy.data.objects.new("PreviewCam", cd)
    scene.collection.objects.link(co)
    co.location = cam
    co.rotation_euler = (Vector(look_at) - cam).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = co
    temp.append(co)
    if label:
        temp.append(add_label(co, label, lens if vfov is None else 36.0 / (2.0 * math.tan(math.radians(vfov) / 2.0)
                                                                          * res[0] / res[1]), shift, res))
    bpy.context.view_layer.update()
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = fmt
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if fmt == 'PNG':
        print("PREVIEW", engine, path)
    for o in temp:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
        elif isinstance(data, bpy.types.Curve):
            bpy.data.curves.remove(data)
    return path


# ------------------------------------------------------------------ image I/O with Python built-ins (zlib/struct)
def read_tga(path):
    data = open(path, 'rb').read()
    idlen, cmap, kind = data[0], data[1], data[2]
    if kind != 2 or cmap != 0:
        raise RuntimeError("expected uncompressed true-colour TGA: %s" % path)
    w, h = struct.unpack('<HH', data[12:16])
    n = data[16] // 8
    top = bool(data[17] & 0x20)
    px = data[18 + idlen:18 + idlen + w * h * n]
    rows = []
    for r in range(h):
        row = px[r * w * n:(r + 1) * w * n]
        rgb = bytearray(w * 3)
        rgb[0::3], rgb[1::3], rgb[2::3] = row[2::n], row[1::n], row[0::n]
        rows.append(rgb)
    if not top:
        rows.reverse()
    return w, h, rows


def read_png(path):
    """Minimal 8-bit non-interlaced PNG reader (RGB/RGBA/grey) -> top-down RGB rows."""
    data = open(path, 'rb').read()
    pos, idat = 8, []
    w = h = ct = None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + ln]
        if tag == b'IHDR':
            w, h, depth, ct, _c, _f, inter = struct.unpack('>IIBBBBB', body)
            if depth != 8 or inter != 0:
                raise RuntimeError("unsupported PNG: %s" % path)
        elif tag == b'IDAT':
            idat.append(body)
        elif tag == b'IEND':
            break
        pos += 12 + ln
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(b''.join(idat))
    stride = w * bpp
    prev = bytearray(stride)
    rows, i = [], 0
    for _r in range(h):
        ft = raw[i]
        cur = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ft == 1:
            for x in range(bpp, stride):
                cur[x] = (cur[x] + cur[x - bpp]) & 255
        elif ft == 2:
            cur = bytearray((a + b) & 255 for a, b in zip(cur, prev))
        elif ft == 3:
            for x in range(stride):
                left = cur[x - bpp] if x >= bpp else 0
                cur[x] = (cur[x] + ((left + prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(stride):
                a = cur[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                cur[x] = (cur[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        rows.append(cur)
        prev = cur
    out = []
    for r in rows:
        if ct == 2:
            out.append(r)
        elif ct == 6:
            rgb = bytearray(w * 3)
            rgb[0::3], rgb[1::3], rgb[2::3] = r[0::4], r[1::4], r[2::4]
            out.append(rgb)
        else:
            g = r[0::bpp]
            rgb = bytearray(w * 3)
            rgb[0::3], rgb[1::3], rgb[2::3] = g, g, g
            out.append(rgb)
    return w, h, out


def downsample2(w, h, rows):
    out = []
    for r in range(0, h - 1, 2):
        a, b = rows[r], rows[r + 1]
        row = bytearray((w // 2) * 3)
        for x in range(w // 2):
            for c in range(3):
                i0 = 6 * x + c
                row[3 * x + c] = (a[i0] + a[i0 + 3] + b[i0] + b[i0 + 3] + 2) >> 2
        out.append(row)
    return w // 2, h // 2, out


def write_png(path, w, h, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)

    def chunk(tag, body):
        return struct.pack('>I', len(body)) + tag + body + struct.pack('>I', zlib.crc32(tag + body) & 0xFFFFFFFF)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    with open(path, 'wb') as fh:
        fh.write(png)
    print("PREVIEW sheet", path)


def compose(path, tiles, cols, rows_n, cw, ch, bg=(0x2A, 0x1B, 0x4A), sep=(0x5A, 0x42, 0x96)):
    W, H = cols * cw, rows_n * ch
    canvas = [bytearray(bytes(bg) * W) for _ in range(H)]
    for i, (w, h, rws) in enumerate(tiles):
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        for r in range(min(h, ch)):
            canvas[y0 + r][x0 * 3:(x0 + min(w, cw)) * 3] = rws[r][:min(w, cw) * 3]
    for c in range(1, cols):
        for r in range(H):
            canvas[r][c * cw * 3:c * cw * 3 + 3] = bytes(sep)
    for r in range(1, rows_n):
        canvas[r * ch][:] = bytes(sep) * W
    write_png(path, W, H, canvas)


# ------------------------------------------------------------------ previews
REAR_CAM = ((0.0, 2.8, 1.35), (0.0, -1.5, 0.45))
FRONT_GAME_CAM = ((0.0, -2.3, 0.98), (0.0, 1.5, 0.30))
# Unity portrait gameplay camera (RunnerCameraRig): 2.55 m behind, 1.5 m above the slide, 10 deg down, vFOV 58
GAME_BACK, GAME_HEIGHT, GAME_PITCH, GAME_VFOV = 2.55, 1.5, 10.0, 58.0
# effective hero camera in the mascot frame: approved rig 2.75 m back / 1.3 m up / pitch 10 / vFOV 58 on the 12.2 deg
# downhill at 105.5 m (slope compensation, look-ahead) with the runner pitching the mascot 7.3 deg forward net
HERO_CAM, HERO_PITCH = (0.0, 2.566, 1.039), 8.21
SIDE_CAM = ((2.75, -0.30, 0.62), (0.0, -0.10, 0.42))
FRONT_CAM = ((0.0, -2.7, 0.78), (0.0, 0.0, 0.52))


def game_view_cam():
    cam = Vector(HERO_CAM)
    look = cam + Vector((0.0, -math.cos(math.radians(HERO_PITCH)), -math.sin(math.radians(HERO_PITCH))))
    return cam, look


def render_game_view(path, label="Slide f7 - Unity portrait gameplay camera", res=(540, 960)):
    cam, look = game_view_cam()
    return render(path, cam, look, 0.0, res, label=label, vfov=GAME_VFOV, subject=(0.0, -0.05, 0.5), samples=40)


def make_previews(arm, actions):
    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(PRIVATE_OUT, exist_ok=True)
    add_floor()
    mesh = bpy.data.objects["SK_Mascot_Body"]
    setup_preview_fur(mesh)

    set_action(arm, actions, "Slide", 7)            # the Unity hero capture samples Slide at 0.25 s
    render_game_view(prev("SK_Mascot_game_9x16"))
    if QUICK:
        set_action(arm, actions, "Slide", 7)
        render(prev("SK_Mascot_seated_side"), SIDE_CAM[0], SIDE_CAM[1], 50.0, (700, 700),
               subject=(0.0, -0.1, 0.45), label="Slide - side (travel = left)", samples=24)
        tag = os.environ.get("BWK_INSPECT", "")
        if tag:                                     # named inspection set (our renders only: public folder)
            render(prev("SK_Mascot_%s_game_9x16" % tag), *game_view_cam(), 0.0, (540, 960),
                   label="Slide f7 - hero camera", vfov=GAME_VFOV, subject=(0.0, -0.05, 0.5), samples=40)
            render(prev("SK_Mascot_%s_rear" % tag), REAR_CAM[0], REAR_CAM[1], 50.0, (700, 700),
                   subject=(0.0, 0.0, 0.62), label="Slide - rear", samples=32)
            render(prev("SK_Mascot_%s_side" % tag), SIDE_CAM[0], SIDE_CAM[1], 45.0, (700, 700),
                   subject=(0.0, -0.1, 0.62), label="Slide - side (travel = left)", samples=32)
            render(prev("SK_Mascot_%s_front" % tag), FRONT_CAM[0], FRONT_CAM[1], 45.0, (700, 700),
                   subject=(0.0, -0.1, 0.62), label="Slide - front", samples=32)
        return
    set_action(arm, actions, "Slide", 0)
    p_rear = os.path.join(SCRATCH, "rear_gameplay.tga")
    render(p_rear, REAR_CAM[0], REAR_CAM[1], 25.0, (1280, 720), label="Slide - rear", fmt='TARGA_RAW')
    rear = read_tga(p_rear)
    write_png(prev("SK_Mascot_seated_back"), *rear)
    render(prev("SK_Mascot_seated_side"), SIDE_CAM[0], SIDE_CAM[1], 50.0, (900, 900),
           subject=(0.0, -0.1, 0.45), label="Slide - side (travel = left)")
    render(prev("SK_Mascot_front"), FRONT_CAM[0], FRONT_CAM[1], 50.0, (900, 900),
           subject=(0.0, -0.1, 0.5), label="Slide - front")
    if QUICK:
        return

    cw, ch = 256, 240
    lens, shift = frame_camera(REAR_CAM[0], REAR_CAM[1], (0.0, 0.0, 0.70), 1.6, (cw, ch))
    cells = [("Idle", 15), ("Slide", 8), ("LeanLeft", 6), ("LeanRight", 6), ("TurnLeft", 6), ("TurnRight", 6),
             ("Accelerate", 4), ("Balance", 9), ("Jump", 13), ("Splash", 2), ("Bump", 2), ("Swim", 6),
             ("Celebrate", 9)]
    tiles = []
    for i, (name, frame) in enumerate(cells):
        set_action(arm, actions, name, frame)
        p = os.path.join(SCRATCH, "cell_%02d.tga" % i)
        render(p, REAR_CAM[0], REAR_CAM[1], lens, (cw, ch), shift=shift, label="%s  f%d" % (name, frame),
               fmt='TARGA_RAW', samples=20)
        tiles.append(read_tga(p))
    for name, frame, cam, label in (("Slide", 0, SIDE_CAM, "Slide  side"), ("Celebrate", 9, FRONT_CAM, "Celebrate  front")):
        set_action(arm, actions, name, frame)
        lens2, shift2 = frame_camera(cam[0], cam[1], (0.0, -0.12, 0.62), 1.5, (cw, ch))
        p = os.path.join(SCRATCH, "cell_%s.tga" % name)
        render(p, cam[0], cam[1], lens2, (cw, ch), shift=shift2, label=label, fmt='TARGA_RAW', samples=20)
        tiles.append(read_tga(p))
    compose(prev("SK_Mascot_poses"), tiles, 5, 3, cw, ch)

    # approved video frames vs. this rig (PRIVATE: written to Captures/, never to tracked folders)
    try:
        set_action(arm, actions, "Slide", 0)
        p_front = os.path.join(SCRATCH, "front_gameplay.tga")
        render(p_front, FRONT_GAME_CAM[0], FRONT_GAME_CAM[1], 25.0, (1280, 720), label="Rig preview - front (Slide)",
               fmt='TARGA_RAW', subject=(0.0, -0.1, 0.5))
        tiles = [downsample2(*read_png(os.path.join(REF_DIR, "f_003.00s.png"))), downsample2(*rear),
                 downsample2(*read_png(os.path.join(REF_DIR, "f_005.00s.png"))), downsample2(*read_tga(p_front))]
        compose(os.path.join(PRIVATE_OUT, PREVIEW_PREFIX + "_vs_reference.png"), tiles, 2, 2, 640, 360)
    except Exception as exc:  # comparison is a bonus; never fail the build on it
        print("WARNING comparison sheet skipped:", exc)


# ------------------------------------------------------------------ verification
def verify_fbx(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for a in arms:
        print("VERIFY armature", a.name, "bones", len(a.data.bones), [b.name for b in a.data.bones])
    for m in meshes:
        me = m.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        infl = max((sum(1 for g in v.groups if g.weight > 0.0) for v in me.vertices), default=0)
        print("VERIFY mesh", m.name, "tris", tris, "uv", [u.name for u in me.uv_layers], "materials",
              [mt.name for mt in me.materials], "vgroups", len(m.vertex_groups), "max influences", infl,
              "colors", [c.name for c in me.color_attributes])
    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        fr = act.frame_range
        print("VERIFY take %-22s frames %.0f-%.0f" % (act.name, fr[0], fr[1]))
    print("VERIFY takes", len(bpy.data.actions))


# ------------------------------------------------------------------ main
def main():
    bpy.ops.wm.open_mainfile(filepath=MODEL_BLEND)
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = FPS, 1.0
    names = ['Body', 'Eye.L', 'Eye.R', 'Catchlight.L1', 'Catchlight.L2', 'Catchlight.R1', 'Catchlight.R2', 'Mouth',
             'Tongue', 'Arm.L', 'Arm.R', 'Leg.L', 'Leg.R', 'Tail', 'Beanie', 'PomPom', 'StarBadge']
    objs = {n: bpy.data.objects[n] for n in names}
    for n, o in objs.items():
        if o.modifiers:
            print("NOTE modifiers on", o.name, [m.type for m in o.modifiers])
        assert o.matrix_world == Matrix.Identity(4), ("model objects must have identity transforms", o.name)
        assert len(o.data.vertices) == CONTRACT['counts'][n], ("model / json mismatch", n)
    base_tris = sum(C.tri_count(o) for o in objs.values())

    info = analyze(objs)
    seat = seat_legs(info)
    coll = bpy.data.collections.new("SK_Mascot")
    scene.collection.children.link(coll)
    arm = build_armature(info, seat, coll)
    assign_weights(objs, info, seat)
    tag_fur(objs, info)

    body = C.join([objs[n] for n in names], "SK_Mascot_Body")
    for c in list(body.users_collection):
        c.objects.unlink(body)
    coll.objects.link(body)
    old = bpy.data.collections.get("SK_Mascot_model")
    if old is not None and not old.objects:
        bpy.data.collections.remove(old)
    stats = build_shells(body)
    body.parent = arm
    mod = body.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm
    mod.use_vertex_groups = True

    total = C.tri_count(body)
    shell_tris = N_SHELLS * (stats['fur'] + stats['pompom'])
    print("TRIS SK_Mascot %d" % total)
    print("TRIS breakdown base %d + shells %d (%d x (fur %d + pompom %d))  budget %d  %s" % (
        base_tris, shell_tris, N_SHELLS, stats['fur'], stats['pompom'], TRI_BUDGET,
        "OK" if total <= TRI_BUDGET else "OVER BUDGET"))
    me = body.data
    print("MESH uv layers", [u.name for u in me.uv_layers], "materials", [m.name for m in me.materials],
          "vgroups", [g.name for g in body.vertex_groups])
    infl = max(sum(1 for g in v.groups if g.weight > 1e-4) for v in me.vertices)
    unw = sum(1 for v in me.vertices if sum(g.weight for g in v.groups) < 0.999)
    print("WEIGHTS max influences %d, verts with weight sum < 1: %d" % (infl, unw))

    rig = Rig(arm, info, seat)
    clips = clip_list()
    actions = bake_clips(rig, clips)

    # default pose of the FBX nodes = seated Slide frame 0 (bind pose is always the modelled rest pose)
    arm.animation_data.action = None
    basis, _g = rig.solve(clips[1][3](0.0))
    apply_pose(arm, basis)
    bpy.context.view_layer.update()
    assert not any(m.type == 'NODES' for m in body.modifiers)
    arm.scale = (MASCOT_SCALE, MASCOT_SCALE, MASCOT_SCALE)
    # BWK_RIG_TEST_YAW (deg, default 0): TEST-ONLY yaw of the exported armature object, for Animator-less candidate
    # captures (their FBX default pose faces the camera); never set it for a deliverable export.
    arm.rotation_euler.z = math.radians(float(os.environ.get("BWK_RIG_TEST_YAW") or 0.0))
    bpy.context.view_layer.update()
    path = C.export_fbx([arm], FBX_OUT, anim=True)

    set_action(arm, actions, "Slide", 0)
    scene.frame_start, scene.frame_end = 0, 30
    bpy.ops.wm.save_as_mainfile(filepath=WORK_BLEND, compress=True)
    print("SAVED", WORK_BLEND)

    make_previews(arm, actions)
    if not QUICK:
        verify_fbx(path)
    print("MASCOT_RIG_DONE")


if __name__ == "__main__":
    main()
