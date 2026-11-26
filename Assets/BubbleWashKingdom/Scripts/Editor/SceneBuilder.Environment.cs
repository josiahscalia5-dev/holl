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
    // OWNER: Agent 3 - 3D environment & machinery (tunnel modules, rings, bulkheads, side chambers, pipes, hall machinery, portal).
    // Only this domain's agent edits this file; the lead developer runs the scene build that calls it.
    public static partial class SceneBuilder
    {
        // ---------------------------------------------------------------- agent preview hook (in memory, never saved)
        /// <summary>false while PreviewEnvironmentDomain rebuilds pieces: combined meshes stay in memory.</summary>
        static bool envSave = true;

        /// <summary>
        /// Called by PreviewRefreshDomains in every agent's preview (before lighting is rebuilt): rebuilds the gold rings /
        /// lavender rims, the side chamber windows and the chamber glass risers inside the open scene, in memory only, so
        /// environment changes can be judged without a full build. Exception-safe; keeps the shared rng untouched.
        /// </summary>
        static partial void PreviewEnvironmentDomain(GameObject root, float L)
        {
            if (!PreviewRebuildsEnvironment) { Debug.Log("[BWK] preview: environment = saved scene (r7 dressing needs a full build)"); return; }
            var savedRng = rng;
            try
            {
                var envT = root.transform.Find("Environment");
                if (envT == null) return;
                var env = envT.gameObject;
                envSave = false;
                rng = new System.Random(4242);
                void Rebuild(string name, System.Action build)
                {
                    var old = env.transform.Find(name);
                    if (old != null) Object.DestroyImmediate(old.gameObject);
                    build();
                }
                Rebuild("Rings", () => BuildRings(env, L));
                Rebuild("SideChambers", () => BuildPortholes(env));
                Rebuild("ChamberPipes", () => BuildPipes(env, L));
                Debug.Log("[BWK] preview: environment rings / chambers / pipes rebuilt in memory");
                // chamber-section shots (EnvPreviewShots) are paused: hero frame only (lead directive 22:55)
            }
            catch (System.Exception e) { Debug.LogWarning("[BWK] preview: environment rebuild failed: " + e.Message); }
            finally { envSave = true; rng = savedRng; }
        }

        /// <summary>
        /// Environment-only preview extras: rear gameplay shots in the side chamber section and one front comparison angle
        /// (like CaptureStills 07_chambers / C2), rendered with the saved scene's lighting (the hook runs before the
        /// lighting rebuild). Files: OUT/env_*.png. CaptureHero teleports the runner again afterwards.
        /// </summary>
        static void EnvPreviewShots(string outDir)
        {
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            var cam = Camera.main;
            if (runner == null || rig == null || cam == null) return;
            Directory.CreateDirectory(outDir);
            var brain = cam.GetComponent<CinemachineBrain>();
            bool brainOn = brain != null && brain.enabled;
            if (brain) brain.enabled = false;
            try
            {
                foreach (var (name, d) in new[] { ("env_chambers_a", 205f), ("env_chambers_b", 215f), ("env_tunnel", 120f) })
                {
                    runner.TeleportTo(d, 0f);
                    foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
                    {
                        rig.aspectOverride = w / (float)h;
                        rig.Snap();
                        var lens = rig.vcam.Lens;
                        cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                        cam.fieldOfView = lens.FieldOfView;
                        CaptureTools.Render(cam, w, h, $"{outDir}/{name}_{tag}.png");
                    }
                }
                runner.TeleportTo(220f, 0f);
                var f = runner.Frame;
                Vector3 camPos = runner.transform.position + f.forward * 2.6f + f.flatUp * 0.95f;
                cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(runner.transform.position + f.flatUp * 0.55f - camPos, f.flatUp));
                cam.fieldOfView = 46f;
                CaptureTools.Render(cam, 1280, 720, $"{outDir}/env_front_chambers_16x9.png");
            }
            finally
            {
                rig.aspectOverride = 0f;
                if (brain) brain.enabled = brainOn;
            }
        }

        /// <summary>Combines parts per material like Combiner; writes the meshes only when envSave (full builds).</summary>
        class EnvCombiner
        {
            readonly Dictionary<Material, List<CombineInstance>> groups = new Dictionary<Material, List<CombineInstance>>();
            readonly Dictionary<Material, int> vertexCounts = new Dictionary<Material, int>();

            public void Add(List<Part> parts, Matrix4x4 world)
            {
                foreach (var p in parts)
                    for (int s = 0; s < p.mesh.subMeshCount; s++)
                    {
                        var mat = p.mats != null && p.mats.Length > 0 ? p.mats[Mathf.Min(s, p.mats.Length - 1)] : Mat("M_Gold");
                        if (mat == null) continue;
                        if (!groups.TryGetValue(mat, out var l)) { l = new List<CombineInstance>(); groups[mat] = l; vertexCounts[mat] = 0; }
                        l.Add(new CombineInstance { mesh = p.mesh, subMeshIndex = s, transform = world * p.local });
                        vertexCounts[mat] += p.mesh.vertexCount;
                    }
            }

            public void Flush(GameObject parent, string name, bool castShadows)
            {
                foreach (var kv in groups)
                {
                    var mesh = new Mesh { name = $"{name}_{kv.Key.name}" };
                    mesh.indexFormat = vertexCounts[kv.Key] > 60000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
                    mesh.CombineMeshes(kv.Value.ToArray(), true, true);
                    mesh.RecalculateBounds();
                    if (envSave) SaveMesh(mesh);
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

        // ---------------------------------------------------------------- tunnel ring layout (reference f_003.00s, key 5.0 s)
        // A slim polished gold marquee ring (SM_Ring, 28 bulbs built in) every GoldRingSpacing m and RimsPerGap fat
        // lavender drum lips (SM_DrumRim) between them, so the tunnel reads as a long nest of drum sections receding to the
        // portal. m1 (hero camera 2.75 back / 1.3 up / pitch 10 / FOV 58 at 105.5 m): the reference shows violet drum
        // metal and lavender lips near the camera, the first gold ring at mid-distance (on-screen radius ~0.34 of the
        // portrait width) and the next one at ~0.20 W. Gold every 12.75 m with the phase below puts gold rings ~6 m
        // (out of frame), ~19.5 m and ~32 m ahead of the camera and three lips (0.69 / 0.51 / 0.41 W) in between - the
        // same radii as the reference. The lighting ring lights / star spacing should follow FirstRingDistance and
        // GoldRingSpacing (lead's RingSpacing 8.5 stays for code that has not moved yet).
        // Round 3: ONE big lavender rim per gap at RimPhase (see below) instead of three lips -> broad perforated bays.
        // BWK_DrumWall (_Pattern 1) lines its plain metal / slot rows up with these positions: BuildRings writes
        // _BandOffset = FirstRingDistance, _BandLength = GoldRingSpacing and _RimPhase = RimPhase into M_DrumWall.
        // Chamber gaps (side porthole windows) skip their rims so the big windows fit between two gold rings.
        // Round 3 (mirrored track, reference f_003.00s measured on the ceiling): gold ring ~7 m (off frame), ONE big lavender
        // rim at ~12.2 m (on-screen r ~0.55 W), a broad perforated bay, gold ring 19.75 m (0.33 W), bay, rim ~25 m, gold
        // 32.5 m (0.20 W). So one rim per gap at RimPhase of the gap (was 3 evenly spaced lips = dense ribbed-hose look).
        const int RimsPerGap = 1;
        const float RimLamps = 24f;                           // SM_DrumRim pink LED lamps (build_track RIM_LEDS, r4: was 32)
        internal const float RimPhase = 0.40f;
        internal const float GoldRingSpacing = 12.75f;
        const float ChamberStart = 160f, ChamberEnd = 314f;   // r7: window gaps 160.75-301 m (S4-S6), 1-2 windows / gap
        const float ChamberPlaneRadius = 3.62f;               // SM_Porthole fallback: window plane distance from the axis
        const float ChamberWindowPlaneRadius = 3.40f;         // SM_ChamberWindow (build_machinery CW_PLANE_R, 1.4x porthole)
        internal static float FirstRingDistance => tunnelStart + 9.5f;

        /// <summary>Gold-ring gaps [d, d + GoldRingSpacing) that hold a side chamber window (centre d + GoldRingSpacing / 2).</summary>
        static List<float> ChamberGaps()
        {
            var gaps = new List<float>();
            for (float d = FirstRingDistance; d < portalD - 5f; d += GoldRingSpacing)
                if (d >= ChamberStart && d + GoldRingSpacing <= ChamberEnd) gaps.Add(d);
            return gaps;
        }

        static void BuildRings(GameObject env, float L)
        {
            var ring = ModelParts("Track", "SM_Ring");
            var rim = ModelParts("Track", "SM_DrumRim");
            if (ring.Count == 0) { Debug.LogWarning("[BWK] SM_Ring missing - rings skipped"); return; }
            if (rim.Count == 0) Debug.LogWarning("[BWK] SM_DrumRim missing - lavender rims skipped");
            // current SM_Ring carries its marquee bulbs (M_Bulb submesh); older exports need the separate SM_Bulb
            bool ringHasBulbs = ring.Any(p => p.mats != null && p.mats.Any(m => m != null && m.name == "M_Bulb"));
            var bulb = ringHasBulbs ? new List<Part>() : ModelParts("Track", "SM_Bulb");
            // r3: one rim per gap at RimPhase; BWK_DrumWall splits each gold section at the same phase (_RimPhase)
            float rimOffset = RimsPerGap == 1 ? RimPhase * GoldRingSpacing : GoldRingSpacing / (RimsPerGap + 1);
            float band = RimsPerGap == 1 ? GoldRingSpacing : GoldRingSpacing / (RimsPerGap + 1);
            var wall = Mat("M_DrumWall");
            if (wall != null)
            {
                wall.SetFloat("_BandOffset", FirstRingDistance);
                wall.SetFloat("_BandLength", band);
                wall.SetFloat("_RimPhase", RimsPerGap == 1 ? RimPhase : 0f);
                EditorUtility.SetDirty(wall);
            }
            var chamberGaps = new HashSet<float>(ChamberGaps());
            var holder = Child(env, "Rings");
            var comb = new EnvCombiner();
            int chunk = 0, rings = 0, rims = 0;
            float chunkStart = tunnelStart;
            Matrix4x4 World(float d, float scale)
            {
                var f = track.Evaluate(d);
                return Matrix4x4.TRS(f.FlatPoint(0, TunnelCenter), f.FlatRotation, Vector3.one * scale);
            }
            // r3: subtle per-ring variation (owner: no identical-looking repetition) - each gold ring / rim is rolled
            // about the tunnel axis by a deterministic fraction of its bulb / stud pitch and scaled +-1 %
            float Hash(float d) => Mathf.Abs(Mathf.Sin(d * 12.9898f + 78.233f) * 43758.5453f) % 1f;
            Matrix4x4 Vary(float d, float pitchDeg) =>
                Matrix4x4.TRS(Vector3.zero, Quaternion.Euler(0f, 0f, (Hash(d) - 0.5f) * pitchDeg), Vector3.one * (1f + (Hash(d + 3.7f) - 0.5f) * 0.02f));
            void PlaceRing(float d, float scale)
            {
                var world = World(d, scale) * Vary(d, 360f / BulbsPerRing);
                comb.Add(ring, world);
                rings++;
                int bulbs = bulb.Count > 0 ? BulbsPerRing : 0;
                for (int b = 0; b < bulbs; b++)
                {
                    float a = b / (float)BulbsPerRing * Mathf.PI * 2f;
                    var radial = new Vector3(Mathf.Sin(a), Mathf.Cos(a), 0f);
                    var local = Matrix4x4.TRS(radial * BulbRadius, Quaternion.FromToRotation(Vector3.up, -radial), Vector3.one * 1.5f);
                    comb.Add(bulb, world * local);
                }
            }
            PlaceRing(tunnelStart - 0.3f, 1.18f); // entrance gate
            // lips in the first gap too (between the entrance gate and the first gold ring)
            if (rim.Count > 0)
                for (float dr = FirstRingDistance - (RimsPerGap == 1 ? GoldRingSpacing - rimOffset : rimOffset); dr > tunnelStart + 0.8f; dr -= RimsPerGap == 1 ? GoldRingSpacing : rimOffset)
                {
                    comb.Add(rim, World(dr, 1f) * Vary(dr, 360f / RimLamps));
                    rims++;
                }
            for (float d = FirstRingDistance; d < portalD - 5f; d += GoldRingSpacing)
            {
                PlaceRing(d, 1f);
                if (rim.Count > 0 && !chamberGaps.Contains(d))
                    for (int r = 1; r <= RimsPerGap; r++)
                    {
                        float dr = d + r * rimOffset;
                        if (dr > portalD - 4f) break;
                        comb.Add(rim, World(dr, 1f) * Vary(dr, 360f / RimLamps));
                        rims++;
                    }
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Rings_{chunk++:00}", true); chunkStart = d; }
            }
            comb.Flush(holder, $"Rings_{chunk:00}", true);
            Debug.Log($"[BWK] rings: {rings} gold (bulbs built in: {ringHasBulbs}), {rims} lavender rims, drum sections {band:F3} m (rim at +{rimOffset:F2} m) from {FirstRingDistance} m");
        }

        // ---------------------------------------------------------------- round 7 tunnel dressing (S3-S7, 110 m -> portal)
        // Measured on the reference front frames (Captures/agents/environment/r7/section_specs.md). The video's front camera
        // looks back along the slide, so its screen-LEFT wall is the travel-RIGHT wall: the sock chamber windows, pink glass
        // risers and the cyan water pipe sit on the travel-right wall (S6 adds windows on the travel-left wall), the
        // decorative coin lines on the travel-left wall. Window gaps (ChamberGaps) skip their drum rim.
        const float WindowScale = 1.0f;          // SM_ChamberWindow_v2 frame outer r 2.32 m (ref near window 3.9-4.6 m)
        const float WindowAngle = 100f;          // window centre from the ceiling: centre 1.7 m = measured ~camera height (8.25 s solve); v1 76 / v2 86 sat above the C-still frame top
        // r7: +14 (toward the travel direction, for the front comparison stills) left the REAR gameplay camera looking at the
        // window ~90 deg off its face = a tall gold slab (projection test 14:55; owner sheet 02 item 1). r8 (asset artist):
        // turned toward the ONCOMING rear camera, yaw only (same wall positions / heights). -26 is the most the frame can turn
        // before its forward edge reaches the slide: inner edge x = 3.35 - 2.17 sin 26 = 2.40 m at rail-top height (rail
        // outer 2.38 m) and 2.33 m at camera height (camera <= ~1.3 m off the axis). The rear camera at 10-15 m now sees the
        // face 45-51 deg off-axis (ellipse 0.63-0.71 wide) instead of ~90 deg.
        const float WindowYaw = -26f;
        // r8 v2 (asset artist, owner sheet 02 item 1 "lower the chamber window into view"): the window centre drops 0.6 m
        // (straight down, same lateral position, so the -26 deg frame keeps its 2.40 m inner edge clear of the 2.38 m rail);
        // rear still 07 showed the near window cut by the frame top (v -0.1 .. 0.55), R5 had it above the top-left corner
        const float WindowDrop = 0.6f;
        const float CyanPipeAngle = 35f, CyanPipeRadius = 2.8f, CyanPipeScale = 2.0f, CyanPipeStart = 238f;
        const float CyanPipeEnd = 312f;          // the hall agent's portal set (318-351 m) has its own curved cyan pipe (travel-left)
        static readonly bool PreviewRebuildsEnvironment = false;   // r7: agent previews keep the saved scene's environment

        /// <summary>Chamber windows (track distance, side +1 = travel-right). In-gap offsets put the near window of the front
        /// comparison stills C4 / C2 / C5 6-9 m from their camera (reference 6.75 / 8.25 / 11.0 s: big window at the left).</summary>
        static List<(float d, int side)> ChamberWindows()
        {
            var list = new List<(float d, int side)>();
            foreach (float g in ChamberGaps())
            {
                float off = 6.4f;
                if (Mathf.Abs(g - 173.5f) < 0.2f) off = 10.1f;        // C4 (190 m)
                else if (Mathf.Abs(g - 211.75f) < 0.2f) off = 4.3f;   // C2 (220 m)
                else if (Mathf.Abs(g - 275.5f) < 0.2f) off = 2.7f;    // C5 (280 m)
                list.Add((g + off, 1));
                if (g >= 236f && g < 300f) list.Add((g + 9.5f, -1)); // S6: windows on both walls
            }
            return list;
        }

        /// <summary>True when p lies inside the fixed hero camera's (16:9-wide) frustum closer than maxDepth: the hero frame
        /// (S2) keeps its designed layout, so round-7 dressing skips those spots.</summary>
        static System.Func<Vector3, bool> HeroViewTest(float maxDepth)
        {
            HeroCameraPose(out var camPos, out var camRot);
            float tanV = Mathf.Tan(HeroCamFov * 0.5f * Mathf.Deg2Rad) * 1.15f, tanH = tanV * (16f / 9f);
            var inv = Quaternion.Inverse(camRot);
            return p =>
            {
                var c = inv * (p - camPos);
                return c.z > 0.3f && c.z < maxDepth && Mathf.Abs(c.x) < c.z * tanH && Mathf.Abs(c.y) < c.z * tanV;
            };
        }

        /// <summary>
        /// Side washing chambers v2 (reference 6.75-13.5 s): SM_ChamberWindow_v2 (thick polished gold band, hinge block,
        /// rainbow arch, foam bank) upright at MID-WALL facing the tunnel axis, turned a little toward the travel direction,
        /// with 3-4 big striped socks floating in front of the swirling rainbow water (as the shot-matched 8.25 s window).
        /// </summary>
        static void BuildPortholes(GameObject env)
        {
            DrainLegacyPortholeRng();
            var holder = Child(env, "SideChambers");
            var prefab = ModelPrefab("Machinery", "SM_ChamberWindow_v2");
            if (prefab == null) { Debug.LogWarning("[BWK] SM_ChamberWindow_v2 missing - chamber windows skipped"); }
            else
            {
                string[] sockSet = { "SM_Sock_A", "SM_Sock_B", "SM_Sock_C" };
                var socks = new (Vector3 p, Vector3 e)[]
                {
                    (new Vector3(-0.25f, 0.70f, -0.10f), new Vector3(20f, 70f, -25f)),
                    (new Vector3(-0.75f, -0.25f, -0.10f), new Vector3(-10f, 80f, 35f)),
                    (new Vector3(0.35f, -0.55f, -0.10f), new Vector3(15f, 95f, 120f)),
                    (new Vector3(0.80f, 0.25f, -0.12f), new Vector3(-25f, 60f, 200f)),
                };
                var crng = new System.Random(7031);   // own sequence: the shared rng feeds the gameplay item layout
                int i = 0;
                foreach (var (d, side) in ChamberWindows())
                {
                    var f = track.Evaluate(d);
                    float ang = side * WindowAngle * Mathf.Deg2Rad;
                    var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                    var pos = f.FlatPoint(0, TunnelCenter) + radial * ChamberWindowPlaneRadius - Vector3.up * WindowDrop;
                    var inward = Vector3.ProjectOnPlane(-radial, Vector3.up).normalized;
                    var rot = Quaternion.AngleAxis(side * WindowYaw, Vector3.up) * Quaternion.LookRotation(inward, Vector3.up);
                    var go = Spawn(prefab);
                    go.name = $"ChamberV2_{d:000}_{(side > 0 ? "R" : "L")}";
                    go.transform.SetParent(holder.transform, false);
                    go.transform.SetPositionAndRotation(pos, rot);
                    // the travel-right window is mirrored (ShotMatchTool v3: hinge on the camera side)
                    go.transform.localScale = new Vector3(side > 0 ? -WindowScale : WindowScale, WindowScale, WindowScale);
                    foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
                    int n = 3 + (i % 2);
                    for (int s = 0; s < n; s++)
                    {
                        var sp = ModelPrefab("Props", sockSet[(s + i) % sockSet.Length]);
                        if (sp == null) continue;
                        var sock = Spawn(sp);
                        sock.transform.SetParent(go.transform, false);
                        sock.transform.localPosition = socks[s].p;
                        sock.transform.localRotation = Quaternion.Euler(socks[s].e + new Vector3(0f, 0f, (float)crng.NextDouble() * 50f - 25f));
                        sock.transform.localScale = Vector3.one * 2.6f;
                        var bob = sock.AddComponent<FloatBob>();
                        bob.orbitAxis = Vector3.forward;
                        bob.orbitRadius = 0.25f;
                        bob.orbitSpeed = 45f + 10f * s;
                        bob.amplitude = 0.05f;
                        foreach (var r in sock.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
                    }
                    i++;
                }
                Debug.Log($"[BWK] r7 chamber windows v2: {i} between {ChamberStart} and {ChamberEnd} m");
            }
            BuildTunnelStarsV2(env);
            BuildWallCoins(env);
        }

        /// <summary>
        /// Consumes exactly the shared-rng values the previous porthole layout used (checkpoint-6), so foam, bubbles and the
        /// gameplay items built after this step keep their layout (and the hero shot keeps its track distance).
        /// </summary>
        static void DrainLegacyPortholeRng()
        {
            string[] legacy = { "SM_Sock_A", "SM_Sock_B", "SM_Sock_C", "SM_Towel", "SM_Shirt" };
            for (float d = tunnelStart + 14f; d < portalD - 10f; d += 13f + (float)rng.NextDouble() * 6f)
                for (int s = 0; s < 4; s++)
                {
                    if (ModelPrefab("Props", legacy[(s + (int)d) % legacy.Length]) == null) continue;
                    rng.NextDouble(); rng.NextDouble();
                }
        }

        /// <summary>Positions of the lighting domain's sparse tunnel stars (SceneBuilder.Lighting BuildNeonStars, seed 5150),
        /// replayed so the round-7 stars never overlap them.</summary>
        static List<Vector3> LegacyTunnelStarPositions()
        {
            var list = new List<Vector3>();
            var r = new System.Random(5150);
            float Rand() => (float)r.NextDouble();
            for (float d = tunnelStart + 3f; d < portalD - 4f; d += 4.5f + Rand() * 4f)
            {
                float ringPhase = Mathf.Repeat(d - FirstRingDistance, GoldRingSpacing);
                if (ringPhase < 0.9f || ringPhase > GoldRingSpacing - 0.9f) continue;
                var f = track.Evaluate(d);
                float side = Rand() < 0.5f ? -1f : 1f;
                float angDeg = Rand() < 0.06f ? Mathf.Lerp(-10f, 10f, Rand()) : side * Mathf.Lerp(26f, 66f, Rand());
                float ang = angDeg * Mathf.Deg2Rad;
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                float scale = Rand() < 0.55f ? Mathf.Lerp(1.6f, 2.2f, Rand()) : Mathf.Lerp(1.1f, 1.5f, Rand());
                list.Add(f.FlatPoint(0, TunnelCenter) + radial * (TunnelRadius - 0.38f - 0.18f * scale));
                Rand(); Rand(); Rand();   // tilt, roll, colour
            }
            return list;
        }

        /// <summary>
        /// Dense big neon tube stars v2 (reference S3-S7: 8-15 per frame, pink / cyan / yellow-orange, near ones 120-180 px
        /// = 0.9-1.4 m tall). Each star stands in the tunnel cross-section plane just inside the drum (tips ~0.15 m from the
        /// wall), so both the rear gameplay camera and the front comparison camera see it face-on like the reference, with a
        /// soft double-sided glow card in the same plane. Colour mix per section as measured; never inside the hero frame.
        /// </summary>
        static void BuildTunnelStarsV2(GameObject env)
        {
            var star = ModelParts("Lighting", "SM_NeonStarTube_v2");
            if (star.Count == 0) { Debug.LogWarning("[BWK] SM_NeonStarTube_v2 missing - r7 stars skipped"); return; }
            var mats = new[] { Mat("M_Neon_Pink"), Mat("M_Neon_Cyan"), Mat("M_Neon_Yellow") };
            var glowMats = new[] { Mat("M_StarGlow_Pink"), Mat("M_StarGlow_Cyan"), Mat("M_StarGlow_Yellow") };
            if (mats.Any(m => m == null)) { Debug.LogWarning("[BWK] neon materials missing - r7 stars skipped"); return; }
            var quad = Resources.GetBuiltinResource<Mesh>("Quad.fbx");
            var tinted = mats.Select(m => star.Select(p => new Part(p.mesh, Enumerable.Repeat(m, Mathf.Max(1, p.mesh.subMeshCount)).ToArray(), p.local)).ToList()).ToArray();
            var legacy = LegacyTunnelStarPositions();
            var windows = ChamberWindows();
            var inHero = HeroViewTest(30f);   // far stars (>30 m) may show small deep in the hero tunnel
            var holder = Child(env, "TunnelStarsV2");
            var comb = new EnvCombiner();
            var glow = new EnvCombiner();
            var r = new System.Random(7707);
            float Rand() => (float)r.NextDouble();
            int count = 0, chunk = 0, last = -1, k = 0;
            float chunkStart = 110f;
            for (float d = 110f; d < portalD - 2.5f; d += 0.75f + Rand() * 0.4f)
            {
                k++;
                float ph = Mathf.Repeat(d - FirstRingDistance, GoldRingSpacing);
                if (ph < 1.0f || ph > GoldRingSpacing - 1.0f) continue;                       // gold ring planes
                float g = d - ph;
                bool windowGap = g >= ChamberStart - 0.01f && g + GoldRingSpacing <= ChamberEnd + 0.01f;
                if (!windowGap && Mathf.Abs(ph - RimPhase * GoldRingSpacing) < 0.9f) continue;  // drum rim plane
                // spread around the upper 3/4 of the drum (0 = ceiling, + = travel-right) with a golden-ratio sequence
                float u = Mathf.Repeat(k * 0.618034f + Rand() * 0.12f, 1f);
                float a2 = 2f * u - 1f;   // v2: warped toward the side walls (the cameras see the near side walls, the ceiling only far away)
                float angDeg = 105f * Mathf.Sign(a2) * Mathf.Pow(Mathf.Abs(a2), 0.7f);
                float s = Rand() < 0.3f ? Mathf.Lerp(0.8f, 0.95f, Rand()) : Mathf.Lerp(0.5f, 0.75f, Rand());
                float roll = Rand() * 50f - 25f;
                float cr = Rand();
                bool blocked = false;
                foreach (var w in windows)
                    if (Mathf.Abs(d - w.d) < 2.7f && Mathf.Abs(angDeg - w.side * WindowAngle) < 42f) { blocked = true; break; }
                if (d > 184f && d < 240f && angDeg > 40f)   // pink risers 3 m before the S4-S5 windows
                    foreach (var w in windows)
                        if (w.side > 0 && Mathf.Abs(d - (w.d - 3f)) < 1.0f) { blocked = true; break; }
                if (d > CyanPipeStart - 1f && d < CyanPipeEnd + 1f && Mathf.Abs(angDeg - CyanPipeAngle) < 22f) blocked = true;
                if (d > portalD - 10f && angDeg < -35f) blocked = true;   // hall agent: portal chamber window + cyan pipe curve (travel-left)
                if (d > 173f && d < 237f && ph > 1.3f && ph < 9.6f && angDeg < -72f) blocked = true;   // wall coin rows
                if (blocked) continue;
                var f = track.Evaluate(d);
                float ang = angDeg * Mathf.Deg2Rad;
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                var pos = f.FlatPoint(0, TunnelCenter) + radial * (TunnelRadius - 0.2f - 1.07f * s);
                if (legacy.Any(p => (p - pos).sqrMagnitude < 1.3f * 1.3f)) continue;
                if (inHero(pos)) continue;
                float pink, cyan;
                if (d < 170f) { pink = 0.33f; cyan = 0.36f; }
                else if (d < 205f) { pink = 0.42f; cyan = 0.25f; }
                else if (d < 240f) { pink = 0.58f; cyan = 0.17f; }
                else if (d < 310f) { pink = 0.36f; cyan = 0.40f; }
                else { pink = 0.36f; cyan = 0.36f; }
                int ci = cr < pink ? 0 : cr < pink + cyan ? 1 : 2;
                if (ci == last) ci = (ci + 1 + (k % 2)) % 3;
                last = ci;
                var rot = Quaternion.LookRotation(f.forward, f.flatUp) * Quaternion.Euler(0f, 0f, roll);
                comb.Add(tinted[ci], Matrix4x4.TRS(pos, rot, Vector3.one * s));
                if (quad != null && glowMats[ci] != null)
                    glow.Add(new List<Part> { new Part(quad, new[] { glowMats[ci] }, Matrix4x4.identity) }, Matrix4x4.TRS(pos, rot, new Vector3(3.2f * s, 3.2f * s, 1f)));
                count++;
                if (d - chunkStart > ChunkLength)
                {
                    comb.Flush(holder, $"StarsV2_{chunk:00}", false);
                    glow.Flush(holder, $"StarGlowV2_{chunk:00}", false);
                    chunk++; chunkStart = d;
                }
            }
            comb.Flush(holder, $"StarsV2_{chunk:00}", false);
            glow.Flush(holder, $"StarGlowV2_{chunk:00}", false);
            Debug.Log($"[BWK] r7 neon stars v2: {count} from 110 m to {portalD - 2.5f:F0} m (+{legacy.Count} lighting stars kept)");
        }

        /// <summary>Decorative gold paw coins in lines on the travel-left wall in S4-S5 (reference 6.75-8.25 s, screen-right),
        /// static scenery without colliders (the gameplay coins stay TrackItems on the slide).</summary>
        static void BuildWallCoins(GameObject env)
        {
            var coin = ModelParts("Props", "SM_Coin");
            if (coin.Count == 0) return;
            var holder = Child(env, "WallCoins");
            var comb = new EnvCombiner();
            int n = 0;
            foreach (float g in ChamberGaps())
            {
                if (g < 173f || g > 230f) continue;
                for (int i = 0; i < 5; i++)
                {
                    float d = g + 2.0f + i * 1.7f;
                    var f = track.Evaluate(d);
                    comb.Add(coin, Matrix4x4.TRS(f.FlatPoint(-3.05f, 1.35f + (i % 2) * 0.35f), f.FlatRotation, Vector3.one * 1.3f));   // v2: lower zigzag line
                    n++;
                }
            }
            comb.Flush(holder, "WallCoins", false);
            Debug.Log($"[BWK] r7 wall coins: {n}");
        }

        /// <summary>
        /// Pink glass risers v2 (reference 7.5-8.75 s: vertical pipe with glowing magenta liquid and a gold clamp collar) 3 m
        /// before each S4-S5 window, and the flowing cyan glass water pipe along the travel-right upper wall from S6 to the
        /// portal (reference 10-15 s), bent along the track inside the gold rings, with polished gold couplers.
        /// </summary>
        static void BuildPipes(GameObject env, float L)
        {
            var holder = Child(env, "ChamberPipes");
            var pink = ModelPrefab("Machinery", "SM_GlassPipe_Pink_v2");
            int np = 0;
            if (pink != null)
                foreach (var (d, side) in ChamberWindows())
                {
                    if (side < 0 || d < 185f || d > 240f) continue;
                    float dp = d - 3f;
                    var f = track.Evaluate(dp);
                    var inward = Vector3.ProjectOnPlane(-f.flatRight * side, Vector3.up).normalized;
                    var go = Spawn(pink);
                    go.name = $"PinkPipe_{dp:000}";
                    go.transform.SetParent(holder.transform, false);
                    go.transform.SetPositionAndRotation(f.FlatPoint(side * 3.45f, -0.7f), Quaternion.LookRotation(inward, Vector3.up));
                    go.transform.localScale = Vector3.one * 0.9f;
                    foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
                    np++;
                }
            var glass = ModelParts("Track", "SM_GlassPipe_Module");
            int nc = 0;
            float pipeEnd = Mathf.Min(CyanPipeEnd, portalD - 3f);
            if (glass.Count > 0 && pipeEnd > CyanPipeStart + 5f)
            {
                float a = CyanPipeAngle * Mathf.Deg2Rad;
                float lat = Mathf.Sin(a) * CyanPipeRadius, h = TunnelCenter + Mathf.Cos(a) * CyanPipeRadius;
                var cyan = Mat("M_PipeWaterCyan") ?? Mat("M_PipeWater");
                var mats = glass[0].mats.Select(m => m != null && m.name == "M_PipeWater" ? cyan : m).ToArray();
                BendChunks(holder, "CyanPipe", new Part(glass[0].mesh, mats, Matrix4x4.identity), CyanPipeStart, pipeEnd, false,
                           new Vector3(CyanPipeScale, CyanPipeScale, 1f), lat, h, 4f, false);
                var coupler = ModelParts("Track", "SM_Pipe_Coupler");
                if (coupler.Count > 0)
                {
                    var comb = new EnvCombiner();
                    for (float d = CyanPipeStart + 0.15f; d < pipeEnd + 0.1f; d = d + GoldRingSpacing * 0.5f > pipeEnd - 0.3f && d < pipeEnd - 0.2f ? pipeEnd - 0.12f : d + GoldRingSpacing * 0.5f)
                    {
                        var f = track.Evaluate(d);
                        comb.Add(coupler, Matrix4x4.TRS(f.FlatPoint(lat, h), f.FlatRotation, new Vector3(CyanPipeScale, CyanPipeScale, CyanPipeScale * 1.4f)));
                        nc++;
                    }
                    comb.Flush(holder, "CyanPipeCouplers", false);
                }
            }
            Debug.Log($"[BWK] r7 pipes: {np} pink risers v2, cyan wall pipe {CyanPipeStart}-{Mathf.Min(CyanPipeEnd, portalD - 3f):F0} m with {nc} gold couplers");
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
            Place("Machinery", "SM_BrushRoller", 20f, -3.6f, 3.3f, new Vector3(0, 32, 12), 1.15f, 45f, Vector3.right);
            Place("Machinery", "SM_BrushRoller", 44f, -6.2f, 6.0f, new Vector3(0, 25, 8), 1.15f, -40f, Vector3.right);
            Place("Machinery", "SM_BrushRoller", 30f, 6.8f, 7.5f, new Vector3(0, -30, -6), 1.0f, 38f, Vector3.right);
            // control console on the left, facing the slide
            Place("Machinery", "SM_ControlPanel", 24f, -5.0f, 1.4f, new Vector3(0, 120, 0), 1.2f);
            // lavender pillars with gold bands on the right
            Place("Machinery", "SM_Pillar", 19f, 3.7f, -1.0f, new Vector3(0, -90, 0), 1.0f);
            Place("Machinery", "SM_Pillar", 38f, 5.0f, -2.0f, new Vector3(0, -90, 0), 1.0f);
            Place("Machinery", "SM_Pillar", 56f, 5.4f, -2.5f, new Vector3(0, -90, 0), 1.0f);
            Place("Machinery", "SM_Pillar", 50f, -6.5f, -2.5f, new Vector3(0, 90, 0), 1.0f);
            // agitator column and golden plumbing in the background
            Place("Machinery", "SM_Agitator", 34f, -11f, -4f, Vector3.zero, 1.6f, 25f, Vector3.up);
            for (int i = 0; i < 5; i++)
            {
                Place("Machinery", "SM_GoldPipe_Straight", 12f + i * 2.05f, -4.4f, 2.5f, new Vector3(0, 180, 0), 1f);
                Place("Machinery", "SM_GoldPipe_Straight", 28f + i * 2.05f, 7.4f, 4.2f, new Vector3(0, 180, 0), 1f);
            }
            Place("Machinery", "SM_ValveWheel", 17f, -4.1f, 2.5f, new Vector3(0, 90, 0), 1f, 30f, Vector3.forward);
            Place("Machinery", "SM_Porthole", 40f, -9.5f, 3.5f, new Vector3(0, 70, 0), 1.6f);
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
    }
}
