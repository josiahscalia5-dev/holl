"""S2 Tunnel v1 (LEAD): measure the ORIGINAL 3.00 s frame's layout in 3D through the game's R2 camera.
Detects gold bulbs, neon stars (yellow / cyan / pink) and the bright lavender band in Reference/frames4k_720/f_03.00s.png, then casts
rays from the exact R2 camera (Tools/Blender/work/s2v1/unity_export/s2_layout.json) into the tunnel (radius 4.2 around the track axis
at height 2.3) -> track distance d and angle around the axis for every element; ring / band radii -> the d where a ring of that radius
projects to that screen radius. Output: Captures/s2v1/original_layout.json (numbers only) + Captures/s2v1/original_layout_marked.png.
Usage: "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/Blender/scripts/s2v1/measure_original_layout.py
"""
import json
import math
import sys

import numpy as np

ROOT = 'C:/Users/josia/thanksgiving'
sys.path.insert(0, ROOT + '/Tools')
from img_crop import read_png, write_png  # noqa: E402

L = json.load(open(ROOT + '/Tools/Blender/work/s2v1/unity_export/s2_layout.json', encoding='utf-8'))
cam = [c for c in L['cameras'] if c['name'] == 'R2_16x9'][0]
F = {k: np.array([f[k] for f in L['frames']], float) for k in ('pos', 'fwd', 'flatUp', 'flatRight')}
D = np.array([f['d'] for f in L['frames']], float)
AX = F['pos'] + F['flatUp'] * 2.3            # tunnel axis (Unity world)
R_T = 4.2
W, H = 1280, 720
FY = (H / 2) / math.tan(math.radians(cam['vfov']) / 2)


def qrot(q, v):
    x, y, z, w = q; qv = np.array([x, y, z]); v = np.asarray(v, float)
    t = 2 * np.cross(qv, v); return v + w * t + np.cross(qv, t)


CP = np.array(cam['pos'], float)
RIGHT, UP, FWD = qrot(cam['rot'], (1, 0, 0)), qrot(cam['rot'], (0, 1, 0)), qrot(cam['rot'], (0, 0, 1))


def project(P):
    v = P - CP; z = v @ FWD
    return np.stack([W / 2 + FY * (v @ RIGHT) / z, H / 2 - FY * (v @ UP) / z], -1), z


def ray(u, v):
    d = FWD + RIGHT * (u - W / 2) / FY + UP * (H / 2 - v) / FY
    return d / np.linalg.norm(d)


def axis_info(P):
    """nearest axis sample -> (d, radial distance, angle deg around the axis; 0 = top, + = clockwise seen down the tunnel = right)."""
    k = int(np.argmin(((AX - P) ** 2).sum(1)))
    rel = P - AX[k]; rel -= (rel @ F['fwd'][k]) * F['fwd'][k]
    r = np.linalg.norm(rel)
    ang = math.degrees(math.atan2(rel @ F['flatRight'][k], rel @ F['flatUp'][k]))
    return D[k], r, ang


def hit_wall(u, v, d_min=40.0):
    dr = ray(u, v)
    for t in np.arange(1.0, 160.0, 0.02):
        P = CP + dr * t
        d, r, ang = axis_info(P)
        if d >= d_min and r >= R_T - 0.25:
            return round(float(d), 2), round(float(ang), 1), round(float(t), 2)
    return None


def ring_d_for_radius(r_px, center_px, R_el):
    """track distance where a ring of radius R_el (m, around the axis) projects to a mean screen radius r_px around center_px."""
    best = None
    for k in range(len(D)):
        if D[k] < 40.0:
            continue
        a = np.linspace(0, 2 * np.pi, 48, endpoint=False)
        P = AX[k] + np.outer(np.cos(a), F['flatUp'][k]) * R_el + np.outer(np.sin(a), F['flatRight'][k]) * R_el
        xy, z = project(P)
        if (z <= 0).any():
            continue
        rr = np.linalg.norm(xy - xy.mean(0), axis=1).mean()
        err = abs(rr - r_px)
        if best is None or err < best[0]:
            best = (err, D[k], xy.mean(0))
    return round(float(best[1]), 2), [round(float(c), 1) for c in best[2]]


img = np.asarray(read_png(ROOT + '/Reference/frames4k_720/f_03.00s.png'))[..., :3].astype(np.float32) / 255
mx = img.max(-1); mn = img.min(-1); s = (mx - mn) / np.maximum(mx, 1e-6); dlt = np.maximum(mx - mn, 1e-6)
R_, G_, B_ = img[..., 0], img[..., 1], img[..., 2]
hue = np.where(mx == R_, (G_ - B_) / dlt % 6, np.where(mx == G_, (B_ - R_) / dlt + 2, (R_ - G_) / dlt + 4)) * 60
yy, xx = np.mgrid[0:H, 0:W]
mascot = ((xx - 640) / 215.) ** 2 + ((yy - 430) / 300.) ** 2 < 1
upper = (yy < 470) & ~mascot


