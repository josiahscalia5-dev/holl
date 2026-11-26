using System.Collections.Generic;
using System.IO;
using System.Linq;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Renders real Unity stills of the built scene through the gameplay camera rig (rear view) at fixed track
    /// positions, in landscape 16:9 (for comparison with the reference frames) and portrait 9:16 (mobile), plus
    /// front-facing comparison angles that match the reference camera in the tunnel section.
    /// Output: Captures/stills/*.png. Batch entry: BubbleWash.EditorTools.CaptureTools.CaptureStillsBatch
    /// </summary>
    public static class CaptureTools
    {
        public const string OutDir = "Captures/stills";

        public static void MaterialsAndStillsBatch()
        {
            try { MaterialLibrary.Run(); CaptureStills(); EditorApplication.Exit(0); }
            catch (System.Exception e) { Debug.LogError("[BWK] capture failed: " + e); EditorApplication.Exit(1); }
        }

        public static void CaptureStillsBatch()
        {
            try { CaptureStills(); EditorApplication.Exit(0); }
            catch (System.Exception e) { Debug.LogError("[BWK] capture failed: " + e); EditorApplication.Exit(1); }
        }

        public static void HeroBatch()
        {
            try { CaptureHero(); EditorApplication.Exit(0); }
            catch (System.Exception e) { Debug.LogError("[BWK] hero capture failed: " + e); EditorApplication.Exit(1); }
        }

        const string CompareDir = "Captures/compare";

        /// <summary>
        /// Agent preview (no scene save): regenerates textures + materials, rebuilds lighting/post and runner FX in memory,
        /// then renders the hero screen + reference comparisons into -bwkOut DIR (default Captures/agents/preview).
        /// Run via: Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch LOGNAME -bwkOut Captures/agents/NAME
        /// </summary>
        public static void AgentPreviewBatch()
        {
            try
            {
                string outDir = ArgValue("-bwkOut") ?? "Captures/agents/preview";
                TextureGenerator.Run();
                MaterialLibrary.Run();
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                SceneBuilder.PreviewRefreshDomains();
                CaptureHero(outDir, outDir);
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] agent preview failed: " + e); EditorApplication.Exit(1); }
        }

        /// <summary>
        /// Lead tool (no scene save): renders the hero position through several PORTRAIT rear-camera framings in one run,
        /// plus side / three-quarter views that show the seated pose, and reference side-by-sides.
        ///   -bwkCamVariants "back,height,pitch,fov;back,height,pitch,fov"   (default: the rig's current values)
        ///   -bwkOut DIR (default Captures/agents/_lead_cam)
        /// Writes DIR/cam_v{i}_9x16.png, DIR/cam_v{i}_vs_reference_9x16.png, DIR/pose_side.png, DIR/pose_rear34.png.
        /// </summary>
        public static void LeadViewsBatch()
        {
            try
            {
                string outDir = ArgValue("-bwkOut") ?? "Captures/agents/_lead_cam";
                Directory.CreateDirectory(outDir);
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
                var registry = Object.FindFirstObjectByType<TrackItemRegistry>();
                var cam = Camera.main;
                if (runner == null || rig == null || cam == null || registry == null) throw new System.Exception("scene objects missing");
                SceneBuilder.ApplyHeroCamera(rig);   // default variant = the owner-approved hero camera
                var brain = cam.GetComponent<CinemachineBrain>();
                if (brain) brain.enabled = false;
                runner.track.Rebuild();
                float best = FindHeroDistance(runner, registry);
                PoseHero(runner, best);

                string spec = ArgValue("-bwkCamVariants");
                var variants = new List<float[]>();
                if (!string.IsNullOrEmpty(spec))
                    foreach (var part in spec.Split(';'))
                    {
                        var v = part.Split(',').Select(s => float.Parse(s.Trim(), System.Globalization.CultureInfo.InvariantCulture)).ToArray();
                        if (v.Length == 4) variants.Add(v);
                    }
                if (variants.Count == 0) variants.Add(new[] { rig.distanceBackPortrait, rig.heightPortrait, rig.pitchDownPortrait, rig.fovPortrait });

                var saved = new[] { rig.distanceBackPortrait, rig.heightPortrait, rig.pitchDownPortrait, rig.fovPortrait };
                Texture2D refCrop = null;
                if (File.Exists(RefRear))
                {
                    var refTex = LoadPng(RefRear);
                    int cw = Mathf.RoundToInt(refTex.height * 9f / 16f);
                    refCrop = Resize(Crop(refTex, Mathf.RoundToInt(refTex.width * 0.49f - cw * 0.5f), 0, cw, refTex.height), 720, 1280);
                }
                for (int i = 0; i < variants.Count; i++)
                {
                    var v = variants[i];
                    rig.distanceBackPortrait = v[0]; rig.heightPortrait = v[1]; rig.pitchDownPortrait = v[2]; rig.fovPortrait = v[3];
                    rig.aspectOverride = 720f / 1280f;
                    rig.Snap();
                    var lens = rig.vcam.Lens;
                    cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                    cam.fieldOfView = lens.FieldOfView;
                    string path = $"{outDir}/cam_v{i}_9x16.png";
                    Render(cam, 720, 1280, path);
                    if (refCrop != null) SaveSideBySide(new[] { refCrop, LoadPng(path) }, $"{outDir}/cam_v{i}_vs_reference_9x16.png");
                    Debug.Log($"[BWK] camera variant v{i}: back {v[0]} height {v[1]} pitch {v[2]} fov {v[3]}");
                }
                rig.distanceBackPortrait = saved[0]; rig.heightPortrait = saved[1]; rig.pitchDownPortrait = saved[2]; rig.fovPortrait = saved[3];
                rig.aspectOverride = 0f;

                // Seated-pose views (verification only, never gameplay cameras): right side and rear three-quarter.
                var f = runner.Frame;
                Vector3 target = runner.transform.position + f.flatUp * 0.45f;
                foreach (var (name, offset) in new[] {
                    ("pose_side", f.flatRight * 1.55f + f.flatUp * 0.75f + f.forward * 0.35f),
                    ("pose_rear34", -f.forward * 2.2f + f.flatRight * 1.5f + f.flatUp * 1.2f) })
                {
                    Vector3 p = target + offset;
                    cam.transform.SetPositionAndRotation(p, Quaternion.LookRotation(target - p, f.flatUp));
                    cam.fieldOfView = 42f;
                    Render(cam, 1280, 720, $"{outDir}/{name}.png");
                }
                if (brain) brain.enabled = true;
                Debug.Log("[BWK] Lead views written to " + Path.GetFullPath(outDir));
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] lead views failed: " + e); EditorApplication.Exit(1); }
        }

        /// <summary>Track distance with the most collectibles 2.5-14 m ahead (side-lane coins count double, gems x3).</summary>
        static float FindHeroDistance(RunnerController runner, TrackItemRegistry registry)
        {
            if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-bwkHeroSearch") < 0) return SceneBuilder.HeroDistance;
            float L = runner.track.Length;
            float best = 90f; float bestScore = -1f;
            for (float d = 75f; d < L - 45f; d += 0.5f)
            {
                float score = 0f;
                foreach (var it in registry.items)
                {
                    float a = it.distance - d;
                    if (a < 2.5f || a > 14f) continue;
                    if (it.kind == TrackItemKind.Coin) score += Mathf.Abs(it.lateral) > 0.5f ? (a < 9f ? 3f : 1.5f) : 0.5f;
                    else if (it.kind == TrackItemKind.Gem) score += 3f;
                    else if (it.kind == TrackItemKind.Boost) score += 1f;
                }
                if (score > bestScore) { bestScore = score; best = d; }
            }
            return best;
        }

        /// <summary>Puts the mascot at the hero distance in the Slide pose with the slide FX and ambient bubbles running.</summary>
        static void PoseHero(RunnerController runner, float distance)
        {
            var animator = runner.GetComponentInChildren<Animator>();
            AnimationClip slide = null;
            if (animator != null && animator.runtimeAnimatorController != null)
                slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
            foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);
            runner.TeleportTo(distance, 0f);
            if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
            SimulateSlideFX(runner);
        }

        static string ArgValue(string key)
        {
            var args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++) if (args[i] == key) return args[i + 1];
            return null;
        }
        const string RefRear = "Reference/frames4k/f_03.00s.png";   // owner's 4K export of the same video (was frames/f_003.00s.png at 720p)   // rear view inside the tunnel (hero screen target)

        /// <summary>
        /// Hero gameplay screen: a tunnel position with coins (and ideally a gem) just ahead, rendered through the
        /// rear gameplay rig at 16:9 and 9:16, then composed side by side with the approved reference rear frame
        /// (left = reference video, right = real Unity render). Reference stays private: output goes to Captures/.
        /// </summary>
        [MenuItem("Bubble Wash/Capture Hero + Comparison")]
        public static void CaptureHero() => CaptureHero(OutDir, CompareDir);

        public static void CaptureHero(string stillsDir, string compareDir)
        {
            if (EditorSceneManager.GetActiveScene().path != SceneBuilder.ScenePath)
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
            Directory.CreateDirectory(stillsDir);
            Directory.CreateDirectory(compareDir);
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            var registry = Object.FindFirstObjectByType<TrackItemRegistry>();
            var cam = Camera.main;
            if (runner == null || rig == null || cam == null || registry == null) { Debug.LogError("[BWK] hero: scene objects missing"); return; }
            SceneBuilder.ApplyHeroCamera(rig);   // owner-approved fixed hero camera, even on a scene saved before it
            var brain = cam.GetComponent<CinemachineBrain>();
            if (brain) brain.enabled = false;
            runner.track.Rebuild();
            float L = runner.track.Length;

            // Score candidate positions: coins 4-16 m ahead (side lanes count double: visible beside the mascot), gems x3.
            float best = 90f; float bestScore = -1f;
            for (float d = 75f; d < L - 45f; d += 0.5f)
            {
                float score = 0f;
                foreach (var it in registry.items)
                {
                    float a = it.distance - d;
                    if (a < 2.5f || a > 14f) continue;
                    // reference 3.0 s: big paw coins right beside the camera in the side lanes
                    if (it.kind == TrackItemKind.Coin) score += Mathf.Abs(it.lateral) > 0.5f ? (a < 9f ? 3f : 1.5f) : 0.5f;
                    else if (it.kind == TrackItemKind.Gem) score += 3f;
                    else if (it.kind == TrackItemKind.Boost) score += 1f;
                }
                if (score > bestScore) { bestScore = score; best = d; }
            }
            // Owner workflow: FIXED reference camera for like-for-like before/after comparisons (item changes must not
            // move the hero shot). -bwkHeroSearch restores the old automatic search.
            if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-bwkHeroSearch") < 0)
            {
                Debug.Log($"[BWK] hero search would pick {best:F1} m (score {bestScore}); using fixed hero distance {SceneBuilder.HeroDistance:F1} m");
                best = SceneBuilder.HeroDistance;
            }
            Debug.Log($"[BWK] hero shot at {best:F1} m (score {bestScore})");
            foreach (var it in registry.items)
            {
                float a = it.distance - best;
                if (a < 0f || a > 14f) continue;
                var rs = it.GetComponentsInChildren<Renderer>(true);
                var b = rs.Length > 0 ? rs[0].bounds : new Bounds();
                var mf = rs.Length > 0 ? rs[0].GetComponent<MeshFilter>() : null;
                Debug.Log($"[BWK] hero item {it.kind} +{a:F1} m lat {it.lateral:F2} active {it.gameObject.activeInHierarchy} renderers {rs.Length} " +
                          $"enabled {(rs.Length > 0 && rs[0].enabled)} mesh {(mf != null && mf.sharedMesh != null ? mf.sharedMesh.name : "-")} " +
                          $"bounds c{b.center} s{b.size} pos {it.transform.position}");
            }

            var animator = runner.GetComponentInChildren<Animator>();
            AnimationClip slide = null;
            if (animator != null && animator.runtimeAnimatorController != null)
                slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
            foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);
            runner.TeleportTo(best, 0f);
            if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
            SimulateSlideFX(runner);
            foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
            {
                rig.aspectOverride = w / (float)h;
                rig.Snap();
                var lens = rig.vcam.Lens;
                cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                cam.fieldOfView = lens.FieldOfView;
                Render(cam, w, h, $"{stillsDir}/hero_{tag}.png");
            }
            rig.aspectOverride = 0f;
            if (brain) brain.enabled = true;

            if (!File.Exists(RefRear)) { Debug.LogWarning("[BWK] reference frame missing - comparison skipped"); return; }
            var refTex = LoadPng(RefRear);
            var ours16 = LoadPng($"{stillsDir}/hero_16x9.png");
            var ours9 = LoadPng($"{stillsDir}/hero_9x16.png");
            // 16:9 pair: reference | Unity (both 1280x720)
            SaveSideBySide(new[] { Resize(refTex, 1280, 720), Resize(ours16, 1280, 720) }, $"{compareDir}/hero_vs_reference_16x9.png");
            // 9:16 pair: centre 9:16 crop of the reference (mascot-centred) | Unity portrait, both 720x1280
            int cw = Mathf.RoundToInt(refTex.height * 9f / 16f);
            var crop = Crop(refTex, Mathf.RoundToInt(refTex.width * 0.49f - cw * 0.5f), 0, cw, refTex.height);
            SaveSideBySide(new[] { Resize(crop, 720, 1280), ours9 }, $"{compareDir}/hero_vs_reference_9x16.png");
            Debug.Log("[BWK] Hero comparison written to " + Path.GetFullPath(compareDir));
        }

        static Texture2D LoadPng(string path)
        {
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            t.LoadImage(File.ReadAllBytes(path));
            return t;
        }

        static Texture2D Resize(Texture2D src, int w, int h)
        {
            if (src.width == w && src.height == h) return src;
            var dst = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var px = new Color[w * h];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                    px[y * w + x] = src.GetPixelBilinear((x + 0.5f) / w, (y + 0.5f) / h);
            dst.SetPixels(px);
            dst.Apply(false);
            return dst;
        }

        static Texture2D Crop(Texture2D src, int x0, int y0, int w, int h)
        {
            x0 = Mathf.Clamp(x0, 0, src.width - w);
            var dst = new Texture2D(w, h, TextureFormat.RGBA32, false);
            dst.SetPixels(src.GetPixels(x0, y0, w, h));
            dst.Apply(false);
            return dst;
        }

        /// <summary>Equal-height images side by side with a 12 px dark divider.</summary>
        static void SaveSideBySide(Texture2D[] imgs, string path)
        {
            const int gap = 12;
            int h = imgs[0].height;
            int w = imgs.Sum(t => t.width) + gap * (imgs.Length - 1);
            var outTex = new Texture2D(w, h, TextureFormat.RGB24, false);
            var fill = new Color[w * h];
            for (int i = 0; i < fill.Length; i++) fill[i] = new Color(0.08f, 0.05f, 0.14f);
            outTex.SetPixels(fill);
            int x = 0;
            foreach (var t in imgs)
            {
                outTex.SetPixels(x, 0, t.width, t.height, t.GetPixels());
                x += t.width + gap;
            }
            outTex.Apply(false);
            File.WriteAllBytes(path, outTex.EncodeToPNG());
        }

        [MenuItem("Bubble Wash/Capture Stills")]
        public static void CaptureStills()
        {
            if (EditorSceneManager.GetActiveScene().path != SceneBuilder.ScenePath)
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
            Directory.CreateDirectory(OutDir);
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            var cam = Camera.main;
            if (runner == null || rig == null || cam == null) { Debug.LogError("[BWK] capture: scene objects missing"); return; }
            var brain = cam.GetComponent<CinemachineBrain>();
            if (brain) brain.enabled = false;
            runner.track.Rebuild();
            float L = runner.track.Length;

            var animator = runner.GetComponentInChildren<Animator>();
            AnimationClip slide = null;
            if (animator != null && animator.runtimeAnimatorController != null)
                slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");

            foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);

            var shots = new (string name, float d, float lat)[]
            {
                ("01_hall_start", 16f, 0f), ("02_hall_curve", 36f, 0f), ("03_tunnel_entry", 55f, 0f),
                ("04_tunnel", 92f, 0f), ("05_tunnel_lane_left", 128f, -1.15f), ("06_tunnel_lane_right", 170f, 1.15f),
                ("07_chambers", 215f, 0f), ("08_sweep", 250f, 0f), ("09_portal", L - 34f, 0f),
            };
            foreach (var s in shots)
            {
                runner.TeleportTo(s.d, s.lat);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                SimulateSlideFX(runner);
                foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
                {
                    rig.aspectOverride = w / (float)h;
                    rig.Snap();
                    var lens = rig.vcam.Lens;
                    cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                    cam.fieldOfView = lens.FieldOfView;
                    Render(cam, w, h, $"{OutDir}/{s.name}_{tag}.png");
                }
            }

            // Front-facing comparison angles (reference 3.75-15 s camera) - comparison only, never used in gameplay.
            foreach (var (name, d) in new[] { ("C1_front_tunnel_like_5s", 100f), ("C2_front_chambers_like_10s", 220f), ("C3_front_portal_like_14s", L - 22f) })
            {
                runner.TeleportTo(d, 0f);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                var f = runner.Frame;
                Vector3 camPos = runner.transform.position + f.forward * 2.6f + f.flatUp * 0.95f;
                cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(runner.transform.position + f.flatUp * 0.55f - camPos, f.flatUp));
                cam.fieldOfView = 46f;
                Render(cam, 1280, 720, $"{OutDir}/{name}_16x9.png");
            }
            rig.aspectOverride = 0f;
            if (brain) brain.enabled = true;
            Debug.Log("[BWK] Stills written to " + Path.GetFullPath(OutDir));
        }

        /// <summary>Edit-mode stills: run the sliding splash emitters for a moment so the water FX show like in play.</summary>
        static void SimulateSlideFX(RunnerController runner)
        {
            var fx = runner.GetComponentInChildren<SplashFX>();
            if (fx == null) return;
            var list = new List<(ParticleSystem ps, float rate)> { (fx.spray, fx.sprayRateAtBase), (fx.foamTrail, fx.trailRateAtBase) };
            if (fx.sheets != null) foreach (var sh in fx.sheets) list.Add((sh, fx.sheetRateAtBase));
            foreach (var (ps, rate) in list)
            {
                if (ps == null) continue;
                var em = ps.emission;
                em.rateOverTime = rate;
                ps.Simulate(0.8f, true, true);
                em.rateOverTime = 0f;
            }
        }

        public static void Render(Camera cam, int w, int h, string path)
        {
            var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB, 4);
            cam.aspect = w / (float)h;
            CaptureUtil.RenderHdr(cam, rt);
            var tex = CaptureUtil.ReadBack(rt, null, TextureFormat.RGB24);
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            cam.ResetAspect();
            RenderTexture.ReleaseTemporary(rt);
        }
    }
}
