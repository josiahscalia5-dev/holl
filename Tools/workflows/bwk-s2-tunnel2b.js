export const meta = {
  name: 'bwk-s2-tunnel2b',
  description: 'S2 tunnel step 2b (lead lane): planner + skeptic order single-lever changes from the measured maps and the ORIGINAL video crops, then each lever is applied alone, previewed, compared side by side and kept or reverted by an independent judge',
  whenToUse: 'Lead 6d001969 2026-11-27 17:58 (owner 17:35 sections 5-6 + 17:45 authoritative Google Flow pack): tunnel 2b redo, one change at a time with a side-by-side. args {max_levers?: 4, before?: "Captures/stills_s2p10g"}',
  phases: [
    { title: 'Plan', detail: 'planner orders single-lever changes; a skeptic refutes the weak ones' },
    { title: 'Levers', detail: 'one lever at a time: apply -> no-save preview -> side-by-side -> independent judge -> keep or revert' },
  ],
}

const ROOT = 'C:/Users/josia/thanksgiving'
const A = (typeof args === 'object' && args) ? args : {}
const MAX_LEVERS = A.max_levers || 4
const PY = '"/c/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe"'

const REFS = `AUTHORITATIVE ORIGINAL (owner 17:45, the Google Flow video pixels): ${ROOT}/Reference/google_flow_pack_1735/Frames/frame_03.00s.png (THE S2 frame, 1280x720 = Reference/frames4k_720/f_03.00s.png), Crops/violet_wall_stars_03s.png, Crops/gold_violet_rings_03s.png, Crops/hatch_and_tunnel_00s.png, Frames/frame_00.00s.png; 4K: ${ROOT}/Reference/frames4k/f_03.00s.png. SECONDARY (generated ChatGPT sheets, only for construction the video never shows; the ORIGINAL wins wherever they differ): ${ROOT}/Reference/owner_sheets_1735/crops/R3_interior_perforation.png, R3_ring_sequence_depth.png, R3_tunnel_turnaround.png, R3_material_spheres.png, R2_wall_material.png, R2_bands_gold_ring.png.`
const OWNER = `OWNER 17:35 master directive, verbatim ${ROOT}/Captures/agents/_shared/OWNER_BRIEF_1735_master_visual_directive.txt - read sections 3, 5 (A tunnel structure, B blue-violet metallic walls, C drum perforations, D gold rings, E glowing violet bands, F distant core) and 6 (neon stars) IN FULL. Key lines: walls = deep cobalt-blue + rich violet polished metal with reflections of the gold lights and pink / violet bands, never uniformly pale lavender / flat purple / grey; the R2 right-wall brightness must move DOWN toward ~0.45 (same measurement), never brighter - but do not chase numbers over artistic quality; perforations = many SMALL dark elongated recessed slots following the curvature with consistent spacing; gold rings thick polished bevelled with integrated warm bulbs, number / spacing as in the ORIGINAL (no extra rings); violet bands = thick luminous rounded metallic structures with strong but controlled luminous edges and rich violet interiors (never fairy-light strings); far core = controlled cool blue-white glow that pulls the eye forward without a white wall; stars = rounded tubular neon objects (decor only). Preserve the gameplay path, camera, collisions.`
const STATE = `CURRENT STATE: newest build lead_s2p10g (Captures/stills_s2p10g/R2_rear_S2_like_3s_16x9.png = the fixed comparison camera, hero_mouth_9x16.png = the PORTRAIT gameplay rig at the same spot, bg/ = mascot hidden; side-by-sides Captures/compare/build_s2p10g/). The cut 2b analysis (lead 15a68124, 17:05) = ${ROOT}/Captures/lead/s2_step2b_redo/maps_1705.json: 'wall' (how M_DrumWall / BWK_DrumWall shades the S2 drum + 11 levers), 'bands' (doors, rings, SM_LedRim_s2 violet bands, ring lights, far end + 11 levers), 'meas' (13 measured regions, reference vs ours) + images in Captures/lead/s2_step2b_redo/{wall,bands,measure}/. ON DISK, UNREVIEWED BY A JUDGE: v10 = 4 SetColor lines at the end of the M_DrumWall block in Assets/BubbleWashKingdom/Scripts/Editor/MaterialLibrary.Environment.cs (door ramp stops under the bloom knee). LEAD MEASURED v10 (Tools/wall_luma.py, preview Captures/lead/s2_2b/v10/): R2 right wall (950,0,1280,360) .490 -> .487 (reference .442), RW4 (1090,300,1160,345) .503 -> .507 (reference .322), tunnel core (520,60,760,260) .567 -> .550 (reference .492), left wall .528 -> .532 (reference .515) = v10 barely touches the right wall, so the bright right-wall pixels at R2 (camera ~30.8 m, before the door at 40 m) are mostly NOT the door-ramp drum (structure-matched: 'our smooth light-lavender panel inside the white rim line' - door hatch SM_DoorHatch_s2 / M_HatchViolet_s2, the mouth drum, M_DrumRim or the hall wall: IDENTIFY it from the scene code, SceneBuilder.Hall.cs / SceneBuilder.Environment.cs, before choosing a lever). Measure with: ${PY} -I Tools/wall_luma.py Reference/frames4k_720/f_03.00s.png <before R2 png> <after R2 png>; Tools/img_stats.py / Tools/img_crop.py for other boxes.`
const FILES = `LEAD FILES you may edit (one lever = the smallest change in ONE place): BWK_DrumWall.shader, BWK_Gold.shader, BWK_Emissive.shader, MaterialLibrary.Environment.cs, MaterialLibrary.Assets.cs, MaterialLibrary.Lighting.cs, SceneBuilder.Environment.cs, SceneBuilder.Lighting.cs, SceneBuilder.Hall.cs, Tools/Blender/scripts/build_s2_rims_p10.py, build_s2_rings_p9.py. NEVER touch the character files (BWK_Fur, BWK_Character, MaterialLibrary.Character.cs, mascot Blender scripts / FBX) or the water files (BWK_Water, BWK_Soft, BWK_Glass, MaterialLibrary.WaterFX.cs, SceneBuilder.WaterFX.cs, TextureGenerator.cs, SplashFX.cs, build_props.py, build_fx_*.py): the character + water specialists of pass 10h edit them right now. No safe_build, no scene save, no git, never kill Unity / Blender, every Unity / Blender command through Tools/unity_run.sh / Tools/blender_run.sh in the FOREGROUND (Bash timeout 600000 - they queue on Tools/heavy_lock.sh behind the specialists' runs, that is expected). bash Tools/cs_check.sh after every C# edit; never leave code that does not compile. Images with reference pixels only under Captures/ (the repo is PUBLIC). No AI generators, no downloads, no purchases.`

