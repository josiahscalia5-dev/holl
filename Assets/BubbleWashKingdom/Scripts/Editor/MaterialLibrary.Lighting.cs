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
            // Polished jewellery gold: deep amber undersides -> rich yellow body -> pale hot highlights, a view-dependent
            // gradient across flat ring faces, partly gold-tinted reflections of the violet tunnel and sharp bulb glints.
            GoldLook("M_Gold", high: "#FFF6D0", mid: "#F5B42A", low: "#7A3A08", rim: "#FFE09A", band: "#FFEDB0",
                brightness: 1.25f, glow: 0.06f, contrast: 1.6f, viewGradient: 1f, env: 0.45f, envTint: 0.55f, envRough: 0.22f,
                specPower: 150f, specStrength: 2.2f, glints: 2.4f, sparkle: 0f, fog: 0.8f, highlightSize: 8f);
            GoldLook("M_GoldDark", high: "#FFE6A6", mid: "#D88E1C", low: "#552406", rim: "#FFD080", band: "#FFDF98",
                brightness: 1.1f, glow: 0.03f, contrast: 1.6f, viewGradient: 1f, env: 0.5f, envTint: 0.65f, envRough: 0.3f,
                specPower: 120f, specStrength: 1.8f, glints: 2f, sparkle: 0f, fog: 0.8f, highlightSize: 8f);
            // big premium paw coins: saturated yellow gold, amber rim, crisp highlights and a little twinkle as they spin
            GoldLook("M_Coin", high: "#FFF6D2", mid: "#FFBE1C", low: "#8C4206", rim: "#FFE290", band: "#FFEBA8",
                brightness: 1.1f, glow: 0.1f, contrast: 1.45f, viewGradient: 0.75f, env: 0.35f, envTint: 0.75f, envRough: 0.2f,
                specPower: 170f, specStrength: 2.4f, glints: 2.5f, sparkle: 1.4f, fog: 0.7f, highlightSize: 10f, sparkleScale: 14f);
            // saturated purple faceted gem: the gold shader with a violet palette gives every flat facet its own tone, plus sparkle
            GoldLook("M_Gem", high: "#FFE4FF", mid: "#B22CF2", low: "#2E0766", rim: "#FF9AF2", band: "#E8B4FF",
                brightness: 1.05f, glow: 0.3f, contrast: 1.6f, viewGradient: 1f, env: 0.45f, envTint: 0.85f, envRough: 0.08f,
                specPower: 240f, specStrength: 3f, glints: 3f, sparkle: 3.2f, fog: 0.6f, highlightSize: 14f, sparkleScale: 9f);

            // Warm amber marquee bulbs: a moderately hot, fully saturated amber source so the Neutral tonemapper keeps the hue
            // (amber-yellow body, whiter centre from _CoreWhite) and the untinted bloom spreads an amber halo.
            EmissiveLook("M_Bulb", "#FF8C0A", 6f, core: 0.28f, corePower: 6f, halo: 0.25f, edgeSat: 0.8f, chase: 1f, chaseMin: 0.7f, pulse: 0.05f, fog: 0.08f);
            // end-of-tunnel portal disc (BuildPortal core): radiant warm white-gold, bright but not a screen-filling flare
            EmissiveLook("M_PortalCore", "#FFC860", 3.4f, core: 0.55f, corePower: 2f, halo: 0.3f, edgeSat: 0.3f, pulse: 0.06f, fog: 0.05f);
            // Saturated neon tubes (reference: thick YELLOW / CYAN / PINK tubes, white-hot only in a thin core line): pure
            // hues (no minor channel) at ~3x so they stay coloured after tonemapping and bloom into tinted halos; a sharp
            // _CorePower makes the white line only where the tube faces the camera.
            EmissiveLook("M_Neon", "#00D4FF", 3.0f, core: 0.55f, corePower: 14f, halo: 0.45f, edgeSat: 1f, fog: 0.12f, pulse: 0.06f);
            EmissiveLook("M_Neon_Cyan", "#00D4FF", 3.0f, core: 0.55f, corePower: 14f, halo: 0.45f, edgeSat: 1f, fog: 0.12f, pulse: 0.06f);
            EmissiveLook("M_Neon_Pink", "#FF1EA8", 3.2f, core: 0.5f, corePower: 14f, halo: 0.45f, edgeSat: 1f, fog: 0.12f, pulse: 0.06f);
            EmissiveLook("M_Neon_Yellow", "#FFC000", 2.9f, core: 0.5f, corePower: 14f, halo: 0.45f, edgeSat: 1f, fog: 0.12f, pulse: 0.06f);

            // soft coloured glow cards behind every neon star (additive BWK/LightBlob): the star's light spilling over the wall
            StarGlow("M_StarGlow_Yellow", "#FFAE1A", 0.85f);
            StarGlow("M_StarGlow_Cyan", "#14C6FF", 0.85f);
            StarGlow("M_StarGlow_Pink", "#FF2EB2", 0.85f);

            // soft violet contact shadow under the mascot (multiply card, BWK/LightBlob)
            Mat("M_ContactShadow", "BWK/LightBlob", m =>
            {
                C(m, "_Color", "#3C1E6E"); F(m, "_Strength", 0.72f); F(m, "_Softness", 0.85f); F(m, "_Core", 1.3f);
                F(m, "_Mode", 0f); F(m, "_SrcBlend", (float)BlendMode.DstColor); F(m, "_DstBlend", (float)BlendMode.Zero);
            }, (int)RenderQueue.Transparent - 20);
        }

        static void StarGlow(string name, string hex, float strength)
        {
            Mat(name, "BWK/LightBlob", m =>
            {
                C(m, "_Color", hex); F(m, "_Strength", strength); F(m, "_Softness", 1f); F(m, "_Core", 2.1f);
                F(m, "_Mode", 1f); F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One);
            }, (int)RenderQueue.Transparent - 10);
        }

        static void GoldLook(string name, string high, string mid, string low, string rim, string band, float brightness, float glow,
            float contrast, float viewGradient, float env, float envTint, float envRough, float specPower, float specStrength,
            float glints, float sparkle, float fog, float highlightSize, float sparkleScale = 18f, float lightInfluence = 0.35f, float streak = 0.9f)
        {
            Mat(name, "BWK/Gold", m =>
            {
                C(m, "_HighColor", high); C(m, "_MidColor", mid); C(m, "_LowColor", low); C(m, "_RimColor", rim); C(m, "_BandColor", band);
                F(m, "_Brightness", brightness); F(m, "_Emission", glow); F(m, "_Contrast", contrast); F(m, "_ViewGradient", viewGradient);
                F(m, "_EnvReflect", env); F(m, "_EnvTint", envTint); F(m, "_EnvRoughness", envRough);
                F(m, "_SpecPower", specPower); F(m, "_SpecStrength", specStrength); F(m, "_GlintStrength", glints);
                F(m, "_Sparkle", sparkle); F(m, "_SparkleScale", sparkleScale); F(m, "_FogAmount", fog);
                F(m, "_HighlightSize", highlightSize); F(m, "_BandSharpness", 18f); F(m, "_LightInfluence", lightInfluence); F(m, "_StreakStrength", streak); F(m, "_StreakHeight", 0.6f);
            });
        }

        static void EmissiveLook(string name, string hex, float intensity, float core, float corePower, float halo, float edgeSat,
            float chase = 0f, float chaseMin = 0.45f, float pulse = 0.12f, float fog = 0.35f)
        {
            Mat(name, "BWK/Emissive", m =>
            {
                C(m, "_Color", hex); F(m, "_Intensity", intensity); F(m, "_CoreWhite", core); F(m, "_CorePower", corePower);
                F(m, "_HaloBoost", halo); F(m, "_EdgeSaturate", edgeSat); F(m, "_Chase", chase); F(m, "_ChaseMin", chaseMin);
                F(m, "_PulseAmount", pulse); F(m, "_FogAmount", fog);
            });
        }
    }
}
