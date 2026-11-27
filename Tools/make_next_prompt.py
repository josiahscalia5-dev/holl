"""Self-renewing ready-to-paste prompt for the NEXT Claude account (lead 6d001969, 2026-11-27 18:10).

Owner 2026-11-27 ~18:08: make sure it auto-saves, so that whenever the account he is using runs out of usage, the next account
(he switches between accounts) gets a prompt that continues exactly where the work stopped - and the next account keeps doing
the same. The autosave loop (Tools/autosave.sh -> Tools/export_chat.py) runs this script every 5 minutes, so the prompt is
never more than ~5 minutes old even when an account is cut off without warning.

Inputs (all local): the newest STATE block of the private handoff Captures/handoff/NEXT_ACCOUNT_START.md, the lead's current
owner priorities Captures/handoff/PROMPT_PRIORITIES.md (edited by the lead whenever they change), the Claude transcripts of this
project (workflow runs + their activity) and the running processes (after_wave watchers, heavy Unity / Blender jobs, autosave).
Output: the private Captures/handoff/NEXT_ACCOUNT_PROMPT.md (Captures/ is gitignored - it never reaches the public repo).
Run by hand: "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/make_next_prompt.py
"""
import glob
import json
import os
import re
import subprocess
import time

ROOT = "C:/Users/josia/thanksgiving"
PROJ = os.path.join(os.path.expanduser("~"), ".claude", "projects", "C--Users-josia-thanksgiving")
HANDOFF = os.path.join(ROOT, "Captures", "handoff", "NEXT_ACCOUNT_START.md")
PRIORITIES = os.path.join(ROOT, "Captures", "handoff", "PROMPT_PRIORITIES.md")
OUT = os.path.join(ROOT, "Captures", "handoff", "NEXT_ACCOUNT_PROMPT.md")
NOW = time.time()


def hm(t):
    return time.strftime("%H:%M", time.localtime(t))


def read(path, default=""):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return default


def newest_state():
    for line in read(HANDOFF).splitlines():
        if line.startswith("## STATE"):
            return line[3:].strip()
    return "(no STATE block found)"


def sessions():
    """Top-level lead / side sessions of this project, newest first: (id, last activity)."""
    out = []
    for p in glob.glob(os.path.join(PROJ, "*.jsonl")):
        out.append((os.path.basename(p)[:-6], os.path.getmtime(p)))
    return sorted(out, key=lambda x: -x[1])


def tail_has_limit(path):
    try:
        with open(path, "rb") as f:
            f.seek(max(0, os.path.getsize(path) - 6000))
            t = f.read().decode("utf-8", "replace")
        return ("hit your" in t and "limit" in t) or "out of usage credits" in t
    except OSError:
        return False


def runs(hours=6):
    handoff = read(HANDOFF)
    out = []
    for d in glob.glob(os.path.join(PROJ, "*", "subagents", "workflows", "wf_*")):
        files = glob.glob(os.path.join(d, "agent-*.jsonl")) + glob.glob(os.path.join(d, "journal.jsonl"))
        if not files:
            continue
        last = max(os.path.getmtime(f) for f in files)
        if NOW - last > hours * 3600:
            continue
        rid = os.path.basename(d)
        session = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(d))))
        metas = glob.glob(os.path.join(d, "agent-*.meta.json"))
        labels = []
        for m in sorted(metas, key=os.path.getmtime):
            try:
                labels.append(json.loads(read(m) or "{}").get("description", "?"))
            except ValueError:
                labels.append("?")
        results = read(os.path.join(d, "journal.jsonl")).count('"type":"result"')
        cut = any(tail_has_limit(a) for a in glob.glob(os.path.join(d, "agent-*.jsonl")))
        script = ""
        lines = handoff.splitlines()
        for i, line in enumerate(lines):
            if rid in line:
                m = re.search(r"Tools/workflows/[\w.-]+\.js", " ".join(lines[i:i + 2]))
                if m:
                    script = m.group(0)
                    break
        if cut:
            status = "CUT BY A USAGE LIMIT at %s (%d of %d agents returned)" % (hm(last), results, len(metas))
        elif NOW - last < 15 * 60:
            status = "RUNNING (last activity %s, %d of %d agents returned so far)" % (hm(last), results, len(metas))
        elif results >= len(metas):
            status = "FINISHED at %s (all %d agents returned - read its result in journal.jsonl)" % (hm(last), len(metas))
        else:
            status = "STOPPED OR CUT at %s (%d of %d agents returned)" % (hm(last), results, len(metas))
        out.append({"id": rid, "session": session, "dir": d.replace("\\", "/"), "last": last, "status": status,
                    "labels": labels, "script": script})
    return sorted(out, key=lambda r: -r["last"])


