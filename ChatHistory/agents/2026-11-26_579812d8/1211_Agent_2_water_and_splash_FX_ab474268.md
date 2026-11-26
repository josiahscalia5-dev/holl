# Agent: Agent 2: water and splash FX

Agent ab474268c06388b9a, lead session 579812d8-e060-4c0e-8af0-5ba372173dc3, started 2026-11-26 12:11 UTC.

_Text-only export: the lead's brief, the agent's statements and one line per tool action (no tool outputs, images, hidden reasoning or system context; e-mails and tokens redacted)._

### Brief from the lead (2026-11-26 12:11 UTC)

You are Agent 2 (water + visual effects specialist, acting as the Claude Unity Game Studio unity-shader-specialist; its "ask before writing" protocol does NOT apply: the owner pre-approved autonomous work inside your files) on the Bubble Wash Kingdom Unity 6.3 URP project at C:\Users\josia\thanksgiving, Round 4, working for the lead (main session). Read first: CLAUDE.md (rules: file ownership under "Parallel specialists", Reference/ privacy, toolchain), Captures/agents/LEAD_DIRECTIVES.md, and Captures/agents/waterfx/NOTES.md (your rounds 1-3). You may load the studio skills unity-lighting-vfx / unity-graphics with the Skill tool if useful.

