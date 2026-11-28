"""Bubble Wash Kingdom - S2 ART PASS milk splash skeleton (lead 470ca906, 2026-11-27, owner 23:36 "beautiful natural water
splashes"; ORIGINAL 3.00 s frame + crop water_splashes_03s: big milky crowns at BOTH feet = a lacy milk wall rising beside each
sole, fingers leaning outward with round bulb tips, branching milk splats lying on the water toward the camera, flying droplets).

Pure numpy (no bpy): build_fx_splash_art.py turns the skeleton into metaball meshes; the lead's overlay check projects it
through the matched comparison camera R2 onto the original frame. Coordinates = runner-local Unity (x right, y up, z forward).
Anchors are hand-picked pixel positions of the ORIGINAL frame (layout only, no reference pixels), cast onto the water plane.
"""
import math

import numpy as np

W, H = 1280, 720
YW = -0.02            # water line (runner-local y), as build_fx_crown_v7.py
FRAMES = 6
VIS = 0.575           # visible sphere radius / metaball element radius (threshold 0.6, stiffness 2)


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
        self.R = R
        self.right, self.up, self.fwd = R[:, 0], R[:, 1], R[:, 2]
        self.f = (h / 2.0) / math.tan(math.radians(vfov / 2.0))
        self.w, self.h = w, h

    def ray(self, u, v):
        xc = (u - self.w / 2.0) / self.f
        yc = -(v - self.h / 2.0) / self.f
        d = xc * self.right + yc * self.up + self.fwd
        return d / np.linalg.norm(d)

    def water(self, u, v, y=YW):
        d = self.ray(u, v)
        t = (y - self.c[1]) / d[1]
        return self.c + t * d

    def project(self, p):
        q = (np.asarray(p, float) - self.c) @ self.R          # camera coords (x right, y up, z forward)
        z = np.maximum(q[..., 2], 1e-4)
        return np.stack([self.w / 2.0 + self.f * q[..., 0] / z, self.h / 2.0 - self.f * q[..., 1] / z, z], -1)


# R2 comparison camera in runner-local space (build_fx_crown_v7.py: waterfx S2 camera log, CaptureTools R2 Euler(6, -7, 0))
Q_RF = euler(0.49, 351.02, 358.68) @ euler(6, -9, 0).T
CAM = Cam((0.328, 0.733, -2.830), Q_RF @ euler(6, -7, 0), 58.0, W, H)

UP = np.array([0.0, 1.0, 0.0])

# ORIGINAL 3.00 s layout (1280 x 720 px): where each milk wall meets the water, from the sole outward toward the camera
BASE_R = [(748, 522), (790, 540), (835, 560), (880, 580), (925, 598), (965, 612)]
BASE_L = [(538, 520), (506, 538), (474, 560), (446, 584), (424, 606)]
# flat branching milk splats on the water (right side: lower right of the frame; left: below the coin's right edge)
SPLATS_R = [(985, 640), (1060, 668), (1105, 606), (930, 690)]
SPLATS_L = [(470, 640)]


def _curve(pix):
    pts = np.array([CAM.water(u, v) for u, v in pix])
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    return pts, s / s[-1]


def _at(pts, s, t):
    t = min(max(t, 0.0), 1.0)
    i = int(np.searchsorted(s, t, side="right") - 1)
    i = min(max(i, 0), len(pts) - 2)
    k = (t - s[i]) / max(s[i + 1] - s[i], 1e-9)
    return pts[i] * (1 - k) + pts[i + 1] * k, (pts[i + 1] - pts[i]) / max(np.linalg.norm(pts[i + 1] - pts[i]), 1e-9)


def _hump(t):
    """Wall height profile along the base: tall beside the sole, falling toward the camera."""
    rise = 0.55 + 0.45 * math.exp(-((t - 0.22) / 0.26) ** 2)
    return rise * (1.0 - 0.55 * t)


