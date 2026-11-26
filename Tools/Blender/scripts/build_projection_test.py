"""Projection test (owner decision 2026-11-26 14:15): reference colour projected from a SOLVED video camera onto the
EXISTING SM_ChamberWindow_v2 geometry and baked into a new, non-overlapping UV atlas (texel-space reprojection in numpy).

Steps (one headless Blender run, no Cycles):
  1. import Art/Models/Machinery/SM_ChamberWindow_v2.fbx (as Unity sees it), mirror X like the level's travel-right
     instance (ChamberV2_216_R, localScale -1,1,1) for the projection maths only;
  2. new UV atlas (Smart UV Project) -> becomes UV0 for Unity, the original UVs move to UV1;
  3. solve the 8.25 s projector camera (vFOV 52, 3840x2160) from landmarks traced on the frame: the bright chamber
     interior boundary (glass / inner lip ellipse, r 1.73 m) + the hinge block; Nelder-Mead over 6 DOF from 36 starts;
     verification overlay -> Captures/agents/projection/solve_overlay_0825.png;
  4. rasterise every UV triangle (texel world position + normal), z-buffer the mesh from the projector (glass excluded),
     project every texel, depth test, facing weight, hand masks (pipe + collar in front of the hinge, pom-pom), sample
     the 4K frame bilinearly; de-light gold (contrast toward the median), fill unseen texels with the per-material median;
  5. write T_Proj_Chamber_BaseColor.png (2048, sRGB) + T_Proj_Chamber_MetalSmooth.png (R metallic, A smoothness),
     export SM_ChamberWindow_v2_proj.fbx and SM_ProjCams.fbx (camera markers PC/PF/PU, variants A = level mirror,
     B = unmirrored) into Assets/BubbleWashKingdom/Art/Projected/ (gitignored: reference pixels, never published).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_projection_test.py projection_bake
"""
import math
import os
import struct
import sys
import time
import zlib

import bpy
import numpy as np

ROOT = "C:/Users/josia/thanksgiving"
sys.path.insert(0, ROOT + "/Tools")
from img_crop import read_png, write_png  # noqa: E402

OUT = ROOT + "/Captures/agents/projection"
PROJ = ROOT + "/Assets/BubbleWashKingdom/Art/Projected"
SRC_FBX = ROOT + "/Assets/BubbleWashKingdom/Art/Models/Machinery/SM_ChamberWindow_v2.fbx"
FRAME = OUT + "/frames4k/f_08.25s.png"
TEX = 2048
W4, H4 = 3840, 2160
F720 = 738.1                       # vFOV 52 deg at 720 px (camera.json focal_px_720)
VFOV = 52.0
MIRROR = True                      # the level's travel-right window is mirrored (localScale x -1)

# traced on Captures/agents/projection/grid_0825.png (720p coordinates): bright interior boundary + hinge block centre
INTERIOR_PX = [(240, 57.5), (280, 75), (305, 107.5), (320, 150), (327.5, 200), (325, 250), (317.5, 295), (300, 330),
               (275, 350), (255, 352.5), (225, 340), (200, 310), (182.5, 270), (176, 235), (174, 190), (177.5, 125),
               (190, 90), (212.5, 67.5)]
HINGE_PX = (158, 190)
R_INNER, Y_INNER = 1.73, -0.02     # inner lip radius / depth (Blender model coords, front = -Y)
HINGE_3D = np.array([-2.576, -0.056, 0.0])
# occluders in the reference frame (720p polygons): pink pipe + gold clamp collar (left), the mascot's pom-pom
MASKS = [
    [(0, 0), (128, 0), (128, 78), (146, 78), (146, 228), (128, 228), (128, 720), (0, 720)],
    [(390 + 66 * math.cos(a), 268 + 66 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40, endpoint=False)],
    [(362, 0), (1280, 0), (1280, 720), (362, 720)],
]


def log(*a):
    print("[proj]", *a, flush=True)


def write_rgba(path, img):
    img = np.ascontiguousarray(img.astype(np.uint8))
    h, w, c = img.shape
    raw = np.hstack([np.zeros((h, 1), dtype=np.uint8), img.reshape(h, w * c)]).tobytes()

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    ct = 6 if c == 4 else 2
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


