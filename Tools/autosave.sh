#!/bin/bash
# Auto-save to GitHub every N seconds (default 300 = 5 minutes), as the owner requested on 2026-11-25.
#   1. exports the Claude chat history as text (Tools/export_chat.py -> ChatHistory/, no images / tool outputs / e-mails)
#   2. snapshots the whole working tree (everything not in .gitignore) into the local branch "github-main" through a
#      separate index, leaving out PRIVATE_PATHS (files that show frames of the private reference video)
#   3. pushes github-main to origin/main (public repo) - only when something changed.
# The local "main" branch and the checkpoint tags are never touched or rewritten. Reference/, Captures/ and Logs/ stay
# out (gitignored). Stop: create Logs/autosave.stop (or stop the background task).
INTERVAL="${1:-300}"
ROOT=/c/Users/josia/thanksgiving
PY="/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe"
PUBLIC_REF=refs/heads/github-main
BASE=0c51785                     # last commit before any reference-derived image was committed
INDEX="$ROOT/.git/autosave-index"
LOG="$ROOT/Logs/autosave.log"
PRIVATE_PATHS=("Docs/AssetPreviews/SK_Mascot_vs_reference.png")
cd "$ROOT" || exit 1
mkdir -p Logs
rm -f Logs/autosave.stop

snapshot() {
  "$PY" Tools/export_chat.py >> "$LOG" 2>&1
  [ -f "$INDEX" ] || GIT_INDEX_FILE="$INDEX" git read-tree "$(git rev-parse -q --verify $PUBLIC_REF || echo $BASE)"
  GIT_INDEX_FILE="$INDEX" git add -A >> "$LOG" 2>&1
  for p in "${PRIVATE_PATHS[@]}"; do GIT_INDEX_FILE="$INDEX" git rm -q --cached --ignore-unmatch -- "$p"; done
  # 2026-11-26 09:10: the owner's newest transfer brief says to keep conversation histories OFF the public repo (an earlier
  # message asked to publish them). Until the owner decides, chat exports are still written locally (ChatHistory/) but the
  # public copy stays frozen at its last pushed state: nothing new is published and nothing is deleted. BWK_PUBLISH_CHAT=1
  # restores publishing.
  if [ "${BWK_PUBLISH_CHAT:-0}" != 1 ] && git rev-parse -q --verify $PUBLIC_REF >/dev/null; then
    GIT_INDEX_FILE="$INDEX" git reset -q "$PUBLIC_REF" -- ChatHistory >> "$LOG" 2>&1
  fi
  # Second line of defence (2026-11-26): the repo is public, so any video file, and any image whose file name looks like a
  # reference frame, side-by-side, triptych or contact sheet, stays local even if someone saves it outside Captures/.
  local p b
  while IFS= read -r p; do
    b=${p##*/}; b=${b,,}
    if [[ "$b" =~ \.(mp4|mov|webm|mkv|avi|m4v)$ ]] || { [[ "$b" =~ \.(png|jpe?g|webp|gif|bmp|tga|exr|tiff?)$ ]] && \
       { [[ "$b" =~ ^f_[0-9] ]] || [[ "$b" =~ (^|[_.-])(ref|refs|reference|references|vs|versus|frame|frames|25982|flow|contact|sheet|4k|k4|compare|comparison|triptych)([_.0-9-]|$) ]]; }; }; then
      GIT_INDEX_FILE="$INDEX" git rm -q --cached --ignore-unmatch -- "$p"
      echo "$(date '+%F %T') kept private (not published): $p" >> "$LOG"
    fi
  done < <(GIT_INDEX_FILE="$INDEX" git ls-files)
  # Exact copies of private reference material (frames, videos, correction sheets, owner uploads) stay local under ANY
  # name or folder: compare blob hashes against everything in Reference/ and the Claude upload folder. Archives never go.
  local reflist; reflist=$(mktemp)
  find Reference "$HOME/.claude/uploads" -type f 2>/dev/null | grep -iE '\.(png|jpe?g|webp|gif|bmp|tga|exr|tiff?|mp4|mov|webm|mkv|avi|m4v|zip)$' \
    | git hash-object --stdin-paths 2>/dev/null | sort -u > "$reflist"
  GIT_INDEX_FILE="$INDEX" git ls-files -s | awk -v F="$reflist" -v Q="'" '
      BEGIN { while ((getline h < F) > 0) bad[h] = 1 }
      { split($0, a, "\t"); split(a[1], m, " "); n = tolower(a[2]); if ((m[2] in bad) || n ~ /\.(zip|7z|rar)$/) print a[2] }' \
    | while IFS= read -r p; do
        GIT_INDEX_FILE="$INDEX" git rm -q --cached --ignore-unmatch -- "$p"
        echo "$(date '+%F %T') kept private (reference copy or archive): $p" >> "$LOG"
      done
  rm -f "$reflist"
  local tree parent commit
  tree=$(GIT_INDEX_FILE="$INDEX" git write-tree) || return 1
  parent=$(git rev-parse -q --verify $PUBLIC_REF || git rev-parse $BASE)
  if [ "$(git rev-parse "$parent^{tree}")" != "$tree" ]; then
    commit=$(git commit-tree "$tree" -p "$parent" -m "Autosave $(date '+%Y-%m-%d %H:%M')" \
      -m "Automatic 5-minute snapshot of the Bubble Wash Kingdom project and chat history (text export)." \
      -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>") || return 1
    git update-ref $PUBLIC_REF "$commit"
    echo "$(date '+%F %T') committed $commit" >> "$LOG"
  elif [ -z "$(git rev-parse -q --verify $PUBLIC_REF)" ]; then
    git update-ref $PUBLIC_REF "$parent"
  fi
  if [ "$(git rev-parse -q --verify refs/remotes/origin/main)" != "$(git rev-parse $PUBLIC_REF)" ]; then
    if git push origin $PUBLIC_REF:refs/heads/main >> "$LOG" 2>&1; then
      git update-ref refs/remotes/origin/main "$(git rev-parse $PUBLIC_REF)"
      echo "$(date '+%F %T') pushed $(git rev-parse --short $PUBLIC_REF)" >> "$LOG"
    else
      echo "$(date '+%F %T') PUSH FAILED (see above)" >> "$LOG"
    fi
  fi
}

if [ "$1" = "--once" ]; then snapshot; exit $?; fi
while true; do
  [ -f Logs/autosave.stop ] && { echo "$(date '+%F %T') stop file found - autosave ended" >> "$LOG"; exit 0; }
  snapshot
  sleep "$INTERVAL"
done
