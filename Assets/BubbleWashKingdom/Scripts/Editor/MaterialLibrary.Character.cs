using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: Agent 1 - character & animation (fur, pom-pom, beanie knit, eyes, mouth, paw pads, star badge).
    // Only this domain's agent edits this file. Helpers (Mat, Lit_, Gold, Emissive, Soft, Particle, C, F, Get) live in MaterialLibrary.cs.
    public static partial class MaterialLibrary
    {
        static void CharacterMaterials()
        {
            Emissive("M_EyeHighlight", "#FFFFFF", 1.6f, pulse: 0f, core: 0f);
            Mat("M_HatKnit", "BWK/Character", m =>
            {
                // reference beanie dome: violet ribbed knit. The ribs are geometry (build_mascot_model.py CROWN_RIBS = 72,
                // UV.x = 0..1 around, UV.y = arc length in metres): _StitchU must equal CROWN_RIBS, _StitchV = rows per metre.
                // albedo chosen so the dome renders like the reference crown (~#76319f) under the tunnel's violet light
                // round 3: 44 BOLD vertical ribs around (CROWN_RIBS = CUFF_RIBS = 44), soft stitch rows, deep grooves
                F(m, "_Mode", 2); C(m, "_ColorA", "#7A467A"); C(m, "_ColorB", "#EDE6FF"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 38); F(m, "_BumpStrength", 1.0f); F(m, "_Smoothness", 0.14f); F(m, "_Glow", 0.08f);
            });
            Mat("M_HatCuff", "BWK/Character", m =>
            {
                // folded ribbed brim: CUFF_RIBS = 44 deep geometric ribs
                // warmer, lighter violet than before (rendered indigo #5414a9; reference cuff ~#74329e)
                F(m, "_Mode", 2); C(m, "_ColorA", "#945A84"); C(m, "_ColorB", "#945A84"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 40); F(m, "_BumpStrength", 1.05f); F(m, "_Smoothness", 0.12f); F(m, "_Glow", 0.12f);
            });
            Mat("M_HatStripe", "BWK/Character", m =>
            {
                // thick pale lavender-white ribbed band knitted into the crown (same 44 ribs as the dome)
                // bright pale pink-white knit band (reference ~#d7acd5, lit #f1c8ef): it sits in the hat's shade, so it self-lights
                F(m, "_Mode", 2); C(m, "_ColorA", "#F4E0F4"); C(m, "_ColorB", "#F4E0F4"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 44); F(m, "_StitchV", 46); F(m, "_BumpStrength", 0.95f); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.18f);
            });
            Mat("M_EyeIris", "BWK/Character", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#2E1409"); C(m, "_ColorB", "#C47C34"); C(m, "_ColorC", "#070302");
                F(m, "_Glow", 0.1f); F(m, "_RimStrength", 0.05f);
            });
            Lit_("M_Mouth", "#4B0F1E", metallic: 0f, smooth: 0.6f);
            Lit_("M_Tongue", "#FF6F93", metallic: 0f, smooth: 0.55f, emission: "#300812");
            Mat("M_PawPad", "BWK/Character", m =>
            {
                // soft candy-pink toe beans: fabric mode multiplies _ColorA by the vertex colour (pads = pink Col)
                F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFFF"); F(m, "_BumpScale", 0.6f); F(m, "_Smoothness", 0.3f); F(m, "_Glow", 0.65f);
                F(m, "_RimStrength", 0.25f);
            });
            Lit_("M_StarBadge", "#FFD43F", metallic: 0.1f, smooth: 0.6f, emission: "#7A4A00");
            var furNoise = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Tex}/T_FurNoise.png");
            Mat("M_Fur", "BWK/Fur", m =>
            {
                // warm plush pink (slightly salmon; the tunnel's violet light adds blue): light roots, soft pale tips.
                // Strand cells are square (the shader doubles UV.x); fine dense guard hairs + thick underfur = plush.
                // coral-leaning albedo: the tunnel light is violet, so this renders as the reference's warm pink (~#d06e94).
                // Short dense minky pile, soft alpha-to-coverage strands, little clumping/curl: plush, not needles.
                // round 3 (owner: "longer irregular plush clumps, avoid uniformly short fuzz"): longer pile, strong clump
                // length variation, more lean/swirl, lighter tips; the seat blends toward the cream coat (vertex alpha)
                C(m, "_RootColor", "#D06C66"); C(m, "_BaseColor", "#F28C7E"); C(m, "_TipColor", "#FFD0C2");
                C(m, "_PawRootColor", "#FFF0E2"); C(m, "_PawTipColor", "#FFF9EE"); F(m, "_PawGlow", 0.45f);   // warm white: reads WHITE under the violet light
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 200); F(m, "_FurLength", 0.052f); F(m, "_Gravity", 0.012f); F(m, "_Thinning", 0.8f); F(m, "_ClumpAmount", 0.8f); F(m, "_ClumpScale", 5f);
                F(m, "_AO", 0.2f); F(m, "_Curl", 1.5f); F(m, "_Underfur", 0.8f); F(m, "_EdgeSoft", 0.16f); F(m, "_SilhouetteFade", 0.45f);
                F(m, "_TuftScale", 20f); F(m, "_TuftAmount", 0.3f);   // ~6.5 cm irregular plush tufts converging toward their tips
                C(m, "_RimColor", "#FFD0C8"); F(m, "_Glow", 0.2f); F(m, "_RimStrength", 0.5f);
            }, (int)RenderQueue.AlphaTest);
            Mat("M_PomPom", "BWK/Fur", m =>
            {
                // dense soft yarn pom-pom: short, very dense, little thinning so the silhouette stays round and soft
                // deeper violet yarn (reference ~#8741b3, dark centre, lighter radiating tips): straight radial fibres
                // round 3: this is now only the DARK CORE of the pom-pom; the starburst is real radial yarn fibres
                // (Hair Curves + Geometry Nodes in build_mascot_model.py, material slot M_PawPad, vertex colour)
                C(m, "_RootColor", "#2E1040"); C(m, "_BaseColor", "#5C2672"); C(m, "_TipColor", "#9A5CB0");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 170); F(m, "_FurLength", 0.034f); F(m, "_Gravity", 0.0f); F(m, "_Thinning", 0.8f); F(m, "_AO", 0.5f);
                F(m, "_Curl", 0.12f); F(m, "_Underfur", 0.8f); F(m, "_ClumpAmount", 0.3f); F(m, "_EdgeSoft", 0.16f); F(m, "_SilhouetteFade", 0.3f);
                C(m, "_RimColor", "#C8A8F0"); F(m, "_Glow", 0.03f); F(m, "_RimStrength", 0.4f);
            }, (int)RenderQueue.AlphaTest);
            // static (shell-less) preview variants: no clipping, no offset
            foreach (var n in new[] { "M_Fur", "M_PomPom" })
            {
                var src = Get(n);
                if (src == null) continue;
                Mat(n + "_Static", "BWK/Fur", m => { m.CopyPropertiesFromMaterial(src); F(m, "_Thinning", 0f); F(m, "_FurLength", 0f); F(m, "_Gravity", 0f); F(m, "_StaticMode", 1f); }, (int)RenderQueue.AlphaTest);
            }
        }
    }
}
