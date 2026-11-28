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
    """Metaball elements [(x, y, z, r_elem)], milky droplets [(x, y, z, r_vis)], clear bubbles [(x, y, z, r_vis)], pivot.
    Shape (crop water_splashes_03s): a LOW lacy milk lip on the water along the wake line, a dense crown of branching fingers
    fanning up / outward from the sole (longest beside the foot), round bulb tips + beads, splats on the water, flying drops."""
    rng = np.random.default_rng(rng_seed)
    ph = frame / float(FRAMES)
    tau = 2.0 * math.pi
    pts, s = _curve(BASE_R if side > 0 else BASE_L)
    out = np.array([float(side), 0.0, 0.0])                      # outward from the body
    back = np.array([0.0, 0.0, -1.0])                            # toward the camera
    Hb = 0.15 if side > 0 else 0.13                              # lacy lip height beside the sole (m)
    lean = math.radians(28.0)
    balls, drops, bubbles = [], [], []

    def frame_at(t):
        b, tan = _at(pts, s, t)
        nrm = np.cross(UP, tan)
        if np.dot(nrm, out) < 0:
            nrm = -nrm
        return b, tan, nrm

    def lip(t):
        return Hb * (1.0 if t < 0.3 else max(0.0, 1.0 - (t - 0.3) * 3.2))

    # 1) lacy milk lip on the water: tall + holey beside the sole, a low rolled ribbon toward the camera
    n_t = 26 if side > 0 else 22
    for ti in range(n_t):
        t = 0.55 * ti / (n_t - 1.0)
        b, tan, nrm = frame_at(t)
        hb = lip(t) * (1.0 + 0.10 * math.sin(tau * (ph + 0.9 * t))) * (1.0 + 0.25 * (rng.random() - 0.5))
        y = YW - 0.01
        while y < hb:
            frac = (y - YW) / max(hb, 1e-3)
            hole = math.sin(19.0 * t + tau * ph) * math.sin(37.0 * y - tau * ph * 0.5 + 1.3 * side)
            if frac > 0.28 and hole > 0.42:
                y += 0.020
                continue
            rv = 0.019 * (1.1 - 0.4 * frac)
            p = b + UP * y + nrm * (math.tan(lean) * (y - YW))
            balls.append((p[0], p[1], p[2], rv / VIS))
            y += 0.020
        p = b + nrm * 0.025
        balls.append((p[0], p[1], p[2], 0.024 / VIS))              # rolled foot of the lip on the water

    # 2) crown of branching fingers fanning from the sole: lean outward, some forward, some back toward the camera; bend
    #    under gravity; a fork on about half of them; round bulb tips; beads about to leave
    def finger(p, d0, L, r0, r1, bend, phi, depth):
        steps = 10 if depth == 0 else 6
        dk = d0
        fork_at = 4 + int(rng.random() * 3)
        do_fork = depth == 0 and rng.random() < 0.55
        fork_sign = 1.0 if rng.random() < 0.5 else -1.0
        fork_len = 0.4 + 0.25 * rng.random()
        for k in range(steps):
            u = k / (steps - 1.0)
            dk = d0 * math.cos(bend * u) - UP * math.sin(bend * u) * 0.9 + out * math.sin(bend * u) * 0.35
            dk = dk / np.linalg.norm(dk)
            p = p + dk * (L / steps)
            rv = r0 + (r1 - r0) * u
            balls.append((p[0], p[1], p[2], rv / VIS))
            if do_fork and k == fork_at:
                side_dir = np.cross(dk, UP)
                n_ = np.linalg.norm(side_dir)
                side_dir = side_dir / n_ if n_ > 1e-6 else out
                fd = dk * 0.75 + side_dir * 0.65 * fork_sign + UP * 0.15
                finger(p.copy(), fd / np.linalg.norm(fd), L * fork_len, rv * 0.9, r1 * 0.9, bend * 1.2, phi + 0.37, 1)
        tip = p + dk * 0.010
        rb = (0.026 + 0.012 * rng.random()) * (0.85 if depth else 1.0)
        balls.append((tip[0], tip[1], tip[2], rb / VIS))
        if rng.random() < 0.5:                                     # bead about to leave the finger
            q = tip + dk * (0.045 + 0.04 * ((ph + phi) % 1.0))
            drops.append((q[0], q[1], q[2], 0.012 + 0.008 * rng.random()))

    n_f = 15 if side > 0 else 11
    for i in range(n_f):
        t = 0.62 * ((i + 0.5 * rng.random()) / n_f) ** 1.25
        b, tan, nrm = frame_at(t)
        hb = lip(t)
        phi = rng.random()
        L = (0.15 + 0.24 * rng.random()) * (1.2 - 0.9 * t) * (1.0 + 0.18 * math.sin(tau * (ph + phi)))
        a = math.radians(8.0 + 58.0 * (i / max(1.0, n_f - 1.0)) + 16.0 * (rng.random() - 0.5) + 5.0 * math.sin(tau * (ph + phi + 0.25)))
        fwdk = (rng.random() - 0.55) * 0.9                       # fan: some lean forward (+z), most back toward the camera
        d0 = UP * math.cos(a) + nrm * math.sin(a) - back * fwdk
        d0 /= np.linalg.norm(d0)
        bend = math.radians(15.0 + 40.0 * rng.random())
        p0 = b + UP * (hb * 0.7) + nrm * (math.tan(lean) * hb * 0.7)
        finger(p0, d0, L, 0.028 + 0.006 * rng.random(), 0.015, bend, phi, 0)

    # 2b) the far wake: separate milk tendrils on the water that leave the lip toward the camera (no straight ribbon)
    for t0 in ((0.52, 0.70, 0.88) if side > 0 else (0.55, 0.80)):
        b, tan, nrm = frame_at(t0)
        L = 0.10 + 0.10 * rng.random()
        dirv = tan * 0.8 + nrm * (0.6 * (rng.random() - 0.3))
        dirv = dirv / np.linalg.norm(dirv)
        steps = 7
        for k in range(steps + 1):
            u = k / float(steps)
            rv = 0.020 - 0.006 * u
            p = b + dirv * L * u + nrm * 0.02 * math.sin(3.0 * u + tau * ph)
            balls.append((p[0], YW + rv * 0.6 + 0.01 * (1.0 - u), p[2], rv / VIS))
        tip = b + dirv * (L + 0.015)
        rb = 0.022 + 0.010 * rng.random()
        balls.append((tip[0], YW + rb * 0.6, tip[2], rb / VIS))
        side_dir = np.cross(UP, dirv)
        fb = dirv * 0.6 + side_dir * (0.8 if rng.random() < 0.5 else -0.8)
        fb = fb / np.linalg.norm(fb)
        m = b + dirv * L * 0.5
        for k in range(1, 5):
            p = m + fb * 0.018 * k
            balls.append((p[0], YW + 0.012, p[2], 0.015 / VIS))
        q = m + fb * 0.09
        balls.append((q[0], YW + 0.014, q[2], 0.022 / VIS))

    # 3) branching milk splats lying on the water toward the camera
    for (u, v) in (SPLATS_R if side > 0 else SPLATS_L):
        c = CAM.water(u, v)
        n_b = 3
        base_ang = rng.random() * tau
        for j in range(n_b):
            ang = base_ang + tau * j / n_b + 0.6 * (rng.random() - 0.5)
            dirv = np.array([math.cos(ang), 0.0, math.sin(ang) * 1.3])
            dirv /= np.linalg.norm(dirv)
            Lb = (0.07 + 0.09 * rng.random()) * (1.0 + 0.15 * math.sin(tau * (ph + j * 0.3)))
            steps = 6
            for k in range(steps + 1):
                uu = k / float(steps)
                rv = 0.017 - 0.005 * uu
                p = c + dirv * Lb * uu
                balls.append((p[0], YW + rv * 0.5, p[2], rv / VIS))
            tip = c + dirv * (Lb + 0.012)
            rb = 0.019 + 0.008 * rng.random()
            balls.append((tip[0], YW + rb * 0.55, tip[2], rb / VIS))
        balls.append((c[0], YW + 0.010, c[2], 0.026 / VIS))

    # 4) flying droplets (milky beads) spraying up / outward on looping ballistic paths; clear water bubbles on the water
    n_d = 24 if side > 0 else 15
    for j in range(n_d):
        t = rng.random() * 0.75
        b, tan, nrm = frame_at(t)
        phi = rng.random()
        q = (ph + phi) % 1.0
        v0 = UP * (1.0 + 1.0 * rng.random()) + nrm * (0.7 + 1.3 * rng.random()) + back * (0.2 + 0.6 * rng.random())
        size = 0.009 + 0.017 * rng.random()                       # drawn before any frame-dependent skip (stable ids)
        T = 0.45
        tt = q * T
        p = b + UP * (lip(t) * 0.8) + v0 * tt + np.array([0.0, -4.9, 0.0]) * tt * tt
        if p[1] < YW + 0.03:
            continue
        drops.append((p[0], p[1], p[2], size))
    for j in range(7 if side > 0 else 6):
        t = 0.15 + 0.85 * rng.random()
        b, tan, nrm = frame_at(t)
        p = b + nrm * (0.06 + 0.35 * rng.random()) + back * (0.05 + 0.45 * rng.random()) + UP * (0.015 + 0.06 * rng.random())
        bubbles.append((p[0], p[1], p[2], 0.014 + 0.020 * rng.random()))

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
