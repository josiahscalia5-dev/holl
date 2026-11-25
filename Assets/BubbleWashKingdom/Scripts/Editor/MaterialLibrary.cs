using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Creates/updates every project material. Names match the Blender material slots (M_*) so imported FBX
    /// materials remap to these automatically. Colours follow the approved reference (Reference/VISUAL_ANALYSIS.md).
    /// </summary>
    public static class MaterialLibrary
    {
        public const string Dir = "Assets/BubbleWashKingdom/Art/Materials";
        const string Tex = "Assets/BubbleWashKingdom/Art/Textures";

        static Shader Lit => Shader.Find("Universal Render Pipeline/Lit");
        static Shader ParticlesUnlit => Shader.Find("Universal Render Pipeline/Particles/Unlit");

        [MenuItem("Bubble Wash/Setup/3 Build Materials")]
        public static void Run()
        {
            Directory.CreateDirectory(Dir);

            // ---------------- slide and water
            Mat("M_Water", "BWK/Water", m =>
            {
                C(m, "_DeepColor", "#1F7BC1"); C(m, "_ShallowColor", "#3FB3E0"); C(m, "_StreakColor", "#C2EFFC");
                C(m, "_EdgeTint", "#B386CD"); F(m, "_FlowSpeed", 7.5f); F(m, "_Width", 3.6f); F(m, "_Glow", 0.34f); F(m, "_Smoothness", 0.82f); F(m, "_StreakAmount", 0.45f); F(m, "_EdgeTintAmount", 0.3f);
            });
            Mat("M_RailRainbow", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#97A1D2"); C(m, "_ColorB", "#D56FC7"); C(m, "_ColorC", "#E062A8");
                F(m, "_Smoothness", 0.9f); F(m, "_Glow", 0.48f); F(m, "_RimStrength", 0.25f);
            });
            Mat("M_RailPink", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#EC8CA4"); C(m, "_ColorB", "#FDFED5"); C(m, "_ColorC", "#F3AE7D");
                F(m, "_Smoothness", 0.94f); F(m, "_Glow", 0.5f); F(m, "_RimStrength", 0.35f);
            });
            Lit_("M_SlideShell", "#E24AB8", metallic: 0.05f, smooth: 0.85f, emission: "#3A0A30");

            // ---------------- drum, gold, lights
            Mat("M_DrumWall", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#7954B4"); C(m, "_HighlightColor", "#9390D2"); C(m, "_HoleColor", "#1A2235");
                C(m, "_HoleGlow", "#4E4683"); F(m, "_Circumference", 26.4f); F(m, "_HoleSpacing", 0.42f);
                F(m, "_HoleRadius", 0.27f); F(m, "_Glow", 0.14f);
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
            Lit_("M_Gold", "#F0B85A", metallic: 1f, smooth: 0.9f, emission: "#5A3A10");
            Lit_("M_GoldDark", "#B77D4B", metallic: 1f, smooth: 0.72f, emission: "#1E1000");
            Lit_("M_Coin", "#F5D45A", metallic: 1f, smooth: 0.88f, emission: "#7A5A00");
            Emissive("M_Bulb", "#FFE9A0", 8f, chase: 1f, core: 0.7f);
            Emissive("M_Neon", "#45D5E5", 4.2f);
            Emissive("M_Neon_Cyan", "#45D5E5", 4.2f);
            Emissive("M_Neon_Pink", "#E070D0", 4.2f);
            Emissive("M_Neon_Yellow", "#F8DC6A", 4.0f);
            Emissive("M_EyeHighlight", "#FFFFFF", 1.6f, pulse: 0f, core: 0f);
            Emissive("M_ArrowRim", "#F2FFFF", 2.5f, pulse: 0f);
            Emissive("M_Screen", "#5E8FC7", 1.6f, pulse: 0.05f);
            Emissive("M_ButtonCyan", "#3FF0FF", 2.2f);
            Emissive("M_ButtonYellow", "#F4D82B", 2.2f);
            Emissive("M_ButtonPink", "#FF5FD0", 2.2f);

            // ---------------- glass, liquids, swirl, arrows, portal
            Mat("M_Glass", "BWK/Glass", m => { C(m, "_Tint", "#A5C6E7"); F(m, "_Alpha", 0.1f); F(m, "_Glow", 0.2f); }, (int)RenderQueue.Transparent);
            Mat("M_Bubble", "BWK/Glass", m => { C(m, "_Tint", "#FFFFFF"); F(m, "_Alpha", 0.03f); F(m, "_Iridescence", 1f); F(m, "_FresnelPower", 2.2f); F(m, "_Glow", 0.35f); }, (int)RenderQueue.Transparent);
            Mat("M_PipeWater", "BWK/FlowGlow", m => { F(m, "_Mode", 0); C(m, "_ColorA", "#6CCBDF"); C(m, "_ColorB", "#A943A6"); F(m, "_Intensity", 1.8f); F(m, "_Speed", 1.2f); });
            Mat("M_ChamberSwirl", "BWK/FlowGlow", m => { F(m, "_Mode", 1); C(m, "_ColorA", "#9FE8FF"); F(m, "_Intensity", 1.35f); F(m, "_Speed", 1f); });
            Mat("M_Arrow", "BWK/FlowGlow", m => { F(m, "_Mode", 2); C(m, "_ColorA", "#22EEFF"); F(m, "_Intensity", 2.6f); F(m, "_Speed", 1.4f); });
            Mat("M_PortalRays", "BWK/FlowGlow", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#FFF6D8"); C(m, "_ColorB", "#FFB43A"); F(m, "_Intensity", 2.4f); F(m, "_Speed", 1f);
                F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One); F(m, "_ZWrite", 0); F(m, "_RayCount", 18);
            }, (int)RenderQueue.Transparent + 10);

            // ---------------- soft materials
            Mat("M_Foam", "BWK/Soft", m =>
            {
                F(m, "_Mode", 0); C(m, "_ColorA", "#FFFFFF"); C(m, "_ShadowColor", "#C9BFE6"); F(m, "_Wrap", 0.65f);
                F(m, "_BumpScale", 3.5f); F(m, "_BumpStrength", 0.35f); F(m, "_Glow", 0.12f); F(m, "_RimStrength", 0.3f);
            });
            Soft("M_BrushPink", "#E463B1", "#FFB6E1");
            Soft("M_BrushBlue", "#6FD3FF", "#B4ECFF");
            Soft("M_BrushWhite", "#FFF6FF", "#FFFFFF");
            Mat("M_HatKnit", "BWK/Soft", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#6C2EA0"); C(m, "_ColorB", "#CDB2F5"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 70); F(m, "_StitchV", 22); F(m, "_BumpStrength", 0.55f); F(m, "_Smoothness", 0.2f); F(m, "_Glow", 0.08f);
            });
            Mat("M_HatCuff", "BWK/Soft", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#5E2A94"); C(m, "_ColorB", "#5E2A94"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 96); F(m, "_StitchV", 7); F(m, "_BumpStrength", 0.75f); F(m, "_Smoothness", 0.18f); F(m, "_Glow", 0.06f);
            });
            Mat("M_HatStripe", "BWK/Soft", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#E0B3D7"); C(m, "_ColorB", "#E0B3D7"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 70); F(m, "_StitchV", 22); F(m, "_BumpStrength", 0.5f); F(m, "_Smoothness", 0.2f); F(m, "_Glow", 0.1f);
            });
            Mat("M_EyeIris", "BWK/Soft", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#5A2E14"); C(m, "_ColorB", "#A8642A"); C(m, "_ColorC", "#120804");
                F(m, "_Glow", 0.05f); F(m, "_RimStrength", 0.1f);
            });
            Lit_("M_Mouth", "#4B0F1E", metallic: 0f, smooth: 0.6f);
            Lit_("M_Tongue", "#FF6F93", metallic: 0f, smooth: 0.55f, emission: "#300812");
            Lit_("M_PawPad", "#F2F4FF", metallic: 0f, smooth: 0.35f, emission: "#2A1A20");
            Lit_("M_StarBadge", "#FFD43F", metallic: 0.1f, smooth: 0.6f, emission: "#7A4A00");
            Lit_("M_MachinePink", "#E84AA3", metallic: 0.05f, smooth: 0.78f, emission: "#2A0A1E");
            Lit_("M_MachineLavender", "#D79AD8", metallic: 0.05f, smooth: 0.75f, emission: "#1E1430");
            Lit_("M_PlasticWhite", "#F6F1FF", metallic: 0f, smooth: 0.8f, emission: "#1A181F");
            Lit_("M_MetalPurple", "#6C3FC4", metallic: 0.85f, smooth: 0.75f);
            Lit_("M_Gem", "#C42BE0", metallic: 0.15f, smooth: 0.96f, emission: "#6A0F80");
            Mat("M_Fabric", "BWK/Soft", m => { F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFFF"); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.12f); F(m, "_BumpScale", 2f); });

            // ---------------- fur
            var furNoise = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Tex}/T_FurNoise.png");
            Mat("M_Fur", "BWK/Fur", m =>
            {
                C(m, "_RootColor", "#8D486C"); C(m, "_BaseColor", "#D2678F"); C(m, "_TipColor", "#EC9FB9");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 42); F(m, "_FurLength", 0.05f); F(m, "_Gravity", 0.012f); F(m, "_Thinning", 1.05f);
                C(m, "_RimColor", "#FFD0E2"); F(m, "_Glow", 0.12f);
            }, (int)RenderQueue.AlphaTest);
            Mat("M_PomPom", "BWK/Fur", m =>
            {
                C(m, "_RootColor", "#4B2680"); C(m, "_BaseColor", "#793AAB"); C(m, "_TipColor", "#B45BDB");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 46); F(m, "_FurLength", 0.04f); F(m, "_Gravity", 0.006f); F(m, "_Thinning", 0.95f);
                C(m, "_RimColor", "#E2CCFF"); F(m, "_Glow", 0.1f);
            }, (int)RenderQueue.AlphaTest);

            // ---------------- particles
            Particle("M_FX_Splash", $"{Tex}/T_Splash.png", additive: false, "#FFFFFF");
            Particle("M_FX_Soft", $"{Tex}/T_SoftCircle.png", additive: false, "#FFFFFF");
            Particle("M_FX_Sparkle", $"{Tex}/T_Sparkle.png", additive: true, "#FFF2B0");
            Particle("M_FX_GemSparkle", $"{Tex}/T_Sparkle.png", additive: true, "#E7B8FF");
            Particle("M_FX_Bubble", $"{Tex}/T_Bubble.png", additive: false, "#FFFFFF");
            Particle("M_FX_Streak", $"{Tex}/T_Streak.png", additive: true, "#BFF6FF");

            AssetDatabase.SaveAssets();
            Debug.Log("[BWK] Materials built.");
        }

        // ------------------------------------------------------------------ helpers
        static Material Mat(string name, string shaderName, System.Action<Material> setup, int queue = -1)
        {
            var shader = Shader.Find(shaderName);
            if (shader == null) { Debug.LogError($"[BWK] Shader {shaderName} not found for {name}"); shader = Lit; }
            string path = $"{Dir}/{name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(shader) { name = name }; AssetDatabase.CreateAsset(m, path); }
            else if (m.shader != shader) m.shader = shader;
            setup?.Invoke(m);
            m.renderQueue = queue;
            m.enableInstancing = true;
            EditorUtility.SetDirty(m);
            return m;
        }

        static void Lit_(string name, string hex, float metallic, float smooth, string emission = null)
        {
            Mat(name, "Universal Render Pipeline/Lit", m =>
            {
                C(m, "_BaseColor", hex);
                F(m, "_Metallic", metallic);
                F(m, "_Smoothness", smooth);
                if (emission != null)
                {
                    m.EnableKeyword("_EMISSION");
                    m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                    C(m, "_EmissionColor", emission);
                }
                else m.DisableKeyword("_EMISSION");
            });
        }

        static void Emissive(string name, string hex, float intensity, float chase = 0f, float pulse = 0.12f, float core = 0.45f)
        {
            Mat(name, "BWK/Emissive", m =>
            {
                C(m, "_Color", hex); F(m, "_Intensity", intensity); F(m, "_Chase", chase); F(m, "_PulseAmount", pulse); F(m, "_CoreWhite", core);
            });
        }

        static void Soft(string name, string hex, string light)
        {
            Mat(name, "BWK/Soft", m =>
            {
                F(m, "_Mode", 0); C(m, "_ColorA", hex); C(m, "_ShadowColor", light); F(m, "_Wrap", 0.7f);
                F(m, "_BumpScale", 9f); F(m, "_BumpStrength", 0.6f); F(m, "_Glow", 0.12f); F(m, "_RimStrength", 0.35f);
            });
        }

        static void Particle(string name, string texPath, bool additive, string tint)
        {
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(texPath);
            var shader = ParticlesUnlit;
            string path = $"{Dir}/{name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(shader) { name = name }; AssetDatabase.CreateAsset(m, path); }
            m.shader = shader;
            m.SetTexture("_BaseMap", tex);
            C(m, "_BaseColor", tint);
            // URP particle surface setup: transparent, alpha or additive blending.
            m.SetFloat("_Surface", 1f);
            m.SetFloat("_Blend", additive ? 2f : 0f);
            m.SetOverrideTag("RenderType", "Transparent");
            m.SetInt("_SrcBlend", additive ? (int)BlendMode.SrcAlpha : (int)BlendMode.SrcAlpha);
            m.SetInt("_DstBlend", additive ? (int)BlendMode.One : (int)BlendMode.OneMinusSrcAlpha);
            m.SetInt("_ZWrite", 0);
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.renderQueue = (int)RenderQueue.Transparent;
            EditorUtility.SetDirty(m);
        }

        static void C(Material m, string prop, string hex)
        {
            if (!m.HasProperty(prop)) return;
            ColorUtility.TryParseHtmlString(hex, out var c);
            m.SetColor(prop, c);
        }

        static void F(Material m, string prop, float v)
        {
            if (m.HasProperty(prop)) m.SetFloat(prop, v);
        }

        public static Material Get(string name) => AssetDatabase.LoadAssetAtPath<Material>($"{Dir}/{name}.mat");
    }
}
