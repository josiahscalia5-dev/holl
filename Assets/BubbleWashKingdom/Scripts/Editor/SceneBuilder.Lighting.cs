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
        static void BuildLighting(GameObject root, float L, string profilePath = null)
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
            RenderSettings.ambientSkyColor = new Color(0.55f, 0.38f, 0.95f);
            RenderSettings.ambientEquatorColor = new Color(0.9f, 0.4f, 0.78f);
            RenderSettings.ambientGroundColor = new Color(0.22f, 0.42f, 1.0f);
            RenderSettings.ambientIntensity = 0.85f;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = new Color(0.46f, 0.32f, 0.82f);
            RenderSettings.fogDensity = 0.008f;
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
            AssetDatabase.CreateAsset(profile, profilePath ?? $"{GenDir}/PostFX_Level01.asset");
            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.Override(0.95f); bloom.intensity.Override(1.6f); bloom.scatter.Override(0.74f);
            bloom.tint.Override(new Color(1f, 0.92f, 0.95f)); bloom.highQualityFiltering.Override(false);
            var tm = profile.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.Neutral);
            var ca = profile.Add<ColorAdjustments>(true);
            ca.saturation.Override(32f); ca.contrast.Override(22f); ca.postExposure.Override(-0.05f);
            var vg = profile.Add<Vignette>(true); vg.intensity.Override(0.27f); vg.smoothness.Override(0.5f); vg.color.Override(new Color(0.16f, 0.05f, 0.3f));
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
            for (float d = tunnelStart + 2f; d < portalD - 4f; d += 1.1f + (float)rng.NextDouble() * 1.3f, i++)
            {
                var f = track.Evaluate(d);
                float ang = Mathf.Lerp(-118f, 118f, (float)rng.NextDouble()) * Mathf.Deg2Rad; // 0 = ceiling
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                var center = f.FlatPoint(0, TunnelCenter);
                var pos = center + radial * (TunnelRadius - 0.5f);
                // Face the tunnel centre AND tilt ~35 deg back toward the oncoming rear camera, so the stars read as
                // bold shapes (flat on the wall they were seen edge-on). Tip points "up" on screen, small random roll.
                Vector3 facing = (-radial * 0.8f - f.forward * 0.55f).normalized;
                Vector3 upHint = Vector3.ProjectOnPlane(f.flatUp + radial * 0.3f, facing);
                if (upHint.sqrMagnitude < 1e-4f) upHint = Vector3.ProjectOnPlane(f.forward, facing);
                var rot = Quaternion.LookRotation(facing, upHint.normalized) * Quaternion.Euler(0, 0, (float)rng.NextDouble() * 36f - 18f);
                float scale = Mathf.Lerp(0.9f, 1.7f, (float)rng.NextDouble());
                var src = (filled.Count > 0 && i % 6 == 3) ? filled : outline;
                var mat = mats[i % 3];
                var recolored = src.Select(p => new Part(p.mesh, Enumerable.Repeat(mat, Mathf.Max(1, p.mesh.subMeshCount)).ToArray(), p.local)).ToList();
                comb.Add(recolored, Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Stars_{chunk++:00}", false); chunkStart = d; }
            }
            comb.Flush(holder, $"Stars_{chunk:00}", false);
        }

        /// <summary>Lights parented to the runner so the mascot always gets the reference's warm top glow and soft back rim.</summary>
        static void BuildCharacterLights(GameObject runnerGo)
        {
            // Character lights riding with the mascot (reference: warm bulb glow on the hat/fur top, pink bounce on the back).
            // Keep every character light under the "CharacterLights" child (agent previews rebuild it in memory).
            var group = Child(runnerGo, "CharacterLights");
            var warm = Child(group, "CharLight_WarmTop");
            warm.transform.localPosition = new Vector3(0.6f, 2.3f, 1.2f);
            var wl = warm.AddComponent<Light>();
            wl.type = LightType.Point; wl.color = new Color(1f, 0.72f, 0.38f); wl.intensity = 1.6f; wl.range = 4.5f; wl.shadows = LightShadows.None;
            var rim = Child(group, "CharLight_PinkBack");
            rim.transform.localPosition = new Vector3(-0.5f, 1.1f, -1.6f);
            var rl = rim.AddComponent<Light>();
            rl.type = LightType.Point; rl.color = new Color(1f, 0.78f, 0.86f); rl.intensity = 0.6f; rl.range = 3.2f; rl.shadows = LightShadows.None;
        }
    }
}
