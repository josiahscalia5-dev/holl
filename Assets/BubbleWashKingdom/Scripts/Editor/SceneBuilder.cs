using System.Collections.Generic;
using System.IO;
using System.Linq;
using Unity.Cinemachine;
using Unity.Mathematics;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Splines;

namespace BubbleWash.EditorTools
{
    // OWNER: lead developer (scene assembly, track, gameplay items, runner/mascot, cameras, HUD). Domain code lives in
    // SceneBuilder.Environment.cs (Agent 3), SceneBuilder.WaterFX.cs (Agent 2) and SceneBuilder.Lighting.cs (Agent 4).
    /// <summary>
    /// Builds the first playable section (Screens 04-06: Rainbow Rush -> Rainbow Water Slide -> Twisty Tunnel) from
    /// code: spline track, bent Blender modules, machinery, collectibles, lighting, post FX, cameras, mascot, UI.
    /// Missing Blender assets fall back to procedural meshes so the pipeline always runs.
    /// Batch entry: BubbleWash.EditorTools.SceneBuilder.BuildAllBatch
    /// </summary>
    public static partial class SceneBuilder
    {
        public const string ScenePath = "Assets/BubbleWashKingdom/Scenes/Level01_RainbowRush.unity";
        const string GenDir = "Assets/BubbleWashKingdom/Generated/Level01";
        const string ModelsDir = "Assets/BubbleWashKingdom/Art/Models";

        // World layout (meters)
        const float TunnelRadius = 4.2f, TunnelCenter = 2.3f;
        const float HallScale = 3.2f;
        const float RingSpacing = 8.5f;   // reference: a few thick rings receding, drum wall between them
        const int BulbsPerRing = 28;
        const float BulbRadius = 3.70f;
        const float ChunkLength = 30f;

        static readonly Vector3[] Knots =
        {
            new Vector3(0, 0, 0), new Vector3(0, -0.6f, 12), new Vector3(0.6f, -1.6f, 24), new Vector3(2.4f, -2.9f, 36),
            new Vector3(5.6f, -4.3f, 48), new Vector3(10.4f, -5.6f, 59), new Vector3(15.6f, -6.6f, 70), new Vector3(20f, -7.8f, 82),
            new Vector3(22f, -10.5f, 96), new Vector3(21f, -13.6f, 110), new Vector3(17f, -15.4f, 124), new Vector3(11f, -17f, 138),
            new Vector3(7.5f, -18.8f, 153), new Vector3(8f, -20.8f, 168), new Vector3(12f, -22.8f, 182), new Vector3(19f, -24.6f, 194),
            new Vector3(28f, -26.2f, 203), new Vector3(39f, -27.6f, 208), new Vector3(50f, -29f, 207), new Vector3(60f, -30.4f, 201),
            new Vector3(67f, -31.8f, 191), new Vector3(70f, -33.2f, 178), new Vector3(70f, -35f, 163), new Vector3(68f, -36.6f, 148),
            new Vector3(68f, -38f, 133), new Vector3(69f, -39f, 118), new Vector3(69f, -39.6f, 104),
        };

        static System.Random rng;
        static TrackPath track;
        static float tunnelStart, portalD;

        public static void BuildAllBatch()
        {
            try
            {
                ProjectSetup.Run();
                TextureGenerator.Run();
                MaterialLibrary.Run();
                ModelImportRules.RemapAllMaterials();
                if (File.Exists(AnimatorBuilder.FbxPath)) AnimatorBuilder.Run();
                Build();
                SceneStats.Log();
                CaptureTools.CaptureStills();
                CaptureTools.CaptureHero();
                EditorApplication.Exit(0);
            }
            catch (System.Exception e)
            {
                Debug.LogError("[BWK] BuildAllBatch failed: " + e);
                EditorApplication.Exit(1);
            }
        }

