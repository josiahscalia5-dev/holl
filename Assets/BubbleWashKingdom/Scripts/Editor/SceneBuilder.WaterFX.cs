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
    public static partial class SceneBuilder
    {
        static void BuildFoam(GameObject env, float L)
        {
            // LOD0 = smooth sphere clusters near the camera, LOD1 = low-poly twins for distant chunks (same placement)
            string[] names = { "SM_Foam_A", "SM_Foam_B", "SM_Foam_C" };
            var lod0 = names.Select(n => ModelParts("Props", n)).Where(v => v.Count > 0).ToArray();
            var lod1 = names.Select(n => { var p = ModelParts("Props", n + "_LOD1"); return p.Count > 0 ? p : ModelParts("Props", n); }).Where(v => v.Count > 0).ToArray();
            if (lod0.Length == 0)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                var sm = s.GetComponent<MeshFilter>().sharedMesh;
                Object.DestroyImmediate(s);
                lod0 = lod1 = new[] { new List<Part> { new Part(sm, new[] { Mat("M_Foam") }, Matrix4x4.Scale(new Vector3(1.6f, 0.9f, 1.2f))) } };
            }
            var holder = Child(env, "Foam");
            var comb0 = new Combiner();
            var comb1 = new Combiner();
            int chunk = 0; float chunkStart = 0f;
            void FlushChunk()
            {
                var go = Child(holder, $"Foam_{chunk:00}");
                var r0 = comb0.Flush(go, $"Foam_{chunk:00}_LOD0", false);
                var r1 = comb1.Flush(go, $"Foam_{chunk:00}_LOD1", false);
                var lg = go.AddComponent<LODGroup>();
                lg.SetLODs(new[] { new LOD(0.45f, r0.ToArray()), new LOD(0.01f, r1.ToArray()) });
                lg.RecalculateBounds();
                chunk++;
            }
            for (float d = 0f; d < L; d += (d < tunnelStart ? 2.0f : 2.3f))
            {
                var f = track.Evaluate(d);
                bool hall = d < tunnelStart;
                foreach (int side in new[] { -1, 1 })
                {
                    // reference: continuous puffy foam banks right outside both rails (front row) + a taller back row
                    for (int c = 0; c < 2; c++)
                    {
                        float lat = side * (hall ? (c == 0 ? Mathf.Lerp(2.45f, 3.0f, (float)rng.NextDouble()) : Mathf.Lerp(3.2f, 7.5f, (float)rng.NextDouble()))
                                                 : (c == 0 ? Mathf.Lerp(2.4f, 2.75f, (float)rng.NextDouble()) : Mathf.Lerp(2.95f, 3.35f, (float)rng.NextDouble())));
                        float h = hall ? Mathf.Lerp(-0.6f, 0.1f, (float)rng.NextDouble()) : (c == 0 ? Mathf.Lerp(-0.2f, 0.12f, (float)rng.NextDouble()) : Mathf.Lerp(-0.15f, 0.35f, (float)rng.NextDouble()));
                        float sc = hall ? Mathf.Lerp(0.85f, 1.6f, (float)rng.NextDouble()) : (c == 0 ? Mathf.Lerp(0.7f, 1.05f, (float)rng.NextDouble()) : Mathf.Lerp(0.9f, 1.35f, (float)rng.NextDouble()));
                        int vi = rng.Next(lod0.Length);
                        // clusters are long along asset X: turn them to run along the track so they never cover the water
                        var rot = f.FlatRotation * Quaternion.Euler(0, 90f + Mathf.Lerp(-22f, 22f, (float)rng.NextDouble()) + (rng.NextDouble() < 0.5 ? 180f : 0f), 0);
                        var m = Matrix4x4.TRS(f.FlatPoint(lat, h), rot, Vector3.one * sc);
                        comb0.Add(lod0[vi], m);
                        comb1.Add(lod1[Mathf.Min(vi, lod1.Length - 1)], m);
                    }
                }
                if (d - chunkStart > ChunkLength) { FlushChunk(); chunkStart = d; }
            }
            FlushChunk();
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

        static SplashFX BuildRunnerFX(GameObject runnerGo, RunnerController runner, TrackItemRegistry registry)
        {
            var fxRoot = Child(runnerGo, "FX");
            var fx = fxRoot.AddComponent<SplashFX>();
            fx.runner = runner;
            fx.items = registry;
            // droplets thrown up and back around the feet (velocity-stretched milky drops)
            fx.spray = Particles(fxRoot, "Spray", "M_FX_Splash", new Vector3(0, 0.05f, 0.18f), new Vector3(-120, 0, 0), ps =>
            {
                var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.25f, 0.45f); m.startSpeed = new ParticleSystem.MinMaxCurve(2.0f, 3.6f);
                m.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.13f); m.gravityModifier = 1.5f; m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 160;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 55f; sh.radius = 0.45f;
                var e = ps.emission; e.rateOverTime = 0f;
                var r = ps.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.035f; r.lengthScale = 1.3f;
            });
            // milky crown splash sheets flanking the mascot, like the reference's white splash shapes
            ParticleSystem Sheet(string n, float side)
            {
                return Particles(fxRoot, n, "M_FX_SplashSheet", new Vector3(side * 0.44f, 0.26f, 0.06f), new Vector3(-74, side * 48f, 0), ps =>
                {
                    var m = ps.main; m.startLifetime = new ParticleSystem.MinMaxCurve(0.2f, 0.34f); m.startSpeed = new ParticleSystem.MinMaxCurve(0.4f, 1.1f);
                    m.startSize = new ParticleSystem.MinMaxCurve(0.7f, 1.05f); m.simulationSpace = ParticleSystemSimulationSpace.Local; m.maxParticles = 16;
                    m.startRotation = new ParticleSystem.MinMaxCurve(-0.25f, 0.25f); m.gravityModifier = 0.4f;
                    var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 20f; sh.radius = 0.12f;
                    var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.EaseInOut(0, 0.55f, 1, 1.15f));
                    var col = ps.colorOverLifetime; col.enabled = true;
                    var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
                                                      new[] { new GradientAlphaKey(1f, 0), new GradientAlphaKey(1f, 0.78f), new GradientAlphaKey(0f, 1) });
                    col.color = g;
                    var e = ps.emission; e.rateOverTime = 0f;
                    var r = ps.GetComponent<ParticleSystemRenderer>(); r.flip = new Vector3(0.5f, 0f, 0f); r.sortingFudge = -1f;
                });
            }
            fx.sheets = new[] { Sheet("SplashSheetL", -1f), Sheet("SplashSheetR", 1f) };
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

        static void BuildDecorChevrons(GameObject env, float L)
        {
            var chevron = ModelParts("Props", "SM_Chevron");
            if (chevron.Count == 0) return;
            var holder = Child(env, "DecorChevrons");
            var comb = new Combiner();
            int chunk = 0; float chunkStart = 0;
            for (float d = 6f; d < L - 6f; d += 2.4f)
            {
                var f = track.Evaluate(d);
                comb.Add(chevron, Matrix4x4.TRS(f.Point(0, 0.03f), f.Rotation, new Vector3(0.85f, 1f, 0.85f)));
                if (d - chunkStart > ChunkLength) { comb.Flush(holder, $"Chevrons_{chunk++:00}", false); chunkStart = d; }
            }
            comb.Flush(holder, $"Chevrons_{chunk:00}", false);
        }
    }
}
