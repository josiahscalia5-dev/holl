#!/bin/bash
# Usage: Tools/unity_run.sh <Class.Method> [logname] [extra args...]
# Runs Unity in batchmode on this project under the heavy-process lock (never two Unity instances at once) and prints a
# compact summary (compile errors, [BWK] lines, exceptions). Agents: only BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch.
# When the run wrote a fresh hero side-by-side it also prints objective reference-vs-ours colour metrics
# (Tools/img_stats.py), and it always ends with the lead's current directives (Captures/agents/LEAD_DIRECTIVES.md),
# so specialists get the lead's feedback on every run.
METHOD="$1"; NAME="${2:-run}"; shift 2 2>/dev/null
ROOT=/c/Users/josia/thanksgiving
LOG="C:/Users/josia/thanksgiving/Logs/unity_${NAME}.log"
OUT=""; prev=""
for a in "$@"; do [ "$prev" = "-bwkOut" ] && OUT="$a"; prev="$a"; done
STAMP=$(date +%s)
bash $ROOT/Tools/heavy_lock.sh "unity:$NAME" "/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe" -batchmode -projectPath "C:/Users/josia/thanksgiving" -executeMethod "$METHOD" -logFile "$LOG" "$@"
CODE=$?
echo "exit=$CODE log=$LOG"
grep -E "error CS[0-9]+|\[BWK\]|Exception|Shader error|error:|Aborting batchmode|executeMethod" "$LOG" | grep -v "^UnityEngine\.\|(Filename:\|(info) property" | sort -u | head -${MAXLINES:-60} | cut -c1-260
CMP="$ROOT/${OUT:-Captures/compare}/hero_vs_reference_9x16.png"
if [ -f "$CMP" ] && [ "$(stat -c %Y "$CMP")" -ge "$STAMP" ]; then
  echo "--- objective metrics, LEFT reference vs RIGHT ours (Tools/img_stats.py $CMP):"
  "/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I "$ROOT/Tools/img_stats.py" "$CMP" 2>&1 | head -20
fi
if [ -f "$ROOT/Captures/agents/LEAD_DIRECTIVES.md" ]; then
  echo "--- lead directives from the main session (Captures/agents/LEAD_DIRECTIVES.md, updated $(date -r "$ROOT/Captures/agents/LEAD_DIRECTIVES.md" '+%H:%M')):"
  cat "$ROOT/Captures/agents/LEAD_DIRECTIVES.md"
fi
exit $CODE