def components(mask, min_area):
    lab = np.zeros(mask.shape, np.int32); out = []; cur = 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0]:
            continue
        cur += 1; stack = [(y0, x0)]; lab[y0, x0] = cur; pts = []
        while stack:
            y, x = stack.pop(); pts.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = cur; stack.append((ny, nx))
        if len(pts) >= min_area:
            p = np.array(pts); out.append({'cx': float(p[:, 1].mean()), 'cy': float(p[:, 0].mean()), 'area': len(pts),
                                           'bbox': [int(p[:, 1].min()), int(p[:, 0].min()), int(p[:, 1].max()), int(p[:, 0].max())]})
    return out


res = {'camera': 'R2_16x9 (game comparison camera solved to the original, rms ~15 px)', 'vp_px': [760, 205]}
bulb = upper & (hue > 25) & (hue < 62) & (s > 0.3) & (mx > 0.9)
bulbs = [b for b in components(bulb, 6) if b['area'] < 400]
res['gold_bulbs_px'] = [[round(b['cx'], 1), round(b['cy'], 1)] for b in bulbs]
stars = {}
for name, m, amin in (('yellow', upper & (hue > 45) & (hue < 72) & (s > 0.45) & (mx > 0.8), 60),
                      ('cyan', upper & (hue > 165) & (hue < 205) & (s > 0.4) & (mx > 0.7), 60),
                      ('pink', upper & (hue > 295) & (hue < 345) & (s > 0.45) & (mx > 0.85), 60)):
    comps = components(m, amin)
    stars[name] = []
    for c in comps:
        h = hit_wall(c['cx'], c['cy'])
        stars[name].append({'px': [round(c['cx'], 1), round(c['cy'], 1)], 'bbox_px': c['bbox'], 'area_px': c['area'],
                            'wall_hit_d_angle_dist': h})
res['neon_stars'] = stars
# gold bulb rings: cluster bulbs by distance from the VP, fit radius per cluster -> d
vp = np.array(res['vp_px'], float)
if bulbs:
    rb = np.array([math.hypot(b['cx'] - vp[0], b['cy'] - vp[1]) for b in bulbs])
    order = np.sort(rb); groups = []; cur = [order[0]]
    for r in order[1:]:
        (cur.append(r) if r - cur[-1] < 18 else (groups.append(cur), cur := [r]))
    groups.append(cur)
    res['gold_rings'] = []
    for g in groups:
        if len(g) < 5:
            continue
        rpx = float(np.median(g))
        dd, cen = ring_d_for_radius(rpx, vp, 3.95)
        res['gold_rings'].append({'bulbs_seen': len(g), 'screen_radius_px': round(rpx, 1), 'track_d_if_bulb_radius_3.95m': dd, 'projected_centre_px': cen})
# lavender glow band: radial histogram of bright lavender pixels around the VP
lav = upper & (hue > 250) & (hue < 305) & (s < 0.45) & (mx > 0.85)
rr = np.hypot(xx - vp[0], yy - vp[1])[lav]
hist, edges = np.histogram(rr, bins=np.arange(0, 700, 10))
peaks = [(int(edges[i]), int(hist[i])) for i in np.argsort(-hist)[:8]]
res['lavender_glow_radial_hist_top'] = peaks
res['band_guess'] = []
for lo, hi in ((200, 260), (140, 200), (90, 140)):
    sel = (rr >= lo) & (rr < hi)
    if sel.sum() > 80:
        rpx = float(np.median(rr[sel]))
        res['band_guess'].append({'screen_radius_px': round(rpx, 1), 'pixels': int(sel.sum()),
                                  'track_d_if_band_radius_3.9m': ring_d_for_radius(rpx, vp, 3.9)[0]})
json.dump(res, open(ROOT + '/Captures/s2v1/original_layout.json', 'w'), indent=1)
mark = (img * 255).astype(np.uint8).copy()
for b in bulbs:
    x, y = int(b['cx']), int(b['cy']); mark[max(0, y - 2):y + 3, max(0, x - 2):x + 3] = (0, 255, 0)
for name, col in (('yellow', (255, 0, 0)), ('cyan', (0, 0, 255)), ('pink', (0, 255, 255))):
    for st in stars[name]:
        x0, y0, x1, y1 = st['bbox_px']; mark[y0, x0:x1] = col; mark[y1, x0:x1] = col; mark[y0:y1, x0] = col; mark[y0:y1, x1] = col
write_png(ROOT + '/Captures/s2v1/original_layout_marked.png', mark)
print(json.dumps({k: res[k] for k in ('gold_rings', 'band_guess')}, indent=1))
for k, v in stars.items():
    print(k, [(s_['px'], s_['wall_hit_d_angle_dist']) for s_ in v])
