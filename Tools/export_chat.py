"""Export Claude Code chat history for this project as readable Markdown (text only).

Reads every top-level session transcript in ~/.claude/projects/C--Users-josia-thanksgiving/*.jsonl and writes
ChatHistory/<first-date>_<session8>.md containing the user's messages and Claude's replies, plus one line per tool action.
Deliberately left out: screenshots / images, tool outputs (file contents, logs), hidden reasoning, and system context.
Redacted: e-mail addresses and anything that looks like an access token.

Run with any Python 3 (this PC has no system Python; Blender's bundled one works):
  "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" Tools/export_chat.py
"""
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(os.path.expanduser("~"), ".claude", "projects", "C--Users-josia-thanksgiving")
OUT = os.path.join(ROOT, "ChatHistory")

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


def export(path):
    session = os.path.splitext(os.path.basename(path))[0]
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


if __name__ == "__main__":
    done = [n for n in (export(p) for p in sorted(glob.glob(os.path.join(SRC, "*.jsonl")))) if n]
    print("exported:", ", ".join(done) if done else "nothing")
