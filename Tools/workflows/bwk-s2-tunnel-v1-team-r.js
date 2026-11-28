export const meta = {
  name: 'bwk-s2-tunnel-v1-team-r',
  description: 'RELAUNCH (lead c7e89796) of the S2 Tunnel v1 art team cut at 21:19: modeler + water resume their Build work, then materials + lighting, independent critic review, refine, final score',
  whenToUse: 'Relaunch 2026-11-27 ~21:36 of run wf_0b48fae2-372 (session 8d2d815d, both Build agents cut at 21:19 by the old account 5-hour limit, 0 reports). Owner 2026-11-27 21:03: build a genuinely high-quality replacement S2 environment in Blender (isolated s2v1 workspace) with a coordinated specialist team. Foundations by lead 8d2d815d: Captures/s2v1/TEAM_BRIEF.md.',
  phases: [
    { title: 'Build', detail: 'environment-modeler (new tunnel geometry) + water-fx-artist (water, foam, crowns, bubbles) in parallel' },
    { title: 'Look', detail: 'materials-artist (premium PBR + bakes) + lighting-artist (emissive-motivated light, depth, grade) in parallel' },
    { title: 'Review', detail: 'asset-critic renders all cameras and judges vs the ORIGINAL' },
    { title: 'Refine', detail: 'the owners fix the critic findings (max two at once)' },
    { title: 'Final', detail: 'asset-critic final renders + honest score' },
  ],
}

const ROOT = 'C:/Users/josia/thanksgiving'
const COMMON = `S2 TUNNEL V1 ART TEAM (owner 2026-11-27 21:03: build a genuinely high-quality replacement of the ENTIRE S2 scenery in Blender, ORIGINAL Google Flow video = authoritative reference, >= 9/10, ACTUAL RENDERS for comparison; stop modifying the old cylinder / thin rings; preserve the Unity game; one heavy operation at a time; no purchases).
FIRST read ${ROOT}/Captures/s2v1/TEAM_BRIEF.md completely (job, workspace + file ownership, module contract, the ONLY render command, measured original layout, budgets, rules) and the project skill bwk-s2-cinematic-look (${ROOT}/.claude/skills/bwk-s2-cinematic-look/SKILL.md). Look at the ORIGINAL yourself with the Read tool: ${ROOT}/Reference/google_flow_pack_1735/Frames/frame_03.00s.png and the Crops named in the brief.
Ready for you (verified by the lead 21:02): ${ROOT}/Tools/Blender/work/s2v1/context.blend = the Unity S2 context in Blender world space (191 objects in collections CTX_*, the 8 game cameras CAM_*; R2 framing overlays Unity's own R2 render; drum normals verified), the shared ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_common.py and the assembly ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_render.py (read both before writing your module). EEVEE renders R2 in ~11 s here.
Render ONLY through the assembly command in the brief, in the FOREGROUND with Bash timeout 600000 (it queues on Tools/heavy_lock.sh behind the other specialist - expected; prepare your next change meanwhile). After every render READ the SHEET_R2.png / SHEET_RIG.png it prints and compare with the original yourself. Log every pass in your NOTES file. Write only your own files. Do not modify the Unity project. Honest results only.`

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
    summary: { type: 'string' },
  },
  required: ['verdict', 'score_v1', 'score_unity_current', 'gameplay_views', 'findings', 'renders_judged', 'summary'],
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

