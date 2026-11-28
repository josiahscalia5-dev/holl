"""Bubble Wash Kingdom - automatic 5-minute RECOVERY CHECKPOINT (owner rule 2026-11-27 18:36, verbatim private copy
Captures/agents/_shared/OWNER_RULE_1836_autosave_recovery_diagnostic.txt).

Run by the ONE autosave loop: Tools/autosave.sh -> Tools/export_chat.py (chat export) -> this script (subprocess, time-limited,
never breaks the export). It needs no tokens and never starts, stops or duplicates anything. Every run it refreshes:
  1. Captures/handoff/AUTO_STATUS.md       - full live status: autosave loops, watchers, Unity / Blender jobs, workflow runs
                                            (from Captures/handoff/RUNS.json + the live journals), builds, previews, owner sheets,
                                            modified files, chat backups, references, tools, the newest lead STATE block
  2. Captures/handoff/NEXT_ACCOUNT_START.md - the <!-- AUTO-STATUS --> block under the title (the lead's STATE blocks stay untouched)
  3. Captures/handoff/NEXT_ACCOUNT_PROMPT.md - a complete ready-to-copy prompt rendered from NEXT_ACCOUNT_PROMPT_TEMPLATE.md
     (mirrored to C:/Users/josia/Downloads/NEXT_ACCOUNT_PROMPT.md, where the owner keeps it)
Everything stays LOCAL (Captures/ is gitignored). Manual run (an extra checkpoint, e.g. on a usage warning):
  "/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/recovery_checkpoint.py
"""
import glob
import json
import os
import re
import subprocess
import sys
import time

ROOT = "C:/Users/josia/thanksgiving"
HOME = os.path.expanduser("~").replace("\\", "/")
PROJ = f"{HOME}/.claude/projects/C--Users-josia-thanksgiving"
HAND = f"{ROOT}/Captures/handoff"
PS = "C:/Users/josia/PortableGit/usr/bin/ps.exe"
DOWNLOADS_PROMPT = "C:/Users/josia/Downloads/NEXT_ACCOUNT_PROMPT.md"
BEGIN, END = "<!-- AUTO-STATUS:BEGIN", "<!-- AUTO-STATUS:END -->"
NOW = time.time()


def ts(t):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(t))


def hm(t):
    return time.strftime("%H:%M", time.localtime(t))


def age(t):
    m = max(0, int((NOW - t) // 60))
    return f"{m} min ago" if m < 120 else f"{m // 60} h {m % 60} min ago"


def run(cmd, timeout=20):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT,
                              encoding="utf-8", errors="replace").stdout
    except Exception as e:  # noqa: BLE001
        return f"<{type(e).__name__}: {e}>"


def rel(p):
    p = p.replace("\\", "/")
    return p[len(ROOT) + 1:] if p.startswith(ROOT + "/") else p


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


# ------------------------------------------------------------------ live processes
def processes():
    rows = []
    for line in run([PS, "-ef"]).splitlines()[1:]:
        parts = line.split(None, 5)
        if len(parts) == 6:
            rows.append({"pid": parts[1], "ppid": parts[2], "start": parts[4], "cmd": parts[5].strip()})
    return rows


def top_level(rows, needle):
    hit = [r for r in rows if needle in r["cmd"] and "grep" not in r["cmd"] and "/usr/bin/bash -c" not in r["cmd"]]
    pids = {r["pid"] for r in hit}
    return [r for r in hit if r["ppid"] not in pids]


def heavy_jobs():
    ps1 = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(Unity|blender)\\.exe$' } | "
           "ForEach-Object { '{0}|{1}|{2}' -f $_.ProcessId, $_.CreationDate.ToString('HH:mm'), $_.CommandLine }")
    out = run(["powershell.exe", "-NoProfile", "-Command", ps1], timeout=30)
    jobs = []
    for line in out.splitlines():
        if line.count("|") < 2:
            continue
        pid, start, cmd = line.split("|", 2)
        c = cmd.replace("\\", "/")
        if "/Editor/Unity.exe" in c:
            m = re.search(r"-logFile\s+\"?([^\" ]+)", c)
            m2 = re.search(r"-executeMethod\s+(\S+)", c)
            jobs.append(f"Unity editor (batchmode) PID {pid} since {start}: {m2.group(1) if m2 else ('tests' if '-runTests' in c else '?')}"
                        f" log {rel(m.group(1)) if m else '?'}")
        elif "blender.exe" in c.lower():
            if "--background" in c:
                m = re.search(r"--python\s+\"?([^\" ]+)", c)
                jobs.append(f"Blender headless PID {pid} since {start}: {rel(m.group(1)) if m else c[-120:]}")
            else:
                jobs.append(f"Blender GUI window PID {pid} since {start} (MCP add-on, leave it open - not a job)")
    lock = f"{ROOT}/Logs/heavy.lock"
    if os.path.isdir(lock):
        try:
            label = open(f"{lock}/label").read().strip()
        except OSError:
            label = "?"
        jobs.insert(0, f"heavy_lock HELD by '{label}' since {hm(os.path.getmtime(lock))}")
    else:
        jobs.insert(0, "heavy_lock free")
    return jobs


