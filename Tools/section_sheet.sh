#!/bin/bash
# Usage: Tools/section_sheet.sh <tag>
# Private per-section comparison sheets (LEFT original video frame | RIGHT Unity still) for the 7 video sections of
# Docs/VideoCoverageChecklist.md -> Captures/sections/S<n>_ref_vs_unity_<tag>.png + ALL_ref_vs_unity_<tag>.png
# (Captures/ is gitignored: these sheets contain reference pixels and never go to the public repo).
# Inputs: the 720p original frames in Reference/frames/ and the newest Captures/stills/ (full build or CaptureStillsBatch).
# Front-facing Unity stills (C*) are comparison angles only; gameplay always uses the rear camera.
TAG="${1:-latest}"
ROOT=/c/Users/josia/thanksgiving
PY="/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe"
cd "$ROOT" || exit 1
mkdir -p Captures/sections
pick() { for f in "$@"; do [ -f "Captures/stills/$f" ] && { echo "Captures/stills/$f"; return; }; done; }
ROWS=(
  "S1|f_000.50s|01_hall_start_16x9.png"
  "S2|f_003.00s|hero_16x9.png"
  "S3|f_005.00s|C1_front_tunnel_like_5s_16x9.png"
  "S4|f_006.75s|C4_front_window_like_7s_16x9.png 06_tunnel_lane_right_16x9.png"
  "S5|f_008.25s|C2_front_chambers_like_10s_16x9.png"
  "S6|f_011.00s|C5_front_chambers2_like_11s_16x9.png 08_sweep_16x9.png"
  "S7|f_014.50s|C3_front_portal_like_14s_16x9.png"
)
ALL=()
for row in "${ROWS[@]}"; do
  IFS='|' read -r S REF CANDS <<< "$row"
  U=$(pick $CANDS)
  if [ -z "$U" ]; then echo "$S: no Unity still found ($CANDS)"; continue; fi
  echo "$S: Reference/frames/$REF.png | $U"
  "$PY" -I Tools/contact_sheet.py "Captures/sections/${S}_ref_vs_unity_${TAG}.png" 2 960 "Reference/frames/${REF}.png" "$U" | tail -1
  ALL+=("Reference/frames/${REF}.png" "$U")
done
"$PY" -I Tools/contact_sheet.py "Captures/sections/ALL_ref_vs_unity_${TAG}.png" 2 640 "${ALL[@]}" | tail -1