phase('Build')
const build = await parallel([
  () => specialist('environment-modeler', `YOUR TASK NOW (time box: ~90 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_env.py with build(ctx) per the contract - the NEW S2 tunnel in TRACK SPACE for the door drum d 40.2 -> 62 m (and, if the vanishing point needs it, a simple matching deeper continuation; otherwise leave the old deeper tunnel visible by keeping REPLACES limited to what you replace).
Passes, each rendered through the assembly (TAG=model_<nn>, SCALE 0.5 for quick passes) and compared with the original:
(1) BLOCKOUT at game scale (drum radius 4.2 around the axis at height 2.3): drum shell 40.2-62 m, the THICK glowing band right inside the door (~42-43 m), the ONE big gold bulb ring (~52-55 m), the smaller second gold ring (~61 m), stars at the measured positions. Match the ring / band screen radii, spacing and the vanishing point of the ORIGINAL in SHEET_R2 before any detail.
(2) DRUM: a high-poly bake source with REAL recessed, bevelled slots (many small dark elongated slots in rows following the curvature, spacing as in the original) tagged drum_hp (hide_render), and the game mesh with clean UVs tagged drum (<= ~40k tris). Geometry Nodes / bmesh as you see fit.
(3) THICK ROUNDED violet band(s): sculpted D / torus profile (procedural-modeling gn_curve_profile.py or a bmesh sweep with a custom profile), deep faces, SEPARATE luminous lip parts tagged band_lip; band body tagged band.
(4) LUXURIOUS GOLD RING: multi-step bevelled profile (thick, polished, layered like the original) tagged gold_ring, sockets tagged bulb_socket, glass bulbs tagged bulb (count / spacing as in the original). The second ring the same family, smaller.
(5) NEON STARS: rounded tubes along a star outline (5 points, rounded corners), tagged star with obj["s2v1_color"] = yellow | cyan | pink, placed at the original's positions on the wall (or near the door frame where the original has them).
(6) finish: bevel / weighted normals (hard-surface bevel_stack.py), tri counts per part.
Give every part a flat placeholder colour by tag (the materials-artist owns the real materials; the lighting-artist owns the light). Write Captures/s2v1/NOTES_modeling.md after every pass. Your partner working at the same time is the water-fx-artist (water / foam / crowns / bubbles).
RESUME (lead c7e89796): your previous run of this exact task was CUT at 21:19 by the old account's usage limit BEFORE its first render. On disk: ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_env.py (593 lines, complete first version written 21:18-21:19: drum game meshes S2V1_drum_A 40.2-62 m / S2V1_drum_B 62-80 m, perforated drum_hp bake sources per zone (SLOT_BIG ovals near the door, SLOT_DASH rows deeper), bands A 41.05 / B 43.70 / C 72.80 / D 79.55, gold rings G1 52.5 m (28 bulbs) / G2 74.4 m (24 bulbs), 7 stars, trim_old() deletes the old tunnel faces in d 40.2-80 in memory, a render_pre handler showing drum_hp until a drum bake exists). Your star solve (Captures/s2v1/env/solve_stars.py): Y_UL d 41.9 / -52 deg, C_L 49.2 / -49, C_R 44.9 / 71, P_s 67.8 / 116 fitted well; Y_UR, P_R, Y_s did NOT fit the drum wall (18-56 px error - they sit on / near the door frame or deeper; check them against the original). NOTES_modeling.md does not exist yet - create it. The lead rendered your file once, unchanged: ${ROOT}/Captures/s2v1/renders/lead_env_01/ (SHEET_R2.png, SHEET_RIG.png, log ${ROOT}/Logs/blender_s2v1_lead_env_01.log). RESULT: build() CRASHED before creating anything (the assembly skipped the module, so lead_env_01 = the old context only): 'ValueError: all input arrays must have the same shape' at s2v1_env.py line 104 cyl() <- line 222 drum_game() <- line 559 build() - cyl() np.stack()s an array theta with a SCALAR d; broadcast first (e.g. th, dd = np.broadcast_arrays(theta, d)) and check the other helpers for the same pattern. The file was never executed, so expect more first-run errors: test build() quickly in a headless Blender run of your own before each full assembly render (one assembly render of 4 cameras at SCALE 0.5 takes ~4.5 min here, mostly opening the 117 MB context.blend + EEVEE shader compile). Look at lead_env_01 only for the log; then fix, then continue from pass 1 (correct the blockout against the original) through the later passes. Do not start over.`,
    { label: 'environment-modeler: new S2 tunnel', phase: 'Build', schema: REPORT, effort: 'xhigh' }),
  () => specialist('water-fx-artist', `YOUR TASK NOW (time box: ~60 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_water.py with apply(ctx) per the contract, working on the context collections (already in world space):
(1) CTX_water: the slide water - deep blue-turquoise, glossy, with transparent depth and SOFT, WIDE, low-contrast light bands along the flow (no thin white scratch lines; inspect the water mesh UVs / geometry to align a procedural flow pattern), like water_splashes_03s / water_rails_00s.
(2) CTX_slide: the glossy pink / rainbow rails like the original.
(3) CTX_foam: soft white rounded soap-foam banks (soft / subsurface look, not plastic).
(4) splash crowns (find the CrownL / CrownR objects in the context): milky white translucent sheets with rounded tips beside BOTH feet + detached round droplets (geometry-nodes scatter or bmesh spheres), never over the mascot body.
(5) CTX_bubbles: iridescent thin-film soap bubbles. CTX_pickups (coins / gems): polished gold coin material. CTX_mascot: if it renders untextured, give it a neutral soft rose-pink plush placeholder material + purple hat so the frame reads (the character team owns the real mascot - do not model it).
Render through the assembly after each pass (TAG=water_<nn>, SCALE 0.5 quick) - the modeler's s2v1_env.py may be missing or half-done at first, that is fine - and compare the LOWER HALF of SHEET_R2 and SHEET_RIG with the original. Write Captures/s2v1/NOTES_water.md after every pass. Your partner working at the same time is the environment-modeler.
RESUME (lead c7e89796): your previous run of this exact task was CUT at 21:19 by the old account's usage limit right after its pass-02 render. On disk: ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_water.py (680 lines: pass 01 = full WFX_* material set + droplets; pass 02 = crown relax / subdivision, fewer and smaller droplets, saturated chevrons, preview_light_if_no_lighting() while s2v1_lighting.py is missing) and ${ROOT}/Captures/s2v1/NOTES_water.md (pass 01 logged with its 'next' list; pass 02 NOT logged yet). Your pass-02 render ${ROOT}/Captures/s2v1/renders/water_02/ was never looked at: READ its SHEET_R2.png + SHEET_RIG.png first and log pass 02. The lead's own look at water_02 (v1 lower half vs the ORIGINAL): pale and low-contrast - the water reads light sky-blue instead of the original's deep saturated blue-turquoise with glossy highlights, the rails pale salmon instead of hot pink / magenta with bright highlight stripes, the crowns stiff white plates instead of milky translucent liquid with rounded tips, the coins brown-orange instead of polished gold, the chevron pale instead of glowing cyan; part of that is the missing lighting module - judge your materials honestly under your preview light. Continue from there. Do not start over.`,
    { label: 'water-fx-artist: water + FX', phase: 'Build', schema: REPORT, effort: 'xhigh' }),
])
const modelR = build[0], waterR = build[1]
log(`Build done: modeler ${modelR ? modelR.honest_score : 'no report'} / water ${waterR ? waterR.honest_score : 'no report'}`)