        [MenuItem("Bubble Wash/Build Level 01 Section")]
        public static void Build()
        {
            rng = new System.Random(20261125);
            if (AssetDatabase.IsValidFolder(GenDir)) AssetDatabase.DeleteAsset(GenDir);
            Directory.CreateDirectory(GenDir);
            AssetDatabase.Refresh();
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject("Level01_RainbowRush");
            var env = Child(root, "Environment");

            // ---------------------------------------------------------------- track spline
            var trackGo = Child(root, "Track");
            var container = trackGo.AddComponent<SplineContainer>();
            var spline = container.Spline;
            spline.Clear();
            foreach (var k in Knots) spline.Add(new BezierKnot(new float3(k.x, k.y, k.z)), TangentMode.AutoSmooth);
            track = trackGo.AddComponent<TrackPath>();
            track.Rebuild();
            float L = track.Length;
            tunnelStart = 62f;
            portalD = L - 12f;
            Debug.Log($"[BWK] Track length {L:F1} m, tunnel from {tunnelStart} m, portal at {portalD:F1} m");

            // ---------------------------------------------------------------- slide, tunnel, hall shells
            var slide = ModelParts("Track", "SM_Slide_Module");
            if (slide.Count == 0) slide.Add(new Part(ProceduralModules.SlideModule(), new[] { Mat("M_Water"), Mat("M_RailPink"), Mat("M_SlideShell") }, Matrix4x4.identity));
            BendChunks(env, "Slide", slide[0], 0f, L, true, Vector3.one, 0f, 0f, 4f, castShadows: true);

            var tunnel = ModelParts("Track", "SM_Tunnel_Module");
            if (tunnel.Count == 0) tunnel.Add(new Part(ProceduralModules.TunnelModule(TunnelRadius, TunnelCenter), new[] { Mat("M_DrumWall") }, Matrix4x4.identity));
            BendChunks(env, "Tunnel", tunnel[0], tunnelStart, L, false, Vector3.one, 0f, 0f, 4f, castShadows: false);
            var hallPart = new Part(tunnel[0].mesh, new[] { Mat("M_DrumWallHall") }, Matrix4x4.identity);
            BendChunks(env, "Hall", hallPart, 0f, tunnelStart + 1f, false, new Vector3(HallScale, HallScale, 1f), 0f, 0f, 4f, castShadows: false);
            BuildBulkheads(env);

            // ---------------------------------------------------------------- rings, stars, portholes, pipes, foam
            BuildRings(env, L);
            BuildNeonStars(env);
            BuildPortholes(env);
            BuildPipes(env, L);
            BuildFoam(env, L);
            BuildHallMachinery(env);
            BuildFloatingBubbles(env, L);

            // ---------------------------------------------------------------- gameplay items
            var itemsGo = Child(root, "TrackItems");
            var registry = itemsGo.AddComponent<TrackItemRegistry>();
            BuildItems(itemsGo, registry, L);
            BuildDecorChevrons(env, L);

            // ---------------------------------------------------------------- portal
            var runnerGo = new GameObject("Runner");
            var runner = runnerGo.AddComponent<RunnerController>();
            BuildPortal(env, runner);

            // ---------------------------------------------------------------- lighting and post
            BuildLighting(root, L);

            // ---------------------------------------------------------------- runner + mascot
            runnerGo.transform.SetParent(root.transform, false);
            var input = runnerGo.AddComponent<SwipeInput>();
            runner.track = track;
            runner.input = input;
            runner.items = registry;
            runner.startDistance = 14f;
            var visual = Child(runnerGo, "Visual");
            runner.visual = visual.transform;
            Animator animator = null;
            Transform mascotHolder = null;
            var mascotPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(AnimatorBuilder.FbxPath);
            if (mascotPrefab != null)
            {
                var m = Spawn(mascotPrefab);
                m.name = "SK_Mascot";
                m.transform.SetParent(visual.transform, false);
                animator = m.GetComponentInChildren<Animator>();
                if (animator == null) animator = m.transform.GetChild(0).gameObject.AddComponent<Animator>();
                mascotHolder = m.transform;
                animator.runtimeAnimatorController = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(AnimatorBuilder.ControllerPath);
                animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                foreach (var r in m.GetComponentsInChildren<Renderer>()) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }
            }
            else if (AssetDatabase.LoadAssetAtPath<GameObject>(StaticMascotPath) is GameObject staticModel)
            {
                // Until the rigged SK_Mascot.fbx exists: the finished static Blender model, posed seated and feet-first.
                var m = Spawn(staticModel);
                m.name = "SK_Mascot_SeatedPreview";
                m.transform.SetParent(visual.transform, false);
                PoseSeated(m.transform);
                foreach (var r in m.GetComponentsInChildren<Renderer>())
                    r.sharedMaterials = r.sharedMaterials.Select(mat => mat != null && (mat.name == "M_Fur" || mat.name == "M_PomPom") ? (Mat(mat.name + "_Static") ?? mat) : mat).ToArray();
                foreach (var r in m.GetComponentsInChildren<Renderer>()) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }
                mascotHolder = m.transform;
                Debug.Log("[BWK] Using static seated mascot preview (rig pending).");
            }
            else
            {
                Debug.LogWarning("[BWK] SK_Mascot.fbx not found yet - using a temporary placeholder (pipeline test only).");
                var body = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                Object.DestroyImmediate(body.GetComponent<Collider>());
                body.name = "PLACEHOLDER_Mascot";
                body.transform.SetParent(visual.transform, false);
                body.transform.localPosition = new Vector3(0, 0.47f, 0);
                body.transform.localScale = new Vector3(0.85f, 0.8f, 0.78f);
                body.GetComponent<Renderer>().sharedMaterial = Mat("M_MachinePink");
            }
            var driver = runnerGo.AddComponent<MascotAnimatorDriver>();
            if (mascotHolder != null) driver.squashRoot = mascotHolder;
            driver.runner = runner;
            driver.animator = animator;
            var autopilot = runnerGo.AddComponent<AutopilotBrain>();
            autopilot.runner = runner;
            autopilot.items = registry;
            autopilot.enabled = false;
            var fx = BuildRunnerFX(runnerGo, runner, registry);
            BuildCharacterLights(runnerGo);

