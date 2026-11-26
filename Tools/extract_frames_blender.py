"""Extract still frames from a video with Blender's bundled FFmpeg (this PC has no ffmpeg on PATH).

Usage (headless, through the heavy lock):
  bash Tools/heavy_lock.sh blender:frames "C:/Users/josia/Blender/blender-5.3.0-windows-x64/blender.exe" --background \
      --factory-startup --python Tools/extract_frames_blender.py -- VIDEO OUTDIR STEP_SECONDS [MAX_HEIGHT]
Writes OUTDIR/f_SS.SSs.png every STEP_SECONDS and prints the video's size, fps and duration.
Output must go under Reference/ (private, gitignored): frames of the owner's video never go into tracked folders.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
video, out_dir, step = argv[0], argv[1], float(argv[2])
max_h = int(argv[3]) if len(argv) > 3 else 0
os.makedirs(out_dir, exist_ok=True)

clip = bpy.data.movieclips.load(video)
w, h = clip.size
fps = clip.fps or 24.0
n = clip.frame_duration
print(f"[frames] {video}: {w}x{h}, {fps:.3f} fps, {n} frames, {n / fps:.2f} s")

scene = bpy.context.scene
scene.sequence_editor_create()
strip = scene.sequence_editor.strips.new_movie("v", video, 1, 1)
scene.render.fps = int(round(fps))
scene.render.fps_base = scene.render.fps / fps
scale = 1.0 if not max_h or h <= max_h else max_h / h
scene.render.resolution_x = int(round(w * scale))
scene.render.resolution_y = int(round(h * scale))
scene.render.resolution_percentage = 100
strip.transform.scale_x = strip.transform.scale_y = scale   # shrink the whole frame (else the strip is centre-cropped)
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.view_settings.view_transform = "Standard"
scene.render.use_sequencer = True
scene.frame_start, scene.frame_end = 1, n

t = 0.0
while True:
    f = 1 + int(round(t * fps))
    if f > n:
        break
    scene.frame_set(f)
    scene.render.filepath = os.path.join(out_dir, f"f_{t:05.2f}s.png")
    bpy.ops.render.render(write_still=True)
    t = round(t + step, 4)
print(f"[frames] wrote frames to {out_dir}")
