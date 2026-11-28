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

        /// <summary>Stills of the saved scene, no save. -bwkOut DIR (default Captures/stills); -bwkHero also renders the hero
        /// shot into DIR (+ DIR/bg) and the comparisons into DIR/compare.</summary>
        public static void CaptureStillsBatch()
        {
            try
            {
                string dir = ArgValue("-bwkOut") ?? OutDir;
                CaptureStills(dir);
                if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-bwkHero") >= 0)
                    CaptureHero(dir, dir == OutDir ? CompareDir : dir + "/compare");
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] capture failed: " + e); EditorApplication.Exit(1); }
        }

        /// <summary>Renderers of the mascot model under the runner's Visual (hidden for background-only stills).</summary>
        static List<Renderer> MascotRenderers(RunnerController runner)
        {
            var list = new List<Renderer>();
            if (runner != null && runner.visual != null)
                foreach (Transform c in runner.visual)
                    if (c.name.Contains("Mascot"))
                        list.AddRange(c.GetComponentsInChildren<Renderer>().Where(r => r.enabled));
            return list;
        }

        /// <summary>Renders dir/file and, with the mascot model hidden, dir/bg/file (owner brief 2026-11-26: background-only
        /// comparisons so the scenery can be judged on its own; water / splash FX stay visible).</summary>
        static void RenderWithBackground(Camera cam, int w, int h, string dir, string file, List<Renderer> mascot)
        {
            Render(cam, w, h, $"{dir}/{file}");
            Directory.CreateDirectory($"{dir}/bg");
            foreach (var r in mascot) r.enabled = false;
            try { Render(cam, w, h, $"{dir}/bg/{file}"); }
            finally { foreach (var r in mascot) r.enabled = true; }
        }

        public static void HeroBatch()
        {
            try
            {
                string dir = ArgValue("-bwkOut");   // lead 20:40: optional, e.g. a baseline of the saved scene
                if (dir != null) CaptureHero(dir, dir + "/compare"); else CaptureHero();
                EditorApplication.Exit(0);
            }
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
                // lead 8d2d815d 2026-11-27 19:30 (owner: ChatGPT's experimental S2 optics patches, "use the protected preview,
                // enable only for S2"): optional -bwkS2Optics drum|water|both = _S2OpticsPreview 1 on the in-memory BWK/DrumWall
                // and / or BWK/Water materials of this preview only (the shaders confine it to the door drum / S2 water zone);
                // reset to 0 before exit and never saved, so builds and other previews keep the legacy look
                ApplyS2OpticsPreview(ArgValue("-bwkS2Optics"));
                CaptureHero(outDir, outDir);
                // lead 2026-11-26 17:55: optional -bwkStills = also render every section still (+ bg/) of the in-memory
                // refreshed level into DIR/stills (no save, ~5 extra minutes), so one preview shows a change in all sections
                if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-bwkStills") >= 0)
                    CaptureStills(outDir + "/stills");
                // lead 15a68124 2026-11-27 17:00 (owner 16:55 "show me mascot-only front / side / rear previews"): optional
                // -bwkMascotViews = also render the mascot ALONE (everything else hidden, neutral backdrop) from rear / side /
                // front / three-quarter with the in-memory refreshed materials into DIR/mascot (M1..M4, the S2ProofViewsBatch
                // cameras), so the character artist judges the whole plush look without a lead build (~20 s extra)
                if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-bwkMascotViews") >= 0)
                    CaptureMascotViews(outDir + "/mascot");
                ResetS2OpticsPreview();
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { ResetS2OpticsPreview(); Debug.LogError("[BWK] agent preview failed: " + e); EditorApplication.Exit(1); }
        }

        static readonly List<Material> s2OpticsTouched = new List<Material>();

        /// <summary>-bwkS2Optics drum|water|both: in-memory only (see AgentPreviewBatch).</summary>
        static void ApplyS2OpticsPreview(string mode)
        {
            if (string.IsNullOrEmpty(mode)) return;
            bool drum = mode == "drum" || mode == "both", water = mode == "water" || mode == "both";
            var seen = new HashSet<Material>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                foreach (var m in r.sharedMaterials)
                {
                    if (m == null || m.shader == null || !seen.Add(m) || !m.HasProperty("_S2OpticsPreview")) continue;
                    bool hit = (drum && m.shader.name == "BWK/DrumWall") || (water && m.shader.name == "BWK/Water");
                    if (!hit) continue;
                    m.SetFloat("_S2OpticsPreview", 1f);
                    s2OpticsTouched.Add(m);
                }
            Debug.Log("[BWK] S2 optics preview '" + mode + "' ON (in memory, not saved): "
                      + string.Join(", ", s2OpticsTouched.Select(m => m.name + " [" + m.shader.name + "]")));
        }

        static void ResetS2OpticsPreview()
        {
            foreach (var m in s2OpticsTouched) if (m != null) m.SetFloat("_S2OpticsPreview", 0f);
            s2OpticsTouched.Clear();
        }

        /// <summary>Mascot alone (M1 rear, M2 side right, M3 front, M4 three-quarter) at the S2 hero spot in the Slide pose,
        /// same cameras / backdrop as S2ProofViewsBatch; used by AgentPreviewBatch -bwkMascotViews (no save).</summary>
        static void CaptureMascotViews(string dir)
        {
            Directory.CreateDirectory(dir);
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var cam = Camera.main;
            if (runner == null || cam == null) { Debug.LogWarning("[BWK] mascot views: runner / camera missing"); return; }
            var brain = cam.GetComponent<CinemachineBrain>();
            bool brainOn = brain != null && brain.enabled;
            if (brain) brain.enabled = false;
            try
            {
                runner.TeleportTo(SceneBuilder.HeroMouthDistance, 0f);
                var animator = runner.GetComponentInChildren<Animator>();
                AnimationClip slide = null;
                if (animator != null && animator.runtimeAnimatorController != null)
                    slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                var mascot = MascotRenderers(runner);
                if (mascot.Count == 0) { Debug.LogWarning("[BWK] mascot views: no mascot renderers"); return; }
                var mset = new HashSet<Renderer>(mascot);
                var fr = runner.Frame;
                Vector3 fwd = Vector3.ProjectOnPlane(fr.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd), up = Vector3.up;
                var mb = mascot[0].bounds;
                foreach (var r in mascot) mb.Encapsulate(r.bounds);
                Vector3 mc = mb.center; float mh = Mathf.Max(mb.size.y, 0.4f), md = mh * 2.5f;
                var mviews = new List<(string name, Vector3 pos, Vector3 look)>
                {
                    ("M1_mascot_rear", mc - fwd * md + up * mh * 0.35f, mc),
                    ("M2_mascot_side_right", mc + right * md + up * mh * 0.15f, mc),
                    ("M3_mascot_front", mc + fwd * md + up * mh * 0.2f, mc),
                    ("M4_mascot_three_quarter", mc + (fwd - right).normalized * md + up * mh * 0.3f, mc),
                };
                RenderMascotAlone(cam, mset, mviews, up, dir, "");
                Debug.Log("[BWK] mascot views (M1 rear, M2 side, M3 front, M4 three-quarter) written to " + Path.GetFullPath(dir));
            }
            finally { if (brain) brain.enabled = brainOn; }
        }

        /// <summary>
        /// Lead tool (no scene save): like AgentPreviewBatch, but swaps the scene mascot for a CANDIDATE model shown in its
        /// rest pose (= the seated hero pose), so the owner can judge a new mascot in the real game before it replaces
        /// SK_Mascot.fbx. Run via: Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.MascotCandidateBatch lead_mascot
        ///   -bwkOut Captures/agents/_lead_mascot -bwkMascot Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_v4.fbx
        /// </summary>
        public static void MascotCandidateBatch()
        {
            try
            {
                string outDir = ArgValue("-bwkOut") ?? "Captures/agents/_lead_mascot";
                string fbx = ArgValue("-bwkMascot") ?? "Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_v4.fbx";
                TextureGenerator.Run();
                MaterialLibrary.Run();
                if (AssetImporter.GetAtPath(fbx) is ModelImporter mi)
                {
                    // same M_* project materials as the in-game mascot (embedded FBX materials remapped by name)
                    mi.materialLocation = ModelImporterMaterialLocation.InPrefab;
                    mi.SearchAndRemapMaterials(ModelImporterMaterialName.BasedOnMaterialName, ModelImporterMaterialSearch.Everywhere);
                    ModelImportRules.RemapVersionedMaterials(mi, fbx);   // SK_Mascot_v5 -> its own *_v5 materials (v4 keeps M_*)
                    mi.SaveAndReimport();
                }
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                SceneBuilder.PreviewRefreshDomains();
                SwapMascot(fbx);
                CaptureHero(outDir, outDir);
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] mascot candidate preview failed: " + e); EditorApplication.Exit(1); }
        }

        static void SwapMascot(string fbx)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(fbx);
            if (prefab == null) throw new System.Exception("candidate mascot not found: " + fbx);
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var old = runner != null && runner.visual != null ? runner.visual.Find("SK_Mascot") : null;
            if (old == null) throw new System.Exception("scene mascot SK_Mascot not found under the runner's Visual");
            var m = (GameObject)Object.Instantiate(prefab);
            m.name = "SK_Mascot_Candidate";
            m.transform.SetParent(old.parent, false);
            m.transform.localPosition = old.localPosition;
            // lead 2026-11-27: this preview REMOVES the Animator, and an Animator-less FBX rest pose of a correct export (no
            // BWK_RIG_TEST_YAW, see build_mascot_rig.py) faces the camera -> -bwkMascotYaw DEG, default 180 for correct exports;
            // pass 0 only for test-yaw exports like SK_Mascot_v4.fbx. In-game (with the Animator) a correct export needs
            // AnimatorBuilder.ModelYaw 0. Never copy the scene mascot's turn (v4 carries ModelYaw 180).
            m.transform.localRotation = Quaternion.Euler(0f, float.Parse(ArgValue("-bwkMascotYaw") ?? "180", System.Globalization.CultureInfo.InvariantCulture), 0f);
            m.transform.localScale = old.localScale;
            // No Animator: the old controller's clips belong to the old skeleton proportions; the candidate's rest pose
            // is its seated hero pose, and CaptureHero skips clip sampling when no Animator is found.
            foreach (var a in m.GetComponentsInChildren<Animator>(true)) Object.DestroyImmediate(a);
            foreach (var r in m.GetComponentsInChildren<Renderer>(true))
            {
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                r.receiveShadows = true;
                if (r is SkinnedMeshRenderer smr) smr.updateWhenOffscreen = true;
            }
            Object.DestroyImmediate(old.gameObject);
            var driver = runner.GetComponent<MascotAnimatorDriver>();
            if (driver != null) { driver.squashRoot = m.transform; driver.animator = null; }
            Debug.Log("[BWK] candidate mascot swapped in (rest pose): " + fbx);
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
                // lead 2026-11-26 21:45 (owner 21:25: keep PORTRAIT, optimise the gameplay camera to reveal more scenery):
                //   -bwkCamDistances "35,105.5,215" renders every variant at each track distance -> cam_d<d>_v<i>_9x16.png
                var dists = new List<float>();
                string dspec = ArgValue("-bwkCamDistances");
                if (!string.IsNullOrEmpty(dspec))
                    foreach (var s in dspec.Split(','))
                        dists.Add(float.Parse(s.Trim(), System.Globalization.CultureInfo.InvariantCulture));
                bool multi = dists.Count > 0;
                if (!multi) dists.Add(best);
                foreach (float d in dists)
                {
                    if (multi) { PoseHero(runner, d); HideCollectedItems(runner); }
                    for (int i = 0; i < variants.Count; i++)
                    {
                        var v = variants[i];
                        rig.distanceBackPortrait = v[0]; rig.heightPortrait = v[1]; rig.pitchDownPortrait = v[2]; rig.fovPortrait = v[3];
                        rig.aspectOverride = 720f / 1280f;
                        rig.Snap();
                        var lens = rig.vcam.Lens;
                        cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                        cam.fieldOfView = lens.FieldOfView;
                        string path = multi ? $"{outDir}/cam_d{d:000}_v{i}_9x16.png" : $"{outDir}/cam_v{i}_9x16.png";
                        Render(cam, 720, 1280, path);
                        if (!multi && refCrop != null) SaveSideBySide(new[] { refCrop, LoadPng(path) }, $"{outDir}/cam_v{i}_vs_reference_9x16.png");
                        Debug.Log($"[BWK] camera variant v{i} at {d:F1} m: back {v[0]} height {v[1]} pitch {v[2]} fov {v[3]}");
                    }
                }
                if (multi) PoseHero(runner, best);
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

        /// <summary>
        /// Lead tool (no scene save; owner takeover brief 2026-11-26 20:15, item 5 "correct the comparison camera first"):
        /// the reference hero frame (3.0 s) is taken AT the washing-machine door - thick gold hatch rim at both screen edges,
        /// pink roller upper left, blue machinery + gold pipe left - while hero_16x9 is 65 m past that door (105.5 m).
        /// Renders the UNCHANGED gameplay rig (2.75 / 1.3 / 10 / 58) with the mascot at several track distances / lanes and
        /// logs where the door ring (SM_MouthRing_r7 at 40 m) lands on the 1280x720 frame (outer circle centre + extent),
        /// so the matching comparison position is measured instead of guessed.
        ///   -bwkDistances "32,33,34" (default 30-39 step 1)  -bwkLanes "0,-1.15" (default 0,-1.15)  -bwkOut DIR
        /// </summary>
        public static void MouthSearchBatch()
        {
            try
            {
                string outDir = ArgValue("-bwkOut") ?? "Captures/agents/_lead_mouth";
                Directory.CreateDirectory(outDir);
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
                var cam = Camera.main;
                if (runner == null || rig == null || cam == null) throw new System.Exception("scene objects missing");
                SceneBuilder.ApplyHeroCamera(rig);
                var brain = cam.GetComponent<CinemachineBrain>();
                if (brain) brain.enabled = false;
                runner.track.Rebuild();
                var ring = GameObject.Find("SM_MouthRing_r7");
                Bounds rb = default; bool haveRing = false;
                if (ring != null)
                    foreach (var r in ring.GetComponentsInChildren<Renderer>())
                    { if (!haveRing) { rb = r.bounds; haveRing = true; } else rb.Encapsulate(r.bounds); }
                Debug.Log($"[BWK] mouth ring {(haveRing ? $"centre {rb.center} extents {rb.extents}" : "NOT FOUND")}");
                var animator = runner.GetComponentInChildren<Animator>();
                AnimationClip slide = animator != null && animator.runtimeAnimatorController != null
                    ? animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide") : null;
                foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                    if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);
                float[] Parse(string s, float[] def) => string.IsNullOrEmpty(s) ? def
                    : s.Split(',').Select(x => float.Parse(x.Trim(), System.Globalization.CultureInfo.InvariantCulture)).ToArray();
                var dists = Parse(ArgValue("-bwkDistances"), new[] { 30f, 31f, 32f, 33f, 34f, 35f, 36f, 37f, 38f, 39f });
                var lanes = Parse(ArgValue("-bwkLanes"), new[] { 0f, -SlideProfile.LaneWidth });
                foreach (float lat in lanes)
                    foreach (float d in dists)
                    {
                        runner.TeleportTo(d, lat);
                        if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                        SimulateSlideFX(runner);
                        rig.aspectOverride = 1280f / 720f;
                        rig.Snap();
                        var lens = rig.vcam.Lens;
                        cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                        cam.fieldOfView = lens.FieldOfView;
                        string tag = ("d" + d.ToString("00.0", System.Globalization.CultureInfo.InvariantCulture) + "_l"
                                      + lat.ToString("+0.00;-0.00;0", System.Globalization.CultureInfo.InvariantCulture)).Replace('.', 'p');
                        Render(cam, 1280, 720, $"{outDir}/mouth_{tag}.png");
                        if (!haveRing) continue;
                        // outer circle of the ring in its own plane (ring forward = track forward), R = vertical half size
                        float R = rb.extents.y;
                        Vector3 c = rb.center, ax = ring.transform.right, ay = ring.transform.up;
                        float minX = 1e9f, maxX = -1e9f, minY = 1e9f, maxY = -1e9f; int behind = 0;
                        for (int i = 0; i < 72; i++)
                        {
                            float a = i * 5f * Mathf.Deg2Rad;
                            var px = ProjectPx(cam, c + (ax * Mathf.Cos(a) + ay * Mathf.Sin(a)) * R, 1280, 720, out bool front);
                            if (!front) { behind++; continue; }
                            minX = Mathf.Min(minX, px.x); maxX = Mathf.Max(maxX, px.x); minY = Mathf.Min(minY, px.y); maxY = Mathf.Max(maxY, px.y);
                        }
                        var cc = ProjectPx(cam, c, 1280, 720, out _);
                        Debug.Log($"[BWK] mouth {tag}: cam->ring {Vector3.Distance(cam.transform.position, c):F2} m, ring centre px ({cc.x:F0},{cc.y:F0}), " +
                                  $"outer x {minX:F0}..{maxX:F0} y {minY:F0}..{maxY:F0}, points behind cam {behind}");
                    }
                rig.aspectOverride = 0f;
                if (brain) brain.enabled = true;
                Debug.Log("[BWK] mouth search written to " + Path.GetFullPath(outDir));
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] mouth search failed: " + e); EditorApplication.Exit(1); }
        }

        /// <summary>
        /// Lead tool (no scene save): solves a COMPARISON-ONLY rear camera for the S2 hero frame (reference f_03.00s) instead of
        /// guessing it. Landmarks measured on the 1280x720 reference: door-ring outer rim leftmost (248,230) and rightmost
        /// (~1270,230) points, mascot pompom top (640,183), mascot body bottom (640,520). Grid search over the mascot's track
        /// distance d (lane 0), camera back / height / lateral offset, yaw / pitch and vertical FOV; logs the 5 best poses and
        /// renders the best one (+ the unchanged gameplay rig at the same d) into -bwkOut DIR. The gameplay rig is not touched.
        /// </summary>
        /// <summary>S2 comparison-only camera (R2_rear_S2_like_3s): mascot at SceneBuilder.HeroMouthDistance, camera back /
        /// height / lateral (m) from the runner, yaw / pitch (deg) on the flat track heading, vertical FOV. Solved 2026-11-26
        /// 20:25 by S2CameraSolveBatch (door ring both sides + mascot, rms 8.4 px). Re-solve after any S2 geometry change
        /// (2026-11-27: tunnel bend right inside the door) with -bwkSolveVP so the vanishing point counts too.</summary>
        public static float R2Back = 2.75f, R2Height = 1.0f, R2Lat = 0.3f, R2Yaw = -7f, R2Pitch = 6f, R2Fov = 58f;   // re-solved 2026-11-27 07:44 (lead cd16e551, lead_s2solve5, vpWeight 1.0) on the CLIMBING tunnel (S2RiseY 07:40) with the v5 mascot: rms 15.7 px, VP (770,213) vs ref (760,205), ring L (241,216) / R (1243,202) vs (248,230) / (1270,230). Before: 3.0 / 0.9 / 0.3 / -7 / 5 / 50 (06:52, rms 27.9, VP (793,272)); 2.5 / 1.1 / 0.3 / -8 / 10 / 58 at d 34.5 (06:13, rms 35.9)

        public static void S2CameraSolveBatch()
        {
            try
            {
                string outDir = ArgValue("-bwkOut") ?? "Captures/agents/_lead_mouth";
                // lead 2026-11-27: optional vanishing-point term (weight), reference VP ~(760,205) = tunnel centre ~50 m ahead
                float vpW = float.Parse(ArgValue("-bwkSolveVP") ?? "0", System.Globalization.CultureInfo.InvariantCulture);
                var vpTarget = new Vector2(760f, 205f);
                Directory.CreateDirectory(outDir);
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
                var cam = Camera.main;
                if (runner == null || rig == null || cam == null) throw new System.Exception("scene objects missing");
                SceneBuilder.ApplyHeroCamera(rig);
                var brain = cam.GetComponent<CinemachineBrain>();
                if (brain) brain.enabled = false;
                runner.track.Rebuild();
                // lead 2026-11-27: there can be several SM_MouthRing_r7 (e.g. the S7 portal chamber); GameObject.Find returned a
                // far one and the solve collapsed (rms 259 px) -> take the instance nearest the door (HallMouthD)
                var mouthPos = runner.track.Evaluate(SceneBuilder.HallMouthD).position;
                GameObject ring = null; float ringDist = float.MaxValue;
                // lead 2026-11-27 06:50: S2 pass 6 replaced the door ring at the mouth by the layered master SM_DoorHatch_s2
                // (SM_MouthRing_r7 stays only as its fallback) - accept either, nearest the door wins
                foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsSortMode.None))
                    if ((t.name == "SM_MouthRing_r7" || t.name == "SM_DoorHatch_s2") && (t.position - mouthPos).sqrMagnitude < ringDist) { ringDist = (t.position - mouthPos).sqrMagnitude; ring = t.gameObject; }
                if (ring == null) throw new System.Exception("door ring (SM_DoorHatch_s2 / SM_MouthRing_r7) not found");
                Debug.Log($"[BWK] S2 solve: door ring {ring.name} at {Mathf.Sqrt(ringDist):F1} m from the mouth point");
                Bounds rb = default; bool first = true;
                foreach (var r in ring.GetComponentsInChildren<Renderer>()) { if (first) { rb = r.bounds; first = false; } else rb.Encapsulate(r.bounds); }
                var rf = runner.track.Evaluate(SceneBuilder.HallMouthD);
                float R = rb.extents.y;
                Vector3 ringL = rb.center - rf.flatRight * R, ringR = rb.center + rf.flatRight * R;
                var animator = runner.GetComponentInChildren<Animator>();
                AnimationClip slide = animator != null && animator.runtimeAnimatorController != null
                    ? animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide") : null;
                var mascot = MascotRenderers(runner);
                var best = new List<(float cost, float d, float b, float h, float s, float yaw, float pitch, float fov)>();
                for (float d = 33f; d <= 37.01f; d += 0.25f)
                {
                    runner.TeleportTo(d, 0f);
                    if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                    // real posed extremes (skinned bounds are conservative and made the solved mascot ~25 % too small)
                    Vector3 top = Vector3.zero, bot = Vector3.zero; float topU = float.MinValue, botU = float.MaxValue;
                    var baked = new Mesh();
                    foreach (var mr in mascot)
                    {
                        Vector3[] vs; Matrix4x4 m;
                        if (mr is SkinnedMeshRenderer smr) { smr.BakeMesh(baked, true); vs = baked.vertices; m = Matrix4x4.TRS(smr.transform.position, smr.transform.rotation, Vector3.one); }
                        else { var mf = mr.GetComponent<MeshFilter>(); if (mf == null || mf.sharedMesh == null) continue; vs = mf.sharedMesh.vertices; m = mr.transform.localToWorldMatrix; }
                        foreach (var v in vs)
                        {
                            var wv = m.MultiplyPoint3x4(v);
                            float u = wv.y;
                            if (u > topU) { topU = u; top = wv; }
                            if (u < botU) { botU = u; bot = wv; }
                        }
                    }
                    Object.DestroyImmediate(baked);
                    if (d == 33f) Debug.Log($"[BWK] S2 solve: mascot top {top} bottom {bot} (height {topU - botU:F2} m)");
                    var f = runner.Frame;
                    Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
                    Vector3 basePos = runner.transform.position;
                    var baseRot = Quaternion.LookRotation(fwd, Vector3.up);
                    Vector3 vp = runner.track.Evaluate(Mathf.Min(d + 50f, runner.track.Length)).FlatPoint(0f, 2.3f);   // tunnel centre (TunnelCenter 2.3)
                    foreach (float fov in new[] { 50f, 58f, 66f })
                        for (float b = 2.25f; b <= 4.01f; b += 0.25f)
                            for (float h = 0.5f; h <= 1.61f; h += 0.1f)
                                for (float s = -1.2f; s <= 1.21f; s += 0.3f)
                                {
                                    Vector3 cp = basePos - fwd * b + Vector3.up * h + right * s;
                                    for (float yaw = -18f; yaw <= 18.01f; yaw += 1f)
                                        for (float pitch = -6f; pitch <= 18.01f; pitch += 1f)
                                        {
                                            var cr = baseRot * Quaternion.Euler(pitch, yaw, 0f);
                                            var pL = ProjectPose(cp, cr, fov, ringL, 1280, 720, out bool f1);
                                            var pR = ProjectPose(cp, cr, fov, ringR, 1280, 720, out bool f2);
                                            var pT = ProjectPose(cp, cr, fov, top, 1280, 720, out bool f3);
                                            var pB = ProjectPose(cp, cr, fov, bot, 1280, 720, out bool f4);
                                            if (!(f1 && f2 && f3 && f4)) continue;
                                            float cost = (pL - new Vector2(248f, 230f)).sqrMagnitude
                                                       + 0.5f * (pR - new Vector2(1270f, 230f)).sqrMagnitude
                                                       + (pT - new Vector2(640f, 183f)).sqrMagnitude
                                                       + (pB.y - 520f) * (pB.y - 520f) + 0.5f * (pB.x - 640f) * (pB.x - 640f);
                                            if (vpW > 0f) cost += vpW * (ProjectPose(cp, cr, fov, vp, 1280, 720, out _) - vpTarget).sqrMagnitude;
                                            if (best.Count < 5 || cost < best[best.Count - 1].cost)
                                            {
                                                best.Add((cost, d, b, h, s, yaw, pitch, fov));
                                                best.Sort((x, y) => x.cost.CompareTo(y.cost));
                                                if (best.Count > 5) best.RemoveAt(5);
                                            }
                                        }
                                }
                }
                foreach (var p in best)
                    Debug.Log($"[BWK] S2 solve: rms {Mathf.Sqrt(p.cost / (4.5f + vpW)):F1} px  d {p.d:F2} back {p.b:F2} height {p.h:F2} lat {p.s:F2} yaw {p.yaw:F0} pitch {p.pitch:F0} vfov {p.fov:F0}");
                var w = best[0];
                {   // where the solved pose puts the vanishing point and the door ring (compare with the reference VP ~(760,205))
                    runner.TeleportTo(w.d, 0f);
                    var f0 = runner.Frame;
                    Vector3 fw0 = Vector3.ProjectOnPlane(f0.forward, Vector3.up).normalized, rt0 = Vector3.Cross(Vector3.up, fw0);
                    Vector3 cp0 = runner.transform.position - fw0 * w.b + Vector3.up * w.h + rt0 * w.s;
                    var cr0 = Quaternion.LookRotation(fw0, Vector3.up) * Quaternion.Euler(w.pitch, w.yaw, 0f);
                    var pv = ProjectPose(cp0, cr0, w.fov, runner.track.Evaluate(Mathf.Min(w.d + 50f, runner.track.Length)).FlatPoint(0f, 2.3f), 1280, 720, out _);
                    var pl = ProjectPose(cp0, cr0, w.fov, ringL, 1280, 720, out _);
                    var pr = ProjectPose(cp0, cr0, w.fov, ringR, 1280, 720, out _);
                    Debug.Log($"[BWK] S2 solve best: VP ({pv.x:F0},{pv.y:F0}) vs reference (760,205); ring L ({pl.x:F0},{pl.y:F0}) vs (248,230); ring R ({pr.x:F0},{pr.y:F0}) vs (1270,230); vpWeight {vpW}");
                }
                runner.TeleportTo(w.d, 0f);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                SimulateSlideFX(runner);
                {
                    var f = runner.Frame;
                    Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
                    Vector3 cp = runner.transform.position - fwd * w.b + Vector3.up * w.h + right * w.s;
                    cam.transform.SetPositionAndRotation(cp, Quaternion.LookRotation(fwd, Vector3.up) * Quaternion.Euler(w.pitch, w.yaw, 0f));
                    cam.fieldOfView = w.fov;
                    RenderWithBackground(cam, 1280, 720, outDir, "R2_solved_16x9.png", mascot);
                }
                rig.aspectOverride = 1280f / 720f;
                rig.Snap();
                var lens = rig.vcam.Lens;
                cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                cam.fieldOfView = lens.FieldOfView;
                RenderWithBackground(cam, 1280, 720, outDir, "rig_at_solved_d_16x9.png", mascot);
                rig.aspectOverride = 0f;
                if (brain) brain.enabled = true;
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] S2 solve failed: " + e); EditorApplication.Exit(1); }
        }

        static Vector2 ProjectPose(Vector3 camPos, Quaternion camRot, float vfov, Vector3 world, int w, int h, out bool inFront)
        {
            var p = Quaternion.Inverse(camRot) * (world - camPos);
            inFront = p.z > 0.05f;
            float z = Mathf.Max(p.z, 0.05f);
            float f = h * 0.5f / Mathf.Tan(vfov * 0.5f * Mathf.Deg2Rad);
            return new Vector2(w * 0.5f + p.x / z * f, h * 0.5f - p.y / z * f);
        }

        /// <summary>Pinhole projection of a world point to w x h pixels (y down) through cam's pose and vertical FOV.</summary>
        static Vector2 ProjectPx(Camera cam, Vector3 world, int w, int h, out bool inFront)
        {
            var p = cam.transform.InverseTransformPoint(world);
            inFront = p.z > 0.05f;
            float z = Mathf.Max(p.z, 0.05f);
            float f = h * 0.5f / Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
            return new Vector2(w * 0.5f + p.x / z * f, h * 0.5f - p.y / z * f);
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
            var collectedHero = HideCollectedItems(runner);
            foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
            {
                rig.aspectOverride = w / (float)h;
                rig.Snap();
                var lens = rig.vcam.Lens;
                cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                cam.fieldOfView = lens.FieldOfView;
                RenderWithBackground(cam, w, h, stillsDir, $"hero_{tag}.png", MascotRenderers(runner));
            }
            foreach (var r in collectedHero) r.enabled = true;
            // S2 at the washing-machine door (lead 2026-11-26 20:25, owner takeover brief item 5 "correct the comparison
            // camera first"): the reference 3.0 s frame is taken at the door ring (40 m), hero_* above is 65 m past it.
            // hero_mouth = the UNCHANGED gameplay rig with the mascot at 35 m (what the player sees at the door);
            // R2_rear_S2_like_3s = comparison-only camera solved by S2CameraSolveBatch on the reference landmarks (door rim
            // left / right, mascot top / bottom; rms 8.4 px): 2.75 back, 1.0 up, 0.3 right, yaw -9, pitch 6, vFOV 58 -
            // the rig's own back / FOV, 0.3 m lower, 4 deg less pitch, turned 9 deg toward the door.
            runner.TeleportTo(SceneBuilder.HeroMouthDistance, 0f);
            if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
            SimulateSlideFX(runner);
            // lead 84b218d4 2026-11-27: coins the mascot has just collected in his lane vanish in play - hide them here too (the
            // s2p9a hero_mouth_9x16 showed a giant already-collected coin right in front of the portrait camera)
            var collectedMouth = HideCollectedItems(runner);
            foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
            {
                rig.aspectOverride = w / (float)h;
                rig.Snap();
                var lens = rig.vcam.Lens;
                cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                cam.fieldOfView = lens.FieldOfView;
                RenderWithBackground(cam, w, h, stillsDir, $"hero_mouth_{tag}.png", MascotRenderers(runner));
            }
            {
                var f = runner.Frame;
                Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
                Vector3 cp = runner.transform.position - fwd * R2Back + Vector3.up * R2Height + right * R2Lat;
                cam.transform.SetPositionAndRotation(cp, Quaternion.LookRotation(fwd, Vector3.up) * Quaternion.Euler(R2Pitch, R2Yaw, 0f));
                cam.fieldOfView = R2Fov;
                RenderWithBackground(cam, 1280, 720, stillsDir, "R2_rear_S2_like_3s_16x9.png", MascotRenderers(runner));
            }
            foreach (var r in collectedMouth) r.enabled = true;
            rig.aspectOverride = 0f;
            runner.TeleportTo(best, 0f);
            rig.Snap();
            if (brain) brain.enabled = true;

            if (!File.Exists(RefRear)) { Debug.LogWarning("[BWK] reference frame missing - comparison skipped"); return; }
            var refTex = LoadPng(RefRear);
            SaveSideBySide(new[] { Resize(refTex, 1280, 720), LoadPng($"{stillsDir}/R2_rear_S2_like_3s_16x9.png") }, $"{compareDir}/R2_vs_reference_16x9.png");
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
        public static void CaptureStills() => CaptureStills(OutDir);

        /// <summary>Every still is written twice: outDir/NAME (normal) and outDir/bg/NAME (mascot hidden).</summary>
        public static void CaptureStills(string outDir)
        {
            if (EditorSceneManager.GetActiveScene().path != SceneBuilder.ScenePath)
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
            Directory.CreateDirectory(outDir);
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            var cam = Camera.main;
            if (runner == null || rig == null || cam == null) { Debug.LogError("[BWK] capture: scene objects missing"); return; }
            var brain = cam.GetComponent<CinemachineBrain>();
            if (brain) brain.enabled = false;
            runner.track.Rebuild();
            float L = runner.track.Length;
            var mascot = MascotRenderers(runner);

            var animator = runner.GetComponentInChildren<Animator>();
            AnimationClip slide = null;
            if (animator != null && animator.runtimeAnimatorController != null)
                slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");

            foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);

            var shots = new (string name, float d, float lat)[]
            {
                ("01_hall_start", 16f, 0f), ("02_hall_curve", 36f, 0f), ("03_tunnel_entry", 55f, 0f),
                ("04_tunnel", 92f, 0f), ("05_tunnel_lane_left", 128f, -SlideProfile.LaneWidth), ("06_tunnel_lane_right", 170f, SlideProfile.LaneWidth),
                ("07_chambers", 215f, 0f), ("08_sweep", 250f, 0f), ("09_portal", L - 34f, 0f),
            };
            foreach (var s in shots)
            {
                runner.TeleportTo(s.d, s.lat);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                SimulateSlideFX(runner);
                var collected = HideCollectedItems(runner);
                foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
                {
                    rig.aspectOverride = w / (float)h;
                    rig.Snap();
                    var lens = rig.vcam.Lens;
                    cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                    cam.fieldOfView = lens.FieldOfView;
                    RenderWithBackground(cam, w, h, outDir, $"{s.name}_{tag}.png", mascot);
                }
                foreach (var r in collected) r.enabled = true;
            }

            // 10_finale (lead 2026-11-26, owner corrections 7 + 8): the finishing sequence's front-facing celebration exactly as
            // the game shows it - the mascot at rest in front of the golden portal, turned toward the rear gameplay camera,
            // which has eased into its finale framing (RunnerCameraRig finale offsets). The game's version of the reference's
            // 14.5 s composition = the S7 comparison still (section_triptych.sh prefers it).
            {
                runner.TeleportTo(runner.FinishRestDistance, 0f);
                runner.PoseFinishForCapture(180f);
                AnimationClip cel = animator != null && animator.runtimeAnimatorController != null
                    ? animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Celebrate") : null;
                if (cel != null) cel.SampleAnimation(animator.gameObject, cel.length * 0.45f);
                else if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                var fxRoot = runner.GetComponentInChildren<SplashFX>();
                if (fxRoot != null) foreach (var ps in fxRoot.GetComponentsInChildren<ParticleSystem>()) ps.Clear(true);
                foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
                {
                    rig.aspectOverride = w / (float)h;
                    rig.SnapFinale();
                    var lens = rig.vcam.Lens;
                    cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                    cam.fieldOfView = lens.FieldOfView;
                    RenderWithBackground(cam, w, h, outDir, $"10_finale_{tag}.png", mascot);
                }
                runner.PoseFinishForCapture(0f);
                rig.Snap();
            }

            // Front-facing comparison angles (reference 3.75-15 s camera) - comparison only, never used in gameplay.
            // C4 / C5 (2026-11-26): front angles for video sections S4 (first sock window, 6-7 s) and S6 (chamber tunnel 2,
            // 9-12.75 s), so every section of Docs/VideoCoverageChecklist.md has a comparable camera angle.
            foreach (var (name, d) in new[] { ("C1_front_tunnel_like_5s", 100f), ("C4_front_window_like_7s", 190f), ("C2_front_chambers_like_10s", 220f),
                                              ("C5_front_chambers2_like_11s", 280f), ("C3_front_portal_like_14s", L - 22f) })
            {
                runner.TeleportTo(d, 0f);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                var f = runner.Frame;
                Vector3 camPos = runner.transform.position + f.forward * 2.6f + f.flatUp * 0.95f;
                cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(runner.transform.position + f.flatUp * 0.55f - camPos, f.flatUp));
                cam.fieldOfView = 46f;
                // A coin / gem right in front of the front camera hid the mascot (2026-11-26): hide track items within 4 m of
                // the camera for this comparison still only.
                var hiddenItems = new List<Renderer>();
                foreach (var it in Object.FindObjectsByType<BubbleWash.TrackItem>(FindObjectsSortMode.None))
                    if ((it.transform.position - camPos).sqrMagnitude < 16f)
                        foreach (var r in it.GetComponentsInChildren<Renderer>())
                            if (r.enabled) { r.enabled = false; hiddenItems.Add(r); }
                RenderWithBackground(cam, 1280, 720, outDir, $"{name}_16x9.png", mascot);
                foreach (var r in hiddenItems) r.enabled = true;
            }

            // R stills (2026-11-26, owner: "correct the S3 comparison camera so the new scenery can be evaluated accurately"):
            // REFERENCE-MATCHED front comparison cameras from the solved 8.25 s video camera
            // (Captures/agents/environment/shot0825/camera.json): 2.6 m ahead of the mascot, 1.3 m above the slide, 0.3 m to
            // travel-right, vertical FOV 52, aimed so the mascot centre lands at (522,397) of 1280x720 (camera turned 9.1 deg
            // right and 2.9 deg up from the mascot) - the video's lens sees the upper tunnel the C stills miss. R3 at 158 m
            // looks back over the S3 star tunnel (C1 at 100 m looked back at 60-100 m). Comparison only, never gameplay.
            foreach (var (name, d) in new[] { ("R3_front_S3_like_5s", 158f), ("R4_front_S4_like_7s", 190f),
                                              ("R5_front_S5_like_8s", 220f), ("R6_front_S6_like_11s", 280f) })
            {
                runner.TeleportTo(d, 0f);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                var f = runner.Frame;
                Vector3 camPos = runner.transform.position + f.forward * 2.6f + f.flatUp * 1.3f + f.flatRight * 0.3f;
                Vector3 centre = runner.transform.position + f.flatUp * 0.6f;
                cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(centre - camPos, f.flatUp) * Quaternion.Euler(-2.9f, 9.1f, 0f));
                cam.fieldOfView = 52f;
                var hiddenR = new List<Renderer>();
                foreach (var it in Object.FindObjectsByType<BubbleWash.TrackItem>(FindObjectsSortMode.None))
                    if ((it.transform.position - camPos).sqrMagnitude < 16f)
                        foreach (var r in it.GetComponentsInChildren<Renderer>())
                            if (r.enabled) { r.enabled = false; hiddenR.Add(r); }
                RenderWithBackground(cam, 1280, 720, outDir, $"{name}_16x9.png", mascot);
                foreach (var r in hiddenR) r.enabled = true;
            }
            rig.aspectOverride = 0f;
            if (brain) brain.enabled = true;
            Debug.Log("[BWK] Stills written to " + Path.GetFullPath(outDir) + " (+ bg/ with the mascot hidden)");
        }

        /// <summary>
        /// Lead 84b218d4 / ffbcca5a 2026-11-27 (owner 10:48 + 12:30: "prove it is real 3D"): renders the S2 door area of the SAVED
        /// scene (nothing is saved) with the mascot at HeroMouthDistance from 5 camera angles (A matched gameplay-rear comparison
        /// camera R2, B high rear, C side, D inside the door looking back, E wide hall view): colour with the mascot, colour with
        /// the mascot hidden (_nomascot), and NEUTRAL CLAY (_clay: every material = one grey URP Lit, all scene lights / fog /
        /// volumes off, one white key light + flat grey ambient, camera-facing particle sprites hidden). Plus the mascot ALONE
        /// (everything else hidden) from 4 sides in colour and clay (M1..M4), and geometry_audit.txt / .csv: every renderer seen
        /// by the 5 cameras within 90 m, its mesh / triangle count / size, and whether it is a flat card or a billboard sprite.
        ///   Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.S2ProofViewsBatch lead_s2proof -bwkOut Captures/proof_s2p9
        /// </summary>
        public static void S2ProofViewsBatch()
        {
            try
            {
                string outDir = ArgValue("-bwkOut") ?? "Captures/proof";
                Directory.CreateDirectory(outDir);
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var cam = Camera.main;
                if (runner == null || cam == null) { Debug.LogError("[BWK] proof: scene objects missing"); EditorApplication.Exit(1); return; }
                var brain = cam.GetComponent<CinemachineBrain>();
                if (brain) brain.enabled = false;
                runner.track.Rebuild();
                foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                    if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);
                runner.TeleportTo(SceneBuilder.HeroMouthDistance, 0f);
                var animator = runner.GetComponentInChildren<Animator>();
                AnimationClip slide = null;
                if (animator != null && animator.runtimeAnimatorController != null)
                    slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                SimulateSlideFX(runner);
                HideCollectedItems(runner);   // as in play: coins just collected in his lane are gone
                var mascot = MascotRenderers(runner);
                var mset = new HashSet<Renderer>(mascot);
                var fr = runner.Frame;
                Vector3 fwd = Vector3.ProjectOnPlane(fr.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd), up = Vector3.up;
                Vector3 p = runner.transform.position;
                Quaternion r2 = Quaternion.LookRotation(fwd, up) * Quaternion.Euler(R2Pitch, R2Yaw, 0f);
                var views = new (string name, Vector3 pos, Vector3 look, float fov)[]
                {
                    ("A_matched_R2", p - fwd * R2Back + up * R2Height + right * R2Lat, Vector3.zero, R2Fov),
                    // s2p9a: B at -6.5 / 4.2 / -3.2 m sat behind pale hall panels -> moved into the open hall (E's side)
                    ("B_high_rear_right", p - fwd * 8f + up * 3.2f + right * 1.0f, p + fwd * 6f + up * 0.8f, 60f),
                    ("C_side_right_low", p - fwd * 1.0f + up * 1.3f + right * 3.4f, p + fwd * 2.5f - right * 0.8f + up * 0.5f, 70f),
                    ("D_ahead_looking_back", p + fwd * 7f + up * 1.6f + right * 0.4f, p - fwd * 3f + up * 0.6f, 62f),
                    ("E_hall_wide_from_behind", p - fwd * 14f + up * 5.5f + right * 1.5f, p + fwd * 4f + up * 1.2f, 58f),
                };
                // 1) colour, mascot visible + hidden
                foreach (var v in views) { PlaceProofCam(cam, v, r2, up); Render(cam, 1280, 720, $"{outDir}/{v.name}.png"); }
                foreach (var r in mascot) r.enabled = false;
                try { foreach (var v in views) { PlaceProofCam(cam, v, r2, up); Render(cam, 1280, 720, $"{outDir}/{v.name}_nomascot.png"); } }
                finally { foreach (var r in mascot) r.enabled = true; }
                // 2) geometry audit of everything the 5 cameras see (before any material swap)
                WriteGeometryAudit(cam, views, r2, up, p, mset, outDir);
                // 3) the mascot alone (separate skinned asset): everything else hidden, neutral backdrop
                var mviews = new List<(string name, Vector3 pos, Vector3 look)>();
                if (mascot.Count > 0)
                {
                    var mb = mascot[0].bounds;
                    foreach (var r in mascot) mb.Encapsulate(r.bounds);
                    Vector3 mc = mb.center; float mh = Mathf.Max(mb.size.y, 0.4f), md = mh * 2.5f;
                    mviews.Add(("M1_mascot_rear", mc - fwd * md + up * mh * 0.35f, mc));
                    mviews.Add(("M2_mascot_side_right", mc + right * md + up * mh * 0.15f, mc));
                    mviews.Add(("M3_mascot_front", mc + fwd * md + up * mh * 0.2f, mc));
                    mviews.Add(("M4_mascot_three_quarter", mc + (fwd - right).normalized * md + up * mh * 0.3f, mc));
                }
                RenderMascotAlone(cam, mset, mviews, up, outDir, "");
                // 4) NEUTRAL CLAY (s2p9 clay was still tinted pink / lavender by the coloured scene lights + probes)
                var clay = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                clay.SetColor("_BaseColor", new Color(0.72f, 0.72f, 0.72f));
                clay.SetFloat("_Smoothness", 0.15f);
                clay.SetFloat("_EnvironmentReflections", 0f); clay.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
                clay.SetFloat("_SpecularHighlights", 0f); clay.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
                var all = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None);
                var saved = all.Select(r => r.sharedMaterials).ToArray();
                var sprites = all.Where(r => r.enabled && IsBillboard(r)).ToList();
                var vols = Object.FindObjectsByType<UnityEngine.Rendering.Volume>(FindObjectsSortMode.None).Where(v => v.enabled).ToArray();
                var lights = Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Where(l => l.enabled).ToList();
                bool fog = RenderSettings.fog;
                var ambMode = RenderSettings.ambientMode; var ambCol = RenderSettings.ambientLight; var probe = RenderSettings.ambientProbe;
                GameObject key = null;
                try
                {
                    RenderSettings.fog = false;
                    foreach (var v in vols) v.enabled = false;
                    foreach (var l in lights) l.enabled = false;
                    key = new GameObject("BWK_ClayKeyLight");
                    var kl = key.AddComponent<Light>();
                    kl.type = LightType.Directional; kl.color = Color.white; kl.intensity = 1.25f; kl.shadows = LightShadows.Soft;
                    key.transform.rotation = Quaternion.LookRotation((fwd * 0.55f - up + right * 0.45f).normalized, up);
                    RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
                    RenderSettings.ambientLight = new Color(0.46f, 0.46f, 0.48f);
                    var sh = new UnityEngine.Rendering.SphericalHarmonicsL2();
                    sh.AddAmbientLight(new Color(0.46f, 0.46f, 0.48f));
                    RenderSettings.ambientProbe = sh;
                    foreach (var r in sprites) r.enabled = false;
                    foreach (var r in all) r.sharedMaterials = Enumerable.Repeat(clay, Mathf.Max(1, r.sharedMaterials.Length)).ToArray();
                    foreach (var v in views) { PlaceProofCam(cam, v, r2, up); Render(cam, 1280, 720, $"{outDir}/{v.name}_clay.png"); }
                    RenderMascotAlone(cam, mset, mviews, up, outDir, "_clay");
                }
                finally
                {
                    for (int i = 0; i < all.Length; i++) if (all[i] != null) all[i].sharedMaterials = saved[i];
                    foreach (var r in sprites) if (r != null) r.enabled = true;
                    if (key != null) Object.DestroyImmediate(key);
                    foreach (var l in lights) if (l != null) l.enabled = true;
                    RenderSettings.fog = fog;
                    RenderSettings.ambientMode = ambMode; RenderSettings.ambientLight = ambCol; RenderSettings.ambientProbe = probe;
                    foreach (var v in vols) v.enabled = true;
                }
                Debug.Log("[BWK] S2 proof views + geometry audit written to " + Path.GetFullPath(outDir));
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] S2 proof views failed: " + e); EditorApplication.Exit(1); }
        }

        static void PlaceProofCam(Camera cam, (string name, Vector3 pos, Vector3 look, float fov) v, Quaternion r2, Vector3 up)
        {
            cam.transform.SetPositionAndRotation(v.pos, v.name.StartsWith("A_") ? r2 : Quaternion.LookRotation(v.look - v.pos, up));
            cam.fieldOfView = v.fov;
        }

        /// <summary>Camera-facing sprites (billboard / stretched particles, line / trail / sprite / billboard renderers).</summary>
        static bool IsBillboard(Renderer r)
        {
            if (r is ParticleSystemRenderer psr) return psr.renderMode != ParticleSystemRenderMode.Mesh;
            return r is LineRenderer || r is TrailRenderer || r is SpriteRenderer || r is BillboardRenderer;
        }

        /// <summary>Renders only the mascot's own renderers (everything else disabled) on a neutral backdrop.</summary>
        static void RenderMascotAlone(Camera cam, HashSet<Renderer> mset, List<(string name, Vector3 pos, Vector3 look)> mviews,
                                      Vector3 up, string outDir, string suffix)
        {
            if (mviews.Count == 0) return;
            var off = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.enabled && !mset.Contains(r)).ToList();
            var flags = cam.clearFlags; var bg = cam.backgroundColor; float fov = cam.fieldOfView;
            foreach (var r in off) r.enabled = false;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.16f, 0.16f, 0.19f);
            try
            {
                foreach (var mv in mviews)
                {
                    cam.transform.SetPositionAndRotation(mv.pos, Quaternion.LookRotation(mv.look - mv.pos, up));
                    cam.fieldOfView = 30f;
                    Render(cam, 1280, 720, $"{outDir}/{mv.name}{suffix}.png");
                }
            }
            finally
            {
                foreach (var r in off) if (r != null) r.enabled = true;
                cam.clearFlags = flags; cam.backgroundColor = bg; cam.fieldOfView = fov;
            }
        }

        static string ProofCategory(string k)
        {
            if (k.Contains("coin") || k.Contains("gem")) return "coins / gems";
            if (k.Contains("bubble")) return "bubbles";
            if (k.Contains("foam") || k.Contains("puff") || k.Contains("mound")) return "foam banks";
            if (k.Contains("splash") || k.Contains("crown") || k.Contains("spray") || k.Contains("droplet") || k.Contains("sparkle") || k.Contains("trail")) return "splash / sparkle FX";
            if (k.Contains("star")) return "neon stars";
            if (k.Contains("chevron") || k.Contains("arrow") || k.Contains("boost")) return "boost arrows";
            if (k.Contains("water") || k.Contains("flow")) return "water lane";
            if (k.Contains("rail") || k.Contains("slide") || k.Contains("track")) return "slide + rails";
            if (k.Contains("hatch") || k.Contains("door")) return "hatch";
            if (k.Contains("marquee") || k.Contains("ring") || k.Contains("bulb") || k.Contains("led")) return "gold light rings";
            if (k.Contains("roller") || k.Contains("bristle") || k.Contains("brush")) return "rollers";
            if (k.Contains("machin") || k.Contains("pipe") || k.Contains("gear") || k.Contains("valve") || k.Contains("console") || k.Contains("panel")) return "side machinery";
            if (k.Contains("drum") || k.Contains("tunnel") || k.Contains("wall") || k.Contains("mouth")) return "tunnel";
            return "other";
        }

        static string ProofPath(Transform t)
        {
            var parts = new List<string>();
            for (int i = 0; t != null && i < 4; i++, t = t.parent) parts.Insert(0, t.name);
            return string.Join("/", parts).Replace(",", " ");
        }

        /// <summary>geometry_audit.csv / .txt: every enabled renderer inside any of the 5 proof frustums (within 90 m), with its
        /// mesh, triangle count, local size and a FLAT flag (camera-facing sprite, a mesh of <= 4 triangles, or thinner than 2 %
        /// of its largest side) - so the owner sees honestly what is modelled geometry and what is a card / sprite.</summary>
        static void WriteGeometryAudit(Camera cam, (string name, Vector3 pos, Vector3 look, float fov)[] views, Quaternion r2, Vector3 up,
                                       Vector3 center, HashSet<Renderer> mset, string outDir)
        {
            var planes = new List<Plane[]>();
            foreach (var v in views) { PlaceProofCam(cam, v, r2, up); cam.aspect = 1280f / 720f; planes.Add(GeometryUtility.CalculateFrustumPlanes(cam)); }
            cam.ResetAspect();
            var csv = new List<string> { "category,flat,component,mode,mesh,triangles,size_x,size_y,size_z,material,shader,path" };
            var stats = new SortedDictionary<string, (int n, long tris, int flat, List<string> flatNames)>();
            var inv = System.Globalization.CultureInfo.InvariantCulture;
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                var b = r.bounds;
                if ((b.center - center).magnitude > 90f) continue;
                if (!planes.Any(pl => GeometryUtility.TestPlanesAABB(pl, b))) continue;
                Mesh mesh = null; string mode = "mesh";
                if (r is SkinnedMeshRenderer smr) { mesh = smr.sharedMesh; mode = "skinned mesh"; }
                else if (r is ParticleSystemRenderer psr) { mode = "particles " + psr.renderMode; if (psr.renderMode == ParticleSystemRenderMode.Mesh) mesh = psr.mesh; }
                else if (r is MeshRenderer) { var mf = r.GetComponent<MeshFilter>(); mesh = mf ? mf.sharedMesh : null; }
                else mode = r.GetType().Name;
                long tris = 0;
                if (mesh != null) for (int s = 0; s < mesh.subMeshCount; s++) tris += mesh.GetIndexCount(s) / 3;
                Vector3 sz = mesh != null && !(r is ParticleSystemRenderer) ? Vector3.Scale(mesh.bounds.size, r.transform.lossyScale) : b.size;
                sz = new Vector3(Mathf.Abs(sz.x), Mathf.Abs(sz.y), Mathf.Abs(sz.z));
                float mx = Mathf.Max(sz.x, Mathf.Max(sz.y, sz.z)), mn = Mathf.Min(sz.x, Mathf.Min(sz.y, sz.z));
                bool sprite = IsBillboard(r);
                bool flat = sprite || (mesh != null && !(r is ParticleSystemRenderer) && (tris <= 4 || (mx > 0.05f && mn / mx < 0.02f)));
                var m0 = r.sharedMaterial;
                string mat = m0 ? m0.name : "-", shader = m0 && m0.shader ? m0.shader.name : "-";
                string path = ProofPath(r.transform);
                string cat = mset.Contains(r) ? "mascot" : ProofCategory((path + " " + (mesh ? mesh.name : "") + " " + mat).ToLowerInvariant());
                csv.Add(string.Join(",", cat, flat ? (sprite ? "SPRITE" : "FLAT") : "3D", r.GetType().Name, mode, mesh ? mesh.name.Replace(",", " ") : "-",
                    tris.ToString(inv), sz.x.ToString("F2", inv), sz.y.ToString("F2", inv), sz.z.ToString("F2", inv), mat.Replace(",", " "), shader.Replace(",", " "), path));
                stats.TryGetValue(cat, out var st);
                if (st.flatNames == null) st.flatNames = new List<string>();
                st.n++; st.tris += tris;
                if (flat) { st.flat++; if (st.flatNames.Count < 10) st.flatNames.Add($"{path} [{mode}, {(mesh ? mesh.name : "-")}, {sz.x:F2} x {sz.y:F2} x {sz.z:F2} m, {mat}]"); }
                stats[cat] = st;
            }
            File.WriteAllLines($"{outDir}/geometry_audit.csv", csv);
            var txt = new List<string> { "S2 GEOMETRY AUDIT - every renderer the 5 proof cameras see (within 90 m of the mascot). 3D = modelled mesh;",
                "FLAT = a mesh of <= 4 triangles or thinner than 2 % of its largest side (card / plane); SPRITE = camera-facing particles / lines.", "" };
            foreach (var kv in stats)
            {
                txt.Add($"{kv.Key}: {kv.Value.n} renderers, {kv.Value.tris:N0} triangles, flat / sprite: {kv.Value.flat}");
                foreach (var f in kv.Value.flatNames) txt.Add("    flat: " + f);
            }
            File.WriteAllLines($"{outDir}/geometry_audit.txt", txt);
            Debug.Log("[BWK] geometry audit: " + string.Join(" | ", stats.Select(kv => $"{kv.Key} {kv.Value.n} ({kv.Value.flat} flat)")));
        }

        /// <summary>Rear stills place the mascot without playing the level, so coins / gems it would already have collected in
        /// its own lane (between the camera and the mascot) float in front of the lens - lead 2026-11-26 21:10: 07_chambers
        /// showed one filling the portrait frame. Hides those for the still (re-enable the returned renderers afterwards);
        /// items in the other lanes, which the player really sees passing by, stay visible.</summary>
        static List<Renderer> HideCollectedItems(RunnerController runner)
        {
            var hidden = new List<Renderer>();
            float d = runner.Distance, lat = runner.Lateral;
            foreach (var it in Object.FindObjectsByType<BubbleWash.TrackItem>(FindObjectsSortMode.None))
            {
                if (it.kind != TrackItemKind.Coin && it.kind != TrackItemKind.Gem) continue;
                if (it.distance < d - 4f || it.distance > d + 0.6f || Mathf.Abs(it.lateral - lat) > TrackItemRegistry.HitHalfWidth(it, runner.laneWidth)) continue;
                foreach (var r in it.GetComponentsInChildren<Renderer>())
                    if (r.enabled) { r.enabled = false; hidden.Add(r); }
            }
            if (hidden.Count > 0) Debug.Log($"[BWK] still at {d:F1} m: {hidden.Count} already-collected item renderers hidden");
            return hidden;
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
