export const meta = {
  name: 'bwk-round8-cinematic',
  description: 'Round 8: cinematic look pass for the WHOLE level with the existing URP features (reflection probes, post-processing volume, our URP shaders): polished gold, glass pipes, metallic walls, glossy flowing water, iridescent bubbles, warm light, controlled neon glow',
  phases: [{ title: 'Cinematic look', detail: 'two specialists; Unity/Blender runs serialized by Tools/heavy_lock.sh' }],
}

// args: { base: 'checkpoint-18-r7', before: 'Captures/stills_r7' }
const BASE = (args && args.base) || 'checkpoint-18-r7'
const BEFORE = (args && args.before) || 'Captures/stills_r7'

const REPORT = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: 'What changed in the look of the LEVEL, <= 200 words, plain language' },
    sections_changed: { type: 'array', items: { type: 'string' }, description: 'S1..S7: what now looks different' },
    files_changed: { type: 'array', items: { type: 'string' } },
    best_outputs: { type: 'array', items: { type: 'string' }, description: 'Absolute paths: before/after preview renders and measurement sheets' },
    measurements: { type: 'string', description: 'Reference vs ours before -> after (img_stats: gold hue/value, wall brightness, water colour, neon halo size)' },
    mobile: { type: 'string', description: 'Mobile (Android URP Mobile_RPAsset) impact and what is PC-only' },
    method_verdict: { type: 'string' },
    remaining_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'sections_changed', 'files_changed', 'best_outputs', 'measurements', 'mobile', 'method_verdict', 'remaining_gaps'],
}

const COMMON = `You work on Bubble Wash Kingdom (Unity 6.3 URP 17.3 + Blender 5.3) at C:\\Users\\josia\\thanksgiving for the lead, ROUND 8 = CINEMATIC LOOK PASS. Base: local tag ${BASE} (round-7 whole-level scenery integrated). Read Docs/HANDOFF.md (top status block), Docs/VideoCoverageChecklist.md (S1-S7, track distances) and your own Captures/agents/<domain>/NOTES.md first; continue from the files on disk.
OWNER'S BRIEF (2026-11-26): "use the existing Unity URP, Shader Graph, reflection probes and post-processing capabilities to improve the cinematic appearance of my entire game. Prioritize polished gold machinery, realistic glass pipes, rich metallic tunnel walls, glossy flowing water, beautiful iridescent bubbles, warm lighting and controlled neon glow. Use my original approved Google Flow video as the visual reference throughout all seven sections." No new packages (never Needle Engine), no purchases. Our materials use hand-written URP HLSL shaders in Assets/BubbleWashKingdom/Art/Shaders (the project's deterministic equivalent of Shader Graph) - improve those; use Shader Graph 17.3 (installed) only if one effect is clearly easier there.
EXISTING FEATURES TO TUNE (SceneBuilder.Lighting.cs): reflection probes (hall + one per 30 m tunnel chunk, box bounds), PostFX Volume (Bloom threshold 1.0 / intensity 1.38 / scatter 0.78, Neutral tonemapping, ColorAdjustments, ShadowsMidtonesHighlights, Vignette 0.22, WhiteBalance, Gaussian DOF 15-42 m), key / fill / character lights, BWK_Gold, BWK_Emissive, BWK_DrumWall, BWK_Water, BWK_Glass, BWK_Soft.
OWNER 13:05 (approval of this round): "Use my exact original Google Flow video to match the lighting, metallic reflections, glass pipes, water, colors, shadows, neon glow and overall premium animated-movie appearance. Do not apply generic cinematic effects or excessive bloom. Match my actual approved reference. Preserve all Round 7 scenery improvements and existing gameplay systems." So: NO generic film effects (no film grain, chromatic aberration, lens flares/dirt, heavy DOF, blanket bloom or haze); every change must REDUCE a measured difference to the reference (img_stats on the same crop: reference vs before vs after - report the numbers); bloom halos only as large as the reference's halos around neon tubes and bulbs.
SKILLS: load the project skills unity-graphics and unity-lighting-vfx (Skill tool) before tuning; if Unity Technologies' official plugin is installed (its skills appear as <plugin-id>:urp-postprocessing, :validate-urp-render-graph-renderer-feature, :shader-graph-create-custom-node - check the Skill tool's list), load urp-postprocessing too and follow it where it fits URP 17.3 on Unity 6.3.
KNOWN ROUND-7 LOOK PROBLEMS (from the round-7 reports): the hall's pink console / lavender towers render navy or plum under the hall's blue light (pink pixels 2.2 % vs 12.3 % in the reference at 0.5 s; two material attempts failed - fix it with light colour / self-lit material copies M_HallLavender_r7 / M_HallPink_r7); the portal starburst blooms almost white (gold pixels 2.3 % vs 13.6 % in the reference at 14.5 s); the hall upper half is too blue-purple (58 % vs 33 %).
DO NOT CHANGE: object placement / density from round 7, the camera rig (frozen 2.75/1.3/10/58), gameplay, the track path, the mascot model or its materials, the intro cinematic.
REFERENCE: Reference/frames4k_720/f_SS.SSs.png (every 0.25 s) and Reference/frames4k/ (4K every 1 s) for all 7 sections; measure with Tools/img_stats.py on crops (gold ring pixels ref V50 #e6be8d / V99 #ffe0a6 hue ~33 deg; wall brightness 0.63-0.71; water p50 #4ba5db / p10 #2e86cd; milk #E9F9F9) and compare against ours before -> after.
BEFORE = ${BEFORE}/ and ${BEFORE}/bg/ (mascot hidden). Previews: bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <log> -bwkOut Captures/agents/<domain>/r8 (hero + comparisons, no scene save); stills of the saved scene: bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.CaptureStillsBatch <log> -bwkOut Captures/agents/<domain>/r8/stills (+ bg/). Sheets: Tools/contact_sheet.py, Tools/triptych.py, Tools/overlay.py.
MOBILE (Android, Assets/Settings/Mobile_RPAsset): baked / on-demand reflection probes only (no every-frame realtime probes), no screen-space reflections, no extra per-object realtime lights, cheap shader math; say which effects are PC-only.
RULES: every Unity/Blender command through Tools/unity_run.sh, Tools/safe_build.sh or Tools/blender_run.sh in the FOREGROUND with the Bash timeout 600000 ms; never kill Unity/Blender; bash Tools/cs_check.sh after EVERY C# edit and never leave code that does not compile. No git commits, no scene saves except safe_build where allowed. Images with reference pixels only in Captures/ (the repo is PUBLIC). If one approach fails twice without visible improvement, switch methods and say so. Append 2-4 lines to a "Round 8" section of your NOTES.md after EVERY run (the lead may stop the wave at the usage limit).
`

