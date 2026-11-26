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
                C(m, "_DeepColor", "#0C46B8"); C(m, "_ShallowColor", "#1C86DC"); C(m, "_StreakColor", "#B8F6FF");
                C(m, "_CausticColor", "#7FE9FF"); C(m, "_ChevronColor", "#2FE6FF"); C(m, "_EdgeTint", "#E66AC8");
                F(m, "_FlowSpeed", 7.5f); F(m, "_Width", 3.6f); F(m, "_Glow", 0.16f); F(m, "_Smoothness", 0.95f);
                F(m, "_StreakAmount", 0.85f); F(m, "_StreakDensity", 1.25f); F(m, "_EdgeTintAmount", 0.28f); F(m, "_SparkleAmount", 1.1f);
                F(m, "_RainbowAmount", 0.32f); F(m, "_RippleStrength", 0.9f); F(m, "_EdgeFoam", 0.6f);
                F(m, "_CausticAmount", 0.5f); F(m, "_Depth", 0.22f); F(m, "_NearBrighten", 0.15f); F(m, "_ReflectBoost", 0.45f); F(m, "_CenterGlow", 0.1f);
                // light pools under the decor chevrons: same period / scale as SceneBuilder.BuildDecorChevrons
                F(m, "_ChevronStart", SceneBuilder.ChevronStart); F(m, "_ChevronSpacing", SceneBuilder.ChevronSpacing);
                F(m, "_ChevronScale", SceneBuilder.ChevronScale); F(m, "_ChevronGlow", 0.9f);
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
                C(m, "_Tint", "#EAF6FF"); F(m, "_Alpha", 0.04f); F(m, "_Iridescence", 0.4f); F(m, "_FresnelPower", 2.2f); F(m, "_Glow", 0.5f);
                F(m, "_Reflectivity", 0.7f); F(m, "_Bubble", 1f); F(m, "_FilmStrength", 0.5f); F(m, "_WindowStrength", 1.1f); F(m, "_RimWidth", 2.4f);
            }, (int)RenderQueue.Transparent);
            // speed-boost chevrons (BWK/Soft Mode 7): luminous teal glass, mint-white arm centres, HDR so bloom catches them
            Mat("M_Arrow", "BWK/Soft", m =>
            {
                // round 3: turquoise (#3ef0e6) with a mint core; white-cyan (#e0fff8) and hotter right under / behind the mascot
                F(m, "_Mode", 7); C(m, "_ColorA", "#A6FFF4"); C(m, "_ColorB", "#14D8CE"); C(m, "_ColorC", "#F2FFFC");
                F(m, "_Glow", 0.36f); F(m, "_StreakAmount", 0.25f); F(m, "_StreakSpeed", 1.6f); F(m, "_ReflectBoost", 0.4f);
                F(m, "_HotNear", 3.0f); F(m, "_HotFar", 3.6f); F(m, "_HotBoost", 0.7f);
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
                F(m, "_Mode", 6); C(m, "_ColorA", "#FFFFFF"); C(m, "_ShadowColor", "#B6C4EC"); C(m, "_ColorB", "#9ED8F5"); F(m, "_Wrap", 0.6f);
                F(m, "_RimPower", 2.0f); F(m, "_RimStrength", 0.45f); F(m, "_SpecStrength", 1.0f); F(m, "_ReflectBoost", 0.3f); F(m, "_Glow", 0.22f);
                F(m, "_Wobble", 0.01f); F(m, "_WobbleFreq", 7f);
            });
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
