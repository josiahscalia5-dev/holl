export const meta = {
  name: 'bwk-annotated-blueprint',
  description: 'Transform the EXISTING Unity scene to the owner annotated blueprint: 3 domain artists (sequential Unity runs) + adversarial critic + one revise round',
  phases: [
    { title: 'Implement', detail: 'A metal+architecture, B machinery+props, C water+light+neon - one Unity run at a time' },
    { title: 'Critique', detail: 'asset-critic judges each domain before/after against the annotated pages, images only' },
    { title: 'Revise', detail: 'one revision round for REVISE / REJECT verdicts' },
    { title: 'Recheck', detail: 'critic re-judges the revised steps' },
  ],
}

const BASE_STEPS = 'splash,bigsplash,glow,depth,roller,walls,foam,bubbles'
const OWNER = 'OWNER 2026-11-28 ~06:00 (verbatim): "I have provided my ORIGINAL approved Google Flow video with precise visual annotations and arrows identifying the artwork I want. Study every arrow, every marked object and every visual detail. These are my actual requirements, not artistic suggestions. Improve my EXISTING Unity game to reproduce these specific visual details. Do not redesign or rebuild my game. Preserve my rear gameplay camera, controls, animations and gameplay. Focus on matching the scenery, materials, shapes, proportions, machinery, colors, reflections, lighting and environmental richness shown in these references. Do not waste my credits creating another lengthy report or unnecessary technical system. No purchases or additional paid tools. Use these annotated references as your artistic blueprint. Show me actual improvements inside Unity. If you cannot reproduce something accurately, tell me why rather than giving me false hope." Footer on every annotated page: "Match the marked artwork in the existing Unity game. Later front views are scenery references only. Preserve existing gameplay and rear camera | No full rebuild | No paid tools".'

