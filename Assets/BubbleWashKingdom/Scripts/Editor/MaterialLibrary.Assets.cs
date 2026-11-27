using UnityEditor;
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
            // Screen S2 pass 2 (judge gap #6 "rails pink-orange; reference saturated glossy hot pink + rainbow"): the wide
            // amber middle band (#FFB357) read orange -> golden yellow stripe, saturated hot pink outer bands (hue ~330 so
            // the violet tunnel light lands on the reference ~325), stronger racing rainbow streaks + clear coat.
            Mat("M_RailBand_r8", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF4FAE"); C(m, "_ColorB", "#FFD25E"); C(m, "_ColorC", "#FF3D9E");
                F(m, "_Smoothness", 0.96f); F(m, "_Metallic", 0f); F(m, "_Glow", 0.3f);
                F(m, "_RimPower", 3f); F(m, "_RimStrength", 0.35f);
                F(m, "_StreakAmount", 1.25f); F(m, "_StreakSpeed", 7f);      // racing rainbow reflections (pink / yellow / cyan)
                F(m, "_ReflectBoost", 1.0f);                                   // clear-coat probe reflection (baked probes)
            });
            Mat("M_RailTube_r8", "BWK/Soft", m =>
            {
                // hot pink tube with a pale glossy crest on the channel side and a deep hot pink back
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF4FAE"); C(m, "_ColorB", "#FFE0F0"); C(m, "_ColorC", "#FF3A9C");
                F(m, "_Smoothness", 0.97f); F(m, "_Metallic", 0f); F(m, "_Glow", 0.32f);
                F(m, "_RimPower", 2.6f); F(m, "_RimStrength", 0.45f);
                F(m, "_StreakAmount", 0.7f); F(m, "_StreakSpeed", 7f); F(m, "_ReflectBoost", 1.1f);
            });

            // ---------------------------------------------------------------- S2 door machinery (pass 2)
            // SM_DoorMachine_s2 (build_door_machinery_s2.py): reference f_03.00s crop left of the hatch (0,150)-(250,300)
            // mean #6F6177, blue 50 %: a DARK blue machine housing with lighter steel-blue panels; the hall light is blue-
            // violet, so the paint stays navy (not lavender) with a clear-coat gloss; small self-light keeps it off black.
            Mat("M_DoorMachineBlue_s2", "Universal Render Pipeline/Lit", m =>
            {
                C(m, "_BaseColor", "#2A3A96"); F(m, "_Metallic", 0.25f); F(m, "_Smoothness", 0.72f);
                m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                C(m, "_EmissionColor", "#101A52");
            });
            Mat("M_DoorMachinePanel_s2", "Universal Render Pipeline/Lit", m =>
            {
                C(m, "_BaseColor", "#6C8CE8"); F(m, "_Metallic", 0.3f); F(m, "_Smoothness", 0.66f);
                m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                C(m, "_EmissionColor", "#1E2C6E");
            });
            Mat("M_DoorMachineVent_s2", "Universal Render Pipeline/Lit", m =>
            {
                C(m, "_BaseColor", "#121838"); F(m, "_Metallic", 0.1f); F(m, "_Smoothness", 0.5f);
                m.DisableKeyword("_EMISSION");
            });

            // ---------------------------------------------------------------- 02 striped fluffy washing roller
            // SM_BrushRoller_r8 (build_hall_assets.py): smooth rounded band body + 8 coincident fur shells (UV1.x = shell
            // fraction, UV1.y = 1), band colour in the vertex colour (linear pink / white / cyan), alpha 1 = "coat" path of
            // BWK/Fur. White-ish albedo ramps so the vertex colour sets the hue; dark lilac roots give the tuft depth.
            // r8 v2: v1 rendered 93 % blue-violet (roller crop of 01_hall_start; ref f_00.50s pink 33 % / cyan 6.7 % / white
            // 7.5 %). Pixel solve on the v1 bands (pink band rendered lin .16/.03/.44, white band .07/.10/.60): the hall light
            // reaching the roller is almost pure blue (~.03/.04/.75 + glow), so no albedo can make pink from it. Fix = more
            // colour-true self light (glow .6, the only R/G source) + a cream ramp (lin 1/1/.57) that takes the surplus blue
            // out of every band: predicted pink #D05EA4 / white #D0C7DD / cyan #63A9D9 vs ref #C35FA2 / #E2D1E9 / #6CB0D2.
            Mat("M_RollerFur_r8", "BWK/Fur", m =>
            {
                C(m, "_RootColor", "#E1E1AF"); C(m, "_BaseColor", "#FFFFC6"); C(m, "_TipColor", "#FFFFD2");
                F(m, "_UseVertexTint", 1f); F(m, "_StaticMode", 0f);
                F(m, "_Density", 30f); F(m, "_FurLength", 0.30f); F(m, "_Gravity", 0f); F(m, "_Thinning", 0.85f);
                F(m, "_ClumpAmount", 0.5f); F(m, "_ClumpScale", 4f); F(m, "_AO", 0.35f); F(m, "_Curl", 0.45f);
                F(m, "_Underfur", 0.85f); F(m, "_EdgeSoft", 0.22f); F(m, "_SilhouetteFade", 0.5f);
                F(m, "_TuftScale", 7f); F(m, "_TuftAmount", 0.55f);           // ~14 cm soft rounded tufts (reference)
                F(m, "_Wrap", 0.65f); C(m, "_RimColor", "#FFF4E6"); F(m, "_RimPower", 2.4f); F(m, "_RimStrength", 0.3f);
                F(m, "_Glow", 0.6f);
            }, (int)RenderQueue.AlphaTest);

            // ---------------------------------------------------------------- 01 pink laundry console (r8 v2)
            // v1 still: the console body rendered deep violet #5A28B0 (ref f_00.50s console crop pink 25.6 % #CF64A1, ours
            // 0.9 %): M_HallPink_r7's emission keyword is not saved (m_ValidKeywords empty), so URP Lit pink x the blue hall
            // light = violet. Console-only copy on BWK/Soft mode 1 (uniform candy plastic, clear-coat probe reflection,
            // colour-true glow; the glow is a property, not a keyword): albedo lin .95/.20/.32 x (light + .6) ~ #CB63AE.
            Mat("M_ConsolePink_r8", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#F97C99"); C(m, "_ColorB", "#F97C99"); C(m, "_ColorC", "#F97C99");
                F(m, "_Smoothness", 0.9f); F(m, "_Metallic", 0f); F(m, "_Glow", 0.6f);
                F(m, "_RimPower", 3f); F(m, "_RimStrength", 0.3f);
                F(m, "_StreakAmount", 0f); F(m, "_ReflectBoost", 0.6f);
            });
            // ---------------------------------------------------------------- 12 colourful socks (r8 v2)
            // rear still 07 (v1): the chamber socks read pale blue-grey - M_Fabric (white, glow .12) x the blue tunnel light,
            // the same loss as the roller. Sock-only copy (remapped in BuildPortholes): cream tint takes the surplus blue out,
            // colour-true glow keeps the vertex-colour stripes saturated (reference 8.25-11 s: red / yellow / blue / green).
            Mat("M_Sock_r8", "BWK/Soft", m =>
            {
                F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFC6"); F(m, "_Smoothness", 0.2f); F(m, "_Glow", 0.5f); F(m, "_BumpScale", 2f);
            });

            // ---------------------------------------------------------------- 11 + 12 MASTER washing-machine door (r8 masters)
            // SM_WashDoor_Master (build_master_door.py, prefab PF_WashDoor_Master): the 7 raised rainbow arches + the turquoise
            // water pool carry LINEAR vertex colours under ONE glossy candy material (mode 4 = albedo x vertex colour through
            // BWK_PBR: smoothness .9 = sharp highlights + baked probe reflections). Cream tint + colour-true glow keep the bands
            // from going violet under the blue tunnel light (the loss measured on the r8 socks / roller).
            Mat("M_DoorRainbow_r8", "BWK/Soft", m =>
            {
                // preview 1 (glow .45): bands rendered olive / teal-dark under the violet tunnel light (rear still 07) while the
                // reference rainbow chamber is luminous -> colour-true self light .75 (the bands ARE the chamber's light)
                F(m, "_Mode", 4); C(m, "_ColorA", "#FFF6E0"); F(m, "_Smoothness", 0.88f); F(m, "_Metallic", 0f);
                F(m, "_Glow", 0.75f); F(m, "_BumpScale", 0.5f); F(m, "_RimPower", 3f); F(m, "_RimStrength", 0.25f);
            });
            // door socks = material VARIANT of the sock master M_Sock_r8 (overrides tint / glow only)
            var sockMaster = AssetDatabase.LoadAssetAtPath<Material>($"{Dir}/M_Sock_r8.mat");
            Mat("M_DoorSock_r8", "BWK/Soft", m =>
            {
                try { if (sockMaster != null && m.parent != sockMaster) m.parent = sockMaster; }
                catch (System.Exception e) { Debug.LogWarning("[BWK] M_DoorSock_r8 variant: " + e.Message); }
                F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFD8"); F(m, "_Smoothness", 0.25f); F(m, "_Glow", 0.5f); F(m, "_BumpScale", 2f);
            });

            // ---------------------------------------------------------------- 24 golden starburst geometry (r8 v2)
            // SM_Starburst_r8 (build_hall_assets.py): additive soft quads for BWK/LightBlob (radial UV falloff): 132 thin rays
            // that fade outward, 42 soft 4-point sparkles, an amber halo and a small CREAM core (reference f_14.50s: warm
            // amber-gold glow, many thin soft rays, cream not white centre). Blue stays low in every colour, so overlaps sum
            // to amber / cream instead of clipping white; moderate strengths (no blanket bloom). Metal keeps M_PortalCore.
            void Burst(string name, string hex, float strength, float core) => Mat(name, "BWK/LightBlob", m =>
            {
                C(m, "_Color", hex); F(m, "_Strength", strength); F(m, "_Softness", 1f); F(m, "_Core", core);
                F(m, "_Mode", 1f); F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One);
                F(m, "_NearFade", 0f);
            }, (int)RenderQueue.Transparent - 9);
            // v2 build (10_finale bg, portal crop 360-920 x 0-560): gold 14.1 % vs ref 21.8 % (v1 hard lemon 25.3 %), the ring
            // interior stayed bare violet (#674799 at 700,200; ref haze #F4E6A4) -> golden haze + rays stronger and yellower,
            // cream core weaker (the centre already reads cream #FDE9C2 with the metal's Core disc)
            Burst("M_BurstRays_r8", "#FFB040", 2.2f, 1.2f);
            Burst("M_BurstSparkle_r8", "#FFC860", 2.0f, 1.2f);
            Burst("M_BurstGlow_r8", "#FFD27A", 1.15f, 1.15f);
            Burst("M_BurstCore_r8", "#FFD58A", 0.6f, 1.5f);

            // the screen read as a pale grey-white card (M_Screen emissive #5E8FC7 x 1.6); reference = deep blue glass behind
            // the cyan neon T-shirt (the icon keeps M_Neon_Cyan)
            Mat("M_ConsoleScreen_r8", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#1E5A8C"); C(m, "_ColorB", "#1E5A8C"); C(m, "_ColorC", "#1E5A8C");
                F(m, "_Smoothness", 0.96f); F(m, "_Metallic", 0f); F(m, "_Glow", 0.5f);
                F(m, "_RimPower", 4f); F(m, "_RimStrength", 0.2f);
                F(m, "_StreakAmount", 0f); F(m, "_ReflectBoost", 0.8f);
            });
        }
    }
}
