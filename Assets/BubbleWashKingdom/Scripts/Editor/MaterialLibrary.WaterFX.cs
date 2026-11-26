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
                C(m, "_DeepColor", "#0B4AA8"); C(m, "_ShallowColor", "#1A72C0"); C(m, "_StreakColor", "#B8F6FF");
                C(m, "_TurquoiseColor", "#2CC0DC"); F(m, "_PatchAmount", 0.22f); F(m, "_DetailStrength", 0.7f); C(m, "_ReflectTint", "#8CC8FF");
                C(m, "_CausticColor", "#7FE9FF"); C(m, "_ChevronColor", "#24E0DA"); C(m, "_EdgeTint", "#E66AC8");
                F(m, "_FlowSpeed", 7.5f); F(m, "_Width", 3.6f); F(m, "_Glow", 0.1f); F(m, "_Smoothness", 0.6f);   // PBR gloss low: at 0.95 the pink CharLight_RimFront drew a wavy streak behind him; the glossy look comes from _ReflectBoost
                F(m, "_StreakAmount", 0.12f); F(m, "_StreakDensity", 1.25f); F(m, "_EdgeTintAmount", 0.28f); F(m, "_SparkleAmount", 0.9f);
                F(m, "_RainbowAmount", 0.32f); F(m, "_RippleStrength", 0.9f); F(m, "_EdgeFoam", 0.6f);
                F(m, "_CausticAmount", 0.28f); F(m, "_Depth", 0.22f); F(m, "_NearBrighten", 0.05f); F(m, "_ReflectBoost", 0.45f); F(m, "_CenterGlow", 0.06f);
                // light halos around the decor chevrons: same period / geometry / runway offset as SceneBuilder.BuildDecorChevrons
                F(m, "_ChevronStart", SceneBuilder.ChevronStart); F(m, "_ChevronSpacing", SceneBuilder.ChevronSpacing);
                F(m, "_ChevronScale", SceneBuilder.ChevronScale); F(m, "_ChevronWidth", SceneBuilder.ChevronWidth); F(m, "_ChevronGlow", 0.75f);
                F(m, "_ChevronHalfLen", SceneBuilder.ChevronHalfLen); F(m, "_ChevronHalfWidth", SceneBuilder.ChevronHalfWidth);
                F(m, "_ChevronThick", SceneBuilder.ChevronThick); F(m, "_ChevronOffset", SceneBuilder.ChevronLateral);
                F(m, "_ChevronEndX", SceneBuilder.ChevronEndX);
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
            Emissive("M_ArrowRim", "#E6FFFF", 2.6f, pulse: 0f);
            Mat("M_Bubble", "BWK/Glass", m =>
            {
                // soap bubbles: clear centre, thin bright rim, thin-film colour patches, studio window highlights
                C(m, "_Tint", "#EAF6FF"); F(m, "_Alpha", 0.08f); F(m, "_Iridescence", 0.4f); F(m, "_FresnelPower", 2.2f); F(m, "_Glow", 0.5f);
                F(m, "_Reflectivity", 0.7f); F(m, "_Bubble", 1f); F(m, "_FilmStrength", 0.5f); F(m, "_WindowStrength", 1.6f); F(m, "_RimWidth", 2.0f);
            }, (int)RenderQueue.Transparent);
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
                F(m, "_Mode", 7); C(m, "_ColorA", "#5CFFEA"); C(m, "_ColorB", "#1FC4D2"); C(m, "_ColorC", "#A8FFF0");
                F(m, "_Glow", 0.85f); F(m, "_StreakAmount", 0.12f); F(m, "_StreakSpeed", 1.6f); F(m, "_ReflectBoost", 0.15f);
                F(m, "_HotNear", 1.75f); F(m, "_HotFar", 2.15f); F(m, "_HotBoost", 0.3f);
            });
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
            }, (int)RenderQueue.Transparent);
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
    }
}
