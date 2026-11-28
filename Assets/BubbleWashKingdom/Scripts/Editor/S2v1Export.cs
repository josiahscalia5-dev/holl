using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Unity.Collections;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Lead 8d2d815d 2026-11-27 (owner 21:03 "S2 Tunnel v1 art team"): exports the S2 context of the SAVED scene (nothing is saved) for the
    /// isolated Blender environment Tools/Blender/scripts/s2v1/: exact track frames 20-80 m, the R2 comparison camera + the unchanged
    /// gameplay rig cameras at several track distances, the lights, and every mesh those cameras can see as ONE world-space OBJ
    /// (Unity coordinates; groups tagged by category so Blender can hide the old tunnel / re-material water, slide, mascot ...).
    /// Run: Tools/unity_run.sh BubbleWash.EditorTools.S2v1Export.ExportBatch lead_s2v1_export -bwkOut Tools/Blender/work/s2v1/unity_export
    /// </summary>
    public static class S2v1Export
    {
        static readonly CultureInfo IC = CultureInfo.InvariantCulture;
        static readonly float[] RigDistances = { 33.5f, 36f, 38.5f, 41f, 44f, 47f, 50f };

        static string Arg(string key)
        {
            var a = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == key) return a[i + 1];
            return null;
        }

        static string V(Vector3 v) => string.Format(IC, "[{0:0.#####},{1:0.#####},{2:0.#####}]", v.x, v.y, v.z);
        static string Q(Quaternion q) => string.Format(IC, "[{0:0.######},{1:0.######},{2:0.######},{3:0.######}]", q.x, q.y, q.z, q.w);
        static string C(Color c) => string.Format(IC, "[{0:0.####},{1:0.####},{2:0.####}]", c.r, c.g, c.b);
        static string Esc(string s) => (s ?? "").Replace("\\", "/").Replace("\"", "'");

        static string Category(Renderer r, Transform runnerRoot)
        {
            string path = GetPath(r.transform);
            string n = r.gameObject.name;
            var mats = r.sharedMaterials.Where(m => m != null).Select(m => m.name).ToArray();
            if (runnerRoot != null && r.transform.IsChildOf(runnerRoot)) return "mascot";
            if (path.Contains("MouthDrum_r7") || path.Contains("/Tunnel/") || n.StartsWith("Tunnel_")) return "old_tunnel_wall";
            if (n.Contains("LedRim") || n.Contains("MarqueeRing") || n.Contains("MouthDrumRing") || n.Contains("MouthDrumRim")
                || n.Contains("DrumRim") || n.StartsWith("SM_Ring") || n.StartsWith("Ring_") || path.Contains("/Rings/")) return "old_tunnel_rings";
            if (n.Contains("Starburst") || path.Contains("TunnelStars") || n.Contains("Star")) return "old_tunnel_stars";
            if (mats.Any(m => m.StartsWith("M_Water"))) return "water";
            if (mats.Any(m => m.Contains("Foam"))) return "foam";
            if (mats.Any(m => m.Contains("Coin") || m.Contains("Gem")) || n.Contains("Coin") || n.Contains("Gem")) return "pickups";
            if (mats.Any(m => m.Contains("Bubble"))) return "bubbles";
            if (mats.Any(m => m.StartsWith("M_Rail") || m.StartsWith("M_Slide"))) return "slide";
            if (path.Contains("Hall") || path.Contains("Machinery")) return "machinery";
            return "context";
        }

        static string GetPath(Transform t)
        {
            var sb = new StringBuilder(t.name);
            for (var p = t.parent; p != null; p = p.parent) sb.Insert(0, p.name + "/");
            return sb.ToString();
        }

        public static void ExportBatch()
        {
            try
            {
                string outDir = Arg("-bwkOut") ?? "Tools/Blender/work/s2v1/unity_export";
                Directory.CreateDirectory(outDir);
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                SceneBuilder.PreviewRefreshDomains();
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var cam = Camera.main;
                var brain = cam.GetComponent<CinemachineBrain>();
                if (brain) brain.enabled = false;
                var track = runner.track != null ? runner.track : Object.FindFirstObjectByType<TrackPath>();
                var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);

                var js = new StringBuilder();
                js.Append("{\n\"note\":\"Unity world coordinates (left-handed, Y up). Blender: (x,y,z)_unity -> (x,z,y)_blender + flip winding.\",\n");
                js.AppendFormat(IC, "\"tunnel_radius\":4.2,\"tunnel_center\":2.3,\"hall_mouth_d\":{0},\"hero_mouth_d\":{1},\"track_length\":{2:0.###},\n",
                    SceneBuilder.HallMouthD, SceneBuilder.HeroMouthDistance, track.Length);
                js.Append("\"frames\":[\n");
                bool first = true;
                for (float d = 20f; d <= 80.001f; d += 0.25f)
                {
                    var f = track.Evaluate(d);
                    js.Append(first ? "" : ",\n"); first = false;
                    js.AppendFormat(IC, "{{\"d\":{0:0.##},\"pos\":{1},\"fwd\":{2},\"flatUp\":{3},\"flatRight\":{4},\"up\":{5},\"right\":{6}}}",
                        d, V(f.position), V(f.forward), V(f.flatUp), V(f.flatRight), V(f.up), V(f.right));
                }
                js.Append("\n],\n\"cameras\":[\n");

                // cameras: R2 (as CaptureTools.CaptureHero) + the gameplay rig at several distances (portrait)
                var cams = new List<(string name, Vector3 pos, Quaternion rot, float vfov, int w, int h)>();
                void PoseRunner(float d)
                {
                    runner.TeleportTo(d, 0f);
                    var animator = runner.GetComponentInChildren<Animator>();
                    if (animator != null && animator.runtimeAnimatorController != null)
                    {
                        var slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
                        if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                    }
                }
                foreach (float d in RigDistances)
                {
                    PoseRunner(d);
                    rig.aspectOverride = 720f / 1280f;
                    rig.Snap();
                    var lens = rig.vcam.Lens;
                    cams.Add(($"RIG_d{d.ToString("0.0", IC)}_9x16", rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch), lens.FieldOfView, 720, 1280));
                }
                rig.aspectOverride = 0f;
                PoseRunner(SceneBuilder.HeroMouthDistance);
                {
                    var f = runner.Frame;
                    Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
                    Vector3 cp = runner.transform.position - fwd * CaptureTools.R2Back + Vector3.up * CaptureTools.R2Height + right * CaptureTools.R2Lat;
                    cams.Insert(0, ("R2_16x9", cp, Quaternion.LookRotation(fwd, Vector3.up) * Quaternion.Euler(CaptureTools.R2Pitch, CaptureTools.R2Yaw, 0f), CaptureTools.R2Fov, 1280, 720));
                }
                js.Append(string.Join(",\n", cams.Select(c => string.Format(IC, "{{\"name\":\"{0}\",\"pos\":{1},\"rot\":{2},\"vfov\":{3:0.###},\"w\":{4},\"h\":{5}}}",
                    c.name, V(c.pos), Q(c.rot), c.vfov, c.w, c.h))));
                js.Append("\n],\n\"lights\":[\n");
                Vector3 door = track.Evaluate(SceneBuilder.HallMouthD).position;
                var lights = Object.FindObjectsByType<Light>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
                    .Where(l => l.enabled && (l.type == LightType.Directional || Vector3.Distance(l.transform.position, door) < 90f)).ToList();
                js.Append(string.Join(",\n", lights.Select(l => string.Format(IC, "{{\"name\":\"{0}\",\"type\":\"{1}\",\"pos\":{2},\"rot\":{3},\"color\":{4},\"intensity\":{5:0.###},\"range\":{6:0.##},\"spot\":{7:0.#}}}",
                    Esc(l.name), l.type, V(l.transform.position), Q(l.transform.rotation), C(l.color), l.intensity, l.range, l.spotAngle))));
                js.Append("\n],\n\"objects\":[\n");

                // meshes visible from any exported camera (LOD0 only, no particles / trails)
                var skip = new HashSet<Renderer>();
                foreach (var lg in Object.FindObjectsByType<LODGroup>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
                {
                    var lods = lg.GetLODs();
                    for (int i = 1; i < lods.Length; i++) foreach (var r in lods[i].renderers) if (r) skip.Add(r);
                }
                var planes = new List<Plane[]>();
                foreach (var c in cams)
                {
                    cam.transform.SetPositionAndRotation(c.pos, c.rot); cam.fieldOfView = c.vfov; cam.aspect = c.w / (float)c.h;
                    cam.farClipPlane = 200f;
                    planes.Add(GeometryUtility.CalculateFrustumPlanes(cam));
                }
                cam.ResetAspect();
                var runnerRoot = runner.transform;
                var objPath = Path.Combine(outDir, "s2_context_unity_world.obj");
                int vBase = 1, nObj = 0, nTri = 0;
                var objList = new List<string>();
                using (var w = new StreamWriter(objPath, false, new UTF8Encoding(false), 1 << 20))
                {
                    w.WriteLine("# S2 context, Unity world coordinates (left-handed, Y up), lead 8d2d815d S2v1Export");
                    foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
                    {
                        if (!r.enabled || !r.gameObject.activeInHierarchy || skip.Contains(r)) continue;
                        if (r is ParticleSystemRenderer || r is TrailRenderer || r is LineRenderer) continue;
                        if (!planes.Any(p => GeometryUtility.TestPlanesAABB(p, r.bounds))) continue;
                        Mesh mesh = null; Matrix4x4 m;
                        if (r is SkinnedMeshRenderer smr)
                        {
                            mesh = new Mesh(); smr.BakeMesh(mesh, true);
                            m = Matrix4x4.TRS(smr.transform.position, smr.transform.rotation, Vector3.one);
                        }
                        else
                        {
                            var mf = r.GetComponent<MeshFilter>();
                            if (mf == null || mf.sharedMesh == null) continue;
                            mesh = mf.sharedMesh; m = r.transform.localToWorldMatrix;
                        }
                        // Mesh.AcquireReadOnlyMeshData also reads import-locked (Read/Write off) meshes in the Editor - no import change
                        Vector3[] vs; Vector3[] ns = null; Vector2[] uv = null; var subTris = new List<int[]>();
                        using (var mda = Mesh.AcquireReadOnlyMeshData(mesh))
                        {
                            var md = mda[0];
                            int vc = md.vertexCount;
                            if (vc == 0) { if (r is SkinnedMeshRenderer) Object.DestroyImmediate(mesh); continue; }
                            using (var na = new NativeArray<Vector3>(vc, Allocator.Temp)) { md.GetVertices(na); vs = na.ToArray(); }
                            if (md.HasVertexAttribute(VertexAttribute.Normal)) using (var na = new NativeArray<Vector3>(vc, Allocator.Temp)) { md.GetNormals(na); ns = na.ToArray(); }
                            if (md.HasVertexAttribute(VertexAttribute.TexCoord0)) using (var na = new NativeArray<Vector2>(vc, Allocator.Temp)) { md.GetUVs(0, na); uv = na.ToArray(); }
                            for (int s = 0; s < md.subMeshCount; s++)
                            {
                                var desc = md.GetSubMesh(s);
                                if (desc.topology != MeshTopology.Triangles) { subTris.Add(new int[0]); continue; }
                                using (var ia = new NativeArray<int>(desc.indexCount, Allocator.Temp)) { md.GetIndices(ia, s, true); subTris.Add(ia.ToArray()); }
                            }
                        }
                        string cat = Category(r, runnerRoot);
                        string safe = (r.gameObject.name + "_" + r.GetInstanceID()).Replace(' ', '_');
                        w.WriteLine("o " + cat + "__" + safe);
                        foreach (var v in vs) { var p = m.MultiplyPoint3x4(v); w.Write("v "); w.Write(p.x.ToString("0.####", IC)); w.Write(' '); w.Write(p.y.ToString("0.####", IC)); w.Write(' '); w.WriteLine(p.z.ToString("0.####", IC)); }
                        bool hasN = ns != null && ns.Length == vs.Length, hasUV = uv != null && uv.Length == vs.Length;
                        if (hasN) foreach (var n in ns) { var q = m.MultiplyVector(n).normalized; w.Write("vn "); w.Write(q.x.ToString("0.###", IC)); w.Write(' '); w.Write(q.y.ToString("0.###", IC)); w.Write(' '); w.WriteLine(q.z.ToString("0.###", IC)); }
                        if (hasUV) foreach (var t in uv) { w.Write("vt "); w.Write(t.x.ToString("0.#####", IC)); w.Write(' '); w.WriteLine(t.y.ToString("0.#####", IC)); }
                        var mats = r.sharedMaterials;
                        for (int s = 0; s < subTris.Count; s++)
                        {
                            string mat = s < mats.Length && mats[s] != null ? mats[s].name.Replace(' ', '_') : "none";
                            w.WriteLine("usemtl " + mat);
                            var tri = subTris[s];
                            for (int i = 0; i + 2 < tri.Length; i += 3)
                            {
                                int a = tri[i] + vBase, b = tri[i + 1] + vBase, c = tri[i + 2] + vBase;
                                if (hasN && hasUV) w.WriteLine($"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}");
                                else if (hasN) w.WriteLine($"f {a}//{a} {b}//{b} {c}//{c}");
                                else if (hasUV) w.WriteLine($"f {a}/{a} {b}/{b} {c}/{c}");
                                else w.WriteLine($"f {a} {b} {c}");
                            }
                            nTri += tri.Length / 3;
                        }
                        vBase += vs.Length; nObj++;
                        var b0 = r.bounds;
                        objList.Add(string.Format(IC, "{{\"obj\":\"{0}__{1}\",\"path\":\"{2}\",\"category\":\"{3}\",\"materials\":[{4}],\"center\":{5},\"size\":{6}}}",
                            cat, Esc(safe), Esc(GetPath(r.transform)), cat, string.Join(",", r.sharedMaterials.Where(x => x).Select(x => "\"" + Esc(x.name) + "\"")), V(b0.center), V(b0.size)));
                        if (r is SkinnedMeshRenderer) Object.DestroyImmediate(mesh);
                    }
                }
                js.Append(string.Join(",\n", objList));
                js.Append("\n]\n}\n");
                File.WriteAllText(Path.Combine(outDir, "s2_layout.json"), js.ToString());
                if (brain) brain.enabled = true;
                Debug.Log($"[BWK] S2v1 export: {nObj} objects, {nTri} triangles, {cams.Count} cameras, {lights.Count} lights -> {outDir}");
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] S2v1 export failed: " + e); EditorApplication.Exit(1); }
        }
    }
}
