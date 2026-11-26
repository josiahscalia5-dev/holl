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
                // reference beanie: violet ribbed knit, ~46 rib columns around, stacked V stitches
                F(m, "_Mode", 2); C(m, "_ColorA", "#7536BC"); C(m, "_ColorB", "#EDE6FF"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 46); F(m, "_StitchV", 24); F(m, "_BumpStrength", 0.9f); F(m, "_Smoothness", 0.18f); F(m, "_Glow", 0.1f);
            });
            Mat("M_HatCuff", "BWK/Character", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#6A31AE"); C(m, "_ColorB", "#6A31AE"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 40); F(m, "_StitchV", 9); F(m, "_BumpStrength", 1.0f); F(m, "_Smoothness", 0.16f); F(m, "_Glow", 0.08f);
            });
            Mat("M_HatStripe", "BWK/Character", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#F1EAFF"); C(m, "_ColorB", "#F1EAFF"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 46); F(m, "_StitchV", 24); F(m, "_BumpStrength", 0.8f); F(m, "_Smoothness", 0.2f); F(m, "_Glow", 0.12f);
            });
            Mat("M_EyeIris", "BWK/Character", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#2E1409"); C(m, "_ColorB", "#C47C34"); C(m, "_ColorC", "#070302");
                F(m, "_Glow", 0.1f); F(m, "_RimStrength", 0.05f);
            });
            Lit_("M_Mouth", "#4B0F1E", metallic: 0f, smooth: 0.6f);
            Lit_("M_Tongue", "#FF6F93", metallic: 0f, smooth: 0.55f, emission: "#300812");
            Lit_("M_PawPad", "#F2F4FF", metallic: 0f, smooth: 0.35f, emission: "#2A1A20");
            Lit_("M_StarBadge", "#FFD43F", metallic: 0.1f, smooth: 0.6f, emission: "#7A4A00");
            var furNoise = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Tex}/T_FurNoise.png");
            Mat("M_Fur", "BWK/Fur", m =>
            {
                // plush hot-pink coat: light roots (no dark gaps between strands), warm pink body, pale pink tips
                C(m, "_RootColor", "#B24A66"); C(m, "_BaseColor", "#E97B91"); C(m, "_TipColor", "#FFC3CB");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 235); F(m, "_FurLength", 0.04f); F(m, "_Gravity", 0.01f); F(m, "_Thinning", 0.7f); F(m, "_ClumpAmount", 0.6f); F(m, "_ClumpScale", 8f);
                F(m, "_AO", 0.22f); F(m, "_Curl", 1.3f); F(m, "_Underfur", 0.6f);
                C(m, "_RimColor", "#FFD6E8"); F(m, "_Glow", 0.14f); F(m, "_RimStrength", 0.8f);
            }, (int)RenderQueue.AlphaTest);
            Mat("M_PomPom", "BWK/Fur", m =>
            {
                C(m, "_RootColor", "#45288A"); C(m, "_BaseColor", "#7445C2"); C(m, "_TipColor", "#AE86EA");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 120); F(m, "_FurLength", 0.03f); F(m, "_Gravity", 0.003f); F(m, "_Thinning", 0.72f); F(m, "_AO", 0.3f);
                F(m, "_Curl", 1.6f); F(m, "_Underfur", 0.7f); F(m, "_ClumpAmount", 0.6f);
                C(m, "_RimColor", "#E2CCFF"); F(m, "_Glow", 0.1f);
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