            // ---------------------------------------------------------------- cameras
            var director = BuildCameras(root, runner);

            // ---------------------------------------------------------------- game flow, HUD, perf
            var hudGo = Child(root, "HUD");
            var hud = hudGo.AddComponent<HUDController>();
            hud.items = registry;
            hud.runner = runner;
            var gmGo = Child(root, "GameManager");
            var gm = gmGo.AddComponent<GameManager>();
            gm.runner = runner;
            gm.director = director;
            gm.hud = hud;
            gm.items = registry;
            gm.autopilot = autopilot;
            gmGo.AddComponent<PerfStats>();

            runner.ResetRun();
            EditorSceneManager.SaveScene(scene, ScenePath);
            var scenes = EditorBuildSettings.scenes.Where(s => s.path != ScenePath).ToList();
            scenes.Insert(0, new EditorBuildSettingsScene(ScenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();
            BakeProbes();
            EditorSceneManager.SaveScene(SceneManagerActive(), ScenePath);
            AssetDatabase.SaveAssets();
            Debug.Log("[BWK] Scene built: " + ScenePath);
        }

        static UnityEngine.SceneManagement.Scene SceneManagerActive() => UnityEngine.SceneManagement.SceneManager.GetActiveScene();

        /// <summary>
        /// Agent previews (CaptureTools.AgentPreviewBatch): rebuilds the lighting / post-processing (Agent 4) and the runner
        /// splash FX + character lights (Agents 2 and 4) inside the OPEN scene, in memory only. The scene is never saved
        /// here; the post profile goes to a separate preview asset so the saved main scene keeps its own.
        /// Geometry / placement changes (environment, foam, stars) appear only after the lead's full scene build.
        /// </summary>
        public static void PreviewRefreshDomains()
        {
            var root = GameObject.Find("Level01_RainbowRush");
            track = Object.FindFirstObjectByType<TrackPath>();
            if (root == null || track == null) { Debug.LogError("[BWK] preview: scene root/track missing"); return; }
            track.Rebuild();
            rng = new System.Random(20261125);
            tunnelStart = 62f;
            portalD = track.Length - 12f;
            foreach (var n in new[] { "Lighting", "PostFX Volume" })
            {
                var t = root.transform.Find(n);
                if (t != null) Object.DestroyImmediate(t.gameObject);
            }
            string previewProfile = $"{GenDir}/PostFX_Preview.asset";
            AssetDatabase.DeleteAsset(previewProfile);
            BuildLighting(root, track.Length, previewProfile);
            BakeProbes();
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var registry = Object.FindFirstObjectByType<TrackItemRegistry>();
            foreach (var n in new[] { "FX", "CharacterLights", "CharLight_WarmTop", "CharLight_PinkBack" })
            {
                var t = runner.transform.Find(n);
                if (t != null) Object.DestroyImmediate(t.gameObject);
            }
            BuildRunnerFX(runner.gameObject, runner, registry);
            BuildCharacterLights(runner.gameObject);
            Debug.Log("[BWK] preview: lighting/post + runner FX rebuilt in memory (scene not saved)");
        }

        // ==================================================================== parts and combining
        public struct Part
        {
            public Mesh mesh; public Material[] mats; public Matrix4x4 local;
            public Part(Mesh mesh, Material[] mats, Matrix4x4 local) { this.mesh = mesh; this.mats = mats; this.local = local; }
        }

        static readonly Dictionary<string, List<Part>> partCache = new Dictionary<string, List<Part>>();

        static List<Part> ModelParts(string group, string name)
        {
            string key = group + "/" + name;
            if (partCache.TryGetValue(key, out var cached)) return cached;
            var list = new List<Part>();
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"{ModelsDir}/{group}/{name}.fbx");
            if (prefab != null)
            {
                foreach (var mf in prefab.GetComponentsInChildren<MeshFilter>(true))
                {
                    var mr = mf.GetComponent<MeshRenderer>();
                    if (mf.sharedMesh == null || mr == null) continue;
                    var toAsset = Matrix4x4.Rotate(Fix) * mf.transform.localToWorldMatrix;
                    list.Add(new Part(BakeTransform(mf.sharedMesh, toAsset), mr.sharedMaterials, Matrix4x4.identity));
                }
            }
            partCache[key] = list;
            return list;
        }

