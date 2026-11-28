export const meta = {
  name: 'bwk-s2-pass10j',
  description: 'One screen at a time: an independent judge lists the biggest differences of ONE gameplay screen vs its approved video frame, two specialists fix only those with a fast preview loop; judge mode scores the screen after the lead build',
  whenToUse: 'Owner 2026-11-26 18:05 "do a couple of screens, one at a time": args {screen, mode: "fix"} -> lead build + Captures/sections/<screen>_focus_<tag>.png -> args {screen, mode: "judge", tag}',
  phases: [
    { title: 'Gaps', detail: 'one independent judge ranks the screen\'s visible differences and assigns each to a specialist' },
    { title: 'Fix', detail: 'two specialists fix only this screen (max 2 at once on this 4-thread laptop)' },
    { title: 'Judge', detail: 'judge mode: one judge + one skeptic score the screen before -> after' },
    { title: 'Accept', detail: 'mascot acceptance gate (owner 17:35 4H): independent judge + skeptic vs the ORIGINAL video before any full build' },
  ],
}

// args (fix):   { screen: 'S2', mode: 'fix', pass: 1, base: '<newest tag>', before: 'Captures/stills_r8m', agents?: ['metal','water'], resume?: {all, metal, assets, water} }
// args (judge): { screen: 'S2', mode: 'judge', tag: 's2p1' }  -> reads Captures/sections/<screen>_focus_<tag>.png (made by the lead)
// args (gaps):  { screen: 'S2', mode: 'gaps', before: 'Captures/stills_r8m' } -> only the gap list (pass it to fix mode as args.gaps)
const ROOT = 'C:/Users/josia/thanksgiving'
// lead 8d2d815d 19:50: pass 10j = resume of the cut pass 10i (water only; character -> pass 10k later); args copy Captures/agents/_shared/PASS10J_S2_ARGS.json
// lead 6d001969 17:50: RELAUNCH with the owner's 17:35 directive, 17:45 authoritative Google Flow pack and the Accept phase
// lead 9e4e986e 18:50: pass 10i = resume of the cut pass 10h (run wf_48cc4b5b-713 cut 18:10 by the 5-hour limit; args copy Captures/agents/_shared/PASS10I_S2_ARGS.json; Accept also compares with the s2p10h gate state)
// lead 6d001969 17:30: pass 10h = resume of the cut-off pass 10g (character = owner 17:20 Blender groom + bake method; args copy Captures/agents/_shared/PASS10H_S2_ARGS.json)
// lead 15a68124 16:45: pass 10g = resume of the cut-off pass 10f (args EMBEDDED below, copy in Captures/agents/_shared/PASS10G_S2_ARGS.json)
// lead ffbcca5a: args EMBEDDED = Captures/agents/_shared/PASS10_S2_ARGS.json (make_pass10_args.py)
const A = {"_note": "Lead 8d2d815d 2026-11-27 19:50: S2 PASS 10j = RESUME of the cut pass 10i (run wf_0a7050be-d2e cut ~19:20 by lead 9e4e986e's 5-hour limit). WATER ONLY now (owner 19:2x: the ENTIRE approved scenery is the target; max 2 specialists = this + the tunnel lane); the character resume follows as pass 10k when a slot frees.", "screen": "S2", "mode": "fix", "pass": "10j", "base": "lead_s2p10g", "before": "Captures/lead/s2_optics/water_kept", "agents": ["water"], "minutes": 75, "directives": {"character": "OWNER 2026-11-27 17:20 (new account, verbatim): \"TOP PRIORITY, my 16:55 directive: STOP the pinecone / scale fur. The mascot must be a soft, premium, warm light-pink plush toy: smooth round body (the v5 body mesh is already smooth, so fix the fur shader first), plush/fuzzy shader, subtle breakup, light silhouette tufts only where needed, a real chunky knit hat (deep purple, cream cuff, fibrous round pom-pom, soft fabric, not rigid ribs). Keep the rig, animations, gameplay and mobile performance. v4 stays the fallback. ... Never call it a success unless the images show it.\" and: \"Mascot method: sculpt to the approved views in Blender (keep the v5 skeleton), groom real fur + knit hat in Blender, BAKE them into textures for a smooth plush body in Unity (no procedural cone fur), then front/side/rear + gameplay comparison with an honest score.\"\nOWNER 2026-11-27 ~16:55 (verbatim, session 15a68124):\nSTOP using the current pinecone / scale / petal fur approach for the mascot.\nThe main problem is the character surface treatment, not the gameplay.\nI want the mascot to read as a soft plush toy with warm light-pink fur, not as a cone-covered object.\nUse the fastest reliable route:\n1. Keep the existing gameplay rig if possible.\n2. Either reshape the existing mascot mesh or create a cleaner versioned mascot mesh in Blender.\n3. Make the underlying body very smooth, round and plush.\n4. Do NOT cover the whole body with repeated cone clumps.\n5. Fur should come mostly from:\n   - a soft plush / fuzzy shader in Unity,\n   - subtle surface breakup,\n   - light fluffy silhouette tufts only where needed.\n6. The hat must be rebuilt or reworked to look like a real chunky knit hat:\n   - deep purple knit body,\n   - cream cuff,\n   - fibrous pom-pom,\n   - soft fabric look rather than rigid ribbing.\n7. Preserve mobile performance and preserve the existing animation / gameplay compatibility.\n8. Show me:\n   - mascot-only front / side / rear previews,\n   - mascot in gameplay,\n   - direct comparison against my approved frame.\nPrioritize the mascot before more tunnel decoration work, because the mascot is currently the biggest visual problem.\nMy target is a soft, fluffy, premium pink plush character very close to my approved artwork - not a procedural fur experiment.\nContinue with the tunnel step 2B plan too, but I want you to look at this too.", "water": "OWNER 2026-11-27 ~16:30 (new account, verbatim): \"The character and water specialists keep improving the thick pink fur, the knitted hat, the flowing water and the translucent splashes ... Preserve my working gameplay, mascot, water, controls, collisions and camera. One change at a time, each checked with a side-by-side. Visual quality first.\" OWNER 2026-11-27 15:55 (verbatim): \"Have the existing character and water specialists prioritize realistic thick pink fur, knitted hat materials, natural flowing water and beautiful translucent splashes ... I want substantial visual improvements, not another series of tiny adjustments ... Improve the actual 3D materials, depth, reflections and artistic quality ... Work toward the appearance of my ENTIRE approved screen ... Preserve my existing working Unity gameplay ... Do not claim success prematurely.\" WATER, in this order: (1) NATURAL FLOWING WATER: glossy turquoise-blue water with visible downhill flow streaks, depth colour, reflections and soft translucency over the slide (approved frame: bright cyan-blue water with white flow lines and highlight streaks). (2) BEAUTIFUL TRANSLUCENT SPLASHES: milky, translucent splash crowns at both sides of the mascot with flying droplets (keep the V6 crown meshes in Art/Projected/FX as the base; translucent milky look, lowered onto the water). Bubbles stay; no extra glow."}, "resume": {"all": "PASS 10j = RESUME of pass 10i (cut ~19:20 by the 5-hour limit; NEW LEAD = session 8d2d815d from 19:25). Earlier: PASS 10i = RESUME of pass 10h: the previous account hit its 5-hour usage limit at 18:10 (run wf_48cc4b5b-713: both specialists cut without a report, the Accept phase never ran). NEW LEAD = session 9e4e986e (from 18:36). Read your own 'Screen S2 pass 10h' NOTES section + the files on disk and CONTINUE under a new NOTES heading 'Screen S2 pass 10j' (read your 'Screen S2 pass 10h' AND '10i' lines first) (never redo finished work). Output folder for this pass: screen_S2_p10j/ (your 10h / 10i files stay in screen_S2_p10h/, screen_S2_p10i/). Write NOTES after EVERY preview (usage limits cut runs).\nAUTHORITATIVE REFERENCES (owner 17:45, verbatim Captures/agents/_shared/OWNER_BRIEF_1745_google_flow_pack.txt): the ORIGINAL Google Flow video pack Reference/google_flow_pack_1735/ - Frames/frame_03.00s.png = THE S2 target (same frame as Reference/frames4k_720/f_03.00s.png), frame_04.00s.png = the mascot's real face + front, frame_07.50s.png = its angled front, frame_00.00s.png = entrance / roller / console; Crops/: mascot_rear_03s, mascot_front_04s, mascot_angled_07_5s, mascot_angled_rear_00s, fur_and_hat_03s, face_and_paws_04s, water_splashes_03s, splash_crown_04s, water_rails_00s, violet_wall_stars_03s, gold_violet_rings_03s, hatch_and_tunnel_00s, roller_00s, left_machinery_00s, later_machinery_07_5s, foam_and_bubble_00s, coin_03s, gem_00s; labelled sheets Flow_01_Mascot_Actual.png, Flow_02_Tunnel_Actual.png, Flow_03_Water_Objects_Actual.png. The three GENERATED ChatGPT sheets the owner sent at 17:35 (Reference/owner_sheets_1735/REF1-3 + crops/) are SECONDARY: use them only for angles / construction the video never shows; wherever they differ from the original, the ORIGINAL wins (owner: 'Replace any conflicting artistic guidance from the previously generated ChatGPT reference sheets ... NO REDESIGNING MY APPROVED ARTWORK'). Never change the rear gameplay camera because front frames exist.\nOWNER 17:35 MASTER DIRECTIVE (verbatim Captures/agents/_shared/OWNER_BRIEF_1735_master_visual_directive.txt - read the sections of your domain in full): premium animated-movie quality, 9/10+ similarity to the ORIGINAL, never call a build better without side-by-side proof.\nOWNER 18:36 (verbatim Captures/agents/_shared/OWNER_RULE_1836_autosave_recovery_diagnostic.txt): NO REPEATED FAILED METHODS, NO WASTED CREDITS, QUALITY FIRST. The owner is having ChatGPT audit the mascot pipeline because the character stayed ~5.5-6/10 over many passes: this pass must show a REAL visible gain in the images or say honestly that it did not.\nNO BUILD since lead_s2p10g (17:22): your BEFORE is still Captures/stills_s2p10g (+ bg/) and Captures/compare/build_s2p10g/. The lead's GATED preview of the cut 10h state (18:25, = the on-disk state now) = Captures/lead/gate_s2p10h/ (+ mascot/M1-M4), owner sheet Captures/sections/OWNER_S2_mascot_accept_s2p10h.png. NO FULL BUILD WITH A NEW MASCOT before the owner's acceptance sheet (owner 17:35 section 4H): the lead builds only after the Accept review; you never build or save the scene. Your Unity / Blender runs queue on Tools/heavy_lock.sh (also behind the lead's tunnel-lane previews) - expected; never kill anything.\nIn parallel the LEAD tunnel lane (Tools/workflows/bwk-s2-tunnel2b-r.js) applies one lever at a time in BWK_DrumWall, BWK_Gold, BWK_Emissive, MaterialLibrary.Environment.cs, MaterialLibrary.Assets.cs, MaterialLibrary.Lighting.cs, SceneBuilder.Environment.cs, SceneBuilder.Lighting.cs, SceneBuilder.Hall.cs, build_s2_rims_p10.py, build_s2_rings_p9.py and the hall / roller / machinery Blender scripts - never touch those. AI generators (SAM 3D, WorldGen, HunyuanWorld, Marble, TRELLIS, Meshy, the Blender MCP generate_3d / search_assets / import_asset) were rejected - never use them. The open Blender GUI window (MCP add-on, localhost:9876) belongs to the lead - leave it alone; run your own Blender headless through Tools/blender_run.sh. Judge on R2_rear_S2_like_3s_16x9 AND hero_mouth_9x16 (portrait gameplay): the owner reviews the PORTRAIT gameplay frame.", "water": "WHERE YOU STOPPED (pass 10i, water agent a4573c130456c4262, stopped early 19:20 by a stray lead wrap-up message meant for another stream - IGNORE that message, this pass is yours): NEW V7 splash crowns (Tools/Blender/scripts/build_fx_crown_v7.py -> private Art/Projected/FX/SM_FX_CrownV7_L/_R.fbx 5.1k / 6.0k tris; SceneBuilder.WaterFX.cs CrownV7On / UseCrownV7 / BuildCrownsV7, drop emitters on the V7 crowns): preview screen_S2_p10i/p1 = the RIGHT crown is a substantial milky sheet beside the right foot (R2 x ~750-940, y ~400-610 vs the original 720-941 / 403-650, silhouette IoU .93); the LEFT crown is still FAINT (too see-through on the pale water, mostly behind the coin). Landmark check NOT run yet. Your 19:14 MaterialLibrary.WaterFX.cs edit (S2 zone 29-52 m: _FlowLines 0, _GlossLines .1, _StreakAmount .05, _Out* = s2p10g water elsewhere) stays.\nLEAD 19:45 DECISION YOU MUST KEEP: the owner had ChatGPT review the environment ZIP; its BWK_S2_Water_Optics_Preview.patch is now IN BWK_Water.shader (_S2OpticsPreview, opticsW = zone only: flow lines x0, foam streaks x.45, ridge paint x.25, gloss x.2, probe reflection x.35, fresnel reflection off) and ENABLED on M_Water (MaterialLibrary.WaterFX.cs F(m, \"_S2OpticsPreview\", 1f)) after a protected side-by-side (Captures/lead/s2_optics/NOTES.md, sheets vs_gate/ + vs_gate_water2/): in the PORTRAIT gameplay view the thin white swirl / scratch lines vanish (they were the foam streaks: a test without the foam cut brought them back) = deeper smoother blue like the original. Cost: in R2 the bright fan rays across the water vanished and the water there now reads a little FLAT. Do not revert it; build ON it.\nTASK, one change at a time, each checked side by side (ref | before | after, + bg/ mascot hidden; before = Captures/lead/s2_optics/water_kept, the newest lead preview of exactly the current state incl. stills/): (1) LEFT crown: milky, dense, clearly visible beside the LEFT foot like the original's (water_splashes_03s / splash_crown_04s: curved milky sheets, rounded tips, aqua highlights, detached round droplets), not hidden by the coin, NEVER over his body -> preview; run Tools/landmark_check.py once against water_kept/stills (with -bwkStills on that preview) and fix any non-S2 regression; (2) flowing water on top of the kept optics: the original's water near the mascot = deep blue-turquoise with a FEW SOFT, WIDE, low-contrast light bands ALONG the flow + glossy highlights (no thin lines, no fan rays) - add depth / gloss without bringing back thin white lines; (3) splash material + flying round droplets if time remains. Never touch the mascot files, the lead tunnel-lane files (BWK_DrumWall, MaterialLibrary.Environment/Assets/Lighting.cs, SceneBuilder.Environment/Lighting/Hall.cs) or CaptureTools.cs. A tunnel-lane worker runs concurrently: heavy runs queue on Tools/heavy_lock.sh (expected)."}, "gaps": {"score_with_mascot": 7.3, "score_scenery_only": 7.0, "gaps": [{"rank": 1, "owner": "character", "what": "Mascot coat = scale-like 'pinecone' cells over the whole body and arms (s2p10f-s2p10g), coral-orange colour, lower body tapering to a point; the ORIGINAL (Google Flow 3.00 / 4.00 / 7.50 s) is a soft round plush ball in warm ROSE pink with fine soft strands, a fluffy irregular outline and a lighter cream-pink seat", "where": "mascot body, centre", "fix": "OWNER METHOD 17:20: sculpt to the approved views in Blender (v5 skeleton), groom real fur, BAKE albedo / normal / AO into the body textures, smooth plush shader in Unity (no procedural cone fur)", "measure": "crop (560,330,760,520) on R2 + hero_mouth_9x16 body crop: mean colour, silhouette fluff visible"}, {"rank": 2, "owner": "water", "what": "Water is a flat cyan sheet without flow; the approved water is glossy turquoise with white downhill flow streaks, highlight lines and translucency", "where": "lane centre and lower third", "fix": "flow-streak detail scrolling along the slide, stronger fresnel reflections, depth tint, translucency", "measure": "crop (300,500,1000,720): streak contrast, highlight lines"}, {"rank": 3, "owner": "character", "what": "Knitted hat looks like hard plastic ribs and the pom-pom is spiky / flat; approved = chunky SOFT knit (deep purple, pale lilac-white stripe, cream cuff), big ROUND fibrous pom-pom", "where": "hat, upper centre", "fix": "real knit high-poly (round yarn tubes, V-stitch ribs) baked to normal / AO / albedo on the smooth hat; groomed yarn-ball pom-pom baked onto a round core + soft fibrous fringe", "measure": "crop (520,170,720,400)"}, {"rank": 4, "owner": "water", "what": "Splash crowns: the approved splashes are big translucent milky crowns with flying droplets rising out of the water at BOTH FEET, beside the body (never over it); ours are either small beside the arms (s2p10e) or, in pass 10f p2-p4, tall sprays standing in front of his back that cover the body", "where": "mascot left and right, water line", "fix": "translucent milky material on the V6 crowns, droplets, sit on the water", "measure": "crops (400,380,560,620) and (740,380,960,620)"}, {"rank": 5, "owner": "lead", "what": "Tunnel: violet bands should be thick glowing lilac neon bands, walls deep reflective blue-violet metal with small dark slits, bright glowing core far away", "where": "tunnel, upper half", "fix": "lead step 2b redo (darker walls, glow only at the band edges, smaller slits, distant core) - lead session 6d001969", "measure": "lead"}, {"rank": 6, "owner": "lead", "what": "Pink fluffy roller top-left is a flat pink block", "where": "upper left", "fix": "lead, after step 2b", "measure": "lead"}]}}
const SCREEN = A.screen || 'S2'
const MODE = A.mode || 'fix'
const PASS = A.pass || 1
const BASE = A.base || 'checkpoint-20-r8'
const BEFORE = A.before || 'Captures/stills_r8'
const RESUME = A.resume || {}
const resumeFor = k => (RESUME.all ? RESUME.all + '\n' : '') + (RESUME[k] ? RESUME[k] + '\n' : '')