# ------------------------------------------------------------------ workflows
def registry():
    try:
        return json.load(open(f"{HAND}/RUNS.json", encoding="utf-8")).get("runs", [])
    except Exception:  # noqa: BLE001
        return []


def workflow_runs(hours=6):
    reg = {r.get("run"): r for r in registry()}
    out = []
    for jp in glob.glob(f"{PROJ}/*/subagents/workflows/wf_*/journal.jsonl"):
        d = os.path.dirname(jp)
        run_id = os.path.basename(d)
        agents = glob.glob(f"{d}/agent-*.jsonl")
        newest = max([os.path.getmtime(p) for p in agents] + [os.path.getmtime(jp)])
        if NOW - newest > hours * 3600 and run_id not in reg:
            continue
        started, results = {}, {}
        try:
            for line in open(jp, encoding="utf-8", errors="replace"):
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("type") == "started":
                    started[r.get("key")] = r.get("label") or r.get("agentId")
                elif r.get("type") == "result":
                    results[r.get("key")] = r.get("result")
        except OSError:
            pass
        unfinished = [lab for k, lab in started.items() if k not in results]
        notable = []
        for k, res in results.items():
            lab = started.get(k, "?")
            if isinstance(res, dict):
                if "verdict" in res and "score_new" in res:
                    notable.append(f"{lab}: {res.get('verdict')} new {res.get('score_new')}")
                elif "keep" in res and "score_after" in res:
                    notable.append(f"{lab}: {'KEEP' if res.get('keep') else 'REVERT'} {res.get('score_before')} -> {res.get('score_after')}")
        quiet = NOW - newest
        if unfinished and quiet < 15 * 60:
            state = "RUNNING"
        elif unfinished:
            state = f"CUT or STALLED (no agent activity for {int(quiet // 60)} min)"
        else:
            state = "finished (all started agents returned)" if started else "launched, no agent yet"
        entry = reg.get(run_id, {})
        if entry.get("done") and state.startswith("CUT"):
            state = "closed by the lead (superseded / resumed elsewhere)"
        out.append({"run": run_id, "session": os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(d)))),
                    "state": state, "newest": newest, "started": len(started), "results": len(results),
                    "unfinished": unfinished, "notable": notable, "reg": entry})
    out.sort(key=lambda r: -r["newest"])
    return out


# ------------------------------------------------------------------ files
def newest(pattern, n, dirs=False):
    items = [p for p in glob.glob(f"{ROOT}/{pattern}") if (os.path.isdir(p) if dirs else os.path.isfile(p))]
    items.sort(key=os.path.getmtime, reverse=True)
    return items[:n]


def newest_state_block():
    try:
        s = open(f"{HAND}/NEXT_ACCOUNT_START.md", encoding="utf-8").read()
    except OSError:
        return "", ""
    i = s.find("\n## STATE ")
    if i < 0:
        return "", ""
    j = s.find("\n## STATE ", i + 5)
    block = s[i + 1: j if j > 0 else len(s)].strip()
    return block.split("\n", 1)[0].lstrip("# ").strip(), block


