"""Export Claude Code chat history for this project as readable Markdown (text only).

Main sessions: every top-level transcript in ~/.claude/projects/C--Users-josia-thanksgiving/*.jsonl ->
  ChatHistory/<first-date>_<session8>.md (the user's messages, Claude's replies, one line per tool action).
Specialist agents (owner request 2026-11-26: "all agents chat history"): every subagent / workflow-agent transcript in
  <session>/subagents/**/agent-*.jsonl -> ChatHistory/agents/<first-date>_<session8>/<HHMM>_<description>_<agent8>.md
  (the agent's brief, its statements and one line per tool action) + ChatHistory/agents/README.md (index).
Deliberately left out: screenshots / images, tool outputs (file contents, logs), hidden reasoning, and system context.
Redacted: e-mail addresses and anything that looks like an access token.
Incremental: a transcript is only re-exported when it changed since its Markdown was written (the 5-minute autosave
calls this script every cycle).

Run with any Python 3 (this PC has no system Python; Blender's bundled one works):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" Tools/export_chat.py
"""
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "projects")
SRC = os.path.join(PROJECTS, "C--Users-josia-thanksgiving")
# Lead 2026-11-27 06:45: Bubble Wash sessions opened in ANOTHER folder (e.g. C:\Users\josia\.unity) keep their transcripts
# under that folder's project dir. List them here (one "<project dir>/<session id>" per line, '#' = comment) so the
# 5-minute autosave exports them too. Only list Bubble Wash Kingdom sessions - never another game's.
EXTRA_LIST = os.path.join(ROOT, "Tools", "chat_extra_sessions.txt")


def extra_sessions():
    """Absolute '<projects>/<dir>/<session id>' bases (no .jsonl) of the listed Bubble Wash sessions outside SRC."""
    out = []
    try:
        with open(EXTRA_LIST, encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip().replace("\\", "/").strip("/")
                if line and ".." not in line:
                    base = os.path.join(PROJECTS, *line.split("/"))
                    if os.path.exists(base + ".jsonl") or os.path.isdir(base):
                        out.append(base)
    except OSError:
        pass
    return out
OUT = os.path.join(ROOT, "ChatHistory")
AGENTS_OUT = os.path.join(OUT, "agents")

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TOKENS = re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9-]{20,}|xox[abp]-[A-Za-z0-9-]{10,})\b")
SYSTEM_BLOCKS = re.compile(r"<(system-reminder|command-message|command-name|skill-format|local-command-stdout)[^>]*>.*?</\1>", re.S)
NOREPLY = "@users.noreply.github.com"


def clean(text):
    text = SYSTEM_BLOCKS.sub("", text)
    text = TOKENS.sub("[token redacted]", text)
    text = EMAIL.sub(lambda m: m.group(0) if m.group(0).endswith(NOREPLY) else "[email redacted]", text)
    return text.strip()


def tool_line(block):
    name = block.get("name", "tool")
    inp = block.get("input") or {}
    what = inp.get("description") or inp.get("file_path") or inp.get("pattern") or inp.get("query") or ""
    if name in ("Agent", "Workflow"):
        what = inp.get("description") or "subagents"
    return "> _tool: %s%s_" % (name, (" - " + clean(str(what))[:160]) if what else "")


def up_to_date(src, pattern):
    """True when an export matching `pattern` exists and is newer than the transcript `src`."""
    hits = glob.glob(pattern)
    return bool(hits) and min(os.path.getmtime(h) for h in hits) >= os.path.getmtime(src)


def export(path):
    session = os.path.splitext(os.path.basename(path))[0]
    if up_to_date(path, os.path.join(OUT, "*_%s.md" % session[:8])):
        return None
    lines, first_ts = [], None
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            try:
                e = json.loads(raw)
            except ValueError:
                continue
            if e.get("type") == "queue-operation" and e.get("operation") == "enqueue" and isinstance(e.get("content"), str):
                # messages the user sent while Claude was mid-turn
                ts = (e.get("timestamp") or "")[:16].replace("T", " ")
                first_ts = first_ts or ts
                text = clean(e["content"])
                if text:
                    lines.append("### User - sent mid-turn (%s UTC)\n\n%s\n" % (ts, text))
                continue
            if e.get("isSidechain") or e.get("type") not in ("user", "assistant"):
                continue
            msg = e.get("message") or {}
            content = msg.get("content")
            ts = (e.get("timestamp") or "")[:16].replace("T", " ")
            first_ts = first_ts or ts
            parts = []
            if isinstance(content, str):
                parts.append(clean(content))
            elif isinstance(content, list):
                for b in content:
                    t = b.get("type")
                    if t == "text":
                        parts.append(clean(b.get("text", "")))
                    elif t == "tool_use" and e["type"] == "assistant":
                        parts.append(tool_line(b))
            parts = [p for p in parts if p]
            if not parts:
                continue
            who = "User" if e["type"] == "user" else "Claude"
            lines.append("### %s (%s UTC)\n\n%s\n" % (who, ts, "\n\n".join(parts)))
    if not lines:
        return None
    os.makedirs(OUT, exist_ok=True)
    name = "%s_%s.md" % ((first_ts or "undated")[:10], session[:8])
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Bubble Wash Kingdom - Claude Code session %s\n\n" % session[:8])
        f.write("_Text-only export (no images, tool outputs or system context; e-mails redacted)._\n\n")
        f.write("\n".join(lines))
    return name


