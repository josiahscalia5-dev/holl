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
                F(m, "_Mode", 2); C(m, "_ColorA", "#7A467A"); C(m, "_ColorB", "#EDE6FF"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 72); F(m, "_StitchV", 55); F(m, "_BumpStrength", 0.75f); F(m, "_Smoothness", 0.14f); F(m, "_Glow", 0.08f);
            });
            Mat("M_HatCuff", "BWK/Character", m =>
            {
                // tall folded cuff: CUFF_RIBS = 96 deep geometric ribs
                // warmer, lighter violet than before (rendered indigo #5414a9; reference cuff ~#74329e)
                F(m, "_Mode", 2); C(m, "_ColorA", "#945A84"); C(m, "_ColorB", "#945A84"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 96); F(m, "_StitchV", 60); F(m, "_BumpStrength", 0.8f); F(m, "_Smoothness", 0.12f); F(m, "_Glow", 0.12f);
            });
            Mat("M_HatStripe", "BWK/Character", m =>
            {
                // pale pink-lavender ribbed band above the cuff (same 72 ribs as the dome)
                // bright pale pink-white knit band (reference ~#d7acd5, lit #f1c8ef): it sits in the hat's shade, so it self-lights
                F(m, "_Mode", 2); C(m, "_ColorA", "#F8DDF0"); C(m, "_ColorB", "#F8DDF0"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 72); F(m, "_StitchV", 55); F(m, "_BumpStrength", 0.7f); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.18f);
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
                C(m, "_RootColor", "#C45E58"); C(m, "_BaseColor", "#E8786A"); C(m, "_TipColor", "#F6B0A0");
                C(m, "_PawRootColor", "#FFF0E2"); C(m, "_PawTipColor", "#FFF9EE"); F(m, "_PawGlow", 0.45f);   // warm white: reads WHITE under the violet light
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 260); F(m, "_FurLength", 0.032f); F(m, "_Gravity", 0.005f); F(m, "_Thinning", 0.6f); F(m, "_ClumpAmount", 0.45f); F(m, "_ClumpScale", 9f);
                F(m, "_AO", 0.15f); F(m, "_Curl", 1.0f); F(m, "_Underfur", 0.85f); F(m, "_EdgeSoft", 0.16f); F(m, "_SilhouetteFade", 0.6f);
                C(m, "_RimColor", "#FFD0C8"); F(m, "_Glow", 0.14f); F(m, "_RimStrength", 0.5f);
            }, (int)RenderQueue.AlphaTest);
            Mat("M_PomPom", "BWK/Fur", m =>
            {
                // dense soft yarn pom-pom: short, very dense, little thinning so the silhouette stays round and soft
                // deeper violet yarn (reference ~#8741b3, dark centre, lighter radiating tips): straight radial fibres
                C(m, "_RootColor", "#4A2058"); C(m, "_BaseColor", "#86408A"); C(m, "_TipColor", "#CA90D0");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 190); F(m, "_FurLength", 0.042f); F(m, "_Gravity", 0.0f); F(m, "_Thinning", 0.8f); F(m, "_AO", 0.4f);
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