TARGET: the approved Google Flow video is the strict visual target (owner minimum 9/10, honest scores only from real renders). Hero frame Reference/frames4k/f_03.00s.png (720p original Reference/frames/f_003.00s.png); water correction sheet Reference/correction_pack/03_water_unity.jpg ("deep blue water, curved milky lace and a bright but clean cyan speed arrow"; its "current Unity" panel is an older build). Start from the integrated R4 base: Captures/milestones/m4_r4base_vs_9x16.png (left reference crop, right our Unity render, 07:05 full build with all round-3 work and the gentler bend) and zoom into the water area with Tools/img_crop.py ("C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/img_crop.py IN OUT X0 Y0 X1 Y1 [SCALE]).

LEAD'S GAPS at the hero frame (verify yourself):
1. Splash crowns: ours read as opaque flat white sheets / cauliflower with holes at both sides. Reference: curved milky lace sheets rising beside the feet, milky white with blue tint and translucency in thin areas, thick rounded rims around round holes, finger tips throwing drops, plus moving droplets; feet stay fully visible. Fix shading (milky translucent look, soft Fresnel, light blue in thin parts, no plastic specular) and the silhouette (curved, more lace-like, rounded openings).
2. Water: deeper glossy blue (reference p50 ~#4BA5DB, darker ~#2E86CD), layered flow and normal detail, animated flowing reflections and a sense of depth; no flat cyan, no artificial grid/under-surface lines, no broad white streaks.
3. Chevron arrows: reference has one big SOLID glowing turquoise-cyan chevron right under / in front of the mascot and a large white-cyan chevron at the bottom of the frame, integrated into the water (glow into the water, clean edges). Ours read as thin outlines / hard slabs. Make them filled, glowing, naturally integrated.
4. Bubbles: transparent iridescent (keep); soap foam soft, irregular, clustered (reference: cumulus foam banks on the LEFT ahead at x 0-0.3, y 0.35-0.5 and low on both sides).
Also check the reference 720p sequence 0-3.25 s (Reference/frames4k_720/) so the animation (droplets, crown frames, flow speed) reads right in motion.

YOUR FILES ONLY: SceneBuilder.WaterFX.cs, MaterialLibrary.WaterFX.cs, BWK_Water / BWK_Soft / BWK_Glass shaders, TextureGenerator.cs, SplashFX.cs, SplashCrowns.cs, Tools/Blender/scripts/build_fx_splash.py, build_props.py, Captures/agents/waterfx/. Requests for other domains go into your NOTES.md and final answer.

TOOLING: Unity preview (no save; batched with other agents): bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch fx_r4_vN -bwkOut Captures/agents/waterfx (writes hero_9x16.png + hero_vs_reference_9x16.png there + colour metrics). Blender: bash Tools/blender_run.sh Tools/Blender/scripts/build_fx_splash.py <logname> (BWK_FX_QUICK=1 env = quick preview frames only, as in your notes). Run every Unity/Blender command in the FOREGROUND with the Bash timeout 600000 ms; never kill Unity/Blender; never run the full build or save the scene; never commit. Max 6 Unity previews; after each, copy the side-by-side to Captures/agents/waterfx/r4_vN_vs_ref_9x16.png; revert any change that looks worse. Note: decor chevron spacing / foam layout changes only reach the saved scene in the lead's full build; say which of your changes need it. Images with reference pixels only in Captures/. Time box ~80 minutes.

FINAL ANSWER to the lead (<=300 words): files changed; best preview path; honest water/splash/foam/bubbles score /10 before -> after with evidence; what needs the lead's full build; remaining gaps; requests. Append a "Round 4" section to your NOTES.md.

**Agent (2026-11-26 12:12 UTC):**

> _tool: mcp__ccd_turn__update_plan_

**Agent (2026-11-26 12:12 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\LEAD_DIRECTIVES.md_

**Agent (2026-11-26 12:12 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\NOTES.md_

**Agent (2026-11-26 12:12 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\milestones\m4_r4base_vs_9x16.png_

**Agent (2026-11-26 12:12 UTC):**

> _tool: Bash - List waterfx captures, milestones and reference folders_

**Agent (2026-11-26 12:12 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\correction_pack\03_water_unity.jpg_

**Agent (2026-11-26 12:12 UTC):**

> _tool: Bash - Read correction pack readme and list 4K frames_

**Agent (2026-11-26 12:12 UTC):**

> _tool: Bash - Print image sizes of baseline and reference frames_

**Agent (2026-11-26 12:13 UTC):**

> _tool: Grep - frames4k|refCrop|RefCrop|f_03.00s_

**Agent (2026-11-26 12:13 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\CaptureTools.cs_

**Agent (2026-11-26 12:13 UTC):**

> _tool: Bash - List scripts, shaders and line counts of owned files_

**Agent (2026-11-26 12:13 UTC):**

> _tool: Bash - Read rest of img_crop tool and list Tools folder_

**Agent (2026-11-26 12:13 UTC):**

> _tool: Bash - Time a crop of the 4K reference lower half_

**Agent (2026-11-26 12:14 UTC):**

> _tool: Read - C:\Users\josia\AppData\Local\Temp\claude\3d632b96432924fe\579812d8-e060-4c0e-8af0-5ba372173dc3\scratchpad\ref4k_low.png_

**Agent (2026-11-26 12:14 UTC):**

> _tool: Bash - Read img_stats and unity_run helper scripts_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\3d632b96432924fe\579812d8-e060-4c0e-8af0-5ba372173dc3\scratchpad\cmp.py_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Bash - Make zoomed lower-half reference vs ours crop_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\r4b_low.png_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Bash - Read overlay tool docstring and list lead R4 captures_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\lead\r4\overlay_r4base.png_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.WaterFX.cs_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWKCommon.hlsl_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Bash - List FX runtime scripts and FX asset previews_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\FX_SplashCrown_r3.png_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Runtime\FX\SplashCrowns.cs_

**Agent (2026-11-26 12:15 UTC):**

> _tool: Bash - Crop left and right crown regions reference vs ours_

**Agent (2026-11-26 12:16 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\r4b_crownL.png_

**Agent (2026-11-26 12:16 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\r4b_crownR.png_

**Agent (2026-11-26 12:16 UTC):**

> _tool: Bash - List recent logs and read Blender run helper_

**Agent (2026-11-26 12:16 UTC):**

> _tool: Bash - Inspect previous full crown build log for timings_

**Agent (2026-11-26 12:16 UTC):**

> _tool: Bash - Check time and heavy lock state_

**Agent (2026-11-26 12:17 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\3d632b96432924fe\579812d8-e060-4c0e-8af0-5ba372173dc3\scratchpad\masks.py_

**Agent (2026-11-26 12:17 UTC):**

> _tool: Bash - Row extents of chevron and milk colour classes_

**Agent (2026-11-26 12:18 UTC):**

> _tool: Bash - Per-region colour class means for reference vs ours_

**Agent (2026-11-26 12:18 UTC):**

> _tool: Bash - Crop chevron region reference vs ours_

**Agent (2026-11-26 12:18 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\r4b_chev.png_

**Agent (2026-11-26 12:19 UTC):**

> _tool: Bash - Build a strip of reference 9:16 crops over 0.5-3.0 s_

**Agent (2026-11-26 12:19 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\ref_seq_a.png_

**Agent (2026-11-26 12:20 UTC):**

> _tool: Grep - colorFilter|SplitToning|WhiteBalance|ShadowsMidtonesHighlights|postExposure|Tonemapping|ColorAdjustments|LiftGammaGain|ChannelMixer|fogColor|RenderSettings.fog_

**Agent (2026-11-26 12:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Lighting.cs_

**Agent (2026-11-26 12:20 UTC):**

> _tool: Grep - def build_chevron|SM_Chevron|ARM|arm_w|def chevron_

**Agent (2026-11-26 12:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_props.py_

**Agent (2026-11-26 12:21 UTC):**

> _tool: Bash - Read build_props main and env switches_

**Agent (2026-11-26 12:22 UTC):**

> _tool: Bash - Check water UV conventions and TrackFrame API_

**Agent (2026-11-26 12:22 UTC):**

> _tool: Bash - Read water module profile construction_

**Agent (2026-11-26 12:22 UTC):**

> _tool: Bash - Check how water UVs are authored and deformed_

**Agent (2026-11-26 12:22 UTC):**

> _tool: Bash - Find water surface construction in track builder_

**Agent (2026-11-26 12:22 UTC):**

> _tool: Bash - Find Part class, helpers and chevron users_

**Agent (2026-11-26 12:22 UTC):**

> _tool: Bash - Read Mat helper, Part struct and agent preview flow_

**Agent (2026-11-26 12:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\CaptureTools.cs_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Bash - Check crown references and preview refresh flow_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Bash - Read rest of preview refresh and FX call sites_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Bash - Read the batched preview runner script_

**Agent (2026-11-26 12:24 UTC):**

Now let me make the crown geometry changes in the Blender script (more open lace, right-side family without the skirt).

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_fx_splash.py_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Bash - Update crown script docstring and preview name_

**Agent (2026-11-26 12:24 UTC):**

> _tool: Bash - Build crown splash meshes in Blender (both families)_

**Agent (2026-11-26 12:27 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\FX_SplashCrown_r4.png_

**Agent (2026-11-26 12:27 UTC):**

Crowns rebuilt (more open lace, right asset without the skirt). Now the shader changes: transparent-capable BWK_Soft, softer cyan-white milk, filled chevrons.

**Agent (2026-11-26 12:27 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 12:27 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 12:27 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 12:27 UTC):**

Now the milk (Mode 6) shading with translucent edges.

**Agent (2026-11-26 12:28 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 12:28 UTC):**

> _tool: Grep - ChevronScale|ChevronWidth|ChevronStart|ChevronSpacing|CrownRoot|SM_FX_Crown_

**Agent (2026-11-26 12:28 UTC):**

> _tool: Bash - Check TrackFrame Point API and Mat helper_

**Agent (2026-11-26 12:28 UTC):**

Now the SceneBuilder.WaterFX.cs changes: constants, thick decor chevron mesh with lateral offset, right-crown family.

**Agent (2026-11-26 12:28 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Runtime\FX\SplashCrowns.cs_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Runtime\FX\SplashCrowns.cs_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 12:29 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 12:30 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.WaterFX.cs_

**Agent (2026-11-26 12:30 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.WaterFX.cs_

**Agent (2026-11-26 12:30 UTC):**

> _tool: Edit - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.WaterFX.cs_

**Agent (2026-11-26 12:30 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 12:30 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 12:30 UTC):**

> _tool: Bash - Review edited chevron shading block_

**Agent (2026-11-26 12:30 UTC):**

> _tool: Bash - Run Unity agent preview v1 for water/FX changes_

**Agent (2026-11-26 12:33 UTC):**

> _tool: Bash - Save v1 side-by-side copies_

**Agent (2026-11-26 12:33 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\r4_v1_vs_ref_9x16.png_

**Agent (2026-11-26 12:33 UTC):**

> _tool: Bash - Zoom v1 lower half and compute class colour stats_

**Agent (2026-11-26 12:34 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\v1_low.png_

**Agent (2026-11-26 12:34 UTC):**

> _tool: Bash - Crop bottom part of our v1 render_

**Agent (2026-11-26 12:34 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\v1_ours_bottom.png_

**Agent (2026-11-26 12:37 UTC):**

> _tool: Bash - Zoom apex region and print full herotrack log_

**Agent (2026-11-26 12:37 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\waterfx\z\v1_apex.png_

**Agent (2026-11-26 12:37 UTC):**

> _tool: Bash - Sample rendered chevron, wall, water and crown colours_

**Agent (2026-11-26 12:38 UTC):**

> _tool: Bash - Check current time_

**Agent (2026-11-26 12:38 UTC):**

You've hit your 5-hour limit · resets 11:50am (America/New_York)
