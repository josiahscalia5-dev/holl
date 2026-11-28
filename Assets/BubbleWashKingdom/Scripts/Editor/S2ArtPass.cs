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
    /// Lead 470ca906 2026-11-27 - S2 ART PASS on the EXISTING Unity scene (owner 23:36 "noticeable artistic transformation, not tiny
    /// technical adjustments"; 23:33 "transform my existing Unity scene ... no reconstruction"; 23:11 "artistic production first").
    /// Opens the saved S2 scene IN MEMORY with the same setup as the 'Unity current' R2 baseline (TextureGenerator + MaterialLibrary +
    /// PreviewRefreshDomains), renders it, then applies the art steps CUMULATIVELY and renders after each one:
    ///   splash = new milk crowns (Tools/Blender/scripts/build_fx_splash_art.py: metaball milk crowns with branching fingers, bulb tips,
    ///            wake tendrils, splats, beads + clear bubbles, 6 frames per side) on the game's own SplashCrowns flipbook, creamy milk
    ///   glow   = brighter bulbs / neon stars with wider soft bloom halos (lighting artist's Unity mapping: emitters up, threshold 1.0)
    ///   depth  = deeper violet atmospheric fog (lighting artist: #6A44A8) + calmer, lavender deep rims instead of white hoops
    ///   roller = the door roller (top-left of S2) bright fluffy pink instead of a dark magenta block
    /// Shared .mat assets are NEVER edited: every change goes onto in-memory CLONES assigned to the scene's renderers, so the game
    /// keeps its materials; the main scene is never saved. -bwkSave 1 writes the PROTECTED test scene (S2v1TestScene.TestScenePath,
    /// gitignored) with the clones / meshes / post profile persisted in Art/S2v1Test/Art/ (gitignored).
    /// Batch (heavy, through the lock):
    ///   Tools/unity_run.sh BubbleWash.EditorTools.S2ArtPass.PreviewBatch lead_s2art -bwkOut Captures/s2art/NAME
    ///     [-bwkSteps "splash,glow,depth,roller"] [-bwkSplash Tools/Blender/work/s2art/splash] [-bwkDists 33.5,38.5,44] [-bwkSave 1]
    /// Writes DIR/current/... and DIR/art_&lt;steps so far&gt;/R2_16x9.png, R2_bg_16x9.png, rig_dXX.X_9x16.png (Tools/s2v1_unity_sheet.py
    /// makes the labelled owner sheets) + DIR/summary.txt (incl. what sits under key R2 pixels).
    /// </summary>
    public static class S2ArtPass
    {
        const string AssetDir = "Assets/BubbleWashKingdom/Art/S2v1Test/Art";
        static readonly CultureInfo IC = CultureInfo.InvariantCulture;

        static string Arg(string key)
        {
            var a = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == key) return a[i + 1];
            return null;
        }

        [System.Serializable] class SplashMan { public int frames; public float[] pivot_L, pivot_R; public string[] L, R; }

        // ------------------------------------------------------------------------------------------- material clones (never the assets)
        static readonly Dictionary<Material, Material> cloneOf = new Dictionary<Material, Material>();
        static readonly Dictionary<Material, Material> srcOf = new Dictionary<Material, Material>();
        static readonly List<Mesh> newMeshes = new List<Mesh>();

        static void C(Material m, string p, string hex) { if (m.HasProperty(p) && ColorUtility.TryParseHtmlString(hex, out var c)) m.SetColor(p, c); }
        static void F(Material m, string p, float v) { if (m.HasProperty(p)) m.SetFloat(p, v); }
        static void Mul(Material m, string p, float k) { if (m.HasProperty(p)) m.SetFloat(p, m.GetFloat(p) * k); }

        /// <summary>Replace every scene use of a material matching <paramref name="match"/> (by its SOURCE asset) with one clone
        /// per source; <paramref name="edit"/> runs once per clone per call. Returns the number of slots changed.</summary>
        static int Swap(string what, System.Func<Material, bool> match, System.Action<Material> edit, StringBuilder log)
        {
            int slots = 0;
            var edited = new HashSet<Material>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                var mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    var m = mats[i];
                    if (m == null) continue;
                    var src = srcOf.TryGetValue(m, out var s0) ? s0 : m;
                    if (!match(src)) continue;
                    if (!cloneOf.TryGetValue(src, out var c))
                    {
                        c = new Material(src) { name = src.name + "_art" };
                        cloneOf[src] = c; srcOf[c] = src;
                    }
                    if (edited.Add(c)) edit(c);
                    if (mats[i] != c) { mats[i] = c; changed = true; }
                    slots++;
                }
                if (changed) r.sharedMaterials = mats;
            }
            log.AppendLine($"  {what}: {slots} slots, materials [{string.Join(", ", edited.Select(m => m.name))}]");
            return slots;
        }

        static bool Named(Material m, params string[] names) => names.Contains(m.name);
        static bool Starts(Material m, params string[] prefixes) => prefixes.Any(p => m.name.StartsWith(p));

        // ------------------------------------------------------------------------------------------- steps
        static void Splash(RunnerController runner, string dir, StringBuilder log)
        {
            var man = JsonUtility.FromJson<SplashMan>(File.ReadAllText(Path.Combine(dir, "manifest.json")));
            var sc = runner.GetComponentsInChildren<SplashCrowns>(true).FirstOrDefault(c => c.crowns != null && c.crowns.Length >= 2 && c.crowns[0] != null && c.crowns[1] != null);
            if (sc == null) { log.AppendLine("  splash: no SplashCrowns with two crowns on the runner - skipped"); return; }
            Mesh[] Load(string[] files) => files.Select(f =>
            {
                var m = S2v1TestScene.ReadBwkm(Path.Combine(dir, f), out _);
                m.name = "SM_FX_SplashArt_" + Path.GetFileNameWithoutExtension(f);
                newMeshes.Add(m);
                return m;
            }).ToArray();
            var fl = Load(man.L);
            var fr = Load(man.R);
            var milk = MilkArt();
            var bubble = MaterialLibrary.Get("M_FX_Bubble") ?? MaterialLibrary.Get("M_Bubble");
            var holder = sc.crowns[0].transform.parent;
            var rt = runner.transform;
            var rel = Quaternion.Inverse(holder.rotation) * rt.rotation;
            Vector3 Piv(float[] p) => holder.InverseTransformPoint(rt.TransformPoint(new Vector3(p[0], p[1], p[2])));
            var piv = new[] { Piv(man.pivot_L), Piv(man.pivot_R) };
            for (int i = 0; i < 2; i++)
            {
                var mf = sc.crowns[i];
                mf.transform.localPosition = piv[i];
                mf.transform.localRotation = rel;
                mf.transform.localScale = Vector3.one;
                mf.sharedMesh = i == 0 ? fl[0] : fr[fr.Length / 2];
                var mr = mf.GetComponent<MeshRenderer>();
                mr.sharedMaterials = bubble != null ? new[] { milk, bubble } : new[] { milk, milk };
                mr.shadowCastingMode = ShadowCastingMode.Off;
                mr.receiveShadows = true;
                mr.enabled = true;
            }
            sc.frames = fl;
            sc.framesRight = fr;
            sc.baseScale = new[] { Vector3.one, Vector3.one };
            sc.baseRotation = new[] { rel, rel };
            sc.phase = new[] { 0, fr.Length / 2 };
            EditorUtility.SetDirty(sc);
            log.AppendLine(string.Format(IC, "  splash: {0} + {1} frames from {2}; holder {3} rel-rot {4}; pivots holder-space L {5} R {6}; tris L0 {7} R3 {8}; milk {9} + {10}",
                fl.Length, fr.Length, dir, holder.name, rel.eulerAngles, piv[0], piv[1], fl[0].triangles.Length / 3, fr[fr.Length / 2].triangles.Length / 3,
                milk.name, bubble ? bubble.name : "-"));
        }

        static Material milkArt;
        /// <summary>Creamy milk (ORIGINAL crop water_splashes_03s: opaque milky white bodies, soft blue-grey shading, glossy wet
        /// glints, only the thinnest edges water-lit) on the game's own BWK/Soft milk mode: a clone of M_FX_Milk_v3 without the
        /// see-through thin-film that made today's crowns read as glass shards.</summary>
        static Material MilkArt()
        {
            if (milkArt != null) return milkArt;
            var src = MaterialLibrary.Get("M_FX_Milk_v3");
            milkArt = new Material(src) { name = "M_FX_Milk_art" };
            C(milkArt, "_ColorA", "#F4F9FD"); C(milkArt, "_ShadowColor", "#A9C2DE"); C(milkArt, "_ColorB", "#86C6EA"); C(milkArt, "_MilkThin", "#B4DAF0");
            F(milkArt, "_MilkAlpha", 1f); F(milkArt, "_MilkEdgeAlpha", 0.72f); F(milkArt, "_Glow", 0.10f);
            F(milkArt, "_MilkSoft", 1f); F(milkArt, "_MilkGlass", 0f); F(milkArt, "_BumpScale", 6f); F(milkArt, "_BumpStrength", 0.22f);
            F(milkArt, "_MilkWet", 0.8f); F(milkArt, "_SpecStrength", 1.0f); F(milkArt, "_Wrap", 0.62f); F(milkArt, "_RimStrength", 0.22f);
            F(milkArt, "_Wobble", 0.002f);
            srcOf[milkArt] = src;
            return milkArt;
        }

        static void Glow(StringBuilder log)
        {
            // lighting artist (light_07 Unity mapping): emitters up (bulbs, neon) so they carry wide soft halos; bloom threshold 1.0 so
            // lit walls / foam / gold never veil; wider scatter = the original's soft animated-film glow around every bulb and star
            Swap("glow bulbs", m => Starts(m, "M_Bulb"), m => { Mul(m, "_Intensity", 1.7f); F(m, "_HaloBoost", 1.9f); }, log);
            Swap("glow neon stars", m => Starts(m, "M_Neon_"), m => { Mul(m, "_Intensity", 2.1f); F(m, "_HaloBoost", 1.1f); F(m, "_EdgeSaturate", 0.8f); }, log);
            Swap("glow star fills", m => Starts(m, "M_StarFill_"), m => { Mul(m, "_Intensity", 1.6f); }, log);
            foreach (var vol in Object.FindObjectsByType<Volume>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                if (vol.sharedProfile == null || !vol.sharedProfile.TryGet<Bloom>(out var b)) continue;
                log.AppendLine(string.Format(IC, "  glow bloom {0}: threshold {1} -> 1.0, intensity {2} -> 2.2, scatter {3} -> 0.88",
                    vol.name, b.threshold.value, b.intensity.value, b.scatter.value));
                b.threshold.Override(1.0f); b.intensity.Override(2.2f); b.scatter.Override(0.88f);
            }
        }

        static void Depth(StringBuilder log)
        {
            // lighting artist (light_07): Unity's core is +9 / +22 L* too light at r 0-50 px (white hoops) -> deeper violet aerial
            // perspective #6A44A8 (keeps the bulbs punching through: emissives use little fog) and violet, never white, deep rims
            log.AppendLine(string.Format(IC, "  depth fog: {0} {1} -> #6A44A8, density {2} -> 0.0118", RenderSettings.fogMode, RenderSettings.fogColor, RenderSettings.fogDensity));
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.416f, 0.267f, 0.659f);
            RenderSettings.fogDensity = 0.0118f;
            Swap("depth deep rims", m => Named(m, "M_RimLight", "M_RimSpark_s2"), m => { F(m, "_CoreWhite", 0.04f); Mul(m, "_Intensity", 0.8f); F(m, "_EdgeSaturate", 0.8f); }, log);
            Swap("depth vanish core", m => Starts(m, "M_VanishCore", "M_VanishGlow"), m => { Mul(m, "_Intensity", 0.7f); }, log);
            // art01 pick: the white hoops deep in the tunnel = SM_LedRim_s2 band lips (M_RimGlow_s2, #D85CFF x3.2 tonemapped to white
            // with a white core) -> saturated violet-lavender glow without the white core (lighting artist: lips just under bloom)
            Swap("depth band lips", m => Named(m, "M_RimGlow_s2"), m => { F(m, "_CoreWhite", 0f); Mul(m, "_Intensity", 0.72f); F(m, "_EdgeSaturate", 1f); C(m, "_Color", "#B65CFF"); }, log);
        }

        static void Roller(StringBuilder log)
        {
            // ORIGINAL top-left: a bright hot-pink BRISTLE brush roller with pale pink tips (art01: still a dark smooth velvet disc - the
            // blue hall light turns the cream ramp x vertex pink into magenta) -> own hot-pink ramp, colour-true self light, coarse
            // contrasted strands, a pale rim
            Swap("roller", m => Starts(m, "M_RollerFur"), m =>
            {
                F(m, "_UseVertexTint", 0f);
                C(m, "_RootColor", "#C2275E"); C(m, "_BaseColor", "#FF4A88"); C(m, "_TipColor", "#FFC6DC");
                F(m, "_Glow", 0.95f); F(m, "_StrandContrast", 1f); F(m, "_AO", 0.5f);
                C(m, "_RimColor", "#FFE4F2"); F(m, "_RimStrength", 0.6f); F(m, "_RimPower", 2.0f);
            }, log);
        }

        static void Walls(StringBuilder log)
        {
            // owner 23:36 "rich metallic purple and blue scenery" (ORIGINAL: glossy saturated violet drum metal with lavender sheen and
            // glittering glints, polished violet bands with bright crests; ours: greyer matte violet after the r8 desaturation)
            Swap("walls drum metal", m => Named(m, "M_DrumWall", "M_DrumWallFlat"), m =>
            {
                C(m, "_BaseColor", "#8A6CC4"); C(m, "_HighlightColor", "#CDB6F5"); C(m, "_SheenColor", "#E6C8FF");
                F(m, "_SheenStrength", 0.32f); F(m, "_Sparkle", 0.6f); F(m, "_Metallic", 0.68f); F(m, "_Smoothness", 0.70f);
                F(m, "_BaySheen", 0.28f); F(m, "_Glow", 0.05f);
            }, log);
            Swap("walls violet bands", m => Named(m, "M_HatchViolet_s2"), m =>
            {
                C(m, "_HighColor", "#CFA2F2"); Mul(m, "_SpecStrength", 1.4f); F(m, "_Sparkle", 0.6f); F(m, "_Brightness", 0.9f); F(m, "_GlintStrength", 1.3f);
            }, log);
            Swap("walls gold", m => Named(m, "M_Gold", "M_GoldDark", "M_DrumRim"), m => { Mul(m, "_GlintStrength", 1.4f); Mul(m, "_Sparkle", 1.6f); Mul(m, "_Brightness", 1.06f); }, log);
        }

        static void Foam(StringBuilder log)
        {
            // ORIGINAL foam banks = glossy wet soap suds (many small shiny bubbles with bright glints); ours = matte white cloud puffs
            Swap("foam suds", m => Named(m, "M_Foam_v2", "M_Foam"), m =>
            {
                F(m, "_BumpScale", 22f); F(m, "_BumpStrength", 0.12f); F(m, "_SpecStrength", 1.1f); F(m, "_GlintAmount", 0.45f);
                F(m, "_ReflectBoost", 0.4f); F(m, "_RimStrength", 0.45f);
            }, log);
        }

        /// <summary>ORIGINAL 3.00 s: floating iridescent soap bubbles at the left edge, top left by the roller, along the right wall and
        /// over the left foam (ours: two). Plain spheres (no collider) with the scene's own bubble material, placed in WORLD space
        /// through the R2 camera at the original's screen positions (decor in the door section; gameplay passes them).</summary>
        static void Bubbles(Camera cam, RunnerController runner, StringBuilder log)
        {
            var mat = MaterialLibrary.Get("M_Bubble") ?? MaterialLibrary.Get("M_FX_Bubble");
            if (mat == null) { log.AppendLine("  bubbles: no bubble material - skipped"); return; }
            S2v1TestScene.PoseR2(runner, cam);
            float aspect = cam.aspect;
            cam.aspect = 1280f / 720f;
            float f = 360f / Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
            var parent = new GameObject("S2Art_Bubbles");
            var env = GameObject.Find("Level01_RainbowRush");
            if (env != null) parent.transform.SetParent(env.transform, true);
            // (u, v, radius px, depth m) read off the ORIGINAL frame
            var spec = new (float u, float v, float r, float d)[] { (18, 258, 46, 3.6f), (52, 106, 18, 5f), (878, 320, 14, 9f), (866, 292, 8, 9.5f),
                (905, 342, 6, 9.2f), (405, 150, 7, 8f), (182, 246, 8, 5f), (232, 300, 6, 4.6f), (1188, 300, 10, 6f), (1010, 470, 9, 4.2f) };
            int n = 0;
            foreach (var b in spec)
            {
                var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                Object.DestroyImmediate(go.GetComponent<Collider>());
                go.name = $"S2Art_Bubble_{n:00}";
                go.transform.SetParent(parent.transform, true);
                go.transform.position = cam.ViewportToWorldPoint(new Vector3(b.u / 1280f, 1f - b.v / 720f, b.d));
                float radius = b.r * b.d / f;
                go.transform.localScale = Vector3.one * (2f * radius);
                var mr = go.GetComponent<MeshRenderer>();
                mr.sharedMaterial = mat;
                mr.shadowCastingMode = ShadowCastingMode.Off;
                n++;
            }
            cam.aspect = aspect;
            log.AppendLine($"  bubbles: {n} floating soap bubbles ({mat.name}) placed through R2 at the original's screen positions");
        }

        /// <summary>art04: the milk crowns still read ~15 % smaller than the original's sprays -> the game's own SplashCrowns base scale.</summary>
        static void BigSplash(RunnerController runner, StringBuilder log)
        {
            var sc = runner.GetComponentsInChildren<SplashCrowns>(true).FirstOrDefault(c => c.crowns != null && c.crowns.Length >= 2);
            if (sc == null) return;
            var s3 = new Vector3(1.15f, 1.12f, 1.15f);
            sc.baseScale = new[] { s3, s3 };
            foreach (var mf in sc.crowns) if (mf != null) mf.transform.localScale = s3;
            EditorUtility.SetDirty(sc);
            log.AppendLine($"  bigsplash: crown base scale {s3}");
        }

        // ------------------------------------------------------------------------------------------- what sits under key R2 pixels
        static readonly (string tag, int u, int v)[] PickPixels =
        {
            ("topleft corner", 60, 40), ("topleft roller", 150, 90), ("topleft low", 200, 160), ("left machinery", 110, 230), ("left gold rim", 290, 220),
            ("left foam", 160, 330), ("deep core", 740, 185), ("deep ring A", 700, 160), ("deep ring B", 780, 160), ("deep ring C", 720, 225),
            ("mid wall L", 520, 140), ("mid wall R", 1000, 140), ("band R", 1180, 250), ("upper wall", 640, 40), ("rail R", 1100, 520),
        };

        static void Pick(Camera cam, StringBuilder log)
        {
            float aspect = cam.aspect;
            cam.aspect = 1280f / 720f;
            var cands = Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
                .Where(r => r.enabled && r.gameObject.activeInHierarchy && r.GetComponent<MeshFilter>() != null && r.GetComponent<MeshFilter>().sharedMesh != null).ToList();
            foreach (var (tag, u, v) in PickPixels)
            {
                var ray = cam.ViewportPointToRay(new Vector3(u / 1280f, 1f - v / 720f, 0f));
                float best = float.MaxValue; string hit = "-";
                foreach (var r in cands)
                {
                    if (!r.bounds.IntersectRay(ray, out float bd) || bd > best) continue;
                    var mesh = r.GetComponent<MeshFilter>().sharedMesh;
                    var l2w = r.transform.localToWorldMatrix;
                    using (var ro = Mesh.AcquireReadOnlyMeshData(mesh))
                    {
                        var md = ro[0];
                        var va = new NativeArray<Vector3>(md.vertexCount, Allocator.Temp);
                        md.GetVertices(va);
                        for (int s = 0; s < md.subMeshCount; s++)
                        {
                            var desc = md.GetSubMesh(s);
                            if (desc.topology != MeshTopology.Triangles) continue;
                            var ia = new NativeArray<int>(desc.indexCount, Allocator.Temp);
                            md.GetIndices(ia, s, true);
                            for (int t = 0; t + 2 < ia.Length; t += 3)
                            {
                                Vector3 a = l2w.MultiplyPoint3x4(va[ia[t]]), b = l2w.MultiplyPoint3x4(va[ia[t + 1]]), c = l2w.MultiplyPoint3x4(va[ia[t + 2]]);
                                if (RayTri(ray, a, b, c, out float d) && d < best)
                                {
                                    best = d;
                                    var mats = r.sharedMaterials;
                                    hit = string.Format(IC, "{0} | sub {1} | {2} | {3:0.0} m", TPath(r.transform), s, s < mats.Length && mats[s] ? mats[s].name : "-", d);
                                }
                            }
                            ia.Dispose();
                        }
                        va.Dispose();
                    }
                }
                log.AppendLine($"  pick {tag,-16} ({u},{v}): {hit}");
            }
            cam.aspect = aspect;
        }

        static string TPath(Transform t)
        {
            var sb = new StringBuilder(t.name);
            int n = 0;
            for (var p = t.parent; p != null && n < 3; p = p.parent, n++) sb.Insert(0, p.name + "/");
            return sb.ToString();
        }

        static bool RayTri(Ray r, Vector3 a, Vector3 b, Vector3 c, out float t)
        {
            t = 0f;
            Vector3 e1 = b - a, e2 = c - a, p = Vector3.Cross(r.direction, e2);
            float det = Vector3.Dot(e1, p);
            if (Mathf.Abs(det) < 1e-9f) return false;
            float inv = 1f / det;
            Vector3 s = r.origin - a;
            float u = Vector3.Dot(s, p) * inv;
            if (u < 0f || u > 1f) return false;
            Vector3 q = Vector3.Cross(s, e1);
            float v = Vector3.Dot(r.direction, q) * inv;
            if (v < 0f || u + v > 1f) return false;
            t = Vector3.Dot(e2, q) * inv;
            return t > 0.05f;
        }

        // ------------------------------------------------------------------------------------------- renders
        static void RenderSet(RunnerController runner, Camera cam, string vd, float[] dists, List<Renderer> mascot)
        {
            Directory.CreateDirectory(vd);
            S2v1TestScene.PoseR2(runner, cam);
            CaptureTools.Render(cam, 1280, 720, $"{vd}/R2_16x9.png");
            var was = mascot.Select(r => r.enabled).ToArray();
            foreach (var r in mascot) r.enabled = false;
            CaptureTools.Render(cam, 1280, 720, $"{vd}/R2_bg_16x9.png");
            for (int i = 0; i < mascot.Count; i++) mascot[i].enabled = was[i];
            foreach (float d in dists)
            {
                S2v1TestScene.PoseRig(runner, cam, d, 720f / 1280f);
                CaptureTools.Render(cam, 720, 1280, string.Format(IC, "{0}/rig_d{1:0.0}_9x16.png", vd, d));
            }
        }

        public static void PreviewBatch()
        {
            try
            {
                string outDir = Arg("-bwkOut") ?? "Captures/s2art/preview";
                string steps = Arg("-bwkSteps") ?? "splash,glow,depth,roller";
                string splashDir = Arg("-bwkSplash") ?? "Tools/Blender/work/s2art/splash";
                var dists = (Arg("-bwkDists") ?? "33.5,38.5,44").Split(',').Select(s => float.Parse(s, IC)).ToArray();
                bool save = Arg("-bwkSave") == "1";
                Directory.CreateDirectory(outDir);
                var log = new StringBuilder();
                log.AppendLine($"S2 ART PASS (lead 470ca906): steps {steps}, splash {splashDir}, save {save}");

                TextureGenerator.Run();
                MaterialLibrary.Run();
                var scene = EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                SceneBuilder.PreviewRefreshDomains();
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var cam = Camera.main;
                var brain = cam.GetComponent<CinemachineBrain>();
                if (brain) brain.enabled = false;
                var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
                var mascot = S2v1TestScene.MascotRenderers(runner);
                // the scene's own start state (restored before -bwkSave: art04's saved scene kept the brain OFF and the camera frozen
                // at the last capture pose, so its Play Mode recording showed a static camera)
                float runnerStart = runner.Distance;
                var runnerPos = runner.transform.position; var runnerRot = runner.transform.rotation;
                var camPos = cam.transform.position; var camRot = cam.transform.rotation; float camFov = cam.fieldOfView;
                Vector3 rigPos = rig ? rig.transform.position : Vector3.zero; Quaternion rigRot = rig ? rig.transform.rotation : Quaternion.identity;

                S2v1TestScene.PoseR2(runner, cam);
                Pick(cam, log);
                RenderSet(runner, cam, $"{outDir}/current", dists, mascot);
                log.AppendLine("rendered current");
                string acc = "";
                foreach (var st in steps.Split(',').Select(x => x.Trim()).Where(x => x.Length > 0))
                {
                    log.AppendLine($"step {st}:");
                    switch (st)
                    {
                        case "splash": Splash(runner, splashDir, log); break;
                        case "glow": Glow(log); break;
                        case "depth": Depth(log); break;
                        case "roller": Roller(log); break;
                        case "walls": Walls(log); break;
                        case "foam": Foam(log); break;
                        case "bubbles": Bubbles(cam, runner, log); break;
                        case "bigsplash": BigSplash(runner, log); break;
                        default: log.AppendLine("  unknown step - skipped"); continue;
                    }
                    acc = acc.Length == 0 ? st : acc + "+" + st;
                    RenderSet(runner, cam, $"{outDir}/art_{acc}", dists, mascot);
                    log.AppendLine($"rendered art_{acc}");
                }
                if (rig) { rig.aspectOverride = 0f; rig.transform.SetPositionAndRotation(rigPos, rigRot); }
                runner.TeleportTo(runnerStart, 0f);
                runner.transform.SetPositionAndRotation(runnerPos, runnerRot);
                cam.transform.SetPositionAndRotation(camPos, camRot); cam.fieldOfView = camFov;
                if (brain) brain.enabled = true;
                log.AppendLine(string.Format(IC, "restored start state: runner d {0:0.0}, camera + rig pose, CinemachineBrain {1}", runnerStart, brain ? brain.enabled.ToString() : "-"));
                if (save) SaveIsolated(scene, log);
                File.WriteAllText($"{outDir}/summary.txt", log.ToString());
                Debug.Log("[BWK] S2 art pass:\n" + log);
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] S2 art pass failed: " + e); EditorApplication.Exit(1); }
        }

        /// <summary>Persist the clones / splash meshes / post profile (gitignored Art/S2v1Test/Art/) and save the open, modified copy
        /// of the level as the PROTECTED test scene (saveAsCopy: the main scene file is never written).</summary>
        static void SaveIsolated(UnityEngine.SceneManagement.Scene scene, StringBuilder log)
        {
            Directory.CreateDirectory($"{AssetDir}/Meshes");
            Directory.CreateDirectory($"{AssetDir}/Materials");
            void Persist(Object o, string path)
            {
                if (o == null || AssetDatabase.Contains(o)) return;
                AssetDatabase.DeleteAsset(path);
                AssetDatabase.CreateAsset(o, path);
            }
            foreach (var m in newMeshes) Persist(m, $"{AssetDir}/Meshes/{m.name}.asset");
            if (milkArt != null) Persist(milkArt, $"{AssetDir}/Materials/{milkArt.name}.mat");
            foreach (var c in cloneOf.Values) Persist(c, $"{AssetDir}/Materials/{c.name}.mat");
            foreach (var vol in Object.FindObjectsByType<Volume>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                string pp = vol.sharedProfile != null ? AssetDatabase.GetAssetPath(vol.sharedProfile) : "";
                if (!pp.EndsWith("PostFX_Preview.asset")) continue;
                EditorUtility.SetDirty(vol.sharedProfile);
                foreach (var comp in vol.sharedProfile.components) EditorUtility.SetDirty(comp);
                AssetDatabase.SaveAssets();
                string dst = $"{AssetDir}/PostFX_Art.asset";
                AssetDatabase.DeleteAsset(dst);
                AssetDatabase.CopyAsset(pp, dst);
                vol.sharedProfile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(dst);
            }
            AssetDatabase.SaveAssets();
            Directory.CreateDirectory(System.IO.Path.GetDirectoryName(S2v1TestScene.TestScenePath));
            if (!EditorSceneManager.SaveScene(scene, S2v1TestScene.TestScenePath, true)) throw new System.Exception("saving " + S2v1TestScene.TestScenePath + " failed");
            log.AppendLine($"SAVED protected test scene {S2v1TestScene.TestScenePath} ({newMeshes.Count} splash meshes, {cloneOf.Count} material clones, assets in {AssetDir}); main scene untouched");
        }
    }
}
