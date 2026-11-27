#!/bin/bash
# Usage: Tools/heavy_lock.sh <label> <command...>
# Serializes heavy Unity / Blender runs on this 4-thread, 7.7 GB laptop: one at a time, project-wide.
# Every Unity or Blender invocation (lead and agents) must go through this script (unity_run.sh, blender_run.sh and
# safe_build.sh already do). A lock whose holder process is gone, or older than 30 minutes, is treated as stale.
# Lead priority: a waiting run whose label contains "lead" (lead integration builds / camera tests) is served next:
# it registers in Logs/heavy.priority and other waiters do not take a free lock while that lead process is alive.
LOCK="C:/Users/josia/thanksgiving/Logs/heavy.lock"
PRIO="C:/Users/josia/thanksgiving/Logs/heavy.priority"
LABEL="${1:-run}"; shift
mkdir -p "$(dirname "$LOCK")"
lead=0; case "$LABEL" in *lead*) lead=1; echo $$ > "$PRIO";; esac
yield() {   # true while a different, live lead run is waiting
  [ $lead -eq 0 ] && [ -f "$PRIO" ] || return 1
  local p; p=$(cat "$PRIO" 2>/dev/null)
  [ -n "$p" ] && kill -0 "$p" 2>/dev/null
}
orphan() {  # a Unity / Blender process still running although nobody holds the lock (its shell was killed by a tool timeout)
  # lead 2026-11-27: only a real Unity EDITOR counts - the Unity CLI MCP server (AppData/Local/Unity/bin/unity.exe mcp) has the
  # same image name and blocked every heavy run for 40 min
  powershell.exe -NoProfile -Command 'if (Get-Process -Name Unity -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*\Editor\Unity.exe" }) { exit 0 } else { exit 1 }' && return 0
  # lead 5190fd9a 2026-11-27 (owner: reconnect the Blender MCP): only a HEADLESS Blender (--background) counts - an open
  # Blender window running the MCP add-on (localhost:9876) is not a build job and must not stall the queue
  powershell.exe -NoProfile -Command 'if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "blender.exe" -and $_.CommandLine -match "--background" }) { exit 0 } else { exit 1 }' && return 0
  return 1
}
waited=0; owaited=0
while true; do
  if ! yield && mkdir "$LOCK" 2>/dev/null; then
    # 2026-11-26: two batched previews died with "another Unity instance is running": a tool timeout had killed the shell
    # holding the lock while its Unity kept running. Wait (max 15 min) for such orphans before starting a new run.
    if orphan && [ $owaited -lt 900 ]; then
      rmdir "$LOCK" 2>/dev/null
      [ $((owaited % 60)) -eq 0 ] && echo "[heavy-lock] '$LABEL': lock free but a Unity/Blender process is still running - waiting (${owaited}s)"
      sleep 5; owaited=$((owaited + 5)); continue
    fi
    break
  fi
  if [ -d "$LOCK" ]; then
    holder=$(cat "$LOCK/pid" 2>/dev/null)
    age=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || date +%s) ))
    if { [ -n "$holder" ] && ! kill -0 "$holder" 2>/dev/null; } || [ "$age" -gt 1800 ]; then
      echo "[heavy-lock] removing stale lock ($(cat "$LOCK/label" 2>/dev/null), age ${age}s)"; rm -rf "$LOCK"; continue
    fi
  fi
  if [ $((waited % 60)) -eq 0 ]; then echo "[heavy-lock] '$LABEL' waiting for '$(cat "$LOCK/label" 2>/dev/null)' (${waited}s)"; fi
  sleep 5; waited=$((waited + 5))
done
[ $lead -eq 1 ] && rm -f "$PRIO"
echo $$ > "$LOCK/pid"; echo "$LABEL" > "$LOCK/label"
trap 'rm -rf "$LOCK"' EXIT INT TERM
"$@"