const LEVER = {
  type: 'object',
  properties: {
    name: { type: 'string', description: 'short id, e.g. hatch_panel_darker' },
    target: { type: 'string', enum: ['walls_darker', 'slits_smaller', 'band_faces', 'band_edges_glow', 'gold_rings', 'far_core', 'stars', 'other'] },
    change: { type: 'string', description: 'the ONE concrete change: file + property / line + old value -> new value (or the exact geometry edit)' },
    files: { type: 'array', items: { type: 'string' } },
    preview_flags: { type: 'string', description: 'extra AgentPreviewBatch flags needed (e.g. -bwkEnvHall) or empty' },
    needs_blender: { type: 'boolean' },
    expected: { type: 'string', description: 'what should visibly change in R2 / hero_mouth_9x16 and the measured box -> target values' },
    risk: { type: 'string' },
  },
  required: ['name', 'target', 'change', 'files', 'preview_flags', 'needs_blender', 'expected', 'risk'],
}
const PLAN = {
  type: 'object',
  properties: {
    right_wall_object: { type: 'string', description: 'what object / material actually makes the bright near-right wall pixels at R2 (with file:line evidence)' },
    v10_decision: { type: 'string', enum: ['keep', 'revert'] },
    v10_reason: { type: 'string' },
    levers: { type: 'array', items: LEVER, description: 'ordered, biggest visible gain first, each a single independent change' },
  },
  required: ['right_wall_object', 'v10_decision', 'v10_reason', 'levers'],
}
const APPLIED = {
  type: 'object',
  properties: {
    applied: { type: 'boolean' },
    diff: { type: 'string', description: 'exactly what changed (file, old -> new)' },
    backup_dir: { type: 'string', description: 'folder with the untouched copies of every edited file (for revert)' },
    preview_dir: { type: 'string' },
    sheet_r2: { type: 'string', description: 'ref | before | after triptych of R2 (Tools/triptych.py)' },
    sheet_portrait: { type: 'string', description: 'ref | before | after triptych of hero_9x16 / portrait' },
    measurements: { type: 'string', description: 'wall_luma boxes + any lever-specific box, reference / before / after' },
    landmarks: { type: 'string', description: 'what Tools/landmark_check.py printed (or why not run)' },
    notes: { type: 'string' },
  },
  required: ['applied', 'diff', 'backup_dir', 'preview_dir', 'sheet_r2', 'sheet_portrait', 'measurements', 'landmarks', 'notes'],
}
const VERDICT = {
  type: 'object',
  properties: {
    keep: { type: 'boolean' },
    closer_to_original: { type: 'string', enum: ['clearly', 'slightly', 'no change', 'worse'] },
    regressions: { type: 'array', items: { type: 'string' } },
    score_before: { type: 'number', description: 'tunnel / scenery-only similarity to the ORIGINAL, 0-10' },
    score_after: { type: 'number' },
    reason: { type: 'string' },
    next_hint: { type: 'string', description: 'what the next lever should address, judging only by the images' },
  },
  required: ['keep', 'closer_to_original', 'regressions', 'score_before', 'score_after', 'reason', 'next_hint'],
}