        // Blender FBX arrive with a +90 deg X node rotation and Blender-space vertices; Fix * node maps them to
        // asset space (front +Z, up +Y, right +X) as defined in Docs/AssetSpec.md.
        static readonly Quaternion Fix = Quaternion.Euler(0f, 180f, 0f);

        static Mesh BakeTransform(Mesh src, Matrix4x4 m)
        {
            var mesh = Object.Instantiate(src);
            mesh.name = src.name;
            var v = mesh.vertices; var n = mesh.normals; var t = mesh.tangents;
            for (int i = 0; i < v.Length; i++) v[i] = m.MultiplyPoint3x4(v[i]);
            for (int i = 0; i < n.Length; i++) n[i] = m.MultiplyVector(n[i]).normalized;
            for (int i = 0; i < t.Length; i++) { var d = m.MultiplyVector(new Vector3(t[i].x, t[i].y, t[i].z)).normalized; t[i] = new Vector4(d.x, d.y, d.z, t[i].w); }
            mesh.vertices = v; if (n.Length > 0) mesh.normals = n; if (t.Length > 0) mesh.tangents = t;
            mesh.RecalculateBounds();
            return mesh;
        }

        /// <summary>Instantiates an FBX prefab under a holder whose axes are asset space; returns the holder.</summary>
        static GameObject Spawn(GameObject prefab)
        {
            var holder = new GameObject(prefab.name);
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            inst.transform.SetParent(holder.transform, false);
            inst.transform.localPosition = Fix * inst.transform.localPosition;
            inst.transform.localRotation = Fix * inst.transform.localRotation;
            return holder;
        }

        const string StaticMascotPath = "Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_model.fbx";

