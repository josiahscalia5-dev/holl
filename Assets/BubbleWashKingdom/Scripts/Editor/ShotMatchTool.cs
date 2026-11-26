using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Round 6 (2026-11-26) controlled reconstruction test: reference frame 8.25 s (video section S5, sock chambers and
    /// pink glass pipes), owned by the environment agent.
    /// SHOT-MATCHED SET DRESSING: the reference camera is solved from landmarks (mascot centre + height, tunnel vanishing
    /// point; lens from the chamber window's ellipse, Captures/agents/environment/shot0825/camera.json), then every library
    /// asset is placed by un-projecting its MEASURED reference screen position onto the tunnel wall (or a camera depth)
    /// and scaled so it covers its measured screen size. The level scene is opened but NEVER saved; -bwkSaveTest writes a
    /// dressed COPY (Test_S5_Shot0825.unity) where the shot module repeats along S5 (mirrored every other module) so the
    /// rear gameplay camera drives through dressed chambers in real time.
    /// Run: bash Tools/unity_run.sh BubbleWash.EditorTools.ShotMatchTool.RenderBatch env_shot_v1 -bwkTag v1 [-bwkSaveTest]
    /// </summary>
    public static class ShotMatchTool
    {
        const string OutDir = "Captures/agents/environment/shot0825";
        const string RefFrame = "Reference/frames4k_720/f_08.25s.png";
        public const string TestScenePath = "Assets/BubbleWashKingdom/Scenes/Test_S5_Shot0825.unity";
        const string Mach = "Assets/BubbleWashKingdom/Art/Models/Machinery/";
        const string Props = "Assets/BubbleWashKingdom/Art/Models/Props/";
        const string Lights = "Assets/BubbleWashKingdom/Art/Models/Lighting/";
        const string Mats = "Assets/BubbleWashKingdom/Art/Materials/";
        const float TunnelCenter = 2.3f;
        const int W = 1280, H = 720;
        static readonly string[] V2Models =
        {
            Mach + "SM_ChamberWindow_v2.fbx", Mach + "SM_GlassPipe_Pink_v2.fbx", Lights + "SM_NeonStarTube_v2.fbx",
        };

        // ---- reference camera solve inputs (measured on f_08.25s 1280x720; see camera.json) ----
        const float RunnerD = 207f;        // S5 start: lowest curvature of the 205-240 m stretch (~1 deg/m)
        const float VFov = 52f;            // chamber window ellipse 215 x 365 px flush on an r 3.4 wall -> 50-55 deg
        const float CamLateral = 0.30f;    // m toward the travel-right wall (rails: left slope 0.47 vs right 0.32)
        const float VpBack = 22f;          // tunnel opening (vanishing glow) = axis point this far behind the mascot
        static readonly Vector2 MascotPx = new Vector2(522f, 397f), VpPx = new Vector2(545f, 215f);
        const float MascotHeightPx = 385f; // pom-pom top y 205 .. foot bottom y 590
        const float ModulePeriod = 12.75f; // = SceneBuilder.GoldRingSpacing (one chamber module per gold-ring gap)

        enum Mode { Wall, Depth }

        class Item
        {
            public string name, model, mat;
            public Vector2 px;            // measured reference screen point (1280x720, y down)
            public float sizePx;          // measured screen height
            public float sizeM;           // model height that sizePx covers (0 = renderer bounds height)
            public Mode mode;
            public float radius;          // Wall: distance from the tunnel axis
            public float depth;           // Depth: camera-space depth (m)
            public float spin;            // degrees about the facing axis
            public bool worldUp;          // keep the model upright (pipe, gem)
            public float originUp;        // model origin this far below the matched point (pipe base, m at scale 1)
        }

        // Every entry = one landmark measured on Reference/frames4k_720/f_08.25s.png (grid sheet g_full.png).
        static List<Item> ShotItems()
        {
            var L = new List<Item>
            {
                new Item { name = "ChamberWindow", model = Mach + "SM_ChamberWindow_v2.fbx", px = new Vector2(245, 205), sizePx = 365, sizeM = 4.64f, mode = Mode.Wall, radius = 3.40f, worldUp = true },
                new Item { name = "PinkPipe", model = Mach + "SM_GlassPipe_Pink_v2.fbx", px = new Vector2(62, 150), sizePx = 140, sizeM = 1.10f, mode = Mode.Wall, radius = 3.35f, worldUp = true, originUp = 3.75f },
                new Item { name = "CurvyPipe", model = Mach + "SM_ChamberPipe.fbx", px = new Vector2(395, 150), sizePx = 230, sizeM = 3.9f, mode = Mode.Wall, radius = 3.7f, worldUp = true },
                new Item { name = "Gem", model = Props + "SM_Gem.fbx", px = new Vector2(1043, 222), sizePx = 125, mode = Mode.Wall, radius = 3.0f, worldUp = true, spin = 10f },
                new Item { name = "CoinA", model = Props + "SM_Coin.fbx", px = new Vector2(887, 352), sizePx = 60, mode = Mode.Wall, radius = 3.1f, worldUp = true },
                new Item { name = "CoinB", model = Props + "SM_Coin.fbx", px = new Vector2(1125, 378), sizePx = 105, mode = Mode.Wall, radius = 3.1f, worldUp = true, spin = 60f },
            };
            // neon outline tube stars on the wall / ceiling (x, y, height px, colour, tilt)
            var stars = new (float x, float y, float h, string c, float tilt)[]
            {
                (848, 62, 125, "Pink", -12f), (918, 237, 170, "Pink", 8f), (1205, 200, 260, "Pink", -15f), (730, 172, 80, "Cyan", 6f),
                (635, 207, 55, "Pink", -18f), (765, 278, 70, "Pink", 12f), (663, 275, 50, "Cyan", -4f), (525, 22, 60, "Yellow", 0f),
                (512, 160, 32, "Yellow", 0f), (515, 195, 18, "Yellow", 0f), (600, 120, 26, "Pink", 10f), (470, 120, 22, "Cyan", -8f),
            };
            int i = 0;
            foreach (var s in stars)
                L.Add(new Item { name = "Star" + (i++) + s.c, model = Lights + "SM_NeonStarTube_v2.fbx", mat = Mats + "M_Neon_" + s.c + ".mat",
                                 px = new Vector2(s.x, s.y), sizePx = s.h, sizeM = 1.693f, mode = Mode.Wall, radius = 4.08f, spin = s.tilt });
            // iridescent bubbles (x, y, diameter px, depth m)
            var bubbles = new (float x, float y, float d, float z)[]
            {
                (653, 120, 60, 7f), (828, 188, 40, 7.5f), (800, 333, 52, 5.5f), (1050, 318, 34, 6.5f), (733, 278, 32, 8f),
                (762, 237, 24, 9f), (1170, 125, 70, 5f), (720, 330, 18, 9f), (35, 355, 22, 3.2f),
            };
            i = 0;
            foreach (var b in bubbles)
                L.Add(new Item { name = "Bubble" + (i++), model = Props + "SM_Bubble.fbx", px = new Vector2(b.x, b.y), sizePx = b.d, mode = Mode.Depth, depth = b.z });
            return L;
        }

        struct Cam { public Vector3 pos; public Quaternion rot; public float fpx; }

        public static void RenderBatch()
        {
            try { Run(); EditorApplication.Exit(0); }
            catch (System.Exception e) { Debug.LogError("[BWK] shot0825 failed: " + e); EditorApplication.Exit(1); }
        }

        static string Arg(string key)
        {
            var a = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == key) return a[i + 1];
            return null;
        }

        static void Run()
        {
            string tag = Arg("-bwkTag") ?? "v1";
            bool saveTest = System.Environment.GetCommandLineArgs().Contains("-bwkSaveTest");
            Directory.CreateDirectory(OutDir);
            RemapV2Materials();
            EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            var cam = Camera.main;
            if (runner == null || rig == null || cam == null) throw new System.Exception("scene objects missing");
            var brain = cam.GetComponent<CinemachineBrain>();
            if (brain) brain.enabled = false;
            runner.track.Rebuild();

            // the level's rule-based S5 chambers / risers are replaced by the shot-matched dressing in this test
            int hidden = 0;
            foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
                if (t.name == "SideChambers" || t.name == "ChamberPipes") { t.gameObject.SetActive(false); hidden++; }
            Debug.Log($"[BWK] shot0825: level S5 chamber holders hidden: {hidden}");

            PoseRunner(runner, RunnerD);
            var root = new GameObject("Shot0825_Dressing");
            var c0 = SolveCamera(runner, RunnerD, false, out var mascotH, out var report);
            Dress(runner, c0, RunnerD, false, root.transform, 0);

            // (a) reference camera, 1280x720 + side-by-side with the reference
            var hiddenItems = HideItemsNear(runner, RunnerD, c0.pos);
            cam.transform.SetPositionAndRotation(c0.pos, c0.rot);
            cam.fieldOfView = VFov;
            string front = $"{OutDir}/unity_front_{tag}.png";
            CaptureTools.Render(cam, W, H, front);
            SideBySide(RefFrame, front, $"{OutDir}/front_vs_ref_{tag}.png");
            foreach (var r in hiddenItems) r.enabled = true;
            WriteCameraJson(c0, mascotH, report);

            // the S5 stretch: repeat the module (mirrored every other) so both view directions are dressed
            int k = 1;
            for (float d = RunnerD + ModulePeriod; d <= 246f; d += ModulePeriod, k++)
                Dress(runner, SolveCamera(runner, d, k % 2 == 1, out _, out _), d, k % 2 == 1, root.transform, k);
            for (float d = RunnerD - ModulePeriod; d >= 194f; d -= ModulePeriod)
                Dress(runner, SolveCamera(runner, d, true, out _, out _), d, true, root.transform, -1);

            // (b) frozen rear gameplay camera (SceneBuilder.HeroCam*), 720x1280, a few metres before the shot module
            float rearD = RunnerD - 13f;
            PoseRunner(runner, rearD);
            SceneBuilder.ApplyHeroCamera(rig);
            rig.aspectOverride = 720f / 1280f;
            rig.Snap();
            var lens = rig.vcam.Lens;
            cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
            cam.fieldOfView = lens.FieldOfView;
            CaptureTools.Render(cam, 720, 1280, $"{OutDir}/unity_rear_{tag}.png");
            rig.aspectOverride = 0f;
            Debug.Log($"[BWK] shot0825: rear gameplay still at {rearD} m (camera {SceneBuilder.HeroCamBack}/{SceneBuilder.HeroCamHeight}/{SceneBuilder.HeroCamPitch}/{SceneBuilder.HeroCamFov})");

            if (saveTest)
            {
                PoseRunner(runner, runner.startDistance);
                if (brain) brain.enabled = true;
                EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(), TestScenePath, true);
                Debug.Log("[BWK] shot0825: dressed copy saved -> " + TestScenePath + " (Level01 untouched)");
            }
            Debug.Log($"[BWK] shot0825 {tag}: front {front}");
        }

        static void RemapV2Materials()
        {
            foreach (var p in V2Models)
                if (AssetImporter.GetAtPath(p) is ModelImporter mi)
                {
                    mi.materialLocation = ModelImporterMaterialLocation.InPrefab;
                    mi.SearchAndRemapMaterials(ModelImporterMaterialName.BasedOnMaterialName, ModelImporterMaterialSearch.Everywhere);
                    mi.SaveAndReimport();
                }
                else Debug.LogWarning("[BWK] shot0825: missing model " + p);
        }

        static void PoseRunner(RunnerController runner, float d)
        {
            var animator = runner.GetComponentInChildren<Animator>();
            AnimationClip slide = null;
            if (animator != null && animator.runtimeAnimatorController != null)
                slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
            foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);
            runner.TeleportTo(d, 0f);
            if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
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

        static Bounds MascotBounds(RunnerController runner)
        {
            var from = runner.visual != null ? runner.visual : runner.transform;
            var rs = from.GetComponentsInChildren<SkinnedMeshRenderer>().Where(r => r.enabled).Cast<Renderer>().ToList();
            if (rs.Count == 0) rs = from.GetComponentsInChildren<MeshRenderer>().Where(r => r.enabled).Cast<Renderer>().ToList();
            var b = rs[0].bounds;
            foreach (var r in rs) b.Encapsulate(r.bounds);
            return b;
        }

        static Vector3 CamDir(Vector2 px, float fpx, bool mirror)
        {
            float x = mirror ? W - px.x : px.x;
            return new Vector3((x - W * 0.5f) / fpx, (H * 0.5f - px.y) / fpx, 1f).normalized;
        }

        /// <summary>Camera in front of the mascot looking back: distance from the mascot height in pixels, height from the
        /// angle between the mascot and the vanishing point, orientation from both rays (TRIAD).</summary>
        static Cam SolveCamera(RunnerController runner, float d, bool mirror, out float mascotH, out string report)
        {
            PoseRunner(runner, d);
            var mb = MascotBounds(runner);
            mascotH = mb.size.y;
            var f = runner.track.Evaluate(d);
            float fpx = H * 0.5f / Mathf.Tan(VFov * 0.5f * Mathf.Deg2Rad);
            Vector3 s1 = CamDir(MascotPx, fpx, mirror), s2 = CamDir(VpPx, fpx, mirror);
            float target = Vector3.Angle(s1, s2);
            float z = fpx * mascotH / MascotHeightPx;
            Vector3 mc = mb.center;
            Vector3 vp = runner.track.Evaluate(d - VpBack).FlatPoint(0f, TunnelCenter);
            float lat = (mirror ? -1f : 1f) * CamLateral;
            float lo = -10f, hi = 70f, e = 20f;
            Vector3 pos = mc;
            for (int it = 0; it < 40; it++)
            {
                e = 0.5f * (lo + hi);
                pos = CamPos(f, mc, z, e, lat);
                float ang = Vector3.Angle(mc - pos, vp - pos);
                if (ang < target) lo = e; else hi = e;
            }
            Vector3 d1 = (mc - pos).normalized, d2 = (vp - pos).normalized;
            var q1 = Quaternion.FromToRotation(s1, d1);
            Vector3 s2r = q1 * s2;
            Vector3 a = Vector3.ProjectOnPlane(s2r, d1), b = Vector3.ProjectOnPlane(d2, d1);
            var rot = Quaternion.AngleAxis(Vector3.SignedAngle(a, b, d1), d1) * q1;
            var c = new Cam { pos = pos, rot = rot, fpx = fpx };
            Vector3 camUp = rot * Vector3.up, camFwd = rot * Vector3.forward;
            float roll = Vector3.SignedAngle(Vector3.ProjectOnPlane(Vector3.up, camFwd), camUp, camFwd);
            float pitch = Mathf.Asin(Mathf.Clamp(camFwd.y, -1f, 1f)) * Mathf.Rad2Deg;
            float ahead = Vector3.Dot(pos - f.position, f.forward), up = Vector3.Dot(pos - f.position, f.flatUp);
            float side = Vector3.Dot(pos - f.position, f.flatRight);
            report = string.Format(CultureInfo.InvariantCulture,
                "\"runner_d\": {0:F2}, \"vfov_deg\": {1:F1}, \"hfov_deg\": {2:F1}, \"cam_ahead_of_mascot_m\": {3:F2}, \"cam_height_above_slide_m\": {4:F2}, " +
                "\"cam_lateral_m\": {5:F2}, \"cam_to_mascot_centre_m\": {6:F2}, \"elevation_deg\": {7:F1}, \"pitch_world_deg\": {8:F1}, \"roll_deg\": {9:F1}, " +
                "\"track_slope_deg\": {10:F1}, \"mascot_height_m\": {11:F2}",
                d, VFov, 2f * Mathf.Atan(Mathf.Tan(VFov * 0.5f * Mathf.Deg2Rad) * W / H) * Mathf.Rad2Deg, ahead, up, side, z, e, pitch, roll,
                f.slope, mascotH);
            if (!mirror) Debug.Log("[BWK] shot0825 camera: " + report);
            return c;
        }

        static Vector3 CamPos(TrackFrame f, Vector3 mc, float z, float elevDeg, float lat)
        {
            float e = elevDeg * Mathf.Deg2Rad;
            Vector3 dir = (f.forward * Mathf.Cos(e) + f.flatUp * Mathf.Sin(e)).normalized;
            float l = Mathf.Clamp(lat / z, -0.9f, 0.9f);
            dir = (dir * Mathf.Sqrt(1f - l * l) + f.flatRight * l).normalized;
            return mc + dir * z;
        }

        /// <summary>Offset of X from the local tunnel axis (perpendicular to the track) and the track distance at X.</summary>
        static Vector3 AxisOffset(TrackPath track, Vector3 X, ref float d, out TrackFrame f)
        {
            f = track.Evaluate(d);
            for (int i = 0; i < 4; i++) { d += Vector3.Dot(X - f.position, f.forward); f = track.Evaluate(d); }
            Vector3 v = X - f.FlatPoint(0f, TunnelCenter);
            return v - f.forward * Vector3.Dot(v, f.forward);
        }

        static void Dress(RunnerController runner, Cam c, float d, bool mirror, Transform root, int module)
        {
            var holder = new GameObject($"Module_{module}_{d:000.0}{(mirror ? "_M" : "")}").transform;
            holder.SetParent(root, false);
            var sb = new StringBuilder();
            foreach (var it in ShotItems())
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(it.model);
                if (prefab == null) { Debug.LogWarning("[BWK] shot0825: missing " + it.model); continue; }
                Vector3 dirC = CamDir(it.px, c.fpx, mirror);
                Vector3 dirW = c.rot * dirC;
                Vector3 X; Vector3 radial = Vector3.zero; float depth; float dd = d;
                if (it.mode == Mode.Wall)
                {
                    float t = 0.5f; Vector3 rv = Vector3.zero;
                    X = c.pos;
                    for (; t < 90f; t += 0.05f)
                    {
                        X = c.pos + dirW * t;
                        rv = AxisOffset(runner.track, X, ref dd, out _);
                        if (rv.magnitude >= it.radius) break;
                    }
                    radial = rv.normalized;
                    depth = Vector3.Dot(X - c.pos, c.rot * Vector3.forward);
                }
                else
                {
                    depth = it.depth;
                    X = c.pos + dirW * (depth / dirC.z);
                    AxisOffset(runner.track, X, ref dd, out _);
                }
                var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, holder);
                go.name = it.name;
                Vector3 camUp = c.rot * Vector3.up;
                Quaternion rot;
                if (it.mode == Mode.Wall && !it.worldUp)
                {
                    Vector3 fwd = -radial;
                    rot = Quaternion.LookRotation(fwd, Vector3.ProjectOnPlane(camUp, fwd)) * Quaternion.Euler(0f, 0f, mirror ? -it.spin : it.spin);
                }
                else if (it.mode == Mode.Wall)
                {
                    Vector3 fwd = Vector3.ProjectOnPlane(-radial, Vector3.up);
                    if (it.name.StartsWith("Coin") || it.name == "Gem") fwd = Vector3.ProjectOnPlane(c.pos - X, Vector3.up);
                    rot = Quaternion.LookRotation(fwd.normalized, Vector3.up) * Quaternion.Euler(0f, mirror ? -it.spin : it.spin, 0f);
                }
                else rot = Quaternion.LookRotation(c.pos - X, camUp);
                go.transform.rotation = rot;
                go.transform.localScale = Vector3.one;
                float sizeM = it.sizeM;
                if (sizeM <= 0f)
                {
                    go.transform.position = Vector3.zero;
                    var rs = go.GetComponentsInChildren<Renderer>();
                    if (rs.Length > 0) { var bb = rs[0].bounds; foreach (var r in rs) bb.Encapsulate(r.bounds); sizeM = Mathf.Max(bb.size.y, 0.05f); }
                    else sizeM = 1f;
                }
                float s = it.sizePx * depth / (c.fpx * sizeM);
                go.transform.localScale = new Vector3(mirror ? -s : s, s, s);
                go.transform.position = X - (it.worldUp ? Vector3.up : rot * Vector3.up) * it.originUp * s;
                if (it.name == "CurvyPipe")
                {
                    // SM_ChamberPipe is authored around the tunnel axis (riser at lateral 3.34 m, left wall); the camera-left
                    // wall is the travel-right wall -> turned 180 deg about up (SceneBuilder.BuildPipes convention)
                    var fp = runner.track.Evaluate(dd);
                    go.transform.SetPositionAndRotation(fp.FlatPoint(0f, TunnelCenter), fp.FlatRotation * (mirror ? Quaternion.identity : Quaternion.Euler(0f, 180f, 0f)));
                    go.transform.localScale = Vector3.one;
                    s = 1f;
                }
                if (!string.IsNullOrEmpty(it.mat))
                {
                    var m = AssetDatabase.LoadAssetAtPath<Material>(it.mat);
                    if (m != null) foreach (var r in go.GetComponentsInChildren<Renderer>()) r.sharedMaterials = Enumerable.Repeat(m, r.sharedMaterials.Length).ToArray();
                }
                foreach (var r in go.GetComponentsInChildren<Renderer>()) if (!it.name.StartsWith("Star")) r.shadowCastingMode = ShadowCastingMode.Off;
                if (it.name == "ChamberWindow") AddSocks(go.transform);
                if (it.name.StartsWith("Bubble")) { var bob = go.AddComponent<FloatBob>(); bob.amplitude = 0.15f; }
                sb.AppendFormat(CultureInfo.InvariantCulture, " {0}@{1:F1}m r{2:F2} z{3:F1} s{4:F2};", it.name, dd, (X - runner.track.Evaluate(dd).FlatPoint(0f, TunnelCenter)).magnitude, depth, s);
            }
            if (module == 0) Debug.Log("[BWK] shot0825 placed:" + sb);
        }

        /// <summary>Striped socks floating in front of the swirl disc (as the Blender preview: ~1 m long, 3 of them).</summary>
        static void AddSocks(Transform window)
        {
            var socks = new (string m, Vector3 p, Vector3 e)[]
            {
                ("SM_Sock_A", new Vector3(-0.25f, 0.70f, -0.10f), new Vector3(20f, 70f, -25f)),
                ("SM_Sock_B", new Vector3(-0.75f, -0.25f, -0.10f), new Vector3(-10f, 80f, 35f)),
                ("SM_Sock_C", new Vector3(0.35f, -0.55f, -0.10f), new Vector3(15f, 95f, 120f)),
            };
            int i = 0;
            foreach (var s in socks)
            {
                var pf = AssetDatabase.LoadAssetAtPath<GameObject>(Props + s.m + ".fbx");
                if (pf == null) continue;
                var go = (GameObject)PrefabUtility.InstantiatePrefab(pf, window);
                go.transform.localPosition = s.p;
                go.transform.localRotation = Quaternion.Euler(s.e);
                go.transform.localScale = Vector3.one * 2.6f;
                var bob = go.AddComponent<FloatBob>();
                bob.orbitAxis = Vector3.forward;
                bob.orbitRadius = 0.25f;
                bob.orbitSpeed = 45f + 10f * i++;
                bob.amplitude = 0.05f;
                foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
            }
        }

        static List<Renderer> HideItemsNear(RunnerController runner, float d, Vector3 camPos)
        {
            var hidden = new List<Renderer>();
            foreach (var it in Object.FindObjectsByType<TrackItem>(FindObjectsSortMode.None))
                if ((it.distance > d - 0.6f && it.distance < d + 8f) || (it.transform.position - camPos).sqrMagnitude < 16f)
                    foreach (var r in it.GetComponentsInChildren<Renderer>())
                        if (r.enabled) { r.enabled = false; hidden.Add(r); }
            return hidden;
        }

        static void SideBySide(string refPath, string oursPath, string outPath)
        {
            if (!File.Exists(refPath)) { Debug.LogWarning("[BWK] shot0825: reference missing " + refPath); return; }
            var a = new Texture2D(2, 2); a.LoadImage(File.ReadAllBytes(refPath));
            var b = new Texture2D(2, 2); b.LoadImage(File.ReadAllBytes(oursPath));
            const int gap = 12;
            var o = new Texture2D(W * 2 + gap, H, TextureFormat.RGB24, false);
            var fill = Enumerable.Repeat(new Color32(20, 16, 30, 255), o.width * o.height).ToArray();
            o.SetPixels32(fill);
            if (a.width == W && a.height == H) o.SetPixels(0, 0, W, H, a.GetPixels());
            if (b.width == W && b.height == H) o.SetPixels(W + gap, 0, W, H, b.GetPixels());
            o.Apply();
            File.WriteAllBytes(outPath, o.EncodeToPNG());
            Object.DestroyImmediate(a); Object.DestroyImmediate(b); Object.DestroyImmediate(o);
        }

        static void WriteCameraJson(Cam c, float mascotH, string report)
        {
            var e = c.rot.eulerAngles;
            string json = "{\n  \"frame\": \"" + RefFrame + "\",\n  \"method\": \"landmarks: mascot centre (522,397) + height 385 px, tunnel vanishing point (545,215) = axis 22 m behind the mascot, " +
                          "lens from the chamber window ellipse (215 x 365 px, circle flush on an r 3.4 wall -> vFOV 50-55 deg; 52 used), lateral from the rail slopes (left 0.47 / right 0.32)\",\n  " +
                          report + ",\n" + string.Format(CultureInfo.InvariantCulture,
                          "  \"world_position\": [{0:F3}, {1:F3}, {2:F3}],\n  \"world_euler\": [{3:F2}, {4:F2}, {5:F2}],\n  \"focal_px_720\": {6:F1}\n}}\n",
                          c.pos.x, c.pos.y, c.pos.z, e.x, e.y, e.z, c.fpx);
            File.WriteAllText($"{OutDir}/camera.json", json);
        }
    }
}
