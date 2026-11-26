using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Projection test (owner decision 2026-11-26 14:15): ONE sock-chamber window in S5 re-textured with reference-derived
    /// colour projected from solved video cameras and baked in Blender (Tools/Blender/scripts/build_projection_test.py).
    /// Never saves Level01_RainbowRush.unity: the test scene is a COPY in Scenes/Private (gitignored, reference pixels).
    ///   Inspect         : prints the test chamber's world transform / renderers / nearby renderers and writes
    ///                     Captures/agents/projection/chamber_world.json (matrix + tunnel-axis frames for the wall patch).
    ///   BuildAndCapture : renders the CURRENT level views (front at the solved reference camera, R5, rear gameplay views),
    ///                     copies the level to Scenes/Private/Test_Projection_S5.unity, swaps ONLY the test chamber (+ adds
    ///                     the projected wall patch), saves the copy and renders the same views -> Captures/agents/projection.
    /// Run: bash Tools/unity_run.sh BubbleWash.EditorTools.ProjectionTest.Inspect projection_v1
    /// </summary>
    public static class ProjectionTest
    {
        const string Out = "Captures/agents/projection";
        const string ProjDir = "Assets/BubbleWashKingdom/Art/Projected";
        const string TestScene = "Assets/BubbleWashKingdom/Scenes/Private/Test_Projection_S5.unity";
        const float TargetD = 216.05f;   // C2 gap 211.75 + 4.3 (SceneBuilder.Environment ChamberWindows), travel-right
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        static string F(float v) => v.ToString("0.####", Inv);
        static string V(Vector3 v) => $"[{F(v.x)},{F(v.y)},{F(v.z)}]";

        static GameObject FindChamber(out float d)
        {
            GameObject best = null; d = 0f; float bestErr = float.MaxValue;
            foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                if (!t.name.StartsWith("ChamberV2_") || !t.name.EndsWith("_R")) continue;
                var parts = t.name.Split('_');
                if (parts.Length < 3 || !float.TryParse(parts[1], NumberStyles.Float, Inv, out float dd)) continue;
                float err = Mathf.Abs(dd - TargetD);
                if (err < bestErr) { bestErr = err; best = t.gameObject; d = dd; }
            }
            return best;
        }

        static string PathOf(Transform t)
        {
            var s = t.name;
            while (t.parent != null) { t = t.parent; s = t.name + "/" + s; }
            return s;
        }

        public static void Inspect()
        {
            try
            {
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                Directory.CreateDirectory(Out);
                var runner = Object.FindFirstObjectByType<RunnerController>();
                runner.track.Rebuild();
                var ch = FindChamber(out float dName);
                if (ch == null) throw new System.Exception("no ChamberV2_*_R found");
                var sb = new StringBuilder();
                sb.AppendLine($"chamber {PathOf(ch.transform)} pos {V(ch.transform.position)} rot {V(ch.transform.rotation.eulerAngles)} lossy {V(ch.transform.lossyScale)}");
                foreach (var r in ch.GetComponentsInChildren<Renderer>(true))
                {
                    var mf = r.GetComponent<MeshFilter>();
                    var mesh = mf ? mf.sharedMesh : null;
                    sb.AppendLine($"  R {PathOf(r.transform)} local {V(r.transform.localPosition)} mesh {(mesh ? mesh.name : "-")} sub {(mesh ? mesh.subMeshCount : 0)} meshBounds {(mesh ? V(mesh.bounds.min) + ".." + V(mesh.bounds.max) : "")} mats {string.Join(",", r.sharedMaterials.Select(m => m ? m.name + "(" + m.shader.name + ")" : "null"))}");
                }
                // nearby renderers (other objects within 7 m of the window centre)
                var c = ch.transform.position;
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                {
                    if (r.transform.IsChildOf(ch.transform)) continue;
                    if (r.bounds.SqrDistance(c) > 49f) continue;
                    var mf = r.GetComponent<MeshFilter>();
                    sb.AppendLine($"  NEAR {PathOf(r.transform)} {r.GetType().Name} mesh {(mf && mf.sharedMesh ? mf.sharedMesh.name : "-")} bounds {V(r.bounds.min)}..{V(r.bounds.max)} mats {string.Join(",", r.sharedMaterials.Select(m => m ? m.name + "(" + m.shader.name + ")" : "null"))}");
                }
                File.WriteAllText(Out + "/inspect.txt", sb.ToString());
                Debug.Log("[BWK] projection inspect\n" + sb);

                // JSON for Blender: chamber localToWorld (row-major), tunnel axis frames d-7..d+7 (axis = FlatPoint(0, 2.3))
                var m4 = ch.transform.localToWorldMatrix;
                var js = new StringBuilder();
                js.Append("{\n\"name\": \"" + ch.name + "\", \"d\": " + F(TargetD) + ",\n\"matrix\": [");
                for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) js.Append((i + j > 0 ? "," : "") + F(m4[i, j]));
                js.Append("],\n\"frames\": [\n");
                bool first = true;
                for (float dd = TargetD - 7f; dd <= TargetD + 7.001f; dd += 0.25f)
                {
                    var f = runner.track.Evaluate(dd);
                    js.Append((first ? "" : ",\n") + $"{{\"d\": {F(dd)}, \"axis\": {V(f.FlatPoint(0f, 2.3f))}, \"fwd\": {V(f.forward)}, \"right\": {V(f.flatRight)}, \"up\": {V(f.flatUp)}}}");
                    first = false;
                }
                js.Append("\n]\n}\n");
                File.WriteAllText(Out + "/chamber_world.json", js.ToString());
                Debug.Log($"[BWK] projection inspect: {ch.name} (d {dName}) -> {Out}/chamber_world.json");
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] projection inspect failed: " + e); EditorApplication.Exit(1); }
        }

        // ------------------------------------------------------------------------------------------------ capture views
        struct Views
        {
            public RunnerController runner; public RunnerCameraRig rig; public Camera cam; public CinemachineBrain brain;
        }

        static Views Setup()
        {
            var v = new Views
            {
                runner = Object.FindFirstObjectByType<RunnerController>(),
                rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include),
                cam = Camera.main
            };
            if (v.runner == null || v.rig == null || v.cam == null) throw new System.Exception("scene objects missing");
            v.brain = v.cam.GetComponent<CinemachineBrain>();
            if (v.brain) v.brain.enabled = false;
            v.runner.track.Rebuild();
            foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);
            return v;
        }

        static void SampleSlide(RunnerController runner)
        {
            var animator = runner.GetComponentInChildren<Animator>();
            if (animator == null || animator.runtimeAnimatorController == null) return;
            var slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
            if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
        }

        /// <summary>Rear gameplay views while the mascot passes the chamber (portrait, the approved rig) + front views.</summary>
        static void RenderAll(Views v, float dc, string tag, List<(string name, Vector3 pos, Vector3 fwd, Vector3 up)> cams)
        {
            var rear = new (string name, float d, float lat)[]
            {
                ("rear_far25", dc - 25f, 0f), ("rear_mid12", dc - 12f, 0f), ("rear_near5", dc - 5f, 0f),
                ("rear_beside3", dc - 3f, 0f), ("rear_laneL8", dc - 8f, -1.15f), ("rear_laneR8", dc - 8f, 1.15f),
            };
            foreach (var s in rear)
            {
                v.runner.TeleportTo(s.d, s.lat);
                SampleSlide(v.runner);
                v.rig.aspectOverride = 720f / 1280f;
                v.rig.Snap();
                var lens = v.rig.vcam.Lens;
                v.cam.transform.SetPositionAndRotation(v.rig.transform.position, v.rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                v.cam.fieldOfView = lens.FieldOfView;
                CaptureTools.Render(v.cam, 720, 1280, $"{Out}/{tag}_{s.name}_9x16.png");
                if (s.name == "rear_near5")
                    CaptureTools.Render(v.cam, 1080, 1920, $"{Out}/{tag}_{s.name}_1080x1920.png");
            }
            v.rig.aspectOverride = 0f;

            // R5 replica (CaptureTools R stills: solved 8.25 s lens at 220 m)
            {
                v.runner.TeleportTo(220f, 0f);
                SampleSlide(v.runner);
                var f = v.runner.Frame;
                Vector3 camPos = v.runner.transform.position + f.forward * 2.6f + f.flatUp * 1.3f + f.flatRight * 0.3f;
                Vector3 centre = v.runner.transform.position + f.flatUp * 0.6f;
                v.cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(centre - camPos, f.flatUp) * Quaternion.Euler(-2.9f, 9.1f, 0f));
                v.cam.fieldOfView = 52f;
                CaptureTools.Render(v.cam, 1280, 720, $"{Out}/{tag}_R5_front_16x9.png");
            }

            // the solved reference cameras (chamber-relative markers exported by build_projection_test.py)
            if (cams.Count > 0)
            {
                v.runner.TeleportTo(dc + 30f, 0f);   // mascot behind the front camera: chamber views only
                foreach (var c in cams)
                {
                    v.cam.transform.SetPositionAndRotation(c.pos, Quaternion.LookRotation(c.fwd, c.up));
                    v.cam.fieldOfView = 52f;
                    CaptureTools.Render(v.cam, 1280, 720, $"{Out}/{tag}_front_{c.name}_16x9.png");
                }
                Debug.Log($"[BWK] projection: {cams.Count} solved reference views rendered ({tag})");
            }
        }

        /// <summary>Projector cameras from SM_ProjCams.fbx: tiny cubes PC/PF/PU_{A,B} in the chamber model's own frame,
        /// imported with the chamber's import settings and mapped through the chamber mesh's localToWorld matrix.</summary>
        static List<(string name, Vector3 pos, Vector3 fwd, Vector3 up)> SolvedCams(Transform chamberMesh)
        {
            var list = new List<(string name, Vector3 pos, Vector3 fwd, Vector3 up)>();
            var model = ImportModel("SM_ProjCams.fbx");
            if (model == null) return list;
            var m = chamberMesh.localToWorldMatrix;
            var pts = new Dictionary<string, Vector3>();
            foreach (var mf in model.GetComponentsInChildren<MeshFilter>(true))
                if (mf.sharedMesh != null) pts[mf.name] = m.MultiplyPoint3x4(mf.sharedMesh.bounds.center);
            foreach (var t in new[] { "A", "B" })
                if (pts.TryGetValue("PC_" + t, out var c) && pts.TryGetValue("PF_" + t, out var f) && pts.TryGetValue("PU_" + t, out var u))
                {
                    list.Add(("0825" + t, c, f - c, u - c));
                    Debug.Log($"[BWK] projection camera 0825{t}: pos {V(c)} fwd {V((f - c).normalized)} up {V((u - c).normalized)}");
                }
            return list;
        }

        static MeshRenderer ChamberMesh(GameObject ch) =>
            ch.GetComponentsInChildren<MeshRenderer>(true).First(r => r.GetComponent<MeshFilter>() && r.GetComponent<MeshFilter>().sharedMesh
                && r.GetComponent<MeshFilter>().sharedMesh.name.StartsWith("SM_ChamberWindow_v2"));

        static Texture2D Tex(string file, bool srgb, bool normal = false)
        {
            string p = $"{ProjDir}/{file}";
            if (!File.Exists(p)) return null;
            var ti = (TextureImporter)AssetImporter.GetAtPath(p);
            if (ti != null)
            {
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = srgb;
                ti.mipmapEnabled = true;
                ti.alphaIsTransparency = file.Contains("Wall");
                ti.maxTextureSize = 2048;
                ti.textureCompression = TextureImporterCompression.CompressedHQ;
                ti.anisoLevel = 4;
                ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
        }

        static Material LitMat(string name, Texture2D baseTex, Texture2D ms, Texture2D nrm, float emission, bool transparent)
        {
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = name };
            m.SetTexture("_BaseMap", baseTex);
            m.SetColor("_BaseColor", Color.white);
            if (ms != null)
            {
                m.SetTexture("_MetallicGlossMap", ms);
                m.EnableKeyword("_METALLICSPECGLOSSMAP");
                m.SetFloat("_Smoothness", 1f);
            }
            if (nrm != null) { m.SetTexture("_BumpMap", nrm); m.EnableKeyword("_NORMALMAP"); }
            if (emission > 0f)
            {
                m.SetTexture("_EmissionMap", baseTex);
                m.SetColor("_EmissionColor", Color.white * emission);
                m.EnableKeyword("_EMISSION");
                m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
            }
            if (transparent)
            {
                m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f);
                m.SetOverrideTag("RenderType", "Transparent");
                m.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); m.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
                m.SetFloat("_SrcBlendAlpha", (float)BlendMode.One); m.SetFloat("_DstBlendAlpha", (float)BlendMode.OneMinusSrcAlpha);
                m.SetFloat("_ZWrite", 0f);
                m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                m.renderQueue = (int)RenderQueue.Transparent;
            }
            AssetDatabase.CreateAsset(m, $"{ProjDir}/{name}.mat");
            return m;
        }

        static GameObject ImportModel(string file)
        {
            string p = $"{ProjDir}/{file}";
            if (!File.Exists(p)) return null;
            AssetDatabase.ImportAsset(p, ImportAssetOptions.ForceSynchronousImport);
            var mi = (ModelImporter)AssetImporter.GetAtPath(p);
            mi.bakeAxisConversion = true; mi.globalScale = 1f; mi.useFileScale = true;
            mi.importCameras = false; mi.importLights = false; mi.importVisibility = false;
            mi.importNormals = ModelImporterNormals.Import; mi.importTangents = ModelImporterTangents.CalculateMikk;
            mi.meshCompression = ModelImporterMeshCompression.Off; mi.optimizeMeshPolygons = true; mi.optimizeMeshVertices = true;
            mi.weldVertices = true; mi.importBlendShapes = false;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            mi.materialLocation = ModelImporterMaterialLocation.InPrefab;
            mi.animationType = ModelImporterAnimationType.None; mi.importAnimation = false; mi.generateSecondaryUV = false;
            mi.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<GameObject>(p);
        }

        public static void BuildAndCapture()
        {
            try
            {
                Directory.CreateDirectory(Out);
                // 1) CURRENT level (opened read-only: never saved)
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                var ch0 = FindChamber(out _);
                var cams = SolvedCams(ChamberMesh(ch0).transform);
                var v0 = Setup();
                RenderAll(v0, TargetD, "current", cams);

                // 2) private COPY of the level with only the test chamber swapped
                Directory.CreateDirectory(Path.GetDirectoryName(TestScene));
                AssetDatabase.DeleteAsset(TestScene);
                if (!AssetDatabase.CopyAsset(SceneBuilder.ScenePath, TestScene)) throw new System.Exception("scene copy failed");
                var scene = EditorSceneManager.OpenScene(TestScene);
                var ch = FindChamber(out _);
                var model = ImportModel("SM_ChamberWindow_v2_proj.fbx");
                if (model == null) throw new System.Exception("projected chamber FBX missing");
                var projMesh = model.GetComponentsInChildren<MeshFilter>(true).Select(x => x.sharedMesh).First(x => x != null);
                var projSrc = model.GetComponentsInChildren<MeshRenderer>(true).First();
                var baseTex = Tex("T_Proj_Chamber_BaseColor.png", true);
                var msTex = Tex("T_Proj_Chamber_MetalSmooth.png", false);
                var nrmTex = Tex("T_Proj_Chamber_Normal.png", false, true);
                foreach (var old in AssetDatabase.FindAssets("t:Material", new[] { ProjDir }))
                    AssetDatabase.DeleteAsset(AssetDatabase.GUIDToAssetPath(old));
                var mMetal = LitMat("M_Proj_ChamberFrame", baseTex, msTex, nrmTex, 0f, false);
                var mInner = LitMat("M_Proj_ChamberInterior", baseTex, msTex, nrmTex, 0.55f, false);

                var mr = ChamberMesh(ch);
                var oldMats = mr.sharedMaterials;
                var oldMesh = mr.GetComponent<MeshFilter>().sharedMesh;
                Debug.Log($"[BWK] projection: original mesh {oldMesh.name} bounds {V(oldMesh.bounds.min)}..{V(oldMesh.bounds.max)} sub {oldMesh.subMeshCount}; projected {projMesh.name} bounds {V(projMesh.bounds.min)}..{V(projMesh.bounds.max)} sub {projMesh.subMeshCount}");
                var glass = oldMats.FirstOrDefault(m => m && m.name.Contains("Glass"));
                var mats = new Material[projMesh.subMeshCount];
                for (int i = 0; i < mats.Length; i++)
                {
                    string n = i < projSrc.sharedMaterials.Length && projSrc.sharedMaterials[i] ? projSrc.sharedMaterials[i].name : "";
                    mats[i] = n.Contains("Glass") ? glass : (n.Contains("Swirl") || n.Contains("Foam") || n.Contains("Drum") && !n.Contains("Rim")) ? mInner : mMetal;
                    Debug.Log($"[BWK] projection: submesh {i} '{n}' -> {(mats[i] ? mats[i].name : "null")}");
                }
                mr.GetComponent<MeshFilter>().sharedMesh = projMesh;
                mr.sharedMaterials = mats;
                // the projected interior carries the reference socks: hide the 3D socks of THIS chamber only
                int hidden = 0;
                foreach (var bob in ch.GetComponentsInChildren<FloatBob>(true)) { bob.gameObject.SetActive(false); hidden++; }

                // projected drum-wall patch around the window (alpha-feathered over the level's own wall)
                var patch = ImportModel("SM_ProjWallPatch.fbx");
                var wallTex = Tex("T_Proj_Wall_BaseColor.png", true);
                if (patch != null && wallTex != null)
                {
                    var mWall = LitMat("M_Proj_WallPatch", wallTex, null, null, 0.25f, true);
                    var go = (GameObject)PrefabUtility.InstantiatePrefab(patch);
                    go.name = "ProjWallPatch_" + ch.name;
                    go.transform.SetParent(ch.transform.parent, false);
                    go.transform.SetPositionAndRotation(ch.transform.position, ch.transform.rotation);
                    go.transform.localScale = ch.transform.localScale;
                    foreach (var r in go.GetComponentsInChildren<MeshRenderer>(true))
                    {
                        r.sharedMaterials = Enumerable.Repeat(mWall, r.sharedMaterials.Length).ToArray();
                        r.shadowCastingMode = ShadowCastingMode.Off;
                    }
                }
                EditorSceneManager.MarkSceneDirty(scene);
                EditorSceneManager.SaveScene(scene);
                Debug.Log($"[BWK] projection: test scene saved {TestScene} (chamber {ch.name}, {hidden} 3D socks hidden, patch {(patch != null)})");

                var v1 = Setup();
                RenderAll(v1, TargetD, "projected", cams);
                AssetDatabase.SaveAssets();
                Debug.Log("[BWK] projection BuildAndCapture done -> " + Path.GetFullPath(Out));
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] projection build failed: " + e); EditorApplication.Exit(1); }
        }
    }
}
