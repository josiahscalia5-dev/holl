#!/bin/bash
# Usage: Tools/safe_build.sh <logname>
# LEAD ONLY. Full rebuild (SceneBuilder.BuildAllBatch: setup, textures, materials, model remap, animator, scene, stills,
# hero comparison) under the heavy-process lock. Before Unity starts, the saved scene and the Generated level meshes are
# copied to Builds/_last_good_scene/ (gitignored); if the build fails they are put back inside the same lock, so agent
# previews (which load the saved scene) never see a half-built level.
NAME="${1:-build}"
ROOT=/c/Users/josia/thanksgiving
if [ "$2" != "--inner" ]; then
  bash "$ROOT/Tools/heavy_lock.sh" "unity:$NAME" bash "$ROOT/Tools/safe_build.sh" "$NAME" --inner
  CODE=$?
  LOG="$ROOT/Logs/unity_${NAME}.log"
  echo "exit=$CODE log=$LOG"
  grep -E "error CS[0-9]+|\[BWK\]|Exception|Shader error|error:|Aborting batchmode|executeMethod|safe-build" "$LOG" \
    | grep -v "^UnityEngine\.\|(Filename:\|(info) property" | sort -u | head -${MAXLINES:-80} | cut -c1-260
  exit $CODE
fi

BK="$ROOT/Builds/_last_good_scene"
GEN="$ROOT/Assets/BubbleWashKingdom/Generated"
SCENE="$ROOT/Assets/BubbleWashKingdom/Scenes/Level01_RainbowRush.unity"
LOG="C:/Users/josia/thanksgiving/Logs/unity_${NAME}.log"
rm -rf "$BK" && mkdir -p "$BK"
cp -r "$GEN" "$BK/Generated" && cp "$SCENE" "$BK/" || { echo "[safe-build] backup failed - not building"; exit 3; }
"/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe" -batchmode -projectPath "C:/Users/josia/thanksgiving" \
  -executeMethod BubbleWash.EditorTools.SceneBuilder.BuildAllBatch -logFile "$LOG"
CODE=$?
if [ $CODE -ne 0 ]; then
  echo "[safe-build] build failed (exit $CODE) - restoring the previous scene and Generated meshes" | tee -a "$LOG"
  rm -rf "$GEN" && cp -r "$BK/Generated" "$GEN" && cp "$BK/Level01_RainbowRush.unity" "$SCENE"
fi
exit $CODE
