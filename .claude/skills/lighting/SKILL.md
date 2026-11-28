---
name: lighting
description: "(Blender, proyecto26) Lighting setups: three-point, HDRI, rim, volumetrics and mood. Use when a scene is too dark, blown out or lit with no shape, or needs a quick key/fill/rim. Ships tested scripts. Not for material or shading problems (use lookdev)."
license: MIT
metadata:
  author: https://github.com/proyecto26
  version: "1.0.0"
  domain: blender
  role: specialist
  category: discipline
  stage: light_camera
  triggers: lighting, light, HDRI, three point, rim light, volumetric, fog, mood, cinematic, horror lighting
  related-skills: rendering, materials, realistic-style, horror-style
---

# Lighting Artist

Mood-driven illumination. Guide player attention. Support art direction.

## When to Use

- Scene look development
- Cinematic renders and portfolio shots
- Horror atmosphere setup
- Game lighting blockout (baked or dynamic)
- HDRI environment setup

## Workflow

```
Art Direction → Key Light → Fill/Rim → Accent → Environment
    → Volumetrics → Color Grade Prep → Validation Renders
```

## Three-Point Lighting

| Light | Purpose | Typical Setup |
|-------|---------|---------------|
| Key | Primary illumination | 45° above, 30° side |
| Fill | Shadow softening | Opposite key, 1/2–1/4 intensity |
| Rim | Subject separation | Behind subject, bright edge |

Naming: `LGT_Key_Main`, `LGT_Fill_Soft`, `LGT_Rim_Back`

## Light Types

| Type | Use Case |
|------|----------|
| Sun | Outdoor directional |
| Area | Soft studio, windows |
| Spot | Flashlights, stage, horror |
| Point | Bulbs, emissive fill |

## Color Temperature

| Mood | Kelvin | RGB Approx |
|------|--------|------------|
| Candle/warm | 1800K | Orange |
| Tungsten | 3200K | Warm white |
| Daylight | 5500K | Neutral white |
| Overcast | 6500K | Cool white |
| Moonlight | 8000K+ | Blue |

Horror: mix warm interior tungsten with cold exterior moonlight.

## HDRI Workflow

```
1. Select HDRI matching mood (overcast for horror, clear for hero)
2. Rotate to place brightest area as key
3. Adjust strength (0.5–2.0 typical)
4. Supplement with area lights for subject separation
5. Hide HDRI in background if using solid color/fog
```

## Horror Lighting

See horror-style skill. Key techniques:
- High contrast; deep shadows
- Single source motivation (one visible lamp)
- Flicker via noise modifier on strength
- Volumetric fog for light shafts
- Avoid flat even illumination

## Volumetrics

```
World shader → Volume Scatter
Light → Volume contribution enabled
Density: 0.01–0.1 (subtle to heavy fog)
Anisotropy: 0.3–0.8 for visible light shafts
```

## Game vs Cinematic

| Aspect | Game | Cinematic |
|--------|------|-----------|
| Light count | Minimal (performance) | Unlimited |
| Baked | Lightmaps common | Path trace |
| Dynamic | Real-time shadows | Ray traced |
| Mood | Gameplay readability | Artistic freedom |

## MCP Integration

1. Create lights with naming convention via MCP
2. Set color, intensity, angle via MCP
3. Configure world HDRI via MCP
4. Query light count and types
5. Organize in `COL_Lights` collection

## Constraints

### MUST DO
- Motivate every light source (visible fixture or logical source)
- Name lights `LGT_[Role]_[Descriptor]`
- Test readability of gameplay-critical areas
- Match lighting to style skill (horror, realistic, etc.)
- Separate lighting collections from geometry

### MUST NOT DO
- Write code or snippets for Blender versions before 5.2, or add version fallbacks: this plugin targets 5.2+, and legacy branches teach users APIs that no longer exist
- Flat ambient without direction
- Over-light horror scenes
- Ignore color temperature consistency
- Place lights without purpose
- Skip volumetric consideration for mood scenes

## Scripts

Tested on Blender 5.2 LTS via the official Blender MCP. Run with `execute_blender_code` (or headless,
see the `blender-mcp-workflow` skill); read the script header for every argument.
When the user will paste code into Blender themselves, give them the short `runpy` call with the absolute
path of this installed script and their ARGS. Don't inline or rewrite the script: the tested file is the point.

| Script | What it does |
|--------|--------------|
| `scripts/light_rig.py` | Create a named lighting preset (lights + world + color management) inside a COL_Lights collection. Re-running replaces only the lights this script created (prefix LGT_Rig_), never user lights. |

```python
import runpy
result = runpy.run_path("<skill_dir>/scripts/light_rig.py", init_globals={"ARGS": {...}})["result"]
```

ARGS: `preset`, `target`, `collection`, `set_world`

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Horror setups | `references/horror-lighting-setups.md` | Horror scenes |
| Cinematic rigs | `references/cinematic-light-rigs.md` | Portfolio renders |

## Bubble Wash Kingdom usage (lead 8d2d815d, 2026-11-27 - read before using this skill here)
- Installed selectively from github.com/proyecto26/blender-ai-plugin (MIT, commit 2075bda, 2026-11-16; LICENSE-proyecto26.txt)
  on the owner's 20:35 request. NOT installed on purpose: the Blender Lab MCP server, `npx skills`, hooks, other skills / agents.
  Never add that MCP: this project already has the user-level `blender` MCP (GUI window) and the headless pipeline below.
- Where it applies: Blender look renders of the S2 washing-machine environment (tunnel, violet bands, gold rings, stars,
  machinery, atmosphere) - see the project skill `bwk-s2-cinematic-look` for the S2 targets, palette and verification rules.
- How to run here: headless through `bash Tools/blender_run.sh <our script>.py <log>` (heavy lock, --factory-startup; it does NOT
  forward `--` arguments), so call this skill's script from OUR scene script with
  `runpy.run_path("C:/Users/josia/thanksgiving/.claude/skills/<skill>/scripts/<script>.py", init_globals={"ARGS": {...}})["result"]`;
  or, for a quick look in the open Blender window, through the existing blender MCP's execute_blender_code. One heavy Blender /
  Unity job at a time (Tools/heavy_lock.sh). Owner 20:35: no expensive renders until he provides the Hi3DScan result.
- The scripts are generic (studio / horror / neon presets). For S2 they are starting points only: the original's look is
  emissive-motivated (bulbs, bands, stars, the bright core) - never a generic three-point rig over the tunnel.
- Unity check: Blender's AgX view transform is NOT Unity URP's Neutral tonemapper - a Blender grade only counts after the same
  frame is verified in Unity (R2 matching camera + the gameplay rig), side by side with the original 3.00 s frame.
