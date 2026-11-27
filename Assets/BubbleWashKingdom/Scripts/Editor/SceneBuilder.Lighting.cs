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
            TunePortalDestination(root);
            var lights = Child(root, "Lighting");
            // Key light: near-vertical warm top light. Works for every track heading (the slide winds through all
            // directions), lights hat / pom-pom / coin tops, and drops the mascot's soft shadow right beneath him.
            // It leans slightly toward the rear camera (most of the slide heads +Z) so the mascot reads top-lit / softly
            // back-lit with a visible contact shadow.
            var sunGo = Child(lights, "Key Light");
            sunGo.transform.rotation = Quaternion.Euler(70f, 165f, 0f);
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.82f, 0.64f);   // S2 pass 1 (gap #4): warmer key, same intensity (was 1, .86, .72)
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
            // round 5: agent previews showed NO change for .94 -> .86 (the in-memory ambient SH probe seems to be recomputed only
            // on scene load). UpdateEnvironment only SCHEDULES a refresh: it did not show in the batch preview either, so
            // the .86 is verified only by the lead's full build + reload (stills / hero capture of the saved scene).
            DynamicGI.UpdateEnvironment();
            // Aerial perspective: saturated lavender-violet (never pale grey): the near tunnel stays clear and rich, the far
            // tunnel melts into a lighter violet glow while the warm bulbs still punch through (emissives use little fog).
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            // round 3: bluer violet (owner sheet 04 "blue-violet shading, avoid flat lavender"): the mid tunnel measured
            // p50 #9578d0 vs reference #5c52ac -> the haze between the rings is now a deeper blue-violet
            RenderSettings.fogColor = new Color(0.50f, 0.42f, 1.0f);
            RenderSettings.fogDensity = 0.0102f;   // S2 p1 v4 tested .0078: far-tunnel disk unchanged (mean #b194b4 vs #b294b6) -> kept .0102 (global, other screens unverified)
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
            // OWNER 2026-11-27 05:28 "Yes, apply it" (the video-measured grade + controlled soft glow previewed 2026-11-26 22:30,
            // Captures/look/GRADE_preview_p4_16x9.png / _9x16.png, lead tool GradePreview.Batch -bwkGlow 0.5): 1.0 / 1.38 / 0.78
            // -> threshold 0.90 / intensity 1.93 / scatter 0.82 (softer, wider halos on the bulbs and neon stars).
            // Reversible (owner 05:5x "preserve the previous rendering settings"): VideoLookGrade = false restores the exact
            // pre-grade look of checkpoint-25-p4 (bloom 1.0 / 1.38 / 0.78, no Color Lookup) on the next full build.
            if (VideoLookGrade) { bloom.threshold.Override(0.90f); bloom.intensity.Override(1.93f); bloom.scatter.Override(0.82f); }
            else { bloom.threshold.Override(1.0f); bloom.intensity.Override(1.38f); bloom.scatter.Override(0.78f); }
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
            // r8 v2 (lighting): the reference darks are grey-violet (hero upper half darkest 5 % #433d5f, S .36), ours navy
            // (#1f164b, S .71) because this + the split-toning shadows re-tinted every dark / mid wall pixel blue: much
            // weaker blue push (the drum wall holes get their depth from BWK_DrumWall _HoleDarken instead)
            smh.shadows.Override(new Vector4(0.97f, 0.95f, 1.05f, -0.03f));
            smh.midtones.Override(new Vector4(0.98f, 0.97f, 1.05f, 0f));
            smh.highlights.Override(new Vector4(1.04f, 1f, 0.96f, 0f));
            smh.shadowsStart.Override(0f); smh.shadowsEnd.Override(0.35f); smh.highlightsStart.Override(0.55f); smh.highlightsEnd.Override(1f);
            // gentle warm-highlight / violet-shadow split (neutral grey = 0.5)
            var st = profile.Add<SplitToning>(true);
            // round 5: shadow tone blue (hue ~235) instead of violet (R > G pushed dark cyan water toward violet; reference
            // shading is blue-violet with pink only where lit)
            // r8 v2: shadow tone (.41, .42, .64) -> a weaker grey-violet (hue ~252 like the reference darks)
            // S2 pass 1 v1 tried warmer highlights (.60, .52, .44): it pulled the lilac walls' blue down (top band V .65 -> .56,
            // hue 266 -> 278 = magenta, reference 254-263) -> reverted; the warmth comes from the warmer key light instead
            st.shadows.Override(new Color(0.48f, 0.46f, 0.56f)); st.highlights.Override(new Color(0.56f, 0.52f, 0.48f)); st.balance.Override(-15f);
            // Hue-selective saturation: only the blue-violet range (drum walls, ceiling bays, far tunnel ~225-268 deg) gets
            // richer (x1.28); the purple hat (~280), pink fur, cyan water and gold are untouched.
            var curves = profile.Add<ColorCurves>(true);
            // round 8: the opposite now - measured wall pixels S2-S7 reference S .37-.48 vs ours .55-.68 (too saturated
            // blue-violet everywhere): the same hue band is DE-saturated to x0.9 (with the greyer M_DrumWall base)
            curves.hueVsSat.Override(new TextureCurve(new[] { new Keyframe(0.57f, 0.5f), new Keyframe(0.63f, 0.45f), new Keyframe(0.72f, 0.45f),
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
            // OWNER 2026-11-27 05:28 approved the VIDEO LOOK grade: a 32^3 URP Color Lookup fitted by Tools/look_lut.py (Lab
            // quantile match of the owner's frames 0.75 / 4.50 / 6.75 / 11.25 s vs our matched stills of build p4, strength
            // 0.85; judged on the other sections: palette dE R2 12.0 -> 10.1, R5 11.3 -> 6.1, finale 5.7 -> 2.9). URP applies it
            // after tonemapping (sRGB in -> sRGB out), cheap on mobile (part of the uber post pass). Refit = run look_lut.py on
            // new stills and copy its lut_video_look.png over this file; remove = contribution 0.
            var videoLut = VideoLookGrade ? LoadVideoLookLut() : null;
            if (!VideoLookGrade) Debug.Log("[BWK] video look grade OFF (SceneBuilder.VideoLookGrade = false): pre-grade post settings");
            else if (videoLut != null)
            {
                var lookup = profile.Add<ColorLookup>(true);
                lookup.texture.Override(videoLut);
                lookup.contribution.Override(1f);
                Debug.Log($"[BWK] video look grade: Color Lookup {VideoLookLutPath} ({videoLut.width}x{videoLut.height}, valid {lookup.ValidateLUT()})");
            }
            else Debug.LogWarning("[BWK] video look grade: " + VideoLookLutPath + " missing - no Color Lookup");
            // soft far tunnel (premium film depth): mascot, coins and near rings stay crisp
            var dof = profile.Add<DepthOfField>(true);
            // round 3: a little softer far tunnel (reference is dreamier / softer behind the second ring)
            // round 4: the reference far tunnel is soft from the second gold ring on (ours stayed crisp to ~40 m)
            // S2 pass 1 (lead gap #3): the far tunnel read as a soft pink bokeh blur (edge energy x 480-800 / y 140-360 ours
            // 5.1 vs reference 7.9): the reference's receding gold bulb rings and stars are sharp -> blur only far beyond
            // the third ring, and much less of it (no heavy DOF)
            // S2 pass 3 (judge gap #3, door camera: gold rings 6-8 sit 39-78 m away and blurred into the haze disk) -> 70 / 150
            dof.mode.Override(DepthOfFieldMode.Gaussian); dof.gaussianStart.Override(70f); dof.gaussianEnd.Override(150f);
            dof.gaussianMaxRadius.Override(0.5f); dof.highQualitySampling.Override(true);
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
                // round 8: reflection-probe box projection on (ProjectSetup writes false; the probes are box-projected now)
                var bp = so.FindProperty("m_ReflectionProbeBoxProjection");
                bool changed = false;
                if (p != null && p.intValue != PerObjectLightLimit) { p.intValue = PerObjectLightLimit; changed = true; }
                if (bp != null && !bp.boolValue) { bp.boolValue = true; changed = true; }
                if (!changed) continue;
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(asset);
                AssetDatabase.SaveAssetIfDirty(asset);
                Debug.Log($"[BWK] lighting: {path} per-object light limit -> {PerObjectLightLimit} (high tier), probe box projection on");
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
            // round 8: box projection (owner: "warm cinematic reflections"): each probe's box is the bounds of its own tunnel
            // chunk / hall block, so gold, glass, rails, water and the metal walls reflect the nearby bulbs, rings and neon
            // at their real place instead of an infinitely far cubemap (that read as a flat violet haze). Baked cubemaps,
            // no realtime probes, no SSR: mobile safe (one extra ray-box intersection per reflecting pixel).
            probe.boxProjection = true;
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
                // round 8: the rose light turned every gold glint salmon (rendered gold hue 26-30 deg vs reference 32-36 in
                // S1-S7) -> warm golden-amber bulb light: golden glints on the rings, warm (not pink) pools on the metal
                l.color = new Color(1f, 0.64f, 0.40f);
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
            // S2 p1 v2: both small stars moved ~30 px into the lavender rim's opening (v1: half hidden behind its lip; the
            // reference shows them whole at 720p (820, 205) / (825, 250))
            (0.925f, 0.285f, 0.085f, 18f, 0),   // small yellow star on the right wall, half off-frame
            (0.940f, 0.352f, 0.080f, -10f, 2),  // pink star below it at the frame edge
            // S2 pass 1 (lead gap #1, 16:9 hero vs f_03.00s): the reference's right wall carries three LARGE stars outside
            // the portrait frame (u > 1 = right of it in the 16:9 capture, same vertical FOV; 16:9 x = 437.5 + u * 405).
            // Measured 720p centres / widths: yellow (1010, 65) 95 px, cyan (898, 152) 52 px, pink (1050, 282) 60 px.
            // Our near gold ring (109.75 m) covers x ~925-1060 there, so yellow / pink sit just right of it on the near
            // drum section and cyan between the lavender rim and that ring (same size, colour and roll as the reference).
            // v2: the 16:9 capture lands near stars ~40-60 px right / 20-40 px lower than the portrait mapping (parallax of
            // the landscape rig at 5 m depth; v1 measured yellow (1132, 88), cyan (935, 165), pink (1162, 330)) and they read
            // ~15 % too big -> corrected u / v and widths toward the reference (1080, 65) 95 px / (898, 152) 52 / (1100, 290) 60
            (1.483f, 0.063f, 0.200f, -12f, 0),  // big yellow star, upper-right wall
            (1.080f, 0.196f, 0.125f, -18f, 1),  // cyan star, right wall between rim and gold ring
            (1.512f, 0.346f, 0.130f, 12f, 2),   // pink star, right wall below the yellow one
        };

        /// <summary>Screen S2 pass 3 (owner directive 4): neon outline stars just inside the washing-machine door, measured on
        /// reference f_03.00s at 720p through the R2 door camera (centre x / 1280, y / 720, tip-to-tip width / 1280, roll,
        /// colour 0 yellow 1 cyan 2 pink): yellow (510, 60) ~70 px, cyan (595, 140) ~50, yellow (1010, 60) ~75, cyan
        /// (900, 150) ~50, pink (1050, 285) ~60, small yellow (820, 205) ~26, small pink (825, 250) ~22.</summary>
        static readonly (float x, float y, float w, float roll, int color)[] DoorStarLayout =
        {
            (0.398f, 0.083f, 0.066f, -12f, 0),   // v2: widths x1.2 (v1 yellow ~55 px vs reference ~70)
            (0.465f, 0.194f, 0.047f, 14f, 1),
            (0.789f, 0.083f, 0.071f, 10f, 0),
            (0.672f, 0.215f, 0.047f, -12f, 1),   // v3: left of the nudged right yellow (v2: hidden behind it)
            (0.820f, 0.396f, 0.056f, -8f, 2),
            (0.641f, 0.285f, 0.020f, 6f, 0),
            (0.645f, 0.347f, 0.017f, -6f, 2),
        };

        /// <summary>Screen ALL pass 5: big neon outline stars of the owner's front frames (track distance of the R still, centre
        /// x / 1280, y / 720, tip-to-tip width / 1280, roll, colour 0 yellow 1 cyan 2 pink), measured at 720p on f_04.50s (R3),
        /// f_06.75s (R4), f_08.25s (R5) and f_11.25s (R6).</summary>
        static readonly (float d, float x, float y, float w, float roll, int color)[] RStarLayout =
        {
            (158f, 0.403f, 0.153f, 0.063f, -10f, 1), (158f, 0.778f, 0.167f, 0.086f, 12f, 1), (158f, 0.653f, 0.319f, 0.028f, 0f, 0),
            (190f, 0.766f, 0.125f, 0.148f, -6f, 0), (190f, 0.753f, 0.375f, 0.094f, 10f, 2), (190f, 0.245f, 0.042f, 0.086f, 8f, 0),
            (190f, 0.477f, 0.250f, 0.047f, -8f, 2), (190f, 0.425f, 0.306f, 0.034f, 6f, 1),
            (220f, 0.9375f, 0.283f, 0.140f, 8f, 2), (220f, 0.719f, 0.297f, 0.086f, -10f, 2), (220f, 0.644f, 0.075f, 0.086f, 6f, 2),
            (220f, 0.409f, 0.028f, 0.110f, -4f, 0), (220f, 0.575f, 0.242f, 0.047f, 4f, 1),
            (280f, 0.902f, 0.311f, 0.117f, -8f, 1), (280f, 0.808f, 0.283f, 0.070f, 10f, 0), (280f, 0.695f, 0.067f, 0.070f, 6f, 1),
            (280f, 0.311f, 0.083f, 0.047f, -6f, 1), (280f, 0.516f, 0.139f, 0.047f, 8f, 1), (280f, 0.660f, 0.233f, 0.040f, -4f, 2),
            (280f, 0.386f, 0.214f, 0.030f, 0f, 0),
        };

        const float StarMeshWidth = 1.07f;   // SM_NeonStarTube tip-to-tip incl. tube at scale 1 (outer radius 0.5 + tube 0.085)
        const float StarMeshRadius = 0.585f;
        const float StarGlowCard = 1.6f;     // pass 5: outline-glow card size per unit star scale (star outer radius .625 of the card half)

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
                // S2 p1 v2: the right-wall stars (u > 1, 16:9 only) are clean outline tubes in the reference (purple wall
                // inside, tight glow): no orange fill card and a tighter glow (v1: hot filled blobs, star coverage 6.3 % vs 1.8 %)
                bool outlineOnly = s.x > 1f;
                // Screen ALL pass 5: outline-glow card CO-PLANAR with the tube star (same rotation, 1.6x = star r .625 of the card)
                AddGlow(s.color, pos, rot, StarGlowCard * scale);
                if (s.color == 0 && !outlineOnly) AddCard(Mat("M_StarFill_Yellow"), pos - toCam * (0.04f * scale), Quaternion.LookRotation(-toCam, upHint), StarMeshWidth * 1.15f * scale);
                heroCount++;
                Debug.Log($"[BWK] hero star c{s.color} screen ({s.x:F2},{s.y:F2}) track {wf.distance:F1} m depth {Vector3.Dot(pos - camPos, camFwd):F1} m scale {scale:F2}");
            }

            // ---- Screen S2 pass 3: the door frame (R2 camera = mascot at HeroMouthDistance; the gameplay rig sees the same
            // walls in hero_mouth): clean outline stars just inside the hatch at the reference f_03.00s spots, projected
            // through R2Cam onto the mouth drum (40.2-62 m). A ray that leaves the drum's front edge (hit before the door)
            // is nudged toward the vanishing point until it lands on the drum wall behind the hatch.
            {
                var r2 = R2Cam();
                float tV = r2.tanHalf, tH = r2.tanHalf * r2.aspect;
                var r2Fwd = r2.rot * Vector3.forward; var r2Up = r2.rot * Vector3.up; var r2Right = r2.rot * Vector3.right;
                int doorCount = 0;
                // Screen S2 pass 7 (owner 06:58 s7 + 26480 sheets: "clean hollow outline tubes, distinct under bloom"): the door
                // stars use the SLIM outline master SM_NeonStarTube_v2 (tube 6.5 % of r; reference door stars ~5 px tubes on
                // 70-75 px stars) with its 3.2x outline-glow card; the chubby SM_NeonStarTube (tube 17 % of r) read as filled
                // glowing shapes under the approved bloom
                var slimD = ModelParts("Lighting", "SM_NeonStarTube_v2");
                bool slimDoor = slimD.Count > 0;
                float dW = slimDoor ? 2.13f : StarMeshWidth, dR = slimDoor ? 1.065f : StarMeshRadius, dCard = slimDoor ? 3.2f : StarGlowCard;
                List<Part> RecolorD(Material mat) => slimDoor
                    ? slimD.Select(p => new Part(p.mesh, Enumerable.Repeat(mat, Mathf.Max(1, p.mesh.subMeshCount)).ToArray(), p.local)).ToList()
                    : Recolor(mat);
                foreach (var s in DoorStarLayout)
                {
                    float u = s.x, v = s.y, inset = 0.5f, scale = 1f; Vector3 pos = r2.pos; TrackFrame wf = default; bool ok = false;
                    for (int nudge = 0; nudge < 20; nudge++)
                    {
                        var dir = (r2.rot * new Vector3((2f * u - 1f) * tH, (1f - 2f * v) * tV, 1f)).normalized;
                        inset = 0.5f;
                        for (int it = 0; it < 3; it++)
                        {
                            ok = TunnelWallHit(r2.pos, dir, HeroMouthDistance - 2.75f, inset, out pos, out wf);
                            if (!ok) break;
                            float depth = Vector3.Dot(pos - r2.pos, r2Fwd);
                            scale = s.w * 2f * depth * tH / dW;
                            inset = 0.12f + dR * scale;
                        }
                        // p7: the hatch v2's violet torus rolls back into the drum within ~0.6 m of the door plane -> stars
                        // may sit from 40.8 m (p3: 41.2 m nudged the right yellow / pink 60-80 px off their reference spots)
                        if (ok && wf.distance > HallMouthD + 0.8f) break;
                        ok = false;
                        u = Mathf.Lerp(u, 0.58f, 0.05f); v = Mathf.Lerp(v, 0.40f, 0.05f);   // v3: finer steps (closer to the reference spot)
                    }
                    if (!ok) { Debug.LogWarning($"[BWK] door star at ({s.x}, {s.y}) found no drum wall behind the hatch"); continue; }
                    var toCam = (r2.pos - pos).normalized;
                    var inward = Vector3.ProjectOnPlane(wf.FlatPoint(0, TunnelCenter) - pos, wf.forward).normalized;
                    var facing = (toCam + inward * 0.35f).normalized;
                    scale /= Mathf.Lerp(1f, Mathf.Max(0.5f, Vector3.Dot(facing, toCam)), 0.5f);
                    float rr = s.roll * Mathf.Deg2Rad;
                    var upHint = Vector3.ProjectOnPlane(r2Up * Mathf.Cos(rr) + r2Right * Mathf.Sin(rr), facing).normalized;
                    var rot = Quaternion.LookRotation(facing, upHint);
                    comb.Add(RecolorD(mats[s.color]), Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                    // clean outline tubes with a tight halo (reference: purple wall visible inside every star, no filled blob)
                    AddGlow(s.color, pos, rot, dCard * scale);   // pass 5: co-planar outline glow (p7: slim master card 3.2x)
                    doorCount++;
                    Debug.Log($"[BWK] door star c{s.color} screen ({s.x:F3},{s.y:F3}) -> ({u:F3},{v:F3}) track {wf.distance:F1} m " +
                              $"depth {Vector3.Dot(pos - r2.pos, r2Fwd):F1} m scale {scale:F2}");
                }
                Debug.Log($"[BWK] door stars (S2 pass 3): {doorCount}");
            }

            // ---- Screen ALL pass 5 (judge gap #1): the BIG near-camera neon outline stars of the front sections S3-S6, measured
            // on the owner's frames at 720p and projected through the reference-matched front comparison cameras R3-R6
            // (CaptureTools R stills: runner at d, camera 2.6 m ahead / 1.3 up / 0.3 right, aimed at the mascot, then -2.9 /
            // +9.1 deg, vFOV 52, 16:9) onto the drum wall. Walls above the slide only (never in the lanes); the gameplay camera
            // sees the same 3D tubes from behind (double-sided outline halo cards).
            {
                int rCount = 0;
                // v3: the SLIM outline master SM_NeonStarTube_v2 (outer r 1.0, tube .065 = 6.5 % of r) - the chubby SM_NeonStarTube
                // (tube 17 % of r) read as a FILLED glowing shape at these near sizes (v2 R5 top yellow); its 3.2x card = r .625
                var slim = ModelParts("Lighting", "SM_NeonStarTube_v2");
                bool useSlim = slim.Count > 0;
                float rW = useSlim ? 2.13f : StarMeshWidth, rR = useSlim ? 1.065f : StarMeshRadius, rCard = useSlim ? 3.2f : StarGlowCard;
                List<Part> RecolorR(Material mat) => useSlim
                    ? slim.Select(p => new Part(p.mesh, Enumerable.Repeat(mat, Mathf.Max(1, p.mesh.subMeshCount)).ToArray(), p.local)).ToList()
                    : Recolor(mat);
                float tV = Mathf.Tan(26f * Mathf.Deg2Rad), tH = tV * 16f / 9f;
                foreach (var s in RStarLayout)
                {
                    var rf = track.Evaluate(s.d);
                    Vector3 rp = rf.position;
                    Vector3 cPos = rp + rf.forward * 2.6f + rf.flatUp * 1.3f + rf.flatRight * 0.3f;
                    var cRot = Quaternion.LookRotation(rp + rf.flatUp * 0.6f - cPos, rf.flatUp) * Quaternion.Euler(-2.9f, 9.1f, 0f);
                    var cFwd = cRot * Vector3.forward; var cUp = cRot * Vector3.up; var cRight = cRot * Vector3.right;
                    var dir = (cRot * new Vector3((2f * s.x - 1f) * tH, (1f - 2f * s.y) * tV, 1f)).normalized;
                    float inset = 0.5f, scale = 1f; Vector3 pos = cPos; TrackFrame wf = default; bool ok = false;
                    for (int it = 0; it < 3; it++)
                    {
                        ok = TunnelWallHit(cPos, dir, s.d + 2.6f, inset, out pos, out wf);
                        if (!ok) break;
                        float depth = Vector3.Dot(pos - cPos, cFwd);
                        scale = s.w * 2f * depth * tH / rW;
                        inset = 0.12f + rR * scale;
                    }
                    if (!ok) { Debug.LogWarning($"[BWK] R star d{s.d} ({s.x}, {s.y}) found no wall"); continue; }
                    float hUp = Vector3.Dot(pos - wf.position, wf.flatUp), lat = Mathf.Abs(Vector3.Dot(pos - wf.position, wf.flatRight));
                    if (hUp < 2.6f && !(lat > 3.0f && hUp > 1.2f))
                    { Debug.LogWarning($"[BWK] R star d{s.d} ({s.x}, {s.y}) too low (h {hUp:F1} lat {lat:F1}) - skipped"); continue; }
                    var toCam = (cPos - pos).normalized;
                    var inward = Vector3.ProjectOnPlane(wf.FlatPoint(0, TunnelCenter) - pos, wf.forward).normalized;
                    var facing = (toCam + inward * 0.35f).normalized;
                    scale /= Mathf.Lerp(1f, Mathf.Max(0.5f, Vector3.Dot(facing, toCam)), 0.5f);
                    float rr = s.roll * Mathf.Deg2Rad;
                    var upHint = Vector3.ProjectOnPlane(cUp * Mathf.Cos(rr) + cRight * Mathf.Sin(rr), facing).normalized;
                    var rot = Quaternion.LookRotation(facing, upHint);
                    comb.Add(RecolorR(mats[s.color]), Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                    AddGlow(s.color, pos, rot, rCard * scale);
                    rCount++;
                    Debug.Log($"[BWK] R star d{s.d} c{s.color} ({s.x:F2},{s.y:F2}) track {wf.distance:F1} m depth " +
                              $"{Vector3.Dot(pos - cPos, cFwd):F1} m scale {scale:F2} h {hUp:F1} lat {lat:F1}");
                }
                Debug.Log($"[BWK] front-section stars (pass 5): {rCount}");
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
            // Screen S2 pass 7 (owner 26480 sheets: the deep tunnel seen through the door = "clusters of FILLED FLOWER
            // shapes"; R2 lead_s2p6b showed 6 sparse stars at 65-90 m piled at (700-830, 195-280) around the vanishing point,
            // reference f_03.00s has only the small yellow (820, 205) + small pink (825, 250) there): the S2 door frame shows
            // only its designed DoorStarLayout, like the hero frame
            var r2v = R2Cam();
            float r2tV = r2v.tanHalf, r2tH = r2v.tanHalf * r2v.aspect;
            var r2Inv = Quaternion.Inverse(r2v.rot);
            bool InR2View(Vector3 p, float margin)
            {
                var c = r2Inv * (p - r2v.pos);
                if (c.z < 0.3f) return false;
                float u = 0.5f + 0.5f * c.x / (c.z * r2tH), v = 0.5f - 0.5f * c.y / (c.z * r2tV);
                return u > -margin && u < 1f + margin && v > -margin && v < 1f + margin;
            }
            int r2Skipped = 0;
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
                if (InR2View(pos, 0.04f)) { r2Skipped++; continue; }   // p7: so does the S2 door frame
                lastColor = ci;
                comb.Add(Recolor(mats[ci]), Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                // glow card ~2x the star size, just behind the tubes; tilted only half as much toward the camera as
                // the star so its soft far edge stays in front of the curved drum wall (no visible intersection)
                Vector3 gFacing = (-radial * 0.8f - f.forward * tilt * 0.45f).normalized;
                Vector3 gUp = Vector3.ProjectOnPlane(rot * Vector3.up, gFacing);
                if (gUp.sqrMagnitude < 1e-4f) gUp = Vector3.ProjectOnPlane(f.forward, gFacing);
                AddGlow(ci, pos, rot, StarGlowCard * scale);   // pass 5: co-planar outline glow (was a tilted radial card)
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
            Debug.Log($"[BWK] neon stars: {heroCount} hero-frame + {count} tunnel stars with glow cards ({r2Skipped} skipped in the S2 door frame)");
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

        /// <summary>
        /// Master 24 golden destination (masters wave 2026-11-26 17:56, owner: the portal starburst is "STILL too white").
        /// Runs at the start of BuildLighting, i.e. after BuildPortal / BuildPortalExtras in the full build AND in every
        /// agent preview (in memory), on the placed LightPortal:
        ///  - the Core disc (an opaque M_Bulb x5 annulus, r 1.18 m) WAS the hard cream-white "sun" of the r8 finale
        ///    (measured ~60 px radius, matches the disc): its renderer goes off; the starburst's own soft cream core takes over
        ///    (PortalGlow still swells the transform, harmless);
        ///  - SM_Starburst_r8 scale .55 -> .8 (owner sheet 03 / lead S7 proportion fix: the rays reach the bulb ring, R 3.56 m);
        ///  - its four additive layers use the lighting masters M_DestHaze / M_DestRays / M_DestCream / M_DestSparkle.
        /// Idempotent; does nothing when the portal or the r8 starburst is missing (r7 fallback keeps M_PortalBurst).
        /// </summary>
        static void TunePortalDestination(GameObject root)
        {
            try
            {
                var portal = root.transform.Find("Environment/LightPortal");
                if (portal == null) { Debug.LogWarning("[BWK] destination: LightPortal missing"); return; }
                var core = portal.Find("Core");
                if (core != null && core.TryGetComponent<MeshRenderer>(out var cr)) cr.enabled = false;
                var map = new Dictionary<string, Material>
                {
                    ["M_BurstRays_r8"] = Mat("M_DestRays"), ["M_BurstSparkle_r8"] = Mat("M_DestSparkle"),
                    ["M_BurstGlow_r8"] = Mat("M_DestHaze"), ["M_BurstCore_r8"] = Mat("M_DestCream"),
                };
                int n = 0;
                for (int i = 0; i < portal.childCount; i++)
                {
                    var c = portal.GetChild(i);
                    if (!c.name.StartsWith("SM_Starburst_r8")) continue;
                    c.localScale = Vector3.one * 0.8f;
                    foreach (var r in c.GetComponentsInChildren<Renderer>(true))
                    {
                        var mats = r.sharedMaterials;
                        for (int k = 0; k < mats.Length; k++)
                            if (mats[k] != null && map.TryGetValue(mats[k].name, out var rep) && rep != null) { mats[k] = rep; n++; }
                        r.sharedMaterials = mats;
                    }
                }
                // Screen ALL pass 5 (judge gap #6): the reference burst is full of glowing GOLD 5-point stars (+ a few pink ones)
                // between the cream centre and the bulb ring; ours showed rays only. Filled-star cards in the portal plane just in
                // front of the rays (local z ~1.0; bulb ring -0.35, rays 1.3), golden-angle spiral r 0.95-3.0 m (ring R ~3.56)
                var oldStars = portal.Find("DestStars");
                if (oldStars != null) Object.DestroyImmediate(oldStars.gameObject);
                var starRoot = new GameObject("DestStars").transform;
                starRoot.SetParent(portal, false);
                var quad = Resources.GetBuiltinResource<Mesh>("Quad.fbx");
                Material gold = Mat("M_DestStarGold"), pink = Mat("M_DestStarPink");
                var rnd = new System.Random(2414);
                int ns = 0;
                if (quad != null && gold != null)
                    for (int i = 0; i < 26; i++)
                    {
                        float t = (i + 0.5f) / 26f;
                        float rad = Mathf.Lerp(0.95f, 3.0f, Mathf.Sqrt(t));
                        float ang = (i * 137.508f + (float)rnd.NextDouble() * 20f) * Mathf.Deg2Rad;
                        bool isPink = i % 6 == 3;
                        float size = isPink ? Mathf.Lerp(0.80f, 1.15f, (float)rnd.NextDouble()) : Mathf.Lerp(0.60f, 1.25f, (float)rnd.NextDouble());   // v2: x2 (v1 12-27 px stars)
                        var go = new GameObject($"DestStar_{i:00}");
                        go.transform.SetParent(starRoot, false);
                        go.transform.localPosition = new Vector3(Mathf.Cos(ang) * rad, Mathf.Sin(ang) * rad, 1.0f - 0.01f * i);
                        go.transform.localRotation = Quaternion.Euler(0f, 0f, (float)rnd.NextDouble() * 50f - 25f);
                        go.transform.localScale = new Vector3(size, size, 1f);
                        go.AddComponent<MeshFilter>().sharedMesh = quad;
                        var mr = go.AddComponent<MeshRenderer>();
                        mr.sharedMaterial = isPink && pink != null ? pink : gold;
                        mr.shadowCastingMode = ShadowCastingMode.Off; mr.receiveShadows = false;
                        ns++;
                    }
                Debug.Log($"[BWK] destination: core disc off, starburst x0.8, {n} glow slots on the M_Dest* masters, {ns} star cards");
            }
            catch (System.Exception e) { Debug.LogWarning($"[BWK] destination tune failed: {e.Message}"); }
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

        /// <summary>Owner 2026-11-27: the approved video look grade (Color Lookup + softer bloom) is ON; set false and run a
        /// full build to get the previous rendering settings back exactly (they stay in code next to the new ones).</summary>
        public static readonly bool VideoLookGrade = true;   // readonly (not const): both branches stay compiled, no warnings

        /// <summary>Owner-approved video look LUT (2026-11-27 05:28): 1024 x 32 URP strip from Tools/look_lut.py. No reference
        /// pixels, only a colour mapping, so it is tracked like any other texture.</summary>
        public const string VideoLookLutPath = "Assets/BubbleWashKingdom/Art/Textures/Post/LUT_VideoLook_p4.png";

        /// <summary>Loads the LUT with the import settings URP Color Lookup needs (linear data, no mips, clamp, uncompressed).</summary>
        static Texture2D LoadVideoLookLut()
        {
            if (!File.Exists(VideoLookLutPath)) return null;
            AssetDatabase.ImportAsset(VideoLookLutPath);
            if (AssetImporter.GetAtPath(VideoLookLutPath) is TextureImporter ti &&
                (ti.sRGBTexture || ti.mipmapEnabled || ti.wrapMode != TextureWrapMode.Clamp || ti.filterMode != FilterMode.Bilinear ||
                 ti.textureCompression != TextureImporterCompression.Uncompressed || ti.npotScale != TextureImporterNPOTScale.None))
            {
                ti.textureType = TextureImporterType.Default;
                ti.sRGBTexture = false; ti.mipmapEnabled = false; ti.wrapMode = TextureWrapMode.Clamp; ti.filterMode = FilterMode.Bilinear;
                ti.textureCompression = TextureImporterCompression.Uncompressed; ti.npotScale = TextureImporterNPOTScale.None;
                ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(VideoLookLutPath);
        }
    }
}
