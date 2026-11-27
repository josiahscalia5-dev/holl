# Bubble Wash Kingdom — project instructions

A brand-new Unity mobile water-slide adventure: a fluffy hot-pink mascot slides through the inside
of one enormous magical washing machine. These instructions come only from the owner's brief
(`Docs/ProjectBrief.md`) and the approved Google Flow video `25982.mp4`.

## Current handoff (read first)
- NEXT ACCOUNT START (2026-11-26 13:45): the private `Captures/handoff/NEXT_ACCOUNT_START.md` (state, private reference
  paths, the exact next steps) and the "Round 7 status" block at the top of `Docs/HANDOFF.md`.
- `Docs/HANDOFF.md` (2026-11-26 10:30): state, owner decisions, the measured asset-library + shot-matched set dressing
  method, the 8.25 s reconstruction test (prepared workflow `Tools/workflows/bwk-round6-shot0825.js`), mascot export fixes
  and the 7 section requirements (`Docs/VideoCoverageChecklist.md`). The opening cinematic is PAUSED (owner makes it).

## Independence (hard rule)
- This project is new and independent. Never open, read, copy or modify any previous game project
  (for example `C:\RainbowUnity`, `C:\Whirlwash`) or reuse their scenes, models, scripts, shaders,
  settings, designs, names or memories. The global pointer about "Rainbow Unity" does not apply here.
- Never use the video or its frames as backgrounds or textures pretending to be the game. Everything
  on screen is real 3D geometry, real materials, real particles, real animation.
  OWNER DECISION 2026-11-26 14:15 (exception): reference-derived detail MAY be transferred onto correctly shaped 3D
  geometry by Blender camera projection (UV Project modifier / multi-view projection) and baked into the model's own UV
  textures - never flat cards, backgrounds or video. Occluders (mascot, water, coins, splashes) are removed from those
  textures; an asset is rejected (conventional geometry + materials instead) if it looks blurry, stretched, seamed or
  flat from the gameplay camera. Such textures / models / test scenes contain reference pixels and stay LOCAL:
  `Assets/BubbleWashKingdom/Art/Projected/` and `Assets/BubbleWashKingdom/Scenes/Private/` (gitignored).

## Source of truth
- 2026-11-26: the owner sent a 4K export of the SAME video (3840x2160, 15 s, 24 fps, identical timing):
  `Reference/video4k/Bubble_Wash_Kingdom_4K.mp4`, full-res frames every 1 s in `Reference/frames4k/`, 1280x720 frames
  every 0.25 s in `Reference/frames4k_720/`, sheet `Reference/contact_sheet_4k.png`. Use the 4K frames for all detail
  matching; the hero comparison now uses `Reference/frames4k/f_03.00s.png`. Extract more with `Tools/extract_frames_blender.py`
  (no ffmpeg on this PC). The original 720p video stays at `C:\Users\josia\Downloads\25982.mp4`.
- `Reference/` (private, gitignored, never publish): frames every 0.25 s (`frames/`), named key frames
  (`key/`) and contact sheets. (A `VISUAL_ANALYSIS.md` art bible was planned but never written: compare
  against the frames directly.) The original video stays at `C:\Users\josia\Downloads\25982.mp4`.
- Hero gameplay screen = rear view inside the tunnel, target frame `Reference/frames/f_003.00s.png`. Every full
  build writes `Captures/compare/hero_vs_reference_{9x16,16x9}.png` (left reference, right real Unity render).
- The video is the single source of truth for art direction. Camera and gameplay corrections in the
  brief override it: **normal gameplay camera is behind and slightly above the mascot, who faces the
  direction of travel** (back of hat, pom-pom, fluffy back, tail puff and sole pads visible). Front-facing
  shots only for the opening or celebration.
- Reference 0.00-3.25 s is the target gameplay framing; 3.75-15 s supplies the tunnel, side chambers,
  neon stars, pipes and the golden light portal.
- Must include: purple perforated metallic drum walls, polished gold rings with warm marquee bulbs,
  cyan/pink/yellow neon stars, vibrant blue flowing water slide with glossy pink/rainbow rails, curved
  and downhill slides, glass pipes with glowing water, circular side chambers with swirling water and
  floating socks/laundry, pink/white/blue fluffy brush rollers, white foam banks and splashes, iridescent
  bubbles, gold paw-print coins, purple gems, glowing cyan chevron speed-boost arrows, reflections, soft
  shadows, bloom. Never: outdoor scenery, trees/grass, schools, gardens, castles, unrelated buildings.

## Scope and stages
- Level 1 has 12 proposed screens (see brief). Build and perfect only the section shown in the video
  first (Screens 04-06: Rainbow Rush, Rainbow Water Slide, Twisty Tunnel) until the owner approves it;
  then use its quality as the bar for the remaining screens.
- Quality target: 9/10 similarity to the video (allowing for the rear camera). Never claim a match
  without actual Unity screenshots compared against `Reference/` frames.

## Toolchain
- Unity 6000.3.29f1 (6.3 LTS), URP 17.3, Shader Graph 17.3, Cinemachine 3.1.8, Splines 2.9.2,
  Input System 1.20.1, Recorder 5.1.8, Test Framework 1.6, Timeline 1.8. Windows Standalone module only
  (Android Build Support is not installed yet).
- Blender 5.3 (portable): `C:\Users\josia\Blender\blender-5.3.0-windows-x64\blender.exe`. Every asset is
  built from a script in `Tools/Blender/scripts/` (headless: `blender --background --factory-startup
  --python <script>`), exported as FBX to `Assets/BubbleWashKingdom/Art/Models/`, with a preview render in
  `Docs/AssetPreviews/`. Blender working files go to `Tools/Blender/work/` (gitignored).