phase('Look')
const look = await parallel([
  () => specialist('materials-artist', `YOUR TASK NOW (time box: ~60 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_materials.py with apply(ctx): premium materials for the modeler's tagged parts via C.parts(ctx, tag) - drum (polished blue-violet metal ~#634F9B, metallic, roughness ~0.25-0.35, dark recessed slots ~#3A2F51; bake normal / AO / curvature from drum_hp into the drum game mesh with texture-workflow bake_maps.py into Tools/Blender/work/s2v1/bakes/ - 2048 px, modest samples, this is an Intel N150 laptop), band (rich violet lacquer with coat), band_lip (luminous lavender-pink emissive, sensible default strength), gold_ring (luxurious polished gold ~#C6934F, roughness ~0.15-0.25, coat), bulb_socket, bulb (warm glass ~#F3D882 emissive), star (neon tube by obj["s2v1_color"]: yellow ~#EFD66F, cyan ~#59CADC, pink ~#E172B6), and better gold / metal for the door hatch and machinery in CTX_machinery (by object / material name) if it helps the whole frame. Never paint reference pixels into textures.
MODELER'S REPORT: ${brief(modelR)}
WATER ARTIST'S REPORT (do not touch water): ${brief(waterR)}
Render through the assembly after each pass (TAG=mat_<nn>), compare region by region with the original, write Captures/s2v1/NOTES_materials.md, include the Unity mapping (URP Lit / BWK shaders, which maps) in your report. Your partner at the same time is the lighting-artist (light, emission strengths, world, grade).`,
    { label: 'materials-artist: premium materials + bakes', phase: 'Look', schema: REPORT, effort: 'xhigh' }),
  () => specialist('lighting-artist', `YOUR TASK NOW (time box: ~60 minutes of work, then report): create ${ROOT}/Tools/Blender/scripts/s2v1/s2v1_lighting.py with apply(ctx): EEVEE for iteration (raytraced reflections if they help the polished metal; 32-64 samples for review renders), view transform Standard or Khronos PBR Neutral (Unity parity; justify anything else), a very dark violet world, EMISSIVE-MOTIVATED light - warm light at the gold bulb ring(s), lavender-pink at the band lips, coloured light at the stars, a small cool core accent deep in the tunnel - polished metal reflecting them, deep violet shade between, atmospheric depth that keeps the core DARK and saturated (targets in bwk-s2-cinematic-look / Tools/s2_look_metrics.py: r 25-80 px L* 38-45 #68479D, glowing mid rings r 120-330), compositor Glare bloom on the emitters only (threshold ~0.9), mild colour balance. No generic three-point rig, no white fog, no brightened core.
MODELER'S REPORT (geometry + tags): ${brief(modelR)}
WATER ARTIST'S REPORT: ${brief(waterR)}
Render through the assembly after each pass (TAG=light_<nn>, SCALE 0.5 quick / 1.0 review), measure the R2 render with Tools/s2_look_metrics.py (the assembly writes metrics_R2.txt), write Captures/s2v1/NOTES_lighting.md with the Unity mapping (URP Bloom threshold / intensity, light types / intensities, probes, fog) for every decision. Your partner at the same time is the materials-artist (surfaces, emission colours).`,
    { label: 'lighting-artist: light, depth, grade', phase: 'Look', schema: REPORT, effort: 'xhigh' }),
])
const matR = look[0], lightR = look[1]
log(`Look done: materials ${matR ? matR.honest_score : 'no report'} / lighting ${lightR ? lightR.honest_score : 'no report'}`)