def git_changes(n=25):
    out = run(["git", "-c", "core.quotepath=off", "status", "--porcelain"], timeout=40)
    paths = [line[3:].strip().strip('"') for line in out.splitlines() if len(line) > 3]
    stamped = []
    for p in paths:
        fp = f"{ROOT}/{p}"
        if os.path.exists(fp) and not os.path.isdir(fp):
            stamped.append((os.path.getmtime(fp), p))
    stamped.sort(reverse=True)
    return len(paths), stamped[:n]


def lead_chat():
    mains = [p for p in glob.glob(f"{PROJ}/*.jsonl")]
    mains.sort(key=os.path.getmtime, reverse=True)
    if not mains:
        return "?"
    sid = os.path.basename(mains[0])[:-6]
    chat = newest(f"ChatHistory/*_{sid[:8]}.md", 1)
    return (f"session {sid} (transcript ~/.claude/projects/C--Users-josia-thanksgiving/{sid}.jsonl"
            + (f", text export {rel(chat[0])}" if chat else "") + f", last activity {hm(os.path.getmtime(mains[0]))})")


# ------------------------------------------------------------------ render
def main():
    rows = processes()
    autosaves = top_level(rows, "Tools/autosave.sh")
    watchers = top_level(rows, "Tools/after_wave.sh")
    jobs = heavy_jobs()
    runs = workflow_runs()
    title, block = newest_state_block()
    n_changed, changed = git_changes()
    sheets = newest("Captures/sections/OWNER_S2_mascot_accept_*.png", 3)
    owner_sheets = newest("Captures/sections/OWNER_*.png", 5)
    builds = newest("Captures/stills_*", 3, dirs=True)
    plays = newest("Captures/playmode/run_summary_*.txt", 2)
    previews = (newest("Captures/agents/*/screen_S2_*/*", 6, dirs=True) + newest("Captures/lead/*", 6, dirs=True))
    previews.sort(key=os.path.getmtime, reverse=True)
    chats = newest("ChatHistory/*.md", 4)
    diag = f"{ROOT}/Captures/diagnostic/Bubble_Wash_Kingdom_Mascot_Diagnostic.zip"
    pushed = ""
    try:
        with open(f"{ROOT}/Logs/autosave.log", encoding="utf-8", errors="replace") as f:
            tail = f.readlines()[-400:]
        p = [l.strip() for l in tail if " pushed " in l or "PUSH FAILED" in l]
        pushed = p[-1] if p else "no push in the last 400 log lines"
    except OSError:
        pass
    gen = ts(NOW)

    def run_lines(prefix="  - "):
        lines = []
        live = [r for r in runs if (r["reg"] and not r["reg"].get("done")) or (not r["reg"] and NOW - r["newest"] < 3600)]
        for r in live:
            reg = r["reg"]
            lines.append(f"{prefix}workflow {r['run']} [{r['state']}] session {r['session'][:8]}, agents {r['results']}/{r['started']} returned"
                         + (f", last activity {age(r['newest'])}" if r['newest'] else "")
                         + (f"; script {reg['script']}" if reg.get("script") else "")
                         + (f"; {reg['purpose']}" if reg.get("purpose") else ""))
            if r["unfinished"]:
                lines.append(f"{prefix}  unfinished agents: {', '.join(r['unfinished'])}")
            if r["notable"]:
                lines.append(f"{prefix}  results: {'; '.join(r['notable'])}")
            if reg.get("watcher"):
                lines.append(f"{prefix}  watcher: {reg['watcher']}")
            if reg.get("on_cut") and r["unfinished"]:
                lines.append(f"{prefix}  if cut: {reg['on_cut']}")
        if not live:
            lines.append(f"{prefix}no workflow run active in the last 6 hours")
        for w in watchers:
            a = w["cmd"].split()
            lines.append(f"{prefix}watcher after_wave {a[4] if len(a) > 4 else '?'} (MSYS PID {w['pid']}, since {w['start']}) watching "
                         f"{os.path.basename(a[2]) if len(a) > 2 else '?'} - Logs/after_wave_{a[4] if len(a) > 4 else '?'}.log")
        if not watchers:
            lines.append(f"{prefix}no after_wave watcher running")
        lines.append(f"{prefix}autosave loops: {len(autosaves)} (" + ", ".join(f"MSYS PID {a['pid']} since {a['start']}" for a in autosaves)
                     + ") - must be exactly ONE" + (" - OK" if len(autosaves) == 1 else " - CHECK!"))
        for j in jobs:
            lines.append(f"{prefix}{j}")
        return lines

    # 1. AUTO_STATUS.md
    L = [f"# Bubble Wash Kingdom - AUTO STATUS {gen} (private, generated every 5 minutes by Tools/recovery_checkpoint.py)", "",
         "Facts only, from live processes / journals / files. Decisions, scores and the plan live in the lead's newest STATE block "
         "(Captures/handoff/NEXT_ACCOUNT_START.md, copied at the end of this file). Ready-to-paste prompt: Captures/handoff/NEXT_ACCOUNT_PROMPT.md.", "",
         "## Running now / active specialists and workflows"] + run_lines() + [
         "- older runs (HISTORY - already resumed, superseded or closed; do NOT relaunch): " + (", ".join(
             f"{r['run']} ({r['session'][:8]}, {r['results']}/{r['started']}, {hm(r['newest'])})" for r in runs
             if not ((r["reg"] and not r["reg"].get("done")) or (not r["reg"] and NOW - r["newest"] < 3600))) or "none"),
         "", "## Latest Unity builds, Play Mode, previews"]
    L += [f"- build stills {rel(b)} ({ts(os.path.getmtime(b))})" for b in builds]
    for p in plays:
        try:
            first = open(p, encoding="utf-8", errors="replace").read().strip().splitlines()[:2]
        except OSError:
            first = []
        L.append(f"- play mode {rel(p)} ({hm(os.path.getmtime(p))}): {' | '.join(first)[:220]}")
    L += [f"- preview {rel(p)} ({hm(os.path.getmtime(p))})" for p in previews[:10]]
    L += ["", "## Owner sheets, acceptance decisions, scores"]
    L += [f"- {rel(s)} ({ts(os.path.getmtime(s))})" for s in owner_sheets]
    L += ["- scores / decisions: see the lead's STATE block below (honest scores only) and the workflow results above"]
    L += ["", f"## Modified files ({n_changed} paths in git status; newest {len(changed)})"]
    L += [f"- {hm(t)} {p}" for t, p in changed]
    L += ["", "## Saves and backups",
          f"- autosave push: {pushed}",
          *[f"- chat export (LOCAL only) {rel(c)} ({hm(os.path.getmtime(c))}, {os.path.getsize(c) // 1024} KB)" for c in chats],
          f"- ChatGPT mascot diagnostic ZIP: " + (f"{rel(diag)} ({ts(os.path.getmtime(diag))}, {os.path.getsize(diag) / 1048576:.1f} MB; copy in "
                                                   "C:/Users/josia/Downloads)" if os.path.exists(diag) else "not built"),
          "", "## Approved references (authoritative first)",
          "- Reference/google_flow_pack_1735/ (ORIGINAL Google Flow pack: Frames/frame_03.00s = S2, 04.00s = face / front, 07.50s = angled; Crops/)",
          "- Reference/frames4k/, Reference/frames4k_720/ (4K export of the same video); Reference/owner_sheets_1735/ (generated sheets: unseen angles only)",
          "", "## Tools and configuration (unchanged unless noted)",
          "- Tools/autosave.sh 300 (ONE loop) -> Tools/export_chat.py -> Tools/recovery_checkpoint.py; Tools/heavy_lock.sh; Tools/unity_run.sh; "
          "Tools/blender_run.sh; Tools/safe_build.sh; Tools/after_wave.sh (GATE=1 + GATE_BEFORE / GATE_VERSIONS / GATE_BLABEL); "
          "Tools/mascot_owner_sheet.py --accept; Tools/triptych.py; Tools/workflows/*.js; run registry Captures/handoff/RUNS.json",
          "", f"## Newest lead STATE block (verbatim): {title}", "", block[:12000] if block else "(none)", ""]
    write_atomic(f"{HAND}/AUTO_STATUS.md", "\n".join(L))

    # 2. AUTO-STATUS block in NEXT_ACCOUNT_START.md
    nas = f"{HAND}/NEXT_ACCOUNT_START.md"
    try:
        s = open(nas, encoding="utf-8").read()
        auto = "\n".join([f"{BEGIN} generated {gen} by Tools/recovery_checkpoint.py every 5 minutes - do not edit by hand -->",
                          f"## AUTO STATUS {gen} (live facts; full list Captures/handoff/AUTO_STATUS.md; ready-to-paste prompt "
                          "Captures/handoff/NEXT_ACCOUNT_PROMPT.md)"] + run_lines("- ")
                         + [f"- newest owner acceptance sheet: {rel(sheets[0])} ({ts(os.path.getmtime(sheets[0]))})" if sheets else "- no acceptance sheet yet",
                            f"- newest build stills: {rel(builds[0])} ({ts(os.path.getmtime(builds[0]))})" if builds else "- no build stills",
                            f"- newest lead STATE block below: {title}", END])
        if BEGIN in s and END in s:
            a, b = s.index(BEGIN), s.index(END) + len(END)
            s2 = s[:a] + auto + s[b:]
        else:
            first, _, rest = s.partition("\n")
            s2 = first + "\n\n" + auto + "\n" + rest
        if s2 != s:
            write_atomic(nas, s2)
    except OSError as e:
        print("recovery_checkpoint: NEXT_ACCOUNT_START.md not updated:", e)

    # 3. NEXT_ACCOUNT_PROMPT.md from the template
    try:
        tpl = open(f"{HAND}/NEXT_ACCOUNT_PROMPT_TEMPLATE.md", encoding="utf-8").read()
        passes = sorted(glob.glob(f"{ROOT}/Tools/workflows/bwk-s2-pass10*.js"), key=os.path.getmtime)
        hint = "e.g. bwk-s2-pass10i.js -> bwk-s2-pass10j.js"
        if passes:
            b = os.path.basename(passes[-1])
            m = re.match(r"(bwk-s2-pass\d+)([a-y])\.js$", b)
            if m:
                hint = f"newest {b} -> {m.group(1)}{chr(ord(m.group(2)) + 1)}.js"
        rep = {
            "{{GENERATED}}": gen,
            "{{NEWEST_STATE_TITLE}}": title or "(none)",
            "{{LEAD_CHAT}}": lead_chat(),
            "{{RUNNING}}": "\n".join(run_lines("   - ")),
            "{{NEXT_PASS_HINT}}": hint,
            "{{SHEETS}}": "; ".join(f"{rel(x)} ({ts(os.path.getmtime(x))})" for x in sheets) or "none yet",
            "{{DIAG_ZIP}}": (f"{rel(diag)} ({ts(os.path.getmtime(diag))}, copy C:\\Users\\josia\\Downloads\\Bubble_Wash_Kingdom_Mascot_Diagnostic.zip)"
                             if os.path.exists(diag) else "not built yet - build it from existing files (< 30 MB, no credentials / chats)"),
        }
        for k, v in rep.items():
            tpl = tpl.replace(k, v)
        prompt = f"{HAND}/NEXT_ACCOUNT_PROMPT.md"
        old = open(prompt, encoding="utf-8").read() if os.path.exists(prompt) else ""
        if old and "AUTO-GENERATED" not in old.split("\n", 1)[0]:
            stamp = time.strftime("%H%M", time.localtime(os.path.getmtime(prompt)))
            keep = f"{HAND}/NEXT_ACCOUNT_PROMPT_{stamp}.md"
            if not os.path.exists(keep):
                os.replace(prompt, keep)          # keep the last hand-written prompt
        write_atomic(prompt, tpl)
        if os.path.isdir(os.path.dirname(DOWNLOADS_PROMPT)):
            write_atomic(DOWNLOADS_PROMPT, tpl)
    except OSError as e:
        print("recovery_checkpoint: prompt not updated:", e)
    print(f"recovery_checkpoint {gen}: {len([r for r in runs if r['state'] == 'RUNNING'])} running run(s), {len(watchers)} watcher(s), "
          f"{len(autosaves)} autosave loop(s), {n_changed} changed paths")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 - the autosave must never break
        print("recovery_checkpoint FAILED:", type(e).__name__, e)
        sys.exit(0)