- No Unity MCP bridge is connected in Code sessions; drive Unity through batchmode
  (`Unity.exe -batchmode -projectPath C:\Users\josia\thanksgiving -executeMethod <Class.Method> -logFile <log> -quit`).
  Never run two Unity instances on this project at once.
- Windows Smart App Control must stay OFF on this PC; when it was on it blocked Unity's unsigned build
  DLLs (`Bee.*.dll`, Burst JIT DLLs).

## Build commands (batchmode, from the project root)
- Full rebuild (setup, textures, materials, model remap, animator, scene, stills). Run this after cloning:
  the bent/combined level meshes in Assets/BubbleWashKingdom/Generated are not in git.
  `Tools/unity_run.sh BubbleWash.EditorTools.SceneBuilder.BuildAllBatch build`
- Stills only: `Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.CaptureStillsBatch stills` -> `Captures/stills/`
- Hero + comparison only: `Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.HeroBatch hero`
- No-save agent preview (textures, materials, lighting/post + runner FX rebuilt in memory, hero capture):
  `Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut Captures/agents/<name>`
- Play Mode test (autopilot run, MP4 + stills + rear-camera assertions + editor FPS) -> `Captures/playmode/`:
  `Unity.exe -batchmode -projectPath . -runTests -testPlatform PlayMode -testResults Captures/playmode/results.xml`
- Windows dev build for PC perf: `Tools/unity_run.sh BubbleWash.EditorTools.BuildTools.BuildWindowsDevBatch winbuild`
- Blender assets: `Tools/blender_run.sh Tools/Blender/scripts/build_<group>.py [log]`
- Every Unity / Blender run goes through `Tools/heavy_lock.sh` (unity_run.sh and blender_run.sh already do):
  one heavy process at a time on this laptop.

## Claude Unity Game Studio (selective, fresh-project manual copy)
- Only these specialists/skills were copied into `.claude/`: art-director, technical-artist, unity-shader-specialist,
  performance-analyst, qa-tester, level-designer; skills unity-performance, unity-lighting-vfx, unity-cinemachine,
  unity-graphics. Not installed: its hooks/statusline/settings, its template CLAUDE.md, its unity-mcp bridge.

## Machine limits (plan around them)
- Intel N150 (4 threads), 7.7 GB RAM, Intel iGPU, ~9 GB free disk. Run Unity and Blender one at a time,
  keep Library size in check, prefer short batchmode runs. Performance numbers measured here are PC
  numbers; anything not run on a physical Android device must be reported as untested.

## Parallel specialists (file ownership)
- Lead developer: scene assembly (`SceneBuilder.cs` core, full builds, scene saves), gameplay, camera rig, capture
  tools, tests, git. Domain code lives in partial files with one owner each:
  character = `MaterialLibrary.Character.cs`, `BWK_Fur` / `BWK_Character` shaders, mascot Blender scripts;
  water/VFX = `SceneBuilder.WaterFX.cs`, `MaterialLibrary.WaterFX.cs`, `BWK_Water` / `BWK_Soft` / `BWK_Glass`,
  `TextureGenerator.cs`, `SplashFX.cs`, `build_props.py`;
  environment = `SceneBuilder.Environment.cs`, `MaterialLibrary.Environment.cs`, `BWK_DrumWall` / `BWK_FlowGlow`,
  `build_track.py`, `build_machinery.py`;
  lighting = `SceneBuilder.Lighting.cs`, `MaterialLibrary.Lighting.cs`, `BWK_Gold` / `BWK_Emissive`, `BWKCommon.hlsl`,
  `Assets/Settings/*`. Agents never run the full build or save the scene.

## Code layout
- All game content lives under `Assets/BubbleWashKingdom/` (Art, Animation, Prefabs, Scenes, Scripts,
  Tests). Runtime code namespace `BubbleWash`, editor code `BubbleWash.EditorTools`.
- Shaders are hand-written URP HLSL in `Art/Shaders/` (deterministic and reviewable in text).
- Track geometry: Blender-authored straight modules bent along Unity Splines by `SplineMeshDeformer`.

## Git
- Local repo on `main`, remote `origin` = https://github.com/josiahscalia5-dev/holl (PUBLIC).
- Ask the owner before any push. Never force-push, rewrite history or delete branches.
- Owner-approved auto-save (2026-11-25): `Tools/autosave.sh 300` (run while a session is open) exports the chat as
  text (`Tools/export_chat.py` -> `ChatHistory/`, no images / tool outputs / system context, e-mails and tokens redacted;
  owner 2026-11-26 20:03: chat history is PUBLISHED with every snapshot - script default BWK_PUBLISH_CHAT=1; it was
  local-only 12:35-20:03; set BWK_PUBLISH_CHAT=0 only on the owner's request) and pushes 5-minute snapshots of
  the working tree via the local branch `github-main` -> `origin/main`, built on `0c51785` and leaving out files that show
  the private reference video (`PRIVATE_PATHS`, e.g. `Docs/AssetPreviews/SK_Mascot_vs_reference.png`). Local `main` and
  checkpoint tags 4+ stay local (they contain that image); tags 0-3 are on GitHub. Never put reference frames in tracked
  files (comparison images belong in `Captures/`, which is gitignored).
- `Reference/`, `Captures/`, `Tools/Blender/work/`, `Library/`, `Temp/`, `Logs/`, `UserSettings/` stay out of git.
  Binary art (fbx, png, blend, audio) goes through Git LFS (`.gitattributes`).
- Commit meaningful checkpoints (tag `checkpoint-*`) before major changes.