// One entry per screen. ours = the still name written by every full build / CaptureStills (+ bg/ = mascot hidden);
// preview = the fastest Unity run that shows this screen after an agent's change.
const SCREENS = {
  S2: {
    // lead 2026-11-26 20:25 (owner takeover brief item 5): the reference 3.0 s frame is AT the washing-machine door (40 m);
    // the old hero_* stills are 65 m past it (105.5 m). R2 = comparison-only camera solved on the reference landmarks
    // (door rim + mascot, rms 8.4 px), hero_mouth = the unchanged gameplay rig at the same spot (35 m).
    name: 'S2 HERO GAMEPLAY SCREEN AT THE WASHING-MACHINE DOOR: the mascot slides down the blue water slide with glossy pink / rainbow rails, about to pass through the huge gold hatch ring (40 m); outside the hatch: pink fluffy roller upper left, blue machinery + gold pipe left, big foam banks; inside: perforated violet drum, neon stars, receding gold bulb rings (video 3.0 s). Our matched camera = R2_rear_S2_like_3s_16x9.png (comparison only, mascot at 35 m); hero_mouth_* = the gameplay rig at the same spot',
    ref4k: ['Reference/frames4k/f_03.00s.png'],
    ref720: ['Reference/frames4k_720/f_02.75s.png', 'Reference/frames4k_720/f_03.00s.png', 'Reference/frames4k_720/f_03.25s.png'],
    ours: ['R2_rear_S2_like_3s_16x9.png', 'hero_mouth_16x9.png', 'hero_mouth_9x16.png'],
    preview: 'bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut <dir> (~2.5 min: <dir>/R2_rear_S2_like_3s_16x9.png, hero_mouth_16x9.png, hero_mouth_9x16.png, bg/, R2_vs_reference_16x9.png; add -bwkEnvHall to rebuild the hall set HallExtras_r7 - door ring, mouth drum, rollers, machinery - in memory so new hall models / placements show)',
  },
  S7: {
    name: 'S7 GOLDEN PORTAL FINALE: the mascot rests ~5.5 m before the portal and turns to face the rear camera; thick gold bulb ring + warm golden starburst fill the frame (video 14.5 s)',
    ref4k: ['Reference/frames4k/f_14.00s.png', 'Reference/frames4k/f_15.00s.png'],
    ref720: ['Reference/frames4k_720/f_14.25s.png', 'Reference/frames4k_720/f_14.50s.png', 'Reference/frames4k_720/f_14.75s.png'],
    ours: ['10_finale_16x9.png', '10_finale_9x16.png'],
    preview: 'bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut <dir> -bwkStills (~7 min: <dir>/stills/10_finale_16x9.png, _9x16, bg/)',
  },
  S1: {
    name: 'S1 OPENING MACHINE HALL: pink console, fluffy pink / white / cyan rollers, cyan glass arches, large illuminated tunnel entrance (video 0.5 s)',
    ref4k: ['Reference/frames4k/f_00.00s.png', 'Reference/frames4k/f_01.00s.png'],
    ref720: ['Reference/frames4k_720/f_00.25s.png', 'Reference/frames4k_720/f_00.50s.png', 'Reference/frames4k_720/f_00.75s.png'],
    ours: ['01_hall_start_16x9.png', '01_hall_start_9x16.png'],
    preview: 'bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut <dir> -bwkStills (~7 min: <dir>/stills/01_hall_start_*)',
  },
  S5: {
    name: 'S5 SOCK CHAMBERS: master washing-machine doors with socks + rainbow interior, pink glass pipes, gold rings (video 8.25 s; front comparison camera R5 + rear 07_chambers)',
    ref4k: ['Reference/frames4k/f_08.00s.png', 'Reference/frames4k/f_09.00s.png'],
    ref720: ['Reference/frames4k_720/f_08.00s.png', 'Reference/frames4k_720/f_08.25s.png', 'Reference/frames4k_720/f_08.50s.png'],
    ours: ['R5_front_S5_like_8s_16x9.png', '07_chambers_9x16.png'],
    preview: 'bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut <dir> -bwkStills (~7 min: <dir>/stills/R5_front_*, 07_chambers_*)',
  },
}
// lead 2026-11-26 21:50: owner 21:33 sent his 7 authoritative section frames (identical to Reference/frames4k_720 at
// 0.75 / 3.00 / 4.50 / 6.75 / 8.25 / 11.25 / 14.25 s) + 10 priority asset sheets (02 07 11 12 15 16 17 18 23 24) and asked
// to correct the scenery of ALL seven sections -> a whole-level "masters" screen: fix assets that recur in several sections.
SCREENS.ALL = {
  name: 'WHOLE LEVEL, ALL SEVEN SECTIONS (owner frames: S1 0.75 s opening laundry hall; S2 3.00 s golden tunnel entrance; S3 4.50 s metallic drum tunnel; S4 6.75 s first golden sock chamber; S5 8.25 s pink pipes + sock chambers; S6 11.25 s cyan pipes + later chambers; S7 14.25 s golden destination). S3-S7 are FRONT views in the video (our matched comparison cameras R3-R6 + 10_finale); the gameplay camera is always BEHIND the mascot (07_chambers / hero_mouth = gameplay views)',
  scope: 'OWNER 2026-11-26 21:33 (sent his 7 authoritative section frames + 10 priority asset sheets): "Use them to correct the complete scenery throughout all seven sections ... reconstruct the actual geometry, scenery placement, golden doors, washing chambers, rollers, machinery, glass pipes, water, foam, bubbles, lighting, materials ... approximately 9-10/10 ... Use Blender to construct properly detailed 3D assets and Unity to assemble ... substantial visible improvements". THIS RUN builds / fixes MASTER assets that recur across the sections (one change -> every section that shows it); check each change in every section still that shows it.',
  ref4k: ['Reference/frames4k/f_03.00s.png'],
  ref720: ['00.75', '03.00', '04.50', '06.75', '08.25', '11.25', '14.25'].map(t => `Reference/frames4k_720/f_${t}s.png`)
    .concat(['02_Striped_fluffy_washing_roller', '11_Ornate_gold_sock_chamber', '12_Colorful_socks_and_rainbow_insert', '15_Glossy_multicolored_slide_rails', '16_Flowing_turquoise_water', '17_Soft_soap_foam_banks', '18_Milky_splash_crown'].map(n => `Reference/asset_library/Individual_References/${n}.png`)),
  ours: ['01_hall_start_16x9.png', 'R2_rear_S2_like_3s_16x9.png', 'R3_front_S3_like_5s_16x9.png', 'R4_front_S4_like_7s_16x9.png', 'R5_front_S5_like_8s_16x9.png', 'R6_front_S6_like_11s_16x9.png', '10_finale_16x9.png', '07_chambers_9x16.png', 'hero_mouth_9x16.png'],
  preview: 'bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut <dir> (~2.5 min: R2 + hero_mouth only) ; add -bwkStills for every section still (~7 min: <dir>/stills/01_hall_start_*, R3..R6_*, 07_chambers_*, 10_finale_* + bg/) ; add -bwkEnvHall (hall set: door ring, rollers, machinery) and / or -bwkEnvChambers (PF_WashDoor_Master chambers) to rebuild those sets in memory so new models / placements show',
}
const S = SCREENS[SCREEN]
if (!S) throw new Error('unknown screen ' + SCREEN + ' (known: ' + Object.keys(SCREENS).join(', ') + ')')
const OURS = S.ours.map(f => `${ROOT}/${BEFORE}/${f}`).concat(S.ours.map(f => `${ROOT}/${BEFORE}/bg/${f}`))
const REFS = S.ref4k.concat(S.ref720).map(f => `${ROOT}/${f}`)