phase('Plan')
const plan0 = await agent(`You are the lead's TUNNEL PLANNER for Bubble Wash Kingdom (Unity 6.3 URP + Blender 5.3) at ${ROOT}. Read-only: change no file.
${REFS}
${OWNER}
${STATE}
${FILES}
TASK: (1) identify with code evidence which object / material forms the bright near-right wall at R2 (box (950,0)-(1280,360) and RW4 (1090,300)-(1160,345)) and the other regions the maps measured; (2) decide whether v10 stays (keep unless it visibly hurts); (3) return an ORDERED list of up to 8 single-lever changes, biggest visible gain toward the ORIGINAL first, each independently testable with ONE no-save preview (AgentPreviewBatch; say which -bwkEnv* flags make placed geometry / material references show) - darker deep cobalt-violet reflective walls, glowing violet BAND EDGES over deep band faces, smaller recessed slits, the cool far core, then (if justified) gold-ring polish or star tubes. Use the maps' measured targets; prefer changes that alter what the camera sees most. Never propose brightening the drum, extra gold rings, fairy-light strings or a global grade.`,
  { label: 'planner 2b', phase: 'Plan', schema: PLAN, effort: 'high' })
if (!plan0 || !plan0.levers || !plan0.levers.length) return { error: 'planner returned no levers', plan: plan0 }
const plan = await agent(`You are the SKEPTIC for the lead's tunnel plan (Bubble Wash Kingdom at ${ROOT}). Read-only.
${REFS}
${OWNER}
${STATE}
PLAN: ${JSON.stringify(plan0)}
Check every claim against the code and the images yourself: is the right-wall object really what the planner says (file:line)? Would each lever visibly move the R2 / portrait frame toward the ORIGINAL (not just a number)? Is each lever ONE independent change in a lead-owned file (${FILES.split('NEVER')[0].trim()})? Drop or fix wrong / weak / risky levers (anything that brightens the drum, adds rings, touches character / water files, or breaks the gameplay corridor), reorder by real visible gain, and return the corrected plan (same schema).`,
  { label: 'skeptic 2b', phase: 'Plan', schema: PLAN, effort: 'high' })
const P = (plan && plan.levers && plan.levers.length) ? plan : plan0
log(`2b plan: ${P.levers.length} levers; right wall = ${P.right_wall_object.slice(0, 120)}; v10 ${P.v10_decision}`)

