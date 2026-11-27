"""Lead 6d001969 2026-11-27: luma of the S2 tunnel-wall boxes on 1280x720 R2 renders (reference vs before vs after).
Usage: python -I Tools/wall_luma.py Reference/frames4k_720/f_03.00s.png <before R2 png> <after R2 png> (Blender bundled Python)."""
import sys, os
sys.path.insert(0, 'C:/Users/josia/thanksgiving/Tools')
from img_crop import read_png
import numpy as np
def load(p):
    a = read_png(p)
    a = np.asarray(a)[..., :3].astype(np.float32) / 255.0
    return a
def luma(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
boxes = {'R2 right wall (950,0,1280,360)': (950,0,1280,360), 'RW4 (1090,300,1160,345)': (1090,300,1160,345),
         'left wall (0,0,330,360)': (0,0,330,360), 'tunnel core (520,60,760,260)': (520,60,760,260)}
imgs = sys.argv[1:]
for name, (x0,y0,x1,y1) in boxes.items():
    row = []
    for p in imgs:
        a = load(p)
        h, w = a.shape[:2]
        if w != 1280:  # side-by-side: take right half (ours) unless tagged
            pass
        L = luma(a[y0:y1, x0:x1])
        row.append('%s mean %.3f p10 %.3f p50 %.3f p90 %.3f' % (os.path.basename(os.path.dirname(p)) + '/' + os.path.basename(p), L.mean(), np.percentile(L,10), np.percentile(L,50), np.percentile(L,90)))
    print(name); [print('   ', r) for r in row]
