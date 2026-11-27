# Agent: Agent 2 water & VFX

Agent af071b32161ee8c36, lead session b3410996-81ad-4e2d-9d43-bf3d56c2a918, started 2026-11-26 02:20 UTC.

_Text-only export: the lead's brief, the agent's statements and one line per tool action (no tool outputs, images, hidden reasoning or system context; e-mails and tokens redacted)._

### Brief from the lead (2026-11-26 02:20 UTC)

You are AGENT 2 - WATER AND VISUAL EFFECTS, one of four specialist agents improving the Unity game "Bubble Wash Kingdom" (Unity 6.3 URP, portrait 9:16) in C:\Users\josia\thanksgiving. The lead developer (the main session) coordinates you and is the ONLY one who builds/saves the main scene. Follow the project CLAUDE.md (independence rule, never use the reference video or frames as textures, Reference/ is private).

OWNER DIRECTIVE (highest priority): achieve the closest possible visual match to the owner's approved Google Flow video. Visual quality beats token cost, development effort and mobile optimization. Use high-quality custom assets instead of simplistic procedural substitutes wherever it matters. Target 9-10/10 similarity. Do not claim success without actual rendered evidence. Keep the computer stable and normal security protections intact.

GOAL: make the water, splashes, foam and bubbles of the HERO GAMEPLAY SCREEN (rear camera inside the tunnel; mascot sits on his bottom, feet forward, back to the camera - never change that) match the reference.

