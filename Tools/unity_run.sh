#!/bin/bash
# Usage: Tools/unity_run.sh <Class.Method> [logname] [extra args...]
# Runs Unity in batchmode on this project and prints a compact summary (compile errors, [BWK] lines, exceptions).
METHOD="$1"; NAME="${2:-run}"; shift 2 2>/dev/null
LOG="C:/Users/josia/AppData/Local/Temp/claude/5d9ef3fae1e6adff/8f069e21-87bb-4ad0-a6be-d40e2e41c643/scratchpad/unity_${NAME}.log"
"/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe" -batchmode -projectPath "C:/Users/josia/thanksgiving" -executeMethod "$METHOD" -logFile "$LOG" "$@"
CODE=$?
echo "exit=$CODE log=$LOG"
grep -E "error CS[0-9]+|\[BWK\]|Exception|Shader error|error:|Aborting batchmode|executeMethod" "$LOG" | grep -v "^UnityEngine\.\|(Filename:" | sort -u | head -${MAXLINES:-60} | cut -c1-260
