#!/bin/bash
# Usage: Tools/after_wave.sh <workflow transcript dir> <agents in the wave> <tag> [before stills dir]
# LEAD helper (2026-11-26 18:16). Runs the lead integration automatically when a specialist wave ends - also when the Pro
# usage limit cuts the wave (no agent transcript written for IDLE_MIN minutes while no Unity / Blender runs) - so the
# build, stills, section sheets and the gameplay recording are ready when the usage window resets (they need no tokens):
#   wait -> cs_check (no build on compile errors) -> free-disk guard -> safe_build lead_<tag> -> Captures/stills_<tag>
#   -> section_triptych <tag> <before> stills_<tag> -> Play Mode autopilot recording -> review frames.
# Log: Logs/after_wave_<tag>.log. Never kills anything; every heavy run goes through heavy_lock (lead priority).
DIR="$1"; N="${2:-3}"; TAG="${3:-r8m}"; BEFORE="${4:-Captures/stills_r8}"; IDLE_MIN="${IDLE_MIN:-12}"
ROOT=/c/Users/josia/thanksgiving
UNITY="/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe"
cd "$ROOT" || exit 1
LOG="$ROOT/Logs/after_wave_${TAG}.log"
say() { echo "$(date +%H:%M:%S) $*" | tee -a "$LOG"; }
heavy_running() {
  # lead 84b218d4 2026-11-27: only a real Unity EDITOR counts - the Unity CLI MCP server (AppData/Local/Unity/bin/unity.exe mcp)
  # has the same image name and would keep this watcher waiting forever (same fix as heavy_lock.sh orphan()).
  powershell.exe -NoProfile -Command 'if (Get-Process -Name Unity -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*\Editor\Unity.exe" }) { exit 0 } else { exit 1 }' && return 0
  # lead 5190fd9a 2026-11-27 (owner: reconnect the Blender MCP): only a HEADLESS Blender (--background) counts - an open
  # Blender window running the MCP add-on (localhost:9876) is not a build job and must not stall the queue
  powershell.exe -NoProfile -Command 'if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "blender.exe" -and $_.CommandLine -match "--background" }) { exit 0 } else { exit 1 }' && return 0
  return 1
}
say "watching $DIR for $N agent results (idle limit ${IDLE_MIN} min)"
while true; do
  done_n=$(grep -c '"type":"result"' "$DIR/journal.jsonl" 2>/dev/null); done_n=${done_n:-0}
  if [ "$done_n" -ge "$N" ]; then say "wave finished ($done_n results)"; break; fi
  newest=$(ls -t "$DIR"/agent-*.jsonl 2>/dev/null | head -1)
  if [ -n "$newest" ]; then
    age=$(( $(date +%s) - $(stat -c %Y "$newest") ))
    if [ "$age" -gt $((IDLE_MIN * 60)) ] && ! heavy_running; then
      say "no agent activity for $((age / 60)) min and no Unity/Blender - wave treated as cut ($done_n/$N results)"; break
    fi
  fi
  sleep 60
done
while heavy_running; do sleep 30; done
bash Tools/cs_check.sh >> "$LOG" 2>&1; CS=$?
if [ $CS -eq 1 ]; then say "cs_check: compile errors - NO build (fix first, see the log)"; exit 2; fi
[ $CS -ne 0 ] && say "cs_check setup problem (exit $CS) - building anyway (Unity compiles itself)"
FREE=$(df -k /c | awk 'NR==2 {print $4}')
if [ "${FREE:-0}" -lt 1500000 ]; then say "only $((FREE / 1024)) MB free on C: - NO build"; exit 3; fi
say "safe_build lead_${TAG} ($((FREE / 1024)) MB free)"
bash Tools/safe_build.sh "lead_${TAG}" >> "$LOG" 2>&1; CODE=$?
say "safe_build lead_${TAG} exit=$CODE"
[ $CODE -ne 0 ] && exit $CODE
rm -rf "Captures/stills_${TAG}" && cp -r Captures/stills "Captures/stills_${TAG}"
bash Tools/section_triptych.sh "$TAG" "$BEFORE" "Captures/stills_${TAG}" >> "$LOG" 2>&1
say "sheets: Captures/sections/S1..S7_triptych_${TAG}.png (+ ALL_*)"
bash Tools/heavy_lock.sh "lead_play_${TAG}" "$UNITY" -batchmode -projectPath "C:/Users/josia/thanksgiving" -runTests \
  -testPlatform PlayMode -testFilter "BubbleWash.Tests.GameplayCaptureTests.A_RecordAutopilotRun" \
  -testResults "C:/Users/josia/thanksgiving/Captures/playmode/results_${TAG}.xml" \
  -logFile "C:/Users/josia/thanksgiving/Logs/lead_play_${TAG}.log" >> "$LOG" 2>&1
say "play mode exit=$? ($(grep -o 'result="[A-Za-z]*"' "Captures/playmode/results_${TAG}.xml" 2>/dev/null | head -1))"
if [ -f Captures/playmode/gameplay_autopilot_9x16.mp4 ]; then
  cp Captures/playmode/gameplay_autopilot_9x16.mp4 "Captures/playmode/gameplay_autopilot_9x16_${TAG}.mp4"
  bash Tools/review_recording.sh "Captures/playmode/gameplay_autopilot_9x16_${TAG}.mp4" "Captures/review_${TAG}" >> "$LOG" 2>&1
  say "recording: Captures/playmode/gameplay_autopilot_9x16_${TAG}.mp4, review frames Captures/review_${TAG}/"
fi
say "after_wave ${TAG} done"
