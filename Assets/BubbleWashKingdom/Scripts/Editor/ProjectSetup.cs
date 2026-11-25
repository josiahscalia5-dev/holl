using UnityEditor;
using UnityEditor.Build;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace BubbleWash.EditorTools
{
    /// <summary>Player, quality and URP configuration for a portrait mobile water-slide game.</summary>
    public static class ProjectSetup
    {
        [MenuItem("Bubble Wash/Setup/1 Configure Project")]
        public static void Run()
        {
            PlayerSettings.companyName = "BubbleWashKingdom";
            PlayerSettings.productName = "Bubble Wash Kingdom";
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, "com.BubbleWashKingdom.Game");
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Standalone, "com.BubbleWashKingdom.Game");
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.Portrait;
            PlayerSettings.allowedAutorotateToPortrait = true;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.allowedAutorotateToLandscapeLeft = false;
            PlayerSettings.allowedAutorotateToLandscapeRight = false;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 405;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.runInBackground = true;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
            try
            {
                PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.Vulkan, GraphicsDeviceType.OpenGLES3 });
                PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
            }
            catch (System.Exception e) { Debug.LogWarning("[BWK] Android graphics API setup skipped: " + e.Message); }

            ConfigureUrp();
            AssetDatabase.SaveAssets();
            Debug.Log("[BWK] Project configured.");
        }

        static void ConfigureUrp()
        {
            var mobile = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/Settings/Mobile_RPAsset.asset");
            var pc = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/Settings/PC_RPAsset.asset");
            if (mobile != null) ConfigureAsset(mobile, msaa: 2, shadowRes: 1024, cascades: 1, shadowDistance: 32f);
            if (pc != null) ConfigureAsset(pc, msaa: 4, shadowRes: 2048, cascades: 2, shadowDistance: 40f);
            foreach (var path in new[] { "Assets/Settings/Mobile_Renderer.asset", "Assets/Settings/PC_Renderer.asset" })
            {
                var data = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(path);
                if (data == null) continue;
                var so = new SerializedObject(data);
                SetInt(so, "m_RenderingMode", 0); // Forward (custom shaders use the classic additional-light loop)
                SetInt(so, "m_DepthPrimingMode", 0);
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(data);
            }
            // Quality: index of "Mobile" for Android, "PC" for Standalone (template defaults).
            string[] names = QualitySettings.names;
            for (int i = 0; i < names.Length; i++)
            {
                if (names[i].ToLowerInvariant().Contains("mobile")) QualitySettings.SetQualityLevel(i, false);
            }
        }

        static void ConfigureAsset(UniversalRenderPipelineAsset asset, int msaa, int shadowRes, int cascades, float shadowDistance)
        {
            asset.supportsHDR = true;
            asset.msaaSampleCount = msaa;
            asset.renderScale = 1f;
            asset.shadowDistance = shadowDistance;
            asset.shadowCascadeCount = cascades;
            var so = new SerializedObject(asset);
            SetBool(so, "m_SoftShadowsSupported", true);
            SetInt(so, "m_MainLightShadowmapResolution", shadowRes);
            SetInt(so, "m_AdditionalLightsRenderingMode", 1); // per pixel
            SetInt(so, "m_AdditionalLightsPerObjectLimit", 4);
            SetBool(so, "m_SupportsCameraDepthTexture", false);
            SetBool(so, "m_SupportsCameraOpaqueTexture", false);
            SetBool(so, "m_AdditionalLightShadowsSupported", false);
            SetBool(so, "m_ReflectionProbeBlending", true);
            SetBool(so, "m_ReflectionProbeBoxProjection", false);
            so.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(asset);
        }

        static void SetInt(SerializedObject so, string name, int value)
        {
            var p = so.FindProperty(name);
            if (p != null) p.intValue = value; else Debug.Log($"[BWK] (info) property {name} not found on {so.targetObject.name}");
        }

        static void SetBool(SerializedObject so, string name, bool value)
        {
            var p = so.FindProperty(name);
            if (p != null) p.boolValue = value; else Debug.Log($"[BWK] (info) property {name} not found on {so.targetObject.name}");
        }
    }
}
