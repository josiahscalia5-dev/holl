# Agent: Water/FX specialist: Round 3 splash and water

Agent a862e55376f12b7c1, lead session ee36a165-51da-442d-ac34-6d0d55e46c0d, started 2026-11-26 10:52 UTC.

_Text-only export: the lead's brief, the agent's statements and one line per tool action (no tool outputs, images, hidden reasoning or system context; e-mails and tokens redacted)._

### Brief from the lead (2026-11-26 10:52 UTC)

You are AGENT 2 - WATER & VISUAL EFFECTS specialist (Unity shader/VFX + Blender FX modelling) for Bubble Wash Kingdom, Round 3. Project: C:\Users\josia\thanksgiving (Unity 6.3 URP + Blender 5.3). CLAUDE.md is loaded for you: follow its file-ownership, heavy-lock and privacy rules exactly. The lead (main session) coordinates, integrates and runs full builds. Work autonomously, do real Blender/Unity work, do not ask questions.

GOAL: make the ONE hero gameplay screen match the owner's approved Google Flow frame at 3.0 s as closely as possible (owner target 8.5-9/10; weighted scorecard: character 25 %, environment 20 %, water/splashes/foam/bubbles 20 %, lighting 20 %, composition 15 %).

REFERENCE (private): 4K hero frame Reference/frames4k/f_03.00s.png (3840x2160). The 4K is an UPSCALE of the 720p original Reference/frames/f_003.00s.png: use both to tell real design detail from sharpening artifacts; neighbouring frames (Reference/frames4k_720/f_02.75s.png, f_03.25s.png) show how the splash moves. Ready 4K splash crop: Captures/lead/r3/ref4k_splash.png (4K region x 1180-2780, y 1080-2160, scaled 0.5). More crops with Tools/img_crop.py (Blender python, usage in its header), only into Captures/agents/waterfx/.

STATE: milestone 2 (honest 6.5/10). The lead just mirrored the track (tunnel now bends right like the reference); the saved scene is that build. Baseline side-by-side (left reference, right Unity): Captures/milestones/m3_r3base_mirror_vs_9x16.png. Your previous notes (measured hero camera, crown anchoring, what was tried): Captures/agents/waterfx/NOTES.md - read first, do not redo work. Live directives: Captures/agents/LEAD_DIRECTIVES.md.

WHAT TO FIX (priority order):
1 SPLASH CROWNS (biggest gap). Reference: a thick, dense, bright milky "milk-crown" splash hugging both feet and spreading outward - a continuous curved milky sheet with ROUND holes of varied size, thick rounded rims, irregular scalloped top edge with droplet beads, lots of flying droplets; white core with faint blue translucency in thin areas; fills roughly screen x 0-0.40 / 0.62-1.0, y 0.60-0.86 of the portrait frame, both feet stay visible. Ours: thin white coral-like branches far out at the frame edges. Rebuild as real curved 3D splash geometry in Blender (sheet-with-holes crown surface: e.g. a curved, thickened sheet perforated with round holes via Voronoi/boolean or SDF remesh, rims beaded, plus droplet meshes), soft milky shading (BWK_Soft/BWK_Glass: wrap lighting, soft subsurface-like glow, fresnel), anchored close to the feet, animated in play (SplashFX/SplashCrowns: frame cycling or vertex rise/fall + droplet particles) so it is alive while he slides. Not generic white particles.
2 WATER. Owner: current water is excessively bright cyan, flat, and shows a grid/tile pattern. Build a layered BWK_Water: deep blue -> turquoise colour variation, flow-mapped / two scrolling normal maps, soft fresnel reflections and specular glints, convincing motion, soft water-to-foam transitions; cyan only where the reference has it (chevrons, glints). Sample the reference colours (Tools/img_stats.py or crops) and match values, not just hue.
3 CHEVRONS: clean glowing cyan arrows IN the water (turquoise core, crisp bright rim, soft glow) like the reference - ours read as hard teal 3D slabs. No excessive bloom.
4 BUBBLES + FOAM: transparent iridescent glass bubbles (thin rims, rainbow fresnel, highlight dot), clusters lower-left and right as in the reference; soft white-pink cumulus foam banks along the LEFT side of the track ahead (reference screen x 0-0.25, y 0.35-0.50; after the mirror ours appear on the right - fix the placement).

