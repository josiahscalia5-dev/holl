# Agent: Environment specialist: tunnel pass

Agent a6fcbcba8d52e6cfa, lead session 7ca46045-7dd2-467b-ae13-bd5a82bcc5e0, started 2026-11-26 04:18 UTC.

_Text-only export: the lead's brief, the agent's statements and one line per tool action (no tool outputs, images, hidden reasoning or system context; e-mails and tokens redacted)._

### Brief from the lead (2026-11-26 04:18 UTC)

You are the ENVIRONMENT specialist (Agent 3: tunnel drum walls, rims/bulkheads, gold rings geometry, machinery, wall materials) on Bubble Wash Kingdom (Unity 6.3 URP, project C:\Users\josia\thanksgiving). The project CLAUDE.md is loaded: follow its independence, toolchain and file-ownership rules. The lead (main session) coordinates you and three other specialists (character, lighting, water/FX) working at the same time.

GOAL: make the portrait 9:16 hero gameplay frame match the owner's approved reference frame Reference/frames/f_003.00s.png (its 9:16 crop is centred at 0.49 of the width) as closely as possible in YOUR domain. Target 9/10 overall. Do not drift into new ideas: match the reference.

OWNER'S WORDS FOR YOUR DOMAIN: "Make the tunnel walls a richer blue-violet like the approved video. Make the gold rings shiny, polished, and bright. Keep the many gold rings with bulbs. Improve depth and richness of the perforated tunnel walls. Add foam banks and better tunnel atmosphere. Only add side details if they are visible in the hero frame. Do not waste time on areas outside the hero frame (side chambers, portal and non-visible areas are paused)."

FIXED CAMERA (owner rule): track distance 105.5 m, RunnerCameraRig portrait values 2.55 m back / 1.5 m up / pitch 10 / FOV 58. Never change RunnerCameraRig, SceneBuilder.HeroDistance, CaptureTools.cs, CaptureUtil.cs or the lead's SceneBuilder.cs. Only what the hero frame shows matters.

