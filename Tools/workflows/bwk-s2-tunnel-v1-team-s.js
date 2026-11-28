export const meta = {
  name: 'bwk-s2-tunnel-v1-team-s',
  description: 'S2 Tunnel v1 art team, RESUMABLE and CONTINUING: reuses finished reports from args.done, resumes cut roles from args.resume, then review -> refine rounds until the critic gives KEEP at >= 9 or args.max_rounds, then a final review',
  whenToUse: 'Any account, after a cut or to keep the team going: python -I Tools/s2v1_resume_args.py builds Captures/s2v1/RESUME_ARGS.json from the last team run (journal + NOTES + renders); launch this script with args = that JSON. Owner 2026-11-27 21:03 (S2 Tunnel v1 art team) + 21:45 (keep the team going until 100 % usage; resumable on another account).',
  phases: [
    { title: 'Build', detail: 'environment-modeler (new tunnel geometry) + water-fx-artist (water, foam, crowns, bubbles); skipped when args.done has their reports' },
    { title: 'Look', detail: 'materials-artist (premium PBR + bakes) + lighting-artist (emissive-motivated light, depth, grade); skipped when done' },
    { title: 'Review', detail: 'asset-critic renders all cameras and judges vs the ORIGINAL, every round' },
    { title: 'Refine', detail: 'the owners fix the critic findings, every round (max two at once)' },
    { title: 'Final', detail: 'asset-critic final review + honest score after the last refine round' },
  ],
}

const ROOT = 'C:/Users/josia/thanksgiving'
const COMMON = `S2 TUNNEL V1 ART TEAM (owner 2026-11-27 21:03: build a genuinely high-quality replacement of the ENTIRE S2 scenery in Blender, ORIGINAL Google Flow video = authoritative reference, >= 9/10, ACTUAL RENDERS for comparison; stop modifying the old cylinder / thin rings; preserve the Unity game; one heavy operation at a time; no purchases).
FIRST read ${ROOT}/Captures/s2v1/TEAM_BRIEF.md completely (job, workspace + file ownership, module contract, the ONLY render command, measured original layout, budgets, rules) and the project skill bwk-s2-cinematic-look (${ROOT}/.claude/skills/bwk-s2-cinematic-look/SKILL.md). Look at the ORIGINAL yourself with the Read tool: ${ROOT}/Reference/google_flow_pack_1735/Frames/frame_03.00s.png and the Crops named in the brief.
Ready for you (verified by the lead 21:02): ${ROOT}/Tools/Blender/work/s2v1/context.blend = the Unity S2 context in Blender world space (191 objects in collections CTX_*, the 8 game cameras CAM_*; R2 framing overlays Unity's own R2 render; drum normals verified), the shared ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_common.py and the assembly ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_render.py (read both before writing your module). EEVEE renders R2 in ~11 s here.
Render ONLY through the assembly command in the brief, in the FOREGROUND with Bash timeout 600000 (it queues on Tools/heavy_lock.sh behind the other specialist - expected; prepare your next change meanwhile). After every render READ the SHEET_R2.png / SHEET_RIG.png it prints and compare with the original yourself. Log every pass in your NOTES file. Write only your own files. Do not modify the Unity project. Honest results only. OWNER 22:20 (verbatim Captures/agents/_shared/OWNER_BRIEF_2220_s2_priorities.txt, section 'OWNER 22:20 PRIORITIES' of the brief): a VISIBLE 7.5-8/10 for the WHOLE scene first (9/10 ultimately) - biggest visible levers first (rich purple / blue materials, cinematic lighting, premium gold machinery, realistic water, plush mascot read), no endless polishing of minor details while the overall scene is unfinished, preserve the best version (renders/<TAG>/_src/, Captures/s2v1/BEST.json; revert changes that make the whole frame worse), never an inferior version into Unity.
OWNER 22:33 (NEWEST, verbatim Captures/agents/_shared/OWNER_BRIEF_2233_unity_first.txt, brief section 'OWNER 22:33 UNITY FIRST'): his ACTUAL GAME is the Unity version = the MIDDLE image of SHEET_R2. The lead will SELECTIVELY transfer only genuinely superior v1 parts into an isolated Unity test scene and keep whatever Unity already does better (milestone 7.5-8/10 in interactive Unity gameplay). So author everything for transfer to Unity URP on mobile - game meshes with UVs, baked maps, materials as URP Lit / BWK_* values (base colour, metallic, smoothness, emission colour + intensity, maps), lights as Unity light types with colour / intensity / range, post as URP Volume settings - and give a per-part 'Unity mapping' in your report and NOTES. A v1 region counts as progress only where it is visibly closer to the original than Unity current.`

