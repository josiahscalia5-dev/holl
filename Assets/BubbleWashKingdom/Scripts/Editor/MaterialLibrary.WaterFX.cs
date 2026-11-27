using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: Agent 2 - water & visual effects (slide water, rails, foam, bubbles, chevrons, particle materials).
    // Only this domain's agent edits this file. Helpers (Mat, Lit_, Gold, Emissive, Soft, Particle, C, F, Get) live in MaterialLibrary.cs.
    public static partial class MaterialLibrary
    {
        static void WaterFXMaterials()
        {
            Mat("M_Water", "BWK/Water", m =>
            {
                // reference f_003.00s: bright turquoise-cyan (#32B5E0 / #49DAE0) over medium blue (#3A92C6), glossy, translucent
                // round 3: deep azure body (#1a5fd0 .. #3095d5 in the reference), cyan streaks, cyan light only around the chevrons
                // round 3b (owner correction 03: deep blue, turquoise variation, no flat cyan / broad white streaks / grid): reference
                // water samples #2F89CD (left of the arrows) .. #49BDE3 (right), hue ~200-206 (ours read #3F6CD8 / periwinkle)
                // round 4 (measured r4 base, lower-left water: ours #46ACE5 vs reference #4E97CF = too cyan / bright): fewer
                // turquoise patches, a deeper shallow colour, less near-camera brightening
                // round 4 continuation (v1 measured: arrow notch #43A7E2 vs reference #3386CC, lower-left #8CC6EC vs #4999D0):
                // deeper shallow colour, fewer turquoise patches, a tighter TURQUOISE halo around the arrows (seam fixed)
                // (v3: lower corners #2355CC / #376DCE violet-dark vs reference #65A2D7 / #8DC8E0: lighter, less violet deep colour)
                C(m, "_DeepColor", "#1460B8"); C(m, "_ShallowColor", "#1A72C0"); C(m, "_StreakColor", "#B8F6FF");
                // round 7 (library 16 "flowing turquoise"; hero bottom water ours #79B6E3 vs reference #6EBCDF = a touch too
                // blue / grey): a few more turquoise flow patches
                C(m, "_TurquoiseColor", "#2CC0DC"); F(m, "_PatchAmount", 0.28f); F(m, "_DetailStrength", 0.7f); C(m, "_ReflectTint", "#8CC8FF");
                // round 8 (r8v1 hero bottom water #72A2D6 L .51 vs reference #6EBCDF L .64: the darker round-8 grade turned it
                // blue-grey again; library 16 "turquoise flowing water with glossy streaks"): a lighter turquoise shallow
                // colour, more turquoise flow patches and a little more of the glossy flow streaks
                C(m, "_ShallowColor", "#1C84C8"); F(m, "_PatchAmount", 0.36f);
                // p4 (rear stills p3: water p50 S1 #4476CD / S4 #3E71CB, hue ~222, vs reference water p50 #4BA5DB hue ~203):
                // turquoise-leaning deep + shallow colours and a less violet probe-reflection tint
                C(m, "_DeepColor", "#146CBC"); C(m, "_ShallowColor", "#1A8ECC"); C(m, "_ReflectTint", "#8CD4FF");
                C(m, "_CausticColor", "#7FE9FF"); C(m, "_ChevronColor", "#24E0DA"); C(m, "_EdgeTint", "#E66AC8");
                F(m, "_FlowSpeed", 7.5f); F(m, "_Width", 3.6f); F(m, "_Glow", 0.1f); F(m, "_Smoothness", 0.6f);   // PBR gloss low: at 0.95 the pink CharLight_RimFront drew a wavy streak behind him; the glossy look comes from _ReflectBoost
                F(m, "_StreakAmount", 0.18f); F(m, "_StreakDensity", 1.25f); F(m, "_EdgeTintAmount", 0.28f); F(m, "_SparkleAmount", 0.9f);
                F(m, "_RainbowAmount", 0.32f); F(m, "_RippleStrength", 0.9f); F(m, "_EdgeFoam", 0.6f);
                F(m, "_CausticAmount", 0.28f); F(m, "_Depth", 0.22f); F(m, "_NearBrighten", 0.05f); F(m, "_ReflectBoost", 0.45f); F(m, "_CenterGlow", 0.06f);
                // round 8 MASTER (library 16 "turquoise flowing water", measured p50 #4BA5DB; the r8 rear stills read periwinkle
                // because the lavender drum walls dominate the probe reflection): cyan reflection tint at a lower boost, more
                // turquoise flow patches, stronger ripples + flow streaks (visible flow under / around the mascot)
                C(m, "_ReflectTint", "#8CE8FF"); F(m, "_ReflectBoost", 0.36f); F(m, "_PatchAmount", 0.44f);
                F(m, "_RippleStrength", 1.15f); F(m, "_StreakAmount", 0.22f);
                // p2 (p1 18:27: still periwinkle - the URP PBR reflection of the lavender walls at the grazing rear angle wins;
                // lower half water-class median ours #8083C8 vs reference #609BD1, lum p50 135 vs 147): less mirror-like PBR
                // gloss, the extra probe reflection tinted by the water's own cyan (lavender walls read blue in it), a little
                // more body glow (we are darker than the reference there)
                F(m, "_Smoothness", 0.45f); C(m, "_ReflectTint", "#6CD8FF"); F(m, "_ReflectBoost", 0.5f); F(m, "_Glow", 0.14f);
                // S2 pass 2 (owner 20:15 "rich vivid turquoise flowing water with realistic reflections and depth"; lane under the
                // mascot measured ours #7099D3 hue 215 (gameplay rig hue 228) vs reference #7ABADE hue 202): the lit water is
                // hue-locked toward turquoise (BWK_Water _HueLock: the lavender drum / violet light reflections stop turning the
                // lane periwinkle), cyan-leaning body + patches, crisper glossy reflection (smoothness .45 -> .62), more visible
                // white flow streaks and subsurface caustic depth
                F(m, "_HueLock", 0.9f); F(m, "_HueTarget", 197f);
                C(m, "_DeepColor", "#0C74BE"); C(m, "_ShallowColor", "#16A2D4"); C(m, "_TurquoiseColor", "#20CCDC"); F(m, "_PatchAmount", 0.5f);
                F(m, "_Smoothness", 0.62f); F(m, "_ReflectBoost", 0.55f); C(m, "_ReflectTint", "#7FF0FF");
                C(m, "_StreakColor", "#E6FCFF"); F(m, "_StreakAmount", 0.42f); F(m, "_CausticAmount", 0.4f); F(m, "_Glow", 0.16f);
                // p2 (p1 lane #4EBED9 hue 192 vs reference #7ABADE hue 202 = overshoot, too saturated / green): hue target 203,
                // bluer turquoise patches, a little more white flow and near-camera translucency
                F(m, "_HueTarget", 203f); F(m, "_HueLock", 0.85f); C(m, "_TurquoiseColor", "#2AC0E2"); C(m, "_ShallowColor", "#1E9ED8");
                F(m, "_StreakAmount", 0.52f); F(m, "_NearBrighten", 0.16f);
                // p3 (p2 lane #51B4D9 hue 196 vs reference #7ABADE hue 202: right hue band, but too saturated - the reference
                // lane carries more white flow): softer turquoise patches, denser white flow streaks
                C(m, "_TurquoiseColor", "#46C2E2"); F(m, "_PatchAmount", 0.42f); F(m, "_StreakAmount", 0.62f); F(m, "_StreakDensity", 1.45f);
                // light halos around the decor chevrons: same period / geometry / runway offset as SceneBuilder.BuildDecorChevrons
                F(m, "_ChevronStart", SceneBuilder.ChevronStart); F(m, "_ChevronSpacing", SceneBuilder.ChevronSpacing);
                // (v2 notch measured #55B8E5 vs reference deep #3386CC: the arrows now bloom on their own -> fainter, tighter pool)
                // round 7: arrow light pool .5 -> .32 (owner: arrows too bright; library 20 "gentle glow")
                F(m, "_ChevronScale", SceneBuilder.ChevronScale); F(m, "_ChevronWidth", SceneBuilder.ChevronWidth); F(m, "_ChevronGlow", 0.32f);
                F(m, "_ChevronHalfLen", SceneBuilder.ChevronHalfLen); F(m, "_ChevronHalfWidth", SceneBuilder.ChevronHalfWidth);
                F(m, "_ChevronThick", SceneBuilder.ChevronThick); F(m, "_ChevronOffset", 0f);   // runway = the weave alone
                F(m, "_ChevronEndX", SceneBuilder.ChevronEndX);
                F(m, "_WeaveAmp", SceneBuilder.ChevronWeaveAmp); F(m, "_WeaveLen", SceneBuilder.ChevronWeaveLen); F(m, "_WeaveZero", SceneBuilder.ChevronWeaveZero);
            });
            Mat("M_RailRainbow", "BWK/Soft", m =>
            {
                // reference banks: water edge cyan -> sunny yellow -> hot pink at the rail (glossy candy rainbow) with racing light streaks
                // round 3: reference banks are glossy pink / magenta with rainbow light streaks (not cyan-yellow bands)
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF86D6"); C(m, "_ColorB", "#FF58C2"); C(m, "_ColorC", "#E443CF");
                F(m, "_Smoothness", 0.95f); F(m, "_Glow", 0.3f); F(m, "_RimStrength", 0.3f);
                F(m, "_StreakAmount", 1.4f); F(m, "_StreakSpeed", 7f); F(m, "_ReflectBoost", 0.65f);
            });
            Mat("M_RailPink", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF5FAF"); C(m, "_ColorB", "#FFC2E2"); C(m, "_ColorC", "#FF7FB8");
                F(m, "_Smoothness", 0.95f); F(m, "_Glow", 0.35f); F(m, "_RimStrength", 0.4f);
                F(m, "_StreakAmount", 0.7f); F(m, "_StreakSpeed", 7f); F(m, "_ReflectBoost", 0.7f);
            });
            Lit_("M_SlideShell", "#E24AB8", metallic: 0.05f, smooth: 0.85f, emission: "#3A0A30");
            Emissive("M_ArrowRim", "#E6FFFF", 1.6f, pulse: 0f);   // round 7: 2.6 -> 1.6 (owner: arrows too bright)
            // M_Bubble = a variant of the M_Glass master since round 8 (GlassLiquidMasters below)
            // speed-boost chevrons (BWK/Soft Mode 7): luminous teal glass, mint-white arm centres, HDR so bloom catches them
            Mat("M_Arrow", "BWK/Soft", m =>
            {
                // round 3: turquoise (#3ef0e6) with a mint core; white-cyan (#e0fff8) and hotter right under / behind the mascot
                // round 3b: A = light cyan toward the edges, B = turquoise core, C = crisp white-cyan rim; less white-hot / bloom
                // round 4 (FILLED, reference near arrow: mint-white top #BEF6F5 over turquoise #4EC6DD): A = mint-white core,
                // B = turquoise border / walls, C = white-cyan hot core under / behind the mascot
                // round 4 continuation (v1 arms measured #BDDFDB = pale grey, reference #A6FBF3 .. #CEFAF6 at full value):
                // saturated aqua x3.4 HDR (Neutral tonemap -> ~#9CF7F1, blooms into the water), turquoise edges, mint-white
                // (#DEFFF7 in the reference) on the arrow nearest the camera
                // (v2 matched the value / saturation: #A6FFFF vs #A6FBF3; hue 180 vs 174 -> a touch greener)
                // round 7 (owner 13:30 "reduce excessive cyan arrow brightness"; library 20 "bright centre and gentle glow,
                // keep the shape legible without washing out the lane"): HDR x3.4 -> x2.2 (core just over the bloom
                // threshold: soft halo instead of a glaring block), less white-hot near the camera, paler mint fill
                // round 8 (library 20: a PALE mint fill inside a glowing saturated-cyan edge, not a solid mint block): paler,
                // less saturated fill (_ColorA), brighter cyan border band (_ColorB), slightly lower HDR so the fill stays mint
                F(m, "_Mode", 7); C(m, "_ColorA", "#9CF5EA"); C(m, "_ColorB", "#16D4EE"); C(m, "_ColorC", "#C2FFF2");
                F(m, "_Glow", 0.5f); F(m, "_StreakAmount", 0.08f); F(m, "_StreakSpeed", 1.6f); F(m, "_ReflectBoost", 0.15f);
                F(m, "_HotNear", 1.75f); F(m, "_HotFar", 2.15f); F(m, "_HotBoost", 0.12f);
                // S2 pass 2 (judge: "big pale cyan-white blocks"; reference = ONE glowing two-tone cyan chevron, bright cyan
                // edges, integrated into the water; crop (500,560,800,720) cyan pixels ref 68 % vs ours 13 %): two-tone mode -
                // saturated turquoise-cyan fill at 72 % opacity (the water's ripples + light pool show through), a crisp
                // bright aqua HDR edge band, no white-hot near-camera block; blended over the water (Transparent queue)
                F(m, "_ArrowEdge", 1.8f); F(m, "_ArrowFillAlpha", 0.72f);
                C(m, "_ColorA", "#0DB2D8"); C(m, "_ColorB", "#18D8EE"); C(m, "_ColorC", "#8CFFF4"); F(m, "_Glow", 0.42f);
                F(m, "_SrcBlend", (float)BlendMode.SrcAlpha); F(m, "_DstBlend", (float)BlendMode.OneMinusSrcAlpha); F(m, "_ZWrite", 1f);
            }, (int)RenderQueue.Transparent);
            Mat("M_Foam", "BWK/Soft", m =>
            {
                // soap suds (Mode 5): white-pink puffs, lavender crevices (#A197C4 in the reference), satin gloss, bubble glints
                // round 3: soft cumulus (owner: "not popcorn"): high wrap, light lavender crevices, faint pink, soft satin sheen
                F(m, "_Mode", 5); C(m, "_ColorA", "#FFF7FD"); C(m, "_ShadowColor", "#B8A8DC"); C(m, "_ColorB", "#FFD8F0"); F(m, "_Wrap", 0.72f);
                F(m, "_BumpScale", 10f); F(m, "_BumpStrength", 0.03f); F(m, "_Glow", 0.08f); F(m, "_RimPower", 2.4f); F(m, "_RimStrength", 0.4f);
                F(m, "_SpecStrength", 0.35f); F(m, "_ReflectBoost", 0.2f); F(m, "_GlintAmount", 0.12f); F(m, "_Wobble", 0.015f); F(m, "_WobbleFreq", 1.6f);
            });
            Mat("M_FX_Milk", "BWK/Soft", m =>
            {
                // milky crown splashes + 3D droplets (Mode 6): creamy white, blue-grey shading, cool water bounce, wet highlights
                // round 3b: brighter milky white sheets (reference: white cores, faint blue in thin / shaded parts)
                // round 4 (measured r4 base: our lace #DCD4DB pinkish-grey vs reference #CFE8F2 cyan-white; lead: "milky
                // translucent, soft Fresnel, light blue in thin parts, no plastic specular"): cyan-white milk, blue shading,
                // soft sheen, alpha-blended so thin / grazing parts let the blue water through (ZWrite on: no sorting holes)
                // round 4 continuation (v1 measured: right crown p50 #C9D3DE grey-blue vs reference #C9E7EE cyan-white):
                // cyan-white milk, cyan-blue shading, a little more self glow
                F(m, "_Mode", 6); C(m, "_ColorA", "#C8F4FF"); C(m, "_ShadowColor", "#84B8E8"); C(m, "_ColorB", "#5CC8F0"); F(m, "_Wrap", 0.7f);
                F(m, "_RimPower", 2.0f); F(m, "_RimStrength", 0.8f); F(m, "_SpecStrength", 0.7f); F(m, "_ReflectBoost", 0.25f); F(m, "_Glow", 0.38f);
                F(m, "_Wobble", 0.01f); F(m, "_WobbleFreq", 7f);
                F(m, "_MilkAlpha", 0.97f); F(m, "_MilkEdgeAlpha", 0.45f);
                F(m, "_SrcBlend", (float)BlendMode.SrcAlpha); F(m, "_DstBlend", (float)BlendMode.OneMinusSrcAlpha); F(m, "_ZWrite", 1f);
                // S2 pass 2: the 3D droplets thrown off the crowns = clear water beads (liquid sheet shading: see-through
                // turquoise centre, white Fresnel rim, sharp glints)
                F(m, "_MilkGlass", 1f); C(m, "_MilkThin", "#9FE6F4"); F(m, "_MilkEdgeAlpha", 0.3f); F(m, "_BumpStrength", 0f);
                F(m, "_RimPower", 2.2f); F(m, "_SpecStrength", 1.3f); F(m, "_ReflectBoost", 0.6f); F(m, "_Glow", 0.05f); C(m, "_ColorB", "#3CC8E0");
            }, (int)RenderQueue.Transparent);
            // round 6 shot 8.25 s test (NEW materials for SM_FX_Crown_v2_* / SM_Foam_v2_*; the level's materials above are unchanged)
            Mat("M_FX_Milk_v2", "BWK/Soft", m =>
            {
                // measured on the reference milk mask (Tools/fx_splash_trace.py, f_08.25s): core p80-100 #E9F9F9, mid #D1E7ED,
                // shade p0-20 #B0C5D6 / #B3B9D6: opaque thick milk (no blending: the reference crowns are not see-through),
                // cyan-white body, blue-grey shading, cool bounce from the water, glossy wet highlights
                F(m, "_Mode", 6); C(m, "_ColorA", "#E9F9F9"); C(m, "_ShadowColor", "#A9BED6"); C(m, "_ColorB", "#9CC6E8"); F(m, "_Wrap", 0.42f);
                F(m, "_RimPower", 2.6f); F(m, "_RimStrength", 0.55f); F(m, "_SpecStrength", 1.1f); F(m, "_ReflectBoost", 0.3f);
                F(m, "_Wobble", 0.006f); F(m, "_WobbleFreq", 6f);
                // round 8 (lead r8v1 review: "flat opaque white cut-out shapes in every rear frame"; measured hero splash pixels
                // ours luma p10/50/90 207/216/228 std 9.7 #D5D8D9 vs reference 178/212/230 std 19.8 #C5D1E4): self glow .22
                // pushed the milk past 1.0 so the tonemapper clipped it flat -> glow .04, rounded volume shading (_MilkSoft:
                // white cores, blue-grey roll-off, water-lit thin edges #7DBFE8, soft wet top rims) and a soft translucent
                // silhouette band (alpha .3 at grazing edges; blended, ZWrite on -> no sorting holes inside a crown)
                F(m, "_Glow", 0.04f); F(m, "_MilkSoft", 1f); C(m, "_MilkThin", "#7DBFE8");
                // p2 (p1 measured: L std 10.7 vs ref 19.8, mean #CCD0D2 neutral vs ref #C5D1E4 / #CAE5EB): thickness
                // variation (thick ribs / thin water-lit film, 9 per metre) and a slightly bluer milk body + shade
                F(m, "_BumpScale", 9f); F(m, "_BumpStrength", 0.85f);
                C(m, "_ColorA", "#E4F6FC"); C(m, "_ShadowColor", "#A2BCE0");
                // p3 (p2: variation std L 12.3 / R 17.3 but too dark + grey: p50 196 / 198 vs ref 212 / 226, mean #BDC4D2 vs
                // #C5D1E4): light cyan film (#A6DCF2, ref thin lace ~#B6DAE9), brighter body, more wrap, stronger wet highlights
                C(m, "_MilkThin", "#A6DCF2"); C(m, "_ColorA", "#EAFAFD"); F(m, "_Wrap", 0.52f); F(m, "_SpecStrength", 1.35f); F(m, "_Glow", 0.08f);
                F(m, "_MilkAlpha", 1f); F(m, "_MilkEdgeAlpha", 0.3f);
                F(m, "_SrcBlend", (float)BlendMode.SrcAlpha); F(m, "_DstBlend", (float)BlendMode.OneMinusSrcAlpha); F(m, "_ZWrite", 1f);
                // S2 pass 2 (owner 20:15 "thin, curved, partly translucent liquid crowns", judge #3: opaque white plaster, white
                // coverage 25 % vs reference 11 % in (380,380,960,720)): LIQUID sheet shading (BWK_Soft _MilkGlass) - see-through
                // water-lit film where the crown faces the camera (alpha .24), opaque white Fresnel rims + milky ribs along
                // the fingers, sharp wet glints and a crisp probe reflection; turquoise bounce from the water below
                F(m, "_MilkGlass", 1f); C(m, "_MilkThin", "#A4E6F4"); F(m, "_MilkEdgeAlpha", 0.24f); F(m, "_MilkAlpha", 0.96f);
                F(m, "_RimPower", 2.4f); F(m, "_BumpScale", 11f); F(m, "_BumpStrength", 0.9f); F(m, "_SpecStrength", 1.4f);
                F(m, "_ReflectBoost", 0.6f); F(m, "_Glow", 0.05f); C(m, "_ColorB", "#3CC8E0"); C(m, "_ColorA", "#F2FCFF");
                // p2 (p1 crowns white 9.6 % vs ref 11.2, edge gradient 3.7 vs 2.5 = glassy; the reference strands are milky):
                // milkier film (alpha .24 -> .4, lighter #C2EEF8) + the _MilkSoft milk floor in the shader
                C(m, "_MilkThin", "#C2EEF8"); F(m, "_MilkEdgeAlpha", 0.4f);
            }, (int)RenderQueue.Transparent);
            // Screen ALL pass 4 (owner 21:33 sheet 18 + judge #1: the reference crowns in S2-S7 are OPAQUE MILKY WHITE, ours
            // read as clear glass shards): the v3 master crowns (build_fx_crown_v3.py) use the round-8 milk VOLUME shading
            // (_MilkSoft) without the see-through liquid film: creamy white body (reference core #E9F9F9), soft blue-grey
            // roll-off (shade #B0C5D6), water-lit translucency only in a thin silhouette band, little thickness noise,
            // wet glints from the key + sun
            Mat("M_FX_Milk_v3", "BWK/Soft", m =>
            {
                F(m, "_Mode", 6); C(m, "_ColorA", "#EEFAFC"); C(m, "_ShadowColor", "#A2B8D6"); C(m, "_ColorB", "#86C8EC");
                F(m, "_Wrap", 0.44f); F(m, "_RimPower", 2.6f); F(m, "_RimStrength", 0.3f); F(m, "_SpecStrength", 1.25f);
                F(m, "_ReflectBoost", 0.35f); F(m, "_Glow", 0.07f); F(m, "_Wobble", 0.004f); F(m, "_WobbleFreq", 6f);
                F(m, "_MilkSoft", 1f); F(m, "_MilkGlass", 0f); C(m, "_MilkThin", "#B4DCF0");
                F(m, "_BumpScale", 8f); F(m, "_BumpStrength", 0.25f);
                F(m, "_MilkAlpha", 1f); F(m, "_MilkEdgeAlpha", 0.6f);
                F(m, "_SrcBlend", (float)BlendMode.SrcAlpha); F(m, "_DstBlend", (float)BlendMode.OneMinusSrcAlpha); F(m, "_ZWrite", 1f);
            }, (int)RenderQueue.Transparent);
            Mat("M_Foam_v2", "BWK/Soft", m =>
            {
                // reference foam (4K f_08.00s crops): bright white bubble tops #F3F5FB, faint blue-lavender crevices #B8BEDC,
                // no pink cast; soft satin sheen (many small bubbles, not plastic)
                F(m, "_Mode", 5); C(m, "_ColorA", "#F4F6FC"); C(m, "_ShadowColor", "#B6BCDC"); C(m, "_ColorB", "#E6ECFA"); F(m, "_Wrap", 0.6f);
                F(m, "_BumpScale", 14f); F(m, "_BumpStrength", 0.02f); F(m, "_Glow", 0.1f); F(m, "_RimPower", 2.6f); F(m, "_RimStrength", 0.3f);
                F(m, "_SpecStrength", 0.3f); F(m, "_ReflectBoost", 0.15f); F(m, "_GlintAmount", 0.08f); F(m, "_Wobble", 0.006f); F(m, "_WobbleFreq", 1.4f);
                // round 8 MASTER (library 17 "soft rounded foam bubbles", owner sheet 01 item 4): softer light wrap on the
                // bigger lumps, a satin sheen + small bubble glints, broader soft rim (no flat white)
                F(m, "_Wrap", 0.68f); F(m, "_SpecStrength", 0.38f); F(m, "_GlintAmount", 0.12f); F(m, "_RimStrength", 0.36f); F(m, "_RimPower", 2.2f);
                // S2 pass 2 p3 (owner item 3 "LARGE, SOFT, THREE-DIMENSIONAL foam banks"; p2 door banks = right size, white 56 %
                // vs ref 59 %, but they shade as one flat grey-white wall): less light wrap so every lobe rounds off into a
                // soft lavender-blue crevice, brighter satin tops
                F(m, "_Wrap", 0.45f); F(m, "_SpecStrength", 0.5f); C(m, "_ShadowColor", "#AEB4DA");
            });
            // round 8 masters: the old hall / fallback foam material is now a VARIANT of M_Foam_v2 (no overrides: one foam look)
            WaterVariant("M_Foam", "M_Foam_v2", null, -1);
            Particle("M_FX_Splash", $"{Tex}/T_Splash.png", additive: false, "#FFFFFF");
            Particle("M_FX_SplashSheet", $"{Tex}/T_SplashCrown.png", additive: false, "#FFFFFF");
            Particle("M_FX_Soft", $"{Tex}/T_SoftCircle.png", additive: false, "#FFFFFF");
            Particle("M_FX_FoamLace", $"{Tex}/T_FoamLace.png", additive: false, "#FFFFFF");
            Particle("M_FX_Sparkle", $"{Tex}/T_Sparkle.png", additive: true, "#FFF2B0");
            Particle("M_FX_GemSparkle", $"{Tex}/T_Sparkle.png", additive: true, "#E7B8FF");
            Particle("M_FX_Bubble", $"{Tex}/T_Bubble.png", additive: false, "#FFFFFF");
            Particle("M_FX_Streak", $"{Tex}/T_Streak.png", additive: true, "#BFF6FF");
            Particle("M_FX_SpeedLine", $"{Tex}/T_Streak.png", additive: true, "#DDFBFF");
        }

        /// <summary>Round 8 masters: a Unity MATERIAL VARIANT of a master (Material.parent; every property inherited, then only
        /// the given overrides - tint / scale / strength). A master change shows on every variant.</summary>
        static Material WaterVariant(string name, string parentName, System.Action<Material> overrides, int queue)
        {
            var parent = AssetDatabase.LoadAssetAtPath<Material>($"{Dir}/{parentName}.mat");
            if (parent == null) { Debug.LogWarning($"[BWK] master {parentName} missing - {name} not re-parented"); return null; }
            string path = $"{Dir}/{name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(parent.shader) { name = name }; AssetDatabase.CreateAsset(m, path); }
            if (m.shader != parent.shader) m.shader = parent.shader;
            m.parent = parent;
            m.RevertAllPropertyOverrides();
            overrides?.Invoke(m);
            m.renderQueue = queue == -1 ? parent.renderQueue : queue;
            m.enableInstancing = true;
            EditorUtility.SetDirty(m);
            return m;
        }

        /// <summary>Round 8 masters (water agent; called from EnvironmentMaterials in place of the four glass / pipe-liquid
        /// lines): M_Glass = the glass master (hall arches 03, S5 risers 13, S6-S7 curved pipes 14, chamber glass, bubbles);
        /// M_PipeWater = the glowing-liquid master, M_PipeWaterCyan / M_PipeWaterPink = its tint variants.</summary>
        static void GlassLiquidMasters()
        {
            // library 13 / 14 "transparent glass with visible thickness, fresnel rims, reflections, glowing liquid inside":
            // a broader fresnel rim (reads as wall thickness at the tube silhouettes), stronger probe reflections, a soft edge
            // glow lit by the liquid, a faint thin-film shimmer; the body stays clear so the liquid shows through
            Mat("M_Glass", "BWK/Glass", m =>
            {
                C(m, "_Tint", "#C6E2FF"); F(m, "_Alpha", 0.07f); F(m, "_Glow", 0.16f); F(m, "_FresnelPower", 2.4f);
                F(m, "_Reflectivity", 1.15f); F(m, "_Smoothness", 0.97f); F(m, "_Iridescence", 0.12f); F(m, "_IridescenceScale", 1.6f);
                F(m, "_Bubble", 0f);
            }, (int)RenderQueue.Transparent);
            Mat("M_PipeWater", "BWK/FlowGlow", m => { F(m, "_Mode", 0); C(m, "_ColorA", "#1FD2FF"); C(m, "_ColorB", "#FF3FC8"); F(m, "_Intensity", 1.6f); F(m, "_Speed", 1.2f); F(m, "_Scale", 3f); });
            // curved cyan pipes (library 14) and the pink risers beside the S5 chambers (library 13, reference key 7.5 s)
            WaterVariant("M_PipeWaterCyan", "M_PipeWater", m => { C(m, "_ColorA", "#1FC8FF"); C(m, "_ColorB", "#9AF6FF"); F(m, "_Intensity", 1.8f); F(m, "_Speed", 1.5f); F(m, "_Scale", 2.0f); }, -1);
            WaterVariant("M_PipeWaterPink", "M_PipeWater", m => { C(m, "_ColorA", "#FF3FB8"); C(m, "_ColorB", "#FFB3EE"); F(m, "_Intensity", 1.7f); F(m, "_Speed", 0.9f); F(m, "_Scale", 2.5f); }, -1);
            // soap bubbles (owner takeover list: transparent IRIDESCENT bubbles - clear centres, thin-film hue-shifting rims,
            // small specular dots) = a variant of the glass master: clearer centre, thinner + more iridescent rim film
            WaterVariant("M_Bubble", "M_Glass", m =>
            {
                C(m, "_Tint", "#F0F8FF"); F(m, "_Alpha", 0.035f); F(m, "_Iridescence", 0.8f); F(m, "_FresnelPower", 2.6f); F(m, "_Glow", 0.34f);
                F(m, "_Reflectivity", 0.8f); F(m, "_Bubble", 1f); F(m, "_FilmStrength", 1.0f); F(m, "_WindowStrength", 1.9f); F(m, "_RimWidth", 3.2f);
            }, (int)RenderQueue.Transparent);
        }
    }
}