const CRITIC_TASK = tag => `ROLE: you are the asset-critic of this team. Your job description is ${ROOT}/.claude/agents/asset-critic.md - read it first and follow it; judge ONLY images and numbers.
${COMMON}
YOUR TASK NOW: render the full review set yourself through the assembly: TAG=${tag} CAMERAS=R2_16x9,RIG_d33.5_9x16,RIG_d38.5_9x16,RIG_d41.0_9x16,RIG_d44.0_9x16,RIG_d47.0_9x16 SCALE=1.0 bash Tools/blender_run.sh Tools/Blender/scripts/s2v1/s2v1_render.py s2v1_${tag} (foreground, Bash timeout 600000). Then Read Captures/s2v1/renders/${tag}/SHEET_R2.png (ORIGINAL | Unity current | v1), SHEET_RIG.png and the single renders at full size, the ORIGINAL frame and the crops, and metrics_R2.txt. Judge the WHOLE screen and every region (tunnel structure / proportions, drum metal + slots, bands, gold rings + bulbs, stars, core / depth, door + machinery, water / foam / crowns / bubbles, colour + light) and the gameplay views (stretching, blur, seams, reflections, path readability, nothing hiding the mascot). Give each finding to the role that owns the fix (modeler, materials, lighting, water). Honest scores - the owner rejects inflated scores.`

async function critic(tag, extra) {
  try { return await agent(CRITIC_TASK(tag) + (extra || ''), { label: `asset-critic: ${tag}`, phase: tag.startsWith('final') ? 'Final' : 'Review', schema: VERDICT, effort: 'xhigh', agentType: 'asset-critic' }) }
  catch (e) { return await agent(CRITIC_TASK(tag) + (extra || ''), { label: `asset-critic: ${tag}`, phase: tag.startsWith('final') ? 'Final' : 'Review', schema: VERDICT, effort: 'xhigh' }) }
}

phase('Review')
const review = await critic('review1')
log(`Review 1: ${review ? review.verdict + ' v1 ' + review.score_v1 + ' vs Unity ' + review.score_unity_current + ', ' + review.findings.length + ' findings' : 'no verdict'}`)

phase('Refine')
const ROLE = { modeler: 'environment-modeler', materials: 'materials-artist', lighting: 'lighting-artist', water: 'water-fx-artist' }
const PREV = { modeler: modelR, materials: matR, lighting: lightR, water: waterR }
const owners = review ? [...new Set(review.findings.filter(f => f.confidence >= 60).map(f => f.owner))] : []
const refine = await pipeline(owners, owner => {
  const mine = review.findings.filter(f => f.owner === owner && f.confidence >= 60)
  return specialist(ROLE[owner], `YOUR TASK NOW (refinement, time box ~45 minutes of work, then report): the independent asset-critic reviewed the team's full renders (Captures/s2v1/renders/review1/) and scored v1 ${review.score_v1}/10 vs the current Unity game ${review.score_unity_current}/10. Fix YOUR findings, biggest first, each re-rendered through the assembly (TAG=fix_${owner}_<nn>) and checked against the original:
${mine.map((f, i) => `${i + 1}. [${f.severity}, ${f.confidence}] ${f.region}: ${f.problem} -> FIX: ${f.fix}`).join('\n')}
Critic summary: ${review.summary}
Your previous report: ${brief(PREV[owner])}
Other roles are fixing their own findings at the same time - touch only your files.`,
    { label: `${ROLE[owner]}: fix review1`, phase: 'Refine', schema: REPORT, effort: 'xhigh' })
})
log(`Refine done: ${owners.join(', ') || 'nothing to refine'}`)

phase('Final')
const final = await critic('final1', `\nCOMPARE also with the review1 renders (Captures/s2v1/renders/review1/) - say what improved or regressed since review1.`)
log(`Final: ${final ? final.verdict + ' v1 ' + final.score_v1 + ' vs Unity ' + final.score_unity_current : 'no verdict'}`)
return { build: { modeler: modelR, water: waterR }, look: { materials: matR, lighting: lightR }, review1: review, refine, final }