const REPORT = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: 'what you built / changed and what the renders show, <= 180 words, plain language' },
    files: { type: 'array', items: { type: 'string' }, description: 'files you created or changed (absolute paths)' },
    renders: { type: 'array', items: { type: 'string' }, description: 'absolute paths of your best SHEET_R2 / SHEET_RIG / camera renders' },
    tags_or_api: { type: 'string', description: 'what the other roles must know: object tags you used, parameters, emission defaults, Unity mapping' },
    remaining_differences: { type: 'array', items: { type: 'string' }, description: 'biggest visible differences from the ORIGINAL still left, biggest first' },
    honest_score: { type: 'number', description: 'your own honest similarity of your domain to the original, 0-10' },
  },
  required: ['summary', 'files', 'renders', 'tags_or_api', 'remaining_differences', 'honest_score'],
}
const VERDICT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['KEEP', 'REVISE', 'REJECT'] },
    score_v1: { type: 'number', description: 'whole-screen similarity of the v1 render to the ORIGINAL 3.00 s frame (R2), 0-10' },
    score_unity_current: { type: 'number', description: 'the same for the current Unity game render (R2), 0-10' },
    gameplay_views: { type: 'string', description: 'what the gameplay rig renders show (stretching, blur, seams, reflections, path readability)' },
    findings: { type: 'array', items: { type: 'object', properties: {
      severity: { type: 'string', enum: ['MAJOR', 'MINOR'] },
      region: { type: 'string' },
      problem: { type: 'string', description: 'what is wrong vs the original, concretely' },
      fix: { type: 'string', description: 'specific change' },
      owner: { type: 'string', enum: ['modeler', 'materials', 'lighting', 'water'] },
      confidence: { type: 'number' } }, required: ['severity', 'region', 'problem', 'fix', 'owner', 'confidence'] } },
    renders_judged: { type: 'array', items: { type: 'string' } },
    transfer_candidates: { type: 'array', description: 'owner 22:33: v1 parts / regions that are ALREADY visibly closer to the ORIGINAL than the current Unity game (candidates for the isolated Unity test scene) and the Unity regions that must stay because they are better; empty if none', items: { type: 'object', properties: {
      part: { type: 'string', description: 's2v1_part tag(s) or region, e.g. band + band_lip, gold_ring + bulb, drum, star, water material' },
      better_in: { type: 'string', enum: ['v1', 'unity_current'] },
      why: { type: 'string' },
      confidence: { type: 'number' } }, required: ['part', 'better_in', 'why', 'confidence'] } },
    summary: { type: 'string' },
  },
  required: ['verdict', 'score_v1', 'score_unity_current', 'gameplay_views', 'findings', 'renders_judged', 'transfer_candidates', 'summary'],
}

async function specialist(role, prompt, opts) {
  const full = `ROLE: you are the ${role} of this team. Your job description is ${ROOT}/.claude/agents/${role}.md - read it first and follow it.\n${COMMON}\n${prompt}`
  try {
    return await agent(full, { ...opts, agentType: role })
  } catch (e) {
    log(`agentType ${role} not registered in this session (${String(e).slice(0, 80)}) - running it from its role file`)
    return await agent(full, opts)
  }
}
const brief = r => r ? JSON.stringify({ summary: r.summary, files: r.files, renders: r.renders, tags_or_api: r.tags_or_api, remaining: r.remaining_differences, score: r.honest_score }) : '(no report - read the NOTES file and the files on disk)'


