# Agent: Character specialist: Round 3 mascot rebuild

Agent adc2459d8b734b8a0, lead session ee36a165-51da-442d-ac34-6d0d55e46c0d, started 2026-11-26 10:51 UTC.

_Text-only export: the lead's brief, the agent's statements and one line per tool action (no tool outputs, images, hidden reasoning or system context; e-mails and tokens redacted)._

### Brief from the lead (2026-11-26 10:51 UTC)

You are AGENT 1 - CHARACTER & ANIMATION specialist (Blender modeller + technical artist) for Bubble Wash Kingdom, Round 3. Project: C:\Users\josia\thanksgiving (Unity 6.3 URP + Blender 5.3). CLAUDE.md is loaded for you: follow its file-ownership, heavy-lock and privacy rules exactly. The lead (main session) coordinates, integrates and runs full builds. Work autonomously, do real Blender/Unity work, do not ask questions.

GOAL: make the ONE hero gameplay screen match the owner's approved Google Flow frame at 3.0 s as closely as possible (owner target 8.5-9/10; weighted scorecard: character shape/fur/clothing 25 %, environment 20 %, water/splash 20 %, lighting 20 %, composition 15 %). Your domain is the biggest single weight.

REFERENCE (private): 4K hero frame Reference/frames4k/f_03.00s.png (3840x2160). The 4K is an UPSCALE of the 720p original Reference/frames/f_003.00s.png: use both to tell real design detail from sharpening artifacts. A ready 4K mascot crop: Captures/lead/r3/ref4k_mascot.png (4K region x 1500-2460, y 480-1700, scaled 0.75). Make more crops with Tools/img_crop.py (Blender python, usage in its header), only into Captures/agents/character/.

STATE: milestone 2 (honest 6.5/10). The lead just mirrored the track (tunnel now bends right like the reference); the saved scene is that build. Baseline side-by-side (left reference, right Unity, 720x1280 each half): Captures/milestones/m3_r3base_mirror_vs_9x16.png. Your previous round notes (measured hero-camera numbers, what was tried): Captures/agents/character/NOTES.md - read first, do not redo work. Live directives: Captures/agents/LEAD_DIRECTIVES.md (also printed after every heavy run).

MEASURED GAPS (lead, fractions of the 720x1280 portrait frame; ref vs ours):
- Hat cuff width 0.61 W vs 0.55 W: the reference hat is WIDER than the body and overhangs it; ours equals the body width.
- Body width just below the cuff 0.47 W vs 0.54 W: our body is too wide/spherical. Reference = soft rounded pear, narrower under the hat, seat rounding at the bottom; body height below the cuff ~0.15 H.
- Hat height (visible crown under the pom-pom -> cuff bottom) ~0.18 H vs 0.14 H: reference crown dome is taller and rounder, the pale stripe is thick (~0.045 H) and the purple folded cuff below it ~0.07 H. Ours reads as flat stacked tubes with a fine horizontal stockinette texture.
- Knit: reference has bold VERTICAL rib knit on crown, stripe and cuff (~40-48 ribs around the full circumference, deep grooves that read at gameplay distance). Stripe = pale lavender-white with crisp ribs.
- Pom-pom diameter 0.28 W vs 0.32 W; ref centre ~(0.49, 0.30), ours (0.48, 0.37). Reference pom-pom = starburst: fibres radiating from a darker violet centre to light lilac tips, fuzzy irregular silhouette, sinks slightly into the crown top. Ours = smooth velvet ball. Replace the construction (e.g. real fibre cards/strands generated in Blender with Geometry Nodes or bmesh, or a dense radial card cluster with an alpha fibre texture you bake), not another shader tweak.
- Fur: reference = long, soft, irregular clumped plush pile, warm coral pink with lighter tips, paler pink-white toward the seat/bottom; ours = short uniform velvet. Use longer shells with clumping + direction noise (BWK_Fur) and/or fur cards; mobile-friendly but beautiful.
- Arms: reference arms are short and thick, emerge from under the hat brim, raised ~40-45 deg up and outward, paws with light pink pads at the tips; ours are long and come out lower.
- Feet: reference = big soft white soles with pink pads (one big pad + 4 toe beans) facing the camera at lower left/right, centres ~(0.32, 0.66) and (0.72, 0.66), bottom edge y ~0.71; ours ~(0.25, 0.69)/(0.60, 0.71), bottom 0.75, slightly flat/lilac.
- The whole figure sits ~0.04 H higher in the reference (pom-pom top 0.23 vs 0.28) while total height matches; fix through proportions/seat depth (taller hat, less sunk), never by floating him above the water. Mascot horizontal offset comes from the frozen camera - not yours.