        /// <summary>Seated, feet-first riding pose for the static model: body on its bottom, feet forward with toes up, slight lean back.</summary>
        static void PoseSeated(Transform holder)
        {
            var inst = holder.GetChild(0);
            inst.localPosition += new Vector3(0f, -0.05f, 0f);
            foreach (var t in holder.GetComponentsInChildren<Transform>(true))
            {
                if (!t.name.ToLowerInvariant().StartsWith("foot")) continue;
                var r = t.GetComponent<Renderer>();
                Vector3 offset = holder.forward * 0.3f + holder.up * 0.05f;
                Vector3 pivot = (r != null ? r.bounds.center : t.position) + offset;
                t.position += offset;
                t.RotateAround(pivot, holder.right, -55f);
            }
            inst.RotateAround(holder.position, holder.right, -8f);
        }

        static GameObject ModelPrefab(string group, string name) => AssetDatabase.LoadAssetAtPath<GameObject>($"{ModelsDir}/{group}/{name}.fbx");

        class Combiner
        {
            readonly Dictionary<Material, List<CombineInstance>> groups = new Dictionary<Material, List<CombineInstance>>();
            readonly Dictionary<Material, int> vertexCounts = new Dictionary<Material, int>();

            public void Add(List<Part> parts, Matrix4x4 world)
            {
                foreach (var p in parts)
                {
                    for (int s = 0; s < p.mesh.subMeshCount; s++)
                    {
                        var mat = p.mats != null && p.mats.Length > 0 ? p.mats[Mathf.Min(s, p.mats.Length - 1)] : Mat("M_Gold");
                        if (mat == null) continue;
                        if (!groups.TryGetValue(mat, out var l)) { l = new List<CombineInstance>(); groups[mat] = l; vertexCounts[mat] = 0; }
                        l.Add(new CombineInstance { mesh = p.mesh, subMeshIndex = s, transform = world * p.local });
                        vertexCounts[mat] += p.mesh.vertexCount;
                    }
                }
            }

            public int Count => groups.Count;

