#!/bin/bash
# Usage: bash Tools/owner_package.sh <newTag> <prevTag> "<prevLabel>" "<newLabel>"
# Lead 84b218d4 2026-11-27: builds the owner's S2 verification package from finished stills / Play Mode review frames, with NO
# tokens (System.Drawing + one Unity batch run through heavy_lock): OWNER_S2_compare_<tag>.png (reference | previous | newest,
# mascot visible / hidden), OWNER_S2_details_<tag>.png, OWNER_portrait_gameplay_<tag>.png and the landmark check.
# Lead ffbcca5a 12:35 (owner 12:30 "prove it is real 3D"): CaptureTools.S2ProofViewsBatch -> Captures/proof_<tag>/ (5 angles with /
# without the mascot, NEUTRAL clay, mascot alone in colour + clay, geometry_audit.txt / .csv) -> three sheets via proof_grid.ps1:
# OWNER_S2_5angle_proof_<tag>.png, OWNER_S2_clay_proof_<tag>.png, OWNER_S2_mascot_alone_<tag>.png. Log: Logs/owner_package_<tag>.log
T="$1"; P="${2:-s2p9a}"; PL="${3:-PREVIOUS UNITY $P}"; NL="${4:-NEWEST UNITY $T}"
cd /c/Users/josia/thanksgiving || exit 1
L=Logs/owner_package_$T.log
echo "$(date +%H:%M:%S) owner package $T (prev $P)" >> $L
[ -f "Captures/stills_$T/R2_rear_S2_like_3s_16x9.png" ] || { echo "$(date +%H:%M:%S) no stills_$T - stop" >> $L; exit 2; }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\josia\\thanksgiving\\Captures\\agents\\_shared\\owner_sheets.ps1" \
  -PrevTag "$P" -PrevLabel "$PL" -NewTag "$T" -NewLabel "$NL" -Suffix "$T" >> $L 2>&1
bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.S2ProofViewsBatch lead_proof_$T -bwkOut Captures/proof_$T >> $L 2>&1
D="C:\\Users\\josia\\thanksgiving\\Captures\\proof_$T"; S="C:\\Users\\josia\\thanksgiving\\Captures\\sections"
G="C:\\Users\\josia\\thanksgiving\\Captures\\agents\\_shared\\proof_grid.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$G" -Dir "$D" -Out "$S\\OWNER_S2_5angle_proof_$T.png" \
  -Title "S2 REAL 3D PROOF (Unity build $T): the same scene at the washing-machine door from 5 camera angles, rendered live by Unity" \
  -Sub "Row 1: mascot visible.  Row 2: the same cameras with the mascot hidden - he is a separate rigged, animated character, not part of the scenery." \
  -Cells "A_matched_R2.png|A  matched gameplay-rear camera;B_high_rear_right.png|B  high rear view;C_side_right_low.png|C  side view;D_ahead_looking_back.png|D  inside the door, looking back;E_hall_wide_from_behind.png|E  wide environment view;A_matched_R2_nomascot.png|A  mascot hidden;B_high_rear_right_nomascot.png|B  mascot hidden;C_side_right_low_nomascot.png|C  mascot hidden;D_ahead_looking_back_nomascot.png|D  mascot hidden;E_hall_wide_from_behind_nomascot.png|E  mascot hidden" >> $L 2>&1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$G" -Dir "$D" -Out "$S\\OWNER_S2_clay_proof_$T.png" \
  -Title "S2 CLAY PROOF (Unity build $T): the same 5 cameras, EVERY material plain grey, coloured lights / glow / grading off, one white light" \
  -Sub "What remains is modelled 3D geometry. Camera-facing sprites (tiny splash drops, sparkles, small floating bubbles) are hidden here and listed in geometry_audit.txt." \
  -Cells "A_matched_R2_clay.png|A  CLAY matched camera;B_high_rear_right_clay.png|B  CLAY high rear;C_side_right_low_clay.png|C  CLAY side;D_ahead_looking_back_clay.png|D  CLAY inside, looking back;E_hall_wide_from_behind_clay.png|E  CLAY wide" >> $L 2>&1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$G" -Dir "$D" -Out "$S\\OWNER_S2_mascot_alone_$T.png" -Cols 4 \
  -Title "MASCOT ALONE (Unity build $T): the in-game mascot with everything else hidden - a separate skinned, rigged, animated 3D character" \
  -Sub "Row 1: his game materials (lit by the scene's lights at the door).  Row 2: the same views in plain grey clay." \
  -Cells "M1_mascot_rear.png|rear;M2_mascot_side_right.png|side;M3_mascot_front.png|front;M4_mascot_three_quarter.png|three-quarter;M1_mascot_rear_clay.png|rear CLAY;M2_mascot_side_right_clay.png|side CLAY;M3_mascot_front_clay.png|front CLAY;M4_mascot_three_quarter_clay.png|three-quarter CLAY" >> $L 2>&1
"/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/landmark_check.py "Captures/stills_$P" "Captures/stills_$T" \
  > "Captures/stills_$T/landmark_vs_$P.txt" 2>&1
echo "$(date +%H:%M:%S) owner package $T done" >> $L
