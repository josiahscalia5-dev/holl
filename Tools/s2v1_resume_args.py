"""Build the args for Tools/workflows/bwk-s2-tunnel-v1-team-s.js from the LAST S2 Tunnel v1 team run, so any Claude account can resume
or continue the art team in one step (owner 2026-11-27 21:45: keep the team going until 100 % usage, resumable on another account).

What it reads (nothing is changed):
  Captures/handoff/RUNS.json                     newest run whose script is Tools/workflows/bwk-s2-tunnel-v1-team*.js (or --run)
  <session>/subagents/workflows/<run>/journal.jsonl   finished agent reports ("result") and cut agents ("started" without a result)
  <run>.args_file in RUNS.json (if any)          the args that run was launched with (its own finished steps are merged first)
  Captures/s2v1/NOTES_<role>.md, Captures/s2v1/renders/<TAG>/, the cut agents' transcripts (last statement, last activity)
What it writes:
  Captures/s2v1/RESUME_ARGS.json (+ a dated copy in Captures/s2v1/resume/) =
  {"done": {modeler, water, materials, lighting, reviews: {"1": verdict, ...}, refines: {"1": {owner: report}}},
   "resume": {"<role>" | "<role>#refine<N>" | "asset-critic#review<N>": "where it stopped"}, "max_rounds", "target_score", "_source"}

Then, in the NEW lead session (after checking that no team agent of the old run still writes - files idle > 15 min):
  Workflow({scriptPath: "C:/Users/josia/thanksgiving/Tools/workflows/bwk-s2-tunnel-v1-team-s.js", args: <the JSON object>})
and register the run in RUNS.json with "args_file": "<the dated copy>".

Run with Blender's Python:  "/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/s2v1_resume_args.py [--run wf_x] [--rounds N]
"""
import argparse
import glob
import io
import json
import os
import re
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "projects")
CAPT = os.path.join(ROOT, "Captures", "s2v1")
RENDERS = os.path.join(CAPT, "renders")
SCRIPTS = os.path.join(ROOT, "Tools", "Blender", "scripts", "s2v1")

ROLE_OF_OWNER = {"modeler": "environment-modeler", "materials": "materials-artist", "lighting": "lighting-artist", "water": "water-fx-artist"}
OWNER_OF_ROLE = {v: k for k, v in ROLE_OF_OWNER.items()}
BUILD_LABELS = {
    "environment-modeler: new S2 tunnel": "modeler",
    "water-fx-artist: water + FX": "water",
    "materials-artist: premium materials + bakes": "materials",
    "lighting-artist: light, depth, grade": "lighting",
}
NOTES = {"environment-modeler": "NOTES_modeling.md", "water-fx-artist": "NOTES_water.md", "materials-artist": "NOTES_materials.md",
         "lighting-artist": "NOTES_lighting.md"}
OWN_FILES = {"environment-modeler": "s2v1_env*.py", "water-fx-artist": "s2v1_water*.py", "materials-artist": "s2v1_materials*.py",
             "lighting-artist": "s2v1_lighting*.py"}
RENDER_PREFIX = {"environment-modeler": ("model_", "fix_modeler_"), "water-fx-artist": ("water_", "fix_water_"),
                 "materials-artist": ("mat_", "fix_materials_"), "lighting-artist": ("light_", "fix_lighting_")}
LIMIT_TEXT = re.compile(r"hit your .{0,20}limit|usage limit|rate limit", re.I)


def hm(ts):
    return time.strftime("%H:%M", time.localtime(ts))


def load_runs():
    with io.open(os.path.join(ROOT, "Captures", "handoff", "RUNS.json"), encoding="utf-8") as f:
        return json.load(f)["runs"]


def find_journal(run, session):
    hits = glob.glob(os.path.join(PROJECTS, "*", session, "subagents", "workflows", run, "journal.jsonl"))
    return hits[0] if hits else None


def parse_journal(path):
    started, results = {}, {}
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                j = json.loads(line)
            except ValueError:
                continue
            key = j.get("key")
            if j.get("type") == "started":
                started[key] = j                                   # the newest start of a key wins (retries)
            elif j.get("type") == "result" and j.get("result") is not None:
                results[key] = j
    return started, results


