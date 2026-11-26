"""Image -> textured 3D model through Microsoft's hosted TRELLIS.2 demo (https://huggingface.co/spaces/microsoft/TRELLIS.2).

Owner-approved free experiment (2026-11-26). Licences checked: TRELLIS.2 code, Space and TRELLIS.2-4B weights are MIT.
Nothing is installed locally except the small official Gradio API client (Tools/.pylibs_gradio, gitignored).

PRIVACY: upload ONLY isolated crops WITH a transparent background (RGBA, alpha < 255 outside the object). The demo then
skips its own background-removal step, which would otherwise forward the image to a second Space (briaai/BRIA-RMBG-2.0,
non-commercial licence). This script refuses images without transparency. The demo keeps uploads in a per-session temp
folder that it deletes after ~10 minutes; there is no flagging / public gallery. Inputs stay private on this PC in
Captures/ (gitignored); the downloaded GLB goes into its own new, empty folder.

Usage (Blender's Python has numpy; the client library lives in Tools/.pylibs_gradio):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/trellis_client.py IN_RGBA.png OUT_DIR
      [--seed 0] [--res 1024] [--faces 300000] [--tex 2048]
Uses a Hugging Face token only if the owner has logged in on this PC themself (HF_TOKEN / cached login); the free
ZeroGPU quota applies (each step reserves up to 120 s of GPU time).
"""
import os
import shutil
import sys
import time
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pylibs_gradio"))


def has_transparency(path):
    """True if the PNG is RGBA / LA and some pixel has alpha < 255 (stdlib only)."""
    import numpy as np
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    pos, idat, w, h, ctype, depth = 8, b"", 0, 0, 0, 8
    while pos < len(data):
        n = int.from_bytes(data[pos:pos + 4], "big"); t = data[pos + 4:pos + 8]; body = data[pos + 8:pos + 8 + n]
        if t == b"IHDR":
            w, h = int.from_bytes(body[0:4], "big"), int.from_bytes(body[4:8], "big"); depth, ctype = body[8], body[9]
        elif t == b"IDAT":
            idat += body
        pos += 12 + n
    if ctype not in (4, 6) or depth != 8:
        return False
    ch = 4 if ctype == 6 else 2
    raw = np.frombuffer(zlib.decompress(idat), dtype=np.uint8)
    stride = w * ch
    rows = raw.reshape(h, stride + 1)
    out = np.zeros((h, stride), dtype=np.int32)
    prev = np.zeros(stride, dtype=np.int32)
    for y in range(h):                      # undo PNG filters (only alpha matters, but all bytes are needed)
        f, line = rows[y, 0], rows[y, 1:].astype(np.int32)
        if f == 0: cur = line
        elif f == 2: cur = (line + prev) & 255
        else:
            cur = np.zeros(stride, dtype=np.int32)
            for x in range(stride):
                a = cur[x - ch] if x >= ch else 0; b = prev[x]; c = prev[x - ch] if x >= ch else 0
                if f == 1: p = a
                elif f == 3: p = (a + b) // 2
                else:
                    pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                    p = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[x] = (line[x] + p) & 255
        out[y] = cur; prev = cur
    alpha = out[:, ch - 1::ch]
    return bool((alpha < 255).any())


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    src, out_dir = os.path.abspath(a[0]), os.path.abspath(a[1])
    opt = {"--seed": "0", "--res": "1024", "--faces": "300000", "--tex": "2048"}
    for i in range(2, len(a) - 1):
        if a[i] in opt: opt[a[i]] = a[i + 1]
    if not has_transparency(src):
        sys.exit("refusing: the image has no transparent background (the demo would forward it to a second site)")
    if os.path.exists(out_dir) and os.listdir(out_dir):
        sys.exit("refusing: output folder must be new or empty: " + out_dir)
    os.makedirs(out_dir, exist_ok=True)
    from gradio_client import Client, handle_file
    t0 = time.time()
    c = Client("microsoft/TRELLIS.2", verbose=False)
    try:
        c.predict(api_name="/start_session")
    except Exception as e:                  # optional; extract_glb creates its folder itself
        print("start_session:", str(e)[:120])
    pre = c.predict(handle_file(src), api_name="/preprocess_image")
    print(f"[trellis] preprocessed in {time.time() - t0:.0f}s")
    c.predict(image=handle_file(pre), seed=int(opt["--seed"]), resolution=opt["--res"], api_name="/image_to_3d")
    print(f"[trellis] generated (res {opt['--res']}, seed {opt['--seed']}) at {time.time() - t0:.0f}s")
    glb, _ = c.predict(decimation_target=int(opt["--faces"]), texture_size=int(opt["--tex"]), api_name="/extract_glb")
    glb_path = glb if isinstance(glb, str) else (glb.get("value") or glb.get("path"))
    dst = os.path.join(out_dir, "model.glb")
    shutil.copyfile(glb_path, dst)
    shutil.copyfile(pre, os.path.join(out_dir, "input_preprocessed.png"))
    print(f"[trellis] GLB {os.path.getsize(dst) / 1e6:.1f} MB -> {dst} ({time.time() - t0:.0f}s total)")


if __name__ == "__main__":
    main()