phase('Levers')
let before = A.before || 'Captures/stills_s2p10g'
let beforeVs = 'Captures/compare/build_s2p10g'
const results = []
if (P.v10_decision === 'revert') {
  const rv = await agent(`Lead tunnel lane, Bubble Wash Kingdom at ${ROOT}. Revert v10: delete exactly the 4 v10 SetColor lines (_DoorRampCeil / _DoorRampMid / _DoorRampHigh / _DoorRampDark with 0.16/0.11/0.74, 0.40/0.24/0.76, 0.62/0.44/0.82, 0.07/0.05/0.30) at the end of the M_DrumWall block in Assets/BubbleWashKingdom/Scripts/Editor/MaterialLibrary.Environment.cs and replace the v10 comment by one line 'v10 reverted (lead tunnel lane): ${P.v10_reason.replace(/[`$]/g, '').slice(0, 200)}'. Back up the file first to Captures/lead/s2_2b/v10_revert_backup/. Run bash Tools/cs_check.sh. Report what you changed.`,
    { label: 'revert v10', phase: 'Levers', effort: 'low' })
  results.push({ lever: 'v10 revert', applied: rv })
}
const n = Math.min(MAX_LEVERS, P.levers.length)
for (let k = 0; k < n; k++) {
  const L = P.levers[k]
  const dir = `Captures/lead/s2_2b/L${k + 1}_${L.name.replace(/[^A-Za-z0-9_]/g, '_')}`
  const r = await agent(`You are the lead's TUNNEL LEVER WORKER (Bubble Wash Kingdom, Unity 6.3 URP + Blender 5.3, ${ROOT}). Apply EXACTLY ONE lever, prove it, report. Do not apply anything else.
LEVER ${k + 1}/${n}: ${JSON.stringify(L)}
${REFS}
${STATE}
${FILES}
STEPS: (1) copy every file you will edit to ${dir}/backup/ (same file names) BEFORE editing; (2) make the change (comment it in the code: 'lead tunnel lane 2b L${k + 1} (owner 17:35 section 5): <what + why>'), bash Tools/cs_check.sh after C# edits; if Blender geometry: bash Tools/blender_run.sh Tools/Blender/scripts/<script>.py (foreground) and check its preview render; (3) preview: bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch lead_2b_L${k + 1} -bwkOut ${dir} ${L.preview_flags || ''} -bwkStills (foreground, Bash timeout 600000; it queues behind other heavy runs); (4) side-by-sides: ${PY} -I Tools/triptych.py ${beforeVs}/R2_vs_reference_16x9.png ${dir}/R2_vs_reference_16x9.png ${dir}/TRIPTYCH_R2.png and the same with hero_vs_reference_9x16.png -> ${dir}/TRIPTYCH_9x16.png (if the BEFORE folder has no *_vs_reference_* files, use its R2 / hero_mouth renders with Tools/labeled_sheet.py); (5) measure: ${PY} -I Tools/wall_luma.py Reference/frames4k_720/f_03.00s.png ${before}/R2_rear_S2_like_3s_16x9.png ${dir}/R2_rear_S2_like_3s_16x9.png + the lever's own box; (6) ${PY} -I Tools/landmark_check.py ${before} ${dir}/stills (no LOST line may come from your change); (7) append 3-5 lines to Captures/lead/s2_2b/NOTES_2b.md (lever, change, numbers, sheets). Time box 25 minutes. If the change cannot be made safely, set applied=false and explain.`,
    { label: `lever ${k + 1}: ${L.name}`, phase: 'Levers', schema: APPLIED })
  if (!r) { results.push({ lever: L, applied: null }); break }
  if (!r.applied) { results.push({ lever: L, applied: r }); continue }
  const v = await agent(`You are an INDEPENDENT VISUAL JUDGE for the Bubble Wash Kingdom S2 tunnel (one lever was just applied). Never read notes or code; judge only images with the Read tool.
${REFS}
Owner standard: 9/10+ similarity to the ORIGINAL; deep reflective cobalt-violet walls (not pale lavender / flat purple / grey), thick violet bands with luminous edges over deep faces, small recessed slits, gold rings with warm bulbs, controlled cool far core; never brighter / milkier; artistic quality over numbers.
LEVER: ${L.name} - ${L.change} (expected: ${L.expected})
BEFORE: ${ROOT}/${before}/R2_rear_S2_like_3s_16x9.png and ${ROOT}/${before}/hero_mouth_9x16.png. AFTER: ${ROOT}/${r.preview_dir || dir}/R2_rear_S2_like_3s_16x9.png and hero_mouth_9x16.png. Side-by-sides (reference | before | after): ${r.sheet_r2}, ${r.sheet_portrait}. Worker's numbers (verify by eye, do not trust blindly): ${r.measurements}. Landmarks: ${r.landmarks}.
Decide KEEP only if the AFTER is visibly closer to the ORIGINAL in the lever's region AND nothing important got worse anywhere (mascot, water, rings, stars, readability of the path). Default to revert when unsure. Score the tunnel / scenery-only similarity before and after honestly.`,
    { label: `judge lever ${k + 1}`, phase: 'Levers', schema: VERDICT, effort: 'high' })
  if (v && v.keep) {
    before = r.preview_dir || dir
    beforeVs = r.preview_dir || dir
  } else {
    await agent(`Lead tunnel lane, Bubble Wash Kingdom at ${ROOT}. The independent judge REJECTED lever ${k + 1} (${L.name}): ${v ? v.reason.replace(/[`$]/g, '') : 'no verdict'}. Revert it exactly: copy every file from ${r.backup_dir} back over its original path (the change was: ${r.diff.replace(/[`$]/g, '').slice(0, 600)}); if a Blender script was changed, also re-run it (bash Tools/blender_run.sh Tools/Blender/scripts/<script>.py, foreground) so the exported FBX matches the restored script; bash Tools/cs_check.sh; then diff the restored files against the backups (must be identical) and append one line 'L${k + 1} REVERTED: <reason>' to Captures/lead/s2_2b/NOTES_2b.md. Report what you restored.`,
      { label: `revert lever ${k + 1}`, phase: 'Levers', effort: 'low' })
  }
  results.push({ lever: L, applied: r, verdict: v })
  log(`L${k + 1} ${L.name}: ${v ? (v.keep ? 'KEPT' : 'REVERTED') + ' (' + v.closer_to_original + ', ' + v.score_before + ' -> ' + v.score_after + ')' : 'no verdict -> reverted'}`)
}
return { plan: P, results, newest_kept_preview: before }