const SCALE = `Scale (strict, the owner rejects inflated scores): 9-10 = the same scene - every landmark present, same proportions, density, materials and lighting, only small details differ; 7-8 = clearly the same place with a few missing or wrong elements; 5-6 = same theme, some right landmarks, many wrong / missing; 3-4 = generic tunnel or hall missing most landmarks; 1-2 = unrelated. Half points allowed. The mascot rows count the mascot (from build s2p3 on, the in-game mascot is the v4 model UNDER TEST - owner 21:25: test it, the old model stays the fallback; s2p3 itself showed v4 turned 180 deg by an export bug, fixed in s2p3b), scenery-only rows ignore it. Our gameplay camera is BEHIND the mascot by the owner's decision, so judge the WORLD (objects, shapes, sizes, placement, density, materials, colours, light), not the exact framing.`

const GAPS = {
  type: 'object',
  properties: {
    score_with_mascot: { type: 'number' },
    score_scenery_only: { type: 'number' },
    gaps: { type: 'array', items: { type: 'object', properties: {
      rank: { type: 'number' },
      what: { type: 'string', description: 'The visible difference, concrete (object, shape, size, colour, material, light)' },
      where: { type: 'string', description: 'Where in the frame (e.g. upper left ring, lane centre, far end)' },
      owner: { type: 'string', enum: ['assets', 'metal', 'water', 'character', 'motion', 'lead'] },
      fix: { type: 'string', description: 'What would make our render match, in one or two sentences' },
      measure: { type: 'string', description: 'How to measure it: crop box (x0,y0,x1,y1 on the 1280x720 frames) + the property (mean colour, coverage %, size in px)' } },
      required: ['rank', 'what', 'where', 'owner', 'fix', 'measure'] } },
  },
  required: ['score_with_mascot', 'score_scenery_only', 'gaps'],
}