const A = (args && typeof args === 'object' && !Array.isArray(args)) ? args : {}
const DONE = A.done || {}
const RES = A.resume || {}
const MAX_ROUNDS = Number(A.max_rounds || 4)
const TARGET = Number(A.target_score || 9)
const EFFORT = A.effort || 'xhigh'
const resumeNote = key => RES[key] ? `\nRESUME (your previous run of this exact task was CUT by an account usage limit - read this first, continue from there, never start over): ${RES[key]}` : ''
const reuse = (v, what) => { log(`reusing finished report: ${what}`); return Promise.resolve(v) }
if (A.lead_note) log(`lead note: ${A.lead_note}`)

const MODEL_TASK = () => `YOUR TASK NOW (time box: ~90 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_env.py with build(ctx) per the contract - the NEW S2 tunnel in TRACK SPACE for the door drum d 40.2 -> 62 m (and, if the vanishing point needs it, a simple matching deeper continuation; otherwise leave the old deeper tunnel visible by keeping REPLACES limited to what you replace).
Passes, each rendered through the assembly (TAG=model_<nn>, SCALE 0.5 for quick passes) and compared with the original:
(1) BLOCKOUT at game scale (drum radius 4.2 around the axis at height 2.3): drum shell 40.2-62 m, the THICK glowing band right inside the door (~42-43 m), the ONE big gold bulb ring (~52-55 m), the smaller second gold ring (~61 m), stars at the measured positions. Match the ring / band screen radii, spacing and the vanishing point of the ORIGINAL in SHEET_R2 before any detail.
(2) DRUM: a high-poly bake source with REAL recessed, bevelled slots (many small dark elongated slots in rows following the curvature, spacing as in the original) tagged drum_hp (hide_render), and the game mesh with clean UVs tagged drum (<= ~40k tris). Geometry Nodes / bmesh as you see fit.
(3) THICK ROUNDED violet band(s): sculpted D / torus profile (procedural-modeling gn_curve_profile.py or a bmesh sweep with a custom profile), deep faces, SEPARATE luminous lip parts tagged band_lip; band body tagged band.
(4) LUXURIOUS GOLD RING: multi-step bevelled profile (thick, polished, layered like the original) tagged gold_ring, sockets tagged bulb_socket, glass bulbs tagged bulb (count / spacing as in the original). The second ring the same family, smaller.
(5) NEON STARS: rounded tubes along a star outline (5 points, rounded corners), tagged star with obj["s2v1_color"] = yellow | cyan | pink, placed at the original's positions on the wall (or near the door frame where the original has them).
(6) finish: bevel / weighted normals (hard-surface bevel_stack.py), tri counts per part.
Give every part a flat placeholder colour by tag (the materials-artist owns the real materials; the lighting-artist owns the light). Write Captures/s2v1/NOTES_modeling.md after every pass. Your partner working at the same time is the water-fx-artist (water / foam / crowns / bubbles).`
const WATER_TASK = () => `YOUR TASK NOW (time box: ~60 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_water.py with apply(ctx) per the contract, working on the context collections (already in world space):
(1) CTX_water: the slide water - deep blue-turquoise, glossy, with transparent depth and SOFT, WIDE, low-contrast light bands along the flow (no thin white scratch lines; inspect the water mesh UVs / geometry to align a procedural flow pattern), like water_splashes_03s / water_rails_00s.
(2) CTX_slide: the glossy pink / rainbow rails like the original.
(3) CTX_foam: soft white rounded soap-foam banks (soft / subsurface look, not plastic).
(4) splash crowns (find the CrownL / CrownR objects in the context): milky white translucent sheets with rounded tips beside BOTH feet + detached round droplets (geometry-nodes scatter or bmesh spheres), never over the mascot body.
(5) CTX_bubbles: iridescent thin-film soap bubbles. CTX_pickups (coins / gems): polished gold coin material. CTX_mascot: if it renders untextured, give it a neutral soft rose-pink plush placeholder material + purple hat so the frame reads (the character team owns the real mascot - do not model it).
Render through the assembly after each pass (TAG=water_<nn>, SCALE 0.5 quick) - the modeler's s2v1_env.py may be missing or half-done at first, that is fine - and compare the LOWER HALF of SHEET_R2 and SHEET_RIG with the original. Write Captures/s2v1/NOTES_water.md after every pass. Your partner working at the same time is the environment-modeler.`
const MAT_TASK = (modelR, waterR) => `YOUR TASK NOW (time box: ~60 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_materials.py with apply(ctx): premium materials for the modeler's tagged parts via C.parts(ctx, tag) - drum (polished blue-violet metal ~#634F9B, metallic, roughness ~0.25-0.35, dark recessed slots ~#3A2F51; bake normal / AO / curvature from drum_hp into the drum game mesh with texture-workflow bake_maps.py into Tools/Blender/work/s2v1/bakes/ - 2048 px, modest samples, this is an Intel N150 laptop), band (rich violet lacquer with coat), band_lip (luminous lavender-pink emissive, sensible default strength), gold_ring (luxurious polished gold ~#C6934F, roughness ~0.15-0.25, coat), bulb_socket, bulb (warm glass ~#F3D882 emissive), star (neon tube by obj["s2v1_color"]: yellow ~#EFD66F, cyan ~#59CADC, pink ~#E172B6), and better gold / metal for the door hatch and machinery in CTX_machinery (by object / material name) if it helps the whole frame. Never paint reference pixels into textures.
MODELER'S REPORT: ${brief(modelR)}
WATER ARTIST'S REPORT (do not touch water): ${brief(waterR)}
Render through the assembly after each pass (TAG=mat_<nn>), compare region by region with the original, write Captures/s2v1/NOTES_materials.md, include the Unity mapping (URP Lit / BWK shaders, which maps) in your report. Your partner at the same time is the lighting-artist (light, emission strengths, world, grade).`
const LIGHT_TASK = (modelR, waterR) => `YOUR TASK NOW (time box: ~60 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_lighting.py with apply(ctx): EEVEE for iteration (raytraced reflections if they help the polished metal; 32-64 samples for review renders), view transform Standard or Khronos PBR Neutral (Unity parity; justify anything else), a very dark violet world, EMISSIVE-MOTIVATED light - warm light at the gold bulb ring(s), lavender-pink at the band lips, coloured light at the stars, a small cool core accent deep in the tunnel - polished metal reflecting them, deep violet shade between, atmospheric depth that keeps the core DARK and saturated (targets in bwk-s2-cinematic-look / Tools/s2_look_metrics.py: r 25-80 px L* 38-45 #68479D, glowing mid rings r 120-330), compositor Glare bloom on the emitters only (threshold ~0.9), mild colour balance. No generic three-point rig, no white fog, no brightened core.
MODELER'S REPORT (geometry + tags): ${brief(modelR)}
WATER ARTIST'S REPORT: ${brief(waterR)}
Render through the assembly after each pass (TAG=light_<nn>, SCALE 0.5 quick / 1.0 review), measure the R2 render with Tools/s2_look_metrics.py (the assembly writes metrics_R2.txt), write Captures/s2v1/NOTES_lighting.md with the Unity mapping (URP Bloom threshold / intensity, light types / intensities, probes, fog) for every decision. Your partner at the same time is the materials-artist (surfaces, emission colours).`

