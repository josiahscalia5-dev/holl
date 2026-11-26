#!/bin/bash
# Usage: Tools/heavy_lock.sh <label> <command...>
# Serializes heavy Unity / Blender runs on this 4-thread, 7.7 GB laptop: one at a time, project-wide.
# Every Unity or Blender invocation (lead and agents) must go through this script (unity_run.sh and
# blender_run.sh already do). A lock whose holder process is gone, or older than 30 minutes, is treated as stale.
LOCK="C:/Users/josia/thanksgiving/Logs/heavy.lock"
LABEL="${1:-run}"; shift
mkdir -p "$(dirname "$LOCK")"
waited=0
until mkdir "$LOCK" 2>/dev/null; do
  holder=$(cat "$LOCK/pid" 2>/dev/null)
  age=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || date +%s) ))
  if { [ -n "$holder" ] && ! kill -0 "$holder" 2>/dev/null; } || [ "$age" -gt 1800 ]; then
    echo "[heavy-lock] removing stale lock ($(cat "$LOCK/label" 2>/dev/null), age ${age}s)"; rm -rf "$LOCK"; continue
  fi
  if [ $((waited % 60)) -eq 0 ]; then echo "[heavy-lock] '$LABEL' waiting for '$(cat "$LOCK/label" 2>/dev/null)' (${waited}s)"; fi
  sleep 5; waited=$((waited + 5))
done
echo $$ > "$LOCK/pid"; echo "$LABEL" > "$LOCK/label"
trap 'rm -rf "$LOCK"' EXIT INT TERM
"$@"
