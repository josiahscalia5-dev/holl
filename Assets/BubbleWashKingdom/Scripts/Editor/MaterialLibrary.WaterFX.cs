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
                // vivid saturated slide water (reference): deep cobalt -> bright cyan, white speed streaks, sparkles, rainbow banks
                C(m, "_DeepColor", "#0B58D0"); C(m, "_ShallowColor", "#16BDFA"); C(m, "_StreakColor", "#E8FCFF");
                C(m, "_EdgeTint", "#C25FD6"); F(m, "_FlowSpeed", 7.5f); F(m, "_Width", 3.6f); F(m, "_Glow", 0.12f); F(m, "_Smoothness", 0.9f);
                F(m, "_StreakAmount", 0.55f); F(m, "_EdgeTintAmount", 0.25f); F(m, "_SparkleAmount", 1.2f); F(m, "_RainbowAmount", 0.4f); F(m, "_RippleStrength", 0.8f);
            });
            Mat("M_RailRainbow", "BWK/Soft", m =>
            {
                // reference banks: water edge cyan -> sunny yellow -> hot pink at the rail (glossy candy rainbow)
                F(m, "_Mode", 1); C(m, "_ColorA", "#4FD8FF"); C(m, "_ColorB", "#FFE66A"); C(m, "_ColorC", "#FF5FB4");
                F(m, "_Smoothness", 0.92f); F(m, "_Glow", 0.32f); F(m, "_RimStrength", 0.3f);
            });
            Mat("M_RailPink", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF5FAF"); C(m, "_ColorB", "#FFC2E2"); C(m, "_ColorC", "#FF7FB8");
                F(m, "_Smoothness", 0.95f); F(m, "_Glow", 0.35f); F(m, "_RimStrength", 0.4f);
            });
            Lit_("M_SlideShell", "#E24AB8", metallic: 0.05f, smooth: 0.85f, emission: "#3A0A30");
            Emissive("M_ArrowRim", "#F2FFFF", 2.5f, pulse: 0f);
            Mat("M_Bubble", "BWK/Glass", m => { C(m, "_Tint", "#FFFFFF"); F(m, "_Alpha", 0.03f); F(m, "_Iridescence", 1f); F(m, "_FresnelPower", 2.2f); F(m, "_Glow", 0.35f); }, (int)RenderQueue.Transparent);
            Mat("M_Arrow", "BWK/FlowGlow", m => { F(m, "_Mode", 2); C(m, "_ColorA", "#22EEFF"); F(m, "_Intensity", 2.6f); F(m, "_Speed", 1.4f); });
            Mat("M_Foam", "BWK/Soft", m =>
            {
                F(m, "_Mode", 0); C(m, "_ColorA", "#FFFFFF"); C(m, "_ShadowColor", "#C9BFE6"); F(m, "_Wrap", 0.65f);
                F(m, "_BumpScale", 3.5f); F(m, "_BumpStrength", 0.35f); F(m, "_Glow", 0.12f); F(m, "_RimStrength", 0.3f);
            });
            Particle("M_FX_Splash", $"{Tex}/T_Splash.png", additive: false, "#FFFFFF");
            Particle("M_FX_SplashSheet", $"{Tex}/T_SplashCrown.png", additive: false, "#FFFFFF");
            Particle("M_FX_Soft", $"{Tex}/T_SoftCircle.png", additive: false, "#FFFFFF");
            Particle("M_FX_Sparkle", $"{Tex}/T_Sparkle.png", additive: true, "#FFF2B0");
            Particle("M_FX_GemSparkle", $"{Tex}/T_Sparkle.png", additive: true, "#E7B8FF");
            Particle("M_FX_Bubble", $"{Tex}/T_Bubble.png", additive: false, "#FFFFFF");
            Particle("M_FX_Streak", $"{Tex}/T_Streak.png", additive: true, "#BFF6FF");
        }
    }
}
