---
name: bwk-s2-cinematic-look
description: "Bubble Wash Kingdom S2 environment look (washing-machine door tunnel = the owner's ORIGINAL Google Flow 3.00 s frame): measured palette, depth profile and element colours, the Blender-first lighting / grading / camera recipe using the installed lighting, compositing and camera-cinematography skills, the Unity URP transfer and the side-by-side verification protocol. Use for ANY S2 environment look, lighting, atmosphere, colour or grading work - tunnel, violet bands, gold rings, stars, machinery, depth."
license: project-internal (Bubble Wash Kingdom)
metadata:
  author: lead 8d2d815d, 2026-11-27 20:45
  related-skills: lighting, compositing, camera-cinematography, unity-lighting-vfx, unity-graphics
---

# S2 cinematic look - targets, recipe, proof

The owner's ORIGINAL Google Flow video is the FINAL approved visual target. The milestone is the closest genuine
interactive 3D recreation of the ENTIRE 3.00 s S2 screen (9/10+). The method is flexible; the look is not.

## Owner rules in force (2026-11-27, newest first)
- 21:03 (NEWEST - supersedes the 20:35 wait below): Hi3DScan is REMOVED from the plan - do not wait for it. Build S2 Tunnel v1 =
  a genuinely high-quality replacement of the ENTIRE S2 scenery in Blender with the coordinated art team (isolated workspace
  Tools/Blender/scripts/s2v1/, Tools/Blender/work/s2v1/, Captures/s2v1/; brief Captures/s2v1/TEAM_BRIEF.md), actual renders next to
  the original 3.00 s frame, 9/10+. Stop modifying the old cylinder and thin rings. Renders through the assembly are expected.
- 20:35 (SUPERSEDED at 21:03): prepare these skills, but NO expensive rendering or reconstruction workflows until the owner provides the result of
  the owner's pending Hi3DScan experiment (the owner's original 15 s video, submitted ~20:23 to that external video-to-3D service; Polycam was
  tested earlier and distorted). Exactly ONE 5-minute autosave. No MCP server / hooks / duplicate agents / replacement studio.
- 20:1x: video pixels MAY be used as surface textures on genuine 3D geometry - but the drum-wall projection test FAILED
  (Captures/lead/s2_projection/NOTES.md); do not repeat it.
- 19:48: STOP minor adjustments to the existing tunnel (the lever lane is closed). ONE isolated, versioned module, rendered in
  Blender FIRST at equivalent framing next to the original, moved into Unity only if substantially closer, then verified there.
- Always: no static backgrounds, video playback or flat scenery substitutes; mascot, water, collectibles and obstacles stay
  independently interactive; one heavy Unity / Blender job at a time (Tools/heavy_lock.sh); no purchases or paid APIs; reference
  pixels and reference-derived textures stay LOCAL (Captures/, Art/Projected/, Scenes/Private/ - the GitHub repo is public).

## Measured targets (Tools/s2_look_metrics.py, R2 matching camera, 1280x720; mascot and lower water excluded)
Radial depth profile around the original's vanishing point (760,205) - ORIGINAL vs ours (gate_s2p10i, 2026-11-27):

| r (px) | ORIGINAL L* / C* / hue / colour | OURS L* / C* / hue / colour | gap |
|---|---|---|---|
| 0-25 | 39.2 / 54.1 / 313 / #75479D | 47.7 / 49.1 / 307 / #7C63B1 | +8.5 L* |
| 25-50 | 37.6 / 54.1 / 309 / #68479D | 59.0 / 43.0 / 313 / #A380C3 | **+21.4 L*, -11 C*** |
| 50-80 | 44.8 / 47.3 / 311 / #775D9E | 67.1 / 35.6 / 331 / #C196BB | **+22.3 L*, -12 C*, pinker** |
| 80-120 | 51.9 / 35.2 / 340 / #9B6E8B | 62.6 / 33.5 / 9 / #B68D92 | +10.7 L*, warmer |
| 120-170 | 51.7 / 39.3 / 298 / #7475AC | 57.8 / 38.5 / 312 / #9781B1 | +6.1 L* |
| 170-240 | 49.8 / 54.4 / 307 / #8366BF | 48.3 / 44.0 / 308 / #8066AB | -10 C* |
| 240-330 | 58.2 / 42.5 / 328 / #A87DA7 | 58.4 / 40.5 / 325 / #A581A8 | ok |
| 330-460 | 54.1 / 38.9 / 327 / #9A759C | 55.2 / 44.8 / 322 / #9E75A9 | ok |

