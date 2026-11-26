#!/bin/bash
# Usage: Tools/section_triptych.sh <tag> [prevDir] [newDir]
# Private per-section before/after sheets for the 7 video sections of Docs/VideoCoverageChecklist.md:
#   row 1: original video frame | previous build | newest build            (mascot visible)
#   row 2: original video frame | previous build bg | newest build bg      (mascot hidden = scenery only)
# -> Captures/sections/S<n>_triptych_<tag>.png + ALL_triptych_<tag>.png (row 1 of every section) + ALL_bg_triptych_<tag>.png.
# prevDir default Captures/stills_prev_r6 (round-6 build, captured 12:18 on 2026-11-26), newDir default Captures/stills.
# Reference frames: Reference/frames4k_720/ (1280x720 from the owner's 4K export). Captures/ is gitignored - these sheets
# contain reference pixels and never go to the public repo.
TAG="${1:-latest}"; PREV="${2:-Captures/stills_prev_r6}"; NEW="${3:-Captures/stills}"
ROOT=/c/Users/josia/thanksgiving
PY="/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe"
cd "$ROOT" || exit 1
mkdir -p Captures/sections
pick() { local d="$1"; shift; for f in "$@"; do [ -f "$d/$f" ] && { echo "$f"; return; }; done; }
ROWS=(
  "S1|f_00.50s|01_hall_start_16x9.png"
  "S2|f_03.00s|hero_16x9.png"
  "S3|f_05.00s|C1_front_tunnel_like_5s_16x9.png"
  "S4|f_06.75s|C4_front_window_like_7s_16x9.png 06_tunnel_lane_right_16x9.png"
  "S5|f_08.25s|C2_front_chambers_like_10s_16x9.png"
  "S6|f_11.00s|C5_front_chambers2_like_11s_16x9.png 08_sweep_16x9.png"
  "S7|f_14.50s|09_portal_16x9.png C3_front_portal_like_14s_16x9.png"
)
ALL=(); ALLBG=()
for row in "${ROWS[@]}"; do
  IFS='|' read -r S REF CANDS <<< "$row"
  R="Reference/frames4k_720/${REF}.png"
  U=$(pick "$NEW" $CANDS)
  if [ -z "$U" ] || [ ! -f "$PREV/$U" ]; then echo "$S: still missing in $NEW or $PREV ($CANDS)"; continue; fi
  BGP="$PREV/bg/$U"; BGN="$NEW/bg/$U"
  [ -f "$BGP" ] || BGP="$PREV/$U"; [ -f "$BGN" ] || BGN="$NEW/$U"
  echo "$S: $R | $PREV/$U | $NEW/$U (+ bg)"
  "$PY" -I Tools/contact_sheet.py "Captures/sections/${S}_triptych_${TAG}.png" 3 640 "$R" "$PREV/$U" "$NEW/$U" "$R" "$BGP" "$BGN" | tail -1
  ALL+=("$R" "$PREV/$U" "$NEW/$U"); ALLBG+=("$R" "$BGP" "$BGN")
done
"$PY" -I Tools/contact_sheet.py "Captures/sections/ALL_triptych_${TAG}.png" 3 420 "${ALL[@]}" | tail -1
"$PY" -I Tools/contact_sheet.py "Captures/sections/ALL_bg_triptych_${TAG}.png" 3 420 "${ALLBG[@]}" | tail -1
