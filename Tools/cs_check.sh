#!/bin/bash
# Usage: Tools/cs_check.sh [-w] [-add <Assembly>=<draft.cs>]...
#   -w    also list the warnings (default: count only)
#   -add  also compile a NEW file that is not in Assets yet (check a draft before Unity can see it), for example
#         Tools/cs_check.sh -add BubbleWash.Editor=C:/Users/josia/AppData/Local/Temp/Draft.cs
# Fast C# compile check of BubbleWash.Runtime, BubbleWash.Editor and BubbleWash.Tests.PlayMode WITHOUT starting Unity
# (seconds instead of a 1-4 minute Unity batch run plus the heavy-lock queue). Run it after every C# edit, before asking
# for a Unity preview. No heavy lock needed: it is one short dotnet process at a time (concurrent cs_check runs queue).
#
# How: Unity's own bundled Roslyn (NetCoreRuntime/dotnet.exe + DotNetSdkRoslyn/csc.dll) with Unity's own response files
# from Library/Bee (read-only; copied to Logs/cs_check/): Unity's defines, references, analyzers/source generators and
# options are kept, the source list is replaced by the CURRENT .cs files of each asmdef folder (new files included), and
# every output (-out, -refout, -pdb, -doc, generated files) goes to Logs/cs_check/. Runtime compiles first; Editor and
# Tests compile against that fresh Runtime (if Runtime itself fails, against Unity's last good Runtime build, so their
# own errors still show).
# Output: "OK ..." or the csc lines "file(line,col): error CSxxxx: message", plus a warnings count (-w lists warnings).
# Exit code: 0 = compiles, 1 = compile errors, 2 = setup problem (missing compiler or Unity response files).
# Limits: C# only (no shaders, assets, ILPostProcessors or Burst); a new package / asmdef reference / define is seen only
# after any Unity run has regenerated Library/Bee/artifacts/1900b0aE.dag/*.rsp.
ROOT=/c/Users/josia/thanksgiving
ED="C:/Program Files/Unity/Hub/Editor/6000.3.29f1/Editor/Data"
DOTNET="$ED/NetCoreRuntime/dotnet.exe"
CSC="$ED/DotNetSdkRoslyn/csc.dll"
DAG="Library/Bee/artifacts/1900b0aE.dag"
OUT="Logs/cs_check"
ASMS="BubbleWash.Runtime BubbleWash.Editor BubbleWash.Tests.PlayMode"   # dependency order
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'                         # pass csc options through untouched
export PATH="/usr/bin:$PATH"                                               # GNU find/sort, never Windows find.exe/sort.exe
SHOWW=0; EXTRA=()
while [ $# -gt 0 ]; do case "$1" in -w) SHOWW=1;; -add) EXTRA+=("$2"); shift;; esac; shift; done
cd "$ROOT" || exit 2
mkdir -p "$OUT"
t0=$(date +%s%N)
[ -f "$DOTNET" ] && [ -f "$CSC" ] || { echo "[cs_check] Unity's compiler not found under $ED"; exit 2; }

free_kb=$(awk '/^MemFree:/{print $2}' /proc/meminfo 2>/dev/null)
if [ -n "$free_kb" ] && [ "$free_kb" -lt 512000 ]; then
  echo "[cs_check] note: only $((free_kb / 1024)) MB RAM free (csc needs ~200-300 MB) - the check may be slow"
fi

# One cs_check at a time (runs share Logs/cs_check/); a lock whose holder is gone or older than 5 minutes is stale.
LOCK="$OUT/.lock"; waited=0
until mkdir "$LOCK" 2>/dev/null; do
  holder=$(cat "$LOCK/pid" 2>/dev/null)
  age=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || date +%s) ))
  if { [ -n "$holder" ] && ! kill -0 "$holder" 2>/dev/null; } || [ "$age" -gt 300 ]; then rm -rf "$LOCK"; continue; fi
  [ $waited -eq 0 ] && echo "[cs_check] waiting for another cs_check run"
  sleep 1; waited=$((waited + 1))
done
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT INT TERM

