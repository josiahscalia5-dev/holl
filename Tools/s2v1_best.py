"""S2 Tunnel v1 - track the BEST critic-scored version (owner 2026-11-27 22:20: "preserve the best version at every checkpoint").

Reads every S2 Tunnel v1 team run in Captures/handoff/RUNS.json (journal "result" entries of the asset-critic) and writes
  Captures/s2v1/SCORES.md   every critic verdict: tag, verdict, v1 score, Unity-current score, render folder, sources kept or not
  Captures/s2v1/BEST.json   the highest v1 score (ties -> the newer one) with its SHEET_R2 / SHEET_RIG and its exact module sources
  Captures/s2v1/best/<tag>/ a protected copy of that render's _src/ + sheets (refreshed only when the best changes)
Nothing else is touched. Run by Tools/recovery_checkpoint.py every 5 minutes (inside the ONE autosave loop); manual:
  "/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/s2v1_best.py
Restore the best state: copy Captures/s2v1/best/<tag>/_src/s2v1_*.py back to Tools/Blender/scripts/s2v1/ (lead decision, after
checking that no team agent is writing them).
"""
import glob
import io
import json
import os
import re
import shutil
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "projects")
CAPT = os.path.join(ROOT, "Captures", "s2v1")
RENDERS = os.path.join(CAPT, "renders")


def hm(t):
    return time.strftime("%m-%d %H:%M", time.localtime(t))


def verdicts():
    try:
        with io.open(os.path.join(ROOT, "Captures", "handoff", "RUNS.json"), encoding="utf-8") as f:
            runs = [r for r in json.load(f)["runs"] if "bwk-s2-tunnel-v1-team" in r.get("script", "")]
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for r in runs:
        for j in glob.glob(os.path.join(PROJECTS, "*", r.get("session", "-"), "subagents", "workflows", r["run"], "journal.jsonl")):
            labels = {}
            with io.open(j, encoding="utf-8", errors="replace") as f:
                rows = []
                for line in f:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
            for e in rows:
                if e.get("type") == "started":
                    labels[e.get("key")] = e.get("label", "")
            for e in rows:
                res = e.get("result")
                lab = labels.get(e.get("key"), "")
                m = re.match(r"asset-critic: (\S+)$", lab)
                if e.get("type") != "result" or not isinstance(res, dict) or not m or "score_v1" not in res:
                    continue
                tag = m.group(1)
                d = os.path.join(RENDERS, tag)
                sheet = os.path.join(d, "SHEET_R2.png")
                t = os.path.getmtime(sheet) if os.path.exists(sheet) else os.path.getmtime(j)
                out.append({"tag": tag, "run": r["run"], "verdict": res.get("verdict"), "score_v1": res.get("score_v1"),
                            "score_unity_current": res.get("score_unity_current"), "time": t, "dir": d,
                            "has_src": os.path.isdir(os.path.join(d, "_src")), "summary": (res.get("summary") or "")[:300]})
    return sorted(out, key=lambda v: v["time"])


def update():
    """Refresh SCORES.md / BEST.json / best/<tag>/ and return short status lines for AUTO_STATUS.md."""
    vs = verdicts()
    os.makedirs(CAPT, exist_ok=True)
    renders = sorted((os.path.getmtime(p), os.path.basename(os.path.dirname(p))) for p in glob.glob(os.path.join(RENDERS, "*", "SHEET_R2.png")))
    newest = renders[-1] if renders else None
    rows = ["# S2 Tunnel v1 - critic scores (auto, Tools/s2v1_best.py every 5 min; honest scores from the independent asset-critic)", "",
            "| time | tag | verdict | v1 | Unity current | render folder | sources kept |", "|---|---|---|---|---|---|---|"]
    for v in vs:
        rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (hm(v["time"]), v["tag"], v["verdict"], v["score_v1"], v["score_unity_current"],
                                                        os.path.relpath(v["dir"], ROOT).replace("\\", "/"), "yes" if v["has_src"] else "no"))
    if not vs:
        rows.append("| - | - | no critic verdict yet | - | - | - | - |")
    if newest:
        rows += ["", "Newest render: %s (%s)" % (newest[1], hm(newest[0]))]
    with io.open(os.path.join(CAPT, "SCORES.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rows) + "\n")

    lines = []
    if not vs:
        lines.append("- S2 Tunnel v1: no critic score yet; newest render %s" % ("%s (%s)" % (newest[1], hm(newest[0])) if newest else "none"))
        return lines
    best = max(vs, key=lambda v: (float(v["score_v1"] or 0), v["time"]))
    bj = os.path.join(CAPT, "BEST.json")
    prev = None
    try:
        with io.open(bj, encoding="utf-8") as f:
            prev = json.load(f)
    except (OSError, ValueError):
        pass
    keep = os.path.join(CAPT, "best", best["tag"])
    if not prev or prev.get("tag") != best["tag"] or not os.path.isdir(keep):
        os.makedirs(keep, exist_ok=True)
        if best["has_src"]:
            shutil.copytree(os.path.join(best["dir"], "_src"), os.path.join(keep, "_src"), dirs_exist_ok=True)
        for n in ("SHEET_R2.png", "SHEET_RIG.png", "metrics_R2.txt"):
            if os.path.exists(os.path.join(best["dir"], n)):
                shutil.copy2(os.path.join(best["dir"], n), os.path.join(keep, n))
    info = dict(best, kept_copy=os.path.relpath(keep, ROOT).replace("\\", "/"), updated=time.strftime("%Y-%m-%d %H:%M"))
    info["dir"] = os.path.relpath(best["dir"], ROOT).replace("\\", "/")
    with io.open(bj, "w", encoding="utf-8", newline="\n") as f:
        json.dump(info, f, indent=1, ensure_ascii=False)
    last = vs[-1]
    lines.append("- S2 Tunnel v1 BEST: %s %s v1 %s vs Unity current %s (%s; copy %s%s)" % (
        best["tag"], best["verdict"], best["score_v1"], best["score_unity_current"], hm(best["time"]), info["kept_copy"],
        "" if best["has_src"] else ", sources not kept - rendered before 22:21"))
    if last is not best:
        lines.append("- S2 Tunnel v1 latest verdict: %s %s v1 %s (%s)" % (last["tag"], last["verdict"], last["score_v1"], hm(last["time"])))
    lines.append("- all critic scores: Captures/s2v1/SCORES.md")
    return lines


if __name__ == "__main__":
    for l in update():
        print(l)
