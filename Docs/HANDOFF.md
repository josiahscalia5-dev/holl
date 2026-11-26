# Bubble Wash Kingdom - lead handoff (2026-11-26 12:30, lead session cd43a82d on the third Pro account)

## STATUS 14:45 (lead a0655f8d) - exact resume point (private details: Captures/handoff/NEXT_ACCOUNT_START.md)
- Done + tagged locally: checkpoint-18c-camera (owner corrections 1, 7, 8: rear opening crane, finish in front of the
  portal, Play Mode test passed) and checkpoint-19-r7w (round-7 water pass integrated by build lead_r7w, stills
  Captures/stills_r7w/, sheets Captures/sections/*_r7w.png; owner's projection decision in CLAUDE.md + .gitignore).
- RUNNING since 14:16: owner's projection test (Tools/workflows/bwk-projection-test.js, run wf_3b08b58e-28a): one
  specialist projects + bakes the approved artwork onto the S5 chamber ChamberV2_216_R (216 m) + wall, isolated test scene
  Scenes/Private/Test_Projection_S5.unity, private assets Art/Projected/ (both gitignored), gameplay recording
  Captures/playmode/projection_s5_9x16.mp4; then an independent judge. Notes: Captures/agents/projection/NOTES.md.
- NEXT: (1) projection verdict -> send the owner reference | current | projected + recording; (2) round 8
  (bwk-round8-cinematic.js, args {base: newest tag, before: "Captures/stills_r7w"}): metal + water first; the assets agent
  gets the projection rollout for the asset types the judge approved (else conventional); (3) lead safe_build lead_r8 ->
  cp stills -> stills_r8 -> section_triptych r8 (before stills_r7w) -> bwk-round7-verify.js {tag: "r8"} -> Play Mode
  recording -> send -> commit + tag -> update this file and the checklist scores.
- Open: portal starburst still white (round 8 metal/assets); the HUD banner panel (14:05) is not yet in a recording;
  in-game mascot is the old SK_Mascot (character work later). Disk 3.6 GB free after the 14:40 cleanup.

## Round 7 continuation (2026-11-26 from 13:36, lead session a0655f8d on the fourth account)
- Takeover 13:36: newest work = local tag checkpoint-18b-handoff, git clean. Exactly ONE autosave loop (PID 1291, started
  12:26, no BWK_PUBLISH_CHAT; public tree has 0 ChatHistory / Reference / Captures files). The previous lead's "17:12
  restart timer" was still alive as an orphaned `sleep 14569` (parent shell gone) -> killed 13:37. No Unity / Blender, no
  heavy lock, no scheduled tasks. Unity's official plugin: enabled on this account (ListPlugins). Remote Control ON.
- FINDING: `Reference/review/Bubble_Wash_Kingdom_4K_Claude.mp4` is byte-identical (same MD5) to the approved 4K reference
  video - it is NOT a gameplay recording. The recording the owner reviewed (26403.mp4, 29.5 s) is our own
  `Captures/playmode/gameplay_autopilot_9x16.mp4` of 13:16 (kept as `..._r7_1316_owner_reviewed.mp4`). Review frames:
  `Captures/review_r7/ours/` + `review_r7_opening_0-5s.png`, `review_r7_end_23-29.5s.png` (new helper
  `Tools/review_recording.sh <mp4> <outDir>`).
- What the review shows: 0-3 s the old FRONT intro orbit fills the portrait frame with the face / hat and its 1.3 s
  Cinemachine blend to the rear camera passes THROUGH the hat (3.0 s); 23-25 s the camera flies into the portal glow
  (whole-portal 1.6x scale + light 14 -> white-out); 26 s the finish point (track end - 6 m) is 6 m PAST the portal, so the
  rear camera looks past the track end into the empty background ("empty purple"); 26.5-29.5 s the celebration orbit
  circles outside the tunnel end through foam (the "awkward camera movement").
- Step 2 R-camera baseline DONE 13:44: `Captures/stills_r7/R3..R6_*` (+ bg/); 13:06 stills backed up in
  `Captures/stills_r7_1306_backup/`.
- Step 4 water pass RUNNING since 13:48 (run wf_73ffac15-515, task wxzedpvmg; resume with resumeFromRunId).
- Step 3 lead camera + finish (owner-approved fix; hero framing 2.75/1.3/10/58 untouched, captures unchanged because
  Snap() clears the new offsets): CameraDirector now keeps ONE live camera (the rear rig) - opening = rear crane
  (+4.4 m back, +1.7 m up, +7 deg pitch easing into the gameplay framing over 3.5 s); finish = the mascot brakes to rest
  5.5 m before the portal (RunnerController.finishRestBeforeEnd 17.5, finishBrakeDistance 8), hops and turns 180 deg to
  face the camera (front-facing celebration, reference 14.5 s composition), the rig eases 1.4 m back / pitch -5 / FOV +5
  with a slow push-in, banner pops in after the turn, soft violet fade before a loop restart. PortalGlow scales only the
  glow pieces (max 1.18x) and caps the light at 6.5. Play Mode test A asserts the celebration pose and that the camera
  stays >= 2 m before the portal plane. Verification recording: lead_play_r7cam (running 13:51).

## Round 7 status (2026-11-26 12:30, lead session cd43a82d) - read this first
- 13:45 HANDOFF TO THE NEXT ACCOUNT (owner): lead session cd43a82d stopped, its 17:12 timer cancelled. Start with the
  private `Captures/handoff/NEXT_ACCOUNT_START.md` (exact steps 1-7). Recording copy: `Reference/review/`.
- Takeover verified 12:13: newest work = local tag `checkpoint-17b-takeover` (checkpoint-17-s5-straight + the previous
  lead's uncommitted round-7 hooks / workflow / TRELLIS helpers). The previous lead session's process was gone; its two
  orphaned `sleep` timers (14:02 and the "15:40 continuation") were stopped, so no second account can start a duplicate
  round. No scheduled tasks or cron jobs exist on this account.
- Autosave: the loop restarted by the previous lead at 12:09 published chat history (BWK_PUBLISH_CHAT=1); the owner's new
  brief says keep chat history local, so it was restarted at 12:20 WITHOUT chat publishing (public ChatHistory/ is frozen
  at autosave c4fdbe9, which already contains the 4e740a08 export and the first 617 lines of this session's export).
  12:35 OWNER: "Yes, remove it" -> autosave.sh now removes ChatHistory/ from the public tree (pushed 3e05fbb, 0 chat files
  on GitHub main; older public commits still contain them - history is never rewritten). Exports stay local in ChatHistory/.
- Integrations (12:20): Claude Docs + scheduled-tasks connectors connected; Remote Control ON for this session; computer
  use, Claude in Chrome and the built-in browser available (computer use asks per app). NOT installed and never were:
  Unity MCP (would block batchmode: Unity can't open the project twice), Playwright, Chrome for Testing, Frontend Design
  plugin, GitHub connector (git CLI pushes work), ProBuilder (not in the manifest). Blender MCP = Claude Desktop chat
  extension only (add-on not installed in Blender, not visible to Code sessions) -> Blender batch scripts. Project agents
  (6) + skills (4) in .claude/ load automatically.
- New lead tooling: CaptureStills / CaptureHero now also write `<dir>/bg/` with the MASCOT HIDDEN (same file names);
  `CaptureStillsBatch -bwkOut DIR -bwkHero`. Previous build captured 12:18 -> `Captures/stills_prev_r6/` (+ bg/, compare/).
  `bash Tools/section_triptych.sh <tag> [prevDir] [newDir]` -> `Captures/sections/S<n>_triptych_<tag>.png` (row 1 reference
  | previous | newest, row 2 the same with the mascot hidden) + ALL sheets. Previous full gameplay recording kept as
  `Captures/playmode/gameplay_autopilot_9x16_prev_r6_1146.mp4 (11:46 run, S5 straight)`.
- 12:27 Round 7 workflow launched (task wzik2ppqr, run wf_e8ef4a2c-f69, prompts updated with the shared colour sheet,
  section boundaries 14-115 / 110-318 / 318-351 m, gameplay-untouched rules, max 5 full builds). Resume a cut-off run with
  `Workflow({scriptPath: ".../bwk-round7-wholelevel.js", resumeFromRunId: "wf_e8ef4a2c-f69"})`; agent transcripts in
  `~/.claude/projects/C--Users-josia-thanksgiving/cd43a82d-d354-43cf-9600-4a89cd571544/subagents/workflows/`.
- After the wave: lead safe_build -> snapshot `Captures/stills_r7/` -> section_triptych -> scores in the checklist ->
  full-level Play Mode recording -> checkpoint-18 -> this file.
- 13:05 tunnel + hall agents DONE (reports in the run journal), water agent PAUSED at 67 % usage at a safe point (foam v2
  rebuilt in Blender with AO vertex colours + LOD1, nothing of it in Unity yet). 13:06 lead build `lead_r7_final` OK ->
  `Captures/stills_r7/` (+bg), sheets `Captures/sections/S1..S7_triptych_r7.png`, recording `lead_play_r7` ->
  `Captures/playmode/gameplay_autopilot_9x16.mp4`, scoring `Tools/workflows/bwk-round7-verify.js` (args {tag: "r7"}).
- 13:20 independent round-7 scores (with mascot / scenery only, details + gaps in Docs/VideoCoverageChecklist.md):
  S1 4/4, S2 5/5, S3 3.5/4 (C1 still does not show S3), S4 4/4.5, S5 4/4.5, S6 4.5/5, S7 4.5/5; whole ~4.2 / ~4.6
  (round 6: ~3.8 / ~3.9). Sheets were sent to the owner. Comparison cameras (front C stills) frame too little of the upper
  tunnel - add reference-matched TEMPORARY comparison cameras next round (keep the old ones for continuity).
- 13:25 recording sent (Play Mode 2 passed / 0 failed, `gameplay_autopilot_9x16.mp4` 13:16). OWNER 13:22: water first,
  then round 8 = a SUBSTANTIAL visual-quality transformation (polished gold, rich metal, FLUFFY roller bristles, GLOSSY
  RAINBOW RAILS, turquoise flowing water, soft soap bubbles, warm reflections; improve every visible asset, no more stars /
  machinery), correct the S3 comparison camera, use the official Unity rendering skills + Blender + Unity.
- 13:25 lead: CaptureStills now also renders REFERENCE-MATCHED front cameras R3 158 m / R4 190 / R5 220 / R6 280 (from
  shot0825/camera.json: 2.6 m ahead, 1.3 m up, 0.3 m right, vFOV 52, mascot at (522,397)); section_triptych.sh uses R
  stills when both builds have them, else the C stills (cs_check OK, not yet rendered).
- 13:30 OWNER reviewed our full recording (uploaded as `~/.claude/uploads/cd43a82d-.../f84dc061-Bubble_Wash_Kingdom_4K_Claude.mp4`,
  22.8 MB; owner calls it 26403.mp4) and added corrections on top of the water pass + round 8: (1) the OPENING CAMERA gets
  too close to the mascot and its hat; (2) richer materials + more accurate scenery proportions everywhere; (3) replace the
  foam blobs and flat lace splashes throughout; (4) restore the glossy multicoloured slide rails; (5) reduce the cyan
  arrow brightness; (6) golden portal = controlled golden starburst, not white; (7) the empty purple environment and the
  AWKWARD CAMERA MOVEMENT around 26-29 s of the recording; (8) a polished, continuous FINISHING SEQUENCE. References: the
  video + the owner's three ANNOTATED SHEETS (received 13:35; private copies Reference/annotated/01_S1_opening_hall.png, 02_S4_tunnel.png, 03_S7_portal.png; numbered notes assigned in the round-7 water and round-8 prompts).
- 13:40 OWNER'S ASSET LIBRARY = the OFFICIAL visual asset construction guide going forward: ZIP extracted to
  `Reference/asset_library/` (private, gitignored; 00_READ_ME_Asset_Index.md, Individual_References/01-24, BWK_Asset_Sheet_01-04,
  frame map). Assets 01-24 mapped to owners in the round-7 water + round-8 prompts; every agent audits its assets first
  (keep / material / refine / replace -> Captures/agents/_shared/asset_audit.md) and delivers per-asset library | before |
  after sheets; the lead then compiles them + section comparisons. 23 mascot = later. Not yet inspected by the lead (usage).
  Ownership: (3)+(5) round-7 water resume prompt; (2)(4)(6)(7 scenery) round-8 prompts; (1)(7 camera)(8) LEAD (camera rig,
  gameplay) - the owner's request counts as approval for fixing the opening / end camera behaviour; the hero framing
  2.75/1.3/10/58 stays; show [reference | before | after] for each camera fix.
- AFTER THE 17:10 RESET (order fixed by the owner): (00) LEAD reviews the uploaded recording first (extract frames 0-5 s,
  24-31 s and the ending with Tools/extract_frames_blender.py into Captures/review_r7/, one contact sheet) and the annotated
  sheets; (0) R-camera baseline of the round-7 scene:
  `bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.CaptureStillsBatch lead_r7_rcam -bwkOut Captures/stills_r7 -bwkHero`;
  (1) finish round-7 water/foam/splash:
  `Workflow({scriptPath: "C:/Users/josia/thanksgiving/Tools/workflows/bwk-round7-wholelevel.js", args: ["water"]})`
  (its prompt has a RESUME note) -> lead `bash Tools/safe_build.sh lead_r7w` -> copy stills to `Captures/stills_r7w/` ->
  `bash Tools/section_triptych.sh r7w Captures/stills_r7 Captures/stills_r7w` -> send -> commit `checkpoint-19-r7w`;
  (2) then round 8 (3 agents: metal / assets / water; max 2 run at once):
  `Workflow({scriptPath: ".../bwk-round8-cinematic.js", args: {base: "checkpoint-19-r7w", before: "Captures/stills_r7w"}})`
  -> lead build -> triptych r8 (before r7w) -> verify workflow {tag: "r8"} -> recording -> send. Round 8 will likely span two
  usage windows (stop at ~80 %, resume with resumeFromRunId). The lead session set a wake timer for 17:12.
- 12:55 OWNER (added after round 7, plan otherwise unchanged): a CINEMATIC LOOK pass for the whole level with the existing
  URP features (reflection probes, post volume, our URP shaders; Shader Graph only if clearly easier; no Needle Engine, no
  new packages, no purchases): polished gold, realistic glass pipes, rich metallic walls, glossy flowing water, iridescent
  bubbles, warm light, controlled neon glow; show real before/after Unity comparisons. Prepared
  `Tools/workflows/bwk-round8-cinematic.js` (agents light+metal / water+glass+bubbles; args {base, before}; before =
  `Captures/stills_r7`). Launch after the round-7 integration (this 5-hour window will be used up -> after the 17:10 reset).
- Plugins 12:58: Unity's OFFICIAL Claude Code plugin ("Unity", Unity Technologies, Anthropic Directory, skills incl.
  urp-postprocessing, shader-graph-create-custom-node, validate-urp-render-graph-renderer-feature) was not enabled at
  12:58; 13:15 the OWNER INSTALLED IT (ListPlugins: enabled; skills only, no Unity package) - use its graphics skills
  alongside the Unity Game Studio specialists (owner 13:05). The project's own unity-graphics /
  unity-lighting-vfx / unity-performance / unity-cinemachine skills (Claude Unity Game Studio copy) are enabled.

## (previous) lead handoff 2026-11-26 10:30, lead session 98d6de44

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
- 11:40 OWNER CHANGED THE METHOD: evaluate free tools (TRELLIS.2 hosted demo, Unity MCP, ProBuilder, Blender Perspective
  Match, Poly Haven) and prove them with Unity before/after renders of the 8.25 s scene, then roll out to S1-S7.
  TRELLIS.2: code / Space / TRELLIS.2-4B / BiRefNet all MIT (commercial use OK); the Space forwards images WITHOUT
  transparency to briaai/BRIA-RMBG-2.0 (non-commercial licence, 3rd party) -> only upload RGBA cutouts
  (`Tools/mask_polygon.py` hand-traced outline -> `Captures/trellis/mascot/mascot_rgba.png` from 4K f_06.00s; client
  `Tools/trellis_client.py`, library in gitignored `Tools/.pylibs_gradio`). First call 11:33 REFUSED: anonymous ZeroGPU
  quota ("120s requested vs. 143s left", retry in 24 h). Needs the owner's own FREE Hugging Face login on this PC
  (docs: 5 min/day free vs 2 min anonymous; the Space reserves 120 s per step, 2 steps per model -> ~1 model/day at best).
- 11:58 TRELLIS.2 ran with the owner's own HF login (device flow, token in ~/.cache/huggingface): mascot GLB 297k tris
  in 105 s (`Captures/trellis/mascot/out_s0/model.glb`, sheet `trellis_vs_ref_sheet.png`). Front recognisable (~5/10) but
  flat (depth 0.54 x width 0.94) and TWO-FACED from behind (back ~1/10), pom-pom wrong -> not usable as the rear-camera
  game mascot. Free quota ~1 model/day. Possible 2nd attempt: a rear frame (0-3 s) as input.
- 12:00 OWNER'S NEW BRIEF: rebuild the ENTIRE level's scenery section by section (priority scenery > water > placement >
  mascot > lighting). Prepared `Tools/workflows/bwk-round7-wholelevel.js` (agents tunnel S3-S7 / hall S1-S2 + portal S7 /
  water everywhere; env agents may run safe_build). Lead added partial hooks BuildHallExtras / BuildPortalExtras in
  SceneBuilder.cs (implemented by the hall agent in SceneBuilder.Hall.cs). "Previous build" stills saved in
  `Captures/stills_r6_1142/`. LAUNCH at the 15:40 window reset: Workflow({scriptPath: ".../bwk-round7-wholelevel.js"}).
  After it: lead safe_build, all-section sheets reference | previous | newest, scores, full-level recording, checkpoint.
- LATER: wave = `args: ["character", "lighting"]` of the round-6 workflow (mascot export fix + lighting); then wave 3 env + water fixes
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