const CRITIC_TASK = tag => `ROLE: you are the asset-critic of this team. Your job description is ${ROOT}/.claude/agents/asset-critic.md - read it first and follow it; judge ONLY images and numbers.
${COMMON}
YOUR TASK NOW: render the full review set yourself through the assembly: TAG=${tag} CAMERAS=R2_16x9,RIG_d33.5_9x16,RIG_d38.5_9x16,RIG_d41.0_9x16,RIG_d44.0_9x16,RIG_d47.0_9x16 SCALE=1.0 bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_render.py s2v1_${tag} (foreground, Bash timeout 600000). Then Read Captures/s2v1/renders/${tag}/SHEET_R2.png (ORIGINAL | Unity current | v1), SHEET_RIG.png and the single renders at full size, the ORIGINAL frame and the crops, and metrics_R2.txt. Judge the WHOLE screen and every region (tunnel structure / proportions, drum metal + slots, bands, gold rings + bulbs, stars, core / depth, door + machinery, water / foam / crowns / bubbles, colour + light) and the gameplay views (stretching, blur, seams, reflections, path readability, nothing hiding the mascot). Give each finding to the role that owns the fix (modeler, materials, lighting, water). Honest scores - the owner rejects inflated scores. Owner 22:33: his actual game is the Unity version (middle image) - in transfer_candidates name, region by region, which v1 parts are ALREADY visibly closer to the original than the current Unity game (candidates for the lead's isolated Unity test scene) and which Unity regions are better and must stay.`


