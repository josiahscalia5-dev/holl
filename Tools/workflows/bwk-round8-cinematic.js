export const meta = {
  name: 'bwk-round8-cinematic',
  description: 'Round 8: substantial visual-quality transformation of the WHOLE level (S1-S7) to the approved video: polished gold, rich metal, fluffy rollers, glossy rainbow rails, turquoise water, soft soap bubbles, warm reflections - better assets and materials, not more objects',
  phases: [{ title: 'Quality pass', detail: 'three specialists (max 2 at once on this laptop); Unity/Blender runs serialized by Tools/heavy_lock.sh' }],
}

// args: { base: '<newest checkpoint tag>', before: 'Captures/stills_r7w', agents: ['metal','assets','water'] }
const BASE = (args && args.base) || 'checkpoint-18-r7'
const BEFORE = (args && args.before) || 'Captures/stills_r7w'

const REPORT = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: 'What changed in the look of the LEVEL, <= 200 words, plain language' },
    sections_changed: { type: 'array', items: { type: 'string' }, description: 'S1..S7: what now looks different' },
    files_changed: { type: 'array', items: { type: 'string' } },
    best_outputs: { type: 'array', items: { type: 'string' }, description: 'Absolute paths: before/after renders next to reference crops' },
    measurements: { type: 'string', description: 'Reference vs ours before -> after on the same crops (img_stats numbers)' },
    mobile: { type: 'string', description: 'Android (Mobile_RPAsset) impact; what is PC-only' },
    method_verdict: { type: 'string' },
    remaining_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'sections_changed', 'files_changed', 'best_outputs', 'measurements', 'mobile', 'method_verdict', 'remaining_gaps'],
}

const COMMON = `You work on Bubble Wash Kingdom (Unity 6.3 URP 17.3 + Blender 5.3) at C:\\Users\\josia\\thanksgiving for the lead, ROUND 8 = VISUAL-QUALITY TRANSFORMATION of the whole playable level. Base: local tag ${BASE} (round-7 scenery + the completed round-7 water / foam / splash pass). Read Docs/HANDOFF.md (top status block), Docs/VideoCoverageChecklist.md ("Round 7 scores" + section details) and your own Captures/agents/<domain>/NOTES.md first; continue from the files on disk.
OWNER'S BRIEF (2026-11-26, strict): "Round 7 shows some visible improvements, but the entire level still lacks the premium visual quality of my original approved Google Flow video ... make Round 8 a substantial visual-quality transformation across all seven sections, not merely a lighting adjustment. Pay particular attention to realistic polished gold, rich metallic materials, fluffy roller bristles, glossy rainbow rails, turquoise flowing water, soft soap bubbles and warm cinematic reflections ... Use the official Unity rendering skills and our existing Blender and Unity capabilities. Do not simply add more stars or machinery. Improve the actual artistic quality of every visible asset and how everything looks together. Preserve the existing gameplay, scenery improvements and checkpoints. My target remains 9/10 visual similarity throughout the entire playable level." Earlier: "Use my exact original Google Flow video to match the lighting, metallic reflections, glass pipes, water, colors, shadows, neon glow and overall premium animated-movie appearance. Do not apply generic cinematic effects or excessive bloom ... Do not simply increase the brightness."
SO: improve the QUALITY of what exists - shapes, bevels, surface detail, material response (specular, reflections, fresnel, roughness, subsurface-like softness), colour and light direction - so every asset reads like the video's premium animated-movie version of it. Never raise overall brightness, never add more stars / machinery / props, no generic film effects (grain, chromatic aberration, lens dirt/flares, heavy DOF, blanket bloom or haze). Every change must reduce a MEASURED difference to the reference on the same crop (Tools/img_stats.py: reference vs before vs after) and be visible in the comparison stills.
SKILLS: load the project skills unity-graphics and unity-lighting-vfx with the Skill tool; Unity Technologies' official plugin is installed on the owner's account - if its skills are listed (names ending :urp-postprocessing, :validate-urp-render-graph-renderer-feature, :shader-graph-create-custom-node), load the ones that fit your task and follow them where they fit URP 17.3 / Unity 6.3. Our materials use hand-written URP HLSL shaders (Assets/BubbleWashKingdom/Art/Shaders, deterministic); Shader Graph 17.3 only if one effect is clearly easier there. No new packages (never Needle Engine), no downloads, no purchases.
REFERENCE: Reference/frames4k_720/f_SS.SSs.png every 0.25 s; Reference/frames4k/ (4K every 1 s) for close crops of gold, glass, rollers, rails, water, foam and bubbles. Measured palette: gold ring pixels V50 #e6be8d / V99 #ffe0a6 (hue ~33 deg); wall brightness 0.63-0.71; water p50 #4ba5db / p10 #2e86cd; milk #E9F9F9 (shade #A9BED6); foam #F4F6FC (shade #B6BCDC); hall S1: pink 12.3 % / gold 11.1 % / blue-purple 33 % of the upper half (ours 2.2 / 6.3 / 58 %); portal 14.5 s gold 13.6 % (ours 2.3 %, starburst blooms white).
COMPARISON STILLS: every full build writes Captures/stills/ + bg/ (mascot hidden), now including REFERENCE-MATCHED front cameras R3 (158 m, S3), R4 (190 m), R5 (220 m), R6 (280 m) solved from the video's camera (2.6 m ahead, 1.3 m up, vFOV 52) next to the older C stills. BEFORE = ${BEFORE}/ (+bg/). Agent previews: bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut Captures/agents/<domain>/r8 (hero + comparisons, saved scene + your material changes, no save); stills of the saved scene: CaptureStillsBatch <log> -bwkOut Captures/agents/<domain>/r8/stills. Sheets: Tools/contact_sheet.py, Tools/triptych.py, Tools/overlay.py, Tools/img_crop.py.
DO NOT CHANGE: object placement / density from round 7, the camera rig (frozen 2.75/1.3/10/58), gameplay (RunnerController, input, coins / gems as TrackItems, colliders, track path), the mascot model and its materials, the intro.
MOBILE (Android, Assets/Settings/Mobile_RPAsset): baked / on-demand reflection probes only, no screen-space reflections, no extra realtime lights per object, keep triangle counts modest (LODs where you add detail); say which effects are PC-only.
RULES: every Unity/Blender command through Tools/unity_run.sh, Tools/safe_build.sh or Tools/blender_run.sh in the FOREGROUND with the Bash timeout 600000 ms; never kill Unity/Blender; bash Tools/cs_check.sh after EVERY C# edit and never leave code that does not compile (other agents' builds compile your files). New Blender assets: preview next to the matching 4K reference crop before Unity. No git commits. Images with reference pixels only in Captures/ (the repo is PUBLIC). If one approach fails twice without visible improvement, switch methods and say so. Append 2-4 lines to a "Round 8" section of your NOTES.md after EVERY run (the lead may stop the wave at the usage limit).
`

