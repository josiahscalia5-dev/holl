#!/bin/bash
# Usage: Tools/unity_run.sh <Class.Method> [logname] [extra args...]
# Runs Unity in batchmode on this project under the heavy-process lock (never two Unity instances at once) and prints a
# compact summary (compile errors, [BWK] lines, exceptions). Agents: only BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch.
# Agent previews (AgentPreviewBatch with just -bwkOut) are BATCHED: every request waiting for the lock is served by one
# shared Unity run (Tools/preview_batch.sh) that includes all agents' current changes and enables each requester's
# preview gates; each requester still gets the images in its own -bwkOut folder and the log under its own name.
# When the run wrote a fresh hero side-by-side it also prints objective reference-vs-ours colour metrics
# (Tools/img_stats.py), and it always ends with the lead's current directives (Captures/agents/LEAD_DIRECTIVES.md).
METHOD="$1"; NAME="${2:-run}"; shift 2 2>/dev/null
ROOT=/c/Users/josia/thanksgiving
LOG="C:/Users/josia/thanksgiving/Logs/unity_${NAME}.log"
OUT=""; prev=""
for a in "$@"; do [ "$prev" = "-bwkOut" ] && OUT="$a"; prev="$a"; done
STAMP=$(date +%s)
if [[ "$METHOD" == *CaptureTools.AgentPreviewBatch ]] && [ -n "$OUT" ] && [ $# -eq 2 ]; then
  Q="$ROOT/Logs/preview_queue"; mkdir -p "$Q"
  REQ="$Q/$(date +%s%N)_$$"
  printf '%s\n%s\n' "$OUT" "$NAME" > "$REQ.req"
  bash $ROOT/Tools/heavy_lock.sh "unity:$NAME" bash "$ROOT/Tools/preview_batch.sh" "$REQ"
  CODE=$(cat "$REQ.done" 2>/dev/null || echo 1)
  rm -f "$REQ.req" "$REQ.done"
else
  bash $ROOT/Tools/heavy_lock.sh "unity:$NAME" "/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe" -batchmode -projectPath "C:/Users/josia/thanksgiving" -executeMethod "$METHOD" -logFile "$LOG" "$@"
  CODE=$?
fi
echo "exit=$CODE log=$LOG"
grep -E "error CS[0-9]+|\[BWK\]|Exception|Shader error|error:|Aborting batchmode|executeMethod|preview-batch" "$LOG" | grep -v "^UnityEngine\.\|(Filename:\|(info) property" | sort -u | head -${MAXLINES:-60} | cut -c1-260
CMP="$ROOT/${OUT:-Captures/compare}/hero_vs_reference_9x16.png"
case "$OUT" in /*|?:*) CMP="$OUT/hero_vs_reference_9x16.png";; esac
if [ -f "$CMP" ] && [ "$(stat -c %Y "$CMP")" -ge "$STAMP" ]; then
  echo "--- objective metrics, LEFT reference vs RIGHT ours (Tools/img_stats.py $CMP):"
  "/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I "$ROOT/Tools/img_stats.py" "$CMP" 2>&1 | head -20
fi
if [ -f "$ROOT/Captures/agents/LEAD_DIRECTIVES.md" ]; then
  echo "--- lead directives from the main session (Captures/agents/LEAD_DIRECTIVES.md, updated $(date -r "$ROOT/Captures/agents/LEAD_DIRECTIVES.md" '+%H:%M')):"
  cat "$ROOT/Captures/agents/LEAD_DIRECTIVES.md"
fi
exit $CODE