const DOMAINS = [
  {
    key: 'A', name: 'metal', role: 'METAL + ARCHITECTURE (look-dev of the drum metal, gold machinery and tunnel structure)',
    file: 'Assets/BubbleWashKingdom/Scripts/Editor/S2ArtPass.Metal.cs', prefix: 'metal',
    callouts: 'P1.3 Massive gold hatch - rounded polished gold rim with warm inset lamps; P2.1 Thick outer rim - broad gold band, rounded edges and warm bulbs; P2.2 Recessed drum holes - dark oval openings on curved metallic panels; P2.3 Blue-violet metal - alternating blue and purple panels with colorful reflections; P2.4 Layered inner rings - solid gold and violet arches with depth and warm lights; P4.3 Perforated metal wall - dark elongated holes, seams and blue-purple metal; P6.4 Blue-violet surroundings - dark seams, reflections (the metal part; its stars / foam belong to C / B); the gold ring of the P6.3 portal (its radiance belongs to C).',
    owns: 'wall / drum / metal materials (M_DrumWall, M_DrumWallFlat, M_DrumWallHall, M_MetalPurple, M_HatchViolet_s2, M_ChamberDrum if it is wall metal), gold (M_Gold, M_GoldDark, M_DrumRim, M_HatchCrest_s2), bulbs (M_Bulb), ring lips / rims (M_RimGlow_s2, M_RimLight, M_RimSpark_s2, M_VanishCore, M_VanishGlow). The lead base steps glow / depth / walls already edited some of these clones (see Captures/s2art/art06_base/summary.txt) - your steps run AFTER them and may override.',
    hints: 'Shaders: Art/Shaders/BWK_DrumWall.shader, BWK_Gold.shader, BWK_Emissive.shader (read the property names; if the perforation / panel look needs data the shader has, drive it; if it needs a texture, generate it in C# and register it with SaveTex). Builders: SceneBuilder.Environment.cs (drum, rings, door / hatch), SceneBuilder.Hall.cs (hall, door ring), MaterialLibrary.Environment.cs, TextureGenerator.cs. If the walls are split into ring / panel renderers, alternating blue / purple panels can be per-renderer clones; otherwise a panel-tint texture or vertex colours.',
  },
  {
    key: 'B', name: 'machinery', role: 'MACHINERY + PROPS (rollers, control panel, glass pipes, laundry windows, foam, coin)',
    file: 'Assets/BubbleWashKingdom/Scripts/Editor/S2ArtPass.Machinery.cs', prefix: 'mach',
    callouts: 'P1.1 Striped brush roller - dense pink, white and cyan bristles; gold hub; P3.1 Fluffy pink roller - distinct bristle tips above gold side machinery; P1.2 Laundry controls - pink control panel, colored buttons and gold pipes; P4.1 Laundry side chamber - gold-rimmed window, colorful socks and foam; P4.2 Glass liquid pipes - curved transparent pink/cyan tubes with gold collars; P5.1 Transparent fluid tube - visible blue liquid and bubbles inside the tube; P5.2 Gold-rimmed window - rainbow lining, floating laundry and soft foam; P6.1 Laundry chamber - gold trim, rainbow interior, socks and rolling foam; P6.2 Liquid outlet - curving translucent blue pipe connects to machinery; P3.2 Foam banks - overlapping white bubbles of varied sizes; P3.3 Paw-print coin - thick gold edge and raised paw emblem (check; change only if clearly off).',
    owns: 'rollers (M_RollerFur_s2, M_RollerFur_r8, M_Bristle*_s2, M_Brush*), console / buttons / machine bodies (M_ConsolePink_r8, M_ConsoleScreen_r8, M_Button*, M_Screen, M_MachinePink, M_MachineLavender, M_DoorMachine*_s2, M_PlasticWhite), glass + liquid (M_Glass, M_PipeWater, M_PipeWaterCyan, M_PipeWaterPink, M_PinkLiquid_p5), windows / chambers / laundry (M_ChamberSwirl, M_DoorRainbow_r8, M_DoorSock_r8, M_Sock_r8, M_Fabric, M_ChamberDrum only if it is the chamber interior), foam (M_Foam, M_Foam_v2, M_Foam_v2_Shade, M_FX_FoamLace), coin (M_Coin). Gold materials belong to A: for gold collars / pipes that need a different gold, assign a NEW clone to those specific renderers only.',
    hints: 'Objects: SceneBuilder.Hall.cs HallRoller (~line 158: SM_BrushRoller_r8, SM_RollerBristle_s2, SM_BrushRollerArm_r7), S2 door roller (~412-422: SM_RollerFur_s2 / SM_RollerDrum_s2), SM_HallConsole_r7 + SM_CyanPipeArch_r7 (~261, 372, 515-535), PlacePortalChamber (~599: SM_ChamberWindow_v2, SM_CyanPipeCurve_r7); SceneBuilder.Environment.cs BuildPortholes (~502: SM_ChamberWindow_v2, socks SM_Sock_A/B/C), BuildPipes (~830: SM_GlassPipe_Pink_v2, SM_CyanPipeCurve_r7, SM_GlassPipe_Module, SM_Pipe_Coupler), hall props (~966-980: SM_BrushRoller, SM_ControlPanel, SM_GoldPipe_Straight). Blender sources: Tools/Blender/scripts/build_machinery.py, build_props.py and the *_r7 / *_r8 / *_s2 hall scripts. A selective replacement mesh (for example a denser, rounder striped brush roller with real bristle tufts and a gold hub, or a liquid column + bubbles inside a glass tube) is allowed where the shape / proportion clearly needs it: build it headless in Blender, write .bwkm (positions, normals, UV0 flag bit 0, submeshes) and load it with LoadArtMesh in your step; keep the original transform, keep collider-less scenery collider-less.',
  },
  {
    key: 'C', name: 'waterlight', role: 'WATER + LIGHT + NEON (water surface, rails, chevrons, splash look, neon stars, coloured light, portal radiance, bubbles)',
    file: 'Assets/BubbleWashKingdom/Scripts/Editor/S2ArtPass.WaterLight.cs', prefix: 'wl',
    callouts: 'P1.4 Curved water route - blue current, glossy pink rails and layered tunnel; P3.6 Glossy water and rails - rich blue current, cyan chevrons and curved pink/gold rails; P5.4 Reflective water and rails - long highlights on pink rails and deep blue water; P4.5 Water silhouette - irregular splash branches on deep blue water; P3.5 Organic splash crowns - irregular branching blue-white sheets and droplets (the lead art05 milk crowns are the base: tune their look, keep them beside the feet, never over the body); P2.5 Neon stars and bubbles - yellow, cyan and pink outlines; iridescent clear bubbles; P4.4 Colored light and trim - pink star glow, warm bulbs and reflected light; P5.3 Glowing ring and stars - colored star outlines (the ring metal belongs to A); P6.3 Golden light portal - radiant stars / burst (the gold ring belongs to A); P6.4 cyan/pink stars.',
    owns: 'water + slide (M_Water, M_SlideShell), rails (M_RailPink, M_RailRainbow, M_RailBand_r8, M_RailTube_r8), chevrons (M_Arrow, M_ArrowRim), water FX (M_FX_Streak, M_FX_SpeedLine, M_FX_Splash, M_FX_SplashSheet, M_FX_Soft, M_FX_Sparkle; the milk crown material via the core accessor MilkArt()), neon (M_Neon*, M_StarGlow_*, M_StarGlowDoor_*, M_StarFill_Yellow, M_StarBadge), portal radiance (M_PortalCore, M_PortalRays, M_PortalBurst, M_Burst*_r8, M_Dest*), bubbles (M_Bubble, M_FX_Bubble), haze (M_PinkHaze), the post-processing Volume (bloom etc.) and scene lights (a FEW coloured point lights at most - mobile). Fog belongs to the lead depth step: change it only if a callout clearly needs it and say so.',
    hints: 'Shaders: BWK_Water.shader, BWK_FlowGlow.shader, BWK_Emissive.shader, BWK_Glass.shader, BWK_Soft.shader. Builders: SceneBuilder.WaterFX.cs, MaterialLibrary.WaterFX.cs, SceneBuilder.Lighting.cs, MaterialLibrary.Lighting.cs, SceneBuilder.Environment.cs (~718 SM_NeonStarTube_v2 star placement and colours - a star colour mix closer to the original can be per-renderer clones), Hall.cs BuildPortalExtras (~551). Water is the largest area of every gameplay frame: the original reads light cyan-blue near the camera at 0.50 / 3.00 s and DEEP saturated blue with long white highlights at 7.50 / 10.00 / 14.00 s - check whether one material serves all sections; keep the lane readable in the rear gameplay views.',
  },
]

