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
    public static partial class MaterialLibrary
    {
        public const string Dir = "Assets/BubbleWashKingdom/Art/Materials";
        const string Tex = "Assets/BubbleWashKingdom/Art/Textures";

        static Shader Lit => Shader.Find("Universal Render Pipeline/Lit");
        static Shader ParticlesUnlit => Shader.Find("Universal Render Pipeline/Particles/Unlit");

        [MenuItem("Bubble Wash/Setup/3 Build Materials")]
        public static void Run()
        {
            Directory.CreateDirectory(Dir);
            // domain partials (one owner each): MaterialLibrary.WaterFX/Environment/Lighting/Character.cs
            WaterFXMaterials();
            EnvironmentMaterials();
            LightingMaterials();
            CharacterMaterials();

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

        static void Gold(string name, string high, string mid, string low, float brightness, float glow)
        {
            Mat(name, "BWK/Gold", m =>
            {
                C(m, "_HighColor", high); C(m, "_MidColor", mid); C(m, "_LowColor", low);
                C(m, "_RimColor", "#FFD27A"); C(m, "_BandColor", "#FFE9A8");
                F(m, "_Brightness", brightness); F(m, "_Emission", glow); F(m, "_SpecStrength", 1.4f); F(m, "_SpecPower", 72f);
                F(m, "_LightInfluence", 0.35f); F(m, "_FogAmount", 0.6f);
            });
        }

        static void Emissive(string name, string hex, float intensity, float chase = 0f, float pulse = 0.12f, float core = 0.45f, float fog = 0.35f, float halo = 0.6f)
        {
            Mat(name, "BWK/Emissive", m =>
            {
                C(m, "_Color", hex); F(m, "_Intensity", intensity); F(m, "_Chase", chase); F(m, "_PulseAmount", pulse); F(m, "_CoreWhite", core);
                F(m, "_FogAmount", fog); F(m, "_HaloBoost", halo);
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
