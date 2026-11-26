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
                F(m, "_Mode", 2); C(m, "_ColorA", "#6A36A6"); C(m, "_ColorB", "#EDE6FF"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 72); F(m, "_StitchV", 55); F(m, "_BumpStrength", 0.75f); F(m, "_Smoothness", 0.16f); F(m, "_Glow", 0.06f);
            });
            Mat("M_HatCuff", "BWK/Character", m =>
            {
                // tall folded cuff: CUFF_RIBS = 96 deep geometric ribs
                F(m, "_Mode", 2); C(m, "_ColorA", "#62329A"); C(m, "_ColorB", "#62329A"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 96); F(m, "_StitchV", 60); F(m, "_BumpStrength", 0.85f); F(m, "_Smoothness", 0.14f); F(m, "_Glow", 0.05f);
            });
            Mat("M_HatStripe", "BWK/Character", m =>
            {
                // pale pink-lavender ribbed band above the cuff (same 72 ribs as the dome)
                F(m, "_Mode", 2); C(m, "_ColorA", "#EED8EE"); C(m, "_ColorB", "#EED8EE"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 72); F(m, "_StitchV", 55); F(m, "_BumpStrength", 0.7f); F(m, "_Smoothness", 0.18f); F(m, "_Glow", 0.08f);
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
                // warm plush pink (slightly salmon; the tunnel's violet light adds blue): light roots, soft pale tips.
                // Strand cells are square (the shader doubles UV.x); fine dense guard hairs + thick underfur = plush.
                C(m, "_RootColor", "#C46C78"); C(m, "_BaseColor", "#E8888E"); C(m, "_TipColor", "#FAC4C0");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 210); F(m, "_FurLength", 0.034f); F(m, "_Gravity", 0.008f); F(m, "_Thinning", 0.62f); F(m, "_ClumpAmount", 0.7f); F(m, "_ClumpScale", 9f);
                F(m, "_AO", 0.12f); F(m, "_Curl", 1.6f); F(m, "_Underfur", 0.75f);
                C(m, "_RimColor", "#FFDCD8"); F(m, "_Glow", 0.12f); F(m, "_RimStrength", 0.7f);
            }, (int)RenderQueue.AlphaTest);
            Mat("M_PomPom", "BWK/Fur", m =>
            {
                // dense soft yarn pom-pom: short, very dense, little thinning so the silhouette stays round and soft
                C(m, "_RootColor", "#3C2470"); C(m, "_BaseColor", "#6A3EA6"); C(m, "_TipColor", "#A07ED2");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 150); F(m, "_FurLength", 0.028f); F(m, "_Gravity", 0.002f); F(m, "_Thinning", 0.5f); F(m, "_AO", 0.35f);
                F(m, "_Curl", 1.8f); F(m, "_Underfur", 0.9f); F(m, "_ClumpAmount", 0.5f);
                C(m, "_RimColor", "#D9C4F5"); F(m, "_Glow", 0.06f); F(m, "_RimStrength", 0.6f);
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
