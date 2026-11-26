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
    // OWNER: Agent 4 - lighting & visual quality (key/ambient/fog, fill + character lights, reflection probes, post-processing, neon star placement).
    // Only this domain's agent edits this file; the lead developer runs the scene build that calls it.
    public static partial class SceneBuilder
    {
        // Look targets (reference f_003.00s): luminous candy palette, warm gold vs violet, soft lavender haze that grows with
        // depth into a bright vanishing point, strong but controlled bloom on bulbs / neon, glossy reflections, soft shadows.
        static void BuildLighting(GameObject root, float L, string profilePath = null)
        {
            var lights = Child(root, "Lighting");
            // Key light: near-vertical warm top light. Works for every track heading (the slide winds through all
            // directions), lights hat / pom-pom / coin tops, and drops the mascot's soft shadow right beneath him.
            // It leans slightly toward the rear camera (most of the slide heads +Z) so the mascot reads top-lit / softly
            // back-lit with a visible contact shadow, instead of the flat front light of the old 48 deg key.
            var sunGo = Child(lights, "Key Light");
            sunGo.transform.rotation = Quaternion.Euler(72f, 165f, 0f);
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.88f, 0.8f);
            sun.intensity = 1.25f;
            sun.shadows = LightShadows.Soft;
            sun.shadowStrength = 0.62f;
            RenderSettings.sun = sun;

            // Ambient: lavender from above, pink-violet around the horizon, cool lavender-blue bounce from the bright water
            // (the "ground" colour is what the tunnel ceiling receives).
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.58f, 0.4f, 0.98f);
            RenderSettings.ambientEquatorColor = new Color(0.9f, 0.44f, 0.82f);
            RenderSettings.ambientGroundColor = new Color(0.4f, 0.4f, 0.98f);
            RenderSettings.ambientIntensity = 0.85f;
            // Aerial perspective: luminous lavender haze, clear near the mascot, ~23 % at 30 m, ~65 % at 60 m (exp2).
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = new Color(0.76f, 0.6f, 1.0f);
            RenderSettings.fogDensity = 0.016f;
            RenderSettings.skybox = null;
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.reflectionIntensity = 1f;

            // colourful fill lights in the hall
            AddPoint(lights, 18f, -4f, 6f, new Color(1f, 0.45f, 0.85f), 3f, 18f);
            AddPoint(lights, 40f, 5f, 6f, new Color(0.35f, 0.85f, 1f), 3f, 18f);

            // Warm pools of bulb light at every gold ring (same spacing as BuildRings): glints on the gold, warm sheen on the
            // metallic drum wall and the water around each ring, violet in between -> depth rhythm down the tunnel.
            BuildRingLights(lights);

            // Reflection probes: hall probes + one per 30 m tunnel chunk, box = bounds of that bent tunnel segment.
            for (float d = 18f; d < tunnelStart; d += 30f)
            {
                var f = track.Evaluate(d);
                AddProbe(lights, $"ReflectionProbe_{d:000}", f.FlatPoint(0, 4f), new Bounds(f.FlatPoint(0, 4f), new Vector3(40, 30, 50)));
            }
            for (float d0 = tunnelStart; d0 < L - 1f; d0 += ChunkLength)
            {
                float d1 = Mathf.Min(L, d0 + ChunkLength);
                float dc = (d0 + d1) * 0.5f;
                var b = new Bounds(track.Evaluate(dc).FlatPoint(0, TunnelCenter), Vector3.zero);
                for (float s = d0; s <= d1 + 0.01f; s += 2.5f)
                {
                    var p = track.Evaluate(Mathf.Min(s, L)).FlatPoint(0, TunnelCenter);
                    b.Encapsulate(p + Vector3.one * (TunnelRadius + 0.6f));
                    b.Encapsulate(p - Vector3.one * (TunnelRadius + 0.6f));
                }
                AddProbe(lights, $"ReflectionProbe_{dc:000}", track.Evaluate(dc).FlatPoint(0, TunnelCenter + 0.4f), b);
            }

            // post-processing volume
            var volGo = Child(root, "PostFX Volume");
            var vol = volGo.AddComponent<Volume>();
            vol.isGlobal = true;
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, profilePath ?? $"{GenDir}/PostFX_Level01.asset");
            // Bloom: very hot HDR bulbs (~20) and neon tubes (~9) carry their saturated hue into wide halos while the
            // tonemapper clips their centres white-hot; the white foam (~1) only glows a little.
            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.Override(1.0f); bloom.intensity.Override(1.1f); bloom.scatter.Override(0.78f);
            bloom.tint.Override(new Color(1f, 0.92f, 0.95f)); bloom.highQualityFiltering.Override(true);
            bloom.maxIterations.Override(8);
            var tm = profile.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.Neutral);
            var ca = profile.Add<ColorAdjustments>(true);
            ca.saturation.Override(24f); ca.contrast.Override(18f); ca.postExposure.Override(0f);
            // warm highlights (gold, bulbs, skin of the light) vs violet shadows
            var st = profile.Add<SplitToning>(true);
            st.shadows.Override(new Color(0.44f, 0.38f, 0.66f)); st.highlights.Override(new Color(0.66f, 0.56f, 0.47f)); st.balance.Override(-10f);
            var vg = profile.Add<Vignette>(true); vg.intensity.Override(0.24f); vg.smoothness.Override(0.5f); vg.color.Override(new Color(0.16f, 0.05f, 0.3f));
            var wb = profile.Add<WhiteBalance>(true); wb.temperature.Override(3f); wb.tint.Override(5f);
            // soft far tunnel (premium film depth): mascot, coins and near rings stay crisp
            var dof = profile.Add<DepthOfField>(true);
            dof.mode.Override(DepthOfFieldMode.Gaussian); dof.gaussianStart.Override(24f); dof.gaussianEnd.Override(75f);
            dof.gaussianMaxRadius.Override(1.1f); dof.highQualitySampling.Override(true);
            foreach (var c in profile.components) AssetDatabase.AddObjectToAsset(c, profile);
            vol.sharedProfile = profile;
        }

        static void AddProbe(GameObject parent, string name, Vector3 position, Bounds box)
        {
            var pg = Child(parent, name);
            pg.transform.position = position;
            var probe = pg.AddComponent<ReflectionProbe>();
            probe.mode = ReflectionProbeMode.Custom;
            probe.resolution = 128;
            probe.size = box.size;
            probe.center = box.center - position;
            probe.blendDistance = 3f;
            probe.importance = 1;
            probe.hdr = true;
            probe.boxProjection = false;
            probe.nearClipPlane = 0.1f;
            probe.farClipPlane = 120f;
        }

        /// <summary>One warm point light per gold ring (positions follow BuildRings: tunnelStart + 3 m, every RingSpacing).</summary>
        static void BuildRingLights(GameObject lights)
        {
            var holder = Child(lights, "RingLights");
            int k = 0;
            for (float d = tunnelStart + 3f; d < portalD - 5f; d += RingSpacing, k++)
            {
                var f = track.Evaluate(d);
                var go = Child(holder, $"RingLight_{d:000}");
                go.transform.position = f.FlatPoint(0f, TunnelCenter + 1.1f) - f.forward * 0.35f;
                var l = go.AddComponent<Light>();
                l.type = LightType.Point;
                l.color = new Color(1f, 0.66f, 0.3f);
                l.intensity = 3.5f;
                l.range = 8f;
                l.shadows = LightShadows.None;
            }
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
            // Bake WITHOUT distance fog: the metallic drum wall, water and gold must reflect the real violet tunnel, gold
            // rings and warm bulbs, not a cubemap filled with pale fog colour (that washed the whole frame out).
            bool fog = RenderSettings.fog;
            RenderSettings.fog = false;
            try
            {
                // two passes: the second bake sees the first pass's reflections on the metal (richer inter-reflections)
                for (int pass = 0; pass < 2; pass++)
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
            finally { RenderSettings.fog = fog; }
        }

        /// <summary>
        /// Neon outline stars (reference: saturated yellow / cyan / pink tubes with white-hot cores and soft glow halos,
        /// scattered over the upper walls and ceiling at varied sizes and angles). Every star gets a soft additive glow
        /// card just behind it (its colour spilling over the drum wall, like the reference's tinted wall inside the star).
        /// Placement uses its own seeded RNG; the shared rng is advanced exactly as the previous version did, so the
        /// portholes / items / hero position built after this stay where they were.
        /// </summary>
        static void BuildNeonStars(GameObject env)
        {
            // keep the shared rng sequence identical to the old placement loop (3 draws per star + 1 per step)
            for (float d = tunnelStart + 2f; d < portalD - 4f; d += 1.1f + (float)rng.NextDouble() * 1.3f)
            { rng.NextDouble(); rng.NextDouble(); rng.NextDouble(); }

            var outline = ModelParts("Props", "SM_NeonStar");
            if (outline.Count == 0) { Debug.LogWarning("[BWK] SM_NeonStar missing - stars skipped"); return; }
            var mats = new[] { Mat("M_Neon_Yellow"), Mat("M_Neon_Cyan"), Mat("M_Neon_Pink") };
            var glowMats = new[] { Mat("M_StarGlow_Yellow"), Mat("M_StarGlow_Cyan"), Mat("M_StarGlow_Pink") };
            var quadMesh = Resources.GetBuiltinResource<Mesh>("Quad.fbx");
            var holder = Child(env, "NeonStars");
            var comb = new Combiner();
            var glowComb = new Combiner();
            var r = new System.Random(5150);
            float Rand() => (float)r.NextDouble();
            int chunk = 0; float chunkStart = tunnelStart;
            int lastColor = -1;
            int count = 0;
            for (float d = tunnelStart + 2.5f; d < portalD - 4f; d += 1.5f + Rand() * 1.9f)
            {
                // keep clear of the gold rings (BuildRings: tunnelStart + 3 + k * RingSpacing)
                float ringPhase = Mathf.Repeat(d - (tunnelStart + 3f), RingSpacing);
                if (ringPhase < 0.8f || ringPhase > RingSpacing - 0.8f) continue;
                var f = track.Evaluate(d);
                // upper side walls (12-62 deg from the ceiling, both sides) with an occasional ceiling star
                float side = Rand() < 0.5f ? -1f : 1f;
                float angDeg = Rand() < 0.14f ? Mathf.Lerp(-10f, 10f, Rand()) : side * Mathf.Lerp(14f, 62f, Rand());
                float ang = angDeg * Mathf.Deg2Rad; // 0 = ceiling
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                var center = f.FlatPoint(0, TunnelCenter);
                // size mix: a few big bold stars, many mid / small ones (reference)
                float pick = Rand();
                float scale = pick < 0.3f ? Mathf.Lerp(1.35f, 1.85f, Rand()) : Mathf.Lerp(0.7f, 1.2f, Rand());
                var pos = center + radial * (TunnelRadius - 0.38f - 0.1f * scale);
                // Face the tunnel centre and tilt back toward the oncoming rear camera so they read as bold shapes;
                // tip up on screen with a varied roll (reference stars sit at many angles).
                float tilt = Mathf.Lerp(0.42f, 0.62f, Rand());
                Vector3 facing = (-radial * 0.8f - f.forward * tilt).normalized;
                Vector3 upHint = Vector3.ProjectOnPlane(f.flatUp + radial * 0.3f, facing);
                if (upHint.sqrMagnitude < 1e-4f) upHint = Vector3.ProjectOnPlane(f.forward, facing);
                var rot = Quaternion.LookRotation(facing, upHint.normalized) * Quaternion.Euler(0, 0, Rand() * 56f - 28f);
                // colour: yellow / cyan / pink, never the same twice in a row
                int ci = Rand() < 0.38f ? 0 : (Rand() < 0.55f ? 1 : 2);
                if (ci == lastColor) ci = (ci + 1 + (Rand() < 0.5f ? 0 : 1)) % 3;
                lastColor = ci;
                var mat = mats[ci];
                var recolored = outline.Select(p => new Part(p.mesh, Enumerable.Repeat(mat, Mathf.Max(1, p.mesh.subMeshCount)).ToArray(), p.local)).ToList();
                comb.Add(recolored, Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                if (quadMesh != null && glowMats[ci] != null)
                {
                    // glow card ~2.3x the star size, just behind the tubes; tilted only half as much toward the camera as
                    // the star so its soft far edge stays in front of the curved drum wall (no visible intersection)
                    Vector3 gFacing = (-radial * 0.8f - f.forward * tilt * 0.45f).normalized;
                    Vector3 gUp = Vector3.ProjectOnPlane(rot * Vector3.up, gFacing);
                    if (gUp.sqrMagnitude < 1e-4f) gUp = Vector3.ProjectOnPlane(f.forward, gFacing);
                    var gRot = Quaternion.LookRotation(gFacing, gUp.normalized);
                    var glowPos = pos - gFacing * 0.12f;
                    glowComb.Add(new List<Part> { new Part(quadMesh, new[] { glowMats[ci] }, Matrix4x4.identity) },
                                 Matrix4x4.TRS(glowPos, gRot, new Vector3(2.3f, 2.3f, 1f) * scale));
                }
                count++;
                if (d - chunkStart > ChunkLength)
                {
                    comb.Flush(holder, $"Stars_{chunk:00}", false);
                    glowComb.Flush(holder, $"StarGlow_{chunk:00}", false);
                    chunk++; chunkStart = d;
                }
            }
            comb.Flush(holder, $"Stars_{chunk:00}", false);
            glowComb.Flush(holder, $"StarGlow_{chunk:00}", false);
            Debug.Log($"[BWK] neon stars: {count} with glow cards");
        }

        /// <summary>Lights parented to the runner so the mascot always gets the reference's warm top glow and soft back rim.</summary>
        static void BuildCharacterLights(GameObject runnerGo)
        {
            // Character lights riding with the mascot (reference: warm bulb glow on the hat/fur top, pink bounce on the back).
            // Keep every character light under the "CharacterLights" child (agent previews rebuild it in memory).
            var group = Child(runnerGo, "CharacterLights");
            // warm bulb glow on the top of the hat / pom-pom (slightly ahead, so it grazes over the top toward the camera)
            CharLight(group, "CharLight_WarmTop", new Vector3(0.35f, 2.3f, 0.6f), new Color(1f, 0.74f, 0.44f), 2.6f, 4f);
            // soft pink fill on the fluffy back the rear camera sees
            CharLight(group, "CharLight_PinkBack", new Vector3(-0.6f, 1.2f, -1.7f), new Color(1f, 0.7f, 0.86f), 1.0f, 3.4f);
            // cool lavender light from the bright tunnel ahead: wraps around the fur silhouette as a rim
            CharLight(group, "CharLight_RimFront", new Vector3(0f, 1.05f, 2.3f), new Color(0.72f, 0.84f, 1f), 2.4f, 3.6f);

            // soft violet contact shadow card on the water right under him (stays on the surface during jumps)
            var card = GameObject.CreatePrimitive(PrimitiveType.Quad);
            card.name = "ContactShadow";
            Object.DestroyImmediate(card.GetComponent<Collider>());
            card.transform.SetParent(group.transform, false);
            card.transform.localPosition = new Vector3(0f, 0.035f, 0.02f);
            card.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            card.transform.localScale = new Vector3(1.3f, 1.5f, 1f);
            var mr = card.GetComponent<MeshRenderer>();
            mr.sharedMaterial = Mat("M_ContactShadow");
            mr.shadowCastingMode = ShadowCastingMode.Off;
            mr.receiveShadows = false;
            var cs = card.AddComponent<LightingContactShadow>();
            cs.runner = runnerGo.GetComponent<RunnerController>();
            cs.baseScale = card.transform.localScale;
            cs.surfaceOffset = 0.035f;
        }

        static void CharLight(GameObject group, string name, Vector3 local, Color c, float intensity, float range)
        {
            var go = Child(group, name);
            go.transform.localPosition = local;
            var l = go.AddComponent<Light>();
            l.type = LightType.Point; l.color = c; l.intensity = intensity; l.range = range; l.shadows = LightShadows.None;
        }
    }
}
