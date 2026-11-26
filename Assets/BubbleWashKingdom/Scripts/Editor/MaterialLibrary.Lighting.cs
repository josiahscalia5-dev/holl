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
            // Round 3 (owner sheet 04 "polished bevelled gold"): the ring read pale tan because the untinted lavender probe and
            // the cream highlight colour dominated -> deeper orange-gold mids, probe almost fully gold-tinted, warmer highlight
            // colour and stronger, crisper streaks (bright white-gold lines on a rich amber-orange body, dark bevel lows).
            // Round 4 (sheet 04 "polished bevelled gold, not uniformly saturated yellow bands"): measured around the first
            // visible ring, reference hottest 2/10/30 % = #fef9bb / #fbe7c2 / #f2d2c9 (pale cream cores, peach-rose band),
            // ours #ffec5f / #f7d16a / #ecbd6f (saturated yellow). Band luminance already matched (L50 .69 vs .68), so the
            // hue moves ~8 deg toward rose-peach: rosier mid / low / rim / band colours, more bevel contrast (bright rolled
            // beads, deeper trough), softer streaks (they made the whole band read pale yellow), a little more violet probe.
            // Round 5 (lead: "uniformly saturated orange-yellow bands" vs "polished bevelled gold with bright specular glints"):
            // a gold-pixel mask over the ring zone measured reference hue 33 deg (golden tan V50 #e6be8d, dark edge V10 #c48d70)
            // vs ours 18 deg (salmon, V10 #d7937b) - round 4's rose shift went the wrong way. Back to golden amber, and the
            // fresnel rim colour (was a BRIGHT salmon, so every grazing bevel brightened) becomes a DARK amber: faces toward the
            // camera stay bright, rolled edges darken -> a bevelled band instead of a flat one; stronger glints / streaks.
            // v2: v1 (mid #F0A040 x1.2, cream streaks 1.45) read as a PALE golden-tan band; the 4K reference band is a deeper
            // saturated orange-amber (~#d08838) with darker brown-orange edges and the bulbs clearly brighter than the band.
            // Round 8 (owner: "realistic polished gold"; measured on the same crops, reference vs r7w stills): rendered gold
            // hue 32-36 deg in every section vs ours 26-30 (orange-salmon: rose ring lights + rose probe tint), the reference's
            // dark bevel side V10 #89613f..#a47a56 vs ours #c17d50..#c78d58 (our edges too light -> flat band), and pale
            // cream glints V99 #fee6af..#fef2a7 vs ours #ffcd82 / lemon #ffdf48. -> body ~5 deg more golden, much darker
            // golden-brown lows + bevel rim (rolled edges fall off into deep amber), paler cream highlight, higher body
            // contrast and sharper / stronger studio streaks (crisp bright specular lines on a rich amber body).
            GoldLook("M_Gold", high: "#FFF0C0", mid: "#E2A23E", low: "#3E2208", rim: "#6A3E12", band: "#F4C478",
                brightness: 0.96f, glow: 0.05f, contrast: 2.2f, viewGradient: 1f, env: 0.38f, envTint: 0.85f, envRough: 0.14f,
                specPower: 260f, specStrength: 3.8f, glints: 3.4f, sparkle: 0f, fog: 0.4f, highlightSize: 11f, streak: 1.25f,
                probeTint: "#8C5A6A");
            GoldLook("M_GoldDark", high: "#FFE8BC", mid: "#C88634", low: "#3A1E10", rim: "#5A3414", band: "#F0C890",
                brightness: 1.0f, glow: 0.03f, contrast: 1.9f, viewGradient: 1f, env: 0.5f, envTint: 0.6f, envRough: 0.22f,
                specPower: 180f, specStrength: 2.2f, glints: 2.2f, sparkle: 0f, fog: 0.8f, highlightSize: 9f, probeTint: "#8C5A6A");
            // big premium paw coins (reference 16:9 frame): rich YELLOW gold body, darker amber relief / rim, crisp highlights
            // and a little twinkle as they spin
            // round 8: darker amber relief / bevel (reference coin V10 deep amber, ours stayed light), creamier glints
            GoldLook("M_Coin", high: "#FFF4CC", mid: "#F0A82A", low: "#5A2A04", rim: "#9A5A12", band: "#FFE2A0",
                brightness: 1.0f, glow: 0.05f, contrast: 1.8f, viewGradient: 0.75f, env: 0.32f, envTint: 0.85f, envRough: 0.16f,
                specPower: 220f, specStrength: 2.8f, glints: 2.6f, sparkle: 1.2f, fog: 0.7f, highlightSize: 11f, sparkleScale: 14f,
                probeTint: "#9A6A60", streak: 1.1f);
            // saturated purple faceted gem: the gold shader with a violet palette gives every flat facet its own tone, plus sparkle
            GoldLook("M_Gem", high: "#FFE4FF", mid: "#B22CF2", low: "#2E0766", rim: "#FF9AF2", band: "#E8B4FF",
                brightness: 1.05f, glow: 0.3f, contrast: 1.6f, viewGradient: 1f, env: 0.45f, envTint: 0.85f, envRough: 0.08f,
                specPower: 240f, specStrength: 3f, glints: 3f, sparkle: 3.2f, fog: 0.6f, highlightSize: 14f, sparkleScale: 9f);

            // Warm AMBER marquee bulbs (lead: hot pale-orange cores ~#ffc060, orange halos ~#ff8a20). With the Neutral
            // tonemapper a source of about (6, 1.4, 0.3) linear shows as a pale warm-orange core and its weaker bloom halo as
            // saturated orange: deep red-orange edge colour + warm-orange core tint (never lemon: G stays < 0.25 R).
            // Round 3 (owner: "excessively bright yellow bulbs -> small warm amber lights with a soft halo"): at x12 the green
            // channel (~2.1 linear) tonemapped to 0.9 -> pale lemon cores. x5.6 with a half-amber core keeps G ~1.0 linear:
            // core tonemaps to golden amber (~#FCC95E), the grazing edge to deep orange, the bloom halo stays orange.
            // Round 4: the R4 cores still measured saturated yellow (#ffec5f) because the whole bulb face was a 50 % orange /
            // amber mix. Now a SMALL pale-cream hot centre (_CorePower 2.6, core #FFC878) inside a deep orange body
            // (_EdgeSaturate 1: G/R ~.02) -> the reference's pale warm cores (#fef9bb) with an orange bloom halo.
            // Round 5: cores still lemon (V99 #ffee9b vs reference #ffe0a6 peach-cream): G too high / B too low after the warm
            // highlight grade. Core #FFAA80 x5 tonemaps (Neutral, exposure -.25) to ~#ffe2c6 before grading -> peach-cream.
            EmissiveLook("M_Bulb", "#FF6A10", 5.0f, core: 0.9f, corePower: 2.6f, halo: 1.0f, edgeSat: 1.0f, chase: 1f, chaseMin: 0.75f,
                pulse: 0.05f, fog: 0.08f, coreColor: "#FFAA80", probeDim: 0.3f);
            // end-of-tunnel portal disc (BuildPortal core): radiant warm white-gold, bright but not a screen-filling flare
            // round 8 (owner sheet 03 item 1 "large warm gold burst, no clipped white centre"; measured portal zone f_14.50s:
            // gold 29.9 % / V99 #fef0a9 vs ours 16.8 % / lemon-white #ffdf48): (3.4, 2.7, 1.25) linear + a white core
            // tonemapped to a pale lemon-white disc. Amber source with G/R ~.62, B/R ~.15 and a warm-gold (not white) core
            // keeps the Neutral tonemapper + bloom on the gold side.
            EmissiveLook("M_PortalCore", "#FFA436", 2.3f, core: 0.4f, corePower: 2.2f, halo: 0.45f, edgeSat: 0.7f, pulse: 0.06f, fog: 0.05f,
                coreColor: "#FFD890", probeDim: 0.5f);
            // round 8: the starburst rays + gold sparkles (SM_Starburst_r7 slot M_PortalCore, remapped in BuildPortalExtras;
            // r7 used M_Neon_Yellow whose cream core (#FFF0A0 x .8 on x3.2) bloomed white). Saturated amber-gold rays, a
            // small warm-gold hot centre, moderate intensity so the rays stay gold after tonemapping and bloom.
            EmissiveLook("M_PortalBurst", "#FF9A1C", 2.1f, core: 0.35f, corePower: 2.6f, halo: 0.6f, edgeSat: 0.5f, pulse: 0.08f, fog: 0.04f,
                coreColor: "#FFCC6A", probeDim: 0.4f);
            // MASTER 24 golden destination (masters wave 17:56; owner: "STILL too white"): the four additive glow layers of the
            // asset artist's SM_Starburst_r8 get lighting-owned materials (remapped by SceneBuilder.TunePortalDestination, so
            // the M_Burst*_r8 copies in MaterialLibrary.Assets.cs no longer drive the portal). Measured r8 finale (bg, portal
            // crop): a hard cream-WHITE sun (the M_Bulb x5 Core disc) + thin rays reaching half the ring; reference f_14.50s =
            // broad golden-yellow rays from a cream centre out to the bulb ring over a dark violet field, golden stars.
            // Every colour keeps B/R < .1 so ray overlaps at the centre tonemap to cream-yellow (B stays low), never white;
            // single rays mid-length stay saturated gold (hue ~35 deg after Neutral tonemapping).
            void DestGlow(string name, string hex, float strength, float core, int queueOffset) => Mat(name, "BWK/LightBlob", m =>
            {
                C(m, "_Color", hex); F(m, "_Strength", strength); F(m, "_Softness", 1f); F(m, "_Core", core);
                F(m, "_Mode", 1f); F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One);
                F(m, "_NearFade", 0f);
            }, (int)RenderQueue.Transparent + queueOffset);
            // The halo layer MULTIPLIES first (like M_StarFill_Yellow): additive gold over the violet tunnel kept the violet's
            // blue (rays read beige-pink, the ring interior "bare violet" #674799); pulling the field behind the burst toward
            // amber first lets the additive rays read golden-yellow, the outer field stays dark violet (reference).
            Mat("M_DestHaze", "BWK/LightBlob", m =>
            {
                C(m, "_Color", "#FFC070"); F(m, "_Strength", 0.8f); F(m, "_Softness", 1f); F(m, "_Core", 0.6f);
                F(m, "_Mode", 0f); F(m, "_SrcBlend", (float)BlendMode.DstColor); F(m, "_DstBlend", (float)BlendMode.Zero);
                F(m, "_NearFade", 0f);
            }, (int)RenderQueue.Transparent - 10);
            DestGlow("M_DestRays", "#FFBE45", 2.6f, 1.1f, -9);     // golden-yellow rays fading toward the ring
            DestGlow("M_DestCream", "#FFD487", 1.8f, 1.6f, -8);    // cream centre (not white: B/R .25) inside the ray roots
            DestGlow("M_DestSparkle", "#FFBA3E", 2.0f, 1.3f, -7);  // small golden 4-point sparkles
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
            // round 3: less yellow glare (owner sheet 01), a little more soft cyan / pink spill on the wall (lead audit)
            StarGlow("M_StarGlow_Yellow", "#FF7A00", 2.7f, 1.45f);
            StarGlow("M_StarGlow_Cyan", "#14B8FF", 1.9f, 1.8f);
            StarGlow("M_StarGlow_Pink", "#FF2AA8", 1.8f, 1.8f);
            StarGlow("M_StarGlow_Purple", "#9A3CFF", 1.8f, 1.8f);
            // inside of the yellow star (reference: filled with warm orange light): a multiply card first pulls the pale
            // lavender wall / rim behind it toward orange, then the additive glow lights it up
            Mat("M_StarFill_Yellow", "BWK/LightBlob", m =>
            {
                C(m, "_Color", "#FF9A40"); F(m, "_Strength", 0.95f); F(m, "_Softness", 0.9f); F(m, "_Core", 0.9f);
                F(m, "_Mode", 0f); F(m, "_SrcBlend", (float)BlendMode.DstColor); F(m, "_DstBlend", (float)BlendMode.Zero);
            }, (int)RenderQueue.Transparent - 12);
            // far-tunnel luminous vanishing point (reference: rings receding into warm white light at x ~.55 y ~.30):
            // a wide soft warm-lavender halo + a tight warm-white core, both fading out when the camera gets close
            Mat("M_VanishGlow", "BWK/LightBlob", m =>
            {
                // round 3: the m3 glow clipped to a big white blob (p90 #ffffff, mean #eddbe9 vs reference #ba8ed3):
                // half the strength, warmer pink-lavender, smaller cards (SceneBuilder) -> soft luminous end, not a flare
                C(m, "_Color", "#D898F0"); F(m, "_Strength", 0.42f); F(m, "_Softness", 1f); F(m, "_Core", 1.5f); F(m, "_NearFade", 14f);
                F(m, "_Mode", 1f); F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One);
            }, (int)RenderQueue.Transparent - 9);
            // round 5: soft pink haze card on the upper-left drum wall of the hero view (SceneBuilder.BuildNeonStars)
            Mat("M_PinkHaze", "BWK/LightBlob", m =>
            {
                C(m, "_Color", "#FF4FA0"); F(m, "_Strength", 0.30f); F(m, "_Softness", 1f); F(m, "_Core", 1.5f); F(m, "_NearFade", 3f);
                F(m, "_Mode", 1f); F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One);
            }, (int)RenderQueue.Transparent - 11);
            Mat("M_VanishCore", "BWK/LightBlob", m =>
            {
                C(m, "_Color", "#FFE4D8"); F(m, "_Strength", 1.0f); F(m, "_Softness", 1f); F(m, "_Core", 2.2f); F(m, "_NearFade", 14f);
                F(m, "_Mode", 1f); F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One);
            }, (int)RenderQueue.Transparent - 8);

            // soft violet contact shadow under the mascot (multiply card, BWK/LightBlob)
            Mat("M_ContactShadow", "BWK/LightBlob", m =>
            {
                // round 3 (owner: "seated on the slide, not floating"): deeper, broader violet-blue occlusion
                C(m, "_Color", "#24145A"); F(m, "_Strength", 0.82f); F(m, "_Softness", 0.9f); F(m, "_Core", 1.2f);
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
