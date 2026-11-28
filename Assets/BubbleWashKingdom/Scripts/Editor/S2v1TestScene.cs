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

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Lead a557ee90 2026-11-27 (owner 22:33: "my actual game is the Unity version ... selectively transfer genuinely superior Blender
    /// assets into an ISOLATED Unity test scene ... preserve everything that already looks better ... show me actual Unity comparison
    /// screenshots before accepting any replacement").
    /// Reads a S2 Tunnel v1 export (Tools/Blender/scripts/s2v1/s2v1_export_unity.py: manifest_unity.json + meshes/*.bwkm in UNITY WORLD
    /// coordinates + textures/) and puts the v1 parts into an IN-MEMORY copy of the saved S2 scene, set up exactly like the 'Unity current'
    /// R2 baseline (TextureGenerator + MaterialLibrary + saved scene + PreviewRefreshDomains). The main scene is NEVER saved.
    /// Element groups (v1 part tags <-> the old Unity parts they replace; old triangles are trimmed by track distance with the same rule as
    /// s2v1_env.trim_old: nearest track frame, d in [replaced_d0, replaced_d1] (stars from stars_from), within 9 m of the track):
    ///   drum  = drum                         <-> old tunnel wall (MouthDrum_r7_*, Tunnel_*)
    ///   bands = band, band_lip               <-> old violet rims (LedRim_s2, DrumRim / RimLight rings)
    ///   gold  = gold_ring, bulb_socket, bulb <-> old gold bulb rings (MarqueeRing_s2*, Gold / GoldDark / Bulb rings)
    ///   stars = star, star_glow, other       <-> old neon stars + star glows
    /// Material flavours: bwk = the project's own Unity materials by tag (M_HatchViolet_s2, M_RimGlow_s2, M_Gold, M_GoldDark, M_Bulb,
    /// M_Neon_*; = v1 GEOMETRY with today's Unity look; v1 drum / star_glow are not shown in bwk), urp = URP Lit from the Blender values
    /// and bakes in the manifest (= the full v1 look).
    /// Batch (heavy, through the lock):
    ///   Tools/unity_run.sh BubbleWash.EditorTools.S2v1TestScene.PreviewBatch lead_s2v1_unity -bwkIn Tools/Blender/work/s2v1/unity_v1/latest
    ///     -bwkOut Captures/s2v1/unity/NAME [-bwkVariants "current;bands:bwk;gold:bwk;stars:bwk;bands+gold+stars:bwk"] [-bwkDists 33.5,38.5,44]
    ///     [-bwkSave "bands+gold+stars:bwk"]
    /// Writes per variant DIR/&lt;variant&gt;/R2_16x9.png, R2_bg_16x9.png (mascot hidden), rig_dXX.X_9x16.png + DIR/summary.txt; the labelled
    /// owner sheet comes from Tools/s2v1_unity_sheet.py. -bwkSave also writes the ISOLATED scene Scenes/Private/S2v1_Test.unity (gitignored)
    /// with its generated meshes / materials / textures in Art/S2v1Test/ (gitignored) for a Play Mode recording (BWK_PLAY_SCENE).
    /// </summary>
    public static class S2v1TestScene
    {
        public const string TestScenePath = "Assets/BubbleWashKingdom/Scenes/Private/S2v1_Test.unity";
        const string AssetDir = "Assets/BubbleWashKingdom/Art/S2v1Test";
        static readonly CultureInfo IC = CultureInfo.InvariantCulture;
        static readonly string[] Groups = { "drum", "bands", "gold", "stars" };

        // ------------------------------------------------------------------------------------------- manifest (JsonUtility)
        [System.Serializable] public class MPart { public string name, part, color, file; public int tris; public bool hide_render; }
        [System.Serializable] public class MMat
        {
            public string name, shader, procedural, tex_base, tex_normal, tex_roughness, tex_metallic, tex_emission, tex_ao;
            public float[] base_color, emission_color;
            public float metallic, roughness, emission_strength, alpha, coat, transmission, normal_strength;
        }
        [System.Serializable] public class MRoot
        {
            public string built, source_modules;
            public float replaced_d0, replaced_d1, stars_from;
            public MPart[] parts; public MMat[] materials;
        }

        static string Arg(string key)
        {
            var a = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == key) return a[i + 1];
            return null;
        }

        static string GroupOfPart(string part)
        {
            switch (part)
            {
                case "drum": return "drum";
                case "band": case "band_lip": return "bands";
                case "gold_ring": case "bulb_socket": case "bulb": return "gold";
                case "star": case "star_glow": case "other": return "stars";
                default: return null;
            }
        }

        // ------------------------------------------------------------------------------------------- .bwkm reader
        static float[] ReadFloats(BinaryReader br, int count)
        {
            var bytes = br.ReadBytes(count * 4);
            var f = new float[count];
            System.Buffer.BlockCopy(bytes, 0, f, 0, bytes.Length);
            return f;
        }

        static Mesh ReadBwkm(string path, out int[] subMat)
        {
            using (var br = new BinaryReader(File.OpenRead(path)))
            {
                var magic = Encoding.ASCII.GetString(br.ReadBytes(4));
                if (magic != "BWKM") throw new IOException("not a .bwkm file: " + path);
                int ver = br.ReadInt32(), n = br.ReadInt32(), flags = br.ReadInt32();
                var p = ReadFloats(br, n * 3); var q = ReadFloats(br, n * 3);
                var pos = new Vector3[n]; var nrm = new Vector3[n];
                for (int i = 0; i < n; i++) { pos[i] = new Vector3(p[3 * i], p[3 * i + 1], p[3 * i + 2]); nrm[i] = new Vector3(q[3 * i], q[3 * i + 1], q[3 * i + 2]); }
                var uvs = new List<Vector2[]>();
                for (int k = 0; k < 2; k++)
                {
                    if ((flags & (1 << k)) == 0) continue;
                    var u = ReadFloats(br, n * 2); var uv = new Vector2[n];
                    for (int i = 0; i < n; i++) uv[i] = new Vector2(u[2 * i], u[2 * i + 1]);
                    uvs.Add(uv);
                }
                int sc = br.ReadInt32();
                subMat = new int[sc];
                var subs = new List<int[]>();
                for (int s = 0; s < sc; s++)
                {
                    subMat[s] = br.ReadInt32();
                    int c = br.ReadInt32();
                    var raw = br.ReadBytes(c * 4); var idx = new int[c];
                    System.Buffer.BlockCopy(raw, 0, idx, 0, raw.Length);
                    subs.Add(idx);
                }
                var m = new Mesh { name = Path.GetFileNameWithoutExtension(path), indexFormat = n > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
                m.SetVertices(pos); m.SetNormals(nrm);
                for (int k = 0; k < uvs.Count; k++) m.SetUVs(k, uvs[k]);
                m.subMeshCount = sc;
                for (int s = 0; s < sc; s++) m.SetTriangles(subs[s], s, false);
                m.RecalculateBounds();
                if (uvs.Count > 0) m.RecalculateTangents();
                return m;
            }
        }

        // ------------------------------------------------------------------------------------------- track distance (= s2v1_env.trim_old)
        class TrackSampler
        {
            readonly float[] d; readonly Vector3[] pos, fwd;
            public TrackSampler(TrackPath t, float d0, float d1, float step = 0.25f)
            {
                var ds = new List<float>(); for (float x = d0; x <= d1 + 1e-3f; x += step) ds.Add(x);
                d = ds.ToArray(); pos = new Vector3[d.Length]; fwd = new Vector3[d.Length];
                for (int i = 0; i < d.Length; i++) { var f = t.Evaluate(d[i]); pos[i] = f.position; fwd[i] = f.forward; }
            }
            public Bounds Bounds(float pad)
            {
                var b = new Bounds(pos[0], Vector3.zero);
                foreach (var p in pos) b.Encapsulate(p);
                b.Expand(pad * 2f);
                return b;
            }
            public float Distance(Vector3 p, out float radial)
            {
                int best = 0; float bd = float.MaxValue;
                for (int i = 0; i < pos.Length; i++) { float q = (p - pos[i]).sqrMagnitude; if (q < bd) { bd = q; best = i; } }
                radial = Mathf.Sqrt(bd);
                return d[best] + Vector3.Dot(p - pos[best], fwd[best]);
            }
        }

        // ------------------------------------------------------------------------------------------- old parts
        static string GetPath(Transform t)
        {
            var sb = new StringBuilder(t.name);
            for (var p = t.parent; p != null; p = p.parent) sb.Insert(0, p.name + "/");
            return sb.ToString();
        }

        /// <summary>Element group of an old Unity renderer's submesh (same name rules as S2v1Export.Category, rings split by material).</summary>
        static string OldGroup(Renderer r, Material m, Transform runnerRoot)
        {
            if (runnerRoot != null && r.transform.IsChildOf(runnerRoot)) return null;
            string path = GetPath(r.transform), n = r.gameObject.name;
            if (path.Contains("MouthDrum_r7") || path.Contains("/Tunnel/") || n.StartsWith("Tunnel_")) return "drum";
            bool ring = n.Contains("LedRim") || n.Contains("MarqueeRing") || n.Contains("MouthDrumRing") || n.Contains("MouthDrumRim")
                || n.Contains("DrumRim") || n.StartsWith("SM_Ring") || n.StartsWith("Ring_") || path.Contains("/Rings/");
            if (ring)
            {
                string mn = m != null ? m.name : "";
                return (mn.StartsWith("M_Gold") || mn.StartsWith("M_Bulb")) ? "gold" : "bands";
            }
            if (n.Contains("Starburst") || path.Contains("TunnelStars") || n.Contains("Star")) return "stars";
            return null;
        }

        class OldPart
        {
            public Renderer r; public MeshFilter mf; public Mesh orig; public string[] subGroup;
            public List<bool[]> keep = new List<bool[]>();         // per submesh: triangle kept when its group is replaced
            public int[] removable;                                  // per submesh: triangles that would be removed
            public Dictionary<string, Mesh> cache = new Dictionary<string, Mesh>();
            public bool wasEnabled;
        }

        static Mesh TrimmedCopy(OldPart op, HashSet<string> replaced, out int kept)
        {
            kept = 0;
            using (var ro = Mesh.AcquireReadOnlyMeshData(op.orig))
            {
                var md = ro[0];
                var attrs = new List<VertexAttributeDescriptor>();
                foreach (VertexAttribute a in System.Enum.GetValues(typeof(VertexAttribute)))
                    if (md.HasVertexAttribute(a))
                        attrs.Add(new VertexAttributeDescriptor(a, md.GetVertexAttributeFormat(a), md.GetVertexAttributeDimension(a), md.GetVertexAttributeStream(a)));
                var lists = new List<int[]>();
                for (int s = 0; s < md.subMeshCount; s++)
                {
                    var desc = md.GetSubMesh(s);
                    if (desc.topology != MeshTopology.Triangles) { lists.Add(new int[0]); continue; }
                    var ia = new NativeArray<int>(desc.indexCount, Allocator.Temp);
                    md.GetIndices(ia, s, true);
                    var all = ia.ToArray(); ia.Dispose();
                    bool trim = s < op.subGroup.Length && op.subGroup[s] != null && replaced.Contains(op.subGroup[s]);
                    if (!trim) { lists.Add(all); kept += all.Length / 3; continue; }
                    var k = op.keep[s]; var outL = new List<int>(all.Length);
                    for (int t = 0; t * 3 + 2 < all.Length; t++)
                        if (k[t]) { outL.Add(all[3 * t]); outL.Add(all[3 * t + 1]); outL.Add(all[3 * t + 2]); }
                    lists.Add(outL.ToArray()); kept += outL.Count / 3;
                }
                var wa = Mesh.AllocateWritableMeshData(1);
                var w = wa[0];
                w.SetVertexBufferParams(md.vertexCount, attrs.ToArray());
                int streams = attrs.Count == 0 ? 0 : attrs.Max(a => a.stream) + 1;
                for (int s = 0; s < streams; s++)
                {
                    if (!attrs.Any(a => a.stream == s)) continue;
                    var dst = w.GetVertexData<byte>(s); var src = md.GetVertexData<byte>(s);
                    NativeArray<byte>.Copy(src, dst, Mathf.Min(src.Length, dst.Length));
                }
                int total = lists.Sum(l => l.Length);
                w.SetIndexBufferParams(total, IndexFormat.UInt32);
                var ib = w.GetIndexData<uint>();
                int at = 0;
                foreach (var l in lists) foreach (var v in l) ib[at++] = (uint)v;
                w.subMeshCount = lists.Count;
                at = 0;
                for (int s = 0; s < lists.Count; s++)
                {
                    w.SetSubMesh(s, new SubMeshDescriptor(at, lists[s].Length, MeshTopology.Triangles), MeshUpdateFlags.DontValidateIndices);
                    at += lists[s].Length;
                }
                var m = new Mesh { name = op.orig.name + "_s2v1trim" };
                Mesh.ApplyAndDisposeWritableMeshData(wa, m, MeshUpdateFlags.DontRecalculateBounds);
                m.bounds = op.orig.bounds;
                return m;
            }
        }

        static List<OldPart> CollectOldParts(Transform runnerRoot, TrackSampler ts, Bounds zone, float d0, float d1, float starsFrom, StringBuilder log)
        {
            var list = new List<OldPart>();
            var removedBy = Groups.ToDictionary(g => g, g => 0);
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
            {
                if (!(r is MeshRenderer) || !r.enabled || !r.gameObject.activeInHierarchy) continue;
                if (!zone.Intersects(r.bounds)) continue;
                var mf = r.GetComponent<MeshFilter>();
                if (mf == null || mf.sharedMesh == null) continue;
                var mats = r.sharedMaterials;
                var mesh = mf.sharedMesh;
                var subGroup = new string[mesh.subMeshCount];
                bool any = false;
                for (int s = 0; s < subGroup.Length; s++) { subGroup[s] = OldGroup(r, s < mats.Length ? mats[s] : null, runnerRoot); any |= subGroup[s] != null; }
                if (!any) continue;
                var op = new OldPart { r = r, mf = mf, orig = mesh, subGroup = subGroup, removable = new int[subGroup.Length], wasEnabled = r.enabled };
                var l2w = r.transform.localToWorldMatrix;
                int totalTris = 0;
                using (var ro = Mesh.AcquireReadOnlyMeshData(mesh))
                {
                    var md = ro[0];
                    var va = new NativeArray<Vector3>(md.vertexCount, Allocator.Temp);
                    md.GetVertices(va);
                    var verts = va.ToArray(); va.Dispose();
                    for (int s = 0; s < md.subMeshCount; s++)
                    {
                        var desc = md.GetSubMesh(s);
                        if (desc.topology == MeshTopology.Triangles) totalTris += desc.indexCount / 3;
                        if (subGroup[s] == null || desc.topology != MeshTopology.Triangles) { op.keep.Add(null); continue; }
                        var ia = new NativeArray<int>(desc.indexCount, Allocator.Temp);
                        md.GetIndices(ia, s, true);
                        var idx = ia.ToArray(); ia.Dispose();
                        int nt = idx.Length / 3; var keep = new bool[nt];
                        float from = subGroup[s] == "stars" ? starsFrom : d0;
                        for (int t = 0; t < nt; t++)
                        {
                            var c = l2w.MultiplyPoint3x4((verts[idx[3 * t]] + verts[idx[3 * t + 1]] + verts[idx[3 * t + 2]]) / 3f);
                            float dist = ts.Distance(c, out float radial);
                            bool kill = dist >= from && dist <= d1 && radial < 9f;
                            keep[t] = !kill;
                            if (kill) op.removable[s]++;
                        }
                        op.keep.Add(keep);
                        removedBy[subGroup[s]] += op.removable[s];
                    }
                }
                if (op.removable.Sum() == 0) continue;
                list.Add(op);
                string rp = GetPath(r.transform);
                log.AppendLine(string.Format(IC, "old {0,-70} groups [{1}] removable tris [{2}] of {3}", rp.Length > 70 ? "..." + rp.Substring(rp.Length - 67) : rp,
                    string.Join(",", subGroup.Select(g => g ?? "-")), string.Join(",", op.removable), totalTris));
            }
            log.AppendLine("old triangles in the replaced range by group: " + string.Join(", ", removedBy.Select(kv => kv.Key + " " + kv.Value)));
            return list;
        }

        static void ApplyOld(List<OldPart> olds, HashSet<string> replaced)
        {
            foreach (var op in olds)
            {
                var mine = new HashSet<string>(op.subGroup.Where(g => g != null && replaced.Contains(g)));
                if (mine.Count == 0) { op.mf.sharedMesh = op.orig; op.r.enabled = op.wasEnabled; continue; }
                string key = string.Join("+", mine.OrderBy(x => x));
                if (!op.cache.TryGetValue(key, out var m))
                {
                    m = TrimmedCopy(op, mine, out int kept);
                    if (kept == 0) { Object.DestroyImmediate(m); m = null; }
                    op.cache[key] = m;
                }
                if (m == null) { op.r.enabled = false; op.mf.sharedMesh = op.orig; }
                else { op.mf.sharedMesh = m; op.r.enabled = op.wasEnabled; }
            }
        }

        // ------------------------------------------------------------------------------------------- materials
        static Material Lib(string name) => MaterialLibrary.Get(name);

        static string Cap(string c) => string.IsNullOrEmpty(c) ? "Yellow" : char.ToUpperInvariant(c[0]) + c.Substring(1).ToLowerInvariant();

        /// <summary>bwk flavour: today's Unity material for a v1 part (null = not shown in this flavour).</summary>
        static Material BwkMaterial(string part, string color)
        {
            switch (part)
            {
                case "band": return Lib("M_HatchViolet_s2");
                case "band_lip": return Lib("M_RimGlow_s2");
                case "gold_ring": return Lib("M_Gold");
                case "bulb_socket": return Lib("M_GoldDark");
                case "bulb": return Lib("M_Bulb");
                case "star": return Lib("M_Neon_" + Cap(color)) ?? Lib("M_Neon_Yellow");
                case "other": return Lib("M_GoldDark");
                default: return null;                        // drum (needs the v1 bakes) and star_glow plates: urp flavour only
            }
        }

        static Color LinToGamma(float r, float g, float b, float a = 1f) =>
            new Color(Mathf.LinearToGammaSpace(Mathf.Max(0f, r)), Mathf.LinearToGammaSpace(Mathf.Max(0f, g)), Mathf.LinearToGammaSpace(Mathf.Max(0f, b)), a);

        static Texture2D ImportTexture(string inDir, string rel, bool linear, bool normal, string texDir)
        {
            if (string.IsNullOrEmpty(rel)) return null;
            string src = Path.Combine(inDir, rel);
            if (!File.Exists(src)) { Debug.LogWarning("[BWK] s2v1 texture missing: " + src); return null; }
            Directory.CreateDirectory(texDir);
            string dst = $"{texDir}/{Path.GetFileName(src)}";
            File.Copy(src, dst, true);
            AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport);
            var ti = AssetImporter.GetAtPath(dst) as TextureImporter;
            if (ti != null)
            {
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = !linear && !normal;
                ti.mipmapEnabled = true; ti.anisoLevel = 8; ti.wrapModeU = TextureWrapMode.Repeat; ti.wrapModeV = TextureWrapMode.Clamp;
                ti.textureCompression = TextureImporterCompression.CompressedHQ;
                ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(dst);
        }

        /// <summary>urp flavour: URP Lit from the Blender Principled values / bakes (colours converted Blender linear -> Unity gamma inputs).</summary>
        static Material UrpMaterial(MMat mm, string inDir, string texDir)
        {
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "S2V1_" + mm.name };
            var bc = mm.base_color != null && mm.base_color.Length >= 3 ? mm.base_color : new[] { 0.5f, 0.5f, 0.5f, 1f };
            m.SetColor("_BaseColor", LinToGamma(bc[0], bc[1], bc[2], bc.Length > 3 ? bc[3] : 1f));
            m.SetFloat("_Metallic", Mathf.Clamp01(mm.metallic));
            m.SetFloat("_Smoothness", Mathf.Clamp01(1f - mm.roughness));
            var baseTex = ImportTexture(inDir, mm.tex_base, false, false, texDir);
            if (baseTex) { m.SetTexture("_BaseMap", baseTex); m.SetColor("_BaseColor", Color.white); }
            var nrmTex = ImportTexture(inDir, mm.tex_normal, true, true, texDir);
            if (nrmTex) { m.SetTexture("_BumpMap", nrmTex); m.SetFloat("_BumpScale", mm.normal_strength > 0f ? mm.normal_strength : 1f); m.EnableKeyword("_NORMALMAP"); }
            var ec = mm.emission_color != null && mm.emission_color.Length >= 3 ? mm.emission_color : new[] { 0f, 0f, 0f };
            float es = mm.emission_strength;
            var emTex = ImportTexture(inDir, mm.tex_emission, false, false, texDir);
            if (es > 1e-4f && (ec[0] + ec[1] + ec[2] > 1e-4f || emTex))
            {
                m.EnableKeyword("_EMISSION");
                m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                m.SetColor("_EmissionColor", emTex ? LinToGamma(es, es, es) : LinToGamma(ec[0] * es, ec[1] * es, ec[2] * es));
                if (emTex) m.SetTexture("_EmissionMap", emTex);
            }
            else m.DisableKeyword("_EMISSION");
            if (mm.alpha < 0.98f || mm.transmission > 0.5f)
            {
                float a = mm.transmission > 0.5f ? Mathf.Min(mm.alpha, 0.45f) : mm.alpha;
                var col = m.GetColor("_BaseColor"); col.a = a; m.SetColor("_BaseColor", col);
                m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f);
                m.SetOverrideTag("RenderType", "Transparent");
                m.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha); m.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha); m.SetInt("_ZWrite", 0);
                m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                m.renderQueue = (int)RenderQueue.Transparent;
            }
            m.enableInstancing = true;
            return m;
        }

        // ------------------------------------------------------------------------------------------- v1 parts
        class V1Part
        {
            public MPart info; public string group; public GameObject go; public MeshRenderer mr; public Mesh mesh; public int[] subMat;
            public Material[] bwk, urp;
        }

        static List<V1Part> LoadV1(MRoot man, string inDir, Transform parent, int layer, StringBuilder log)
        {
            string texDir = $"{AssetDir}/Textures";
            var urpMats = new Material[man.materials != null ? man.materials.Length : 0];
            for (int i = 0; i < urpMats.Length; i++) urpMats[i] = UrpMaterial(man.materials[i], inDir, texDir);
            var parts = new List<V1Part>();
            foreach (var p in man.parts)
            {
                string g = GroupOfPart(p.part);
                if (g == null || p.part == "drum_hp") continue;
                string path = Path.Combine(inDir, p.file);
                if (!File.Exists(path)) { log.AppendLine("v1 part file missing: " + path); continue; }
                var mesh = ReadBwkm(path, out var subMat);
                var go = new GameObject("S2V1_" + p.name) { layer = layer };
                go.transform.SetParent(parent, false);
                var mf = go.AddComponent<MeshFilter>(); mf.sharedMesh = mesh;
                var mr = go.AddComponent<MeshRenderer>();
                mr.shadowCastingMode = ShadowCastingMode.Off; mr.receiveShadows = true;
                mr.reflectionProbeUsage = ReflectionProbeUsage.BlendProbes; mr.lightProbeUsage = LightProbeUsage.BlendProbes;
                var bwk = subMat.Select(_ => BwkMaterial(p.part, p.color)).ToArray();
                var urp = subMat.Select(mi => mi >= 0 && mi < urpMats.Length ? urpMats[mi] : null).ToArray();
                parts.Add(new V1Part { info = p, group = g, go = go, mr = mr, mesh = mesh, subMat = subMat, bwk = bwk, urp = urp });
                log.AppendLine(string.Format(IC, "v1 {0,-28} {1,-12} group {2,-6} tris {3,7} submeshes {4} bwk [{5}] urp [{6}]", p.name, p.part, g, p.tris,
                    subMat.Length, string.Join(",", bwk.Select(m => m ? m.name : "-")), string.Join(",", urp.Select(m => m ? m.name : "-"))));
            }
            return parts;
        }

        static void ApplyV1(List<V1Part> parts, HashSet<string> groups, string flavour)
        {
            foreach (var p in parts)
            {
                bool on = groups.Contains(p.group) && !p.info.hide_render;
                var mats = flavour == "urp" ? p.urp : p.bwk;
                if (on && mats.Any(m => m == null)) on = false;         // a part without a material in this flavour is not shown
                p.go.SetActive(on);
                if (on) p.mr.sharedMaterials = mats;
            }
        }

        // ------------------------------------------------------------------------------------------- cameras (= ProjectionS2Test / CaptureHero)
        static void PoseRunner(RunnerController runner, float d)
        {
            runner.TeleportTo(d, 0f);
            var animator = runner.GetComponentInChildren<Animator>();
            if (animator != null && animator.runtimeAnimatorController != null)
            {
                var slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
            }
        }

        static void PoseR2(RunnerController runner, Camera cam)
        {
            PoseRunner(runner, SceneBuilder.HeroMouthDistance);
            var f = runner.Frame;
            Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
            Vector3 cp = runner.transform.position - fwd * CaptureTools.R2Back + Vector3.up * CaptureTools.R2Height + right * CaptureTools.R2Lat;
            cam.transform.SetPositionAndRotation(cp, Quaternion.LookRotation(fwd, Vector3.up) * Quaternion.Euler(CaptureTools.R2Pitch, CaptureTools.R2Yaw, 0f));
            cam.fieldOfView = CaptureTools.R2Fov;
        }

        static void PoseRig(RunnerController runner, Camera cam, float d, float aspect)
        {
            PoseRunner(runner, d);
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            rig.aspectOverride = aspect;
            rig.Snap();
            var lens = rig.vcam.Lens;
            cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
            cam.fieldOfView = lens.FieldOfView;
        }

        static List<Renderer> MascotRenderers(RunnerController runner) =>
            runner.GetComponentsInChildren<Renderer>(true).Where(r => r.enabled && !(r is ParticleSystemRenderer) && !(r is TrailRenderer)).ToList();

        static (string name, HashSet<string> groups, string flavour) ParseVariant(string spec)
        {
            spec = spec.Trim();
            string flavour = "bwk", body = spec;
            int c = spec.LastIndexOf(':');
            if (c > 0) { flavour = spec.Substring(c + 1).Trim().ToLowerInvariant(); body = spec.Substring(0, c).Trim(); }
            var groups = new HashSet<string>(body == "current" ? new string[0] : (body == "all" ? Groups : body.Split('+').Select(x => x.Trim()).Where(x => x.Length > 0)));
            string name = body == "current" ? "current" : string.Join("+", groups.OrderBy(g => System.Array.IndexOf(Groups, g))) + "_" + flavour;
            return (name, groups, flavour);
        }

        // ------------------------------------------------------------------------------------------- batch
        public static void PreviewBatch()
        {
            try
            {
                string inDir = Arg("-bwkIn") ?? "Tools/Blender/work/s2v1/unity_v1/latest";
                string outDir = Arg("-bwkOut") ?? "Captures/s2v1/unity/preview";
                string variantsArg = Arg("-bwkVariants") ?? "current;bands:bwk;gold:bwk;stars:bwk;bands+gold+stars:bwk";
                var dists = (Arg("-bwkDists") ?? "33.5,38.5,44").Split(',').Select(s => float.Parse(s, IC)).ToArray();
                string saveSpec = Arg("-bwkSave");
                Directory.CreateDirectory(outDir);
                var log = new StringBuilder();
                var manPath = Path.Combine(inDir, "manifest_unity.json");
                var man = JsonUtility.FromJson<MRoot>(File.ReadAllText(manPath));
                log.AppendLine($"S2v1 Unity test (lead a557ee90): export {inDir} built {man.built} from {man.source_modules}; replaced d {man.replaced_d0}-{man.replaced_d1}, stars from {man.stars_from}");

                // the same in-memory setup as the 'Unity current' R2 baseline (ProjectionS2Test.Setup / AgentPreviewBatch)
                TextureGenerator.Run();
                MaterialLibrary.Run();
                var scene = EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                SceneBuilder.PreviewRefreshDomains();
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var cam = Camera.main;
                var brain = cam.GetComponent<CinemachineBrain>();
                if (brain) brain.enabled = false;
                var track = runner.track != null ? runner.track : Object.FindFirstObjectByType<TrackPath>();
                var ts = new TrackSampler(track, Mathf.Max(0f, Mathf.Min(man.replaced_d0, man.stars_from) - 15f), man.replaced_d1 + 15f);
                var zone = ts.Bounds(10f);

                var oldParts = CollectOldParts(runner.transform, ts, zone, man.replaced_d0, man.replaced_d1, man.stars_from, log);
                int layer = oldParts.Count > 0 ? oldParts[0].r.gameObject.layer : 0;
                var root = new GameObject("S2V1_Test");
                var env = GameObject.Find("Level01_RainbowRush");
                if (env != null) root.transform.SetParent(env.transform, false);
                var v1 = LoadV1(man, inDir, root.transform, layer, log);

                var mascot = MascotRenderers(runner);
                var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
                var specs = variantsArg.Split(';').Where(s => s.Trim().Length > 0).Select(ParseVariant).ToList();
                foreach (var (name, groups, flavour) in specs)
                {
                    ApplyOld(oldParts, groups);
                    ApplyV1(v1, groups, flavour);
                    string vd = $"{outDir}/{name}";
                    Directory.CreateDirectory(vd);
                    PoseR2(runner, cam);
                    CaptureTools.Render(cam, 1280, 720, $"{vd}/R2_16x9.png");
                    foreach (var r in mascot) r.enabled = false;
                    CaptureTools.Render(cam, 1280, 720, $"{vd}/R2_bg_16x9.png");
                    foreach (var r in mascot) r.enabled = true;
                    foreach (float d in dists)
                    {
                        PoseRig(runner, cam, d, 720f / 1280f);
                        CaptureTools.Render(cam, 720, 1280, string.Format(IC, "{0}/rig_d{1:0.0}_9x16.png", vd, d));
                    }
                    int shown = v1.Count(p => p.go.activeSelf);
                    log.AppendLine($"variant {name}: groups [{string.Join(",", groups)}] flavour {flavour}: {shown} v1 parts shown -> {vd}");
                }
                if (rig) rig.aspectOverride = 0f;

                if (!string.IsNullOrEmpty(saveSpec))
                {
                    var (sname, sgroups, sflavour) = ParseVariant(saveSpec);
                    ApplyOld(oldParts, sgroups);
                    ApplyV1(v1, sgroups, sflavour);
                    SaveIsolated(scene, v1, oldParts, log);
                    log.AppendLine($"SAVED isolated test scene {TestScenePath} = variant {sname} (main scene untouched)");
                }
                if (brain) brain.enabled = true;
                File.WriteAllText($"{outDir}/summary.txt", log.ToString());
                Debug.Log("[BWK] S2v1 Unity test:\n" + log);
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK] S2v1 Unity test failed: " + e); EditorApplication.Exit(1); }
        }

        /// <summary>Persist the generated meshes / materials as assets (gitignored Art/S2v1Test/) and save the open, modified copy of the
        /// level as the ISOLATED scene Scenes/Private/S2v1_Test.unity (saveAsCopy: the main scene file is never written).</summary>
        static void SaveIsolated(UnityEngine.SceneManagement.Scene scene, List<V1Part> v1, List<OldPart> olds, StringBuilder log)
        {
            Directory.CreateDirectory($"{AssetDir}/Meshes");
            Directory.CreateDirectory($"{AssetDir}/Materials");
            void Persist(Object o, string path)
            {
                if (o == null || AssetDatabase.Contains(o)) return;
                AssetDatabase.DeleteAsset(path);
                AssetDatabase.CreateAsset(o, path);
            }
            foreach (var p in v1)
            {
                if (!p.go.activeSelf) { Object.DestroyImmediate(p.go); continue; }
                Persist(p.mesh, $"{AssetDir}/Meshes/{p.mesh.name}.asset");
                foreach (var m in p.mr.sharedMaterials) Persist(m, $"{AssetDir}/Materials/{m.name}.mat");
            }
            int n = 0;
            foreach (var op in olds)
            {
                var m = op.mf.sharedMesh;
                if (m != null && m != op.orig) Persist(m, $"{AssetDir}/Meshes/{m.name}_{n++:000}.asset");
            }
            foreach (var vol in Object.FindObjectsByType<Volume>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                string pp = vol.sharedProfile != null ? AssetDatabase.GetAssetPath(vol.sharedProfile) : "";
                if (pp.EndsWith("PostFX_Preview.asset"))
                {
                    string dst = $"{AssetDir}/PostFX_S2v1Test.asset";
                    AssetDatabase.DeleteAsset(dst);
                    AssetDatabase.CopyAsset(pp, dst);
                    vol.sharedProfile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(dst);
                }
            }
            AssetDatabase.SaveAssets();
            Directory.CreateDirectory(Path.GetDirectoryName(TestScenePath));
            if (!EditorSceneManager.SaveScene(scene, TestScenePath, true)) throw new System.Exception("saving " + TestScenePath + " failed");
            log.AppendLine($"persisted {v1.Count(p => p != null && p.go != null)} v1 parts + {n} trimmed old meshes in {AssetDir}");
        }
    }
}