def processes():
    """after_wave watchers, heavy Unity / Blender jobs and the autosave loop (MSYS ps; empty if unavailable)."""
    try:
        ps = subprocess.run(["ps", "-ef"], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return [], [], []
    watchers, heavy, autosave = [], [], []
    for line in ps.splitlines():
        if "grep" in line:
            continue
        m = re.search(r"after_wave\.sh\s+(\S+)\s+(\d+)\s+(\S+)", line)
        if m:
            tag = m.group(3)
            log = os.path.join(ROOT, "Logs", "after_wave_%s.log" % tag)
            lastline = (read(log).strip().splitlines() or [""])[-1][:150]
            watchers.append("after_wave %s (watching %s, log Logs/after_wave_%s.log - last line: %s)"
                            % (tag, os.path.basename(m.group(1)), tag, lastline))
        m = re.search(r"heavy_lock\.sh\s+(\S+)", line)
        if m:
            heavy.append(m.group(1))
        if re.search(r"bash Tools/autosave\.sh", line):
            autosave.append(line.split()[1])
    return watchers, sorted(set(heavy)), autosave


def main():
    state = newest_state()
    ss = sessions()
    lead = ss[0] if ss else ("?", NOW)
    rs = runs()
    watchers, heavy, autosave = processes()
    pri = read(PRIORITIES).strip() or "4. Continue the owner's newest priorities (see the newest STATE block and Captures/agents/LEAD_DIRECTIVES.md)."
    run_lines = []
    for r in rs:
        who = ", ".join(r["labels"][:6]) + (" ..." if len(r["labels"]) > 6 else "")
        run_lines.append("   - run %s (%s): %s. Agents: %s. Script: %s. Transcripts: %s/"
                         % (r["id"], "session " + r["session"][:8], r["status"], who or "none yet",
                            r["script"] or "(see the handoff)", r["dir"].replace(os.path.expanduser("~").replace("\\", "/"), "~")))
    if not run_lines:
        run_lines.append("   - no workflow run was active in the last 6 hours (check the newest STATE block)")
    w_lines = ["   - " + w for w in watchers] or ["   - no after_wave watcher is running"]
    h_line = ("   - heavy Unity / Blender jobs in Tools/heavy_lock.sh: " + ", ".join(heavy)) if heavy else "   - no heavy Unity / Blender job"
    a_line = ("   - exactly ONE autosave loop (Tools/autosave.sh 300, PID %s) - never start another" % ", ".join(autosave)) if autosave \
        else "   - NO autosave loop is running - start exactly one: nohup bash Tools/autosave.sh 300 > /dev/null 2>&1 &"
    text = f"""Ready-to-paste prompt for the NEXT Claude account - REFRESHED AUTOMATICALLY every 5 minutes by the autosave (Tools/make_next_prompt.py),
last refresh {time.strftime('%Y-%m-%d %H:%M')}. When the account you are using runs out of usage, open a NEW Code session in C:\\Users\\josia\\thanksgiving
on the other account and paste everything between the lines.
-----------------------------------------------------------------------------------------------------------------------
Continue my Bubble Wash Kingdom Unity game in C:\\Users\\josia\\thanksgiving. It is an EXISTING project: recover the newest state and continue exactly where the previous account stopped. Never restart it and never repeat setup. (Prompt auto-generated {time.strftime('%Y-%m-%d %H:%M')}; newest session {lead[0]}, last active {hm(lead[1])}.)

1. Read CLAUDE.md, then the private Captures/handoff/NEXT_ACCOUNT_START.md - the newest STATE block first ("{state}") - then your memory index (latest-handoff, google-flow-pack-authoritative, mascot-acceptance-gate, mascot-plush-not-procedural). For more detail: the previous lead's chat ChatHistory/<date>_{lead[0][:8]}.md and its transcript ~/.claude/projects/C--Users-josia-thanksgiving/{lead[0]}.jsonl.

2. Before changing anything, check what is still running (ps -ef, tasklist, the logs) and never interrupt, restart or duplicate it. At {hm(NOW)} the autosave saw:
{chr(10).join(run_lines)}
{chr(10).join(w_lines)}
{h_line}
{a_line}
   If the previous account ran out of usage, its agents are dead, but watchers, the autosave and any Unity / Blender job keep running - let them finish.

3. For every run marked CUT or STOPPED: read its agents' transcripts, their newest NOTES.md section (Captures/agents/<role>/NOTES.md) and newest previews, review any unreviewed last change yourself, then copy its script to the next pass name with ONLY the unfinished agent(s) plus a resume note (where each stopped), keep any judge / Accept phase, and launch it once. A tunnel lever that was applied but not judged must be judged with a side-by-side or restored from its backup/ folder first.

{pri}

7. KEEP THIS CHAIN ALIVE (I switch Claude accounts when one runs out of usage): the autosave rewrites Captures/handoff/NEXT_ACCOUNT_PROMPT.md every 5 minutes from the handoff and the running processes. Keep the STATE block at the top of Captures/handoff/NEXT_ACCOUNT_START.md current - after every launch, build, review or owner message, and again whenever your usage passes about 85 % (then keep working; never stop early) - and update Captures/handoff/PROMPT_PRIORITIES.md when my priorities change. Exactly one account works at a time.

Rules: no money, purchases or paid usage. No AI world generators. Private references, chat history and credentials stay out of public GitHub. No duplicate agents, workflows, watchers or autosaves. Preserve my gameplay, controls, collisions and camera. Visual quality first; honest scores only - never call something better unless the images show it. Keep the handoff file updated so any account can continue.
-----------------------------------------------------------------------------------------------------------------------
"""
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, OUT)
    print("next-account prompt refreshed %s (%d runs, %d watchers, %d heavy jobs)" % (hm(NOW), len(rs), len(watchers), len(heavy)))


if __name__ == "__main__":
    main()