def last_statement(agent_path):
    """Last assistant text of an agent transcript that is not the usage-limit message, plus its last write time."""
    text = ""
    try:
        with io.open(agent_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    j = json.loads(line)
                except ValueError:
                    continue
                if j.get("type") != "assistant":
                    continue
                for c in (j.get("message") or {}).get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "text" and c["text"].strip() and not LIMIT_TEXT.search(c["text"][:200]):
                        text = c["text"].strip()
        return text, os.path.getmtime(agent_path)
    except OSError:
        return "", None


def notes_tail(role):
    p = os.path.join(CAPT, NOTES.get(role, "-"))
    if not os.path.exists(p):
        return "no %s yet" % NOTES.get(role, "notes file")
    lines = [l.rstrip() for l in io.open(p, encoding="utf-8", errors="replace")]
    heads = [l for l in lines if l.startswith("## ")]
    tail = [l.strip() for l in lines if l.strip()][-5:]
    return "%s (%s): newest section '%s'; last lines: %s" % (NOTES[role], hm(os.path.getmtime(p)), heads[-1][3:] if heads else "-",
                                                               " / ".join(tail)[:700])


def renders_of(prefixes):
    out = []
    for d in glob.glob(os.path.join(RENDERS, "*")):
        name = os.path.basename(d)
        if os.path.isdir(d) and any(name.startswith(p) or ("fix_" in p and p in name) for p in prefixes):
            sheet = os.path.join(d, "SHEET_R2.png")
            out.append((os.path.getmtime(sheet) if os.path.exists(sheet) else os.path.getmtime(d), name, os.path.exists(sheet)))
    return sorted(out)


def files_of(role):
    pats = glob.glob(os.path.join(SCRIPTS, OWN_FILES.get(role, "-")))
    return ", ".join("%s (%s)" % (os.path.basename(p), hm(os.path.getmtime(p))) for p in sorted(pats)) or "none yet"


def resume_note(role, agent_path, step):
    said, t = last_statement(agent_path) if agent_path else ("", None)
    parts = ["Step: %s. Your previous run was CUT%s by an account usage limit without a final report." % (step, (" at " + hm(t)) if t else "")]
    if role in NOTES:
        parts.append("Your files on disk: %s." % files_of(role))
        parts.append("Your log: " + notes_tail(role) + ".")
        rs = renders_of(RENDER_PREFIX.get(role, ()))
        if rs:
            parts.append("Your renders (oldest -> newest): %s. The NEWEST one (%s) was probably never reviewed - READ its SHEET_R2.png / "
                         "SHEET_RIG.png first, log it, then continue." % (", ".join("%s %s%s" % (n, hm(m), "" if ok else " (no sheet)")
                                                                                   for m, n, ok in rs[-6:]), rs[-1][1]))
    else:
        parts.append("Renders for this review may already be on disk (Captures/s2v1/renders/%s/): if SHEET_R2.png and every camera exist "
                     "and are newer than every s2v1 module, judge them instead of re-rendering." % step.split()[-1])
    if said:
        parts.append("Your last statement before the cut: \"%s\"" % said[:500].replace("\n", " "))
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="team run id (default: newest bwk-s2-tunnel-v1-team* run in RUNS.json)")
    ap.add_argument("--rounds", type=int, default=0, help="extra review/refine rounds beyond the finished ones (default 2, min total 4)")
    ap.add_argument("--out", default=os.path.join(CAPT, "RESUME_ARGS.json"))
    a = ap.parse_args()

    runs = [r for r in load_runs() if "bwk-s2-tunnel-v1-team" in r.get("script", "")]
    if a.run:
        runs = [r for r in runs if r["run"] == a.run]
    if not runs:
        raise SystemExit("no S2 Tunnel v1 team run in RUNS.json")
    run = runs[0]
    journal = find_journal(run["run"], run["session"])
    if not journal:
        raise SystemExit("journal of %s (session %s) not found" % (run["run"], run["session"]))
    wdir = os.path.dirname(journal)
    is_s = run["script"].endswith("-team-s.js")

    base = {}
    if run.get("args_file") and os.path.exists(os.path.join(ROOT, run["args_file"])):
        with io.open(os.path.join(ROOT, run["args_file"]), encoding="utf-8") as f:
            base = json.load(f)
    done = base.get("done", {})
    done.setdefault("reviews", {})
    done.setdefault("refines", {})
    resume = {}
    started, results = parse_journal(journal)

    report_lines = []
    for key, st in started.items():
        label = st.get("label", "")
        res = results.get(key, {}).get("result")
        agent_path = os.path.join(wdir, "agent-%s.jsonl" % st.get("agentId")) if st.get("agentId") else None
        m_rev = re.match(r"asset-critic: (review|final)(\d+)$", label)
        m_fix = re.match(r"(.+): fix review(\d+)$", label)
        if label in BUILD_LABELS:
            slot, role = BUILD_LABELS[label], ROLE_OF_OWNER[BUILD_LABELS[label]]
            if res:
                done[slot] = res
                report_lines.append("DONE    %-46s score %s" % (label, res.get("honest_score")))
            elif slot not in done:
                resume[role] = resume_note(role, agent_path, "%s (%s phase)" % (label, st.get("phase")))
                report_lines.append("RESUME  %-46s (cut)" % label)
        elif m_rev:
            kind, n = m_rev.group(1), int(m_rev.group(2))
            rn = n + 1 if (kind == "final" and not is_s) else n          # the -r / original script: final1 = the review after refine 1
            tag = "%s%d" % (kind, n)
            if res:
                res = dict(res, _dir="%s/Captures/s2v1/renders/%s" % (ROOT.replace("\\", "/"), tag))
                done["reviews"][str(rn)] = res
                report_lines.append("DONE    %-46s %s v1 %s vs Unity %s" % (label, res.get("verdict"), res.get("score_v1"), res.get("score_unity_current")))
            elif str(rn) not in done["reviews"]:
                resume["asset-critic#review%d" % rn] = resume_note("asset-critic", agent_path, "critic %s" % tag)
                report_lines.append("RESUME  %-46s (cut) -> review%d" % (label, rn))
        elif m_fix:
            role, n = m_fix.group(1), m_fix.group(2)
            owner = OWNER_OF_ROLE.get(role)
            if not owner:
                continue
            if res:
                done["refines"].setdefault(n, {})[owner] = res
                report_lines.append("DONE    %-46s score %s" % (label, res.get("honest_score")))
            elif owner not in done["refines"].get(n, {}):
                resume["%s#refine%s" % (role, n)] = resume_note(role, agent_path, "refinement round %s (%s)" % (n, label))
                report_lines.append("RESUME  %-46s (cut)" % label)

    n_reviews = max([int(k) for k in done["reviews"]] or [0])
    rounds = max(4, n_reviews + (a.rounds or 2))
    out = {
        "done": done,
        "resume": resume,
        "max_rounds": rounds,
        "target_score": 9,
        "effort": "xhigh",
        "lead_note": "resumed from run %s (%s) by Tools/s2v1_resume_args.py at %s" % (run["run"], run["script"], time.strftime("%Y-%m-%d %H:%M")),
        "_source": {"run": run["run"], "session": run["session"], "journal": journal.replace("\\", "/"), "built": time.strftime("%Y-%m-%d %H:%M")},
    }
    os.makedirs(os.path.join(CAPT, "resume"), exist_ok=True)
    dated = os.path.join(CAPT, "resume", "ARGS_%s_from_%s.json" % (time.strftime("%Y%m%d_%H%M"), run["run"]))
    for p in (a.out, dated):
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
    print("S2 Tunnel v1 resume args from run %s (%s, journal %s)" % (run["run"], run["script"], journal))
    for l in report_lines:
        print("  " + l)
    if not report_lines:
        print("  (no agent started in that run yet)")
    last = max(os.path.getmtime(os.path.join(wdir, f)) for f in os.listdir(wdir))
    print("  newest write in the run folder: %s (%d min ago) - relaunch only when > 15 min idle and no old process works" % (hm(last), (time.time() - last) / 60))
    print("  done: %s | reviews %s | refines %s | resume: %s | max_rounds %d" % (
        ", ".join(k for k in ("modeler", "water", "materials", "lighting") if done.get(k)) or "-",
        sorted(done["reviews"]) or "-", {k: sorted(v) for k, v in done["refines"].items()} or "-", sorted(resume) or "-", rounds))
    print("  wrote %s and %s" % (os.path.relpath(a.out, ROOT), os.path.relpath(dated, ROOT)))
    print("NEXT: Workflow({scriptPath: \"C:/Users/josia/thanksgiving/Tools/workflows/bwk-s2-tunnel-v1-team-s.js\", args: <contents of %s>})"
          % os.path.relpath(a.out, ROOT).replace("\\", "/"))
    print("      then add the run to Captures/handoff/RUNS.json with \"args_file\": \"%s\"" % os.path.relpath(dated, ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