HARD RULES (owner): he SITS on his bottom, body faces the direction of travel, back of hat/pom-pom/fluffy back toward the camera; feet visible as in the reference; never turn the head alone, never face the camera in gameplay, never a floating ball. Camera is frozen (2.75/1.3/10/58 at track 105.5 m): never change it. Keep the 17 bone names and 13 clip names (AnimatorBuilder is lead-owned). Natural sliding animation: Slide pose sampled at t = 0.25 s is the hero pose; keep other clips sensible.

YOUR FILES ONLY: Tools/Blender/scripts/build_mascot_model.py, build_mascot_rig.py, fix_mascot_normals.py; Assets/BubbleWashKingdom/Art/Shaders/BWK_Fur.shader, BWK_Character.shader; Assets/BubbleWashKingdom/Scripts/Editor/MaterialLibrary.Character.cs; Assets/BubbleWashKingdom/Art/Models/Characters/*; Assets/BubbleWashKingdom/Art/Textures/Character/* (create for baked knit/fibre maps); Docs/AssetPreviews/SK_Mascot_r3_*.png (OUR renders only - that folder is public on GitHub, never put reference pixels there). Anything else: write a request.

PROCESS: Blender first. Use build_mascot_rig.py's hero game-view render (render_game_view, QUICK mode) to compare against the reference crop BEFORE spending a Unity preview; make front, side and rear inspection renders (Docs/AssetPreviews/SK_Mascot_r3_front/side/rear.png) and a hero game-view render. Then export SK_Mascot.fbx and run a Unity preview:
  Blender: bash Tools/blender_run.sh Tools/Blender/scripts/<script>.py <logname>
  Unity preview (batched with other agents, no scene save): bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <logname> -bwkOut Captures/agents/character
  -> Captures/agents/character/hero_9x16.png + hero_vs_reference_9x16.png (+ colour metrics). The saved scene holds an instance of the SK_Mascot.fbx model, so a re-exported FBX shows in previews.
Heavy runs are serialized by Tools/heavy_lock.sh (other agents may be ahead of you; waiting is normal). Never run the full build, never save the scene, never start Unity/Blender directly, never kill another process, no git commands that change anything. Max ~6 Unity previews; if a change looks worse, revert it. If an approach fails to improve after two meaningful attempts, change the construction method. Run `date` now and finish by 06:55 local time (about 60 minutes) with your best result, even if not perfect; the lead will send a follow-up pass.

DELIVERABLES: Captures/agents/character/best_9x16.png + best_vs_ref_9x16.png (copies of your best Unity preview); the Blender inspection renders; append a "## Round 3" section to Captures/agents/character/NOTES.md. FINAL REPLY (your return value, plain text, max 350 words): what changed (files), paths of best Unity preview and Blender renders, honest score /10 for mascot proportions, fur, hat+pom-pom and seated pose vs the reference, the biggest remaining differences, whether a lead full build is needed and why, requests to other domains.

**Agent (2026-11-26 10:51 UTC):**

> _tool: Bash - Show time, list character captures, read lead directives_

**Agent (2026-11-26 10:51 UTC):**

> _tool: mcp__ccd_turn__update_plan_

**Agent (2026-11-26 10:51 UTC):**

> _tool: Bash - Read previous character notes_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Survey file sizes and capture folders_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\lead\r3\ref4k_mascot.png_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\milestones\m3_r3base_mirror_vs_9x16.png_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - List functions and constants in model script_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Read model script header and parameters_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Read hat helpers, body and beanie builders_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - List rig script functions and run wrappers_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Check recent logs and rig main flow_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Inspect previous Blender model/rig run logs_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\blender_r3_vs_ref.png_

**Agent (2026-11-26 10:52 UTC):**

> _tool: Bash - Read img_crop usage and list tools_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Read character material library_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Read fur shader_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Inspect character shader knit code_

**Agent (2026-11-26 10:53 UTC):**

> _tool: Bash - Read character shader fragment_

**Agent (2026-11-26 10:54 UTC):**

> _tool: Bash - Find material remap code and shell builder_

**Agent (2026-11-26 10:54 UTC):**

> _tool: Bash - Find Unity material remap and fur tagging_

**Agent (2026-11-26 10:55 UTC):**

> _tool: Bash - Find hat contract usage between scripts_

**Agent (2026-11-26 10:55 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\correction_pack\02_mascot_blender.jpg_

**Agent (2026-11-26 10:55 UTC):**

> _tool: Bash - Read seat solver and arm/leg builders_

**Agent (2026-11-26 10:56 UTC):**

> _tool: Bash - Check FBX material remap timing in preview_

**Agent (2026-11-26 10:56 UTC):**

> _tool: Bash - Check vertex colour writing and materials setup_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Bash - Read preview rendering code_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:57 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:58 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:58 UTC):**

> _tool: Bash - Check MeshData and pompom usage in main_

**Agent (2026-11-26 10:58 UTC):**

> _tool: Bash - Check normal checks and main assembly_

**Agent (2026-11-26 10:58 UTC):**

> _tool: Bash - Assign fibre material slot to PomPom object_

**Agent (2026-11-26 10:58 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 10:58 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_rig.py_

**Agent (2026-11-26 10:59 UTC):**

> _tool: Bash - Run Blender model and quick rig build_

**Agent (2026-11-26 10:59 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 11:00 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 11:00 UTC):**

> _tool: Bash - Check Blender run progress and lock_

**Agent (2026-11-26 11:00 UTC):**

> _tool: Bash - Check model log details_

**Agent (2026-11-26 11:00 UTC):**

> _tool: Bash - Back up material library before edits_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Character.cs_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Character.cs_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Character.cs_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Bash - Check rig run results_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Bash - Get image sizes for comparison_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\ee36a165-51da-442d-ac34-6d0d55e46c0d\scratchpad\cmp.py_

**Agent (2026-11-26 11:01 UTC):**

> _tool: Bash - Compose Blender game view vs reference_

**Agent (2026-11-26 11:02 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\r3_b1_vs_ref.png_

**Agent (2026-11-26 11:03 UTC):**

> _tool: Bash - Apply hat, pom-pom and feet parameter tweaks_

**Agent (2026-11-26 11:04 UTC):**

> _tool: Bash - Implement bent stubby arms in model script_

**Agent (2026-11-26 11:04 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_rig.py_

**Agent (2026-11-26 11:04 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_rig.py_

**Agent (2026-11-26 11:04 UTC):**

> _tool: Bash - Read rig render function_

**Agent (2026-11-26 11:04 UTC):**

> _tool: Bash - Run model and rig with inspection renders_

**Agent (2026-11-26 11:05 UTC):**

> _tool: Bash - Back up fur shader, check helper signatures_

**Agent (2026-11-26 11:05 UTC):**

Now the tuft-clumping upgrade in BWK_Fur (strands converge into irregular plush tufts with partings).

**Agent (2026-11-26 11:05 UTC):**

> _tool: Bash - Add tuft clumping to fur shader_

**Agent (2026-11-26 11:05 UTC):**

> _tool: Bash - Fix tuft parting to use root cell bounds_

**Agent (2026-11-26 11:05 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Character.cs_

**Agent (2026-11-26 11:05 UTC):**

> _tool: Bash - Check second Blender run progress_

**Agent (2026-11-26 11:06 UTC):**

> _tool: Bash - Inspect second model and rig logs_

**Agent (2026-11-26 11:06 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 11:06 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_mascot_model.py_

**Agent (2026-11-26 11:06 UTC):**

> _tool: Bash - Check lock holder and rig progress_

**Agent (2026-11-26 11:06 UTC):**

> _tool: Bash - Wait for rig run to finish and show results_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Bash - Compose second Blender game view vs reference_

**Agent (2026-11-26 11:09 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\r3_b2_vs_ref.png_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Apply proportion fixes and rerun model and rig_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Verify the Blender run is alive_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Check image stats tool and agent folders_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Wait for model run and check GN fibre path_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Queue Unity agent preview after the rig export_

**Agent (2026-11-26 11:11 UTC):**

> _tool: Bash - Check which process holds the heavy lock_

**Agent (2026-11-26 11:12 UTC):**

> _tool: Bash - Wait for rig, then compose new game view vs reference_

**Agent (2026-11-26 11:14 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\r3_b3_vs_ref.png_

**Agent (2026-11-26 11:15 UTC):**

> _tool: Bash - Check preview batch status_

**Agent (2026-11-26 11:15 UTC):**

> _tool: Bash - Apply crown/pom-pom/arm tweaks and queue next Blender run_

**Agent (2026-11-26 11:15 UTC):**

> _tool: Bash - Wait for the b4 Blender run_

**Agent (2026-11-26 11:18 UTC):**

> _tool: Bash - Read Unity preview v1 output and timing_

**Agent (2026-11-26 11:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\hero_vs_reference_9x16.png_

**Agent (2026-11-26 11:19 UTC):**

> _tool: Bash - Warp tuft cells and soften partings in fur shader_

**Agent (2026-11-26 11:19 UTC):**

> _tool: Bash - Use unwarped strand lookup with tuft offsets_

**Agent (2026-11-26 11:20 UTC):**

> _tool: Bash - Patch feet, fibre colours, foot lift and fur colours_

**Agent (2026-11-26 11:20 UTC):**

> _tool: Bash - Wait for b4 rig and compose its game view_

**Agent (2026-11-26 11:21 UTC):**

> _tool: Bash - Chain b5 model, rig and Unity preview v2_

**Agent (2026-11-26 11:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\r3_b4_vs_ref.png_

**Agent (2026-11-26 11:22 UTC):**

> _tool: Bash - Crop the Unity v1 mascot region_

**Agent (2026-11-26 11:22 UTC):**

> _tool: Bash - Crop the Unity v1 mascot at native size_

**Agent (2026-11-26 11:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\r3_v1_zoom.png_

**Agent (2026-11-26 11:22 UTC):**

> _tool: Bash - Check whether the b5 model run started_

**Agent (2026-11-26 11:22 UTC):**

> _tool: Bash - Narrow the body slightly and soften tufts_

**Agent (2026-11-26 11:22 UTC):**

> _tool: Bash - Save v1 preview copies and a before crop_

**Agent (2026-11-26 11:23 UTC):**

> _tool: Bash - Check queue progress_

**Agent (2026-11-26 11:23 UTC):**

> _tool: Bash - Append Round 3 notes draft_

**Agent (2026-11-26 11:23 UTC):**

> _tool: Bash - Wait for the b5 model run_

**Agent (2026-11-26 11:24 UTC):**

> _tool: Bash - Wait for b5 rig and compose game view_

**Agent (2026-11-26 11:27 UTC):**

> _tool: Bash - Check why the rig run is slow_

**Agent (2026-11-26 11:27 UTC):**

> _tool: Bash - Check running heavy processes and lock script_

**Agent (2026-11-26 11:28 UTC):**

> _tool: Bash - Wait for b5 rig completion_

**Agent (2026-11-26 11:28 UTC):**

> _tool: Bash - Compose b5 Blender game view vs reference_

**Agent (2026-11-26 11:28 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\character\r3_b5_vs_ref.png_

**Agent (2026-11-26 11:29 UTC):**

> _tool: Bash - Make a strip of the inspection renders_

**Agent (2026-11-26 11:29 UTC):**

> _tool: Read - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\ee36a165-51da-442d-ac34-6d0d55e46c0d\scratchpad\r3_inspect.png_

**Agent (2026-11-26 11:29 UTC):**

> _tool: Bash - Wait for Unity preview v2 to finish_

**Agent (2026-11-26 11:29 UTC):**

> _tool: Bash - Find the cause of the Unity batch failure_

**Agent (2026-11-26 11:29 UTC):**

> _tool: Bash - Read the failed Unity log_

**Agent (2026-11-26 11:29 UTC):**

> _tool: Bash - Confirm failure reason and current lock state_

**Agent (2026-11-26 11:30 UTC):**

> _tool: Bash - Re-queue the Unity preview v2_

**Agent (2026-11-26 11:30 UTC):**

> _tool: Bash - Review the final tuft shader code_

**Agent (2026-11-26 11:30 UTC):**

> _tool: Bash - Wait for a fresh v2 hero comparison_

**Agent (2026-11-26 11:33 UTC):**

You've hit your 5-hour limit · resets 10:30am (America/New_York)
