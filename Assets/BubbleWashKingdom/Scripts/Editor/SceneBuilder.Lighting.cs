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
        // Look targets (reference f_003.00s): deep saturated violet tunnel with dark holes, a bright warm vanishing point,
        // neon stars that stay clearly yellow / cyan / pink with tinted halos, warm amber marquee bulbs, polished gold with
        // bright specular streaks, cool cyan from the water. Exposure is kept LOW (dark rich mids) so only the emissives and
        // speculars reach the bloom threshold: no global milky veil.
        static void BuildLighting(GameObject root, float L, string profilePath = null)
        {
            EnsurePerObjectLightLimit();
            var lights = Child(root, "Lighting");
            // Key light: near-vertical warm top light. Works for every track heading (the slide winds through all
            // directions), lights hat / pom-pom / coin tops, and drops the mascot's soft shadow right beneath him.
            // It leans slightly toward the rear camera (most of the slide heads +Z) so the mascot reads top-lit / softly
            // back-lit with a visible contact shadow.
            var sunGo = Child(lights, "Key Light");
            sunGo.transform.rotation = Quaternion.Euler(70f, 165f, 0f);
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.86f, 0.72f);
            sun.intensity = 1.05f;
            sun.shadows = LightShadows.Soft;
            sun.shadowStrength = 0.7f;
            RenderSettings.sun = sun;

            // Water bounce: a weak cool directional light shining UP from the bright slide water. It lifts the ceiling and the
            // upper walls (which face away from the key) to the reference's blue-violet, with a cyan cast like light from the water.
            var bounceGo = Child(lights, "Water Bounce");
            bounceGo.transform.rotation = Quaternion.Euler(-78f, 0f, 0f);
            var bounce = bounceGo.AddComponent<Light>();
            bounce.type = LightType.Directional;
            bounce.color = new Color(0.42f, 0.58f, 1f);
            // round 4: ceiling bays read light periwinkle (tunnel_ahead L50 .57 vs reference .49, reference bays deep blue
            // #554fac): a little less up-light
            // round 5: tunnel_ahead still L50 .57 vs .49 (light periwinkle ceiling bays) -> .30
            bounce.intensity = 0.30f;
            bounce.shadows = LightShadows.None;

            // Ambient (HDR round m1): saturated BLUE-violet from above (reference ceiling bays #40509e..#515aad), violet around
            // the horizon (walls #7250ad..#865aaf), cyan-blue bounce from the water. Saturated, never grey-lavender.
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.40f, 0.38f, 1.0f);
            RenderSettings.ambientEquatorColor = new Color(0.56f, 0.34f, 0.96f);
            RenderSettings.ambientGroundColor = new Color(0.32f, 0.44f, 0.98f);   // round 4: deeper blue on down-facing bays
            // round 4: 1.05 -> 0.94: the walls / ceiling bays read lighter and flatter than the reference (upper-right L50 .44
            // vs .40, tunnel ahead .57 vs .49) and the fur too light (L .61 vs .48); the pink spot / point lights carry the
            // upper-left glow instead
            // round 5: .94 -> .86: tunnel ahead L50 .57 vs .49, upper-right .46 vs .40, fur V .83 vs .77, hat L .35 vs .30
            // (all lighter / flatter than the reference); the pink spot + haze card keep the upper-left glow
            RenderSettings.ambientIntensity = 0.86f;
            // Aerial perspective: saturated lavender-violet (never pale grey): the near tunnel stays clear and rich, the far
            // tunnel melts into a lighter violet glow while the warm bulbs still punch through (emissives use little fog).
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            // round 3: bluer violet (owner sheet 04 "blue-violet shading, avoid flat lavender"): the mid tunnel measured
            // p50 #9578d0 vs reference #5c52ac -> the haze between the rings is now a deeper blue-violet
            RenderSettings.fogColor = new Color(0.50f, 0.42f, 1.0f);
            RenderSettings.fogDensity = 0.0102f;
            RenderSettings.skybox = null;
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.reflectionIntensity = 0.9f;

            // colourful fill lights in the hall
            AddPoint(lights, 18f, -4f, 6f, new Color(1f, 0.45f, 0.85f), 3f, 18f);
            AddPoint(lights, 40f, 5f, 6f, new Color(0.35f, 0.85f, 1f), 3f, 18f);

            // Warm pools of bulb light at every gold ring (same spacing as BuildRings): glints on the gold, warm sheen on the
            // metallic drum wall and the water around each ring, violet in between -> depth rhythm down the tunnel.
            BuildRingLights(lights);
            // soft lavender-white fill on the upper-right drum wall just ahead of the hero camera (reference upper-right wall
            // is a lit mid-violet #8069ad, ours read deep indigo): lifts value and lowers saturation there only
            // round 3 (mirrored track): the upper-right fill (HeroDistance + 8.5, lat 2.4, h 4.6) is no longer needed
            // (removed in round 3 v5: with 8 lights per object the upper-right read too light, L50 .48 vs .40)
            // round 3: pink reflections on the near-left drum rims (reference / owner sheet 04: hot pink-magenta glints on the
            // big near ring at the upper left, from the pink rails and neon) - a pink light inside the upper-left wall ~6 m ahead
            // (the wall around the big yellow star), which also tints that wall lighter mauve like the reference (#a87ea0)
            // round 4: this light was dropped by the 4-lights-per-object limit that the full build re-applied (upper-left wall
            // L50 .40 vs reference .51): limit back to 8 (EnsurePerObjectLightLimit) and a little stronger / pinker
            AddPoint(lights, HeroDistance + 6f, -2.5f, 4.1f, new Color(1f, 0.36f, 0.72f), 6f, 8f);
            // round 4 v2: the point light above lands on the left wall at mid height; the reference's light mauve-pink wall is
            // the UPPER-left (around the big yellow star, #a87ea0 vs ours violet #9d6bab). A wide spot aimed through the hero
            // camera at screen (0.15, 0.20) lands exactly there (independent of track mirroring / bends).
            // (v2 aimed at (0.15, 0.20): that ray reaches the wall only at 118 m; v3 aims nearer the corner -> ~112 m)
            // round 5: upper-left still violet (hue 293, L50 .45) vs the reference's light pink-mauve (311, .51), and the new
            // hue-vs-hue grade pulls violets bluer -> pinker (less blue) and stronger
            // v2: v1 (1, .42, .62) x22 gave L50 .51 (ok) but hue 282 (the bluer vignette / grade) -> pinker, a bit stronger
            AddHeroSpot(lights, "Spot_PinkUpperLeft", 0.09f, 0.14f, 3.4f, new Color(1f, 0.36f, 0.56f), 27f, 90f, 12f);

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
            // Bloom (HDR captures, round m1): LOCAL glow from the emissives only - threshold above lit foam / gold body so lit
            // surfaces never bloom, moderate scatter so dozens of ring bulbs give soft amber halos instead of one milky veil
            // over the tunnel. Untinted: every halo carries its source's own colour (amber bulbs, yellow / cyan / pink stars).
            var bloom = profile.Add<Bloom>(true);
            // round 3: bulbs now ~1/3 as hot -> slightly lower threshold / wider scatter keeps a soft luminous halo on the
            // emissives and the brightest rim glints (controlled: lit foam / walls stay below it)
            // round 4 (lead gap 1 "controlled bloom halos", sheet 04): slightly lower threshold + wider scatter -> soft halos on
            // the bulbs / stars / brightest rims (the reference's soft animated-film glow), still no veil on lit surfaces
            // v2 (threshold .9 / intensity 1.4) lifted every wall into a flat pastel lavender (frame L50 .60 vs .56): v3 keeps
            // the threshold at 1.0 (only emissives + hot glints bloom) and widens the halo instead
            // round 5: bulbs x6 -> x5 (peach cores, no lemon) -> a little more bloom intensity keeps their soft amber halos
            bloom.threshold.Override(1.0f); bloom.intensity.Override(1.38f); bloom.scatter.Override(0.78f);
            bloom.tint.Override(Color.white); bloom.highQualityFiltering.Override(true);
            bloom.maxIterations.Override(8);
            // Neutral keeps saturated hues far better than ACES (which pushes bright yellow / cyan to white).
            var tm = profile.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.Neutral);
            var ca = profile.Add<ColorAdjustments>(true);
            // richer, darker mids than the washed-out HDR baseline (frame L50 .63 -> reference .55)
            // round 4 v3: more contrast (reference: deep blue-violet bays against bright rims / glows; ours read flat)
            ca.saturation.Override(4f); ca.contrast.Override(12f); ca.postExposure.Override(-0.25f);
            // blue-violet shadows / low mids (depth, dark holes); warm highlights keep gold and bulbs warm
            var smh = profile.Add<ShadowsMidtonesHighlights>(true);
            smh.shadows.Override(new Vector4(0.92f, 0.88f, 1.14f, -0.03f));
            smh.midtones.Override(new Vector4(0.98f, 0.97f, 1.05f, 0f));
            smh.highlights.Override(new Vector4(1.04f, 1f, 0.96f, 0f));
            smh.shadowsStart.Override(0f); smh.shadowsEnd.Override(0.35f); smh.highlightsStart.Override(0.55f); smh.highlightsEnd.Override(1f);
            // gentle warm-highlight / violet-shadow split (neutral grey = 0.5)
            var st = profile.Add<SplitToning>(true);
            // round 5: shadow tone blue (hue ~235) instead of violet (R > G pushed dark cyan water toward violet; reference
            // shading is blue-violet with pink only where lit)
            st.shadows.Override(new Color(0.41f, 0.42f, 0.64f)); st.highlights.Override(new Color(0.56f, 0.52f, 0.48f)); st.balance.Override(-15f);
            // Hue-selective saturation: only the blue-violet range (drum walls, ceiling bays, far tunnel ~225-268 deg) gets
            // richer (x1.28); the purple hat (~280), pink fur, cyan water and gold are untouched.
            var curves = profile.Add<ColorCurves>(true);
            curves.hueVsSat.Override(new TextureCurve(new[] { new Keyframe(0.57f, 0.5f), new Keyframe(0.63f, 0.55f), new Keyframe(0.72f, 0.54f),
                new Keyframe(0.765f, 0.5f) }, 0.5f, true, new Vector2(0f, 1f)));
            // round 5: hue-vs-hue (part of the colour-grading LUT, free at runtime): the reference violets sit ~12 deg BLUER
            // than ours (median hue frame 251 vs 264, tunnel ahead 255 vs 270, upper-right wall 262 vs 284, hat 279 vs 286).
            // Only 240-300 deg moves (max -12 deg around 280); cyan water (190-215), pink fur / rails (>300) and gold untouched.
            curves.hueVsHue.Override(new TextureCurve(new[] { new Keyframe(0.66f, 0.5f), new Keyframe(0.70f, 0.475f), new Keyframe(0.775f, 0.4667f),
                new Keyframe(0.81f, 0.488f), new Keyframe(0.835f, 0.5f) }, 0.5f, true, new Vector2(0f, 1f)));
            // round 5 (water request): the vignette colour (.12, .03, .26) multiplied G far more than B -> the cyan water in the
            // bottom corners turned violet (hue 225 / 210 vs reference 205 / 193). Weaker and a neutral deep blue (G ~ B / 2).
            var vg = profile.Add<Vignette>(true); vg.intensity.Override(0.22f); vg.smoothness.Override(0.48f); vg.color.Override(new Color(0.10f, 0.20f, 0.40f));
            var wb = profile.Add<WhiteBalance>(true); wb.temperature.Override(0f); wb.tint.Override(0f);
            // soft far tunnel (premium film depth): mascot, coins and near rings stay crisp
            var dof = profile.Add<DepthOfField>(true);
            // round 3: a little softer far tunnel (reference is dreamier / softer behind the second ring)
            // round 4: the reference far tunnel is soft from the second gold ring on (ours stayed crisp to ~40 m)
            dof.mode.Override(DepthOfFieldMode.Gaussian); dof.gaussianStart.Override(15f); dof.gaussianEnd.Override(42f);
            dof.gaussianMaxRadius.Override(1.5f); dof.highQualitySampling.Override(true);
            foreach (var c in profile.components) AssetDatabase.AddObjectToAsset(c, profile);
            vol.sharedProfile = profile;
        }

        /// <summary>Round 4: URP per-object additional-light limit. The drum walls / rims are long combined section meshes that
        /// several ring lights, the pink upper-left light, the water bounce and the runner's character lights all reach; with
        /// 4 lights per object URP drops a different light on each section -> vertical light seams on the walls and a dead pink
        /// light (round 3 v2/v3). ProjectSetup.Run (full build) writes 4, so the lighting build re-applies 8 afterwards.
        /// HIGH TIER (PC / high-end phones); a low mobile tier should use 4 with fewer ring lights.</summary>
        const int PerObjectLightLimit = 8;

        static void EnsurePerObjectLightLimit()
        {
            foreach (var path in new[] { "Assets/Settings/Mobile_RPAsset.asset", "Assets/Settings/PC_RPAsset.asset" })
            {
                var asset = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(path);
                if (asset == null) continue;
                var so = new SerializedObject(asset);
                var p = so.FindProperty("m_AdditionalLightsPerObjectLimit");
                if (p == null || p.intValue == PerObjectLightLimit) continue;
                p.intValue = PerObjectLightLimit;
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(asset);
                AssetDatabase.SaveAssetIfDirty(asset);
                Debug.Log($"[BWK] lighting: {path} per-object light limit -> {PerObjectLightLimit} (high tier)");
            }
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
            // the metallic drum walls are near-mirrors at the grazing angles the rear camera sees: a slightly weaker probe
            // keeps their own violet albedo / ambient in the mix (less pale reflected haze)
            probe.intensity = 0.9f;
            probe.hdr = true;
            probe.boxProjection = false;
            probe.nearClipPlane = 0.1f;
            probe.farClipPlane = 120f;
        }

        /// <summary>One warm point light per gold ring (positions follow BuildRings: FirstRingDistance, every GoldRingSpacing).</summary>
        static void BuildRingLights(GameObject lights)
        {
            var holder = Child(lights, "RingLights");
            int k = 0;
            for (float d = FirstRingDistance; d < portalD - 5f; d += GoldRingSpacing, k++)
            {
                var f = track.Evaluate(d);
                var go = Child(holder, $"RingLight_{d:000}");
                go.transform.position = f.FlatPoint(0f, TunnelCenter + 1.1f) - f.forward * 0.35f;
                var l = go.AddComponent<Light>();
                l.type = LightType.Point;
                // warm amber-rose: on the violet drum wall this reads as the reference's pink-peach glow around each ring
                // round 4: rosier (reference ring surroundings p30 #f2d2c9 pale pink-peach, median pink-lavender; ours
                // yellow-orange) -> rose-peach pools on the walls and peach glints on the gold
                l.color = new Color(1f, 0.52f, 0.5f);
                l.intensity = 2.6f;
                l.range = 6.5f;
                l.shadows = LightShadows.None;
            }
        }

        /// <summary>Round 4: spot light aimed at the drum wall seen at screen point (sx, sy) of the portrait hero frame (y from
        /// the top), placed `back` m before the wall along that camera ray, so the light lands exactly on the wall area the
        /// reference shows lit. The cone points away from the runner (no light on the mascot).</summary>
        static void AddHeroSpot(GameObject parent, string name, float sx, float sy, float back, Color c, float intensity, float angle, float range)
        {
            HeroCameraPose(out var camPos, out var camRot);
            float tanV = Mathf.Tan(HeroCamFov * 0.5f * Mathf.Deg2Rad), tanH = tanV * (9f / 16f);
            var dir = (camRot * new Vector3((2f * sx - 1f) * tanH, (1f - 2f * sy) * tanV, 1f)).normalized;
            if (!TunnelWallHit(camPos, dir, HeroDistance - HeroCamBack, 0f, out var hit, out var wf))
            {
                Debug.LogWarning($"[BWK] {name}: no drum wall at screen ({sx}, {sy})");
                return;
            }
            var go = Child(parent, name);
            go.transform.position = hit - dir * back;
            go.transform.rotation = Quaternion.LookRotation(dir);
            var l = go.AddComponent<Light>();
            l.type = LightType.Spot; l.color = c; l.intensity = intensity; l.range = range;
            l.spotAngle = angle; l.innerSpotAngle = angle * 0.3f; l.shadows = LightShadows.None;
            Debug.Log($"[BWK] {name}: wall hit at track {wf.distance:F1} m, light {Vector3.Distance(camPos, go.transform.position):F1} m from the hero camera");
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
            // Gold (BWK_Gold _ProbeBakeTint) and bulbs / neon (BWK_Emissive _ProbeBakeDim) are dimmed and rose-tinted while
            // the cubemaps render: the near-mirror drum walls then reflect a violet tunnel with rose glints near the rings
            // instead of a yellow haze (yellow + violet = the grey-lavender wash of the HDR baseline).
            Shader.SetGlobalFloat("_BWK_ProbeBake", 1f);
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
            finally { RenderSettings.fog = fog; Shader.SetGlobalFloat("_BWK_ProbeBake", 0f); }
        }

        /// <summary>Reference f_003.00s star layout in the PORTRAIT hero frame: screen centre (fractions of the 9:16 frame,
        /// y from the top), screen width (fraction of the frame width), clockwise screen roll (deg) and colour (0 yellow,
        /// 1 cyan, 2 pink, 3 purple). Every star is projected from the fixed hero camera onto the drum wall, so it lands
        /// exactly there in the hero capture (lead directive m1: big + few, on the WALLS, none in front of the vanishing point).</summary>
        static readonly (float x, float y, float w, float roll, int color)[] HeroStarLayout =
        {
            (0.200f, 0.090f, 0.19f, 30f, 0),    // big yellow star on the upper-left wall (orange inner glow)
            (0.432f, 0.203f, 0.13f, -14f, 1),   // cyan star below-right of it (round 3: reference ~0.12-0.13 wide)
            (0.968f, 0.285f, 0.085f, 18f, 0),   // small yellow star on the right wall, half off-frame
            (0.988f, 0.360f, 0.080f, -10f, 2),  // pink star below it at the frame edge
        };

        const float StarMeshWidth = 1.07f;   // SM_NeonStarTube tip-to-tip incl. tube at scale 1 (outer radius 0.5 + tube 0.085)
        const float StarMeshRadius = 0.585f;

        /// <summary>Hero camera pose exactly as RunnerCameraRig.Step computes it on a snap (lane 0, no jump, portrait aspect)
        /// with the owner-approved HeroCam* values, so lighting props can be placed in screen space even during the full
        /// build (the camera rig does not exist yet when the stars are built). Includes the lens Dutch (CaptureHero).</summary>
        static void HeroCameraPose(out Vector3 pos, out Quaternion rot)
        {
            float d = HeroDistance;
            var fc = track.Evaluate(d - HeroCamBack);
            var fr = track.Evaluate(d);
            var fl = track.Evaluate(d + 10f);                                     // RunnerCameraRig.lookAhead
            pos = fc.position + fc.flatUp * HeroCamHeight;
            pos -= Vector3.up * ((fc.position.y - fr.position.y) * 0.85f);       // slopeCompensation
            var ahead = fl.position + fl.flatUp * HeroCamHeight;
            ahead += Vector3.up * ((fr.position.y - fl.position.y) * 0.5f);      // lookSlopeCompensation
            var runnerPoint = fr.position + fr.flatUp * 0.45f;
            var look = Vector3.Lerp(ahead, runnerPoint, 0.08f);                  // lookAtRunnerWeight
            rot = Quaternion.LookRotation(look - pos, fc.flatUp) * Quaternion.Euler(HeroCamPitch, 0f, 0f);
            rot *= Quaternion.Euler(0f, 0f, Mathf.Clamp(-fr.roll * 0.5f, -11f, 11f));   // bankFactor / maxDutch
        }

        /// <summary>Marches a ray to the point `inset` m inside the drum wall (radius TunnelRadius around the tunnel axis).</summary>
        static bool TunnelWallHit(Vector3 origin, Vector3 dir, float sStart, float inset, out Vector3 hit, out TrackFrame frame)
        {
            float s = sStart;
            hit = origin; frame = track.Evaluate(s);
            for (float t = 0.3f; t < 90f; t += 0.04f)
            {
                var p = origin + dir * t;
                for (int k = 0; k < 3; k++)
                {
                    var f = track.Evaluate(s);
                    s = Mathf.Clamp(s + Vector3.Dot(p - f.FlatPoint(0, TunnelCenter), f.forward), 0f, track.Length);
                }
                frame = track.Evaluate(s);
                var off = p - frame.FlatPoint(0, TunnelCenter);
                off -= frame.forward * Vector3.Dot(off, frame.forward);
                if (off.magnitude >= TunnelRadius - inset) { hit = p; return true; }
            }
            return false;
        }

        /// <summary>
        /// Neon outline stars (reference: thick yellow / cyan / pink tubes with pale hot cores and soft tinted halos on the
        /// drum walls). The hero frame gets the reference layout (HeroStarLayout, placed through the hero camera); the rest
        /// of the tunnel gets sparse big stars on the upper walls, skipping anything the hero camera would see. Every star
        /// gets a soft additive glow card just behind it (its colour spilling over the wall: the reference's big yellow star
        /// is filled with orange light). Placement uses its own seeded RNG; the shared rng is advanced exactly as the
        /// original version did, so the portholes / items / hero position built after this stay where they were.
        /// </summary>
        static void BuildNeonStars(GameObject env, bool save = true)
        {
            // keep the shared rng sequence identical to the old placement loop (3 draws per star + 1 per step)
            for (float d = tunnelStart + 2f; d < portalD - 4f; d += 1.1f + (float)rng.NextDouble() * 1.3f)
            { rng.NextDouble(); rng.NextDouble(); rng.NextDouble(); }

            // thick single-tube star (Tools/Blender/scripts/build_lighting_stars.py); falls back to the props double-line star
            var outline = ModelParts("Lighting", "SM_NeonStarTube");
            if (outline.Count == 0) outline = ModelParts("Props", "SM_NeonStar");
            if (outline.Count == 0) { Debug.LogWarning("[BWK] SM_NeonStar missing - stars skipped"); return; }
            var mats = new[] { Mat("M_Neon_Yellow"), Mat("M_Neon_Cyan"), Mat("M_Neon_Pink"), Mat("M_Neon_Purple") ?? Mat("M_Neon_Pink") };
            var glowMats = new[] { Mat("M_StarGlow_Yellow"), Mat("M_StarGlow_Cyan"), Mat("M_StarGlow_Pink"), Mat("M_StarGlow_Purple") ?? Mat("M_StarGlow_Pink") };
            var quadMesh = Resources.GetBuiltinResource<Mesh>("Quad.fbx");
            var holder = Child(env, "NeonStars");
            var comb = new LightCombiner(save);
            var glowComb = new LightCombiner(save);
            List<Part> Recolor(Material mat) =>
                outline.Select(p => new Part(p.mesh, Enumerable.Repeat(mat, Mathf.Max(1, p.mesh.subMeshCount)).ToArray(), p.local)).ToList();
            void AddCard(Material m, Vector3 pos, Quaternion rot, float size)
            {
                if (quadMesh == null || m == null) return;
                glowComb.Add(new List<Part> { new Part(quadMesh, new[] { m }, Matrix4x4.identity) }, Matrix4x4.TRS(pos, rot, new Vector3(size, size, 1f)));
            }
            void AddGlow(int ci, Vector3 pos, Quaternion rot, float size)
            {
                if (quadMesh == null || glowMats[ci] == null) return;
                glowComb.Add(new List<Part> { new Part(quadMesh, new[] { glowMats[ci] }, Matrix4x4.identity) },
                             Matrix4x4.TRS(pos, rot, new Vector3(size, size, 1f)));
            }

            // ---- hero frame: the reference layout, projected from the fixed hero camera onto the drum wall
            HeroCameraPose(out var camPos, out var camRot);
            float tanV = Mathf.Tan(HeroCamFov * 0.5f * Mathf.Deg2Rad), tanH = tanV * (9f / 16f);
            var camFwd = camRot * Vector3.forward; var camUp = camRot * Vector3.up; var camRight = camRot * Vector3.right;
            int heroCount = 0;
            foreach (var s in HeroStarLayout)
            {
                var dir = camRot * new Vector3((2f * s.x - 1f) * tanH, (1f - 2f * s.y) * tanV, 1f).normalized;
                float inset = 0.7f, scale = 1f; Vector3 pos = camPos; TrackFrame wf = default; bool ok = false;
                for (int it = 0; it < 3; it++)
                {
                    ok = TunnelWallHit(camPos, dir, HeroDistance - HeroCamBack, inset, out pos, out wf);
                    if (!ok) break;
                    float depth = Vector3.Dot(pos - camPos, camFwd);
                    scale = s.w * 2f * depth * tanH / StarMeshWidth;
                    inset = 0.12f + StarMeshRadius * scale;   // tube tips stay just inside the drum surface
                }
                if (!ok) { Debug.LogWarning($"[BWK] hero star at ({s.x}, {s.y}) found no wall"); continue; }
                var toCam = (camPos - pos).normalized;
                var axisP = wf.FlatPoint(0, TunnelCenter);
                var inward = Vector3.ProjectOnPlane(axisP - pos, wf.forward).normalized;
                // mostly facing the camera (bold full star shape like the reference), leaning a little toward the wall
                var facing = (toCam + inward * 0.35f).normalized;
                scale /= Mathf.Lerp(1f, Mathf.Max(0.5f, Vector3.Dot(facing, toCam)), 0.5f);
                float rr = s.roll * Mathf.Deg2Rad;
                var upHint = Vector3.ProjectOnPlane(camUp * Mathf.Cos(rr) + camRight * Mathf.Sin(rr), facing).normalized;
                var rot = Quaternion.LookRotation(facing, upHint);
                comb.Add(Recolor(mats[s.color]), Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                // glow card facing the camera, just behind the tubes, ~1.8x the star: soft enough that the part cut by the
                // drum wall is invisible (its radius beyond the inset is < 4 % intensity)
                AddGlow(s.color, pos - toCam * (0.06f * scale), Quaternion.LookRotation(-toCam, upHint), StarMeshWidth * 2.2f * scale);
                if (s.color == 0) AddCard(Mat("M_StarFill_Yellow"), pos - toCam * (0.04f * scale), Quaternion.LookRotation(-toCam, upHint), StarMeshWidth * 1.15f * scale);
                heroCount++;
                Debug.Log($"[BWK] hero star c{s.color} screen ({s.x:F2},{s.y:F2}) track {wf.distance:F1} m depth {Vector3.Dot(pos - camPos, camFwd):F1} m scale {scale:F2}");
            }

            // ---- round 5: soft pink-magenta haze on the upper-left drum wall (reference: the wall around the big yellow star
            // glows pink-mauve, hue ~311 vs ours 284 even with the pink spot). One additive LightBlob card, a little inside the
            // wall, facing the hero camera; _NearFade hides it as the runner gets close (no flat card seen up close).
            {
                var dir = (camRot * new Vector3((2f * 0.16f - 1f) * tanH, (1f - 2f * 0.20f) * tanV, 1f)).normalized;
                if (TunnelWallHit(camPos, dir, HeroDistance - HeroCamBack, 0.8f, out var hp, out var hwf))
                {
                    var toCam = (camPos - hp).normalized;
                    AddCard(Mat("M_PinkHaze"), hp, Quaternion.LookRotation(-toCam, camUp), 4.2f);
                    Debug.Log($"[BWK] pink haze card at track {hwf.distance:F1} m, depth {Vector3.Dot(hp - camPos, camFwd):F1} m");
                }
            }

            // ---- luminous far tunnel (reference: rings receding into warm-white light at x ~.55, y ~.30 of the hero frame):
            // pick the tunnel-axis point 35-75 m ahead that projects closest to that spot, put a wide soft halo + a tight
            // warm-white core there facing the hero camera (LightBlob _NearFade: they vanish as the runner approaches)
            {
                Vector3 best = Vector3.zero; float bestErr = float.MaxValue, bestDepth = 0f;
                for (float a = 30f; a <= 55f; a += 1f)
                {
                    var p = track.Evaluate(HeroDistance + a).FlatPoint(0, TunnelCenter - 0.3f);
                    var c = Quaternion.Inverse(camRot) * (p - camPos);
                    if (c.z < 5f) continue;
                    float u = 0.5f + 0.5f * c.x / (c.z * tanH), v = 0.5f - 0.5f * c.y / (c.z * tanV);
                    float err = (u - 0.55f) * (u - 0.55f) * 3.2f + (v - 0.30f) * (v - 0.30f);
                    if (err < bestErr) { bestErr = err; best = p; bestDepth = c.z; }
                }
                if (bestErr < float.MaxValue)
                {
                    var q = Quaternion.LookRotation(best - camPos, camUp);
                    AddCard(Mat("M_VanishGlow"), best, q, 7.5f);
                    AddCard(Mat("M_VanishCore"), best - (best - camPos).normalized * 0.5f, q, 3.6f);
                    var c = Quaternion.Inverse(camRot) * (best - camPos);
                    Debug.Log($"[BWK] vanishing glow at depth {bestDepth:F1} m, screen ({0.5f + 0.5f * c.x / (c.z * tanH):F2},{0.5f - 0.5f * c.y / (c.z * tanV):F2})");
                }
            }

            // ---- rest of the tunnel: sparse big stars on the upper walls, never inside the hero view
            bool InHeroView(Vector3 p, float margin)
            {
                var c = Quaternion.Inverse(camRot) * (p - camPos);
                if (c.z < 0.3f) return false;
                float u = 0.5f + 0.5f * c.x / (c.z * tanH), v = 0.5f - 0.5f * c.y / (c.z * tanV);
                return u > -margin && u < 1f + margin && v > -margin && v < 1f + margin;
            }
            var r = new System.Random(5150);
            float Rand() => (float)r.NextDouble();
            int chunk = 0; float chunkStart = tunnelStart;
            int lastColor = -1;
            int count = 0;
            for (float d = tunnelStart + 3f; d < portalD - 4f; d += 4.5f + Rand() * 4f)
            {
                // keep clear of the gold rings (BuildRings: FirstRingDistance + k * GoldRingSpacing)
                float ringPhase = Mathf.Repeat(d - FirstRingDistance, GoldRingSpacing);
                if (ringPhase < 0.9f || ringPhase > GoldRingSpacing - 0.9f) continue;
                var f = track.Evaluate(d);
                // upper side walls (26-66 deg from the ceiling, both sides) with an occasional ceiling star
                float side = Rand() < 0.5f ? -1f : 1f;
                float angDeg = Rand() < 0.06f ? Mathf.Lerp(-10f, 10f, Rand()) : side * Mathf.Lerp(26f, 66f, Rand());
                float ang = angDeg * Mathf.Deg2Rad; // 0 = ceiling
                var radial = f.flatRight * Mathf.Sin(ang) + f.flatUp * Mathf.Cos(ang);
                var center = f.FlatPoint(0, TunnelCenter);
                // bigger and fewer (lead m1): mostly bold stars, some mid ones
                float scale = Rand() < 0.55f ? Mathf.Lerp(1.6f, 2.2f, Rand()) : Mathf.Lerp(1.1f, 1.5f, Rand());
                var pos = center + radial * (TunnelRadius - 0.38f - 0.18f * scale);
                // Face the tunnel centre and tilt back toward the oncoming rear camera so they read as bold shapes;
                // tip up on screen with a varied roll (reference stars sit at many angles).
                float tilt = Mathf.Lerp(0.42f, 0.62f, Rand());
                Vector3 facing = (-radial * 0.8f - f.forward * tilt).normalized;
                Vector3 upHint = Vector3.ProjectOnPlane(f.flatUp + radial * 0.3f, facing);
                if (upHint.sqrMagnitude < 1e-4f) upHint = Vector3.ProjectOnPlane(f.forward, facing);
                var rot = Quaternion.LookRotation(facing, upHint.normalized) * Quaternion.Euler(0, 0, Rand() * 56f - 28f);
                // colour: yellow / cyan / pink / purple, never the same twice in a row
                float cr = Rand();
                int ci = cr < 0.34f ? 0 : cr < 0.6f ? 1 : cr < 0.84f ? 2 : 3;
                if (ci == lastColor) ci = (ci + 1) % 4;
                if (InHeroView(pos, 0.12f)) continue;   // the hero frame shows only the designed layout
                lastColor = ci;
                comb.Add(Recolor(mats[ci]), Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                // glow card ~2x the star size, just behind the tubes; tilted only half as much toward the camera as
                // the star so its soft far edge stays in front of the curved drum wall (no visible intersection)
                Vector3 gFacing = (-radial * 0.8f - f.forward * tilt * 0.45f).normalized;
                Vector3 gUp = Vector3.ProjectOnPlane(rot * Vector3.up, gFacing);
                if (gUp.sqrMagnitude < 1e-4f) gUp = Vector3.ProjectOnPlane(f.forward, gFacing);
                AddGlow(ci, pos - gFacing * 0.12f, Quaternion.LookRotation(gFacing, gUp.normalized), 2.0f * scale);
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
            Debug.Log($"[BWK] neon stars: {heroCount} hero-frame + {count} tunnel stars with glow cards");
        }

        /// <summary>Lights parented to the runner so the mascot always gets the reference's warm top glow and soft back rim.</summary>
        static void BuildCharacterLights(GameObject runnerGo)
        {
            // Character lights riding with the mascot (reference: warm bulb glow on the hat/fur top, pink bounce on the back).
            // Keep every character light under the "CharacterLights" child (agent previews rebuild it in memory).
            var group = Child(runnerGo, "CharacterLights");
            // warm bulb glow on the top of the hat / pom-pom (slightly ahead, so it grazes over the top toward the camera)
            // round 3: higher + a bit weaker -> no near-field hotspot on the pom-pom (ours p50 #c892e3 vs reference #8a41b9)
            // round 4: weaker + warmer (reference pom-pom / crown are deep saturated purple #7b2eaa, ours read pale lilac #ba83e0)
            // round 5: hat zone L .36 / S .48 vs reference .30 / .58 (warm top light washes the purple knit out) -> weaker
            CharLight(group, "CharLight_WarmTop", new Vector3(0.35f, 2.75f, 0.55f), new Color(1f, 0.62f, 0.40f), 0.85f, 4.4f);
            // soft pink fill on the fluffy back the rear camera sees
            // round 3: warmer coral-pink (reference back fur ~#e58c98 lit; ours read mauve under the violet ambient)
            // round 4 (lead gap 2): reference fur p50 #cc618c (L .48, S .53), ours #d887b3 (L .61, S .38) = too light, washed
            // out, and the hat ribs / white stripe glared. The light moves DOWN to fur height (it was at hat height, 1.3 m
            // from the hat, 1.7 m from the fur) and becomes a saturated rose-coral (no green -> the coral fur stays saturated),
            // less energy overall: the fur gets the warm saturated key, the hat only grazing light (matte knit).
            // v2: v1 (1, .5, .55) x2.0 gave candy-magenta fur #e687b9 (the violet ambient already supplies the blue): now a
            // near-pure warm coral-red key from the left-back (modelling across the back) -> hue toward the reference's rose
            // round 5 (character request: fur #e374ad too magenta / light vs rose #cc618c; body_zone V .85 vs .77): -17 %
            CharLight(group, "CharLight_PinkBack", new Vector3(-0.55f, 0.85f, -1.7f), new Color(1f, 0.38f, 0.36f), 1.5f, 3.4f);
            // cool lavender light from the bright tunnel ahead: wraps around the fur silhouette as a rim
            // round 4: pink rim (reference: pink rim light around the fur and arms), less blue than v1
            // v3: v2 fur #e680b3 had too much blue / green vs the reference rose #cc618c (B/R .57 vs .43): weaker, warmer rim
            // round 5: weaker and less blue (fur hue 324 vs reference 329, too light)
            CharLight(group, "CharLight_RimFront", new Vector3(0f, 1.15f, 2.2f), new Color(1f, 0.40f, 0.50f), 1.6f, 3.6f);

            // soft violet contact shadow card on the water right under him (stays on the surface during jumps)
            var card = GameObject.CreatePrimitive(PrimitiveType.Quad);
            card.name = "ContactShadow";
            Object.DestroyImmediate(card.GetComponent<Collider>());
            card.transform.SetParent(group.transform, false);
            card.transform.localPosition = new Vector3(0f, 0.035f, -0.3f);   // round 3: reaches behind him (visible to the rear camera)
            card.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            card.transform.localScale = new Vector3(1.6f, 2.3f, 1f);   // round 3: broader, reaches past the feet / tail
            var mr = card.GetComponent<MeshRenderer>();
            mr.sharedMaterial = Mat("M_ContactShadow");
            mr.shadowCastingMode = ShadowCastingMode.Off;
            mr.receiveShadows = false;
            var cs = card.AddComponent<LightingContactShadow>();
            cs.runner = runnerGo.GetComponent<RunnerController>();
            cs.baseScale = card.transform.localScale;
            cs.surfaceOffset = 0.035f;
        }

        /// <summary>Agent preview hook: rebuilds the neon stars + glow cards in memory (meshes never saved as assets).</summary>
        static partial void PreviewLightingProps(GameObject root, float L)
        {
            try
            {
                var env = root.transform.Find("Environment");
                if (env == null) return;
                for (int i = env.childCount - 1; i >= 0; i--)
                    if (env.GetChild(i).name == "NeonStars") Object.DestroyImmediate(env.GetChild(i).gameObject);
                var savedRng = rng;
                rng = new System.Random(1); // BuildNeonStars advances the shared rng; keep the caller's sequence untouched
                try { BuildNeonStars(env.gameObject, false); }
                finally { rng = savedRng; }
            }
            catch (System.Exception e) { Debug.LogWarning($"[BWK] preview lighting props failed: {e.Message}"); }
        }

        /// <summary>Combiner for lighting-owned props; with save = false the meshes stay in memory (agent previews).</summary>
        class LightCombiner
        {
            readonly bool save;
            readonly Dictionary<Material, List<CombineInstance>> groups = new Dictionary<Material, List<CombineInstance>>();
            readonly Dictionary<Material, int> verts = new Dictionary<Material, int>();
            public LightCombiner(bool save) { this.save = save; }

            public void Add(List<Part> parts, Matrix4x4 world)
            {
                foreach (var p in parts)
                    for (int s = 0; s < p.mesh.subMeshCount; s++)
                    {
                        var mat = p.mats != null && p.mats.Length > 0 ? p.mats[Mathf.Min(s, p.mats.Length - 1)] : null;
                        if (mat == null) continue;
                        if (!groups.TryGetValue(mat, out var l)) { l = new List<CombineInstance>(); groups[mat] = l; verts[mat] = 0; }
                        l.Add(new CombineInstance { mesh = p.mesh, subMeshIndex = s, transform = world * p.local });
                        verts[mat] += p.mesh.vertexCount;
                    }
            }

            public void Flush(GameObject parent, string name, bool castShadows)
            {
                foreach (var kv in groups)
                {
                    var mesh = new Mesh { name = $"{name}_{kv.Key.name}" };
                    mesh.indexFormat = verts[kv.Key] > 60000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
                    mesh.CombineMeshes(kv.Value.ToArray(), true, true);
                    mesh.RecalculateBounds();
                    if (save) SaveMesh(mesh);
                    var go = Child(parent, mesh.name);
                    go.AddComponent<MeshFilter>().sharedMesh = mesh;
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterial = kv.Key;
                    mr.shadowCastingMode = castShadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
                    mr.receiveShadows = false;
                    if (save)
                        GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic | StaticEditorFlags.ReflectionProbeStatic);
                }
                groups.Clear();
                verts.Clear();
            }
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