YOUR FILES ONLY: Assets/BubbleWashKingdom/Scripts/Editor/SceneBuilder.WaterFX.cs, MaterialLibrary.WaterFX.cs (also owns M_RailPink / M_RailRainbow materials - rail GEOMETRY is environment's), TextureGenerator.cs; shaders BWK_Water, BWK_Soft, BWK_Glass; Scripts/Runtime/FX/SplashFX.cs and SplashCrowns.cs; Tools/Blender/scripts/build_fx_splash.py, build_props.py; Art/Models/FX/*, Art/Models/Props/*; Docs/AssetPreviews/FX_*.png (OUR renders only - public on GitHub, never reference pixels). Anything else: write a request.

PROCESS: check splash geometry in a Blender preview render first, then Unity:
  Blender: bash Tools/blender_run.sh Tools/Blender/scripts/<script>.py <logname>
  Unity preview (batched with other agents, no scene save): bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <logname> -bwkOut Captures/agents/waterfx
  -> Captures/agents/waterfx/hero_9x16.png + hero_vs_reference_9x16.png (+ colour metrics). Previews rebuild textures, materials, runner FX (crowns, bubbles, chevrons near him) and your preview foam in memory; things baked only by the full build (decor chevrons/boost pads spacing, saved foam) show after the lead's build - say so in your report.
Camera is frozen (2.75/1.3/10/58 at track 105.5 m): never change it or the capture framing. Heavy runs are serialized by Tools/heavy_lock.sh (waiting is normal). Never run the full build, never save the scene, never start Unity/Blender directly, never kill another process, no git commands that change anything. Max ~6 Unity previews; revert changes that look worse; if an approach fails twice, change the construction method. Mobile-friendly but quality first. Run `date` now and finish by 06:55 local time (about 60 minutes) with your best result; the lead will send a follow-up pass.

DELIVERABLES: Captures/agents/waterfx/best_9x16.png + best_vs_ref_9x16.png; Docs/AssetPreviews/FX_SplashCrown_r3.png (Blender render); append "## Round 3" to Captures/agents/waterfx/NOTES.md. FINAL REPLY (return value, plain text, max 350 words): what changed (files), best preview path, honest score /10 for water, splashes, foam, bubbles vs the reference, biggest remaining differences, whether a lead full build is needed and why, requests to other domains.

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Show time, list waterfx captures and lead directives_

**Agent (2026-11-26 10:52 UTC):**

> _tool: mcp__ccd_turn__update_plan_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Read previous waterfx notes_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\milestones\m3_r3base_mirror_vs_9x16.png_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\lead\r3\ref4k_splash.png_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Survey owned files and tools_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Read current splash Blender script_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Read SceneBuilder.WaterFX.cs part 1_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Read SceneBuilder.WaterFX.cs part 2_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Check previous FX run times, mirror implementation, helpers_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - List blender logs and heavy lock script_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Check previous splash build timing and lock state_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\FX_SplashCrown.png_

**Agent (2026-11-26 10:54 UTC):**

> _tool: Bash - Read SplashCrowns runtime and latest hero cam measurement_

**Agent (2026-11-26 10:54 UTC):**

> _tool: Bash - Get hero cam measurement from mirrored build_

**Agent (2026-11-26 10:55 UTC):**

> _tool: Bash - Find mascot foot positions in Blender scripts_

**Agent (2026-11-26 10:55 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\correction_pack\03_water_unity.jpg_

**Agent (2026-11-26 10:56 UTC):**

> _tool: Bash - Read FX material library and preview helper_

**Agent (2026-11-26 10:56 UTC):**

> _tool: Bash - Read bwk_common helpers_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Bash - Back up current FX script, meshes and shaders_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Bash - Draft new perforated-sheet crown shape code_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 10:59 UTC):**

> _tool: Write - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 10:59 UTC):**