def agent_description(path):
    meta = path[:-len(".jsonl")] + ".meta.json"
    try:
        with open(meta, encoding="utf-8") as f:
            return json.load(f).get("description") or ""
    except (OSError, ValueError):
        return ""


def export_agent(path, session):
    """One specialist / workflow agent transcript -> Markdown. Returns (relative path, description, start) or None."""
    agent = os.path.basename(path)[len("agent-"):-len(".jsonl")]
    desc = agent_description(path)
    entries, first_ts, first_user = [], None, True
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            try:
                e = json.loads(raw)
            except ValueError:
                continue
            if e.get("type") not in ("user", "assistant"):
                continue
            ts = (e.get("timestamp") or "")[:16].replace("T", " ")
            first_ts = first_ts or ts
            content = (e.get("message") or {}).get("content")
            if e["type"] == "user":
                texts = [content] if isinstance(content, str) else [
                    b.get("text", "") for b in (content or []) if isinstance(b, dict) and b.get("type") == "text"]
                for t in texts:                                  # tool results are skipped on purpose (no tool outputs)
                    t = clean(t)
                    if not t or t.startswith("[Image"):
                        continue
                    entries.append("### %s (%s UTC)\n\n%s\n" % ("Brief from the lead" if first_user else "Message", ts, t))
                    first_user = False
                continue
            parts = []
            for b in content or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    t = clean(b.get("text", ""))
                    if t:
                        parts.append(t)
                elif b.get("type") == "tool_use":
                    parts.append(tool_line(b))
            if parts:
                entries.append("**Agent (%s UTC):**\n\n%s\n" % (ts, "\n\n".join(parts)))
    if not entries:
        return None
    day = (first_ts or "undated")[:10]
    folder = os.path.join(AGENTS_OUT, "%s_%s" % (day, session[:8]))
    slug = re.sub(r"[^A-Za-z0-9]+", "_", desc or "workflow_agent").strip("_")[:60]
    rel = os.path.join(folder, "%s_%s_%s.md" % ((first_ts or "0000-00-00 00:00")[11:16].replace(":", ""), slug, agent[:8]))
    os.makedirs(folder, exist_ok=True)
    with open(rel, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Agent: %s\n\nAgent %s, lead session %s, started %s UTC.\n\n" % (desc or "workflow agent", agent, session, first_ts))
        f.write("_Text-only export: the lead's brief, the agent's statements and one line per tool action "
                "(no tool outputs, images, hidden reasoning or system context; e-mails and tokens redacted)._\n\n")
        f.write("\n".join(entries))
    return os.path.relpath(rel, OUT).replace("\\", "/"), desc, first_ts


def export_agents():
    done, index = [], []
    dirs = sorted(d for d in glob.glob(os.path.join(SRC, "*")) if os.path.isdir(d))
    dirs += [b for b in extra_sessions() if os.path.isdir(b)]
    for session_dir in dirs:
        session = os.path.basename(session_dir)
        for path in sorted(glob.glob(os.path.join(session_dir, "subagents", "**", "agent-*.jsonl"), recursive=True)):
            agent8 = os.path.basename(path)[len("agent-"):len("agent-") + 8]
            existing = glob.glob(os.path.join(AGENTS_OUT, "*_%s" % session[:8], "*_%s.md" % agent8))
            if existing and os.path.getmtime(existing[0]) >= os.path.getmtime(path):
                with open(existing[0], encoding="utf-8") as f:
                    head = f.readline()[len("# Agent: "):].strip()
                index.append((os.path.relpath(existing[0], OUT).replace("\\", "/"), head, ""))
                continue
            r = export_agent(path, session)
            if r:
                done.append(r[0])
                index.append(r)
    if index:
        os.makedirs(AGENTS_OUT, exist_ok=True)
        with open(os.path.join(AGENTS_OUT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# Specialist agent chat history\n\nOne file per agent (lead brief + agent statements + tool actions), "
                    "grouped by lead session (`<date>_<session8>`). Text only; tool outputs, images and private reference "
                    "material are never exported.\n\n")
            for rel, desc, _ in sorted(index):
                f.write("- [%s](%s)\n" % (desc or rel, rel.replace("agents/", "", 1)))
    return done


if __name__ == "__main__":
    mains = sorted(glob.glob(os.path.join(SRC, "*.jsonl")))
    mains += [b + ".jsonl" for b in extra_sessions() if os.path.exists(b + ".jsonl")]
    done = [n for n in (export(p) for p in mains) if n]
    agents = export_agents()
    print("exported:", ", ".join(done) if done else "nothing", "| agents:", len(agents))
