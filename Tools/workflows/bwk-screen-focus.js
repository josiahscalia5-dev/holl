export const meta = {
  name: 'bwk-screen-focus',
  description: 'One screen at a time: an independent judge lists the biggest differences of ONE gameplay screen vs its approved video frame, two specialists fix only those with a fast preview loop; judge mode scores the screen after the lead build',
  whenToUse: 'Owner 2026-11-26 18:05 "do a couple of screens, one at a time": args {screen, mode: "fix"} -> lead build + Captures/sections/<screen>_focus_<tag>.png -> args {screen, mode: "judge", tag}',
  phases: [
    { title: 'Gaps', detail: 'one independent judge ranks the screen\'s visible differences and assigns each to a specialist' },
    { title: 'Fix', detail: 'two specialists fix only this screen (max 2 at once on this 4-thread laptop)' },
    { title: 'Judge', detail: 'judge mode: one judge + one skeptic score the screen before -> after' },
  ],
}

// args (fix):   { screen: 'S2', mode: 'fix', pass: 1, base: '<newest tag>', before: 'Captures/stills_r8m', agents?: ['metal','water'], resume?: {all, metal, assets, water} }
// args (judge): { screen: 'S2', mode: 'judge', tag: 's2p1' }  -> reads Captures/sections/<screen>_focus_<tag>.png (made by the lead)
// args (gaps):  { screen: 'S2', mode: 'gaps', before: 'Captures/stills_r8m' } -> only the gap list (pass it to fix mode as args.gaps)
const ROOT = 'C:/Users/josia/thanksgiving'
const A = args || {}
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
      owner: { type: 'string', enum: ['assets', 'metal', 'water', 'character', 'lead'] },
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
}
const FILES = 'FILE OWNERSHIP (CLAUDE.md "Parallel specialists"): metal = SceneBuilder.Lighting.cs, MaterialLibrary.Lighting.cs, MaterialLibrary.Environment.cs (material values), SceneBuilder.Hall.cs (material values), BWK_Gold, BWK_Emissive, BWK_DrumWall, BWKCommon.hlsl, Assets/Settings/*; assets = build_hall_assets.py, build_track.py, build_machinery.py, build_shot0825_assets.py, build_master_door.py, MaterialLibrary.Assets.cs, Prefabs/PF_*.prefab, SceneBuilder.Environment.cs + SceneBuilder.Hall.cs (model / material references and the placement fixes allowed below); water = BWK_Water, BWK_Glass, BWK_Soft, MaterialLibrary.WaterFX.cs, SceneBuilder.WaterFX.cs, TextureGenerator.cs, SplashFX.cs, build_fx_v2.py, build_props.py. Edit only your own files; ask through your NOTES.md for anything else.'

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
DO NOT CHANGE: the camera rig (owner 21:25 approved a wider PORTRAIT gameplay framing - the LEAD tests and applies it, it may change hero_mouth_* during this run; judge your work on R2_rear_S2_like_3s_16x9 = the fixed comparison camera, and its bg/ copy), gameplay (RunnerController, input, coins / gems as TrackItems, colliders, track path), the mascot model and its materials (character work needs the owner's approval), the intro (paused).
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
const weight = { assets: 0, metal: 0, water: 0 }
gaps.gaps.forEach(g => { if (g.owner in weight) weight[g.owner] += Math.max(1, 11 - g.rank) })
const ranked = Object.keys(weight).sort((a, b) => weight[b] - weight[a])
const pick = (Array.isArray(A.agents) && A.agents.length) ? A.agents : ranked.slice(0, 2)
const skipped = ranked.filter(k => !pick.includes(k) && weight[k] > 0)
log(`fixing with ${pick.join(' + ')} (weights ${JSON.stringify(weight)})` + (skipped.length ? `; not this pass: ${skipped.join(', ')}` : ''))
const leadGaps = gaps.gaps.filter(g => g.owner === 'lead' || g.owner === 'character')
if (leadGaps.length) log(`lead / character gaps (not given to specialists): ${leadGaps.map(g => '#' + g.rank + ' ' + g.what).join('; ')}`)

phase('Fix')
const reports = await parallel(pick.map(k => () =>
  agent(fixBrief(k, gaps), { label: `${k} ${SCREEN} pass ${PASS}`, phase: 'Fix', schema: REPORT })
    .then(r => ({ agent: k, report: r }))))
return { screen: SCREEN, pass: PASS, gaps, reports: reports.filter(Boolean), lead_gaps: leadGaps }