const REPORT = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: 'What now looks different on this screen, <= 150 words, plain language' },
    fixed_gaps: { type: 'array', items: { type: 'string' }, description: 'Gap ranks / names fixed, with the before -> after measurement' },
    files_changed: { type: 'array', items: { type: 'string' } },
    previews: { type: 'array', items: { type: 'string' }, description: 'Absolute paths of the newest preview renders / comparison sheets' },
    needs_lead_build: { type: 'boolean', description: 'true if placed geometry changed (shows only after the lead build)' },
    mobile: { type: 'string' },
    remaining_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'fixed_gaps', 'files_changed', 'previews', 'needs_lead_build', 'mobile', 'remaining_gaps'],
}

const DOMAIN = {
  metal: 'You are GOLD + METAL + LIGHT (lighting owner, technical-artist; the environment agent is idle, so the drum-wall material is yours too). Output folder Captures/agents/lighting/',
  assets: 'You are the 3D ENVIRONMENT RECONSTRUCTION SPECIALIST (the asset artist: Blender Python, bevel / circular-profile modelling, Geometry Nodes where useful, Unity prefabs + materials; MASTER-ASSET CONSTRUCTION - build new, properly detailed geometry where the existing model is inadequate instead of recolouring / resizing it; match the reference scene\'s geometry, sizes, proportions, placement and orientation; the owner\'s 24-asset library Reference/asset_library/ is the construction guide). Output folder Captures/agents/assets/',
  water: 'You are WATER + FOAM + BUBBLES + GLASS (water/FX owner, unity-shader-specialist). Output folder Captures/agents/waterfx/',
  // lead 2026-11-27: owner APPROVED targeted mascot improvements for S2 pass 7 (keep v4 + skeleton + animations as the fallback)
  character: 'You are the CHARACTER ARTIST (the pink mascot: Tools/Blender/scripts/build_mascot_v4.py + build_mascot_rig.py, BWK_Fur / BWK_Character shaders, MaterialLibrary.Character.cs). Your Captures/agents/character/NOTES.md has the v4 history. Output folder Captures/agents/character/',
  // owner 2026-11-27 06:20 role E: seated sliding motion + continuous rear camera (gameplay feel; never the gameplay rules)
  motion: 'You are the CHARACTER ANIMATION + CAMERA SPECIALIST (owner role E): the mascot SITS UPRIGHT ON HIS BOTTOM while sliding, faces the travel direction, feet forward, leans / tilts through curves, bounces gently with the water, natural arm / foot motion, jump / landing / lane-change reactions that always return to the seated pose; the portrait rear camera follows behind his back through every curve, climb and descent with smooth banking, no cuts, no front views in normal play (only the existing destination celebration turns him to the player). Prove it with Play Mode recordings (Tools/review_recording.sh) and the Play Mode test asserts. Output folder Captures/agents/motion/',
}
const FILES = 'FILE OWNERSHIP (CLAUDE.md "Parallel specialists"): metal = SceneBuilder.Lighting.cs, MaterialLibrary.Lighting.cs, MaterialLibrary.Environment.cs (material values), SceneBuilder.Hall.cs (material values), BWK_Gold, BWK_Emissive, BWK_DrumWall, BWKCommon.hlsl, Assets/Settings/*; assets = build_hall_assets.py, build_track.py, build_machinery.py, build_shot0825_assets.py, build_master_door.py, MaterialLibrary.Assets.cs, Prefabs/PF_*.prefab, SceneBuilder.Environment.cs + SceneBuilder.Hall.cs (model / material references and the placement fixes allowed below); water = BWK_Water, BWK_Glass, BWK_Soft, MaterialLibrary.WaterFX.cs, SceneBuilder.WaterFX.cs, TextureGenerator.cs, SplashFX.cs, build_fx_v2.py, build_props.py; character = build_mascot_v4.py (+ its new-version mode), build_mascot_rig.py exports to NEW file names, BWK_Fur, BWK_Character, MaterialLibrary.Character.cs; motion = MascotAnimatorDriver.cs, RunnerCameraRig.cs, CameraDirector.cs, AnimatorBuilder.cs (states / blend tree / transitions - not FbxPath, that is the lead switch), RunnerController.cs VISUAL lean / bob / tilt parameters only (never speed, lanes, jump physics, colliders), GameplayCaptureTests.cs (new asserts only), clip changes requested from the character agent through NOTES.md. Edit only your own files; ask through your NOTES.md for anything else.'