const COMMON = (d) => `You are the ${d.role} artist on Bubble Wash Kingdom, an EXISTING Unity 6 URP mobile game (project C:/Users/josia/thanksgiving, Windows, Git Bash). ${OWNER}
FIRST read Captures/agents/_shared/BLUEPRINT_ANNOTATED_1128.md, then LOOK at the annotated pages (Reference/annotated_1128/pages1080/f_06.00s.png = P1, f_14.00s.png = P2, f_20.00s.png = P3, f_31.00s.png = P4, f_39.00s.png = P5, f_49.00s.png = P6; arrows point at the exact objects) and the clean original frames (Reference/frames4k_720/f_00.50s.png, f_03.00s.png, f_07.50s.png, f_10.00s.png, f_14.00s.png; 4K detail Reference/frames4k/f_03.00s.png, f_07.00s.png, f_08.00s.png, f_10.00s.png, f_14.00s.png).
YOUR CALLOUTS (the owner's exact words): ${d.callouts}
YOU OWN: ${d.owns}
WHERE THINGS ARE: ${d.hints} Material names: MaterialLibrary*.cs. The 'pick' lines in Captures/s2art/art06_base/summary.txt name the object + material under key R2 pixels.
GOAL: make every callout of yours VISIBLY closer to the original INSIDE UNITY by transforming the EXISTING scene - materials (clones: recolour / retune / new generated textures), emissive, lighting, VFX, and SELECTIVE mesh replacement only where the shape or proportion clearly needs it. No rebuild, no redesign; preserve gameplay, the rear camera, controls, animations, collisions. This is artistic production: visible results only - no reports, no new infrastructure.
THE LEAD'S TOOL (read it first): Assets/BubbleWashKingdom/Scripts/Editor/S2ArtPass.cs opens the main scene IN MEMORY, applies art steps cumulatively and renders; it never saves the main scene or edits .mat assets. Put ALL your code in ONE new file ${d.file}:
  namespace BubbleWash.EditorTools { public static partial class S2ArtPass { [ArtStep("${d.prefix}_something")] static void Something(Ctx c) { ... } } }
  (same usings as S2ArtPass.cs). Core helpers you may call: Swap(what, match, edit, c.log) clones each matching SOURCE material once and assigns the clone to every renderer slot (edit with C(mat, "_Prop", "#RRGGBB"), F(mat, "_Prop", v), Mul(mat, "_Prop", k); match with Named(m, "M_X") / Starts(m, "M_X")); c.runner, c.cam, c.mascot, c.log; SaveTex(tex, name, linear, normalMap) for EVERY texture you create; LoadArtMesh(path, out subMat) for replacement meshes; MilkArt() returns the splash clone. Per-renderer variants: new Material(source) assigned to chosen renderers (add nothing to cloneOf for those).
BASELINE already rendered (do NOT re-render it): Captures/s2art/art06_base/stills_current/ = the GAME today; stills_bubbles/ = after the lead's art05 base steps = YOUR BEFORE; current/ and art_08_bubbles/ = R2 (matched 3.00 s rear camera) + rig_d*_9x16 (portrait gameplay) sets. Stills: 01_hall_start .. 09_portal (_16x9 + _9x16 = rear GAMEPLAY views), R3..R6 / C1..C5 _16x9 (front comparison cameras = scenery reference only), 10_finale; every folder has bg/ (mascot hidden).
PREVIEW (heavy; run in the FOREGROUND with the Bash timeout 600000; ~5 min; Unity runs queue on Tools/heavy_lock.sh):
  bash Tools/cs_check.sh      <- after EVERY C# edit, never leave code that does not compile (every Unity run compiles all files)
  bash Tools/unity_run.sh BubbleWash.EditorTools.S2ArtPass.PreviewBatch bp_${d.key}_N -bwkOut Captures/s2art/bp_${d.key}_N -bwkSteps "${BASE_STEPS},<your steps in order>" -bwkStillsAt "<your last step>" -bwkR2Each 0
  -> Captures/s2art/bp_${d.key}_N/stills_<last>/ (+ bg/), art_NN_<last>/ (R2_16x9, R2_bg_16x9, rig_d*_9x16), summary.txt (look for STEP FAILED and the slot counts - 0 slots = your match missed).
  Blender only for a replacement mesh: bash Tools/blender_run.sh Tools/Blender/scripts/<your new script>.py <log> (headless, --factory-startup), outputs under Tools/Blender/work/s2art/${d.name}/.
JUDGE like an art director: crop and compare original | before (stills_bubbles) | after for EVERY view your callouts appear in (rear gameplay 16x9 AND 9x16 first, front comparison cameras second), at the same regions. A quick sheet script with Blender's python is fine: "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I your.py (numpy; Tools/img_crop.py read_png / write_png, Tools/labeled_sheet.py caption_bar). Keep only changes that are visibly closer to the original; revert the rest. Write 3-5 lines to Captures/agents/bp_${d.key}/NOTES.md after every preview (usage limits can cut you; the next session resumes from it).
RULES: never edit .mat assets, MaterialLibrary*.cs, SceneBuilder*.cs, shaders, S2ArtPass.cs (lead) or another artist's S2ArtPass.*.cs; never save the main scene; never run a full build, safe_build, Play Mode tests or -bwkSave; never touch the mascot; no downloads, purchases or new packages; images with reference pixels stay in Captures/ (the repo is PUBLIC); never kill Unity / Blender; do not edit C# under Assets/ while your own Unity run is in progress. Mobile: modest triangle counts, no screen-space reflections, at most a few extra realtime lights; say what is PC-only. If something cannot be reproduced accurately, say exactly why (no false hope).`