const AGENTS = {
  metal: { label: 'Gold, metal + warm reflections', prompt: `You are GOLD + METAL + LIGHT (lighting owner; the environment agent is idle, so its wall material is yours too). Output folder Captures/agents/lighting/r8/.
1. Realistic POLISHED GOLD on every gold asset (rings, window frames, hinges, couplers, valves, coins' material response, portal ring; BWK_Gold + MaterialLibrary.Lighting.cs): amber metal like the reference crops - sharp bright specular lines, warm bulb and neon reflections, darker bevel edges, no salmon, no lemon, no flat yellow.
2. RICH METALLIC tunnel walls (BWK_DrumWall + MaterialLibrary.Environment.cs material values): blue-purple brushed metal with soft sheen, perforations with real depth (dark interiors, lit rims).
3. WARM CINEMATIC REFLECTIONS: reflection probes that cover each section's landmarks (hall, tunnel chunks, windows, portal) with box projection and baked cubemaps so gold, glass, rails and water reflect warm bulbs and neon; light colour / direction like the video (warm golden key from the tunnel end, pink haze upper left, deep blue-purple shadows).
4. Post only where the reference needs it (colour grade to the measured palette, bloom halos no larger than the reference's), never brighter overall.
5. Hall S1-S2 colour (pink console / lavender towers render navy: fix with light colour and self-lit material values in SceneBuilder.Hall.cs) and a GOLDEN, not white, portal starburst (S7).
You MAY run bash Tools/safe_build.sh metal_r8_vN (max 2; it saves the level with every agent's current code), then bash Tools/section_triptych.sh r8_metal_vN ${BEFORE} Captures/stills.
YOUR FILES: SceneBuilder.Lighting.cs, MaterialLibrary.Lighting.cs, MaterialLibrary.Environment.cs (material values only), SceneBuilder.Hall.cs (material values only), BWK_Gold, BWK_Emissive, BWK_DrumWall, BWKCommon.hlsl, Assets/Settings/*, Captures/agents/lighting/. Time box ~40 minutes.` },

  assets: { label: 'Asset artist: rollers, rainbow rails, windows', prompt: `You are the ASSET ARTIST (Blender + Unity materials for the existing props; technical-artist). Output folder Captures/agents/assets/ (create it with NOTES.md).
Make the existing assets look like the video's premium versions - same objects, same places, better quality:
1. FLUFFY ROLLER BRISTLES (hall S1-S2 rollers SM_BrushRoller_r7 render as blocky "pixel" discs): smooth striped pink / white / blue band bodies with soft fluffy bristles (shell fur with a material copy that uses the existing BWK_Fur shader - do not edit the shader file - or a soft fibre card mesh), matching the 4K crops at 0.0-2.0 s.
2. GLOSSY RAINBOW RAILS AND LANES on the slide (judges: "no rainbow lanes - flat blue channel with pink rails"): glossy pink rails and the pink / yellow / cyan lanes the video shows, as track-module material slots / UV stripes (build_track.py) with a new material set in a NEW partial file Assets/BubbleWashKingdom/Scripts/Editor/MaterialLibrary.Assets.cs; the water surface stays the water agent's.
3. Chamber windows (SM_ChamberWindow_v2) and socks: socks clearly striped and readable, glossy window glass, rainbow interior and gold hinge detail like the 8.25-11 s crops; the hall console (pink glossy plastic, buttons, screen) and gold valves / pipes: bevels and surface detail like the reference.
Asset swaps / material assignments may go in SceneBuilder.Environment.cs and SceneBuilder.Hall.cs (model and material references only - no placement or density changes; coordinate with the metal agent through its NOTES.md for SceneBuilder.Hall.cs).
Previews: Blender preview next to the 4K crop first, then bash Tools/safe_build.sh assets_r8_vN (max 2), then bash Tools/section_triptych.sh r8_assets_vN ${BEFORE} Captures/stills.
YOUR FILES: Tools/Blender/scripts/build_hall_assets.py, build_track.py, build_machinery.py, build_shot0825_assets.py, the new *_r8 models, MaterialLibrary.Assets.cs (new), SceneBuilder.Environment.cs + SceneBuilder.Hall.cs (references only), Captures/agents/assets/. Time box ~40 minutes.` },

  water: { label: 'Water, foam, bubbles + glass quality', prompt: `You are WATER + FOAM + BUBBLES + GLASS (water/FX owner, unity-shader-specialist). Output folder Captures/agents/waterfx/r8/. The round-7 water pass (foam clusters, milk crowns, water colour) is already in; now raise the QUALITY:
1. TURQUOISE FLOWING WATER (BWK_Water): the reference's turquoise-blue with glossy specular streaks, flowing ripples and probe reflections in every section; depth tint toward the rails.
2. SOFT FOAM: soap-bubble clusters with soft milky translucency and rim light (not hard white blobs, not cloud domes).
3. SOFT SOAP BUBBLES (BWK_Soft or a bubble variant): clear centres, thin-film iridescent rims that shift hue with the view angle, small specular dots, sizes as in the reference.
4. REALISTIC GLASS PIPES (BWK_Glass: pink S5 risers, the cyan pipe S6-S7, the hall's cyan arches): fresnel rims, tinted transparency, bright specular lines and the glowing liquid flowing inside.
5. Milk crowns: keep the traced shapes; only improve shading (milky translucency, soft rim) if it measurably helps.
Previews only (AgentPreviewBatch / CaptureStillsBatch as above); the metal and asset agents' full builds include your code - keep it compiling.
YOUR FILES: BWK_Water, BWK_Glass, BWK_Soft, MaterialLibrary.WaterFX.cs, SceneBuilder.WaterFX.cs (look only, no placement), TextureGenerator.cs, SplashFX.cs, build_fx_v2.py, Captures/agents/waterfx/. Time box ~35 minutes.` },
}

const pick = (args && Array.isArray(args.agents) && args.agents.length) ? args.agents : ['metal', 'assets', 'water']
log('Round 8 agents: ' + pick.join(', ') + ' | base ' + BASE + ' | before ' + BEFORE + ' (max 2 run at once; the third starts when one finishes)')
phase('Quality pass')
const results = await parallel(pick.map(k => () =>
  agent(COMMON + '\n' + AGENTS[k].prompt, { label: AGENTS[k].label, phase: 'Quality pass', schema: REPORT })
    .then(r => ({ agent: AGENTS[k].label, report: r }))))
return results
