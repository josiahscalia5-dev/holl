#!/bin/bash
# Usage: bash Tools/owner_package.sh <newTag> <prevTag> "<prevLabel>" "<newLabel>"
# Lead 84b218d4 2026-11-27: builds the owner's S2 verification package from finished stills / Play Mode review frames, with NO
# tokens (System.Drawing + one Unity batch run through heavy_lock): OWNER_S2_compare_<tag>.png (reference | previous | newest,
# mascot visible / hidden), OWNER_S2_details_<tag>.png, OWNER_portrait_gameplay_<tag>.png, the extra-angle + CLAY 3D proof
# (Captures/proof_<tag>/ -> OWNER_S2_3D_proof_<tag>.png) and the landmark check. Log: Logs/owner_package_<tag>.log
T="$1"; P="${2:-s2p9a}"; PL="${3:-PREVIOUS UNITY $P}"; NL="${4:-NEWEST UNITY $T}"
cd /c/Users/josia/thanksgiving || exit 1
L=Logs/owner_package_$T.log
echo "$(date +%H:%M:%S) owner package $T (prev $P)" >> $L
[ -f "Captures/stills_$T/R2_rear_S2_like_3s_16x9.png" ] || { echo "$(date +%H:%M:%S) no stills_$T - stop" >> $L; exit 2; }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\josia\\thanksgiving\\Captures\\agents\\_shared\\owner_sheets.ps1" \
  -PrevTag "$P" -PrevLabel "$PL" -NewTag "$T" -NewLabel "$NL" -Suffix "$T" >> $L 2>&1
bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.S2ProofViewsBatch lead_proof_$T -bwkOut Captures/proof_$T >> $L 2>&1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\josia\\thanksgiving\\Captures\\agents\\_shared\\proof_sheet.ps1" \
  -Dir "C:\\Users\\josia\\thanksgiving\\Captures\\proof_$T" -Out "C:\\Users\\josia\\thanksgiving\\Captures\\sections\\OWNER_S2_3D_proof_$T.png" \
  -Label "build $T" >> $L 2>&1
"/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/landmark_check.py "Captures/stills_$P" "Captures/stills_$T" \
  > "Captures/stills_$T/landmark_vs_$P.txt" 2>&1
echo "$(date +%H:%M:%S) owner package $T done" >> $L