async function critic(tag, extra, phaseName, res) {
  const p = CRITIC_TASK(tag) + (extra || '') + (res || '')
  try { return await agent(p, { label: `asset-critic: ${tag}`, phase: phaseName, schema: VERDICT, effort: EFFORT, agentType: 'asset-critic' }) }
  catch (e) { return await agent(p, { label: `asset-critic: ${tag}`, phase: phaseName, schema: VERDICT, effort: EFFORT }) }
}

phase('Build')
const build = await parallel([
  () => DONE.modeler ? reuse(DONE.modeler, 'environment-modeler (Build)') : specialist('environment-modeler', MODEL_TASK() + resumeNote('environment-modeler'),
    { label: 'environment-modeler: new S2 tunnel', phase: 'Build', schema: REPORT, effort: EFFORT }),
  () => DONE.water ? reuse(DONE.water, 'water-fx-artist (Build)') : specialist('water-fx-artist', WATER_TASK() + resumeNote('water-fx-artist'),
    { label: 'water-fx-artist: water + FX', phase: 'Build', schema: REPORT, effort: EFFORT }),
])
const modelR = build[0], waterR = build[1]
log(`Build: modeler ${modelR ? modelR.honest_score : 'no report'} / water ${waterR ? waterR.honest_score : 'no report'}`)
if (!modelR && !waterR) {
  log('Build returned no report at all (cut by a usage limit?) - stopping; resume with Tools/s2v1_resume_args.py')
  return { stopped: 'build', build: { modeler: modelR, water: waterR } }
}

phase('Look')
const look = await parallel([
  () => DONE.materials ? reuse(DONE.materials, 'materials-artist (Look)') : specialist('materials-artist', MAT_TASK(modelR, waterR) + resumeNote('materials-artist'),
    { label: 'materials-artist: premium materials + bakes', phase: 'Look', schema: REPORT, effort: EFFORT }),
  () => DONE.lighting ? reuse(DONE.lighting, 'lighting-artist (Look)') : specialist('lighting-artist', LIGHT_TASK(modelR, waterR) + resumeNote('lighting-artist'),
    { label: 'lighting-artist: light, depth, grade', phase: 'Look', schema: REPORT, effort: EFFORT }),
])
const matR = look[0], lightR = look[1]
log(`Look: materials ${matR ? matR.honest_score : 'no report'} / lighting ${lightR ? lightR.honest_score : 'no report'}`)
if (!matR && !lightR) {
  log('Look returned no report at all (cut by a usage limit?) - stopping; resume with Tools/s2v1_resume_args.py')
  return { stopped: 'look', build: { modeler: modelR, water: waterR }, look: { materials: matR, lighting: lightR } }
}

