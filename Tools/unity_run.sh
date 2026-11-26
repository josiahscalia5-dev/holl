#!/bin/bash
# Usage: Tools/unity_run.sh <Class.Method> [logname] [extra args...]
# Runs Unity in batchmode on this project under the heavy-process lock (never two Unity instances at once) and prints a
# compact summary (compile errors, [BWK] lines, exceptions). Agents: only BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch.
METHOD="$1"; NAME="${2:-run}"; shift 2 2>/dev/null
LOG="C:/Users/josia/thanksgiving/Logs/unity_${NAME}.log"
bash /c/Users/josia/thanksgiving/Tools/heavy_lock.sh "unity:$NAME" "/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe" -batchmode -projectPath "C:/Users/josia/thanksgiving" -executeMethod "$METHOD" -logFile "$LOG" "$@"
CODE=$?
echo "exit=$CODE log=$LOG"
grep -E "error CS[0-9]+|\[BWK\]|Exception|Shader error|error:|Aborting batchmode|executeMethod" "$LOG" | grep -v "^UnityEngine\.\|(Filename:\|(info) property" | sort -u | head -${MAXLINES:-60} | cut -c1-260
