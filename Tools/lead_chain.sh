#!/bin/bash
# Usage: bash Tools/lead_chain.sh <tag> <before stills dir>   (lead cd16e551 2026-11-27: cs_check -> safe_build lead_<tag> -> Captures/stills_<tag>
#   -> section_triptych -> Play Mode autopilot recording (portrait) -> review frames -> landmark_check vs <before>; log Logs/lead_cd16e551.log)
T="$1"; BEFORE="$2"; cd /c/Users/josia/thanksgiving || exit 1
UNITY="/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe"; L=Logs/lead_cd16e551.log
echo "$(date +%H:%M:%S) lead chain $T: cs_check + safe_build lead_$T" >> $L
bash Tools/cs_check.sh >> $L 2>&1; CS=$?
if [ $CS -eq 1 ]; then echo "$(date +%H:%M:%S) $T: COMPILE ERRORS - no build" >> $L; echo "COMPILE ERRORS"; exit 2; fi
bash Tools/safe_build.sh lead_$T >> $L 2>&1; CODE=$?
echo "$(date +%H:%M:%S) safe_build lead_$T exit=$CODE" >> $L
[ $CODE -ne 0 ] && { echo "BUILD FAILED $CODE"; exit $CODE; }
rm -rf Captures/stills_$T && cp -r Captures/stills Captures/stills_$T
bash Tools/section_triptych.sh $T "$BEFORE" Captures/stills_$T >> $L 2>&1
bash Tools/heavy_lock.sh lead_play_$T "$UNITY" -batchmode -projectPath "C:/Users/josia/thanksgiving" -runTests -testPlatform PlayMode \
  -testFilter "BubbleWash.Tests.GameplayCaptureTests.A_RecordAutopilotRun" -testResults "C:/Users/josia/thanksgiving/Captures/playmode/results_$T.xml" \
  -logFile "C:/Users/josia/thanksgiving/Logs/lead_play_$T.log" >> $L 2>&1
echo "$(date +%H:%M:%S) play $T exit=$? $(grep -o 'result="[A-Za-z]*"' Captures/playmode/results_$T.xml | head -1)" >> $L
cp Captures/playmode/run_summary.txt Captures/playmode/run_summary_$T.txt
cp Captures/playmode/gameplay_autopilot_9x16.mp4 Captures/playmode/gameplay_autopilot_9x16_$T.mp4 && bash Tools/review_recording.sh Captures/playmode/gameplay_autopilot_9x16_$T.mp4 Captures/review_$T >> $L 2>&1
"/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/landmark_check.py "$BEFORE" Captures/stills_$T > Captures/stills_$T/landmark_vs_before.txt 2>&1
echo "$(date +%H:%M:%S) $T chain done" >> $L
tail -3 $L; cat Captures/playmode/run_summary_$T.txt | tr '\n' ' '; echo; head -8 Captures/stills_$T/landmark_vs_before.txt