REFERENCE (do NOT re-analyse the whole video, use only these): Reference/frames/f_003.00s.png (hero target), Reference/frames/f_001.75s.png, f_002.50s.png, f_003.25s.png (rear views with splashes), Reference/key/04_very_middle_7.52s.png and f_005.00s.png (big splash crowns, chevrons), Reference/contact_sheet_*.jpg (overview).
CURRENT STATE: Captures/compare/hero_vs_reference_9x16.png and _16x9.png (LEFT = reference, RIGHT = our real Unity render), Captures/stills/*.png, Docs/AssetPreviews/Props_set.png.

YOUR FILES (edit ONLY these): Assets/BubbleWashKingdom/Art/Shaders/BWK_Water.shader, BWK_Soft.shader (Mode 0 foam, Mode 1 rails, Mode 4 fabric; Mode 2/3 are legacy copies - the beanie and eyes now use BWK/Character owned by Agent 1), BWK_Glass.shader (glass + soap bubbles); Assets/BubbleWashKingdom/Scripts/Editor/SceneBuilder.WaterFX.cs (BuildFoam, BuildFloatingBubbles, BuildRunnerFX, Particles, BuildDecorChevrons); MaterialLibrary.WaterFX.cs; TextureGenerator.cs; Assets/BubbleWashKingdom/Scripts/Runtime/FX/SplashFX.cs (you may add new runtime FX scripts under Scripts/Runtime/FX/); Tools/Blender/scripts/build_props.py (foam, bubble, chevron, coin, gem, neon star, laundry meshes - keep every exported name, slot names and origin conventions); Assets/BubbleWashKingdom/Art/Models/Props/*; Docs/AssetPreviews/Props_set.png. Never edit, delete, revert or reformat anyone else's files; put needed changes elsewhere in your report under "lead requests". Never git commit/push/reset/checkout/stash. Never run SceneBuilder.BuildAllBatch (lead only); never save the scene.

HEAVY PROCESSES (4-thread / 7.7 GB laptop shared by four agents): never start Unity or Blender directly. Use only:
  * Blender: bash Tools/blender_run.sh Tools/Blender/scripts/build_props.py <logname>
  * Unity no-save preview: bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <logname> -bwkOut Captures/agents/waterfx
Both wait on a project-wide lock (another agent may hold it for minutes): call them with the Bash tool using timeout 600000 or run_in_background true and wait for the completion notification; never loop-poll, never kill other processes, never delete Logs/heavy.lock unless the script itself reports it stale. Batch several changes into each heavy run. The Unity preview regenerates textures and all materials, re-imports changed meshes/shaders, rebuilds lighting/post and the runner splash FX (BuildRunnerFX) in memory, and simulates the slide FX before rendering hero_9x16.png, hero_16x9.png and side-by-side comparisons into your folder. It does NOT reflect foam / bubble / chevron placement or combined environment meshes - those appear after the lead's integration build (ask the lead via SendMessage when you need one). Read PNGs with the Read tool. C# SAFETY: a C# compile error breaks every Unity run for everyone, so keep every .cs edit compilable and check the preview summary for "error CS"; check for "Shader error" too.

GAPS vs the reference, most visible first:
 1. SPLASH: reference = bright, opaque, milky-white crown splashes at the feet on both sides, rising about a third of the body, lace-like with holes, thick rounded tendrils with droplet tips, many droplets and small bubbles, plus white spray along the slide. Ours = pale-blue translucent "hand" shapes (TextureGenerator.SplashCrown -> T_SplashCrown, M_FX_SplashSheet, emitters SplashSheetL/R + Spray in BuildRunnerFX, rates in SplashFX). Consider real 3D splash meshes (animated crown sheets) or higher-quality textures/flipbooks; shading must read creamy white with soft blue-grey shading and highlights.
 2. WATER: BWK_Water (streaks, sparkles, rainbow sheen). Reference water is brighter turquoise-cyan, glossy and translucent-looking, with speed lines, light caustic glints and a continuous line of glowing cyan chevron arrows with white rims down the middle (DecorChevrons placement + M_Arrow / M_ArrowRim material values are yours; the FlowGlow shader code belongs to Agent 3 - ask via lead requests if you need shader changes).
 3. BANKS / RAILS: reference banks are wide glossy hot-pink candy surfaces with rainbow light streaks (pink, orange, yellow, cyan) racing along them (BWK_Soft Mode 1, M_RailPink, M_RailRainbow). Slide geometry belongs to Agent 3 - change only shading.
 4. FOAM: reference = big puffy white cumulus clouds with soft lavender-blue crevice shading and bright rims on both banks. Ours has good shapes but flat white shading (BWK_Soft Mode 0); improve shading/geometry (build_props.py foam meshes, BuildFoam density); the owner relaxed mobile budgets but keep the editor responsive.
 5. BUBBLES: reference has large iridescent soap bubbles near the camera (rainbow thin-film colours, white window highlights, mostly transparent centre); ours are faint (M_Bubble, BWK_Glass, SM_Bubble, BuildFloatingBubbles, AmbientBubbles particles).
Do as many refinement passes as needed to get close to the reference.

COORDINATION: if you need something from the lead (an integration build to see placement changes, or a change in a file you do not own), send it with SendMessage to "main" and keep working meanwhile.

FINAL REPORT (your last message): what you changed (files), evidence (paths of your best preview images), remaining differences vs the reference, lead requests (exact file / function / values), cost notes, and an honest 1-10 similarity score for your domain.

**Agent (2026-11-26 02:20 UTC):**

I'll start by looking at the current state and my files.

**Agent (2026-11-26 02:20 UTC):**

> _tool: mcp__ccd_turn__update_plan_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\compare\hero_vs_reference_9x16.png_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_003.00s.png_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_001.75s.png_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_002.50s.png_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_003.25s.png_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\key\04_very_middle_7.52s.png_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_005.00s.png_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\compare\hero_vs_reference_16x9.png_

**Agent (2026-11-26 02:20 UTC):**

Now let me look at my owned code files.

**Agent (2026-11-26 02:20 UTC):**

> _tool: Bash - List shader, editor, FX, props and tools folders_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Bash - List scripts, captures and show run wrappers_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.WaterFX.cs_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.WaterFX.cs_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Runtime\FX\SplashFX.cs_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Water.shader_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Soft.shader_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Glass.shader_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\TextureGenerator.cs_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWKCommon.hlsl_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.cs_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\CaptureTools.cs_

**Agent (2026-11-26 02:20 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Tools\Blender\scripts\build_props.py_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Grep - PreviewRefreshDomains|BuildRunnerFX|BuildFoam|BuildFloatingBubbles|BuildDecorChevrons|static .* ModelParts|static .* ModelPrefab|class Combiner|ChunkLength|stat_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.cs_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - List runtime scripts and inspect runner controller API_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Show runner controller and camera rig source_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Show rest of runner controller and track API_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Inspect slide module construction in track script_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Show slide module profile constants and builder_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Show U-mapping helpers for slide profile_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\_lead_test\hero_9x16.png_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Docs\AssetPreviews\Props_set.png_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\_lead_test\hero_16x9.png_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\stills\04_tunnel_16x9.png_

**Agent (2026-11-26 02:21 UTC):**

The lead's camera change is noted. I'll judge my work in the new portrait framing (2.7 m back, 1.75 m up, 9.5 deg pitch, FOV 60). Next I'll zoom into the reference splash and water details.

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Check Python imaging availability and reference files_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Check for image tools and Blender bundled python_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\b3410996-81ad-4e2d-9d43-bf3d56c2a918\scratchpad\crop.ps1_

**Agent (2026-11-26 02:21 UTC):**

> _tool: PowerShell - Crop and zoom the splash region of the reference frame_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\b3410996-81ad-4e2d-9d43-bf3d56c2a918\scratchpad\ref3_splash.png_

**Agent (2026-11-26 02:22 UTC):**

> _tool: PowerShell - Crop splash regions of two more reference frames_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Check scratchpad contents_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Create private agent2 scratch folder with crop script_

**Agent (2026-11-26 02:22 UTC):**

> _tool: PowerShell - Crop splash regions of two more reference frames_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\b3410996-81ad-4e2d-9d43-bf3d56c2a918\scratchpad\agent2\ref25_splash.png_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\b3410996-81ad-4e2d-9d43-bf3d56c2a918\scratchpad\agent2\ref325_splash.png_

**Agent (2026-11-26 02:24 UTC):**

> _tool: Bash - Show FlowGlow and Emissive shader properties_

**Agent (2026-11-26 02:24 UTC):**

> _tool: PowerShell - Crop water and bank regions of the reference_

**Agent (2026-11-26 02:24 UTC):**

> _tool: Read - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\b3410996-81ad-4e2d-9d43-bf3d56c2a918\scratchpad\agent2\ref3_water.png_

**Agent (2026-11-26 02:24 UTC):**

> _tool: Read - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\b3410996-81ad-4e2d-9d43-bf3d56c2a918\scratchpad\agent2\ref175_water.png_

**Agent (2026-11-26 02:25 UTC):**

> _tool: Bash - Inspect lighting setup for light directions_

**Agent (2026-11-26 02:27 UTC):**

> _tool: Bash - Look up mascot proportions and prior props build log_

**Agent (2026-11-26 02:27 UTC):**

> _tool: Bash - Find slide pose and preview log summary_

**Agent (2026-11-26 02:27 UTC):**

> _tool: Bash - Inspect slide clip pose in the rig script_

**Agent (2026-11-26 02:27 UTC):**

> _tool: Bash - Show seated pose constants_

### Message (2026-11-26 02:27 UTC)

[Request interrupted by user]
