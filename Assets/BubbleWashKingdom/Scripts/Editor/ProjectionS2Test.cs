using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Lead 8d2d815d 2026-11-27 (owner 19:5x "STRICT FINAL APPROVED S2 VISUAL MILESTONE", approved option "drum wall only"): ONE
    /// protected camera-projection test of the S2 door drum (MouthDrum_r7 chunks, track 40.2 -> 62 m). Nothing is saved: the scene
    /// is opened and refreshed in memory like AgentPreviewBatch, materials are swapped in memory and restored.
    /// The projection uses the game's OWN comparison camera R2 (CaptureTools.R2*) and the drum's OWN UVs (uv.x = around fraction,
    /// uv.y = track distance / 4), so a baked texel lands exactly where Unity draws that wall (no Blender camera solve).
    ///  UVPassBatch  -bwkOut DIR : 3840x2160 float visibility pass from R2 (RG = around / along of the visible drum texel, B = 1),
    ///                             raw RGBA32F bottom-up rows in DIR/uvpass_r2_3840x2160.f32 + meta json + the normal R2 render.
    ///  PreviewBatch -bwkOut DIR -bwkProjTex PNG [-bwkGain g] [-bwkDists 33.5,36,...] : current vs projected drum from R2 (+ mascot
    ///                             hidden) and from the unchanged gameplay rig (portrait 720x1280) at the listed track distances.
    /// The projected texture contains reference pixels: it stays local (Captures/, gitignored) and is loaded at run time only.
    /// </summary>
    public static class ProjectionS2Test
    {
        const float D0 = SceneBuilder.HallMouthD + 0.2f, D1 = 62f;

        static string Arg(string key)
        {
            var a = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == key) return a[i + 1];
            return null;
        }

        static (RunnerController runner, Camera cam, CinemachineBrain brain) Setup()
        {
            TextureGenerator.Run();
            MaterialLibrary.Run();
            EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
            SceneBuilder.PreviewRefreshDomains();
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var cam = Camera.main;
            var brain = cam.GetComponent<CinemachineBrain>();
            if (brain) brain.enabled = false;
            return (runner, cam, brain);
        }

        static void PoseRunner(RunnerController runner, float d)
        {
            runner.TeleportTo(d, 0f);
            var animator = runner.GetComponentInChildren<Animator>();
            if (animator != null && animator.runtimeAnimatorController != null)
            {
                var slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
            }
        }

        // identical to CaptureTools.CaptureHero's R2_rear_S2_like_3s camera
        static void PoseR2(RunnerController runner, Camera cam)
        {
            PoseRunner(runner, SceneBuilder.HeroMouthDistance);
            var f = runner.Frame;
            Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
            Vector3 cp = runner.transform.position - fwd * CaptureTools.R2Back + Vector3.up * CaptureTools.R2Height + right * CaptureTools.R2Lat;
            cam.transform.SetPositionAndRotation(cp, Quaternion.LookRotation(fwd, Vector3.up) * Quaternion.Euler(CaptureTools.R2Pitch, CaptureTools.R2Yaw, 0f));
            cam.fieldOfView = CaptureTools.R2Fov;
        }

        // the unchanged gameplay rig (as CaptureHero's hero_mouth_*), mascot at track distance d
        static void PoseRig(RunnerController runner, Camera cam, float d, float aspect)
        {
            PoseRunner(runner, d);
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            rig.aspectOverride = aspect;
            rig.Snap();
            var lens = rig.vcam.Lens;
            cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
            cam.fieldOfView = lens.FieldOfView;
        }

        static List<Renderer> DrumRenderers() =>
            Object.FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
                .Where(r => r.enabled && r.gameObject.name.StartsWith("MouthDrum_r7_")).OrderBy(r => r.gameObject.name).ToList();

        static List<Renderer> MascotRenderers(RunnerController runner) =>
            runner.GetComponentsInChildren<Renderer>(true).Where(r => r.enabled && !(r is ParticleSystemRenderer) && !(r is TrailRenderer)).ToList();

        static Material ProjMat(float mode)
        {
            var sh = Shader.Find("Hidden/BWK/ProjTest");
            if (sh == null) throw new System.Exception("Hidden/BWK/ProjTest shader not found");
            var m = new Material(sh);
            m.SetFloat("_Mode", mode); m.SetFloat("_D0", D0); m.SetFloat("_D1", D1); m.SetFloat("_Gain", 1f);
            return m;
        }

        public static void UVPassBatch()
        {
            try
            {
                string outDir = Arg("-bwkOut") ?? "Captures/lead/s2_projection";
                Directory.CreateDirectory(outDir);
                var (runner, cam, brain) = Setup();
                PoseR2(runner, cam);
                CaptureTools.Render(cam, 1280, 720, $"{outDir}/R2_current_1280x720.png");
                CaptureTools.Render(cam, 3840, 2160, $"{outDir}/R2_current_3840x2160.png");

                const int W = 3840, H = 2160;
                cam.aspect = W / (float)H;
                var drum = new HashSet<Renderer>(DrumRenderers());
                var uvMat = ProjMat(0f);
                var blackMat = ProjMat(1f);
                var planes = GeometryUtility.CalculateFrustumPlanes(cam);
                var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear) { antiAliasing = 1 };
                rt.Create();
                var cmd = new CommandBuffer { name = "BWK S2 projection visibility pass" };
                cmd.SetRenderTarget(rt);
                cmd.ClearRenderTarget(true, true, new Color(0f, 0f, 0f, 0f));
                cmd.SetViewProjectionMatrices(cam.worldToCameraMatrix, cam.projectionMatrix);
                int nDrum = 0, nOcc = 0;
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
                {
                    if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                    if (r is ParticleSystemRenderer || r is TrailRenderer || r is LineRenderer) continue;
                    if (!GeometryUtility.TestPlanesAABB(planes, r.bounds)) continue;
                    bool isDrum = drum.Contains(r);
                    var mat = isDrum ? uvMat : blackMat;
                    for (int s = 0; s < Mathf.Max(1, r.sharedMaterials.Length); s++) cmd.DrawRenderer(r, mat, s, 0);
                    if (isDrum) nDrum++; else nOcc++;
                }
                Graphics.ExecuteCommandBuffer(cmd);
                var prev = RenderTexture.active;
                RenderTexture.active = rt;
                var tex = new Texture2D(W, H, TextureFormat.RGBAFloat, false, true);
                tex.ReadPixels(new Rect(0, 0, W, H), 0, 0);
                tex.Apply(false);
                RenderTexture.active = prev;
                File.WriteAllBytes($"{outDir}/uvpass_r2_{W}x{H}.f32", tex.GetRawTextureData());
                var p = cam.transform.position; var q = cam.transform.rotation;
                File.WriteAllText($"{outDir}/uvpass_r2_meta.json", string.Format(CultureInfo.InvariantCulture,
                    "{{\"w\":{0},\"h\":{1},\"rows\":\"bottom-up (ReadPixels)\",\"channels\":\"R around 0..1, G along 0..1 over d0..d1, B drum visible, A 1\",\"d0\":{2},\"d1\":{3},\"cam_pos\":[{4},{5},{6}],\"cam_rot\":[{7},{8},{9},{10}],\"vfov\":{11},\"drum_renderers\":{12},\"occluder_renderers\":{13}}}",
                    W, H, D0, D1, p.x, p.y, p.z, q.x, q.y, q.z, q.w, cam.fieldOfView, nDrum, nOcc));
                Debug.Log($"[BWK] S2 projection UV pass: {nDrum} drum + {nOcc} occluder renderers -> {outDir}");
                Object.DestroyImmediate(tex); rt.Release(); Object.DestroyImmediate(rt);
                cam.ResetAspect();
                if (brain) brain.enabled = true;
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] S2 projection UV pass failed: " + e); EditorApplication.Exit(1); }
        }

        public static void PreviewBatch()
        {
            try
            {
                string outDir = Arg("-bwkOut") ?? "Captures/lead/s2_projection/preview";
                string texPath = Arg("-bwkProjTex");
                float gain = float.Parse(Arg("-bwkGain") ?? "1", CultureInfo.InvariantCulture);
                var dists = (Arg("-bwkDists") ?? "33.5,36,38.5,41,44").Split(',').Select(s => float.Parse(s, CultureInfo.InvariantCulture)).ToArray();
                Directory.CreateDirectory(outDir);
                var (runner, cam, brain) = Setup();
                var drum = DrumRenderers();
                var orig = drum.Select(r => r.sharedMaterials).ToList();
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, true, false);
                tex.LoadImage(File.ReadAllBytes(texPath));
                tex.wrapModeU = TextureWrapMode.Repeat; tex.wrapModeV = TextureWrapMode.Clamp;
                tex.filterMode = FilterMode.Trilinear; tex.anisoLevel = 8;
                tex.Apply(true);
                var show = ProjMat(2f);
                show.SetTexture("_ProjTex", tex);
                show.SetFloat("_Gain", gain);
                var mascot = MascotRenderers(runner);
                var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
                foreach (var variant in new[] { "current", "projected" })
                {
                    for (int i = 0; i < drum.Count; i++)
                        drum[i].sharedMaterials = variant == "current" ? orig[i] : Enumerable.Repeat(show, orig[i].Length).ToArray();
                    PoseR2(runner, cam);
                    CaptureTools.Render(cam, 1280, 720, $"{outDir}/{variant}_R2_16x9.png");
                    foreach (var r in mascot) r.enabled = false;
                    CaptureTools.Render(cam, 1280, 720, $"{outDir}/{variant}_R2_bg_16x9.png");
                    foreach (var r in mascot) r.enabled = true;
                    foreach (float d in dists)
                    {
                        PoseRig(runner, cam, d, 720f / 1280f);
                        CaptureTools.Render(cam, 720, 1280, string.Format(CultureInfo.InvariantCulture, "{0}/{1}_rig_d{2:0.0}_9x16.png", outDir, variant, d));
                    }
                }
                for (int i = 0; i < drum.Count; i++) drum[i].sharedMaterials = orig[i];
                if (rig) rig.aspectOverride = 0f;
                if (brain) brain.enabled = true;
                Debug.Log($"[BWK] S2 projection preview: {drum.Count} drum chunks, gain {gain}, distances {string.Join(",", dists)} -> {outDir}");
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] S2 projection preview failed: " + e); EditorApplication.Exit(1); }
        }
    }
}