# ----------------------------------------------------------------------------------------------------- camera maths
def rodrigues(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3)
    k = w / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def look_at(c, target, up=np.array([0.0, 0.0, 1.0])):
    fw = target - c
    fw /= np.linalg.norm(fw)
    r = np.cross(fw, up)
    r /= np.linalg.norm(r)
    d = np.cross(fw, r)
    return np.stack([r, d, fw])          # rows: image x (right), image y (down), forward


def project(P, R, C, f, cx, cy):
    q = (P - C) @ R.T
    z = q[:, 2]
    return np.stack([cx + f * q[:, 0] / z, cy + f * q[:, 1] / z], 1), z


def nelder_mead(fun, x0, step, iters=1500):
    n = len(x0)
    pts = [x0] + [x0 + np.eye(n)[i] * step[i] for i in range(n)]
    vals = [fun(p) for p in pts]
    for _ in range(iters):
        o = np.argsort(vals)
        pts = [pts[i] for i in o]
        vals = [vals[i] for i in o]
        c = np.mean(pts[:-1], 0)
        xr = c + (c - pts[-1]); fr = fun(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1]); fe = fun(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = fun(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                for i in range(1, n + 1):
                    pts[i] = pts[0] + 0.5 * (pts[i] - pts[0]); vals[i] = fun(pts[i])
        if abs(vals[-1] - vals[0]) < 1e-10:
            break
    i = int(np.argmin(vals))
    return pts[i], vals[i]


def solve_camera(mirror_sign):
    ring = np.array([[mirror_sign * R_INNER * math.cos(t), Y_INNER, R_INNER * math.sin(t)]
                     for t in np.linspace(0, 2 * math.pi, 240, endpoint=False)])
    hinge = HINGE_3D * np.array([mirror_sign, 1, 1])
    obs = np.array(INTERIOR_PX, float)
    hpx = np.array(HINGE_PX, float)

    best = None
    hs = 1.0 if hinge[0] > 0 else -1.0            # camera on the hinge side
    for D in (8.0, 9.5, 11.0):
        for al in (50, 60, 70):
            for rot in (-28, 28):
                a = math.radians(al)
                C0 = np.array([hs * D * math.sin(a), -D * math.cos(a), 0.7])
                dw = -C0 / np.linalg.norm(C0)
                cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
                fw0 = np.array([cr * dw[0] - sr * dw[1], sr * dw[0] + cr * dw[1], dw[2]])
                R0 = look_at(C0, C0 + fw0)

                def cost(x):
                    R = rodrigues(x[3:]) @ R0
                    C = C0 + x[:3]
                    uv, z = project(ring, R, C, F720, 640, 360)
                    if z.min() < 0.5:
                        return 1e9
                    dd = np.sqrt(((obs[:, None, :] - uv[None, :, :]) ** 2).sum(-1)).min(1)
                    hu, hz = project(hinge[None], R, C, F720, 640, 360)
                    if hz[0] < 0.5:
                        return 1e9
                    pen = 1e3 * max(0.0, C[1] + 1.0) ** 2 + 1e3 * max(0.0, -hs * C[0]) ** 2
                    return float((dd ** 2).mean() + 0.25 * ((hu[0] - hpx) ** 2).sum() + pen)
                x, v = nelder_mead(cost, np.zeros(6), np.array([0.4, 0.4, 0.4, 0.08, 0.08, 0.08]), 1200)
                x, v = nelder_mead(cost, x, np.array([0.1, 0.1, 0.1, 0.02, 0.02, 0.02]), 1200)
                if best is None or v < best[0]:
                    best = (v, rodrigues(x[3:]) @ R0, C0 + x[:3])
    v, R, C = best
    uv, _ = project(ring, R, C, F720, 640, 360)
    dd = np.sqrt(((np.array(INTERIOR_PX)[:, None, :] - uv[None]) ** 2).sum(-1)).min(1)
    hu, _ = project(hinge[None], R, C, F720, 640, 360)
    log("solve mirror %+d: rms ring %.2f px (max %.2f), hinge err %.1f px, cam %s, fwd %s" % (
        mirror_sign, math.sqrt((dd ** 2).mean()), dd.max(), np.linalg.norm(hu[0] - np.array(HINGE_PX)),
        np.round(C, 3), np.round(R[2], 3)))
    return R, C, float(math.sqrt((dd ** 2).mean())), float(np.linalg.norm(hu[0] - np.array(HINGE_PX)))


# ----------------------------------------------------------------------------------------------------- rasterisers
def raster_uv(uvs, pos, nrm, mat, size):
    """Per-texel world position / normal / material for UV triangles (uvs: T x 3 x 2, pos/nrm: T x 3 x 3)."""
    P = np.zeros((size, size, 3), np.float32)
    N = np.zeros((size, size, 3), np.float32)
    M = np.full((size, size), -1, np.int16)
    for t in range(len(uvs)):
        a, b, c = uvs[t] * size - 0.5
        x0, x1 = int(max(0, math.floor(min(a[0], b[0], c[0])))), int(min(size - 1, math.ceil(max(a[0], b[0], c[0]))))
        y0, y1 = int(max(0, math.floor(min(a[1], b[1], c[1])))), int(min(size - 1, math.ceil(max(a[1], b[1], c[1]))))
        if x1 < x0 or y1 < y0:
            continue
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-14:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        l2 = 1 - l0 - l1
        ins = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
        if not ins.any():
            continue
        yy, xx = ys[ins], xs[ins]
        w = np.stack([l0[ins], l1[ins], l2[ins]], 1)
        P[yy, xx] = w @ pos[t]
        N[yy, xx] = w @ nrm[t]
        M[yy, xx] = mat[t]
    return P, N, M


def zbuffer(tri_px, tri_z, w, h):
    Z = np.full((h, w), np.inf, np.float32)
    for t in range(len(tri_px)):
        a, b, c = tri_px[t]
        if min(tri_z[t]) < 0.2:
            continue
        x0, x1 = int(max(0, math.floor(min(a[0], b[0], c[0])))), int(min(w - 1, math.ceil(max(a[0], b[0], c[0]))))
        y0, y1 = int(max(0, math.floor(min(a[1], b[1], c[1])))), int(min(h - 1, math.ceil(max(a[1], b[1], c[1]))))
        if x1 < x0 or y1 < y0:
            continue
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        l2 = 1 - l0 - l1
        ins = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not ins.any():
            continue
        # perspective-correct depth: interpolate 1/z
        iz = l0 * (1 / tri_z[t][0]) + l1 * (1 / tri_z[t][1]) + l2 * (1 / tri_z[t][2])
        z = 1 / iz
        yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
        cur = Z[yy, xx]
        Z[yy, xx] = np.minimum(cur, z[ins])
    return Z


def poly_mask(h, w, polys, scale):
    m = np.zeros((h, w), bool)
    yc = np.arange(h) + 0.5
    for pts in polys:
        p = np.array(pts, float) * scale
        x0, y0 = p[:, 0], p[:, 1]
        x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
        for y in range(h):
            hit = ((y0 <= yc[y]) & (y1 > yc[y])) | ((y1 <= yc[y]) & (y0 > yc[y]))
            if not hit.any():
                continue
            xi = np.sort(x0[hit] + (yc[y] - y0[hit]) * (x1[hit] - x0[hit]) / (y1[hit] - y0[hit]))
            for a, b in zip(xi[0::2], xi[1::2]):
                m[y, max(0, int(math.ceil(a - 0.5))):min(w, int(math.floor(b - 0.5)) + 1)] = True
    return m


def bilinear(img, x, y):
    h, w = img.shape[:2]
    x = np.clip(x - 0.5, 0, w - 1.001); y = np.clip(y - 0.5, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def dilate_fill(col, valid, iters):
    col = col.copy(); valid = valid.copy()
    for _ in range(iters):
        acc = np.zeros_like(col); cnt = np.zeros(valid.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            v = np.roll(valid, (dy, dx), (0, 1)); c = np.roll(col, (dy, dx), (0, 1))
            acc += c * v[..., None]; cnt += v
        new = (~valid) & (cnt > 0)
        if not new.any():
            break
        col[new] = acc[new] / cnt[new][:, None]
        valid = valid | new
    return col, valid


# ----------------------------------------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    os.makedirs(PROJ, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=SRC_FBX, axis_forward='-Z', axis_up='Y')
    obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    log("imported %s: %d verts, bounds %s .. %s, materials %s" % (obj.name, len(co), np.round(co.min(0), 3),
                                                                   np.round(co.max(0), 3), [m.name for m in me.materials]))

    # 2. new UV atlas -> layer 0 (Unity UV0); original UVs -> layer 1
    orig = me.uv_layers[0]
    n_loops = len(me.loops)
    uv_orig = np.empty(n_loops * 2, np.float32); orig.data.foreach_get("uv", uv_orig)
    new = me.uv_layers.new(name="ProjUV")
    me.uv_layers.active = new
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0, correct_aspect=True,
                             scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    me = obj.data
    new = me.uv_layers["ProjUV"]                   # Python refs to mesh layers die with the edit-mode toggle
    uv_new = np.empty(n_loops * 2, np.float32); new.data.foreach_get("uv", uv_new)
    log("smart UV done (%.1f s)" % (time.time() - t0))

    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tl = np.empty(nt * 3, np.int32); me.loop_triangles.foreach_get("loops", tl); tl = tl.reshape(-1, 3)
    tv = np.empty(nt * 3, np.int32); me.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
    tm = np.empty(nt, np.int32); me.loop_triangles.foreach_get("material_index", tm)
    cn = np.empty(n_loops * 3, np.float32); me.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3)
    mats = [m.name.split(".")[0] for m in me.materials]
    sgn = np.array([-1.0 if MIRROR else 1.0, 1.0, 1.0], np.float32)
    pos_t = co[tv] * sgn
    nrm_t = cn[tl] * sgn
    uvs_t = uv_new.reshape(-1, 2)[tl].copy()
    uvs_t[..., 1] = 1.0 - uvs_t[..., 1]            # image rows top-down
    log("%d triangles; rasterising %d^2 atlas" % (nt, TEX))
    P, N, Mi = raster_uv(uvs_t, pos_t, nrm_t, tm, TEX)
    Nn = N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-6)
    cover = Mi >= 0
    log("atlas coverage %.1f %% (%.1f s)" % (100 * cover.mean(), time.time() - t0))

    # 3. solve the projector camera (both mirror states: A = level placement, B = unmirrored model)
    RA, CA, rmsA, hA = solve_camera(-1.0 if MIRROR else 1.0)
    RB, CB, rmsB, hB = solve_camera(1.0 if MIRROR else -1.0)
    R, C = RA, CA
    # verification overlay: model edges of the inner lip, outer band (r 2.32) and hinge over the 720p frame
    img4 = read_png(FRAME)[..., :3].astype(np.float32)
    small = img4[1::3, 1::3][:720, :1280].copy()
    for rr, yy, colr in ((R_INNER, Y_INNER, (0, 255, 255)), (2.324, -0.14, (255, 0, 255)), (2.04, -0.28, (255, 255, 0))):
        ring = np.array([[-rr * math.cos(t) if MIRROR else rr * math.cos(t), yy, rr * math.sin(t)]
                         for t in np.linspace(0, 2 * math.pi, 720, endpoint=False)])
        uv, _ = project(ring, R, C, F720, 640, 360)
        for u, v in uv:
            if 0 <= u < 1279 and 0 <= v < 719:
                small[int(v), int(u)] = colr
    for (u, v) in INTERIOR_PX:
        small[int(v) - 2:int(v) + 3, int(u) - 2:int(u) + 3] = (255, 60, 60)
    hu, _ = project((HINGE_3D * sgn)[None], R, C, F720, 640, 360)
    small[int(hu[0][1]) - 4:int(hu[0][1]) + 5, int(hu[0][0]) - 4:int(hu[0][0]) + 5] = (60, 255, 60)
    write_png(OUT + "/solve_overlay_0825.png", small[0:420, 60:480])

    # 4. z-buffer at half 4K + projection of every texel
    f4 = F720 * 3.0
    keep = np.array([("Glass" not in mats[m]) for m in tm])
    tri_uv, tri_z = project(pos_t.reshape(-1, 3), R, C, F720, 640, 360)
    Z = zbuffer(tri_uv.reshape(-1, 3, 2)[keep], tri_z.reshape(-1, 3)[keep], 1280, 720)
    log("z-buffer done (%.1f s)" % (time.time() - t0))
    idx = np.nonzero(cover)
    Pv, Nv = P[idx], Nn[idx]
    uvp, zp = project(Pv, R, C, f4, W4 / 2, H4 / 2)
    inside = (uvp[:, 0] > 2) & (uvp[:, 0] < W4 - 3) & (uvp[:, 1] > 2) & (uvp[:, 1] < H4 - 3) & (zp > 0.2)
    vis = inside.copy()
    zi = np.clip((uvp[:, 1] / 3).astype(int), 0, 719), np.clip((uvp[:, 0] / 3).astype(int), 0, 1279)
    zref = Z[zi]
    vis &= zp <= zref + 0.03 + 0.006 * zp
    view = C[None] - Pv
    view /= np.linalg.norm(view, axis=1, keepdims=True)
    facing = (Nv * view).sum(1)
    vis &= facing > 0.08
    mask720 = poly_mask(720, 1280, MASKS, 1.0)
    mi = np.clip((uvp[:, 1] / 3).astype(int), 0, 719), np.clip((uvp[:, 0] / 3).astype(int), 0, 1279)
    vis &= ~mask720[mi]
    col = np.zeros((len(Pv), 3), np.float32)
    col[vis] = bilinear(img4, uvp[vis, 0], uvp[vis, 1])
    # texel footprint in reference pixels (sharpness budget): reference pixels per texel along the atlas
    log("visible texels %d of %d covered (%.1f %%); masked %d; back-facing %d" % (
        vis.sum(), len(Pv), 100 * vis.mean(), (inside & mask720[mi]).sum(), (inside & (facing <= 0.08)).sum()))

    # per-material statistics + de-lighting
    matv = Mi[idx]
    base = np.zeros((len(Pv), 3), np.float32)
    metal = np.zeros(len(Pv), np.float32)
    smooth = np.zeros(len(Pv), np.float32)
    fallback = {"M_Gold": (200, 150, 70), "M_GoldDark": (110, 76, 34), "M_Glass": (220, 230, 255),
                "M_ChamberDrum": (150, 130, 200), "M_ChamberSwirl": (240, 200, 220), "M_DrumRim": (170, 150, 210),
                "M_Foam": (244, 242, 255)}
    stats = []
    for m in range(len(mats)):
        sel = matv == m
        sv = sel & vis
        name = mats[m]
        gold = name in ("M_Gold", "M_GoldDark")
        if sv.sum() > 50:
            c = col[sv]
            L = c @ np.array([0.2126, 0.7152, 0.0722], np.float32) + 1.0
            Lm = np.median(L)
            k = 0.65 if gold else 0.2           # gold: mostly lighting -> pull 65 % toward the median luminance
            c2 = c * ((Lm / L) ** k)[:, None]
            base[sv] = np.clip(c2, 0, 255)
            fill = np.median(c2, 0)
        else:
            fill = np.array(fallback.get(name, (180, 160, 200)), np.float32)
        base[sel & ~vis] = fill
        metal[sel] = 1.0 if gold else 0.0
        smooth[sel] = 0.78 if gold else (0.15 if name == "M_Foam" else 0.35)
        stats.append("%s: %d texels, seen %.1f %%" % (name, sel.sum(), 100 * sv.sum() / max(1, sel.sum())))
    log("per material: " + "; ".join(stats))

    # write atlases (unseen texels already filled per material; dilate into the gutters)
    A = np.zeros((TEX, TEX, 3), np.float32); A[idx] = base
    MS = np.zeros((TEX, TEX, 3), np.float32); MS[idx] = np.stack([metal, smooth, np.zeros_like(metal)], 1)
    A, _ = dilate_fill(A, cover, 6)
    MS, _ = dilate_fill(MS, cover, 6)
    seen = np.zeros((TEX, TEX), bool); seen[idx] = vis
    write_png(PROJ + "/T_Proj_Chamber_BaseColor.png", np.clip(A, 0, 255))
    rgba = np.zeros((TEX, TEX, 4), np.float32)
    rgba[..., 0] = MS[..., 0] * 255; rgba[..., 1] = MS[..., 0] * 255; rgba[..., 2] = MS[..., 0] * 255
    rgba[..., 3] = MS[..., 1] * 255
    write_rgba(PROJ + "/T_Proj_Chamber_MetalSmooth.png", np.clip(rgba, 0, 255))
    viz = A.copy(); viz[cover & ~seen] = viz[cover & ~seen] * 0.35 + np.array([255, 0, 0]) * 0.65
    write_png(OUT + "/atlas_seen_vs_filled.png", np.clip(viz[::2, ::2], 0, 255))

    # sharpness budget: reference pixels per texel (finite difference of the projection along the atlas)
    du = np.zeros(len(Pv), np.float32)
    Pdx = np.roll(P, -1, 1)[idx]
    okdx = np.roll(cover, -1, 1)[idx]
    uv2, _ = project(Pdx, R, C, f4, W4 / 2, H4 / 2)
    du = np.linalg.norm(uv2 - uvp, axis=1)
    s = vis & okdx
    if s.any():
        log("reference px per atlas texel (4K frame): median %.2f, p10 %.2f, p90 %.2f (<1 = the texture is softer "
            "than the atlas)" % (np.median(du[s]), np.percentile(du[s], 10), np.percentile(du[s], 90)))
        for m in range(len(mats)):
            sm = s & (matv == m)
            if sm.sum() > 50:
                tex_m = np.median(np.linalg.norm(np.roll(P, -1, 1)[idx][sm] - Pv[sm], axis=1))
                log("  %s: %.2f ref px/texel, texel %.1f mm" % (mats[m], np.median(du[sm]), 1000 * tex_m))

    # 5. export: projected UVs become layer 0, the original UVs layer 1
    uv0 = me.uv_layers[0]
    uv0.data.foreach_set("uv", uv_new)
    new.data.foreach_set("uv", uv_orig)
    uv0.name, new.name = "UVMap_tmp", "UVMap_orig"
    uv0.name = "ProjUV"
    obj.name = "SM_ChamberWindow_v2_proj"
    exp = dict(use_selection=True, object_types={'MESH', 'EMPTY'}, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
               axis_forward='-Z', axis_up='Y', bake_space_transform=False, use_mesh_modifiers=True,
               mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False, bake_anim=False, path_mode='AUTO',
               embed_textures=False)
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.ops.export_scene.fbx(filepath=PROJ + "/SM_ChamberWindow_v2_proj.fbx", **exp)
    log("EXPORTED SM_ChamberWindow_v2_proj.fbx")

    # camera markers (Unity reads mesh-local cube centres through the chamber's own matrix -> exact same conversion)
    markers = []
    for tag, (Rm, Cm), msign in (("A", (RA, CA), -1.0 if MIRROR else 1.0), ("B", (RB, CB), 1.0 if MIRROR else -1.0)):
        un = np.array([msign, 1.0, 1.0])          # back to the unmirrored model frame (the level applies the mirror)
        pts = {"PC": Cm, "PF": Cm + Rm[2] * 1.0, "PU": Cm - Rm[1] * 0.5}
        for k, p in pts.items():
            bpy.ops.mesh.primitive_cube_add(size=0.02, location=tuple(p * un))
            o = bpy.context.active_object
            o.name = "%s_%s" % (k, tag)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            markers.append(o)
    for o in bpy.data.objects:
        o.select_set(o in markers)
    bpy.ops.export_scene.fbx(filepath=PROJ + "/SM_ProjCams.fbx", **exp)
    log("EXPORTED SM_ProjCams.fbx (A rms %.2f px hinge %.1f px | B rms %.2f px hinge %.1f px)" % (rmsA, hA, rmsB, hB))
    log("DONE build_projection_test (%.1f s)" % (time.time() - t0))


main()