function fixBrief(k, gaps) {
  const mine = gaps.gaps.filter(g => g.owner === k)
  const rest = gaps.gaps.filter(g => g.owner !== k)
  const directive = (A.directives && A.directives[k]) ? `OWNER DIRECTIVE FOR THIS PASS (highest priority, in this order): ${A.directives[k]}\n` : ''
  return `${resumeFor(k)}${DOMAIN[k]}screen_${SCREEN}_p${PASS}/ (create it). You work on Bubble Wash Kingdom (Unity 6.3 URP 17.3 + Blender 5.3) at ${ROOT} for the lead.
${S.scope ? S.scope + ' Scope: ' + S.name + '.' : `OWNER 2026-11-26 18:05: "do a couple of screens, one at a time" (target about 8.5/10 per screen, honest numbers only). THIS RUN improves ONE screen only - ${S.name}.`}
${directive}OWNER 2026-11-26 20:15: "substantial improvements in actual 3D geometry, materials, scenery composition, lighting and environmental depth - not numerous minor adjustments that barely improve the overall appearance". Spend the time on the few changes that visibly change the frame most.
Approved reference (private, never in tracked files): ${REFS.join(', ')}. Our current render (build ${BASE}): ${OURS.join(', ')} (bg/ = mascot hidden). Independent score now: ${gaps.score_with_mascot} with mascot / ${gaps.score_scenery_only} scenery only.
YOUR GAPS (independent judge, biggest first - fix them in this order):
${mine.map(g => `#${g.rank} ${g.what} [${g.where}] -> ${g.fix} | measure: ${g.measure}`).join('\n') || '(none assigned - take the highest-ranked gaps below that your files can fix)'}
OTHER GAPS (context; other specialists or the lead own them): ${rest.map(g => `#${g.rank} (${g.owner}) ${g.what}`).join('; ')}
Read your own NOTES.md (newest section) first and continue from the files on disk.
LOOP: batch your changes -> ONE preview -> compare the SAME crops (reference vs before vs after) with Tools/img_crop.py / Tools/img_stats.py / Tools/triptych.py -> next batch. Preview: ${S.preview}, with <dir> = your output folder above. At most 4 previews. Append 2-4 lines to a "Screen ${SCREEN} pass ${PASS}" section of your NOTES.md after EVERY preview (the usage limit may cut the run).
WHAT COUNTS: only what this screen's camera sees - shapes and proportions measured on the reference, surface detail, material response (specular shape, reflections, fresnel, roughness), colour, light direction, density of the visible landmarks. Never fake it with overall brightness, saturation, bloom or extra props; no generic film effects (grain, chromatic aberration, lens flares, heavy DOF, haze).
PLACEMENT: allowed ONLY for objects this screen's camera sees, measured on the reference (sizes / positions of rings, rails, stars, windows, pipes, foam, portal), never inside the slide corridor or the lanes. Agent previews keep the SAVED scene's environment geometry (PreviewRebuildsEnvironment = false): material / shader / lighting / FX changes show at once, new placed geometry only after the lead's integration build - say so in needs_lead_build, and prove such changes with a Blender render from this screen's camera angle if you cannot preview them.
DO NOT CHANGE: the camera rig (owner 21:25 approved a wider PORTRAIT gameplay framing - the LEAD tests and applies it, it may change hero_mouth_* during this run; judge your work on R2_rear_S2_like_3s_16x9 = the fixed comparison camera, and its bg/ copy), gameplay (RunnerController, input, coins / gems as TrackItems, colliders, track path), the mascot model and its materials (ONLY the character agent may change them, under the owner's 2026-11-27 approval: new export next to SK_Mascot_v4.fbx, same skeleton / takes / material names, v4 kept as the fallback), the intro (paused).
NO LOST LANDMARKS (owner 2026-11-27: "do not allow improvements to one asset to cause another important asset to disappear from view" - p4 moved the S5 pink glass pipe out of view and nobody noticed until the judges): before your report run \`"/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I Tools/landmark_check.py ${BEFORE} <your newest -bwkStills preview dir>/stills\` and fix every LOST line your change caused (gold rings / portholes, pink or cyan pipes, neon stars, socks / rainbow, crowns); say in your report what it printed.
RULES: every Unity / Blender command through Tools/unity_run.sh or Tools/blender_run.sh in the FOREGROUND with the Bash timeout 600000 ms - they queue on Tools/heavy_lock.sh, so prepare your next batch while the other specialist's run goes; never kill Unity / Blender; bash Tools/cs_check.sh after EVERY C# edit and never leave code that does not compile; NO safe_build (the lead builds once after this run); no git commits; images with reference pixels only in Captures/ (the repo is PUBLIC); camera projection of the reference was rejected (14:55) - real geometry + materials only; downloads only Poly Haven CC0 1K maps (max 2, into a new empty folder, LICENSE.txt line), nothing else; no purchases; no new packages. MOBILE (Assets/Settings/Mobile_RPAsset): modest triangle counts (LODs where you add detail), no screen-space reflections, no extra realtime lights per object; say what is PC-only.
${FILES}
Time box ${A.minutes || 30} minutes from your start, then return the report.`
}

if (MODE === 'judge') {
  const TAG = A.tag || `${SCREEN.toLowerCase()}p${PASS}`
  const SHEET = `${ROOT}/Captures/sections/${SCREEN}_focus_${TAG}.png`
  const EXTRA = (A.extra || []).map(f => `${ROOT}/${f}`)
  const JUDGED = {
    type: 'object',
    properties: {
      prev_with_mascot: { type: 'number' }, new_with_mascot: { type: 'number' },
      prev_scenery_only: { type: 'number' }, new_scenery_only: { type: 'number' },
      improved: { type: 'array', items: { type: 'string' } },
      regressions: { type: 'array', items: { type: 'string' } },
      top_gaps: { type: 'array', items: { type: 'string' }, description: 'Biggest remaining differences first' },
    },
    required: ['prev_with_mascot', 'new_with_mascot', 'prev_scenery_only', 'new_scenery_only', 'improved', 'regressions', 'top_gaps'],
  }
  const RUBRIC = `You are an independent visual judge for Bubble Wash Kingdom, a Unity game rebuilt from the owner's approved Google Flow video. Judge ONLY what the images show; never read the specialists' notes or reports. Screen: ${S.name}.
Sheet ${SHEET}: column 1 = the ORIGINAL VIDEO FRAME, column 2 = PREVIOUS Unity build, column 3 = NEWEST Unity build; row 1 = with the mascot, row 2 = the same renders with the mascot hidden.${EXTRA.length ? ' Extra views (same order): ' + EXTRA.join(', ') + '.' : ''} Full-resolution reference: ${REFS.join(', ')}.
${SCALE}
Read every image with the Read tool (PNG).`
  phase('Judge')
  const j = await agent(`${RUBRIC}\nScore previous and newest, list what improved, what regressed and the remaining gaps (biggest first, concrete).`,
    { label: `judge ${SCREEN} ${TAG}`, phase: 'Judge', schema: JUDGED, effort: 'high' })
  const fin = await agent(`${RUBRIC}\nYou are the SKEPTIC. A judge scored this screen: ${JSON.stringify(j)}. Look at the images yourself and try to REFUTE each score: lower any inflated score (default to the lower score when unsure), raise one only with a concrete visual reason. Return the final scores and the remaining gaps (biggest first) for the next pass.`,
    { label: `skeptic ${SCREEN} ${TAG}`, phase: 'Judge', schema: JUDGED, effort: 'high' })
  return { screen: SCREEN, tag: TAG, judge: j, final: fin }
}

// args.gaps = a gap list from an earlier { mode: 'gaps' } run of the same screen and stills (skips the gap judge)
phase('Gaps')
const gaps = A.gaps || await agent(`You are an independent visual judge for Bubble Wash Kingdom, a Unity game rebuilt from the owner's approved Google Flow video. Never read the specialists' notes or reports.
Screen: ${S.name}. Approved reference frames: ${REFS.join(', ')}. Our current Unity renders: ${OURS.join(', ')} (bg/ = mascot hidden).
${SCALE}
Read every image with the Read tool. Score our render now, then list the 6-10 most visible differences, biggest first, each with its owner: assets = the shape / geometry / proportions of props (rails, rollers, console, windows / doors, socks, pipes' geometry, starburst geometry, arches), metal = gold, metal walls, bulb rings, neon stars' material, light colour / direction, reflections, colour grade, water = water surface, foam, milk crowns, splashes, bubbles, glass + liquid shading, character = the mascot, lead = camera / framing / track layout. Give each a concrete fix and a measurable check on the 1280x720 frames.`,
  { label: `gaps ${SCREEN} pass ${PASS}`, phase: 'Gaps', schema: GAPS, effort: 'high' })
if (!gaps || !gaps.gaps || !gaps.gaps.length) return { screen: SCREEN, pass: PASS, error: 'no gap list' }
log(`${SCREEN} now ${gaps.score_with_mascot} with mascot / ${gaps.score_scenery_only} scenery only; ${gaps.gaps.length} gaps`)
if (MODE === 'gaps') return { screen: SCREEN, before: BEFORE, gaps }   // gap list only (cheap); pass it later as args.gaps

// pick the two specialist domains that own the most (rank-weighted) gaps unless the lead named them
const weight = { assets: 0, metal: 0, water: 0, character: 0, motion: 0 }
gaps.gaps.forEach(g => { if (g.owner in weight) weight[g.owner] += Math.max(1, 11 - g.rank) })
const ranked = Object.keys(weight).sort((a, b) => weight[b] - weight[a])
const pick = (Array.isArray(A.agents) && A.agents.length) ? A.agents : ranked.slice(0, 2)
const skipped = ranked.filter(k => !pick.includes(k) && weight[k] > 0)
log(`fixing with ${pick.join(' + ')} (weights ${JSON.stringify(weight)})` + (skipped.length ? `; not this pass: ${skipped.join(', ')}` : ''))
const leadGaps = gaps.gaps.filter(g => g.owner === 'lead' || g.owner === 'character')
if (leadGaps.length) log(`lead / character gaps (not given to specialists): ${leadGaps.map(g => '#' + g.rank + ' ' + g.what).join('; ')}`)

phase('Fix')
// lead 6d001969 17:50 (owner 17:35 section 4H): the character's result goes through an independent acceptance review BEFORE any full
// build - a judge, then a skeptic who tries to refute it. They read only images (never the specialists' notes).
const ACCEPT = {
  type: 'object',
  properties: {
    score_new: { type: 'number', description: 'NEW mascot vs the ORIGINAL video mascot, 0-10, half points allowed' },
    score_s2p10h_mid: { type: 'number', description: 'the s2p10h gate state (current best)' },
    score_s2p10g: { type: 'number' }, score_s2p10f: { type: 'number' }, score_s2p10e: { type: 'number' },
    elements: { type: 'array', items: { type: 'object', properties: {
      element: { type: 'string', enum: ['body shape', 'fur surface', 'fur colour', 'silhouette softness', 'hat knit', 'cuff + stripe', 'pom-pom', 'face', 'arms + paws', 'feet + pads', 'in-game read'] },
      verdict: { type: 'string', enum: ['better', 'same', 'worse'] },
      note: { type: 'string' } }, required: ['element', 'verdict', 'note'] } },
    verdict: { type: 'string', enum: ['ACCEPT', 'PARTIAL', 'REJECT'] },
    keep: { type: 'string', description: 'Which parts of the new treatment to keep and which to revert to the best previous version' },
    top_gaps: { type: 'array', items: { type: 'string' }, description: 'Biggest remaining differences to the ORIGINAL, biggest first' },
  },
  required: ['score_new', 'score_s2p10h_mid', 'score_s2p10g', 'score_s2p10f', 'score_s2p10e', 'elements', 'verdict', 'keep', 'top_gaps'],
}
async function acceptReview(r) {
  const pv = (r && r.previews) || []
  const RUB = `You are an independent visual judge for the Bubble Wash Kingdom mascot - the owner's ACCEPTANCE GATE before any full game build (owner brief ${ROOT}/Captures/agents/_shared/OWNER_BRIEF_1735_master_visual_directive.txt section 4, and ${ROOT}/Captures/agents/_shared/OWNER_BRIEF_1745_google_flow_pack.txt). Never read the specialists' NOTES.md or reports; judge only images, with the Read tool (PNG).
AUTHORITATIVE ORIGINAL (the owner's Google Flow video pixels): ${ROOT}/Reference/google_flow_pack_1735/Crops/mascot_rear_03s.png, mascot_front_04s.png, mascot_angled_07_5s.png, mascot_angled_rear_00s.png, fur_and_hat_03s.png, face_and_paws_04s.png and Frames/frame_03.00s.png, frame_04.00s.png, frame_07.50s.png. (Generated ChatGPT sheets in ${ROOT}/Reference/owner_sheets_1735/ only for angles the video never shows - the ORIGINAL wins.)
CANDIDATE = the character agent's newest acceptance sheet + preview: ${pv.length ? pv.join(', ') : '(none returned - use the newest ' + ROOT + '/Captures/agents/character/screen_S2_p' + PASS + '/ACCEPT_prev*.png and its prev*/ folder)'} (the preview folder holds mascot/M1_mascot_rear.png, M2_mascot_side_right.png, M3_mascot_front.png, M4_mascot_three_quarter.png, R2_rear_S2_like_3s_16x9.png, hero_mouth_9x16.png).
PREVIOUS VERSIONS: s2p10h-mid (the CURRENT BEST, cut pass 10h quick-win state, lead read ~6.3/10) = ${ROOT}/Captures/lead/gate_s2p10h/ (mascot/M1-M4 + R2_rear_S2_like_3s_16x9.png + hero_mouth_9x16.png) and its sheet ${ROOT}/Captures/sections/OWNER_S2_mascot_accept_s2p10h.png; s2p10g = ${ROOT}/Captures/lead/mascot_before_s2p10g/ (same mascot-alone cameras + in-game) and its sheet ACCEPT_s2p10g_baseline.png; s2p10f in-game ${ROOT}/Captures/stills_s2p10f/R2_rear_S2_like_3s_16x9.png + hero_mouth_9x16.png; s2p10e in-game ${ROOT}/Captures/compare/build_s2p10e/R2_vs_reference_16x9.png + hero_vs_reference_9x16.png (right half = render).
MUST-HAVES: soft round plump plush-toy body (not tall / narrow / tapered); warm LIGHT rose-pink fur with natural variation (never burgundy, flat purple, neon pink, coral-orange or grey); fine irregular strands and a soft irregular fluffy silhouette; ABSOLUTELY NO pinecone / scale / petal clumps, cones, uniform spikes or plastic hair; hat = real thick knitted wool (interlocking loops, yarn variation, soft edges, thick rounded brim, pale stripe), the yellow star in front, a round fibrous pom-pom (lavender tips, dark core, no dots / spikes); big glossy eyes, friendly smile; short rounded arms; white fluffy feet with pink pads.
SCALE (strict - the owner rejects inflated scores): 9-10 = matches the original in style, colour and detail; 7-8 = clearly the same character, some material / shape differences; 5-6 = same idea, visibly different surface or proportions; below 5 = wrong.`
  const j = await agent(`${RUB}\nScore the NEW mascot and each previous version against the ORIGINAL, judge every element (new vs the best previous version) and give ACCEPT (clearly better overall than the BEST previous version = s2p10h-mid, nothing important worse), PARTIAL (keep the better parts, revert the worse ones - say exactly which) or REJECT (keep the best previous version).`,
    { label: `judge mascot p${PASS}`, phase: 'Accept', schema: ACCEPT, effort: 'high' })
  const sk = await agent(`${RUB}\nYou are the SKEPTIC. A judge returned: ${JSON.stringify(j)}. Look at every image yourself and try to REFUTE it: lower any inflated score (take the lower one when unsure), downgrade ACCEPT to PARTIAL / REJECT if any must-have regressed (scale / pinecone look, darker, greyer or more orange fur, plastic hat, spiky pom-pom, broken face). Return the final verdict.`,
    { label: `skeptic mascot p${PASS}`, phase: 'Accept', schema: ACCEPT, effort: 'high' })
  return { judge: j, final: sk }
}
const reports = await parallel(pick.map(k => () =>
  agent(fixBrief(k, gaps), { label: `${k} ${SCREEN} pass ${PASS}`, phase: 'Fix', schema: REPORT })
    .then(async r => (k === 'character' && r) ? { agent: k, report: r, accept: await acceptReview(r) } : { agent: k, report: r })))
const acc = reports.filter(Boolean).find(x => x.accept)
if (acc && acc.accept.final) log(`mascot acceptance: ${acc.accept.final.verdict} (new ${acc.accept.final.score_new} vs s2p10h-mid ${acc.accept.final.score_s2p10h_mid}, s2p10g ${acc.accept.final.score_s2p10g})`)
return { screen: SCREEN, pass: PASS, gaps, reports: reports.filter(Boolean), lead_gaps: leadGaps }
