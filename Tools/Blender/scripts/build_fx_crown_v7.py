"""Bubble Wash Kingdom - milk splash crowns v7 = the S2 hero frame's OWN two crowns rebuilt as 3D wake walls
(waterfx specialist, S2 pass 10i, 2026-11-27).

Why: V6 inflated ONE crown outline from another shot (library crop 18) and every placement search on the S2 comparison
camera topped out at silhouette IoU ~.31; the lead's 18:45 read of pass 10h: "crowns still SMALL and on the RIGHT only, the
left foot shows no crown". V7 uses the two crowns the approved S2 frame (3.00 s) actually shows:
  1. the milky splash pixels of the left / right crown are segmented (bright, low saturation, blue >= red; one hand-drawn
     region per crown; the soles and the cyan chevron excluded),
  2. every masked cell is cast back through the S2 comparison camera (R2, runner-local, CaptureTools R2 = 2.75 back / 1.0 up /
     0.3 right, pitch 6, yaw -7, vFOV 58, 16:9; runner pitch from the waterfx S2 camera log) onto a vertical WAKE WALL whose
     base runs on the water along the crown's lower envelope (from the foot back toward the camera, diverging outward:
     the spray that a seated slider throws up beside each foot); cells below the water line lie on the water,
  3. the sheet is inflated along the view ray (thickness ~ sqrt(distance to the outline), as V6), so every finger becomes a
     round tube ending in its bulb and the broad sheet gets a soft rounded body; smoothed, decimated (mobile budget).
Real 3D geometry only (no textures, no reference pixels on the mesh). The outline is reference-derived -> the FBX files stay
LOCAL in Assets/BubbleWashKingdom/Art/Projected/FX/ (gitignored); SceneBuilder.WaterFX prefers V7 > V6 only when they exist.
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_crown_v7.py fx_crown_v7      (BWK_FX_QUICK=1: previews only)
Env: BWK_REF (reference frame, 1280x720), BWK_PV (preview dir), BWK_CELL (px per cell), BWK_THICK, BWK_TRIS (per side).
Revert: delete Assets/BubbleWashKingdom/Art/Projected/FX/SM_FX_CrownV7_*.fbx (V6 takes over again).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bwk_common as C  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

ROOT = "C:/Users/josia/thanksgiving"
REF = os.environ.get("BWK_REF", ROOT + "/Reference/frames4k_720/f_03.00s.png")
OUT_DIR = ROOT + "/Assets/BubbleWashKingdom/Art/Projected/FX"
PV_DIR = os.environ.get("BWK_PV", ROOT + "/Captures/agents/waterfx/screen_S2_p10i/v7_blender")
QUICK = os.environ.get("BWK_FX_QUICK", "") == "1"
CELL = int(os.environ.get("BWK_CELL", "3"))
THICK = float(os.environ.get("BWK_THICK", "1.5"))
CAP = 10.0
MAX_TRIS = int(os.environ.get("BWK_TRIS", "6000"))
YW = -0.02   # water line (runner-local y)
W, H = 1280, 720


def U(x, y, z):
    """runner-local (x right, y up, z forward) -> Blender space (same mapping as build_fx_crown_v5 / v6)."""
    return Vector((-x, -z, y))


# ---------------------------------------------------------------- camera (runner-local, Unity conventions)
def _rx(a):
    a = math.radians(a)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def _ry(a):
    a = math.radians(a)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def _rz(a):
    a = math.radians(a)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def euler(x, y, z):
    """Unity Quaternion.Euler(x, y, z) as a matrix (z, then x, then y)."""
    return _ry(y) @ _rx(x) @ _rz(z)


class Cam:
    def __init__(self, pos, R, vfov, w, h):
        self.c = np.array(pos, float)
        self.right, self.up, self.fwd = R[:, 0], R[:, 1], R[:, 2]
        self.f = (h / 2.0) / math.tan(math.radians(vfov / 2.0))
        self.w, self.h = w, h

    def rays(self, us, vs):
        xc = (us - self.w / 2.0) / self.f
        yc = -(vs - self.h / 2.0) / self.f
        d = np.outer(xc, self.right) + np.outer(yc, self.up) + self.fwd
        return d / np.linalg.norm(d, axis=1, keepdims=True)


# waterfx S2 camera log 17:52: "S2 cam (runner-local) pos (0.328, 0.733, -2.830) euler (0.49, 351.02, 358.68)", built with
# Euler(6, -9, 0) on the flat heading; CaptureTools R2 uses Euler(6, -7, 0) -> runner frame = logged * inverse(Euler(6, -9, 0))
Q_RF = euler(0.49, 351.02, 358.68) @ euler(6, -9, 0).T
CAM = Cam((0.328, 0.733, -2.830), Q_RF @ euler(6, -7, 0), 58.0, W, H)


# ---------------------------------------------------------------- reference crown masks
def load_ref():
    import OpenImageIO as oiio
    buf = oiio.ImageBuf(REF)
    px = buf.get_pixels(oiio.UINT8)
    assert px.shape[0] == H and px.shape[1] == W, "reference must be 1280x720"
    return px[:, :, :3].astype(np.int32)


def poly_mask(pts):
    yy, xx = np.mgrid[0:H, 0:W]
    pts = np.array(pts, float)
    inside = np.zeros((H, W), bool)
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        if y1 == y0:
            continue
        inside ^= ((y0 > yy) != (y1 > yy)) & (xx < (x1 - x0) * (yy - y0) / (y1 - y0) + x0)
    return inside


def dil(a, r=1):
    o = a.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            o |= np.roll(np.roll(a, dy, 0), dx, 1)
    return o


HOLE_MAX = int(os.environ.get("BWK_HOLE", "260"))   # enclosed gaps up to this many px are milk (the approved sheets are solid)


def fill_small_holes(m, max_px):
    """Fill enclosed background pockets smaller than max_px (the first Blender preview read as a perforated curtain,
    a look the owner rejected in round 3); bigger gaps, where the water shows through the crown, stay open."""
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = max(0, ys.min() - 2), min(H, ys.max() + 3), max(0, xs.min() - 2), min(W, xs.max() + 3)
    sub = m[y0:y1, x0:x1]
    bg = ~sub
    seen = np.zeros_like(bg)
    hh, ww = bg.shape
    filled = 0
    for sy in range(hh):
        for sx in range(ww):
            if not bg[sy, sx] or seen[sy, sx]:
                continue
            stack, comp, edge = [(sy, sx)], [], False
            seen[sy, sx] = True
            while stack:
                cy, cx = stack.pop()
                comp.append((cy, cx))
                if cy == 0 or cx == 0 or cy == hh - 1 or cx == ww - 1:
                    edge = True
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < hh and 0 <= nx < ww and bg[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            if not edge and len(comp) <= max_px:
                for cy, cx in comp:
                    sub[cy, cx] = True
                filled += len(comp)
    print("CHECK filled %d px of small enclosed gaps" % filled)
    return m


def crown_masks():
    ref = load_ref()
    r, g, b = ref[..., 0], ref[..., 1], ref[..., 2]
    mx, mn = ref.max(-1) / 255.0, ref.min(-1) / 255.0
    s = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    milky = (s < 0.30) & (mx > 0.76) & (b >= r + 4) & (g >= r - 6)
    excl = np.zeros((H, W), bool)
    excl[515:600, 560:720] = True      # cyan chevron
    excl[462:540, 515:607] = True      # left sole
    excl[455:530, 686:770] = True      # right sole
    regions = {
        "L": [(400, 392), (480, 392), (520, 440), (560, 468), (566, 540), (560, 620), (470, 625), (400, 615), (398, 500)],
        "R": [(690, 470), (760, 440), (840, 395), (940, 390), (945, 470), (935, 560), (930, 640), (860, 660), (770, 600), (705, 560)],
    }
    out = {}
    for side, pts in regions.items():
        m = milky & poly_mask(pts) & ~excl
        m = ~dil(~dil(m, 3), 3)          # close pinholes and thin bluish seams inside the sheet
        m = dil(~dil(~m, 1), 1)          # drop 1-px specks
        m = fill_small_holes(m, HOLE_MAX)
        ys, xs = np.nonzero(m)
        print("CHECK mask %s: %d px, x %d-%d y %d-%d" % (side, m.sum(), xs.min(), xs.max(), ys.min(), ys.max()))
        out[side] = m
    return out


# ---------------------------------------------------------------- wake wall + back-projection
def base_polyline(m):
    """Lower envelope of the crown (92nd-percentile row per 8 px column) cast onto the water -> base line of the wall."""
    ys, xs = np.nonzero(m)
    env = []
    for b0 in range(xs.min(), xs.max() + 1, 8):
        sel = (xs >= b0) & (xs < b0 + 8)
        if sel.sum() >= 10:
            env.append((b0 + 4.0, float(np.percentile(ys[sel], 92))))
    env = np.array(env)
    d = CAM.rays(env[:, 0], env[:, 1])
    t = (YW - CAM.c[1]) / d[:, 1]
    P = (CAM.c + d * t[:, None])[:, [0, 2]]
    P = P[P[:, 1] < 0.05]               # high outer fingers do not touch the water: not part of the base
    if len(P) >= 3:
        Pm = P.copy()
        for i in range(1, len(P) - 1):
            Pm[i] = np.median(P[i - 1:i + 2], axis=0)
        P = Pm.copy()
        for i in range(1, len(P) - 1):
            P[i] = Pm[i - 1:i + 2].mean(0)
    a = P[0] + (P[0] - P[1]) / max(1e-6, np.linalg.norm(P[0] - P[1])) * 1.5
    z = P[-1] + (P[-1] - P[-2]) / max(1e-6, np.linalg.norm(P[-1] - P[-2])) * 1.5
    return np.concatenate([[a], P, [z]], 0)


def cast(us, vs, poly):
    d = CAM.rays(us, vs)
    c = CAM.c
    best = np.full(len(us), np.inf)
    for i in range(len(poly) - 1):
        p0, e = poly[i], poly[i + 1] - poly[i]
        det = d[:, 0] * (-e[1]) - d[:, 2] * (-e[0])
        rx, rz = p0[0] - c[0], p0[1] - c[2]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (rx * (-e[1]) - rz * (-e[0])) / det
            s = (d[:, 0] * rz - d[:, 2] * rx) / det
        ok = (s >= 0) & (s <= 1) & (t > 0.3) & np.isfinite(t)
        best = np.where(ok & (t < best), t, best)
    P = c + d * np.where(np.isfinite(best), best, 0.0)[:, None]
    under = ~np.isfinite(best) | (P[:, 1] < YW)
    tw = (YW - c[1]) / d[:, 1]
    P[under] = (c + d * tw[:, None])[under]
    return P, d, under


def erode(m, eight):
    p = np.pad(m, 1, constant_values=False)
    out = m & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    if eight:
        out &= p[:-2, :-2] & p[:-2, 2:] & p[2:, :-2] & p[2:, 2:]
    return out


def distance(inside):
    d = np.zeros(inside.shape, np.float32)
    cur = inside.copy()
    k = 0
    while cur.any() and k < 200:
        d += cur
        cur = erode(cur, eight=(k % 2 == 0))
        k += 1
    return d


def build_crown(name, m, milk):
    poly = base_polyline(m)
    print("CHECK %s base line on the water (x,z): %s" % (name, " ".join("(%.2f,%.2f)" % tuple(p) for p in poly[1:-1])))
    hh, ww = (H // CELL) * CELL, (W // CELL) * CELL
    g = m[:hh, :ww].reshape(hh // CELL, CELL, ww // CELL, CELL).mean(axis=(1, 3)) > 0.5
    dd = distance(g)
    rs, cs = np.nonzero(g)
    P, D, under = cast((cs + 0.5) * CELL, (rs + 0.5) * CELL, poly)
    cell_m = np.linalg.norm(P - CAM.c, axis=1) * CELL / CAM.f
    h = THICK * np.sqrt(np.clip(dd[rs, cs] - 1.0, 0.0, CAP)) * cell_m
    front = P - D * h[:, None]
    back = P + D * h[:, None]
    print("CHECK %s: %d cells, %.1f %% on the water, x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f, max half-thickness %.0f mm" % (
        name, len(rs), under.mean() * 100, P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(),
        P[:, 2].min(), P[:, 2].max(), h.max() * 1000))
    bm = bmesh.new()
    fv, bv = {}, {}
    for i, (r, c) in enumerate(zip(rs, cs)):
        fv[(r, c)] = bm.verts.new(U(*front[i]))
        bv[(r, c)] = fv[(r, c)] if dd[r, c] <= 1.0 else bm.verts.new(U(*back[i]))
    rows, cols = g.shape
    for r in range(rows - 1):
        for c in range(cols - 1):
            q = [(r, c), (r, c + 1), (r + 1, c + 1), (r + 1, c)]
            if not all(g[k] for k in q):
                continue
            for verts in ([fv[k] for k in q], [bv[k] for k in reversed(q)]):
                try:
                    bm.faces.new(verts)
                except ValueError:
                    pass
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = C.mesh_from_bmesh(name, bm)
    obj.data.materials.append(milk)
    sm = obj.modifiers.new("Soften", 'SMOOTH')
    sm.factor, sm.iterations = 0.6, 5
    C.select_only([obj])
    bpy.ops.object.modifier_apply(modifier=sm.name)
    tris = C.tri_count(obj)
    if tris > MAX_TRIS:
        dm = obj.modifiers.new("Decimate", 'DECIMATE')
        dm.ratio = MAX_TRIS / float(tris)
        dm.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dm.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    print("CHECK %s %d tris (from %d)" % (name, C.tri_count(obj), tris))
    return obj


def look_cam(name, pos_u, target_u, vfov_deg):
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(vfov_deg)
    co = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = U(*pos_u)
    co.rotation_euler = (U(*target_u) - U(*pos_u)).to_track_quat('-Z', 'Y').to_euler()
    return co


def main():
    C.reset_scene()
    C.setup_preview_scene("#3A3488", 0.55)
    milk = C.material("M_FX_Milk_v3", "#EEF8FB", roughness=0.18, coat=0.4)
    masks = crown_masks()
    objs = [build_crown("SM_FX_CrownV7_" + side, masks[side], milk) for side in ("L", "R")]
    if not QUICK:
        C.ensure_dir(OUT_DIR)
        for o in objs:
            C.export_fbx([o], OUT_DIR + "/" + o.name + ".fbx")
            print("EXPORT", OUT_DIR + "/" + o.name + ".fbx")
    # preview: stand-in mascot (pink ball + soles) on a water plane, seen from the rear, the side and above
    pink = C.material("PV_Pink", "#F08AB8", roughness=0.8)
    cream = C.material("PV_Cream", "#FFF4F6", roughness=0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.46, location=U(0, 0.52, 0.02))
    bpy.context.active_object.data.materials.append(pink)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=U(sx * 0.27, 0.10, 0.0))
        o = bpy.context.active_object
        o.scale = (1.0, 0.6, 1.0)
        o.data.materials.append(cream)
    bpy.ops.mesh.primitive_plane_add(size=14, location=U(0, YW, 0))
    bpy.context.active_object.data.materials.append(C.material("PV_Water", "#1C8ECC", roughness=0.1))
    t = U(0, 0.3, -0.4)
    C._light("Key", 'AREA', 320, "#FFF6EE", t + Vector((-1.5, -2.5, 3.0)), t, 2.5)
    C._light("Key2", 'AREA', 260, "#FFF6EE", t + Vector((1.5, 2.5, 3.0)), t, 2.5)
    C._light("Fill", 'AREA', 90, "#8FB0FF", t + Vector((2.0, 0.0, 0.3)), t, 3.0)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    C.ensure_dir(PV_DIR)
    cams = [("rearR2", look_cam("CamR2", tuple(CAM.c), tuple(CAM.c + CAM.fwd), 58.0)),
            ("rearHigh", look_cam("CamHigh", (0.0, 1.6, -3.6), (0.0, 0.2, -0.3), 50.0)),
            ("side", look_cam("CamSide", (3.0, 0.9, -0.6), (0.0, 0.25, -0.6), 45.0))]
    for tag, cam in cams:
        scene.camera = cam
        scene.render.filepath = "%s/FX_CrownV7_%s.png" % (PV_DIR, tag)
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", scene.render.filepath)
    print("DONE crown v7 (S2 wake walls)")


main()
