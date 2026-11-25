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
                C(m, "_DeepColor", "#1C6BFF"); C(m, "_ShallowColor", "#3FD9FF"); C(m, "_StreakColor", "#EEF9FF");
                C(m, "_EdgeTint", "#FF6BD6"); F(m, "_FlowSpeed", 7.5f); F(m, "_Width", 3.6f); F(m, "_Glow", 0.38f);
            });
            Mat("M_RailRainbow", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF4FB2"); C(m, "_ColorB", "#FF9A3C"); C(m, "_ColorC", "#FFE45A");
                F(m, "_Smoothness", 0.9f); F(m, "_Glow", 0.32f); F(m, "_RimStrength", 0.25f);
            });
            Mat("M_RailPink", "BWK/Soft", m =>
            {
                F(m, "_Mode", 1); C(m, "_ColorA", "#FF5CC0"); C(m, "_ColorB", "#FF8AD4"); C(m, "_ColorC", "#FF4FA8");
                F(m, "_Smoothness", 0.94f); F(m, "_Glow", 0.28f); F(m, "_RimStrength", 0.35f);
            });
            Lit_("M_SlideShell", "#E24AB8", metallic: 0.05f, smooth: 0.85f, emission: "#3A0A30");

            // ---------------- drum, gold, lights
            Mat("M_DrumWall", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#6B44C9"); C(m, "_HighlightColor", "#B593FF"); C(m, "_HoleColor", "#140828");
                C(m, "_HoleGlow", "#7A44E0"); F(m, "_Circumference", 26.4f); F(m, "_HoleSpacing", 0.42f);
                F(m, "_HoleRadius", 0.27f); F(m, "_Glow", 0.14f);
            });
            Mat("M_DrumWallHall", "BWK/DrumWall", m =>
            {
                C(m, "_BaseColor", "#8A63D8"); C(m, "_HighlightColor", "#D3B8FF"); C(m, "_HoleColor", "#2A1450");
                C(m, "_HoleGlow", "#A070FF"); F(m, "_Circumference", 90f); F(m, "_HoleSpacing", 0.9f);
                F(m, "_HoleRadius", 0.24f); F(m, "_Glow", 0.22f);
            });
            Lit_("M_Gold", "#FFC23B", metallic: 1f, smooth: 0.86f, emission: "#4A2C00");
            Lit_("M_GoldDark", "#C7861C", metallic: 1f, smooth: 0.72f, emission: "#1E1000");
            Lit_("M_Coin", "#FFC93F", metallic: 1f, smooth: 0.88f, emission: "#6A3E00");
            Emissive("M_Bulb", "#FFE3A0", 5.5f, chase: 1f, core: 0.7f);
            Emissive("M_Neon", "#38F2FF", 4.2f);
            Emissive("M_Neon_Cyan", "#38F2FF", 4.2f);
            Emissive("M_Neon_Pink", "#FF4FD8", 4.2f);
            Emissive("M_Neon_Yellow", "#FFE04A", 4.0f);
            Emissive("M_EyeHighlight", "#FFFFFF", 1.6f, pulse: 0f, core: 0f);
            Emissive("M_ArrowRim", "#F2FFFF", 2.5f, pulse: 0f);
            Emissive("M_Screen", "#8FEAFF", 1.8f, pulse: 0.05f);
            Emissive("M_ButtonCyan", "#3FF0FF", 2.2f);
            Emissive("M_ButtonYellow", "#FFE14D", 2.2f);
            Emissive("M_ButtonPink", "#FF5FD0", 2.2f);

            // ---------------- glass, liquids, swirl, arrows, portal
            Mat("M_Glass", "BWK/Glass", m => { C(m, "_Tint", "#BFE9FF"); F(m, "_Alpha", 0.1f); F(m, "_Glow", 0.2f); }, RenderQueue.Transparent);
            Mat("M_Bubble", "BWK/Glass", m => { C(m, "_Tint", "#FFFFFF"); F(m, "_Alpha", 0.03f); F(m, "_Iridescence", 1f); F(m, "_FresnelPower", 2.2f); F(m, "_Glow", 0.35f); }, RenderQueue.Transparent);
            Mat("M_PipeWater", "BWK/FlowGlow", m => { F(m, "_Mode", 0); C(m, "_ColorA", "#38E8FF"); C(m, "_ColorB", "#FF6AE0"); F(m, "_Intensity", 1.8f); F(m, "_Speed", 1.2f); });
            Mat("M_ChamberSwirl", "BWK/FlowGlow", m => { F(m, "_Mode", 1); C(m, "_ColorA", "#9FE8FF"); F(m, "_Intensity", 1.35f); F(m, "_Speed", 1f); });
            Mat("M_Arrow", "BWK/FlowGlow", m => { F(m, "_Mode", 2); C(m, "_ColorA", "#22EEFF"); F(m, "_Intensity", 2.6f); F(m, "_Speed", 1.4f); });
            Mat("M_PortalRays", "BWK/FlowGlow", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#FFF6D8"); C(m, "_ColorB", "#FFB43A"); F(m, "_Intensity", 2.4f); F(m, "_Speed", 1f);
                F(m, "_SrcBlend", (float)BlendMode.One); F(m, "_DstBlend", (float)BlendMode.One); F(m, "_ZWrite", 0); F(m, "_RayCount", 18);
            }, RenderQueue.Transparent + 10);

            // ---------------- soft materials
            Mat("M_Foam", "BWK/Soft", m =>
            {
                F(m, "_Mode", 0); C(m, "_ColorA", "#FFFFFF"); C(m, "_ShadowColor", "#BFC6FF"); F(m, "_Wrap", 0.65f);
                F(m, "_BumpScale", 3.5f); F(m, "_BumpStrength", 0.35f); F(m, "_Glow", 0.12f); F(m, "_RimStrength", 0.3f);
            });
            Soft("M_BrushPink", "#FF7CC6", "#FFB6E1");
            Soft("M_BrushBlue", "#6FD3FF", "#B4ECFF");
            Soft("M_BrushWhite", "#FFF6FF", "#FFFFFF");
            Mat("M_HatKnit", "BWK/Soft", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#6A2FC2"); C(m, "_ColorB", "#CDB2F5"); F(m, "_Stripes", 3); F(m, "_StripeWidth", 0.0f);
                F(m, "_StitchU", 70); F(m, "_StitchV", 22); F(m, "_BumpStrength", 0.55f); F(m, "_Smoothness", 0.2f); F(m, "_Glow", 0.08f);
            });
            Mat("M_HatCuff", "BWK/Soft", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#5A23A8"); C(m, "_ColorB", "#5A23A8"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 96); F(m, "_StitchV", 7); F(m, "_BumpStrength", 0.75f); F(m, "_Smoothness", 0.18f); F(m, "_Glow", 0.06f);
            });
            Mat("M_HatStripe", "BWK/Soft", m =>
            {
                F(m, "_Mode", 2); C(m, "_ColorA", "#F1E6FF"); C(m, "_ColorB", "#F1E6FF"); F(m, "_StripeWidth", 0f);
                F(m, "_StitchU", 70); F(m, "_StitchV", 22); F(m, "_BumpStrength", 0.5f); F(m, "_Smoothness", 0.2f); F(m, "_Glow", 0.1f);
            });
            Mat("M_EyeIris", "BWK/Soft", m =>
            {
                F(m, "_Mode", 3); C(m, "_ColorA", "#5A2E14"); C(m, "_ColorB", "#A8642A"); C(m, "_ColorC", "#120804");
                F(m, "_Glow", 0.05f); F(m, "_RimStrength", 0.1f);
            });
            Lit_("M_Mouth", "#4B0F1E", metallic: 0f, smooth: 0.6f);
            Lit_("M_Tongue", "#FF6F93", metallic: 0f, smooth: 0.55f, emission: "#300812");
            Lit_("M_PawPad", "#FFE2EE", metallic: 0f, smooth: 0.35f, emission: "#2A1A20");
            Lit_("M_StarBadge", "#FFD43F", metallic: 0.1f, smooth: 0.6f, emission: "#7A4A00");
            Lit_("M_MachinePink", "#FF7AC8", metallic: 0.05f, smooth: 0.78f, emission: "#2A0A1E");
            Lit_("M_MachineLavender", "#C9A9FF", metallic: 0.05f, smooth: 0.75f, emission: "#1E1430");
            Lit_("M_PlasticWhite", "#F6F1FF", metallic: 0f, smooth: 0.8f, emission: "#1A181F");
            Lit_("M_MetalPurple", "#6C3FC4", metallic: 0.85f, smooth: 0.75f);
            Lit_("M_Gem", "#A43BFF", metallic: 0.15f, smooth: 0.96f, emission: "#5C12B0");
            Mat("M_Fabric", "BWK/Soft", m => { F(m, "_Mode", 4); C(m, "_ColorA", "#FFFFFF"); F(m, "_Smoothness", 0.15f); F(m, "_Glow", 0.12f); F(m, "_BumpScale", 2f); });

            // ---------------- fur
            var furNoise = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Tex}/T_FurNoise.png");
            Mat("M_Fur", "BWK/Fur", m =>
            {
                C(m, "_RootColor", "#D9327D"); C(m, "_BaseColor", "#FF5AA6"); C(m, "_TipColor", "#FF9CCB");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 42); F(m, "_FurLength", 0.05f); F(m, "_Gravity", 0.012f); F(m, "_Thinning", 1.05f);
                C(m, "_RimColor", "#FFD6EC"); F(m, "_Glow", 0.12f);
            }, RenderQueue.AlphaTest);
            Mat("M_PomPom", "BWK/Fur", m =>
            {
                C(m, "_RootColor", "#4C1F96"); C(m, "_BaseColor", "#7A3FD6"); C(m, "_TipColor", "#B07CFF");
                if (furNoise) m.SetTexture("_NoiseTex", furNoise);
                F(m, "_Density", 46); F(m, "_FurLength", 0.04f); F(m, "_Gravity", 0.006f); F(m, "_Thinning", 0.95f);
                C(m, "_RimColor", "#E2CCFF"); F(m, "_Glow", 0.1f);
            }, RenderQueue.AlphaTest);

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
