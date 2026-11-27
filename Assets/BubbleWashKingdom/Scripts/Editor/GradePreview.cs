using System.Globalization;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Lead tool, PREVIEW ONLY (owner 2026-11-26 21:15 / 21:25: "preview reference-based colour grading, cinematic lighting
    /// and controlled soft glow measured from my original video ... show before-and-after renders before permanently
    /// applying the grade"). Nothing is saved: an in-memory global Volume (priority 500) adds URP Color Lookup with the strip
    /// LUT written by Tools/look_lut.py and, optionally, a softer / wider bloom on top of the saved scene's post stack, then
    /// renders the usual hero / comparison stills. The "before" set is the matching build's Captures/stills_<tag>.
    ///   Tools/unity_run.sh BubbleWash.EditorTools.GradePreview.Batch lead_grade -bwkOut Captures/look/unity_p4
    ///     -bwkGradeLUT Captures/look/lut_video_look.png [-bwkGradeAmount 0..1 (1)] [-bwkGlow 0..1 (0)] [-bwkStills]
    /// Applying it for real needs the owner's yes (then the lighting owner moves the LUT + bloom into Assets/Settings).
    /// </summary>
    public static class GradePreview
    {
        public static void Batch()
        {
            try
            {
                string outDir = Arg("-bwkOut") ?? "Captures/look/unity_graded";
                string lut = Arg("-bwkGradeLUT");
                float amount = ParseF(Arg("-bwkGradeAmount"), 1f), glow = ParseF(Arg("-bwkGlow"), 0f);
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                var go = AddVolume(lut, amount, glow);
                CaptureTools.CaptureHero(outDir, outDir);
                if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-bwkStills") >= 0)
                    CaptureTools.CaptureStills(outDir + "/stills");
                Object.DestroyImmediate(go);
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] grade preview failed: " + e); EditorApplication.Exit(1); }
        }

        static string Arg(string key)
        {
            var args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++) if (args[i] == key) return args[i + 1];
            return null;
        }

        static float ParseF(string s, float d) => string.IsNullOrEmpty(s) ? d : float.Parse(s, CultureInfo.InvariantCulture);

        static GameObject AddVolume(string lutPath, float amount, float glow)
        {
            var existing = Object.FindObjectsByType<Volume>(FindObjectsSortMode.None);
            var go = new GameObject("BWK_GradePreview_NotSaved") { hideFlags = HideFlags.DontSave };
            if (existing.Length > 0) go.layer = existing[0].gameObject.layer;
            var vol = go.AddComponent<Volume>();
            vol.isGlobal = true;
            vol.priority = 500f;
            vol.weight = 1f;
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            vol.sharedProfile = profile;
            if (!string.IsNullOrEmpty(lutPath))
            {
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false, true) { name = Path.GetFileNameWithoutExtension(lutPath) };
                tex.LoadImage(File.ReadAllBytes(lutPath), false);
                tex.filterMode = FilterMode.Bilinear;
                tex.wrapMode = TextureWrapMode.Clamp;
                var cl = profile.Add<ColorLookup>(false);
                cl.texture.Override(tex);
                cl.contribution.Override(Mathf.Clamp01(amount));
                Debug.Log($"[BWK] grade preview: Color Lookup {lutPath} {tex.width}x{tex.height} (valid {cl.ValidateLUT()}), contribution {amount:F2}");
            }
            if (glow > 0f)
            {
                Bloom baseBloom = null;
                float bestPrio = float.NegativeInfinity;
                foreach (var v in existing)
                    if (v.isGlobal && v.sharedProfile != null && v.priority > bestPrio && v.sharedProfile.TryGet(out Bloom b))
                    { baseBloom = b; bestPrio = v.priority; }
                float bi = baseBloom != null ? baseBloom.intensity.value : 0.6f;
                float bs = baseBloom != null ? baseBloom.scatter.value : 0.7f;
                float bt = baseBloom != null ? baseBloom.threshold.value : 1f;
                var bloom = profile.Add<Bloom>(false);
                bloom.intensity.Override(bi * (1f + 0.8f * glow));
                bloom.scatter.Override(Mathf.Lerp(bs, 0.85f, glow));
                bloom.threshold.Override(bt * (1f - 0.2f * glow));
                Debug.Log($"[BWK] grade preview: bloom intensity/scatter/threshold {bi:F2}/{bs:F2}/{bt:F2} -> " +
                          $"{bloom.intensity.value:F2}/{bloom.scatter.value:F2}/{bloom.threshold.value:F2} (glow {glow:F2})");
            }
            return go;
        }
    }
}
