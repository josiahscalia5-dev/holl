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
    // OWNER: Agent 2 - water & visual effects (foam banks, floating bubbles, runner splash/spray particles, decor chevrons).
    // Only this domain's agent edits this file; the lead developer runs the scene build that calls it.
    // Determinism: these builders use their own seeded System.Random. They still draw the same number of values from the
    // shared `rng` as the original foam / bubble placement did, so the lead's item layout (BuildItems) never shifts.
    public static partial class SceneBuilder
    {
        // decor chevrons down the middle of the water (also drive the light pools in M_Water / BWK_Water). Reference
        // f_002.00-f_003.25: a runway of glowing chevrons about one chevron length apart (SM_Chevron is 1.31 x 0.65 m).
        // phase / spacing put the hero frame's chevron tips at the reference: under him (screen y .72) and at the bottom (y .87)
        // round 4 (reference f_003.00s measured: near apex screen (.64, .745), bottom apex (.64, .93) -> ~1.1 m apart; the
        // mascot rides LEFT of the arrow runway in every reference frame 0.5-3.25 s): spacing 1.1 m, start keeps a chevron
        // origin at 104.9 m (apex just under him), runway ChevronLateral m right of the centre lane.
        public const float ChevronStart = 5.9f, ChevronSpacing = 1.1f, ChevronScale = 1.35f;
        // narrower than long: steeper arms like the reference (bottom chevron arm meets the frame bottom at x ~.2)
        public const float ChevronWidth = 0.5f;
        // round 4 decor chevron (generated, not SM_Chevron): FAT filled arms like the reference (arm 0.30 m across, small
        // notch), arm centre line from the apex (0, HalfLen) to (+-HalfWidth, -HalfLen) in metres (z = travel)
        // round 4 continuation (reference f_03.00s 4K back-projected onto the water through the hero camera: outer apex
        // runner z -0.08, notch 0.51 m behind it, 45-degree arms, arm ends CUT ALONG TRAVEL ~0.42 m beside the axis, arms
        // ~0.36 m across): HalfLen / HalfWidth now only set the arm slope (2 HL / HW = 1 -> 45 deg) and the apex offset;
        // every arm edge ends at |x| = ChevronEndX (the old constant-z cut drew a long thin left spike to screen x .14)
        public const float ChevronLateral = 0.30f, ChevronHalfLen = 0.25f, ChevronHalfWidth = 0.50f, ChevronThick = 0.36f;
        public const float ChevronEndX = 0.38f;
        // the runway WEAVES gently across the slide (reference f_03.00s: near apex at runner x .34, the next arrow's apex 1.14 m
        // closer at x .20 -> the arrow line runs diagonally toward the right bend, arrows turned ~7 deg to follow it):
        // lateral(d) = WeaveAmp sin(2 pi (d - WeaveZero) / WeaveLen), each arrow yawed along that line (BWK_Water does the same)
        // (v3: 22 m / zero 102.87 centred the bottom arrow but swung the near arrow's left arm out to x .28 (ref .36-.41):
        // v4 = steeper line - near origin lateral .31, bottom .13, ~8 deg yaw; arm ends .38)
        public const float ChevronWeaveAmp = 0.5f, ChevronWeaveLen = 17f, ChevronWeaveZero = 103.09f;
        public static float ChevronLateralAt(float d) => ChevronWeaveAmp * Mathf.Sin(2f * Mathf.PI * (d - ChevronWeaveZero) / ChevronWeaveLen);
        public static float ChevronYawAt(float d) =>
            Mathf.Atan(ChevronWeaveAmp * 2f * Mathf.PI / ChevronWeaveLen * Mathf.Cos(2f * Mathf.PI * (d - ChevronWeaveZero) / ChevronWeaveLen)) * Mathf.Rad2Deg;
        const float ChevronHeight = 0.015f;
        // milk crown splashes beside the feet (Art/Models/FX/SM_FX_Crown_xx, left-side asset mirrored for the right).
        // (round 2 anchored the root in screen space; reference f_003.00s: crowns rise at x 0-.40 / .62-1, y .55-.87).
        // Round 3b: the crown asset (build_fx_splash.py) is authored in runner-local space around the left foot (foot ~(-0.30, 0.17, -0.30))
        // and checked through the hero camera in Blender (Docs/AssetPreviews/FX_SplashCrown_r3.png): a perforated milky curtain rising
        // outward beside each foot + a low perforated skirt curling under the foot toward the camera. Origin = (-CrownRootX, 0, CrownRootZ).
        const float CrownRootX = 0.40f, CrownRootZ = -0.05f;
        const float CrownScale = 1.0f, CrownYaw = 0f;   // authored facing the hero camera: no yaw
        // reference f_003.00s foreground bubbles: screen x, screen y (0..1 from the top-left of the 9:16 hero frame),
        // diameter as a fraction of the frame width, w > 0 = height above the water (m), w < 0 = -camera depth (m)
        static readonly Vector4[] HeroBubbleSpots =
        {
            new Vector4(0.315f, 0.849f, 0.075f, 0.30f), new Vector4(0.324f, 0.893f, 0.047f, 0.22f),
            new Vector4(0.215f, 0.891f, 0.042f, 0.22f), new Vector4(0.178f, 0.923f, 0.047f, 0.18f),
            new Vector4(0.136f, 0.916f, 0.030f, 0.18f), new Vector4(0.164f, 0.893f, 0.017f, 0.20f),
            new Vector4(0.333f, 0.802f, 0.033f, 0.30f), new Vector4(0.899f, 0.904f, 0.076f, 0.25f),
            // owner: "more bubbles in front and around the character" (beside the body, never over it)
            new Vector4(0.085f, 0.640f, 0.034f, -2.1f), new Vector4(0.905f, 0.700f, 0.030f, -2.1f),
            new Vector4(0.170f, 0.530f, 0.022f, -2.3f), new Vector4(0.845f, 0.560f, 0.024f, -2.3f),
        };

        // S2 pass 2: reference 3.0 s bubbles at the door, (px x, px y, radius px) on the 1280 x 720 frame + depth (m) from the
        // S2 comparison camera; the first two are the big iridescent ones, the rest small ones beside the mascot / over the foam
        static readonly Vector4[] S2BubbleSpots =
        {
            new Vector4(1115f, 110f, 45f, 4.0f), new Vector4(20f, 250f, 45f, 3.5f),
            new Vector4(40f, 105f, 18f, 3.2f), new Vector4(870f, 325f, 16f, 3.0f), new Vector4(888f, 292f, 10f, 3.0f),
            new Vector4(1090f, 600f, 12f, 2.0f), new Vector4(530f, 650f, 13f, 1.5f), new Vector4(548f, 690f, 9f, 1.4f),
            new Vector4(805f, 688f, 13f, 1.5f), new Vector4(232f, 455f, 9f, 2.4f), new Vector4(175f, 245f, 8f, 3.0f),
        };

        /// <summary>Runner-local point on the S2 comparison camera's ray through pixel (px, py) of a 1280 x 720 frame at camera
        /// depth z (CaptureTools R2_rear_S2_like_3s: runner - 2.75 fwd + 1.0 up + 0.3 right, Euler(6, -9, 0), vFOV 58).</summary>
        static Vector3 S2CamPoint(float px, float py, float z)
        {
            float ty = Mathf.Tan(29f * Mathf.Deg2Rad);
            var dir = new Vector3((px / 1280f - 0.5f) * 2f * ty * (16f / 9f), (0.5f - py / 720f) * 2f * ty, 1f);
            return s2CamPos + s2CamRot * (dir * z);
        }
        // runner-local S2 camera (p1 used the flat model below and landed ~60 px off: the runner frame is sloped at 35 m)
        static Vector3 s2CamPos = new Vector3(0.3f, 1.0f, -2.75f);
        static Quaternion s2CamRot = Quaternion.Euler(6f, -9f, 0f);

        /// <summary>Measures the S2 comparison camera exactly like CaptureTools (world space at HeroMouthDistance) and stores
        /// it in the runner's local space; the runner is put back where it was.</summary>
        static void MeasureS2Cam(RunnerController runner)
        {
            if (runner == null || runner.track == null) return;
            float d0 = runner.Distance, lat0 = runner.Lateral;
            try
            {
                runner.TeleportTo(HeroMouthDistance, 0f);
                var f = runner.Frame;
                Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
                var rt = runner.transform;
                Vector3 cp = rt.position - fwd * 2.75f + Vector3.up * 1.0f + right * 0.3f;
                var rot = Quaternion.LookRotation(fwd, Vector3.up) * Quaternion.Euler(6f, -9f, 0f);
                s2CamPos = rt.InverseTransformPoint(cp);
                s2CamRot = Quaternion.Inverse(rt.rotation) * rot;
                Debug.Log($"[BWK] waterfx S2 cam (runner-local) pos {s2CamPos:F3} euler {s2CamRot.eulerAngles:F2}");
            }
            catch (System.Exception ex) { Debug.LogWarning("[BWK] waterfx S2 camera measurement failed: " + ex.Message); }
            finally { runner.TeleportTo(d0, lat0); }
        }

        /// <summary>Diameter (m) of a sphere of radius rPx pixels at camera depth z in the S2 comparison camera (720 px tall).</summary>
        static float S2CamSize(float rPx, float z) => 2f * rPx / 360f * Mathf.Tan(29f * Mathf.Deg2Rad) * z;

        // ==================================================================== hero camera (screen-space placement)
        /// <summary>The owner-approved hero camera in the runner's local space (= FX root space) at the hero distance.</summary>
        struct HeroCam
        {
            public Vector3 pos; public Quaternion rot; public float fov, aspect;
            float Ty => Mathf.Tan(fov * 0.5f * Mathf.Deg2Rad);
            /// <summary>Ray through screen point (sx, sy from the top-left, 0..1), scaled so its camera-space z is 1.</summary>
            public Vector3 Ray(float sx, float sy) => rot * new Vector3((sx - 0.5f) * 2f * Ty * aspect, (0.5f - sy) * 2f * Ty, 1f);
            /// <summary>Point on that ray at runner-local height h (w > 0) or at camera depth -w (w < 0).</summary>
            public Vector3 At(float sx, float sy, float w, out float depth)
            {
                var d = Ray(sx, sy);
                depth = w < 0f ? -w : (d.y < -0.02f ? Mathf.Clamp((w - pos.y) / d.y, 0.6f, 12f) : 3f);
                return pos + d * depth;
            }
            public float WidthAt(float frac, float depth) => frac * 2f * depth * Ty * aspect;
            public Vector2 Project(Vector3 p)
            {
                var v = Quaternion.Inverse(rot) * (p - pos);
                return new Vector2(0.5f + 0.5f * v.x / (v.z * Ty * aspect), 0.5f - 0.5f * v.y / (v.z * Ty));
            }
        }

        /// <summary>
        /// Measures the hero camera with the real RunnerCameraRig code: the scene's rig in previews, a temporary rig in the
        /// full build (BuildRunnerFX runs before BuildCameras). Runner and rig state are restored; only logs are written.
        /// </summary>
        static HeroCam MeasureHeroCam(RunnerController runner)
        {
            // fallback = last measurement (2.75 / 1.3 / 10 / 58 camera at 105.5 m)
            var cam = new HeroCam { pos = new Vector3(0.099f, 0.768f, -2.640f), rot = Quaternion.Euler(1.52f, 356.38f, 354.26f), fov = HeroCamFov, aspect = 9f / 16f };
            if (runner == null || runner.track == null) return cam;
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            GameObject temp = null;
            if (rig == null)
            {
                temp = new GameObject("_HeroCamProbe") { hideFlags = HideFlags.HideAndDontSave };
                rig = temp.AddComponent<RunnerCameraRig>();
                rig.runner = runner;
            }
            float d0 = runner.Distance, lat0 = runner.Lateral, asp0 = rig.aspectOverride;
            var saved = new[] { rig.distanceBackPortrait, rig.heightPortrait, rig.pitchDownPortrait, rig.fovPortrait };
            try
            {
                ApplyHeroCamera(rig);
                runner.TeleportTo(HeroDistance, 0f);
                rig.aspectOverride = 9f / 16f;
                rig.Snap();
                var rt = runner.transform;
                float dutch = rig.vcam != null ? rig.vcam.Lens.Dutch : Mathf.Clamp(-runner.Frame.roll * rig.bankFactor, -rig.maxDutch, rig.maxDutch);
                cam.pos = rt.InverseTransformPoint(rig.transform.position);
                cam.rot = Quaternion.Inverse(rt.rotation) * rig.transform.rotation * Quaternion.Euler(0f, 0f, dutch);
                cam.fov = rig.vcam != null ? rig.vcam.Lens.FieldOfView : HeroCamFov;
                var e = cam.rot.eulerAngles;
                Debug.Log($"[BWK] waterfx herocam (runner-local) pos ({cam.pos.x:F3}, {cam.pos.y:F3}, {cam.pos.z:F3}) euler ({e.x:F2}, {e.y:F2}, {e.z:F2}) fov {cam.fov:F1} {(temp != null ? "temp rig" : "scene rig")}");
                if (InWaterFxPreview)
                {
                    var sb = new System.Text.StringBuilder("[BWK] waterfx herotrack d=(local x,y,z)@screen:");
                    for (float d = HeroDistance - 2.5f; d <= HeroDistance + 4.01f; d += 0.5f)
                    {
                        var p = rt.InverseTransformPoint(runner.track.Evaluate(d).Point(0f, 0f));
                        var s = cam.Project(p);
                        sb.Append($" {d:F1}=({p.x:F2},{p.y:F2},{p.z:F2})@({s.x:F2},{s.y:F2})");
                    }
                    Debug.Log(sb.ToString());
                }
            }
            catch (System.Exception ex) { Debug.LogWarning("[BWK] waterfx hero camera measurement failed: " + ex.Message); }
            finally
            {
                rig.distanceBackPortrait = saved[0]; rig.heightPortrait = saved[1]; rig.pitchDownPortrait = saved[2]; rig.fovPortrait = saved[3];
                rig.aspectOverride = asp0;
                runner.TeleportTo(d0, lat0);
                if (temp != null) Object.DestroyImmediate(temp);
            }
            return cam;
        }

        // ==================================================================== preview / persistence helpers
        static string PreviewOutArg()
        {
            var args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++) if (args[i] == "-bwkOut") return args[i + 1].Replace('\\', '/');
            return null;
        }

        /// <summary>
        /// Water/FX agent preview of the WHOLE level (round 7, no save): textures + materials, open the saved scene, rebuild the
        /// preview domains in memory (runner FX + this domain's foam / chevrons / bubbles because -bwkOut contains
        /// agents/waterfx), then every comparison still (01-09, C1-C5, R3-R6, + bg/ with the mascot hidden) into -bwkOut.
        /// Run: bash Tools/unity_run.sh BubbleWash.EditorTools.SceneBuilder.WaterFxStillsBatch LOG -bwkOut Captures/agents/waterfx/r7/stills_vN
        /// </summary>
        public static void WaterFxStillsBatch()
        {
            try
            {
                string outDir = PreviewOutArg() ?? "Captures/agents/waterfx/r7/stills";
                if (!outDir.Contains("agents/waterfx")) throw new System.Exception("-bwkOut must be under Captures/agents/waterfx");
                TextureGenerator.Run();
                MaterialLibrary.Run();
                EditorSceneManager.OpenScene(ScenePath);
                PreviewRefreshDomains();
                CaptureTools.CaptureStills(outDir);
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] waterfx stills failed: " + e); EditorApplication.Exit(1); }
        }

        /// <summary>Any agent preview (AgentPreviewBatch): never write mesh assets.</summary>
        static bool InAgentPreview => PreviewOutArg() != null;

        /// <summary>This domain's own preview: also rebuild foam / chevrons / floating bubbles in memory.</summary>
        static bool InWaterFxPreview => (PreviewOutArg() ?? "").Contains("agents/waterfx");

        static Mesh PersistCopy(Mesh src, bool save)
        {
            var m = Object.Instantiate(src);
            m.name = src.name;
            if (save) SaveMesh(m);
            return m;
        }

        /// <summary>Like Combiner, but can keep the combined meshes in memory (previews never write assets).</summary>
        class FxCombiner
        {
            readonly Dictionary<Material, List<CombineInstance>> groups = new Dictionary<Material, List<CombineInstance>>();
            readonly Dictionary<Material, int> vertexCounts = new Dictionary<Material, int>();

            public void Add(List<Part> parts, Matrix4x4 world)
            {
                foreach (var p in parts)
                    for (int s = 0; s < p.mesh.subMeshCount; s++)
                    {
                        var mat = p.mats != null && p.mats.Length > 0 ? p.mats[Mathf.Min(s, p.mats.Length - 1)] : null;
                        if (mat == null) continue;
                        if (!groups.TryGetValue(mat, out var l)) { l = new List<CombineInstance>(); groups[mat] = l; vertexCounts[mat] = 0; }
                        l.Add(new CombineInstance { mesh = p.mesh, subMeshIndex = s, transform = world * p.local });
                        vertexCounts[mat] += p.mesh.vertexCount;
                    }
            }

            public List<Renderer> Flush(GameObject parent, string name, bool save)
            {
                var made = new List<Renderer>();
                foreach (var kv in groups)
                {
                    var mesh = new Mesh { name = $"{name}_{kv.Key.name}" };
                    mesh.indexFormat = vertexCounts[kv.Key] > 60000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
                    mesh.CombineMeshes(kv.Value.ToArray(), true, true);
                    mesh.RecalculateBounds();
                    if (save) SaveMesh(mesh);
                    var go = Child(parent, mesh.name);
                    go.AddComponent<MeshFilter>().sharedMesh = mesh;
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterial = kv.Key;
                    mr.shadowCastingMode = ShadowCastingMode.Off;
                    GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic | StaticEditorFlags.ReflectionProbeStatic);
                    made.Add(mr);
                }
                groups.Clear();
                vertexCounts.Clear();
                return made;
            }
        }

        // exact replicas of the original placement loops' shared-rng draws (6 per foam cluster, 4 per bubble step)
        static void ConsumeLegacyFoamRng(float L)
        {
            if (rng == null) return;
            for (float d = 0f; d < L; d += (d < tunnelStart ? 2.0f : 2.3f))
                for (int k = 0; k < 4; k++)
                {
                    rng.NextDouble(); rng.NextDouble(); rng.NextDouble(); rng.Next(3); rng.NextDouble(); rng.NextDouble();
                }
        }

        static void ConsumeLegacyBubbleRng(float L)
        {
            if (rng == null) return;
            for (float d = 6f; d < L - 4f; d += 4.5f + (float)rng.NextDouble() * 4f)
            {
                rng.NextDouble(); rng.NextDouble(); rng.NextDouble();
            }
        }

        // ==================================================================== foam banks
        static void BuildFoam(GameObject env, float L) => BuildFoam(env, L, false);

        static void BuildFoam(GameObject env, float L, bool preview)
        {
            if (!preview) ConsumeLegacyFoamRng(L);
            var r = new System.Random(4471);
            float Rand(float a, float b) => Mathf.Lerp(a, b, (float)r.NextDouble());
            // LOD0 = full soap-suds clusters near the camera, LOD1 = low-poly twins for distant chunks (same placement)
            // round 7 (owner 13:30 "replace the artificial foam blobs throughout the level"; asset library 17 "many small,
            // rounded foam bubbles ... never huge opaque cloud blobs"): the v2 bubble clusters (build_fx_v2.py: core + ~190
            // half-sunk 3.5-7.5 cm bubbles, baked crevice AO in vertex colour R, LOD1 twins) replace SM_Foam_A-C everywhere,
            // all on the measured M_Foam_v2 (#F4F6FC / #B6BCDC). Old assets only as a fallback.
            string[] names = { "SM_Foam_v2_Bank", "SM_Foam_v2_Mound", "SM_Foam_v2_Puffs" };
            var foamV2 = new[] { Mat("M_Foam_v2") };
            List<Part> V2(string n) => ModelParts("FX", n).Select(p => new Part(p.mesh, foamV2, p.local)).ToList();
            var lod0 = names.Select(V2).Where(v => v.Count > 0).ToArray();
            var lod1 = names.Select(n => { var p = V2(n + "_LOD1"); return p.Count > 0 ? p : V2(n); }).Where(v => v.Count > 0).ToArray();
            bool v2 = lod0.Length == names.Length && lod1.Length == names.Length;
            if (!v2)
            {
                Debug.LogWarning("[BWK] foam v2 assets missing - falling back to SM_Foam_A-C");
                names = new[] { "SM_Foam_A", "SM_Foam_B", "SM_Foam_C" };
                lod0 = names.Select(n => ModelParts("Props", n)).Where(v => v.Count > 0).ToArray();
                lod1 = names.Select(n => { var p = ModelParts("Props", n + "_LOD1"); return p.Count > 0 ? p : ModelParts("Props", n); }).Where(v => v.Count > 0).ToArray();
            }
            if (lod0.Length == 0)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                var sm = s.GetComponent<MeshFilter>().sharedMesh;
                Object.DestroyImmediate(s);
                lod0 = lod1 = new[] { new List<Part> { new Part(sm, new[] { Mat("M_Foam") }, Matrix4x4.Scale(new Vector3(1.6f, 0.9f, 1.2f))) } };
            }
            int small = lod0.Length > 2 ? 2 : lod0.Length - 1;   // SM_Foam_C = the small cluster
            var holder = Child(env, "Foam");
            var comb0 = new FxCombiner();
            var comb1 = new FxCombiner();
            int chunk = 0; float chunkStart = 0f;
            void FlushChunk()
            {
                var go = Child(holder, $"Foam_{chunk:00}");
                var r0 = comb0.Flush(go, $"Foam_{chunk:00}_LOD0", !preview);
                var r1 = comb1.Flush(go, $"Foam_{chunk:00}_LOD1", !preview);
                var lg = go.AddComponent<LODGroup>();
                lg.SetLODs(new[] { new LOD(0.4f, r0.ToArray()), new LOD(0.01f, r1.ToArray()) });
                lg.RecalculateBounds();
                chunk++;
            }
            // round 3b (reference f_003.00s, owner sheet 03): in the hero view the soft cumulus banks sit on the LEFT bank ahead
            // (screen x 0-.25, y .35-.50) and the right bank ahead stays clear (the track bends right after the mirror, so
            // the right bank is in full view there). Same rng draws either way: the rest of the foam layout never shifts.
            float heroD = 0f;
            void Place(TrackFrame f, float lat, float h, float sc, int vi)
            {
                // clusters are long along asset X: turn them to run along the track so they never cover the water
                var rot = f.FlatRotation * Quaternion.Euler(0, 90f + Rand(-20f, 20f) + (r.NextDouble() < 0.5 ? 180f : 0f), 0);
                float yS = Rand(0.9f, 1.15f);
                bool heroWin = heroD > HeroDistance - 1.5f && heroD < HeroDistance + 15f;
                // right bank clear in the hero view (round 4: to +26 m - a right-bank cumulus still showed at screen (.8, .4))
                if (lat > 0f && heroD > HeroDistance - 1.5f && heroD < HeroDistance + 26f) return;
                if (heroWin) { sc *= 1.3f; h += 0.12f; }                  // fuller, taller left banks
                var m = Matrix4x4.TRS(f.FlatPoint(lat, h), rot, new Vector3(sc, sc * yS, sc));
                comb0.Add(lod0[vi], m);
                comb1.Add(lod1[Mathf.Min(vi, lod1.Length - 1)], m);
            }
            int placed = 0;
            if (v2)
            {
                // v2 sizes (Bank 1.77 x 0.61 x 0.38 m, Mound 0.96 x 0.50 x 0.28, Puffs = flat pillows): a continuous front bank
                // along each rail (1.3 m steps, banks ~1.9 m long overlap), a taller back row of mounds stacked against the
                // wall base and small pillows spilling onto the rail top - reference 8.00-10.00 s: 0.3-0.45 m tall cumulus
                // banks of 17-33 px bubbles at 720p on BOTH sides from S3 on; the hall keeps wider scattered clusters.
                // S2 pass 2 (owner 20:15 item 3 "LARGE, SOFT, THREE-DIMENSIONAL FOAM BANKS"; reference 3.0 s at the door: big
                // rounded clustered banks on the LEFT bank outside the hatch (screen x 0-450, y 270-450, white 59 % vs ours 37 %)
                // and a smaller cluster on the right rail (x 1040-1150, y 380-450, ref 35 % vs ours 0 %)): extra big v2 banks
                // at the door, measured through the S2 camera (front row tops ~1.1 m at lat -2.85, back-row mounds behind),
                // all outside the water (inner edges >= 1.95 m from the centre line), with their own rng (the rest of the
                // foam layout keeps its draws)
                var rm = new System.Random(3571);
                float RM(float a, float b) => Mathf.Lerp(a, b, (float)rm.NextDouble());
                void MouthBank(float dm, float lat, float h, float sc, int vi)
                {
                    var fm = track.Evaluate(dm);
                    var rot = fm.FlatRotation * Quaternion.Euler(0, 90f + RM(-8f, 8f) + (rm.NextDouble() < 0.5 ? 180f : 0f), 0);
                    var mm = Matrix4x4.TRS(fm.FlatPoint(lat, h), rot, new Vector3(sc, sc * RM(1.05f, 1.25f), sc));
                    comb0.Add(lod0[vi], mm);
                    comb1.Add(lod1[Mathf.Min(vi, lod1.Length - 1)], mm);
                }
                bool mouthDone = false;
                for (float d = 0f; d < L; d += (d < tunnelStart ? 1.6f : 1.3f))
                {
                    var f = track.Evaluate(d);
                    heroD = d;
                    if (!mouthDone && d >= HeroMouthDistance - 1f)
                    {
                        mouthDone = true;
                        float d0 = HeroMouthDistance;
                        for (float dm = d0 - 0.8f; dm < d0 + 5.0f; dm += 0.9f)
                        {
                            float near = Mathf.InverseLerp(d0 + 5.0f, d0 - 0.8f, dm);              // 1 = nearest the camera
                            MouthBank(dm, -RM(2.78f, 2.95f), RM(0.36f, 0.46f), Mathf.Lerp(1.35f, 1.8f, near) * RM(0.92f, 1.08f), 0);
                            MouthBank(dm + 0.45f, -RM(3.35f, 3.9f), RM(0.38f, 0.6f), Mathf.Lerp(1.7f, 2.4f, near) * RM(0.92f, 1.08f), 1);
                        }
                        MouthBank(d0 + 1.6f, RM(2.62f, 2.72f), RM(0.42f, 0.5f), 1.25f, 1);
                        MouthBank(d0 + 2.3f, RM(2.66f, 2.78f), RM(0.46f, 0.56f), 1.05f, 2);
                    }
                    bool hall = d < tunnelStart;
                    foreach (int side in new[] { -1, 1 })
                    {
                        if (hall)
                        {
                            Place(f, side * Rand(2.42f, 2.75f), Rand(0.40f, 0.56f), Rand(1.0f, 1.4f), 0);
                            Place(f, side * Rand(3.1f, 7.5f), Rand(-0.2f, 0.3f), Rand(1.4f, 2.2f), r.NextDouble() < 0.5 ? 0 : 1);
                        }
                        else
                        {
                            // v1 preview: at water level (h ~0) the banks hid behind the rail tubes (+-2.22 m, 0.72 m high) ->
                            // seated at the rail line so 0.3-0.5 m of foam shows above the rail like the reference
                            Place(f, side * Rand(2.40f, 2.62f), Rand(0.42f, 0.58f), Rand(0.95f, 1.3f), 0);
                            if (r.NextDouble() < 0.7) Place(f, side * Rand(2.72f, 3.1f), Rand(0.55f, 0.8f), Rand(1.05f, 1.55f), 1);
                        }
                        if (r.NextDouble() < 0.45) Place(f, side * Rand(2.36f, 2.46f), Rand(0.52f, 0.64f), Rand(0.85f, 1.15f), 2);
                        placed++;
                    }
                    if (d - chunkStart > ChunkLength) { FlushChunk(); chunkStart = d; }
                }
                FlushChunk();
                Debug.Log($"[BWK] waterfx foam v2: {placed} bank slots, {chunk} chunks (SM_Foam_v2_Bank / Mound / Puffs, M_Foam_v2)");
                return;
            }
            for (float d = 0f; d < L; d += (d < tunnelStart ? 1.9f : 1.75f))
            {
                var f = track.Evaluate(d);
                heroD = d;
                bool hall = d < tunnelStart;
                foreach (int side in new[] { -1, 1 })
                {
                    // reference: continuous puffy soap-suds banks right outside both rails (front row) + a taller back row,
                    // with small puffs spilling onto the rail top between them
                    if (hall)
                    {
                        Place(f, side * Rand(2.45f, 3.0f), Rand(-0.5f, 0.1f), Rand(0.85f, 1.5f), r.Next(lod0.Length));
                        Place(f, side * Rand(3.2f, 7.5f), Rand(-0.6f, 0.1f), Rand(0.9f, 1.6f), r.Next(lod0.Length));
                    }
                    else
                    {
                        Place(f, side * Rand(2.42f, 2.72f), Rand(-0.18f, 0.08f), Rand(0.75f, 1.05f), r.Next(lod0.Length));
                        if (r.NextDouble() < 0.8) Place(f, side * Rand(2.95f, 3.35f), Rand(-0.1f, 0.3f), Rand(0.95f, 1.35f), r.Next(lod0.Length));
                    }
                    if (r.NextDouble() < 0.6) Place(f, side * Rand(2.28f, 2.45f), Rand(0.02f, 0.14f), Rand(0.42f, 0.62f), small);
                }
                if (d - chunkStart > ChunkLength) { FlushChunk(); chunkStart = d; }
            }
            FlushChunk();
        }

        // ==================================================================== floating soap bubbles along the track
        static void BuildFloatingBubbles(GameObject env, float L) => BuildFloatingBubbles(env, L, false);

        static void BuildFloatingBubbles(GameObject env, float L, bool preview)
        {
            var bubble = ModelPrefab("Props", "SM_Bubble");
            if (bubble == null) return;
            if (!preview) ConsumeLegacyBubbleRng(L);
            var r = new System.Random(9157);
            float Rand(float a, float b) => Mathf.Lerp(a, b, (float)r.NextDouble());
            var holder = Child(env, "FloatingBubbles");
            // round 7 (asset library 19 "vary size and depth"; brief: dense iridescent bubbles along the walls): ~1.6x denser
            for (float d = 6f; d < L - 4f; d += Rand(2.0f, 4.0f))
            {
                var f = track.Evaluate(d);
                bool hall = d < tunnelStart;
                // keep the centre above the slide clear (mascot + camera): bubbles drift beside and above the water
                float side = r.NextDouble() < 0.5 ? -1f : 1f;
                float lat = hall ? (float)(r.NextDouble() * 2 - 1) * 7f : side * Rand(1.3f, 3.0f);
                float h = Mathf.Lerp(0.8f, hall ? 7f : 4.2f, (float)r.NextDouble());
                var go = Spawn(bubble);
                go.transform.SetParent(holder.transform, false);
                go.transform.position = f.FlatPoint(lat, h);
                go.transform.localScale = Vector3.one * Rand(0.22f, 0.75f);
                var bob = go.AddComponent<FloatBob>();
                bob.amplitude = 0.25f;
                bob.frequency = 0.2f;
                bob.swayDegrees = 0f;
                foreach (var rr in go.GetComponentsInChildren<Renderer>()) rr.shadowCastingMode = ShadowCastingMode.Off;
            }
        }

        // ==================================================================== runner FX
        static SplashFX BuildRunnerFX(GameObject runnerGo, RunnerController runner, TrackItemRegistry registry)
        {
            bool save = !InAgentPreview;
            var heroCam = MeasureHeroCam(runner);
            var crownL = new Vector3(-CrownRootX, 0f, CrownRootZ);
            var crownR = new Vector3(CrownRootX, 0f, CrownRootZ);
            var fxRoot = Child(runnerGo, "FX");
            var fx = fxRoot.AddComponent<SplashFX>();
            fx.runner = runner;
            fx.items = registry;
            Mesh dropMesh = null, bubbleMesh = null;
            var dp = ModelParts("FX", "SM_FX_Droplet");
            if (dp.Count > 0) dropMesh = PersistCopy(dp[0].mesh, save);
            var bp = ModelParts("FX", "SM_FX_BubbleLow");
            if (bp.Count > 0) bubbleMesh = PersistCopy(bp[0].mesh, save);

            // fine milky spray thrown up and back around the feet (velocity-stretched drop sprites)
            fx.spray = Particles(fxRoot, "Spray", "M_FX_Splash", new Vector3(0, 0.05f, 0.18f), new Vector3(-120, 0, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.25f, 0.45f); m.startSpeed = new ParticleSystem.MinMaxCurve(2.0f, 3.6f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.04f, 0.1f); m.gravityModifier = 1.5f; m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 160;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 60f; sh.radius = 0.5f;
                var e = ps.emission; e.rateOverTime = 0f;
                var r = ps.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.035f; r.lengthScale = 1.3f;
                Seed(ps, 11);
            });
            ParticleSystem Sub(ParticleSystem parent, string n, string mat, Vector3 pos, Vector3 euler, System.Action<ParticleSystem> setup)
            {
                var ps = Particles(fxRoot, n, mat, pos, euler, setup);
                ps.transform.SetParent(parent.transform, true);   // children of Spray are simulated with it in still captures
                return ps;
            }
            // 3D milk droplets flung from both crowns (real lit meshes, velocity-aligned, shrink before they vanish)
            ParticleSystem Drops(string n, float side, uint seed)
            {
                var dir = Quaternion.LookRotation(new Vector3(side * 0.62f, 0.78f, -0.38f)).eulerAngles;
                return Sub(fx.spray, n, "M_FX_Milk", new Vector3(side < 0 ? -(Mathf.Abs(crownL.x) + 0.2f) : Mathf.Abs(crownR.x) + 0.2f, 0.35f, crownL.z - 0.1f), dir, ps =>
                {
                    var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.3f, 0.6f); m.startSpeed = new ParticleSystem.MinMaxCurve(1.3f, 2.8f);
                    m.startSize = new ParticleSystem.MinMaxCurve(0.02f, 0.055f); m.gravityModifier = 1.3f; m.simulationSpace = ParticleSystemSimulationSpace.Local;
                    m.maxParticles = 140; m.startColor = Color.white;
                    var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 30f; sh.radius = 0.2f;
                    var sz = ps.sizeOverLifetime; sz.enabled = true;
                    sz.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0f, 0.7f), new Keyframe(0.15f, 1f), new Keyframe(0.75f, 1f), new Keyframe(1f, 0f)));
                    var e = ps.emission; e.rateOverTime = 30f;
                    MeshParticles(ps, dropMesh, true);
                    Seed(ps, seed);
                });
            }
            var dropsL = Drops("MilkDropsL", -1f, 21);
            var dropsR = Drops("MilkDropsR", 1f, 22);
            // subtle speed lines streaming past the camera at the edges of the view (sense of speed)
            var speedLines = Sub(fx.spray, "SpeedLines", "M_FX_SpeedLine", new Vector3(0, 1.1f, 7.5f), new Vector3(0, 180, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.25f, 0.32f); m.startSpeed = new ParticleSystem.MinMaxCurve(26f, 32f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.02f, 0.045f); m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 60;
                m.startColor = new Color(1f, 1f, 1f, 0.28f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 2.7f; sh.radiusThickness = 0.25f;
                var e = ps.emission; e.rateOverTime = 30f;
                var r = ps.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.06f; r.lengthScale = 3f;
                Seed(ps, 24);
            });
            fx.extra = new[] { dropsL, dropsR, speedLines };
            fx.extraRates = new[] { 30f, 30f, 30f };
            fx.sheets = new ParticleSystem[0];   // flat crown sprites replaced by the 3D crowns below

            // glassy bubbles at the reference screen positions (lower-left cluster, a big one lower-right, a few beside
            // the body); SplashFX makes them bob, drift back, pop and re-form in play, still captures keep this layout
            var bubbleParts = ModelParts("Props", "SM_Bubble");
            if (bubbleParts.Count > 0)
            {
                var hb = Child(fxRoot, "HeroBubbles");
                var hbMesh = PersistCopy(bubbleParts[0].mesh, save);
                var list = new List<Transform>();
                for (int i = 0; i < HeroBubbleSpots.Length; i++)
                {
                    var s = HeroBubbleSpots[i];
                    var p = heroCam.At(s.x, s.y, s.w, out float depth);
                    var b = Child(hb, $"Bubble_{i:00}");
                    b.transform.localPosition = p;
                    b.transform.localRotation = Quaternion.Euler(0f, i * 47f, 0f);
                    b.transform.localScale = Vector3.one * heroCam.WidthAt(s.z, depth);
                    b.AddComponent<MeshFilter>().sharedMesh = hbMesh;
                    var mr = b.AddComponent<MeshRenderer>();
                    mr.sharedMaterial = Mat("M_Bubble");
                    mr.shadowCastingMode = ShadowCastingMode.Off;
                    mr.receiveShadows = false;
                    list.Add(b.transform);
                }
                // S2 pass 2 (owner 20:15 item 4 "beautiful transparent iridescent bubbles"; reference 3.0 s at the door: two
                // BIG ones, upper right (1115,110) r45 px and at the left edge (20,250) r45, small ones around the mascot):
                // placed through the S2 comparison camera (CaptureTools R2: 2.75 back, 1.0 up, 0.3 right, pitch 6, yaw -9,
                // vFOV 58, 16:9) in runner space. The big pair floats outside the 9:16 hero frame (x +2.5 / -3.6 m, beside
                // the slide, never over the lanes); SplashFX bobs / drifts / pops them like the other hero bubbles.
                MeasureS2Cam(runner);
                for (int i = 0; i < S2BubbleSpots.Length; i++)
                {
                    var s = S2BubbleSpots[i];
                    var b = Child(hb, $"BubbleS2_{i:00}");
                    b.transform.localPosition = S2CamPoint(s.x, s.y, s.w);
                    b.transform.localRotation = Quaternion.Euler(0f, 23f + i * 61f, 0f);
                    b.transform.localScale = Vector3.one * S2CamSize(s.z, s.w);
                    b.AddComponent<MeshFilter>().sharedMesh = hbMesh;
                    var mr = b.AddComponent<MeshRenderer>();
                    mr.sharedMaterial = Mat("M_Bubble");
                    mr.shadowCastingMode = ShadowCastingMode.Off;
                    mr.receiveShadows = false;
                    list.Add(b.transform);
                }
                fx.heroBubbles = list.ToArray();
            }

            // lacy milk foam on the water around and behind the feet
            fx.foamTrail = Particles(fxRoot, "FoamTrail", "M_FX_FoamLace", new Vector3(0, 0.05f, -0.1f), new Vector3(-90, 0, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.3f, 0.5f); m.startSpeed = 0.2f;
                m.startSize = new ParticleSystem.MinMaxCurve(0.4f, 0.75f); m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 40;
                m.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                // round 4: fainter (reference 2.0-3.25 s: no white lace web on the water between the feet, only shadowed teal)
                m.startColor = new Color(1f, 1f, 1f, 0.4f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 0.4f;
                var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0, 0.7f, 1, 1.35f));
                var col = ps.colorOverLifetime; col.enabled = true;
                var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) }, new[] { new GradientAlphaKey(0.95f, 0), new GradientAlphaKey(0.8f, 0.5f), new GradientAlphaKey(0f, 1) });
                col.color = g;
                var r = ps.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.HorizontalBillboard;
                var e = ps.emission; e.rateOverTime = 0f;
                Seed(ps, 12);
            });
            // round 7 (owner: "replace the flat lace splashes throughout the level"): the flat lace sprites on the water stay
            // built (gameplay code references them) but no longer emit - the v2 milk crowns + 3D drops carry the splash
            fx.trailRateAtBase = 0f;
            // landing / boost burst: a ring of 3D milk drops
            fx.crown = Particles(fxRoot, "Crown", "M_FX_Milk", new Vector3(0, 0.1f, 0), new Vector3(-90, 0, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.35f, 0.7f); m.startSpeed = new ParticleSystem.MinMaxCurve(2.5f, 4.5f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.04f, 0.1f); m.gravityModifier = 1.8f; m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 120;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 45f; sh.radius = 0.5f;
                var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(0.7f, 1f), new Keyframe(1f, 0f)));
                var e = ps.emission; e.rateOverTime = 0f;
                MeshParticles(ps, dropMesh, true);
                Seed(ps, 13);
            });
            fx.speedStreaks = Particles(fxRoot, "SpeedStreaks", "M_FX_Streak", new Vector3(0, 1.0f, 6f), new Vector3(0, 180, 0), ps =>
            {
                var m = ps.main; m.startLifetime = 0.35f; m.startSpeed = 22f; m.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.12f);
                m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 120; m.loop = true; m.playOnAwake = false;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 2.4f; sh.radiusThickness = 0.3f;
                var e = ps.emission; e.rateOverTime = 120f;
                var r = ps.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.06f; r.lengthScale = 2f;
            });
            // S2 pass 7 (owner s18 + recording 26480 at 7-16 s: gold collect sparkles covered his hat / fur for long stretches):
            // smaller (0.15-0.4 -> 0.05-0.14 m), fewer (SplashFX coinBurst 14 -> 6, gem 22 -> 9), shorter (<= 0.3 s), slower
            // (travel <= 0.25 m) and restrained (alpha .7); SplashFX.PickupBurstPoint spawns them 0.8 m beside him, low.
            fx.pickupSparkles = Particles(fxRoot, "PickupSparkles", "M_FX_Sparkle", Vector3.zero, Vector3.zero, ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.14f, 0.28f); m.startSpeed = new ParticleSystem.MinMaxCurve(0.3f, 0.9f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.14f); m.simulationSpace = ParticleSystemSimulationSpace.World; m.maxParticles = 60;
                m.startColor = new Color(1f, 1f, 1f, 0.7f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.1f;
                var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.EaseInOut(0f, 1f, 1f, 0f));
                var e = ps.emission; e.rateOverTime = 0f;
            });
            fx.gemSparkles = Particles(fxRoot, "GemSparkles", "M_FX_GemSparkle", Vector3.zero, Vector3.zero, ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.16f, 0.32f); m.startSpeed = new ParticleSystem.MinMaxCurve(0.4f, 1.0f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.06f, 0.16f); m.simulationSpace = ParticleSystemSimulationSpace.World; m.maxParticles = 60;
                m.startColor = new Color(1f, 1f, 1f, 0.7f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.12f;
                var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.EaseInOut(0f, 1f, 1f, 0f));
                var e = ps.emission; e.rateOverTime = 0f;
            });
            // ambient soap bubbles drifting in front of the mascot (small sprites) ...
            var ambient = Particles(fxRoot, "AmbientBubbles", "M_FX_Bubble", new Vector3(0, 2.2f, 9f), Vector3.zero, ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(3f, 5f); m.startSpeed = new ParticleSystem.MinMaxCurve(0.1f, 0.5f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.08f, 0.3f); m.simulationSpace = ParticleSystemSimulationSpace.World; m.maxParticles = 120;
                m.gravityModifier = -0.04f; m.prewarm = true;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(8f, 4f, 10f);
                var e = ps.emission; e.rateOverTime = 18f;
                Seed(ps, 31);
            });
            // ... and big iridescent 3D bubbles beside the camera (children: simulated with AmbientBubbles in still captures)
            foreach (var (n, side, seed) in new[] { ("NearBubblesL", -1f, 32u), ("NearBubblesR", 1f, 33u) })
            {
                var near = Particles(fxRoot, n, "M_Bubble", new Vector3(side * 1.75f, 1.75f, 0.6f), Vector3.zero, ps =>
                {
                    var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(4f, 6f); m.startSpeed = new ParticleSystem.MinMaxCurve(0.05f, 0.2f);
                    m.startSize = new ParticleSystem.MinMaxCurve(0.18f, 0.55f); m.simulationSpace = ParticleSystemSimulationSpace.World; m.maxParticles = 12;
                    m.gravityModifier = -0.01f;
                    var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(1.3f, 1.6f, 6f);
                    var e = ps.emission; e.rateOverTime = 1.1f;
                    MeshParticles(ps, ModelParts("Props", "SM_Bubble").Select(p => p.mesh).FirstOrDefault() is Mesh bm ? PersistCopy(bm, save) : bubbleMesh, false);
                    Seed(ps, seed);
                });
                near.transform.SetParent(ambient.transform, true);
            }

            BuildCrowns(fxRoot, runner, save, crownL, crownR);
            if (InWaterFxPreview) RebuildEnvironmentFxPreview();
            return fx;
        }

        // round 7 (owner 13:30 "replace the flat lace splashes"; annotated sheet 02 item 4 "thick, rounded milk-white splash
        // crowns - not lace"; asset library 18): the MEASURED v2 crowns (build_fx_v2.py, traced from f_08.25s, silhouette IoU
        // .924) replace the perforated SM_FX_Crown_xx flipbook. They are authored for the front reference camera in runner-local
        // space; turned 180 deg for the rear gameplay camera (v2_L then sits at the LEFT foot, v2_R at the right), pushed
        // outward so both sole pads stay visible, a little taller (the hero reference crowns rise beside the feet).
        // (v1 preview: the right asset's band starts ~0.7 m further out than the left one -> per-side offsets; lift 1.2 -> 1.45)
        const float CrownV2OutL = 0.26f, CrownV2OutR = -0.42f, CrownV2Fwd = 0.12f, CrownV2Scale = 1.3f, CrownV2Lift = 1.45f;
        const int CrownV2Frames = 6;

        /// <summary>Stop-motion frames for one v2 crown: the measured mesh with a travelling liquid swell (displacement along
        /// the normals growing with height + a slow rise / fall of the fingers), seamless over CrownV2Frames.</summary>
        static List<Mesh> CrownV2FrameMeshes(Mesh src, string name, bool save)
        {
            var frames = new List<Mesh>();
            var v0 = src.vertices;
            var n0 = src.normals;
            float top = 0.001f;
            foreach (var v in v0) top = Mathf.Max(top, v.y);
            for (int k = 0; k < CrownV2Frames; k++)
            {
                float ph = 2f * Mathf.PI * k / CrownV2Frames;
                var vs = new Vector3[v0.Length];
                for (int i = 0; i < v0.Length; i++)
                {
                    var v = v0[i];
                    float h = Mathf.Clamp01(v.y / top);
                    float w = Mathf.Sin(ph + v.x * 9.0f + v.z * 7.0f);
                    float rise = Mathf.Sin(ph + v.x * 4.0f - v.z * 3.0f);
                    var nn = n0 != null && n0.Length == v0.Length ? n0[i] : Vector3.up;
                    vs[i] = v + nn * (0.009f * h * w) + Vector3.up * (v.y * 0.07f * rise);
                }
                var m = Object.Instantiate(src);
                m.name = $"{name}_f{k}";
                m.vertices = vs;
                m.RecalculateBounds();
                if (save) SaveMesh(m);
                frames.Add(m);
            }
            return frames;
        }

        // round 8 masters (owner: "thick rounded connected liquid crowns", annotated 02 item 4; library 18): crowns RE-TRACED from
        // the REAR hero frame f_03.00s (Tools/fx_splash_trace.py preset rear0300 -> data/fx_crown_rear_f0300.json) and solved
        // through the hero gameplay camera (build_fx_v2.py BWK_FX_REAR=1: 2.75 / 1.3 / pitch 10 / vFOV 58): milk rising on the
        // plane of the soles, low parts lying on the water nearer the camera, separate droplets. Authored in runner-local space
        // (no yaw, no per-side offsets); 0.95 because the reference feet stand ~0.5 m further from its camera than ours.
        // (p1 18:27: both crowns sat ~80-100 px outside the soles vs the reference, which touches them -> 0.3 m inward each)
        // (p2 18:31 9:16 hero: the reference crowns rise above the sole tops, ours reach mid-sole -> lift 1.3)
        const float CrownRearScale = 0.95f, CrownRearFwd = 0f, CrownRearIn = 0.3f, CrownRearLift = 1.3f;

        // Screen ALL pass 4 (owner 21:33, sheet 18, judge #1 "biggest gap in every section frame S2-S7"): ONE master pair for
        // the rear gameplay rig AND the front comparison cameras - build_fx_crown_v3.py SM_FX_CrownV3_L/R, authored in
        // runner-local metres (no offset / yaw / scale): a thick curved milk band lying on the water in a V that opens forward
        // from the feet (the front frames f_04.50-14.25 s: crowns at the bottom of the frame reaching the corners), breaking
        // into rounded fingers that lean outward and end in round bead bulbs + separate droplets, and a milk sheet climbing
        // beside each sole (the rear frames f_01.25-3.25 s). The rear-traced crowns were flat sheets on the plane of the
        // soles: from the front cameras only their thin backs showed (clear "wings" beside the body). Revert = delete
        // SM_FX_CrownV3_* (the rear-traced pair takes over again).
        // Screen S2 pass 7 (owner 2026-11-27 item 04 + s13 "the latest splashes still look like rigid clusters of white
        // fingers"; 26480 sheets: rigid white comb): build_fx_crown_v4.py SM_FX_CrownV4_L/R = branching gravity-bent liquid
        // strands fanning outward from a connected curved base at each foot, beads, tip beads and separate droplets (the
        // reference's bigger right spray + low wake arm toward the camera; low forward V bow for the front cameras), same
        // runner-local frame as V3. Revert = delete SM_FX_CrownV4_*.fbx (V3 takes over again).
        static bool BuildCrownsV2(GameObject fxRoot, RunnerController runner, bool save)
        {
            var pl = ModelParts("FX", "SM_FX_CrownV4_L");
            var pr = ModelParts("FX", "SM_FX_CrownV4_R");
            if (pl.Count > 0 && pr.Count > 0 && Mat("M_FX_Milk_v3") != null) return BuildCrownsV3(fxRoot, runner, save, pl[0].mesh, pr[0].mesh);
            pl = ModelParts("FX", "SM_FX_CrownV3_L");
            pr = ModelParts("FX", "SM_FX_CrownV3_R");
            bool v3 = pl.Count > 0 && pr.Count > 0 && Mat("M_FX_Milk_v3") != null;
            if (v3) return BuildCrownsV3(fxRoot, runner, save, pl[0].mesh, pr[0].mesh);
            pl = ModelParts("FX", "SM_FX_CrownRear_L");
            pr = ModelParts("FX", "SM_FX_CrownRear_R");
            bool rear = pl.Count > 0 && pr.Count > 0;
            if (!rear)
            {
                pl = ModelParts("FX", "SM_FX_Crown_v2_L");
                pr = ModelParts("FX", "SM_FX_Crown_v2_R");
            }
            var milk = Mat("M_FX_Milk_v2");
            if (pl.Count == 0 || pr.Count == 0 || milk == null) return false;
            var framesL = CrownV2FrameMeshes(pl[0].mesh, "SM_FX_CrownV2_L", save);
            var framesR = CrownV2FrameMeshes(pr[0].mesh, "SM_FX_CrownV2_R", save);
            var holder = Child(fxRoot, "Crowns");
            var sc = holder.AddComponent<SplashCrowns>();
            sc.runner = runner;
            sc.frames = framesL.ToArray();
            sc.framesRight = framesR.ToArray();
            sc.fps = 12f;
            var rot = rear ? Quaternion.identity : Quaternion.Euler(0f, 180f, 0f);
            var s = rear ? new Vector3(CrownRearScale, CrownRearScale * CrownRearLift, CrownRearScale) : new Vector3(CrownV2Scale, CrownV2Scale * CrownV2Lift, CrownV2Scale);
            var crowns = new List<MeshFilter>();
            foreach (float side in new[] { -1f, 1f })
            {
                var go = Child(holder, side < 0 ? "CrownL" : "CrownR");
                go.transform.localPosition = rear ? new Vector3(side < 0 ? CrownRearIn : -CrownRearIn, 0f, CrownRearFwd) : new Vector3(side < 0 ? -CrownV2OutL : CrownV2OutR, 0f, CrownV2Fwd);
                go.transform.localRotation = rot;
                go.transform.localScale = s;
                var mf = go.AddComponent<MeshFilter>();
                mf.sharedMesh = (side < 0 ? framesL : framesR)[side < 0 ? 0 : CrownV2Frames / 2];
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = milk;
                mr.shadowCastingMode = ShadowCastingMode.Off;
                mr.receiveShadows = true;
                crowns.Add(mf);
            }
            sc.crowns = crowns.ToArray();
            sc.baseScale = new[] { s, s };
            sc.baseRotation = new[] { rot, rot };
            sc.phase = new[] { 0, CrownV2Frames / 2 };
            Debug.Log(rear ? $"[BWK] waterfx crowns REAR-traced: SM_FX_CrownRear_L/R x{CrownV2Frames} frames, no yaw, scale {CrownRearScale} lift {CrownRearLift} in {CrownRearIn} fwd {CrownRearFwd}, M_FX_Milk_v2"
                           : $"[BWK] waterfx crowns v2: SM_FX_Crown_v2_L/R x{CrownV2Frames} frames, yaw 180, out L {CrownV2OutL} R {CrownV2OutR} fwd {CrownV2Fwd} scale {CrownV2Scale} lift {CrownV2Lift}, M_FX_Milk_v2");
            return true;
        }

        static bool BuildCrownsV3(GameObject fxRoot, RunnerController runner, bool save, Mesh left, Mesh right)
        {
            var milk = Mat("M_FX_Milk_v3");
            var framesL = CrownV2FrameMeshes(left, left.name.Contains("V4") ? "SM_FX_CrownV4_L" : "SM_FX_CrownV3_L", save);
            var framesR = CrownV2FrameMeshes(right, right.name.Contains("V4") ? "SM_FX_CrownV4_R" : "SM_FX_CrownV3_R", save);
            var holder = Child(fxRoot, "Crowns");
            var sc = holder.AddComponent<SplashCrowns>();
            sc.runner = runner;
            sc.frames = framesL.ToArray();
            sc.framesRight = framesR.ToArray();
            sc.fps = 12f;
            var crowns = new List<MeshFilter>();
            foreach (float side in new[] { -1f, 1f })
            {
                var go = Child(holder, side < 0 ? "CrownL" : "CrownR");
                go.transform.localPosition = Vector3.zero;
                go.transform.localRotation = Quaternion.identity;
                go.transform.localScale = Vector3.one;
                var mf = go.AddComponent<MeshFilter>();
                mf.sharedMesh = (side < 0 ? framesL : framesR)[side < 0 ? 0 : CrownV2Frames / 2];
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = milk;
                mr.shadowCastingMode = ShadowCastingMode.Off;
                mr.receiveShadows = true;
                crowns.Add(mf);
            }
            sc.crowns = crowns.ToArray();
            sc.baseScale = new[] { Vector3.one, Vector3.one };
            sc.baseRotation = new[] { Quaternion.identity, Quaternion.identity };
            sc.phase = new[] { 0, CrownV2Frames / 2 };
            Debug.Log($"[BWK] waterfx crowns MASTER: {left.name} / {right.name} x{CrownV2Frames} frames ({left.triangles.Length / 3} + {right.triangles.Length / 3} tris), runner-local, M_FX_Milk_v3");
            return true;
        }

        static void BuildCrowns(GameObject fxRoot, RunnerController runner, bool save, Vector3 rootL, Vector3 rootR)
        {
            if (BuildCrownsV2(fxRoot, runner, save)) return;
            var frames = new List<Mesh>();
            for (int k = 0; k < 32; k++)
            {
                var parts = ModelParts("FX", $"SM_FX_Crown_{k:00}");
                if (parts.Count == 0) break;
                frames.Add(PersistCopy(parts[0].mesh, save));
            }
            if (frames.Count == 0) { Debug.LogWarning("[BWK] SM_FX_Crown frames missing - no 3D splash crowns"); return; }
            // round 4: the right crown uses the skirt-less SM_FX_CrownR_xx family (reference: open water lower right)
            var framesR = new List<Mesh>();
            for (int k = 0; k < frames.Count; k++)
            {
                var parts = ModelParts("FX", $"SM_FX_CrownR_{k:00}");
                if (parts.Count == 0) break;
                framesR.Add(PersistCopy(parts[0].mesh, save));
            }
            if (framesR.Count != frames.Count) framesR.Clear();
            // (round 4 continuation v3 tried the skirt-less family on BOTH sides: the lower-left turned into open dark water
            // where the reference has milky lace (#B6DAE9) -> reverted; the left keeps its skirt)
            var holder = Child(fxRoot, "Crowns");
            var sc = holder.AddComponent<SplashCrowns>();
            sc.runner = runner;
            sc.frames = frames.ToArray();
            sc.framesRight = framesR.Count > 0 ? framesR.ToArray() : null;
            var milk = Mat("M_FX_Milk");
            int[] phase = { 0, frames.Count / 2 };
            var crowns = new List<MeshFilter>();
            var scales = new List<Vector3>();
            int idx = 0;
            foreach (float side in new[] { -1f, 1f })
            {
                var go = Child(holder, side < 0 ? "CrownL" : "CrownR");
                go.transform.localPosition = side < 0 ? new Vector3(-Mathf.Abs(rootL.x), 0f, rootL.z) : new Vector3(Mathf.Abs(rootR.x), 0f, rootR.z);
                go.transform.localRotation = Quaternion.Euler(0f, -side * CrownYaw, 0f);
                // asset extends to -X (left); mirror for the right side
                var s = new Vector3(-side * CrownScale, CrownScale, CrownScale);
                go.transform.localScale = s;
                var mf = go.AddComponent<MeshFilter>();
                var fam = side > 0 && framesR.Count > 0 ? framesR : frames;
                mf.sharedMesh = fam[phase[idx] % fam.Count];
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = milk;
                mr.shadowCastingMode = ShadowCastingMode.Off;
                mr.receiveShadows = true;
                crowns.Add(mf); scales.Add(s);
                idx++;
            }
            sc.crowns = crowns.ToArray();
            sc.baseScale = scales.ToArray();
            sc.baseRotation = new[] { Quaternion.Euler(0f, CrownYaw, 0f), Quaternion.Euler(0f, -CrownYaw, 0f) };
            Debug.Log($"[BWK] waterfx crowns: root L ({-Mathf.Abs(rootL.x):F2}, 0, {rootL.z:F2}) R ({Mathf.Abs(rootR.x):F2}, 0, {rootR.z:F2}) scale {CrownScale} yaw {CrownYaw}, {frames.Count} frames");
            sc.phase = phase;
        }

        static void Seed(ParticleSystem ps, uint seed)
        {
            ps.useAutoRandomSeed = false;
            ps.randomSeed = seed;
        }

        static void MeshParticles(ParticleSystem ps, Mesh mesh, bool velocityAligned)
        {
            if (mesh == null) return;
            var r = ps.GetComponent<ParticleSystemRenderer>();
            r.renderMode = ParticleSystemRenderMode.Mesh;
            r.mesh = mesh;
            r.alignment = velocityAligned ? ParticleSystemRenderSpace.Velocity : ParticleSystemRenderSpace.Local;
            r.SetActiveVertexStreams(new List<ParticleSystemVertexStream>
            {
                ParticleSystemVertexStream.Position, ParticleSystemVertexStream.Normal, ParticleSystemVertexStream.Tangent,
                ParticleSystemVertexStream.Color, ParticleSystemVertexStream.UV
            });
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

        // ==================================================================== decor chevrons
        static void BuildDecorChevrons(GameObject env, float L) => BuildDecorChevrons(env, L, false);

        /// <summary>
        /// Round 4 decor chevron: a thick, FILLED glowing arrow lying in the water (x right, y up, z = travel, apex toward
        /// travel). Same UV contract as SM_Chevron for BWK/Soft Mode 7: U across the arm (0 outer / front edge .. 1 inner
        /// edge), V along the V (0 left arm end, 0.5 apex, 1 right arm end). Crisp edges (walls / caps use their own verts).
        /// </summary>
        static Mesh BuildDecorChevronMesh()
        {
            const int Rows = 8;
            float[] cols = { 0f, 0.12f, 0.3f, 0.5f, 0.7f, 0.88f, 1f };
            float HL = ChevronHalfLen, HW = ChevronHalfWidth, T = ChevronThick, H = ChevronHeight;
            float len = Mathf.Sqrt(HW * HW + 4f * HL * HL);
            float a = HW / len, b = 2f * HL / len;           // arm direction from the apex: (+-a, -b)
            int nr = 2 * Rows + 1;
            Vector3 P(int r, float c, float y)
            {
                float o = T * 0.5f - c * T;                  // offset toward the outer (front) edge
                float my = HL + o / a;                       // where both arms' offset lines meet (mitre) on the axis
                float side = r < Rows ? -1f : 1f;
                float t = ChevronEndX / a * (Mathf.Abs(r - Rows) / (float)Rows);   // every edge ends at |x| = ChevronEndX
                return new Vector3(side * a * t, y, my - b * t);
            }
            var v = new List<Vector3>(); var uv = new List<Vector2>(); var nm = new List<Vector3>(); var tri = new List<int>();
            int Vert(Vector3 p, Vector2 t, Vector3 n) { v.Add(p); uv.Add(t); nm.Add(n); return v.Count - 1; }
            void Tri(int i0, int i1, int i2, Vector3 want)
            {
                // Unity front faces: Cross(v1 - v0, v2 - v0) points toward the viewer
                if (Vector3.Dot(Vector3.Cross(v[i1] - v[i0], v[i2] - v[i0]), want) >= 0f) { tri.Add(i0); tri.Add(i1); tri.Add(i2); }
                else { tri.Add(i0); tri.Add(i2); tri.Add(i1); }
            }
            void Quad(int i0, int i1, int i2, int i3, Vector3 want) { Tri(i0, i1, i2, want); Tri(i0, i2, i3, want); }
            var top = new int[nr, cols.Length];
            for (int r = 0; r < nr; r++)
                for (int k = 0; k < cols.Length; k++)
                    top[r, k] = Vert(P(r, cols[k], H), new Vector2(cols[k], r / (float)(nr - 1)), Vector3.up);
            for (int r = 0; r < nr - 1; r++)
                for (int k = 0; k < cols.Length - 1; k++)
                    Quad(top[r, k], top[r, k + 1], top[r + 1, k + 1], top[r + 1, k], Vector3.up);
            // outer + inner walls along the whole V
            foreach (int k in new[] { 0, cols.Length - 1 })
                for (int r = 0; r < nr - 1; r++)
                {
                    Vector3 pa = P(r, cols[k], 0f), pb = P(r + 1, cols[k], 0f);
                    Vector3 out3 = (pa + pb) * 0.5f - (P(r, 0.5f, 0f) + P(r + 1, 0.5f, 0f)) * 0.5f;
                    var wn = new Vector3(out3.x, 0f, out3.z).normalized;
                    float v0 = r / (float)(nr - 1), v1 = (r + 1) / (float)(nr - 1);
                    Quad(Vert(P(r, cols[k], H), new Vector2(cols[k], v0), wn), Vert(P(r + 1, cols[k], H), new Vector2(cols[k], v1), wn),
                         Vert(P(r + 1, cols[k], -0.01f), new Vector2(cols[k], v1), wn), Vert(P(r, cols[k], -0.01f), new Vector2(cols[k], v0), wn), wn);
                }
            // flat arm-end caps, cut along travel (facing outward +-x)
            foreach (int r in new[] { 0, nr - 1 })
                for (int k = 0; k < cols.Length - 1; k++)
                {
                    float vv = r / (float)(nr - 1);
                    var cn = r == 0 ? Vector3.left : Vector3.right;
                    Quad(Vert(P(r, cols[k], H), new Vector2(cols[k], vv), cn), Vert(P(r, cols[k + 1], H), new Vector2(cols[k + 1], vv), cn),
                         Vert(P(r, cols[k + 1], -0.01f), new Vector2(cols[k + 1], vv), cn), Vert(P(r, cols[k], -0.01f), new Vector2(cols[k], vv), cn), cn);
                }
            var mesh = new Mesh { name = "SM_ChevronDecor" };
            mesh.SetVertices(v); mesh.SetUVs(0, uv); mesh.SetNormals(nm); mesh.SetTriangles(tri, 0);
            mesh.RecalculateTangents(); mesh.RecalculateBounds();
            return mesh;
        }

        static void BuildDecorChevrons(GameObject env, float L, bool preview)
        {
            var arrow = Mat("M_Arrow");
            if (arrow == null) return;
            var chevron = new List<Part> { new Part(BuildDecorChevronMesh(), new[] { arrow }, Matrix4x4.identity) };
            var holder = Child(env, "DecorChevrons");
            // skip the decor line where a centre-lane boost pad already lies on the water
            var registry = Object.FindFirstObjectByType<TrackItemRegistry>();
            var boosts = registry != null
                ? registry.items.Where(it => it != null && it.kind == TrackItemKind.Boost && Mathf.Abs(it.lateral) < 0.6f).Select(it => it.distance).ToList()
                : new List<float>();
            var comb = new FxCombiner();
            int chunk = 0; float chunkStart = 0;
            for (float d = ChevronStart; d < L - 6f; d += ChevronSpacing)
            {
                if (boosts.Any(b => Mathf.Abs(b - d) < 1.4f)) continue;
                var f = track.Evaluate(d);
                // round 4: generated fat chevron, flat in the water, on the weaving runway, turned along it
                comb.Add(chevron, Matrix4x4.TRS(f.Point(ChevronLateralAt(d), 0.03f), f.Rotation * Quaternion.Euler(0f, ChevronYawAt(d), 0f), Vector3.one));
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Chevrons_{chunk++:00}", !preview); chunkStart = d; }
            }
            comb.Flush(holder, $"Chevrons_{chunk:00}", !preview);
        }

        /// <summary>
        /// Water/FX agent preview only (-bwkOut .../agents/waterfx): rebuild this domain's environment pieces in memory so
        /// placement changes can be judged without the lead's full build. Never saved; never runs in other agents' previews.
        /// </summary>
        static void RebuildEnvironmentFxPreview()
        {
            var root = GameObject.Find("Level01_RainbowRush");
            var envT = root != null ? root.transform.Find("Environment") : null;
            if (envT == null || track == null) return;
            foreach (var n in new[] { "Foam", "DecorChevrons", "FloatingBubbles" })
            {
                var t = envT.Find(n);
                if (t != null) Object.DestroyImmediate(t.gameObject);
            }
            float L = track.Length;
            BuildFoam(envT.gameObject, L, true);
            BuildFloatingBubbles(envT.gameObject, L, true);
            BuildDecorChevrons(envT.gameObject, L, true);
            Debug.Log("[BWK] waterfx preview: foam, floating bubbles and decor chevrons rebuilt in memory");
        }
    }
}
