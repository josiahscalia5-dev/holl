"""S2 look metrics (lead 8d2d815d 2026-11-27): compares any 1280x720 S2 render made with the R2 matching camera against the ORIGINAL
Google Flow 3.00 s frame - radial depth profile around the vanishing point (L*, C*, hue, mean colour per ring of radius), the tunnel
palette (k-means, 8 colours with shares) and, for the original, the element colours (bulbs, gold, neon stars, lavender glow, drum
metal, slots). Numbers only (safe to quote anywhere); the images stay in Captures/. Mascot and the lower water area are excluded.
Usage (Blender's bundled Python has numpy):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/s2_look_metrics.py <R2 render.png> [more renders...]
  e.g. Captures/lead/gate_s2p10i/R2_rear_S2_like_3s_16x9.png (or a Blender render from the same camera, 1280x720).
Measured 2026-11-27 20:45 (ORIGINAL | ours gate_s2p10i): core r 0-80 px L* 37.6-44.8 C* 47-54 #68479D | L* 48-67 C* 36-49 #A380C3
(ours far too pale + pink); r > 170 px within 1-2 L*. Palette: original 14 % deep violet #55406B, no near-white | ours 6 % / 11 % #F0E5D7.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png  # noqa: E402

REF = 'C:/Users/josia/thanksgiving/Reference/frames4k_720/f_03.00s.png'
VP = (760, 205)                      # original vanishing point (R2 solve: ours ~ (770, 213))
RINGS = [(0, 25), (25, 50), (50, 80), (80, 120), (120, 170), (170, 240), (240, 330), (330, 460)]


def load(p):
    a = np.asarray(read_png(p))[..., :3].astype(np.float32) / 255.0
    if a.shape[:2] != (720, 1280):
        ys = np.linspace(0, a.shape[0] - 1, 720).astype(int); xs = np.linspace(0, a.shape[1] - 1, 1280).astype(int)
        a = a[ys][:, xs]
    return a


def lab(a):
    c = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return 116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])


def hexs(c):
    return '#%02X%02X%02X' % tuple(int(round(v * 255)) for v in c)


def kmeans(X, k=8, it=25, seed=1):
    rng = np.random.default_rng(seed); C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(it):
        lab_ = ((X[:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
        C = np.array([X[lab_ == j].mean(0) if (lab_ == j).any() else C[j] for j in range(k)])
    return C, np.bincount(lab_, minlength=k) / len(X)


H, W = 720, 1280
yy, xx = np.mgrid[0:H, 0:W]
MASCOT = ((xx - 640) / 215.) ** 2 + ((yy - 430) / 300.) ** 2 < 1
UPPER = (yy < 450) & ~MASCOT
R = np.hypot(xx - VP[0], yy - VP[1])


def profile(img):
    out = []
    for a, b in RINGS:
        m = (R >= a) & (R < b) & UPPER
        L, A, B = lab(img[m]); C = np.hypot(A, B); h = (np.degrees(np.arctan2(B.mean(), A.mean())) + 360) % 360
        out.append((L.mean(), C.mean(), h, hexs(img[m].mean(0))))
    return out


def main(paths):
    imgs = [('ORIGINAL', load(REF))] + [(os.path.basename(os.path.dirname(p)) + '/' + os.path.basename(p), load(p)) for p in paths]
    profs = [profile(i) for _, i in imgs]
    print('RADIAL DEPTH PROFILE around VP %s (L* C* hue mean-colour); delta = render - original' % (VP,))
    for k, (a, b) in enumerate(RINGS):
        cells = ['%5.1f %5.1f %5.1f %s' % profs[0][k]]
        for p in profs[1:]:
            cells.append('%5.1f %5.1f %5.1f %s (dL %+5.1f dC %+5.1f)' % (p[k] + (p[k][0] - profs[0][k][0], p[k][1] - profs[0][k][1])))
        print(' r %3d-%3d | %s' % (a, b, ' | '.join(cells)))
    for name, img in imgs:
        C, s = kmeans(img[UPPER][::7]); o = np.argsort(-s)
        print('%s palette: %s' % (name[-40:], ' '.join('%s %.0f%%' % (hexs(C[j]), 100 * s[j]) for j in o)))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1:])
