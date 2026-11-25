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
    /// <summary>
    /// Builds the first playable section (Screens 04-06: Rainbow Rush -> Rainbow Water Slide -> Twisty Tunnel) from
    /// code: spline track, bent Blender modules, machinery, collectibles, lighting, post FX, cameras, mascot, UI.
    /// Missing Blender assets fall back to procedural meshes so the pipeline always runs.
    /// Batch entry: BubbleWash.EditorTools.SceneBuilder.BuildAllBatch
    /// </summary>
    public static class SceneBuilder
    {
        public const string ScenePath = "Assets/BubbleWashKingdom/Scenes/Level01_RainbowRush.unity";
        const string GenDir = "Assets/BubbleWashKingdom/Generated/Level01";
        const string ModelsDir = "Assets/BubbleWashKingdom/Art/Models";

        // World layout (meters)
        const float TunnelRadius = 4.2f, TunnelCenter = 2.3f;
        const float HallScale = 3.2f;
        const float RingSpacing = 4.5f;
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
                CaptureTools.CaptureStills();
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

            public void Flush(GameObject parent, string name, bool castShadows)
            {
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
                }
                groups.Clear();
                vertexCounts.Clear();
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
        static void BuildBulkheads(GameObject env)
        {
            var mouth = track.Evaluate(tunnelStart);
            var wall = Child(env, "TunnelMouthWall");
            wall.transform.SetPositionAndRotation(mouth.FlatPoint(0, TunnelCenter), Quaternion.LookRotation(-mouth.forward, mouth.flatUp));
            var m = ProceduralModules.Annulus(TunnelRadius + 0.05f, 24f);
            SaveMesh(m);
            wall.AddComponent<MeshFilter>().sharedMesh = m;
            wall.AddComponent<MeshRenderer>().sharedMaterial = Mat("M_DrumWallFlat");
            wall.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;

            var back = track.Evaluate(0f);
            var bw = Child(env, "HallBackWall");
            bw.transform.SetPositionAndRotation(back.FlatPoint(0, TunnelCenter * HallScale) - back.forward * 0.5f, Quaternion.LookRotation(back.forward, back.flatUp));
            var m2 = ProceduralModules.Annulus(0.01f, TunnelRadius * HallScale + 1f);
            SaveMesh(m2);
            bw.AddComponent<MeshFilter>().sharedMesh = m2;
            bw.AddComponent<MeshRenderer>().sharedMaterial = Mat("M_DrumWallFlat");
            bw.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
        }

        static void BuildRings(GameObject env, float L)
        {
            var ring = ModelParts("Track", "SM_Ring");
            var bulb = ModelParts("Track", "SM_Bulb");
            if (ring.Count == 0) { Debug.LogWarning("[BWK] SM_Ring missing - rings skipped"); return; }
            if (bulb.Count == 0)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                var sm = s.GetComponent<MeshFilter>().sharedMesh;
                Object.DestroyImmediate(s);
                bulb.Add(new Part(sm, new[] { Mat("M_Bulb") }, Matrix4x4.TRS(new Vector3(0, 0.08f, 0), Quaternion.identity, Vector3.one * 0.17f)));
            }
            var holder = Child(env, "Rings");
            var comb = new Combiner();
            int chunk = 0;
            float chunkStart = tunnelStart;
            void PlaceRing(float d, float scale)
            {
                var f = track.Evaluate(d);
                var world = Matrix4x4.TRS(f.FlatPoint(0, TunnelCenter), f.FlatRotation, Vector3.one * scale);
                comb.Add(ring, world);
                for (int b = 0; b < BulbsPerRing; b++)
                {
                    float a = b / (float)BulbsPerRing * Mathf.PI * 2f;
                    var radial = new Vector3(Mathf.Sin(a), Mathf.Cos(a), 0f);
                    var local = Matrix4x4.TRS(radial * BulbRadius, Quaternion.FromToRotation(Vector3.up, -radial), Vector3.one * 1.5f);
                    comb.Add(bulb, world * local);
                }
            }
            PlaceRing(tunnelStart - 0.3f, 1.18f); // entrance gate
            for (float d = tunnelStart + 3f; d < portalD - 5f; d += RingSpacing)
            {
                PlaceRing(d, 1f);
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Rings_{chunk++:00}", true); chunkStart = d; }
            }
            comb.Flush(holder, $"Rings_{chunk:00}", true);
        }

        static void BuildNeonStars(GameObject env)
        {
            var outline = ModelParts("Props", "SM_NeonStar");
            var filled = ModelParts("Props", "SM_StarFilled");
            if (outline.Count == 0) { Debug.LogWarning("[BWK] SM_NeonStar missing - stars skipped"); return; }
            var mats = new[] { Mat("M_Neon_Cyan"), Mat("M_Neon_Pink"), Mat("M_Neon_Yellow") };
            var holder = Child(env, "NeonStars");
            var comb = new Combiner();
            int chunk = 0; float chunkStart = tunnelStart;
            int i = 0;
            for (float d = tunnelStart + 2f; d < portalD - 4f; d += 1.7f + (float)rng.NextDouble() * 1.6f, i++)
            {
                var f = track.Evaluate(d);
                float ang = Mathf.Lerp(-118f, 118f, (float)rng.NextDouble()) * Mathf.Deg2Rad; // 0 = ceiling
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                var center = f.FlatPoint(0, TunnelCenter);
                var pos = center + radial * (TunnelRadius - 0.25f);
                var rot = Quaternion.LookRotation(radial, f.forward) * Quaternion.Euler(0, 0, (float)rng.NextDouble() * 40f - 20f);
                // star mesh faces +Z after import; LookRotation(radial) makes it face outward -> flip to face the centre
                rot = Quaternion.LookRotation(-radial, f.forward);
                float scale = Mathf.Lerp(0.6f, 1.3f, (float)rng.NextDouble());
                var src = (filled.Count > 0 && i % 7 == 3) ? filled : outline;
                var mat = mats[i % 3];
                var recolored = src.Select(p => new Part(p.mesh, Enumerable.Repeat(mat, Mathf.Max(1, p.mesh.subMeshCount)).ToArray(), p.local)).ToList();
                comb.Add(recolored, Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Stars_{chunk++:00}", false); chunkStart = d; }
            }
            comb.Flush(holder, $"Stars_{chunk:00}", false);
        }

        static void BuildPortholes(GameObject env)
        {
            var prefab = ModelPrefab("Machinery", "SM_Porthole");
            if (prefab == null) { Debug.LogWarning("[BWK] SM_Porthole missing - portholes skipped"); return; }
            string[] socks = { "SM_Sock_A", "SM_Sock_B", "SM_Sock_C", "SM_Towel", "SM_Shirt" };
            var holder = Child(env, "SideChambers");
            int side = -1;
            for (float d = tunnelStart + 14f; d < portalD - 10f; d += 13f + (float)rng.NextDouble() * 6f)
            {
                var f = track.Evaluate(d);
                float ang = side * 68f * Mathf.Deg2Rad;
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                var pos = f.FlatPoint(0, TunnelCenter) + radial * (TunnelRadius - 0.12f);
                var go = Spawn(prefab);
                go.name = $"Porthole_{d:000}";
                go.transform.SetParent(holder.transform, false);
                go.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(-radial, f.forward));
                // floating laundry inside the drum, behind the glass
                for (int s = 0; s < 4; s++)
                {
                    var sp = ModelPrefab("Props", socks[(s + (int)d) % socks.Length]);
                    if (sp == null) continue;
                    var sock = Spawn(sp);
                    sock.transform.SetParent(go.transform, false);
                    float a = s / 4f * Mathf.PI * 2f;
                    sock.transform.localPosition = new Vector3(Mathf.Cos(a) * 0.55f, Mathf.Sin(a) * 0.55f, -0.45f);
                    sock.transform.localRotation = Quaternion.Euler((float)rng.NextDouble() * 360f, (float)rng.NextDouble() * 360f, 0);
                    sock.transform.localScale = Vector3.one * 0.8f;
                    var bob = sock.AddComponent<FloatBob>();
                    bob.orbitAxis = Vector3.forward;
                    bob.orbitRadius = 0.25f;
                    bob.orbitSpeed = 55f + s * 7f;
                    bob.amplitude = 0.08f;
                }
                side = -side;
            }
        }

        static void BuildPipes(GameObject env, float L)
        {
            var pipe = ModelParts("Track", "SM_GlassPipe_Module");
            if (pipe.Count == 0) { Debug.LogWarning("[BWK] SM_GlassPipe_Module missing - pipes skipped"); return; }
            float a = 52f * Mathf.Deg2Rad;
            float lat = Mathf.Sin(a) * (TunnelRadius - 0.45f), up = TunnelCenter + Mathf.Cos(a) * (TunnelRadius - 0.45f);
            BendChunks(env, "GlassPipeLeft", pipe[0], tunnelStart + 1f, portalD - 3f, false, Vector3.one, -lat, up, 4f, false);
            BendChunks(env, "GlassPipeRight", pipe[0], tunnelStart + 1f, portalD - 3f, false, Vector3.one, lat, up, 4f, false);
            var coupler = ModelParts("Track", "SM_Pipe_Coupler");
            if (coupler.Count == 0) return;
            var holder = Child(env, "PipeCouplers");
            var comb = new Combiner();
            for (float d = tunnelStart + 3f; d < portalD - 3f; d += 6f)
            {
                var f = track.Evaluate(d);
                foreach (float sx in new[] { -lat, lat })
                    comb.Add(coupler, Matrix4x4.TRS(f.FlatPoint(sx, up), f.FlatRotation, Vector3.one));
            }
            comb.Flush(holder, "Couplers", false);
        }

        static void BuildFoam(GameObject env, float L)
        {
            var variants = new[] { ModelParts("Props", "SM_Foam_A"), ModelParts("Props", "SM_Foam_B"), ModelParts("Props", "SM_Foam_C") }.Where(v => v.Count > 0).ToArray();
            if (variants.Length == 0)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                var sm = s.GetComponent<MeshFilter>().sharedMesh;
                Object.DestroyImmediate(s);
                variants = new[] { new List<Part> { new Part(sm, new[] { Mat("M_Foam") }, Matrix4x4.Scale(new Vector3(1.6f, 0.9f, 1.2f))) } };
            }
            var holder = Child(env, "Foam");
            var comb = new Combiner();
            int chunk = 0; float chunkStart = 0f;
            for (float d = 0f; d < L; d += 1.3f)
            {
                var f = track.Evaluate(d);
                bool hall = d < tunnelStart;
                foreach (int side in new[] { -1, 1 })
                {
                    int count = hall ? 2 : 1;
                    for (int c = 0; c < count; c++)
                    {
                        float lat = side * (hall ? Mathf.Lerp(2.6f, 7.5f, (float)rng.NextDouble()) : Mathf.Lerp(2.55f, 3.15f, (float)rng.NextDouble()));
                        float h = hall ? Mathf.Lerp(-1.2f, 0.1f, (float)rng.NextDouble()) : Mathf.Lerp(-0.45f, 0.05f, (float)rng.NextDouble());
                        float sc = hall ? Mathf.Lerp(1.0f, 2.4f, (float)rng.NextDouble()) : Mathf.Lerp(0.75f, 1.25f, (float)rng.NextDouble());
                        var v = variants[rng.Next(variants.Length)];
                        var rot = f.FlatRotation * Quaternion.Euler(0, (float)rng.NextDouble() * 360f, 0);
                        comb.Add(v, Matrix4x4.TRS(f.FlatPoint(lat, h), rot, Vector3.one * sc));
                    }
                }
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Foam_{chunk++:00}", false); chunkStart = d; }
            }
            comb.Flush(holder, $"Foam_{chunk:00}", false);
        }

        static void BuildHallMachinery(GameObject env)
        {
            var holder = Child(env, "HallMachinery");
            void Place(string group, string name, float d, float lat, float h, Vector3 euler, float scale, float spin = 0f, Vector3 spinAxis = default)
            {
                var p = ModelPrefab(group, name);
                if (p == null) return;
                var f = track.Evaluate(d);
                var go = Spawn(p);
                go.transform.SetParent(holder.transform, false);
                go.transform.SetPositionAndRotation(f.FlatPoint(lat, h), f.FlatRotation * Quaternion.Euler(euler));
                go.transform.localScale = Vector3.one * scale;
                if (spin != 0f)
                {
                    var sp = go.AddComponent<Spinner>();
                    sp.degreesPerSecond = spin;
                    sp.localAxis = spinAxis == default ? Vector3.right : spinAxis;
                }
            }
            // big fluffy brush rollers high on the left (reference top-left), spinning
            Place("Machinery", "SM_BrushRoller", 22f, -5.6f, 5.2f, new Vector3(0, 35, 10), 1.25f, 45f, Vector3.right);
            Place("Machinery", "SM_BrushRoller", 44f, -6.2f, 6.0f, new Vector3(0, 25, 8), 1.15f, -40f, Vector3.right);
            Place("Machinery", "SM_BrushRoller", 30f, 6.8f, 7.5f, new Vector3(0, -30, -6), 1.0f, 38f, Vector3.right);
            // control console on the left, facing the slide
            Place("Machinery", "SM_ControlPanel", 16f, -5.4f, 1.6f, new Vector3(0, 125, 0), 1.2f);
            // lavender pillars with gold bands on the right
            Place("Machinery", "SM_Pillar", 19f, 4.6f, -1.5f, new Vector3(0, -90, 0), 1.0f);
            Place("Machinery", "SM_Pillar", 38f, 5.0f, -2.0f, new Vector3(0, -90, 0), 1.0f);
            Place("Machinery", "SM_Pillar", 56f, 5.4f, -2.5f, new Vector3(0, -90, 0), 1.0f);
            Place("Machinery", "SM_Pillar", 50f, -6.5f, -2.5f, new Vector3(0, 90, 0), 1.0f);
            // agitator column and golden plumbing in the background
            Place("Machinery", "SM_Agitator", 34f, -11f, -4f, Vector3.zero, 1.6f, 25f, Vector3.up);
            for (int i = 0; i < 5; i++)
            {
                Place("Machinery", "SM_GoldPipe_Straight", 10f + i * 2.05f, -6.8f, 3.4f, new Vector3(0, 180, 0), 1f);
                Place("Machinery", "SM_GoldPipe_Straight", 28f + i * 2.05f, 7.4f, 4.2f, new Vector3(0, 180, 0), 1f);
            }
            Place("Machinery", "SM_ValveWheel", 14f, -6.5f, 3.4f, new Vector3(0, 90, 0), 1f, 30f, Vector3.forward);
            Place("Machinery", "SM_Porthole", 40f, -9.5f, 3.5f, new Vector3(0, 70, 0), 1.6f);
        }

        static void BuildFloatingBubbles(GameObject env, float L)
        {
            var bubble = ModelPrefab("Props", "SM_Bubble");
            if (bubble == null) return;
            var holder = Child(env, "FloatingBubbles");
            for (float d = 6f; d < L - 4f; d += 4.5f + (float)rng.NextDouble() * 4f)
            {
                var f = track.Evaluate(d);
                bool hall = d < tunnelStart;
                float lat = (float)(rng.NextDouble() * 2 - 1) * (hall ? 7f : 3.0f);
                float h = Mathf.Lerp(0.9f, hall ? 7f : 4.8f, (float)rng.NextDouble());
                var go = Spawn(bubble);
                go.transform.SetParent(holder.transform, false);
                go.transform.position = f.FlatPoint(lat, h);
                go.transform.localScale = Vector3.one * Mathf.Lerp(0.25f, 0.9f, (float)rng.NextDouble());
                var bob = go.AddComponent<FloatBob>();
                bob.amplitude = 0.25f;
                bob.frequency = 0.2f;
                bob.swayDegrees = 0f;
                foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
            }
        }

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

        static void BuildDecorChevrons(GameObject env, float L)
        {
            var chevron = ModelParts("Props", "SM_Chevron");
            if (chevron.Count == 0) return;
            var holder = Child(env, "DecorChevrons");
            var comb = new Combiner();
            int chunk = 0; float chunkStart = 0;
            for (float d = 6f; d < L - 6f; d += 3.2f)
            {
                var f = track.Evaluate(d);
                comb.Add(chevron, Matrix4x4.TRS(f.Point(0, 0.03f), f.Rotation, new Vector3(0.75f, 1f, 0.75f)));
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Chevrons_{chunk++:00}", false); chunkStart = d; }
            }
            comb.Flush(holder, $"Chevrons_{chunk:00}", false);
        }

        static void BuildPortal(GameObject env, RunnerController runner)
        {
            var f = track.Evaluate(portalD);
            var portal = Child(env, "LightPortal");
            portal.transform.SetPositionAndRotation(f.FlatPoint(0, TunnelCenter), f.FlatRotation);
            var ring = ModelPrefab("Track", "SM_Ring");
            if (ring != null)
            {
                var r = Spawn(ring);
                r.transform.SetParent(portal.transform, false);
                r.transform.localScale = Vector3.one * 0.98f;
            }
            var rays = Child(portal, "Rays");
            rays.transform.localPosition = new Vector3(0, 0, 1.5f);
            rays.transform.localRotation = Quaternion.Euler(0, 180, 0);
            var quad = ProceduralModules.Quad(9.5f);
            SaveMesh(quad);
            rays.AddComponent<MeshFilter>().sharedMesh = quad;
            var rr = rays.AddComponent<MeshRenderer>();
            rr.sharedMaterial = Mat("M_PortalRays");
            rr.shadowCastingMode = ShadowCastingMode.Off;
            var core = Child(portal, "Core");
            core.transform.localPosition = new Vector3(0, 0, 3f);
            core.transform.localRotation = Quaternion.Euler(0, 180, 0);
            var coreMesh = ProceduralModules.Annulus(0.01f, 3.7f);
            SaveMesh(coreMesh);
            core.AddComponent<MeshFilter>().sharedMesh = coreMesh;
            var cr = core.AddComponent<MeshRenderer>();
            cr.sharedMaterial = Mat("M_Bulb");
            cr.shadowCastingMode = ShadowCastingMode.Off;
            var lightGo = Child(portal, "PortalLight");
            lightGo.transform.localPosition = new Vector3(0, 0, -1.5f);
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = new Color(1f, 0.85f, 0.55f);
            light.range = 28f;
            light.intensity = 2f;
            var glow = portal.AddComponent<PortalGlow>();
            glow.runner = runner;
            glow.trackDistance = portalD;
            glow.rays = new Renderer[] { rr };
            glow.portalLight = light;
        }

        // ==================================================================== lighting
        static void BuildLighting(GameObject root, float L)
        {
            var lights = Child(root, "Lighting");
            var sunGo = Child(lights, "Key Light");
            sunGo.transform.rotation = Quaternion.Euler(48f, -25f, 0f);
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.9f, 0.95f);
            sun.intensity = 1.35f;
            sun.shadows = LightShadows.Soft;
            sun.shadowStrength = 0.75f;
            RenderSettings.sun = sun;

            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.62f, 0.5f, 0.95f);
            RenderSettings.ambientEquatorColor = new Color(0.95f, 0.5f, 0.8f);
            RenderSettings.ambientGroundColor = new Color(0.3f, 0.45f, 0.95f);
            RenderSettings.ambientIntensity = 1f;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = new Color(0.55f, 0.38f, 0.86f);
            RenderSettings.fogDensity = 0.012f;
            RenderSettings.skybox = null;
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;

            // colourful fill lights in the hall
            AddPoint(lights, 18f, -4f, 6f, new Color(1f, 0.45f, 0.85f), 3f, 18f);
            AddPoint(lights, 40f, 5f, 6f, new Color(0.35f, 0.85f, 1f), 3f, 18f);

            // reflection probes (baked to custom cubemaps after save)
            for (float d = 18f; d < L; d += d < tunnelStart ? 30f : 55f)
            {
                var f = track.Evaluate(d);
                var pg = Child(lights, $"ReflectionProbe_{d:000}");
                pg.transform.position = f.FlatPoint(0, d < tunnelStart ? 4f : TunnelCenter);
                var probe = pg.AddComponent<ReflectionProbe>();
                probe.mode = ReflectionProbeMode.Custom;
                probe.resolution = 128;
                probe.size = d < tunnelStart ? new Vector3(40, 30, 50) : new Vector3(12, 12, 60);
                probe.importance = 1;
                probe.hdr = true;
                probe.boxProjection = false;
            }

            // post-processing volume
            var volGo = Child(root, "PostFX Volume");
            var vol = volGo.AddComponent<Volume>();
            vol.isGlobal = true;
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, $"{GenDir}/PostFX_Level01.asset");
            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.Override(0.8f); bloom.intensity.Override(1.7f); bloom.scatter.Override(0.72f);
            bloom.tint.Override(new Color(1f, 0.92f, 0.95f)); bloom.highQualityFiltering.Override(false);
            var tm = profile.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.Neutral);
            var ca = profile.Add<ColorAdjustments>(true);
            ca.saturation.Override(18f); ca.contrast.Override(12f); ca.postExposure.Override(0.15f);
            var vg = profile.Add<Vignette>(true); vg.intensity.Override(0.2f); vg.smoothness.Override(0.45f);
            var wb = profile.Add<WhiteBalance>(true); wb.temperature.Override(4f); wb.tint.Override(6f);
            foreach (var c in profile.components) AssetDatabase.AddObjectToAsset(c, profile);
            vol.sharedProfile = profile;
        }

        static void AddPoint(GameObject parent, float d, float lat, float h, Color c, float intensity, float range)
        {
            var f = track.Evaluate(d);
            var go = Child(parent, $"Fill_{d:000}");
            go.transform.position = f.FlatPoint(lat, h);
            var l = go.AddComponent<Light>();
            l.type = LightType.Point; l.color = c; l.intensity = intensity; l.range = range; l.shadows = LightShadows.None;
        }

        static void BakeProbes()
        {
            foreach (var probe in Object.FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None))
            {
                string path = $"{GenDir}/{probe.name}.exr";
                try
                {
                    if (Lightmapping.BakeReflectionProbe(probe, path))
                    {
                        AssetDatabase.ImportAsset(path);
                        probe.customBakedTexture = AssetDatabase.LoadAssetAtPath<Texture>(path);
                    }
                }
                catch (System.Exception e) { Debug.LogWarning($"[BWK] probe bake failed for {probe.name}: {e.Message}"); }
            }
        }

        // ==================================================================== runner FX
        static SplashFX BuildRunnerFX(GameObject runnerGo, RunnerController runner, TrackItemRegistry registry)
        {
            var fxRoot = Child(runnerGo, "FX");
            var fx = fxRoot.AddComponent<SplashFX>();
            fx.runner = runner;
            fx.items = registry;
            fx.spray = Particles(fxRoot, "Spray", "M_FX_Splash", new Vector3(0, 0.08f, -0.2f), new Vector3(-90, 0, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.18f, 0.38f); m.startSpeed = new ParticleSystem.MinMaxCurve(1.8f, 3.4f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.08f, 0.22f); m.gravityModifier = 1.4f; m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 120;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 55f; sh.radius = 0.35f;
                var e = ps.emission; e.rateOverTime = 0f;
            });
            fx.foamTrail = Particles(fxRoot, "FoamTrail", "M_FX_Soft", new Vector3(0, 0.05f, -0.3f), new Vector3(-90, 0, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.25f, 0.45f); m.startSpeed = 0.2f;
                m.startSize = new ParticleSystem.MinMaxCurve(0.3f, 0.6f); m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 60;
                m.startColor = new Color(1f, 1f, 1f, 0.8f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 0.35f;
                var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0, 0.6f, 1, 1.4f));
                var col = ps.colorOverLifetime; col.enabled = true;
                var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) }, new[] { new GradientAlphaKey(0.9f, 0), new GradientAlphaKey(0f, 1) });
                col.color = g;
                var r = ps.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.HorizontalBillboard;
                var e = ps.emission; e.rateOverTime = 0f;
            });
            fx.crown = Particles(fxRoot, "Crown", "M_FX_Splash", new Vector3(0, 0.1f, 0), new Vector3(-90, 0, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.35f, 0.7f); m.startSpeed = new ParticleSystem.MinMaxCurve(3f, 5.5f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.12f, 0.3f); m.gravityModifier = 1.8f; m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 120;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 40f; sh.radius = 0.5f;
                var e = ps.emission; e.rateOverTime = 0f;
            });
            fx.speedStreaks = Particles(fxRoot, "SpeedStreaks", "M_FX_Streak", new Vector3(0, 1.0f, 6f), new Vector3(0, 180, 0), ps =>
            {
                var m = ps.main; m.startLifetime = 0.35f; m.startSpeed = 22f; m.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.12f);
                m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 120; m.loop = true; m.playOnAwake = false;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 2.4f; sh.radiusThickness = 0.3f;
                var e = ps.emission; e.rateOverTime = 120f;
                var r = ps.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.06f; r.lengthScale = 2f;
            });
            fx.pickupSparkles = Particles(fxRoot, "PickupSparkles", "M_FX_Sparkle", Vector3.zero, Vector3.zero, ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.25f, 0.5f); m.startSpeed = new ParticleSystem.MinMaxCurve(1f, 3f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.15f, 0.4f); m.simulationSpace = ParticleSystemSimulationSpace.World; m.maxParticles = 200;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.2f;
                var e = ps.emission; e.rateOverTime = 0f;
            });
            fx.gemSparkles = Particles(fxRoot, "GemSparkles", "M_FX_GemSparkle", Vector3.zero, Vector3.zero, ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.3f, 0.7f); m.startSpeed = new ParticleSystem.MinMaxCurve(1.5f, 3.5f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.2f, 0.5f); m.simulationSpace = ParticleSystemSimulationSpace.World; m.maxParticles = 200;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.25f;
                var e = ps.emission; e.rateOverTime = 0f;
            });
            // ambient soap bubbles drifting in front of the mascot
            Particles(fxRoot, "AmbientBubbles", "M_FX_Bubble", new Vector3(0, 2.2f, 9f), Vector3.zero, ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(3f, 5f); m.startSpeed = new ParticleSystem.MinMaxCurve(0.1f, 0.5f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.12f, 0.55f); m.simulationSpace = ParticleSystemSimulationSpace.World; m.maxParticles = 120;
                m.gravityModifier = -0.04f; m.prewarm = true;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(8f, 4f, 10f);
                var e = ps.emission; e.rateOverTime = 18f;
            });
            return fx;
        }

        static ParticleSystem Particles(GameObject parent, string name, string mat, Vector3 pos, Vector3 euler, System.Action<ParticleSystem> setup)
        {
            var go = Child(parent, name);
            go.transform.localPosition = pos;
            go.transform.localRotation = Quaternion.Euler(euler);
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = Mat(mat);
            r.renderMode = ParticleSystemRenderMode.Billboard;
            r.shadowCastingMode = ShadowCastingMode.Off;
            r.receiveShadows = false;
            var m = ps.main; m.playOnAwake = true;
            setup(ps);
            return ps;
        }

        // ==================================================================== cameras
        static CameraDirector BuildCameras(GameObject root, RunnerController runner)
        {
            var camGo = new GameObject("Main Camera");
            camGo.transform.SetParent(root.transform, false);
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.nearClipPlane = 0.12f;
            cam.farClipPlane = 260f;
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
                lens.FieldOfView = fov; lens.NearClipPlane = 0.12f; lens.FarClipPlane = 260f;
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