def side_skeleton(side, frame, rng_seed):
    """Metaball elements [(x, y, z, r_elem)], milky droplets [(x, y, z, r_vis)], clear bubbles [(x, y, z, r_vis)], pivot."""
    rng = np.random.default_rng(rng_seed)
    ph = frame / float(FRAMES)
    tau = 2.0 * math.pi
    pts, s = _curve(BASE_R if side > 0 else BASE_L)
    out = np.array([float(side), 0.0, 0.0])                      # outward from the body
    back = np.array([0.0, 0.0, -1.0])                            # toward the camera
    Hb = 0.30 if side > 0 else 0.26                              # solid lacy band height beside the sole (m)
    lean = math.radians(24.0)
    balls, drops, bubbles = [], [], []

    # 1) lacy milk wall: dense small balls up the band, irregular top + a few open holes that drift with the frame
    n_t = 46 if side > 0 else 36
    for ti in range(n_t):
        t = ti / (n_t - 1.0)
        b, tan = _at(pts, s, t)
        nrm = np.cross(UP, tan)
        if np.dot(nrm, out) < 0:
            nrm = -nrm
        hb = Hb * _hump(t) * (1.0 + 0.08 * math.sin(tau * (ph + 0.9 * t)))
        hb *= 1.0 + 0.18 * (rng.random() - 0.5)
        y = YW - 0.01
        while y < hb:
            frac = (y - YW) / max(hb, 1e-3)
            hole = math.sin(17.0 * t + tau * ph) * math.sin(29.0 * y - tau * ph * 0.5 + 1.3 * side)
            if frac > 0.45 and hole > 0.62:
                y += 0.022
                continue
            rv = 0.020 * (1.15 - 0.45 * frac)
            p = b + UP * y + nrm * (math.tan(lean) * (y - YW))
            balls.append((p[0], p[1], p[2], rv / VIS))
            y += 0.021
        # thick rounded foot of the wall where it leaves the water (rolls outward)
        p = b + nrm * 0.03 + UP * 0.0
        balls.append((p[0], p[1], p[2], 0.030 / VIS))

    # 2) fingers on the wall's top edge: lean outward + back, bend under gravity, round bulb tips, some detached beads
    n_f = 9 if side > 0 else 7
    for i in range(n_f):
        t = 0.03 + 0.72 * (i + 0.35 * rng.random()) / n_f
        b, tan = _at(pts, s, t)
        nrm = np.cross(UP, tan)
        if np.dot(nrm, out) < 0:
            nrm = -nrm
        hb = Hb * _hump(t)
        phi = rng.random()
        L = (0.16 + 0.20 * rng.random()) * (1.15 - 0.6 * t) * (1.0 + 0.2 * math.sin(tau * (ph + phi)))
        a = math.radians(12.0 + 44.0 * t + 14.0 * (rng.random() - 0.5) + 5.0 * math.sin(tau * (ph + phi + 0.25)))
        d0 = UP * math.cos(a) + nrm * math.sin(a) + back * 0.18
        d0 /= np.linalg.norm(d0)
        bend = math.radians(18.0 + 34.0 * rng.random())
        p = b + UP * (hb * 0.82) + nrm * (math.tan(lean) * hb * 0.82)
        steps = 11
        r0, r1 = 0.019, 0.010
        for k in range(steps):
            u = k / (steps - 1.0)
            dk = d0 * math.cos(bend * u) - UP * math.sin(bend * u) * 0.9 + nrm * math.sin(bend * u) * 0.4
            dk /= np.linalg.norm(dk)
            p = p + dk * (L / steps)
            rv = r0 + (r1 - r0) * u
            balls.append((p[0], p[1], p[2], rv / VIS))
        tip = p + dk * 0.012
        rb = 0.020 + 0.012 * rng.random()
        balls.append((tip[0], tip[1], tip[2], rb / VIS))
        if rng.random() < 0.55:                                    # bead about to leave the finger
            q = tip + dk * (0.05 + 0.04 * ((ph + phi) % 1.0))
            drops.append((q[0], q[1], q[2], 0.014 + 0.008 * rng.random()))

    # 3) branching milk splats lying on the water toward the camera
    for (u, v) in (SPLATS_R if side > 0 else SPLATS_L):
        c = CAM.water(u, v)
        n_b = 3 if side > 0 else 2
        base_ang = rng.random() * tau
        for j in range(n_b):
            ang = base_ang + tau * j / n_b + 0.5 * (rng.random() - 0.5)
            dirv = np.array([math.cos(ang), 0.0, math.sin(ang) * 1.3])
            dirv /= np.linalg.norm(dirv)
            Lb = (0.09 + 0.10 * rng.random()) * (1.0 + 0.15 * math.sin(tau * (ph + j * 0.3)))
            steps = 7
            for k in range(steps + 1):
                uu = k / float(steps)
                rv = 0.016 - 0.004 * uu
                p = c + dirv * Lb * uu
                balls.append((p[0], YW + rv * 0.55, p[2], rv / VIS))
            tip = c + dirv * (Lb + 0.012)
            rb = 0.020 + 0.008 * rng.random()
            balls.append((tip[0], YW + rb * 0.6, tip[2], rb / VIS))
        balls.append((c[0], YW + 0.012, c[2], 0.024 / VIS))

    # 4) flying droplets (milky beads) over / beside the crown, on looping ballistic paths; a few clear water bubbles
    n_d = 16 if side > 0 else 10
    for j in range(n_d):
        t = rng.random() * 0.8
        b, tan = _at(pts, s, t)
        nrm = np.cross(UP, tan)
        if np.dot(nrm, out) < 0:
            nrm = -nrm
        phi = rng.random()
        q = (ph + phi) % 1.0
        v0 = UP * (1.2 + 0.9 * rng.random()) + nrm * (0.5 + 0.8 * rng.random()) + back * (0.3 * rng.random())
        size = 0.010 + 0.016 * rng.random()                       # drawn before any frame-dependent skip (stable ids)
        T = 0.42
        tt = q * T
        p = b + UP * (Hb * _hump(t) * 0.7) + v0 * tt + np.array([0.0, -4.9, 0.0]) * tt * tt
        if p[1] < YW + 0.03:
            continue
        drops.append((p[0], p[1], p[2], size))
    for j in range(5 if side > 0 else 4):
        t = 0.2 + 0.8 * rng.random()
        b, tan = _at(pts, s, t)
        p = b + out * (0.08 + 0.3 * rng.random()) + back * (0.1 + 0.35 * rng.random()) + UP * (0.02 + 0.05 * rng.random())
        bubbles.append((p[0], p[1], p[2], 0.016 + 0.018 * rng.random()))

    pivot, _ = _at(pts, s, 0.15)
    pivot = np.array([pivot[0], 0.0, pivot[2]])
    return balls, drops, bubbles, pivot


def all_frames(seed=20261127):
    """{'L': [(balls, drops, bubbles), ...], 'R': [...], 'pivot_L', 'pivot_R'} - the same seed per side every frame so the
    fingers keep their identity and only move (seamless loop over FRAMES)."""
    res = {}
    for side, key in ((-1, "L"), (1, "R")):
        fr = []
        piv = None
        for k in range(FRAMES):
            b, d, bb, piv = side_skeleton(side, k, seed + (7 if side > 0 else 3))
            fr.append((b, d, bb))
        res[key] = fr
        res["pivot_" + key] = piv
    return res
