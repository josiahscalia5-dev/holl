"""Milestone before/after image: [reference | before | after] from two CaptureTools side-by-sides of the SAME fixed hero
camera (LEFT half = reference, RIGHT half = our render). Output goes to Captures/ only (contains reference frames).

Usage (Blender's bundled Python has numpy):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/triptych.py BEFORE_vs.png AFTER_vs.png OUT.png
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

GAP = 12


def halves(img):
    w = img.shape[1]
    half = (w - GAP) // 2
    return img[:, :half, :3], img[:, half + GAP:half + GAP + half, :3]


def main(before, after, out):
    ref, ours_before = halves(read_png(before))
    _, ours_after = halves(read_png(after))
    h = min(ref.shape[0], ours_before.shape[0], ours_after.shape[0])
    panels = [ref[:h], ours_before[:h], ours_after[:h]]
    gap = np.full((h, GAP, 3), 24, np.uint8)
    img = np.concatenate([panels[0], gap, panels[1], gap, panels[2]], axis=1)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    write_png(out, img)
    print("wrote", out, img.shape[1], "x", img.shape[0])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
