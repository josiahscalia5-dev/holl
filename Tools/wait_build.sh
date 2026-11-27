#!/bin/bash
# Usage: Tools/wait_build.sh <tag> [max_minutes]
# LEAD helper (2026-11-27 16:45, lead 15a68124). Specialists run this before their FIRST file edit of a pass that starts
# while the lead's after_wave build (Logs/after_wave_<tag>.log) is still running, so no half-made edit leaks into the
# lead build. Returns when that log shows the build finished (or was skipped). Exit 0 = finished; exit 1 = still running
# after max_minutes (default 9, so a 10-minute Bash timeout never cuts it) -> run it again.
TAG="$1"; MAX="${2:-9}"
LOG=/c/Users/josia/thanksgiving/Logs/after_wave_${TAG}.log
[ -z "$TAG" ] && { echo "usage: Tools/wait_build.sh <tag> [max_minutes]"; exit 2; }
END=$(( $(date +%s) + MAX * 60 ))
while [ "$(date +%s)" -lt "$END" ]; do
  if grep -qE "safe_build lead_${TAG} exit=|NO build|after_wave ${TAG} done" "$LOG" 2>/dev/null; then
    echo "build finished: $(grep -E "safe_build lead_${TAG} exit=|NO build" "$LOG" | tail -1)"; exit 0
  fi
  sleep 20
done
echo "$(date +%H:%M:%S) build lead_${TAG} still running after ${MAX} min - run Tools/wait_build.sh ${TAG} again"; exit 1