Tunnel palette (k-means 8, share): ORIGINAL #6C56A6 22 %, #E2D5E4 14 %, #55406B 14 %, #9372C0 14 %, #B97D58 12 %,
#D08AC0 11 %, #9F4E86 8 %, #EAC780 5 % - OURS #6E53AA 29 %, #C39466 14 %, #D6B2CB 14 %, **#F0E5D7 11 % (near-white the
original does not have)**, #984D6F 11 %, #9370B1 9 %, #DD59B3 6 %, **#543669 6 % (deep violet shade: original 14 %)**.

Element colours in the original (medians): gold bulbs / hot gold #F3D882, gold metal #C6934F, yellow neon star #EFD66F,
cyan neon star #59CADC, pink neon star / rim #E172B6, lavender glow band / sheen #DDD1E5, blue-violet drum metal #634F9B,
deep shadows / slots #3A2F51.

**What the numbers say:** the original's depth = a DARK, SATURATED VIOLET core (L* 38-45) framed by bright accents (warm
bulbs, lavender band glow, neon). Ours glows PALE and PINK toward the vanishing point (white LED rim dots, white rings, a third
small gold ring) and lacks deep violet shade; our outer walls already match. Never "brighten the tunnel" or add white fog.

## Blender-first recipe (for the versioned module / any S2 look render)
1. Camera (`camera-cinematography`): reproduce the game's R2 matching camera - vertical FOV 58 deg, 16:9, 1280x720; its Unity
   pose is in Captures/lead/s2_projection/uvpass_r2_meta.json (cam_pos / cam_rot, Unity world, left-handed Y-up). Convert with
   the same axis mapping our FBX exports use and VERIFY before judging anything: the Blender render's door ring and vanishing
   point must overlay the Unity R2 render (rms < ~10 px). Also render the gameplay rig views (portrait 720x1280).
2. Lighting (`lighting`): emissive-MOTIVATED, not a generic rig - the bulbs (#F3D882), band lips (#DDD1E5), neon stars and a
   small cool core accent are the light sources; the polished metal reflects them. `light_rig.py` presets are only a weak fill
   base (neon_night at low strength) or not used at all. No three-point rig over a tunnel.
3. Materials: drum metal #634F9B metallic ~0.9, roughness ~0.25-0.35; slots recessed and dark #3A2F51; gold #C6934F polished
   (roughness ~0.15-0.25) with integrated bulbs; thick ROUNDED violet bands with luminous edges over deeper faces.
4. Atmosphere: match the depth profile above - darker and more saturated toward the core, glow in the mid rings (r 120-330)
   from the emitters; any volume / mist must not lift the core.
5. Grade (`compositing`): start from `comp_grade.py` "stylized_bloom", bloom threshold ~0.9 (emitters only) and strength ~0.5,
   saturation ~1.05-1.15, vignette <= 0.2 or off; keep the core dark. View transform: Blender AgX is NOT Unity URP's Neutral
   tonemapper - prefer "Standard" / "Khronos PBR Neutral" for parity and treat any Blender look as provisional until Unity shows it.
6. Run headless through `bash Tools/blender_run.sh <our script>.py <log>` (heavy lock) and call the skill scripts with runpy
   (see each skill's "Bubble Wash Kingdom usage" section). Versioned outputs, previews in Docs/AssetPreviews/ only if they contain
   no reference pixels; comparison sheets with reference pixels go to Captures/.

## Unity transfer (only after a substantially closer Blender render)
- URP post lives in SceneBuilder.Lighting.cs (Tonemapping Neutral, ColorAdjustments saturation 4 / contrast 12 / postExposure
  -0.25, Bloom); emissives BWK_Emissive / BWK_Gold; drum BWK_DrumWall. Lead-owned. Test in a NO-SAVE preview first
  (CaptureTools.AgentPreviewBatch, or the ProjectionS2Test.PreviewBatch pattern: current vs candidate, R2 + gameplay rig at
  33.5 / 36 / 38.5 / 41 / 44 m), then ONE integration with a full build only when the owner's gates allow it.

## Proof (every claim)
- Sheet: ORIGINAL | current Unity | Blender candidate | Unity candidate at the R2 camera, plus the gameplay rig positions
  (stretching, blur, seams, reflections, readability of the path). Tools/s2_look_metrics.py numbers (core r 25-80 within ~±5 L*,
  palette shares) support the eye, never replace it. Honest /10 for the WHOLE screen; reject anything that regresses in gameplay.
- Do NOT: repeat the projection test, tune single tiny levers, use generic presets as the look, brighten the core, add white
  fog, or call a result better because it compiled or a number moved.