> _tool: Bash - Quick Blender crown build with hero-camera preview_

**Agent (2026-11-26 10:59 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\FX_SplashCrown_r3.png_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Bash - Patch crown into curtain + skirt sheets facing the camera_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\ee36a165-51da-442d-ac34-6d0d55e46c0d\scratchpad\patch1.py_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\ee36a165-51da-442d-ac34-6d0d55e46c0d\scratchpad\sheets_block.py_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Bash - Apply patch and run quick crown build_

**Agent (2026-11-26 11:03 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\FX_SplashCrown_r3.png_

**Agent (2026-11-26 11:04 UTC):**

> _tool: Bash - Make crowns taller and skirt rise more, rerun quick_

**Agent (2026-11-26 11:07 UTC):**

> _tool: Bash - Find crown placement references_

**Agent (2026-11-26 11:07 UTC):**

> _tool: Bash - Switch crown placement to runner-local authored roots_

**Agent (2026-11-26 11:07 UTC):**

> _tool: Bash - Tidy comment, check Blender job and lock holder_

**Agent (2026-11-26 11:07 UTC):**

> _tool: Bash - Read water shader_

**Agent (2026-11-26 11:07 UTC):**

> _tool: Bash - Check img_stats usage and Blender job status_

**Agent (2026-11-26 11:07 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\ee36a165-51da-442d-ac34-6d0d55e46c0d\scratchpad\sample.py_

**Agent (2026-11-26 11:08 UTC):**

> _tool: Bash - Sample reference vs ours water colours_

**Agent (2026-11-26 11:08 UTC):**

> _tool: Bash - Crop our water areas from the baseline_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z_base3_bottom.png_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z_base3_ahead.png_

**Agent (2026-11-26 11:09 UTC):**

> _tool: TaskStop_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Bash - Verify quick job stopped and lock state_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Bash - Full 12-frame crown build with hero preview_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Bash - Locate chevron shading and mesh build_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Bash - Read chevron shading and chevron mesh code_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Bash - Update M_Water material values_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 11:10 UTC):**

> _tool: Bash - Update arrow material and flatten decor chevrons_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Restore chevron height, find HeroDistance and FlatPoint_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Locate foam placement lines_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Find the foam loop to set heroD_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Set heroD in foam loop, check Blender job_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Strengthen detail ripples, read milk shading_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Check lock holder_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Confirm HeroDistance and flatRight definitions_

**Agent (2026-11-26 11:12 UTC):**

> _tool: Bash - After Blender export, run Unity agent preview_

**Agent (2026-11-26 11:12 UTC):**

> _tool: Bash - Review foam edit and unity_run script_

**Agent (2026-11-26 11:12 UTC):**

> _tool: Bash - Check Blender job progress_

**Agent (2026-11-26 11:12 UTC):**

> _tool: Bash - Wait for the Blender crown build to finish_

**Agent (2026-11-26 11:15 UTC):**

> _tool: Bash - Check Blender job progress_

**Agent (2026-11-26 11:15 UTC):**

> _tool: Bash - Wait for crown build completion_

**Agent (2026-11-26 11:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\FX_SplashCrown_r3.png_

**Agent (2026-11-26 11:15 UTC):**

> _tool: Bash - Check Unity preview queue state_

**Agent (2026-11-26 11:16 UTC):**

> _tool: Bash - Crown v2: upright skirt, thinner roll; start build_

**Agent (2026-11-26 11:16 UTC):**

> _tool: Bash - Verify the Blender v2 job is alive_

**Agent (2026-11-26 11:16 UTC):**

> _tool: Bash - Check for running v2 job processes_

**Agent (2026-11-26 11:16 UTC):**

> _tool: Bash - Check queue progress_

**Agent (2026-11-26 11:17 UTC):**

> _tool: Bash - Read preview batch script_

**Agent (2026-11-26 11:17 UTC):**

> _tool: Bash - Find the current batch run and its requests_

**Agent (2026-11-26 11:17 UTC):**

> _tool: Bash - Identify which requests the current batch serves_

**Agent (2026-11-26 11:17 UTC):**

> _tool: Bash - Verify water shader edit order_

**Agent (2026-11-26 11:17 UTC):**

> _tool: Bash - Fade under-surface streak lines_

**Agent (2026-11-26 11:17 UTC):**

> _tool: Bash - Wait for crown v2 Blender build_

**Agent (2026-11-26 11:20 UTC):**

> _tool: Bash - Check lock and queue_

**Agent (2026-11-26 11:20 UTC):**

> _tool: Bash - Wait for crown v2 build to finish_

**Agent (2026-11-26 11:20 UTC):**

> _tool: Bash - Check lock status after a short wait_

**Agent (2026-11-26 11:21 UTC):**

> _tool: Bash - Check the running batch log for compile errors_

**Agent (2026-11-26 11:21 UTC):**

> _tool: Bash - Watch batch log for compile errors and waterfx lines_

**Agent (2026-11-26 11:22 UTC):**

> _tool: Bash - Watch batch log progress_

**Agent (2026-11-26 11:23 UTC):**

> _tool: Bash - Inspect crown v2 build result_

**Agent (2026-11-26 11:23 UTC):**

> _tool: Bash - Check batch log end and my preview job output_

**Agent (2026-11-26 11:24 UTC):**

> _tool: Bash - Search batch log for exceptions and capture lines_

**Agent (2026-11-26 11:24 UTC):**

> _tool: Bash - Wait for batch preview to finish_

**Agent (2026-11-26 11:24 UTC):**

> _tool: Bash - Check whether preview images were delivered_

**Agent (2026-11-26 11:24 UTC):**

> _tool: Bash - Wait for the batch to report served_

**Agent (2026-11-26 11:25 UTC):**

> _tool: Bash - Save v1 preview and sample colours_

**Agent (2026-11-26 11:26 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\r3b_v1_vs_9x16.png_

**Agent (2026-11-26 11:26 UTC):**

> _tool: Bash - Crown v3 skirt; brighter milk, arrows, turquoise water_

**Agent (2026-11-26 11:26 UTC):**

> _tool: Bash - Crown v3 build then Unity preview_

**Agent (2026-11-26 11:26 UTC):**

> _tool: Bash - Crop v1 splash region_

**Agent (2026-11-26 11:27 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z_r3b_v1_splash.png_

**Agent (2026-11-26 11:27 UTC):**

> _tool: Bash - Check v3 chain progress_

**Agent (2026-11-26 11:27 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\ee36a165-51da-442d-ac34-6d0d55e46c0d\scratchpad\patch2.py_

**Agent (2026-11-26 11:27 UTC):**

> _tool: Bash - Apply sheet undulation before v3 Blender starts_

**Agent (2026-11-26 11:27 UTC):**

> _tool: Bash - Check lock progress_

**Agent (2026-11-26 11:28 UTC):**

> _tool: Bash - Wait for crown v3 Blender build_

**Agent (2026-11-26 11:29 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\FX_SplashCrown_r3.png_

**Agent (2026-11-26 11:30 UTC):**

> _tool: Bash - Append Round 3 notes draft_

**Agent (2026-11-26 11:30 UTC):**

> _tool: Bash - Check Unity preview queue_

**Agent (2026-11-26 11:30 UTC):**

> _tool: Bash - Wait for the v2 preview batch_

**Agent (2026-11-26 11:32 UTC):**

> _tool: Bash - Save v2 preview and compute metrics_

**Agent (2026-11-26 11:32 UTC):**

You've hit your 5-hour limit · resets 10:30am (America/New_York)
