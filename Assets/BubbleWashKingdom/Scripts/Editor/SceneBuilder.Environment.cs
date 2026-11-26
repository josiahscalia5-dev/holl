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
        // BWK_DrumWall (_Pattern 1) lines its plain metal / slot rows up with these positions: BuildRings writes
        // _BandOffset = FirstRingDistance and _BandLength = GoldRingSpacing / (RimsPerGap + 1) into M_DrumWall.
        // Chamber gaps (side porthole windows) skip their rims so the big windows fit between two gold rings.
        // Round 3 (mirrored track, reference f_003.00s measured on the ceiling): gold ring ~7 m (off frame), ONE big lavender
        // rim at ~12.2 m (on-screen r ~0.55 W), a broad perforated bay, gold ring 19.75 m (0.33 W), bay, rim ~25 m, gold
        // 32.5 m (0.20 W). So one rim per gap at RimPhase of the gap (was 3 evenly spaced lips = dense ribbed-hose look).
        const int RimsPerGap = 1;
        internal const float RimPhase = 0.40f;
        internal const float GoldRingSpacing = 12.75f;
        const float ChamberStart = 190f, ChamberEnd = 262f;   // stills 07_chambers (215 m) / C2 (220 m)
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
            void PlaceRing(float d, float scale)
            {
                var world = World(d, scale);
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
                    comb.Add(rim, World(dr, 1f));
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
                        comb.Add(rim, World(dr, 1f));
                        rims++;
                    }
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Rings_{chunk++:00}", true); chunkStart = d; }
            }
            comb.Flush(holder, $"Rings_{chunk:00}", true);
            Debug.Log($"[BWK] rings: {rings} gold (bulbs built in: {ringHasBulbs}), {rims} lavender rims, drum sections {band:F3} m (rim at +{rimOffset:F2} m) from {FirstRingDistance} m");
        }

        const float ChamberAngle = 84f;        // window centre, degrees from the ceiling: big windows low beside the slide
        const float ChamberPipeOffset = 2.75f;  // glass riser this far past the window centre (before the next gold ring)

        /// <summary>
        /// Side washing chambers (reference key 7.5 s / 10.5 s): big gold-framed porthole windows on the drum wall, one per
        /// chamber gap, alternating left / right, with laundry floating in front of the swirling rainbow water. The whole
        /// window (frame, shallow drum, swirl) sits in front of the tunnel wall; its lavender skirt is shaped in Blender to
        /// meet the r 4.2 drum exactly when the window plane is ChamberPlaneRadius from the axis (no hole in the tunnel).
        /// </summary>
        static void BuildPortholes(GameObject env)
        {
            DrainLegacyPortholeRng();
            var prefab = ModelPrefab("Machinery", "SM_ChamberWindow");
            float plane = ChamberWindowPlaneRadius, size = 1.4f;
            if (prefab == null) { prefab = ModelPrefab("Machinery", "SM_Porthole"); plane = ChamberPlaneRadius; size = 1f; }
            if (prefab == null) { Debug.LogWarning("[BWK] SM_Porthole missing - portholes skipped"); return; }
            string[] socks = { "SM_Sock_A", "SM_Sock_B", "SM_Sock_C", "SM_Towel", "SM_Sock_A", "SM_Shirt", "SM_Sock_B" };
            var crng = new System.Random(7031);   // own sequence: the shared rng feeds the gameplay item layout
            var holder = Child(env, "SideChambers");
            int i = 0;
            foreach (float g in ChamberGaps())
            {
                float d = g + GoldRingSpacing * 0.5f;
                int side = i % 2 == 0 ? -1 : 1;   // left wall first
                var f = track.Evaluate(d);
                float ang = side * ChamberAngle * Mathf.Deg2Rad;
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                var pos = f.FlatPoint(0, TunnelCenter) + radial * plane;
                var go = Spawn(prefab);
                go.name = $"Chamber_{d:000}";
                go.transform.SetParent(holder.transform, false);
                go.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(-radial, f.forward));
                // mirrored on the right wall so the swirl disc's "up" (-U, rainbow arch / foam bank) is world up on both
                // sides and the hinge stays toward the travel direction's back edge
                if (side > 0) go.transform.localScale = new Vector3(-1f, 1f, 1f);
                // floating laundry inside the shallow drum, between the glass and the swirling water
                for (int s = 0; s < 4; s++)
                {
                    var sp = ModelPrefab("Props", socks[(s + i * 3) % socks.Length]);
                    if (sp == null) continue;
                    var sock = Spawn(sp);
                    sock.transform.SetParent(go.transform, false);
                    float a = (s / 4f + i * 0.13f) * Mathf.PI * 2f;
                    sock.transform.localPosition = new Vector3(Mathf.Cos(a) * 0.52f * size, Mathf.Sin(a) * 0.52f * size, -0.17f * size);
                    sock.transform.localRotation = Quaternion.Euler((float)crng.NextDouble() * 360f, (float)crng.NextDouble() * 360f, 0);
                    sock.transform.localScale = Vector3.one * 1.35f * Mathf.Sqrt(size);
                    var bob = sock.AddComponent<FloatBob>();
                    bob.orbitAxis = Vector3.forward;
                    bob.orbitRadius = 0.22f * size;
                    bob.orbitSpeed = 50f + s * 9f;
                    bob.amplitude = 0.05f;
                    foreach (var r in sock.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
                }
                i++;
            }
            Debug.Log($"[BWK] side chambers: {i} windows between {ChamberStart} and {ChamberEnd} m");
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

        /// <summary>
        /// The reference hero frame has no pipes crossing the tunnel view. Glass risers with glowing pink liquid stand beside
        /// the side chamber windows instead (reference key 7.5 s), in the drum plane between two gold rings
        /// (SM_ChamberPipe is authored for the left wall; the right wall uses it turned 180 degrees about up).
        /// </summary>
        static void BuildPipes(GameObject env, float L)
        {
            var riser = ModelParts("Machinery", "SM_ChamberPipe");
            if (riser.Count == 0) { Debug.Log("[BWK] SM_ChamberPipe not built - no tunnel pipes"); return; }
            var holder = Child(env, "ChamberPipes");
            var comb = new EnvCombiner();
            int i = 0;
            foreach (float g in ChamberGaps())
            {
                int side = i % 2 == 0 ? -1 : 1;
                var f = track.Evaluate(g + GoldRingSpacing * 0.5f + ChamberPipeOffset);
                var rot = f.FlatRotation * (side < 0 ? Quaternion.identity : Quaternion.Euler(0f, 180f, 0f));
                comb.Add(riser, Matrix4x4.TRS(f.FlatPoint(0, TunnelCenter), rot, Vector3.one));
                i++;
            }
            comb.Flush(holder, "ChamberPipes", false);
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
            glow.rays = new Rendere