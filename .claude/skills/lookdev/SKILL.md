---
name: lookdev
description: "(Blender, proyecto26) Look-dev loop: iterate material, light and camera against a reference until shading reads right. Use for 'my asset looks flat/wrong' or turntable review. Not for one material (use materials) or a light rig (use lighting)."
license: MIT
metadata:
  author: https://github.com/proyecto26
  version: "1.0.0"
  domain: blender
  role: specialist
  category: discipline
  stage: look_dev
  triggers: lookdev, look development, shading review, material lighting loop, turntable, asset presentation
  related-skills: materials, lighting, rendering, camera-cinematography, compositing, qa-review
---

# Lookdev

Material + light + camera loop. Screenshot compare. Stop when it reads.

## When to Use

- Finalizing asset shading before export/portfolio
- Turntable / grey shader checks
- Matching material references
- Bridging `materials` and `lighting` intentionally

## Workflow

```
Clay/grey pass → Base materials → Neutral light rig
  → Beauty light → Screenshot → Gap list → Iterate (stop after 2 rounds with no visible gain)
  → Optional grade → QA
```

## Standard Rigs

| Rig | Use |
|-----|-----|
| Neutral 3-point | Evaluate materials fairly |
| HDRI studio | Product / character |
| In-situ scene lights | Final context |

Keep a reusable `COL_Lookdev_Lights` + `CAM_Lookdev_*`.

## Checklist

- [ ] Values read in grayscale
- [ ] Specular roughness believable
- [ ] Edges catch light (bevels/normals)
- [ ] Emissive under control
- [ ] No pure black / pure white traps unless stylized
- [ ] Matches reference palette if provided

## Iteration Rule

Each pass: change one major variable (material OR light OR camera), then screenshot.

## Constraints

### MUST DO
- Grey pass before fancy textures when forms unsure
- Capture screenshots each iteration
- Hand off to `qa-review` before ship

### MUST NOT DO
- Fix modeling problems only with roughness maps
- Infinite tweak loops without gap list

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Lookdev Rig | `references/lookdev-rig.md` | When needed |
| Lookdev Checklist | `references/lookdev-checklist.md` | When needed |

## Bubble Wash Kingdom usage (lead 8d2d815d, 2026-11-27 21:10 - read before using this skill here)
- Installed selectively from github.com/proyecto26/blender-ai-plugin (MIT, commit 2075bda; LICENSE-proyecto26.txt) on the owner's
  21:03 request (S2 Tunnel v1 art team). Scripts unmodified; security-reviewed (bpy / bmesh / numpy only, no network / subprocess).
  NOT installed on purpose: the Blender Lab MCP server, `npx skills`, hooks, their orchestrator agent. Never add them.
- Where it applies now: the isolated S2 Tunnel v1 environment - scripts Tools/Blender/scripts/s2v1/, work files Tools/Blender/work/s2v1/,
  renders Captures/s2v1/; brief Captures/s2v1/TEAM_BRIEF.md; look targets: project skill `bwk-s2-cinematic-look`.
- How to run here: headless `bash Tools/blender_run.sh <our s2v1 script>.py <log>` (heavy lock, --factory-startup; it does NOT
  forward `--` arguments), calling this skill's script from OUR script with
  `runpy.run_path("C:/Users/josia/thanksgiving/.claude/skills/<skill>/scripts/<script>.py", init_globals={"ARGS": {...}})["result"]`.
  One heavy Blender / Unity job at a time. Never touch the Unity scene or the old tunnel files from this skill.
