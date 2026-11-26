#!/bin/bash
# Usage: Tools/review_recording.sh <video.mp4> <outDir> [stepSeconds=0.5] [openingFrames=12] [endingFrames=14]
# Lead review of a gameplay recording (owner 2026-11-26: opening camera, 26-29 s camera movement, finishing sequence):
# extracts frames with Blender's bundled FFmpeg (no ffmpeg on this PC; runs through Tools/heavy_lock.sh) and writes
#   <outDir>/frames/f_SS.SSs.png, <outDir>/opening.png (first frames) and <outDir>/ending.png (last frames).
# Output belongs in Captures/ (gitignored, private).
VIDEO="$1"; OUT="$2"; STEP="${3:-0.5}"; NOPEN="${4:-12}"; NEND="${5:-14}"
ROOT=/c/Users/josia/thanksgiving
PY="/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe"
BL="/c/Users/josia/Blender/blender-5.3.0-windows-x64/blender.exe"
[ -f "$VIDEO" ] || { echo "no video: $VIDEO"; exit 1; }
cd "$ROOT" || exit 1
mkdir -p "$OUT/frames"
rm -f "$OUT"/frames/f_*.png
bash Tools/heavy_lock.sh lead_blender_review "$BL" --background --factory-startup --python Tools/extract_frames_blender.py -- \
  "$(cygpath -am "$VIDEO")" "$(cygpath -am "$OUT/frames")" "$STEP" 640 > "$OUT/extract.log" 2>&1
grep "\[frames\]" "$OUT/extract.log" | head -1
mapfile -t ALL < <(ls "$OUT"/frames/f_*.png | sort)
N=${#ALL[@]}
[ "$N" -gt 0 ] || { echo "no frames extracted (see $OUT/extract.log)"; exit 1; }
OPEN=("${ALL[@]:0:$NOPEN}")
S=$(( N > NEND ? N - NEND : 0 ))
END=("${ALL[@]:$S}")
"$PY" -I Tools/contact_sheet.py "$OUT/opening.png" 6 240 "${OPEN[@]}" | tail -1
"$PY" -I Tools/contact_sheet.py "$OUT/ending.png" 7 200 "${END[@]}" | tail -1
echo "frames=$N opening=$(basename "${OPEN[0]}")..$(basename "${OPEN[-1]}") ending=$(basename "${END[0]}")..$(basename "${END[-1]}")"
