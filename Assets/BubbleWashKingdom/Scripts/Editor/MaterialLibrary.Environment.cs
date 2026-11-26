using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: Agent 3 - 3D environment & machinery (drum walls, glass pipes, pipe water, chambers, rollers, machinery, laundry, portal rays).
    // Only this domain's agent edits this file. Helpers (Mat, Lit_, Gold, Emissive, Soft, Particle, C, F, Get) live in MaterialLibrary.cs.
    public static partial class MaterialLibrary
    {
        static void EnvironmentMaterials()
        {
            Mat("M_DrumWall", "BWK/DrumWall", m =>
            {
                // reference f_003.00s / key 5.0 s: deep saturated violet drum sections between the rims, rows of large
                // dark oval slots elongated around the drum, darker values around the holes and next to the rims, a few
                // holes lit from behind, grooves + seams, sparkles. Albedo is kept deep because the tunnel post / lights
                // lift it a lot (r2: the pale lavender read was the main wall gap).
                // _BandOffset / _BandLength are rewritten by SceneBuilder.BuildRings to match the placed rims.
                C(m, "_BaseColor", "#5B44A6"); C(m, "_HighlightColor", "#8D75D8"); C(m, "_HoleColor", "#0B0620");
                C(m, "_HoleGlow", "#4A2E9A"); F(m, "_Circumference", 26.39f); F(m, "_VTile", 4f);
                F(m, "_Pattern", 1f); F(m, "_BandLength", 8.5f / 3f); F(m, "_BandOffset", 65f);
                F(m, "_PlainBack", 0.42f); F(m, "_PlainFront", 0.36f); F(m, "_Rows", 3f); F(m, "_SlotPitch", 0.62f);
                F(m, "_SlotLength", 0.42f); F(m, "_SlotWidth", 0.17f); F(m, "_SlotVariation", 0.35f); F(m, "_LipWidth", 0.04f);
                F(m, "_Bevel", 0.7f); F(m, "_GlowChance", 0.05f);
                m.SetColor("_GlowColorA", new Color(1.7f, 0.85f, 1.6f)); m.SetColor("_GlowColorB", new Color(0.75f, 1.35f, 1.9f));
                C(m, "_SeamColor", "#2A1858"); C(m, "_SheenColor", "#B9A2F2"); F(m, "_SheenStrength", 0.28f);
                F(m, "_Sparkle", 0.8f); F(m, "_CeilingLight", 0.15f); F(m, "_Glow", 0.08f);
                F(m, "_Metallic", 0.7f); F(m, "_Smoothness", 0.8f); F(m, "_HoleBand", 1f);
                F(m, "_EdgeAO", 0.45f); F(m, "_EdgeAOWidth", 0.5f); F(m, "_HoleAO", 0.45f); F(m, "_HoleAOWidth", 0.08f);
            });
            // polished lavender drum lips between the gold rings (SM_DrumRim): the stylised BWK/Gold environment shading
            // with a lavender palette (pink-white highlights, deep violet undersides) - glossy metal that never goes dark
            Mat("M_DrumRim", "BWK/Gold", m =>
            {
                C(m, "_HighColor", "#F4E6FF"); C(m, "_MidColor", "#8E72DA"); C(m, "_LowColor", "#2E1A70");
                C(m, "_RimColor", "#F3A8EC"); C(m, "_BandColor", "#D8C6FF");
                F(m, "_Brightness", 1.0f); F(m, "_Emission", 0.08f); F(m, "_Contrast", 1.4f); F(m, "_ViewGradient", 1f);
                F(m, "_EnvReflect", 0.5f); F(m, "_EnvTint", 0.4f); F(m, "_EnvRoughness", 0.25f);
                F(m, "_SpecPower", 90f); F(m, "_SpecStrength", 1.6f); F(m, "_GlintStrength", 1.2f);
                F(m, "_Sparkle", 0.6f); F(m, "_SparkleScale", 16f); F(m, "_FogAmount", 0.75f);
                F(m, "_HighlightSize", 8f); F(m, "_BandSharpness", 18f); F(m, "_LightInfluence", 0.35f);
            });
            // small white-lavender LED studs along the drum lips (reference: sparkling dots on the lavender rims)
            Mat("M_RimLight", "BWK/Emissive", m =>
            {
                C(m, "_Color", "#E9D8FF"); F(m, "_Intensity", 3.2f); F(m, "_CoreWhite", 0.8f); F(m, "_CorePower", 3f);
                F(m, "_HaloBoost", 0.4f); F(m, "_EdgeSaturate", 0.2f); F(m, "_Chase", 0f); F(m, "_PulseAmount", 0.2f);
                F(m, "_PulseSpeed", 0.8f); F(m, "_FogAmount", 0.25f);
            });
            // inside the side chamber windows: bright silver-lavender washing drum with small round perforations
            Mat("M_ChamberDrum", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#B6A6EA"); C(m, "_HighlightColor", "#E8DFFF"); C(m, "_HoleColor", "#2A1A55");
                C(m, "_HoleGlow", "#B48CFF"); F(m, "_Pattern", 0f); F(m, "_Circumference", 26.4f); F(m, "_VTile", 4f);
                F(m, "_HoleSpacing", 0.22f); F(m, "_HoleRadius", 0.22f); F(m, "_HoleStretch", 1f); F(m, "_PanelLength", 1000f);
                F(m, "_Glow", 0.28f); F(m, "_Metallic", 0.55f); F(m, "_Smoothness", 0.8f); F(m, "_HoleBand", 1f);
                F(m, "_SheenStrength", 0.25f); F(m, "_Sparkle", 0.4f);
            });
            Mat("M_DrumWallHall", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#9A86D6"); C(m, "_HighlightColor", "#BDB3E8"); C(m, "_HoleColor", "#2A1450");
                C(m, "_HoleGlow", "#A070FF"); F(m, "_Circumference", 84.4f); F(m, "_HoleSpacing", 0.9f);
                F(m, "_HoleRadius", 0.24f); F(m, "_Glow", 0.22f);
            });
            Mat("M_DrumWallFlat", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#9A86D6"); C(m, "_HighlightColor", "#BDB3E8"); C(m, "_HoleColor", "#2A1450");
                C(m, "_HoleGlow", "#A070FF"); F(m, "_Circumference", 4f); F(m, "_VTile", 4f); F(m, "_HoleSpacing", 0.8f);
                F(m, "_HoleRadius", 0.25f); F(m, "_Glow", 0.2f); F(m, "_PanelLength", 1000f);
            });
            Emissive("M_Screen", "#5E8FC7", 1.6f, pulse: 0.05f);
            Emissive("M_ButtonCyan", "#3FF0FF", 2.2f);
            Emissive("M_ButtonYellow", "#F4D82B", 2.2f);
            Emissive("M_ButtonPink", "#FF5FD0", 2.2f);
            Mat("M_Glass", "BWK/Glass", m => { C(m, "_Tint", "#B9D8FF"); F(m, "_Alpha", 0.06f); F(m, "_Glow", 0.06f); }, (int)RenderQueue.Transparent);
            Mat("M_PipeWater", "BWK/FlowGlow", m => { F(m, "_Mode", 0); C(m, "_ColorA", "#1FD2FF"); C(m, "_ColorB", "#FF3FC8"); F(m, "_Intensity", 1.6f); F(m, "_Speed", 1.2f); });
            // glowing pink liquid in the glass risers beside the side chambers (reference key 7.5 s)
            Mat("M_PipeWaterPink", "BWK/FlowGlow", m => { F(m, "_Mode", 0); C(m, "_ColorA", "#FF3FB8"); C(m, "_ColorB", "#FFB3EE"); F(m, "_Intensity", 1.7f); F(m, "_Speed", 0.9f); F(m, "_Scale", 2.5f); });
            Mat("M_ChamberSwirl", "BWK/FlowGlow", m => { F(m, "_Mode", 1); C(m, "_ColorA", "#9FE8FF"); F(m, "_Intensity", 1.15f); F(m, "_Speed", 1f); });
            Mat("M_PortalRays", "BWK/FlowGlow", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#FFF6D8"); C(m, "_ColorB", "#FFB43A"); F(m, "_Intensity", 2.4f); F(m, "_Speed", 1f);
                F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One); F(m, "_ZWrite", 0); F(m, "_RayCount", 18);
            }, (int)RenderQueue.Transparent + 10);
            Soft("M_BrushPink", "#E463B1", "#FFB6E1");
            Soft("M_BrushBlue", "#6FD3FF", "#B4ECFF");
            Soft("M_BrushWhite", "#FFF6FF", "#FFFFFF");
            Lit_("M_MachinePink", "#E84AA3", metallic: 0.05f, smooth: 0.78f, emission: "#2A0A1E");
            Lit_("M_MachineLavender", "#D79AD8", metallic: 0.05f, smooth: 0.75f, emission: "#1E1430");
            Lit_("M_PlasticWhite", "#F6F1FF", metallic: 0f, smooth: 0.8f, emission: "#1A181F");
            Lit_("M_MetalPurple", "#6C3FC4", metallic: 0.85f, smooth: 0.75f);
            Mat("M_Fabric", "BWK/Soft", m => { F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFFF"); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.12f); F(m, "_BumpScale", 2f); });
        }
    }
}