const IMPL = {
  type: 'object',
  properties: {
    steps: { type: 'array', items: { type: 'string' }, description: 'your step names in the order to run them after the base steps' },
    files: { type: 'array', items: { type: 'string' } },
    final_dir: { type: 'string', description: 'Captures/s2art/bp_X_N of the preview that shows the final state' },
    callouts: { type: 'array', items: { type: 'object', properties: {
      page: { type: 'string' }, n: { type: 'integer' },
      status: { type: 'string', enum: ['done', 'partial', 'not_possible', 'unchanged'] },
      change: { type: 'string' }, why_not: { type: 'string' } }, required: ['page', 'n', 'status', 'change'] } },
    pages: { type: 'array', items: { type: 'object', properties: {
      page: { type: 'string' }, before: { type: 'number' }, after: { type: 'number' }, proof: { type: 'string' } }, required: ['page', 'before', 'after'] } },
    regressions: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['steps', 'final_dir', 'callouts', 'pages'],
}

const CRIT = {
  type: 'object',
  properties: {
    steps: { type: 'array', items: { type: 'object', properties: {
      step: { type: 'string' }, verdict: { type: 'string', enum: ['KEEP', 'REVISE', 'REJECT'] },
      evidence: { type: 'string' }, fix: { type: 'string' } }, required: ['step', 'verdict', 'evidence'] } },
    callouts: { type: 'array', items: { type: 'object', properties: {
      page: { type: 'string' }, n: { type: 'integer' }, closer: { type: 'string', enum: ['yes', 'no', 'same'] },
      evidence: { type: 'string' } }, required: ['page', 'n', 'closer'] } },
    pages: { type: 'array', items: { type: 'object', properties: {
      page: { type: 'string' }, before: { type: 'number' }, after: { type: 'number' } }, required: ['page', 'before', 'after'] } },
    regressions: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['steps', 'callouts', 'pages', 'regressions'],
}

const critPrompt = (d, r, round) => `Independent critic, ${round}. Judge ONLY from images the ${d.role} artist's change to the EXISTING Unity game against the owner's ANNOTATED BLUEPRINT. Read Captures/agents/_shared/BLUEPRINT_ANNOTATED_1128.md and LOOK at the annotated pages Reference/annotated_1128/pages1080/f_06.00s.png (P1), f_14.00s.png (P2), f_20.00s.png (P3), f_31.00s.png (P4), f_39.00s.png (P5), f_49.00s.png (P6) and the clean originals Reference/frames4k_720/f_00.50s.png, f_03.00s.png, f_07.50s.png, f_10.00s.png, f_14.00s.png.
Callouts to judge: ${d.callouts}
BEFORE = Captures/s2art/art06_base/stills_bubbles/ (+ bg/) and Captures/s2art/art06_base/art_08_bubbles/ (R2 + rig). AFTER = ${r.final_dir}/stills_*/ (+ bg/) and ${r.final_dir}/art_*/ (the highest-numbered art_NN folder). Steps applied: ${JSON.stringify(r.steps)}. Never read the artist's notes or code; images only (you may crop / tile them with Blender's python "C:/Users/josia/Blender/blender-5.3.0-windows-x64/5.3/python/bin/python.exe" -I and Tools/img_crop.py / Tools/labeled_sheet.py, writing only under Captures/agents/bp_critic/).
For EACH callout: is AFTER visibly closer to the original than BEFORE (yes / no / same) with concrete evidence (image + region). Rear gameplay views (01_hall_start .. 09_portal _16x9 and _9x16, rig_d*_9x16, R2) count most; front comparison cameras (R3..R6, C1..C5) are scenery references. Per step: KEEP, REVISE (give the exact visible fix) or REJECT (revert). Check regressions: lost landmarks, worse readability of the slide / mascot / coins in the rear gameplay views, colours moving AWAY from the original, noisy / flickery detail, broken or missing objects. Honest /10 per page (P1..P6 where relevant) before -> after; default to the LOWER score when unsure; never call it better unless the images show it.`

const reviseResult = async (d, r, c) => {
  const prompt = `${COMMON(d)}
REVISION ROUND. Your previous result: ${JSON.stringify(r)}
The independent critic judged it (images only): ${JSON.stringify(c)}
Fix every REVISE item exactly as described where you agree the images show it, remove REJECT steps (delete or disable them in ${d.file} and drop them from your step list), keep KEEP steps unchanged. At most 2 Unity preview runs (name them bp_${d.key}_r1, bp_${d.key}_r2). Return the FINAL state (steps list = what the lead should run).`
  return agent(prompt, { label: `revise:${d.key}-${d.name}`, phase: 'Revise', schema: IMPL })
}

const results = {}
const critics = {}
for (const d of DOMAINS) {
  log(`Implement ${d.key} ${d.name}`)
  const r = await agent(`${COMMON(d)}
BUDGET: at most 3 Unity preview runs (bp_${d.key}_1 .. bp_${d.key}_3); get it right in one run where you can. Return your final state.`,
    { label: `impl:${d.key}-${d.name}`, phase: 'Implement', schema: IMPL })
  results[d.key] = r
  critics[d.key] = r ? agent(critPrompt(d, r, 'round 1'), { label: `critic:${d.key}-${d.name}`, phase: 'Critique', agentType: 'asset-critic', schema: CRIT }) : Promise.resolve(null)
}
for (const d of DOMAINS) critics[d.key] = await critics[d.key]

const revised = {}
const rechecks = {}
for (const d of DOMAINS) {
  const r = results[d.key], c = critics[d.key]
  if (!r || !c) continue
  const bad = (c.steps || []).filter(s => s.verdict !== 'KEEP')
  if (!bad.length) { log(`${d.key}: all steps KEEP - no revision`); continue }
  log(`${d.key}: ${bad.length} step(s) need revision`)
  const r2 = await reviseResult(d, r, c)
  revised[d.key] = r2
  rechecks[d.key] = r2 ? agent(critPrompt(d, r2, 'round 2 (after revision)'), { label: `recheck:${d.key}-${d.name}`, phase: 'Recheck', agentType: 'asset-critic', schema: CRIT }) : Promise.resolve(null)
}
for (const k of Object.keys(rechecks)) rechecks[k] = await rechecks[k]

return { domains: DOMAINS.map(d => ({ key: d.key, name: d.name, impl: results[d.key] || null, critic: critics[d.key] || null, revised: revised[d.key] || null, recheck: rechecks[d.key] || null })) }