const ROLE = { modeler: 'environment-modeler', materials: 'materials-artist', lighting: 'lighting-artist', water: 'water-fx-artist' }
const PREV = { modeler: modelR, materials: matR, lighting: lightR, water: waterR }
const REVIEWS = DONE.reviews || {}
const REFINES = DONE.refines || {}
const FIX_TASK = (round, owner, rv, dir) => {
  const mine = rv.findings.filter(f => f.owner === owner && f.confidence >= 60)
  return `YOUR TASK NOW (refinement round ${round}, time box ~45 minutes of work, then report): the independent asset-critic reviewed the team's full renders (${dir}/) and scored v1 ${rv.score_v1}/10 vs the current Unity game ${rv.score_unity_current}/10. Fix YOUR findings, biggest first, each re-rendered through the assembly (TAG=r${round}fix_${owner}_<nn>) and checked against the original:
${mine.map((f, i) => `${i + 1}. [${f.severity}, ${f.confidence}] ${f.region}: ${f.problem} -> FIX: ${f.fix}`).join('\n')}
Critic summary: ${rv.summary}
Your previous report: ${brief(PREV[owner])}
Other roles are fixing their own findings at the same time - touch only your files.`
}

const history = []
let last = null, lastDir = null, stopped = null, round = 1
for (round = 1; round <= MAX_ROUNDS; round++) {
  phase('Review')
  const tag = `review${round}`
  let rv = REVIEWS[String(round)] || null
  if (rv) log(`reusing finished ${tag}: ${rv.verdict} v1 ${rv.score_v1}`)
  else rv = await critic(tag, lastDir ? `\nCOMPARE also with the previous review renders (${lastDir}/) - say what improved or regressed since then.` : '', 'Review', resumeNote(`asset-critic#${tag}`))
  if (!rv) { log(`${tag}: no verdict (agent failed or was cut) - stopping the rounds; resume with Tools/s2v1_resume_args.py`); stopped = tag; break }
  last = rv
  lastDir = rv._dir || `${ROOT}/Captures/s2v1/renders/${tag}`
  history.push({ round, tag, verdict: rv.verdict, score_v1: rv.score_v1, score_unity_current: rv.score_unity_current, findings: rv.findings.length })
  log(`Review ${round}: ${rv.verdict} v1 ${rv.score_v1} vs Unity ${rv.score_unity_current}, ${rv.findings.length} findings`)
  if (rv.verdict === 'KEEP' && rv.score_v1 >= TARGET) { log(`target reached: KEEP at ${rv.score_v1} >= ${TARGET}`); break }
  phase('Refine')
  const owners = [...new Set(rv.findings.filter(f => f.confidence >= 60).map(f => f.owner))].filter(o => ROLE[o])
  const doneR = REFINES[String(round)] || {}
  const res = await pipeline(owners, owner => doneR[owner] ? reuse(doneR[owner], `refine ${round} ${owner}`)
    : specialist(ROLE[owner], FIX_TASK(round, owner, rv, lastDir) + resumeNote(`${ROLE[owner]}#refine${round}`),
      { label: `${ROLE[owner]}: fix review${round}`, phase: 'Refine', schema: REPORT, effort: EFFORT }))
  owners.forEach((o, i) => { if (res[i]) PREV[o] = res[i] })
  log(`Refine ${round}: ${owners.map((o, i) => o + (res[i] ? ' ' + res[i].honest_score : ' no report')).join(', ') || 'nothing to refine'}`)
  if (owners.length && res.every(r => !r)) { log(`Refine ${round} returned no report at all (cut?) - stopping`); stopped = `refine${round}`; break }
}

let final = last
if (!stopped && !(last && last.verdict === 'KEEP' && last.score_v1 >= TARGET)) {
  phase('Final')
  const tag = `review${round}`
  final = REVIEWS[String(round)] || await critic(tag, lastDir ? `\nFINAL REVIEW of this run. COMPARE also with ${lastDir}/ - say what improved or regressed.` : '', 'Final', resumeNote(`asset-critic#${tag}`))
  if (final) history.push({ round, tag, verdict: final.verdict, score_v1: final.score_v1, score_unity_current: final.score_unity_current, findings: final.findings.length })
  log(`Final: ${final ? final.verdict + ' v1 ' + final.score_v1 + ' vs Unity ' + final.score_unity_current : 'no verdict'}`)
}
return { stopped, history, final, reports: PREV }
