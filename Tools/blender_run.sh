#!/bin/bash
# Usage: Tools/blender_run.sh Tools/Blender/scripts/<script>.py [logname]
# Headless Blender under the heavy-process lock; log in Logs/blender_<logname>.log; prints errors + CHECK/EXPORTED lines.
SCRIPT="$1"; NAME="${2:-$(basename "$SCRIPT" .py)}"
LOG="C:/Users/josia/thanksgiving/Logs/blender_${NAME}.log"
cd /c/Users/josia/thanksgiving
bash Tools/heavy_lock.sh "blender:$NAME" "/c/Users/josia/Blender/blender-5.3.0-windows-x64/blender.exe" --background --factory-startup --python "$SCRIPT" > "$LOG" 2>&1
CODE=$?
echo "exit=$CODE log=$LOG"
grep -E "Traceback|Error|error:|line [0-9]+, in|CHECK|EXPORTED|PREVIEW|VERIFY|SHELLS|DONE" "$LOG" | head -${MAXLINES:-60} | cut -c1-240