# Folder of each assembly = folder of the asmdef whose "name" matches; asmdef folders nested inside it are excluded.
declare -A DIR
mapfile -t ASMDEFS < <(find Assets -name '*.asmdef' -not -path '*/.*' | LC_ALL=C sort)
for f in "${ASMDEFS[@]}"; do
  n=$(tr -d '\r' < "$f" | grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
  [ -n "$n" ] && DIR[$n]=$(dirname "$f")
done
sources() {   # current .cs files of assembly $1, the way Unity collects them (skips hidden, *~ and nested asmdef folders)
  local d="${DIR[$1]}" prune=() o
  for o in "${ASMDEFS[@]}"; do o=$(dirname "$o"); [[ "$o" == "$d"/* ]] && prune+=( -path "$o" -prune -o ); done
  find "$d" \( -name '.*' -o -name '*~' \) -prune -o "${prune[@]}" -type f -name '*.cs' -print | LC_ALL=C sort
}
mkrsp() {     # $1 assembly, $2 BubbleWash.Runtime reference to use -> $OUT/$1.rsp
  local a="$1" src="$DAG/$1.rsp" dst="$OUT/$1.rsp" doc
  doc=$(tr -d '\r' < "$src" | grep -c -E '^[-/]doc:')
  tr -d '\r' < "$src" \
    | grep -v -E '^[-/](out|refout|doc|pdb|generatedfilesout|errorlog|touchedfiles|reportanalyzer)(:|$)' \
    | grep -v -E '^"[^"]*\.cs"[[:space:]]*$' \
    | sed -E "s#^([-/]r(eference)?:)\"[^\"]*/BubbleWash\.Runtime(\.ref)?\.dll\"#\1\"$2\"#" > "$dst"
  [ -s "$DAG/$1.rsp2" ] && tr -d '\r' < "$DAG/$1.rsp2" >> "$dst"
  {
    echo "-out:\"$OUT/$a.dll\""
    echo "-refout:\"$OUT/$a.ref.dll\""
    echo "-pdb:\"$OUT/$a.pdb\""
    [ "$doc" -gt 0 ] && echo "-doc:\"$OUT/$a.xml\""
    echo "-generatedfilesout:\"$OUT/generated/$a\""
    sources "$a" | sed 's/.*/"&"/'
    for x in "${EXTRA[@]}"; do [ "${x%%=*}" = "$a" ] && echo "\"${x#*=}\""; done
  } >> "$dst"
}

for a in $ASMS; do
  if [ ! -f "$DAG/$a.rsp" ] || [ -z "${DIR[$a]}" ]; then
    echo "[cs_check] $a: Unity response file or asmdef missing - run any Unity batch once to regenerate Library/Bee"; exit 2
  fi
done
compile() {   # $1 assembly, $2 Runtime reference -> $OUT/$1.out (csc output) + $OUT/$1.code (csc exit code)
  mkdir -p "$OUT/generated/$1"
  mkrsp "$1" "$2"
  "$DOTNET" exec "$CSC" -nostdlib -noconfig "@$OUT/$1.rsp" > "$OUT/$1.out" 2>&1
  echo $? > "$OUT/$1.code"
}
compile BubbleWash.Runtime "$OUT/BubbleWash.Runtime.ref.dll"
RT="$OUT/BubbleWash.Runtime.ref.dll"; fallback=0
if [ "$(cat "$OUT/BubbleWash.Runtime.code")" != 0 ]; then RT="$DAG/BubbleWash.Runtime.ref.dll"; fallback=1; fi
free_kb=$(awk '/^MemFree:/{print $2}' /proc/meminfo 2>/dev/null)
if [ "${free_kb:-0}" -gt 800000 ]; then   # Editor + Tests in parallel (~1.5 s faster) when there is RAM for two csc
  compile BubbleWash.Editor "$RT" & compile BubbleWash.Tests.PlayMode "$RT"; wait
else
  compile BubbleWash.Editor "$RT"; compile BubbleWash.Tests.PlayMode "$RT"
fi

errs=0; warns=0; failed=""; report=""
for a in $ASMS; do
  code=$(cat "$OUT/$a.code" 2>/dev/null || echo 1)
  e=$(grep -cE '(^|: )error CS[0-9]+' "$OUT/$a.out"); w=$(grep -cE ': warning CS[0-9]+' "$OUT/$a.out")
  [ "$code" != 0 ] && [ "$e" -eq 0 ] && e=1   # csc failed without a CS error line (crash, missing file): show raw output
  errs=$((errs + e)); warns=$((warns + w))
  if [ "$code" != 0 ]; then
    failed="$failed $a"
    report+="$(grep -E 'error CS[0-9]+' "$OUT/$a.out" || head -5 "$OUT/$a.out")"$'\n'
  fi
  [ $SHOWW -eq 1 ] && [ "$w" -gt 0 ] && report+="$(grep -E ': warning CS[0-9]+' "$OUT/$a.out" | sort -u | head -40)"$'\n'
done
secs=$(awk -v n=$(( $(date +%s%N) - t0 )) 'BEGIN{printf "%.1f", n/1e9}')
printf '%s' "$report" | grep -v '^$' | sort -u
if [ -z "$failed" ]; then
  echo "OK - 3 assemblies compile (Runtime, Editor, Tests.PlayMode), $warns warnings, ${secs}s"
  code=0
else
  [ $fallback -eq 1 ] && echo "[cs_check] Runtime failed: Editor/Tests were checked against Unity's last good BubbleWash.Runtime build"
  echo "FAILED - $errs errors in:$failed, $warns warnings, ${secs}s (raw csc output: $OUT/<assembly>.out)"
  code=1
fi
{ date '+%F %T'; [ -z "$failed" ] && echo "OK" || echo "FAILED:$failed"; echo "errors=$errs warnings=$warns time=${secs}s"; } > "$OUT/summary.txt"
exit $code
