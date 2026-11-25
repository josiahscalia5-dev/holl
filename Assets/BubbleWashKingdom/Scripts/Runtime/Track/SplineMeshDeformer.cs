using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash
{
    /// <summary>
    /// Bends a straight modular mesh (authored in Blender running along +Z from its minimum to maximum Z,
    /// cross-section in the XY plane) along a <see cref="TrackPath"/>. Copies are tiled and evenly stretched so
    /// they meet exactly between two distances. Normals and tangents follow the frame basis. Optionally writes
    /// the track distance into UV0.y so flowing-water shaders scroll continuously across module seams.
    /// </summary>
    public static class SplineMeshDeformer
    {
        public struct Options
        {
            public float startDistance;
            public float endDistance;
            public bool useBank;          // banked frame (slide) or flat frame (tunnel shell, pipes)
            public float lateralOffset;   // meters along frame right
            public float verticalOffset;  // meters along frame up
            public Vector3 scale;         // per-axis scale applied to the source cross-section (z ignored)
            public float distanceUVTile;  // > 0: UV0.y = distance / tile for the listed submeshes
            public int[] distanceUVSubmeshes; // null = every submesh
            public float preferredModuleLength; // <= 0: use the source mesh length
        }

        public static Options DefaultOptions(float start, float end) => new Options
        {
            startDistance = start,
            endDistance = end,
            useBank = true,
            scale = Vector3.one,
            distanceUVTile = 0f,
        };

        public static Mesh Bend(Mesh source, TrackPath track, Transform target, Options o, string name = null)
        {
            var srcV = source.vertices;
            var srcN = source.normals;
            var srcT = source.tangents;
            var srcUV = new List<Vector2>(); source.GetUVs(0, srcUV);
            var srcUV1 = new List<Vector2>(); source.GetUVs(1, srcUV1);
            var srcC = source.colors32;
            int vc = srcV.Length;
            if (vc == 0) return null;
            if (o.scale == Vector3.zero) o.scale = Vector3.one;

            float minZ = float.MaxValue, maxZ = float.MinValue;
            for (int i = 0; i < vc; i++) { minZ = Mathf.Min(minZ, srcV[i].z); maxZ = Mathf.Max(maxZ, srcV[i].z); }
            float srcLen = Mathf.Max(1e-4f, maxZ - minZ);
            float moduleLen = o.preferredModuleLength > 0f ? o.preferredModuleLength : srcLen;

            float span = Mathf.Max(0.01f, o.endDistance - o.startDistance);
            int copies = Mathf.Max(1, Mathf.RoundToInt(span / moduleLen));
            float copyLen = span / copies;

            // Which vertices belong to submeshes that get distance UVs.
            var distanceUV = new bool[vc];
            if (o.distanceUVTile > 0f)
            {
                for (int s = 0; s < source.subMeshCount; s++)
                {
                    if (o.distanceUVSubmeshes != null && System.Array.IndexOf(o.distanceUVSubmeshes, s) < 0) continue;
                    foreach (int idx in source.GetTriangles(s)) distanceUV[idx] = true;
                }
            }

            int total = vc * copies;
            var v = new Vector3[total];
            var nrm = new Vector3[total];
            var tan = new Vector4[total];
            var uv = new Vector2[total];
            var uv1 = srcUV1.Count == vc ? new Vector2[total] : null;
            var col = srcC != null && srcC.Length == vc ? new Color32[total] : null;
            bool hasN = srcN != null && srcN.Length == vc;
            bool hasT = srcT != null && srcT.Length == vc;
            bool hasUV = srcUV.Count == vc;

            Matrix4x4 toLocal = target != null ? target.worldToLocalMatrix : Matrix4x4.identity;
            for (int c = 0; c < copies; c++)
            {
                for (int i = 0; i < vc; i++)
                {
                    int k = c * vc + i;
                    Vector3 p = srcV[i];
                    float u01 = (p.z - minZ) / srcLen;
                    float d = o.startDistance + (c + u01) * copyLen;
                    TrackFrame f = track.Evaluate(d);
                    Vector3 r = o.useBank ? f.right : f.flatRight;
                    Vector3 up = o.useBank ? f.up : f.flatUp;
                    Vector3 world = f.position + r * (p.x * o.scale.x + o.lateralOffset) + up * (p.y * o.scale.y + o.verticalOffset);
                    v[k] = toLocal.MultiplyPoint3x4(world);
                    if (hasN)
                    {
                        Vector3 n = srcN[i];
                        Vector3 wn = (r * (n.x / o.scale.x) + up * (n.y / o.scale.y) + f.forward * n.z).normalized;
                        nrm[k] = toLocal.MultiplyVector(wn).normalized;
                    }
                    if (hasT)
                    {
                        Vector4 t = srcT[i];
                        Vector3 wt = (r * t.x + up * t.y + f.forward * t.z).normalized;
                        Vector3 lt = toLocal.MultiplyVector(wt).normalized;
                        tan[k] = new Vector4(lt.x, lt.y, lt.z, t.w);
                    }
                    Vector2 suv = hasUV ? srcUV[i] : Vector2.zero;
                    if (distanceUV[i]) suv.y = d / o.distanceUVTile;
                    uv[k] = suv;
                    if (uv1 != null) uv1[k] = srcUV1[i];
                    if (col != null) col[k] = srcC[i];
                }
            }

            var mesh = new Mesh { name = name ?? (source.name + "_Bent") };
            mesh.indexFormat = total > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
            mesh.vertices = v;
            if (hasN) mesh.normals = nrm;
            if (hasT) mesh.tangents = tan;
            mesh.uv = uv;
            if (uv1 != null) mesh.uv2 = uv1;
            if (col != null) mesh.colors32 = col;
            mesh.subMeshCount = source.subMeshCount;
            for (int s = 0; s < source.subMeshCount; s++)
            {
                int[] tri = source.GetTriangles(s);
                var all = new int[tri.Length * copies];
                for (int c = 0; c < copies; c++)
                {
                    int off = c * vc;
                    for (int j = 0; j < tri.Length; j++) all[c * tri.Length + j] = tri[j] + off;
                }
                mesh.SetTriangles(all, s, false);
            }
            if (!hasN) mesh.RecalculateNormals();
            if (!hasT && hasUV) mesh.RecalculateTangents();
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
