# Bubble Wash Kingdom - lead handoff (2026-11-26 10:30, lead session 98d6de44 -> next Claude account)

Same existing project: `C:\Users\josia\thanksgiving` (Unity 6.3 URP + Blender 5.3). Never restart it, never create a new
project. Newest local checkpoint: tag `checkpoint-15b-handoff` on local `main` (checkpoint-15-r5 = round 5 results).
Nothing is running: no workflows, no Unity / Blender, the 14:02 auto-restart timer was cancelled, the autosave loop was
stopped after a final snapshot (restart it, see step 3).

## Round 6 status (2026-11-26 11:25, lead session 4e740a08, new Pro account) - read this first
- Wave 1 (environment + water) DONE 10:42-11:15 (5-hour window 2 -> 60 %). Lead integration: shot renders v4/v5, test
  scene re-saved, real-time recording. Checkpoint `checkpoint-16-r6w1`. Autosave loop restarted 10:42 (one instance).
- 8.25 s shot (front, `Captures/milestones/m6_shot0825_front_ref_v1_v3_v5.png`): v1 2.5 -> v3 3.9 -> v5 ~4/10. Placement
  works (mascot exact 385 px, window / pipe / 12 neon stars / gem / coins / bubbles in the reference regions); blockers:
  (1) S5 track is a banked left U-turn (~13 deg bank, 1-2.3 deg/m) while the reference slide is straight + level, so the
  rail covers the window and pipe -> OWNER DECISION (straighten S5 vs accept a rolled camera); (2) old in-game mascot;
  (3) lighting: walls too bright/blue (0.77-0.84 vs 0.63-0.71), weak neon halos; (4) foam v2 renders in Unity as giant smooth
  translucent blobs although the Blender preview shows small-bubble clusters (Unity material/import bug, M_Foam_v2);
  (5) crown v2 sits too low in the front shot; (6) window scrolls thin, plain socks, small pale arch, no curvy pink-cyan pipe.
- New: `ShotMatchTool.cs` (RenderBatch, args -bwkTag -bwkCamH 1.3 -bwkRollBank 0.6 -bwkSaveTest -bwkNoWater; hides the old
  SplashCrowns when the v2 crowns are used), `Test_S5_Shot0825.unity` (modules 194-245 m, Level01 untouched), Blender
  `build_shot0825_assets.py` (SM_ChamberWindow_v2, SM_GlassPipe_Pink_v2, SM_NeonStarTube_v2), `build_fx_v2.py` +
  `Tools/fx_splash_trace.py` (SM_FX_Crown_v2_L/R traced from the frame, overlap 0.924; SM_Foam_v2_*).
- Real-time recording: `Captures/playmode/s5_shot0825_r6_9x16.mp4` (4.7 s, 192 -> 248 m, 17 coins, 1 gem, 0 rear-camera
  violations; Play Mode test `C_RecordSegmentFromEnv` with BWK_PLAY_SCENE / _START / _END / _NAME, ignored without them).
