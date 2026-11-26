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
                // reference 3.75-15 s: larger, sparser round perforations (~25 cm) in a violet-blue metallic drum
                C(m, "_BaseColor", "#7A5CC9"); C(m, "_HighlightColor", "#B7A6F2"); C(m, "_HoleColor", "#140C2C");
                C(m, "_HoleGlow", "#5B3FA0"); F(m, "_Circumference", 26.4f); F(m, "_HoleSpacing", 0.6f);
                F(m, "_HoleRadius", 0.19f); F(m, "_HoleStretch", 1.75f); F(m, "_Glow", 0.16f); F(m, "_Smoothness", 0.8f);
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
            Mat("M_ChamberSwirl", "BWK/FlowGlow", m => { F(m, "_Mode", 1); C(m, "_ColorA", "#9FE8FF"); F(m, "_Intensity", 1.35f); F(m, "_Speed", 1f); });
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
