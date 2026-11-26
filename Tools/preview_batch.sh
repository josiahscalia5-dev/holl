#!/bin/bash
# Batches agent previews (called by Tools/unity_run.sh for AgentPreviewBatch, already holding the heavy lock).
# Every waiting agent preview request is served by ONE Unity run instead of one run each:
#   - if this request was already served by a run that started after it was queued, exit at once;
#   - otherwise take every pending request, render once with all their domains' preview gates enabled
#     (-bwkOut path contains each "agents/<domain>"), then give each requester the shared images in its own -bwkOut
#     folder and the shared log as its own Logs/unity_<name>.log.
# Request file <id>.req = line 1 -bwkOut folder, line 2 log name; <id>.done = exit code of the run that served it.
REQ="$1"
ROOT=/c/Users/josia/thanksgiving
Q="${PB_QUEUE:-$ROOT/Logs/preview_queue}"
UNITY="${PB_UNITY:-/c/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Unity.exe}"
[ -f "$REQ.done" ] && exit 0

now=$(date +%s)
reqs=(); tags=()
for r in "$Q"/*.req; do
  [ -f "$r" ] || continue
  base="${r%.req}"
  [ -f "$base.done" ] && continue
  if [ $((now - $(stat -c %Y "$r"))) -gt 2700 ] && [ "$base" != "$REQ" ]; then rm -f "$r"; continue; fi   # abandoned
  reqs+=("$base")
  t="agents/$(basename "$(sed -n 1p "$r" | tr -d '\r')")"
  case " ${tags[*]} " in *" $t "*) ;; *) tags+=("$t");; esac
done
[ ${#reqs[@]} -eq 0 ] && reqs=("$REQ")

joined=$(IFS=_; echo "${tags[*]}")
SHARED="Captures/agents/_batch/${joined:-agents/preview}"
SHLOG="$ROOT/Logs/unity_batch_$(date +%H%M%S).log"
rm -rf "$ROOT/$SHARED" && mkdir -p "$ROOT/$SHARED"
names=""; for b in "${reqs[@]}"; do names="$names $(sed -n 2p "$b.req" | tr -d '\r')"; done
echo "[preview-batch] one Unity run serves ${#reqs[@]} request(s):$names -> $SHARED"
"$UNITY" -batchmode -projectPath "C:/Users/josia/thanksgiving" -executeMethod BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch \
  -logFile "$SHLOG" -bwkOut "$SHARED"
CODE=$?
echo "[preview-batch] served${names} with one run (exit $CODE)" >> "$SHLOG"

for b in "${reqs[@]}"; do
  out=$(sed -n 1p "$b.req" | tr -d '\r'); name=$(sed -n 2p "$b.req" | tr -d '\r')
  case "$out" in /*|?:*) dest="$out";; *) dest="$ROOT/$out";; esac
  mkdir -p "$dest"
  cp -f "$ROOT/$SHARED"/*.png "$dest"/ 2>/dev/null
  cp -f "$SHLOG" "$ROOT/Logs/unity_${name}.log"
  echo "$CODE" > "$b.done"
done
exit $CODE