- NEXT: wave 2 = `args: ["character", "lighting"]` after the window reset (15:40 local); then wave 3 env + water fixes
  (items 4-6 above + the owner's S5 decision). Owner asked (11:12) whether a free image-to-3D website may be tried for the
  mascot (upload of one crop) - no answer yet; do not upload without a yes.

## Start here (next session)
1. Read (CLAUDE.md and the memory index load automatically): this file, `Docs/VideoCoverageChecklist.md`,
   `Captures/agents/LEAD_DIRECTIVES.md`, the specialists' `Captures/agents/<domain>/NOTES.md`. This conversation as text:
   `ChatHistory/2026-11-26_98d6de44.md` (local only).
2. `git log --oneline -3` must show the checkpoint-15b-handoff commit. Never reset, never force-push.
3. Restart the 5-minute GitHub autosave once: check `ps -ef | grep autosave` (only one may run), then
   `bash Tools/autosave.sh 300` as a background command. It keeps new chat exports OFF the public repo (see Open questions).
4. Re-enable Remote Control for the new session if the owner wants phone access; keep paid Fast Mode off.
5. Owner said do NOT wait for 2 pm: launch round 6 wave 1 at once:
   `Workflow({scriptPath: "C:/Users/josia/thanksgiving/Tools/workflows/bwk-round6-shot0825.js", args: ["environment", "water"]})`
   then wave 2 `args: ["character", "lighting"]`. Update the RESUME / state lines in its COMMON block first if anything
   changed. Use the Workflow tool only when the owner's message opts in ("ultracode") or the owner asks for specialists.
6. Pacing (this account was on Pro): max 2 specialists per wave, `get_usage` between steps, stop the workflow at ~75-80 %
   of the 5-hour window so ~20 % stays for the lead's integration and report (memory: pro-plan-budget-pacing).

## Owner decisions in force
- Opening cinematic (girl, towels, washer, emergence, spin, whirlpool, portal video) is PAUSED: the owner makes it with
  other tools and will hand over a finished MP4 to play in Unity before gameplay. No Claude work or credits on it unless
  asked. Keep every intro file (Captures/cinematic/, Tools/Blender/scripts/build_intro_ending.py,
  Tools/Blender/work/intro_ending.blend, Reference/intro_handoff/).
- The WHOLE approved gameplay video `25982.mp4` is the blueprint of the whole game: 7 sections (S1-S7 in
  `Docs/VideoCoverageChecklist.md`), each must reach 9/10 on its own. Hero screen first, then section by section.
  No redesign: only the approved frames. Real 3D only, never the video or frames as textures / backgrounds.
- Gameplay camera = behind the mascot, FROZEN at 2.75 back / 1.3 up / pitch 10 / FOV 58 (track 105.5 m for the hero
  comparison). The video's front-camera parts (3.75-15 s) define scenery; front views only for celebration / finale.
- The in-game mascot stays SK_Mascot.fbx until the owner approves v4. Never wire v4 into the game before that.
- No purchases (Meshy, Tripo, paid plugins, usage credits). Free CC0 textures (ambientCG, Poly Haven) only with the
  owner's OK for the download.
- Privacy: Reference/, Captures/, Tools/Blender/work/ stay local (gitignored); never put reference pixels in tracked files.

## New construction method (owner, 2026-11-26 10:40)
1. Reusable ASSET LIBRARY measured from the approved frames, priority: mascot; rainbow laundry chambers with socks;
   golden machinery; transparent pink and cyan glass pipes; fluffy rollers; metallic perforated walls; neon-outline stars
   and gold bulb rings; glossy rainbow slides; water / splashes / foam / bubbles; golden starburst portal.
   Per asset: measured spec (shape, proportions, colours, details) + reference crop sheet -> Blender build -> preview next
   to the crop (owner sees it) -> only then Unity, then reuse everywhere. No generic primitives.
2. SHOT-MATCHED SET DRESSING instead of rule-based spacing: solve the reference camera of a shot from landmarks
   (Tools/track_camera_model.py approach), place assets so their screen positions and sizes match the frame, check with a
   50 % transparent overlay (this IS our "reference scene matcher"; no external tool of that name exists here).
3. Controlled test = reference frame 8.25 s (`Reference/frames/f_008.25s.png`): Unity render at the reference angle,
   rear gameplay view, a playable test scene `Test_S5_Shot0825.unity` (S5 stretch ~205-240 m) and a REAL-TIME gameplay
   recording through it. Blender previews alone never count as success.
4. Stop rule: an asset or approach that fails twice without substantial improvement stops; report precisely what is
   missing (technique, assets, hardware, or a professional 3D artist).

## Why the game still looks different (lead diagnosis 10:30, verified in code and previews)
- The machinery models mostly EXIST (Docs/AssetPreviews/Machinery_set.png, Machinery_porthole.png: SM_ChamberWindow,
  SM_ChamberPipe, SM_GlassPipe_Module, SM_NeonStarTube, SM_Sock_A/B/C, SM_BrushRoller, console, gold pipes).
- Density: `SceneBuilder.Environment.cs BuildPortholes` places one chamber window per ring gap alternating sides, and
  only a few stars per frame; the video shows 1-3 windows and 15-25 stars in every frame from 6.5 to 15 s.
- Placement: windows sit low beside the slide (ChamberAngle 84 deg from the ceiling), hidden by the tall white foam
  banks; the video's windows are large at mid-wall.
- Camera: our front comparison stills (C1-C5) use a 46 deg lens 2.6 m in front of the mascot; the video's lens is much
  wider and sees both walls.
- Asset differences: porthole interior = rainbow spiral (video: rainbow arc + swirling water + socks, thicker frame with
  a big hinge block); stars too small; portal = plain glowing disc; foam = smooth cloud blobs; splash crowns = flat
  perforated sheets; slide = pink only (video: glossy rainbow lanes).
- Mascot in Unity: the Blender master uses 94-210k hair strands; the mobile export (body decimated to 8.5 %, 16 BWK_Fur
  shells, 74.5k tris) breaks: the pom-pom was exported as a bare core sphere and renders as a dark bald ball, the arms'
  shells render as dark spikes, the hat comes out too large. Pipeline bugs to fix (no new mascot version).

## State at the handoff
- Last full build 10:03 (round-5 lighting integrated); stills 10:05 including new front comparison stills C4 (190 m) and
  C5 (280 m); coins near comparison cameras are hidden (CaptureTools.cs).
- Private evidence: section sheets `Captures/sections/S1..S7_ref_vs_unity_r5_1003.png` + `ALL_...png`
  (`bash Tools/section_sheet.sh <tag>` remakes them), hero triptych reference | 07:05 | 10:03
  `Captures/milestones/m5_r5_triptych_ref_0705_1003.png`, gameplay recording `Captures/playmode/gameplay_autopilot_9x16.mp4`
  (09:21, 8/8 Play Mode tests passed, 14 -> 350 m, 96 coins, 3 gems, 0 rear-camera violations).
- Honest scores (10:03): hero ~6/10; S1 3, S2 6 (9:16) / 5 (16:9), S3 3.5, S4 3, S5 3, S6 3, S7 3.5; whole game ~3.5.
  Mascot v4 Blender f14 ~6.5 (hero/rear 7, front 6.5, three-quarter 6.5, side 5.5, face 6); v4 mobile candidate ~4.

## Specialists (file ownership in CLAUDE.md; notes in Captures/agents/<domain>/NOTES.md)
- Character: v4 f12-f14 done (hat hugs the head, one wide pale-pink stripe, stubby raised arms, smooth white soles with
  pink pads, bigger eyes). Mobile export SK_Mascot_v4.fbx (17 bones, 13 clips, 11 materials) via
  `BWK_V4_MODE=gamemodel` (build_mascot_v4.py) + `BWK_RIG_*` overrides (build_mascot_rig.py); NOT wired. Next = round-6
  "character" prompt (fix the export: pom-pom, arms, hat; bake strand fur to textures; yarn-clump pom-pom).
- Lighting: round 5 v1-v4 in the scene (amber gold + warm bulbs, pink haze upper left, bluer lower water, softer grade).
  Open: tunnel interior too light lavender (environment), fur too light (character albedo). Next = round-6 "lighting".
- Environment: paused at round-5 start, no changes. Next = round-6 "environment" (camera solve, _v2 library assets,
  ShotMatchTool.cs, Test_S5_Shot0825.unity).
- Water/FX: round 4 in the scene (measured arrows, seam fix). Unfinished, never-run round-5 edit saved as
  `Captures/agents/waterfx/r5_stopped_build_fx_splash.patch`. Next = round-6 "water" (crown v2, foam v2, READY.json).
- Intro cinematic: paused (see above).

## Lead tasks after wave 1
- Real-time recording through the test scene: `Assets/BubbleWashKingdom/Tests/PlayMode/GameplayCaptureTests.cs` loads
  "Level01_RainbowRush" by name. Add env-var overrides (scene path via EditorSceneManager.LoadSceneAsyncInPlayMode,
  start / end distance ~195-245 m) without changing the default test, then run Play Mode tests through
  `Tools/heavy_lock.sh lead_...` (command in CLAUDE.md).
- Then section sheets, checklist scores, checkpoint, owner report with honest scores and the method verdict. If the
  8.25 s test reaches >= 8/10, roll the library + set dressing out to S1-S7 (hero S2 first).

## Tools (status 2026-11-26)
- Works: Unity batchmode (`Tools/unity_run.sh`, batched agent previews), safe full build (`Tools/safe_build.sh`), heavy
  lock (`Tools/heavy_lock.sh`, one Unity/Blender job at a time), Blender headless (`Tools/blender_run.sh`, Python, Geometry
  Nodes, Hair Curves), C# compile check in ~10 s without Unity (`Tools/cs_check.sh`, stand-in for the C# LSP),
  comparisons (`Tools/section_sheet.sh`, `triptych.py`, `overlay.py`, `img_stats.py`, `contact_sheet.py`,
  `track_camera_model.py`), Play Mode test + Recorder, PerfStats (render counters only in a standalone build), Claude
  Unity Game Studio agents + skills (.claude/).
- RTK 1.2.1 installed, hook deliberately off. Context Mode not installed (needs Node.js 24). Official C# LSP not
  installed (needs the .NET SDK + 0.5-1.5 GB RAM). Unity MCP not connected (batchmode instead). Blender MCP tools need a
  running Blender with the add-on; batch scripts preferred.
- Hardware: Intel N150 (4 threads), 7.7 GB RAM, iGPU, ~5.2 GB disk free (Android Build Support needs ~6+ GB; do not
  delete project files to make room; Android untested).

## Open questions for the owner
- Chat history: the owner's newest brief says keep conversation histories off the public repo, an earlier message said
  publish them. Since 09:10 new exports stay local and the public copy is frozen (`Tools/autosave.sh`,
  BWK_PUBLISH_CHAT=1 restores publishing). The owner has not answered yet.
- A professional character artist for the mascot master if scripted modelling stays below 9/10 (owner's decision).
