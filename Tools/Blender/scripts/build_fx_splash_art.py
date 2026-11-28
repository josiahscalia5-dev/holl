"""Bubble Wash Kingdom - S2 ART PASS milk splash meshes (lead 470ca906, 2026-11-27; owner 23:36 "beautiful natural water
splashes", 23:33 "transform the existing Unity scene"). The skeleton (fx_splash_art_skel.py: lacy lip beside each sole, a crown
of branching fingers with round bulb tips, wake tendrils + splats on the water, flying beads, clear bubbles) becomes ONE metaball
surface per side and frame (organic merged milk, like a real milk crown), decimated to a mobile budget, plus ico-sphere beads
(milk, submesh 0) and clear water bubbles (submesh 1). Written as .bwkm (S2v1TestScene.ReadBwkm format) in RUNNER-LOCAL Unity
coordinates relative to each side's pivot, FRAMES frames per side for the game's SplashCrowns flipbook (12 fps loop).
Run: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_splash_art.py fx_splash_art
Env: BWK_SPLASH_OUT (dir), BWK_SPLASH_RES (metaball cell m, 0.009), BWK_SPLASH_TRIS (crown tris per side + frame, 7000).
Output (gitignored work dir): Tools/Blender/work/s2art/splash/{L,R}_f<k>.bwkm + manifest.json.
"""
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import fx_splash_art_skel as S  # noqa: E402

ROOT = "C:/Users/josia/thanksgiving"
OUT = os.environ.get("BWK_SPLASH_OUT", ROOT + "/Tools/Blender/work/s2art/splash")
RES = float(os.environ.get("BWK_SPLASH_RES", "0.009"))
TRIS = int(os.environ.get("BWK_SPLASH_TRIS", "7000"))


def metaball_tris(balls, name):
    """Polygonize the metaball skeleton, decimate to TRIS, return (verts (n,3), tris (m,3))."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution = RES
    mb.render_resolution = RES
    mb.threshold = 0.6
    for (x, y, z, r) in balls:
        el = mb.elements.new()
        el.co = (x, y, z)
        el.radius = r
        el.stiffness = 2.0
    ob = bpy.data.objects.new(name, mb)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    raw = sum(len(p.vertices) - 2 for p in me.polygons)
    mo = bpy.data.objects.new(name + "_m", me)
    bpy.context.scene.collection.objects.link(mo)
    bpy.data.objects.remove(ob)
    if raw > TRIS:
        dec = mo.modifiers.new("dec", "DECIMATE")
        dec.decimate_type = "COLLAPSE"
        dec.ratio = TRIS / float(raw)
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(mo.evaluated_get(dg))
    else:
        me2 = me
    bm = bmesh.new()
    bm.from_mesh(me2)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    v = np.array([vv.co[:] for vv in bm.verts], np.float64)
    t = np.array([[l.vert.index for l in f.loops] for f in bm.faces], np.int64)
    bm.free()
    bpy.data.objects.remove(mo)
    print(f"[splash] {name}: {len(balls)} balls -> {raw} raw tris -> {len(t)} tris")
    return v, t


def ico(center, r, subdiv):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    v = np.array([vv.co[:] for vv in bm.verts], np.float64) + np.asarray(center, np.float64)
    bm.verts.ensure_lookup_table()
    t = np.array([[l.vert.index for l in f.loops] for f in bm.faces], np.int64)
    bm.free()
    return v, t


def vertex_normals(v, t):
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])     # area weighted
    n = np.zeros_like(v)
    for k in range(3):
        np.add.at(n, t[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-12)


def write_bwkm(path, v, nrm, subs):
    with open(path, "wb") as f:
        f.write(struct.pack("<4siii", b"BWKM", 1, len(v), 0))
        f.write(v.astype("<f4").tobytes())
        f.write(nrm.astype("<f4").tobytes())
        f.write(struct.pack("<i", len(subs)))
        for mat, tri in subs:
            idx = tri.astype("<i4").reshape(-1)
            f.write(struct.pack("<ii", mat, len(idx)))
            f.write(idx.tobytes())


def main():
    os.makedirs(OUT, exist_ok=True)
    fr = S.all_frames()
    man = {"frames": S.FRAMES, "res": RES, "tris_target": TRIS, "coords": "runner-local Unity (x right, y up, z forward) minus pivot",
           "submeshes": ["milk (crown + beads)", "clear water bubbles"], "L": [], "R": [], "tris": {}}
    for key in ("L", "R"):
        piv = np.asarray(fr["pivot_" + key], np.float64)
        man["pivot_" + key] = [round(float(c), 5) for c in piv]
        for k, (balls, drops, bubbles) in enumerate(fr[key]):
            v, t = metaball_tris(balls, f"Splash{key}{k}")
            vs, ts = [v], [t]
            off = len(v)
            for (x, y, z, r) in drops:
                dv, dt = ico((x, y, z), r, 2 if r >= 0.016 else 1)
                vs.append(dv); ts.append(dt + off); off += len(dv)
            milk_t = np.concatenate(ts)
            bv, bt = [], []
            for (x, y, z, r) in bubbles:
                dv, dt = ico((x, y, z), r, 2)
                bv.append(dv); bt.append(dt + off); off += len(dv)
            allv = np.concatenate(vs + bv)
            nrm = vertex_normals(allv, np.concatenate([milk_t] + bt) if bt else milk_t)
            subs = [(0, milk_t)] + ([(1, np.concatenate(bt))] if bt else [])
            name = f"{key}_f{k}.bwkm"
            write_bwkm(os.path.join(OUT, name), allv - piv, nrm, subs)
            man[key].append(name)
            man["tris"][name] = int(sum(len(s[1]) for s in subs))
            lo, hi = (allv - piv).min(0), (allv - piv).max(0)
            print(f"[splash] wrote {name}: {len(allv)} verts, {man['tris'][name]} tris, bounds {np.round(lo, 3)} .. {np.round(hi, 3)}")
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    print("[splash] done ->", OUT)


main()
