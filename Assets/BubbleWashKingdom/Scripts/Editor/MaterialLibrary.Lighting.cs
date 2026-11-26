using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: Agent 4 - lighting & visual quality (polished gold, coins, gems, marquee bulbs, neon stars).
    // Only this domain's agent edits this file. Helpers (Mat, Lit_, Gold, Emissive, Soft, Particle, C, F, Get) live in MaterialLibrary.cs.
    public static partial class MaterialLibrary
    {
        static void LightingMaterials()
        {
            // polished gold: stylised procedural-environment shader (bright yellow from every angle, like the reference)
            Gold("M_Gold", "#FFF4C8", "#F6B532", "#8A4A0C", 1.0f, 0.12f);
            Gold("M_GoldDark", "#FFD98A", "#D48A1E", "#5E2E06", 0.85f, 0.06f);
            Gold("M_Coin", "#FFF8D2", "#FFC93A", "#A8600E", 1.12f, 0.22f);
            Emissive("M_Bulb", "#FF9A18", 4.6f, chase: 1f, core: 0.2f, fog: 0.06f, halo: 0.8f);
            Emissive("M_Neon", "#12D3F5", 1.8f, core: 0.1f, fog: 0.12f);
            Emissive("M_Neon_Cyan", "#12D3F5", 1.8f, core: 0.1f, fog: 0.12f);
            Emissive("M_Neon_Pink", "#FF35C0", 1.8f, core: 0.1f, fog: 0.12f);
            Emissive("M_Neon_Yellow", "#FFD21F", 1.7f, core: 0.1f, fog: 0.12f);
            Lit_("M_Gem", "#C42BE0", metallic: 0.15f, smooth: 0.96f, emission: "#6A0F80");
        }
    }
}
