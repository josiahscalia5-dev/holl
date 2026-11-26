"""Crop and zoom a PNG without PIL (stdlib zlib + numpy), for inspecting reference / capture details cheaply.

Usage (Blender's bundled Python has numpy; this PC has no system Python):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/img_crop.py IN.png OUT.png X0 Y0 X1 Y1 [SCALE]
  ... Tools/img_crop.py --size IN.png            (prints width height)
Coordinates are pixels of IN.png (X1/Y1 exclusive). SCALE (default 1) enlarges with nearest-neighbour (integer) or
bilinear (fractional). Write crops of Reference/ frames ONLY into Captures/ (gitignored): reference images stay private.
"""
import struct
import sys
import zlib

import numpy as np

try:  # Blender 5.3's bundled Python ships OpenImageIO: native decode, ~100x faster than the pure-Python Paeth loop below
    import OpenImageIO as _oiio
except Exception:  # pragma: no cover - fallback keeps the tools working anywhere numpy exists
    _oiio = None


def _read_oiio(path):
    cfg = _oiio.ImageSpec()
    cfg.attribute("oiio:UnassociatedAlpha", 1)  # keep straight RGB like the pure decoder (no premultiply)
    buf = _oiio.ImageBuf(path, 0, 0, cfg)
    if buf.has_error:
        return None
    px = buf.get_pixels(_oiio.UINT8)
    if px is None or px.ndim != 3:
        return None
    ch = px.shape[2]
    if ch == 1:
        return np.repeat(px, 3, axis=2)
    if ch == 2:
        return np.repeat(px[:, :, :1], 3, axis=2)
    return np.ascontiguousarray(px[:, :, :3])


def read_png(path):
    if _oiio is not None:
        img = _read_oiio(path)
        if img is not None:
            return img
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: " + path)
    pos, idat, w = 8, [], None
    while pos < len(data):
        ln, = struct.unpack(">I", data[pos:pos + 4]); typ = data[pos + 4:pos + 8]; body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace != 0 or ctype not in (0, 2, 4, 6):
                raise ValueError("only 8-bit non-interlaced gray/RGB/RGBA PNGs are supported")
            ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    raw = np.frombuffer(zlib.decompress(b"".join(idat)), dtype=np.uint8)
    stride = w * ch
    rows = raw.reshape(h, stride + 1)
    out = np.zeros((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.int32)
    for y in range(h):
        ft = rows[y, 0]; line = rows[y, 1:].astype(np.int32)
        if ft == 0:
            cur = line
        elif ft == 1:   # Sub: running sum per channel
            cur = line.reshape(-1, ch).cumsum(axis=0).reshape(-1) & 255
        elif ft == 2:   # Up
            cur = (line + prev) & 255
        elif ft == 3:   # Average (sequential)
            cur = np.empty(stride, dtype=np.int32)
            for i in range(stride):
                left = cur[i - ch] if i >= ch else 0
                cur[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:   # Paeth (sequential)
            cur = np.empty(stride, dtype=np.int32)
            for i in range(stride):
                a = cur[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (line[i] + pred) & 255
        else:
            raise ValueError("bad PNG filter %d" % ft)
        out[y] = cur
        prev = cur
    img = out.reshape(h, w, ch)
    if ch == 1:
        img = np.repeat(img, 3, axis=2)
    elif ch == 2:
        img = np.repeat(img[:, :, :1], 3, axis=2)
    return img[:, :, :3] if img.shape[2] >= 3 else img


def write_png(path, img):
    img = np.ascontiguousarray(img[:, :, :3].astype(np.uint8))
    h, w, _ = img.shape
    raw = np.hstack([np.zeros((h, 1), dtype=np.uint8), img.reshape(h, w * 3)]).tobytes()

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def zoom(img, s):
    if s == 1:
        return img
    if float(s).is_integer():
        s = int(s)
        return img.repeat(s, axis=0).repeat(s, axis=1)
    h, w, _ = img.shape
    nh, nw = max(1, int(h * s)), max(1, int(w * s))
    ys = np.clip((np.arange(nh) + 0.5) / s - 0.5, 0, h - 1); xs = np.clip((np.arange(nw) + 0.5) / s - 0.5, 0, w - 1)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, h - 1); x1 = np.minimum(x0 + 1, w - 1)
    fy = (ys - y0)[:, None, None]; fx = (xs - x0)[None, :, None]
    f = img.astype(np.float32)
    top = f[y0][:, x0] * (1 - fx) + f[y0][:, x1] * fx
    bot = f[y1][:, x0] * (1 - fx) + f[y1][:, x1] * fx
    return np.clip(top * (1 - fy) + bot * fy + 0.5, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--size":
        im = read_png(a[1]); print(im.shape[1], im.shape[0]); sys.exit(0)
    if len(a) < 6:
        print(__doc__); sys.exit(1)
    im = read_png(a[0])
    x0, y0, x1, y1 = (int(v) for v in a[2:6])
    x0, x1 = max(0, x0), min(im.shape[1], x1); y0, y1 = max(0, y0), min(im.shape[0], y1)
    out = zoom(im[y0:y1, x0:x1], float(a[6]) if len(a) > 6 else 1)
    write_png(a[1], out)
    print("wrote", a[1], out.shape[1], "x", out.shape[0])
