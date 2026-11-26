export const meta = {
  name: 'bwk-round7-verify',
  description: 'Independent per-section similarity scoring of the newest Unity build vs the approved video (judges per section group, then one skeptic across all sections)',
  whenToUse: 'After a lead integration build and Tools/section_triptych.sh <tag>: honest /10 scores for S1-S7, with and without the mascot',
  phases: [
    { title: 'Judge', detail: 'three independent judges, one per section group' },
    { title: 'Challenge', detail: 'one skeptic re-checks every score across all sections' },
  ],
}

// args: { tag: 'r7' }  -> sheets Captures/sections/S<n>_triptych_<tag>.png, ALL_triptych_<tag>.png, ALL_bg_triptych_<tag>.png
const TAG = (args && args.tag) || 'r7'
const ROOT = 'C:/Users/josia/thanksgiving'

const SECTION = {
  type: 'object',
  properties: {
    id: { type: 'string', description: 'S1..S7' },
    prev_with_mascot: { type: 'number' }, new_with_mascot: { type: 'number' },
    prev_scenery_only: { type: 'number' }, new_scenery_only: { type: 'number' },
    improved: { type: 'array', items: { type: 'string' } },
    regressions: { type: 'array', items: { type: 'string' } },
    top_gaps: { type: 'array', items: { type: 'string' }, description: 'Most visible remaining differences, biggest first' },
  },
  required: ['id', 'prev_with_mascot', 'new_with_mascot', 'prev_scenery_only', 'new_scenery_only', 'improved', 'regressions', 'top_gaps'],
}
const JUDGE = { type: 'object', properties: { sections: { type: 'array', items: SECTION } }, required: ['sections'] }
const FINAL = {
  type: 'object',
  properties: {
    sections: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, final_with_mascot: { type: 'number' }, final_scenery_only: { type: 'number' },
      prev_with_mascot: { type: 'number' }, prev_scenery_only: { type: 'number' },
      changed_from_judge: { type: 'string', description: 'What you lowered/raised and why (or "kept")' },
      top_gaps: { type: 'array', items: { type: 'string' } } },
      required: ['id', 'final_with_mascot', 'final_scenery_only', 'prev_with_mascot', 'prev_scenery_only', 'changed_from_judge', 'top_gaps'] } },
    whole_game: { type: 'string', description: 'Overall estimate before -> after with one sentence of justification' },
    verdict: { type: 'string', description: 'Did this round make the level substantially closer to the video? Where not?' },
  },
  required: ['sections', 'whole_game', 'verdict'],
}

const RUBRIC = `You are an independent visual judge for Bubble Wash Kingdom (a Unity game rebuilt from the owner's approved Google Flow video 25982.mp4). Judge ONLY what the images show; never read the specialists' notes or reports (you must not be influenced by their claims).
Each sheet ${ROOT}/Captures/sections/S<n>_triptych_${TAG}.png has 3 columns and 2 rows: column 1 = the ORIGINAL VIDEO FRAME, column 2 = PREVIOUS Unity build, column 3 = NEWEST Unity build. Row 1 = with the mascot, row 2 = the same renders with the mascot hidden (scenery only). Comparison cameras are approximate (front-facing stills for S3-S6; rear gameplay camera for S1, S2, S7), so judge the WORLD: objects present, their shapes, sizes, placement, density, materials, colours and lighting - not exact framing.
Scale (be strict, the owner rejects inflated scores): 9-10 = the same scene - every landmark present, same density, materials and lighting, only small detail differences; 7-8 = clearly the same place with a few missing or wrong elements; 5-6 = same theme and some right landmarks but many missing / wrong objects or a different look; 3-4 = generic purple tunnel / hall missing most landmarks; 1-2 = unrelated. Use half points. The section requirements are in ${ROOT}/Docs/VideoCoverageChecklist.md ("Section details").
Read each sheet with the Read tool (PNG). Scores for the mascot rows also count the mascot; scenery-only scores ignore it.`

const GROUPS = [
  { key: 'S1-S2', ids: ['S1', 'S2'], note: 'S1 opening machine hall (0-1.25 s), S2 rainbow slide into the gold tunnel mouth (hero frame 3.0 s, rear gameplay camera).' },
  { key: 'S3-S5', ids: ['S3', 'S4', 'S5'], note: 'S3 tunnel of gold bulb rings and neon stars, S4 bend with the first sock-chamber window, S5 sock chambers and pink glass pipes.' },
  { key: 'S6-S7', ids: ['S6', 'S7'], note: 'S6 chamber tunnel 2 (windows both sides, cyan water pipe, dense stars), S7 golden starburst light portal finale.' },
]

phase('Judge')
const judged = await parallel(GROUPS.map(g => () =>
  agent(`${RUBRIC}\nYour sections: ${g.note}\nSheets: ${g.ids.map(s => `${ROOT}/Captures/sections/${s}_triptych_${TAG}.png`).join(', ')}.\nReturn one entry per section (${g.ids.join(', ')}).`,
    { label: `judge ${g.key}`, phase: 'Judge', schema: JUDGE, effort: 'high' })))
const scores = judged.filter(Boolean).flatMap(r => r.sections)
log(`judged ${scores.length} of 7 sections`)

// Barrier is intended: the skeptic needs every section's score at once to keep the scale consistent across sections.
phase('Challenge')
const final = await agent(`${RUBRIC}
You are the SKEPTIC. Three judges scored the sections below. Look at every sheet yourself (${ROOT}/Captures/sections/S1..S7_triptych_${TAG}.png, overview ${ROOT}/Captures/sections/ALL_triptych_${TAG}.png and ALL_bg_triptych_${TAG}.png) and try to REFUTE each score: lower any score that is inflated (default to the lower score when unsure), make the scale consistent across sections, and raise a score only with a concrete visual reason. Keep the judges' previous-build scores unless clearly wrong.
Judges' results (JSON): ${JSON.stringify(scores)}`,
  { label: 'skeptic S1-S7', phase: 'Challenge', schema: FINAL, effort: 'high' })
return { tag: TAG, judges: scores, final }
