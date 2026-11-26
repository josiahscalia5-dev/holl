using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: Agent 4 - lighting & visual quality (polished gold, coins, gems, marquee bulbs, neon stars, light cards).
    // Only this domain's agent edits this file. Helpers (Mat, Lit_, Gold, Emissive, Soft, Particle, C, F, Get) live in MaterialLibrary.cs.
    public static partial class MaterialLibrary
    {
        static void LightingMaterials()
        {
            // HDR captures (bloom + Neutral tonemapping are real since CaptureUtil.RenderHdr): every value below is tuned for
            // the tonemapped result, not for the raw colour.
            // Ring gold (reference f_003.00s): warm COPPER-ORANGE polished gold - the band reads rose / mauve-copper in its
            // shade (#8d537f..#b06a87 measured), salmon-peach around the bulbs (#c27f72..#eec79b) and orange-gold overall, with
            // crisp white-gold streaks. Never lemon yellow. Violet lows pick up the tunnel; part of the probe stays untinted.
            GoldLook("M_Gold", high: "#FFE9C0", mid: "#F08A28", low: "#5A1A40", rim: "#FFB878", band: "#FFD8A0",
                brightness: 1.25f, glow: 0.06f, contrast: 1.45f, viewGradient: 1f, env: 0.5f, envTint: 0.5f, envRough: 0.24f,
                specPower: 150f, specStrength: 2.4f, glints: 2.2f, sparkle: 0f, fog: 0.5f, highlightSize: 8f, streak: 1.0f,
                probeTint: "#8C4E8C");
            GoldLook("M_GoldDark", high: "#FFE0B0", mid: "#C8702A", low: "#4A1636", rim: "#FFB070", band: "#FFCF96",
                brightness: 1.0f, glow: 0.03f, contrast: 1.6f, viewGradient: 1f, env: 0.5f, envTint: 0.55f, envRough: 0.3f,
                specPower: 120f, specStrength: 1.8f, glints: 2f, sparkle: 0f, fog: 0.8f, highlightSize: 8f, probeTint: "#8C4E8C");
            // big premium paw coins (reference 16:9 frame): rich YELLOW gold body, darker amber relief / rim, crisp highlights
            // and a little twinkle as they spin
            GoldLook("M_Coin", high: "#FFF2C4", mid: "#F2A61C", low: "#7A3606", rim: "#FFD47A", band: "#FFE29C",
                brightness: 1.02f, glow: 0.06f, contrast: 1.5f, viewGradient: 0.75f, env: 0.3f, envTint: 0.85f, envRough: 0.2f,
                specPower: 170f, specStrength: 2.4f, glints: 2.5f, sparkle: 1.2f, fog: 0.7f, highlightSize: 10f, sparkleScale: 14f,
                probeTint: "#9A6A60");
            // saturated purple faceted gem: the gold shader with a violet palette gives every flat facet its own tone, plus sparkle
            GoldLook("M_Gem", high: "#FFE4FF", mid: "#B22CF2", low: "#2E0766", rim: "#FF9AF2", band: "#E8B4FF",
                brightness: 1.05f, glow: 0.3f, contrast: 1.6f, viewGradient: 1f, env: 0.45f, envTint: 0.85f, envRough: 0.08f,
                specPower: 240f, specStrength: 3f, glints: 3f, sparkle: 3.2f, fog: 0.6f, highlightSize: 14f, sparkleScale: 9f);

            // Warm AMBER marquee bulbs (lead: hot pale-orange cores ~#ffc060, orange halos ~#ff8a20). With the Neutral
            // tonemapper a source of about (6, 1.4, 0.3) linear shows as a pale warm-orange core and its weaker bloom halo as
            // saturated orange: deep red-orange edge colour + warm-orange core tint (never lemon: G stays < 0.25 R).
            EmissiveLook("M_Bulb", "#FF6527", 9f, core: 0.6f, corePower: 2f, halo: 0.3f, edgeSat: 0.5f, chase: 1f, chaseMin: 0.75f,
                pulse: 0.05f, fog: 0.08f, coreColor: "#FF8C44", probeDim: 0.2f);
            // end-of-tunnel portal disc (BuildPortal core): radiant warm white-gold, bright but not a screen-filling flare
            EmissiveLook("M_PortalCore", "#FFC860", 3.4f, core: 0.55f, corePower: 2f, halo: 0.3f, edgeSat: 0.3f, pulse: 0.06f, fog: 0.05f);
            // Neon tubes (reference: thick tubes with PALE hot cores - yellow #fbe496, cyan #78eaf5 - inside saturated colour
            // edges and soft tinted halos): saturated edge hue, tinted core across most of the tube face (broad _CorePower),
            // moderate intensity so the tonemapper keeps the colour and the bloom carries the hue.
            EmissiveLook("M_Neon", "#00D8FF", 2.8f, core: 0.65f, corePower: 1.6f, halo: 0.5f, edgeSat: 0.6f, fog: 0.1f, pulse: 0.05f,
                coreColor: "#70FFFF", probeDim: 0.45f);
            EmissiveLook("M_Neon_Cyan", "#00D8FF", 2.8f, core: 0.65f, corePower: 1.6f, halo: 0.5f, edgeSat: 0.6f, fog: 0.1f, pulse: 0.05f,
                coreColor: "#70FFFF", probeDim: 0.45f);
            EmissiveLook("M_Neon_Pink", "#FF2E9E", 3.0f, core: 0.5f, corePower: 1.6f, halo: 0.5f, edgeSat: 0.6f, fog: 0.1f, pulse: 0.05f,
                coreColor: "#FFB0E0", probeDim: 0.45f);
            EmissiveLook("M_Neon_Yellow", "#FF9C00", 3.2f, core: 0.8f, corePower: 1.6f, halo: 0.5f, edgeSat: 0.6f, fog: 0.1f, pulse: 0.05f,
                coreColor: "#FFF0A0", probeDim: 0.45f);
            EmissiveLook("M_Neon_Purple", "#B040FF", 2.9f, core: 0.55f, corePower: 1.6f, halo: 0.5f, edgeSat: 0.6f, fog: 0.1f, pulse: 0.05f,
                coreColor: "#E8C8FF", probeDim: 0.45f);

            // soft coloured glow cards behind every neon star (additive BWK/LightBlob): the star's light spilling over the wall
            // (reference: the big yellow star is filled with a warm ORANGE glow, the cyan one with a soft cyan haze)
            StarGlow("M_StarGlow_Yellow", "#FF6A00", 3.4f, 1.35f);
            StarGlow("M_StarGlow_Cyan", "#14B8FF", 1.6f, 2.0f);
            StarGlow("M_StarGlow_Pink", "#FF2AA8", 1.6f, 2.0f);
            StarGlow("M_StarGlow_Purple", "#9A3CFF", 1.6f, 2.0f);

            // soft violet contact shadow under the mascot (multiply card, BWK/LightBlob)
            Mat("M_ContactShadow", "BWK/LightBlob", m =>
            {
                C(m, "_Color", "#3C1E6E"); F(m, "_Strength", 0.72f); F(m, "_Softness", 0.85f); F(m, "_Core", 1.3f);
                F(m, "_Mode", 0f); F(m, "_SrcBlend", (float)BlendMode.DstColor); F(m, "_DstBlend", (float)BlendMode.Zero);
            }, (int)RenderQueue.Transparent - 20);
        }

        static void StarGlow(string name, string hex, float strength, float core = 2.6f)
        {
            Mat(name, "BWK/LightBlob", m =>
            {
                C(m, "_Color", hex); F(m, "_Strength", strength); F(m, "_Softness", 1f); F(m, "_Core", core);
                F(m, "_Mode", 1f); F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One);
            }, (int)RenderQueue.Transparent - 10);
        }

        static void GoldLook(string name, string high, string mid, string low, string rim, string band, float brightness, float glow,
            float contrast, float viewGradient, float env, float envTint, float envRough, float specPower, float specStrength,
            float glints, float sparkle, float fog, float highlightSize, float sparkleScale = 18f, float lightInfluence = 0.35f, float streak = 0.9f,
            string probeTint = "#FFFFFF")
        {
            Mat(name, "BWK/Gold", m =>
            {
                C(m, "_HighColor", high); C(m, "_MidColor", mid); C(m, "_LowColor", low); C(m, "_RimColor", rim); C(m, "_BandColor", band);
                F(m, "_Brightness", brightness); F(m, "_Emission", glow); F(m, "_Contrast", contrast); F(m, "_ViewGradient", viewGradient);
                F(m, "_EnvReflect", env); F(m, "_EnvTint", envTint); F(m, "_EnvRoughness", envRough);
                F(m, "_SpecPower", specPower); F(m, "_SpecStrength", specStrength); F(m, "_GlintStrength", glints);
                F(m, "_Sparkle", sparkle); F(m, "_SparkleScale", sparkleScale); F(m, "_FogAmount", fog);
                F(m, "_HighlightSize", highlightSize); F(m, "_BandSharpness", 18f); F(m, "_LightInfluence", lightInfluence); F(m, "_StreakStrength", streak); F(m, "_StreakHeight", 0.6f);
                C(m, "_ProbeBakeTint", probeTint);
            });
        }

        static void EmissiveLook(string name, string hex, float intensity, float core, float corePower, float halo, float edgeSat,
            float chase = 0f, float chaseMin = 0.45f, float pulse = 0.12f, float fog = 0.35f, string coreColor = "#FFFFFF", float probeDim = 1f)
        {
            Mat(name, "BWK/Emissive", m =>
            {
                C(m, "_Color", hex); F(m, "_Intensity", intensity); F(m, "_CoreWhite", core); F(m, "_CorePower", corePower);
                F(m, "_HaloBoost", halo); F(m, "_EdgeSaturate", edgeSat); F(m, "_Chase", chase); F(m, "_ChaseMin", chaseMin);
                F(m, "_PulseAmount", pulse); F(m, "_FogAmount", fog);
                C(m, "_CoreColor", coreColor); F(m, "_ProbeBakeDim", probeDim);
            });
        }
    }
}