CURRENT STATE: baseline image Captures/milestones/m1_before_vs_9x16.png (left = reference, right = ours), from the lead's full build at 23:14 (scene saved; includes the previous round's WIP: your predecessor's notes are in Captures/agents/environment/NOTES.md). IMPORTANT: captures now render through an HDR target (CaptureUtil.RenderHdr), so bloom and tonemapping are real in every preview; earlier tuning used clamped captures, so judge only from the new images. Measured directives: Captures/agents/LEAD_DIRECTIVES.md (read it now; it is re-printed after every preview and the lead may update it).
What is wrong now (lead's honest read): about ten thick lemon-yellow gold rings stack close together and dominate the whole upper half of the frame (the build log says 33 gold rings, 48 lavender rims, drum bands every 2.833 m from 65 m). In the reference the NEAR tunnel is lavender-violet perforated metal (big panels and rims with soft white-pink specular streaks), the first gold ring with warm bulbs sits at mid-distance (on-screen radius about 0.35 of the frame width, centred on the vanishing point at about x .55, y .30), and further gold rings recede, getting closer together toward a bright vanishing point. The walls are grey-pastel lavender with small dash slots; the reference walls are richer periwinkle/blue-violet metal with bigger, darker perforations that have visible depth (vertical ovals on the left wall near the camera, horizontal slot rows on the ceiling bays).

CHECKLIST:
(a) Gold rings: keep MANY rings, but thinner, with a polished bevelled profile and the warm bulbs embedded in the band; spacing/placement so the near view (the upper third of the frame) is violet metal, with the first visible gold ring at mid-distance as in the reference; coordinate gold material look with the lighting specialist (M_Gold is theirs) via Requests.
(b) Walls: periwinkle/blue-violet perforated drum metal (~#8a6fae lit average, ceiling bays bluer ~#6a6fc0), bigger darker holes with visible depth/AO, soft metallic sheen; lavender rims with soft white-pink highlights.
(c) Depth rhythm toward a bright warm-white vanishing point (lighting owns fog/post; you own the geometry and wall materials).
(d) Anything else only if it is visible in the hero frame. Foam banks belong to the water/FX specialist (BuildFoam): coordinate via Requests if your geometry blocks them.

YOUR FILES (edit only these): Scripts/Editor/SceneBuilder.Environment.cs, Scripts/Editor/MaterialLibrary.Environment.cs, Art/Shaders/BWK_DrumWall.shader, BWK_FlowGlow.shader, Tools/Blender/scripts/build_track.py, build_machinery.py, Art/Models/Track/*, Art/Models/Machinery/*. The ring bulb LIGHTS (BuildRingLights) are the lighting specialist's; RingSpacing/TunnelRadius constants live in the lead's SceneBuilder.cs: if you need different constants, use your own constants in your file and tell the lead.
Preview note: PreviewEnvironmentDomain (your file) rebuilds rings / chambers / pipes in memory in every preview (keep it fast and exception-safe: it runs in everyone's preview). Ring/track Blender assets need a Blender run first. The bent SM_Slide_Module / SM_Tunnel_Module (build_track.py) only change after the lead's full build unless your preview hook re-bends them; keep previews fast (skip anything outside 85-170 m of track).

PREVIEW LOOP:
- Unity preview (no scene save; batched with the other agents; ~2-5 min including the queue): `bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch env_m1_vN -bwkOut Captures/agents/environment` — start it with the Bash tool's run_in_background and wait for the completion notification (or use timeout 600000). Output: Captures/agents/environment/hero_9x16.png and hero_vs_reference_9x16.png (left ref, right ours), printed metrics and any compile errors.
- Blender (heavy lock, one heavy process at a time on this 4-thread laptop): `bash Tools/blender_run.sh Tools/Blender/scripts/<script>.py <logname>`.
- Inspect PNGs with Read; zoom with `"C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/img_crop.py IN OUT x0 y0 x1 y1 [scale]`; metrics `... -I Tools/img_stats.py <side-by-side.png>`. Write crops only under Captures/ (reference frames are private; never put them in tracked folders).
- Batch several related changes per preview. If something still looks cheap after 1-2 tries, build a better Blender asset instead of more parameter passes.
- After each preview compare against the reference honestly. Keep your best result as Captures/agents/environment/best_9x16.png and best_vs_ref_9x16.png (copies).
- Compile/shader errors in your files block everyone's previews: check the printed summary every time and fix immediately.

RULES: edit only your files. Never run the full build (SceneBuilder.BuildAllBatch / Tools/safe_build.sh), never save the scene, never run Unity or Blender except through the wrapper scripts, never git commit/push (the lead and the autosave handle git). Requests for other domains go under "Requests" in Captures/agents/environment/NOTES.md and in your final report. Keep NOTES.md short and current.

FINISH: stop when the checklist is met or after about 8 Unity preview rounds / 90 minutes, whichever comes first. Your final message is your report to the lead: files changed, what changed visually, best image path, honest domain score /10 against the reference, what is still off, requests for other domains, and anything that needs the lead's full build to show.

**Agent (2026-11-26 04:18 UTC):**

> _tool: mcp__ccd_turn__update_plan_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\LEAD_DIRECTIVES.md_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\NOTES.md_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\milestones\m1_before_vs_9x16.png_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_003.00s.png_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Bash - List project editor scripts, shaders, Blender scripts, and capture folders_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Environment.cs_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Environment.cs_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Grep - RingSpacing|TunnelRadius|TunnelCenter|tunnelStart|HeroDistance|BulbsPerRing|BulbRadius|portalD|ChunkLength|HallScale|PreviewEnvironmentDomain|PreviewRefreshDoma_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.cs_

**Agent (2026-11-26 04:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\CaptureTools.cs_

**Agent (2026-11-26 04:19 UTC):**

> _tool: Bash - Show image helper tools, run wrappers, and agent folders_

**Agent (2026-11-26 04:19 UTC):**

> _tool: Bash - Get image sizes and crop the upper halves of reference and baseline_

**Agent (2026-11-26 04:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\ref_upper.png_

**Agent (2026-11-26 04:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\base_upper.png_

**Agent (2026-11-26 04:20 UTC):**

> _tool: Bash - Zoom into the reference tunnel area_

**Agent (2026-11-26 04:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\ref_tunnel_zoom.png_

**Agent (2026-11-26 04:22 UTC):**

> _tool: Bash - Read other specialists' notes and preview queue state_

**Agent (2026-11-26 04:22 UTC):**

> _tool: Bash - Show BWK log lines from the lead's baseline build_

**Agent (2026-11-26 04:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Lighting.cs_

**Agent (2026-11-26 04:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Lighting.cs_

**Agent (2026-11-26 04:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Gold.shader_

**Agent (2026-11-26 04:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWKCommon.hlsl_

**Agent (2026-11-26 04:22 UTC):**

> _tool: Bash - Crop the left wall regions of reference and baseline_

**Agent (2026-11-26 04:23 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\ref_left.png_

**Agent (2026-11-26 04:23 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\base_left.png_

**Agent (2026-11-26 04:24 UTC):**

> _tool: Bash - Zoom 3x into the reference left wall_

**Agent (2026-11-26 04:24 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\ref_leftwall_z3.png_

**Agent (2026-11-26 04:25 UTC):**

> _tool: Bash - Zoom 4x into the reference gold ring top_

**Agent (2026-11-26 04:25 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\ref_goldring_z4.png_

**Agent (2026-11-26 04:26 UTC):**

> _tool: Bash - Zoom into the reference lavender rim and right wall_

**Agent (2026-11-26 04:26 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\ref_rim_z4.png_

**Agent (2026-11-26 04:26 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\ref_right_z3.png_

**Agent (2026-11-26 04:27 UTC):**

> _tool: Bash - Check previous Blender track build log and the heavy lock script_

**Agent (2026-11-26 04:28 UTC):**

> _tool: Bash - Show current time and heavy lock status_

**Agent (2026-11-26 04:29 UTC):**

> _tool: Bash - Zoom baseline top-right and write a color sampling helper_

**Agent (2026-11-26 04:29 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\milestones\m1_before_newcam_vs_9x16.png_

**Agent (2026-11-26 04:30 UTC):**

> _tool: Bash - Split the new baseline and sample wall colors in reference and ours_

**Agent (2026-11-26 04:30 UTC):**

> _tool: Bash - Crop the upper half of our new-camera baseline_

**Agent (2026-11-26 04:30 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\newcam_ours_upper.png_

**Agent (2026-11-26 04:31 UTC):**

> _tool: Bash - Check tangent handling in import rules and mesh bending_

**Agent (2026-11-26 04:31 UTC):**

> _tool: Bash - Inspect mesh deformer tangent handling and BendChunks_

**Agent (2026-11-26 04:31 UTC):**

> _tool: Bash - Locate SplineMeshDeformer and check tangent/UV handling_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Bash - Verify ring-related references in build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_track.py_

**Agent (2026-11-26 04:32 UTC):**

> _tool: Bash - Start the Blender track asset build in the background_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Environment.cs_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Environment.cs_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Environment.cs_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Environment.cs_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Environment.cs_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Grep - FirstRingDistance|RimsPerGap|GoldRingSpacing|ChamberGaps_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Bash - Zoom into the right tunnel wall of the new baseline_

**Agent (2026-11-26 04:33 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\newcam_right_z2.png_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Bash - Check Blender run progress and lock holder_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Bash - Show the Blender track build output summary_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\Track_hero_9x16.png_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\Track_ring_detail.png_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Bash - Zoom the Blender hero preview around the first gold ring_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\bl_hero_z3.png_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:34 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:35 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:35 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:35 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:35 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:35 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:35 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_DrumWall.shader_

**Agent (2026-11-26 04:36 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Environment.cs_

**Agent (2026-11-26 04:36 UTC):**

> _tool: Bash - Check the material helper implementation_

**Agent (2026-11-26 04:36 UTC):**

> _tool: Bash - Run the Unity agent preview for environment round 1_

**Agent (2026-11-26 04:36 UTC):**

> _tool: Write - C:\Users\josia\thanksgiving\Captures\agents\environment\NOTES.md_

**Agent (2026-11-26 04:37 UTC):**

> _tool: Bash - Write a triptych helper script in the scratchpad_

**Agent (2026-11-26 04:37 UTC):**

You've hit your 5-hour limit · resets 4am (America/New_York)

### Message (2026-11-26 09:01 UTC)

The coordinator sent a message while you were working:
Usage limit has reset: continue from where you stopped. Lead preview at 23:3x with everyone's WIP: rings are now thinner with fewer gold (22 gold / 53 lavender, bands 3.19 m from 71.5 m) and the near view reads violet: clearly better. Still off: gold rings read thin orange lines with tiny bulbs (reference: polished gold band with fat warm amber bulbs at mid-distance), wall slots still small. Camera is the approved 2.75/1.3/10/58. BWK/Soft has a shader error from the water agent (being fixed): ignore magenta water/foam if it appears. Keep the remaining budget to about 5 preview rounds.

Address this before completing your current task.

**Agent (2026-11-26 09:02 UTC):**

> _tool: Bash - Check the environment preview output_

**Agent (2026-11-26 09:02 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\hero_vs_reference_9x16.png_

**Agent (2026-11-26 09:02 UTC):**

> _tool: Bash - Save best and zoom upper area of v1_

**Agent (2026-11-26 09:02 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\v1_z.png_

**Agent (2026-11-26 09:02 UTC):**

> _tool: Bash - Make gold band fatter with bigger bulbs and rebuild_

**Agent (2026-11-26 09:02 UTC):**

Now the wall material: lighter, less saturated ceiling, bigger slots.

**Agent (2026-11-26 09:02 UTC):**

> _tool: Bash - Lighten wall colors and enlarge slots_

**Agent (2026-11-26 09:02 UTC):**

> _tool: Bash - Wait for the Blender ring rebuild and show checks_

**Agent (2026-11-26 09:05 UTC):**

> _tool: Bash - Run Unity preview round 2_

**Agent (2026-11-26 09:08 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\hero_vs_reference_9x16.png_

**Agent (2026-11-26 09:08 UTC):**

> _tool: Bash - Save v2 as best and crop the upper frame_

**Agent (2026-11-26 09:08 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\v2_z.png_

**Agent (2026-11-26 09:08 UTC):**

> _tool: Bash - Saturate rims, darken walls slightly, run preview 3_

**Agent (2026-11-26 09:11 UTC):**

> _tool: Bash - Crop upper frame of v3_

**Agent (2026-11-26 09:11 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\m1\v3_z.png_

**Agent (2026-11-26 09:11 UTC):**

> _tool: Bash - Soften ceiling saturation and run preview 4_

**Agent (2026-11-26 09:14 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\environment\hero_vs_reference_9x16.png_

**Agent (2026-11-26 09:14 UTC):**

> _tool: Bash - Save v4 as best and check for compile errors_

**Agent (2026-11-26 09:14 UTC):**

> _tool: Write - C:\Users\josia\thanksgiving\Captures\agents\environment\NOTES.md_

**Agent (2026-11-26 09:14 UTC):**

Environment report (m1, judged at the new 2.75/1.3/10/58 camera). I ran 4 Unity previews and 2 Blender runs, and the final preview log has no compile or shader errors.

**Visual result**
- **Gold rings:** there are now fewer of them. The first visible one is mid-distance at radius about 0.33 W, the same as the reference, and the next is about 0.20 W (reference also 0.20). The gold ring before it is about 7 m away and out of frame, so the upper third of the frame is violet metal with lavender lips.
- **Gold ring shape:** a polished band (inner and outer rolled beads with a dark trough) holding 28 fat bulbs, about 0.20 m each, half sunk in gold cups. I removed the clamp plates and rivets, which brought the ring from 23.7k to 16.5k triangles.
- **Lavender lips:** these are now fat, glossy rolled tubes about 0.45 m deep. They're violet with a magenta-pink edge, light streaks and 32 soft pink-white LED studs, three between each pair of gold rings.
- **Walls:**
  - Colour is lighter violet (#9C7CD2) on the side walls, shifting to periwinkle (#8088CC) on the ceiling.
  - Slots are bigger oval holes, 0.60 × 0.34 m.
  - Each slot now shows depth: a lit inner wall near the edge fading to a black bottom.
  - I reduced sheen and sparkles.
- **Metrics:** reference vs ours.

| Region | Reference | Ours (v4) |
|---|---|---|
| Frame brightness (L50) | 0.55 | 0.55 |
| Tunnel ahead | #8c7bbb | #9a79c4 |
| Upper-left walls | #a174a8 | #ae7cba |

  - Palette match is 4.5/10, up from the baseline's 2.9. That figure was measured in a batch that also included the other specialists' changes.

**Best image:** `C:\Users\josia\thanksgiving\Captures\agents\environment\best_vs_ref_9x16.png` (and `best_9x16.png`).

**Domain score:** about 6.5/10, up from about 4.

**Still off**
- The ring centres and vanishing point sit at about x 0.47. In the reference they are at about 0.75–0.80, which comes from the track curve and camera, so it's yours or the owner's call.
- The gold reads tan-orange and the bulbs look like small pale dots; both materials (M_Gold, M_Bulb) belong to lighting.
- The ceiling bays are less blue and less dark than the reference's #5062b0, and the lips are still slightly milky.

**Files changed**
- `Scripts/Editor/SceneBuilder.Environment.cs`
  - I use my own `GoldRingSpacing` (12.75 m) and `FirstRingDistance` (tunnelStart + 9.5 = 71.5 m), with 3 lips per gap plus lips in the first gap.
  - Chamber gaps, portholes and pipes follow the new spacing, which leaves 4 chamber windows instead of 8.
- `Scripts/Editor/MaterialLibrary.Environment.cs`: M_DrumWall, M_DrumRim and M_RimLight retuned.
- `Art/Shaders/BWK_DrumWall.shader`: new slot-depth effect (`_HoleDepth`, `_InnerWall`) and ceiling tint (`_CeilingColor`, `_CeilingTint`, `_CeilingWidth`). The other wall materials, which use the round-hole pattern, are unchanged.
- `Tools/Blender/scripts/build_track.py`: new SM_Ring and SM_DrumRim, the preview layout, and the new camera. This re-exported every Track FBX; only the ring and lip geometry changed.

**Requests**
- **Lighting:**
  - BuildRingLights and the stars' ring-avoidance check still use `tunnelStart + 3` and `RingSpacing` 8.5. Please switch them to `SceneBuilder.FirstRingDistance` and `SceneBuilder.GoldRingSpacing`; the gold rings around the hero frame are at 109.75, 122.5 and 135.25 m.
  - M_Gold: richer amber-orange mid-tones with white-yellow streaks.
  - M_Bulb: a fatter amber glow with an orange halo.
- **Lead:**
  - A full build is needed for the saved scene and for the 12.75 m chamber/pipe layout (both paused).
  - Optionally set `RingSpacing` = 12.75 so everything shares one constant.

Notes are in `C:\Users\josia\thanksgiving\Captures\agents\environment\NOTES.md`.
