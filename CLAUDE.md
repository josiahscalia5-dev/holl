# Bubble Wash Kingdom — project instructions

A brand-new Unity mobile water-slide adventure: a fluffy hot-pink mascot slides through the inside
of one enormous magical washing machine. These instructions come only from the owner's brief
(`Docs/ProjectBrief.md`) and the approved Google Flow video `25982.mp4`.

## Owner standing rules (2026-11-27, follow in every session)
- OWNER 2026-11-27 12:36 STRICT PERMANENT USAGE AND QUALITY RULE (verbatim in Captures/agents/_shared/OWNER_RULE_1236_usage_quality.txt):
  never voluntarily stop, wrap up, pause development or reduce quality because usage reaches 61 / 75 / 85 / 90 / 95 / 99 % -
  continue productive development until 100 % of the included usage is exhausted or the enforced limit stops the work (usage is
  the owner's responsibility; producing the highest-quality game is ours). Strongest suitable models / reasoning, best
  specialists, skills, plugins, MCPs and integrations; Unity + Blender to their fullest. Continue unfinished specialist work and
  launch the next visual reconstruction tasks without waiting for a reset. Priority: golden hatch, fluffy washing roller,
  metallic tunnel walls, cinematic lighting, mascot, water, scenery (approved references + the closed Marble evaluation; no more
  Marble credits). Goal 9/10+ on ALL approved screens, genuine interactive 3D Android gameplay. Exactly ONE 5-minute autosave,
  safe GitHub sync, private conversation backups. No cash, paid usage, purchases or bypassing enforced limits.
- OWNER 2026-11-27 12:30 REAL 3D PROOF (verbatim Captures/agents/_shared/OWNER_BRIEF_1230_real3d_proof.txt): Marble = look target
  only; no flat image planes / background cards / billboards / placeholders for scenery; every S2 claim proven with the comparison
  sheet, 5-angle proof, neutral clay proof, mascot visible / hidden / alone, a Play Mode recording, a per-item geometry audit
  (Tools/owner_package.sh -> CaptureTools.S2ProofViewsBatch) and an honest score + short gap list.
- QUALITY FIRST, NOT CREDIT CONSERVATION: use the whole subscription allowance; never pick inferior methods, simplify 3D
  assets or compromise visual accuracy to save credits; rebuild inadequate assets properly. Do not voluntarily stop at
  72/80/85/90/95 % usage - keep working until the real limit (respect hardware stability, disk safety; no paid charges,
  no paid Fast Mode, no purchases). Multiple specialists may work concurrently when their files do not conflict; heavy
  Unity / Blender runs stay staggered through Tools/heavy_lock.sh.
- OWNER 2026-11-27 07:10 (permanent): never stop, pause, restart or interrupt running specialists, agents, workflows,
  Unity / Blender runs or background jobs to process a new message - fold new instructions into
  Captures/agents/LEAD_DIRECTIVES.md (printed to every specialist after each heavy run) and the pass args instead. Never
  choose weaker models / reasoning / tools / simplified assets to save usage; work until the REAL limit (no Fast Mode,
  no charges). Storage target: >= 30 GB free on C: if SAFELY achievable - owner-approved categories only (Logs/cleanup.log),
  one concise approval list for anything else; never delete unique personal or synced cloud files, Unity / Unity Hub,
  Blender, Claude, the Android SDK, this project, v4 / v5 mascots, references, checkpoints, chat history; never restart
  the laptop or close development apps. Exactly ONE 5-minute autosave with verified pushes; chat history LOCAL only.
- ONE SCREEN AT A TIME: S2 (video 3.00 s, golden tunnel entrance at the washing-machine door) until the owner has
  reviewed the improved S2 gameplay; aim 9/10+. Private plan: Captures/agents/_shared/S2_FOCUS_PLAN.md; the owner's
  annotated corrections: Reference/s2_corrections/.
- Gameplay: real interactive 3D; the pink mascot SITS UPRIGHT ON HIS BOTTOM while sliding, faces the travel direction,
  little feet forward, leans / tilts through curves, bounces gently with the water, reacts to jumps / landings / lane
  changes and always returns to the seated pose (never swims on his stomach or runs upright). The gameplay camera
  (portrait) always follows behind his back through every curve, climb and descent, banking smoothly - no cuts, no
  front views in normal play; only the existing destination celebration turns him to the player. The front-facing
  video shots are references for the character / scenery only. The matched comparison camera (R2) is for evaluation
  only - never change the gameplay perspective to improve a comparison score.
- Character (owner 2026-11-27 06:20): reconstruct the ACTUAL approved character (target 9/10+, honest scores) as a
  SEPARATE improved version next to v4 (v4 + skeleton + animations + materials stay the complete fallback); the owner
  reviews it in real gameplay before it replaces v4. Scene order: S2, then S1 after his review.
- Team (owner 2026-11-27 06:20): A character artist, B environment artist, C water / VFX, D cinematic graphics
  (metal / lighting), E character animation + camera; clear file ownership (bwk-screen-focus.js FILES), lead integrates;
  heavy Unity / Blender runs staggered (max 2 specialists active at once on this laptop).
- Exactly ONE five-minute autosave loop (`Tools/autosave.sh 300`); private references, chat history and credentials stay
  out of public GitHub (BWK_PUBLISH_CHAT=0 default). Never interrupt running specialists, builds or workflows; keep the
  private handoff (Captures/handoff/NEXT_ACCOUNT_START.md) updated so any authorized session can resume.
- OWNER 2026-11-27 09:20 (permanent, 15-section takeover brief; full text private in
  Captures/agents/_shared/OWNER_BRIEF_0920_15_sections.txt, condensed per specialist in Captures/agents/LEAD_DIRECTIVES.md):
  quality first with the strongest models / tools at ANY usage level until the enforced limit (no purchases, no paid Fast
  Mode, no extra charges, no hiring); a new account RECOVERS the newest state (handoff, workflow journals, the previous
  lead's transcript) and continues - never restarts finished work or interrupts surviving runs; all five specialists A-E
  stay in use, ~2 active at once, heavy runs staggered, no duplicate agents; S2 to 9/10+ before S1 / other scenes, honest
  scores only with visual evidence; no generic substitutes where the references show specific shapes / materials /
  arrangements. Character: improve v5 or a versioned successor, v4 (materials, skeleton, animations) stays the complete
  fallback; fix streaky fur, too-wide body, artificial knitting, spiky pom-pom; front / rear / side / three-quarter proof
  plus Unity gameplay proof. Opening camera: the first ~3.5 s must not make the mascot excessively large or hide the
  scenery. Verification package after each integration: reference | previous | latest (mascot visible + hidden, labelled),
  mascot turnaround, portrait gameplay screenshots, a full gameplay recording, test results, honest scores. Storage is
  settled at ~28.79 GB free - revisit only if it blocks development; never restart the laptop. Exactly ONE 5-minute
  autosave with verified pushes, no force-push / history rewrite, chat history and recovery notes LOCAL only.

## Current handoff (read first)
- 2026-11-27 16:45 (session 15a68124 = LEAD, new account, opened in C:/Users/josia/thanksgiving): pass 10f was CUT at ~16:28 (session
  ee862596 ended); lead reset the unreviewed p4 splash-crown placement (it covered the mascot), after_wave s2p10f is building
  lead_s2p10f (16:40); PASS 10g = resume of character + water, run wf_08237afa-aba (Tools/workflows/bwk-s2-pass10g.js), after_wave
  s2p10g armed. Lead next: owner sheet s2p10e | s2p10f, then tunnel step 2b redo (darker walls). Newest state block: top of
  `Captures/handoff/NEXT_ACCOUNT_START.md`.
- 2026-11-27 16:15 (session ee862596 = acting lead, opened in C:/Users/josia/thanksgiving): PASS 10f RUNNING = character (thick plush
  fur, knitted hat) + water (flowing water, translucent splashes), run wf_9d38984b-cfb (Tools/workflows/bwk-s2-pass10f.js), with
  after_wave s2p10f armed (automatic full build lead_s2p10f + stills + Play Mode when the wave ends). Tunnel step 2 kept (denser gold
  bulbs, neon rims); step 1 grade and step 2b brightening rejected / reverted; AI world generators rejected (private
  Captures/handoff/GENERATOR_TESTS_2026-11-27.md). ONE autosave loop. Newest state block: top of `Captures/handoff/NEXT_ACCOUNT_START.md`.
- 2026-11-27 13:58 (lead 5190fd9a, FIFTEENTH account, opened in C:/Users/josia/thanksgiving): newest build lead_s2p10 (Play Mode
  PASSED 13:44, baseline Captures/stills_s2p10); pass 10d (assets + metal) relaunched as run wf_0579c798-ca4 + after_wave s2p10d;
  Marble World 1 checked: every export is disabled on the Free plan (closed); lead camera first-frame fix (RunnerCameraRig.ForcedAspect);
  TRELLIS.2 splash test REJECTED (flat plate) -> new V6 milk crowns = the approved crown outline inflated in Blender
  (build_fx_crown_v6.py, private Art/Projected/FX/); pass 10d relaunched 14:05 as wf_60dc0310-561; heavy_lock / after_wave ignore an
  open Blender window (only --background counts), so the Blender MCP window can stay open. Newest state block: top of
  `Captures/handoff/NEXT_ACCOUNT_START.md`.
- 2026-11-27 09:35 (lead 72ca2928, ELEVENTH account, opened in C:/Users/josia/.unity): pass 7 water + metal done; the
  08:39 usage limit cut character / motion / assets -> after_wave build lead_s2p7 (09:20, Play Mode PASSED) = baseline
  Captures/stills_s2p7; pass 7 RESUMED as run wf_308eb7af-d9b (Tools/workflows/bwk-s2-pass7r.js, character + assets, then
  motion). Newest state block: top of `Captures/handoff/NEXT_ACCOUNT_START.md`.
- 2026-11-27 07:35 (lead cd16e551, TENTH account, opened in C:/Users/josia/.unity): S2 pass 7 run wf_3eb67e7b-0c4
  (Tools/workflows/bwk-s2-pass7.js); the game now uses the v5 mascot (AnimatorBuilder.UseMascotV5, v4 = fallback), the
  slide climbs after the door (S2RiseY), portrait camera 4.3 / 1.75; Play Mode recordings are now truly portrait-framed.
  Newest state block: top of `Captures/handoff/NEXT_ACCOUNT_START.md`.
- 2026-11-27 06:45 (lead 264e8266, ninth account): S2 pass 6 relaunched (run wf_e52ebd74-a3c) after the old account's
  limit; newest state block at the top of `Captures/handoff/NEXT_ACCOUNT_START.md`. Lead sessions may be opened in
  `C:\Users\josia\.unity` (their transcripts then live under `~/.claude/projects/C--Users-josia--unity/`; list them in
  `Tools/chat_extra_sessions.txt` so the autosave exports them locally).
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
- AI integrations (installed 2026-11-27 by lead 72ca2928 on the owner's request; check before reinstalling, avoid duplicates):
  Node.js 26.13.1 portable `C:\Users\josia\DevTools\node-v26.13.1-win-x64` + uv 0.13.10 `C:\Users\josia\DevTools\uv` (user
  PATH + `~/bin` shims for Git Bash: node, npm, npx, uv, uvx, worldlabs); World Labs CLI 0.6.0 (`worldlabs`, sign-in pending:
  the owner runs `worldlabs auth login` himself - the key goes only into its hidden prompt, never into chat). Claude Code
  plugins (user scope): `worldlabs@worldlabs` 0.2.2 (skills atlas-blender / atlas-flythrough / atlas-splats / worldlabs-cli
  + the hosted Atlas MCP `plugin:worldlabs:worldlabs`, sign in with /mcp in a new session) and `unity@anthropic-plugin-
  directory` 0.1.9-beta (33 skills, no MCP). Never run `worldlabs setup` / `worldlabs skills install` (duplicate skills) or
  `claude mcp add worldlabs` (the plugin already has it). User MCP servers in ~/.claude.json: `unity-editor-mcp` (Unity CLI
  1.0.1 `C:\Users\josia\AppData\Local\Unity\bin\unity.exe mcp --tool-groups --cli-tools`; Editor tools need the Unity
  Pipeline package in this project + an open Editor - NOT added: it changes Packages/manifest.json and an open Editor would
  block the batchmode pipeline; owner decision) and `blender` (`uvx mcp-for-blender`, DISABLE_TELEMETRY=true; add-on
  blender_mcp v2.0 enabled in Blender 5.3 user prefs, localhost:9876, auto-starts only in the Blender GUI). Atlas Blender
  extension 0.1.4 (`bl_ext.user_default.worldlabs_atlas`, online access ON; key only in its own settings or WLT_API_KEY).
  Project Blender scripts run with --factory-startup, so these add-ons never affect builds. Meshy not installed (any
  generation needs a paid Pro plan). Atlas: uploading reference frames needs the owner's approval each time; results that
  contain reference pixels stay local (Art/Projected/, Scenes/Private/); investigation notes Captures/agents/_shared/
  ATLAS_INVESTIGATION_0945.md.
- Unity is still driven through batchmode by default
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
  owner 2026-11-27 ~06:00: "keep private references, chat history and credentials excluded" -> chat history stays
  LOCAL, script default BWK_PUBLISH_CHAT=0 (it was published 11-26 20:03 -> 11-27 05:55; those older public commits keep
  it, history is never rewritten); BWK_PUBLISH_CHAT=1 only on the owner's explicit request) and pushes 5-minute snapshots of
  the working tree via the local branch `github-main` -> `origin/main`, built on `0c51785` and leaving out files that show
  the private reference video (`PRIVATE_PATHS`, e.g. `Docs/AssetPreviews/SK_Mascot_vs_reference.png`). Local `main` and
  checkpoint tags 4+ stay local (they contain that image); tags 0-3 are on GitHub. Never put reference frames in tracked
  files (comparison images belong in `Captures/`, which is gitignored).
- `Reference/`, `Captures/`, `Tools/Blender/work/`, `Library/`, `Temp/`, `Logs/`, `UserSettings/` stay out of git.
  Binary art (fbx, png, blend, audio) goes through Git LFS (`.gitattributes`).
- Commit meaningful checkpoints (tag `checkpoint-*`) before major changes.
