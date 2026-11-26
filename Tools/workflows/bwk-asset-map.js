export const meta = {
  name: 'bwk-asset-map',
  description: 'Map the owner\'s 24 library assets to crop boxes in our capture stills (same cameras every build) and audit each asset vs its library crop -> Captures/agents/_shared/asset_views.json + asset checklist sheets',
  whenToUse: 'Once per camera set (re-run only when CaptureStills cameras change); its boxes drive Tools/asset_checklist.py for every later build',
  phases: [{ title: 'Map + audit', detail: 'one vision agent: 24 assets -> still + crop box + verdict' }],
}

// args: { prev: 'Captures/stills_r7w', cur: 'Captures/stills_r8v1', out: 'Captures/assets_r8v1' }
const PREV = (args && args.prev) || 'Captures/stills_r7w'
const CUR = (args && args.cur) || 'Captures/stills_r8v1'
const OUT = (args && args.out) || 'Captures/assets_r8v1'

const VIEW = {
  type: 'object',
  properties: {
    still: { type: 'string', description: 'file name inside the stills folder, e.g. 01_hall_start_16x9.png' },
    box: { type: 'array', items: { type: 'number' }, description: '[x0, y0, x1, y1] pixels of that still (x1/y1 exclusive)' },
    bg: { type: 'boolean', description: 'true = use the bg/ copy (mascot hidden)' },
  },
  required: ['still', 'box', 'bg'],
}
const ASSET = {
  type: 'object',
  properties: {
    id: { type: 'string', description: '01..24' },
    name: { type: 'string' },
    views: { type: 'array', items: VIEW, description: '1-2 views; empty if the asset is not visible in any still' },
    status: { type: 'string', enum: ['missing', 'inaccurate_shape', 'mispositioned_or_misscaled', 'material_inferior', 'close', 'satisfactory'] },
    score_now: { type: 'number', description: 'similarity of our CURRENT version to the library crop, 0-10, honest' },
    weaknesses: { type: 'array', items: { type: 'string' }, description: 'most visible differences first, concrete (shape, proportion, colour, material, placement)' },
    owner: { type: 'string', enum: ['assets', 'metal', 'water', 'character', 'lead'] },
    priority: { type: 'number', description: '1 = biggest visible gain per effort in gameplay views, 3 = minor' },
  },
  required: ['id', 'name', 'views', 'status', 'score_now', 'weaknesses', 'owner', 'priority'],
}
const RESULT = {
  type: 'object',
  properties: { assets: { type: 'array', items: ASSET }, notes: { type: 'string' } },
  required: ['assets', 'notes'],
}

phase('Map + audit')
const PY = 'C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe'
const r = await agent(`You are the ASSET AUDITOR for Bubble Wash Kingdom (C:/Users/josia/thanksgiving, Unity 6.3 URP). Do not edit any project file except the outputs named below; no Unity / Blender runs; no git.
THE OWNER'S 24-ASSET LIBRARY (private, the official visual target): Reference/asset_library/00_READ_ME_Asset_Index.md (24 numbered assets: what, where, source time), small crops Reference/asset_library/Original_Crops/NN_*.png (23 has 23_ front + 23b_ rear) and larger sheets Individual_References/NN_*.png. The owner's strict brief is Captures/agents/_shared/OWNER_BRIEF_1705_24_assets.md (section 2 = per-asset requirements) - read it.
OUR CAPTURE STILLS (identical cameras in every build): ${CUR}/ = current build (round 8 v1), ${PREV}/ = previous build (round 7w). 1280x720 *_16x9.png and 720x1280 *_9x16.png: 01_hall_start, 02_hall_curve (S1-S2 hall), 03_tunnel_entry, 04_tunnel, 05_tunnel_lane_left, 06_tunnel_lane_right, 07_chambers, 08_sweep, 09_portal, 10_finale (rear gameplay camera, S7 = mascot turned toward the camera in front of the portal), hero (rear, 105 m), 16x9-only front cameras C1..C5 and R3..R6 (reference-matched S3-S6 views). bg/ holds the same stills with the MASCOT HIDDEN.
TASK for each asset 01-24: pick 1-2 views where OUR version is most visible and closest to the library crop's viewpoint (scenery: prefer bg/ = true; mascot 23: one rear hero view + one view where the face shows; splash crowns 18 / chevrons 20 / coins 21 / gems 22: views with the mascot, bg false, unless bg shows them too) and a crop box [x0,y0,x1,y1] in that still's pixels, generous (~15 % margin) so the same box also contains the asset in the previous build and after small proportion fixes (rollers / chamber windows / tunnel entrance may move a little). Verify boxes by cropping: "${PY}" -I Tools/img_crop.py <still> Captures/agents/_shared/asset_map_check/A<NN>.png x0 y0 x1 y1 and Read the crop (at most ~35 image reads in total - Read whole stills only when needed, 1280x720 is fine). Then audit our CURRENT version against the library crop: status, an honest 0-10 score, concrete weaknesses (shape, proportion, colour, material, placement; e.g. 'console reads navy, library is glossy hot pink'), owner (assets = 01-06 + 11-12 + 15 geometry; metal = materials of 04-11, 21-22, the whole 24 destination; water = 03, 13-14, 16-20; character = 23; lead = camera / gameplay) and priority (1 = biggest gain in gameplay views).
OUTPUTS: write Captures/agents/_shared/asset_views.json = {"assets": [{"id","name","views":[{"still","box","bg"}],"note"}]} (same boxes as you return), then run "${PY}" -I Tools/asset_checklist.py Captures/agents/_shared/asset_views.json ${PREV} ${CUR} ${OUT} 220 and Read ONE of the resulting ${OUT}/GROUP_*.png to confirm the rows show the right asset (fix boxes if not, re-run). Append one audit line per asset to Captures/agents/_shared/asset_audit.md under a heading "## Lead asset audit r8v1 (17:2x)". Return the full result.`,
  { label: 'Asset auditor: 24 assets -> crop boxes + verdicts', phase: 'Map + audit', schema: RESULT })
return r