const AGENTS = {
  light: { label: 'Light + metal: probes, post, gold, walls, neon', prompt: `You are LIGHTING + METAL (lighting owner; the environment agent is idle this round, so you also own its wall material). Output folder Captures/agents/lighting/r8/.
1. Warm cinematic lighting like the video: warm golden key light from the tunnel end / portal, pink haze upper left, deep blue-purple shadows, bright but not flat.
2. Reflection probes so gold, glass and water reflect the warm bulbs and neon: check placement covers S1 hall, every section landmark and the portal; box projection on, sensible resolution (128-256), baked in the build (mobile-safe).
3. Post-processing: tonemapping / colour grade to the reference palette (measure), bloom = controlled neon and bulb halos without a milky veil, subtle vignette; keep DOF only if it helps the reference look at the gameplay camera.
4. Polished gold machinery (BWK_Gold, MaterialLibrary.Lighting.cs): amber metal, sharp bright highlights, visible bulb reflections, darker edges - not salmon, not lemon.
5. Rich metallic tunnel walls (BWK_DrumWall, MaterialLibrary.Environment.cs): deeper blue-purple metal with a soft sheen, dark perforations.
6. Controlled neon glow (BWK_Emissive): saturated pink / cyan / yellow tube cores with soft halos.
7. Hall colours (S1-S2) and the portal (S7): see KNOWN ROUND-7 LOOK PROBLEMS - pink / lavender machines and a GOLDEN (not white) starburst, measured against 0.5 s, 2.0 s and 14.5 s.
You MAY run bash Tools/safe_build.sh light_r8_vN (max 2) to see the whole level (it saves the level scene with every agent's current code - keep yours compiling), then bash Tools/section_triptych.sh r8_light_vN ${BEFORE} Captures/stills.
YOUR FILES: SceneBuilder.Lighting.cs, MaterialLibrary.Lighting.cs, MaterialLibrary.Environment.cs (materials only, no placement code), SceneBuilder.Hall.cs (its M_Hall*_r7 / portal material values only, no placement), BWK_Gold, BWK_Emissive, BWK_DrumWall, BWKCommon.hlsl, Assets/Settings/*, Captures/agents/lighting/. Time box ~35 minutes.` },

  water: { label: 'Water + glass + bubbles look', prompt: `You are WATER + GLASS + BUBBLES (water/FX owner, unity-shader-specialist). Output folder Captures/agents/waterfx/r8/.
1. Glossy flowing water (BWK_Water): turquoise-blue like the reference (measure), clearly flowing in every section, glossy specular streaks and reflections from the reflection probes, depth tint, soft edge foam kept.
2. Realistic glass pipes (BWK_Glass, the pink pipes in S5 and the cyan pipe S6-S7, the hall's cyan pipe): fresnel rim highlights, tinted transparency, internal glowing liquid that flows, bright specular lines - like polished glass in the video.
3. Beautiful iridescent bubbles (BWK_Soft or a bubble variant): thin-film rainbow hue shift by view angle, bright rim, clear centre, small specular dot; sizes and density as in the reference.
4. Milk crowns / foam from round 7 keep their shapes; only improve shading (soft milky translucency, rim light) if it clearly helps.
Previews only (no full builds): AgentPreviewBatch and CaptureStillsBatch as above; the lighting agent's full builds include your code - keep it compiling.
YOUR FILES: BWK_Water, BWK_Glass, BWK_Soft, MaterialLibrary.WaterFX.cs, SceneBuilder.WaterFX.cs (materials / particle look only, no placement changes), TextureGenerator.cs, SplashFX.cs, Captures/agents/waterfx/. Time box ~35 minutes.` },
}

const pick = (args && Array.isArray(args.agents) && args.agents.length) ? args.agents : ['light', 'water']
log('Round 8 agents: ' + pick.join(', ') + ' | base ' + BASE + ' | before ' + BEFORE)
phase('Cinematic look')
const results = await parallel(pick.map(k => () =>
  agent(COMMON + '\n' + AGENTS[k].prompt, { label: AGENTS[k].label, phase: 'Cinematic look', schema: REPORT })
    .then(r => ({ agent: AGENTS[k].label, report: r }))))
return results