            public List<Renderer> Flush(GameObject parent, string name, bool castShadows)
            {
                var made = new List<Renderer>();
                foreach (var kv in groups)
                {
                    var mesh = new Mesh { name = $"{name}_{kv.Key.name}" };
                    mesh.indexFormat = vertexCounts[kv.Key] > 60000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
                    mesh.CombineMeshes(kv.Value.ToArray(), true, true);
                    mesh.RecalculateBounds();
                    SaveMesh(mesh);
                    var go = Child(parent, mesh.name);
                    go.AddComponent<MeshFilter>().sharedMesh = mesh;
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterial = kv.Key;
                    mr.shadowCastingMode = castShadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
                    GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic | StaticEditorFlags.ReflectionProbeStatic);
                    made.Add(mr);
                }
                groups.Clear();
                vertexCounts.Clear();
                return made;
            }
        }

        static void SaveMesh(Mesh mesh)
        {
            string path = $"{GenDir}/{Sanitize(mesh.name)}.asset";
            path = AssetDatabase.GenerateUniqueAssetPath(path);
            AssetDatabase.CreateAsset(mesh, path);
        }

        static string Sanitize(string s) => string.Concat(s.Select(c => char.IsLetterOrDigit(c) || c == '_' || c == '-' ? c : '_'));

        static void BendChunks(GameObject parent, string name, Part part, float start, float end, bool bank, Vector3 scale,
                               float lateral, float vertical, float uvTile, bool castShadows)
        {
            var holder = Child(parent, name);
            int idx = 0;
            for (float d = start; d < end - 0.5f; d += ChunkLength, idx++)
            {
                float e = Mathf.Min(end, d + ChunkLength);
                if (end - e < 6f) e = end; // avoid a tiny last chunk
                var opt = SplineMeshDeformer.DefaultOptions(d, e);
                opt.useBank = bank;
                opt.scale = scale;
                opt.lateralOffset = lateral;
                opt.verticalOffset = vertical;
                opt.distanceUVTile = uvTile;
                opt.preferredModuleLength = 4f * Mathf.Max(1f, scale.x * 0.5f);
                var mesh = SplineMeshDeformer.Bend(part.mesh, track, null, opt, $"{name}_{idx:00}");
                SaveMesh(mesh);
                var go = Child(holder, mesh.name);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterials = Enumerable.Range(0, mesh.subMeshCount).Select(s => part.mats[Mathf.Min(s, part.mats.Length - 1)]).ToArray();
                mr.shadowCastingMode = castShadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
                GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.ReflectionProbeStatic);
                if (e >= end) break;
            }
        }

        // ==================================================================== environment pieces








        // ==================================================================== gameplay items
        static void BuildItems(GameObject parent, TrackItemRegistry registry, float L)
        {
            var coin = ModelPrefab("Props", "SM_Coin");
            var gem = ModelPrefab("Props", "SM_Gem");
            var chevron = ModelPrefab("Props", "SM_Chevron");
            var roller = ModelPrefab("Machinery", "SM_BrushRoller");
            float lane = 1.15f;

            TrackItem Make(GameObject prefab, PrimitiveType fallback, string fallbackMat, TrackItemKind kind, float d, float lat, float h, float scale)
            {
                GameObject go;
                if (prefab != null) go = Spawn(prefab);
                else
                {
                    go = GameObject.CreatePrimitive(fallback);
                    Object.DestroyImmediate(go.GetComponent<Collider>());
                    go.GetComponent<Renderer>().sharedMaterial = Mat(fallbackMat);
                }
                go.transform.SetParent(parent.transform, false);
                var f = track.Evaluate(d);
                float surf = Mathf.Abs(lat) > 1.25f ? 0.9f * (Mathf.Abs(lat) - 1.25f) * (Mathf.Abs(lat) - 1.25f) : 0f;
                go.transform.SetPositionAndRotation(f.Point(lat, surf + h), f.Rotation);
                go.transform.localScale = Vector3.one * scale;
                var it = go.AddComponent<TrackItem>();
                it.kind = kind; it.distance = d; it.lateral = lat; it.height = h;
                registry.items.Add(it);
                foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = kind == TrackItemKind.Boost ? ShadowCastingMode.Off : ShadowCastingMode.On;
                return it;
            }

            float dd = 20f;
            int laneIdx = 0;
            int pattern = 0;
            while (dd < portalD - 12f)
            {
                switch (pattern % 6)
                {
                    case 0: case 3: // straight coin line
                        for (int i = 0; i < 7; i++) Make(coin, PrimitiveType.Cylinder, "M_Coin", TrackItemKind.Coin, dd + i * 1.7f, laneIdx * lane, 0.55f, 1f);
                        dd += 7 * 1.7f;
                        break;
                    case 1: // lane-switch arc
                        int next = Mathf.Clamp(laneIdx + (rng.NextDouble() < 0.5 ? -1 : 1), -1, 1);
                        if (next == laneIdx) next = -laneIdx;
                        for (int i = 0; i < 8; i++)
                        {
                            float t = i / 7f;
                            Make(coin, PrimitiveType.Cylinder, "M_Coin", TrackItemKind.Coin, dd + i * 1.6f, Mathf.Lerp(laneIdx, next, Mathf.SmoothStep(0, 1, t)) * lane, 0.55f, 1f);
                        }
                        laneIdx = next;
                        dd += 8 * 1.6f;
                        break;
                    case 2: // gem, sometimes raised (jump)
                        bool raised = rng.NextDouble() < 0.5;
                        Make(gem, PrimitiveType.Cube, "M_Gem", TrackItemKind.Gem, dd + 2f, laneIdx * lane, raised ? 1.55f : 0.6f, 1f).value = 1;
                        if (raised) for (int i = 0; i < 3; i++) Make(coin, PrimitiveType.Cylinder, "M_Coin", TrackItemKind.Coin, dd + 0.6f + i * 0.7f, laneIdx * lane, 0.9f + i * 0.25f, 1f);
                        dd += 6f;
                        break;
                    case 4: // boost pad: three bright chevrons
                        for (int i = 0; i < 3; i++)
                        {
                            var b = Make(chevron, PrimitiveType.Quad, "M_Arrow", TrackItemKind.Boost, dd + i * 1.1f, laneIdx * lane, 0.04f, 1.25f);
                            b.halfLength = 0.7f; b.halfWidth = 0.6f;
                        }
                        dd += 5f;
                        break;
                    case 5: // soft rotating roller obstacle (after the tunnel entrance), jumpable
                        if (dd > tunnelStart + 30f && roller != null)
                        {
                            int obstacleLane = rng.Next(-1, 2);
                            var o = Make(roller, PrimitiveType.Cylinder, "M_BrushPink", TrackItemKind.Obstacle, dd + 4f, obstacleLane * lane, 0.32f, 0.3f);
                            o.halfLength = 0.45f; o.halfWidth = 0.55f; o.jumpable = true; o.clearHeight = 0.5f;
                            o.transform.rotation = track.Evaluate(dd + 4f).Rotation;
                            var sp = o.gameObject.AddComponent<Spinner>(); sp.localAxis = Vector3.right; sp.degreesPerSecond = 160f;
                            o.spinSpeed = 0f; o.bobAmplitude = 0f;
                            // lead coins in another lane
                            int other = obstacleLane == laneIdx ? (laneIdx == 0 ? 1 : 0) : laneIdx;
                            for (int i = 0; i < 4; i++) Make(coin, PrimitiveType.Cylinder, "M_Coin", TrackItemKind.Coin, dd + 2f + i * 1.6f, other * lane, 0.55f, 1f);
                            laneIdx = other;
                        }
                        dd += 9f;
                        break;
                }
                dd += 4f + (float)rng.NextDouble() * 3f;
                pattern++;
            }
            foreach (var it in registry.items)
                if (it.kind == TrackItemKind.Boost || it.kind == TrackItemKind.Obstacle) { it.spinSpeed = 0f; it.bobAmplitude = 0f; }
            registry.Sort();
        }



        // ==================================================================== lighting



        // ==================================================================== runner FX


        // ==================================================================== cameras
        static CameraDirector BuildCameras(GameObject root, RunnerController runner)
        {
            var camGo = new GameObject("Main Camera");
            camGo.transform.SetParent(root.transform, false);
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.nearClipPlane = 0.12f;
            cam.farClipPlane = 120f;
            cam.fieldOfView = 52f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.32f, 0.2f, 0.55f);
            camGo.AddComponent<AudioListener>();
            var data = cam.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = true;
            data.antialiasing = AntialiasingMode.FastApproximateAntialiasing;
            data.renderShadows = true;
            var brain = camGo.AddComponent<CinemachineBrain>();
            brain.DefaultBlend = new CinemachineBlendDefinition(CinemachineBlendDefinition.Styles.EaseInOut, 1.3f);

            CinemachineCamera MakeVcam(string name, float fov)
            {
                var go = Child(root, name);
                var vc = go.AddComponent<CinemachineCamera>();
                var lens = LensSettings.Default;
                lens.FieldOfView = fov; lens.NearClipPlane = 0.12f; lens.FarClipPlane = 120f;
                vc.Lens = lens;
                return vc;
            }
            var intro = MakeVcam("CM Intro (front, stationary)", 40f);
            var gameplay = MakeVcam("CM Gameplay (rear)", 52f);
            var celebrate = MakeVcam("CM Celebrate (front)", 42f);
            var rig = gameplay.gameObject.AddComponent<RunnerCameraRig>();
            rig.runner = runner;
            rig.vcam = gameplay;
            var director = Child(root, "CameraDirector").AddComponent<CameraDirector>();
            director.runner = runner;
            director.introCam = intro;
            director.gameplayCam = gameplay;
            director.celebrateCam = celebrate;
            intro.gameObject.SetActive(true);
            gameplay.gameObject.SetActive(false);
            celebrate.gameObject.SetActive(false);
            return director;
        }

        // ==================================================================== utilities
        static GameObject Child(GameObject parent, string name)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent.transform, false);
            return go;
        }

        static Material Mat(string name)
        {
            var m = MaterialLibrary.Get(name);
            if (m == null) Debug.LogWarning("[BWK] material missing: " + name);
            return m;
        }
    }
}
