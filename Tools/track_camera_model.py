"""Lead design tool: predicts where the hero camera puts the mascot and the tunnel vanishing point for a set of track
knots, WITHOUT a Unity run. Re-implements Unity Splines' AutoSmooth tangents, TrackPath arc-length frames and the
RunnerCameraRig portrait maths (approved camera 2.75 back / 1.3 up / pitch 10 / FOV 58, lookAhead 10, look-at-runner
0.08, slope compensation 0.85 / 0.5). Calibrate against a real build's [BWK] log lines (hero camera runner-local yaw,
vanishing-glow screen position) before trusting a new layout.

Usage (Blender's bundled Python has numpy):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/track_camera_model.py
"""
import math
import sys

import numpy as np

KNOTS = [
    (0, 0, 0), (0, -0.6, 12), (0.6, -1.6, 24), (2.4, -2.9, 36),
    (5.6, -4.3, 48), (10.4, -5.6, 59), (15.6, -6.6, 70), (20, -7.8, 82),
    (22, -10.5, 96), (21, -13.6, 110), (17, -15.4, 124), (11, -17, 138),
    (7.5, -18.8, 153), (8, -20.8, 168), (12, -22.8, 182), (19, -24.6, 194),
    (28, -26.2, 203), (39, -27.6, 208), (50, -29, 207), (60, -30.4, 201),
    (67, -31.8, 191), (70, -33.2, 178), (70, -35, 163), (68, -36.6, 148),
    (68, -38, 133), (69, -39, 118), (69, -39.6, 104),
]
HERO_D = 105.5
BACK, HEIGHT, PITCH, VFOV, ASPECT = 2.75, 1.3, 10.0, 58.0, 9 / 16
LOOK_AHEAD, LOOK_RUNNER_W, SLOPE_COMP, LOOK_SLOPE_COMP = 10.0, 0.08, 0.85, 0.5
TENSION = 1 / 3


def auto_smooth_tangent(prev, cur, nxt, a=TENSION):
    d1, d2 = np.linalg.norm(cur - prev), np.linalg.norm(nxt - cur)
    if d1 == 0:
        return (nxt - cur) * 0.1
    if d2 == 0:
        return (cur - prev) * 0.1
    d1a, d1a2, d2a, d2a2 = d1 ** a, d1 ** (2 * a), d2 ** a, d2 ** (2 * a)
    return (d1a2 * nxt - d2a2 * prev + (d2a2 - d1a2) * cur) / (3 * d1a * (d1a + d2a))


def build_track(knots, mirror=-1.0, spacing=0.5):
    k = np.array([(mirror * x, y, z) for x, y, z in knots], float)
    n = len(k)
    tan = []
    for i in range(n):
        prev = k[i - 1] if i > 0 else k[i] - (k[i + 1] - k[i])
        nxt = k[i + 1] if i < n - 1 else k[i] + (k[i] - k[i - 1])
        tan.append(auto_smooth_tangent(prev, k[i], nxt))
    pts = []
    for i in range(n - 1):
        p0, p1, p2, p3 = k[i], k[i] + tan[i], k[i + 1] - tan[i + 1], k[i + 1]
        for t in np.linspace(0, 1, 400, endpoint=False):
            u = 1 - t
            pts.append(u ** 3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t ** 3 * p3)
    pts.append(k[-1])
    pts = np.array(pts)
    cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    ds = np.arange(0, cum[-1], spacing)
    pos = np.stack([np.interp(ds, cum, pts[:, j]) for j in range(3)], 1)
    fwd = np.gradient(pos, axis=0)
    fwd /= np.linalg.norm(fwd, axis=1, keepdims=True)
    up = np.array([0, 1, 0.0])
    fu = up - fwd * (fwd @ up)[:, None]
    fu /= np.linalg.norm(fu, axis=1, keepdims=True)
    fr = np.cross(fu, fwd)          # Unity is left-handed: Cross(up, forward) = right
    return ds, pos, fwd, fu, fr


def frame(track, d):
    ds, pos, fwd, fu, fr = track
    i = int(np.clip(np.searchsorted(ds, d), 1, len(ds) - 1))
    t = (d - ds[i - 1]) / (ds[i] - ds[i - 1])
    lerp = lambda a: a[i - 1] * (1 - t) + a[i] * t
    f = lerp(fwd); f /= np.linalg.norm(f)
    u = lerp(fu); u /= np.linalg.norm(u)
    return lerp(pos), f, u, np.cross(u, f)


def look_rotation(fwd, up):
    z = fwd / np.linalg.norm(fwd)
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], 1)    # columns = camera right, up, forward (world)


def camera(track, d=HERO_D, look_ahead=LOOK_AHEAD, dutch_deg=0.0):
    pc, _, uc, _ = frame(track, d - BACK)
    pr, fr_, ur, rr = frame(track, d)
    pl, _, ul, _ = frame(track, d + look_ahead)
    Y = np.array([0, 1, 0.0])
    pos = pc + uc * HEIGHT - Y * ((pc[1] - pr[1]) * SLOPE_COMP)
    ahead = pl + ul * HEIGHT + Y * ((pr[1] - pl[1]) * LOOK_SLOPE_COMP)
    look = ahead * (1 - LOOK_RUNNER_W) + (pr + ur * 0.45) * LOOK_RUNNER_W
    R = look_rotation(look - pos, uc)
    p = math.radians(PITCH)            # * Euler(pitch, 0, 0): Unity +x rotation tilts forward downward
    Rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    R = R @ Rx
    q = math.radians(dutch_deg)
    Rz = np.array([[math.cos(q), -math.sin(q), 0], [math.sin(q), math.cos(q), 0], [0, 0, 1]])
    return pos, R @ Rz, (pr, fr_, ur, rr)


def project(pos, R, world):
    v = R.T @ (world - pos)
    th = math.tan(math.radians(VFOV / 2))
    return 0.5 + 0.5 * v[0] / (v[2] * th * ASPECT), 0.5 - 0.5 * v[1] / (v[2] * th), v[2]


def report(knots, label, dutch_deg=0.0, glow_depth=31.5):
    tr = build_track(knots)
    pos, R, (pr, fr_, ur, rr) = camera(tr, dutch_deg=dutch_deg)
    yaw = math.degrees(math.atan2(np.dot(R[:, 2], rr), np.dot(R[:, 2], fr_)))
    lat = float(np.dot(pos - pr, rr))
    hat = project(pos, R, pr + ur * 0.95)
    # vanishing point: tunnel axis point whose camera depth is glow_depth
    best = None
    for dd in np.arange(HERO_D, HERO_D + 80, 0.25):
        pa, _, ua, _ = frame(tr, dd)
        sx, sy, z = project(pos, R, pa + ua * 2.3)
        if z >= glow_depth:
            best = (sx, sy, dd)
            break
    print(f"{label:28s} cam yaw {yaw:+5.2f} deg  cam lateral {lat:+.3f} m  mascot hat x {hat[0]:.3f} y {hat[1]:.3f}  "
          f"VP@{glow_depth:.1f}m x {best[0]:.3f} y {best[1]:.3f} (track {best[2]:.1f} m)")


if __name__ == "__main__":
    report(KNOTS, "current (mirrored)", dutch_deg=float(sys.argv[1]) if len(sys.argv) > 1 else 5.74)
