using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: asset artist (round 8, 2026-11-26) - materials of the improved EXISTING props (official asset library
    // Reference/asset_library: 15 slide rails, 02 roller fur, ...). Only this domain's agent edits this file.
    // Called from MaterialLibrary.Run() after the other domains, so it may copy their settings.
    public static partial class MaterialLibrary
    {
        static void AssetMaterials()
        {
            // ---------------------------------------------------------------- 15 glossy multicoloured slide rails
            // SM_Slide_Module slots (build_track.py r8): 1 = bank between the water line (UV.x 0) and the rail tube (UV.x 1),
            // 2 = the rail tube (UV.x around the tube from the hidden seam; 0.5 = the side facing the channel / camera).
            // Measured (hero f_03.00s + f_00.50s banks): reference candy pink hue 321-327 deg (ours r7w 302-305 = magenta-
            // violet), amber layers 8.6-22 % of the bank pixels (ours 0-4 %), white glints 11-22 % (ours 8-11 %). The tunnel
            // light is violet, so the albedo sits warmer (hue ~334) than the rendered target; amber = the warm layer the
            // library describes ("layered pink, magenta, amber and iridescent bands; strong elongated reflections").
            Mat("M_RailBand_r8", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF8EC0"); C(m, "_ColorB", "#FFB357"); C(m, "_ColorC", "#FF62AA");
                F(m, "_Smoothness", 0.95f); F(m, "_Metallic", 0f); F(m, "_Glow", 0.24f);
                F(m, "_RimPower", 3f); F(m, "_RimStrength", 0.3f);
                F(m, "_StreakAmount", 0.9f); F(m, "_StreakSpeed", 7f);       // warm racing reflections, fewer white lines
                F(m, "_ReflectBoost", 0.9f);                                   // clear-coat probe reflection (baked probes)
            });
            Mat("M_RailTube_r8", "BWK/Soft", m =>
            {
                // candy pink tube with a pale glossy crest on the channel side and a hot pink back
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF79B4"); C(m, "_ColorB", "#FFDCEB"); C(m, "_ColorC", "#FF5CA6");
                F(m, "_Smoothness", 0.96f); F(m, "_Metallic", 0f); F(m, "_Glow", 0.28f);
                F(m, "_RimPower", 2.6f); F(m, "_RimStrength", 0.4f);
                F(m, "_StreakAmount", 0.5f); F(m, "_StreakSpeed", 7f); F(m, "_ReflectBoost", 1.0f);
            });

            // ---------------------------------------------------------------- 02 striped fluffy washing roller
            // SM_BrushRoller_r8 (build_hall_assets.py): smooth rounded band body + 8 coincident fur shells (UV1.x = shell
            // fraction, UV1.y = 1), band colour in the vertex colour (linear pink / white / cyan), alpha 1 = "coat" path of
            // BWK/Fur. White-ish albedo ramps so the vertex colour sets the hue; dark lilac roots give the tuft depth.
            Mat("M_RollerFur_r8", "BWK/Fur", m =>
            {
                C(m, "_RootColor", "#B3A0C6"); C(m, "_BaseColor", "#F6F0F8"); C(m, "_TipColor", "#FFFFFF");
                F(m, "_UseVertexTint", 1f); F(m, "_StaticMode", 0f);
                F(m, "_Density", 30f); F(m, "_FurLength", 0.30f); F(m, "_Gravity", 0f); F(m, "_Thinning", 0.85f);
                F(m, "_ClumpAmount", 0.5f); F(m, "_ClumpScale", 4f); F(m, "_AO", 0.45f); F(m, "_Curl", 0.45f);
                F(m, "_Underfur", 0.85f); F(m, "_EdgeSoft", 0.22f); F(m, "_SilhouetteFade", 0.5f);
                F(m, "_TuftScale", 7f); F(m, "_TuftAmount", 0.55f);           // ~14 cm soft rounded tufts (reference)
                F(m, "_Wrap", 0.65f); C(m, "_RimColor", "#FFFFFF"); F(m, "_RimPower", 2.4f); F(m, "_RimStrength", 0.45f);
                F(m, "_Glow", 0.16f);
            }, (int)RenderQueue.AlphaTest);
        }
    }
}
