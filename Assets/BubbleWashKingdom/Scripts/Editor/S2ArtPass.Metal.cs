using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Unity.Cinemachine;
using Unity.Collections;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// bp_A METAL + ARCHITECTURE (owner 2026-11-28 06:00 annotated blueprint): P1.3 massive gold hatch, P2.1 thick outer rim,
    /// P2.2 recessed drum holes, P2.3 blue-violet metal (alternating blue / purple), P2.4 layered inner rings, P4.3 perforated
    /// wall, P6.4 blue-violet surroundings, the P6.3 portal ring. Runs AFTER the lead's base steps (glow / depth / walls) and
    /// edits only the in-memory CLONES (Swap) + per-renderer mesh copies; .mat assets and the main scene are never written.
    /// Measured before (art06_base, R2 bg vs ORIGINAL 3.00 s): drum walls S .35 vs .44-.57 (the walls step's pale #E6C8FF
    /// grazing sheen x .32 = a lavender veil over the whole tunnel), deep tunnel S3-S7 hue 271-307 (magenta) vs 235-252
    /// (blue-violet), violet bands = same pale lavender as the wall (invisible as arches), gold S .49 / V90 .83 vs .58 / .94.
    /// </summary>
    public static partial class S2ArtPass
    {
        /// <summary>Intermediate R2 (mascot hidden) + one portrait rig render after a metal step (bp_A judges each step).</summary>
        static void MetalMid(Ctx c, string tag)
        {
            if (Arg("-bwkMetalMid") == "0") return;
            string vd = $"{c.outDir}/metal_mid_{tag}";
            Directory.CreateDirectory(vd);
            S2v1TestScene.PoseR2(c.runner, c.cam);
            var was = c.mascot.Select(r => r.enabled).ToArray();
            foreach (var r in c.mascot) r.enabled = false;
            CaptureTools.Render(c.cam, 1280, 720, $"{vd}/R2_bg_16x9.png");
            for (int i = 0; i < c.mascot.Count; i++) c.mascot[i].enabled = was[i];
            S2v1TestScene.PoseRig(c.runner, c.cam, 38.5f, 720f / 1280f);
            CaptureTools.Render(c.cam, 720, 1280, $"{vd}/rig_d38.5_9x16.png");
            c.log.AppendLine($"  metal mid render {vd}");
        }

        // ------------------------------------------------------------------------------------------------ P2.2 P2.3 P4.3 P6.4
        [ArtStep("metal_walls")]
        static void MetalWalls(Ctx c)
        {
            Swap("metal drum walls", m => Named(m, "M_DrumWall"), m =>
            {
                // pale veil off: grazing sheen back to a trace, saturated violet instead of pale lilac; fewer glitter dots
                F(m, "_SheenStrength", 0.07f); C(m, "_SheenColor", "#B266FF"); F(m, "_Sparkle", 0.3f);
                // ORIGINAL 3.00 s: violet near drum, COBALT blue section behind the first band (P2.3 arrow), glossy cyan-blue
                // band on the blue ceiling ("colorful reflections"), lavender-violet gloss; body stops kept under the bloom knee
                // bp_A_1 -> 2: the scene's warm bloom veil lifts R / G (hole bottoms #6c4a67 vs ORIGINAL #432a68), so the body is
                // pushed purple on the side walls (ORIGINAL #9161ad vs ours #7d63b2: +R -B) and low-green cobalt on the ceiling
                C(m, "_DoorRampMid", "#7E3CC0"); C(m, "_DoorRampCeil", "#2A28C6"); C(m, "_DoorRampHigh", "#B070E8");
                C(m, "_DoorRampDark", "#0E0A44");
                F(m, "_DoorRampCap", 0.70f); F(m, "_DoorRampDeepBlue", 0.95f); F(m, "_DoorRampFar", 0.85f);
                F(m, "_DoorRampNear", 12f); F(m, "_DoorRampFarDist", 17f);   // cobalt from just behind the first violet band
                C(m, "_BaySheenColor", "#4466FF"); F(m, "_BaySheen", 0.15f);
                // P2.2: darker recesses, curved pressed panels a little deeper (soft sheen band per panel, value step at seams)
                F(m, "_DoorHole", 0.10f); F(m, "_DoorPanelCurve", 0.30f);
                // ORIGINAL ceiling = short dark dashes in BROKEN rows with plain metal between (ours: a dense even grille)
                F(m, "_SlotDropout", 0.30f);
                // colourful reflections: warmer gold / pinker rim pickup in the polished door drum, a little wider
                C(m, "_MirrorGold", "#A8561A"); C(m, "_MirrorRim", "#A82AA0"); F(m, "_MirrorF0", 0.42f); F(m, "_MirrorRingWidth", 0.40f);
                C(m, "_PinkSpill", "#D050FF");
                // P4.3 / P6.4 deep tunnel (S3-S7, graded from 68 m): magenta-mauve -> slate blue-violet metal (ORIGINAL 7.5 s
                // #514580 hue 252, 14 s #4b508a hue 235), black elongated holes, dark seams, less pink emission
                // (bp_A_1 .62 / #B8BDFF / #99A8EB: hue 287-307 -> 271-285; bp_A_2 .74 / #A2A8FF / #8E9EF0: 262-290 - the rest is the pink rail bloom veil)
                C(m, "_LitTint", "#9AA4FF"); F(m, "_LitDesat", 0.80f);
                C(m, "_DeepTint", "#8898F2"); F(m, "_DeepHole", 0.12f); F(m, "_DeepEmit", 0.35f);
                C(m, "_SeamColor", "#0A0620");
            }, c.log);
            // the dark recessed violet band seen through the gap between the hatch and the mouth drum (ORIGINAL: #3A2A80 groove)
            // - the walls step had made it the pale drum colour
            Swap("metal dark bulkhead", m => Named(m, "M_DrumWallFlat"), m =>
            {
                C(m, "_BaseColor", "#34226E"); C(m, "_HighlightColor", "#58449A"); F(m, "_SheenStrength", 0.05f);
                C(m, "_SheenColor", "#9A5CFF"); F(m, "_Sparkle", 0f); F(m, "_BaySheen", 0f); F(m, "_Glow", 0.03f);
            }, c.log);
            MetalMouthBand(c);
            MetalMid(c, "walls");
        }

        /// <summary>P2.4 / P2.3: the ORIGINAL 3.00 s shows a thick glossy VIOLET band with pink lights between the hatch and the
        /// gold bulb ring (R2 x ~517-555 on the left), the cobalt-blue drum section behind it. SceneBuilder.Hall places
        /// SM_LedRim_s2 there ("MouthLedRim_s2", 46 m, lead lane 2b L4) but the saved scene predates it: the same existing
        /// band master is placed in memory exactly as the builder does (track frame at HallMouthD + 6, tunnel centre 2.3 m,
        /// renderers only, inner apex 3.655 m = clear of the rails, mascot and camera).</summary>
        static void MetalMouthBand(Ctx c)
        {
            var all = Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            if (all.Any(t => t.name.StartsWith("MouthLedRim_s2"))) { c.log.AppendLine("  metal mouth band: already in the scene"); return; }
            var src = all.FirstOrDefault(t => t.name == "LedRim_s2");
            var tp = Object.FindFirstObjectByType<TrackPath>();
            if (src == null || tp == null) { c.log.AppendLine("  metal mouth band: no LedRim_s2 / TrackPath - skipped"); return; }
            var go = Object.Instantiate(src.gameObject, src.parent);
            go.name = "MouthLedRim_s2art";
            const float tunnelCenter = 2.3f;   // SceneBuilder.TunnelCenter
            var f = tp.Evaluate(SceneBuilder.HallMouthD + 6f);
            go.transform.SetPositionAndRotation(f.FlatPoint(0f, tunnelCenter), f.FlatRotation);
            go.transform.localScale = src.localScale;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true)) r.shadowCastingMode = ShadowCastingMode.Off;
            foreach (var lg in go.GetComponentsInChildren<LODGroup>(true)) lg.RecalculateBounds();
            foreach (var col in go.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(col);
            c.log.AppendLine(string.Format(IC, "  metal mouth band: {0} copied to {1:0.0} m ({2} renderers) at {3}", src.name,
                SceneBuilder.HallMouthD + 6f, go.GetComponentsInChildren<Renderer>(true).Length, go.transform.position));
        }

        // ------------------------------------------------------------------------------------------------ P2.3 P2.4 (bands)
        [ArtStep("metal_bands")]
        static void MetalBands(Ctx c)
        {
            // violet arches (SM_LedRim_s2 band faces + the hatch's violet rim): saturated purple lacquer with magenta edges
            // instead of the pale lavender that matched the wall; no square object-space sparkle cells (read as noise)
            Swap("metal violet bands", m => Named(m, "M_HatchViolet_s2"), m =>
            {
                C(m, "_MidColor", "#7434D6"); C(m, "_LowColor", "#1E0A52"); C(m, "_HighColor", "#C68CFF");
                C(m, "_BandColor", "#9A5CEB"); C(m, "_RimColor", "#F055D8");
                F(m, "_EnvReflect", 0.22f); F(m, "_EnvTint", 0.8f); F(m, "_Sparkle", 0f); F(m, "_Contrast", 1.9f);
                F(m, "_StreakStrength", 0.45f);
                // bp_A_1: the arches still read close to the wall -> self-lit violet lacquer, less fog on the deeper ones
                F(m, "_Brightness", 1.1f); F(m, "_Emission", 0.2f); F(m, "_FogAmount", 0.3f);
            }, c.log);
            Swap("metal hatch crest", m => Named(m, "M_HatchCrest_s2"), m =>
            {
                C(m, "_HighColor", "#EBC4FF"); C(m, "_MidColor", "#A872F0"); C(m, "_RimColor", "#E070E8"); F(m, "_Emission", 0.15f);
            }, c.log);
            // band lips: pink-magenta glow (never pale white hoops); the far hoops fade into the violet depth
            Swap("metal band lips", m => Named(m, "M_RimGlow_s2"), m =>
            {
                // bp_A_1 (1.9): eight crisp magenta hoops -> softer, the band body carries the arch
                C(m, "_Color", "#FF46D2"); F(m, "_Intensity", 1.4f); F(m, "_CoreWhite", 0f); F(m, "_EdgeSaturate", 1f);
                F(m, "_HaloBoost", 1.0f); F(m, "_FogAmount", 1f);
            }, c.log);
            Swap("metal band glints", m => Named(m, "M_RimSpark_s2"), m =>
            {
                C(m, "_Color", "#FF4CC8"); F(m, "_Intensity", 1.0f); F(m, "_CoreWhite", 0f); F(m, "_EdgeSaturate", 1f); F(m, "_FogAmount", 1f);
            }, c.log);
            // far-end lavender haze over the ring zone (R2 ring zone >.9 bright 27 % vs ORIGINAL 12.5 %)
            Swap("metal vanish glow", m => Named(m, "M_VanishGlow"), m => { Mul(m, "_Strength", 0.6f); }, c.log);
            // the first band inside the hatch (ORIGINAL: bright pink-white LED dots + a pink glowing lip along the violet band)
            // keeps strong lights; the deeper bands stay subtle (per-renderer variants of the edited clones)
            var mouth = Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .FirstOrDefault(t => t.name.StartsWith("MouthLedRim_s2"));
            if (mouth != null)
            {
                Material lipV = null, sparkV = null;
                int n = 0;
                foreach (var r in mouth.GetComponentsInChildren<Renderer>(true))
                {
                    var mats = r.sharedMaterials;
                    for (int i = 0; i < mats.Length; i++)
                    {
                        if (mats[i] == null) continue;
                        var src = srcOf.TryGetValue(mats[i], out var s0) ? s0 : mats[i];
                        if (src.name == "M_RimGlow_s2")
                        {
                            if (lipV == null) { lipV = new Material(mats[i]) { name = "M_RimGlow_s2_mouth" }; F(lipV, "_Intensity", 2.3f); F(lipV, "_FogAmount", 0.4f); }
                            mats[i] = lipV; n++;
                        }
                        else if (src.name == "M_RimSpark_s2")
                        {
                            if (sparkV == null)
                            {
                                sparkV = new Material(mats[i]) { name = "M_RimSpark_s2_mouth" };
                                C(sparkV, "_Color", "#FF6CD6"); F(sparkV, "_Intensity", 2.4f); F(sparkV, "_CoreWhite", 0.35f); F(sparkV, "_FogAmount", 0.4f);
                            }
                            mats[i] = sparkV; n++;
                        }
                    }
                    r.sharedMaterials = mats;
                }
                c.log.AppendLine($"  metal mouth band lights: {n} slots (bright pink lip + LED dots)");
            }
            Swap("metal rim leds", m => Named(m, "M_RimLight"), m => { F(m, "_FogAmount", 0.6f); }, c.log);
            // S3-S7 drum lips (BWK/Gold violet): no square sparkle cells, deeper violet body
            Swap("metal drum lips", m => Named(m, "M_DrumRim"), m =>
            {
                F(m, "_Sparkle", 0f); C(m, "_MidColor", "#6A44CC"); C(m, "_HighColor", "#E2A6FF"); C(m, "_BandColor", "#B88CF0");
                F(m, "_EnvReflect", 0.28f);
            }, c.log);
            MetalMid(c, "bands");
        }

        // ------------------------------------------------------------------------------------------------ P1.3 P2.1 P2.4 P6.3 gold
        [ArtStep("metal_gold")]
        static void MetalGold(Ctx c)
        {
            // ORIGINAL hatch band #cd9657 S .58 V90 .94 vs ours #c69764 S .49 V90 .83: richer amber body, brighter broad
            // highlight streaks, darker rolled edges (contrast), less lavender probe / violet fog washing it to tan
            Swap("metal gold", m => Named(m, "M_Gold"), m =>
            {
                C(m, "_MidColor", "#EB9A2C"); C(m, "_BandColor", "#FFC456"); C(m, "_HighColor", "#FFF0B0");
                F(m, "_EnvReflect", 0.26f); F(m, "_StreakStrength", 1.55f); F(m, "_HighlightSize", 8.5f); F(m, "_Contrast", 2.4f);
                F(m, "_FogAmount", 0.3f);
            }, c.log);
            Swap("metal gold dark", m => Named(m, "M_GoldDark"), m => { C(m, "_MidColor", "#D2862A"); F(m, "_EnvReflect", 0.35f); }, c.log);
            MetalMid(c, "gold");
        }

        // ------------------------------------------------------------------------------------------------ P1.3 P2.1 lamps
        /// <summary>ORIGINAL 0.50 / 3.00 s: the hatch's warm lamps are ~45 % of the gold band width (ours 27 %). Selective mesh
        /// change on copies of the hatch LODs (and the portal ring, P6.3): every lamp assembly (M_Bulb dome + its socket /
        /// collar parts) is scaled about its own lamp centre; the rest of the mesh is untouched.</summary>
        [ArtStep("metal_lamps")]
        static void MetalLamps(Ctx c)
        {
            int done = 0;
            foreach (var mf in Object.FindObjectsByType<MeshFilter>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                if (mf.sharedMesh == null) continue;
                float k = 0f;
                if (mf.name.StartsWith("DoorHatch_LOD")) k = 1.45f;
                else if (mf.GetComponentInParent<PortalGlow>(true) != null) k = 1.3f;   // portal bulb rings (P6.3)
                if (k <= 0f) continue;
                var r = mf.GetComponent<MeshRenderer>();
                if (r == null) continue;
                if (MetalScaleLamps(mf, r, k, c.log)) done++;
            }
            c.log.AppendLine($"  metal lamps: {done} meshes with bigger lamp assemblies");
        }

        static bool MetalScaleLamps(MeshFilter mf, MeshRenderer r, float k, StringBuilder log)
        {
            var src = mf.sharedMesh;
            var mats = r.sharedMaterials;
            int bulbSub = -1;
            for (int i = 0; i < mats.Length && i < src.subMeshCount; i++)
                if (mats[i] != null && (srcOf.TryGetValue(mats[i], out var s0) ? s0 : mats[i]).name.StartsWith("M_Bulb")) bulbSub = i;
            if (bulbSub < 0) return false;
            Mesh m;
            Vector3[] v;
            try { m = Object.Instantiate(src); v = m.vertices; }
            catch (System.Exception e) { log.AppendLine($"  metal lamps {mf.name}: mesh not readable ({e.Message}) - skipped"); return false; }
            // lamp centres: greedy spatial clusters of the bulb submesh vertices (lamps are >= 1.7 m apart, r <= .26 m)
            var bulbIdx = m.GetIndices(bulbSub).Distinct().ToArray();
            var seeds = new List<Vector3>();
            var lo = new List<Vector3>();
            var hi = new List<Vector3>();
            foreach (int vi in bulbIdx)
            {
                var p = v[vi];
                int ci = -1;
                for (int s = 0; s < seeds.Count; s++) if ((p - seeds[s]).sqrMagnitude < 0.6f * 0.6f) { ci = s; break; }
                if (ci < 0) { seeds.Add(p); lo.Add(p); hi.Add(p); continue; }
                lo[ci] = Vector3.Min(lo[ci], p); hi[ci] = Vector3.Max(hi[ci], p);
            }
            var centres = Enumerable.Range(0, seeds.Count).Select(s => (lo[s] + hi[s]) * 0.5f).ToList();
            if (centres.Count < 8 || centres.Count > 48)
            {
                log.AppendLine($"  metal lamps {mf.name}: {centres.Count} lamp clusters (expected 16-24) - skipped");
                Object.DestroyImmediate(m);
                return false;
            }
            float lampR = Enumerable.Range(0, seeds.Count).Average(s => (hi[s] - lo[s]).magnitude) * 0.5f;
            // small connected parts (bulb domes, sockets, collars) whose box centre sits near a lamp centre -> scale about it
            int[] parent = Enumerable.Range(0, v.Length).ToArray();
            int Find(int a) { while (parent[a] != a) { parent[a] = parent[parent[a]]; a = parent[a]; } return a; }
            for (int sm = 0; sm < m.subMeshCount; sm++)
            {
                if (m.GetTopology(sm) != MeshTopology.Triangles) continue;
                var t = m.GetIndices(sm);
                for (int i = 0; i + 2 < t.Length; i += 3)
                {
                    int a = Find(t[i]), b = Find(t[i + 1]), cc = Find(t[i + 2]);
                    if (a != b) parent[b] = a;
                    cc = Find(cc); a = Find(a);
                    if (a != cc) parent[cc] = a;
                }
            }
            var cLo = new Dictionary<int, Vector3>();
            var cHi = new Dictionary<int, Vector3>();
            for (int i = 0; i < v.Length; i++)
            {
                int root = Find(i);
                if (!cLo.ContainsKey(root)) { cLo[root] = v[i]; cHi[root] = v[i]; }
                else { cLo[root] = Vector3.Min(cLo[root], v[i]); cHi[root] = Vector3.Max(cHi[root], v[i]); }
            }
            float near = Mathf.Max(0.3f, lampR * 1.6f), maxSize = Mathf.Max(0.9f, lampR * 4.5f);
            var pivotOf = new Dictionary<int, int>();
            foreach (var root in cLo.Keys)
            {
                var size = (cHi[root] - cLo[root]).magnitude;
                if (size > maxSize) continue;
                var cen = (cLo[root] + cHi[root]) * 0.5f;
                int best = -1; float bd = near * near;
                for (int s = 0; s < centres.Count; s++) { float d = (cen - centres[s]).sqrMagnitude; if (d < bd) { bd = d; best = s; } }
                if (best >= 0) pivotOf[root] = best;
            }
            // bp_A_1 moved 960 parts on LOD0 (expected ~5 per lamp): keep only parts that lie ENTIRELY inside the lamp's
            // neighbourhood and are either bulb-slot parts or real sub-objects (>= 12 verts: sockets, collars), so no split
            // face strip of the gold band / flange near a lamp can ever be pulled out of the surface
            var compSub = new Dictionary<int, int>();
            for (int sm = 0; sm < m.subMeshCount; sm++)
                foreach (int ix in m.GetIndices(sm)) { int rt = Find(ix); if (!compSub.ContainsKey(rt)) compSub[rt] = sm; }
            var vcount = new Dictionary<int, int>();
            var reach = new Dictionary<int, float>();
            for (int i = 0; i < v.Length; i++)
            {
                int rt = Find(i);
                if (!pivotOf.TryGetValue(rt, out int s0)) continue;
                vcount[rt] = vcount.TryGetValue(rt, out int n0) ? n0 + 1 : 1;
                float d = (v[i] - centres[s0]).magnitude;
                reach[rt] = reach.TryGetValue(rt, out float r0) ? Mathf.Max(r0, d) : d;
            }
            var subParts = new int[m.subMeshCount];
            foreach (var rt in pivotOf.Keys.ToList())
            {
                int sub = compSub.TryGetValue(rt, out int sb) ? sb : -1;
                bool ok = reach[rt] <= lampR * 1.6f && (sub == bulbSub || vcount[rt] >= 12);
                if (!ok) pivotOf.Remove(rt);
                else if (sub >= 0) subParts[sub]++;
            }
            int moved = 0;
            for (int i = 0; i < v.Length; i++)
                if (pivotOf.TryGetValue(Find(i), out int s)) { v[i] = centres[s] + (v[i] - centres[s]) * k; moved++; }
            if (moved == 0) { Object.DestroyImmediate(m); return false; }
            log.AppendLine($"  metal lamps {mf.name}: parts per slot [{string.Join(", ", Enumerable.Range(0, subParts.Length).Select(i => (i < mats.Length && mats[i] ? mats[i].name : "-") + " " + subParts[i]))}]");
            m.vertices = v;
            m.RecalculateBounds();
            m.name = src.name + "_lampsx" + k.ToString("0.00", IC);
            mf.sharedMesh = m;
            newMeshes.Add(m);
            var lg = mf.GetComponentInParent<LODGroup>();
            if (lg != null) lg.RecalculateBounds();
            log.AppendLine(string.Format(IC, "  metal lamps {0}: {1} lamps (r {2:0.00} m, centre rho ~{3:0.00}) x{4} -> {5} parts, {6} verts moved",
                mf.name, centres.Count, lampR, centres.Average(p => new Vector2(p.x, p.z).magnitude), k, pivotOf.Count, moved));
            return true;
        }
    }
}
