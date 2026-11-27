"""Stack images into ONE labelled sheet: every row is scaled to the same width and gets a caption bar above it.
Stdlib + numpy (Blender's bundled Python), no PIL / FreeType: captions use a built-in 5x7 pixel font (A-Z 0-9 and
 .,:;-+/|()%=#'), drawn in UPPER CASE. Output belongs in Captures/ (gitignored) when it shows reference pixels.

Usage:
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/labeled_sheet.py OUT.png WIDTH \
      "CAPTION FOR ROW 1" row1.png  "CAPTION FOR ROW 2" row2.png ...
A caption may hold several column titles separated by " || ": they are centred over equal-width thirds / quarters of the
row (matching Tools/triptych.py panels), e.g. "APPROVED || PREVIOUS S2P10E || NEW S2P10F".
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_crop import read_png, write_png  # noqa: E402

BG = (20, 12, 36)
FG = (255, 255, 255)
GAP = 10

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "01010", "01010", "00100", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000"] * 7,
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "|": ["00100", "00100", "00100", "00100", "00100", "00100", "00100"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
}


def text_bitmap(text, px):
    """Boolean mask of the text at `px` pixels per font dot (glyph cell 6 x 8 dots)."""
    text = text.upper()
    cols = []
    for ch in text:
        g = FONT.get(ch, FONT[" "])
        cell = np.array([[c == "1" for c in row] + [False] for row in g] + [[False] * 6], bool)
        cols.append(cell)
    if not cols:
        return np.zeros((8 * px, 1), bool)
    m = np.concatenate(cols, axis=1)
    return np.repeat(np.repeat(m, px, axis=0), px, axis=1)


def fit_w(img, tw):
    h, w, _ = img.shape
    th = max(1, int(round(h * tw / w)))
    ys = (np.arange(th) * h / th).astype(int)
    xs = (np.arange(tw) * w / tw).astype(int)
    ys1 = np.minimum(ys + max(1, h // th // 2), h - 1)
    xs1 = np.minimum(xs + max(1, w // tw // 2), w - 1)
    f = img[..., :3].astype(np.float32)
    return ((f[ys][:, xs] + f[ys1][:, xs] + f[ys][:, xs1] + f[ys1][:, xs1]) / 4).astype(np.uint8)


def caption_bar(caption, width, px):
    parts = [p.strip() for p in caption.split("||")]
    bar = np.zeros((8 * px + 2 * px + 4, width, 3), np.uint8)
    bar[:] = BG
    n = len(parts)
    for i, part in enumerate(parts):
        m = text_bitmap(part, px)
        if m.shape[1] > width // n - 8:  # shrink a too-long title
            scale = max(1, px - 1)
            m = text_bitmap(part, scale)
        x0 = i * width // n + max(0, (width // n - m.shape[1]) // 2)
        y0 = px + 2
        hh, ww = m.shape
        ww = min(ww, width - x0)
        region = bar[y0:y0 + hh, x0:x0 + ww]
        region[m[:, :ww]] = FG
    return bar


def main(argv):
    out, width = argv[0], int(argv[1])
    pairs = argv[2:]
    if len(pairs) % 2:
        raise SystemExit("captions and images must come in pairs")
    px = max(2, width // 500)
    blocks = []
    for i in range(0, len(pairs), 2):
        cap, path = pairs[i], pairs[i + 1]
        img = fit_w(read_png(path), width)
        blocks.append(caption_bar(cap, width, px))
        blocks.append(img)
        blocks.append(np.full((GAP, width, 3), BG, np.uint8))
    sheet = np.concatenate(blocks[:-1], axis=0)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    write_png(out, sheet)
    print("wrote", out, sheet.shape[1], "x", sheet.shape[0])


if __name__ == "__main__":
    main(sys.argv[1:])
